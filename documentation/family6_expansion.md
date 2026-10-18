> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# F6-E — Expansión informada de variables

**Primera batería completada: E0 recuperado; E1 historia2, E2 pendiente y E3 DTR ajustados. E4/E5 no ejecutados. Referencias y modelo TOP20/TOP15 intactos; sin modelo final/PRED.**

## Métricas OOF completas

| experiment | climate_profile | municipality | random | spatial |
| --- | --- | --- | --- | --- |
| C-T3 | 0.520604 | 0.581259 | 0.511582 | 0.678778 |
| CHAMPION | nan | nan | 0.498127 | nan |
| F5-01 | 0.499759 | 0.544208 | 0.504006 | 0.734797 |
| F6-00 | 0.527190 | 0.608372 | 0.514005 | 0.762037 |
| F6-E0 | 0.512979 | 0.638586 | 0.506296 | 0.758923 |
| F6-E1 | 0.506796 | 0.675872 | 0.509249 | 0.741689 |
| F6-E2 | 0.510588 | 0.662413 | 0.508354 | 0.735425 |
| F6-E3 | 0.526775 | 0.665630 | 0.515563 | 0.788119 |

RMSE en t/ha. Se calculan138 OOF por repetición y luego el promedio de diez repeticiones aleatorias; no se promedian RMSE de folds como métrica primaria. Los folds y repeticiones comparten parcelas: no se declara superioridad estadística. E0 reproduce exactamente F6-01; F6-00 se conserva solo como contexto RF. modelo TOP20/TOP15 y etapas se comparan únicamente en los50 folds aleatorios compatibles.

## Utilidad incremental por bloque — ablación con reajuste

| candidate | protocol | delta_RMSE | delta_MAE | delta_bias |
| --- | --- | --- | --- | --- |
| F6-E1 | climate_profile | -0.006184 | 0.005095 | 0.000521 |
| F6-E1 | municipality | 0.037286 | 0.047409 | -0.011267 |
| F6-E1 | random | 0.002952 | 0.011546 | -0.004122 |
| F6-E1 | spatial | -0.017234 | -0.007649 | -0.032643 |
| F6-E2 | climate_profile | -0.002392 | -0.000106 | 0.002730 |
| F6-E2 | municipality | 0.023827 | 0.028199 | -0.015694 |
| F6-E2 | random | 0.002058 | 0.010509 | -0.004679 |
| F6-E2 | spatial | -0.023498 | -0.024024 | -0.006650 |
| F6-E3 | climate_profile | 0.013796 | 0.013246 | -0.000900 |
| F6-E3 | municipality | 0.027044 | 0.020695 | 0.002014 |
| F6-E3 | random | 0.009267 | 0.010936 | -0.002492 |
| F6-E3 | spatial | 0.029196 | 0.034894 | -0.039494 |

Negativo favorece la extensión. E0 y las extensiones se ajustaron y retunearon independientemente dentro de entrenamiento, con el mismo motor, ocho configuraciones,384 árboles y65 particiones. La ablación de quitar el bloque es el núcleo E0 ya ajustado: se recuperan sus modelos y OOF en lugar de duplicar ajustes idénticos. No es enmascarar columnas de un modelo ampliado.

| experiment | block | delta_RMSE_municipal | delta_RMSE_spatial | max_RMSE_MAE_harm | n_spatial_blocks_improved | max_spatial_omission_delta | max_municipal_omission_delta | delta_intraprofile_spatial | delta_intraprofile_municipal | descriptive_promise |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F6-E1 | HIST_S2_ndvi_promedio_mean;HIST_S2_ndvi_promedio_std | 0.037286 | -0.017234 | 0.047409 | 4 | -0.005436 | 0.049563 | -0.010975 | -0.000985 | False |
| F6-E2 | TOPO_BASIC_slope_mean | 0.023827 | -0.023498 | 0.028199 | 4 | -0.009101 | 0.033969 | -0.005297 | 0.000618 | False |
| F6-E3 | CLIMATE_dtr_mean_std | 0.027044 | 0.029196 | 0.034894 | 2 | 0.039025 | 0.055491 | -0.001361 | -0.000918 | False |

