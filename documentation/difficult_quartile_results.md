# Cuartil difícil y signo del error: resultados exploratorios

El inventario usa35parcelas por error OOF J7 original. Los clasificadores usan umbrales y etiquetas cross-fitted dentro del entrenamiento de cada fold, no la etiqueta global top35. No se entrenaron correctores de rendimiento.

## Composición

| group | n | yield_median | prediction_median | mean_error | mean_absolute_error | sse_share |
| --- | --- | --- | --- | --- | --- | --- |
| hard_over | 17 | 2.500 | 3.261 | 0.896 | 0.896 | 0.553 |
| hard_under | 18 | 4.860 | 4.250 | -0.664 | 0.664 | 0.255 |
| remaining | 103 | 4.410 | 4.290 | -0.048 | 0.201 | 0.192 |

| Municipio | n | hard_n | hard_fraction | hard_over | hard_under | low_yield_n |
| --- | --- | --- | --- | --- | --- | --- |
| Almoloya | 10 | 0 | 0.000 | 0 | 0 | 0 |
| Apan | 1 | 0 | 0.000 | 0 | 0 | 1 |
| Calpulalpan | 30 | 11 | 0.367 | 5 | 6 | 22 |
| Chignahuapan | 71 | 19 | 0.268 | 8 | 11 | 3 |
| Cuautepec de Hinojosa | 5 | 1 | 0.200 | 0 | 1 | 0 |
| Emiliano Zapata | 3 | 0 | 0.000 | 0 | 0 | 0 |
| Nanacamilpa de Mariano Arista | 1 | 1 | 1.000 | 1 | 0 | 1 |
| Singuilucan | 16 | 3 | 0.188 | 3 | 0 | 9 |
| Tepeapulco | 1 | 0 | 0.000 | 0 | 0 | 0 |

## Variables descriptivas con contraste dentro de municipio

