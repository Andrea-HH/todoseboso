# Familia 4 — Sensibilidades condicionales y señales complementarias

NDVI de mayo aporta una mejora local modesta; su percentil temporal bajo produce resultados parecidos y es muy redundante. La variabilidad de amplitud térmica añadida directamente a lluvia aporta una mejora espacial distinta. Las interacciones no ofrecen una ventaja general y ninguna prueba cumple todos los márgenes operativos previos. Estos resultados son exploratorios: las candidatas se eligieron retrospectivamente entre 1,473 variables usando las mismas 138 etiquetas.

## Diseño y alcance

No existía una implementación previa de Familia 4 en los archivos de este repositorio. Se creó una versión separada bajo `outputs/modeling/family_4/conditional_yield_response/v1`, conservando J, K, L, M y Champion. Se congelaron once pruebas antes de entrenar:

| Prueba | Arquitectura |
|---|---|
| F4-S1 | Lluvia mensual + NDVI mayo, aditiva |
| F4-S2 | Lluvia + corrección residual NDVI mayo |
| F4-S3 | Lluvia + corrección residual NDVI q10 |
| F4-S4 | Lluvia + corrección residual duración ascenso SAVI |
| F4-S5 | Lluvia mensual + desviación temporal de Tmax−Tmin, aditiva |
| F4-S6 | Lluvia + corrección residual de esa amplitud térmica |
| F4-A | Corrector residual con pendiente, lluvia acumulada y su producto |
| F4-B | Corrector residual con NDVI mayo, lluvia acumulada y su producto |
| F4-C | Corrector residual con NDVI mayo, rendimiento climático esperado y su producto |
| F4-D | Sensibilidad residual pendiente × cobertura de unidades que mencionan Vertisol |
| F4-G1 | Corrector residual con una curva suave de pendiente: tres nudos, grado dos |

Se conservaron cuatro hipótesis: H1 diferenciación intraperfil; H2 sensibilidad de la corrección a condiciones observables; H3 transferencia regional de amplitud térmica; H4 complementariedad respecto a residuos de lluvia y comparación con K5. La evaluación después de K5 queda limitada a comparación de predicciones: no se entrenó una tercera etapa válida.

**F4-S7 está suspendido.** No se reconstruyó en esta versión el cross-fitting anidado de toda la arquitectura K5 requerido para entrenar y seleccionar una tercera etapa. Las cachés verificadas contienen modelos climáticos cruzados, pero no contextos completos K5 retunados dentro de todos los entrenamientos de esa tercera etapa. Por tanto no se reutilizaron residuos OOF globales de K5 para entrenar NDVI. Es una limitación explícita de implementación, no evidencia de ausencia de señal después de pendiente. Tampoco se probó pendiente × rendimiento esperado, que no forma parte de las arquitecturas congeladas.

Se reutilizaron exactamente los 65 folds externos y las particiones internas existentes: 50 aleatorios —cinco folds, diez repeticiones— y cinco por perfil, municipio y espacio. Se guardaron 715 modelos externos y 19,734 predicciones fuera de muestra. Ningún rendimiento PRED se utilizó: hay 138 TRAIN y 59 PRED.

Todos los predictores se imputan y escalan dentro del entrenamiento; las constantes se excluyen. Las interacciones contienen ambos efectos principales, con penalización Elastic Net conjunta; esto es jerarquía en el diseño, no una restricción que obligue a conservar coeficientes principales distintos de cero. Los correctores usan los mismos cuatro valores de alpha y tres l1_ratio de K/L/M, con eta ∈ {0, .25, .5, 1}; se seleccionan por RMSE interno de la arquitectura completa. La curva suave tiene complejidad fija y se ajusta únicamente en entrenamiento. No se ensayaron interacciones de orden superior ni nuevas combinaciones de las cuatro candidatas.

Para los correctores, los residuos de entrenamiento proceden de predicciones climáticas cruzadas; cada uno de esos modelos selecciona sus parámetros dentro de su propio entrenamiento. F4-C utiliza esos mismos valores cruzados como característica en entrenamiento y predicciones del modelo climático entrenado sobre el conjunto pertinente en validación. Nunca usa Y observado para activar una corrección. Se reutilizan cachés inmutables de L/K, cuya procedencia se auditó con 1,278 registros; los grupos y etiquetas de validación están excluidos de los entrenamientos y ajustes internos.

