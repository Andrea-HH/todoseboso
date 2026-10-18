> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Seis combinaciones: síntesis de evidencia

Ninguna de las seis combinaciones reduce el RMSE en los cuatro protocolos originales frente a Reference26. Se conserva Reference26 como referencia; no se declara un nuevo Champion.

Ninguna combinación conserva simultáneamente el RMSE y percentil95 de Reference26 y la proporción dentro de ±.5 de C-T3 en aleatoria y espacial. No se ha resuelto por completo ese compromiso.

Ningún contraste de las mezclas frente a Reference26 supera Holm.

## Modelos

- B1: C-T3 + peso constante del desplazamiento Reference26−C-T3.
- B2: C-T3 + peso constante del desplazamiento Compact14−C-T3.
- B3: mezcla convexa constante Reference26/L40.
- B4: mezcla convexa regularizada C-T3/Reference26/L40.
- B5: mezcla C-T3/Reference26 con cuatro indicadores de desacuerdo y soporte.
- B6: mezcla Reference26/L40 con desacuerdo, soporte y dispersión de etiquetas vecinas del entrenamiento.

## Mismos65 folds: RMSE t/ha / R²

| experiment | random | climate_profile | municipality | spatial |
| --- | --- | --- | --- | --- |
| CT3 | 0.5116 / 0.6361 | 0.5206 / 0.6232 | 0.5813 / 0.5302 | 0.6788 / 0.3594 |
| L40 | 0.4930 / 0.6619 | 0.5031 / 0.6481 | 0.7602 / 0.1964 | 0.9794 / -0.3337 |
| Compact14 | 0.4773 / 0.6832 | 0.4793 / 0.6805 | 0.5755 / 0.5395 | 0.6431 / 0.4250 |
| Reference26 | 0.4748 / 0.6865 | 0.4774 / 0.6831 | 0.5752 / 0.5400 | 0.6333 / 0.4423 |
| B1 | 0.4755 / 0.6856 | 0.4839 / 0.6744 | 0.5681 / 0.5513 | 0.6813 / 0.3546 |
| B2 | 0.4781 / 0.6821 | 0.4793 / 0.6805 | 0.5849 / 0.5244 | 0.6864 / 0.3450 |
| B3 | 0.4778 / 0.6824 | 0.4803 / 0.6792 | 0.6096 / 0.4833 | 0.7152 / 0.2888 |
| B4 | 0.4778 / 0.6825 | 0.4827 / 0.6760 | 0.6041 / 0.4926 | 0.6832 / 0.3511 |
| B5 | 0.4757 / 0.6853 | 0.4832 / 0.6754 | 0.5688 / 0.5502 | 0.6820 / 0.3533 |
| B6 | 0.4774 / 0.6830 | 0.4808 / 0.6786 | 0.6095 / 0.4835 | 0.7175 / 0.2841 |

## Banco nuevo97/41 separado

| experiment | fresh_97_41 |
| --- | --- |
| CT3 | 0.4918 / 0.6571 |
| L40 | 0.4893 / 0.6621 |
| Compact14 | 0.4661 / 0.6933 |
| Reference26 | 0.4625 / 0.6971 |
| B1 | 0.4622 / 0.6975 |
| B2 | 0.4657 / 0.6939 |
| B3 | 0.4710 / 0.6858 |
| B4 | 0.4688 / 0.6888 |
| B5 | 0.4624 / 0.6972 |
| B6 | 0.4706 / 0.6862 |

Son 16 particiones nuevas de las mismas138 respuestas ya investigadas; no validación independiente. Cada métrica se calcula en 41 casos por partición y luego se promedia. No mezclar con las OOF completas de los 65 folds ni con el banco histórico de GeoC.

## Diferencias de RMSE frente a Reference26

Negativo favorece la combinación.

