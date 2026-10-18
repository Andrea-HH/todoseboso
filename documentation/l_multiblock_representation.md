> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# L — Multiblock Representation and Residual Complementarity

| experiment | protocol | RMSE_mean | MAE_mean | R2_mean | bias_pred_minus_y_mean |
| --- | --- | --- | --- | --- | --- |
| L0_BASE | climate_profile | 0.5444 | 0.3903 | 0.5880 | 0.0231 |
| L1_BASE | climate_profile | 0.5403 | 0.4027 | 0.5941 | 0.0439 |
| L0_BASE | municipality | 0.6954 | 0.5002 | 0.3277 | 0.0838 |
| L1_BASE | municipality | 0.7773 | 0.5928 | 0.1598 | 0.2280 |
| L0_BASE | random | 0.5214 | 0.3695 | 0.6220 | -0.0016 |
| L1_BASE | random | 0.5200 | 0.3693 | 0.6240 | 0.0002 |
| L0_BASE | spatial | 0.7348 | 0.5620 | 0.2493 | 0.3023 |
| L1_BASE | spatial | 0.9798 | 0.7796 | -0.3349 | 0.5015 |

Las dos bases reproducen J0/H8 a tolerancia1e-8, mismos65folds. Climate Current48 no es TOP20 ni modelo TOP20/TOP15. Es una comparación de representación completa, no un efecto exclusivo de temperatura.

| experiment | climate_profile | municipality | random | spatial |
| --- | --- | --- | --- | --- |
| L0_BASE | 0.5444 | 0.6954 | 0.5214 | 0.7348 |
| L1_BASE | 0.5403 | 0.7773 | 0.5200 | 0.9798 |
| L2 | 0.5674 | 0.9857 | 0.5220 | 0.7418 |
| L3 | 0.5402 | 0.7759 | 0.5202 | 1.0195 |
| L4 | 0.5439 | 0.7060 | 0.5194 | 0.7215 |
| L5 | 0.5514 | 0.7595 | 0.5172 | 0.9881 |
| L6_HELL_DIRECT | 0.5468 | 0.6983 | 0.5206 | 1.0111 |
| L6_HELL_JOINT_PCA | 0.6302 | 0.8968 | 0.5371 | 0.8356 |
| L7_HELL_DIRECT | 0.4995 | 0.7779 | 0.5178 | 0.9763 |
| L7_HELL_JOINT_PCA | 0.6503 | 0.7998 | 0.5670 | 1.0132 |
| LC_current_S2_RAW_DIRECT | 0.5328 | 0.7846 | 0.5208 | 0.8798 |
| LC_current_soil_direct_pca | 0.5146 | 0.8361 | 0.5270 | 0.9963 |
| LC_current_soil_direct_raw | 0.5336 | 0.8404 | 0.5311 | 1.0100 |
| LC_current_soil_residual_raw | 0.5404 | 0.7761 | 0.5211 | 1.0021 |
| LC_current_topo_soil_direct_pca | 0.5111 | 0.8008 | 0.5245 | 0.9620 |
| LC_current_topo_soil_direct_raw | 0.5325 | 0.7665 | 0.5280 | 0.9474 |
| LC_current_topo_soil_residual_raw | 0.5459 | 0.7849 | 0.5212 | 1.0508 |
| LC_rain_S2_RAW_DIRECT | 0.5464 | 0.6990 | 0.5220 | 1.0176 |
| LC_rain_soil_direct_pca | 0.5606 | 0.7132 | 0.5256 | 1.0800 |
| LC_rain_soil_direct_raw | 0.5582 | 0.7326 | 0.5294 | 1.0027 |
| LC_rain_soil_residual_raw | 0.5532 | 0.7410 | 0.5223 | 0.7344 |
| LC_rain_topo_soil_direct_pca | 0.5392 | 0.7131 | 0.5219 | 0.9082 |
| LC_rain_topo_soil_direct_raw | 0.5450 | 0.9055 | 0.5289 | 0.9671 |
| LC_rain_topo_soil_residual_raw | 0.5471 | 0.7142 | 0.5213 | 0.7339 |

