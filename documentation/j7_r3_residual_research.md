# Investigación de residuos: J7 y J7 + corrector global R3

Se conservan las 138 respuestas y 65 folds. Cada modelo tiene 1,794 OOF: 10 repeticiones aleatorias y una evaluación completa por perfil, municipal y espacial. Son 138 parcelas, no 1,794 observaciones independientes. Error = predicho − observado; positivo es sobreestimación. Las métricas se calculan por OOF completa de cada repetición y luego se promedian. No se ajustó ningún calibrador sobre las OOF externas.

## Métricas globales

| experiment | protocol | rmse | r2 | mae | bias | p95_absolute | within_05 | calibration_slope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| J7_BOTH | climate_profile | 0.4890 | 0.6675 | 0.3445 | -0.0139 | 0.9172 | 0.7609 | 1.0138 |
| J7_BOTH | municipality | 0.5808 | 0.5309 | 0.4604 | -0.0205 | 1.0790 | 0.6884 | 1.1388 |
| J7_BOTH | random | 0.4864 | 0.6709 | 0.3470 | -0.0121 | 0.8553 | 0.7616 | 0.9958 |
| J7_BOTH | spatial | 0.6808 | 0.3556 | 0.5291 | 0.2913 | 1.4279 | 0.5580 | 1.2907 |
| J7_GLOBAL_R3 | climate_profile | 0.4748 | 0.6865 | 0.3346 | -0.0089 | 0.8777 | 0.7609 | 1.0113 |
| J7_GLOBAL_R3 | municipality | 0.5726 | 0.5442 | 0.4441 | -0.0412 | 1.0794 | 0.6812 | 1.0782 |
| J7_GLOBAL_R3 | random | 0.4756 | 0.6854 | 0.3408 | -0.0077 | 0.8214 | 0.7674 | 0.9914 |
| J7_GLOBAL_R3 | spatial | 0.6550 | 0.4035 | 0.5198 | 0.2210 | 1.3240 | 0.5362 | 1.1902 |

## Qué hace la corrección

| protocol | mean_correction | mean_absolute_correction | fraction_helped | fraction_harmed | fraction_zero | fraction_cap | base_bias | corrected_bias | bias_squared_gain | error_variance_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| climate_profile | 0.0050 | 0.0538 | 0.5435 | 0.4565 | 0.0000 | 0.0072 | -0.0139 | -0.0089 | 0.0001 | 0.0136 |
| municipality | -0.0207 | 0.0315 | 0.2029 | 0.0942 | 0.7029 | 0.0217 | -0.0205 | -0.0412 | -0.0013 | 0.0108 |
| random | 0.0043 | 0.0512 | 0.5159 | 0.4841 | 0.0000 | 0.0029 | -0.0121 | -0.0077 | 0.0001 | 0.0103 |
| spatial | -0.0703 | 0.1032 | 0.5362 | 0.4638 | 0.0000 | 0.0870 | 0.2913 | 0.2210 | 0.0360 | -0.0016 |

En aleatoria mejora 51.6% de las predicciones individuales y perjudica 48.4%; el cambio absoluto medio es .0512 t/ha. Esto no es una mejora uniforme. En municipal 70.3% queda sin cambio porque la selección interna apaga la corrección en tres de los cinco folds. La ganancia municipal no se distribuye entre todos los municipios: Puebla/Chignahuapan queda exactamente igual.

En espacial reduce el sesgo +.2913→+.2210. La reducción de sesgo al cuadrado aporta .0360 (t/ha)²; la varianza del error aumenta .0016. Por tanto, allí mejora fundamentalmente el nivel medio y no la dispersión. En aleatoria/perfil la ganancia procede principalmente de menor varianza del error. En municipal aumenta la magnitud del sesgo global negativo, aunque baja RMSE/MAE: sesgo y precisión no son equivalentes.

La cola espacial mejora: percentil95 absoluto 1.4279→1.3240, pero la proporción dentro de ±.5 t/ha cae 55.8%→53.6%. En aleatoria ese umbral mejora sólo 76.2%→76.7%. R3 reduce algunos errores grandes y empeora algunos moderados; su menor RMSE no implica que la mayoría de las parcelas quede más cerca dentro de cualquier tolerancia.

