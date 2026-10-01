-- Pregunta: ¿Qué días concentran más viajes? DuckDB: 0=domingo, 6=sábado.
SELECT file_year AS anio, taxi_type AS tipo,
       dayofweek(pickup_datetime) AS dia_semana, count(*) AS viajes
FROM trips
WHERE year(pickup_datetime) = file_year
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
