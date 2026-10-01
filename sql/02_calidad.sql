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