## Cuartiles de rendimiento observado

| experiment | protocol | zone | n | rmse | r2 | mae | bias |
| --- | --- | --- | --- | --- | --- | --- | --- |
| J7_BOTH | climate_profile | (1.999, 3.2] | 36.0000 | 0.6697 | -4.0286 | 0.4438 | 0.3729 |
| J7_BOTH | climate_profile | (3.2, 4.34] | 33.0000 | 0.4779 | -1.5307 | 0.4071 | -0.0011 |
| J7_BOTH | climate_profile | (4.34, 4.55] | 35.0000 | 0.1301 | -5.1968 | 0.1059 | -0.0253 |
| J7_BOTH | climate_profile | (4.55, 5.59] | 34.0000 | 0.5067 | -1.5613 | 0.4241 | -0.4241 |
| J7_BOTH | municipality | (1.999, 3.2] | 36.0000 | 0.8089 | -6.3360 | 0.6404 | 0.6004 |
| J7_BOTH | municipality | (3.2, 4.34] | 33.0000 | 0.4516 | -1.2603 | 0.3682 | 0.0509 |
| J7_BOTH | municipality | (4.34, 4.55] | 35.0000 | 0.3005 | -32.0326 | 0.2673 | -0.2044 |
| J7_BOTH | municipality | (4.55, 5.59] | 34.0000 | 0.6210 | -2.8482 | 0.5580 | -0.5580 |
| J7_BOTH | random | (1.999, 3.2] | 36.0000 | 0.6648 | -3.9580 | 0.4110 | 0.3710 |
| J7_BOTH | random | (3.2, 4.34] | 33.0000 | 0.4723 | -1.4735 | 0.4050 | -0.0132 |
| J7_BOTH | random | (4.34, 4.55] | 35.0000 | 0.2006 | -13.7554 | 0.1598 | -0.0177 |
| J7_BOTH | random | (4.55, 5.59] | 34.0000 | 0.4837 | -1.3367 | 0.4158 | -0.4108 |
| J7_BOTH | spatial | (1.999, 3.2] | 36.0000 | 1.1198 | -13.0601 | 1.0269 | 1.0247 |
| J7_BOTH | spatial | (3.2, 4.34] | 33.0000 | 0.5535 | -2.3955 | 0.5023 | 0.3884 |
| J7_BOTH | spatial | (4.34, 4.55] | 35.0000 | 0.2508 | -22.0141 | 0.2118 | 0.0394 |
| J7_BOTH | spatial | (4.55, 5.59] | 34.0000 | 0.4374 | -0.9090 | 0.3546 | -0.3201 |
| J7_GLOBAL_R3 | climate_profile | (1.999, 3.2] | 36.0000 | 0.6494 | -3.7279 | 0.4292 | 0.3466 |
| J7_GLOBAL_R3 | climate_profile | (3.2, 4.34] | 33.0000 | 0.4590 | -1.3351 | 0.3950 | 0.0184 |
| J7_GLOBAL_R3 | climate_profile | (4.34, 4.55] | 35.0000 | 0.1605 | -8.4237 | 0.1253 | -0.0295 |
| J7_GLOBAL_R3 | climate_profile | (4.55, 5.59] | 34.0000 | 0.4875 | -1.3709 | 0.3915 | -0.3905 |
| J7_GLOBAL_R3 | municipality | (1.999, 3.2] | 36.0000 | 0.7792 | -5.8080 | 0.5740 | 0.5250 |
| J7_GLOBAL_R3 | municipality | (3.2, 4.34] | 33.0000 | 0.4661 | -1.4078 | 0.3800 | 0.0391 |
| J7_GLOBAL_R3 | municipality | (4.34, 4.55] | 35.0000 | 0.2959 | -31.0354 | 0.2608 | -0.1979 |
| J7_GLOBAL_R3 | municipality | (4.55, 5.59] | 34.0000 | 0.6219 | -2.8588 | 0.5575 | -0.5575 |
| J7_GLOBAL_R3 | random | (1.999, 3.2] | 36.0000 | 0.6469 | -3.6953 | 0.4070 | 0.3526 |
| J7_GLOBAL_R3 | random | (3.2, 4.34] | 33.0000 | 0.4612 | -1.3586 | 0.3966 | -0.0031 |
| J7_GLOBAL_R3 | random | (4.34, 4.55] | 35.0000 | 0.2231 | -17.2357 | 0.1715 | -0.0181 |
| J7_GLOBAL_R3 | random | (4.55, 5.59] | 34.0000 | 0.4659 | -1.1674 | 0.3908 | -0.3830 |
| J7_GLOBAL_R3 | spatial | (1.999, 3.2] | 36.0000 | 1.0317 | -10.9351 | 0.9368 | 0.9326 |
| J7_GLOBAL_R3 | spatial | (3.2, 4.34] | 33.0000 | 0.5073 | -1.8525 | 0.4473 | 0.3215 |
| J7_GLOBAL_R3 | spatial | (4.34, 4.55] | 35.0000 | 0.3337 | -39.7309 | 0.2666 | -0.0319 |
| J7_GLOBAL_R3 | spatial | (4.55, 5.59] | 34.0000 | 0.4998 | -1.4925 | 0.4094 | -0.3696 |