| contrast | original_feature | family | median_a | median_b | cliffs_delta | municipal_equal_weight_delta | n_supported_municipalities | profile_equal_weight_delta | n_supported_profiles |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hard_over_vs_hard_under | sat_basic_2025__landsat__vi6t_max__mean | Otras señales | -0.599 | -0.606 | 0.314 | 0.684 | 2.000 | 0.958 | 3.000 |
| hard_over_vs_hard_under | S2_msi_derived_upper_gap_normalized_auc | Señal satelital de humedad | 0.307 | 0.259 | 0.582 | 0.618 | 2.000 | 0.808 | 3.000 |
| hard_over_vs_hard_under | TOPO_BASIC_slope_min | Relieve/topografía | 0.778 | 1.529 | -0.376 | -0.605 | 2.000 | -0.511 | 3.000 |
| hard_over_vs_hard_under | PLANET_lai_derived_range_std | Vegetación/heterogeneidad | 0.401 | 0.337 | 0.340 | 0.603 | 2.000 | 0.508 | 3.000 |
| hard_over_vs_hard_under | sat_basic_hist__landsat__vi6t_max__mean | Otras señales | -0.592 | -0.603 | 0.314 | 0.573 | 2.000 | 0.611 | 3.000 |
| hard_over_vs_hard_under | sat_basic_hist__sentinel_2__ndvi_max__std | Vegetación/heterogeneidad | 0.202 | 0.202 | 0.209 | 0.570 | 2.000 | 0.467 | 3.000 |
| hard_over_vs_hard_under | S2_nddi_derived_lower_gap_normalized_auc | Señal satelital de humedad | 0.063 | 0.051 | 0.386 | 0.561 | 2.000 | 0.750 | 3.000 |
| hard_over_vs_hard_under | TOPO_ADV_aspect_cos_max | Relieve/topografía | 0.970 | 0.754 | 0.301 | 0.502 | 2.000 | 0.642 | 3.000 |
| hard_over_vs_hard_under | geo250_share__UNKNOWN_OUTSIDE | Geología/fisiografía | 0.000 | 0.000 | 0.304 | 0.473 | 2.000 | 0.407 | 3.000 |
| hard_over_vs_hard_under | soilgrids__nitrogen__30_60cm__std | Suelo | 0.026 | 0.009 | 0.484 | 0.461 | 2.000 | 0.767 | 3.000 |
| hard_over_vs_hard_under | soilgrids__bdod__0_5cm__std | Suelo | 0.012 | 0.005 | 0.408 | 0.452 | 2.000 | 0.408 | 3.000 |
| hard_over_vs_hard_under | geo250_mapped_share | Geología/fisiografía | 1.000 | 1.000 | -0.206 | -0.421 | 2.000 | -0.319 | 3.000 |
| hard_over_vs_remaining | EXT_LOC_nearest_population | Geometría/contexto geográfico | 136.000 | 21.000 | 0.238 | 0.590 | 3.000 | 0.484 | 3.000 |
| hard_over_vs_remaining | emp_distribution__hist_s2_lai__mean_position_in_range | Vegetación/heterogeneidad | 0.236 | 0.212 | 0.362 | 0.533 | 3.000 | 0.583 | 3.000 |
| hard_over_vs_remaining | emp_distribution__hist_s2_ndvi__std_over_range | Vegetación/heterogeneidad | 0.276 | 0.261 | 0.457 | 0.530 | 3.000 | 0.295 | 3.000 |
| hard_over_vs_remaining | TOPO_ADV_aspect_sin_std | Relieve/topografía | 0.295 | 0.168 | 0.375 | 0.492 | 3.000 | 0.153 | 3.000 |
| hard_over_vs_remaining | sat_basic_hist_monthly__sentinel_2__ndti_promedio__m07 | Otras señales | 0.173 | 0.167 | 0.170 | 0.473 | 3.000 | 0.267 | 3.000 |
| hard_over_vs_remaining | soilgrids__nitrogen__5_15cm__mean | Suelo | 1.702 | 1.696 | 0.171 | 0.468 | 3.000 | 0.190 | 3.000 |
| hard_over_vs_remaining | TOPO_ADV_aspect_sin_iqr | Relieve/topografía | 0.295 | 0.178 | 0.347 | 0.467 | 3.000 | 0.220 | 3.000 |
| hard_over_vs_remaining | S2_nddi_derived_lower_gap_max_decline_rate | Señal satelital de humedad | -0.028 | -0.022 | -0.199 | -0.466 | 3.000 | -0.054 | 3.000 |
| hard_over_vs_remaining | emp_distribution__y2025_landsat_vi6t__std_over_range | Otras señales | 0.286 | 0.261 | 0.451 | 0.460 | 3.000 | 0.314 | 3.000 |
| hard_over_vs_remaining | S2_nddi_derived_range_max_decline_rate | Señal satelital de humedad | -0.051 | -0.043 | -0.138 | -0.447 | 3.000 | -0.090 | 3.000 |
| hard_over_vs_remaining | soilgrids__bdod__30_60cm__std | Suelo | 0.011 | 0.009 | 0.300 | 0.406 | 3.000 | 0.479 | 3.000 |
| hard_over_vs_remaining | base_geom_area_ha | Geometría/contexto geográfico | 7.652 | 4.104 | 0.232 | 0.389 | 3.000 | 0.012 | 3.000 |
| hard_under_vs_remaining | sat_basic_hist__sentinel_2__fapar_min__mean | Vegetación/heterogeneidad | 0.138 | 0.127 | 0.304 | 0.491 | 2.000 | 0.641 | 3.000 |
| hard_under_vs_remaining | agro_interaction__nitrogen_x_ndvi_historical | Vegetación/heterogeneidad | 0.464 | 0.444 | 0.259 | 0.473 | 2.000 | 0.572 | 3.000 |
| hard_under_vs_remaining | sat_basic_hist__sentinel_2__mra_min__mean | Otras señales | 0.022 | 0.022 | 0.296 | 0.459 | 2.000 | 0.436 | 3.000 |
| hard_under_vs_remaining | sat_basic_hist__landsat__vi6t_max__mean | Otras señales | -0.603 | -0.599 | -0.135 | -0.447 | 2.000 | -0.530 | 3.000 |
| hard_under_vs_remaining | soilgrids__soc__15_30cm__mean | Suelo | 10.343 | 10.117 | 0.088 | 0.431 | 2.000 | 0.322 | 3.000 |
| hard_under_vs_remaining | TOPO_ADV_plan_curvature_iqr | Relieve/topografía | 0.002 | 0.003 | -0.326 | -0.428 | 2.000 | -0.549 | 3.000 |
| hard_under_vs_remaining | agro_soil__clay_to_sand | Suelo | 0.524 | 0.538 | -0.083 | -0.426 | 2.000 | -0.428 | 3.000 |
| hard_under_vs_remaining | emp_shape__y2025_s2_msi__peak_sharpness | Señal satelital de humedad | 0.044 | 0.028 | 0.243 | 0.414 | 2.000 | 0.257 | 3.000 |
| hard_under_vs_remaining | sat_basic_hist__sentinel_2__ndwi_min__min | Señal satelital de humedad | -0.309 | -0.337 | 0.310 | 0.391 | 2.000 | 0.460 | 3.000 |
| hard_under_vs_remaining | TOPO_BASIC_slope_min | Relieve/topografía | 1.529 | 1.199 | 0.147 | 0.375 | 2.000 | 0.502 | 3.000 |
| hard_under_vs_remaining | tmin_cycle_range | Clima | 3.812 | 3.812 | -0.050 | -0.338 | 2.000 | 0.000 | 3.000 |
| hard_under_vs_remaining | tmean_anomaly_jun | Clima | -0.886 | -0.851 | -0.320 | -0.320 | 2.000 | 0.000 | 3.000 |
| hard_vs_remaining | soilgrids__nitrogen__5_15cm__mean | Suelo | 1.700 | 1.696 | 0.125 | 0.512 | 3.000 | 0.331 | 3.000 |
| hard_vs_remaining | EXT_LOC_nearest_population | Geometría/contexto geográfico | 34.000 | 21.000 | 0.154 | 0.476 | 3.000 | 0.342 | 3.000 |
| hard_vs_remaining | sat_basic_2025__sentinel_2__mcrc_std__max | Otras señales | 0.158 | 0.137 | 0.169 | 0.464 | 3.000 | 0.021 | 3.000 |
| hard_vs_remaining | sat_basic_2025__sentinel_2__dswi2_std__max | Otras señales | 0.423 | 0.397 | 0.123 | 0.438 | 3.000 | 0.006 | 3.000 |
| hard_vs_remaining | S2_ndvi_promedio_kurtosis | Vegetación/heterogeneidad | -1.626 | -1.549 | -0.172 | -0.435 | 3.000 | -0.016 | 3.000 |
| hard_vs_remaining | emp_distribution__hist_s2_lai__std_over_range | Vegetación/heterogeneidad | 0.237 | 0.217 | 0.361 | 0.432 | 3.000 | 0.127 | 3.000 |
| hard_vs_remaining | S2_msi_derived_cv_slope | Señal satelital de humedad | 0.000 | 0.001 | -0.087 | -0.421 | 3.000 | -0.205 | 3.000 |
| hard_vs_remaining | S2_nddi_derived_range_max_decline_rate | Señal satelital de humedad | -0.047 | -0.043 | -0.089 | -0.413 | 3.000 | -0.060 | 3.000 |
| hard_vs_remaining | soilgrids__nitrogen__depth_weighted_0_30cm | Suelo | 1.513 | 1.515 | 0.083 | 0.405 | 3.000 | 0.223 | 3.000 |
| hard_vs_remaining | rain_relative_anomaly_jun | Clima | 1.516 | 1.516 | -0.042 | -0.363 | 3.000 | 0.000 | 3.000 |
| hard_vs_remaining | TOPO_ADV_aspect_sin_iqr | Relieve/topografía | 0.245 | 0.178 | 0.126 | 0.351 | 3.000 | 0.151 | 3.000 |
| hard_vs_remaining | tmean_change_apr_may | Clima | 1.628 | 1.679 | -0.190 | -0.344 | 3.000 | 0.000 | 3.000 |

