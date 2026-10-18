> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# R2: investigación de sesgo residual municipal

Se completó el diagnóstico solicitado. **No se justifica todavía añadir una calibración municipal a R2 bajo el soporte conservador de la etapa anterior.** Los municipios con al menos 15 parcelas no muestran una dirección suficientemente estable entre parcelas y perfiles. Almoloya presenta la señal positiva más persistente, pero solo tiene 10 parcelas.

## Qué se analizó

Se recuperaron las 1,794 predicciones OOF de R2, correspondientes a los 65 folds originales. Para el remuestreo aleatorio se promedió el residuo de cada parcela entre sus diez repeticiones: se mantienen 138 unidades, no 1,380 observaciones independientes. Residuo = observado − predicho; positivo indica subestimación y negativo sobreestimación.

Se examinó consistencia entre repeticiones y protocolos; 4,000 remuestreos por parcela y por cluster de perfil climático; omisión de 1/3/5 mayores residuos absolutos, positivos y negativos; omisión de cada perfil completo. No se reajustaron modelos al hacer estas sensibilidades.

Los rangos de remuestreo al 95% describen estabilidad de los residuos congelados. No son intervalos de incertidumbre del pipeline vuelto a entrenar, no incluyen campañas nuevas y no constituyen una prueba formal de significancia. Los diez acuerdos de signo reutilizan las mismas parcelas. Los rangos degenerados de municipios con una sola parcela no representan certeza.

## Resultados aleatorios

| Municipio | Parcelas | Residuo medio, t/ha | Rango por perfil climático | Lectura |
|---|---:|---:|---:|---|
| Chignahuapan | 71 | +0.023 | −0.163 a +0.106 | Sesgo agregado pequeño e inestable |
| Calpulalpan | 30 | −0.051 | −0.179 a +0.108 | Sobreestimación pequeña, rango cruza cero |
| Singuilucan | 16 | −0.145 | −0.495 a +0.012 | Mayor sobreestimación, muy sensible al soporte |
| Almoloya | 10 | +0.127 | +0.001 a +0.213 | Subestimación persistente, muestra insuficiente bajo mínimo15 |

La dirección de las medias aleatorias coincide con la de validación por perfil. Sin embargo, eso no elimina la variabilidad entre parcelas o la influencia de perfiles particulares.

**Singuilucan:** retirar las cinco parcelas con mayores residuos absolutos cambia la media −0.1448 → −0.0106 t/ha: se pierde aproximadamente 93% de su magnitud. Otras omisiones de errores absolutos pueden invertir el signo; al retirar perfiles completos individualmente permanece negativo, con medias −0.2709 a −0.0946. No corresponde aplicar automáticamente −0.145 a todas sus predicciones.

**Calpulalpan:** tras retirar los cinco mayores errores absolutos, la media queda −0.0344. El sesgo conserva su signo en esas omisiones, pero sus rangos de remuestreo cubren valores positivos y negativos. La media espacial −0.8121 no es una corrección disponible para un municipio retenido sin etiquetas: describe error de transferencia.

**Chignahuapan:** la media +0.0230 es pequeña frente a la dispersión de errores. Al retirar los cinco errores absolutos mayores pasa a +0.1093, por lo que incluso su magnitud depende de pocas observaciones. Una constante tampoco resolvería las diferencias de rendimiento entre parcelas de sus perfiles dominantes.

**Almoloya:** subestimación media +0.1266 aleatoria, +0.1425 por perfil, +0.2002 municipal y +0.3278 espacial. Su signo aleatorio permanece positivo al retirar los mayores errores absolutos y cada perfil. El remuestreo por perfil apenas excluye cero por el extremo inferior: no interpretar como confirmación estadística. Con solo diez parcelas, es un candidato para aumentar datos y confirmar, no una corrección desplegable.

## Decisión de calibración

Se conservó el soporte de R2: mínimo 15 parcelas y 2 perfiles. Se exigió además dirección compartida aleatoria/perfil, estabilidad por parcela y perfil, ausencia de inversión de signo en omisiones de mayores errores absolutos y perfiles, y acuerdo de signo en al menos 80% de repeticiones. Ningún municipio satisface el conjunto. Las condiciones son un filtro exploratorio conservador, no una prueba de inexistencia de sesgo ni un mínimo universal para estimar una media municipal.

La inspección inicial de medias e influencia precedió a guardar el diseño del diagnóstico. Esto se documentó explícitamente: no se presenta como descubrimiento preregistrado o confirmación independiente. No se escogieron reglas o pesos para optimizar las métricas externas.

**No se entrenó el calibrador condicional**, porque su condición de avance no se cumple. No hay un RMSE nuevo de calibración que reportar y no se afirma que añadir una constante haya sido probado y rechazado predictivamente. Se diagnosticó que falta fundamento estable para esa siguiente ejecución.

Una calibración futura justificada usaría `n/(n+λ) × media(observado−predicho)` con opción de ajuste cero y selección de λ exclusivamente interna. Los targets residuales tendrían que provenir de R2 completamente ajustado y seleccionado sin las etiquetas que predice: excluirlas solo del ajuste de expertos no basta si la selección del mezclador las utilizó. No reutilizar otras OOF externas cuyos entrenamientos incluyan el fold que se quiere evaluar.

Municipio desconocido recibe corrección cero. Una constante municipal no cambia diferencias entre parcelas de ese municipio, por lo que no puede reducir directamente errores intraperfil de pares del mismo municipio.

## Recomendación

Conservar R2 como candidato para municipios representados y C-T3/EQUAL3 como referencias. No fijar correcciones municipales con estas medias. Priorizar nuevos datos de Almoloya y Singuilucan y aclarar las parcelas/perfiles que concentran la influencia; no eliminarlos de entrenamiento ni modificar sus rendimientos sin evidencia de un error de origen. Si se desea forzar una sensibilidad de calibración con muestras pequeñas, sería una investigación adicional, con límites propios y evaluación anidada, no una mejora ya respaldada por este diagnóstico.

## Artefactos y verificación

Dos pruebas pasaron: remuestreo determinista que conserva perfiles como unidades y omisiones sin alterar residuos originales. Se verificaron por SHA-256 los archivos consumidos. Cero ajustes de modelos, cero nuevas OOF, sin modificación del Champion, rendimientos o predicciones PRED.

- [Diseño diagnóstico y límites](../outputs/research/r2_residual_diagnosis/v1/frozen_diagnostic_design.json)
- [Informe y tablas](../outputs/research/r2_residual_diagnosis/v1/report/informe.md)
- [Estabilidad por municipio](../outputs/research/r2_residual_diagnosis/v1/tables/municipal_stability.csv)
- [Sensibilidad a parcelas y perfiles](../outputs/research/r2_residual_diagnosis/v1/tables/influence_sensitivity.csv)
- [Figura de sesgos](../outputs/research/r2_residual_diagnosis/v1/figures/supported_municipal_bias.png)
- [Script reproducible](../scripts/386_r2_residual_diagnosis.py)