F4-D usa la cobertura cartográfica que menciona VR, no una medición física del porcentaje de Vertisol. El producto se desactiva dentro de cada ajuste si no hay diez parcelas a cada lado de presencia/ausencia y tres perfiles a cada lado. Los 65 ajustes externos tuvieron soporte; la regla también se aplica dentro de entrenamiento interno. No se utiliza estado, municipio, coordenadas ni cuartil observado como predictor.

## Resultados globales

RMSE t/ha; métricas de todas las predicciones de cada repetición, posteriormente promediadas. No se promedian primero predicciones ni RMSE de folds.

| Modelo | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| J0 lluvia | 0.52136 | 0.54435 | 0.69536 | 0.73479 |
| K5 lluvia + pendiente residual | 0.51624 | 0.53756 | 0.69606 | 0.71393 |
| Climate Current original | 0.52002 | 0.54028 | 0.77735 | 0.97985 |
| S1 NDVI mayo aditivo | **0.50483** | **0.52626** | **0.67110** | 0.73904 |
| S2 NDVI mayo residual | 0.50864 | 0.53448 | 0.72329 | 0.67339 |
| S3 NDVI q10 residual | 0.51065 | 0.53645 | 0.71767 | 0.66514 |
| S4 ascenso SAVI residual | 0.52081 | 0.55737 | 0.69907 | 0.73853 |
| S5 amplitud térmica aditiva | 0.52412 | 0.56029 | 0.68540 | **0.60047** |
| S6 amplitud térmica residual | 0.52123 | 0.56068 | 0.69907 | 0.81975 |
| A pendiente × lluvia | 0.51809 | 0.54981 | 0.73006 | 0.71057 |
| B NDVI × lluvia | 0.51524 | 0.54525 | 0.82606 | 0.67803 |
| C NDVI × rendimiento esperado | 0.50591 | 0.53888 | 0.71815 | 0.71927 |
| D pendiente × VR | 0.51973 | 0.54995 | 0.73082 | 0.71356 |
| G1 curva suave pendiente | 0.51711 | 0.54277 | 0.70207 | 0.70813 |

S1, S2, S3 y C mejoran RMSE aleatorio en las diez repeticiones, que reutilizan las mismas parcelas y no son diez muestras independientes. S1 mejora también MAE aleatorio 0.36946→0.36411, por perfil 0.39035→0.38889 y municipal 0.50022→0.49856, pero empeora espacial 0.56199→0.57291. S5 reduce MAE espacial a 0.44654, pero empeora por perfil a 0.40777 y municipal a 0.51500.

Ninguna prueba cumple simultáneamente mejora aleatoria, deterioro RMSE agrupado ≤0.01 y deterioro MAE en todos los protocolos ≤0.01. S1 es la más cercana: excede el margen MAE espacial por aproximadamente 0.00091 t/ha. No se cambian los criterios después de observar resultados. Las comparaciones pareadas contra J0 y K5, incluidas las diez repeticiones, están en las tablas adjuntas.

El Champion archivado `A_CURRENT_CH_H_T` tiene RMSE aleatorio compatible 0.49813 y MAE 0.35887. Se verificaron las mismas 1,380 combinaciones ID/repetición/fold. No hay benchmark Champion compatible municipal o espacial y no se inventa uno.

## Diferenciación dentro de perfiles

Las parejas siempre pertenecen al mismo perfil y al mismo modelo externo. La predicción de J0 es idéntica para sus dos parcelas; el RMSE de diferencias incluye la variación intraperfil que lluvia no puede describir.

| Modelo | RMSE parejas aleatorio | RMSE con igual peso por perfil | Igual peso sin Chignahuapan |
|---|---:|---:|---:|
| J0 | 0.80449 | 0.61041 | 0.51558 |
| K5 | 0.79373 | 0.60655 | 0.51463 |
| S1 | **0.77325** | **0.58920** | 0.50572 |
| S2 | 0.77940 | 0.59384 | 0.50774 |
| S3 | 0.78733 | 0.58936 | **0.49424** |
| S4 | 0.79901 | 0.60198 | 0.50564 |

En aleatoria hay 198–222 parejas elegibles por repetición, 7–11 perfiles y 84–94 parcelas; sus medias son 208.4 parejas, 8.6 perfiles y 87.7 parcelas. Sin Chignahuapan quedan en promedio 21.3 parejas, 6.4 perfiles y 24.2 parcelas. El protocolo por perfil conserva 1,073 parejas de 12 perfiles y 107 parcelas; municipal 1,034 de 12 y 103; espacial 1,007 de 12 y 106. Las parejas comparten parcelas y no son observaciones independientes.

