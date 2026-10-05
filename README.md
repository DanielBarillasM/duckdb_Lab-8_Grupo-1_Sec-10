# Laboratorio 8 · DuckDB y NYC TLC

Análisis reproducible de viajes **Yellow y Green Taxi** en archivos Parquet oficiales de 2024, 2025 y los meses publicados de 2026. Proyecto de **CC3084 · Data Science · Sección 10 · Grupo 1**, Universidad del Valle de Guatemala, segundo semestre de 2026.

| Integrante | Carné |
|---|---:|
| Jorge Gabriel Palacios Sales | 231385 |
| Pablo Daniel Barillas Moreno | 22193 |
| Roberto Emiliano Otoniel Camposeco Torres | 23968 |

Este trabajo parte del [repositorio docente](https://github.com/menene/duckdb). La entrega solicitada es la **URL del fork del equipo**, con código, consultas, libreta, metodología, benchmark y evidencia del tablero. Los Parquet y la base materializada **no se suben a Git**.

## Resultados en breve

- **64 Parquet válidos** y **121,184,384 filas**: 12 meses por servicio en 2024 y 2025, y enero–agosto por servicio en 2026. Corte observado: **1 de octubre de 2026**; los meses restantes de 2026 aún no estaban publicados.
- **12 consultas SQL** directas sobre Parquet; el catálogo explica su pregunta, filtros, resultado y decisión: [docs/consultas.md](docs/consultas.md).
- **7 indicadores** en un tablero real de Metabase, con [evidencia](docs/evidencia_metabase.png), más un [tablero HTML](docs/tablero.html) y figuras SVG reproducibles.
- Benchmark de **3 consultas equivalentes × 3 tamaños × 2 fuentes**, cuatro repeticiones con orden alternado: [resumen](docs/benchmark_resultados.csv) y [mediciones individuales](docs/benchmark_detalle.csv).
- [Libreta ejecutada](notebooks/lab8_analisis.ipynb) con tablas, gráficos e interpretación; [metodología y discusión](docs/metodologia.md).

## Requisitos y puesta en marcha

Se necesita Docker con Compose, Git, conexión a internet y espacio libre suficiente. Los datos descargados ocupan aproximadamente 2 GB; Docker y la tabla de DuckDB requieren varios GB adicionales. Los servicios se exponen solo en `127.0.0.1`, sin autenticación en Jupyter, por lo que **no deben publicarse en una red externa**.

1. Hacer fork de <https://github.com/menene/duckdb> en GitHub y clonar **el fork propio**. Si ya se trabajó sobre un clon del docente, cambiar `origin` al fork antes de enviar; no hacer `push` al repositorio del docente.
2. Desde la raíz del proyecto:

   ```powershell
   docker compose up -d --build
   docker compose ps
   ```

3. Abrir JupyterLab en <http://127.0.0.1:8888/lab> y Metabase en <http://127.0.0.1:3000>. El arranque inicial de Metabase puede tardar unos minutos.

El contenedor de análisis se llama `lab8-lab`. Las instrucciones siguientes usan `docker exec`; también pueden ejecutarse dentro de la terminal de JupyterLab sin el prefijo `docker exec lab8-lab`.

## Reproducir datos y análisis

```powershell
# Descarga incremental: no repite archivos existentes.
docker exec lab8-lab python scripts/download_data.py --years 2024 2025 2026

# Comprueba metadatos Parquet y, con --online, tamaño y disponibilidad remota.
docker exec lab8-lab python scripts/verify_data.py --online

# Ejecuta las 12 consultas SQL y guarda resultados pequeños como CSV.
docker exec lab8-lab python scripts/run_analysis.py

# Genera siete SVG y el tablero HTML a partir de esos resultados.
docker exec lab8-lab python scripts/build_dashboard.py

# Materializa una proyección de seis columnas y realiza el benchmark completo.
docker exec lab8-lab python scripts/benchmark.py --repetitions 4

# Ejecuta y guarda la libreta con tablas y gráficos visibles.
docker exec lab8-lab jupyter nbconvert --to notebook --execute --inplace notebooks/lab8_analisis.ipynb --ExecutePreprocessor.timeout=600
```

La primera materialización se guarda en `data/processed/taxis.duckdb`. Para repetir solo las mediciones **si los Parquet no han cambiado**, use `docker exec lab8-lab python scripts/benchmark.py --repetitions 4 --reuse-table`. Si entra un nuevo mes, vuelva a descargar y ejecutar el flujo completo, **sin** `--reuse-table`; la tabla anterior no incluiría las nuevas filas. `verify_data.py` genera además inventario, resumen y comparación de esquemas en `data/processed/`.

## Crear el tablero de Metabase

Metabase conserva su estado en un volumen local de Docker; el tablero también puede reconstruirse con código versionado. Después de `run_analysis.py`, use el mismo contenedor de análisis:

```powershell
docker exec -e LAB8_METABASE_URL=http://metabase:3000 lab8-lab python scripts/setup_metabase.py
docker exec -e LAB8_METABASE_URL=http://metabase:3000 lab8-lab python scripts/create_metabase_dashboard.py
```

Abra la URL del tablero que imprime el segundo comando. En una instalación nueva, `setup_metabase.py` crea una cuenta **solo local** y guarda sus credenciales en `data/processed/metabase_credentials.json`, carpeta excluida de Git. Si Metabase ya estaba configurado, proporcione `LAB8_MB_EMAIL` y `LAB8_MB_PASSWORD` como variables de entorno para esa instancia. Las siete tarjetas consultan los CSV agregados mediante el controlador DuckDB de Metabase; no exponen ni importan los 121 millones de viajes. La configuración del controlador está fijada en `metabase.Dockerfile`.

## Estructura y trazabilidad

| Ruta | Propósito |
|---|---|
| `scripts/download_data.py`, `scripts/verify_data.py` | Descarga incremental e inventario de integridad. |
| `scripts/lab8_common.py`, `scripts/run_analysis.py` | Vista temporal sobre Parquet y ejecución de SQL. |
| `sql/01_*.sql` a `sql/12_*.sql` | Preguntas y filtros reproducibles. |
| `scripts/benchmark.py`, `docs/benchmark_*.csv` | Comparación Parquet frente a tabla DuckDB y tiempos medidos. |
| `scripts/build_dashboard.py`, `scripts/create_metabase_dashboard.py` | Indicadores SVG/HTML y tablero Metabase. |
| `notebooks/lab8_analisis.ipynb` | Exploración, visualizaciones y conclusiones ejecutadas. |
| `docs/consultas.md`, `docs/metodologia.md` | Catálogo, hallazgos, límites y respuestas de discusión. |
| `docs/auditoria_rubrica.md` | Mapa de cada ejercicio del enunciado a su evidencia. |
| `data/raw/`, `data/processed/` | Datos originales y derivados locales, ignorados por Git. |

La vista `trips` usa `read_parquet(..., union_by_name=true, filename=true)` para combinar esquemas y derivar servicio, año y mes del archivo. Los análisis principales consultan Parquet **sin importar previamente los viajes a DuckDB**; solo el benchmark crea una tabla materializada. El corte 2026 es parcial: las comparaciones entre años emplean enero–agosto de cada año, sin atribuir causalidad a las diferencias.

**Fuente primaria:** [NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page). Las definiciones de columnas y códigos de pago deben comprobarse contra los [diccionarios oficiales](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page). Consulte [docs/metodologia.md](docs/metodologia.md) para las limitaciones y referencias adicionales.
