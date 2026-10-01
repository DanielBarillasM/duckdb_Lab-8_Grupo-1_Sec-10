"""Reproduce siete tarjetas y un tablero real en la instancia local de Metabase."""

from __future__ import annotations

import json
import os

from lab8_common import PROCESSED
from setup_metabase import BASE_URL, session

RESULT_DIR = "/workspace/data/processed/results"
DATABASE_NAME = "NYC TLC - DuckDB"
DASHBOARD_NAME = "Laboratorio 8 | Yellow y Green Taxi"


def require(response):
    if not response.ok:
        raise RuntimeError(f"Metabase {response.request.method} {response.url}: "
                           f"HTTP {response.status_code}: {response.text[:700]}")
    return response.json()


def series_query(filename: str, column: str) -> str:
    return f"""
        SELECT cast(anio AS VARCHAR) AS anio,
               max({column}) FILTER (WHERE tipo = 'yellow') AS amarillo,
               max({column}) FILTER (WHERE tipo = 'green') AS verde
        FROM read_csv_auto('{RESULT_DIR}/{filename}.csv')
        GROUP BY anio ORDER BY anio
    """


CARDS = [
    ("01 · Viajes mensuales", "line", f"""
        SELECT make_date(anio, mes, 1) AS periodo,
               sum(viajes) FILTER (WHERE tipo = 'yellow') AS amarillo,
               sum(viajes) FILTER (WHERE tipo = 'green') AS verde
        FROM read_csv_auto('{RESULT_DIR}/03_viajes_mensuales.csv')
        GROUP BY 1 ORDER BY 1
    """, "03_viajes_mensuales.sql; 2026 termina en agosto", "periodo"),
    ("02 · Volumen enero-agosto", "bar",
     series_query("12_comparacion_ene_ago", "viajes"),
     "12_comparacion_ene_ago.sql; mismo periodo entre años", "anio"),
    ("03 · Importe medio (USD)", "bar",
     series_query("12_comparacion_ene_ago", "importe_medio_usd"),
     "12_comparacion_ene_ago.sql; USD nominales", "anio"),
    ("04 · Distancia mediana (millas)", "bar",
     series_query("12_comparacion_ene_ago", "distancia_p50_millas"),
     "12_comparacion_ene_ago.sql; solo distancias positivas", "anio"),
    ("05 · Pagos con tarjeta (%)", "bar",
     series_query("12_comparacion_ene_ago", "tarjeta_pct"),
     "12_comparacion_ene_ago.sql; payment_type=1", "anio"),
    ("06 · Propina sobre tarifa (%)", "bar",
     series_query("12_comparacion_ene_ago", "propina_sobre_tarifa_pct"),
     "12_comparacion_ene_ago.sql; tarjeta y tarifa positiva", "anio"),
    ("07 · Perfil horario 2026", "line", f"""
        SELECT hora,
               sum(viajes) FILTER (WHERE tipo = 'yellow') AS amarillo,
               sum(viajes) FILTER (WHERE tipo = 'green') AS verde
        FROM read_csv_auto('{RESULT_DIR}/06_horas.csv')
        WHERE anio = 2026 GROUP BY hora ORDER BY hora
    """, "06_horas.sql; los volúmenes absolutos difieren entre tipos", "hora"),
]


def database_id(client) -> int:
    databases = require(client.get(f"{BASE_URL}/api/database", timeout=30))["data"]
    for db in databases:
        if db["name"] == DATABASE_NAME:
            return db["id"]
    created = require(client.post(f"{BASE_URL}/api/database", json={
        "name": DATABASE_NAME, "engine": "duckdb",
        "details": {"database_file": ":memory:", "read_only": False},
    }, timeout=90))
    return created["id"]


def query_check(client, db_id: int) -> None:
    payload = {"database": db_id, "type": "native",
               "native": {"query": "SELECT count(*) AS n FROM "
                         f"read_csv_auto('{RESULT_DIR}/12_comparacion_ene_ago.csv')"}}
    result = require(client.post(f"{BASE_URL}/api/dataset", json=payload, timeout=90))
    if result.get("status") != "completed" or result["data"]["rows"][0][0] != 6:
        raise RuntimeError(f"DuckDB no pudo leer el resumen de seis filas: {result.get('error')}")


def card_ids(client, db_id: int) -> list[int]:
    existing = {card["name"]: card["id"] for card in
                require(client.get(f"{BASE_URL}/api/card", timeout=30))}
    result = []
    for name, display, query, description, dimension in CARDS:
        payload = {
            "name": name, "description": description, "display": display,
            "visualization_settings": {
                "graph.dimensions": [dimension],
                "graph.metrics": ["amarillo", "verde"],
                "series_settings": {
                    "amarillo": {"color": "#DF9B1D"},
                    "verde": {"color": "#16806B"},
                },
            },
            "dataset_query": {"database": db_id, "type": "native",
                              "native": {"query": query, "template-tags": {}}},
        }
        if name in existing:
            card_id = existing[name]
            require(client.put(f"{BASE_URL}/api/card/{card_id}", json=payload, timeout=40))
        else:
            card_id = require(client.post(f"{BASE_URL}/api/card", json=payload,
                                          timeout=40))["id"]
        result.append(card_id)
        print(f"Tarjeta {name}: {card_id}", flush=True)
    return result


def dashboard_id(client, cards: list[int]) -> int:
    dashboards = require(client.get(f"{BASE_URL}/api/dashboard", timeout=30))
    if isinstance(dashboards, dict):
        dashboards = dashboards.get("data", [])
    found = next((item for item in dashboards if item["name"] == DASHBOARD_NAME), None)
    if found:
        dashboard = found["id"]
    else:
        dashboard = require(client.post(f"{BASE_URL}/api/dashboard", json={
            "name": DASHBOARD_NAME,
            "description": "Siete indicadores SQL de NYC TLC; comparación enero-agosto 2024-2026.",
        }, timeout=40))["id"]
    layout = []
    for index, card_id in enumerate(cards):
        layout.append({"id": -(index + 1), "card_id": card_id,
                       "row": (index // 2) * 7, "col": (index % 2) * 12,
                       "size_x": 12, "size_y": 6})
    require(client.put(f"{BASE_URL}/api/dashboard/{dashboard}/cards",
                       json={"cards": layout}, timeout=40))
    return dashboard


def main() -> int:
    client = session()
    db_id = database_id(client)
    query_check(client, db_id)
    cards = card_ids(client, db_id)
    dashboard = dashboard_id(client, cards)
    browser_url = os.getenv("LAB8_METABASE_PUBLIC_URL", "http://127.0.0.1:3000")
    output = {"database_id": db_id, "dashboard_id": dashboard,
              "card_ids": cards, "url": f"{browser_url}/dashboard/{dashboard}"}
    (PROCESSED / "metabase_dashboard.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Tablero Metabase:", output["url"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