La mejora local es modesta y no uniforme: S2 mejora el RMSE de diferencias con igual peso por perfil en aleatoria y por perfil, pero empeora municipal y espacial. S1 empeora ese criterio por perfil pese a mejorar su RMSE global. S3 supera S1 fuera de Chignahuapan en el diagnóstico local aleatorio, sin una ventaja global universal. Las tablas conservan dispersión de predicciones/correcciones y errores por perfil, de modo que el promedio no sustituye la evaluación de cada perfil.

NDVI mayo y q10 tienen correlación 0.937 global y 0.946 intraperfil: son muy redundantes. SAVI ascenso tiene correlación intraperfil 0.176 con NDVI mayo y 0.140 con q10; describe otra trayectoria, pero esa diferencia no se convierte en una mejora global apreciable. No se entrenó una combinación adicional de estos predictores para buscar sin límite una ganancia.

## Extremos y condiciones observables

Q1 [2,3.20], Q2 (3.20,4.34], Q3 (4.34,4.55] y Q4 (4.55,5.59] t/ha conservan los cortes previos y 36/33/35/34 parcelas. Son diagnósticos posteriores.

| Modelo | RMSE Q1 aleatorio | Sesgo Q1 | RMSE Q4 aleatorio | Sesgo Q4 |
|---|---:|---:|---:|---:|
| J0 | 0.72643 | +0.43280 | 0.51999 | −0.42485 |
| K5 | 0.71527 | +0.40999 | 0.51020 | −0.41461 |
| S1 | 0.69788 | +0.41752 | 0.48877 | −0.40437 |
| S2 | 0.70045 | +0.35193 | 0.45609 | −0.36101 |
| S3 | 0.71109 | +0.36302 | 0.46349 | −0.36535 |
| S5 | 0.72690 | +0.43173 | 0.52307 | −0.42649 |

S2 reduce también MAE Q1 0.49179→0.46797 y Q4 0.42760→0.36949. Su mejora en Q4 aparece en todos los protocolos: por perfil 0.5283→0.4457, municipal 0.4716→0.3188, espacial 0.4965→0.3627. En cambio Q1 empeora por perfil y municipal, aunque mejora espacial. NDVI residual ayuda especialmente al extremo alto; no corrige uniformemente el extremo bajo.

S5 mejora principalmente Q1 espacial 1.2164→0.8863, y también Q4 espacial 0.4965→0.4872. Empeora ambos extremos por perfil. Esto distingue su fortaleza regional de la fortaleza local satelital.

Para estudiar activaciones observables se usan bandas de lluvia acumulada y rendimiento esperado con cortes terciles calculados exclusivamente sobre el entrenamiento pertinente; el rendimiento esperado de ese entrenamiento es cruzado. Los errores se agregan mediante sumas de errores cuadrados y tamaños de muestra antes de calcular métricas de repetición. S2 mejora sobre todo la banda de rendimiento esperado medio en aleatoria —0.5522→0.5198— y las bandas baja/media espacialmente —0.9212→0.7660 y 0.9463→0.8754—; la banda alta espacial empeora 0.5406→0.5583. No existe un umbral único que corresponda de manera transportable a Q1 o Q4 observado. No se optimizaron umbrales después de ver esos diagnósticos ni se utiliza el cuartil real para activar modelos.

Las interacciones tampoco proporcionan una regla estable. El coeficiente pendiente × lluvia es negativo solo en 46% de los ajustes aleatorios y positivo en 4%; en los restantes queda en cero. NDVI × lluvia es negativo en 56% y positivo en 12%, pero el modelo B deteriora notablemente la validación municipal. NDVI × rendimiento esperado cambia de signo entre ajustes/protocolos. Las curvas de sensibilidad guardadas muestran cambios predictivos al recorrer el intervalo intercuartílico del predictor a tres niveles de la condición aprendidos en entrenamiento; son relaciones del modelo, no efectos causales.

No hay predicciones negativas en estas pruebas. En S2, la corrección absoluta máxima es 0.693 t/ha en aleatoria, 1.282 municipal y 0.941 espacial. La mejora de sesgo no se interpreta aislada de los errores individuales. Los datos no justifican una activación operacional automática.

## Amplitud térmica, región y soporte

La desviación temporal de Tmax−Tmin está fuertemente relacionada con lluvia de mayo (+0.782), octubre (−0.855), longitud (−0.953), latitud (−0.764) y altitud (−0.408). Son asociaciones de las parcelas etiquetadas; no implican que coordenadas se hayan utilizado en los modelos. Su distribución por estado/municipio y todos los meses están tabulados. La combinación aditiva S5 supera lluvia en municipios y espacio, especialmente en el extremo bajo espacial, pero no en nuevos perfiles climáticos. El corrector S6 empeora espacio a 0.820. Esto indica que la arquitectura importa y que la variable sigue representando un gradiente regional; no constituye una señal parcelaria intraperfil.

