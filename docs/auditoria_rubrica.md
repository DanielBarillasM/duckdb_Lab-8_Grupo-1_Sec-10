# Auditoría de cumplimiento de la rúbrica

Esta matriz relaciona cada ejercicio del enunciado con evidencia concreta y reproducible del repositorio. El corte analítico corresponde al 1 de octubre de 2026: 64 archivos Parquet oficiales y 121,184,384 registros. La verificación en línea del 5 de octubre confirmó que no había archivos publicados adicionales.

## Resumen

| Bloque evaluado | Estado | Evidencia principal |
|---|---|---|
| Fase 1: ambiente y descarga | Cumple | `docker-compose.yml`, `scripts/download_data.py`, `scripts/verify_data.py`, `README.md` |
| Consultas directas y exploración | Cumple | `scripts/lab8_common.py`, `sql/01_*.sql` a `sql/12_*.sql`, notebook |
| Análisis exploratorio | Cumple | `docs/consultas.md`, `docs/metodologia.md`, notebook |
| Incorporación incremental | Cumple | Descarga parametrizada para 2024, 2025 y 2026; verificador de integridad |
| Benchmark | Cumple | `scripts/benchmark.py`, `docs/benchmark_consultas.md`, CSV de resultados |
| Indicadores y visualización | Cumple | Siete indicadores, tablero Metabase, HTML y SVG |
| Análisis completo y discusión | Cumple | Comparación enero-agosto y respuestas 9.1-9.8 |
| Reproducibilidad y versionado | Cumple | Docker, dependencias fijadas, README e historial Git; datos excluidos |

## Ejercicio 1 - Preparación del ambiente

- El fork del equipo es <https://github.com/DanielBarillasM/duckdb_Lab-8_Grupo-1_Sec-10>.
- `docker-compose.yml` levanta JupyterLab y Metabase en interfaces locales.
- `Dockerfile`, `metabase.Dockerfile` y `requirements.txt` fijan el entorno y sus versiones.
- El procedimiento completo de construcción, arranque y acceso está documentado en `README.md`.
- `docs/estructura.md` explica la función de cada directorio.

## Ejercicio 2 - Sistema de descarga

- `scripts/download_data.py` descarga Yellow y Green Taxi, con 2026 como valor inicial.
- `--years` permite incorporar 2024 y 2025 sin reemplazar archivos anteriores.
- La ruta es `data/raw/<tipo>/<año>/archivo.parquet`.
- Un archivo existente y no vacío se omite; la descarga usa un archivo temporal `.part` antes de renombrarlo.
- `scripts/verify_data.py --online` valida cabeceras Parquet, filas, grupos, esquema, tamaño remoto y cobertura publicada.

## Ejercicio 3 - Consulta directa de Parquet

- `scripts/lab8_common.py` crea la vista temporal `trips` con `read_parquet`, `union_by_name=true` y `filename=true`.
- `sql/01_cobertura.sql` obtiene archivos, registros y cobertura temporal.
- El notebook muestra `DESCRIBE` y muestras originales de Yellow y Green Taxi.
- `sql/02_calidad.sql` audita nulos, fechas fuera de año, duraciones negativas, distancias no plausibles e importes negativos.
- Las sentencias, objetivos, fuentes, resultados y decisiones están documentados en `docs/consultas.md`.

## Ejercicio 4 - Análisis exploratorio

- Se plantean doce preguntas reproducibles en `sql/01_*.sql` a `sql/12_*.sql`.
- El análisis cubre tiempo, distancia, pagos, propinas, horarios, días, zonas, duración, importes y valores extremos.
- `docs/consultas.md` presenta al menos tres hallazgos y separa descripción de causalidad.
- Yellow y Green Taxi se comparan con filtros equivalentes y unidades explícitas.

## Ejercicio 5 - Incorporación de 2024

- La descarga admite `--years 2024` y conserva los Parquet existentes de 2026.
- La vista descubre archivos por año y permite consultar 2024 y 2026 conjuntamente.
- `sql/01_cobertura.sql`, `03_viajes_mensuales.sql` y `12_comparacion_ene_ago.sql` verifican la incorporación.
- `union_by_name` y la normalización de fechas evitan reescribir el flujo por diferencias de esquema.

## Ejercicio 6 - Parquet frente a DuckDB

- `scripts/benchmark.py` crea `trips_materialized` con las seis columnas utilizadas.
- Ejecuta tres consultas equivalentes sobre la vista Parquet y la tabla, y comprueba igualdad de resultados antes de cronometrar.
- Evalúa 16, 40 y 64 archivos, con cuatro repeticiones y orden alternado.
- `docs/benchmark_resultados.csv` resume medianas, mínimos y máximos; `docs/benchmark_detalle.csv` conserva las 72 mediciones.
- `docs/benchmark_consultas.md` contiene las sentencias exactas y `docs/metodologia.md` interpreta los resultados y costos de materialización.

## Ejercicio 7 - Indicadores y visualización

- Las doce preguntas documentadas superan el mínimo de diez.
- Se construyen siete indicadores respaldados por SQL: viajes mensuales, volumen comparable, importe medio, distancia mediana, pagos con tarjeta, propina sobre tarifa y perfil horario.
- `scripts/create_metabase_dashboard.py` reproduce siete tarjetas y el tablero Metabase.
- `scripts/build_dashboard.py` produce una alternativa estática en `docs/tablero.html` y siete SVG.
- `docs/evidencia_metabase.png` demuestra el tablero integrado y `docs/metodologia.md` justifica e interpreta cada indicador.

## Ejercicio 8 - Incorporación de 2025

- El mismo descargador admite `--years 2025` y evita repetir 2024 y 2026.
- Las doce consultas funcionan sobre los tres años.
- `sql/12_comparacion_ene_ago.sql` utiliza la ventana común enero-agosto, porque 2026 es parcial.
- La metodología presenta tres patrones interanuales respaldados por los resultados.

## Ejercicio 9 - Discusión

`docs/metodologia.md`, sección 5, responde explícitamente los incisos 9.1 a 9.8: utilidad de DuckDB, ventajas y límites de Parquet, materialización, comparación con Pandas, incrementalidad, automatización, reproducibilidad y aprendizajes a escala.

## Material de entrega

El fork contiene el código modificado, descargador, verificador, doce consultas SQL, notebook ejecutado, documentación, benchmark, código de visualización, tablero y evidencia, README y ficha de presentación. `data/raw/` y `data/processed/` están excluidos por `.gitignore`; únicamente sus archivos `.gitkeep` se versionan.

La comprobación operativa final está descrita en [checklist_verificacion.md](checklist_verificacion.md).
