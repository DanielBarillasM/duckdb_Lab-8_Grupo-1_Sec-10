"""Genera siete figuras SVG y un tablero HTML reproducible desde resultados SQL."""

from __future__ import annotations

import html
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from lab8_common import RESULTS, ROOT

DOCS = ROOT / "docs"
FIGURES = DOCS / "figures"
YELLOW = "#df9b1d"
GREEN = "#16806b"
NAVY = "#17263e"
GRID = "#dbe3e8"
YEAR_COLORS = {2024: "#7890aa", 2025: "#3d5f83", 2026: "#df9b1d"}


def frame(name: str) -> pd.DataFrame:
    path = RESULTS / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Falta {path}; ejecute scripts/run_analysis.py")
    return pd.read_csv(path)


def style(ax, title: str, ylabel: str = "") -> None:
    ax.set_title(title, loc="left", fontsize=14, color=NAVY, fontweight="bold", pad=18)
    ax.set_ylabel(ylabel, color=NAVY)
    ax.tick_params(colors=NAVY)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(GRID)


def save(fig, name: str) -> None:
    fig.savefig(FIGURES / name, format="svg", bbox_inches="tight",
                facecolor="#ffffff")
    plt.close(fig)


def grouped_bars(data: pd.DataFrame, column: str, title: str, ylabel: str,
                 name: str, fmt: str = ",.1f") -> None:
    years = [2024, 2025, 2026]
    fig, ax = plt.subplots(figsize=(8.4, 4.5), constrained_layout=True)
    width = 0.32
    for index, (taxi, color, label) in enumerate(
        (("yellow", YELLOW, "Amarillo"), ("green", GREEN, "Verde"))
    ):
        subset = data[data["tipo"] == taxi].set_index("anio").reindex(years)
        positions = [n + (index - 0.5) * width for n in range(3)]
        bars = ax.bar(positions, subset[column], width=width, color=color, label=label)
        for bar in bars:
            value = bar.get_height()
            if pd.notna(value):
                ax.annotate(format(value, fmt),
                            (bar.get_x() + bar.get_width() / 2, value),
                            xytext=(0, 4), textcoords="offset points",
                            ha="center", fontsize=8, color=NAVY)
    ax.set_xticks(range(3), [str(year) for year in years])
    ax.legend(frameon=False, ncol=2)
    ax.margins(y=0.17)
    style(ax, title, ylabel)
    save(fig, name)


def monthly_chart(monthly: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.4), constrained_layout=True)
    for ax, taxi, label in zip(axes, ("yellow", "green"), ("Amarillo", "Verde")):
        for year in (2024, 2025, 2026):
            subset = monthly[(monthly["tipo"] == taxi) & (monthly["anio"] == year)]
            ax.plot(subset["mes"], subset["viajes"], marker="o", markersize=4,
                    linewidth=2.2, color=YEAR_COLORS[year], label=str(year))
        ax.set_xlim(1, 12)
        ax.set_xticks(range(1, 13))
        ax.set_xlabel("Mes")
        ax.legend(frameon=False, ncol=3, fontsize=8)
        style(ax, f"Viajes mensuales · taxi {label.lower()}", "Viajes")
    save(fig, "01_viajes_mensuales.svg")


def hourly_chart(hourly: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8.4, 4.5), constrained_layout=True)
    for taxi, color, label in (("yellow", YELLOW, "Amarillo"),
                               ("green", GREEN, "Verde")):
        subset = hourly[(hourly["tipo"] == taxi) & (hourly["anio"] == 2026)]
        values = subset["viajes"] / subset["viajes"].sum() * 100
        ax.plot(subset["hora"], values, linewidth=2.3, color=color, label=label)
    ax.set_xticks(range(0, 24, 2))
    ax.set_xlabel("Hora de recogida")
    ax.legend(frameon=False)
    style(ax, "Demanda por hora · 2026", "% de viajes del tipo")
    save(fig, "07_horas_2026.svg")


