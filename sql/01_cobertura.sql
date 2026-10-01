-- Pregunta: ¿Cuántos archivos y viajes hay por tipo, año y mes?
-- Fuente: vista trips sobre los Parquet originales; sin tabla importada.
SELECT file_year AS anio, file_month AS mes, taxi_type AS tipo,
       count(DISTINCT source_file) AS archivos, count(*) AS viajes,
       min(pickup_datetime) AS primera_recogida,
       max(pickup_datetime) AS ultima_recogida
FROM trips
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
