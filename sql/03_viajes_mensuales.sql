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
