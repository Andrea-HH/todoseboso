> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# L/M — Síntesis transversal

Se preservaron E–K, fuentes originales y modelo TOP20/TOP15. Se usan138etiquetas,59parcelas sinY,53perfiles completos y los65folds congelados. Las métricas se calculan sobre cada OOF completo138 y luego se promedian las10repeticiones aleatorias.

1. **Base climática.** Lluvia y Climate Current48 tienen resultados aleatorios cercanos. Los valores por protocolo son:

| experiment | protocol | RMSE_mean | MAE_mean | R2_mean |
| --- | --- | --- | --- | --- |
| L0_BASE | climate_profile | 0.5444 | 0.3903 | 0.5880 |
| L1_BASE | climate_profile | 0.5403 | 0.4027 | 0.5941 |
| L0_BASE | municipality | 0.6954 | 0.5002 | 0.3277 |
| L1_BASE | municipality | 0.7773 | 0.5928 | 0.1598 |
| L0_BASE | random | 0.5214 | 0.3695 | 0.6220 |
| L1_BASE | random | 0.5200 | 0.3693 | 0.6240 |
| L0_BASE | spatial | 0.7348 | 0.5620 | 0.2493 |
| L1_BASE | spatial | 0.9798 | 0.7796 | -0.3349 |

Se compara representación mensual de lluvia con una representación agregada más amplia que incluye temperatura: no es un efecto aislado de temperatura. Climate Current48 tampoco es TOP20 ni el modelo TOP20/TOP15.

2. **PCA edafológico y arquitectura.** Ganancias deRMSE positivas favorecen al candidato. Misma S1 y mismas grillas en controles:

| base | block | protocol | PCA_vs_original_residual | residual_vs_direct_PCA |
| --- | --- | --- | --- | --- |
| rain | soil | random | 0.0004 | 0.0037 |
| rain | soil | climate_profile | -0.0141 | -0.0068 |
| rain | soil | municipality | -0.2446 | -0.2725 |
| rain | soil | spatial | -0.0073 | 0.3382 |
| rain | topo_soil | random | 0.0019 | 0.0025 |
| rain | topo_soil | climate_profile | 0.0032 | -0.0048 |
| rain | topo_soil | municipality | 0.0082 | 0.0072 |
| rain | topo_soil | spatial | 0.0124 | 0.1866 |
| current | soil | random | 0.0010 | 0.0069 |
| current | soil | climate_profile | 0.0002 | -0.0256 |
| current | soil | municipality | 0.0003 | 0.0602 |
| current | soil | spatial | -0.0174 | -0.0232 |
| current | topo_soil | random | 0.0040 | 0.0073 |
| current | topo_soil | climate_profile | -0.0054 | -0.0403 |
| current | topo_soil | municipality | 0.0253 | 0.0413 |
| current | topo_soil | spatial | 0.0627 | -0.0262 |

PCA rota y reduce el espacio, pero no añade información intrínseca ni interacciones. Elastic Net L1 cambia geometría al rotar ejes; se distinguen cambio de representación y arquitectura. Los signos dePCs locales no se comparan ciegamente entre folds.

3. **Después del modelo TOP20/TOP15.** Solo auditoría descriptiva de su residuo final OOF y asociaciones totales/intra/interperfil. L8 no se evaluó predictivamente: no se dispone de cross-fitting de las tres etapas con selección íntegramente anidada para reproducir fielmente el original. Las asociaciones no demuestran ganancia incremental ni justifican reentrenarlo.

4. **Historia, Planet y Landsat.** Incrementos controlados frente a Sentinel y otras combinaciones:

