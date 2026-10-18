# Comparación explicada: Reference26, Compact14, B1 y Local04D

Fecha: 2026-10-18. Análisis de artefactos existentes; no se entrenaron modelos ni se generaron predicciones PRED59. Script reproducible: `scripts/518_explain_four_architectures.py`.

## Decisión y ventajas reales

Reference26 ofrece el mejor equilibrio de precisión y transferencia entre estos cuatro en las OOF disponibles. Compact14 es la alternativa de menor dependencia de datos: elimina 12 entradas, Planet, la compuerta geológica y la corrección climática interna del experto, con una pérdida pequeña de RMSE. B1 no simplifica los datos: conserva las 26 entradas y añade un peso; su mejora municipal no compensa automáticamente la pérdida espacial. L40 mantiene ventajas locales importantes, especialmente Almoloya y Cuautepec, pero transfiere peor cuando se retienen territorios enteros.

Estas son ventajas observadas, no pruebas de superioridad estadística universal. Se han reutilizado ampliamente los mismos 138 rendimientos para investigar. La batería anterior no encontró mejoras de las nuevas mezclas frente a26 que superaran el ajuste Holm. Esto no demuestra equivalencia, y no sustituye una prueba específica de no inferioridad entre14 y26.

## 1. Reference26: las entradas y sus funciones

26 entradas finales distintas =4 globales +7 del experto local +2 coordenadas +10 proporciones geológicas +3 indicadores. Son variables derivadas, no26 mediciones brutas ni26 coeficientes. Construirlas sigue requiriendo sus series satelitales e insumos cartográficos.

**Núcleo global C-T3**, Elastic Net con imputación, escalado y selección de regularización dentro del entrenamiento:

1. `compact_precip_total`: lluvia total abril–octubre2025.
2. `compact_early_fraction`: fracción de esa lluvia que cae abril–junio.
3. `compact_concentration_hhi`: suma de cuadrados de las fracciones mensuales; distingue lluvia repartida frente a concentrada.
4. `S2_ndvi_month_05`: NDVI Sentinel-2 de mayo2025.

**Experto Ridge local7**, con24 vecinos geográficos, alpha30 y potencia de distancia1:

5. `sat_basic_hist__sentinel_2__ndvi_promedio__mean`: nivel histórico NDVI.
6. `sat_basic_hist__sentinel_2__ndvi_promedio__std`: variabilidad del resumen histórico NDVI.
7. `emp_shape__y2025_planet_evi__turning_fraction`: indicador de cambios de dirección de la curva EVI Planet2025.
8. `agro_pheno__y2025_planet_ndvi__jun_to_aug_delta`: cambio NDVI Planet junio–agosto2025.
9. `sat_basic_2025__sentinel_2__ndwi_promedio__mean`: nivel de NDWI2025.
10. `sat_basic_2025__sentinel_2__ndwi_promedio__std`: variabilidad de NDWI2025.
11. `topo_official__slope__mean`: pendiente media del terreno.

Las coordenadas latitud y longitud (12–13) seleccionan vecinos: no equivalen a agregar dos pendientes lineales globales. El experto7 también recibe una corrección climática Elastic Net interna, ajustada sobre residuos cross-fitted del entrenamiento. Usa el núcleo4 ya contado; no añade otras cuatro variables distintas.

Las diez proporciones de composición geológica (14–23) construyen una compuerta física: grupos KMeans de4 u8 seleccionados internamente, con pesos de mezcla regularizados hacia un peso global. Modifican cuánto se utiliza C-T3 frente al experto; no son diez términos aditivos libres. No confundir esta compuerta con la antigua variante de textura/fase, ni con escoger vecinos por semejanza física: aquí los24 vecinos siguen siendo geográficos.

**Corrector final R3** (24–26):

- `I_history_ndvi_floor`: media2022–2024 del nivel mínimo NDVI resumido mensualmente mayo–octubre; requiere soporte histórico completo.
- `I_gap_excess_persistence`: persistencia en2025 de exceso de heterogeneidad NDVI respecto a la historia propia del mismo mes. Para los seis excesos positivos z: `(sum z)^2/(6*sum z^2)`, cero si no hay exceso. No es simplemente NDVI bajo.
- `I_slope_min`: pendiente mínima topográfica; no es pendiente temporal de NDVI.