| experiment | delta_random | delta_profile | delta_municipal | delta_spatial | delta_fresh |
| --- | --- | --- | --- | --- | --- |
| B1 | +0.0007 | +0.0065 | -0.0072 | +0.0480 | -0.0003 |
| B2 | +0.0033 | +0.0019 | +0.0096 | +0.0530 | +0.0032 |
| B3 | +0.0031 | +0.0029 | +0.0344 | +0.0818 | +0.0085 |
| B4 | +0.0030 | +0.0053 | +0.0289 | +0.0498 | +0.0063 |
| B5 | +0.0009 | +0.0057 | -0.0064 | +0.0487 | -0.0001 |
| B6 | +0.0026 | +0.0034 | +0.0343 | +0.0842 | +0.0082 |

## Distribución espacial de errores

| experiment | mae | bias | p95_absolute | within_05 |
| --- | --- | --- | --- | --- |
| CT3 | 0.5306 | 0.1912 | 1.4223 | 0.5942 |
| L40 | 0.7434 | 0.4707 | 1.9792 | 0.4928 |
| Compact14 | 0.5140 | 0.1232 | 1.2776 | 0.5580 |
| Reference26 | 0.5004 | 0.2285 | 1.2538 | 0.5507 |
| B1 | 0.5388 | 0.2857 | 1.4223 | 0.5507 |
| B2 | 0.5481 | 0.1625 | 1.4223 | 0.5362 |
| B3 | 0.5607 | 0.2893 | 1.4489 | 0.5362 |
| B4 | 0.5416 | 0.2660 | 1.4223 | 0.5580 |
| B5 | 0.5398 | 0.2848 | 1.4223 | 0.5507 |
| B6 | 0.5613 | 0.2836 | 1.4499 | 0.5435 |

Error=predicho−observado; positivo sobreestima. Menor sesgo no implica menor dispersión. El umbral±.5 y el percentil95 responden preguntas diferentes del RMSE.

## Municipios espaciales: RMSE / sesgo

| experiment | Almoloya | Calpulalpan | Chignahuapan | Cuautepec de Hinojosa | Singuilucan |
| --- | --- | --- | --- | --- | --- |
| CT3 | 0.3602 / -0.3278 | 0.9088 / +0.6980 | 0.5499 / -0.0817 | 0.4205 / -0.1471 | 0.8247 / +0.7099 |
| L40 | 0.2140 / -0.1546 | 1.4985 / +1.4543 | 0.6082 / -0.0442 | 0.2289 / -0.0612 | 1.3881 / +1.3260 |
| Compact14 | 0.4562 / -0.4048 | 0.8129 / +0.5974 | 0.5607 / -0.1229 | 0.4402 / -0.1904 | 0.7450 / +0.6191 |
| Reference26 | 0.5505 / -0.5177 | 0.8125 / +0.6183 | 0.5450 / +0.1002 | 0.5243 / +0.0278 | 0.6611 / +0.5152 |
| B1 | 0.4574 / -0.4275 | 0.9088 / +0.6980 | 0.5450 / +0.1002 | 0.4362 / +0.0778 | 0.8247 / +0.7099 |
| B2 | 0.4562 / -0.4048 | 0.9088 / +0.6980 | 0.5594 / -0.1254 | 0.3956 / -0.1634 | 0.8247 / +0.7099 |
| B3 | 0.5505 / -0.5177 | 1.0513 / +0.9631 | 0.5489 / +0.0610 | 0.5243 / +0.0278 | 0.6611 / +0.5152 |
| B4 | 0.4651 / -0.4351 | 0.9088 / +0.6980 | 0.5485 / +0.0631 | 0.4362 / +0.0778 | 0.8247 / +0.7099 |
| B5 | 0.4709 / -0.4403 | 0.9088 / +0.6980 | 0.5450 / +0.1002 | 0.4362 / +0.0778 | 0.8247 / +0.7099 |
| B6 | 0.5505 / -0.5177 | 1.0581 / +0.9685 | 0.5495 / +0.0479 | 0.5228 / +0.0246 | 0.6611 / +0.5152 |

Almoloya tiene10 parcelas, Cuautepec5, Singuilucan16, Calpulalpan30 y Chignahuapan71. Estas cifras describen resultados y no se convierten en reglas municipales. Omitir regiones del cómputo no reajusta modelos; ver omissions.csv.

