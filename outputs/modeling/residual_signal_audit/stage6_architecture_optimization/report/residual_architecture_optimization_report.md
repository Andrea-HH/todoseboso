# RS6 — Residual Architecture Optimization

## Controles
Sólo siete arquitecturas predefinidas, mismos 50 outer folds e inner 4-fold. Residuales de cada capa se generaron cross-fitted dentro de outer-train; A reutiliza residual2 nested de RS5 para reproducibilidad. Sin nuevas fuentes salvo la sensibilidad conjunta Topography+Planet, sin clustering, MoE, entrenamiento final o PREDICTION.

## Respuestas
1. **Reproducción A:** RMSE=0.4865.
2–3. **Orden:** A=0.4865; B Topo→History=0.4906, delta=+0.0041.
4–5. **Joint H+T:** Ridge=0.4984; XGB=0.4915; secuencial A=0.4865.
6. **History2:** RMSE=0.4868, delta=+0.0003, wins=40%; no conservar.
7. **Planet conjunto:** E1 Ridge=0.5824; E2 XGB=0.4883.
8–11. **Menor RMSE:** A_CURRENT_CH_H_T=0.4865; delta=+0.0000; wins=0%; repeticiones=0/10.
12. **Difficult parcels:** {'A_CURRENT_CH_H_T': {'mean_abs_error': 0.786, 'median_abs_error': 0.653, 'prop_improved': 0.0, 'largest_gain': 0.0, 'largest_deterioration': 0.0}, 'B_REVERSED_CT_H': {'mean_abs_error': 0.8, 'median_abs_error': 0.739, 'prop_improved': 0.357, 'largest_gain': 0.115, 'largest_deterioration': -0.154}, 'C1_JOINT_HT_RIDGE': {'mean_abs_error': 0.833, 'median_abs_error': 0.699, 'prop_improved': 0.321, 'largest_gain': 0.1, 'largest_deterioration': -0.305}, 'C2_JOINT_HT_XGB': {'mean_abs_error': 0.819, 'median_abs_error': 0.766, 'prop_improved': 0.286, 'largest_gain': 0.062, 'largest_deterioration': -0.283}, 'D_CH_T_H2': {'mean_abs_error': 0.778, 'median_abs_error': 0.631, 'prop_improved': 0.607, 'largest_gain': 0.063, 'largest_deterioration': -0.035}, 'E1_CH_JOINT_TP_RIDGE': {'mean_abs_error': 0.833, 'median_abs_error': 0.657, 'prop_improved': 0.321, 'largest_gain': 0.404, 'largest_deterioration': -0.387}, 'E2_CH_JOINT_TP_XGB': {'mean_abs_error': 0.784, 'median_abs_error': 0.675, 'prop_improved': 0.464, 'largest_gain': 0.231, 'largest_deterioration': -0.221}}.
13. **y-atypical mean gain vs A:** {'A_CURRENT_CH_H_T': 0.0, 'B_REVERSED_CT_H': -0.006, 'C1_JOINT_HT_RIDGE': -0.039, 'C2_JOINT_HT_XGB': -0.01, 'D_CH_T_H2': 0.014, 'E1_CH_JOINT_TP_RIDGE': -0.074, 'E2_CH_JOINT_TP_XGB': 0.002}.
14–15. **LOW/HIGH del mejor:** [{'segment': 'LOW', 'RMSE': 0.684, 'MAE': 0.437, 'bias': 0.375}, {'segment': 'MID', 'RMSE': 0.373, 'MAE': 0.286, 'bias': -0.005}, {'segment': 'HIGH', 'RMSE': 0.45, 'MAE': 0.387, 'bias': -0.38}].
16. **Mejor calibración:** D_CH_T_H2, slope=0.692.
17. **Menor complejidad en empate práctico:** A_CURRENT_CH_H_T.
18. **Practical ties |Δ|<0.0015:** ['A_CURRENT_CH_H_T', 'D_CH_T_H2']; residuales corr>0.98=[('A_CURRENT_CH_H_T', 'B_REVERSED_CT_H', np.float64(0.996)), ('A_CURRENT_CH_H_T', 'C1_JOINT_HT_RIDGE', np.float64(0.985)), ('A_CURRENT_CH_H_T', 'C2_JOINT_HT_XGB', np.float64(0.988)), ('A_CURRENT_CH_H_T', 'D_CH_T_H2', np.float64(0.998)), ('B_REVERSED_CT_H', 'C1_JOINT_HT_RIDGE', np.float64(0.986)), ('B_REVERSED_CT_H', 'C2_JOINT_HT_XGB', np.float64(0.989)), ('B_REVERSED_CT_H', 'D_CH_T_H2', np.float64(0.997)), ('C1_JOINT_HT_RIDGE', 'C2_JOINT_HT_XGB', np.float64(0.986)), ('C1_JOINT_HT_RIDGE', 'D_CH_T_H2', np.float64(0.98)), ('C2_JOINT_HT_XGB', 'D_CH_T_H2', np.float64(0.986))].
19. **Best performance:** A_CURRENT_CH_H_T, RMSE=0.4865.
20. **Best parsimonious:** A_CURRENT_CH_H_T, RMSE=0.4865.
21. **¿Mantener secuencial actual?** sí.
22. **Consolidación final:** técnicamente lista con máximo estas dos candidatas; no se ejecutó entrenamiento final.
