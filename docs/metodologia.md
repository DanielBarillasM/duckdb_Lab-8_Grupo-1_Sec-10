# Metodología, resultados y discusión

**Corte del análisis:** 1 de octubre de 2026. **Fuente:** archivos mensuales Yellow y Green Taxi de la [NYC TLC](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page). El conjunto local comprende 2024 y 2025 completos y enero–agosto de 2026. La TLC no había publicado septiembre–diciembre de 2026 al momento de la verificación; **ausencia de publicación no equivale a falla de descarga**. Todos los números de esta nota son descriptivos y se obtienen al volver a ejecutar los scripts; no son estimaciones poblacionales ni pruebas causales.

## 1. Preparación, estructura y descarga (ejercicios 1–2)

El proyecto usa `data/raw/` para los Parquet originales y `data/processed/` para inventario, CSV resumidos, base DuckDB y credenciales locales; ninguna de esas salidas entra a Git. `scripts/` contiene el flujo ejecutable, `sql/` las consultas, `notebooks/` la exploración narrada y `docs/` resultados y decisiones. Véase [estructura.md](estructura.md).

Docker Compose fija las dependencias de Python y del controlador DuckDB de Metabase, crea rutas montadas coherentes y permite repetir el mismo procedimiento sin depender de paquetes instalados en cada computadora. Se verificaron JupyterLab, Metabase y el driver de DuckDB. El trabajo se versiona en el fork del equipo ([DanielBarillasM/duckdb_Lab-8_Grupo-1_Sec-10](https://github.com/DanielBarillasM/duckdb_Lab-8_Grupo-1_Sec-10)), que es el `origin` del clon; nada se envía al repositorio docente.

El script docente descargaba inicialmente 2026. Se amplió con `--years` para 2024, 2025 y 2026, conservando el valor por defecto 2026; con `--taxi` para un servicio o ambos; estructura `data/raw/<tipo>/<año>/`; comprobación de existencia antes de descargar; distinción entre HTTP 403/404 de meses no publicados y fallos de red; reintentos; y escritura temporal `.part` antes del renombrado. Las incorporaciones se hicieron en secuencia 2026 → 2024 → 2025, sin borrar ni repetir archivos existentes. La verificación independiente `verify_data.py --online` inspecciona la cabecera Parquet, número de filas, grupos, columnas, tipos y tamaño publicado en el servidor. Resultado del corte: **64/64 archivos publicados presentes y válidos**, **121,184,384 filas**, cero históricos faltantes y cero publicados faltantes. La mera existencia local no sustituye esta auditoría: si un archivo está truncado debe retirarse únicamente ese archivo y volver a descargarlo.

## 2. Lectura directa, exploración y transformaciones (ejercicios 3–5)

La vista temporal `trips` en `scripts/lab8_common.py` utiliza `read_parquet` de DuckDB con lista explícita de archivos, `union_by_name=true` y `filename=true`. Deriva `taxi_type`, `file_year` y `file_month` del nombre/ruta del archivo, y unifica la fecha de recogida entre `tpep_pickup_datetime` y `lpep_pickup_datetime`. También proyecta una selección común de importes, distancia, pago, pasajeros y zonas. No altera los Parquet originales y no materializa los 121 millones de viajes para el análisis principal. La libreta muestra `DESCRIBE` y tres filas de cada tipo; `data/processed/esquemas.csv` registra las columnas y tipos de los 64 archivos.

`sql/01_cobertura.sql` cuenta archivos y registros por mes; `02_calidad.sql` audita fechas fuera del año del archivo, nulos y valores no plausibles. En los indicadores de viaje se exige `year(pickup_datetime)=file_year`: hay **157 recogidas fuera de año** entre los 121 millones de registros. Otras exclusiones dependen de la pregunta: distancia positiva para mediana, tarifa positiva y pago con tarjeta para proporción de propinas, duración positiva para duración típica. La auditoría conserva **todas** las filas para no esconder anomalías. Las medianas y percentiles usan `quantile_cont` (exacto): `approx_quantile` cambiaba la segunda decimal entre ejecuciones paralelas y rompía la reproducibilidad de las cifras. En 2026, Yellow registra **7,716,688** valores nulos en `passenger_count` y **952,231** distancias cero; por ello ninguna de esas variables se usa sin su contexto de calidad. Los códigos de pago deben leerse conforme a los [diccionarios de la TLC](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page); el código 0 no se interpreta automáticamente como efectivo.

Los detalles de las **12 preguntas** —objetivo, sentencia SQL, archivos de fuente, resultado y decisión— están en [consultas.md](consultas.md) y en `sql/01_*.sql` a `sql/12_*.sql`. Consultar Parquet directamente significa que DuckDB lee columnas, metadatos y grupos de filas del archivo en la consulta, sin una etapa obligatoria de carga a una tabla. Esto evita duplicación inicial y facilita incorporar meses; su costo puede reaparecer en agregaciones complejas repetidas.

La vista y las 12 consultas siguieron funcionando tras sumar 2024 y 2025; `union_by_name` absorbe columnas presentes solo en ciertos archivos y `coalesce` normaliza las fechas. Las consultas entre años filtran por año de archivo y, cuando corresponde, usan la ventana común enero–agosto para no comparar 2026 parcial contra años enteros. La comprobación de incorporación está reflejada en `01_cobertura.sql`, `03_viajes_mensuales.sql` y `12_comparacion_ene_ago.sql`.

## 3. Preguntas, indicadores y tablero (ejercicios 4, 7–8)

Las 12 preguntas analíticas de [consultas.md](consultas.md) superan el mínimo de 10. Siete indicadores se visualizan conjuntamente en **Metabase**; el código que crea las tarjetas y el tablero está en `scripts/create_metabase_dashboard.py`. Las tarjetas ejecutan SQL en el controlador DuckDB contra **CSV agregados producidos por consultas DuckDB**, evitando reconsultar 121 millones de viajes en cada apertura. `scripts/build_dashboard.py` genera adicionalmente figuras SVG y un HTML estático para revisar el resultado sin depender del estado local de Metabase. [Evidencia del tablero real](evidencia_metabase.png).

| Indicador / pregunta | SQL de origen | Justificación e interpretación |
|---|---|---|
| Viajes mensuales: ¿cómo evoluciona la demanda? | `03_viajes_mensuales.sql` | Revela cobertura y oscilación mensual; 2026 se detiene en agosto, no representa un año completo. |
| Volumen enero–agosto: ¿cambia por servicio y año? | `12_comparacion_ene_ago.sql` | Mismo periodo para tres años; Yellow 26.39 M → 31.56 M → 29.70 M y Green 443 mil → 398 mil → 337 mil. |
| Importe medio: ¿cómo cambia el cobro? | `12_comparacion_ene_ago.sql` | USD nominales, no ajustados; Yellow 28.37 → 27.49 → 30.40. No equivale a ingreso neto. |
| Distancia mediana: ¿cambia el viaje típico? | `12_comparacion_ene_ago.sql` | Resiste valores extremos; Green 1.96 → 2.02 → 2.14 millas. |
| Porcentaje de tarjeta: ¿cómo cambia el código de pago? | `12_comparacion_ene_ago.sql` | Yellow 74.05% → 63.81% → 63.77%; el crecimiento del código 0 impide inferir preferencias sin más datos. |
| Propina sobre tarifa: ¿cómo cambia la proporción registrada? | `12_comparacion_ene_ago.sql` | Solo tarjeta, tarifa positiva y propina no negativa; Yellow 21.99% → 22.19% → 21.53%. |
| Perfil horario: ¿cuándo se concentran los viajes? | `06_horas.sql` | Picos 2026: 18:00 Yellow y 17:00 Green. Los volúmenes absolutos difieren mucho; comparar forma, no solo altura. |

Tres patrones visibles con los tres años: (1) Yellow creció de 2024 a 2025 y descendió parcialmente en 2026, pero queda **12.6% por encima de 2024** en enero–agosto; (2) Green disminuye de forma continua y 2026 está **24.0% por debajo de 2024**; (3) la distancia mediana de Green aumenta levemente, mientras la fracción Yellow codificada como tarjeta cae entre 2024 y 2025 y se estabiliza en 2026. No se atribuyen causas de mercado ni cambios de conducta a estos patrones.

## 4. Benchmark Parquet frente a tabla DuckDB (ejercicio 6)

`scripts/benchmark.py` crea `trips_materialized` con **las seis columnas exactas** requeridas por las tres consultas representativas: conteo por año/tipo, importe medio mensual y distribución de pagos. La consulta sobre Parquet y la consulta sobre tabla usan la **misma proyección, filtros, agrupaciones y orden**; el programa compara las filas devueltas antes de medir y falla si no son equivalentes. Los escenarios tienen 16 archivos (2026), 40 (2024+2026) y 64 (2024+2025+2026). Cada par se calienta, se mide cuatro veces y alterna qué fuente corre primero; se reporta la mediana, más mínimo/máximo y mediciones individuales. En la reproducción del 4 de octubre de 2026 (Docker con 8 núcleos y 4 GB de RAM; DuckDB limitado a 4 hilos), la materialización inicial tardó **9.8 s** y creó una base de **0.83 GB**; las cifras de consulta no incluyen ese costo. Las sentencias SQL exactas y la definición de la tabla están en [benchmark_consultas.md](benchmark_consultas.md). Los [resultados completos](benchmark_resultados.csv) y [detalle por repetición](benchmark_detalle.csv) permiten comprobarlo.

| Escenario | Consulta | Parquet (s) | Tabla (s) | Lectura |
|---|---|---:|---:|---|
| 2026 | conteo | 0.045 | 0.058 | Parquet algo más rápido. |
| 2026 | importe mensual | 0.370 | 0.149 | Tabla ~2.5 veces más rápida. |
| 2026 | pagos | 0.316 | 0.098 | Tabla ~3.2 veces más rápida. |
| 2024+2026 | conteo | 0.113 | 0.221 | Parquet ~2 veces más rápido. |
| 2024+2026 | importe mensual | 1.442 | 0.557 | Tabla ~2.6 veces más rápida. |
| 2024+2026 | pagos | 0.923 | 0.434 | Tabla ~2.1 veces más rápida. |
| 2024+2025+2026 | conteo | 0.178 | 0.265 | Parquet ~1.5 veces más rápido. |
| 2024+2025+2026 | importe mensual | 2.076 | 0.788 | Tabla ~2.6 veces más rápida. |
| 2024+2025+2026 | pagos | 1.778 | 0.524 | Tabla ~3.4 veces más rápida. |

Al pasar de 16 a 64 archivos, el tiempo de las agregaciones crece aproximadamente con el volumen en ambas fuentes, y la tabla mantiene una ventaja de 2–3.4 veces. El conteo por año y tipo es la excepción en los tres tamaños: Parquet resulta más rápido. Una medición previa del equipo, en otra computadora, obtuvo tiempos 3–5 veces mayores (materialización de ~27 s), pero la misma conclusión para agregaciones; la diferencia confirma que los valores absolutos dependen del hardware.

Los tiempos son de **una computadora y un estado de caché**, no una propiedad universal de los formatos. Parquet es apropiado para consultas ad hoc, crecimiento mensual y cuando se quiere evitar materializar; las tablas convienen para agregaciones repetidas sobre un conjunto relativamente estable, aceptando costo de carga, almacenamiento y reconstrucción. El conteo solo necesita el nombre de archivo y los recuentos de filas, que Parquet guarda en sus metadatos; eso ayuda a explicar que ahí no gane la tabla. La comparación de este laboratorio no evalúa concurrencia, compresión, particionado optimizado ni servidores distribuidos.

## 5. Respuestas de discusión (ejercicio 9)

**9.1. DuckDB útil.** SQL sobre archivos, lectura selectiva de Parquet, `union_by_name`, agregaciones y tablas locales permitieron una misma interfaz para exploración y benchmark, sin servidor SQL tradicional.

**9.2. Parquet directo.** Evita carga inicial y duplicación, acepta nuevos archivos con cambiar la lista de entrada y permite selección de columnas. En consultas repetidas o que cruzan muchas filas se vuelve a pagar parte de la lectura; hay que vigilar diferencias de esquema y archivos ausentes.

**9.3. Tabla materializada.** Aceleró agregaciones repetidas y ofrece un esquema ya normalizado, pero consumió ~0.83 GB, tardó ~10 s en construirse en esta máquina y debe reconstruirse al añadir meses. Un archivo DuckDB con escritura concurrente también requiere coordinación.

**9.4. Frente a cargar todo en Pandas.** DuckDB procesa y agrega en el motor SQL; Pandas recibe solo tablas pequeñas para presentación. Esto reduce la necesidad de mantener los 121 millones de viajes como objetos DataFrame en RAM. No significa que DuckDB carezca de límites de memoria o disco.

**9.5. Incorporación de datos.** Descarga idempotente por archivo, directorios por tipo/año, descubrimiento automático de Parquet y vista normalizada permiten añadir años sin reescribir todas las consultas. La tabla del benchmark sí exige actualización explícita.

**9.6. Automatización de producción.** Programaría la búsqueda de nuevos archivos, verificación de integridad/esquema, ejecución de SQL, pruebas de coherencia, actualización de indicadores y alertas ante fallos. Añadiría registros de ejecución y retención controlada.

**9.7. Reproducibilidad.** Docker y dependencias fijadas, fuente y rutas claras, SQL separado, filtros documentados, benchmark con parámetros/versionado y datos fuera de Git. El fork y un historial de commits descriptivos deben cerrar la trazabilidad de entrega.

**9.8. Aprendizaje a escala.** Una cantidad pequeña de registros habría ocultado discrepancias de esquema, millones de nulos, códigos de pago ambiguos, valores extremos y el efecto del tamaño/caché sobre el rendimiento. Validar calidad y cobertura antes de interpretar porcentajes resultó indispensable.

## Referencias y límites

- [NYC TLC, Trip Record Data y diccionarios de datos](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page).
- [DuckDB, lectura de archivos Parquet](https://duckdb.org/docs/stable/data/parquet/overview).
- [Metabase, API para tarjetas y tableros](https://www.metabase.com/docs/latest/api).
- Kassis, T., Agarwal, V., He, Y., Patel, D., y Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. [arXiv:2609.00065](https://doi.org/10.48550/arXiv.2609.00065). Apoyo metodológico para la presentación reproducible de figuras.

Las diferencias anuales pueden reflejar inflación, tarifas, cobertura, cambios de codificación, composición de rutas y otros factores no modelados. Los importes son nominales. Los resultados de 2026 son una **instantánea parcial**: para otro corte, reejecute descarga, verificación, análisis, benchmark, tablero y libreta; no reutilice números de esta nota sin actualizarlos.