def render_card(number: str, title: str, image: str, question: str,
                sql: str, interpretation: str) -> str:
    return f"""<article class="chart-card">
      <div class="eyebrow">INDICADOR {number} · <code>{html.escape(sql)}</code></div>
      <h2>{html.escape(title)}</h2>
      <p class="question">{html.escape(question)}</p>
      <img src="figures/{html.escape(image)}" alt="{html.escape(title)}">
      <p class="interpretation">{html.escape(interpretation)}</p>
    </article>"""


def build() -> Path:
    FIGURES.mkdir(parents=True, exist_ok=True)
    monthly = frame("03_viajes_mensuales")
    comparable = frame("12_comparacion_ene_ago")
    hourly = frame("06_horas")
    coverage = frame("01_cobertura")
    monthly_chart(monthly)
    grouped_bars(comparable.assign(viajes_millones=comparable["viajes"] / 1e6),
                 "viajes_millones", "Volumen comparable · enero a agosto",
                 "Millones de viajes", "02_volumen_comparable.svg", ",.2f")
    grouped_bars(comparable, "importe_medio_usd", "Importe medio por viaje",
                 "USD", "03_importe_medio.svg", ",.2f")
    grouped_bars(comparable, "distancia_p50_millas", "Distancia mediana",
                 "Millas", "04_distancia_mediana.svg", ",.2f")
    grouped_bars(comparable, "tarjeta_pct", "Viajes pagados con tarjeta",
                 "% de viajes", "05_tarjeta.svg", ",.1f")
    grouped_bars(comparable, "propina_sobre_tarifa_pct", "Propina registrada sobre tarifa",
                 "% en pagos con tarjeta", "06_propinas.svg", ",.1f")
    hourly_chart(hourly)

    a24 = comparable[(comparable.anio == 2024) & (comparable.tipo == "yellow")].iloc[0]
    a26 = comparable[(comparable.anio == 2026) & (comparable.tipo == "yellow")].iloc[0]
    g24 = comparable[(comparable.anio == 2024) & (comparable.tipo == "green")].iloc[0]
    g26 = comparable[(comparable.anio == 2026) & (comparable.tipo == "green")].iloc[0]
    change_yellow = (a26.viajes / a24.viajes - 1) * 100
    change_green = (g26.viajes / g24.viajes - 1) * 100
    peak = hourly[hourly.anio == 2026].sort_values("viajes", ascending=False).groupby("tipo").first()

    cards = "\n".join([
        render_card("01", "Serie mensual de viajes", "01_viajes_mensuales.svg",
                    "¿Cuándo cambia la demanda de cada servicio?", "03_viajes_mensuales.sql",
                    "El corte de 2026 termina en agosto; las líneas no extrapolan septiembre-diciembre."),
        render_card("02", "Volumen enero-agosto", "02_volumen_comparable.svg",
                    "¿Cómo cambió la demanda en una ventana común?", "12_comparacion_ene_ago.sql",
                    f"Amarillos: {change_yellow:+.1f}% entre 2024 y 2026; verdes: {change_green:+.1f}%."),
        render_card("03", "Importe medio", "03_importe_medio.svg",
                    "¿Cómo evoluciona el importe cobrado por viaje?", "12_comparacion_ene_ago.sql",
                    "Importes nominales en USD; la comparación no ajusta por inflación ni mezcla de rutas."),
        render_card("04", "Distancia mediana", "04_distancia_mediana.svg",
                    "¿Cambió la longitud típica de los viajes?", "12_comparacion_ene_ago.sql",
                    "La mediana se calcula sobre distancias positivas y resiste mejor viajes extremos."),
        render_card("05", "Pago con tarjeta", "05_tarjeta.svg",
                    "¿Qué fracción de viajes se paga con tarjeta?", "12_comparacion_ene_ago.sql",
                    "El código 1 de payment_type se identifica como tarjeta según el diccionario TLC."),
        render_card("06", "Propinas registradas", "06_propinas.svg",
                    "¿Qué parte de la tarifa representan las propinas?", "12_comparacion_ene_ago.sql",
                    "Se consideran pagos con tarjeta y tarifas positivas; las propinas en efectivo pueden no registrarse."),
        render_card("07", "Perfil horario", "07_horas_2026.svg",
                    "¿A qué hora se concentra la demanda de cada taxi?", "06_horas.sql",
                    f"Pico amarillo: {int(peak.loc['yellow', 'hora']):02d}:00; "
                    f"pico verde: {int(peak.loc['green', 'hora']):02d}:00 en 2026."),
    ])
    total = int(coverage.viajes.sum())
    document = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Laboratorio 8 · Tablero de taxis NYC</title>