La columna descriptive_promise usa el margen orientativo0.01 de F6 para describir una ganancia geográfica con daños pequeños; no es un gate prospectivo nuevo ni una selección automática. Los nuevos bloques fueron explícitamente autorizados después del cierre compacto y se evaluaron los tres, sin buscar entre1354 variables. La misma fracción max_features se conserva, pero el número efectivo de candidatas cambia cuando cambia la dimensión; esa regularización se registra.

**F6-E1 (HIST_S2_ndvi_promedio_mean; HIST_S2_ndvi_promedio_std):** ΔRMSE frente a E0 en aleatoria/perfil/municipal/espacial = +0.00295, -0.00618, +0.03729, -0.01723. Las diferencias de MAE y sesgo se reportan aparte; ganancia en un protocolo no implica transferencia uniforme.
**F6-E2 (TOPO_BASIC_slope_mean):** ΔRMSE frente a E0 en aleatoria/perfil/municipal/espacial = +0.00206, -0.00239, +0.02383, -0.02350. Las diferencias de MAE y sesgo se reportan aparte; ganancia en un protocolo no implica transferencia uniforme.
**F6-E3 (CLIMATE_dtr_mean_std):** ΔRMSE frente a E0 en aleatoria/perfil/municipal/espacial = +0.00927, +0.01380, +0.02704, +0.02920. Las diferencias de MAE y sesgo se reportan aparte; ganancia en un protocolo no implica transferencia uniforme.

**La representación sí influye parcialmente:** historia mejora RMSE espacial0.01723 y pendiente0.02350 t/ha frente a E0, con mejoras en cuatro de cinco bloques en ambos casos. No resuelven el conjunto de transferencia: deterioran RMSE municipal0.03729 y0.02383, respectivamente, y sus RMSE espaciales0.74169/0.73542 aún superan0.67878 de C-T3. No se declara una representación ganadora global.

**Historia aporta la señal local más diferenciada de esta batería:** RMSE de diferencias intraperfil espacial0.52004 frente a0.53101 de E0 (igual peso por perfil), y también mejora el ponderado por pares0.78512 frente a0.79265. Esa fortaleza no se repite en aleatoria y el resultado municipal global empeora. Pendiente ofrece una mejora local espacial menor con igual peso, pero no con ponderación por pares. La variación fina de X no garantiza que sea señal predictiva transferible.

**DTR debilita la hipótesis de una partición térmica útil bajo Extra Trees compacto:** empeora los cuatro RMSE y MAE frente a E0. En aleatoria aparece en87.5% de árboles y39.9% de raíces, con impureza descriptiva≈30.2%; esa frecuencia alta contrasta con la falta de utilidad incremental. No demuestra causalidad ni rechaza temperatura bajo otros métodos o representaciones.

## Diagnóstico regional, intraperfil y concentración

| candidate | fold | n | delta_RMSE | bias_candidate | bias_base | SSE_gain | bias_squared_gain | error_variance_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F6-E1 | 1 | 38 | -0.000796 | -0.109654 | -0.062726 | 0.032454 | -0.307399 | 0.339853 |
| F6-E1 | 2 | 37 | -0.011667 | -0.223294 | -0.223801 | 0.511915 | 0.008388 | 0.503527 |
| F6-E1 | 3 | 35 | -0.040084 | 0.854065 | 0.898232 | 2.859424 | 2.708774 | 0.150650 |
| F6-E1 | 4 | 18 | -0.023010 | 0.659899 | 0.692293 | 0.744491 | 0.788432 | -0.043941 |
| F6-E1 | 5 | 10 | 0.054413 | -0.518292 | -0.457165 | -0.579489 | -0.596263 | 0.016774 |
| F6-E2 | 1 | 38 | -0.003144 | -0.071621 | -0.062726 | 0.127922 | -0.045407 | 0.173329 |
| F6-E2 | 2 | 37 | -0.022532 | -0.147376 | -0.223801 | 0.979575 | 1.049587 | -0.070012 |
| F6-E2 | 3 | 35 | -0.012300 | 0.884396 | 0.898232 | 0.889385 | 0.863226 | 0.026159 |
| F6-E2 | 4 | 18 | -0.105388 | 0.554482 | 0.692293 | 3.253515 | 3.092741 | 0.160774 |
| F6-E2 | 5 | 10 | 0.038562 | -0.501427 | -0.457165 | -0.404573 | -0.424287 | 0.019714 |
| F6-E3 | 1 | 38 | -0.000543 | -0.042573 | -0.062726 | 0.022156 | 0.080643 | -0.058486 |
| F6-E3 | 2 | 37 | 0.040227 | -0.303876 | -0.223801 | -1.842301 | -1.563392 | -0.278909 |
| F6-E3 | 3 | 35 | 0.019734 | 0.923250 | 0.898232 | -1.449073 | -1.594915 | 0.145842 |
| F6-E3 | 4 | 18 | -0.025376 | 0.629944 | 0.692293 | 0.819963 | 1.483901 | -0.663937 |
| F6-E3 | 5 | 10 | 0.290767 | -0.757819 | -0.457165 | -3.783886 | -3.652902 | -0.130984 |

