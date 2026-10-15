# Calendarios agroclimáticos: expansión congelada de modelado

Diseño y ejecución iniciados el14 de octubre2026. Esta batería completa los contrastes pendientes definidos en la conversación: selección ElasticNet, no linealidad CatBoost, EVI, señales de humedad, historia climática y resúmenes trimestrales/estacionales. No constituye una búsqueda de todas las combinaciones posibles del inventario ni nuevas reglas regionales.

## Datos y validación

138etiquetas de2025 y mismos65folds externos/particiones internas archivados. Sentinel es la única base satelital de esta batería; datos2022–2024 son contextoX, no etiquetas adicionales. No uso de PRED para ajustar o seleccionar. Las59geometrías pueden conservar atributos deterministas en el set target-free, pero la matriz usada por los modelos contiene exclusivamente138filasTRAIN.

Las ventanas principales son abril, mayo–junio, julio–agosto y septiembre–octubre. Se agregan tres ventanas congeladas: abril–junio, julio–septiembre y abril–octubre. Los dos trimestres no incluyen octubre: comparar contra siete meses mezcla anchura de ventana y cobertura temporal. No se atribuirá cualquier diferencia exclusivamente a la longitud del resumen. Se conservan los mismos cálculos para2022,2023,2024,2025 en`data/processed/agronomic_calendar_set/v2_temporal_extension`. No se extrapolan fechas reales de siembra/cosecha ni se introducen datosnoviembre–diciembre.

Agregación Sentinel: media de medianas mensuales, cada mes con igual peso y todos los meses requeridos. Precipitación acumulada por suma; temperaturas ponderadas por días calendario. Se preservanNaN, historia con tres años completos y diferencias respecto de2025. Medias de tres años no son normales climáticas de largo plazo; no se supone mismo cultivo todos los años.

## Bloques

Ambos algoritmos reciben las mismas columnas por bloque. CAL00–CAL07 tienen la definición de la primera batería, ahora con nueva selección ElasticNet/CatBoost. No se repiten los ajustes Ridge sellados.

|Bloque|Pregunta|
|---|---|
|CAL00|Controlcompact4 con procedimiento interno común|
|CAL01|Lluvia en cuatro ventanas+NDVI mayo|
|CAL02|CAL01+Tmax en cuatro ventanas|
|CAL03|compact4+cuatroNDVI de ventana+desviación espacialNDVIjulio–agosto|
|CAL04|Clima deCAL02+cinco variables Sentinel deCAL03|
|CAL05|CAL04+medias/SD históricas de esas cinco variables Sentinel+indicadores|
|CAL06|CAL04+desviaciones2025/SD históricas Sentinel+indicadores|
|CAL07|CAL05sin indicadores de ausencia|
|CAL08|CAL04+cuatro ventanas EVI|
|CAL09|CAL04+cuatro ventanasNDWI y cuatroMSI|
|CAL10|CAL04+EVI+NDWI+MSI|
|CAL11|CAL04+medias/SD históricas de lluvia yTmax de las cuatro ventanas|
|CAL12|CAL04+desviaciones/SD históricas de ese mismo clima|
|CAL13|compact4+cinco resúmenes Sentinel en dos trimestres|
|CAL14|compact4+cinco resúmenes Sentinel en siete meses|
|CAL15|Lluvia/Tmax en dos trimestres y temporada completa+NDVI mayo|
|CAL16|CAL15+los diez atributos Sentinel trimestrales|

Los cinco resúmenes Sentinel trimestrales/estacionales sonNDVI,EVI,NDWI,MSI y desviación espacialNDVI. ElNDVI exclusivo de mayo original se conserva. NDWI/MSI son índices espectrales: no se interpretan como agua del suelo o estrés medidos directamente.

Quedan fuera de esta batería la expansión de historiaEVI/NDWI/MSI, variables Tmin adicionales, fenología inferida por umbrales, índices derivados de rendimientos/costos FIRA y todas las combinaciones del inventario. Los cambiosNDVI entre ventanas son combinaciones lineales de los niveles; no se añaden como señales independientes simultáneas. No se añaden variables vía screening abierto.

## Selección dentro de entrenamiento

ElasticNet: alpha={1,0.1,0.01,0.001},l1_ratio={1,0.9,0.5,0.1};max_iter100000,tol1e-7. Medianas y escalas se aprenden por entrenamiento, conallmissing0. Para historia,gamma={0,0.25,0.5,1} multiplica sus columnas después del escalado y se selecciona conjuntamente. Gamma0 permite omitir historia; lasgamma menores refuerzan la contracción, pero no son porcentajes de la predicción. L1 puede eliminar variables individualmente. Los indicadores de ausencia heredan penalización histórica; solo se añaden cuando lo indica el bloque.

