"""Compone la libreta del laboratorio sobre la plantilla oficial de experimento."""

from __future__ import annotations

from textwrap import dedent

import nbformat

from lab8_common import ROOT

NOTEBOOK = ROOT / "notebooks" / "lab8_analisis.ipynb"


def md(text: str):
    return nbformat.v4.new_markdown_cell(dedent(text).strip())


def code(text: str):
    return nbformat.v4.new_code_cell(dedent(text).strip())


def build() -> None:
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    notebook.metadata["kernelspec"] = {
        "display_name": "Python 3", "language": "python", "name": "python3"
    }
    notebook.metadata["language_info"] = {"name": "python", "version": "3.11"}
    notebook.cells = [
        md("""
        <style>
        .lab8-hero {background:linear-gradient(130deg,#10263c,#176b79);color:white;
          border-radius:18px;padding:34px 40px;margin:8px 0 22px;font-family:Segoe UI,Arial,sans-serif}
        .lab8-hero h1{font-size:2.1rem;margin:10px 0 8px;color:white}
        .lab8-hero p{color:#dcecee;margin:0}.lab8-kicker{letter-spacing:.13em;font-size:.78rem;font-weight:700}
        .lab8-note{background:#f1f6f7;border-left:4px solid #176b79;padding:12px 16px}
        </style>
        <div class="lab8-hero"><div class="lab8-kicker">UNIVERSIDAD DEL VALLE DE GUATEMALA · CC3084 · GRUPO 1 · SECCIÓN 10</div>
        <h1>Laboratorio 8 · DuckDB</h1><p>Análisis incremental de Yellow y Green Taxi · NYC TLC · 2024–2026</p></div>

        **Integrantes:** Jorge Gabriel Palacios Sales (231385), Pablo Daniel Barillas Moreno (22193) y Roberto Emiliano Otoniel (23968).

        **Objetivo.** Consultar Parquet directamente, analizar viajes y calidad, incorporar años sin rehacer el flujo, comparar consultas con una tabla DuckDB y comunicar siete indicadores.
        """),
        md("""
        ## 1 · Preparación y reproducibilidad

        El repositorio se ejecuta con Docker Compose. Los datos originales viven en `data/raw/` y se excluyen de Git. Antes de esta libreta ejecute, desde el contenedor o siguiendo el README, `download_data.py --years 2024 2025 2026`, `verify_data.py --online`, `run_analysis.py`, `benchmark.py` y `build_dashboard.py`. Esta libreta comprueba que existen los resultados y los vuelve a generar si detecta una descarga posterior.

        **Hipótesis exploratorias:** el volumen mensual y el perfil horario difieren entre tipos de taxi; los valores extremos pueden elevar la media de distancia; los tres años deben compararse con una ventana temporal común.
        """),
        code("""
        from pathlib import Path
        import json, sys
        import pandas as pd
        from IPython.display import display, HTML, SVG

        root = next(p for p in (Path.cwd(), *Path.cwd().parents)
                    if (p / 'scripts' / 'lab8_common.py').exists())
        sys.path.insert(0, str(root / 'scripts'))
        from lab8_common import connect_with_view, parquet_files, sql_path_list
        from run_analysis import run

        files = parquet_files((2024, 2025, 2026))
        assert files, 'Primero descargue los Parquet con scripts/download_data.py'
        results = root / 'data' / 'processed' / 'results'
        manifest_path = results / 'manifest.json'
        if not manifest_path.exists() or json.loads(manifest_path.read_text())['archivos'] != len(files):
            run((2024, 2025, 2026))
        manifest = json.loads(manifest_path.read_text())
        conn = connect_with_view((2024, 2025, 2026))
        display(HTML(f'<div class="lab8-note"><b>{len(files)} Parquet</b> · '
                     f'DuckDB {manifest["duckdb"]} · '
                     f'{len(manifest["resultados"])} consultas documentadas</div>'))
        """),
        md("""
        ## 2 · Exploración directa de Parquet

        `read_parquet` interpreta metadatos y columnas sin una importación previa. Los esquemas originales de Yellow y Green Taxi difieren; `union_by_name=true` permite leerlos juntos y la vista temporal `trips` unifica los nombres de fecha. Las muestras siguientes vienen directamente de los archivos originales.
        """),
        code("""
        for taxi in ('yellow', 'green'):
            path = next(p for p in files if p.parent.parent.name == taxi and p.parent.name == '2026')
            source = sql_path_list([path])
            print(f'\\n{taxi.upper()} · {path.name} · esquema original')
            display(conn.execute(f'DESCRIBE SELECT * FROM read_parquet({source})').df().head(25))
            display(conn.execute(f'SELECT * FROM read_parquet({source}) LIMIT 3').df())
        """),
        code("""
        coverage = pd.read_csv(results / '01_cobertura.csv')
        quality = pd.read_csv(results / '02_calidad.csv')
        print('Archivos:', int(coverage.archivos.sum()),
              '| registros:', f'{int(coverage.viajes.sum()):,}')
        display(coverage.groupby(['anio', 'tipo'], as_index=False)[['archivos', 'viajes']].sum())
        display(quality)
        """),
        md("""
        **Decisión de calidad.** Conservamos los registros originales. Las métricas de viajes excluyen recogidas fuera del año del archivo. Para distancias típicas usamos mediana de valores positivos; para propinas usamos solo pagos con tarjeta y tarifas positivas. `payment_type=0` y pasajeros nulos se informan como problemas de interpretación. La tabla completa de consultas, objetivos, resultados y decisiones está en `docs/consultas.md`.
        """),
        md("""
        ## 3 · Preguntas analíticas y resultados

        Las doce preguntas están implementadas en `sql/01_*.sql` a `sql/12_*.sql`: cobertura, calidad, serie mensual, distancias, pagos, horas, propinas, días, zonas, duración, importes y comparación enero–agosto. La vista lee los archivos requeridos según el año y el tipo. Aquí se muestran resultados resumidos; cada CSV completo es regenerable con `scripts/run_analysis.py`.
        """),
        code("""
        comparable = pd.read_csv(results / '12_comparacion_ene_ago.csv')
        distances = pd.read_csv(results / '04_distancias.csv')
        payments = pd.read_csv(results / '05_pagos.csv')
        display(comparable)
        display(distances[['anio','tipo','media_millas','p50_millas','p99_millas','mas_100_millas']])
        """),
        md("""
        ## 4 · Siete indicadores visualizados

        Cada figura se obtiene de consultas DuckDB documentadas. Para comparar 2024, 2025 y 2026 se emplea enero–agosto en los indicadores anuales; 2026 todavía no tiene doce meses publicados. El tablero conjunto también está en `docs/tablero.html` y Metabase se reproduce con `scripts/create_metabase_dashboard.py`.
        """),
        code("""
        figures = root / 'docs' / 'figures'
        for name in ('01_viajes_mensuales.svg', '02_volumen_comparable.svg',
                     '03_importe_medio.svg', '04_distancia_mediana.svg'):
            display(SVG(filename=str(figures / name)))
        """),
        code("""
        for name in ('05_tarjeta.svg', '06_propinas.svg', '07_horas_2026.svg'):
            display(SVG(filename=str(figures / name)))
        """),
        md("""
        **Interpretación.** En enero–agosto, Yellow Taxi pasa de 26.39 M viajes (2024) a 29.70 M (2026), mientras Green Taxi desciende de 443 mil a 337 mil. La distancia mediana es cercana a dos millas para ambos tipos; las medias se elevan por extremos. La cuota registrada como tarjeta en amarillo baja de 74.05% a 63.77%, pero aumenta el código 0, por lo que no atribuimos el cambio a preferencias de pago sin investigar la codificación.
        """),
        md("""
        ## 5 · Benchmark: Parquet frente a tabla DuckDB

        `scripts/benchmark.py` materializa una proyección de seis columnas, ejecuta las **mismas tres consultas** sobre ambos orígenes, verifica equivalencia de resultados y cronometra cuatro repeticiones con orden alternado. Los tamaños son 16 archivos (2026), 40 (2024+2026) y 64 (los tres años). La tabla de abajo usa la mediana de tiempos; la creación de la tabla es un costo previo distinto del tiempo de consulta.
        """),
        code("""
        benchmark_path = root / 'docs' / 'benchmark_resultados.csv'
        assert benchmark_path.exists(), 'Ejecute primero scripts/benchmark.py'
        benchmark = pd.read_csv(benchmark_path)
        view = benchmark.pivot_table(index=['escenario','consulta'], columns='fuente',
                                     values='mediana_segundos').reset_index()
        view['Parquet / DuckDB'] = (view['Parquet'] / view['DuckDB']).round(2)
        display(view)
        """),
        md("""
        **Lectura del benchmark.** La tabla materializada suele acelerar agregaciones repetidas sobre el conjunto grande, pero exige espacio y tiempo de construcción. Parquet permite consultas ad hoc y nuevos meses sin cargar una tabla; en consultas simples o algunos tamaños puede igualar o superar a la tabla. Las mediciones dependen de caché, hardware y orden de ejecución. `docs/benchmark_detalle.csv` conserva cada repetición.
        """),
        md("""
        ## 6 · Discusión y conclusiones

        1. **Utilidad de DuckDB.** SQL directo sobre Parquet, proyección de columnas, lectura de metadatos, `union_by_name` y almacenamiento local facilitaron un flujo sin servidor SQL tradicional.
        2. **Parquet directo.** Ahorra la importación y acepta archivos mensuales nuevos; consultas repetidas pueden pagar de nuevo el costo de lectura y hay que manejar esquemas distintos.
        3. **Tabla materializada.** Mejora varias agregaciones repetidas, pero duplica una parte de los datos, requiere reconstrucción al entrar nuevos archivos y puede bloquearse si otro proceso abre la base para escritura.
        4. **Frente a Pandas.** DuckDB agrega millones de filas sin cargar todo el conjunto como un DataFrame en memoria; Pandas queda para los resultados pequeños y las figuras.
        5. **Incrementalidad.** La descarga evita duplicados y usa rutas `tipo/año/mes`; la vista deriva año y tipo del nombre, mientras `union_by_name` tolera columnas añadidas o ausentes.
        6. **Automatización futura.** Programar descarga, inventario, pruebas de integridad, actualización de indicadores y alertas de cambios de esquema.
        7. **Reproducibilidad.** Dependencias fijadas en Docker, SQL versionado, filtros explícitos y datos excluidos de Git permiten rehacer los resultados.
        8. **Aprendizaje a escala.** Nulos, códigos de pago nuevos y valores extremos cambian de manera material la interpretación; una muestra pequeña podría no revelarlo.

        **Limitaciones:** 2026 solo incluye enero–agosto; importes nominales sin ajuste de inflación; los cambios observados no prueban causalidad. Véanse `docs/consultas.md` y `docs/metodologia.md` para detalle.
        """),
        code("""
        conn.close()
        print('Laboratorio ejecutado con resultados visibles y fuentes trazables.')
        """),
    ]
    nbformat.validate(notebook)
    nbformat.write(notebook, NOTEBOOK)
    print(f"Libreta generada: {NOTEBOOK} ({len(notebook.cells)} celdas)")


if __name__ == "__main__":
    build()