Se analizan los cinco bloques, incluido3, sin optimizar sobre ninguno. La ganancia SSE se descompone algebraicamente en reducción del sesgo cuadrado y reducción de dispersión de errores (ddof0). Omisiones de bloques, municipios y top1/5/10 casos recalculan OOF existentes, sin reajustar ni eliminar etiquetas de entrenamiento. Los archivos fold_omission_sensitivity.csv y municipality_omission_sensitivity.csv contienen todos los contrastes.

| experiment | protocol | n_pairs | n_profiles | n_parcels | equal_profile_RMSE | equal_profile_MAE | pair_weighted_RMSE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F6-E0 | climate_profile | 1073.000000 | 12.000000 | 107.000000 | 0.546051 | 0.387558 | 0.783407 |
| F6-E0 | municipality | 1034.000000 | 12.000000 | 103.000000 | 0.521596 | 0.332620 | 0.796176 |
| F6-E0 | random | 208.400000 | 8.600000 | 87.700000 | 0.608918 | 0.439535 | 0.798473 |
| F6-E0 | spatial | 1007.000000 | 12.000000 | 106.000000 | 0.531013 | 0.351412 | 0.792651 |
| F6-E1 | climate_profile | 1073.000000 | 12.000000 | 107.000000 | 0.545117 | 0.391295 | 0.768613 |
| F6-E1 | municipality | 1034.000000 | 12.000000 | 103.000000 | 0.520611 | 0.341043 | 0.801339 |
| F6-E1 | random | 208.400000 | 8.600000 | 87.700000 | 0.613168 | 0.440078 | 0.800573 |
| F6-E1 | spatial | 1007.000000 | 12.000000 | 106.000000 | 0.520038 | 0.350394 | 0.785121 |
| F6-E2 | climate_profile | 1073.000000 | 12.000000 | 107.000000 | 0.553647 | 0.394469 | 0.785980 |
| F6-E2 | municipality | 1034.000000 | 12.000000 | 103.000000 | 0.522214 | 0.336557 | 0.795011 |
| F6-E2 | random | 208.400000 | 8.600000 | 87.700000 | 0.614028 | 0.447074 | 0.797610 |
| F6-E2 | spatial | 1007.000000 | 12.000000 | 106.000000 | 0.525716 | 0.355766 | 0.793952 |
| F6-E3 | climate_profile | 1073.000000 | 12.000000 | 107.000000 | 0.545501 | 0.385728 | 0.786804 |
| F6-E3 | municipality | 1034.000000 | 12.000000 | 103.000000 | 0.520678 | 0.334305 | 0.795557 |
| F6-E3 | random | 208.400000 | 8.600000 | 87.700000 | 0.610295 | 0.440577 | 0.800198 |
| F6-E3 | spatial | 1007.000000 | 12.000000 | 106.000000 | 0.529653 | 0.353820 | 0.796297 |

Diferencias intraperfil únicamente entre predicciones del mismo modelo externo. Hay12 perfiles repetidos; pares dependientes y pesos por perfil/pair distintos. La discriminación local no se confunde con separar perfiles de clima. Historia2 y pendiente varían en los12 perfiles repetidos; DTRstd no varía en ninguno. Por ello E3 puede cambiar particiones entre perfiles, pero no agrega resolución climática intraperfil.