CatBoost: los ocho candidatos conservadores originalesF7, profundidades2/3,150/300árboles,learning_rate0.03/0.06,l2_leaf_reg10/30, según lista curada archivada, no producto cartesiano. Sin eval_set externo,early stopping,bootstrap ni aleatoriedad adicional de puntuación. Semilla2026,thread_count1,border_count64,leaf_estimation_iterations1. Cada variable histórica/indicador recibefeature_weight0.5frente a1para2025 al puntuar divisiones. Esto es una preferencia de arquitectura, no equivalente a la regularización lineal ni garantía de dominio2025. Definición oficial: https://catboost.ai/docs/en/references/training-parameters/common#feature_weights

Multiplicar valores históricos de una columna no reduce de forma equivalente su influencia en árboles. Aquí se utiliza el parámetro específico de selección de divisiones. La eliminación de historia se evalúa además mediante las ablaciones con2025solo; CatBoost no tiene una alternativa gamma0 explícita dentro del mismo bloque.

Todos los candidatos se comparan porRMSE sobre OOF internas completas, no media deRMSE porfold. Empates redondeados12eligen el primer candidato conservador. La selección de variables, escalado, imputación y opciones de regularización no ven el fold externo. CatBoost elige divisiones, pero no garantiza un subconjunto estable o agronómicamente causal.

CAL00se ajusta con este procedimiento común. Sus ajustes no son idénticos alcontrol archivadoC-T3ni aF7-00: cambia la rejillaElasticNet y el criterio interno conjunto respecto a media porfold deF7original. Se conservan ambos controles archivados por separado para evitar atribuir sus diferencias únicamente a nuevas variables. La primera bateríaRidge se recupera sin reajustar.

## Lectura de resultados

RMSE,MAE,sesgo predicho−observado yR² por OOF completa/repetición; diez repeticiones aleatorias y una para los otros tres protocolos. Comparaciones pareadas contra controles, entre algoritmos con el mismo bloque y entre bloques padre/hijo. Comparaciones externas exploratorias por reutilización repetida de estas138etiquetas.

Diagnósticos: intraperfil dentro del mismofold (igual peso por perfil y por par), por estado/municipio/bloque, omisión de regiones sin reajustar, distribución de ganancias por parcela, parcelas extremas, sesgo/dispersión, estabilidad de selección. Coeficientes y frecuencias de división son diagnósticos predictivos, no causas.

ElasticNet reporta variables con efecto estandarizado no nulo; CatBoost variables realmente usadas en divisiones, no importancia por impureza como causalidad. Se conservan configuraciones, advertencias, modelos y predicciones. Árboles y hojas no equivalen directamente a grados de libertad de Ridge.

Se evalúa si historia ayuda contra su base2025, si EVI y humedad se complementan, y si la mejora persiste fuera del bloque3o de un municipio. No elegir la mejor variante por espacial y presentar esa misma evaluación como confirmación independiente. No construir reglas regionales posteriores con estos errores.

## Preservación y ejecución

DiseñoJSON escrito antes del entrenamiento:`outputs/modeling/agronomic_calendar/expansion/v1/frozen_design.json`, con hashes de fuentes, referencias e implementación. Scripts397–399, módulo`src/calendar_expansion.py`. Siete pruebas automatizadas pasaron antes de entrenar.

Ejecución inicial4procesos; se retomaron checkpoints válidos con12procesos por rendimiento operativo. La preferencia de historia, candidatos y splits no cambiaron. Registro en`audit/execution_parallelism.json`; los camposworkers del diseño original describen la configuración inicial. Sin agentes adicionales.

Se ajustó después a6procesos por saturación del equipo. Se detectó que CatBoost usa todos los núcleos por defecto al predecir y al calcular importancia posterior al ajuste, independientemente dethread_count1de entrenamiento. El módulo adicional`src/calendar_execution.py` cambia solo esos valores por defecto a1; no modifica archivos fuente protegidos, datos, entrenamiento, rejillas ni selección. Se verificó igualdad exacta de predicciones e importancias de un modelo existente antes/después. Hash del módulo y resultados en`audit/single_thread_scoring.json`; script401retoma checkpoints. El replay final utiliza la misma concurrencia de puntuación. La limitación de un hilo evita sobreasignación entre procesos.

No Champion sobrescrito, no modelo final ajustado sobre138, no59prediccionesPRED, no modelos residuales. No decisión automática de promoción.
