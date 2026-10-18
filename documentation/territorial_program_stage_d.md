> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Etapa D — Síntesis de evidencia y diagnóstico de generalización

## 1. Resumen

Cierre metodológico A–D, exclusivamente descriptivo sobre predicciones archivadas. Se preservan las decisiones previas; no se vuelve a seleccionar un ganador ni se entrena ningún modelo. C-T3 merece validación municipal; Champion/mezcla siguen limitados al ámbito aleatorio compatible; C-T1 mantiene una hipótesis espacial con dependencia del bloque3; H1 no aporta ventaja frente a H0M.

## 2. Objetivos

D1 concentración de ganancias; D2 composición bloque3; D3 escenarios de generalización; D4 heterogeneidad local; D5 información/validación externa; D6 candidatos y controles; D7 alcance científico. Ninguno introduce un nuevo experimento predictivo.

## 3. Datos y protocolos

197 parcelas:138Y y59PRED sin uso de etiquetas;53perfiles completos,43conY,12repetidos. Chignahuapan71Y. Los subconjuntos locales de perfiles4/24 tienen29/33etiquetas; el perfil24 completo incluye una observación fuera del municipio y tiene34. No confundir n local con tamaño total del perfil.

65folds congelados:50aleatorios(5×10),5porperfil,5municipales,5espaciales, con sus particiones internas originales. Métrica primaria:138OOF completas por repetición, después media de repeticiones. Media de folds, métrica de predicción media por parcela y RMS de pérdidas promediadas entre repeticiones son diagnósticos distintos, identificados por separado.

## 4. Inventario y 5. Comparabilidad

`model_inventory.csv` recupera todas las series OOF de antecedentes, incluidos controles descartados, IDs exactos, configuraciones/especificaciones recuperables, disponibilidad y hashes. `background_artifact_inventory.csv` registra reportes/configuraciones; `protected_inputs.csv` conserva scripts, fuentes, métricas y modelos previos. Donde una especificación no está en JSON se conserva referencia a fuentes/tablas, sin inventarla.

Llave explícita: (ID_POLIGONO, protocolo, repetición, fold), con Y idéntico. `comparability.csv` verifica conjuntos completos uno-a-uno; los IDs de validación corresponden a splits congelados y a procedencia OOF anterior. Champion no se reconstruye. F4-S1 y C-T0 son la misma referencia, y B2/F4-E2 son alias: no constituyen evidencia independiente.

| index | experiment | protocol | n_parcels | n_repeats | RMSE | RMSE_sd_repeats | MAE | bias | MSE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | B2 | random | 138 | 10 | 0.50561 | 0.00739 | 0.36368 | -0.00288 | 0.25569 |
| 6 | B3 | random | 138 | 10 | 0.51244 | 0.00859 | 0.36799 | -0.00150 | 0.26266 |
| 10 | C-H0M | random | 138 | 10 | 0.50945 | 0.00742 | 0.36840 | -0.00428 | 0.25959 |
| 14 | C-T1 | random | 138 | 10 | 0.52412 | 0.00568 | 0.37360 | -0.00454 | 0.27473 |
| 18 | C-T3 | random | 138 | 10 | 0.51158 | 0.00600 | 0.37495 | 0.00053 | 0.26175 |
| 20 | CHAMPION | random | 138 | 10 | 0.49813 | 0.00750 | 0.35887 | 0.00183 | 0.24818 |
| 23 | F4-E2 | random | 138 | 10 | 0.50561 | 0.00739 | 0.36368 | -0.00288 | 0.25569 |
| 27 | F4-S1 | random | 138 | 10 | 0.50483 | 0.00675 | 0.36411 | -0.00256 | 0.25490 |
| 29 | FIXED_50_50 | random | 138 | 10 | 0.49360 | 0.00626 | 0.35343 | -0.00036 | 0.24368 |

| index | experiment | protocol | n_parcels | n_repeats | RMSE | RMSE_sd_repeats | MAE | bias | MSE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | B2 | climate_profile | 138 | 1 | 0.53333 | nan | 0.39454 | 0.02192 | 0.28445 |
| 1 | B2 | municipality | 138 | 1 | 0.67500 | nan | 0.49993 | 0.01889 | 0.45562 |
| 3 | B2 | spatial | 138 | 1 | 0.73845 | nan | 0.57336 | 0.17145 | 0.54530 |
| 4 | B3 | climate_profile | 138 | 1 | 0.54364 | nan | 0.39922 | 0.04651 | 0.29555 |
| 5 | B3 | municipality | 138 | 1 | 0.86500 | nan | 0.72851 | -0.30910 | 0.74823 |
| 7 | B3 | spatial | 138 | 1 | 0.72267 | nan | 0.56802 | 0.13508 | 0.52224 |
| 8 | C-H0M | climate_profile | 138 | 1 | 0.51777 | nan | 0.38212 | 0.00956 | 0.26809 |
| 9 | C-H0M | municipality | 138 | 1 | 0.63945 | nan | 0.47859 | -0.00372 | 0.40889 |
| 11 | C-H0M | spatial | 138 | 1 | 0.67244 | nan | 0.52226 | 0.11130 | 0.45217 |
| 12 | C-T1 | climate_profile | 138 | 1 | 0.56029 | nan | 0.40777 | 0.02070 | 0.31393 |
| 13 | C-T1 | municipality | 138 | 1 | 0.68540 | nan | 0.51500 | 0.02458 | 0.46977 |
| 15 | C-T1 | spatial | 138 | 1 | 0.60047 | nan | 0.44654 | 0.09301 | 0.36056 |
| 16 | C-T3 | climate_profile | 138 | 1 | 0.52060 | nan | 0.39150 | 0.00459 | 0.27103 |
| 17 | C-T3 | municipality | 138 | 1 | 0.58126 | nan | 0.46033 | -0.02033 | 0.33786 |
| 19 | C-T3 | spatial | 138 | 1 | 0.67878 | nan | 0.53061 | 0.19116 | 0.46074 |
| 21 | F4-E2 | climate_profile | 138 | 1 | 0.53333 | nan | 0.39454 | 0.02192 | 0.28445 |
| 22 | F4-E2 | municipality | 138 | 1 | 0.67500 | nan | 0.49993 | 0.01889 | 0.45562 |
| 24 | F4-E2 | spatial | 138 | 1 | 0.73845 | nan | 0.57336 | 0.17145 | 0.54530 |
| 25 | F4-S1 | climate_profile | 138 | 1 | 0.52626 | nan | 0.38889 | 0.02275 | 0.27695 |
| 26 | F4-S1 | municipality | 138 | 1 | 0.67110 | nan | 0.49856 | 0.01326 | 0.45038 |
| 28 | F4-S1 | spatial | 138 | 1 | 0.73904 | nan | 0.57291 | 0.17102 | 0.54618 |

Estas tablas son universos separados. Los resultados históricos de Familias2/3 con mediafold se preservan en sus archivos y no se insertan como si fueran estas mismas métricas. Las decisiones originales estaban basadas en comparaciones propias; D no altera sus números archivados.

## 6. Caracterización del bloque espacial3

| index | block | n | n_profiles | municipalities | states | profiles | n_Chignahuapan |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 38 | 5 | {"Chignahuapan": 34, "Cuautepec de Hinojosa": 4} | {"Puebla": 34, "Hidalgo": 4} | {"24": 32, "29": 3, "27": 1, "28": 1, "30": 1} | 34 |
| 1 | 2 | 37 | 8 | {"Chignahuapan": 37} | {"Puebla": 37} | {"4": 29, "24": 2, "14": 1, "13": 1, "11": 1, "6": 1, "5": 1, "9": 1} | 37 |
| 2 | 3 | 35 | 16 | {"Calpulalpan": 30, "Emiliano Zapata": 3, "Nanacamilpa de Mariano Arista": 1, "Apan": 1} | {"Tlaxcala": 31, "Hidalgo": 4} | {"38": 11, "47": 5, "43": 3, "21": 3, "51": 2, "41": 1, "46": 1, "36": 1, "53": 1, "52": 1, "48": 1, "45": 1, "50": 1, "40": 1, "42": 1, "39": 1} | 0 |
| 3 | 4 | 18 | 9 | {"Singuilucan": 16, "Cuautepec de Hinojosa": 1, "Tepeapulco": 1} | {"Hidalgo": 18} | {"35": 6, "37": 5, "12": 1, "19": 1, "3": 1, "20": 1, "33": 1, "18": 1, "32": 1} | 0 |
| 4 | 5 | 10 | 7 | {"Almoloya": 10} | {"Hidalgo": 10} | {"15": 3, "30": 2, "7": 1, "16": 1, "17": 1, "1": 1, "2": 1} | 0 |

El bloque 3 contiene 35 etiquetas: 30 de Calpulalpan, 3 de Emiliano Zapata, 1 de Nanacamilpa y 1 de Apan; 31 son de Tlaxcala y 4 de Hidalgo, sin Chignahuapan. Su Y medio de 3.028571 t/ha y rango 2.5–3.5 están dentro del rango restante. El problema no es un extremo de Y fuera del entrenamiento: sí hay extrapolación de covariables. 33/35 exceden el máximo del resto en fracción temprana de lluvia y 34/35 en DTRstd. La lluvia total tiene SMD 0.231077, frente a 5.137570 de fracción temprana y 3.868436 de DTRstd; NDVI es menor (SMD −1.317668). Por tanto, distribución temporal y temperatura distinguen más este bloque que intensidad total. Estas diferencias no prueban una causa agronómica.

El modelo F4-S1 tiene sesgo +1.041033 t/ha en bloque 3; T1 baja a +0.064922 y T3 a +0.718204. La ganancia SSE del bloque 3 es 33.852255 para T1 y 15.550063 para T3. La reducción de sesgo cuadrático aporta 37.783737 y 19.877660 respectivamente, compensada por **aumento** de la dispersión de errores. La mejora es principalmente corregir nivel regional; no reducir toda la variabilidad local. 31/35 parcelas mejoran con ambos, 2 solo con T3 y 2 con ninguno. El bloque representa 25.36% de parcelas pero 131.9%/132.2% de las ganancias netas T3/T1 porque otros bloques deterioran. No es únicamente peso por tamaño ni solo cinco casos extremos.

Distribuciones seleccionadas, con unidades originales: lluvia total mm, DTRstd °C, NDVI sin unidad, Y t/ha, altitud m, pendiente grados.

