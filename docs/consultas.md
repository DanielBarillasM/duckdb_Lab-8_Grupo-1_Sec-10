# Catálogo y decisiones de las consultas

Fuente de todas las consultas: archivos oficiales `data/raw/{yellow,green}/{2024,2025,2026}/*.parquet`. La vista temporal `trips`, definida en `scripts/lab8_common.py`, los lee directamente con `read_parquet(..., union_by_name=true, filename=true)` y normaliza nombres de columnas, año, mes y tipo de taxi. No importa los Parquet a una tabla para los ejercicios 3 al 5 y 7 al 8. Los resultados completos se regeneran en `data/processed/results/` con `scripts/run_analysis.py`.

| SQL | Objetivo | Resultado obtenido | Decisión para el análisis |
|---|---|---|---|
| `01_cobertura.sql` | Contar archivos y filas por mes y servicio. | 64 archivos y 121,184,384 filas: 24 de 2024, 24 de 2025 y 16 de 2026. | Separar cobertura de 2026 de años completos. |
| `02_calidad.sql` | Auditar tiempos, distancias, importes y nulos. | 2026 amarillo contiene 7,716,688 pasajeros nulos y 952,231 distancias cero; hay 157 recogidas fuera del año de su archivo en todo el conjunto. | Excluir recogidas fuera de año en indicadores; no usar pasajeros como indicador principal. Mantener auditoría sin borrar datos. |
| `03_viajes_mensuales.sql` | Medir volumen e importe por mes y tipo. | 64 filas tipo-mes; en 2026 enero-agosto: 29,703,338 viajes amarillos y 337,100 verdes tras filtrar año de recogida. | Usar meses publicados y evitar extrapolaciones. |
| `04_distancias.sql` | Describir distancias y extremos. | En 2026, mediana de 1.92 millas en amarillo y 2.14 en verde; las medias son mucho mayores (5.74 y 13.85). | Priorizar medianas y reportar extremos por separado. |
| `05_pagos.sql` | Comparar códigos de pago. | En 2026, tarjeta (código 1) representa 63.77% en amarillo y 65.25% en verde; el código 0 llega a 25.98% en amarillo. | Mostrar explícitamente pagos sin código claro; no interpretar el cambio de tarjeta como cambio de conducta sin revisar codificación. |
| `06_horas.sql` | Localizar horas de demanda. | En 2026 el pico amarillo es 18:00 y el verde 17:00. | Usar porcentajes dentro de cada tipo para comparar perfiles horarios con escalas distintas. |
| `07_propinas.sql` | Medir propinas en pagos con tarjeta. | En 2026 la propina registrada sobre tarifa es 21.53% en amarillo y 20.93% en verde. | Excluir efectivo, tarifas no positivas y propinas negativas. |
| `08_dias_semana.sql` | Describir demanda semanal. | El jueves (código 4 de DuckDB) es el día con mayor volumen en 2026 para ambos tipos. | Usar los códigos de día documentados: 0 domingo a 6 sábado. |
| `09_zonas_origen.sql` | Detectar concentración por zona de recogida. | En 2026 lideran los códigos TLC 237 (amarillo) y 74 (verde). | Presentar códigos, sin inventar nombres de zonas no incluidos en los Parquet. |
| `10_duracion.sql` | Medir duración y anomalías. | Mediana 2026: 14 minutos en amarillo y 13 en verde; existen duraciones negativas. | Excluir duraciones negativas al calcular medias y medianas. |
| `11_importes.sql` | Describir la distribución de cobros. | Mediana 2026: USD 23.69 amarillo y USD 20.50 verde; existen importes superiores a USD 500. | Mantener percentiles y umbrales exploratorios sin tratar todo extremo como error. |
| `12_comparacion_ene_ago.sql` | Comparar los tres años en una ventana común. | Amarillo: 26.39 M (2024), 31.56 M (2025), 29.70 M (2026). Verde: 443 mil, 398 mil y 337 mil. | Comparar enero-agosto de cada año, porque 2026 no está completo. |