Cliff delta positivo: primer grupo tiene valores más altos. Medianas son globales; efectos condicionados comparan sólo dentro del mismo municipio/perfil. Las categorías y todas las variables están en Excel. No se atribuyen causas ni significancia confirmatoria.

## Clasificación fuera de muestra

| classifier | protocol | balanced_accuracy | macro_f1 | hard_detection_auc | hard_direction_auc | hard_direction_balanced_accuracy |
| --- | --- | --- | --- | --- | --- | --- |
| ALL_SIGNALS | climate_profile | 0.324 | 0.297 | 0.414 | 0.360 | 0.441 |
| ALL_SIGNALS | municipality | 0.252 | 0.275 | 0.368 | 0.647 | 0.523 |
| ALL_SIGNALS | random | 0.309 | 0.299 | 0.479 | 0.462 | 0.453 |
| ALL_SIGNALS | spatial | 0.226 | 0.239 | 0.166 | 0.000 | 0.396 |
| PHYSICAL | climate_profile | 0.407 | 0.273 | 0.522 | 0.723 | 0.676 |
| PHYSICAL | municipality | 0.411 | 0.293 | 0.503 | 0.526 | 0.549 |
| PHYSICAL | random | 0.311 | 0.296 | 0.534 | 0.451 | 0.418 |
| PHYSICAL | spatial | 0.281 | 0.297 | 0.515 | 0.771 | 0.625 |
| PRIOR | climate_profile | 0.333 | 0.287 | 0.594 | 0.334 | 0.412 |
| PRIOR | municipality | 0.333 | 0.299 | 0.661 | 0.271 | 0.500 |
| PRIOR | random | 0.333 | 0.288 | 0.491 | 0.456 | 0.465 |
| PRIOR | spatial | 0.333 | 0.299 | 0.555 | 0.542 | 0.500 |

Accuracy y métricas por clase están en tablas. PHYSICAL=suelo/relieve/geología numéricos; ALL_SIGNALS=todas las señales numéricas sin campos de calidad ni identificadores geográficos directos; PRIOR=frecuencias internas. La probabilidad de difícil no es un intervalo predictivo ni una corrección de rendimiento.

La reutilización histórica de estos datos y el origen de algunas features en residuos examinados hacen exploratoria toda la etapa. El cuartil de bajo rendimiento se conserva como cohorte separada, con empates.