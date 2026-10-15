"""Reviewed exploratory interpretation for S1 v1, not an outer-fold selector."""
import json
from . import execution as e

TEXT='''

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
'''

def append():
    path=e.OUT/'report/synthesis.md';text=path.read_text(encoding='utf8')
    if '## Respuestas y recomendación' not in text:path.write_text(text+TEXT,encoding='utf8')
    decision=dict(recommendation='stop_active_GPR_family_return_to_other_methods',champion_promoted=False,history_topography_executed=False,statistical_superiority_claimed=False,interpretation='C reduces spatial bias mainly in block3; municipal tradeoff, concentration and undercoverage prevent consistent improvement')
    (e.OUT/'report/decision.json').write_text(json.dumps(decision,indent=2),encoding='utf8')