La corrección mejora el cuartil bajo en los cuatro protocolos. En espacial su RMSE baja 1.1198→1.0317, pero el sesgo sigue siendo +.9326 t/ha. Empeora los cuartiles altos espaciales: tercero .2508→.3337 y cuarto .4374→.4998. En aleatoria el tercero también empeora .2006→.2231; el superior mejora .4837→.4659. El modelo todavía comprime extremos. Estos cuartiles se definen usando la respuesta observada: son diagnóstico, nunca una regla utilizable al predecir. R² de grupos estrechos no es comparable con R² global.

## Estados y transferencia territorial

| experiment | protocol | zone | n | rmse | r2 | mae | bias |
| --- | --- | --- | --- | --- | --- | --- | --- |
| J7_BOTH | climate_profile | Hidalgo | 36.0000 | 0.3505 | 0.7910 | 0.2626 | -0.0179 |
| J7_BOTH | climate_profile | Puebla | 71.0000 | 0.5625 | 0.0602 | 0.3732 | -0.0149 |
| J7_BOTH | climate_profile | Tlaxcala | 31.0000 | 0.4441 | -0.4410 | 0.3738 | -0.0069 |
| J7_BOTH | municipality | Hidalgo | 36.0000 | 0.6615 | 0.2558 | 0.5375 | 0.2164 |
| J7_BOTH | municipality | Puebla | 71.0000 | 0.5798 | 0.0015 | 0.4465 | -0.1983 |
| J7_BOTH | municipality | Tlaxcala | 31.0000 | 0.4731 | -0.6355 | 0.4025 | 0.1114 |
| J7_BOTH | random | Hidalgo | 36.0000 | 0.3678 | 0.7698 | 0.2715 | -0.0278 |
| J7_BOTH | random | Puebla | 71.0000 | 0.5626 | 0.0598 | 0.3928 | -0.0127 |
| J7_BOTH | random | Tlaxcala | 31.0000 | 0.4136 | -0.2520 | 0.3298 | 0.0077 |
| J7_BOTH | spatial | Hidalgo | 36.0000 | 0.6536 | 0.2733 | 0.5408 | 0.3002 |
| J7_BOTH | spatial | Puebla | 71.0000 | 0.5493 | 0.1040 | 0.3846 | 0.0928 |
| J7_BOTH | spatial | Tlaxcala | 31.0000 | 0.9361 | -5.4032 | 0.8463 | 0.7357 |
| J7_GLOBAL_R3 | climate_profile | Hidalgo | 36.0000 | 0.3410 | 0.8022 | 0.2582 | -0.0320 |
| J7_GLOBAL_R3 | climate_profile | Puebla | 71.0000 | 0.5502 | 0.1009 | 0.3646 | -0.0021 |
| J7_GLOBAL_R3 | climate_profile | Tlaxcala | 31.0000 | 0.4187 | -0.2810 | 0.3549 | 0.0024 |
| J7_GLOBAL_R3 | municipality | Hidalgo | 36.0000 | 0.6590 | 0.2612 | 0.5286 | 0.2211 |
| J7_GLOBAL_R3 | municipality | Puebla | 71.0000 | 0.5798 | 0.0015 | 0.4465 | -0.1983 |
| J7_GLOBAL_R3 | municipality | Tlaxcala | 31.0000 | 0.4302 | -0.3526 | 0.3405 | 0.0139 |
| J7_GLOBAL_R3 | random | Hidalgo | 36.0000 | 0.3642 | 0.7743 | 0.2728 | -0.0403 |
| J7_GLOBAL_R3 | random | Puebla | 71.0000 | 0.5512 | 0.0974 | 0.3829 | -0.0013 |
| J7_GLOBAL_R3 | random | Tlaxcala | 31.0000 | 0.3962 | -0.1492 | 0.3234 | 0.0155 |
| J7_GLOBAL_R3 | spatial | Hidalgo | 36.0000 | 0.6476 | 0.2866 | 0.5599 | 0.1743 |
| J7_GLOBAL_R3 | spatial | Puebla | 71.0000 | 0.5378 | 0.1409 | 0.3830 | 0.0451 |
| J7_GLOBAL_R3 | spatial | Tlaxcala | 31.0000 | 0.8720 | -4.5565 | 0.7867 | 0.6781 |

