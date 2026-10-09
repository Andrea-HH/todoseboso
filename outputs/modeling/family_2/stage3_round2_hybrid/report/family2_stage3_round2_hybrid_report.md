# Familia 2 — F2.3 Round 2 Hybrid

## Controles

Se ejecutaron exclusivamente ocho pipelines en cuatro pares matched, con los 50 outer folds congelados y 4 inner folds. Climate Current contiene exactamente 48 features de Familia 1. Imputación, escala, FPCA, penalizaciones y regresores se ajustaron dentro del train correspondiente. No se añadieron otras fuentes, no se inició Familia 3 y no se predijeron las 59 parcelas.

## Respuestas

1. **Mejor Climate-only:** `CLIMATE_ENET`, RMSE=0.5101.
2. **Mejor híbrido:** `CLIMATE_FPCA_ENET`, RMSE=0.5232.
3. **¿Supera XGB Climate 0.5107?** No.
4. **Diferencia:** 0.0125 RMSE peor.
5. **Consistencia:** mean Δ=+0.0130, median Δ=+0.0093, wins=28%. Los resultados por repetición están en `paired_incremental_comparisons.csv`; Wilcoxon es sólo descriptivo porque repeated-CV induce dependencia.
6. **FPCA + Ridge:** mean Δ=+0.0101, median Δ=+0.0092, wins=20%.
7. **FPCA + Elastic Net:** mean Δ=+0.0130, median Δ=+0.0093, wins=28%.
8. **FPCA + XGBoost:** mean Δ=+0.0160, median Δ=+0.0082, wins=24%.
9. **SOF_ALL4 controlando Climate:** mean Δ=+0.0698, median Δ=+0.0622, wins=4%.
10. **Mejor complemento funcional:** `CLIMATE_FPCA_RIDGE` por delta medio.
11. **Scores que sobreviven ENET:** [{'index': 'dswi4', 'mean_selection_frequency': 0.35, 'scores': 4}, {'index': 'ndvi', 'mean_selection_frequency': 0.516, 'scores': 5}, {'index': 'ndwi', 'mean_selection_frequency': 0.337, 'scores': 5}, {'index': 'savi', 'mean_selection_frequency': 0.035, 'scores': 4}].
12. **Importancia XGBoost agregada:** {'climate': 0.868, 'functional': 0.132}. Importancia gain normalizada por fold; no se calculó SHAP.
13. **Beta(t) estable:** [{'signal': 'ndvi', 'start_t': 1, 'end_t': 78, 'n_days': 78, 'dominant_sign': 'positive', 'mean_sign_stability': 0.901, 'mean_beta': 0.117}, {'signal': 'ndvi', 'start_t': 149, 'end_t': 213, 'n_days': 65, 'dominant_sign': 'positive', 'mean_sign_stability': 0.943, 'mean_beta': 0.068}, {'signal': 'ndwi', 'start_t': 30, 'end_t': 93, 'n_days': 64, 'dominant_sign': 'positive', 'mean_sign_stability': 0.952, 'mean_beta': 0.057}, {'signal': 'dswi4', 'start_t': 35, 'end_t': 89, 'n_days': 55, 'dominant_sign': 'negative', 'mean_sign_stability': 0.94, 'mean_beta': -0.061}, {'signal': 'ndwi', 'start_t': 106, 'end_t': 158, 'n_days': 53, 'dominant_sign': 'negative', 'mean_sign_stability': 0.895, 'mean_beta': -0.026}, {'signal': 'savi', 'start_t': 169, 'end_t': 213, 'n_days': 45, 'dominant_sign': 'negative', 'mean_sign_stability': 0.954, 'mean_beta': -0.082}, {'signal': 'dswi4', 'start_t': 98, 'end_t': 138, 'n_days': 41, 'dominant_sign': 'positive', 'mean_sign_stability': 0.958, 'mean_beta': 0.028}, {'signal': 'ndvi', 'start_t': 101, 'end_t': 126, 'n_days': 26, 'dominant_sign': 'negative', 'mean_sign_stability': 0.849, 'mean_beta': -0.034}, {'signal': 'ndwi', 'start_t': 0, 'end_t': 22, 'n_days': 23, 'dominant_sign': 'negative', 'mean_sign_stability': 0.955, 'mean_beta': -0.134}, {'signal': 'dswi4', 'start_t': 153, 'end_t': 170, 'n_days': 18, 'dominant_sign': 'negative', 'mean_sign_stability': 0.874, 'mean_beta': -0.017}]. Son asociaciones condicionales descriptivas, no eventos causales.
14. **Bajos rendimientos, mejor híbrido:** RMSE=0.7339, bias=+0.4689; compárese por par en `yield_segment_performance.csv`.
15. **Altos rendimientos:** RMSE=0.4974, bias=-0.3870.
16. **Regresión a la media:** beta híbrido=0.617, baseline matched=0.630. Sólo es favorable si mejora hacia 1 sin sacrificar RMSE.
17. **Nueve parcelas difíciles:** mejoran 4/9; mejora media=-0.0101 t/ha en error absoluto. De las seis separadas funcionalmente mejoran 2/6.
18. **Contribución predictiva:** no hay evidencia útil de valor incremental bajo el criterio predefinido.
19. **Papel de Familia 2:** debe conservarse principalmente como análisis temporal e interpretativo.
20. **Cierre:** Round 2 es la prueba decisiva. conviene cerrar Familia 2 sin promover un híbrido y comenzar después Familia 3.