| question | representation | protocol | baseline | candidate | delta_RMSE | delta_MAE |
| --- | --- | --- | --- | --- | --- | --- |
| history | RAW | random | M0 | M1 | 0.0612 | 0.0449 |
| history | RAW | climate_profile | M0 | M1 | -0.0003 | 0.0042 |
| history | RAW | municipality | M0 | M1 | 0.1130 | 0.1251 |
| history | RAW | spatial | M0 | M1 | -0.1018 | -0.1057 |
| Planet | RAW | random | M0 | M2 | 0.0406 | 0.0314 |
| Planet | RAW | climate_profile | M0 | M2 | 0.0547 | 0.0607 |
| Planet | RAW | municipality | M0 | M2 | -0.0051 | -0.0138 |
| Planet | RAW | spatial | M0 | M2 | -0.0004 | 0.0154 |
| Landsat | RAW | random | M0 | M3 | 0.0284 | 0.0294 |
| Landsat | RAW | climate_profile | M0 | M3 | 0.0285 | 0.0254 |
| Landsat | RAW | municipality | M0 | M3 | 0.0599 | 0.0458 |
| Landsat | RAW | spatial | M0 | M3 | 0.0271 | 0.0218 |
| Landsat_given_Planet | RAW | random | M2 | M4 | 0.0058 | 0.0090 |
| Landsat_given_Planet | RAW | climate_profile | M2 | M4 | 0.0326 | 0.0340 |
| Landsat_given_Planet | RAW | municipality | M2 | M4 | 0.0144 | 0.0113 |
| Landsat_given_Planet | RAW | spatial | M2 | M4 | 0.0050 | -0.0073 |
| history_given_multisensor | RAW | random | M4 | M5 | 0.0158 | 0.0104 |
| history_given_multisensor | RAW | climate_profile | M4 | M5 | -0.0832 | -0.0855 |
| history_given_multisensor | RAW | municipality | M4 | M5 | 0.0195 | 0.0304 |
| history_given_multisensor | RAW | spatial | M4 | M5 | -0.1053 | -0.1111 |
| multisensor_given_history | RAW | random | M1 | M5 | 0.0010 | 0.0059 |
| multisensor_given_history | RAW | climate_profile | M1 | M5 | 0.0043 | 0.0050 |
| multisensor_given_history | RAW | municipality | M1 | M5 | -0.0842 | -0.0972 |
| multisensor_given_history | RAW | spatial | M1 | M5 | 0.0011 | 0.0027 |
| history | BLOCK_PCA | random | M0 | M1 | -0.0518 | -0.0502 |
| history | BLOCK_PCA | climate_profile | M0 | M1 | -0.1685 | -0.1914 |
| history | BLOCK_PCA | municipality | M0 | M1 | -0.1328 | -0.1764 |
| history | BLOCK_PCA | spatial | M0 | M1 | -0.1439 | -0.1787 |
| Planet | BLOCK_PCA | random | M0 | M2 | -0.0333 | -0.0268 |
| Planet | BLOCK_PCA | climate_profile | M0 | M2 | -0.0538 | -0.0491 |
| Planet | BLOCK_PCA | municipality | M0 | M2 | -0.0510 | -0.0609 |
| Planet | BLOCK_PCA | spatial | M0 | M2 | -0.0354 | -0.0240 |
| Landsat | BLOCK_PCA | random | M0 | M3 | 0.0033 | -0.0004 |
| Landsat | BLOCK_PCA | climate_profile | M0 | M3 | -0.0124 | -0.0313 |
| Landsat | BLOCK_PCA | municipality | M0 | M3 | -0.2031 | -0.2609 |
| Landsat | BLOCK_PCA | spatial | M0 | M3 | -0.1178 | -0.1592 |
| Landsat_given_Planet | BLOCK_PCA | random | M2 | M4 | 0.0111 | 0.0078 |
| Landsat_given_Planet | BLOCK_PCA | climate_profile | M2 | M4 | -0.0348 | -0.0611 |
| Landsat_given_Planet | BLOCK_PCA | municipality | M2 | M4 | -0.0645 | -0.0940 |
| Landsat_given_Planet | BLOCK_PCA | spatial | M2 | M4 | -0.0354 | -0.0740 |
| history_given_multisensor | BLOCK_PCA | random | M4 | M5 | -0.0184 | -0.0175 |
| history_given_multisensor | BLOCK_PCA | climate_profile | M4 | M5 | -0.0468 | -0.0389 |
| history_given_multisensor | BLOCK_PCA | municipality | M4 | M5 | -0.0182 | -0.0195 |
| history_given_multisensor | BLOCK_PCA | spatial | M4 | M5 | -0.0544 | -0.0505 |
| multisensor_given_history | BLOCK_PCA | random | M1 | M5 | 0.0111 | 0.0135 |
| multisensor_given_history | BLOCK_PCA | climate_profile | M1 | M5 | 0.0331 | 0.0422 |
| multisensor_given_history | BLOCK_PCA | municipality | M1 | M5 | -0.0010 | 0.0021 |
| multisensor_given_history | BLOCK_PCA | spatial | M1 | M5 | 0.0187 | 0.0302 |

La filaBLOCK_PCA usa presupuestos totales1/2/4, ajustados internamente; dimensiones efectivamente elegidas están en tabla35. Raw cambia número de variables: una ganancia allí no se atribuye exclusivamente a nueva información sin contrastar presupuesto.

Las anomalías actuales−historia son deterministas a partir de esas dos fuentes. Familia1 ya contenía resúmenes históricos/anomalías; tabla05M identifica superposición. M estudia trayectoria mensual, soporte y diferencias de distribución, no un primer descubrimiento de historia. La referencia2022–24 no incluye2025 y no es una normal climatológica.

