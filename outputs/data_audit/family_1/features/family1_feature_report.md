# Familia 1 — Etapa 3: reporte de features sin target

## Resumen ejecutivo

Se construyó una tabla de **197 parcelas × 1354 features**, con ID único y sin rendimiento. Las fechas reales se usan en pendientes, AUC y tasas; no se interpolaron series. CORE y EXTENDED permanecen separados y los cutoffs futuros pueden reproducirse cambiando el final de ventana sin mirar datos posteriores.

## Respuestas a las preguntas de la etapa

1. **Features por fuente/bloque.** [{'block': 'anomaly_features', 'features': 143}, {'block': 'climate_features', 'features': 55}, {'block': 'history_features', 'features': 39}, {'block': 'landsat_features', 'features': 24}, {'block': 'planet_features', 'features': 304}, {'block': 'sentinel_features_core', 'features': 592}, {'block': 'sentinel_features_extended', 'features': 256}, {'block': 'topography_advanced_features', 'features': 87}, {'block': 'topography_basic_features', 'features': 25}].
2. **CORE estables.** Nivel, cuantiles, AUC normalizada, slope, bordes y eventos son calculables cuando existen ≥2 observaciones; cobertura media no faltante de CORE Sentinel: 100.0%.
3. **Pico, crecimiento y caída.** El pico requiere ≥1 dato; crecimiento/caída requieren ≥2 fechas distintas. Se registra timing en días desde 2025-04-01, evitando strings de fecha en la matriz.
4. **Pre/post-peak slope.** Calculabilidad promedio: pre 98.5% y post 99.9% de parcela-serie.
5. **Drawdown/runup.** Son matemáticamente estables con ≥2 puntos, pero su comparabilidad depende de densidad/cobertura; se deben acompañar por n_obs y gaps.
6. **Heterogeneidad Sentinel.** std, range, lower/upper gap son utilizables. CV se recalculó sólo con |media|≥0.05; fuera de ello queda NaN para evitar explosiones silenciosas.
7. **Landsat robusto.** Mediana/cuantiles, AUC normalizada, slope con días reales, extremos, n válido, fracción válida y gaps; sin interpolación.
8. **Sentinel vs Planet.** Se conservaron como sensores distintos. Hay 0 pares homólogos con |r|>0.98 de 142 comparables; están en `sentinel_planet_descriptive_correlations.csv`. No se eliminó por correlación ni se usó rendimiento.
9. **Clima redundante.** El CORE usa sólo medias espaciales mensuales; min/max/median/std espaciales se excluyen porque la resolución gruesa suele producir un píxel efectivo por parcela.
10. **Histórico.** Para cada parcela y mes calendario abril-octubre se calculó baseline exclusivamente con 2022-2024; luego se resume por variable.
11. **Anomalías.** Absolutas son estables; estandarizadas sólo se calculan con std histórica≥1e-6 e incluyen `unstable_fraction`.
12. **Topografía.** Elevación y pendiente incluyen cuantiles ponderados, dispersión y relieve; consultar los parquets y diagnósticos para rangos.
13. **Clases de pendiente.** Cortes configurables 0–2, 2–5, 5–10, >10°. Desviaciones entre parcelas: {'TOPO_BASIC_pct_area_slope_0_2': 44.02, 'TOPO_BASIC_pct_area_slope_2_5': 37.7, 'TOPO_BASIC_pct_area_slope_5_10': 28.7, 'TOPO_BASIC_pct_area_slope_gt_10': 4.56}; sus porcentajes suman aproximadamente 100%.
14. **Aspect/TPI/curvatura.** Sí. Aspect se representa como sin/cos; TPI/relieve usan vecindad 3×3; curvaturas usan derivadas del DEM y se reportan por signo sin imponer interpretación universal.
15. **Flow direction/accumulation.** Sí, D8 después de llenar pits/depresiones y resolver planos, sobre el DEM entregado completo, sin recortes por parcela ni buffer arbitrario.
16. **TWI.** Se calculó como `ln((accumulation_cells × cellsize) / max(tan(slope), 1e-6))`; es defendible como índice estructural relativo dentro del DEM, no como humedad medida.
17. **Limitaciones hidrológicas.** El borde del raster desconoce aportes externos; resolución 120 m; el acondicionamiento y D8 simplifican el flujo; lluvia y topografía siguen separadas; TWI no valida escurrimiento ni humedad.
18. **CORE vs EXTENDED.** Conteo exacto de features incluidas según el catálogo: {'CORE': 818, 'EXTENDED': 294, 'ANOMALY': 104, 'TOPO_ADVANCED': 87, 'HISTORY': 26, 'TOPO_BASIC': 25}. Los archivos Sentinel CORE y EXTENDED permanecen separados.
19. **Duplicadas por construcción.** Se eliminaron 144 duplicados exactos y 27 constantes/all-missing; detalle en `feature_eliminations.csv`. Correlación alta no implicó eliminación.
20. **Lista para modelado.** Sí como matriz no supervisada de 197 filas e ID único. Antes de entrenar hay que unir target externamente, definir validación, estrategia de missingness y controlar dimensionalidad dentro de cada fold.

## Decisiones antes de modelado supervisado

- Definir EOS frente a cutoffs tempranos y recalcular todos los bloques con el mismo cutoff.
- Diseñar validación que respete la estructura espacial y sólo entonces ajustar imputación/selección.
- Elegir CORE inicial dado el número reducido de parcelas con target y evaluar EXTENDED como ablation.
- Tratar correlaciones >0.98 y eventos con baja cobertura dentro de folds, nunca usando todo el target para seleccionar.
- No interpretar flow accumulation/TWI como mediciones de agua; interacciones clima×terreno requieren una etapa posterior y validación explícita.
