# Modelado por calendario: primera batería lineal regularizada

Ejecutado el14 de octubre2026. **Ninguna variante nueva ofrece una mejora territorial equilibrada frente a C-T3.** Lluvia+Tmax por ventanas presenta una señal predictiva interesante pero su mejora espacial depende del bloque3 y pierde transferencia municipal. La trayectoria Sentinel añadida y el histórico no aportan mejoras en esta formulación. No se promueve ningún modelo.

## Diseño congelado y ejecución

Se reutilizó `outputs/modeling/ct3_residual_conditional/v1/cache/frozen65_splits.joblib`, con50folds aleatorios (10repeticiones×5),5por perfil,5municipales y5espaciales. Cada fold conserva sus cuatro particiones internas originales. Se verificó disyunción y cobertura, y se contrastaron IDs y targets de la referencia C-T3. Todas las138parcelas participan exactamente una vez por repetición/protocolo. No se usaron las59parcelas PRED para ajuste, selección o predicción.

Ocho variantes Ridge, misma rejillaalpha={100,10,1,0.1,0.01,0.001}; se usa alpha_sklearn=n_train×alpha para optimizar MSE+alpha×L2. Selección por RMSE de OOF internas completas; empate redondeado12 favorece mayoralpha y menorgamma. No se promedian métricas porfold para elegir el candidato. Sin early stopping ni selección externa. La media del objetivo se ajusta mediante intercepto dentro de entrenamiento; no hay normalización global de Y.

Imputación por mediana y escalado ajustados exclusivamente en el entrenamiento correspondiente; columnas completamente ausentes usan0, según diseño congelado. Historia estandarizada multiplicada porgamma={0.25,0.5,1} antes de Ridge: menor gamma equivale a mayor penalización L2 del efecto histórico. Indicadores de ausencia históricos, cuando corresponden, reciben la misma penalización del bloque. No se introducen etiquetas regionales como predictores ni correcciones locales.

|Modelo|Entradas|Columnas de diseño|
|---|---|---:|
|C-T3|Referencia ElasticNet compact3+NDVI mayo, OOF recuperadas|4|
|CAL00|Las mismas cuatro entradas, Ridge; control de arquitectura|4|
|CAL01|Lluvia en cuatro ventanas+NDVI mayo original|5|
|CAL02|CAL01+Tmax en cuatro ventanas|9|
|CAL03|compact4+cuatro niveles NDVI por ventana+heterogeneidad NDVI julio–agosto|9|
|CAL04|Clima de CAL02+las cinco variables Sentinel de CAL03|14|
|CAL05|CAL04+medias/SD históricas de esas cinco variables Sentinel+indicadores de ausencia|29 (24numéricas+5indicadores)|
|CAL06|CAL04+desviaciones2025−historia/SD históricas+indicadores|29|
|CAL07|CAL05 sin indicadores de ausencia|24|

Las cuatro ventanas son abril, mayo–junio, julio–agosto y septiembre–octubre. El NDVI mayo original se conserva como ancla/control, aunque tenga correlación con ventanas ampliadas. No se incluyeron todos los148atributos del inventario ni se seleccionaron índices mediante screening de Y. La historia climática se conserva en el set, pero esta primera ablación histórica se limita a Sentinel, conforme al plan.

CAL01 frente aCAL02 permite aislar el aporte deTmax en esta representación; comparar soloCAL02 con C-T3 mezclaría cambios de variables, calendario y algoritmo. CAL00 controla el cambio ElasticNet→Ridge.

Se realizaron22,360ajustes internos/externos,520modelos externos, en131.95segundos de ejecución del script. Cero advertencias registradas. Los hashes de los insumos protegidos permanecieron iguales. No se entrenó modelo final sobre138ni se cambió Champion.

## Resultados OOF

RMSE t/ha; menor es mejor. Aleatorio es la media de métricas sobre OOF completas de cada una de las10repeticiones. Los otros protocolos tienen una repetición completa de138parcelas. No son promedios de RMSE de los cincofolds.

|Modelo|Aleatoria|Perfil|Municipal|Espacial|
|---|---:|---:|---:|---:|
|C-T3|0.5116|0.5206|0.5813|0.6788|
|CAL00: Ridge compacto|0.5118|0.5178|0.5654|0.6861|
|CAL01: lluvia ventanas|0.5133|0.5317|0.8216|0.8733|
|CAL02: lluvia+Tmax ventanas|0.4953|0.5105|0.7958|0.6067|
|CAL03: compacto+Sentinel|0.5276|0.5297|0.6981|0.8373|
|CAL04: combinación2025|0.5122|0.5111|0.8213|0.7239|
|CAL05: +historia|0.5295|0.5356|0.8527|0.8139|
|CAL06: +desviaciones|0.5266|0.5383|0.8398|0.7675|
|CAL07: historia sin indicadores|0.5298|0.5464|0.8625|0.8329|

