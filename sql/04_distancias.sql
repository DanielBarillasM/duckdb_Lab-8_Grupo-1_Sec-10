-- Pregunta: ¿En qué difieren las distancias y qué valores extremos aparecen?
-- Para cuantiles se consideran distancias positivas; >100 millas se reporta
-- como umbral exploratorio y no implica automáticamente un error.
SELECT file_year AS anio, taxi_type AS tipo,
       count(*) AS viajes_distancia_positiva,
       round(avg(trip_distance), 2) AS media_millas,
       round(approx_quantile(trip_distance, 0.50), 2) AS p50_millas,
       round(approx_quantile(trip_distance, 0.90), 2) AS p90_millas,
       round(approx_quantile(trip_distance, 0.99), 2) AS p99_millas,
       count(*) FILTER (WHERE trip_distance > 100) AS mas_100_millas
FROM trips
WHERE year(pickup_datetime) = file_year AND trip_distance > 0
GROUP BY 1, 2
ORDER BY 1, 2;
