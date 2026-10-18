# Bases simplificadas y corrección condicionada a vecinos

## Resultado de la investigación

Se investigó la simplificación de la base completa, manteniendo R3 fijo como representación del corrector. Se cruzaron seis bases con siete usos del corrector (global, y soporte/atipicidad en tres geometrías), además de las seis bases sin R3: 48 entradas sobre los 65 folds originales. Se conservaron las respuestas, los modelos anteriores y las referencias exactas C-T3, J7, C-T3+R3 y J7+R3. La reconstrucción SHARES también reprodujo exactamente las OOF antiguas J7_SHARES.

Hay dos resultados diferentes: reducir el gate de J7 y añadir R3 produce una candidata de 26 entradas; partir de C-T3 y ponderar R3 por soporte satelital produce otra de sólo ocho entradas, con un costo claro en aleatoria/perfil y resultados territoriales próximos a J7+R3. No hay una arquitectura que gane en todos los protocolos ni evidencia de superioridad estadística tras ajuste múltiple.

## Cómo funciona la corrección por distribución local

La predicción es `base(x) + (amplitud/.5) * peso(x) * delta_R3(x)`, donde `delta_R3` incluye el recorte y factor .5 originales. La amplitud elegida es 0/.25/.5 y la corrección final nunca supera ±.25 t/ha.

R3 se ajusta sobre residuos cross-fitted propios de cada base, nunca sobre residuos externos ni sobre los de otro modelo. Sus tres indicadores son: promedio histórico 2022–2024 de mínimos NDVI mensuales de mayo–octubre; persistencia de excesos de la brecha relativa NDVI medio–mínimo de 2025 frente a su propia historia; y pendiente mínima. La persistencia resume la extensión temporal de los excesos, sin exigir meses consecutivos.

Primero se eligen los vecinos usando GEO (centroides), PHYSICAL (suelo, geología y relieve) o SATELLITE (NDVI mínimo histórico, FAPAR mínimo histórico y persistencia). Después se compara R3 de la parcela con las medianas/MAD de R3 de sus vecinos. Es una distancia robusta con escalas marginales y piso de dispersión, no una estimación completa de densidad ni una probabilidad calibrada.

SUPPORT usa `exp(−media(z²)/2)`: atenúa la corrección cuando la parcela se aleja de la distribución local. NOVELTY usa su complemento: aplica más corrección cuanto más atípica es. Ambos conservan el signo aprendido por R3. La distancia por sí sola no determina sobreestimación/subestimación. Si faltan valores R3 o hay menos de cuatro referencias completas, ambos pesos valen cero y queda la base.

Se probaron k=8/16/24/48/72, elegidos junto con amplitud mediante OOF internas completas. Se incluyen empates en la frontera; el número efectivo puede superar k. Los 24 vecinos geográficos que ajustan el Ridge de la base son un mecanismo diferente: se mantuvieron fijos.

## Comparación principal

Cada celda es RMSE t/ha / R². Aleatoria promedia diez métricas de OOF completas, no errores por fold. Los conteos incluyen entradas necesarias para base, corrector y vecindario; no equivalen a parámetros efectivos.

| Modelo | Entradas | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---|---|---|---|
| C-T3 | 4 | .5116 / .6361 | .5206 / .6232 | .5813 / .5302 | .6788 / .3594 |
| C-T3 + R3 global | 7 | .4968 / .6568 | .5050 / .6454 | .5726 / .5442 | .6766 / .3635 |
| C-T3 + R3 soporte geográfico | 9 | .5027 / .6486 | .5108 / .6372 | .5682 / .5511 | .6622 / .3903 |
| C-T3 + R3 soporte satelital | 8 | .5016 / .6502 | .5096 / .6390 | .5706 / .5472 | .6581 / .3979 |
| J7 original | 28 | .4864 / .6709 | .4890 / .6675 | .5808 / .5309 | .6808 / .3556 |
| J7 + R3 global | 31 | .4756 / .6854 | .4748 / .6865 | .5726 / .5442 | .6550 / .4035 |
| J7 gate reducido, sin R3 | 23 | .4865 / .6708 | .4913 / .6644 | .5835 / .5266 | .6894 / .3393 |
| J7 gate reducido + R3 global | 26 | .4753 / .6858 | .4772 / .6834 | .5751 / .5402 | .6447 / .4221 |
| J7 gate reducido + R3 soporte satelital | 27 | .4792 / .6807 | .4808 / .6786 | .5771 / .5370 | .6412 / .4283 |
| J7 completo + R3 soporte satelital | 32 | .4792 / .6806 | .4789 / .6812 | .5744 / .5412 | .6440 / .4234 |
| Mezcla fija C-T3/EXPERT7 + R3 global | 16 | .4756 / .6854 | .4664 / .6975 | .5909 / .5146 | .7192 / .2808 |
| EXPERT7 sin gate + R3 global | 16 | .4808 / .6784 | .4774 / .6831 | .6526 / .4079 | .7882 / .1363 |
| RAW7 sin gate ni corrector interno + R3 | 12 | .4832 / .6752 | .4802 / .6794 | .7434 / .2316 | .9312 / −.2056 |

