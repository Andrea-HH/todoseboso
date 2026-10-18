> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# F5-S1 — Representación, suavidad y extrapolación

Evaluación exploratoria de tres sensibilidades previamente congeladas, sobre las mismas 65 particiones y 138 rendimientos. Ninguna variante se selecciona mediante resultados espaciales; no hay promoción de Champion ni predicciones de las 59 parcelas.

## RMSE OOF (t/ha)

| Modelo | climate_profile | municipality | random | spatial |
| --- | --- | --- | --- | --- |
| C-T3 | 0.520604 | 0.581259 | 0.511582 | 0.678778 |
| F5-00-C | 0.518851 | 0.553414 | 0.515296 | 0.790466 |
| F5-01 | 0.499759 | 0.544208 | 0.504006 | 0.734797 |
| F5-S1-A | 0.504708 | 0.563410 | 0.505365 | 0.768225 |
| F5-S1-B | 0.517652 | 0.572587 | 0.507730 | 0.730979 |
| F5-S1-C | 0.501798 | 0.576121 | 0.504478 | 0.679278 |

## Método e incertidumbre

Métricas calculadas sobre las 138 OOF de cada repetición; aleatoria resume las diez repeticiones. Los resultados por fold son diagnósticos y no reemplazan esta agregación. A cambia solo Matérn 3/2 por RBF. B sustituye compact3 por siete lluvias mensuales, escaladas dentro de entrenamiento y divididas por √7. C ajusta Ridge con penalización n·α, intercepto libre y α∈{0.001,0.01,0.1,1}; selecciona por RMSE medio de cuatro folds internos del pipeline completo y reajusta tendencia y GP usando únicamente entrenamiento externo.

La media lineal C es determinista estimada, no un kernel DotProduct: este último define covarianza aleatoria, otra distribución y otra inferencia. Los residuos de C se calculan dentro del mismo entrenamiento de la tendencia; no provienen del Champion ni de validación. El GP normaliza sus residuos dentro de entrenamiento. Esto también cambia la unidad cruda de los límites de amplitud y ruido, aunque conserva exactamente los límites estandarizados originales.

Los intervalos son gaussianos observacionales de 90%, incluyen WhiteKernel y excluyen incertidumbre de hiperparámetros y cambio de dominio. C además omite incertidumbre de los coeficientes de la tendencia. Cobertura observada y amplitud se reportan por separado: mayor cobertura con intervalos más anchos no demuestra mejor calibración.

Las distancias nativas de B y compact3 tienen distinta dimensión; la comparación entre modelos utiliza además un soporte común transformado por el F5-01 archivado del mismo fold, sin reajustarlo. El acercamiento a la media se examina mediante desviaciones predichas y observadas respecto de la media de entrenamiento. Son diagnósticos descriptivos, no una demostración causal de extrapolación.

Las omisiones de bloques, municipios y parcelas recalculan métricas de OOF existentes; no eliminan observaciones de los ajustes. Pares intraperfil se restringen a predicciones del mismo ajuste externo. Sus perfiles tienen igual peso, pero pocos perfiles repetidos y pares dependientes limitan las conclusiones. No se declara superioridad estadística.


## Respuestas y recomendación

1. **Suavidad: RBF empeora frente a Matérn 3/2.** A aumenta el RMSE en los cuatro protocolos: +0.00136 aleatorio, +0.00495 perfil, +0.01920 municipal y +0.03343 espacial. El sesgo del bloque 3 aumenta de +1.016 a +1.089 t/ha. La hipótesis de que una mayor suavidad resolvería esta extrapolación queda debilitada bajo estos límites; esto no compara todos los kernels posibles.

2. **Representación temporal: las siete lluvias no recuperan una ventaja consistente.** B mejora el RMSE espacial apenas 0.00382 t/ha, mientras empeora el MAE espacial 0.01993 y los otros tres RMSE. Mejora el bloque 3 (ganancia SSE +4.409), pero deteriora especialmente el bloque 4 (−3.252). Al omitir el bloque 3 del cálculo, B empeora respecto de F5-01. Los resúmenes compactos no parecen ser la causa principal del problema en esta familia. Esto no demuestra que la distribución temporal carezca de información agronómica.

3. **Media lineal: corrige parte de la extrapolación, con un costo.** C reduce RMSE espacial 0.05552 y MAE 0.02099 frente a F5-01. En el bloque 3 reduce el sesgo de +1.016 a +0.725 t/ha: su ganancia SSE +15.149 se descompone en +17.729 por reducción del sesgo y −2.581 por mayor dispersión. Sin embargo, empeora 0.17317 el RMSE del bloque 4 y pierde 0.03191 en RMSE municipal global. Mejora únicamente dos de cinco bloques espaciales frente a F5-01. La ganancia espacial neta (+10.834 SSE) es menor que la del bloque 3 por los deterioros compensatorios.

4. **Ninguna conserva simultáneamente la ventaja municipal de F5-01 y resuelve su deterioro espacial.** C aproxima el RMSE espacial de C-T3 (0.67928 frente a 0.67878, diferencia +0.00050) y mejora su MAE espacial 0.00966, pero la ventaja municipal sobre C-T3 queda en solo 0.00514 t/ha, frente a 0.03705 de F5-01. A conserva una ventaja municipal parcial pero agrava el problema espacial. B también reduce la ventaja municipal y mantiene un deterioro espacial importante.

