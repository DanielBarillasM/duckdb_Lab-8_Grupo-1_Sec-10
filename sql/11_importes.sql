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
