# Ingeniería de señales: interpretación y decisión

Se completaron14 recetas nuevas sobre65folds,910modelos externos, con las referencias CT3/J7 intactas. Cuatro pruebas automatizadas pasaron. La evaluación reproduce todos los modelos y verifica las exclusiones de entrenamiento. Es una investigación exploratoria: sus hipótesis proceden de errores observados en estos mismos datos.

## Comparación principal: RMSE / R²

|Modelo|Aleatoria|Perfil climático|Municipal|Espacial|
|---|---|---|---|---|
|CT3|0.5116 / 0.6361|0.5206 / 0.6232|0.5813 / 0.5302|0.6788 / 0.3594|
|J7_BOTH|0.4864 / 0.6709|0.4890 / 0.6675|0.5808 / 0.5309|0.6808 / 0.3556|
|CT3_P_RAW: corrector cuatro padres|0.5121 / 0.6353|0.5235 / 0.6189|0.5787 / 0.5344|0.6656 / 0.3839|
|J7_P_RAW: corrector cuatro padres|0.4863 / 0.6711|0.4955 / 0.6586|0.5774 / 0.5365|0.6490 / 0.4143|
|J7_P_ENG: padres e interacciones|0.4864 / 0.6710|0.4972 / 0.6563|0.5810 / 0.5306|0.6605 / 0.3934|

La tabla completa de16entradas, incluidos los controles sólo de intercepto, está en signal_feature_engineering_results.md y Excel. Las métricas aleatorias promedian métricas de138OOF completas de cada una de diez repeticiones. Los protocolos no se promedian entre sí.

## Qué aprendimos sobre las representaciones

**Historia propia:** seis anomalías normalizadas por la SD2022–2024 no mejoran de forma equilibrada ninguna base. En J7 producen RMSE0.4872/0.4909/0.5774/0.6929 frente a0.4864/0.4890/0.5808/0.6808. La mejora municipal coincide exactamente con SHIFT: los correctores históricos quedaron con cero coeficientes en los cinco folds municipales; la diferencia viene del intercepto. No es evidencia incremental de la historia en ese protocolo. Las anomalías suelen ser menos perjudiciales que incorporar18componentes históricos, pero eso no demuestra mejora frente a la base.

**Momento y persistencia de heterogeneidad:** las seis derivadas tampoco superan consistentemente las bases. En J7 dan0.4869/0.4906/0.5803/0.6842. Los21descriptores mensuales originales empeoran más en varios protocolos; la reducción temporal controla parte del deterioro, pero no añade una mejora predictiva clara. La brecha medio−mínimo representa heterogeneidad del resumen satelital, no área afectada ni enfermedad observada. La persistencia es media/máximo de brecha relativa, no una fracción de píxeles.

**Contexto físico y dos señales derivadas:** el resultado prometedor corresponde a cuatro padres:

1. TPI3×3 medio.
2. Pendiente media.
3. Anomalía propia del NDWI de julio–agosto: (2025−media2022–2024)/max(SD,.02), recortada±6.
4. Cambio de EVI Sentinel: media julio–agosto menos media mayo–junio.

P_RAW significa control de los padres de las interacciones; no significa que sus cuatro columnas sean mediciones sin transformación. Ya contiene dos variables derivadas. El corrector usa Elastic Net con intercepto seleccionado internamente. TPI/pendiente participan directamente en la corrección y no sólo en el peso físico que J7 ya tenía.

Añadir TPI negativo y productos con humedad/cambio EVI (P_ENG) resulta inferior al corrector de cuatro padres en los cuatro protocolos para ambas bases. La muestra no respalda aumentar esta complejidad bajo el protocolo y regularización probados. No se concluye que estas interacciones carezcan de sentido agronómico.

## De dónde viene la mejora espacial J7_P_RAW

Su RMSE espacial baja0.03179t/ha, aproximadamente4.67%. No cambia materialmente el error aleatorio (−0.000086); empeora por perfil climático (+0.00650). La mejora municipal (−0.00349) coincide exactamente con SHIFT, también con cero coeficientes en los cinco folds: allí sólo recalibra intercepto.

