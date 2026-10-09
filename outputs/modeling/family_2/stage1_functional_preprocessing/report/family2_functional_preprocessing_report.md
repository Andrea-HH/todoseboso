# Familia 2 - F2.1 Functional preprocessing and smoothing

## Alcance

Se construyeron funciones para 197 parcelas usando exclusivamente tablas canónicas procesadas. No se leyó ni utilizó rendimiento, no se ejecutó FPCA, clustering o modelado. Dominio: días desde 2025-04-01, t=0..213. La malla diaria es evaluación matemática, no resolución observacional.

## Método

Sentinel y Planet usan B-splines cúbicos penalizados por segundas diferencias. `n_basis` y lambda se eligen globalmente por source×índice minimizando la mediana del GCV target-free. Las curvas de media y heterogeneidad están separadas. Climate compara interpolación lineal, cúbica natural y P-splines de cinco bases mediante leave-one-month-out; precipitación conserva `monthly_accumulation`. Low support satelital: n<8, fracción<25%, gap>60 días o cobertura que omite >30 días de un borde. Las banderas son diagnósticas, no exclusiones.

## Respuestas

1. **Series estables:** [{'source': 'Planet', 'variable': 'evi'}, {'source': 'Planet', 'variable': 'lai'}, {'source': 'Planet', 'variable': 'msavi'}, {'source': 'Planet', 'variable': 'ndvi'}, {'source': 'Sentinel', 'variable': 'dswi4'}, {'source': 'Sentinel', 'variable': 'dswi5'}, {'source': 'Sentinel', 'variable': 'endwi'}, {'source': 'Sentinel', 'variable': 'evi'}, {'source': 'Sentinel', 'variable': 'fapar'}, {'source': 'Sentinel', 'variable': 'lai'}, {'source': 'Sentinel', 'variable': 'ndvi'}, {'source': 'Sentinel', 'variable': 'ndwi'}, {'source': 'Sentinel', 'variable': 'savi'}].
2. **Sentinel:** 100.0% de curvas-indice sin low-support en promedio; sí tiene soporte para FDA, conservando banderas por curva.
3. **Planet:** 100.0% sin low-support en promedio; sí tiene soporte para FDA.
4. **Landsat:** mediana n=18, gap máximo mediano=32.0, low-support=0.5%. Recomendación: FUNCTIONAL_NOT_RECOMMENDED_INITIAL_STAGE.
5. **Sentinel smoothing:** P-spline cúbico penalizado, seleccionado por GCV global source×índice; evita interpolación exacta y mantiene comparabilidad.
6. **Climate:** configuraciones elegidas por LOOCV mensual: [{'variable': 'precip', 'basis_type': 'piecewise_linear', 'n_basis': nan, 'lambda': nan}, {'variable': 'tmin', 'basis_type': 'natural_cubic', 'n_basis': nan, 'lambda': nan}, {'variable': 'tmax', 'basis_type': 'low_flex_pspline_l10', 'n_basis': 5.0, 'lambda': 10.0}, {'variable': 'tmean', 'basis_type': 'piecewise_linear', 'n_basis': nan, 'lambda': nan}, {'variable': 'dtr', 'basis_type': 'piecewise_linear', 'n_basis': nan, 'lambda': nan}]. Cada valor diario es función derivada de siete resúmenes mensuales.
7. **Bases/lambda:** detalle completo por índice en `functional_smoothing_metadata.csv`; rangos Sentinel: n_basis 6-12, lambda 0.01-1; Planet: 12-12, lambda 0.01-0.01.
8. **AUC:** distorsión absoluta mediana Sentinel=0.005, Planet=0.003; consultar índice por índice.
9. **Peak magnitude:** diferencia absoluta mediana Sentinel=0.037, Planet=0.061.
10. **Peak timing:** desplazamiento absoluto mediano Sentinel=10.0 días, Planet=5.5.
11. **Tasas:** distorsiones de crecimiento/caída están en `functional_quality_summary.csv`; derivadas se guardaron pero no se interpretaron como siembra/cosecha.
12. **Over-smoothing:** Sentinel mediana entre índices=22.8%; Planet=9.6%. Casos se conservan con bandera.
13. **Boundary effects:** ninguna curva omite más de 14 días de un borde bajo la regla principal, pero la malla contiene 3.7% de puntos Sentinel, 1.6% Planet y 14.0% Climate fuera del rango observado. Están marcados `BOUNDARY_EXTRAPOLATION` y no deben interpretarse como igual soporte.
14. **Índices estables:** {'Planet': ['evi', 'lai', 'msavi', 'ndvi'], 'Sentinel': ['dswi4', 'dswi5', 'endwi', 'evi', 'fapar', 'lai', 'ndvi', 'ndwi', 'savi']}.
15. **Potencialmente ruidosos:** ninguna curva activó la regla conservadora de under-smoothing. Los índices menos estables por distorsión de eventos/posible over-smoothing son [{'source': 'Sentinel', 'variable': 'enddi', 'pct_potentially_over_smoothed': 73.1}, {'source': 'Sentinel', 'variable': 'crc', 'pct_potentially_over_smoothed': 62.94}, {'source': 'Sentinel', 'variable': 'srndi', 'pct_potentially_over_smoothed': 59.39}, {'source': 'Sentinel', 'variable': 'mcrc', 'pct_potentially_over_smoothed': 52.28}, {'source': 'Sentinel', 'variable': 'dswi2', 'pct_potentially_over_smoothed': 51.27}]; es diagnóstico, no descarte.
16. **Sentinel vs Planet:** [{'index': 'evi', 'median_correlation': 0.985, 'median_abs_peak_difference': 6.0}, {'index': 'lai', 'median_correlation': 0.964, 'median_abs_peak_difference': 10.0}, {'index': 'ndvi', 'median_correlation': 0.989, 'median_abs_peak_difference': 8.0}]. Se comparan sin fusionarlos.
17. **Naturaleza climática:** preservada explícitamente mediante `variable_type`, siete soportes mensuales y etiqueta `MONTHLY_FUNCTION_EVALUATION`; precipitación no se interpreta como lluvia diaria.
18. **A F2.2/FPCA:** curvas promedio estables Sentinel y Planet; Climate como bloque funcional de baja frecuencia separado. Empezar con representantes conceptuales (NDVI/EVI/LAI, humedad/estrés) en vez de incluir automáticamente todos.
19. **Secundarias:** heterogeneidad Sentinel std/range, índices con low-support/over-smoothing y Landsat; no mezclarlos aún con MEAN_FUNCTIONS.
20. **Infraestructura:** sí: grids diarios/semanales, coeficientes, derivadas, metadata, soporte y calidad están persistidos. Antes de FPCA se debe fijar el subconjunto de señales usando sólo estos diagnósticos target-free.

## Recomendación F2.2

Iniciar con funciones promedio Sentinel/Planet estables, sensores separados, y Climate como bloque mensual de baja frecuencia. Mantener heterogeneidad en sensibilidad secundaria y Landsat fuera de la primera ronda. No se ejecutó FPCA.
