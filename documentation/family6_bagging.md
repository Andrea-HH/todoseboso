> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# F6 — Bagging y árboles aleatorizados

**Estado: ejecución exploratoria; referencias intactas; sin promoción del Champion ni entrenamiento final/PRED.**

## Métricas primarias

| experiment | climate_profile | municipality | random | spatial |
| --- | --- | --- | --- | --- |
| C-T3 | 0.520604 | 0.581259 | 0.511582 | 0.678778 |
| CHAMPION | nan | nan | 0.498127 | nan |
| F5-01 | 0.499759 | 0.544208 | 0.504006 | 0.734797 |
| F6-00 | 0.527190 | 0.608372 | 0.514005 | 0.762037 |
| F6-01 | 0.512979 | 0.638586 | 0.506296 | 0.758923 |

RMSE en t/ha:138 OOF completas por repetición, luego promedio de diez repeticiones aleatorias. No es media de RMSE por fold. Las repeticiones y folds comparten parcelas; su dispersión no equivale a un error estándar independiente ni a una prueba de significancia. MAE, sesgo, dispersión entre repeticiones y métricas territoriales están en las tablas. C-T3 y F5-01 son controles con los mismos cuatro predictores; Champion y sus etapas usan otras columnas y solo tienen cincuenta folds aleatorios compatibles. Sus comparaciones son contexto arquitectónico, no efecto aislado del algoritmo.

## Criterio de continuación

| experiment | municipal_RMSE_gain | max_RMSE_MAE_harm | municipal_improving_folds | max_space_omission_RMSE_harm | passes |
| --- | --- | --- | --- | --- | --- |
| F6-00 | -0.027113 | 0.083259 | 2 | 0.105425 | False |
| F6-01 | -0.057327 | 0.080145 | 0 | 0.095947 | False |

Criterio congelado antes de ajustar: ganancia municipal RMSE≥0.01 frente a C-T3; al menos tres folds municipales mejoran; ningún RMSE/MAE de ningún protocolo empeora>0.01; al omitir cada bloque espacial, ningún RMSE restante empeora>0.01. Márgenes exploratorios orientativos, no significancia estadística.

**No se abrió la etapa2. F6-02–05 no se ejecutaron.** La lluvia mensual, DTRstd, historia NDVI2 y pendiente media conservan su carácter de hipótesis, sin evidencia incremental directa de F6. No se amplió la búsqueda ni se cambió la regularización tras observar OOF.

## Respuestas a las seis preguntas

**1. F6-00 frente a las referencias:** ΔRMSE versus C-T3 (aleatoria/perfil/municipal/espacial) = +0.00242, +0.00659, +0.02711, +0.08326 t/ha; versus F5-01 = +0.01000, +0.02743, +0.06416, +0.02724. Un resultado negativo favorece F6. La comparación pareada incluye todas las parcelas; no se elimina ningún caso influyente.
**1. F6-01 frente a las referencias:** ΔRMSE versus C-T3 (aleatoria/perfil/municipal/espacial) = -0.00529, -0.00762, +0.05733, +0.08014 t/ha; versus F5-01 = +0.00229, +0.01322, +0.09438, +0.02413. Un resultado negativo favorece F6. La comparación pareada incluye todas las parcelas; no se elimina ningún caso influyente.

Extra Trees conserva una fortaleza pequeña de MAE aleatoria: 0.356612, frente a 0.358869 del Champion. Su RMSE aleatorio es 0.506296, frente a 0.498127; esa diferencia de objetivos y arquitectura impide declarar que reemplaza al Champion.

**2. Transferencia territorial:** el RMSE espacial RF es 0.762037 y ET 0.758923; el municipal RF es 0.608372 y ET 0.638586. Esta comparación descriptiva no acredita superioridad estadística. Bloques, municipios, sesgo y omisiones sin reajuste permiten evaluar si existe una ventaja regionalmente consistente.

**3. Representación de lluvia:** no se puede responder compact3 frente a mensual7 con F6: solo se evaluó compact3 y no se alcanzó el criterio para F6-02. El resultado previo de GPR mensual no se extrapola a árboles.

**4. Historia/topografía:** no se evaluaron las ablaciones F6-04/F6-05. El éxito residual de History15/slope14 no demuestra utilidad directa de NDVI2/pendiente media; F6 no las confirma ni las rechaza.

**5. Continuidad:** cerrar esta ejecución de F6 y avanzar a una propuesta F7 — Gradient Boosting. Las dos configuraciones iniciales no cumplen el criterio prospectivo de continuidad; no se justifica abrir ablaciones adicionales ni un screening. Este cierre corresponde a la representación y regularización acotadas evaluadas, no a todos los bosques posibles.

