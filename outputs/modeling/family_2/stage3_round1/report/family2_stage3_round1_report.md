# Familia 2 — F2.3 Round 1 functional-only

## Controles

Se reutilizaron exactamente 50 outer folds (5×10) y 4 inner folds. Las cuatro señales quedaron congeladas por F2.2. En cada inner y outer train se reajustaron media funcional, FPCA, proyección, escalado, joint PCA y regresor. Smoothing default de F2.1 permaneció congelado y target-free. No se incorporaron fuentes prohibidas ni se inició el modelo híbrido.

## Respuestas

1. **Mejor modelo functional-only:** `SOF_ALL4`.
2. **RMSE:** media 0.6719, mediana 0.6690.
3. **Family1 Satellite-only:** no supera 0.5845.
4. **Diferencia:** Family 2 es 0.0873 RMSE peor que Satellite-only.
5. **XGB_CORE 0.5270:** diferencia del mejor F2 = +0.1448; no lo alcanza.
6. **Climate Current 0.5107:** diferencia = +0.1612; no lo alcanza.
7. **F_INDEX vs F_JOINT:** mejores respectivos `F2_RIDGE_INDEX` (0.6824) y `F2_ENET_JOINT` (0.6833); gana F_INDEX.
8. **Dimensiones:** selección de ejes joint por fold/modelo: {8.0: 115, 6.0: 35}. Se eligieron 8 en 115/150 ajustes outer y 6 en 35/150; 4 nunca ganó. Aproximadamente 6 ejes no parecen suficientes bajo inner CV. La FPCA por índice usa 17–18 scores.
9. **Linealidad:** Ridge/ENET mejor = 0.6824. Regularización lineal es suficiente frente a XGB, pero SOF_ALL4 mejora modestamente a ambas representaciones FPCA.
10. **No linealidad XGB:** XGB_INDEX=0.6838, frente a Ridge INDEX=0.6824; XGB_JOINT=0.6955, frente a ENET JOINT=0.6833. No hay ganancia no lineal consistente.
11. **PLS compacto:** PLS_INDEX=0.6865, peor que PLS_CORE≈0.5565 y PLS_ALL≈0.5556 de Familia 1. Reabrir PLS no recuperó la señal perdida.
12. **Scalar-on-function:** mejor `SOF_ALL4`=0.6719; es competitivo respecto al mejor.
13. **Curvas individuales:** [{'pipeline': 'SOF_SAVI', 'RMSE_mean': 0.6882141563949857}, {'pipeline': 'SOF_NDVI', 'RMSE_mean': 0.6942460836942576}, {'pipeline': 'SOF_NDWI', 'RMSE_mean': 0.6997423395921163}, {'pipeline': 'SOF_DSWI4', 'RMSE_mean': 0.7529452008920677}].
14. **Vigor vs humedad:** SOF_VIGOR=0.7010; SOF_MOISTURE=0.7353.
15. **Regiones beta estables:** [{'pipeline': 'SOF_ALL4', 'signal': 'savi', 'start_t': 123, 'end_t': 185, 'n_days': 63, 'dominant_sign': 'negative', 'mean_same_sign_proportion': 0.9441269841269844, 'mean_beta': -0.1366401955527228}, {'pipeline': 'SOF_ALL4', 'signal': 'dswi4', 'start_t': 27, 'end_t': 85, 'n_days': 59, 'dominant_sign': 'negative', 'mean_same_sign_proportion': 0.9722033898305084, 'mean_beta': -0.1853252877717665}, {'pipeline': 'SOF_ALL4', 'signal': 'ndwi', 'start_t': 28, 'end_t': 86, 'n_days': 59, 'dominant_sign': 'positive', 'mean_same_sign_proportion': 0.9759322033898306, 'mean_beta': 0.2606195136421633}, {'pipeline': 'SOF_ALL4', 'signal': 'ndvi', 'start_t': 24, 'end_t': 73, 'n_days': 50, 'dominant_sign': 'positive', 'mean_same_sign_proportion': 0.94, 'mean_beta': 0.1860164692311453}, {'pipeline': 'SOF_VIGOR', 'signal': 'savi', 'start_t': 15, 'end_t': 63, 'n_days': 49, 'dominant_sign': 'positive', 'mean_same_sign_proportion': 0.9583673469387752, 'mean_beta': 0.3922367343329281}, {'pipeline': 'SOF_VIGOR', 'signal': 'ndvi', 'start_t': 42, 'end_t': 90, 'n_days': 49, 'dominant_sign': 'positive', 'mean_same_sign_proportion': 0.9583673469387756, 'mean_beta': 0.1407223266880009}, {'pipeline': 'SOF_ALL4', 'signal': 'savi', 'start_t': 31, 'end_t': 76, 'n_days': 46, 'dominant_sign': 'positive', 'mean_same_sign_proportion': 0.8791304347826087, 'mean_beta': 0.2112006989168826}, {'pipeline': 'SOF_MOISTURE', 'signal': 'ndwi', 'start_t': 39, 'end_t': 81, 'n_days': 43, 'dominant_sign': 'positive', 'mean_same_sign_proportion': 0.9613953488372092, 'mean_beta': 0.2346525163612566}, {'pipeline': 'SOF_NDVI', 'signal': 'ndvi', 'start_t': 33, 'end_t': 72, 'n_days': 40, 'dominant_sign': 'positive', 'mean_same_sign_proportion': 0.9785, 'mean_beta': 0.3141497581465973}, {'pipeline': 'SOF_ALL4', 'signal': 'ndvi', 'start_t': 140, 'end_t': 179, 'n_days': 40, 'dominant_sign': 'positive', 'mean_same_sign_proportion': 0.97, 'mean_beta': 0.1409925688812486}, {'pipeline': 'SOF_SAVI', 'signal': 'savi', 'start_t': 33, 'end_t': 72, 'n_days': 40, 'dominant_sign': 'positive', 'mean_same_sign_proportion': 0.98, 'mean_beta': 0.5291640903241065}, {'pipeline': 'SOF_NDVI', 'signal': 'ndvi', 'start_t': 156, 'end_t': 191, 'n_days': 36, 'dominant_sign': 'negative', 'mean_same_sign_proportion': 0.9711111111111111, 'mean_beta': -0.0576853293515312}]. Son estabilidad de signo descriptiva, no evidencia de un evento biológico puntual.
16. **Parcelas difíciles:** mejora media frente a Satellite-only=-0.0119; mejoran 4/9. Entre las seis con mayor distancia funcional, mejoran 2/6.
17. **Extremos:** mejor F2 LOW RMSE=0.8546, bias=+0.6046, frente a Satellite 0.7984/+0.6277; HIGH RMSE=0.6853, bias=-0.4934, frente a Satellite 0.6275/-0.5320. F2 reduce levemente el sesgo absoluto, pero empeora el error en ambos extremos.
18. **Regresión a la media:** beta de calibración=0.515, frente a XGB_SATELLITE=0.470 y XGB_CORE=0.586. F2 reduce algo la compresión respecto a Satellite-only, pero sigue peor que CORE y lejos de 1; no se calibraron predicciones.
19. **Avance híbrido:** la señal funcional aislada no supera el benchmark directo; un híbrido sólo se justifica como prueba acotada de complementariedad.
20. **Conservar:** SOF_ALL4, F2_RIDGE_INDEX, F2_ENET_JOINT como candidatos provisionales por RMSE; en la ronda híbrida conviene evitar representaciones casi duplicadas y decidir con comparaciones pareadas.

## Advertencias

Los 18 scores globales de F2.2 no se usaron como predictores fijos. Las funciones beta resumen 50 outer folds; un pico aislado no se interpreta causalmente. Los benchmarks se reutilizaron, no se reentrenaron.
