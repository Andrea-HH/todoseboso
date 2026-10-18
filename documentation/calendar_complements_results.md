> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Complementos de modelado: unión climática y correcciones residuales

**Conclusión: conservar C-T3.** La unión de representaciones mejora el error espacial agregado, pero perjudica la transferencia municipal. Las nuevas correcciones vegetales no ofrecen una ganancia consistente sobre la base seleccionada internamente. Pendiente produce cambios de pocas milésimas; historia ofrece una mejora espacial pequeña con costo municipal. No se recomienda integrar estas correcciones ni promover una nueva base.

## Diseño ejecutado

Se completaron 11 configuraciones predictivas sobre las 65 particiones externas originales: cinco representaciones Elastic Net, su selector interno y cinco correctores separados. Se guardaron 19,734 predicciones OOF nuevas. El selector es un procedimiento que puede elegir una representación distinta en cada entrenamiento; no es un único conjunto fijo de coeficientes.

Los controles COMPACT4 y CAL02 reproducen exactamente EN_CAL00 y EN_CAL02, respectivamente. Se incluyen como controles de implementación, no como nuevas confirmaciones independientes. COMPACT4 usa las entradas de C-T3 pero el procedimiento común de selección de esta batería; C-T3 conserva su ajuste y protocolo originales. F7-00 se recupera como referencia sin reentrenarlo.

Se seleccionaron hiperparámetros, representación y amplitud correctora exclusivamente dentro del entrenamiento. Cada target residual procede de una base que excluye la observación tanto del ajuste como de la selección de hiperparámetros y representación. El procedimiento conserva el posible desajuste entre bases cross-fitted pequeñas y bases reajustadas con todo el entrenamiento externo. No se usaron estados, municipios ni coordenadas como predictores o reglas de selección.

[Diseño y límites](calendar_complements_design.md). Configuración congelada: `outputs/modeling/agronomic_calendar/complements/v1/frozen_design.json`.

## Comparación de representaciones

RMSE en t/ha. Cada métrica se calcula sobre OOF completas por repetición; aleatoria promedia sus diez repeticiones, nunca RMSE por fold.

| Modelo | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| C-T3 original | 0.511582 | 0.520604 | 0.581259 | 0.678778 |
| COMPACT4: control de procedimiento | 0.511730 | 0.519022 | 0.575767 | 0.677852 |
| CAL02: lluvia/Tmax por ventanas + NDVI mayo | 0.497490 | 0.503178 | 0.839296 | 0.625262 |
| WINDOW_SHAPES7: lluvias + fracción temprana/HHI + NDVI | 0.504293 | 0.524230 | 0.582569 | 0.728317 |
| UNION11: CAL02 + fracción temprana/HHI | 0.500333 | 0.520124 | 0.741679 | 0.615599 |
| COMPACT_TMAX8: compact4 + cuatro Tmax | 0.514449 | 0.535838 | 0.775965 | 0.764631 |
| SELECTED_BASE: selección completamente interna | 0.505912 | 0.517178 | 0.598578 | 0.618396 |
| F7-00 CatBoost compacto, archivado | 0.504874 | 0.515345 | 0.528223 | 0.642591 |

La unión elimina el total de lluvia, que es una combinación lineal exacta de las cuatro ventanas. Conserva fracción temprana, una transformación de esas ventanas, y HHI mensual, que no se reconstruye en general a partir de los bimestres. La ablación cambia también la geometría de la penalización de predictores correlacionados; sus resultados no identifican efectos agronómicos causales.

Agregar Tmax directamente a compact4 empeora los cuatro protocolos. Agregar fracción temprana/HHI a CAL02 reduce parte del deterioro municipal de CAL02 (0.839 a 0.742), pero no recupera C-T3 (0.581). Por tanto, la complementariedad descriptiva no se traduce en una base única con transferencia equilibrada.

SELECTED_BASE es menos perjudicial municipalmente que CAL02 o UNION11, pero conserva un costo de +0.017319 respecto a C-T3 y una mejora espacial de -0.060382. Esa mejora espacial sigue siendo territorialmente concentrada.

### Variables que sobreviven

En UNION11, los 50 ajustes aleatorios conservan NDVI mayo, HHI, Tmax abril y lluvia julio-agosto en el 100% de los folds. Fracción temprana aparece en 96%, lluvia abril y mayo-junio en 98%, Tmax mayo-junio en 86%, Tmax septiembre-octubre en 94% y lluvia septiembre-octubre en 70%. Tmax julio-agosto aparece solo en 28% y tiene coeficiente mediano cero.

Estas frecuencias no demuestran utilidad incremental independiente. Con predictores correlacionados, Elastic Net reparte o intercambia coeficientes. No se entrenó un modelo reducido nuevo escogiendo estas frecuencias externas.

UNION11 conserva una mediana de 10 coeficientes no nulos de sus 11 entradas en aleatoria (rango 7-11), siete por perfil, ocho municipalmente y nueve espacialmente. Por tanto, la penalización no lo convierte automáticamente en un modelo tan sencillo como C-T3.