R² global aleatorio .6854 convive con .0974 dentro de Puebla y −.1492 dentro de Tlaxcala. Parte de la explicación global corresponde a diferencias entre estados; no demuestra ordenamiento preciso dentro de cada estado. Hidalgo conserva .7743. Los R² territoriales usan la media de evaluación de cada grupo como referencia descriptiva, no un baseline entrenable.

En espacial Almoloya empeora .3621→.5859, y la corrección es negativa en sus diez parcelas, donde J7 ya subestimaba. Singuilucan mejora .8247→.7384 y Chignahuapan .5493→.5378. Tlaxcala mejora, pero mantiene fuerte sobreestimación y R² negativo. Municipios con una o tres parcelas no permiten conclusiones sólidas; no se generan reglas regionales.

## Casos de mejora y deterioro (aleatoria)

| ID_POLIGONO | Municipio | y_true | base_error | corrected_error | correction | sse_gain |
| --- | --- | --- | --- | --- | --- | --- |
| AGC_160 | Chignahuapan | 3.6200 | 1.1328 | 1.1777 | 0.0450 | -0.1046 |
| AGC_047 | Tepeapulco | 4.4500 | -0.4778 | -0.5625 | -0.0847 | -0.0885 |
| AGC_119 | Cuautepec de Hinojosa | 4.4000 | 0.4234 | 0.5100 | 0.0867 | -0.0818 |
| AGC_197 | Chignahuapan | 4.5200 | -0.2485 | -0.3682 | -0.1196 | -0.0746 |
| AGC_032 | Chignahuapan | 4.0300 | 0.4030 | 0.4868 | 0.0838 | -0.0744 |
| AGC_015 | Chignahuapan | 2.6400 | 2.0800 | 1.9970 | -0.0829 | 0.3384 |
| AGC_005 | Chignahuapan | 5.1600 | -0.5106 | -0.3350 | 0.1756 | 0.1481 |
| AGC_041 | Singuilucan | 2.5000 | 0.6683 | 0.5487 | -0.1196 | 0.1438 |
| AGC_026 | Chignahuapan | 3.5500 | 0.8594 | 0.7726 | -0.0868 | 0.1406 |
| AGC_166 | Singuilucan | 2.5000 | 0.7614 | 0.6714 | -0.0899 | 0.1284 |

AGC_015 mejora de +2.0800 a +1.9970 t/ha: sigue siendo un error muy grande. No se resolvió la parcela por mejorar el agregado. El deterioro espacial más claro es AGC_152, de −.6468 a −.8968, por alcanzar el límite de corrección negativa. Se entregan cambios para las 138 parcelas, no sólo los casos destacados.

## Concentración, soporte e intraperfil