## Alcance y complejidad

B1/B5 reutilizan C-T3 que ya forma parte de Reference26 y conservan sus 26 entradas. B2 conserva las 14 entradas de Compact14. B3/B4/B6 requieren además la representación C4 completa de L40;20 componentes PCA no equivalen a20 mediciones originales. Los pesos condicionales no son importancias causales.

Los pesos se aprenden exclusivamente de predicciones internas de expertos reajustados sin la consulta: incluso la intensidad R3 se selecciona dentro de ese entrenamiento. Las penalizaciones meta se congelaron. Las comparaciones externas y las recomendaciones posteriores son exploratorias; no se usaron para ajustar hiperparámetros ni se presentan como confirmación independiente. Se conserva el cambio de tamaño entrenamiento-crossfit frente a reajuste final. L40 conserva PCA transductiva sobre 197 X, sin etiquetas ocultas; esto no prueba generalización inductiva a parcelas nuevas.

Las comparaciones son exploratorias tras amplia reutilización de las mismas etiquetas. Se realizan130 contrastes con Holm. En espacial hay 5 bloques y el test exacto bilateral tiene p mínima .0625: no obtener significación no demuestra igualdad. Las tablas de selección retrospectiva de expertos usan el rendimiento observado, no son modelos aplicables ni límites inferiores de una mezcla convexa.

## Entrega y decisión

Los resultados no autorizan cambios automáticos del Champion. Una ventaja pequeña o localizada debe valorarse junto con complejidad, pérdida por región, cuartiles e intraperfil. Antes de recomendar otra capa se debe comprobar su ganancia frente a la mezcla constante y su estabilidad territorial. Si no hay mejora consistente, priorizar cierre, interpretación y demostración del modelo existente sobre nuevas búsquedas.

Se conservan los 138 rendimientos, modelos anteriores y las 59 parcelas PRED. No se entrenó modelo final con las 138 etiquetas ni se generaron predicciones para las 59 parcelas. Scripts 503–517, OOF, modelos, pesos, pruebas, Excel y auditorías están en la estructura del repositorio.

<!-- FINAL_REVIEW_START -->
## Lectura final revisada

Recomendación: conservar Reference26 como referencia de precisión y Compact14 sin otra mezcla como alternativa de menor complejidad de datos. No incorporaría L40 mediante B3/B4/B6 ni promovería una nueva mezcla con esta evidencia. Reference26 ya contiene un experto Ridge local con 24 vecinos geográficos: añadir L40 evalúa principalmente su representación C4 completa, no la utilidad de los vecinos por primera vez.

La mezcla constante C-T3/26 (B1) mejora municipal de .5752 a .5681 t/ha, pero pierde por perfil (.4774→.4839) y espacial (.6333→.6813). La variante condicional B5 no elimina ese deterioro. En el banco nuevo97/41, B1 mejora sólo 0.000290 t/ha de RMSE, aproximadamente 0.29 kg/ha. No es evidencia de una mejora relevante ni estadísticamente demostrada frente a Reference26. En ese mismo banco, Reference26 obtiene .4625/.6971 RMSE/R², frente a .4893/.6621 de L40. Este contraste se hace en las mismas particiones, sin mezclar el banco histórico de GeoC.

La ganancia municipal de B1 se concentra en Emiliano Zapata y Singuilucan; Chignahuapan y Calpulalpan quedan sin cambio y varios municipios empeoran. En espacial, en cambio, Singuilucan empeora de .6611 con Reference26 a .8247 con B1. La ventaja por municipio cambia con el escenario de validación y no respalda reglas fijas con nombres de municipios.

### El objetivo de conservar el centro y mejorar extremos

En las diez repeticiones aleatorias completas, C-T3 mantiene 77.54% dentro de ±.5 t/ha, Reference26 76.88% y B1 77.32%. La pequeña recuperación frente a Reference26 no alcanza C-T3. El percentil95 absoluto pasa de 0.8147 a 0.8278: la cola empeora ligeramente.

