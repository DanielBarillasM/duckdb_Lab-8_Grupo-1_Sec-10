# Consultas del benchmark (ejercicio 6.8)

Estas tres consultas viven en `QUERIES` de `scripts/benchmark.py`. Cada una se ejecuta con **la misma sentencia** cambiando solo `{source}`: `trips` (vista sobre Parquet) o `trips_materialized` (tabla DuckDB). `{years}` toma los años del escenario. Antes de medir, el script compara las filas devueltas por ambas fuentes y falla si no son equivalentes.

## Tabla materializada

```sql
CREATE OR REPLACE TABLE trips_materialized AS
SELECT taxi_type, file_year, file_month, pickup_datetime,
       total_amount, payment_type FROM trips;
```

Contiene solo las seis columnas que usan las tres consultas. Se guarda en `data/processed/taxis.duckdb` (no versionado).

## Escenarios

| Escenario | Años | Archivos |
|---|---|---:|
| `2026` | 2026 | 16 |
| `2024+2026` | 2024, 2026 | 40 |
| `2024+2025+2026` | 2024, 2025, 2026 | 64 |

Cada par fuente/consulta se calienta una vez, se mide `--repetitions` veces (por defecto 4) alternando qué fuente corre primero, y se reporta mediana, mínimo y máximo en `docs/benchmark_resultados.csv`; las mediciones individuales están en `docs/benchmark_detalle.csv`.

## `conteo_tipo`

**Pregunta:** ¿Cuántos viajes hay por año y tipo de taxi?  
**Nota:** Casi solo requiere nombre de archivo y conteos de filas, que Parquet guarda en sus metadatos.

```sql
SELECT file_year, taxi_type, count(*) AS viajes
FROM {source} WHERE file_year IN ({years})
GROUP BY 1, 2 ORDER BY 1, 2
    
```

## `importe_mensual`

**Pregunta:** ¿Cuál es el importe medio por mes y tipo, y cuántos viajes lo respaldan?  
**Nota:** Lee `total_amount` y la fecha de recogida; filtra recogidas fuera del año del archivo y excluye importes negativos del promedio.

```sql
SELECT file_year, file_month, taxi_type,
       count(*) AS viajes,
       round(avg(total_amount) FILTER (WHERE total_amount >= 0), 2) AS media_usd
FROM {source}
WHERE file_year IN ({years}) AND year(pickup_datetime) = file_year
GROUP BY 1, 2, 3 ORDER BY 1, 2, 3
    
```

## `pagos`

**Pregunta:** ¿Cómo se distribuyen los códigos de pago por año y tipo?  
**Nota:** Lee `payment_type`; agrupa por código sin interpretarlo.

```sql
SELECT file_year, taxi_type, payment_type, count(*) AS viajes
FROM {source}
WHERE file_year IN ({years}) AND year(pickup_datetime) = file_year
GROUP BY 1, 2, 3 ORDER BY 1, 2, 3
    
```

Los tiempos y su interpretación están en [metodologia.md](metodologia.md), sección 4.
