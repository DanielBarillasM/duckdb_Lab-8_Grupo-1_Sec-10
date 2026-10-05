-- Pregunta: ¿Cómo evolucionan indicadores comparables en enero-agosto?
-- 2026 solo tiene ocho meses publicados al 01-10-2026, así que se usa la
-- misma ventana de 2024 y 2025 para evitar comparar 8 contra 12 meses.
-- La mediana es exacta (quantile_cont) para que el resultado sea reproducible.
SELECT file_year AS anio, taxi_type AS tipo,
       count(*) AS viajes,
       round(avg(total_amount) FILTER (WHERE total_amount >= 0), 2) AS importe_medio_usd,
       round(quantile_cont(trip_distance, 0.50)
             FILTER (WHERE trip_distance > 0), 2) AS distancia_p50_millas,
       round(100.0 * count(*) FILTER (WHERE payment_type = 1) / count(*), 2)
             AS tarjeta_pct,
       round(100.0 * sum(tip_amount) FILTER
             (WHERE payment_type = 1 AND fare_amount > 0 AND tip_amount >= 0)
             / nullif(sum(fare_amount) FILTER
             (WHERE payment_type = 1 AND fare_amount > 0 AND tip_amount >= 0), 0), 2)
             AS propina_sobre_tarifa_pct
FROM trips
WHERE file_month BETWEEN 1 AND 8 AND year(pickup_datetime) = file_year
GROUP BY 1, 2
ORDER BY 1, 2;
