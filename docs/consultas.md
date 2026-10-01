# Catálogo y decisiones de las consultas

Fuente de todas las consultas: archivos oficiales `data/raw/{yellow,green}/{2024,2025,2026}/*.parquet`. La vista temporal `trips`, definida en `scripts/lab8_common.py`, los lee directamente con `read_parquet(..., union_by_name=true, filename=true)` y normaliza nombres de columnas, año, mes y tipo de taxi. No importa los Parquet a una tabla para los ejercicios 3 al 5 y 7 al 8. Los resultados completos se regeneran en `data/processed/results/` con `scripts/run_analysis.py`.

| SQL | Objetivo | Resultado obtenido | Decisión para el análisis |
|---|---|---|---|
| `01_cobertura.sql` | Contar archivos y filas por mes y servicio. | 64 archivos y 121,184,384 filas: 24 de 2024, 24 de 2025 y 16 de 2026. | Separar cobertura de 2026 de años completos. |
| `02_calidad.sql` | Auditar tiempos, distancias, importes y nulos. | 2026 amarillo contiene 7,716,688 pasajeros nulos y 952,231 distancias cero; hay 157 recogidas fuera del año de su archivo en todo el conjunto. | Excluir recogidas fuera de año en indicadores; no usar pasajeros como indicador principal. Mantener auditoría sin borrar datos. |
| `03_viajes_mensuales.sql` | Medir volumen e importe por mes y tipo. | 64 filas tipo-mes; en 2026 enero-agosto: 29,703,338 viajes amarillos y 337,100 verdes tras filtrar año de recogida. | Usar meses publicados y evitar extrapolaciones. |
| `04_distancias.sql` | Describir distancias y extremos. | En 2026, mediana de 1.93 millas en amarillo y 2.14 en verde; las medias son mucho mayores (5.74 y 13.85). | Priorizar medianas y reportar extremos por separado. |
| `05_pagos.sql` | Comparar códigos de pago. | En 2026, tarjeta (código 1) representa 63.77% en amarillo y 65.25% en verde; el código 0 llega a 25.98% en amarillo. | Mostrar explícitamente pagos sin código claro; no interpretar el cambio de tarjeta como cambio de conducta sin revisar codificación. |
| `06_horas.sql` | Localizar horas de demanda. | En 2026 el pico amarillo es 18:00 y el verde 17:00. | Usar porcentajes dentro de cada tipo para comparar perfiles horarios con escalas distintas. |
| `07_propinas.sql` | Medir propinas en pagos con tarjeta. | En 2026 la propina registrada sobre tarifa es 21.53% en amarillo y 20.93% en verde. | Excluir efectivo, tarifas no positivas y propinas negativas. |
| `08_dias_semana.sql` | Describir demanda semanal. | El jueves (código 4 de DuckDB) es el día con mayor volumen en 2026 para ambos tipos. | Usar los códigos de día documentados: 0 domingo a 6 sábado. |
| `09_zonas_origen.sql` | Detectar concentración por zona de recogida. | En 2026 lideran los códigos TLC 237 (amarillo) y 74 (verde). | Presentar códigos, sin inventar nombres de zonas no incluidos en los Parquet. |
| `10_duracion.sql` | Medir duración y anomalías. | Mediana 2026: 14 minutos en amarillo y 13 en verde; existen duraciones negativas. | Excluir duraciones negativas al calcular medias y medianas. |
| `11_importes.sql` | Describir la distribución de cobros. | Mediana 2026: USD 23.71 amarillo y USD 20.49 verde; existen importes superiores a USD 500. | Mantener percentiles y umbrales exploratorios sin tratar todo extremo como error. |
| `12_comparacion_ene_ago.sql` | Comparar los tres años en una ventana común. | Amarillo: 26.39 M (2024), 31.56 M (2025), 29.70 M (2026). Verde: 443 mil, 398 mil y 337 mil. | Comparar enero-agosto de cada año, porque 2026 no está completo. |

Cada archivo SQL contiene la sentencia exacta y comentarios sobre su pregunta, fuentes y filtros. La tabla anterior registra el resultado y la decisión. Los filtros de calidad son específicos de cada pregunta: la auditoría incluye todos los registros, mientras las métricas de viajes suelen exigir `year(pickup_datetime)=file_year`.

## Hallazgos principales

1. En enero-agosto, el volumen amarillo de 2026 supera al de 2024 en aproximadamente 12.6%, mientras el verde baja alrededor de 24.0%. La comparación usa la misma ventana temporal; no atribuye causas.
2. La media de distancia está fuertemente influida por valores extremos, especialmente en Green Taxi: 13.85 millas de media frente a 2.14 de mediana en 2026. La mediana describe mejor el viaje típico.
3. La fracción de pagos codificados como tarjeta en Yellow Taxi pasa de 74.05% (enero-agosto 2024) a 63.77% (2026), mientras crece la presencia del código 0 y de pasajeros nulos. Esto puede reflejar cambios de registro, no necesariamente una transición real de medios de pago.

Los importes están en USD nominales. No se ajustaron por inflación, cambios tarifarios, composición de rutas ni estacionalidad más allá de la ventana común; por tanto, estas diferencias son descriptivas.