| index | block | feature | n | mean | std | min | q10 | q25 | median | q75 | q90 | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7 | 1 | compact_precip_total | 38 | 964.54513 | 27.24269 | 910.26735 | 961.35081 | 961.35081 | 961.35081 | 961.35081 | 961.35081 | 1046.50362 |
| 10 | 1 | CLIMATE_dtr_mean_std | 38 | 2.30901 | 0.02657 | 2.23988 | 2.30967 | 2.30967 | 2.30967 | 2.30967 | 2.30967 | 2.37997 |
| 11 | 1 | S2_ndvi_month_05 | 38 | 0.15063 | 0.03047 | 0.11820 | 0.12714 | 0.13255 | 0.14082 | 0.15960 | 0.18405 | 0.27500 |
| 12 | 1 | RENDIMIENTO_T_HA | 38 | 4.37237 | 0.55093 | 2.15000 | 3.96400 | 4.21000 | 4.50500 | 4.59750 | 4.80200 | 5.57000 |
| 13 | 1 | altitude_m | 38 | 2624.97586 | 29.24759 | 2564.03773 | 2600.49366 | 2607.66685 | 2620.81860 | 2632.76596 | 2643.67581 | 2726.68311 |
| 14 | 1 | slope_degrees | 38 | 2.40946 | 2.49229 | 0.31939 | 0.37715 | 0.62045 | 1.39815 | 2.86310 | 7.03418 | 9.39639 |
| 43 | 2 | compact_precip_total | 37 | 810.77620 | 42.45642 | 793.73032 | 793.73032 | 793.73032 | 793.73032 | 793.73032 | 856.17012 | 961.35081 |
| 46 | 2 | CLIMATE_dtr_mean_std | 37 | 2.23178 | 0.02470 | 2.18854 | 2.22466 | 2.22466 | 2.22466 | 2.22466 | 2.25627 | 2.30967 |
| 47 | 2 | S2_ndvi_month_05 | 37 | 0.14690 | 0.02375 | 0.09600 | 0.12200 | 0.13000 | 0.14100 | 0.16500 | 0.17730 | 0.19500 |
| 48 | 2 | RENDIMIENTO_T_HA | 37 | 4.59595 | 0.57395 | 2.64000 | 3.97000 | 4.47000 | 4.55000 | 4.94000 | 5.29400 | 5.59000 |
| 49 | 2 | altitude_m | 37 | 2761.60509 | 100.87435 | 2613.79527 | 2625.47010 | 2670.97452 | 2751.88185 | 2869.56068 | 2887.82462 | 2903.99038 |
| 50 | 2 | slope_degrees | 37 | 3.84099 | 1.96190 | 0.78930 | 1.52521 | 2.38277 | 3.67425 | 5.31830 | 6.40026 | 8.24309 |
| 79 | 3 | compact_precip_total | 35 | 981.83527 | 187.10806 | 770.92774 | 813.46550 | 887.94609 | 887.94609 | 1074.46364 | 1284.82867 | 1459.13842 |
| 82 | 3 | CLIMATE_dtr_mean_std | 35 | 2.63561 | 0.03753 | 2.56442 | 2.60262 | 2.60262 | 2.63179 | 2.65930 | 2.68863 | 2.71974 |
| 83 | 3 | S2_ndvi_month_05 | 35 | 0.11869 | 0.01199 | 0.09480 | 0.10194 | 0.11290 | 0.11940 | 0.12517 | 0.12932 | 0.15450 |
| 84 | 3 | RENDIMIENTO_T_HA | 35 | 3.02857 | 0.38239 | 2.50000 | 2.50000 | 2.75000 | 3.00000 | 3.50000 | 3.50000 | 3.50000 |
| 85 | 3 | altitude_m | 35 | 2597.87468 | 73.76550 | 2496.64847 | 2516.91886 | 2535.09839 | 2583.34215 | 2644.41657 | 2696.27972 | 2812.36036 |
| 86 | 3 | slope_degrees | 35 | 2.05805 | 1.14849 | 0.34886 | 0.97115 | 1.42830 | 1.76618 | 2.34684 | 3.38756 | 5.31704 |
| 115 | 4 | compact_precip_total | 18 | 1229.91214 | 143.66346 | 805.16933 | 1078.17876 | 1240.50330 | 1274.55693 | 1324.10578 | 1335.09023 | 1335.09023 |
| 118 | 4 | CLIMATE_dtr_mean_std | 18 | 2.48590 | 0.05923 | 2.41255 | 2.41255 | 2.41487 | 2.51642 | 2.53503 | 2.54029 | 2.56374 |
| 119 | 4 | S2_ndvi_month_05 | 18 | 0.12528 | 0.01633 | 0.08660 | 0.10603 | 0.11900 | 0.12537 | 0.13330 | 0.14620 | 0.14967 |
| 120 | 4 | RENDIMIENTO_T_HA | 18 | 3.24611 | 0.63081 | 2.00000 | 2.50000 | 3.00000 | 3.25000 | 3.45000 | 3.92500 | 4.68000 |
| 121 | 4 | altitude_m | 18 | 2702.99253 | 71.61206 | 2527.72548 | 2603.59890 | 2693.48084 | 2727.70530 | 2747.28427 | 2756.26100 | 2762.99248 |
| 122 | 4 | slope_degrees | 18 | 2.25272 | 1.31834 | 0.28767 | 0.58108 | 1.12270 | 2.22947 | 3.49075 | 3.75690 | 4.25548 |
| 151 | 5 | compact_precip_total | 10 | 813.02477 | 74.93326 | 702.78865 | 705.63804 | 760.69545 | 821.31283 | 850.88579 | 910.26735 | 910.26735 |
| 154 | 5 | CLIMATE_dtr_mean_std | 10 | 2.46585 | 0.07342 | 2.37997 | 2.37997 | 2.42716 | 2.45074 | 2.50553 | 2.57968 | 2.58493 |
| 155 | 5 | S2_ndvi_month_05 | 10 | 0.17100 | 0.02235 | 0.13780 | 0.14263 | 0.15545 | 0.17110 | 0.18755 | 0.19373 | 0.20700 |
| 156 | 5 | RENDIMIENTO_T_HA | 10 | 4.52100 | 0.18847 | 4.14000 | 4.38300 | 4.45500 | 4.53000 | 4.57000 | 4.70800 | 4.87000 |
| 157 | 5 | altitude_m | 10 | 2708.50498 | 57.85944 | 2627.09390 | 2628.52774 | 2654.73084 | 2725.08349 | 2759.26273 | 2764.68391 | 2773.83640 |
| 158 | 5 | slope_degrees | 10 | 4.09829 | 2.29002 | 0.39492 | 0.60727 | 3.31476 | 4.22259 | 5.54614 | 6.70438 | 7.31509 |

Contraste3/resto SMD usa desviaciones muestrales y no se calcula ante varianza degenerada. No hay pruebas masivas ni búsqueda de una variable ganadora.

| index | feature | n_block3 | n_rest | SMD | block3_min | block3_max | rest_min | rest_max | n_block3_outside_rest_range | warning |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7 | compact_precip_total | 35 | 103 | 0.23108 | 770.92774 | 1459.13842 | 702.78865 | 1335.09023 | 4 | Y differences descriptive; no variable selection or causal attribution |
| 8 | compact_early_fraction | 35 | 103 | 5.13757 | 0.41821 | 0.47939 | 0.37637 | 0.42501 | 33 | Y differences descriptive; no variable selection or causal attribution |
| 9 | compact_concentration_hhi | 35 | 103 | 1.64717 | 0.17916 | 0.19195 | 0.17018 | 0.19238 | 0 | Y differences descriptive; no variable selection or causal attribution |
| 10 | CLIMATE_dtr_mean_std | 35 | 103 | 3.86844 | 2.56442 | 2.71974 | 2.18854 | 2.58493 | 34 | Y differences descriptive; no variable selection or causal attribution |
| 11 | S2_ndvi_month_05 | 35 | 103 | -1.31767 | 0.09480 | 0.15450 | 0.08660 | 0.27500 | 0 | Y differences descriptive; no variable selection or causal attribution |
| 12 | RENDIMIENTO_T_HA | 35 | 103 | -2.13636 | 2.50000 | 3.50000 | 2.00000 | 5.59000 | 0 | Y differences descriptive; no variable selection or causal attribution |
| 13 | altitude_m | 35 | 103 | -1.17220 | 2496.64847 | 2812.36036 | 2527.72548 | 2903.99038 | 5 | Y differences descriptive; no variable selection or causal attribution |
| 14 | slope_degrees | 35 | 103 | -0.56547 | 0.34886 | 5.31704 | 0.28767 | 9.39639 | 0 | Y differences descriptive; no variable selection or causal attribution |

`spatial_support.csv` distingue rangos marginales, cercanía al límite y distancia estandarizada conjunta al entrenamiento en lluvia total/DTR/NDVI. Estar dentro de cada rango no garantiza combinaciones conocidas ni soporte del Champion. Los rangos de Y son descripción ex post, nunca una regla para definir soporte predictivo. Suelo y geología se describen mediante cuotas cartográficas existentes; no se atribuyen textura o capacidad hídrica física a una categoría.

## 7. Descomposición de errores y sensibilidad

Ganancia=SSE_F4S1−SSE_candidato; positiva favorece candidato. Las contribuciones suman la ganancia total; ganancia deRMSE no es sumable. La tabla separa tamaño, SSE y sesgo.

