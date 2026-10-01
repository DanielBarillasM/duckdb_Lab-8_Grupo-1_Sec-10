-- Pregunta: ¿Cuál es la distribución de importes y dónde aparecen extremos?
SELECT file_year AS anio, taxi_type AS tipo,
       count(*) AS viajes_importe_no_negativo,
       round(avg(total_amount), 2) AS media_usd,
       round(approx_quantile(total_amount, 0.50), 2) AS p50_usd,
       round(approx_quantile(total_amount, 0.90), 2) AS p90_usd,
       round(approx_quantile(total_amount, 0.99), 2) AS p99_usd,
       count(*) FILTER (WHERE total_amount > 500) AS mas_500_usd
FROM trips
WHERE year(pickup_datetime) = file_year AND total_amount >= 0
GROUP BY 1, 2
ORDER BY 1, 2;