Planet solo tiene2025 en Básico/PRO; sus datos agregados no permiten inventar percentiles espaciales de píxeles. NDVI/EVI compartidos no certifican ecuaciones/bandas idénticas ni calibración. LandsatVI6T se trata como bloque propio. Comparación por calendario no equivale a misma fecha ni prueba que la resolución cause una mejora.

5. **Transferencia y futura integración.** Cribado con mejora aleatoria y sin deterioro>.01 de RMSEagrupado/MAEen todos los protocolos:

| experiment | base | random_RMSE_gain | worst_grouped_RMSE_gain | worst_MAE_gain | passes_metric_margins |
| --- | --- | --- | --- | --- | --- |
| L2 | rain | -0.0006 | -0.2903 | -0.2673 | False |
| LC_rain_soil_residual_raw | rain | -0.0010 | -0.0457 | -0.0472 | False |
| LC_rain_soil_direct_pca | rain | -0.0043 | -0.3452 | -0.2639 | False |
| LC_rain_soil_direct_raw | rain | -0.0080 | -0.2679 | -0.2276 | False |
| L4 | rain | 0.0020 | -0.0106 | -0.0204 | False |
| LC_rain_topo_soil_residual_raw | rain | 0.0000 | -0.0188 | -0.0218 | False |
| LC_rain_topo_soil_direct_pca | rain | -0.0006 | -0.1734 | -0.1660 | False |
| LC_rain_topo_soil_direct_raw | rain | -0.0076 | -0.2324 | -0.2687 | False |
| L6_HELL_DIRECT | rain | 0.0008 | -0.2763 | -0.2037 | False |
| L6_HELL_JOINT_PCA | rain | -0.0158 | -0.2014 | -0.1329 | False |
| LC_rain_S2_RAW_DIRECT | rain | -0.0007 | -0.2829 | -0.2122 | False |
| L3 | current | -0.0001 | -0.0396 | -0.0607 | False |
| LC_current_soil_residual_raw | current | -0.0011 | -0.0223 | -0.0212 | False |
| LC_current_soil_direct_pca | current | -0.0070 | -0.0587 | -0.0294 | False |
| LC_current_soil_direct_raw | current | -0.0111 | -0.0631 | -0.0319 | False |
| L5 | current | 0.0028 | -0.0111 | -0.0686 | False |
| LC_current_topo_soil_residual_raw | current | -0.0012 | -0.0710 | -0.0978 | False |
| LC_current_topo_soil_direct_pca | current | -0.0045 | -0.0235 | -0.0218 | False |
| LC_current_topo_soil_direct_raw | current | -0.0080 | 0.0078 | -0.0110 | False |
| L7_HELL_DIRECT | current | 0.0022 | -0.0005 | -0.0111 | False |
| L7_HELL_JOINT_PCA | current | -0.0470 | -0.1100 | -0.1203 | False |
| LC_current_S2_RAW_DIRECT | current | -0.0008 | -0.0072 | -0.0043 | False |

| experiment | base | random_RMSE_gain | worst_grouped_RMSE_gain | worst_MAE_gain | passes_metric_margins |
| --- | --- | --- | --- | --- | --- |
| MA_rain_M0 | rain | -0.0074 | -0.1927 | -0.2542 | False |
| MR_rain_M0 | rain | -0.0038 | -0.0129 | -0.0095 | False |
| MA_current_M0 | current | -0.0147 | -0.2624 | -0.3001 | False |
| MR_current_M0 | current | -0.0013 | -0.0162 | -0.0165 | False |
| MA_rain_M1 | rain | -0.0397 | -0.0775 | -0.1090 | False |
| MR_rain_M1 | rain | -0.0035 | -0.0959 | -0.0942 | False |
| MA_current_M1 | current | -0.0223 | -0.0470 | -0.0564 | False |
| MR_current_M1 | current | -0.0025 | -0.0433 | -0.0402 | False |
| MA_rain_M5 | rain | -0.0488 | -0.1430 | -0.1783 | False |
| MR_rain_M5 | rain | -0.0043 | -0.2048 | -0.1987 | False |
| MA_current_M5 | current | -0.0222 | -0.0125 | -0.0293 | False |
| MR_current_M5 | current | -0.0031 | -0.1816 | -0.1516 | False |

Estas pantallas son exploratorias, no significancia ni decisión automática. Para integración hacen falta además estabilidad, soporte, ausencia de correcciones extremas, mejora intraperfil y validación con nuevas etiquetas/geografías. Los folds/repeticiones comparten observaciones. Ningún resultado cambiaChampion.

