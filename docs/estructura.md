# Estructura del proyecto

- `data/raw/`: archivos Parquet originales de la TLC, organizados por tipo de taxi y año. No se versionan.
- `data/processed/`: base DuckDB, tablas derivadas y resultados generados. No se versionan.
- `notebooks/`: análisis ejecutable y narrativo para revisar preguntas, resultados e interpretaciones.
- `scripts/`: descarga, validación, análisis, benchmarks y generación del tablero.
- `sql/`: consultas SQL reproducibles, separadas del código que las ejecuta.
- `docs/`: decisiones metodológicas, catálogo de consultas y evidencia del tablero.

Docker fija las versiones de las bibliotecas y monta las carpetas del proyecto en los contenedores. Esto permite ejecutar el mismo flujo en otro equipo y evita que una instalación local cambie los resultados por diferencias de dependencias.