| index | candidate | baseline | block | n | sse_gain | gain_per_parcel | fraction_net_sse_gain | parcel_fraction | baseline_sse | candidate_sse | baseline_bias | candidate_bias |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | C-T1 | F4-S1 | 1 | 38 | -1.52478 | -0.04013 | -0.05953 | 0.27536 | 9.96409 | 11.48887 | 0.06361 | 0.08029 |
| 1 | C-T1 | F4-S1 | 2 | 37 | 1.13358 | 0.03064 | 0.04425 | 0.26812 | 12.67385 | 11.54027 | -0.17779 | 0.00332 |
| 2 | C-T1 | F4-S1 | 3 | 35 | 33.85225 | 0.96721 | 1.32156 | 0.25362 | 44.50762 | 10.65536 | 1.04103 | 0.06492 |
| 3 | C-T1 | F4-S1 | 4 | 18 | -6.19277 | -0.34404 | -0.24176 | 0.13043 | 7.80200 | 13.99477 | -0.40123 | 0.63705 |
| 4 | C-T1 | F4-S1 | 5 | 10 | -1.65291 | -0.16529 | -0.06453 | 0.07246 | 0.42552 | 2.07843 | -0.14525 | -0.40785 |
| 5 | C-T3 | F4-S1 | 1 | 38 | 0.25604 | 0.00674 | 0.02171 | 0.27536 | 9.96409 | 9.70805 | 0.06361 | -0.03690 |
| 6 | C-T3 | F4-S1 | 2 | 37 | 0.54592 | 0.01475 | 0.04630 | 0.26812 | 12.67385 | 12.12794 | -0.17779 | -0.11929 |
| 7 | C-T3 | F4-S1 | 3 | 35 | 15.55006 | 0.44429 | 1.31881 | 0.25362 | 44.50762 | 28.95755 | 1.04103 | 0.71820 |
| 8 | C-T3 | F4-S1 | 4 | 18 | -3.68910 | -0.20495 | -0.31287 | 0.13043 | 7.80200 | 11.49110 | -0.40123 | 0.57431 |
| 9 | C-T3 | F4-S1 | 5 | 10 | -0.87190 | -0.08719 | -0.07395 | 0.07246 | 0.42552 | 1.29743 | -0.14525 | -0.32783 |

| index | candidate | baseline | omitted_block | n | delta_RMSE | delta_MAE | sse_gain | analysis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | C-T1 | F4-S1 | 1 | 100 | -0.19014 | -0.17537 | 27.14016 | OOF aggregation sensitivity; no retraining |
| 1 | C-T1 | F4-S1 | 2 | 101 | -0.17276 | -0.15267 | 24.48180 | OOF aggregation sensitivity; no retraining |
| 2 | C-T1 | F4-S1 | 3 | 103 | 0.06873 | 0.02828 | -8.23688 | OOF aggregation sensitivity; no retraining |
| 3 | C-T1 | F4-S1 | 4 | 120 | -0.20448 | -0.16610 | 31.80815 | OOF aggregation sensitivity; no retraining |
| 4 | C-T1 | F4-S1 | 5 | 128 | -0.15487 | -0.15455 | 27.26829 | OOF aggregation sensitivity; no retraining |
| 5 | C-T3 | F4-S1 | 1 | 100 | -0.07477 | -0.06282 | 11.53497 | OOF aggregation sensitivity; no retraining |
| 6 | C-T3 | F4-S1 | 2 | 101 | -0.07414 | -0.04809 | 11.24510 | OOF aggregation sensitivity; no retraining |
| 7 | C-T3 | F4-S1 | 3 | 103 | 0.03238 | 0.02192 | -3.75905 | OOF aggregation sensitivity; no retraining |
| 8 | C-T3 | F4-S1 | 4 | 120 | -0.09154 | -0.05905 | 15.48011 | OOF aggregation sensitivity; no retraining |
| 9 | C-T3 | F4-S1 | 5 | 128 | -0.06763 | -0.05765 | 12.66292 | OOF aggregation sensitivity; no retraining |

Se denomina **sensibilidad de agregación OOF al omitir el bloque**. Ningún modelo fue ajustado de nuevo. La reversión T3 al omitir3 es un límite de estabilidad territorial, no una nueva validación leave-one-block-out.

| index | scope | n | both_improve | T1_only | T3_only | neither | gain_correlation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | block3 | 35 | 31 | 0 | 2 | 2 | 0.64077 |
| 1 | all | 138 | 64 | 20 | 19 | 35 | 0.83113 |

| index | candidate | block | n | sse_gain | bias_squared_gain | error_variance_gain | fraction_gain_from_bias |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | C-T1 | 3 | 35 | 33.85225 | 37.78374 | -3.93148 | 1.11614 |
| 7 | C-T3 | 3 | 35 | 15.55006 | 19.87766 | -4.32760 | 1.27830 |
| 12 | C-H0M | 3 | 35 | 13.64589 | 15.88773 | -2.24185 | 1.16429 |
| 17 | F4-E2 | 3 | 35 | 0.34007 | 0.62776 | -0.28769 | 1.84596 |

Las ganancias superpuestas y las contribuciones por parcela están en `spatial_parcel_gain_overlap.csv`; un mismo caso puede beneficiar ambos modelos. `spatial_block_errors.csv` registraRMSE/MAE/sesgo y cuantiles de error. La diferenciaSSE por bloque puede descomponerse como n·(bias_base²−bias_candidato²) más cambio de varianza de errores: ambos términos se reportan en `block_bias_variance_decomposition.csv`. Un sesgo regional reducido no demuestra que DTR cause el rendimiento.

Hipótesis futuras verificables: comprobar en varias regiones independientes si condiciones parecidas al bloque3 vuelven a producir sesgo de lluvia mensual y si T1/T3 lo reducen; contrastar regiones con solapamiento y fuera del soporte; verificar si la ventaja persiste sin pocos beneficiarios. No se crea una regla territorial de activación.

## 8. Influencia de parcelas y casos persistentes

`paired_losses.parquet` conserva todas las filas e IDs. En aleatoria se promedian pérdidas de las diez repeticiones por parcela para influencia; no se promedian predicciones para métricas primarias. Se reportan SE/AE, medianas, cuantiles, proporciones de mejora y ganancias municipales/perfil.

| index | candidate | baseline | protocol | k | net_gain | positive_gain | top_gain | top_fraction_net | top_fraction_positive | bottom_gain | top_ids | bottom_ids |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | FIXED_50_50 | CHAMPION | random | 1 | 0.62112 | 3.08272 | 0.30887 | 0.49728 | 0.10020 | -0.30491 | ["AGC_015"] | ["AGC_122"] |
| 1 | FIXED_50_50 | CHAMPION | random | 5 | 0.62112 | 3.08272 | 1.01674 | 1.63693 | 0.32982 | -1.02268 | ["AGC_015", "AGC_074", "AGC_057", "AGC_127", "AGC_081"] | ["AGC_047", "AGC_049", "AGC_171", "AGC_162", "AGC_122"] |
| 3 | C-T3 | F4-S1 | climate_profile | 1 | 0.81769 | 5.68753 | 0.76093 | 0.93059 | 0.13379 | -0.73955 | ["AGC_122"] | ["AGC_001"] |
| 4 | C-T3 | F4-S1 | climate_profile | 5 | 0.81769 | 5.68753 | 1.78879 | 2.18761 | 0.31451 | -1.94118 | ["AGC_122", "AGC_187", "AGC_171", "AGC_035", "AGC_054"] | ["AGC_015", "AGC_152", "AGC_034", "AGC_041", "AGC_001"] |
| 6 | C-T3 | F4-S1 | municipality | 1 | 15.52694 | 22.38789 | 3.01410 | 0.19412 | 0.13463 | -0.35186 | ["AGC_122"] | ["AGC_172"] |
| 7 | C-T3 | F4-S1 | municipality | 5 | 15.52694 | 22.38789 | 8.59097 | 0.55329 | 0.38373 | -1.36841 | ["AGC_122", "AGC_001", "AGC_034", "AGC_145", "AGC_098"] | ["AGC_169", "AGC_138", "AGC_162", "AGC_014", "AGC_172"] |
| 9 | C-T3 | F4-S1 | random | 1 | -0.94525 | 3.49387 | 0.40473 | -0.42818 | 0.11584 | -0.66659 | ["AGC_047"] | ["AGC_001"] |
| 10 | C-T3 | F4-S1 | random | 5 | -0.94525 | 3.49387 | 1.26783 | -1.34126 | 0.36287 | -1.67426 | ["AGC_047", "AGC_187", "AGC_054", "AGC_035", "AGC_081"] | ["AGC_145", "AGC_041", "AGC_166", "AGC_034", "AGC_001"] |
| 12 | C-T3 | F4-S1 | spatial | 1 | 11.79101 | 23.66542 | 1.32402 | 0.11229 | 0.05595 | -2.43616 | ["AGC_144"] | ["AGC_034"] |
| 13 | C-T3 | F4-S1 | spatial | 5 | 11.79101 | 23.66542 | 5.32012 | 0.45120 | 0.22481 | -6.62667 | ["AGC_144", "AGC_187", "AGC_123", "AGC_080", "AGC_019"] | ["AGC_122", "AGC_001", "AGC_041", "AGC_166", "AGC_034"] |
| 15 | C-T1 | F4-S1 | climate_profile | 1 | -5.10263 | 5.03420 | 0.59557 | -0.11672 | 0.11830 | -1.22279 | ["AGC_122"] | ["AGC_127"] |
| 16 | C-T1 | F4-S1 | climate_profile | 5 | -5.10263 | 5.03420 | 2.16630 | -0.42455 | 0.43032 | -3.54846 | ["AGC_122", "AGC_172", "AGC_160", "AGC_119", "AGC_015"] | ["AGC_166", "AGC_049", "AGC_055", "AGC_034", "AGC_127"] |
| 18 | C-T1 | F4-S1 | municipality | 1 | -2.67587 | 7.44525 | 0.71234 | -0.26621 | 0.09568 | -1.46109 | ["AGC_162"] | ["AGC_127"] |
| 19 | C-T1 | F4-S1 | municipality | 5 | -2.67587 | 7.44525 | 2.44097 | -0.91222 | 0.32786 | -3.74740 | ["AGC_162", "AGC_172", "AGC_119", "AGC_021", "AGC_047"] | ["AGC_171", "AGC_152", "AGC_134", "AGC_015", "AGC_127"] |
| 21 | C-T1 | F4-S1 | random | 1 | -2.73704 | 3.94997 | 0.42562 | -0.15550 | 0.10775 | -1.18182 | ["AGC_172"] | ["AGC_127"] |
| 22 | C-T1 | F4-S1 | random | 5 | -2.73704 | 3.94997 | 1.48374 | -0.54210 | 0.37563 | -2.61565 | ["AGC_172", "AGC_119", "AGC_122", "AGC_162", "AGC_160"] | ["AGC_055", "AGC_054", "AGC_171", "AGC_034", "AGC_127"] |
| 24 | C-T1 | F4-S1 | spatial | 1 | 25.61538 | 44.84104 | 2.42254 | 0.09457 | 0.05403 | -3.53736 | ["AGC_138"] | ["AGC_034"] |
| 25 | C-T1 | F4-S1 | spatial | 5 | 25.61538 | 44.84104 | 11.68969 | 0.45635 | 0.26069 | -10.03476 | ["AGC_138", "AGC_169", "AGC_144", "AGC_058", "AGC_068"] | ["AGC_127", "AGC_122", "AGC_166", "AGC_041", "AGC_034"] |
| 51 | C-T3 | C-H0M | climate_profile | 1 | -0.40588 | 4.00207 | 0.68398 | -1.68518 | 0.17091 | -0.52559 | ["AGC_122"] | ["AGC_001"] |
| 52 | C-T3 | C-H0M | climate_profile | 5 | -0.40588 | 4.00207 | 1.66163 | -4.09389 | 0.41519 | -1.53757 | ["AGC_122", "AGC_187", "AGC_035", "AGC_080", "AGC_054"] | ["AGC_014", "AGC_015", "AGC_152", "AGC_041", "AGC_001"] |
| 54 | C-T3 | C-H0M | municipality | 1 | 9.80221 | 17.92201 | 2.23725 | 0.22824 | 0.12483 | -0.41814 | ["AGC_122"] | ["AGC_138"] |
| 55 | C-T3 | C-H0M | municipality | 5 | 9.80221 | 17.92201 | 5.89535 | 0.60143 | 0.32894 | -2.00050 | ["AGC_122", "AGC_034", "AGC_145", "AGC_001", "AGC_041"] | ["AGC_068", "AGC_172", "AGC_058", "AGC_169", "AGC_138"] |
| 57 | C-T3 | C-H0M | random | 1 | -0.29778 | 3.62246 | 0.41899 | -1.40705 | 0.11566 | -0.59452 | ["AGC_047"] | ["AGC_001"] |
| 58 | C-T3 | C-H0M | random | 5 | -0.29778 | 3.62246 | 1.36749 | -4.59234 | 0.37750 | -1.48826 | ["AGC_047", "AGC_187", "AGC_035", "AGC_054", "AGC_127"] | ["AGC_014", "AGC_166", "AGC_041", "AGC_034", "AGC_001"] |
| 60 | C-T3 | C-H0M | spatial | 1 | -1.18253 | 11.51579 | 0.71008 | -0.60047 | 0.06166 | -1.65360 | ["AGC_049"] | ["AGC_034"] |
| 61 | C-T3 | C-H0M | spatial | 5 | -1.18253 | 11.51579 | 2.96505 | -2.50737 | 0.25748 | -5.14161 | ["AGC_049", "AGC_055", "AGC_069", "AGC_162", "AGC_005"] | ["AGC_160", "AGC_015", "AGC_041", "AGC_166", "AGC_034"] |

