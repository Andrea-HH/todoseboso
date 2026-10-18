# Relevancia del núcleo C-T3 y evidencia para Reference26

Análisis exploratorio retrospectivo,2026-10-18. Se estudiaron138 rendimientos conocidos, agrupados en43 perfiles climáticos. **No se modificaron los champions, sus hiperparámetros, sus predicciones finales ni las59 PRED.** Se reprodujo C-T3 exactamente y se reentrenaron sólo sus ablaciones y controles con las65 particiones originales.

## Qué pregunta responde cada prueba

| Análisis | Hipótesis nula | Qué permite concluir | Qué no demuestra |
|---|---|---|---|
| Asociación OLS ajustada por estado | Coeficiente parcial de la variable igual a cero, manteniendo las otras entradas y el estado | Evidencia de asociación lineal condicional bajo el modelo de diagnóstico | Significancia del coeficiente penalizado de Elastic Net, causalidad o ganancia predictiva de26 |
| Contraste conjunto del bloque de lluvia | Los tres coeficientes de lluvia son simultáneamente cero | Asociación conjunta que no depende de que cada columna pase un umbral individual | Que las tres sean indispensables para todo protocolo |
| NDVI con efectos fijos por perfil | Coeficiente NDVI dentro del perfil igual a cero | Asociación entre parcelas de un mismo perfil climático | Que se hayan eliminado todas las diferencias de suelo, manejo o medición |
| Ablación reajustada de C-T3 | Diferencia agrupada de pérdidas cuadráticas entre modelo reducido y completo compatible con cero | Aporte predictivo bajo la receta, rejillas y protocolos evaluados | Aporte de esa entrada en la arquitectura completa de26 ni información causal |
| Contrastes pareados26 frente a C-T3 ya existentes | Ausencia de diferencia de pérdidas entre las arquitecturas | Evidencia sobre el sistema completo en el protocolo identificado | Relevancia individual de sus26 entradas o confirmación independiente nueva |

## Asociación: ajustes y resultados

Se ajustaron OLS diagnósticas con las cuatro entradas estandarizadas: una sin estado y otra con interceptos por estado. No son sustitutos de Elastic Net ni se usaron para seleccionar parámetros de los champions. En ambas, la covarianza se agrupó por los43 perfiles, con corrección de muestra finita y referencia t/F con grados de libertad por número de grupos. El contraste de NDVI con efectos fijos se restringe a los12 perfiles informativos,107 parcelas, con referencia t de11 grados de libertad; los31 perfiles sin variación interna no cuentan como grupos informativos. No se intentó identificar lluvia dentro de perfil porque allí es constante. Este criterio de soporte depende de X, no del rendimiento ni de su p-valor; su corrección quedó registrada en [la enmienda metodológica](../../../configs/core4_relevance/v1/amendment_01.json).

La familia conjunta contiene **13 contrastes**: cuatro coeficientes y dos bloques en cada una de las dos OLS, más NDVI intraperfil. Se aplica Holm a los13. Los intervalos95% de coeficientes son marginales, sin ajuste simultáneo.

| Entrada en OLS ajustada por estado | Coeficiente por1 SD, t/ha | IC95% marginal | p sin ajuste | p Holm,13 pruebas |
|---|---|---|---|---|
| `compact_precip_total` | -0.2595 | [-0.3771, -0.1419] | 6.1279e-05 | 0.0003064 |
| `compact_early_fraction` | -0.3368 | [-0.5539, -0.1197] | 0.003168 | 0.0095039 |
| `compact_concentration_hhi` | -0.1024 | [-0.2621, +0.0572] | 0.20244 | 0.20244 |
| `S2_ndvi_month_05` | +0.2058 | [+0.1252, +0.2863] | 6.4417e-06 | 4.5092e-05 |

El bloque conjunto de lluvia conserva asociación ajustada por estado: **p Holm=1.3004e-06**. NDVI conserva asociación intraperfil: **p Holm=0.0022216**. Este último contraste dispone de12 perfiles con varias parcelas y NDVI variable, que reúnen107 parcelas; los perfiles restantes no aportan variación interna de NDVI.

