-- Pregunta: ¿Cuánto duran los viajes y cuántos exceden tres horas?
-- Mediana exacta (quantile_cont), reproducible entre ejecuciones.
WITH base AS (
    SELECT file_year AS anio, taxi_type AS tipo,
           date_diff('minute', pickup_datetime, dropoff_datetime) AS minutos
    FROM trips
    WHERE year(pickup_datetime) = file_year
      AND pickup_datetime IS NOT NULL AND dropoff_datetime IS NOT NULL
)
SELECT anio, tipo, count(*) AS viajes_con_hora,
       count(*) FILTER (WHERE minutos < 0) AS duracion_negativa,
       round(avg(minutos) FILTER (WHERE minutos >= 0), 1) AS media_minutos,
       round(quantile_cont(minutos, 0.50) FILTER (WHERE minutos >= 0), 1) AS p50_minutos,
       count(*) FILTER (WHERE minutos > 180) AS mas_tres_horas
FROM base
GROUP BY 1, 2
ORDER BY 1, 2;
