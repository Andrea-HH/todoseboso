# Indicadores temporales para pesos continuos de corrección: diseño congelado

Continuación exploratoria del inventario del cuartil difícil. Las asociaciones observadas no son confirmatorias. No se ajusta una regla a35parcelas ni se utilizan sus etiquetas globales para aprender pesos. Se mantienen138targets,65folds e internas congeladas, CT3/J7 originales, ningún PRED59 ni modelo final138, ningún cambio de Champion.

## Nueve entradas predefinidas para indicadores/pesos

Ocho temporales y un contexto físico, sin screening abierto:

1. Piso histórico NDVI: media anual de medianas mensuales NDVImin mayo–octubre, promediada2022–2024.
2. Piso histórico FAPARmin: misma construcción.
3. Intensidad de exceso de brecha NDVI: media de z mensual positivo2025frente a historia propia2022–2024.
4. Persistencia efectiva de ese exceso: (suma z positivo)²/(6×suma z²);0si no hay exceso, faltante si falta soporte. Distingue un pico de varios meses de exceso sin umbral de evento elegido con Y.
5. Anomalía propia de volatilidad de brecha: SD de seis meses2025frente a media/SD de las SD anuales2022–2024.
6. Exceso de brecha superior MSI: media de z positivo de la brecha máximo−medio relativa al nivel medio, contra historia propia mensual.
7. Anomalía de forma del pico EVI: z histórico de(max−mediana)/max(rango,.05) de las seis medianas mensuales.
8. Desacuerdo de forma Sentinel–Planet: (1−correlación Pearson de seis medianas mensuales EVI2025)/2, tras centrado implícito propio; ausencia/constancia=>faltante.
9. Pendiente mínima original: TOPO_BASIC_slope_min. No se confunde con pendiente temporal de un índice.

Brechas se calculan primero por adquisición y luego se obtiene mediana por mes. Se requiere soporte de los seis meses y los tres años históricos para cada resumen correspondiente. No interpolación ni ausencia convertida a cero. Brecha relativa=max(media−mínimo,0)/max(abs(media),.1) para NDVI y max(máximo−media,0)/max(abs(media),.1) para MSI; recortar0..5. Pares materialmente invertidos se marcan inválidos. SD histórica con ddof1y suelo fijo.05para z, recorte±6. Imputación por mediana y escalado únicamente en cada entrenamiento. Planet sólo se usa en2025; no se inventa su historia.

Se conservan soporte por mes y cobertura, fuera del modelo. No se interpreta NDVImin como píxel físicamente localizado, persistencia como fracción de superficie, MSI como estrés medido ni historia como cebada confirmada. Los indicadores de temporada completa sólo están disponibles al cierre de octubre, no para pronóstico temprano. La historia de tres años puede reflejar rotación/cobertura/cultivos distintos y no es una climatología estable.

## Corrector candidato y controles

Corrector C4 fijo sobre los cuatro padres del candidato anterior: TPI medio, pendiente media, anomalía propia NDWI julio–agosto y cambio EVI julio–agosto menos mayo–junio. Elastic Net alpha=.01,l1_ratio=.5,intercepto, imputación/escalado de entrenamiento, max_iter200000. Ajuste final δ=.5×clip(predicción residual,−.5,+.5), máximo±.25t/ha. Es un control nuevo con parámetros fijos, distinto del C4 previo seleccionado internamente; también se conserva éste como benchmark exacto. No se usan sus hiperparámetros externos para calibrar capas internas.

Seis arquitecturas por base CT3/J7,12nuevas,780modelos externos:

- C4_FIXED: aplicar candidato sin atenuación.
- C4_CONSTANT: un peso constante aprendido sobre predicciones cross-fitted del candidato.
- C4_SHARED: peso continuo dependiente de los nueve indicadores.
- C4_DIRECTIONAL: pesos separados para candidatos δ>0yδ<0. La ruta usa signo de la corrección predicha, nunca signo real de error o rendimiento externo.
- INDICATORS_DIRECT: EN fijo directamente sobre las nueve entradas.
- C4_INDICATORS_DIRECT: EN fijo sobre los cuatro padres más las nueve entradas.

Las dos últimas distinguen utilidad de la representación de utilidad específica de ponderar C4. No se inicia una búsqueda abierta de arquitecturas ni más combinaciones después de los resultados.

## Cómo se aprende un peso

Se ajusta r≈δ×(b0+Zb), donde r=Y−predicción base fuera de muestra y δes una corrección candidata también fuera de muestra. Zestandarizado e imputado en entrenamiento, recortado±6. Ridge ponderado porδ², penalización intercepto=.1×sumaδ²y coeficientes=1×sumaδ². Peso desplegado=clip(b0+Zb,0,1). El control constante es clip(sumaδr/(1.1sumaδ²),0,1). No es una probabilidad calibrada de error.

Para pesos por signo se exigen15casos en la ruta y energíaδ²>1e−12; si no, respaldo al peso constante global del entrenamiento. Todos los hiperparámetros se fijan antes de resultados; no se seleccionan con folds externos ni se alternan posteriormente para rescatar regiones. Se permite peso0 como no corregir, peso1como aplicar el candidato completo. Ningún peso puede cambiar signo ni aumentar magnitud del candidato.

## Anidamiento sin residuos externos

Se recupera calibración base cross-fitted de neighbor_signal_linear y contextos más profundos de signal_feature_engineering, con posiciones y exclusiones exactas. Para construir δOOF de entrenamiento A, cada candidato se ajusta en A_j con residuos base cross-fitted exclusivamente dentro de A_j y predice D_jexcluido. Su imputación/escalado también excluye D_j. El peso se ajusta en A con esos δOOF y residuos baseOOF. Finalmente el candidato se ajusta sobre A, y candidato+peso predicen el fold externo desconocido. Los hiperparámetros fijos no requieren selección adicional; se mantienen las particiones internas para generar la calibración honesta. Se comprueba exclusión externa en los ledgers heredados.

No se utilizan residuos globales OOF externos como targets de entrenamiento. Se conserva la predicción externa exacta de CT3/J7; benchmarks C4 previos se copian únicamente para comparación, no para entrenar los pesos.

## Evaluación y decisión

RMSE/R², MAE, sesgo y SD del error, siempre OOF completas por repetición y luego promedio aleatorio de diez; perfiles/municipios/espacial separados. Regiones, bloque5/Almoloya y bloque3, omisiones sin reajuste, cuartiles de Y y cuartil difícil previamente congelado, sin top10/sin35, pares intraperfil, mejoras y deterioros por parcela. Pesos por región y por signo, fracción de candidatos bien/mal dirigidos, pesos cuando ayudan/perjudican, fallbacks, estabilidad de coeficientes y relación del peso con error real sólo como diagnóstico externo.

Contrastes predefinidos por base: seis nuevas vs base; tres pesos vs C4_FIXED; dos pesos variables vs C4_CONSTANT; SHAREDvsDIRECTIONAL; integración directa13vsindicadores9; C4_FIXEDvsC4previo internamente seleccionado. Son14por base,28en total×4protocolos=112pruebas. Bootstrap5000por conglomerados, signos agrupados y Holm conjunto112. Inferencia exploratoria de OOF fijas, limitada por pocos grupos espaciales y búsqueda histórica. No proclamar superioridad con una región o un único cuartil.

Se considera útil el peso variable si mejora frente al mismo corrector sin ponderar y al peso constante, no sólo frente a la base, y mantiene estabilidad territorial. Si falla, distinguir representación nueva débil de candidato mal dirigido o de un peso que sólo recalibra sesgo. No promover ni producir PRED automáticamente.