Lluvia total, fracción temprana y NDVI presentan evidencia de asociación en este diagnóstico. **HHI no mantiene evidencia suficiente tras ajustar por estado** (p ajustada≈.2024), aunque sí la presenta en la OLS sin estado. Esto muestra sensibilidad a la estructura territorial; no demuestra que HHI carezca de información. Los coeficientes negativos de lluvia son asociaciones condicionales del conjunto observado, no una demostración agronómica de que aumentar lluvia reduzca rendimiento.

## Aporte predictivo: ablaciones con reajuste

Se congelaron siete recetas: núcleo completo, retirada individual de cada entrada, NDVI solo y media de entrenamiento. Cada Elastic Net reducido se recalibró con las particiones internas originales y la misma rejilla12 de alpha/l1_ratio, con imputación/escalado propios del entrenamiento. **C-T3 completo reproduce sus1,794 predicciones originales con diferencia máxima0.0.** Se generaron12,558 predicciones de evaluación, siete recetas por1,794 casos; no se tratan como12,558 observaciones independientes.

Cada celda es **RMSE t/ha / R²**; MAE y sesgo están en [metrics.csv](metrics.csv). Aleatoria: métricas sobre138 OOF por repetición y promedio de10 repeticiones. Otros protocolos:138 OOF completas.

| Receta C-T3 | Aleatoria | Perfil | Municipal | Espacial |
|---|---|---|---|---|
| Completo4 | 0.5116 / 0.6361 | 0.5206 / 0.6232 | 0.5813 / 0.5302 | 0.6788 / 0.3594 |
| Sin lluvia total | 0.5342 / 0.6032 | 0.5444 / 0.5879 | 0.6768 / 0.3632 | 1.0248 / -0.4601 |
| Sin fracción temprana | 0.5665 / 0.5538 | 0.6017 / 0.4967 | 0.7330 / 0.2530 | 0.6971 / 0.3243 |
| Sin HHI | 0.5145 / 0.6320 | 0.5257 / 0.6158 | 0.6011 / 0.4976 | 0.5596 / 0.5646 |
| Sin NDVI de mayo | 0.5386 / 0.5966 | 0.5447 / 0.5875 | 0.6002 / 0.4992 | 0.7661 / 0.1839 |
| Sólo NDVI de mayo | 0.7152 / 0.2888 | 0.7733 / 0.1685 | 0.9289 / -0.1997 | 0.8819 / -0.0814 |
| Media de entrenamiento | 0.8560 / -0.0188 | 0.9368 / -0.2201 | 1.1518 / -0.8447 | 1.0276 / -0.4683 |

**Lectura:** retirar total, fracción temprana o NDVI empeora el RMSE en los cuatro protocolos. Eliminar HHI empeora ligeramente aleatoria/perfil/municipal, pero mejora espacial de.6788 a.5596 t/ha (−.1192). Es una señal exploratoria específica de transferencia, no un criterio para borrar HHI de26 sin reajustar su arquitectura completa.

### Qué respaldo estadístico tienen las diferencias predictivas

Se contrastan24 diferencias: seis recetas frente a completo, en cuatro protocolos. Prueba bilateral de inversión de signos de pérdidas cuadráticas agregadas por perfil (aleatoria/perfil), municipio (municipal) o bloque (espacial). Las repeticiones aleatorias se promedian por parcela antes de inferir. Se enumeran todas las asignaciones para9 municipios y5 bloques; con43 perfiles se usan20,000 asignaciones y semilla2026. Holm se aplica a las24 comparaciones.

**Ninguna de las cuatro retiradas individuales resulta significativa tras Holm.** Los cuatro contrastes que sobreviven corresponden a completo frente a NDVI solo y a media de entrenamiento, bajo aleatoria y por perfil. Por tanto, existe respaldo del conjunto frente a controles débiles; no una prueba de indispensabilidad individual de cada entrada.