CAL00 muestra que cambiar a Ridge no soluciona por sí solo el problema: mejora municipal0.0159, conserva aproximadamente aleatoria/perfil y empeora espacial0.0074. No es una ventaja equilibrada demostrada.

CAL02 mejora aleatoria frente a C-T3 en las10repeticiones; son repeticiones correlacionadas de las mismas etiquetas, no10confirmaciones independientes. Añadir Tmax aCAL01 reduce RMSE en los cuatro protocolos, especialmente espacial−0.2666. Sin embargo, aun así municipal queda muy por debajo de C-T3. El beneficio depende de representación/protocolo; no prueba superioridad general de temperatura ni de nuevas fechas.

|Métrica|C-T3 aleatoria / perfil / municipal / espacial|CAL02 aleatoria / perfil / municipal / espacial|
|---|---|---|
|MAE|0.3749 /0.3915 /0.4603 /0.5306|0.3613 /0.3869 /0.6585 /0.4535|
|R²|0.6361 /0.6232 /0.5302 /0.3594|0.6589 /0.6377 /0.1194 /0.4882|
|Sesgo predicho−observado|+0.0005 /+0.0046 /−0.0203 /+0.1912|+0.0002 /−0.0128 /−0.2385 /+0.0593|

## Transferencia regional y concentración

**La ganancia espacial deCAL02 depende del bloque3.** Su RMSE cae de0.9096 a0.4346 y el sesgo de+0.7182 a−0.1144. Pero el bloque4 empeora de0.7990 a1.0875, sesgo+0.5743→+0.9093. Los bloques1y2 cambian poco; el5mejora de0.3602a0.2257.

Al omitir el bloque3 del cálculo, sin reajustar modelos, CAL02 tiene RMSE0.0752mayor que C-T3. Por tanto, la mejora espacial global no persiste sin su principal región beneficiada. El descenso global de MSE proviene tanto de menor sesgo al cuadrado (0.03654→0.00351) como de menor dispersión de errores (0.42420→0.36458).

En validación municipal, Chignahuapan pasa deRMSE0.5807a0.8144 y de sesgo−0.2011a−0.6037. Singuilucan pasa de0.8677a1.3399 y sesgo+0.7589a+1.2923. Calpulalpan también empeora, mientras Almoloya mejora. La pérdida municipal global permanece al omitir por separado cualquiera de los nueve municipios; no depende únicamente de uno. LosR² de grupos muy pequeños, o casi constantes, no tienen interpretación estable.

Las cinco mayores mejoras espaciales deCAL02 se ubican en Tlaxcala (AGC_138,169,058,068,048); los cinco mayores deterioros están en Singuilucan (AGC_089,148,078,067,140). Son diagnósticos de las mismas OOF, no autorización para construir reglas territoriales ni eliminar casos.

## Intraperfil

Se reutiliza el cálculo original de errores en diferencias de rendimiento entre pares del mismo perfil dentro del mismofold, reportando ponderación por par e igual por perfil. No se mezclan pares entre modelos entrenados en folds diferentes. Los pares comparten parcelas y no son observaciones independientes.

CAL02 espacial presenta RMSE intraperfil con igual peso por perfil0.5444frente a0.5401 de C-T3; por pares0.7766frente a0.7675. Su ganancia espacial global no se traduce en mejor diferenciación intraperfil. En aleatoria, el cambio es mínimo y mixto según ponderación.

Añadir Sentinel2025 empeora esta capacidad: CAL04 aleatoria0.6139frente aCAL02 0.5883 (igual peso por perfil); espacial0.5691frente a0.5444. El hecho de que Sentinel distinga X dentro del mismo perfil no garantiza que esas diferencias correspondan al rendimiento.

## Historia y desviaciones2025

CAL05 yCAL06 empeoran RMSE en los cuatro protocolos frente aCAL04. CAL05 selecciona elgamma mínimo0.25en62de65folds: la selección interna tiende a reducir el peso histórico. Ese mínimo es un límite congelado, no se amplió después de observar resultados. La opción de no usar historia está representada porCAL04, pero no se seleccionó internamente como una opción nula dentro deCAL05/06. En futuras pruebas podría fijarse esa alternativa desde el diseño; no se reejecutó aquí.