| candidate | protocol | net_SSE_gain | top_positive_gain | fraction_net_gain | bottom_gain |
| --- | --- | --- | --- | --- | --- |
| F6-E1 | climate_profile | 0.870215 | 1.507532 | 1.732368 | -0.708913 |
| F6-E1 | municipality | -6.763509 | 1.071083 | -0.158362 | -1.804053 |
| F6-E1 | random | -0.414594 | 0.985498 | -2.377020 | -0.567318 |
| F6-E1 | spatial | 3.568794 | 1.195137 | 0.334885 | -0.729653 |
| F6-E2 | climate_profile | 0.337847 | 0.970495 | 2.872591 | -0.884257 |
| F6-E2 | municipality | -4.277809 | 0.879406 | -0.205574 | -1.144850 |
| F6-E2 | random | -0.290801 | 0.726216 | -2.497297 | -0.876218 |
| F6-E2 | spatial | 4.845824 | 2.228371 | 0.459854 | -0.985736 |
| F6-E3 | climate_profile | -1.979505 | 0.323699 | -0.163525 | -1.386661 |
| F6-E3 | municipality | -4.867348 | 0.347842 | -0.071464 | -2.375846 |
| F6-E3 | random | -1.309214 | 0.231015 | -0.176453 | -0.986330 |
| F6-E3 | spatial | -6.233140 | 0.964303 | -0.154706 | -2.549701 |

| candidate | protocol | n_remaining | delta_RMSE_pooled_mean_loss | delta_MAE | SSE_gain |
| --- | --- | --- | --- | --- | --- |
| F6-E1 | climate_profile | 133 | 0.005384 | 0.009806 | -0.637317 |
| F6-E1 | municipality | 133 | 0.050241 | 0.051721 | -7.834592 |
| F6-E1 | random | 133 | 0.010793 | 0.016173 | -1.400092 |
| F6-E1 | spatial | 133 | -0.012457 | -0.004436 | 2.373658 |
| F6-E2 | climate_profile | 133 | 0.005258 | 0.003185 | -0.632649 |
| F6-E2 | municipality | 133 | 0.031913 | 0.033248 | -5.157216 |
| F6-E2 | random | 133 | 0.008044 | 0.013904 | -1.017017 |
| F6-E2 | spatial | 133 | -0.013788 | -0.018674 | 2.617453 |
| F6-E3 | climate_profile | 133 | 0.016850 | 0.016279 | -2.303204 |
| F6-E3 | municipality | 133 | 0.030656 | 0.023054 | -5.215190 |
| F6-E3 | random | 133 | 0.012620 | 0.012301 | -1.540229 |
| F6-E3 | spatial | 133 | 0.035508 | 0.040163 | -7.197444 |

Las omisiones de parcelas usan medias de pérdida por parcela; su RMSE agregado no sustituye la media primaria de RMSE por repetición. Una fracción top5>100% indica compensación por deterioros en otros casos; con ganancia neta negativa esa razón no se interpreta como porcentaje de mejora.

## Qué aporta cada fuente

Historia representa nivel y estacionalidad de la firma histórica NDVI entre meses calendario, no variabilidad interanual ni todo History15/16. Pendiente es un descriptor estático del terreno; puede actuar como proxy territorial y no demuestra un mecanismo hídrico. DTRstd describe variabilidad temporal de la amplitud térmica; el campo no proporciona diferencias dentro de perfiles climáticos idénticos. Las asociaciones anteriores justificaron las hipótesis, pero únicamente las ablaciones OOF determinan utilidad incremental con Extra Trees.