Las fracciones de ganancia neta pueden superar100% porque otros casos deterioran; si el neto es negativo, esa razón no mide concentración de una mejora. Se acompaña fracción de ganancias positivas. `parcel_omission_sensitivity.csv` elimina IDs solo del cálculo diagnóstico y preserva predicciones/etiquetas. No se utiliza para favorecer un ranking.

La mezcla fija depende más de pocos beneficiarios: top 5 explican 163.69% de la ganancia neta y omitirlos descriptivamente revierte SSE. En T3 municipal top 5 explican 55.33%, y al omitirlos todavía mejora RMSE en 0.045040 t/ha; no es la misma fragilidad de la mezcla. Sin embargo, solo 54/138 parcelas (39.13%) mejoran su pérdida cuadrática municipal y la mediana de ganancia es negativa: el beneficio se concentra en reducir errores grandes, no en mejorar a la mayoría. En espacio, top 5 explican 45.12% de la ganancia T3 y 45.64% de T1; omitirlos conserva la ventaja de ambos. Su fragilidad espacial es principalmente regional: omitir bloque 3 elimina/revierte la ganancia. En perfil, T3 sí revierte al omitir sus cinco principales beneficiarios. Cada conclusión corresponde a un protocolo concreto, sin combinar rankings.

| index | candidate | baseline | protocol | order | k | n_remaining | pooled_delta_RMSE | delta_MAE | net_gain | removed_ids | aggregation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | FIXED_50_50 | CHAMPION | random | largest_gain | 5 | 133 | 0.00326 | -0.00108 | -0.39561 | ["AGC_015", "AGC_074", "AGC_057", "AGC_127", "AGC_081"] | RMS of mean parcel losses; distinct from primary mean-repeat RMSE; no retraining |
| 8 | C-T3 | F4-S1 | climate_profile | largest_gain | 5 | 133 | 0.00756 | 0.01076 | -0.97110 | ["AGC_122", "AGC_187", "AGC_171", "AGC_035", "AGC_054"] | RMS of mean parcel losses; distinct from primary mean-repeat RMSE; no retraining |
| 14 | C-T3 | F4-S1 | municipality | largest_gain | 5 | 133 | -0.04504 | -0.01371 | 6.93598 | ["AGC_122", "AGC_001", "AGC_034", "AGC_145", "AGC_098"] | RMS of mean parcel losses; distinct from primary mean-repeat RMSE; no retraining |
| 20 | C-T3 | F4-S1 | random | largest_gain | 5 | 133 | 0.01651 | 0.02046 | -2.21308 | ["AGC_047", "AGC_187", "AGC_054", "AGC_035", "AGC_081"] | RMS of mean parcel losses; distinct from primary mean-repeat RMSE; no retraining |
| 26 | C-T3 | F4-S1 | spatial | largest_gain | 5 | 133 | -0.03524 | -0.02337 | 6.47089 | ["AGC_144", "AGC_187", "AGC_123", "AGC_080", "AGC_019"] | RMS of mean parcel losses; distinct from primary mean-repeat RMSE; no retraining |
| 32 | C-T1 | F4-S1 | climate_profile | largest_gain | 5 | 133 | 0.05368 | 0.03064 | -7.26893 | ["AGC_122", "AGC_172", "AGC_160", "AGC_119", "AGC_015"] | RMS of mean parcel losses; distinct from primary mean-repeat RMSE; no retraining |
| 38 | C-T1 | F4-S1 | municipality | largest_gain | 5 | 133 | 0.02843 | 0.03299 | -5.11684 | ["AGC_162", "AGC_172", "AGC_119", "AGC_021", "AGC_047"] | RMS of mean parcel losses; distinct from primary mean-repeat RMSE; no retraining |
| 44 | C-T1 | F4-S1 | random | largest_gain | 5 | 133 | 0.03197 | 0.01856 | -4.22078 | ["AGC_172", "AGC_119", "AGC_122", "AGC_162", "AGC_160"] | RMS of mean parcel losses; distinct from primary mean-repeat RMSE; no retraining |
| 50 | C-T1 | F4-S1 | spatial | largest_gain | 5 | 133 | -0.08144 | -0.08994 | 13.92569 | ["AGC_138", "AGC_169", "AGC_144", "AGC_058", "AGC_068"] | RMS of mean parcel losses; distinct from primary mean-repeat RMSE; no retraining |
| 104 | C-T3 | C-H0M | climate_profile | largest_gain | 5 | 133 | 0.01525 | 0.01883 | -2.06751 | ["AGC_122", "AGC_187", "AGC_035", "AGC_080", "AGC_054"] | RMS of mean parcel losses; distinct from primary mean-repeat RMSE; no retraining |
| 110 | C-T3 | C-H0M | municipality | largest_gain | 5 | 133 | -0.02638 | -0.00194 | 3.90686 | ["AGC_122", "AGC_034", "AGC_145", "AGC_001", "AGC_041"] | RMS of mean parcel losses; distinct from primary mean-repeat RMSE; no retraining |
| 116 | C-T3 | C-H0M | random | largest_gain | 5 | 133 | 0.01240 | 0.01544 | -1.66527 | ["AGC_047", "AGC_187", "AGC_035", "AGC_054", "AGC_127"] | RMS of mean parcel losses; distinct from primary mean-repeat RMSE; no retraining |
| 122 | C-T3 | C-H0M | spatial | largest_gain | 5 | 133 | 0.02363 | 0.02060 | -4.14758 | ["AGC_049", "AGC_055", "AGC_069", "AGC_162", "AGC_005"] | RMS of mean parcel losses; distinct from primary mean-repeat RMSE; no retraining |

Casos prioritarios, orden descriptivo por recurrencia en el top10% de error absoluto y magnitud, equilibrando modelo/protocolo para que diez repeticiones no pesen como diez campañas:

| index | ID_POLIGONO | Municipio | climate_profile | balanced_mean_AE | balanced_large_error_fraction | same_sign_unit_fraction | archived_C_support_outside_fraction | classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | AGC_171 | Chignahuapan | 24 | 2.09810 | 1.00000 | 1.00000 | 0.00000 | recurrent_large_same_sign |
| 1 | AGC_015 | Chignahuapan | 4 | 1.90586 | 0.96154 | 1.00000 | 0.15385 | recurrent_large_same_sign |
| 2 | AGC_024 | Chignahuapan | 24 | 1.24440 | 0.96154 | 1.00000 | 0.00000 | recurrent_large_same_sign |
| 3 | AGC_162 | Chignahuapan | 4 | 1.15742 | 0.96154 | 1.00000 | 0.15385 | recurrent_large_same_sign |
| 4 | AGC_034 | Singuilucan | 37 | 1.40304 | 0.84615 | 1.00000 | 1.00000 | recurrent_large_same_sign |
| 5 | AGC_166 | Singuilucan | 18 | 1.21224 | 0.84615 | 1.00000 | 0.00000 | recurrent_large_same_sign |
| 6 | AGC_122 | Calpulalpan | 52 | 1.08161 | 0.66923 | 1.00000 | 0.38462 | recurrent_large_same_sign |
| 7 | AGC_160 | Chignahuapan | 4 | 1.01503 | 0.65385 | 1.00000 | 0.15385 | recurrent_large_same_sign |
| 8 | AGC_041 | Singuilucan | 19 | 1.09574 | 0.65000 | 1.00000 | 0.00000 | recurrent_large_same_sign |
| 9 | AGC_035 | Cuautepec de Hinojosa | 12 | 0.98521 | 0.61538 | 1.00000 | 0.00000 | recurrent_large_same_sign |
| 10 | AGC_026 | Chignahuapan | 14 | 0.80778 | 0.53077 | 1.00000 | 0.00000 | recurrent_large_same_sign |
| 11 | AGC_138 | Calpulalpan | 38 | 0.89639 | 0.43077 | 1.00000 | 0.07692 | other_or_model_compensation |
| 12 | AGC_058 | Calpulalpan | 38 | 0.84488 | 0.42692 | 1.00000 | 0.07692 | other_or_model_compensation |
| 13 | AGC_001 | Calpulalpan | 51 | 0.78768 | 0.42692 | 1.00000 | 0.15385 | other_or_model_compensation |
| 14 | AGC_169 | Calpulalpan | 38 | 0.89486 | 0.42308 | 1.00000 | 0.07692 | other_or_model_compensation |