## Qué simplificación sí parece útil

El gate reducido conserva diez proporciones geológicas y retira textura/fase y las tres distancias a estructuras/fallas/fracturas. Con R3 global queda en 26 campos frente a 31 de J7+R3. El RMSE aleatorio es prácticamente igual; perfil y municipal pierden alrededor de .0024–.0025 t/ha; espacial mejora .0103. Retirar cinco entradas no elimina la arquitectura local ni las fuentes Sentinel/Planet/geología. Es simplificación de información del gate, no conversión a un modelo lineal único.

La ganancia espacial frente a J7+R3 está concentrada territorialmente: al omitir el bloque3 del cálculo, se convierte en deterioro de .0055 t/ha. Almoloya sigue empeorando frente a J7 original: RMSE .3621→.5862. Por tanto, 26 entradas es una candidata de parsimonia, no una mejora territorial uniforme demostrada.

C-T3+R3 soporte satelital es la alternativa de reducción fuerte: ocho entradas, dos regresiones globales y un cálculo de vecindario; no ajusta una Ridge por parcela. Frente a J7+R3 pierde .0259 t/ha aleatoria y .0347 por perfil, mejora municipal .0019 y pierde sólo .0031 espacial. Esa proximidad territorial no demuestra equivalencia estadística, pero hace explícito el compromiso costo/precisión. La versión geográfica de nueve entradas alcanza el menor RMSE municipal de esta batería, .5682, con peor aleatoria y perfil que el corrector global.

Las ocho entradas de la versión compacta satelital son las cuatro C-T3 (lluvia total, fracción temprana, concentración HHI y NDVI mayo), los tres indicadores R3 y FAPAR mínimo histórico usado únicamente para la geometría. C-T3+R3 geográfico usa esas siete entradas de base/corrector y latitud/longitud. Con vecinos físicos, C-T3+R3 requiere 25 campos: no es una simplificación comparable de ocho entradas.

## Qué simplificación no conserva la transferencia

Eliminar todo el gate deja EXPERT7 con RMSE espacial .7882 tras R3. Eliminar también su corrector climático interno deja RAW7 en .9312. R3 no recupera esa pérdida. La mezcla fija 50/50 logra el mejor resultado por perfil de esta batería (.4664), pero cae en municipal y espacial; fijar pesos no sustituye satisfactoriamente la adaptación aprendida. No se recomienda elegirla por ese único protocolo.

## ¿Sirve condicionar por cercanía o por atipicidad?

SUPPORT supera a NOVELTY espacialmente en las 18 comparaciones emparejadas de base/geometría. Sin embargo, ninguna de las 36 ponderaciones locales mejora simultáneamente todos los protocolos frente a R3 global: en las seis bases, R3 global conserva el menor RMSE aleatorio y por perfil. El beneficio de atenuar está principalmente en transferencia espacial. Ser atípica no implica que una parcela necesite una corrección mayor del signo que aprendió R3.

C-T3 soporte satelital mejora espacial .6766→.6581 frente a su propio R3 global; la mejora persiste al omitir cualquiera de los cinco bloques, entre .0123 y .0241 t/ha. Entre las 109 parcelas con R3 completo baja .7241→.7041 y entre las 29 incompletas .4557→.4444. Por tanto, allí la ganancia no procede exclusivamente de apagar imputaciones.