<style>
:root{{--ink:#17263e;--muted:#617187;--paper:#f3f6f8;--card:#fff;--accent:#176b79;--line:#dce5e9}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font-family:Inter,Segoe UI,Arial,sans-serif;line-height:1.5}}
header{{background:linear-gradient(125deg,#10263c,#176b79);color:white;padding:52px max(24px,calc((100vw - 1250px)/2)) 48px}}
header .eyebrow{{color:#bfe4e5}}h1{{font-size:clamp(2rem,4vw,3.4rem);line-height:1.1;margin:12px 0}}
header p{{max-width:740px;color:#dcecee}}main{{max-width:1250px;margin:auto;padding:28px 24px 64px}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:-54px;position:relative}}
.stat,.chart-card{{background:var(--card);border:1px solid var(--line);border-radius:18px;box-shadow:0 9px 26px #12263a0b}}
.stat{{padding:22px}}.stat strong{{display:block;font-size:2rem;color:var(--accent)}}.stat span{{color:var(--muted)}}
.section-title{{margin:38px 0 18px;font-size:1.5rem}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}
.chart-card{{padding:22px}}.chart-card h2{{margin:7px 0 2px;font-size:1.25rem}}.eyebrow{{font-size:.72rem;letter-spacing:.1em;font-weight:700;color:var(--accent)}}
.question{{margin:0;color:var(--muted)}}.chart-card img{{display:block;width:100%;height:auto;margin:15px 0}}
.interpretation{{border-top:1px solid var(--line);padding-top:13px;margin-bottom:0}}code{{letter-spacing:0;font-size:.75rem}}
footer{{max-width:1250px;margin:auto;padding:0 24px 38px;color:var(--muted);font-size:.9rem}}
@media(max-width:800px){{.grid,.stats{{grid-template-columns:1fr}}.stats{{margin-top:18px}}}}
</style></head><body>
<header><div class="eyebrow">UNIVERSIDAD DEL VALLE DE GUATEMALA · CC3084 · DATA SCIENCE</div>
<h1>NYC Taxi / DuckDB</h1><p>Laboratorio 8 · Grupo 1 · Sección 10. Indicadores derivados de Parquet oficiales de Yellow y Green Taxi para 2024, 2025 y los meses publicados de 2026.</p></header>
<main><div class="stats"><div class="stat"><strong>{total:,}</strong><span>Registros originales</span></div>
<div class="stat"><strong>{len(coverage)}</strong><span>Archivos mensuales</span></div>
<div class="stat"><strong>7</strong><span>Indicadores visualizados</span></div></div>
<h2 class="section-title">Panorama conjunto</h2><div class="grid">{cards}</div></main>
<footer>Fuente: NYC TLC Trip Record Data. Cada gráfico se reproduce con el archivo SQL indicado y scripts/build_dashboard.py. La ventana enero-agosto iguala la cobertura temporal entre años; 2026 no representa un año completo.</footer>
</body></html>"""
    path = DOCS / "tablero.html"
    path.write_text(document, encoding="utf-8")
    print(f"Tablero listo: {path}")
    return path


if __name__ == "__main__":
    build()
