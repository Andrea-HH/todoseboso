# RS2 — History Signal Decomposition

## Controles

HISTORY tiene 39 features: 13 variables × `mean`, `std`, `months`; periodo real abril–octubre 2022–2024 agrupado por mes calendario. No hay identidad anual después del feature engineering. Residual=`y−ŷ_CLIMATE_ENET`; todo resultado predictivo reutiliza los mismos 50 outer folds, ranking top-k rehecho dentro de outer-train y corrección evaluada sólo en outer-validation. No se ejecutó clustering, GMM, MoE, Planet ni predicción final.

## Respuestas

1. **Contenido:** 24 Sentinel-2 históricas y 15 climáticas históricas; {'historical_level': 13, 'historical_variability': 13, 'coverage': 13}.
2. **Subfamilias:** por fuente, estadístico real (nivel, variabilidad, cobertura) e índice: {'vigor_structure': 15, 'moisture_stress': 9, 'temperature': 9, 'precipitation': 3, 'thermal_range': 3}.
3. **Mayor asociación residual:** [{'feature': 'HIST_S2_ndvi_promedio_mean', 'spearman_residual': 0.1623762240604216}, {'feature': 'HIST_CLIMATE_tmin_mean_mean', 'spearman_residual': 0.1127761230953232}, {'feature': 'HIST_S2_savi_promedio_mean', 'spearman_residual': 0.11072652509537909}, {'feature': 'HIST_S2_ndvi_promedio_std', 'spearman_residual': -0.10505971611159183}, {'feature': 'HIST_CLIMATE_tmean_mean_mean', 'spearman_residual': 0.09565218731584675}, {'feature': 'HIST_S2_evi_promedio_mean', 'spearman_residual': 0.09478548548022894}, {'feature': 'HIST_S2_savi_promedio_std', 'spearman_residual': -0.0924064302984778}, {'feature': 'HIST_S2_nddi_promedio_std', 'spearman_residual': 0.08404548972691094}].
4. **Después de descontar Climate:** [{'feature': 'HIST_S2_ndvi_promedio_std', 'spearman_conditional': -0.185}, {'feature': 'HIST_S2_ndvi_promedio_mean', 'spearman_conditional': 0.179}, {'feature': 'HIST_S2_savi_promedio_std', 'spearman_conditional': -0.166}, {'feature': 'HIST_S2_evi_promedio_std', 'spearman_conditional': -0.158}, {'feature': 'HIST_S2_fapar_promedio_std', 'spearman_conditional': -0.154}, {'feature': 'HIST_CLIMATE_dtr_mean_std', 'spearman_conditional': 0.131}, {'feature': 'HIST_CLIMATE_tmin_mean_mean', 'spearman_conditional': -0.124}, {'feature': 'HIST_S2_nddi_promedio_std', 'spearman_conditional': 0.118}].
5. **Más reconstruibles desde Climate:** [{'feature': 'HIST_CLIMATE_dtr_mean_mean', 'R2_History_from_Climate_OOF': 1.0}, {'feature': 'HIST_CLIMATE_tmax_mean_std', 'R2_History_from_Climate_OOF': 1.0}, {'feature': 'HIST_CLIMATE_tmin_mean_mean', 'R2_History_from_Climate_OOF': 1.0}, {'feature': 'HIST_CLIMATE_tmean_mean_std', 'R2_History_from_Climate_OOF': 1.0}, {'feature': 'HIST_CLIMATE_tmean_mean_mean', 'R2_History_from_Climate_OOF': 1.0}].
6. **Información independiente:** consultar `history_climate_redundancy.csv`; priorizar alta asociación condicional y R² de redundancia bajo/moderado.
7. **Mejor subfamilia sola:** ONLY_source_sensor::Sentinel-2, RMSE=0.4941, Δ=-0.0160.
8. **Ablación más dañina:** WITHOUT_source_sensor::Sentinel-2, cambio contra HISTORY_ALL=+0.0172.
9. **Suficiencia individual:** ranking completo en `subfamily_only_metrics.csv`.
10. **Año dominante:** no puede evaluarse; 2022–2024 fueron agrupados antes de crear las 39 features.
11. **Vigor vs moisture/stress:** comparar filas `ONLY_index_family::*` en `index_family_decomposition.csv`.
12. **Concentración:** top-5/top-10 concentran 34.3%/55.9% de importancia XGB agregada.
13. **Tamaño mínimo observado:** 39 features en HISTORY_ALL; RMSE=0.4942.
14. **Top 5/10 vs ALL:** [{'experiment': 'HISTORY_ALL', 'corrected_RMSE': 0.4942, 'delta_RMSE_mean': -0.0159, 'fold_win_rate': 0.8}, {'experiment': 'TOP_15', 'corrected_RMSE': 0.4968, 'delta_RMSE_mean': -0.0134, 'fold_win_rate': 0.78}, {'experiment': 'TOP_10', 'corrected_RMSE': 0.4995, 'delta_RMSE_mean': -0.0106, 'fold_win_rate': 0.7}, {'experiment': 'TOP_5', 'corrected_RMSE': 0.5031, 'delta_RMSE_mean': -0.007, 'fold_win_rate': 0.66}, {'experiment': 'TOP_3', 'corrected_RMSE': 0.5055, 'delta_RMSE_mean': -0.0047, 'fold_win_rate': 0.62}].
15. **Lineal vs no lineal:** [{'experiment': 'MODEL_ALL_XGB', 'corrected_RMSE': 0.4942, 'delta_RMSE_mean': -0.0159}, {'experiment': 'MODEL_ALL_RIDGE', 'corrected_RMSE': 0.5036, 'delta_RMSE_mean': -0.0065}, {'experiment': 'MODEL_ALL_ENET', 'corrected_RMSE': 0.5103, 'delta_RMSE_mean': 0.0002}]. XGB superior implica thresholds/interacciones predictivas, no causalidad.
16. **Formas:** ALE descriptivo en `top_history_feature_shapes.csv` y figuras individuales.
17. **Interacciones Climate:** estratificación limitada en `history_climate_interactions.csv`; exploratoria, no selección supervisada adicional.
18. **Difficult parcels:** mejora media=0.060; proporción mejorada=78.6%.
19. **y-atypical:** mejora media=0.063; proporción mejorada=77.8%.
20. **Vecinos:** similitud residual/y por all y compact History: {'all_history': {'mean_abs_residual_difference_to_neighbors': 0.529, 'mean_abs_yield_difference_to_neighbors': 0.51}, 'compact_history': {'mean_abs_residual_difference_to_neighbors': 0.52, 'mean_abs_yield_difference_to_neighbors': 0.556}}.
21. **Firma persistente:** evidencia compatible: historia pre-2025, mejora residual reproducible y ayuda a casos difíciles; no demuestra suelo, manejo ni productividad histórica.
22. **Leakage:** las 39 pasan auditoría de construcción pre-2025; `months` es cobertura, no señal biológica, y debe interpretarse con cautela.
23. **Uso directo:** RS1 mostró que Climate+History directo mejora, pero la corrección residual fue ligeramente mejor; conservar corrección residual como opción principal.
24. **Subconjunto compacto:** decidir según curva top-k nested; no usar ranking global para estimar desempeño.
25. **Regímenes:** no hay prueba de clusters en RS2 y no se ejecutaron; no justificarlos sólo por esta señal.
26. **Clasificación final:** **NONLINEAR CONTINUOUS SIGNAL**. Si XGB conserva ventaja, preferir función continua no lineal y NO clusterizar.