R3 es otro Elastic Net conservador (alpha.01,l1_ratio.5), con delta `0.5*clip(pred,-0.5,0.5)`: máximo absoluto0.25t/ha antes de intensidad. Su intensidad0/.5/1 se selecciona internamente; se desactiva cuando faltan indicadores (29 de138 parcelas tienen soporte R3 incompleto). Los residuos para entrenar correctores son observado menos predicción OOF, mientras que las tablas de evaluación llaman error a predicción menos observado.

Esquema: `R26 = C + g_geología(x)*(E7-C) + intensidad*completo_R3*delta_R3`.

Ventaja arquitectónica: combina señal agroclimática global con respuesta local y un ajuste acotado; el ancla global reduce la dependencia exclusiva de vecinos. Las aportaciones numéricas de un componente no son evidencia causal de su mecanismo agronómico.

## 2. Compact14: qué conserva y qué elimina

14 =4 C-T3 +5 experto local +2 coordenadas +3 R3. Conserva historia NDVI media/desviación, NDWI2025 media/desviación y pendiente media. Elimina los dos indicadores Planet y las diez proporciones geológicas. Usa los mismos24 vecinos geográficos y Ridge alpha30,potencia1. Elimina además la corrección climática interna del experto.

Esquema: `M14 = C + w_entrenamiento*(L5-C) + intensidad*completo_R3*delta_R3`.

El peso w es global para cada modelo ajustado y aprendido con OOF internas; no es un50/50 fijo ni una regla municipal. Mantiene el corrector R3 y sus límites. La reducción es de46.2% de entradas finales; elimina una fuente satelital y una capa cartográfica de la receta, además de simplificar la mezcla y quitar una capa Elastic Net. No demuestra que todas las series originales sean prescindibles: hay que derivar los14 indicadores.

Su desventaja observada es una pequeña pérdida de RMSE y mayor error en el cuartil alto bajo validación espacial. No empeora todas las métricas: su sesgo espacial es menor que el de26 y su MAE municipal es ligeramente menor.

## 3. B1: atenuar26 hacia C-T3

`B1 = C + a_entrenamiento*(R26-C)`, con0<=a<=1. Un único peso aprendido por mínimos cuadrados restringidos sobre OOF internas honestas. No es un clasificador por municipio, no selecciona el peso con la evaluación externa y no agrega variables. Como C-T3 ya está dentro de26, B1 vuelve a atenuar conjuntamente sus desviaciones locales y correctores. Conserva26 entradas más un metaparámetro aprendido; no es una alternativa de14 entradas.

Peso medio de26: aleatoria91.4%, perfil87.1%, municipal20.0%, espacial50.5%, banco97/4193.6%. Son resúmenes de distintos ajustes de CV, no pesos operativos definidos por protocolo. No hay un único peso de despliegue porque no se entrenó el modelo final con138.

En espacial, B1 mantiene26 en los dos bloques predominantemente de Chignahuapan, elige C-T3 en los bloques originales1 y3, y mezcla aproximadamente52.5% de26 en Almoloya. El selector interno no transfirió bien en los dos bloques donde volvió a C-T3. Una mezcla convexa puede empeorar a ambos extremos en el agregado si cambia de peso entre folds y selecciona el extremo menos favorable en distintos grupos; no contradice que cada predicción esté entre sus dos extremos.

## 4. L40 / Local04D

Representación C4 de2082 variables, imputación/escalado y PCA20; Ridge local por consulta sobre24 vecinos geográficos, alpha30,potencia1. Sus20 componentes no son20 variables originales y no hay20 coeficientes globales válidos para todas las parcelas. Aquí el PCA/escalado congelado utiliza las X de197 parcelas: transductivo, sin las etiquetas ocultas. Es una condición distinta de una representación puramente inductiva ajustada sólo al entrenamiento externo.