6. **Suelo tras satélite.** Tabla32M informa asociaciones residuales de suelo tras clima+M5. Es exploración fuera de muestra, no una tercera etapa validada ni prueba de mejora predictiva adicional.

Diagnósticos específicos: Chignahuapan71etiquetas pertenece al mismoOOF; parejas intraperfil solo por un mismo modelo externo; nubes/faltantes y reservas50/125/250m se retienen. Suelo1:250000 es cartografía temática, topografíaCEM4 tiene120m local, clima≈.05°, resoluciones satelitales son referencias de sensor no grillas verificadas de extracción. Fechas de procesamiento/disponibilidad y cultivos históricos no se suministran; los máximos no validan fenología. No hay etiquetas históricas para validar transferencia a otro año.

Reportes: [L](l_multiblock_representation.md), [M](m_historical_multisensor.md).

## Respuestas para toma de decisiones

1. La lluvia mensual es la base m?s robusta para transferencia municipal y espacial. Climate Current aporta una representaci?n m?s amplia y rinde parecido en aleatorio, pero generaliza peor en esos protocolos. No es una comparaci?n exclusivamente de temperatura.

2. PCA de suelo resume bien la estructura: cuatro componentes de S1 explican95.4% de la varianza. No muestra mejora predictiva consistente frente a originales estabilizadas. PCA conjunto1/2/4 pierde direcciones ?tiles para rendimiento, aunque retenga estructura geogr?fica.

3. La correcci?n residual evita algunas degradaciones de mezclas directas, pero sueloPCA no supera consistentemente a lluvia. Topograf?a+sueloPCAresidual sobre lluvia logra.5194aleatorio/.7215espacial, frente a.5214/.7348, con deterioro municipal.7060frente a.6954. No cumple todos los m?rgenes, ni mejora el antecedente de pendiente residual en K para aleatorio. Hellinger directo sobre Climate Current mejora el perfil(.4994), pero su espacial(.9763) queda lejos de lluvia(.7348).

4. Hay asociaciones descriptivas de suelo en el residuo finalChampion; no se demostr? utilidad predictiva posterior. L8 conserva ?nicamente la auditor?a por falta de reconstrucci?n fiel y trazabilidad plenamente anidada de las tres etapas. No se entren? sobre residuos OOF globales.

5. La historia de Sentinel mejora el modelo satelital independiente en aleatorio(.6921?.6310) y municipal(.9894?.8763), pero empeora espacial(.9064?1.0082). Sus correcciones no a?aden ganancia consistente sobre clima. Anomal?as medias nuevas y anteriores se correlacionan.994?.999: gran parte es informaci?n ya utilizada, no una nueva fuente.

6. Planet mejora al Sentinel independiente en aleatorio(.6921?.6515) y perfil(.7363?.6816), con espacial pr?cticamente igual. Landsat complementario mejora tambi?n municipal(.9894?.9295) y espacial(.9064?.8792), aunque VI6T no se considera equivalente a NDVI. Mezclar todo mejora poco sobre Sentinel+historia en aleatorio(.6310?.6299) y no resuelve su deterioro espacial. No se atribuyen esas diferencias ?nicamente a resoluci?n.

7. El corrector de Sentinel2025 sobre lluvia ofrece el mejor resultado espacial entre las variantes L/M(.6813frente a lluvia.7348), pero empeora aleatorio(.5252frente a.5214) y municipal(.7083frente a.6954). Es un compromiso para investigar transferencia, no un ganador general. Los sat?lites por s? solos no superan la base clim?tica. La compresi?n de pocos componentes satelitales empeora en general a las variables originales; futuras cantidades mayores requerir?an otro dise?o predefinido, no retuning de estos resultados.

8. Ninguna variante L/M supera la pantalla completa de mejora aleatoria y m?rgenes RMSE/MAE en todos los protocolos. Candidata exploratoria para validaci?n externa: lluvia+correctorSentinel actual con objetivo espacial, junto con el antecedente de pendiente residual K. No hay una integraci?n autom?tica ni reemplazo del modelo TOP20/TOP15. La informaci?n edafol?gica posterior a sat?lite sigue siendo diagn?stico descriptivo, no una tercera etapa validada.

Estos resultados corresponden a las representaciones, cuatro ?ndicesSentinel seleccionados y Elastic Net estudiados. No prueban irrelevancia agron?mica de suelo, historia o sensores, ni generalizaci?n a otro a?o sin nuevas etiquetas. Los folds/repeticiones se superponen y las mejoras peque?as no constituyen confirmaci?n independiente.
