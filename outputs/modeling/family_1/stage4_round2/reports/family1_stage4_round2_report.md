# Familia 1 — Etapa 4, Ronda 2

Se ejecutaron exactamente nueve pipelines sobre los 50 outer folds congelados. Las referencias de Ronda 1 fueron reutilizadas, no reentrenadas. No se ejecutó ninguna etapa posterior.

1. **Mejor RMSE medio Ronda 2:** XGB_CORE_EXTENDED, 0.5308.
2. **Mejor RMSE mediano:** XGB_PRUNED, 0.5195.
3. **Más estable:** ENET_PRUNED, std=0.0908.
4. **Mejora frente a XGB_CORE:** mejor nuevo vs XGB_CORE: delta=+0.0037, gana 32% folds, intervalo repetición [-0.0048,+0.0124].
5. **Pruning XGBoost:** delta=+0.0048, gana 36% folds, intervalo repetición [-0.0036,+0.0106].
6. **Pruning LightGBM:** delta=+0.0120, gana 20% folds, intervalo repetición [+0.0018,+0.0292].
7. **Pruning Elastic Net:** vs ALL delta=+0.0041, gana 24% folds, intervalo repetición [-0.0011,+0.0128]; vs CORE delta=-0.0019, gana 54% folds, intervalo repetición [-0.0111,+0.0153].
8. **Threshold preferido:** [{'pipeline': 'ENET_PRUNED', 'threshold': 0.98, 'selection_frequency': 0.88, 'median_features_retained': 1126.0}, {'pipeline': 'LGBM_PRUNED', 'threshold': 0.98, 'selection_frequency': 0.68, 'median_features_retained': 1127.0}, {'pipeline': 'XGB_PRUNED', 'threshold': 0.98, 'selection_frequency': 0.42, 'median_features_retained': 1127.0}].
9. **Sentinel EXTENDED:** XGB delta=+0.0037, gana 32% folds, intervalo repetición [-0.0048,+0.0124]; LGBM delta=+0.0070, gana 36% folds, intervalo repetición [+0.0021,+0.0140]; ENET delta=-0.0074, gana 68% folds, intervalo repetición [-0.0143,+0.0091].
10. **Topografía avanzada:** XGB delta=+0.0042, gana 38% folds, intervalo repetición [-0.0061,+0.0104]; LGBM delta=+0.0031, gana 38% folds, intervalo repetición [-0.0041,+0.0151]; ENET delta=+0.0010, gana 36% folds, intervalo repetición [-0.0149,+0.0164].
11. **Consistencia EXTENDED:** se evalúa por signo, proporción de victorias e intervalos anteriores; no basta el promedio.
12. **Consistencia TOPOADV:** se evalúa análogamente; consultar `round2_paired_comparisons.csv`.
13. **Mejor en rendimiento bajo:** XGB_CORE por RMSE OOF agregado.
14. **Mejor en rendimiento alto:** XGB_CORE.
15. **Mayor regresión a la media:** betas más bajas: [{'pipeline': 'BASELINE_MEAN', 'beta': -0.008, 'R2_descriptive': 0.244}, {'pipeline': 'ENET_CORE_TOPOADV', 'beta': 0.503, 'R2_descriptive': 0.594}, {'pipeline': 'ENET_ALL', 'beta': 0.51, 'R2_descriptive': 0.605}, {'pipeline': 'ENET_PRUNED', 'beta': 0.511, 'R2_descriptive': 0.6}, {'pipeline': 'ENET_CORE_EXTENDED', 'beta': 0.515, 'R2_descriptive': 0.608}].
16. **Parcelas sistemáticamente difíciles:** ['AGC_171', 'AGC_015', 'AGC_034', 'AGC_162', 'AGC_024', 'AGC_166', 'AGC_055', 'AGC_127', 'AGC_069', 'AGC_160']. No se excluyó ninguna.
17. **Features individuales:** frecuencias completas en `elasticnet_feature_frequency_round2.csv`; la estabilidad sigue siendo limitada si pocas superan 0.8.
18. **Familias:** `feature_family_stability_round2.csv` permite contrastar estabilidad agregada frente a nombres individuales.
19. **Finalistas para source ablation:** ['XGB_CORE', 'LGBM_CORE', 'ENET_CORE_EXTENDED']; uno por familia, considerando desempeño, estabilidad y complejidad.
20. **Modelos descartados:** no hay evidencia en esta ronda que justifique reabrir PLS/PCR/PCA local; no fueron ejecutados.

## Nota

Los intervalos son percentiles 2.5/97.5 de los diez deltas medios por repetición, no t-tests sobre 50 folds supuestamente independientes. Los rangos low/middle/high y regresiones a la media son sólo diagnósticos OOF.