Cada archivo SQL contiene la sentencia exacta y comentarios sobre su pregunta, fuentes y filtros. La tabla anterior registra el resultado y la decisión. Medianas y percentiles se calculan con `quantile_cont` (exacto), no con `approx_quantile`, porque la aproximación variaba en la segunda decimal entre ejecuciones paralelas. Los filtros de calidad son específicos de cada pregunta: la auditoría incluye todos los registros, mientras las métricas de viajes suelen exigir `year(pickup_datetime)=file_year`.

## Hallazgos principales

1. En enero-agosto, el volumen amarillo de 2026 supera al de 2024 en aproximadamente 12.6%, mientras el verde baja alrededor de 24.0%. La comparación usa la misma ventana temporal; no atribuye causas.
2. La media de distancia está fuertemente influida por valores extremos, especialmente en Green Taxi: 13.85 millas de media frente a 2.14 de mediana en 2026. La mediana describe mejor el viaje típico.
3. La fracción de pagos codificados como tarjeta en Yellow Taxi pasa de 74.05% (enero-agosto 2024) a 63.77% (2026), mientras crece la presencia del código 0 y de pasajeros nulos. Esto puede reflejar cambios de registro, no necesariamente una transición real de medios de pago.

Los importes están en USD nominales. No se ajustaron por inflación, cambios tarifarios, composición de rutas ni estacionalidad más allá de la ventana común; por tanto, estas diferencias son descriptivas.

## Apéndice: sentencias SQL

Copia textual de `sql/*.sql` para que cada consulta quede documentada junto a su objetivo y resultado. La fuente de verdad es la carpeta `sql/`; todas leen la vista `trips` (Parquet directo en `data/raw/{yellow,green}/<año>/`).

### `01_cobertura.sql`

```sql
-- Pregunta: ¿Cuántos archivos y viajes hay por tipo, año y mes?
-- Fuente: vista trips sobre los Parquet originales; sin tabla importada.
SELECT file_year AS anio, file_month AS mes, taxi_type AS tipo,
       count(DISTINCT source_file) AS archivos, count(*) AS viajes,
       min(pickup_datetime) AS primera_recogida,
       max(pickup_datetime) AS ultima_recogida
FROM trips
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
```

### `02_calidad.sql`

```sql
-- Pregunta: ¿Qué problemas de calidad podrían sesgar el análisis?
-- Fuente: todos los Parquet; no se descartan registros en esta auditoría.
SELECT file_year AS anio, taxi_type AS tipo, count(*) AS viajes,
       count(*) FILTER (WHERE pickup_datetime IS NULL) AS sin_recogida,
       count(*) FILTER (WHERE pickup_datetime IS NOT NULL
                        AND year(pickup_datetime) <> file_year) AS fuera_de_anio,
       count(*) FILTER (WHERE dropoff_datetime < pickup_datetime) AS duracion_negativa,
       count(*) FILTER (WHERE trip_distance IS NULL) AS distancia_nula,
       count(*) FILTER (WHERE trip_distance < 0) AS distancia_negativa,
       count(*) FILTER (WHERE trip_distance = 0) AS distancia_cero,
       count(*) FILTER (WHERE total_amount < 0) AS importe_negativo,
       count(*) FILTER (WHERE total_amount IS NULL) AS importe_nulo,
       count(*) FILTER (WHERE passenger_count IS NULL) AS pasajeros_nulos
FROM trips
GROUP BY 1, 2
ORDER BY 1, 2;
```

### `03_viajes_mensuales.sql`