Signo se define predicho−observado. Errores constantes de signo, signos variables y compensaciones entre modelos se conservan en `case_model_protocol_details.csv`. Las banderas de soporte abarcan solo tres covariables deC. No hay evidencia independiente de error de etiqueta; la tabla es una agenda de verificación documental/campo, no una lista de exclusión. Registro primario, superficie y fechas deben verificarse antes de atribuir causas individuales.

## 9. Heterogeneidad intraperfil

| index | scope | n | n_profiles | SS_total | SS_within | SS_between | fraction_within | fraction_between | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | all_labels | 138 | 43 | 99.25303 | 25.35581 | 73.89722 | 0.25547 | 0.74453 | descriptive label decomposition; not explained predictive variance or causal contribution |
| 1 | Chignahuapan | 71 | 11 | 23.90619 | 20.51580 | 3.39039 | 0.85818 | 0.14182 | descriptive label decomposition; not explained predictive variance or causal contribution |

SS_total=SS_entre+SS_dentro es una identidad descriptiva ponderada por parcelas. La fracción entre perfiles no equivale a varianza causalmente explicada por clima ni aR² predictivo fuera de muestra. Los perfiles singleton tienen SS_dentro0 por construcción.

En las 138 etiquetas, 74.4534% de la suma de cuadrados queda entre perfiles y 25.5466% dentro. En Chignahuapan, 85.8179% queda dentro de perfiles y 14.1821% entre ellos. El problema local tiene una estructura distinta del contraste regional; esas proporciones no son una cota del error reducible ni explicación causal del clima. Los casos AGC_171, AGC_015 y AGC_024 mantienen sobreestimación alta entre modelos/protocolos y son prioridades documentales, sin evidencia de etiqueta incorrecta.

| index | profile | scope | n | n_possible_pairs | y_mean | y_variance | y_min | y_max | ndvi_mean | ndvi_sd | ndvi_min | ndvi_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 4 | full_profile | 29 | 406 | 4.64517 | 0.34910 | 2.64000 | 5.59000 | 0.14972 | 0.02513 | 0.09600 | 0.19500 |
| 1 | 4 | Chignahuapan_only | 29 | 406 | 4.64517 | 0.34910 | 2.64000 | 5.59000 | 0.14972 | 0.02513 | 0.09600 | 0.19500 |
| 4 | 24 | full_profile | 34 | 561 | 4.37794 | 0.32716 | 2.15000 | 5.57000 | 0.14669 | 0.02803 | 0.11820 | 0.27500 |
| 5 | 24 | Chignahuapan_only | 33 | 528 | 4.37091 | 0.33565 | 2.15000 | 5.57000 | 0.14702 | 0.02840 | 0.11820 | 0.27500 |

| index | experiment | protocol | scope | repeat | n_profiles | mean_pair_MSE | equal_profile_MAE | equal_profile_RMSE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | B2 | climate_profile | full_profile | 1.00000 | 12.00000 | 0.29026 | 0.39158 | 0.53876 |
| 2 | B2 | climate_profile | outside_Chignahuapan | 1.00000 | 10.00000 | 0.22002 | 0.34690 | 0.46906 |
| 4 | B2 | municipality | full_profile | 1.00000 | 12.00000 | 0.27580 | 0.34730 | 0.52517 |
| 5 | B2 | municipality | outside_Chignahuapan | 1.00000 | 10.00000 | 0.20359 | 0.30535 | 0.45121 |
| 7 | B2 | random | full_profile | 5.50000 | 8.60000 | 0.34497 | 0.42947 | 0.58335 |
| 8 | B2 | random | outside_Chignahuapan | 5.50000 | 6.40000 | 0.26052 | 0.39452 | 0.49992 |
| 10 | B2 | spatial | full_profile | 1.00000 | 12.00000 | 0.28704 | 0.37853 | 0.53576 |
| 11 | B2 | spatial | outside_Chignahuapan | 1.00000 | 10.00000 | 0.21899 | 0.34411 | 0.46797 |
| 13 | B3 | climate_profile | full_profile | 1.00000 | 12.00000 | 0.28578 | 0.38394 | 0.53459 |
| 14 | B3 | climate_profile | outside_Chignahuapan | 1.00000 | 10.00000 | 0.21762 | 0.33992 | 0.46650 |
| 16 | B3 | municipality | full_profile | 1.00000 | 12.00000 | 0.29093 | 0.35657 | 0.53938 |
| 17 | B3 | municipality | outside_Chignahuapan | 1.00000 | 10.00000 | 0.21836 | 0.31547 | 0.46729 |
| 19 | B3 | random | full_profile | 5.50000 | 8.60000 | 0.34264 | 0.42340 | 0.58116 |
| 20 | B3 | random | outside_Chignahuapan | 5.50000 | 6.40000 | 0.25960 | 0.38806 | 0.49802 |
| 22 | B3 | spatial | full_profile | 1.00000 | 12.00000 | 0.29423 | 0.38287 | 0.54243 |
| 23 | B3 | spatial | outside_Chignahuapan | 1.00000 | 10.00000 | 0.22656 | 0.34882 | 0.47598 |
| 25 | C-H0M | climate_profile | full_profile | 1.00000 | 12.00000 | 0.28994 | 0.39117 | 0.53846 |
| 26 | C-H0M | climate_profile | outside_Chignahuapan | 1.00000 | 10.00000 | 0.21687 | 0.34105 | 0.46569 |
| 28 | C-H0M | municipality | full_profile | 1.00000 | 12.00000 | 0.27113 | 0.34815 | 0.52070 |
| 29 | C-H0M | municipality | outside_Chignahuapan | 1.00000 | 10.00000 | 0.19987 | 0.30748 | 0.44707 |
| 31 | C-H0M | random | full_profile | 5.50000 | 8.60000 | 0.35380 | 0.43485 | 0.59062 |
| 32 | C-H0M | random | outside_Chignahuapan | 5.50000 | 6.40000 | 0.26919 | 0.39922 | 0.50788 |
| 34 | C-H0M | spatial | full_profile | 1.00000 | 12.00000 | 0.28163 | 0.37237 | 0.53069 |
| 35 | C-H0M | spatial | outside_Chignahuapan | 1.00000 | 10.00000 | 0.21217 | 0.33667 | 0.46062 |
| 37 | C-T1 | climate_profile | full_profile | 1.00000 | 12.00000 | 0.29484 | 0.37419 | 0.54299 |
| 38 | C-T1 | climate_profile | outside_Chignahuapan | 1.00000 | 10.00000 | 0.20282 | 0.30924 | 0.45036 |
| 40 | C-T1 | municipality | full_profile | 1.00000 | 12.00000 | 0.26926 | 0.32593 | 0.51890 |
| 41 | C-T1 | municipality | outside_Chignahuapan | 1.00000 | 10.00000 | 0.18616 | 0.27591 | 0.43146 |
| 43 | C-T1 | random | full_profile | 5.50000 | 8.60000 | 0.38155 | 0.42761 | 0.61041 |
| 44 | C-T1 | random | outside_Chignahuapan | 5.50000 | 6.40000 | 0.28683 | 0.37871 | 0.51558 |
| 46 | C-T1 | spatial | full_profile | 1.00000 | 12.00000 | 0.28412 | 0.35413 | 0.53303 |
| 47 | C-T1 | spatial | outside_Chignahuapan | 1.00000 | 10.00000 | 0.20282 | 0.30924 | 0.45036 |
| 49 | C-T3 | climate_profile | full_profile | 1.00000 | 12.00000 | 0.30018 | 0.40197 | 0.54789 |
| 50 | C-T3 | climate_profile | outside_Chignahuapan | 1.00000 | 10.00000 | 0.22801 | 0.35293 | 0.47751 |
| 52 | C-T3 | municipality | full_profile | 1.00000 | 12.00000 | 0.27143 | 0.35217 | 0.52099 |
| 53 | C-T3 | municipality | outside_Chignahuapan | 1.00000 | 10.00000 | 0.20005 | 0.31214 | 0.44727 |
| 55 | C-T3 | random | full_profile | 5.50000 | 8.60000 | 0.35288 | 0.43574 | 0.58995 |
| 56 | C-T3 | random | outside_Chignahuapan | 5.50000 | 6.40000 | 0.26935 | 0.40173 | 0.50842 |
| 58 | C-T3 | spatial | full_profile | 1.00000 | 12.00000 | 0.29176 | 0.38376 | 0.54015 |
| 59 | C-T3 | spatial | outside_Chignahuapan | 1.00000 | 10.00000 | 0.22463 | 0.35035 | 0.47395 |
| 61 | CHAMPION | random | full_profile | 5.50000 | 8.60000 | 0.36550 | 0.43060 | 0.59729 |
| 62 | CHAMPION | random | outside_Chignahuapan | 5.50000 | 6.40000 | 0.27746 | 0.38571 | 0.50681 |
| 64 | F4-E2 | climate_profile | full_profile | 1.00000 | 12.00000 | 0.29026 | 0.39158 | 0.53876 |
| 65 | F4-E2 | climate_profile | outside_Chignahuapan | 1.00000 | 10.00000 | 0.22002 | 0.34690 | 0.46906 |
| 67 | F4-E2 | municipality | full_profile | 1.00000 | 12.00000 | 0.27580 | 0.34730 | 0.52517 |
| 68 | F4-E2 | municipality | outside_Chignahuapan | 1.00000 | 10.00000 | 0.20359 | 0.30535 | 0.45121 |
| 70 | F4-E2 | random | full_profile | 5.50000 | 8.60000 | 0.34497 | 0.42947 | 0.58335 |
| 71 | F4-E2 | random | outside_Chignahuapan | 5.50000 | 6.40000 | 0.26052 | 0.39452 | 0.49992 |
| 73 | F4-E2 | spatial | full_profile | 1.00000 | 12.00000 | 0.28704 | 0.37853 | 0.53576 |
| 74 | F4-E2 | spatial | outside_Chignahuapan | 1.00000 | 10.00000 | 0.21899 | 0.34411 | 0.46797 |
| 76 | F4-S1 | climate_profile | full_profile | 1.00000 | 12.00000 | 0.29613 | 0.39741 | 0.54417 |
| 77 | F4-S1 | climate_profile | outside_Chignahuapan | 1.00000 | 10.00000 | 0.22405 | 0.34841 | 0.47334 |
| 79 | F4-S1 | municipality | full_profile | 1.00000 | 12.00000 | 0.27774 | 0.34857 | 0.52701 |
| 80 | F4-S1 | municipality | outside_Chignahuapan | 1.00000 | 10.00000 | 0.20779 | 0.30798 | 0.45584 |
| 82 | F4-S1 | random | full_profile | 5.50000 | 8.60000 | 0.35175 | 0.43441 | 0.58920 |
| 83 | F4-S1 | random | outside_Chignahuapan | 5.50000 | 6.40000 | 0.26622 | 0.39845 | 0.50572 |
| 85 | F4-S1 | spatial | full_profile | 1.00000 | 12.00000 | 0.29027 | 0.38036 | 0.53877 |
| 86 | F4-S1 | spatial | outside_Chignahuapan | 1.00000 | 10.00000 | 0.22243 | 0.34618 | 0.47162 |
| 88 | FIXED_50_50 | random | full_profile | 5.50000 | 8.60000 | 0.35177 | 0.42776 | 0.58787 |
| 89 | FIXED_50_50 | random | outside_Chignahuapan | 5.50000 | 6.40000 | 0.26623 | 0.38829 | 0.50170 |

