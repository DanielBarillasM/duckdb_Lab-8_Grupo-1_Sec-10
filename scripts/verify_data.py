"""Audita integridad y cobertura de los Parquet TLC sin cargar filas en RAM."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq
import requests

from download_data import ANIOS_PERMITIDOS, TIPOS_TAXI, URL_BASE, ruta_destino
from lab8_common import PROCESSED


def remote_status(url: str) -> tuple[int, int | None]:
    response = requests.head(url, timeout=30, allow_redirects=True)
    if response.status_code not in (200, 403, 404):
        response.raise_for_status()
    size = response.headers.get("Content-Length")
    return response.status_code, int(size) if size and size.isdigit() else None


def audit(years: tuple[int, ...], online: bool) -> tuple[list[dict], list[dict]]:
    inventory: list[dict] = []
    schemas: list[dict] = []
    for year in years:
        for taxi in TIPOS_TAXI:
            for month in range(1, 13):
                path = ruta_destino(taxi, year, month)
                status, remote_size = (None, None)
                if online:
                    url = f"{URL_BASE}/{path.name}"
                    try:
                        status, remote_size = remote_status(url)
                    except requests.RequestException as error:
                        status = f"network_error:{error.__class__.__name__}"
                row = {
                    "anio": year, "tipo": taxi, "mes": month,
                    "archivo": path.name, "existe": path.is_file(),
                    "bytes": path.stat().st_size if path.is_file() else 0,
                    "filas": None, "row_groups": None, "valido": False,
                    "estado_remoto": status, "bytes_remotos": remote_size,
                    "error": "",
                }
                if path.is_file():
                    try:
                        parquet = pq.ParquetFile(path)
                        row["filas"] = parquet.metadata.num_rows
                        row["row_groups"] = parquet.metadata.num_row_groups
                        row["valido"] = row["bytes"] > 0
                        for field in parquet.schema_arrow:
                            schemas.append({"anio": year, "tipo": taxi, "mes": month,
                                            "archivo": path.name, "columna": field.name,
                                            "tipo_dato": str(field.type)})
                    except Exception as error:
                        row["error"] = f"{error.__class__.__name__}: {error}"
                if remote_size is not None and row["existe"] and row["bytes"] != remote_size:
                    row["valido"] = False
                    row["error"] = "tamanio local distinto al publicado"
                inventory.append(row)
    return inventory, schemas


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", nargs="+", type=int, choices=ANIOS_PERMITIDOS,
                        default=list(ANIOS_PERMITIDOS))
    parser.add_argument("--online", action="store_true",
                        help="consulta la fuente para distinguir archivos faltantes de meses no publicados")
    args = parser.parse_args()
    inventory, schemas = audit(tuple(dict.fromkeys(args.years)), args.online)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    for name, rows in (("inventario.csv", inventory), ("esquemas.csv", schemas)):
        if rows:
            with (PROCESSED / name).open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
    summary = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "anios": args.years,
        "archivos_locales": sum(bool(row["existe"]) for row in inventory),
        "archivos_validos": sum(bool(row["valido"]) for row in inventory),
        "filas": sum(row["filas"] or 0 for row in inventory),
        "publicados": sum(row["estado_remoto"] == 200 for row in inventory) if args.online else None,
        "publicados_faltantes": [row["archivo"] for row in inventory
                                if row["estado_remoto"] == 200 and not row["valido"]],
        "historicos_faltantes": [row["archivo"] for row in inventory
                                 if row["anio"] in (2024, 2025) and not row["valido"]],
    }
    (PROCESSED / "verificacion.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.online and summary["publicados_faltantes"]:
        return 1
    if summary["historicos_faltantes"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
