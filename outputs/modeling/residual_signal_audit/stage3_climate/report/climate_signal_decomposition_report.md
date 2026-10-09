# RS3 — Climate Signal Decomposition

## Controles
Se analizaron sólo las 48 features Climate Current de Family 1, periodo abril–octubre 2025, con los mismos 50 outer folds. Selección supervised, redundancia y PCA predictiva se recalcularon dentro de cada outer-train. No se usó History, Sentinel histórico, Planet, Topography, clustering ni predicción final.

## Respuestas
1. **Contenido:** {'precip': 10, 'tmin': 10, 'tmax': 10, 'tmean': 9, 'dtr': 9}; familias={'temperature_level': 29, 'precipitation': 10, 'thermal_amplitude': 9}.
2. **Redundancia:** {'n_features': 48.0, 'constant_features': 0.0, 'exact_duplicate_pairs': 0.0, 'median_abs_corr': 0.583, 'p75_abs_corr': 0.854, 'p90_abs_corr': 0.96, 'p95_abs_corr': 0.984, 'p99_abs_corr': 0.998}.
3. **Dimensión PCA:** PCs para 80/90/95/99%={0.8: 3, 0.9: 3, 0.95: 3, 0.99: 5}.
4. **Mejor subfamilia sola:** {'experiment': 'ONLY_PRECIPITATION_XGB', 'RMSE': 0.5027519875418617, 'delta_vs_CLIMATE_ENET': -0.007393529469086066, 'fold_win_rate_vs_ENET': 0.6}.
5. **Ablación más dañina:** {'experiment': 'WITHOUT_PRECIPITATION_XGB', 'RMSE': 0.549321374710226, 'delta_vs_CLIMATE_ENET': 0.03917585769927841}.
6. **Precipitación vs temperatura:** precipitación XGB=0.5028; temperatura ENET=0.5304. Domina precipitación.
7. **DTR incremental:** retirar amplitud térmica da ENET=0.5092 frente a ALL_ENET=0.5101; DTR no aporta mejora incremental demostrable.
8. **Timing de lluvia:** total solo XGB=0.6316, timing solo XGB=0.5668, precipitación completa XGB=0.5028. Se necesita la estructura conjunta, no sólo el total ni sólo timing.
9. **Ventanas:** early XGB=0.5126, mid=0.5328, late=0.5295; early es la mejor aislada, pero no supera ALL_ENET.
10. **Features estables:** `climate_feature_stability.csv` y `climate_xgb_importance.csv`.
11. **Concentración:** se evalúa por top-k nested, no por importancia global.
12. **TOP-k:** [{'experiment': 'SUPERVISED_TOP20_ENET', 'n_features_mean': 20.0, 'RMSE': 0.5052, 'delta_vs_CLIMATE_ENET': -0.0049, 'fold_win_rate_vs_ENET': 0.72}, {'experiment': 'SUPERVISED_TOP30_ENET', 'n_features_mean': 30.0, 'RMSE': 0.5082, 'delta_vs_CLIMATE_ENET': -0.002, 'fold_win_rate_vs_ENET': 0.62}, {'experiment': 'SUPERVISED_TOP48_ENET', 'n_features_mean': 48.0, 'RMSE': 0.5102, 'delta_vs_CLIMATE_ENET': 0.0, 'fold_win_rate_vs_ENET': 0.5}, {'experiment': 'SUPERVISED_TOP15_ENET', 'n_features_mean': 15.0, 'RMSE': 0.512, 'delta_vs_CLIMATE_ENET': 0.0019, 'fold_win_rate_vs_ENET': 0.46}, {'experiment': 'SUPERVISED_TOP10_ENET', 'n_features_mean': 10.0, 'RMSE': 0.5454, 'delta_vs_CLIMATE_ENET': 0.0352, 'fold_win_rate_vs_ENET': 0.14}, {'experiment': 'SUPERVISED_TOP5_ENET', 'n_features_mean': 5.0, 'RMSE': 0.5763, 'delta_vs_CLIMATE_ENET': 0.0661, 'fold_win_rate_vs_ENET': 0.02}].
13. **Target-free:** [{'experiment': 'TARGETFREE95_XGB', 'n_features_mean': 17.56, 'RMSE': 0.5079, 'delta_vs_CLIMATE_ENET': -0.0022}, {'experiment': 'TARGETFREE95_ENET', 'n_features_mean': 17.56, 'RMSE': 0.5084, 'delta_vs_CLIMATE_ENET': -0.0018}, {'experiment': 'TARGETFREE95_RIDGE', 'n_features_mean': 17.56, 'RMSE': 0.5133, 'delta_vs_CLIMATE_ENET': 0.0032}].
14. **PCA predictiva:** [{'experiment': 'PCA99_ENET', 'n_features_mean': 5.0, 'RMSE': 0.5226, 'delta_vs_CLIMATE_ENET': 0.0125}, {'experiment': 'PCA99_RIDGE', 'n_features_mean': 5.0, 'RMSE': 0.5234, 'delta_vs_CLIMATE_ENET': 0.0133}, {'experiment': 'PCA90_RIDGE', 'n_features_mean': 3.0, 'RMSE': 0.5555, 'delta_vs_CLIMATE_ENET': 0.0454}, {'experiment': 'PCA90_ENET', 'n_features_mean': 3.0, 'RMSE': 0.5556, 'delta_vs_CLIMATE_ENET': 0.0455}, {'experiment': 'PCA95_ENET', 'n_features_mean': 3.36, 'RMSE': 0.5569, 'delta_vs_CLIMATE_ENET': 0.0468}, {'experiment': 'PCA95_RIDGE', 'n_features_mean': 3.36, 'RMSE': 0.5571, 'delta_vs_CLIMATE_ENET': 0.0469}].
15. **Ridge/ENET suficientes:** [{'experiment': 'ALL_ENET', 'RMSE': 0.5101, 'MAE': 0.3709, 'R2': 0.6054}, {'experiment': 'ALL_XGB', 'RMSE': 0.5112, 'MAE': 0.37, 'R2': 0.605}, {'experiment': 'ALL_RIDGE', 'RMSE': 0.5144, 'MAE': 0.3755, 'R2': 0.5982}].
16. **No linealidad XGB:** en las 48 variables ENET≈XGB; dentro de precipitación XGB sí es claramente superior a ENET, compatible con thresholds/interacciones específicas.
17. **Saturación:** curva en `supervised_topk_metrics.csv`.
18. **Extremos:** `climate_yield_segments.csv`.
19. **Difficult parcels:** `difficult_parcels_climate.csv`; no se usaron para seleccionar.
20. **Candidato predictivo RS4:** ONLY_PRECIPITATION_XGB, RMSE=0.5028.
21. **Alternativa compacta:** SUPERVISED_TOP20_ENET, n≈20.0, RMSE=0.5052.
22. **Mantener/reducir:** decidir por diferencia y estabilidad, no por un único fold.
23. **Interpretación:** la taxonomía separa precipitación, nivel térmico, amplitud y fase; asociación no implica causalidad.
24. **Decisión:** etiquetas=['CLIMATE_COMPACT', 'CLIMATE_LINEAR']; listo para RS4 únicamente con los dos candidatos anteriores. RS4 no fue ejecutado.