L40 no tiene el ancla C-T3 ni el corrector R3 explícitos de las otras recetas. Tanto26 como14 ya utilizan el principio de Ridge con24 vecinos; L40 aporta principalmente otra representación. Para estas197 parcelas las componentes están disponibles y el cálculo local puede ser ligero; su mayor dependencia de insumos no implica necesariamente inferencia lenta. Para nuevas parcelas hay que reproducir C4 y su proyección.

## 5. Validación y métricas

Mismas65 particiones externas:50aleatorias (10repeticiones de5folds),5por perfil,5municipales y5espaciales. Dentro de cada repetición se calcula la métrica sobre OOF completas y luego se promedian repeticiones. No son medias de RMSE por fold. Los16 splits nuevos97/41 se muestran aparte: reutilizan los mismos138 rendimientos y no son confirmación independiente.

- Aleatoria: faltantes dispersos entre territorios ya representados.
- Perfil: se retienen perfiles climáticos completos.
- Municipal: se retienen grupos municipales según las particiones originales.
- Espacial: se retienen bloques contiguos; exige transferencia territorial.

RMSE penaliza especialmente errores grandes; MAE da el tamaño absoluto medio, no un intervalo garantizado. R²=1-SSE/TSS: más alto es mejor en la misma muestra y protocolo; .686 significa reducir68.6% la suma de errores cuadrados frente al promedio observado de esa evaluación, no68.6% de predicciones correctas. R² negativo significa peor SSE que ese promedio. Entre RMSE y R² no hay dos evidencias independientes cuando comparten muestra: ambos dependen de SSE.

El R² global mezcla separación entre estados con variación dentro de cada estado. En espacial26 tieneR² global.442, pero por estado Puebla.118,Hidalgo.390 yTlaxcala-4.035. Tlaxcala tiene poca variación y está completamente fuera del entrenamiento en uno de los bloques: por eso un desplazamiento de nivel produce un R² muy negativo. No presentar el R² global como capacidad para ordenar parcelas de cada municipio.

**R² ajustado: no reportable válidamente con los conteos14/26/20.** La fórmula clásica es `1-(1-R²)*(n-1)/(n-p-1)` para regresión lineal de dimensión fija bajo sus supuestos. En estas recetas p no equivale al número de entradas: hay regularización, regresiones distintas por consulta, vecinos, compuertas, selección interna y correctores. B1 tampoco tiene p=1: contiene todos los expertos previos. Un número calculado sustituyendo esos conteos sería una penalización arbitraria. No se estimaron grados de libertad efectivos del pipeline completo. Las OOF y la validación territorial aportan una evaluación predictiva defendible de la complejidad, aunque no eliminan la selección adaptativa entre experimentos.

Tabla: unidades t/ha excepto R².

| experiment | protocol | rmse | r2 | mae | bias |
| --- | --- | --- | --- | --- | --- |
| B1 | climate_profile | 0.4839 | 0.6744 | 0.3408 | 0.0021 |
| B1 | municipality | 0.5681 | 0.5513 | 0.4426 | -0.0417 |
| B1 | random | 0.4755 | 0.6856 | 0.3396 | -0.0069 |
| B1 | spatial | 0.6813 | 0.3546 | 0.5388 | 0.2857 |
| Compact14 | climate_profile | 0.4793 | 0.6805 | 0.3336 | 0.0177 |
| Compact14 | municipality | 0.5755 | 0.5395 | 0.4468 | -0.0103 |
| Compact14 | random | 0.4773 | 0.6832 | 0.3399 | -0.0074 |
| Compact14 | spatial | 0.6431 | 0.4250 | 0.5140 | 0.1232 |
| L40 | climate_profile | 0.5031 | 0.6481 | 0.3479 | 0.0108 |
| L40 | municipality | 0.7602 | 0.1964 | 0.5991 | 0.1051 |
| L40 | random | 0.4930 | 0.6619 | 0.3526 | -0.0090 |
| L40 | spatial | 0.9794 | -0.3337 | 0.7434 | 0.4707 |
| Reference26 | climate_profile | 0.4774 | 0.6831 | 0.3342 | -0.0010 |
| Reference26 | municipality | 0.5752 | 0.5400 | 0.4491 | -0.0413 |
| Reference26 | random | 0.4748 | 0.6865 | 0.3396 | -0.0071 |
| Reference26 | spatial | 0.6333 | 0.4423 | 0.5004 | 0.2285 |