El selector aleatorio elige CAL02 en 21/50 folds, UNION11 en 16, WINDOW_SHAPES7 en 11 y cada una de las otras dos representaciones en uno. Municipalmente elige WINDOW_SHAPES7 en 4/5 y CAL02 en 1/5. Espacialmente elige CAL02 en 3/5, UNION11 en 1/5 y COMPACT4 en 1/5. No se debe convertir esta observación en reglas regionales retrospectivas.

## Correcciones sobre SELECTED_BASE

Todas se suman a la misma base elegida internamente y pueden seleccionar amplitud cero. Su comparación incremental apropiada es contra SELECTED_BASE; superar C-T3 espacialmente no demuestra que el corrector haya ayudado, pues parte de esa mejora ya estaba en la base.

| Corrector | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| Sin corrección: SELECTED_BASE | 0.505912 | 0.517178 | 0.598578 | 0.618396 |
| Ridge vegetal, 17 variables | 0.506218 | 0.517178 | 0.773828 | 0.632799 |
| CART vegetal + contexto, 20 entradas | 0.509319 | 0.518735 | 0.592172 | 0.626486 |
| CART contexto, sin ventanas vegetales | 0.507239 | 0.518635 | 0.607873 | 0.619844 |
| Ridge pendiente media | 0.506007 | 0.516830 | 0.597877 | 0.616044 |
| Ridge historia NDVI2 | 0.505177 | 0.516846 | 0.621037 | 0.612640 |

Ridge vegetal se desactiva en 48/50 folds aleatorios y 5/5 por perfil. Cuando se activa municipalmente llega a empeorar mucho: no hay respaldo para integrarlo. El árbol vegetal mejora municipalmente frente a la base en 0.006406, pero empeora aleatoria, perfil y espacial. La comparación contra el árbol sin vegetación también tiene costos fuera de municipal; no demuestra una ventaja general de los satélites.

La inspección de las particiones efectivas refuerza esa limitación: en los correctores activos municipales y espaciales de VEG_CONTEXT_CART, **ninguna división utiliza una ventana vegetal nueva**. Solo aparecen fracción temprana, HHI o el NDVI de mayo ya presente en la base. Las diferencias frente al control contextual pueden proceder de la selección interna de parámetros y amplitud dentro de espacios de candidatos distintos, sin que el árbol externo final use los nuevos predictores. La mejora municipal de Chignahuapan no se atribuye a información satelital adicional. Las divisiones observadas tampoco tienen interpretación causal.

Pendiente cambia RMSE municipal en -0.000702 y espacial en -0.002351, con cambios casi nulos en los otros protocolos. Historia mejora espacial en -0.005755, pero empeora municipal en +0.022459. No se sumaron correctores ni se supuso que sus beneficios fueran aditivos.

## R2, MAE y concentración territorial

| Procedimiento | R2 aleatoria | R2 perfil | R2 municipal | R2 espacial |
|---|---:|---:|---:|---:|
| C-T3 | .636069 | .623166 | .530242 | .359394 |
| UNION11 | .651861 | .623861 | .235166 | .473096 |
| SELECTED_BASE | .644028 | .628109 | .501830 | .468298 |
| SELECTED_BASE + árbol vegetal | .639195 | .625866 | .512436 | .454295 |
| SELECTED_BASE + pendiente | .643897 | .628609 | .502998 | .472334 |

MAE de SELECTED_BASE: .369273 aleatoria, .390312 perfil, .440855 municipal y .457536 espacial. Aunque su RMSE municipal es peor que C-T3, su MAE municipal es menor (.441 frente a .460); existen diferencias en la cola de errores y en el sesgo. Ninguna de esas métricas por sí sola decide integración.

### Bloques espaciales

| Bloque | C-T3 RMSE | SELECTED_BASE RMSE | UNION11 RMSE |
|---|---:|---:|---:|
| 1 | .505445 | .518451 | .509962 |
| 2 | .572523 | .567906 | .567906 |
| 3 | .909593 | .469798 | .456301 |
| 4 | .798996 | 1.104089 | 1.130398 |
| 5 | .360198 | .309633 | .139139 |

Al excluir el bloque 3 solo del cálculo, sin reajustar, C-T3 tiene RMSE .579793, SELECTED_BASE .661333 y UNION11 .661048. La mejora espacial agregada depende del bloque 3. El bloque 4, principalmente Singuilucan, empeora. El sesgo espacial global de SELECTED_BASE baja de +.191161 a +.044346, pero sigue sobreestimando el bloque 4 en +.926466: menor sesgo agregado puede ocultar cancelaciones regionales.

Municipalmente UNION11 empeora Chignahuapan de .580680 a .785743 y Singuilucan de .867689 a 1.152065. SELECTED_BASE obtiene .579081 en Chignahuapan y .902557 en Singuilucan. El árbol vegetal reduce Chignahuapan a .567161, pero deja Singuilucan en .902557. Es una mejora local, no evidencia de superioridad territorial general.