**6. Propuesta posterior F7, sin ejecución:** comparar CatBoost y XGBoost conservadores directamente con el núcleo compacto y controles C-T3/F5-01; mantener los65 folds y selección interna. Probar mensual7 como ablation predefinida del mismo algoritmo; luego DTR, historia2 y pendiente únicamente con un criterio congelado. Separar entrenamiento directo de cualquier arquitectura residual. Incluir profundidad baja, regularización de hojas, learning_rate y número de iteraciones seleccionados solo en entrenamiento interno; nunca usar el fold externo para early stopping. No reejecutar bajo otros nombres las configuraciones XGBoost históricas ni trasladar sus beneficios residuales a bloques compactos.

## Bloques, concentración e intraperfil

| candidate | fold | n | delta_RMSE | bias_candidate | bias_base | SSE_gain | bias_squared_gain | error_variance_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F6-00 | 1 | 38 | 0.036861 | 0.118808 | -0.036903 | -1.467589 | -0.484634 | -0.982955 |
| F6-00 | 2 | 37 | 0.026808 | -0.193884 | -0.119293 | -1.162340 | -0.864331 | -0.298009 |
| F6-00 | 3 | 35 | 0.205022 | 0.930901 | 0.718204 | -14.525220 | -12.276614 | -2.248606 |
| F6-00 | 4 | 18 | -0.052092 | 0.527435 | 0.574306 | 1.449518 | 0.929523 | 0.519995 |
| F6-00 | 5 | 10 | 0.103099 | -0.215769 | -0.327834 | -0.849019 | 0.609192 | -1.458211 |
| F6-01 | 1 | 38 | 0.031550 | -0.062726 | -0.036903 | -1.249779 | -0.097767 | -1.152012 |
| F6-01 | 2 | 37 | 0.026251 | -0.223801 | -0.119293 | -1.137677 | -1.326678 | 0.189001 |
| F6-01 | 3 | 35 | 0.129537 | 0.898232 | 0.718204 | -8.835074 | -10.185127 | 1.350054 |
| F6-01 | 4 | 18 | 0.111248 | 0.692293 | 0.574306 | -3.422694 | -2.689942 | -0.732752 |
| F6-01 | 5 | 10 | 0.145090 | -0.457165 | -0.327834 | -1.255737 | -1.015245 | -0.240492 |

Ganancia SSE = ganancia de sesgo cuadrado + ganancia de varianza de errores (varianza con ddof0); la descomposición es algebraica, no causal. Bloque3 conserva sus35 parcelas; se analiza también cada uno de los otros cuatro. `fold_omission_sensitivity.csv` y `municipality_omission_sensitivity.csv` omiten únicamente observaciones del cálculo, sin modificar ajustes.

| experiment | protocol | n_pairs | n_profiles | n_parcels | equal_profile_RMSE | pair_weighted_RMSE |
| --- | --- | --- | --- | --- | --- | --- |
| C-T3 | climate_profile | 1073.000000 | 12.000000 | 107.000000 | 0.547885 | 0.763380 |
| C-T3 | municipality | 1034.000000 | 12.000000 | 103.000000 | 0.520989 | 0.768841 |
| C-T3 | random | 208.400000 | 8.600000 | 87.700000 | 0.589951 | 0.771183 |
| C-T3 | spatial | 1007.000000 | 12.000000 | 106.000000 | 0.540147 | 0.767538 |
| F5-01 | climate_profile | 1073.000000 | 12.000000 | 107.000000 | 0.531827 | 0.773656 |
| F5-01 | municipality | 1034.000000 | 12.000000 | 103.000000 | 0.538821 | 0.818600 |
| F5-01 | random | 208.400000 | 8.600000 | 87.700000 | 0.602212 | 0.786774 |
| F5-01 | spatial | 1007.000000 | 12.000000 | 106.000000 | 0.531899 | 0.789029 |
| F6-00 | climate_profile | 1073.000000 | 12.000000 | 107.000000 | 0.539510 | 0.785001 |
| F6-00 | municipality | 1034.000000 | 12.000000 | 103.000000 | 0.524813 | 0.794569 |
| F6-00 | random | 208.400000 | 8.600000 | 87.700000 | 0.613341 | 0.800509 |
| F6-00 | spatial | 1007.000000 | 12.000000 | 106.000000 | 0.535438 | 0.796523 |
| F6-01 | climate_profile | 1073.000000 | 12.000000 | 107.000000 | 0.546051 | 0.783407 |
| F6-01 | municipality | 1034.000000 | 12.000000 | 103.000000 | 0.521596 | 0.796176 |
| F6-01 | random | 208.400000 | 8.600000 | 87.700000 | 0.608918 | 0.798473 |
| F6-01 | spatial | 1007.000000 | 12.000000 | 106.000000 | 0.531013 | 0.792651 |