Banco97/41 separado:

| experiment | rmse | r2 | mae |
| --- | --- | --- | --- |
| B1 | 0.4622 | 0.6975 | 0.3373 |
| Compact14 | 0.4661 | 0.6933 | 0.3398 |
| L40 | 0.4893 | 0.6621 | 0.3552 |
| Reference26 | 0.4625 | 0.6971 | 0.3387 |

La mejora de26 frente a14 en aleatoria es0.002514t/ha, unos2.5kg/ha de RMSE; municipal0.000262t/ha; espacial0.009720t/ha. No justificaría la complejidad adicional solamente con esa diferencia aleatoria. En espacial la diferencia26 frente aL40 es0.346054t/ha: aquí sí cambia mucho el comportamiento territorial observado.

El objetivo observado va de2.00 a5.59t/ha, media3.955 y rango3.59. El RMSE aleatorio de26 equivale aproximadamente al12.0% de la media y13.2% del rango; su MAE.3396 equivale8.6% de la media. En espacial su RMSE representa16.0% de la media. El rango depende de extremos y no debe ser la única escala de comparación; el RMSE no significa error garantizado±.475 en cada parcela.

## 6. Convenciones de residuos y forma de la pérdida

En este repositorio, `error = predicción - observado`: positivo=sobreestimación; negativo=subestimación. Ejemplo observado4.5,predicho4.0 => error-.5. El residuo clásico suele ser observado-predicción: es el signo opuesto. El archivo de entrega incluye ambas convenciones explícitas. Al entrenar una corrección aditiva se usa observado-base, no se suma el error con el signo incorrecto.

Sesgo es error medio: puede ser casi cero por cancelación de errores grandes. RMSE²=sesgo²+varianza del error en cada evaluación; el promedio de RMSE entre repeticiones no se descompone tomando el cuadrado del promedio. P95 absoluto indica el tamaño bajo el cual cae95% de errores en esa evaluación; no es cobertura de un intervalo predictivo. Porcentaje dentro de±.5 es una tolerancia descriptiva.

| experiment | protocol | median_absolute | p95_absolute | within_05 | within_1 |
| --- | --- | --- | --- | --- | --- |
| B1 | random | 0.2577 | 0.8278 | 0.7732 | 0.9623 |
| B1 | spatial | 0.4781 | 1.4223 | 0.5507 | 0.8478 |
| Compact14 | random | 0.2535 | 0.8510 | 0.7645 | 0.9609 |
| Compact14 | spatial | 0.4304 | 1.2776 | 0.5580 | 0.8841 |
| L40 | random | 0.2570 | 0.9053 | 0.7355 | 0.9587 |
| L40 | spatial | 0.5786 | 1.9792 | 0.4928 | 0.6812 |
| Reference26 | random | 0.2575 | 0.8147 | 0.7688 | 0.9630 |
| Reference26 | spatial | 0.4274 | 1.2538 | 0.5507 | 0.8986 |

Las dos últimas columnas son proporciones. En aleatoria26 y14 son muy próximos en MAE;26 reduce más la cola P95. B1 mejora poco la proporción dentro de±.5, pero no la cola. En espacial26 mantiene menor RMSE y MAE que14 aun teniendo mayor sesgo positivo: reduce la dispersión de errores lo suficiente para compensar parte de ese desplazamiento. B1 aumenta el sesgo espacial a+.286 frente a+.229 de26. L40 llega a+.471.

Cuartiles del rendimiento observado en espacial, análisis descriptivo y no una regla utilizable al predecir:

