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
