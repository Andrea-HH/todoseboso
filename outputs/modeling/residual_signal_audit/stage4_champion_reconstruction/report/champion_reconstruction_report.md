# RS4 — Champion Reconstruction

## Controles
Mismos 50 outer folds (5×10) e inner CV 4-fold. Los targets residuales de outer-train se generaron con predicciones inner-OOF; TOP20 se re-rankeó dentro de cada inner-train. El bloque fuente Sentinel Historical tiene 24 columnas pre-2025; se excluyeron sus 8 `months` constantes, dejando 16 variables efectivas. No se usó Planet, Topography, clustering, MoE, RS5 ni predicción final.

## Respuestas
1. **Reproducción original:** CLIMATE_ENET+History24 RMSE=0.4942, frente a ~0.4941 esperado.
2. **Precipitation+History:** RMSE=0.4910; delta matched=-0.0118; wins=76%; repeticiones=10/10.
3. **TOP20+History:** RMSE=0.4896; delta matched=-0.0156; wins=78%; repeticiones=10/10.
4. **Mejor total:** TOP20_ENET_HISTORY15, RMSE=0.4895.
5. **Valor incremental post-refinamiento:** sí para precipitación; sí para TOP20.
6. **Ganancia History conservada:** precipitación=74.2%; TOP20=98.1% de la ganancia original (magnitud, sólo si delta negativo).
7. **Folds:** original=80%, precip=76%, TOP20=78%.
8. **Repeticiones:** original=10, precip=10, TOP20=10 de 10.
9. **Errores compartidos:** `residual_correlation_summary.csv` compara antes/después y reducción de varianza/|residual|.
10. **Difficult parcels:** {'CLIMATE_ENET_HISTORY24': {'mean_MAE': np.float64(0.811), 'proportion_improved': np.float64(0.786)}, 'PRECIPITATION_XGB_HISTORY24': {'mean_MAE': np.float64(0.767), 'proportion_improved': np.float64(0.786)}, 'TOP20_ENET_HISTORY24': {'mean_MAE': np.float64(0.804), 'proportion_improved': np.float64(0.786)}}.
11. **y-atypical:** {'CLIMATE_ENET_HISTORY24': {'mean_MAE': np.float64(1.188), 'proportion_improved': np.float64(0.778)}, 'PRECIPITATION_XGB_HISTORY24': {'mean_MAE': np.float64(1.163), 'proportion_improved': np.float64(0.778)}, 'TOP20_ENET_HISTORY24': {'mean_MAE': np.float64(1.197), 'proportion_improved': np.float64(0.778)}}.
12. **LOW/MID/HIGH del campeón:** [{'segment': 'LOW', 'RMSE': 0.688, 'MAE': 0.437, 'bias': 0.378}, {'segment': 'MID', 'RMSE': 0.364, 'MAE': 0.279, 'bias': -0.015}, {'segment': 'HIGH', 'RMSE': 0.479, 'MAE': 0.399, 'bias': -0.396}]; no se usaron segmentos para selección.
13. **Calibración:** beta base TOP20=0.631; beta campeón=0.671; History reduce compresión, aunque beta permanece <1.
14. **Residual vs directa:** [{'baseline': 'TOP20_ENET', 'architecture': 'residual24', 'pipeline': 'TOP20_ENET_HISTORY24', 'RMSE': 0.4896, 'mean_delta_RMSE': -0.0156, 'fold_win_rate': 0.78, 'repetitions_improved': 10}, {'baseline': 'PRECIPITATION_XGB', 'architecture': 'residual24', 'pipeline': 'PRECIPITATION_XGB_HISTORY24', 'RMSE': 0.491, 'mean_delta_RMSE': -0.0118, 'fold_win_rate': 0.76, 'repetitions_improved': 10}, {'baseline': 'CLIMATE_ENET', 'architecture': 'residual24', 'pipeline': 'CLIMATE_ENET_HISTORY24', 'RMSE': 0.4942, 'mean_delta_RMSE': -0.0159, 'fold_win_rate': 0.8, 'repetitions_improved': 10}, {'baseline': 'TOP20_ENET', 'architecture': 'direct24', 'pipeline': 'TOP20_ENET_DIRECT_HISTORY24', 'RMSE': 0.5053, 'mean_delta_RMSE': 0.0, 'fold_win_rate': 0.54, 'repetitions_improved': 6}, {'baseline': 'PRECIPITATION_XGB', 'architecture': 'direct24', 'pipeline': 'PRECIPITATION_XGB_DIRECT_HISTORY24', 'RMSE': 0.509, 'mean_delta_RMSE': 0.0063, 'fold_win_rate': 0.44, 'repetitions_improved': 3}].
15. **Necesidad del bloque completo efectivo:** [{'baseline': 'TOP20_ENET', 'architecture': 'residual15', 'pipeline': 'TOP20_ENET_HISTORY15', 'RMSE': 0.4895, 'mean_delta_RMSE': -0.0157, 'fold_win_rate': 0.76, 'repetitions_improved': 10}, {'baseline': 'TOP20_ENET', 'architecture': 'residual24', 'pipeline': 'TOP20_ENET_HISTORY24', 'RMSE': 0.4896, 'mean_delta_RMSE': -0.0156, 'fold_win_rate': 0.78, 'repetitions_improved': 10}, {'baseline': 'PRECIPITATION_XGB', 'architecture': 'residual15', 'pipeline': 'PRECIPITATION_XGB_HISTORY15', 'RMSE': 0.4903, 'mean_delta_RMSE': -0.0125, 'fold_win_rate': 0.76, 'repetitions_improved': 10}, {'baseline': 'PRECIPITATION_XGB', 'architecture': 'residual24', 'pipeline': 'PRECIPITATION_XGB_HISTORY24', 'RMSE': 0.491, 'mean_delta_RMSE': -0.0118, 'fold_win_rate': 0.76, 'repetitions_improved': 10}, {'baseline': 'CLIMATE_ENET', 'architecture': 'residual24', 'pipeline': 'CLIMATE_ENET_HISTORY24', 'RMSE': 0.4942, 'mean_delta_RMSE': -0.0159, 'fold_win_rate': 0.8, 'repetitions_improved': 10}, {'baseline': 'CLIMATE_ENET', 'architecture': 'residual15', 'pipeline': 'CLIMATE_ENET_HISTORY15', 'RMSE': 0.4947, 'mean_delta_RMSE': -0.0155, 'fold_win_rate': 0.8, 'repetitions_improved': 10}].
16. **TOP15:** iguala prácticamente a las 16 variables efectivas y es ligeramente mejor en TOP20/Precipitation; diferencia mínima, por lo que se favorece como opción compacta.
17. **Best performance:** TOP20_ENET_HISTORY15.
18. **Best compact:** PRECIPITATION_XGB_HISTORY15, RMSE=0.4903.
19. **Benchmark RS5 recomendado:** TOP20_ENET_HISTORY15; mantener PRECIPITATION_XGB_HISTORY15 como alternativa compacta.
20. **Preparación para RS5:** sí desde el punto de vista técnico, pero RS5 no fue iniciado.