El soporte satelital se examina mediante meses válidos y número de observaciones NDVI, tanto en mayo como en abril–octubre. Los estratos de soporte bajo usan el percentil 25 del entrenamiento, sin eliminar parcelas ni optimizar filtros de nube. Conteos de observaciones no equivalen a escenas independientes y el soporte no elimina posibles diferencias de cultivo o fenología. Se conservan las tablas por fold, repetición y protocolo; no se deducen reglas a partir de estratos muy pequeños.

En aleatoria S1 mejora Chignahuapan 0.57644→0.55759 y fuera de ese municipio 0.45574→0.44203. S2 también mejora ambos ámbitos. La asociación local no desaparece al excluir Chignahuapan, aunque el número de parejas fuera de él es pequeño. Excluir sus predicciones en el diagnóstico no equivale a volver a entrenar todos los modelos sin ese municipio.

## Síntesis de las diez preguntas

1. **NDVI mayo:** sí produce una mejora fuera de muestra intraperfil pequeña, con la comparación apropiada de parejas del mismo modelo. No funciona uniformemente en todas las regiones.
2. **NDVI q10 y SAVI:** q10 es muy redundante con mayo y merece contrastarse como alternativa, no agregarse automáticamente. SAVI es distinto pero de utilidad predictiva débil.
3. **Pendiente e interacciones:** no hay evidencia estable de una interacción transportable con lluvia. Pendiente × rendimiento esperado no se evaluó; NDVI × rendimiento esperado no demuestra ese efecto de pendiente.
4. **Amplitud térmica:** la adición directa mejora transferencia espacial y, menos, municipal. No mejora por perfil; la corrección residual no reproduce esa fortaleza.
5. **Arquitectura:** NDVI aditivo ofrece el mejor balance global de estas pruebas; NDVI residual y q10 residual ayudan más al extremo alto y espacio; las interacciones no dominan sus alternativas sencillas.
6. **Cuartiles:** se identifican asociaciones con características observables, pero no una regla estable que anticipe y corrija ambos extremos. Y observado solo aparece en evaluación posterior.
7. **Chignahuapan:** concentra muchas parejas; las mejoras locales no dependen exclusivamente de él, pero la evidencia fuera de ese municipio es limitada y no es una validación independiente.
8. **Validación independiente:** priorizar NDVI mayo aditivo para diferenciación, NDVI/q10 residual para errores altos y amplitud térmica aditiva para transferencia. Deben validarse con nuevos rendimientos o regiones externas.
9. **Relaciones descriptivas:** correlaciones, curvas de coeficientes, bandas diagnósticas y distribución regional no demuestran causalidad ni confirmación independiente. La ganancia posterior a K5 sigue sin evaluarse como tercera etapa.
10. **Reducir investigación con esta muestra:** detener nuevas variantes de SAVI ascenso, ampliaciones de pendiente × suelo, interacciones más complejas y combinaciones automáticas de índices redundantes. No convertir el screening retrospectivo en una búsqueda reiterada sobre los mismos folds.

## Verificación y reproducción

Cinco pruebas automatizadas pasaron: transformación aprendida en entrenamiento, efectos principales de interacciones, soporte edafológico, invariancia a etiquetas/ubicación como entradas, auditoría de los 65 contextos climáticos y reproducción de las once arquitecturas en un fold de cada protocolo. Se verificó integridad SHA-256 de 3,491 artefactos previos de L/M mediante sus manifiestos, sin modificaciones. Los modelos históricos y el Champion se leyeron como referencias.

Entrenamiento: `python scripts/336_family4_conditional_response.py`. La versión completa está protegida contra reentrenamiento accidental. Diagnósticos adicionales: `python scripts/337_family4_diagnostics.py`. Pruebas: `python -m pytest tests/test_family4_conditional_response.py -q`. Configuración, parámetros internos, modelos, procedencia, comparaciones pareadas, errores por cuartil/región, soporte y sensibilidades están en el directorio versionado indicado arriba.

![RMSE por protocolo](../outputs/modeling/family_4/conditional_yield_response/v1/figures/protocol_rmse.png)

![Diferencias dentro de perfiles con igual peso](../outputs/modeling/family_4/conditional_yield_response/v1/figures/intraprofile.png)