| experiment | protocol | mean_delta_MSE | mean_delta_MAE | n_eligible_mean | n_profiles_mean | n_permutations |
| --- | --- | --- | --- | --- | --- | --- |
| F6-E0 | climate_profile | 0.007968 | 0.000664 | 21.400000 | 2.400000 | 50 |
| F6-E0 | municipality | 0.010677 | 0.000398 | 31.000000 | 2.666667 | 30 |
| F6-E0 | random | 0.006012 | 0.000818 | 17.540000 | 3.960000 | 500 |
| F6-E0 | spatial | 0.006739 | 0.001041 | 25.250000 | 2.750000 | 40 |
| F6-E1 | climate_profile | 0.006926 | 0.000599 | 21.400000 | 2.400000 | 50 |
| F6-E1 | municipality | 0.002609 | -0.002264 | 31.000000 | 2.666667 | 30 |
| F6-E1 | random | 0.004398 | -0.001772 | 17.540000 | 3.960000 | 500 |
| F6-E1 | spatial | 0.006120 | -0.000109 | 25.250000 | 2.750000 | 40 |
| F6-E2 | climate_profile | 0.001227 | -0.002043 | 21.400000 | 2.400000 | 50 |
| F6-E2 | municipality | 0.003339 | 0.000201 | 31.000000 | 2.666667 | 30 |
| F6-E2 | random | 0.006453 | -0.000715 | 17.540000 | 3.960000 | 500 |
| F6-E2 | spatial | 0.003210 | -0.002378 | 25.250000 | 2.750000 | 40 |

Permutación: el bloque histórico se mueve conjuntamente, manteniendo sus dos columnas emparejadas, entre parcelas del mismo perfil dentro de validación. Se repite diez veces si≥10 parcelas tienen variación del bloque. Condiciona sobre clima, no sobre todos los demás predictores; es dependencia predictiva descriptiva, no mecanismo causal. Un bloque constante o insuficiente se marca no identificable. DTRstd tiene precisamente ese límite: no se interpreta un cero mecánico como irrelevancia. No se usan permutaciones marginales que mezclen lluvia/DTR sin soporte.

ALE e interacciones se limitan a regiones respaldadas: q95 de distancia leave-one-out en entrenamiento define el radio; cada bin/celda requiere≥5 parcelas y≥80% de esquinas dentro del radio. Solo esas esquinas se predicen. Si falta soporte no se conecta la curva a través del hueco; se muestran cambios locales respaldados cuando existen. Distancias y cuantiles son propios de cada transformación/fold, no directamente comparables entre representaciones. Esta vecindad es aproximada y no certifica soporte físico ni causalidad. Se conserva el detalle por fit y la fracción respaldada en effects_by_outer_fit.csv, interactions_by_outer_fit.csv y ALE_support_summary.csv.

Interacciones examinadas exclusivamente: mayo×hist_mean, hist_mean×hist_std, mayo×pendiente, lluvia_total×pendiente, HHI×DTR y mayo×DTR. No se escanean pares adicionales. Umbrales en unidades originales, soporte de hojas y frecuencias de uso por árbol se conservan con dispersión entre ajustes. Frecuencia e impureza son descripciones, no evidencia suficiente de utilidad ni causalidad.

## Estabilidad y recomendaciones

| experiment | protocol | mean_RMS_difference | max_RMS_difference |
| --- | --- | --- | --- |
| F6-E0 | climate_profile | 0.012255 | 0.016194 |
| F6-E0 | municipality | 0.019988 | 0.035704 |
| F6-E0 | random | 0.006990 | 0.012940 |
| F6-E0 | spatial | 0.018540 | 0.043980 |
| F6-E1 | climate_profile | 0.012196 | 0.017357 |
| F6-E1 | municipality | 0.013814 | 0.030248 |
| F6-E1 | random | 0.008086 | 0.013975 |
| F6-E1 | spatial | 0.013388 | 0.020244 |
| F6-E2 | climate_profile | 0.010363 | 0.014926 |
| F6-E2 | municipality | 0.011108 | 0.016103 |
| F6-E2 | random | 0.008948 | 0.015733 |
| F6-E2 | spatial | 0.014606 | 0.026497 |
| F6-E3 | climate_profile | 0.008177 | 0.010431 |
| F6-E3 | municipality | 0.014075 | 0.018444 |
| F6-E3 | random | 0.007536 | 0.017277 |
| F6-E3 | spatial | 0.015919 | 0.023115 |

La variación entre prefijos256 y384 señala sensibilidad Monte Carlo;384 permanece fijo y no se abre otra búsqueda de árboles como respuesta a los resultados. La dispersión entre árboles no es un intervalo predictivo observacional.

