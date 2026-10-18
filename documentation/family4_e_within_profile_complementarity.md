> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# F4-E — Complementariedad intraperfil de vegetación, dinámica temporal y relieve

Esta extensión evalúa únicamente tres cambios aditivos frente a lluvia + NDVI mayo: inicio del mayor ascenso LAI (E2), relieve local medio (E3) y sustitución de NDVI mayo por LAI q10 (E4). No hay una nueva etapa residual ni nuevas búsquedas de variables. Los resultados siguen siendo exploratorios: las candidatas proceden del screening retrospectivo de 1,473 variables sobre las mismas 138 etiquetas.

## Antecedentes, diseño y controles

Se verificó el manifiesto anterior de Familia 4 antes de entrenar. Se recuperó `F4-S1` —el nombre real de la referencia aditiva— como F4-E1 y `J0_RAIN` como F4-E0. Las 1,794 predicciones de cada control se reutilizan literalmente. El modelo S1 archivado se reprodujo en los 65 folds sobre los mismos IDs, con tolerancia absoluta 1e-10. Los modelos/transformaciones de E0/E1 permanecen en sus rutas originales y son referencias inmutables; se guardan 195 modelos nuevos de E2/E3/E4 y 8,970 predicciones OOF totales incluyendo los controles.

La matriz tiene cinco modelos, 138 TRAIN y 59 PRED sin etiquetas usadas, 53 perfiles climáticos totales y 43 perfiles con etiquetas. Se conservan 50 folds aleatorios —cinco por diez repeticiones— y cinco por perfil, municipio y espacio; también sus particiones internas exactas. En protocolo por perfil, las parcelas de un perfil permanecen retenidas juntas.

Elastic Net y `ConditionalFeatures` son exactamente los de F4-S1, con el mismo grid de cuatro alpha y tres l1_ratio, max_iter=200000, imputación mediana, centrado/escala y eliminación de constantes aprendidos dentro de cada entrenamiento. Los nuevos modelos usan exclusivamente columnas predictoras declaradas. No se utilizan medias de Y por perfil, ID, estado, municipio, coordenadas, cuartiles observados ni diagnósticos de soporte como entradas. E2 y E3 añaden una sola columna; E4 sustituye NDVI por LAI q10. La alternativa LAI y el relieve medio se congelaron después de la auditoría y antes de inspeccionar nuevas métricas predictivas.

El relieve medio se eligió por ser un resumen representativo ponderado de cobertura, evitando seleccionar un mínimo o extremo por su correlación. Pendiente q10 y orientación seno/coseno son diagnósticos secundarios; EVI/FAPAR q10 y SAVI ascenso no se entrenan como sensibilidades para buscar ganadores.

## Definiciones verificadas y reservas

- NDVI/EVI mayo son medias de los promedios parcelarios válidos de mayo de 2025; LAI, NDVI y FAPAR q10 son percentiles **temporales** de promedios observados entre abril y octubre, no percentiles espaciales de píxeles.
- LAI inicio de ascenso se define mediante el mínimo acumulado de la trayectoria: se localiza el punto posterior con la mayor diferencia frente a ese mínimo y se toma la primera fecha del mínimo anterior. Se expresa en días desde el 1 de abril. Duplicados de fecha se promedian, observaciones faltantes se omiten y no se interpola ni suaviza. No es una fecha validada de emergencia, siembra o fase fenológica. La ventana completa llega hasta el 31 de octubre, por lo que no constituye un pronóstico temprano de mayo.
- La fuente contiene LAI negativos; las unidades y transformación física del índice entregado no están establecidas. E4 evalúa el índice numérico existente, sin corregirlo ni afirmar área foliar física. También el inicio de ascenso se interpreta como forma de esa serie suministrada.
- Relieve es el máximo menos mínimo de elevación en 3×3 celdas de DEM CEM de 120 m, luego promediado dentro de cada parcela con pesos de cobertura. Sus diferencias son metros y su soporte vecinal es unos 360 m: no mide microrelieve fino ni drenaje observado.
- La orientación se calculó como atan2(-gx,gy) a partir del gradiente raster y se conserva como medias zonales de seno y coseno. No se modelan grados linealmente ni se asume una convención cardinal no verificada. Se conserva el módulo de ese vector medio y se marca pendiente q10<2° como sensibilidad descriptiva de terrenos casi planos; no es una certificación de que toda la parcela sea plana.
- Se conservan los valores válidos suministrados y su máscara original, sin inventar máscaras de nubes ni eliminar parcelas. Cloud_raw es metadato del proveedor, no una máscara local verificada. Fechas de observación no certifican disponibilidad operativa o versión de procesamiento.

