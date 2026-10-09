# Familia 1 — Etapa 4.1 diagnóstica

No se ejecutaron modelos de Ronda 2 ni se modificaron resultados de Etapa 4. La correlación general usa exclusivamente las 138 parcelas TRAIN; cualquier pruning futuro deberá reaprenderse dentro de cada train fold.

## Correlación y pruning

Pares por threshold: [{'threshold': 0.8, 'n_pairs': 6419, 'pct_pairs': 0.7007787279430469}, {'threshold': 0.85, 'n_pairs': 4180, 'pct_pairs': 0.45634134332480697}, {'threshold': 0.9, 'n_pairs': 2564, 'pct_pairs': 0.2799184699245945}, {'threshold': 0.92, 'n_pairs': 1931, 'pct_pairs': 0.21081223300483307}, {'threshold': 0.95, 'n_pairs': 1132, 'pct_pairs': 0.12358334943628745}, {'threshold': 0.97, 'n_pairs': 652, 'pct_pairs': 0.07118051575305602}, {'threshold': 0.98, 'n_pairs': 416, 'pct_pairs': 0.0454157891921339}, {'threshold': 0.99, 'n_pairs': 191, 'pct_pairs': 0.02085196090311917}].

Sensibilidad: [{'threshold': 0.85, 'features_retained': 590, 'features_removed': 764, 'pct_reduced': 56.425406203840474, 'n_correlated_components': 146, 'largest_component_size': 243, 'median_component_size': 2.5, 'q90_component_size': 8.0, 'features_in_correlated_components': 1086, 'delta_retained_vs_previous_threshold': nan}, {'threshold': 0.9, 'features_retained': 716, 'features_removed': 638, 'pct_reduced': 47.11964549483013, 'n_correlated_components': 197, 'largest_component_size': 76, 'median_component_size': 2.0, 'q90_component_size': 8.0, 'features_in_correlated_components': 958, 'delta_retained_vs_previous_threshold': 126.0}, {'threshold': 0.92, 'features_retained': 782, 'features_removed': 572, 'pct_reduced': 42.24519940915805, 'n_correlated_components': 209, 'largest_component_size': 59, 'median_component_size': 2.0, 'q90_component_size': 7.0, 'features_in_correlated_components': 891, 'delta_retained_vs_previous_threshold': 66.0}, {'threshold': 0.95, 'features_retained': 918, 'features_removed': 436, 'pct_reduced': 32.20088626292467, 'n_correlated_components': 221, 'largest_component_size': 49, 'median_component_size': 2.0, 'q90_component_size': 6.0, 'features_in_correlated_components': 729, 'delta_retained_vs_previous_threshold': 136.0}, {'threshold': 0.97, 'features_retained': 1047, 'features_removed': 307, 'pct_reduced': 22.673559822747414, 'n_correlated_components': 187, 'largest_component_size': 44, 'median_component_size': 2.0, 'q90_component_size': 4.0, 'features_in_correlated_components': 538, 'delta_retained_vs_previous_threshold': 129.0}, {'threshold': 0.98, 'features_retained': 1124, 'features_removed': 230, 'pct_reduced': 16.986706056129986, 'n_correlated_components': 163, 'largest_component_size': 40, 'median_component_size': 2.0, 'q90_component_size': 3.0, 'features_in_correlated_components': 423, 'delta_retained_vs_previous_threshold': 77.0}, {'threshold': 0.99, 'features_retained': 1231, 'features_removed': 123, 'pct_reduced': 9.084194977843428, 'n_correlated_components': 94, 'largest_component_size': 11, 'median_component_size': 2.0, 'q90_component_size': 3.0, 'features_in_correlated_components': 226, 'delta_retained_vs_previous_threshold': 107.0}].

