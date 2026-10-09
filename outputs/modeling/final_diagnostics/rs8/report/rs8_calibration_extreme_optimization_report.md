# RS8 — Calibration and Extreme-Aware Optimization

## Resultado
Clasificación: **NEITHER**. Se preservaron fuentes, orden y 50 outer folds; calibradores y pesos se aprendieron sólo dentro de outer-train. No hubo PREDICTION ni entrenamiento final.

## Respuestas
1. Champion reproducido: fold RMSE=0.4865; parcel RMSE=0.4903.
2–11. Mejor calibración: CAL_ISOTONIC; parcel RMSE=0.4876, delta=-0.0026, fold wins=50%, repeticiones=6/10, slope=0.689→0.680, range=0.677→0.637. Tabla completa compara linear, expansion, isotonic y splines. Éxito=False.
12–18. Weighting: RMSE=0.4931, delta=+0.0029, fold wins=36%, repeticiones=2/10. Threshold/lambda/capas seleccionados por fold están en `selected_weights.csv`; LOW/HIGH/EXTREME10 en `extreme_segment_metrics.csv`. Éxito=False.
19. Concentración SSE: [{'model': 'BASE_CHAMPION', 'top5_SSE': 0.459, 'top10_SSE': 0.598, 'top20_SSE': 0.757, 'difficult_SSE': 0.697, 'yatypical_SSE': 0.458}, {'model': 'BEST_WEIGHTING', 'top5_SSE': 0.462, 'top10_SSE': 0.597, 'top20_SSE': 0.758, 'difficult_SSE': 0.687, 'yatypical_SSE': 0.457}, {'model': 'CAL_ISOTONIC', 'top5_SSE': 0.47, 'top10_SSE': 0.611, 'top20_SSE': 0.766, 'difficult_SSE': 0.727, 'yatypical_SSE': 0.482}].
20. Huber/pseudo-Huber: ver `robust_loss_metrics.csv`; es sensibilidad porque robustificar puede ignorar extremos verdaderos.
21. Complementariedad: NEITHER; combined no se ejecutó salvo doble éxito y no se aproximó con calibración global.
22–27. Menor RMSE: CAL_ISOTONIC=0.4876; R²=0.669, MAE=0.339, slope=0.680, range=0.637, Spearman=0.719.
28–29. y-atypical/difficult: comparar columnas homónimas de `sse_concentration.csv`.
30. **Best predictive seleccionado:** BASE_CHAMPION. Isotonic tuvo el menor RMSE agregado, pero no cumplió estabilidad fold/repetición ni mejoró calibración.
31. Alternativa interpretable: BASE_CHAMPION.
32. **Reemplazar champion:** no; ninguna intervención cumplió los criterios de promoción.
33. Consolidar.
