-- Pregunta: ¿Qué códigos de zona de origen concentran la demanda?
-- Se muestran IDs TLC; su nombre requiere el catálogo externo de zonas.
SELECT file_year AS anio, taxi_type AS tipo, pickup_zone_id,
       count(*) AS viajes
FROM trips
WHERE year(pickup_datetime) = file_year AND pickup_zone_id IS NOT NULL
GROUP BY 1, 2, 3
QUALIFY row_number() OVER (PARTITION BY file_year, taxi_type ORDER BY count(*) DESC) <= 10
ORDER BY 1, 2, viajes DESC;