Soporte temporal de las 197 parcelas:

| index | n_parcels | median_valid_dates | min_valid_dates | median_valid_months | median_gap_days | max_gap_days | n_insufficient | negative_observations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| evi | 197 | 37.0000 | 31 | 7.0000 | 5.0000 | 28.0000 | 0 | 0 |
| fapar | 197 | 37.0000 | 31 | 7.0000 | 5.0000 | 28.0000 | 0 | 0 |
| lai | 197 | 37.0000 | 31 | 7.0000 | 5.0000 | 28.0000 | 0 | 1885 |
| ndvi | 197 | 37.0000 | 31 | 7.0000 | 5.0000 | 28.0000 | 0 | 1 |
| savi | 197 | 37.0000 | 31 | 7.0000 | 5.0000 | 28.0000 | 0 | 0 |

La auditoría incluye por parcela/índice meses válidos, faltantes, número de fechas únicas, concentración mensual, gaps, nubes y trayectorias insuficientes (<4 fechas o <4 meses, umbral descriptivo). La omisión de cada mes documenta la sensibilidad del q10 y del inicio de ascenso; estos cálculos son auditorías y no reemplazan las matrices existentes. No se interpretan muchas observaciones de una parcela como escenas independientes.

## Redundancia y descomposición descriptiva

Se calculan Pearson y Spearman globales, intraperfil y entre medias de perfiles. Las asociaciones intraperfil excluyen grupos singleton; los tamaños efectivos están en cada tabla. Se reportan asociaciones por estado/municipio, sin Chignahuapan y al excluir cada perfil por turno. Las medias de perfil y su relación con Y solo se utilizan aquí para describir la muestra, nunca como transformación predictiva.

Para la correlación parcial intraperfil se residualizan tanto X como Y contra NDVI mayo centrado dentro del perfil. La lluvia mensual es idéntica dentro de cada perfil y su componente intraperfil es cero: no añade otra dimensión a ese ajuste dentro de grupos. Los residuos calculados con todas las etiquetas son exclusivamente descriptivos y no se usan para entrenar ni seleccionar nuevos candidatos.

| index | n | n_profiles | partial_within_correlation |
| --- | --- | --- | --- |
| NDVI q10 | 107 | 12 | -0.0084 |
| LAI q10 | 107 | 12 | -0.0256 |
| FAPAR q10 | 107 | 12 | 0.0237 |
| EVI mayo | 107 | 12 | -0.1731 |
| Inicio ascenso LAI | 107 | 12 | -0.2099 |
| Duración ascenso SAVI | 107 | 12 | 0.2382 |
| Relieve local medio | 107 | 12 | 0.0770 |
| Pendiente q10 | 107 | 12 | 0.1481 |
| Orientación seno | 107 | 12 | -0.0015 |
| Orientación coseno | 107 | 12 | -0.1984 |

Una correlación parcial no equivale a complementariedad validada. Se examina su sensibilidad regional y a la exclusión de perfiles. La extensión tampoco prueba que los contrastes se mantengan en parcelas con NDVI casi idéntico: controla NDVI como covariable continua, sin crear un experimento adicional de emparejamiento por NDVI.

## Predicción y transferencia

RMSE t/ha, calculado con todas las predicciones de cada repetición y después promediado:

| experiment | climate_profile | municipality | random | spatial |
| --- | --- | --- | --- | --- |
| F4-E0 | 0.5444 | 0.6954 | 0.5214 | 0.7348 |
| F4-E1 | 0.5263 | 0.6711 | 0.5048 | 0.7390 |
| F4-E2 | 0.5333 | 0.6750 | 0.5056 | 0.7384 |
| F4-E3 | 0.5249 | 0.6820 | 0.5074 | 0.7815 |
| F4-E4 | 0.5378 | 0.8356 | 0.5119 | 0.9526 |

MAE t/ha:

| experiment | climate_profile | municipality | random | spatial |
| --- | --- | --- | --- | --- |
| F4-E0 | 0.3903 | 0.5002 | 0.3695 | 0.5620 |
| F4-E1 | 0.3889 | 0.4986 | 0.3641 | 0.5729 |
| F4-E2 | 0.3945 | 0.4999 | 0.3637 | 0.5734 |
| F4-E3 | 0.3926 | 0.5007 | 0.3672 | 0.5946 |
| F4-E4 | 0.3977 | 0.7114 | 0.3684 | 0.7041 |

Las tablas contienen también R², sesgo, diferencias pareadas frente a E1, municipio/estado, Chignahuapan/resto y los cuatro cuartiles previamente definidos. Los resultados no promedian primero predicciones ni RMSE de folds.

La sensibilidad a soporte temporal define soporte bajo mediante el cuartil inferior de número de fechas válidas en entrenamiento, por índice. Se agregan errores cuadrados y absolutos individuales antes de calcular métricas por repetición. No se modifican folds, características ni filtros a partir de esos diagnósticos.

## Diferencias de rendimiento dentro de perfiles

Las parejas comparten perfil y modelo externo; se ordenan por ID ascendente para fijar una orientación reproducible. El error es diferencia observada menos diferencia predicha. El sesgo de parejas depende de esa orientación administrativa, sin interpretación agronómica. Las tablas incluyen diferencias observadas/predichas, correlación, RMSE/MAE, dispersión Y/predicción/incremento, soporte y ganancias/deterioros por perfil. Ninguna pareja de folds externos distintos se usa para atribuir diferenciación a variables.

Con igual peso por perfil se promedian los errores cuadrados individuales dentro de cada perfil y se toma la raíz del promedio de esos MSE. No se promedian RMSE de grupos. Las repeticiones se resumen posteriormente. También se conserva la perspectiva ponderada implícitamente por número de parejas.

RMSE de diferencias con igual peso por perfil:

| experiment | climate_profile | municipality | random | spatial |
| --- | --- | --- | --- | --- |
| F4-E0 | 0.5430 | 0.5189 | 0.6104 | 0.5330 |
| F4-E1 | 0.5442 | 0.5270 | 0.5892 | 0.5388 |
| F4-E2 | 0.5388 | 0.5252 | 0.5833 | 0.5358 |
| F4-E3 | 0.5444 | 0.5347 | 0.5924 | 0.5378 |
| F4-E4 | 0.5367 | 0.5220 | 0.5799 | 0.5377 |

Igual peso por perfil excluyendo parejas con Chignahuapan:

| experiment | climate_profile | municipality | random | spatial |
| --- | --- | --- | --- | --- |
| F4-E0 | 0.4504 | 0.4315 | 0.5156 | 0.4504 |
| F4-E1 | 0.4733 | 0.4558 | 0.5057 | 0.4716 |
| F4-E2 | 0.4691 | 0.4512 | 0.4999 | 0.4680 |
| F4-E3 | 0.4716 | 0.4567 | 0.5096 | 0.4711 |
| F4-E4 | 0.4538 | 0.4440 | 0.4791 | 0.4641 |

El informe de soporte distingue parcelas, perfiles y parejas por repetición. Las parejas comparten parcelas y no son muestras independientes. Excluir Chignahuapan en evaluación no equivale a reentrenar los modelos sin ese municipio. Dispersión mayor no se considera mejora sin reducción del error.

