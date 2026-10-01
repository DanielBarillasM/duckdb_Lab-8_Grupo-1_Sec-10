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