S1 primaria:10coberturas solapadas que mencionan grupos, sin z-score. S2 sensibilidad:22unidades agrupadas con soporte>=5 por fit y Other. Hellinger h_j=sqrt(p_j): distancia Euclídea en raíces, ceros válidos sin CLR/pseudoconteos. Los PCA se centran sin whitening; PCs1/2/4 se seleccionan en CV interna. L2/L3 sueloPCAresidual; L4/L5 topografía+sueloPCAresidual; LC controles originales y PCAs directos con mismas variables y escalas. L6/L7 mezcla Hellinger, PCAconjunto y control S2natural. Los cambios por rotación también cambian penalización L1; no toda diferencia PCA procede de reducción dimensional.

El PCA descriptivo usa197parcelas o53perfiles de igual peso, sin usarse para preprocesar predicción. La ponderación equilibrada divide cada bloque por raíz de su varianza total; sensibilidad target-free. Cargas, scores, biplots/scree y eta² estatal/municipal se guardan separados. Clima48 estandarizado puede dominar suelo natural por dimensión/energía; la sensibilidad equilibrada permite distinguir eso de nueva información. PCA no modela interacciones no lineales.

Cada corrector utiliza residuos cruzados SOLO de outer-train. La selección interna evalúa base+eta×corrección y regenera/tunea sus propias predicciones climáticas sin sus etiquetas. Se reutiliza el cross-fitting legítimo de K para lluvia, en lectura. BasesCurrent se cruzan con las mismas restricciones geográficas. Proveniencia en tabla14, residuos en15, coeficientes en13/30, decisiones en31.

L8 es exclusivamente descriptivo: no hay cross-fitting anidado y selección de hiperparámetros de TODAS las tres etapas originales archivados; los residuosRS5 preceden topografía. Retunear todo definiría una variante nueva y no garantiza reproducción fiel. Asociaciones del residuo finalChampion con suelo/PCs/topografía e intraperfil no demuestran mejora predictiva. No se entrenó una nueva etapaChampion ni se reutilizaron sus OOF como objetivos.

Diagnósticos: regiones, Chignahuapan(71etiquetas, mismoOOF), bajos<3/altos>5, buffers50/125/250m, claves discrepantes, negativos/extremos conservados y diferencias de parejas evaluadas por el mismo modelo. Más dispersión intraperfil no prueba mejor precisión. Folds/repeticiones correlacionados; margen .01t/ha exploratorio para RMSEgeográfico/MAEen TODOS los protocolos, sin significancia formal.

![RMSE](../outputs/modeling/family_1/l_multiblock_representation/v1/figures/RMSE_protocol.png)

![MAE](../outputs/modeling/family_1/l_multiblock_representation/v1/figures/MAE_protocol.png)

## Lectura de los resultados

Las bases reproducen exactamente los resultados anteriores. Lluvia sostiene menor RMSE municipal(.6954frente a.7773) y espacial(.7348frente a.9798); los resultados aleatorios son cercanos(.5214/.5200). La mayor representaci?n clim?tica no garantiza transferencia.

PCA de suelo residual no mejora lluvia consistentemente: L2 aleatorio.5220, municipal.9857 frente a lluvia.5214/.6954. Topograf?a+sueloPCAresidualL4 mejora modestamente aleatorio(.5194) y espacio(.7215), pero deteriora municipal(.7060) ligeramente m?s que el margen.01. La pendiente residual de K ya obtuvo mejor RMSE aleatorio(.5162); no se declara una nueva mejora por a?adir suelo.

Hellinger directo sobre Climate Current mejora el perfil(.4994frente a.5403), pero su espacial.9763 sigue lejos de lluvia.7348. PCA conjunto agresivo1/2/4 empeora rendimiento en ambas bases; la varianza dominante no equivale a las direcciones ?tiles para Y. PCA aporta interpretaci?n de bloques y filtrado/rotaci?n; no evidencia estable de informaci?n intr?nseca nueva. La elecci?n de base cambia los residuos y la aparente utilidad del mismo suelo.

Los53perfiles del PCA descriptivo son centroides de sus variables, con Ymedio calculado solo sobre etiquetas disponibles; no equivalen a preservar toda la variaci?n edafol?gica intraperfil. Localidades recuperadas son proximidades a puntos, no asignaciones territoriales. La auditor?a de fechas confirma todos los sensores en B?sico/PRO y la ausencia de historiaPlanet en esas fuentes.

## Comparaciones controladas finales

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

Mejoras positivas favorecen al candidato. Interpretar cada protocolo por separado; revisar MAE, categorías y error intraperfil antes de integrar. La síntesis transversal conserva resultados negativos y limita conclusiones al objetivo evaluado.