## Decisión sobre ámbitos de utilidad

Ganancias positivas favorecen el candidato; los deterioros se comparan con el margen descriptivo previo de 0.01 t/ha:

| experiment | random_rmse_gain | worst_grouped_rmse_harm | worst_mae_harm | random_equal_profile_pair_gain | random_no_chig_pair_gain | all_metric_margins |
| --- | --- | --- | --- | --- | --- | --- |
| F4-E2 | -0.0008 | 0.0071 | 0.0057 | 0.0059 | 0.0058 | False |
| F4-E3 | -0.0026 | 0.0424 | 0.0217 | -0.0032 | -0.0039 | False |
| F4-E4 | -0.0071 | 0.2136 | 0.2128 | 0.0093 | 0.0266 | False |

Estos márgenes no son pruebas de significación. Los resultados requieren interpretación conjunta de diferenciación local y transferencia, sin declarar superioridad universal por ganar una sola métrica. Las conclusiones específicas y el conjunto mínimo recomendado se documentan en la síntesis de decisiones que acompaña este reporte.

## Integridad, reproducibilidad y limitaciones

La configuración y los hashes de las fuentes están congelados antes del ajuste. Los controles mantienen sus especificaciones originales. Se guardan selección interna, modelos, escalas, coeficientes y las listas de IDs de entrenamiento/validación. No se sobrescriben Familias 1–3, E–M, Familia 4 original ni Champion. La integridad de los artefactos anteriores se verifica nuevamente al finalizar.

La reutilización de etiquetas/folds tras el screening conserva sesgo de descubrimiento, incluso con validación interna correcta. Los perfiles y estados se solapan con la estructura geográfica; el significado físico de LAI y la fase fenológica son reservas materiales. Se necesitan nuevos rendimientos, campañas o geografías para validación independiente. No se recomienda una expansión de combinaciones sobre esta misma muestra.

Reproducción: `python scripts/338_family4_within_profile_complementarity.py`; una versión completada es inmutable. Pruebas: `python -m pytest tests/test_family4_within_profile_complementarity.py -q`. Artefactos: `outputs/modeling/family_4/conditional_yield_response/extensions/within_profile_complementarity/v1`.


## Figuras

![01_redundancy.png](../outputs/modeling/family_4/conditional_yield_response/extensions/within_profile_complementarity/v1/figures/01_redundancy.png)

![02_variance_decomposition.png](../outputs/modeling/family_4/conditional_yield_response/extensions/within_profile_complementarity/v1/figures/02_variance_decomposition.png)

![03_ndvi_dynamics_relief.png](../outputs/modeling/family_4/conditional_yield_response/extensions/within_profile_complementarity/v1/figures/03_ndvi_dynamics_relief.png)

![04_RMSE_protocol.png](../outputs/modeling/family_4/conditional_yield_response/extensions/within_profile_complementarity/v1/figures/04_RMSE_protocol.png)

![05_MAE_protocol.png](../outputs/modeling/family_4/conditional_yield_response/extensions/within_profile_complementarity/v1/figures/05_MAE_protocol.png)

![06_intraprofile.png](../outputs/modeling/family_4/conditional_yield_response/extensions/within_profile_complementarity/v1/figures/06_intraprofile.png)

![07_observed_predicted_pairs.png](../outputs/modeling/family_4/conditional_yield_response/extensions/within_profile_complementarity/v1/figures/07_observed_predicted_pairs.png)

![08_profile_gains.png](../outputs/modeling/family_4/conditional_yield_response/extensions/within_profile_complementarity/v1/figures/08_profile_gains.png)

![09_Chignahuapan.png](../outputs/modeling/family_4/conditional_yield_response/extensions/within_profile_complementarity/v1/figures/09_Chignahuapan.png)

![10_coefficients_support.png](../outputs/modeling/family_4/conditional_yield_response/extensions/within_profile_complementarity/v1/figures/10_coefficients_support.png)