5. **Concentración: los resultados no son uniformes.** La ventaja espacial C versus F5-01 depende del bloque 3: omitirlo invierte la comparación. Frente a C-T3, C queda esencialmente empatado; omitir cualquiera de los bloques produce diferencias RMSE entre −0.00197 y +0.00204. La ventaja municipal C depende de Singuilucan: su +1.686 SSE supera la ganancia municipal neta +0.821; Chignahuapan y Calpulalpan aportan pérdidas. Al omitir las cinco parcelas de mayor beneficio en cada protocolo, las pequeñas ventajas RMSE de C sobre C-T3 se invierten en aleatoria (+0.00616) y municipal (+0.00643). Esta es sensibilidad descriptiva sobre las mismas OOF, no una recomendación de excluir parcelas ni una evaluación independiente.

### Intervalos e intraperfil

La mejora puntual de C no se acompaña de intervalos espaciales adecuados: cobertura observada 78.99% para intervalos nominales 90%, frente a 92.75% de F5-01; amplitud media 1.615 frente a 2.105 t/ha. En municipal C cubre 84.78% frente a 88.41%. Al omitir incertidumbre de la tendencia, C puede subestimar parte de la incertidumbre; estos resultados no permiten atribuir toda la falta de cobertura únicamente a esa omisión. Los intervalos y el sesgo residual impiden presentar C como solución espacial completa.

El RMSE de diferencias intraperfil con igual peso por perfil para C es 0.59370 aleatorio, 0.53330 por perfil, 0.52774 municipal y 0.54269 espacial. Mejora frente a F5-01 en aleatoria y municipal, empeora en perfil y espacial, y no supera a C-T3 en aleatoria, municipal ni espacial. No hay evidencia de una solución uniforme a la heterogeneidad intraperfil. El diagnóstico local dispone de 12 perfiles repetidos en protocolos agrupados; los pares son dependientes y el soporte fuera de Chignahuapan es escaso.

### Hipótesis y decisión

En el bloque 3 la media de entrenamiento es 4.270 t/ha y la observada 3.029. F5-01 predice en promedio 4.045, A 4.118 y B 4.028: se mantienen mucho más cerca de la media de entrenamiento que de la respuesta del dominio retenido. C predice 3.754, casi exactamente su tendencia (3.753861), con corrección GP media −0.000035 t/ha. Su α fue 0.01, elegido internamente; el GP alcanza amplitud mínima 0.01 y ambas longitudes máximas 20, con ruido estandarizado 1.005. La mejoría en ese bloque corresponde fundamentalmente a extrapolación lineal, no a una señal GP residual sustancial. Los límites no se ampliaron. Esta observación apoya una limitación de la media constante, pero debilita la necesidad de una corrección GP para ese dominio bajo esta formulación.

Los resultados apoyan parcialmente que una media constante limita la extrapolación: una tendencia regularizada reduce el sesgo en un dominio poco representado. No apoyan que aumentar suavidad o sustituir compact3 por lluvia mensual baste para resolver el problema. La geometría del soporte, el retorno hacia la media y la asociación geográfica son compatibles con el deterioro observado, pero no identifican por sí solos una causa única. C cambia conjuntamente la media y la escala residual de los límites en unidades crudas; por ello la atribución a la media no es una comparación perfectamente aislada de todos los efectos de escala.

**Recomendación: detener por ahora la experimentación activa de esta familia GPR y regresar a otros métodos con validación geográfica estricta.** Conservar F5-01 como referencia investigativa y C como evidencia de que una tendencia puede reducir sesgo, sin promover ninguno. No abrir todavía historia/topografía: las tres sensibilidades autorizadas no dan una mejora municipal y espacial consistente y C deteriora la cobertura. Una reapertura de GPR requeriría una pregunta nueva y evaluación independiente; este resultado no rechaza todos los Gaussian Processes. No se ejecuta esa reapertura ni se elige retrospectivamente una variante como nuevo champion.

Las tablas `paired_fold_contributions.csv`, `fold_omission_sensitivity.csv`, `municipality_omission_sensitivity.csv`, `gain_concentration.csv`, `influential_parcel_omission.csv` y `parcel_gains_*` contienen los cambios por bloque, municipio y parcela. `common_support_return_to_mean.parquet`, `common_support_quartiles.csv`, `kernel_support_and_trend_by_fold.csv` y `linear_mean_component_diagnostic.csv` permiten revisar soporte, retorno a la media y contribuciones de tendencia/GP. La interpretación es exploratoria y no declara superioridad estadística.

## Optimización

Los 1755 ajustes seleccionados convergieron; la condición máxima de sus covarianzas fue 2171.063. Se registraron 1730 incidencias de parámetros en límites y 1730 advertencias de ajuste, principalmente límites de optimización; no se ampliaron. Cada ajuste conserva sus tres inicios y el log-marginal-likelihood. Los LML de C corresponden a residuos normalizados condicionados a una tendencia estimada: no se usan como evidencia de superioridad ni se comparan directamente como likelihood de modelos de respuesta equivalentes. α=1 fue elegido en 48 de 65 ajustes externos C, 0.1 en diez, 0.01 en seis y 0.001 en uno. La frecuencia en el extremo de la grilla se registra sin abrir opciones adicionales. Las correlaciones de soporte no definidas por entradas constantes se conservan como NaN, sin imputarles cero. Las advertencias ambientales de OpenMP se registran por separado de convergencia y límites del GP.


## Integridad y reproducibilidad

Pasaron ocho pruebas matemáticas y de integración, incluyendo replay de los 1755 ajustes guardados. Se verificaron 6894 archivos anteriores protegidos. Se conservan 195 modelos externos, 1560 internos, 5265 inicios de optimización y 10764 filas OOF (tres referencias y tres sensibilidades). No se ajustó ningún modelo final ni se generaron predicciones PRED. Diagnósticos numéricos y tiempos: `audit/execution_diagnostics.json`; advertencias del entorno y pruebas: `audit/tests.txt`.
