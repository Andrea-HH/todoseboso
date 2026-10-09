# Climate Regime Stage R2 — Characterization and Prediction

## Controles

La caracterización usa memberships globales R1; toda evaluación predictiva reajusta StandardScaler, PCA 95% y GMM K=2 full dentro de cada inner/outer train. Los componentes se alinean contra perfiles climáticos R1 mediante distancia de centroides estandarizados, nunca usando yield. Se reutilizan 50 outer folds y 4 inner folds. No se entrenaron expertos separados ni se inició R3/Familia 3. Diagnóstico de transportabilidad: 28/50 outer GMM alcanzan el piso de covarianza y el tamaño efectivo train de R2 varía entre 28.0 y 88.0; 99.8% de memberships validation tienen probabilidad dominante >0.90.

## Respuestas

1. **Distribuciones distintas:** [{'regime': 1, 'hard_n': 103, 'hard_mean_yield': 4.27, 'hard_median_yield': 4.5, 'hard_std_yield': 0.728}, {'regime': 2, 'hard_n': 35, 'hard_mean_yield': 3.029, 'hard_median_yield': 3.0, 'hard_std_yield': 0.382}]; Spearman yield–P(R2)=-0.595. Es asociación descriptiva, no causal.
2. **Mayor rendimiento:** régimen 1 en media y régimen 1 en mediana.
3. **Nivel/dispersión/extremos:** cuantiles y proporciones LOW/MID/HIGH están en `yield_by_regime.csv`; las diferencias no redefinen los regímenes.
4. **Régimen más difícil:** [{'pipeline': 'CLIMATE_ENET', 'group': 'R1', 'RMSE': 0.546, 'MAE': 0.377, 'R2': 0.431, 'bias': -0.006}, {'pipeline': 'CLIMATE_ENET', 'group': 'R2', 'RMSE': 0.419, 'MAE': 0.338, 'R2': -0.236, 'bias': 0.02}, {'pipeline': 'CLIMATE_XGB', 'group': 'R1', 'RMSE': 0.544, 'MAE': 0.367, 'R2': 0.436, 'bias': -0.013}, {'pipeline': 'CLIMATE_XGB', 'group': 'R2', 'RMSE': 0.428, 'MAE': 0.354, 'R2': -0.29, 'bias': 0.065}, {'pipeline': 'XGB_CORE', 'group': 'R1', 'RMSE': 0.557, 'MAE': 0.395, 'R2': 0.408, 'bias': -0.053}, {'pipeline': 'XGB_CORE', 'group': 'R2', 'RMSE': 0.409, 'MAE': 0.341, 'R2': -0.176, 'bias': 0.1}]. R1 tiene mayor RMSE absoluto por su mayor dispersión; R2 tiene R² negativo y slope≈0, por lo que es más difícil explicar internamente.
5. **Bias CLIMATE_ENET:** [{'group': 'R1', 'bias': -0.006, 'calibration_slope': 0.433}, {'group': 'R2', 'bias': 0.02, 'calibration_slope': -0.051}].
6. **Bias XGB:** [{'group': 'R1', 'bias': -0.013, 'calibration_slope': 0.448}, {'group': 'R2', 'bias': 0.065, 'calibration_slope': -0.05}].
7. **Membership en ENET:** Δ medio=+0.0022, mediano=+0.0003, wins=34%.
8. **Membership en XGB:** Δ medio=+0.0001, wins=48%.
9. **Soft interactions:** RMSE=0.5139; Δ=+0.0038, mediana=+0.0007.
10. **Magnitud:** el signo anterior es regime-aware menos baseline; negativo representa mejora.
11. **Proporción de folds:** 36%; resultados por repetición en `paired_comparisons.csv`.
12. **Hard vs soft:** hard RMSE=0.5139, soft=0.5139; Δ soft−hard=-0.0000. Son prácticamente idénticos porque las memberships fold-wise también son casi discretas.
13. **Interacciones estables:** [].
14. **Temperatura/DTR:** revisar las filas `tmin/tmax/tmean/dtr` anteriores; sólo se consideran relativamente estables si frecuencia≥50% y estabilidad de signo≥70%.
15. **Precipitación:** mismo criterio para total, early, mid, late y concentración; no son efectos causales.
16. **Régimen minoritario R2:** RMSE baseline=0.4435, regime-aware=0.4440; empeora.
17. **Extremos:** [{'pipeline': 'CLIMATE_XGB_BASE', 'segment': 'LOW', 'RMSE': 0.715, 'bias': 0.462}, {'pipeline': 'CLIMATE_XGB_BASE', 'segment': 'MID', 'RMSE': 0.387, 'bias': -0.022}, {'pipeline': 'CLIMATE_XGB_BASE', 'segment': 'HIGH', 'RMSE': 0.482, 'bias': -0.367}, {'pipeline': 'XGB_CLIMATE_PLUS_MEMBERSHIP', 'segment': 'LOW', 'RMSE': 0.716, 'bias': 0.463}, {'pipeline': 'XGB_CLIMATE_PLUS_MEMBERSHIP', 'segment': 'MID', 'RMSE': 0.387, 'bias': -0.022}, {'pipeline': 'XGB_CLIMATE_PLUS_MEMBERSHIP', 'segment': 'HIGH', 'RMSE': 0.481, 'bias': -0.367}].
18. **Parcelas difíciles:** mejoran 11/28; entre las 9 y-atypical mejoran 4/9.
19. **Heterogeneidad climate→yield:** no hay evidencia predictiva consistente bajo los criterios predefinidos. Además, la inestabilidad/singularidad fold-wise indica que la partición global climática no se transporta limpiamente a muestras de ~110 parcelas.
20. **Stage R3:** no existe soporte suficiente para mixture-of-experts.
21. **Papel de regímenes:** deben conservarse principalmente como descripción climática.