La auditoría previa de vecindarios muestra que R3 empeora RMSE aleatorio .0059 fuera de las 35 difíciles previamente definidas; la ganancia aleatoria se concentra allí. La ganancia espacial persiste al omitir cualquiera de los cinco bloques del cálculo, sin reentrenar, pero no elimina el daño de Almoloya. Las diferencias intraperfil con igual peso por perfil mejoran en aleatoria (.5777→.5697), por perfil (.5317→.5169) y espacial (.5320→.5198), pero municipal apenas empeora (.5257→.5262). Son errores de diferencias entre pares, no errores individuales.

Los mínimos históricos usan mayo–octubre 2022–2024 y la persistencia compara 2025 con esa historia. Hay 29 parcelas con historia incompleta; se imputan sólo con estadísticas del entrenamiento. La imputación no aporta la información faltante. Las correlaciones del archivo descriptive_associations son descriptivas, sin selección automática ni interpretación causal.

## Estabilidad de los coeficientes del corrector

| protocol | feature | mean | min | max |
| --- | --- | --- | --- | --- |
| climate_profile | I_gap_excess_persistence | 0.0938 | 0.0656 | 0.1142 |
| climate_profile | I_history_ndvi_floor | 0.0913 | 0.0702 | 0.1048 |
| climate_profile | I_slope_min | 0.0812 | 0.0696 | 0.1125 |
| municipality | I_gap_excess_persistence | 0.1663 | 0.1577 | 0.1749 |
| municipality | I_history_ndvi_floor | 0.0782 | 0.0718 | 0.0846 |
| municipality | I_slope_min | 0.0835 | 0.0720 | 0.0950 |
| random | I_gap_excess_persistence | 0.0913 | 0.0326 | 0.1418 |
| random | I_history_ndvi_floor | 0.0795 | 0.0401 | 0.1066 |
| random | I_slope_min | 0.0485 | 0.0202 | 0.0944 |
| spatial | I_gap_excess_persistence | 0.1554 | 0.1027 | 0.2398 |
| spatial | I_history_ndvi_floor | 0.0306 | -0.0327 | 0.0847 |
| spatial | I_slope_min | 0.1965 | 0.0954 | 0.3292 |

Los coeficientes describen residuos condicionales en escala estandarizada, antes de amplitud y recorte: no son efectos causales ni t/ha por unidad física original. En aleatoria los tres signos permanecen positivos en los 50 folds; en espacial el coeficiente de NDVI histórico cambia de signo entre folds. Pendiente y persistencia conservan signo positivo en los folds activos, pero con magnitudes variables. El signo del coeficiente no equivale al signo de la corrección total: también intervienen centrado, intercepto, las otras variables, amplitud y recorte.

## Incertidumbre y conclusión

| experiment | reference | protocol | delta_rmse | low95 | high95 | p_mse_signflip | n_clusters | exact_sign_enumeration | n_sign_assignments | p_holm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| J7_GLOBAL_R3 | J7_BOTH | climate_profile | -0.0142 | -0.0228 | -0.0064 | 0.0081 | 43 | False | 20000 | 0.2187 |
| J7_GLOBAL_R3 | J7_BOTH | municipality | -0.0083 | -0.0351 | 0.0000 | 0.2500 | 9 | True | 512 | 1.0000 |
| J7_GLOBAL_R3 | J7_BOTH | random | -0.0108 | -0.0172 | -0.0046 | 0.0245 | 43 | False | 20000 | 0.5390 |
| J7_GLOBAL_R3 | J7_BOTH | spatial | -0.0258 | -0.0585 | 0.0412 | 0.4375 | 5 | True | 32 | 1.0000 |

Los intervalos usan 5,000 remuestreos por conglomerados de OOF fijas; no incorporan toda la selección histórica ni incertidumbre de reajuste. Hay 43 perfiles TRAIN, nueve municipios y cinco bloques. Ningún contraste R3 vs J7 supera Holm en esta batería de 28 contrastes; tampoco lo hizo en la batería anterior de 208. No son intervalos predictivos individuales. R3 reduce errores agregados y corrige parcialmente sobreestimación territorial, pero no resuelve transferencia, extremos ni la mayoría de las parcelas difíciles.

Gráfica: outputs/research/j7_r3_residual_simplification/v1/figures/residual_comparison.png. Las gráficas aleatorias promedian predicciones por parcela únicamente para visualizar; las métricas no usan ese promedio.