| experiment | quartile | n | rmse | bias |
| --- | --- | --- | --- | --- |
| B1 | 1 | 36.0000 | 1.1036 | 1.0095 |
| B1 | 2 | 33.0000 | 0.5632 | 0.3884 |
| B1 | 3 | 35.0000 | 0.2870 | 0.0351 |
| B1 | 4 | 34.0000 | 0.4493 | -0.3225 |
| Compact14 | 1 | 36.0000 | 0.9947 | 0.8940 |
| Compact14 | 2 | 33.0000 | 0.4424 | 0.2528 |
| Compact14 | 3 | 35.0000 | 0.2558 | -0.1389 |
| Compact14 | 4 | 34.0000 | 0.6112 | -0.5488 |
| L40 | 1 | 36.0000 | 1.6697 | 1.6395 |
| L40 | 2 | 33.0000 | 0.7736 | 0.7110 |
| L40 | 3 | 35.0000 | 0.1442 | -0.0543 |
| L40 | 4 | 34.0000 | 0.5822 | -0.4594 |
| Reference26 | 1 | 36.0000 | 0.9914 | 0.8866 |
| Reference26 | 2 | 33.0000 | 0.5139 | 0.3223 |
| Reference26 | 3 | 35.0000 | 0.3223 | 0.0123 |
| Reference26 | 4 | 34.0000 | 0.4736 | -0.3367 |

Los cuatro sobreestiman el cuartil bajo y subestiman el alto, con distinta intensidad. L40 destaca en el tercer cuartil pero falla mucho en el primero;14 sacrifica más el cuartil alto que26; B1 conserva mejor parte alta a costa del primer cuartil. Por eso no existe un ganador por cada criterio a la vez.

## 7. Dónde difieren las predicciones

| pair | protocol | mean_absolute_prediction_difference | p95_prediction_disagreement | fraction_A_lower_absolute_error | fraction_ties |
| --- | --- | --- | --- | --- | --- |
| Reference26 minus Compact14 | random | 0.0450 | 0.1369 | 0.4855 | 0.0000 |
| Reference26 minus Compact14 | spatial | 0.1603 | 0.4502 | 0.5797 | 0.0145 |
| Reference26 minus B1 | random | 0.0116 | 0.0541 | 0.3145 | 0.4036 |
| Reference26 minus B1 | spatial | 0.0631 | 0.2500 | 0.3043 | 0.5580 |
| Reference26 minus L40 | random | 0.0917 | 0.2449 | 0.5304 | 0.0000 |
| Reference26 minus L40 | spatial | 0.4518 | 1.1504 | 0.6449 | 0.0000 |
| Compact14 minus B1 | random | 0.0434 | 0.1293 | 0.5145 | 0.0000 |
| Compact14 minus B1 | spatial | 0.1804 | 0.4502 | 0.5507 | 0.0145 |
| Compact14 minus L40 | random | 0.0861 | 0.2324 | 0.5341 | 0.0000 |
| Compact14 minus L40 | spatial | 0.3920 | 1.1896 | 0.6884 | 0.0000 |
| B1 minus L40 | random | 0.0966 | 0.2593 | 0.5341 | 0.0000 |
| B1 minus L40 | spatial | 0.3955 | 1.0252 | 0.6377 | 0.0000 |

Estos desacuerdos aleatorios describen las1380 predicciones OOF, no1380 parcelas independientes. En aleatoria26 y14 difieren en promedio.045t/ha;26 yL40 en.092. En espacial aumentan a.160 y.452, respectivamente. El efecto de arquitectura es mucho mayor al cambiar el soporte territorial. Una predicción diferente no implica mejor predicción; las columnas de ganancia por parcela usan el rendimiento observado para comprobarlo.

| ID_POLIGONO | Municipio | y_true | pred_Reference26 | pred_Compact14 | pred_B1 | pred_L40 |
| --- | --- | --- | --- | --- | --- | --- |
| AGC_001 | Calpulalpan | 3.5000 | 2.6751 | 2.5673 | 2.6389 | 4.4799 |
| AGC_074 | Calpulalpan | 2.5000 | 2.7926 | 2.6978 | 2.9471 | 4.4886 |
| AGC_059 | Almoloya | 4.4100 | 3.8287 | 3.9205 | 3.9455 | 4.3983 |
| AGC_152 | Almoloya | 4.8700 | 3.9732 | 4.0344 | 4.0911 | 4.4151 |