La mejora espacial global procede fundamentalmente de reducir sesgo:0.2913→0.2052t/ha; la SD de errores permanece prácticamente igual,0.6153→0.6157. No significa que se haya explicado de forma general la variación entre parcelas. El RMSE de diferencias intraperfil con igual peso por perfil espacial pasa0.5320→0.5257, pero en aleatoria queda0.5777→0.5778 y por perfil0.5317→0.5361. Tampoco se demuestra una solución consistente al problema intraperfil.

|Bloque espacial|n|J7 RMSE|J7_P_RAW RMSE|Cambio|
|---|---:|---:|---:|---:|
|1|38|0.5246|0.5010|−0.0236|
|2|37|0.5537|0.5537|0.0000|
|3|35|0.9160|0.8550|−0.0610|
|4|18|0.7988|0.6715|−0.1273|
|5|10|0.3621|0.5954|+0.2333|

El bloque5 corresponde aquí a Almoloya. La corrección agrava su subestimación: sesgo−0.3316→−0.5778t/ha. Los cambios son heterogéneos; el buen RMSE espacial total no equivale a transferencia territorial equilibrada. En los bloques3/4 reduce principalmente sobreestimación: sesgos0.7311→0.6293 y0.5746→0.3744.

La ganancia no depende de un solo bloque: al omitir cualquiera de los cinco bloques del cálculo sin reajustar, el cambio global de RMSE sigue siendo favorable (−0.0157 a−0.0466). Tampoco depende exclusivamente de las diez parcelas que motivaron esta etapa: sin ellas la mejora espacial se conserva en−0.02498t/ha. El64.0% de la ganancia cuadrática espacial proviene de las otras128parcelas. Estas sensibilidades son descriptivas y no constituyen nuevas validaciones independientes.

Por municipio dentro de validación espacial, Singuilucan mejora−0.1690t/ha y Chignahuapan−0.0152; Almoloya empeora+0.2333 y Cuautepec+0.1369. Los municipios con1–3parcelas se conservan en tablas, sin extrapolar estabilidad a partir de tan poco soporte.

CT3_P_RAW también mejora espacialmente (−0.01313), pero su ganancia prácticamente desaparece al omitir bloque3 (+0.00047). No tiene la misma distribución de mejora que J7_P_RAW.

## Incertidumbre, límites y decisión

Ninguno de los80contrastes predefinidos supera Holm0.05. J7_P_RAW vs J7 espacial tiene diferencia−0.03179 e intervalo bootstrap agrupado95%[−0.0750,+0.0314], prueba de signos agrupada p=0.375, Holm1.0. Sólo hay cinco conglomerados espaciales; el bootstrap sobre OOF fijas no incorpora toda la búsqueda histórica ni el reajuste. No se declara superioridad estadística.

Las correcciones se limitaron a±.25t/ha desplegadas. El resultado evalúa esta familia conservadora de correctores EN y estas definiciones; no rechaza toda ingeniería temporal o modelos alternativos. Historia de tres años, observación óptica y posible rotación/cambio de cobertura limitan la interpretación. La alerta de bibliotecas OpenMP coexistentes del entorno quedó registrada; la ejecución terminó y el replay numérico de910modelos verifica sus salidas. No aparecieron advertencias de convergencia EN en el registro final.

**Recomendación:** conservar CT3 y J7 como referencias; no promover una variante ni combinar automáticamente todos los bloques. Retener J7_P_RAW como candidato exploratorio acotado por su mejora espacial fuera del top10, y dirigir una futura confirmación hacia estabilidad territorial/contracción de este corrector de cuatro entradas. Las anomalías históricas aisladas, la heterogeneidad aislada y los productos adicionales no justifican por ahora una expansión. Para una afirmación confirmatoria hace falta evidencia independiente del banco que hemos utilizado repetidamente.

Fuentes: outputs/modeling/signal_feature_engineering/v1/tables y evaluacion_ingenieria_de_senales.xlsx. Scripts470preparación,471ejecución,472evaluación y473auditoría. Fuentes/modelos anteriores protegidos por hashes; sin entrenamiento final138, cambios Champion ni PRED59.
