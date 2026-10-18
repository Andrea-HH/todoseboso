> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# F7 — Primera ejecución: CatBoost y XGBoost directos

Se ejecutaron únicamente F7-00 y F7-01. E1–E3 permanecen predefinidas para CatBoost y requieren revisión. Las comparaciones son exploratorias sobre etiquetas y folds reutilizados; no constituyen confirmación independiente ni superioridad estadística.

## Rendimiento OOF

| Modelo | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| F7-00 | 0.504874 | 0.515345 | 0.528223 | 0.642591 |
| F7-01 | 0.503252 | 0.568064 | 0.512862 | 0.727521 |
| C-T3 | 0.511582 | 0.520604 | 0.581259 | 0.678778 |
| F5-01 | 0.504006 | 0.499759 | 0.544208 | 0.734797 |
| F6-E0 | 0.506296 | 0.512979 | 0.638586 | 0.758923 |

RMSE en t/ha: cada repetición tiene138 OOF completas; aleatoria promedia diez repeticiones. MAE, sesgo y diferencias pareadas están en las tablas. Champion solo se compara en aleatoria, con RMSE OOF completa 0.498127. No se reconstruye evaluación territorial del Champion.

## Arquitectura y transferencia

- F7-00: ΔRMSE vs C-T3 municipal -0.053036, espacial -0.036187; mejora RMSE en 4/4 protocolos. Mayor ΔRMSE al omitir un fold territorial: +0.005000. Estas omisiones solo recalculan OOF, sin reajustar.
- F7-01: ΔRMSE vs C-T3 municipal -0.068397, espacial +0.048743; mejora RMSE en 2/4 protocolos. Mayor ΔRMSE al omitir un fold territorial: +0.093476. Estas omisiones solo recalculan OOF, sin reajustar.

## Concentración territorial y explicación de la mejora

CatBoost mejora agregados municipales y espaciales frente a los tres controles, pero las ganancias no están territorialmente equilibradas. Singuilucan (16 parcelas; fold municipal3) aporta 108.0% de la ganancia municipal neta de SSE frente a C-T3. El bloque espacial4, con16 de Singuilucan y2 de otros municipios, aporta 97.6% de la ganancia espacial neta. Un porcentaje superior a100% significa que otras regiones compensan parte de esa mejora con deterioros; no es una proporción de parcelas.
Al excluir Singuilucan solo del cálculo OOF climate_profile, ΔRMSE vs C-T3 = +0.009016, ΔMAE = +0.011709, con122 parcelas restantes. No se reajusta ningún modelo.
Al excluir Singuilucan solo del cálculo OOF municipality, ΔRMSE vs C-T3 = +0.005000, ΔMAE = -0.037907, con122 parcelas restantes. No se reajusta ningún modelo.
Al excluir Singuilucan solo del cálculo OOF random, ΔRMSE vs C-T3 = +0.004508, ΔMAE = -0.001446, con122 parcelas restantes. No se reajusta ningún modelo.
Al excluir Singuilucan solo del cálculo OOF spatial, ΔRMSE vs C-T3 = +0.001912, ΔMAE = +0.004318, con122 parcelas restantes. No se reajusta ningún modelo.

CatBoost empeora RMSE de Chignahuapan en municipal y espacial, aunque su MAE municipal mejora. Excluir Hidalgo completo revierte también la ganancia espacial frente a C-T3. Las localidades con una a cinco parcelas tienen soporte reducido y no sostienen conclusiones municipales firmes.

El problema espacial no se resuelve simplemente en bloque3: CatBoost conserva sesgo positivo0.734682 frente a0.718204 de C-T3 en ese bloque, y XGBoost tiene un deterioro importante allí. La ganancia principal de CatBoost surge en el bloque4; sin ese bloque su ΔRMSE espacial es solo−0.001010 y su MAE empeora ligeramente.

En municipal, la ganancia SSE de CatBoost 8.120274 se descompone en mejora de sesgos por fold 12.641459 y deterioro de dispersión -4.521185. En espacial: ganancia SSE 6.598704, parte de sesgo 4.342412, parte de dispersión 2.256292. Es una descomposición descriptiva de los errores, no una prueba causal del mecanismo.

Omitir las cinco parcelas con mayores ganancias conserva ventaja RMSE municipal y espacial; omitir las diez la revierte. La mejora por perfil es pequeña y se revierte al retirar incluso la parcela con mayor ganancia. Los casos permanecen en todos los ajustes y evaluaciones principales; estas omisiones solo diagnostican concentración.

## Diferencias entre parcelas del mismo clima

| Modelo | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| F7-00 | 0.628178 | 0.543412 | 0.544684 | 0.584666 |
| F7-01 | 0.627715 | 0.565005 | 0.550192 | 0.562216 |
| C-T3 | 0.589951 | 0.547885 | 0.520989 | 0.540147 |
| F5-01 | 0.602212 | 0.531827 | 0.538821 | 0.531899 |
| F6-E0 | 0.608918 | 0.546051 | 0.521596 | 0.531013 |

La tabla mide RMSE de diferencias entre parcelas, con igual peso por perfil, y no es RMSE de rendimiento individual. CatBoost empeora respecto a C-T3 en aleatoria, municipal y espacial; XGBoost empeora en los cuatro. Las ganancias agregadas municipales no prueban que estos modelos distingan mejor parcelas con clima idéntico. La lluvia compacta es constante dentro de perfil; en esta etapa MayNDVI es el único diferenciador intraperfil. Historia y pendiente podrían añadir variación local, pero ese beneficio aún no se ha probado en boosting.

## Interpretabilidad y límites