| experiment | status | recommendation | reason |
| --- | --- | --- | --- |
| F6-E4 | no ejecutado | posponer: las ganancias espaciales tienen costes municipales importantes | La sinergia no está probada; no se suman beneficios individuales. Ganancias de E1/E2 se concentran en bloques3/4 y ambos perjudican muchas de las mismas parcelas municipales. |
| F6-E5 | no ejecutado | posponer; revisar primero E4 y un contraste de lluvia con bloques idénticos | Mensual7+historia2+pendiente cambia representación y bloques a la vez. Si se reabre, comparar contra E4 aislaría la representación de lluvia; no existe todavía evidencia mensual bagging. |

E4/E5 son propuestas para revisión, sin ejecución. Combinar ganancias individuales no garantiza sinergia; E5 debe contrastarse con E4 si se quiere atribuir la diferencia a la representación de lluvia. Una decisión basada en estas OOF externas continúa siendo exploratoria, no confirmación independiente ni promoción global.

**F7:** mantener como alternativa una comparación CatBoost/XGBoost directa con núcleo y los mismos bloques predefinidos; revisión técnica antes de ejecutar. No se asume que boosting resolverá la transferencia. Su selección y cualquier early stopping deben quedar dentro de entrenamiento externo. No se instala ni ejecuta F7 aquí.

## Síntesis de hipótesis y decisión revisada

La ganancia espacial de historia procede sobre todo del bloque3 (2.859 de3.569 SSE neta,≈80%); la de pendiente, del bloque4 (3.254 de4.846,≈67%). Al omitir esos bloques todavía queda mejora RMSE, pero se reduce a0.00544 para historia sin bloque3 y0.00910 para pendiente sin bloque4. Ambas ganancias espaciales sobreviven a omitir los cinco casos de mayor beneficio; son menos concentradas que las pequeñas ganancias aleatorias originales de F6.

Existe complementariedad espacial descriptiva:48.6% de parcelas mejoran con ambos bloques;9.4% solo con historia y13.0% solo con pendiente. En municipal63.0% empeoran con ambos. Esa coincidencia de deterioros es la principal objeción a recomendar E4 de inmediato. Los porcentajes usan medias de pérdida por parcela y no construyen un ensamble ni predicciones combinadas. La sinergia de un modelo conjunto permanece desconocida.

Las permutaciones indican dependencia local pequeña de historia y pendiente (aumentos MSE, cambios MAE pequeños y a menudo negativos). La frecuencia de uso es alta: historia_mean83.2%, historia_std91.5%, pendiente93.9% de árboles aleatorios; eso no revierte sus costes municipales. Las hojas conservan al menos cinco muestras, con medianas7–8 para E1/E2. El soporte multivariado es limitado: ninguna curva ALE completa de pendiente o DTR supera el gate, y la historia solo permite curvas completas en un fit de65 para su media y ninguno para std. Se entregan cambios locales y celdas respaldadas, sin llenar los huecos.

**Recomendación explícita:** posponer E4/E5 y preparar la propuesta F7 como siguiente línea. Conservar historia y pendiente como hipótesis de fortalezas espaciales/locales, no como añadidos aprobados a un modelo final. No hay evidencia equilibrada municipal/espacial para recomendar ampliar inmediatamente bagging. Si se decide reabrir F6 posteriormente, E4 debería preceder a E5 y abordar expresamente los deterioros municipales compartidos. Este resultado apoya una limitación parcial de la representación compacta, debilita el DTR como extensión Extra Trees evaluada y no rechaza todos los bloques históricos, toda topografía o todos los bosques.


## Verificación final

Pasaron nueve pruebas unitarias y de integración: aislamiento/restauración del adaptador, bloques/regulación originales, soporte antes de predicción, permutación conjunta/constancia, replay de975 modelos guardados, selección entre ocho candidatos y particiones internas originales, E0/OOF/métricas exactas, gates de soporte/hojas y hashes de código/cache/folds. Se verificaron 11576 archivos anteriores sin cambios. Se recuperó E0, se ajustaron195 modelos externos y6240 candidatos internos (6435 bosques en total), y se guardaron13938 filas OOF entre referencias y extensiones. No se ejecutaron E4/E5 ni F7, no se ajustó un modelo final y no se generaron59 predicciones PRED.