Con sólo cinco bloques, el mínimo p bilateral de la enumeración de signos es2/32=.0625 incluso antes de Holm. La ausencia de significancia espacial es especialmente poco informativa. La enumeración es exacta para las asignaciones de signos, no una garantía de exactitud inferencial si no se cumplen independencia y simetría de pérdidas por grupo. Los modelos comparten datos de entrenamiento, por lo que los contrastes se interpretan con cautela adicional.

## Qué respalda ya al modelo26

Los siguientes contrastes proceden de la comparación previa de cuatro líderes; **se recuperan, no se cuentan como replicación nueva**. Su Holm original comprende24 comparaciones entre modelos y protocolos, distinto de la familia nueva de24 ablaciones.

| Protocolo | Reducción RMSE26 frente a C-T3, t/ha | p bilateral | p Holm original |
|---|---|---|---|
| climate_profile | 0.0432 | 0.0037498 | 0.078746 |
| municipality | 0.0060 | 0.85938 | 1 |
| random | 0.0368 | 0.0010999 | 0.025299 |
| spatial | 0.0454 | 0.375 | 1 |

La mejora aleatoria26 frente a C-T3 conserva p ajustada≈.0253 bajo esa prueba. Las diferencias por perfil, municipal y espacial no sobreviven su ajuste. Esto respalda una parte del rendimiento observado, no superioridad territorial demostrada. El banco97/41 es otra evaluación sobre las mismas etiquetas, no una campaña independiente.

## Límites y decisión metodológica

Los predictores y arquitecturas se eligieron después de investigación extensa con estas etiquetas. **Holm corrige las familias enumeradas aquí, no toda la selección histórica**; los p-valores no son confirmatorios posteriores a selección ni una certificación del modelo. Agrupar por perfil evita tratar duplicados climáticos como independientes, pero no garantiza independencia geográfica entre perfiles. La OLS supone una forma aditiva y su ajuste por estado no controla todas las diferencias territoriales. No se interpreta su R² ajustado ni sus p-valores como propiedades del modelo26.

La evidencia mejora la documentación: permite sostener asociación del núcleo, mostrar aportes predictivos observados y explicitar que HHI es la entrada más discutible. No permite escribir que «las26 variables son estadísticamente significativas».

Para aumentar credibilidad de26 priorizaría: (1) conservar la receta congelada y obtener rendimientos externos o de las59 cuando se revelen; (2) si se abre otra sensibilidad, retirar HHI **en C-T3 y en el corrector interno del experto**, recalibrando pesos y R3 dentro de entrenamiento con los mismos protocolos; (3) evaluar ablaciones de bloques completos y estabilidad regional antes de añadir complejidad. Esa sensibilidad completa no se ejecutó aquí y un nuevo resultado sobre estos mismos folds seguiría siendo exploratorio.

## Reproducción y archivos

Ejecución: `python scripts/529_core4_relevance.py`; informe: `python scripts/530_report_core4_relevance.py`. Configuración previa: [frozen_design.json](../../../configs/core4_relevance/v1/frozen_design.json). Excel y OOF privados: `outputs/research/core4_relevance/v1/relevancia_core4.xlsx` y `oof_predictions.parquet`. Resultados agregados en este directorio, sin IDs ni rendimientos por parcela. [Auditoría](audit.json), [contrastes de asociación](association_tests.csv), [coeficientes diagnósticos](association_coefficients.csv), [contrastes de ablación](ablation_tests.csv), [contrastes previos26](existing_26_vs_CT3_tests.csv). No se leyó PRED ni se modificaron finales.

Fuentes metodológicas: [Statsmodels: covarianza robusta y agrupada, corrección y grados de libertad](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html); [scikit-learn: importancia predictiva y variables correlacionadas](https://scikit-learn.org/1.7/modules/permutation_importance.html). No se usó permutación irrestricta de variables correlacionadas ni se inventaron p-valores para Elastic Net.