Las parejas se calculan solo cuando las dos parcelas fueron evaluadas por el mismo ajuste externo. En aleatoria muchos pares entre folds no son evaluables para esta métrica; cada protocolo tiene soporte distinto. Tablas por perfil reportan n_parejas/n_parcelas y dispersión de predicciones. Las934parejas posibles locales no son934observaciones independientes. Ninguna línea resuelve la heterogeneidad de manera general; B3 añade un beneficio local pequeño con costo municipal inaceptable.

EtapaA: 727/934 parejas presentan geología250k distinta; 480 además tienen NDVI similar. Soporte de categorías:

| index | climate_profile | unit_key | n_labels | mean_share |
| --- | --- | --- | --- | --- |
| 0 | 4 | Q(al) | 2 | 0.53757 |
| 1 | 4 | Ts(A) | 10 | 0.65509 |
| 2 | 4 | Ts(R) | 17 | 0.78677 |
| 3 | 4 | Ts(Ta) | 8 | 0.99985 |
| 4 | 24 | Q(al) | 9 | 0.73541 |
| 5 | 24 | Ts(B) | 15 | 0.91827 |
| 6 | 24 | Ts(R) | 8 | 0.79427 |
| 7 | 24 | Ts(R-Ta) | 9 | 0.69479 |

Son contrastes repetidos en solo dos perfiles, con categorías escasas y reservas de límites. La no redundancia descriptiva respecto a NDVI no demuestra contribución incremental. Se justificaría una investigación futura separada si se verifican unidades/límites y se amplían grupos, no integración automática. Suelo50k no existe en el repositorio; imagen1996 es topográfica; PDF SGM2017 no proporciona geometría temática fiable. D no reabre esas fuentes.

Parcelas semejantes enX pueden diferir en variedad, fecha de siembra, densidad, fertilización, malezas, agua, profundidad/textura, enfermedades, cosecha o calidad de registro. Son variables no observadas hipotéticas; residuo no equivale a error irreducible.

## 10. Escenarios y decisiones

| index | model_or_hypothesis | decision_state | question_specification | evidence_result | utility_scope | external_evidence_pending | risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Champion | Referencia histórica | Arquitectura clima→historia→terreno | Mejor referencia histórica aleatoria evaluada; sin OOF geográfica equivalente | S1 | Faltan validación externa y reconstrucción geográfica compatible | Exploratorio; reutilización de 138 etiquetas; asociaciones no causales |
| 1 | FIXED_50_50 | Candidato congelado | Media fija Champion/F4-S1 | Mejora aleatoria pequeña; influencia concentrada; extremos no uniformes | S1 | Comparación externa frente a Champion; no nuevos pesos | Exploratorio; reutilización de 138 etiquetas; asociaciones no causales |
| 2 | F4-S1 | Candidato congelado | Lluvia mensual + NDVI mayo | Control climático parcelario parsimonioso; heterogeneidad local persiste | S1/S2/S3/S4/S5 | Campañas y municipios independientes | Exploratorio; reutilización de 138 etiquetas; asociaciones no causales |
| 3 | C-T3 | Candidato congelado | Lluvia compacta + NDVI mayo | Ventaja municipal; mejora espacial concentrada y costo aleatorio | S3 principal; S2 secundario | Municipios nuevos y costo aleatorio/local | Exploratorio; reutilización de 138 etiquetas; asociaciones no causales |
| 4 | C-H0M | Control metodológico | Gaussian Ridge sin intercepto aleatorio | Separa cambio L2 de efecto jerárquico | S2/S3/S4/S5 | Control externo bajo mismo procedimiento | Exploratorio; reutilización de 138 etiquetas; asociaciones no causales |
| 5 | C-T1 | Candidato congelado | Lluvia mensual + SD temporal DTR | Hipótesis espacial; depende del bloque 3 | S4 experimental | Regiones nuevas con/sin covariables del bloque3 | Exploratorio; reutilización de 138 etiquetas; asociaciones no causales |
| 6 | F4-E2 / B2 | Control metodológico | Añade inicio ascenso LAI a F4-S1 | Mejora local pequeña, sin ventaja global uniforme | S5 | Fechas reales y prueba local independiente | Exploratorio; reutilización de 138 etiquetas; asociaciones no causales |
| 7 | B1/B3 | No recomendado bajo la formulación evaluada | Objetivo y selección intraperfil | Costo municipal excesivo; cambio hiperparámetros incluso lambda0 | Metodológico | No priorizar más complejidad sobre estas etiquetas | Exploratorio; reutilización de 138 etiquetas; asociaciones no causales |
| 8 | C-H1 | No recomendado bajo la formulación evaluada | Intercepto aleatorio de perfil | No supera H0M; ratio0 frecuente; intervalos municipales subcubren | Metodológico | Más grupos repetidos si se retoma la hipótesis | Exploratorio; reutilización de 138 etiquetas; asociaciones no causales |
| 9 | C-T2/C-T4 | Exploratorio sin prioridad | NDVI + DTR mensuales/compactos | No reúne fortalezas de forma general | Comparación conceptual | No abrir nuevas combinaciones retrospectivas | Exploratorio; reutilización de 138 etiquetas; asociaciones no causales |
| 10 | J/K/L suelo y terreno | Exploratorio sin prioridad | Adiciones/correcciones y representaciones de bloques | Asociación propia no garantiza incremento estable sobre clima | Descriptivo regional/local | Suelo medido, escala y soporte de categorías | Exploratorio; reutilización de 138 etiquetas; asociaciones no causales |
| 11 | M histórico/multisensor | Exploratorio sin prioridad | Índices actuales e historia; raw/PCA | Ganancias cambian por arquitectura/protocolo; no integración automática | Descriptivo y controles | Campañas independientes, calidad y corte temporal | Exploratorio; reutilización de 138 etiquetas; asociaciones no causales |
| 12 | Familia2 FPCA/SOF | Exploratorio sin prioridad | Funciones temporales e híbridos | Interpretación temporal sin superar controles de manera suficiente | Interpretativo | No reabrir concurso de parametrizaciones | Exploratorio; reutilización de 138 etiquetas; asociaciones no causales |
| 13 | Familia3 factores/interacciones | No recomendado bajo la formulación evaluada | Estructura y condicionamiento climático | Interacciones no justifican expertos/GMM supervisados | Metodológico | Más datos y nueva hipótesis previa si se retoma | Exploratorio; reutilización de 138 etiquetas; asociaciones no causales |
| 14 | Screening1473 | Exploratorio sin prioridad | Ridge univariado + asociaciones | Descubrimiento retrospectivo; no evaluación imparcial de selección | Generación de hipótesis | Validar candidatos fijados sin volver a seleccionar | Exploratorio; reutilización de 138 etiquetas; asociaciones no causales |
| 15 | Suelo50k / SGM50k | Suspendido por datos | Cartografía local solicitada | Suelo inexistente; PDF geológico sin geometría temática fiable | Inventario | Fuente oficial vectorial y auditoría geométrica | Exploratorio; reutilización de 138 etiquetas; asociaciones no causales |
| 16 | Geología250k | Exploratorio sin prioridad | Composición parcelaria existente | Contrastes locales repetidos, sin ganancia incremental demostrada | Descriptivo intraperfil | Verificar límites y soporte; no integración en D | Exploratorio; reutilización de 138 etiquetas; asociaciones no causales |

S1:Champion como referencia histórica y mezcla como candidato exploratorio; S2:compararF4-S1/T3/H0M sin confundir perfil con municipio; S3:T3 es candidato principal observado, con costo aleatorio y local; S4:no hay ganador espacial robusto general; S5:E2 ofrece una mejora local pequeña, H0M sirve de control yB3 no se promueve. No hay ponderación retrospectiva para combinar escenarios.

La sensibilidad municipal existente de T3 está preservada en `municipal_fold_omission_archived.csv`: el beneficio RMSE persiste al omitir cada fold del cálculo, pero MAE puede deteriorar ligeramente al omitir uno. Su costo aleatorio e intraperfil está en las tablas compatibles. La persistencia de RMSE no implica que cada municipio ni cada parcela mejore.

## 11. Incertidumbre y límites