Retirar indicadores de ausencia no rescata la historia: CAL07 empeora los cuatro RMSE frente aCAL05. La ausencia histórica no parece ser la única causa del deterioro. Tampoco se demuestra que los indicadores tengan significado agronómico.

CAL06 supera aCAL05 espacialmente, pero sigue por debajo deCAL04 y C-T3. En un modelo lineal nivel+historia y nivel+desviación abarcan el mismo espacio cuando hay datos completos; aquí cambian penalización y tratamiento de ausencias. No se interpreta esa diferencia como información nueva proporcionada porDELTA.

La asociación exploratoria entre ganancias deCAL05vsCAL04 y tres descriptores históricos tiene Spearman entre−0.136y+0.193 según protocolo/variable. No aparece una relación fuerte que justifique una regla de corrección dependiente de una anomalía grande. No se realizaron pruebas de significancia ni se seleccionó modelo con estas asociaciones.

## Complejidad

Promedio de grados de libertad efectivos del Ridge, incluyendo intercepto, primero por protocolo y después con igual peso entre protocolos: CAL00≈4.46, CAL02≈7.22, CAL04≈10.90, CAL05≈16.48. No equivalen a número de variables seleccionadas: Ridge conserva coeficientes continuos y reduce su flexibilidad. La mayor complejidad de historia no viene acompañada de mejor desempeño OOF.

La rejilla alcanza alpha mínimo en algunosfolds (CAL00:5,CAL01:11,CAL02:7,CAL03:1,CAL04:4,CAL05/06/07:1cada uno); no alcanza el máximo. No se amplió retrospectivamente. Los coeficientes y sus signos se conservan como diagnóstico de estabilidad, sin interpretación causal.

## Decisión

Mantener C-T3 como referencia simple equilibrada. CAL00 queda como control comparable, no como nuevo champion. CAL02 sirve como evidencia exploratoria de una interacción entre representación climática y transferencia territorial; no recomendar su uso general, porque pierde municipalmente y su ganancia espacial depende del bloque3.

La hipótesis de que estas cinco representaciones Sentinel y sus medias/SD históricas añaden valor de forma lineal sobre este núcleo queda debilitada. No se rechaza toda historia satelital ni toda representación temporal: solo se probó este subconjunto, ventanas regionales aproximadas y familia Ridge. El cultivo histórico desconocido, la contaminación óptica y la correspondencia entre calendario regional y fecha real permanecen como limitaciones.

Si se continúa, priorizar la comparación no lineal conservadora de representaciones2025 previamente definidas, antes de ampliar historia o variables. Su diseño debe congelarse antes de entrenar y reconocer que usa evidencia externa exploratoria para formular el siguiente experimento. No ejecutar correcciones regionales aprendidas a partir de estos errores. CatBoost todavía no se ejecutó en esta batería.

Solo tenemos rendimientos2025: estos resultados no evalúan pronósticos en otros años. La singularidad climática2025 observada en X no garantiza señal incremental de rendimiento ni calibración temporal. No se declara superioridad estadística sobre comparaciones repetidas de las mismas138etiquetas.

## Artefactos y verificación

`outputs/modeling/agronomic_calendar/v1/`: diseño congelado con hashes,520modelos,65checkpoints, OOF completas (14352predicciones nuevas+1794referencia), selección interna, coeficientes, RMSE/MAE/sesgo/R² por repetición, intraperfil, regiones y omisiones sin reajuste. `diagnostics/` contiene ablaciones, complejidad, concentración de ganancias, parcelas extremas, sesgo/dispersión y figura `rmse_vs_ct3.png`.

Scripts394y395; implementación`src/calendar_modeling.py`. Cinco pruebas pasaron: historia temporal, agregación, faltantes, corte, aislamiento de transformación y mayor contracción histórica con menorgamma. Se guardó y verificó la integridad de las referencias. No intervalos predictivos: Ridge aquí genera predicciones puntuales, no una incertidumbre calibrada.

El script396recargó los520modelos externos y reprodujo las14352predicciones nuevas sobre sus parcelas retenidas: diferencia absoluta máxima0.0. Verificó disyunción de IDs de entrenamiento/evaluación, ausencia de ajustes finales138 e integridad de hashes. Evidencia en`audit/model_replay.json`.