AGC_074 ilustra el riesgo de extrapolar un nivel alto: L40 predice4.489 frente a2.5 observado;26 y14 moderan el nivel. AGC_059 muestra la contrapartida: L40 casi acierta4.41, y26 subestima cerca de.58. No hay una regla conocida antes de observar Y que seleccione siempre el mejor experto. Esos ejemplos documentan comportamiento, no demuestran una causa agronómica particular.

RMSE por municipio en validación espacial:

| region | B1 | Compact14 | L40 | Reference26 |
| --- | --- | --- | --- | --- |
| Almoloya | 0.4574 | 0.4562 | 0.2140 | 0.5505 |
| Apan | 1.1280 | 0.8812 | 1.4869 | 0.9121 |
| Calpulalpan | 0.9088 | 0.8129 | 1.4985 | 0.8125 |
| Chignahuapan | 0.5450 | 0.5607 | 0.6082 | 0.5450 |
| Cuautepec de Hinojosa | 0.4362 | 0.4402 | 0.2289 | 0.5243 |
| Emiliano Zapata | 0.5560 | 0.4033 | 0.5904 | 0.3539 |
| Nanacamilpa de Mariano Arista | 1.4077 | 1.2443 | 1.9809 | 1.2465 |
| Singuilucan | 0.8247 | 0.7450 | 1.3881 | 0.6611 |
| Tepeapulco | 0.3004 | 0.4254 | 0.1281 | 0.5504 |

Calpulalpan deja expuesto el principal problema deL40; Almoloya yCuautepec conservan fortalezas deL40. En Chignahuapan26 mejora aL40 en RMSE pero no gana en todas las tolerancias. B1 conserva exactamente26 en Puebla en espacial; su ganancia municipal se concentra en otros casos y no se mantiene en Singuilucan al cambiar a validación espacial.

La estructura de estas diferencias es compatible con cambios en soporte de vecinos, anclaje climático, representación y calibración interna. No identifica por sí sola qué variable causó cada diferencia. Se necesitarían atribuciones por componentes del ajuste concreto o ablaciones para hacer esa afirmación; no se infiere causalidad de comparar cuatro predicciones.

## 8. Qué contiene la entrega

- `four_models_predictions_and_residuals.xlsx`: las cuatro predicciones alineadas, métricas, errores, regiones y diferencias.
- `original_65_folds_predictions.csv`:1794 filas de evaluación con las cuatro predicciones cada una.
- `separate_97_41_predictions.csv`:656 filas del banco adicional, separado.
- `parcel_oof_summary.csv`: resumen por parcela/protocolo; media y desviación de predicciones OOF. La desviación entre repeticiones no es un intervalo predictivo; la predicción media OOF no es un modelo final.
- `every_pairwise_oof_difference.csv`: las seis parejas, diferencia de predicción y ganancias de error absoluto/cuadrático. Ganancia positiva favorece al primer modelo.
- `actual_spatial_blocks.csv`, `actual_block_omissions.csv`, `intraprofile.csv`: diagnósticos originales filtrados, sin reajuste. Intraperfil evalúa diferencias entre pares y tiene soporte limitado; no es RMSE individual.
- `predictions_and_residuals.png`: gráfico por protocolo; en aleatoria representa la media OOF por parcela y no sustituye las métricas calculadas por repetición.
- `audit.json`: verificación de alineación, signos y reproducción de las métricas anteriores.

Todas son predicciones de validación de138 parcelas con Y conocido. No se generaron ni se presentan como estimaciones finales de las59 parcelas PRED. Los modelos anteriores se conservaron sin sobrescribir.

## Recomendación

Usaría26 como referencia de precisión observada y14 como candidato preferente si importan simplicidad de fuentes, mantenimiento y explicación. La cercanía de14 no demuestra equivalencia estadística, pero sí pone un coste explícito a conservar12 entradas adicionales. No promoveríaB1 por su mínima ganancia municipal ni usaríaL40 como único modelo para territorios no representados. MantendríaL40 como benchmark de interpolación y fortaleza local, sin convertir retrospectivamente sus mejores municipios en reglas. La siguiente evidencia más valiosa es confirmación con nuevos rendimientos y evaluación operacional, antes de añadir capas para diferencias de pocos kg/ha.