| index | experiment | protocol | stratum | n | coverage | mean_width | min_width | max_width |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 83 | C-H1 | climate_profile | Chignahuapan | 71.00000 | 0.88732 | 1.57853 | 1.55254 | 1.76205 |
| 84 | C-H1 | climate_profile | Q1 | 36.00000 | 0.77778 | 1.71958 | 1.55437 | 2.00904 |
| 85 | C-H1 | climate_profile | Q2 | 33.00000 | 0.90909 | 1.67927 | 1.55254 | 1.96645 |
| 86 | C-H1 | climate_profile | Q3 | 35.00000 | 1.00000 | 1.60699 | 1.55255 | 1.74144 |
| 87 | C-H1 | climate_profile | Q4 | 34.00000 | 0.88235 | 1.59539 | 1.55270 | 1.76205 |
| 88 | C-H1 | climate_profile | all | 138.00000 | 0.89130 | 1.65079 | 1.55254 | 2.00904 |
| 89 | C-H1 | climate_profile | municipality:Almoloya | 10.00000 | 1.00000 | 1.70162 | 1.66028 | 1.74144 |
| 90 | C-H1 | climate_profile | municipality:Apan | 1.00000 | 1.00000 | 1.68490 | 1.68490 | 1.68490 |
| 91 | C-H1 | climate_profile | municipality:Calpulalpan | 30.00000 | 0.86667 | 1.73296 | 1.66525 | 2.00904 |
| 92 | C-H1 | climate_profile | municipality:Chignahuapan | 71.00000 | 0.88732 | 1.57853 | 1.55254 | 1.76205 |
| 93 | C-H1 | climate_profile | municipality:Cuautepec de Hinojosa | 5.00000 | 0.80000 | 1.66385 | 1.55582 | 1.72373 |
| 94 | C-H1 | climate_profile | municipality:Emiliano Zapata | 3.00000 | 1.00000 | 1.73029 | 1.72529 | 1.73381 |
| 95 | C-H1 | climate_profile | municipality:Nanacamilpa de Mariano Arista | 1.00000 | 1.00000 | 1.64999 | 1.64999 | 1.64999 |
| 96 | C-H1 | climate_profile | municipality:Singuilucan | 16.00000 | 0.87500 | 1.76207 | 1.65917 | 1.83218 |
| 97 | C-H1 | climate_profile | municipality:Tepeapulco | 1.00000 | 1.00000 | 1.68977 | 1.68977 | 1.68977 |
| 98 | C-H1 | climate_profile | new_profile | 138.00000 | 0.89130 | 1.65079 | 1.55254 | 2.00904 |
| 99 | C-H1 | climate_profile | state:Hidalgo | 36.00000 | 0.91667 | 1.72484 | 1.55582 | 1.83218 |
| 100 | C-H1 | climate_profile | state:Puebla | 71.00000 | 0.88732 | 1.57853 | 1.55254 | 1.76205 |
| 101 | C-H1 | climate_profile | state:Tlaxcala | 31.00000 | 0.87097 | 1.73029 | 1.64999 | 2.00904 |
| 102 | C-H1 | climate_profile | without_Chignahuapan | 67.00000 | 0.89552 | 1.72736 | 1.55582 | 2.00904 |
| 103 | C-H1 | municipality | Chignahuapan | 71.00000 | 0.84507 | 1.42181 | 1.34712 | 1.65094 |
| 104 | C-H1 | municipality | Q1 | 36.00000 | 0.75000 | 1.93923 | 1.40461 | 2.63810 |
| 105 | C-H1 | municipality | Q2 | 33.00000 | 0.78788 | 1.74916 | 1.37797 | 2.62847 |
| 106 | C-H1 | municipality | Q3 | 35.00000 | 0.97143 | 1.49067 | 1.34712 | 1.79045 |
| 107 | C-H1 | municipality | Q4 | 34.00000 | 0.79412 | 1.46861 | 1.38250 | 1.74328 |
| 108 | C-H1 | municipality | all | 138.00000 | 0.82609 | 1.66406 | 1.34712 | 2.63810 |
| 109 | C-H1 | municipality | known_profile | 43.00000 | 0.93023 | 1.47268 | 1.38250 | 1.80626 |
| 110 | C-H1 | municipality | municipality:Almoloya | 10.00000 | 1.00000 | 1.71714 | 1.65780 | 1.79045 |
| 111 | C-H1 | municipality | municipality:Apan | 1.00000 | 1.00000 | 1.68124 | 1.68124 | 1.68124 |
| 112 | C-H1 | municipality | municipality:Calpulalpan | 30.00000 | 0.90000 | 2.07692 | 1.74874 | 2.63810 |
| 113 | C-H1 | municipality | municipality:Chignahuapan | 71.00000 | 0.84507 | 1.42181 | 1.34712 | 1.65094 |
| 114 | C-H1 | municipality | municipality:Cuautepec de Hinojosa | 5.00000 | 0.80000 | 1.61872 | 1.58045 | 1.66800 |
| 115 | C-H1 | municipality | municipality:Emiliano Zapata | 3.00000 | 1.00000 | 1.74306 | 1.67638 | 1.87303 |
| 116 | C-H1 | municipality | municipality:Nanacamilpa de Mariano Arista | 1.00000 | 1.00000 | 1.59022 | 1.59022 | 1.59022 |
| 117 | C-H1 | municipality | municipality:Singuilucan | 16.00000 | 0.50000 | 1.93459 | 1.77837 | 2.01206 |
| 118 | C-H1 | municipality | municipality:Tepeapulco | 1.00000 | 0.00000 | 1.66515 | 1.66515 | 1.66515 |
| 119 | C-H1 | municipality | new_profile | 95.00000 | 0.77895 | 1.75069 | 1.34712 | 2.63810 |
| 120 | C-H1 | municipality | state:Hidalgo | 36.00000 | 0.72222 | 1.79983 | 1.58045 | 2.01206 |
| 121 | C-H1 | municipality | state:Puebla | 71.00000 | 0.84507 | 1.42181 | 1.34712 | 1.65094 |
| 122 | C-H1 | municipality | state:Tlaxcala | 31.00000 | 0.90323 | 2.06122 | 1.59022 | 2.63810 |
| 123 | C-H1 | municipality | without_Chignahuapan | 67.00000 | 0.80597 | 1.92077 | 1.58045 | 2.63810 |
| 124 | C-H1 | random | Chignahuapan | 71.00000 | 0.89155 | 1.58538 | 1.41807 | 1.85847 |
| 125 | C-H1 | random | Q1 | 36.00000 | 0.83889 | 1.65119 | 1.42140 | 1.98680 |
| 126 | C-H1 | random | Q2 | 33.00000 | 0.91818 | 1.64679 | 1.41857 | 2.05507 |
| 127 | C-H1 | random | Q3 | 35.00000 | 0.99143 | 1.60102 | 1.41953 | 1.83789 |
| 128 | C-H1 | random | Q4 | 34.00000 | 0.89118 | 1.60598 | 1.41905 | 1.85760 |
| 129 | C-H1 | random | all | 138.00000 | 0.90942 | 1.62627 | 1.41807 | 2.08362 |
| 130 | C-H1 | random | known_profile | 105.50000 | 0.92989 | 1.60595 | 1.41866 | 1.85683 |
| 131 | C-H1 | random | municipality:Almoloya | 10.00000 | 1.00000 | 1.66305 | 1.48765 | 1.80630 |
| 132 | C-H1 | random | municipality:Apan | 1.00000 | 1.00000 | 1.67738 | 1.67738 | 1.67738 |
| 133 | C-H1 | random | municipality:Calpulalpan | 30.00000 | 0.97333 | 1.66942 | 1.46704 | 1.98807 |
| 134 | C-H1 | random | municipality:Chignahuapan | 71.00000 | 0.89155 | 1.58538 | 1.41807 | 1.85847 |
| 135 | C-H1 | random | municipality:Cuautepec de Hinojosa | 5.00000 | 0.80000 | 1.63975 | 1.50226 | 1.75869 |
| 136 | C-H1 | random | municipality:Emiliano Zapata | 3.00000 | 1.00000 | 1.77437 | 1.61507 | 1.98142 |
| 137 | C-H1 | random | municipality:Nanacamilpa de Mariano Arista | 1.00000 | 1.00000 | 1.71219 | 1.71219 | 1.71219 |
| 138 | C-H1 | random | municipality:Singuilucan | 16.00000 | 0.83125 | 1.66020 | 1.49146 | 1.81277 |
| 139 | C-H1 | random | municipality:Tepeapulco | 1.00000 | 0.70000 | 1.67599 | 1.67599 | 1.67599 |
| 140 | C-H1 | random | new_profile | 32.50000 | 0.84313 | 1.69220 | 1.46756 | 2.08362 |
| 141 | C-H1 | random | state:Hidalgo | 36.00000 | 0.88889 | 1.66858 | 1.46140 | 2.02661 |
| 142 | C-H1 | random | state:Puebla | 71.00000 | 0.89155 | 1.58538 | 1.41807 | 1.85847 |
| 143 | C-H1 | random | state:Tlaxcala | 31.00000 | 0.97419 | 1.67080 | 1.46577 | 1.99284 |
| 144 | C-H1 | random | without_Chignahuapan | 67.00000 | 0.92836 | 1.66961 | 1.44963 | 2.08362 |
| 145 | C-H1 | spatial | Chignahuapan | 71.00000 | 0.94366 | 2.12859 | 1.32328 | 2.71582 |
| 146 | C-H1 | spatial | Q1 | 36.00000 | 0.80556 | 2.85787 | 1.57446 | 3.88064 |
| 147 | C-H1 | spatial | Q2 | 33.00000 | 1.00000 | 2.46801 | 1.56727 | 3.85498 |
| 148 | C-H1 | spatial | Q3 | 35.00000 | 1.00000 | 2.09044 | 1.57423 | 2.71452 |
| 149 | C-H1 | spatial | Q4 | 34.00000 | 0.94118 | 2.09954 | 1.32328 | 2.71582 |
| 150 | C-H1 | spatial | all | 138.00000 | 0.93478 | 2.38317 | 1.32328 | 3.88064 |
| 151 | C-H1 | spatial | known_profile | 37.00000 | 0.94595 | 1.58342 | 1.32328 | 1.85342 |
| 152 | C-H1 | spatial | municipality:Almoloya | 10.00000 | 1.00000 | 1.89444 | 1.77337 | 2.02164 |
| 153 | C-H1 | spatial | municipality:Apan | 1.00000 | 1.00000 | 2.26629 | 2.26629 | 2.26629 |
| 154 | C-H1 | spatial | municipality:Calpulalpan | 30.00000 | 0.86667 | 3.17227 | 2.26373 | 3.88064 |
| 155 | C-H1 | spatial | municipality:Chignahuapan | 71.00000 | 0.94366 | 2.12859 | 1.32328 | 2.71582 |
| 156 | C-H1 | spatial | municipality:Cuautepec de Hinojosa | 5.00000 | 0.80000 | 1.65096 | 1.57520 | 1.75216 |
| 157 | C-H1 | spatial | municipality:Emiliano Zapata | 3.00000 | 1.00000 | 2.45593 | 2.18442 | 2.59308 |
| 158 | C-H1 | spatial | municipality:Nanacamilpa de Mariano Arista | 1.00000 | 1.00000 | 2.81852 | 2.81852 | 2.81852 |
| 159 | C-H1 | spatial | municipality:Singuilucan | 16.00000 | 1.00000 | 2.57600 | 2.11761 | 2.82380 |
| 160 | C-H1 | spatial | municipality:Tepeapulco | 1.00000 | 1.00000 | 1.71173 | 1.71173 | 1.71173 |
| 161 | C-H1 | spatial | new_profile | 101.00000 | 0.93069 | 2.67615 | 1.56727 | 3.88064 |
| 162 | C-H1 | spatial | state:Hidalgo | 36.00000 | 0.97222 | 2.21558 | 1.57520 | 2.82380 |
| 163 | C-H1 | spatial | state:Puebla | 71.00000 | 0.94366 | 2.12859 | 1.32328 | 2.71582 |
| 164 | C-H1 | spatial | state:Tlaxcala | 31.00000 | 0.87097 | 3.16086 | 2.26373 | 3.88064 |
| 165 | C-H1 | spatial | without_Chignahuapan | 67.00000 | 0.92537 | 2.65295 | 1.57520 | 3.88064 |

