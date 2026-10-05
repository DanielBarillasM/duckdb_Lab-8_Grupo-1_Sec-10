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