En espacial, Reference26 y B1 quedan ambos en 55.07% dentro de ±.5, por debajo del59.42% de C-T3. El percentil95 empeora de 1.2538 a1.4223 t/ha al mezclar. Las ventajas no se combinan de manera consistente. Un mayor porcentaje dentro de una tolerancia no significa necesariamente mejor predicción de rendimientos próximos a la media; son ejes de análisis distintos. Se entregan ambos diagnósticos en level_bins.csv.

### Qué ocurre con L40

L40 conserva fortalezas descriptivas en Almoloya y Cuautepec. Pero B3 y B6 asignan peso cero a L40 en la evaluación espacial de Almoloya, perdiendo esa oportunidad. En Calpulalpan el RMSE pasa de .8125 con Reference26 a1.0513 con B3 y1.0581 con B6. El selector no reconoció de forma transferible dónde convenía L40.

El bloque que contiene Calpulalpan concentra 97.8% del aumento de SSE espacial de B6 frente a Reference26. Al omitir ese bloque del cómputo, sin reajustar, RMSE queda 0.5642 para Reference26 y 0.5672 para B6: desaparece casi toda la pérdida grande, pero no aparece una ventaja general. Esta omisión es un diagnóstico de concentración, no una nueva validación ni una justificación para excluir parcelas.

Ese bloque contiene las 31 parcelas etiquetadas de Tlaxcala y cuatro de Hidalgo. Por tanto, evalúa extrapolación con Tlaxcala completamente ausente del entrenamiento externo. El banco97/41 evalúa otro escenario: faltantes aleatorios dentro del mismo conjunto de parcelas. Ambos escenarios se conservan separados.

### Pesos y soporte

Los pesos son constantes dentro de cada modelo entrenado, no iguales entre todos los folds. Por eso una mezcla puede quedar peor que ambos extremos en la métrica agregada si selecciona al experto menos conveniente en distintos territorios. Se verificaron los límites convexos en las 2,450 observaciones OOF por modelo: no es un error aritmético ni una mezcla fuera de [0,1].

En espacial, B1 conserva Reference26 en los dos bloques predominantemente de Chignahuapan, pero cambia a C-T3 en los bloques1 y3, precisamente donde Reference26 aporta ventajas. B3 asigna aproximadamente41.2% a L40 en el bloque1. Allí el desacuerdo RMS entre L40 y Reference26 pasa de .1793 en las predicciones internas a .8762 en las externas (4.89 veces). Este cambio y los pesos que no transfieren son compatibles con un problema de calibración bajo cambio territorial y tamaños de entrenamiento distintos. No prueban una causa única. Los cinco pesos B1 sí estaban identificados por diferencias internas no nulas; no se atribuye el resultado a un empate exacto.

La etiqueta espacial3 original corresponde al fold4: Singuilucan, Cuautepec y Tepeapulco. El fold3 corresponde a la etiqueta1, que contiene Calpulalpan y otros municipios. La correspondencia completa está en spatial_fold_block_crosswalk.csv y usa las etiquetas originales, sin renumerarlas.

### Alcance estadístico y siguiente paso

Ninguna comparación de las nuevas mezclas contra Reference26 supera Holm. El único contraste significativo de los 130 es B2 frente a C-T3 por perfil; en ese protocolo B2 coincide exactamente con Compact14, por lo que recupera una ventaja ya existente del control, no una mejora nueva por mezclar. La falta de significación no demuestra equivalencia: con cinco bloques el test exacto bilateral no puede dar p menor de .0625.

Detendría esta batería sin añadir reglas regionales ni nuevos pesos elegidos retrospectivamente sobre estas OOF. Priorizaría cerrar la presentación reproducible del modelo 26, mantener14 como opción compacta y buscar confirmación con nuevas respuestas para sostener afirmaciones de superioridad. Los resultados debilitan estas seis mezclas y estos indicadores de fiabilidad; no refutan todos los modelos locales ni todas las mezclas posibles.
<!-- FINAL_REVIEW_END -->