- ALE completo F7-00, S2_ndvi_month_05: 6/65 fits respaldados.
- ALE completo F7-00, compact_concentration_hhi: 0/65 fits respaldados.
- ALE completo F7-00, compact_early_fraction: 5/65 fits respaldados.
- ALE completo F7-00, compact_precip_total: 0/65 fits respaldados.
- ALE completo F7-01, S2_ndvi_month_05: 6/65 fits respaldados.
- ALE completo F7-01, compact_concentration_hhi: 0/65 fits respaldados.
- ALE completo F7-01, compact_early_fraction: 5/65 fits respaldados.
- ALE completo F7-01, compact_precip_total: 0/65 fits respaldados.

Las figuras distinguen diferencias locales respaldadas de curvas ALE completas. No se interpolan huecos sin soporte. Las interacciones lluvia–NDVI son diferencias locales mixtas de cuatro esquinas, no causas ni un screening abierto. Las interacciones con historia/pendiente se difieren porque esas variables aún no entran a modelos.

HHI concentra gran parte de PredictionValuesChange de CatBoost y de la ganancia de XGBoost, con medianas de umbral próximas a0.18. Ello describe una partición climática fuerte, potencialmente vinculada a territorio; no demuestra que cambiar concentración cause un rendimiento diferente. No hay ALE completa respaldada para HHI ni total de lluvia. MayNDVI tiene respuestas locales positivas más pronunciadas en el cuartil inferior con CatBoost; XGBoost las concentra más arriba, pero el soporte en el cuartil superior es escaso. No se afirma monotonicidad global.

Las interacciones respaldadas cubren151/585 celdas HHI–NDVI,277/585 temprana–NDVI y236/585 total–NDVI por algoritmo. Mezclan entrenamientos superpuestos y no son585 réplicas independientes. La permutación condicional de MayNDVI incrementa MSE en promedio donde es identificable, con efecto de MAE inconsistente para CatBoost. Uso frecuente no garantiza mejora intraperfil ni aporte incremental frente a un boosting de lluvia sola, que aquí no fue ajustado.

La permutación de lluvia3 es conjunta y condicionada al perfil: al ser constante en ese perfil, su utilidad no es identificable por esta permutación. Esto no equivale a irrelevancia. MayNDVI se evalúa solo con pares/clases suficientes dentro del perfil y no controla todas las demás variables. Frecuencia de partición, PredictionValuesChange de CatBoost y ganancia media de XGBoost son medidas descriptivas diferentes; no se comparan como escalas equivalentes ni importancia causal. Hojas simétricas pueden estar vacías o tener pocas observaciones, pese a L2; el soporte real se registra.

Pares intraperfil usan solo parcelas evaluadas por el mismo modelo externo, con resultados de igual peso por perfil y ponderación por pares. Su soporte puede ser reducido fuera de Chignahuapan. No se entregan intervalos predictivos de boosting: ni variación entre árboles ni dispersión de OOF proporciona cobertura calibrada.

## Próximo paso

Recomiendo continuar, tras revisión, con las ablaciones acotadas CatBoost E1/E2/E3 ya predefinidas. La razón metodológica es que árboles simétricos regularizados pueden corregir sesgos regionales mejor que Extra Trees con compact4, pero aún fallan en la discriminación intraperfil. Historia NDVI2 y pendiente introducen variación dentro de perfiles que la lluvia no ofrece; las ablaciones deben comprobar si esa variación reduce errores locales sin perder los beneficios municipales. Esta es una hipótesis pendiente, no garantía de que los complementos mejoren. No recomiendo expandir XGBoost usando su RMSE municipal aislado: por perfil y espacial empeora frente a C-T3.

La evidencia apoya capacidad no lineal para corregir ciertos niveles regionales; debilita la hipótesis de superioridad general o mejora homogénea intraperfil del boosting compacto. No descarta otras regularizaciones o todos los modelos de boosting. Los límites se mantienen:300 árboles seleccionados con frecuencia y poca profundidad son resultados de una búsqueda acotada, no evidencia de óptimo global. No se amplían tras ver las OOF.

El próximo residual propuesto, después de revisar las ablaciones, es una base C-T3 compacta más una corrección CatBoost pequeña sobre MayNDVI, historia NDVI2 y pendiente, con amplitud de corrección que pueda elegirse como cero mediante validación interna. Los targets de corrección deben generarse por cross-fitting del núcleo exclusivamente dentro de cada entrenamiento correspondiente; cada evaluación interna debe repetir la construcción sin ver sus etiquetas de validación. Posteriormente se reajusta el núcleo sobre todo ese entrenamiento y se suma la corrección. Esa construcción difiere de usar residuos ajustados sobre las mismas filas, de residuos OOF globales y de corregir el Champion. Se propone para preservar una tendencia lineal y estudiar señales locales; no se presupone mejor extrapolación y no se ejecuta ahora.

La ejecución se detiene aquí para revisión antes de E1–E3. CatBoost se asignó antes de las OOF, y cualquier cambio posterior de algoritmo motivado por resultados externos se documentará como exploratorio. No se ejecuta residual, no se promueve champion y no se generan59 PRED.

Fuentes técnicas: [CatBoost: parameter tuning](https://catboost.ai/docs/en/concepts/parameter-tuning), [XGBoost: parameters](https://xgboost.readthedocs.io/en/stable/parameter.html).


## Verificación

Nueve pruebas pasaron: transformaciones exclusivamente de entrenamiento, particiones internas originales y selección acotada, replay de650 modelos, referencias y agregación exactas, soporte de efectos y contabilidad de hojas. 12862 archivos anteriores conservaron su hash. Se ajustaron130 modelos externos y4160 candidatos internos; se guardaron10350 filas OOF entre referencias y candidatos. Advertencias de ajuste: 0. No se ejecutaron E1–E3, modelo final, residuos ni59 PRED.