```sql
-- Pregunta: ¿Cómo cambia el volumen mensual de viajes entre tipos y años?
-- Se usa el mes del archivo para medir cobertura y el año de recogida para
-- excluir registros desfasados que la TLC incluye en algunos archivos.
SELECT file_year AS anio, file_month AS mes, taxi_type AS tipo,
       count(*) AS viajes,
       round(avg(total_amount) FILTER (WHERE total_amount >= 0), 2) AS importe_medio_usd,
       round(sum(total_amount) FILTER (WHERE total_amount >= 0), 2) AS importe_total_usd
FROM trips
WHERE year(pickup_datetime) = file_year
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
```

### `04_distancias.sql`

```sql
-- Pregunta: ¿En qué difieren las distancias y qué valores extremos aparecen?
-- Para cuantiles se consideran distancias positivas; >100 millas se reporta
-- como umbral exploratorio y no implica automáticamente un error.
-- Cuantiles exactos (quantile_cont): approx_quantile varía entre ejecuciones
-- paralelas. La forma de lista comparte un solo estado y limita la memoria.
WITH agregados AS (
    SELECT file_year AS anio, taxi_type AS tipo,
           count(*) AS viajes_distancia_positiva,
           avg(trip_distance) AS media,
           quantile_cont(trip_distance, [0.50, 0.90, 0.99]) AS q,
           count(*) FILTER (WHERE trip_distance > 100) AS mas_100_millas
    FROM trips
    WHERE year(pickup_datetime) = file_year AND trip_distance > 0
    GROUP BY 1, 2
)
SELECT anio, tipo, viajes_distancia_positiva,
       round(media, 2) AS media_millas,
       round(q[1], 2) AS p50_millas,
       round(q[2], 2) AS p90_millas,
       round(q[3], 2) AS p99_millas,
       mas_100_millas
FROM agregados
ORDER BY 1, 2;
```

### `05_pagos.sql`

```sql
-- Pregunta: ¿Qué proporción de viajes usa cada método de pago?
-- payment_type=1 se interpreta como tarjeta según el diccionario TLC.
SELECT file_year AS anio, taxi_type AS tipo, payment_type,
       count(*) AS viajes,
       round(100.0 * count(*) / sum(count(*)) OVER (PARTITION BY file_year, taxi_type), 2)
           AS porcentaje
FROM trips
WHERE year(pickup_datetime) = file_year
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
```

### `06_horas.sql`

```sql
-- Pregunta: ¿En qué horas se concentra la demanda por tipo de taxi?
SELECT file_year AS anio, taxi_type AS tipo,
       hour(pickup_datetime) AS hora, count(*) AS viajes
FROM trips
WHERE year(pickup_datetime) = file_year
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
```

### `07_propinas.sql`

```sql
-- Pregunta: ¿Cómo varían las propinas registradas en pagos con tarjeta?
-- El efectivo no registra necesariamente la propina, por eso se excluye.
SELECT file_year AS anio, taxi_type AS tipo,
       count(*) AS viajes_tarjeta,
       round(avg(tip_amount), 2) AS propina_media_usd,
       round(100.0 * sum(tip_amount) / nullif(sum(fare_amount), 0), 2)
           AS propina_sobre_tarifa_pct
FROM trips
WHERE year(pickup_datetime) = file_year
  AND payment_type = 1 AND fare_amount > 0 AND tip_amount >= 0
GROUP BY 1, 2
ORDER BY 1, 2;
```

### `08_dias_semana.sql`

```sql
-- Pregunta: ¿Qué días concentran más viajes? DuckDB: 0=domingo, 6=sábado.
SELECT file_year AS anio, taxi_type AS tipo,
       dayofweek(pickup_datetime) AS dia_semana, count(*) AS viajes
FROM trips
WHERE year(pickup_datetime) = file_year
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
```

### `09_zonas_origen.sql`