J7 completo soporte satelital mejora espacial .6550→.6440, también con ganancia al omitir cualquiera de los bloques. Gran parte se explica por atenuar el daño en Almoloya: .5859→.4113; sigue siendo peor que J7 sin R3 (.3621). La mejora espacial restante al omitir ese bloque es pequeña: .0014 t/ha.

El menor RMSE espacial de la tabla, .6412 de gate reducido + soporte satelital, requiere especial cautela: frente a su R3 global, al omitir Almoloya/bloque5 la mejora se convierte en deterioro de .0046. Entre parcelas con R3 completo apenas cambia .6877→.6875; entre las incompletas baja .4477→.4243 al retirar la corrección. No puede atribuirse esa ganancia a un descubrimiento general sobre proximidad. No se ejecutó un control independiente que sólo apague R3 en historias incompletas; sería un control necesario antes de atribuir causalmente el beneficio al peso continuo.

En aleatoria el peso satelital de J7 apenas separa las correcciones globales que ayudan de las que perjudican (.475 frente a .469 de peso medio); en espacial la diferencia descriptiva es mayor (.532 frente a .318). Estas son asociaciones OOF, no probabilidades de corrección correcta ni un clasificador validado independientemente.

## Vecinos y activación

No hay k universal. C-T3 soporte satelital selecciona k8 en 24 de 50 folds aleatorios, k72 en 11 y k48 en nueve; por perfil k8 en cuatro de cinco; espacial reparte entre k8,24,48. C-T3 soporte geográfico selecciona k72 en 38 de 50 aleatorios. Gate reducido soporte satelital selecciona k8 en 19 de 50 aleatorios y k72 en 13; espacial usa k16,24,48,72. Los conteos excluyen amplitudes cero. Elegir k externamente para el mejor bloque invalidaría la comparación.

El 21.0% de parcelas tiene historia insuficiente para R3 completo; la ponderación queda en cero. Los pesos medios alrededor de .43–.47 incluyen esos ceros, no sólo consultas soportadas. La geometría y sus escalas se ajustan sólo con referencias de entrenamiento; nunca incluyen etiquetas ni la identidad de la parcela evaluada.

## Recomendación

Conservar tres rutas para revisión, sin sustituir el Champion: (1) J7+R3 como referencia; (2) gate reducido+R3 global como candidata de 26 entradas; (3) C-T3+R3 soporte satelital como candidata compacta de ocho. La versión compacta geográfica es una sensibilidad útil si el objetivo es transferencia municipal. No seguir reduciendo el experto hasta quitar la mezcla con C-T3: esta batería muestra una pérdida territorial grande.

Antes de preferir un peso continuo sobre la versión global, contrastar un control de disponibilidad histórica y confirmar fuera de los bloques que concentran la ganancia. La siguiente confirmación debe congelar estas pocas candidatas, no volver a seleccionar entre 48 con el mismo resultado externo. Una nueva partición de las mismas 138 etiquetas sigue teniendo límites de selección histórica; otro ciclo o territorio aportaría evidencia más independiente.

Se realizaron 332 contrastes pareados y ninguno alcanza .05 tras Holm. Los intervalos se basan en OOF fijas, con 43 perfiles TRAIN, nueve municipios y cinco bloques; no incorporan toda la búsqueda histórica o reajuste. No significancia no equivale a equivalencia entre arquitecturas.

## Reproducibilidad

Scripts 489–492; módulo `src/base_distribution_correction.py`; diseño previo `base_distribution_correction_design.md`; salida `outputs/modeling/base_distribution_correction/v1`. Se guardaron 86,112 filas OOF y se reprodujeron 390 bases y 2,730 correcciones externas. C-T3/J7 y sus R3 globales permanecen exactamente iguales; la reconstrucción de SHARES coincide con el archivo previo en todos los protocolos.

La comprobación inicial detectó que se regeneraban particiones internas externas con otra semilla. La enmienda `amendment_01.json` obligó a reutilizar las originales; el diseño, grillas y recetas permanecieron congelados. Los artefactos previos al arreglo se conservaron en `pre_amendment`. No se usaron métricas externas para ajustar esa corrección de implementación. Pasaron tres pruebas de soporte/atipicidad/exclusión de identidad y respeto de la CV original. No se modificó Champion ni se ajustó el modelo final138 ni se generaron nuevas PRED59.