El mayor salto en retención entre thresholds consecutivos fue 136 features. La evolución del mayor componente permite detectar el chain effect: [{'threshold': 0.85, 'largest_component_size': 243, 'largest_share_pct': 17.95}, {'threshold': 0.9, 'largest_component_size': 76, 'largest_share_pct': 5.61}, {'threshold': 0.92, 'largest_component_size': 59, 'largest_share_pct': 4.36}, {'threshold': 0.95, 'largest_component_size': 49, 'largest_share_pct': 3.62}, {'threshold': 0.97, 'largest_component_size': 44, 'largest_share_pct': 3.25}, {'threshold': 0.98, 'largest_component_size': 40, 'largest_share_pct': 2.95}, {'threshold': 0.99, 'largest_component_size': 11, 'largest_share_pct': 0.81}].

No se elige threshold ganador. Se recomiendan **[0.9, 0.95, 0.98]** para nested CV: 0.90 como pruning fuerte, 0.95 intermedio y 0.98 conservador/referencia actual.

## Interpretación PLS

VIP implementado como `sqrt(p * sum_a(SSY_a * (w_ja/||w_a||)^2) / sum_a SSY_a)`, con `SSY_a = sum(t_a^2) * q_a^2`. La verificación numérica exige `mean(VIP^2)=1`; error máximo observado=1.776e-15.

Contribuciones dominantes por fuente y componente: [{'pipeline': 'PLS_ALL', 'group': 'Sentinel', 'component_1_contribution_pct': 47.31, 'component_2_contribution_pct': 56.83}, {'pipeline': 'PLS_ALL', 'group': 'Planet', 'component_1_contribution_pct': 17.45, 'component_2_contribution_pct': 22.63}, {'pipeline': 'PLS_ALL', 'group': 'Anomaly', 'component_1_contribution_pct': 10.97, 'component_2_contribution_pct': 6.68}, {'pipeline': 'PLS_CORE', 'group': 'Sentinel', 'component_1_contribution_pct': 41.03, 'component_2_contribution_pct': 51.03}, {'pipeline': 'PLS_CORE', 'group': 'Planet', 'component_1_contribution_pct': 21.7, 'component_2_contribution_pct': 27.7}, {'pipeline': 'PLS_CORE', 'group': 'Anomaly', 'component_1_contribution_pct': 14.04, 'component_2_contribution_pct': 9.07}].

Familias temporales con VIP agregado más alto: timing, histórico, peak y anomalía. La categoría timing contiene sólo una feature y no debe generalizarse sin considerar ese tamaño.

La estructura macro se repite en CORE y ALL. En contribución total, PLS1 combina satélite con más peso relativo de clima, anomalía e histórico; PLS2 se concentra todavía más en Sentinel/Planet y en heterogeneidad/AUC. Sentinel domina la suma porque contiene muchas columnas, mientras Climate presenta el VIP promedio por feature más alto: 1.792 en CORE y 2.053 en ALL.

Las features climáticas y anomalías climáticas encabezan el ranking estable. Algunas variables CORE cambian más en magnitud o signo del segundo loading, pero las fuentes y familias son más estables. Esto favorece interpretar constructos agregados y no convertir VIP en selector automático.

PLS1 y PLS2 son diferenciables cuando sus rankings agregados divergen; consultar `pls_component_loadings_summary.csv`. La estabilidad debe interpretarse a nivel familia además de feature individual. `VIP>1` es sólo descriptor y no regla de selección.

La figura PLS usa únicamente scores de validation transformados por modelos ajustados en el outer train correspondiente. El rendimiento sólo colorea puntos y no ajusta una transformación nueva.

## Ajuste recomendado del grid de Ronda 2

- Probar thresholds 0.90, 0.95 y 0.98 dentro del inner CV para XGB/LGBM/ElasticNet PRUNED.
- Mantener la regla determinística: menor missingness, CORE antes que EXTENDED y desempate lexicográfico.
- No utilizar VIP para filtrar features en Ronda 2; usarlo únicamente para interpretación posterior.
- No ampliar PLS por encima de la pequeña rejilla actual: los resultados previos favorecen dos componentes.