```sql
-- Pregunta: ¿Qué códigos de zona de origen concentran la demanda?
-- Se muestran IDs TLC; su nombre requiere el catálogo externo de zonas.
SELECT file_year AS anio, taxi_type AS tipo, pickup_zone_id,
       count(*) AS viajes
FROM trips
WHERE year(pickup_datetime) = file_year AND pickup_zone_id IS NOT NULL
GROUP BY 1, 2, 3
QUALIFY row_number() OVER (PARTITION BY file_year, taxi_type ORDER BY count(*) DESC) <= 10
ORDER BY 1, 2, viajes DESC;
```

### `10_duracion.sql`

```sql
-- Pregunta: ¿Cuánto duran los viajes y cuántos exceden tres horas?
-- Mediana exacta (quantile_cont), reproducible entre ejecuciones.
WITH base AS (
    SELECT file_year AS anio, taxi_type AS tipo,
           date_diff('minute', pickup_datetime, dropoff_datetime) AS minutos
    FROM trips
    WHERE year(pickup_datetime) = file_year
      AND pickup_datetime IS NOT NULL AND dropoff_datetime IS NOT NULL
)
SELECT anio, tipo, count(*) AS viajes_con_hora,
       count(*) FILTER (WHERE minutos < 0) AS duracion_negativa,
       round(avg(minutos) FILTER (WHERE minutos >= 0), 1) AS media_minutos,
       round(quantile_cont(minutos, 0.50) FILTER (WHERE minutos >= 0), 1) AS p50_minutos,
       count(*) FILTER (WHERE minutos > 180) AS mas_tres_horas
FROM base
GROUP BY 1, 2
ORDER BY 1, 2;
```

### `11_importes.sql`

```sql
-- Pregunta: ¿Cuál es la distribución de importes y dónde aparecen extremos?
-- Cuantiles exactos (quantile_cont), reproducibles entre ejecuciones.
WITH agregados AS (
    SELECT file_year AS anio, taxi_type AS tipo,
           count(*) AS viajes_importe_no_negativo,
           avg(total_amount) AS media,
           quantile_cont(total_amount, [0.50, 0.90, 0.99]) AS q,
           count(*) FILTER (WHERE total_amount > 500) AS mas_500_usd
    FROM trips
    WHERE year(pickup_datetime) = file_year AND total_amount >= 0
    GROUP BY 1, 2
)
SELECT anio, tipo, viajes_importe_no_negativo,
       round(media, 2) AS media_usd,
       round(q[1], 2) AS p50_usd,
       round(q[2], 2) AS p90_usd,
       round(q[3], 2) AS p99_usd,
       mas_500_usd
FROM agregados
ORDER BY 1, 2;
```

### `12_comparacion_ene_ago.sql`

```sql
-- Pregunta: ¿Cómo evolucionan indicadores comparables en enero-agosto?
-- 2026 solo tiene ocho meses publicados al 01-10-2026, así que se usa la
-- misma ventana de 2024 y 2025 para evitar comparar 8 contra 12 meses.
-- La mediana es exacta (quantile_cont) para que el resultado sea reproducible.
SELECT file_year AS anio, taxi_type AS tipo,
       count(*) AS viajes,
       round(avg(total_amount) FILTER (WHERE total_amount >= 0), 2) AS importe_medio_usd,
       round(quantile_cont(trip_distance, 0.50)
             FILTER (WHERE trip_distance > 0), 2) AS distancia_p50_millas,
       round(100.0 * count(*) FILTER (WHERE payment_type = 1) / count(*), 2)
             AS tarjeta_pct,
       round(100.0 * sum(tip_amount) FILTER
             (WHERE payment_type = 1 AND fare_amount > 0 AND tip_amount >= 0)
             / nullif(sum(fare_amount) FILTER
             (WHERE payment_type = 1 AND fare_amount > 0 AND tip_amount >= 0), 0), 2)
             AS propina_sobre_tarifa_pct
FROM trips
WHERE file_month BETWEEN 1 AND 8 AND year(pickup_datetime) = file_year
GROUP BY 1, 2
ORDER BY 1, 2;
```