Intervalos realmente generados:90% Gaussian working posterior, con sigma/ratio/alpha fijados por ajuste/CV. Incluyen ruido residual, incertidumbre condicional del intercepto y covarianza de efectos fijos bajo regularización; nuevos perfiles añaden tau². Omiten incertidumbre de hiperparámetros, selección, especificación, fuentes/medición y cambio de dominio. No son intervalos plenamente bayesianos ni garantías de cobertura.

La cobertura y ancho por perfil conocido/nuevo y protocolo muestran subcobertura municipal nueva y mayor amplitud espacial. H1 selecciona ratio0 en 36/50ajustes aleatorios; solo12grupos repetidos limitan evidencia de varianza no nula. D no calibra un nuevo método. Investigación futura necesita conjuntos independientes de calibración/evaluación y suficientes grupos/campañas, sin garantías automáticas de bootstrapparcelario o conformal estándar bajo cambio de dominio.

## 12. Diseño independiente y 13. Información adicional

Ver `prospective_validation_protocol.md`: estimandos R_similar/R_newmun/R_newseason, gruposV1–V5, candidatos fijos, reglas pendientes explícitas, precisión agrupada, sellado previo aY, tratamientos de faltantes/soporte y comparaciones incompletas. No se fija un tamaño óptimo inventado ni se entrena el modelo final enD.

| index | source | question | required_variation | resolution | availability | relative_cost | current_limitation | validation_needed | priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Rendimiento y superficie cosechada | ¿Los casos persistentes están correctamente registrados? | Dentro de perfil | Parcela; campaña y fecha exactas | 138Y existentes; documentos primarios pendientes | Bajo-medio, cualitativo | Errores persistentes y extremos | Auditoría ciega a preferencia de modelo | 1: necesario para todos los estimandos |
| 1 | Siembra/cosecha y variedad | ¿NDVI mayo mezcla fases o cultivos? | Dentro de perfil y entre campañas | Fechas diarias; variedad por parcela | No verificadas como campos completos | Bajo-medio, cualitativo | NDVI en fecha fija; dinámica no fenología validada | V1/V5, registro antes de Y | 1: identifica comparabilidad temporal |
| 2 | Fertilización/manejo/malezas/enfermedades | ¿Contrastes locales corresponden a manejo? | Dentro de perfil | Dosis, fechas y eventos por parcela | Pendiente de levantamiento | Medio, cualitativo | Grandes diferencias climáticamente idénticas | V1, varios grupos repetidos | 2: variación local efectiva |
| 3 | Riego/condiciones hídricas | ¿Clima regional omite agua disponible? | Dentro de perfil | Eventos y fuente; parcela/campaña | Pendiente de verificación | Medio, cualitativo | Lluvia de malla común no representa manejo hídrico | V1/V3, observación independiente | 2: hipótesis agronómica concreta |
| 4 | Textura/profundidad de suelo medidas | ¿Suelo real aporta contraste no captado por cartografía? | Dentro de perfil | Muestras georreferenciadas y profundidades registradas | Pendiente; coberturas250k no son mediciones | Medio-alto, cualitativo | Resolución y semántica cartográfica | Submuestra V1 estratificada sin elegir por Y | 2: medir antes de ampliar índices |
| 5 | Suelo local de mayor resolución | ¿El mapa distingue propiedades y límites reales? | Dentro de perfil | Escala documentada, fecha y geometría validada | Fuente50k no presente | Desconocido; requiere cotización | Ausencia fuente edafológica local | Verificación campo y comparación de límites | 3: condicionada a disponibilidad |
| 6 | Geología oficial vectorial50k | ¿Contrastes250k persisten a escala más fina? | Dentro de perfil | Polígonos oficiales, CRS y fecha verificadas | PDF SGM2017 existe; vector no verificado | Desconocido; no estimación monetaria | Límites250k y PDF no clasificable | V1, categorías repetidas y reservas de límite | 3: no ganancia predictiva demostrada |
| 7 | Rendimientos de nuevas campañas | ¿Las señales actuales transfieren en el tiempo? | Entre campañas y dentro de municipios | Campaña completa; varias campañas para inferencia temporal | No disponibles como etiquetas independientes verificadas | Alto por seguimiento, cualitativo | Solo etiquetas2025 | V5, sin mezclar con comparación geográfica | 1: falta central de validación temporal |
| 8 | Calidad/fechas imágenes | ¿Disponibilidad satelital afecta señales y comparabilidad? | Dentro de perfil y entre campañas | Fechas de adquisición, nubes, gaps, cultivo y cobertura | Soporte procesado existente; verificación campo pendiente | Bajo-medio, cualitativo | Índices redundantes y ventanas distintas | V1/V5, reglas predefinidas | 1: control de medición y corte temporal |

## 14. Síntesis científica transversal

Clima distingue contextos, pero una malla compartida no distingue parcelas con vectores iguales. NDVI mayo aporta estado observado y contraste local; no asegura misma fase fenológica. LAI se deriva de SAVI por la ecuaciónFIRA y no es una fuente espectral independiente. Redundancia conSAVI/FAPAR/EVI no es identidad perfecta; las asociaciones parciales deF4-E delimitan evidencia, no justifican otro screening. Descriptores hasta octubre no deben presentarse como predictores disponibles enmayo.

Terreno/suelo/geología pueden tener importancia agronómica aun cuando no mejoren incrementalmente estos modelos. Escala250k, clases con pocas etiquetas, redundancia regional y errores de medición limitan su uso; DEM120m tampoco mide microtopografía ni humedad observada. EnJ/K una arquitectura residual reduce ciertos deterioros de la adición directa, sin demostrar beneficio estable de cada bloque. L/M muestran quePCA y sumar sensores/historia no crean información nueva automáticamente ni una ventaja común entre protocolos.

La pérdida intraperfilB no logró una mejora útil general. Lambda0 puede coexistir con peor validación por cambio de selecciónalpha/rho; no atribuir todo el efecto a una penalización activa. C muestra otra separación: mejoras frente aEN pueden provenir deL2, no de interceptos aleatorios. Para perfiles nuevos el efecto medio es0; conocido no equivale a transferible, y el intercepto cancela en diferencias del mismo perfil.

Compactar lluvia es regularización estructural: reduce siete coeficientes mensuales a tres descriptores, pero fracción/HHI son funciones no lineales del vector original; no es simplemente una rotaciónPCA ni un mecanismo probado. Puede limitar extrapolación de coeficientes mensuales, hipótesis consistente con desempeño municipal, peroRMSE no demuestra esa explicación.

Familias2/3 aportaron interpretación funcional/estructural sin justificar mayor complejidad predictiva. Screening1473 seleccionó señales retrospectivamente sobre las mismas138Y:NDVI/DTR no se descubrieron en una muestra independiente. El propio screening ya evaluóNDVI mayo solo; su predicción global individual fue inferior a lluvia. No confundir esa evidencia con una nueva prueba autorizada de invertir la arquitectura residual, queD no ejecuta.

La complejidad puede distribuir información limitada de manera inestable. Estos resultados distinguen límites de medición/datos y de las hipótesis evaluadas; no prueban que todos los algoritmos complejos fracasen ni que todos los residuos sean inmodelables.

## 15. Conclusiones, 16. Limitaciones y 17. Trabajo futuro

RespuestasD1–D7: concentración y reversión se documentan porIDs/bloques; bloque3 se caracteriza sin causalidad; los candidatos dependen del estimando; heterogeneidad local permanece; validar municipios/campañas y medir manejo/fechas/suelo real es más informativo que otro concurso; se congelan hipótesis/control sin ajuste final;138Y permiten evidencia exploratoria dentro de los protocolos existentes, no generalización nacional/temporal confirmada.

No independencia entre repeticiones, folds entrenados con datos solapados, parejas o modelos aliados; pocas unidades geográficas; regiones definidas con covariables disponibles; múltiples hipótesis retrospectivas; cartografía histórica; ausencia de nuevosY. Omisiones e influencia son sensibilidades descriptivas, no intervalos/p-valores confirmatorios. D no entrena, optimiza, combina pesos, corrige etiquetas, elimina parcelas ni produce nuevas predicciones.

Trabajo futuro se limita al protocolo prospectivo y adquisición, no nuevos experimentos enD. Las cuotas, margen de utilidad y reglas finales de entrenamiento pendientes deben sellarse antes deYexterna. Mantener reportesA–C inmutables, incluso cuando sus frases históricas dicen que etapas posteriores aún no se habían ejecutado.


## Visualizaciones

![01_availability](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_d/figures/01_availability.png)

![02_compatible_errors](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_d/figures/02_compatible_errors.png)

![03_geographic_blocks](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_d/figures/03_geographic_blocks.png)

![04_block_covariates](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_d/figures/04_block_covariates.png)

![05_block_gains](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_d/figures/05_block_gains.png)

![06_block_omission](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_d/figures/06_block_omission.png)

![07_paired_losses](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_d/figures/07_paired_losses.png)

![08_gain_concentration](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_d/figures/08_gain_concentration.png)

![09_dominant_profiles](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_d/figures/09_dominant_profiles.png)

![10_support_map](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_d/figures/10_support_map.png)

![11_scenario_matrix](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_d/figures/11_scenario_matrix.png)

![12_external_design](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_d/figures/12_external_design.png)