Pares restringidos a predicciones del mismo modelo externo; igual peso por perfil y ponderación por pares se reportan por separado. Hay43 perfiles etiquetados y12 repetidos; los pares son dependientes y los dos perfiles grandes de Chignahuapan dominan la ponderación por pares. La capacidad de separar perfiles climáticos no demuestra discriminación local. El núcleo solo puede diferenciar parcelas idénticas en lluvia mediante diferencias en NDVI; vectores completos idénticos reciben la misma predicción.

Ganancias y deterioros por parcela, top1/5/10, omisiones descriptivas y ganancias municipales/perfil están en `parcel_gains_*`, `gain_concentration.csv`, `influential_parcel_omission.csv` y `paired_group_gains.csv`. Las omisiones retrospectivas no son una evaluación independiente ni proponen excluir etiquetas.

En este contraste, Extra Trees empeora el RMSE frente a C-T3 en los cinco bloques espaciales; RF lo empeora en cuatro de cinco. El sesgo del bloque3 es +0.93090 para RF y +0.89823 para ET, frente a +0.71820 de C-T3. Ambos reducen ese sesgo respecto del GP (+1.01614), sin conseguir una mejora espacial global. Al omitir el bloque3 del cálculo, la diferencia RMSE versus C-T3 sigue siendo +0.01675 para RF y +0.05642 para ET: el fracaso espacial no depende exclusivamente de ese bloque.

El RMSE espacial intraperfil con igual peso por perfil de ET (0.53101) mejora modestamente a C-T3 (0.54015), pero su RMSE ponderado por pares (0.79265) empeora respecto a 0.76754. RF también ofrece una mejora local espacial pequeña con igual peso, mientras ambos empeoran esa métrica en validación aleatoria. Esto es una fortaleza localizada, no una solución uniforme a la heterogeneidad intraperfil ni a la transferencia territorial.

| candidate | protocol | net_SSE_gain | top_positive_gain | fraction_net_gain | bottom_gain |
| --- | --- | --- | --- | --- | --- |
| F6-00 | climate_profile | -0.952293 | 3.293717 | -3.458722 | -4.442330 |
| F6-00 | municipality | -4.451088 | 3.281750 | -0.737292 | -5.258407 |
| F6-00 | random | -0.344639 | 3.144381 | -9.123688 | -3.866199 |
| F6-00 | spatial | -16.554650 | 2.284397 | -0.137991 | -6.279001 |
| F6-01 | climate_profile | 1.087529 | 3.509124 | 3.226694 | -3.344931 |
| F6-01 | municipality | -9.650376 | 2.551530 | -0.264397 | -3.890873 |
| F6-01 | random | 0.741416 | 2.877074 | 3.880511 | -2.741401 |
| F6-01 | spatial | -15.900961 | 2.184145 | -0.137359 | -4.240778 |

## Qué aprenden los árboles

Se conservan todos los umbrales internos en unidades originales, su soporte nodal, frecuencias de raíces, uso por árbol y dispersiones por fit. Frecuencia/impureza no son importancia causal ni utilidad incremental. Cambiar algoritmo altera bootstrap y aleatorización de umbrales conjuntamente: este contraste no aísla un solo mecanismo. Los árboles de respuesta media no extrapolan una tendencia lineal: sus predicciones permanecen dentro del rango de Y de entrenamiento y una variable fuera de soporte recorre las hojas límite. El soporte por bloque permite distinguir esa limitación de una regla regional aprendida.

ALE utiliza exclusivamente predictores de entrenamiento del ajuste externo, seis bins de cuantiles y mínimo cinco parcelas por bin. Si hay un hueco sin soporte, no se dibuja una curva acumulada continua. Las diferencias mixtas lluvia×NDVI usan celdas de terciles con≥5 parcelas; son un diagnóstico equivalente de interacción local, no ALE bidimensional completo ni causalidad. Ni ALE ni las esquinas de perturbación garantizan apoyo sobre todo el manifold de predictores correlacionados. La figura de curvas promedia centros de cuantiles entre folds; las tablas por fold conservan sus límites reales.

