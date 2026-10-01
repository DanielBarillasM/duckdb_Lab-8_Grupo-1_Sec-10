-- Pregunta: ¿En qué horas se concentra la demanda por tipo de taxi?
SELECT file_year AS anio, taxi_type AS tipo,
       hour(pickup_datetime) AS hora, count(*) AS viajes
FROM trips
WHERE year(pickup_datetime) = file_year
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