## Diferencias intraperfil

No se resolvió la heterogeneidad parcelaria. En aleatoria, RMSE de diferencias con igual peso por perfil pasa de .589951 en C-T3 a .590471 en SELECTED_BASE y .596462 con el árbol vegetal. Ponderando pares pasa de .771183 a .772868 y .781296, respectivamente.

Espacialmente, C-T3 tiene .540147 por perfil y .767538 por pares; SELECTED_BASE y su árbol vegetal tienen .543758 y .775350. Las correcciones climáticas y de nivel regional no crean resolución entre parcelas de clima idéntico. El árbol vegetal municipal mejora nivel de algunos grupos pero no cambia las diferencias intraperfil evaluadas frente a SELECTED_BASE. Las parejas no se tratan como observaciones independientes.

## Recomendación

Conservar C-T3 como referencia sencilla y F7-00 como alternativa directa ya conocida. No adoptar UNION11, SELECTED_BASE ni sus correctores como sustitutos automáticos. La hipótesis de que unir representaciones y regularizar bastaría para estabilizar territorio queda debilitada. También queda debilitada la utilidad de las nuevas ventanas vegetales como corrección pequeña bajo estas formulaciones; no se rechaza toda información satelital ni todo modelo residual.

Detener esta expansión de ventanas y correctores antes de ampliar profundidad o incorporar más índices sobre las mismas etiquetas. El límite sigue siendo distinguir parcelas dentro del clima con mediciones y tiempos agronómicos verificables, y confirmar transferencia con nuevas campañas/territorios. No se ejecutó una mezcla nueva CatBoost/C-T3 ni se derivaron reglas por municipio de estos resultados.

## Reproducibilidad y límites numéricos

Se verificaron exactamente los 715 predictores externos guardados, contando SELECTED_BASE como predictor compuesto, con diferencia máxima cero. Los 65 controles de cada representación previa también coinciden exactamente con sus archivos originales. Cuatro pruebas pasaron, incluida perturbación de etiquetas excluidas. No se modificó modelo TOP20/TOP15, C-T3, archivos anteriores, los 138 rendimientos ni se generaron 59 PRED o un ajuste final de 138 parcelas.

Se registraron 22 eventos ConvergenceWarning en logs de folds completos; no se ampliaron límites retrospectivamente. El conteo de candidatos descartados no es exhaustivo para contextos interrumpidos antes de guardar su fold; se entrega una auditoría completa adicional de los modelos seleccionados en todos los contextos. La reanudación conservó los checkpoints, verificó cachés y añadió solo memoización del preprocesamiento de X; la prueba de equivalencia sobre las 16 configuraciones tuvo diferencia cero. Los modelos externos finales se exportaron a la clase original sin memoización de predicción. Se registró además la advertencia de Intel/LLVM OpenMP al descubrir pools; la ejecución en Windows terminó y se verificó su reproducción.

La auditoría cubre 1,301 contextos y sus 6,505 reajustes de representaciones seleccionados por hiperparámetros: ninguno presentó advertencias ni alcanzó las 100,000 iteraciones. Tampoco hubo advertencias en los 325 ajustes externos de las cinco representaciones. Las advertencias registradas corresponden a ajustes de candidatos internos. No se detectaron archivos de contexto corruptos que requirieran cuarentena.

El último segmento de entrenamiento duró 415.47 s; no representa el tiempo total de la ejecución, que incluye el segmento anterior, auditorías y síntesis. No se presentan tiempos comparables por algoritmo. La reutilización extensa de estas etiquetas limita cualquier afirmación estadística; los resultados son exploratorios y no se ofrecen intervalos predictivos calibrados.

Artefactos bajo `outputs/modeling/agronomic_calendar/complements/v1/`:

- `tables/oof_predictions.csv` y parquet: OOF nuevas y referencias preservadas.
- `diagnostics/metrics_summary.csv`: RMSE, MAE, sesgo y R2.
- `diagnostics/paired_summary.csv`: diferencias frente a C-T3 y SELECTED_BASE.
- `diagnostics/regional_summary.csv`, `omissions_summary.csv`, `parcel_gains_repeat_average.csv`, `largest_changes.csv`: soporte territorial e influencia.
- `diagnostics/intraprofile_summary.csv`, `feature_selection_stability.csv`, `base_selection_frequency.csv`, `correction_selection.csv`: diferenciación y selección.
- `diagnostics/rmse_vs_ct3.png`: comparación visual.
- `models/`: paquetes externos completos; `audit/`: reproducción, advertencias, equivalencia operacional y convergencia.

Scripts de entrenamiento, reanudación, síntesis y auditoría: 407, 409, 408 y 410. Si se reproduce en la misma carpeta, los artefactos completos se preservan; una nueva ejecución requiere una versión nueva.