La permutación NDVI se realiza únicamente entre pares del mismo perfil dentro de validación, diez veces y con≥10 parcelas elegibles. Evalúa dependencia predictiva local del bosque ya ajustado; no sustituye una ablación reajustada ni una prueba causal. Tampoco se usa para seleccionar variables o hiperparámetros.

Las cinco parcelas con mayor beneficio de ET aportan 388% de su ganancia SSE aleatoria neta y 323% de la ganancia por perfil; otros casos compensan buena parte de ese beneficio. Al omitir retrospectivamente esos cinco IDs de las medias de pérdida por parcela, la diferencia RMSE versus C-T3 se invierte a +0.01627 en aleatoria y +0.01900 por perfil. El MAE conserva pequeñas ganancias. Esa sensibilidad desaconseja interpretar las mejoras pequeñas como consistentes. No se excluyó ninguna parcela de los ajustes.

| experiment | protocol | mean_delta_MSE | mean_delta_MAE | mean_n_eligible | mean_profiles |
| --- | --- | --- | --- | --- | --- |
| F6-00 | climate_profile | 0.010892 | 0.005986 | 21.400000 | 2.400000 |
| F6-00 | municipality | 0.011309 | -0.002850 | 31.000000 | 2.666667 |
| F6-00 | random | 0.010773 | 0.001088 | 17.540000 | 3.960000 |
| F6-00 | spatial | 0.013849 | 0.002033 | 25.250000 | 2.750000 |
| F6-01 | climate_profile | 0.007968 | 0.000664 | 21.400000 | 2.400000 |
| F6-01 | municipality | 0.010677 | 0.000398 | 31.000000 | 2.666667 |
| F6-01 | random | 0.006012 | 0.000818 | 17.540000 | 3.960000 |
| F6-01 | spatial | 0.006739 | 0.001041 | 25.250000 | 2.750000 |

## Estabilidad y reproducibilidad

| experiment | protocol | mean_RMS_prediction_difference | max_RMS_prediction_difference |
| --- | --- | --- | --- |
| F6-00 | climate_profile | 0.011391 | 0.026685 |
| F6-00 | municipality | 0.008846 | 0.012283 |
| F6-00 | random | 0.008915 | 0.017774 |
| F6-00 | spatial | 0.012306 | 0.029343 |
| F6-01 | climate_profile | 0.012255 | 0.016194 |
| F6-01 | municipality | 0.019988 | 0.035704 |
| F6-01 | random | 0.006990 | 0.012940 |
| F6-01 | spatial | 0.018540 | 0.043980 |

Prefijos128/256 frente a384 provienen de los mismos árboles ya entrenados. No seleccionan adaptativamente el número de árboles. Variación>0.01t/ha señala sensibilidad Monte Carlo que debe declararse; no abre otra batería. Las semillas y los parámetros efectivos se conservan por ajuste. La dispersión entre árboles no es incertidumbre observacional y no se ofrecen intervalos predictivos de bagging sin una calibración adicional autorizada.

Se realizaron 4290 ajustes de bosques: ocho candidatos × cuatro folds internos más un reajuste externo por configuración/fold. Se guardan los modelos externos y los cuatro modelos internos de la configuración elegida, todas las OOF candidatas, tiempos, advertencias, parámetros y muestras de bootstrap efectivas. Se reutilizan medianas/escalas solamente dentro del entrenamiento correspondiente. Cualquier interpretación posterior a la evaluación permanece exploratoria.

Fuentes primarias para la propuesta posterior, sin ejecución: [parámetros y regularización de CatBoost](https://catboost.ai/docs/en/concepts/parameter-tuning), [eval_set y early stopping de CatBoost](https://catboost.ai/docs/en/concepts/python-reference_catboostregressor_fit), [parámetros XGBoost](https://xgboost.readthedocs.io/en/stable/parameter.html). Su evaluación temprana debe quedar dentro del entrenamiento externo; no se instala ni ejecuta CatBoost/XGBoost en F6.


## Verificación final

Pasaron nueve pruebas en total: tres del modelo, dos de efectos locales y cuatro de integración. Se reprodujeron todas las predicciones de los 650 modelos guardados externos e internos seleccionados; se verificaron los ocho candidatos por fold contra sus particiones internas originales. Se comprobaron 10679 archivos anteriores sin cambios. Se conservan 8556 filas OOF de referencias y F6; 4290 ajustes de bosque, con384 árboles cada uno. No se entrenó un modelo final sobre138 etiquetas ni se generaron predicciones PRED. La decisión, parámetros, tiempos y procedencia se conservan en esta versión.
