# Climate Regime Extension — Stage R1

## Controles

Análisis target-free de 197 parcelas con exactamente 48 variables Climate Current de Familia 1. No se leyó rendimiento, errores OOF, satélite, topografía ni coordenadas para formar clusters. La geografía se utilizó sólo después de congelar la solución. Tras auditoría quedaron 48 variables; eliminaciones: ninguna. Hay 53 perfiles de fila exactamente distintos.

Missingness, escalas y distribuciones están en `climate_feature_audit.csv`; correlaciones en `climate_feature_correlations.csv`. Resumen de correlación: {'max_abs_correlation': np.float64(1.0000000000000002), 'pairs_abs_ge_0.90': 239, 'pairs_abs_ge_0.95': 151, 'pairs_abs_ge_0.99': 33}. La correlación moderada/alta no se utilizó para eliminar variables; PCA absorbió la redundancia.

## Respuestas

1. **¿Más de un régimen?** Sí, existe evidencia conjunta prometedora.
2. **K defendible:** K=2, covarianza `full`.
3. **Evidencia frente K=1:** mejora BIC de 524.14 puntos (positivo favorece K=2); AIC K1=3195.18, candidato=2628.36. No se decide por una diferencia mínima aislada.
4. **Estabilidad:** ARI bootstrap medio=0.756, correlación media de memberships=0.858, similitud de perfiles=1.000, convergencia=100.0% (50 resamples).
5. **Pertenencia clara:** hard/high-confidence por régimen: [{'regime': 1, 'hard_size': 147, 'high_confidence_hard_n': 147}, {'regime': 2, 'hard_size': 50, 'high_confidence_hard_n': 50}].
6. **Ambigüedad:** {'HIGH_CONFIDENCE_>0.90': 197}.
7. **Tamaños efectivos:** [{'regime': 1, 'effective_size': 147.0, 'hard_size': 147, 'potentially_small': False}, {'regime': 2, 'effective_size': 50.0, 'hard_size': 50, 'potentially_small': False}].
8. **Variables diferenciadoras:** rango máximo estandarizado entre regímenes: {'CLIMATE_tmax_mean_peak_day': 2.298, 'CLIMATE_dtr_mean_late_mean': 2.216, 'CLIMATE_dtr_mean_mid_mean': 2.194, 'CLIMATE_dtr_mean_median': 2.189, 'CLIMATE_dtr_mean_min': 2.188, 'CLIMATE_dtr_mean_mean': 2.16, 'CLIMATE_tmean_mean_max': 2.135, 'CLIMATE_dtr_mean_max': 2.135, 'CLIMATE_tmin_mean_min': 2.13, 'CLIMATE_dtr_mean_early_mean': 2.082, 'CLIMATE_tmin_mean_early_mean': 2.077, 'CLIMATE_tmean_mean_std': 2.063}.
9. **Precipitación mensual:** perfiles completos en `monthly_regime_profiles.csv`; resumen Apr–Oct: {1: {'precip_total': 949.962, 'tmean_average': 18.418, 'dtr_average': 10.479}, 2: {'precip_total': 999.811, 'tmean_average': 17.868, 'dtr_average': 11.703}}.
10. **Temperatura y DTR:** el mismo resumen reporta Tmean/DTR y las figuras muestran Tmin/Tmax/Tmean/DTR por mes.
11. **Naturaleza de clusters:** se interpreta por la combinación de precipitación total/timing y temperatura/DTR indicada por los perfiles; no se asignan nombres agronómicos fuertes.
12. **Estructura espacial post hoc:** concordancia observada con 6 vecinos=1.000, referencia permutada=0.619, p descriptivo=0.001. Distribución por CONJUNTO: {1: {'ENTRENAMIENTO': 103, 'PREDICCION': 44}, 2: {'ENTRENAMIENTO': 35, 'PREDICCION': 15}}. Es un diagnóstico posterior y no intervino en clustering.
13. **GMM vs K-means:** ARI=0.916; macroestructura semejante.
14. **Uso predictivo futuro:** la solución es suficientemente robusta para congelar memberships como candidatos target-free, todavía sin afirmar valor predictivo.
15. **Avance a R2:** Sí, puede avanzarse a caracterización con la solución congelada y sin redefinirla usando yield.

## PCA y selección

PCs para 80/90/95%: 3/3/3. GMM se ajustó sobre 3 PCs. Se evaluaron exclusivamente K=1..5 y covarianzas diagonal, tied y full con `reg_covar=1e-5`. Se excluyó de la selección toda solución que alcanzara el piso de covarianza; permanece en la tabla para auditoría. La tabla documenta likelihood, parámetros, convergencia, singularidad, BIC, AIC, silhouette, entropía y tamaños.

## Stop condition

No se abrió rendimiento, no se entrenaron modelos predictivos, no se ejecutó mixture-of-experts y no se inició Stage R2.
