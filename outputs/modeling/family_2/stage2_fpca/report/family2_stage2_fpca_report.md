# Familia 2 — F2.2 Redundancia funcional y FPCA

## Alcance y controles

Se analizaron 197 parcelas sobre t=0..213. La selección de señales, smoothing y FPCA fue completamente target-free. El rendimiento no se leyó para construir la representación. La FPCA se calculó en la métrica funcional L2 mediante cuadratura trapezoidal de las funciones suavizadas; el grid diario no fue tratado como 214 features independientes. Climate y Landsat permanecen fuera. Planet no se fusionó con Sentinel. F2.3 no fue ejecutada.

## Respuestas

1. **Vigor redundante.** Las aristas compuestas fuertes fueron: NDVI–EVI, NDVI–LAI, NDVI–FAPAR, EVI–LAI, EVI–FAPAR, EVI–SAVI, LAI–FAPAR, LAI–SAVI, FAPAR–SAVI.
2. **Humedad/estrés redundante.** Aristas fuertes: NDWI–ENDWI, NDWI–DSWI5, ENDWI–DSWI4, ENDWI–DSWI5, DSWI4–DSWI5.
3. **Dinámica diferenciada.** Se conservan señales sin arista fuerte respecto de las ya seleccionadas; la decisión combina nivel, derivada y timings, no una correlación aislada.
4. **Conjunto compacto Sentinel.** NDVI, SAVI, NDWI, DSWI4 (4 señales). La tabla `selected_functional_signals.csv` documenta inclusiones y exclusiones.
5. **Planet vs Sentinel.** Resumen: [{'index': 'evi', 'curve_correlation_median': 0.985, 'derivative_correlation_median': 0.851, 'peak_timing_difference_days_median': 6.0}, {'index': 'lai', 'curve_correlation_median': 0.964, 'derivative_correlation_median': 0.741, 'peak_timing_difference_days_median': 10.0}, {'index': 'ndvi', 'curve_correlation_median': 0.989, 'derivative_correlation_median': 0.876, 'peak_timing_difference_days_median': 8.0}]. Correlación alta de forma con desplazamientos de eventos indica principalmente mayor densidad y pequeñas diferencias temporales; se mantiene como replicación separada.
6. **FPCs para 80/90/95%.** [{'signal': 'ndvi', 'n_fpc_80': 3, 'n_fpc_90': 4, 'n_fpc_95': 5}, {'signal': 'savi', 'n_fpc_80': 3, 'n_fpc_90': 3, 'n_fpc_95': 4}, {'signal': 'ndwi', 'n_fpc_80': 3, 'n_fpc_90': 4, 'n_fpc_95': 5}, {'signal': 'dswi4', 'n_fpc_80': 3, 'n_fpc_90': 3, 'n_fpc_95': 4}].
7. **Interpretación FPC1–FPC3.** Las figuras `fpca_modes_*` muestran media ±2√λφ (el signo de cada FPC es arbitrario). En las cuatro señales, FPC1 (47.6–53.9%) contrasta un máximo central más temprano con mantenimiento/segundo máximo tardío: domina **timing y duración**, no sólo nivel. FPC2 (19.8–21.5%) vuelve a separar ascenso temprano alrededor de t≈90–110 de máximo central/tardío alrededor de t≈145–200. FPC3 (15.3–18.3%) captura principalmente **amplitud y persistencia tardía**; en NDWI también contrasta el nivel alrededor de t≈90 con t≈150–210. Son modos mixtos, por lo que no se presentan como fechas agronómicas exactas.
8. **Redundancia entre scores.** Hay 9 pares de scores con |r|≥0.90. Véanse `functional_score_correlation.csv` y el heatmap.
9. **Dimensión efectiva.** La suma de FPCs requeridas al 95% es 18, pero la matriz conjunta tiene rango efectivo de participación 5.91 y 6 ejes explican 90% de su varianza estandarizada. Esto confirma redundancia cruzada y no equivale automáticamente al número final de features predictivas.
10. **Parcelas difíciles.** En 6 de 9 aumenta el percentil de distancia 5NN en el espacio funcional; mediana del cambio=0.087. Esto indica separación funcional sólo para parte de ellas, no demuestra explicación del error.
11. **¿Family 1 perdió información temporal?** Hay evidencia descriptiva si cambian vecinos/distancias y existen FPC2/FPC3 no redundantes, pero no evidencia predictiva hasta nested CV en F2.3.
12. **Scores para F2.3.** Llevar los scores hasta 95% como candidato completo y definir una alternativa compacta (90%) dentro del pipeline. FPCA debe reajustarse dentro de cada train fold; no reutilizar scores globales para validación.
13. **Grid de smoothing futuro.** Por señal: λ/10, λ default y 10λ, detallado en `fpca_metadata.csv`. Selección sólo por RMSE de inner CV y con smoothing+FPCA reajustados en train fold.
14. **Preparación.** F2.2 queda lista técnicamente para F2.3: artefactos completos, representación target-free y benchmark Climate Current separado. No se inició modelado híbrido.

## Regla de redundancia

Arista sólo si mediana corr(curva)≥0.95, mediana corr(derivada)≥0.90, diferencia mediana de pico≤10 días y diferencias medianas de máximo crecimiento y declive≤14 días. Una señal excluida no es declarada inútil: sólo es redundante para esta primera representación compacta.

## Precaución de validación

Los scores globales son diagnósticos y un insumo de desarrollo. En F2.3, smoothing, centrado, FPCA, número de scores y cualquier selección deben ajustarse exclusivamente en cada train fold interno/externo para evitar leakage.
