> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Predicciones de los tres ganadores y validación estadística

Entrega autorizada el 15 de octubre de 2026: **C-T3, modelo TOP20/TOP15 y EQUAL3**, con 59 predicciones por modelo. Se ajustaron seis componentes finales con las 138 etiquetas TRAIN; no se usaron rendimientos de PRED. Los archivos y modelos históricos permanecen intactos.

## Archivos principales

- [Excel: 59 predicciones, métricas e intervalos, comparaciones y soporte](../outputs/modeling/winner_predictions/v1/predicciones_ganadores_59.xlsx).
- [CSV con predicciones y descomposición](../outputs/modeling/winner_predictions/v1/tables/predictions59.csv).
- [Comparaciones estadísticas pareadas](../outputs/modeling/winner_predictions/v1/statistics/paired_tests_and_intervals.csv).
- [Métricas e intervalos de remuestreo](../outputs/modeling/winner_predictions/v1/statistics/metrics_cluster_intervals.csv).
- [Figura de predicciones y validación](../outputs/modeling/winner_predictions/v1/statistics/predictions_and_validation.png).

Las unidades son t/ha. No hay error observable para las 59 parcelas porque no tenemos sus rendimientos. La diferencia entre los tres modelos es un indicador de desacuerdo, no un intervalo predictivo ni una estimación calibrada de incertidumbre.

## Consolidación final, congelada antes de predecir

Se conserva la arquitectura de cada ganador. Para evitar elegir configuraciones mirando PRED se fijó el vector completo de hiperparámetros más frecuente entre sus 50 ajustes aleatorios archivados; empate por orden JSON. Esto es una regla de consolidación de modelos finales definida ahora, no un nuevo modelo con prueba independiente. Las métricas posteriores proceden de las OOF originales, no del ajuste final de las 138 etiquetas.

- **C-T3:** las cuatro variables originales y su ConditionalFeatures original, incluido el piso de escala de NDVI. Consenso alpha .01, l1_ratio .1; 34/50 ajustes aleatorios habían elegido ese par. Ajuste final sobre 138 TRAIN.
- **GPR F5-01:** cuatro variables originales, Matérn 3/2 por bloques y límites/reinicios originales; optimización LML exclusivamente con TRAIN.
- **CatBoost F7-00:** compact4, 300 árboles, profundidad 2, learning_rate .03 y l2_leaf_reg 30; combinación modal en 19/50 ajustes. Tratamiento de datos y demás parámetros originales, sin early stopping.
- **EQUAL3:** promedio fijo de un tercio de los tres componentes anteriores, sin intercepto ni pesos aprendidos.
- **modelo TOP20/TOP15 A_CURRENT_CH_H_T:** clima TOP20 Elastic Net + corrección de historia TOP15 XGBoost + corrección topográfica Ridge de 25 entradas. Cada vector de hiperparámetros se consolida por la misma regla modal. Se seleccionan las 20 variables climáticas con TRAIN y las 15 históricas con el target residual TRAIN, conservando el ranking Spearman y los candidatos originales.

Para consolidar modelo TOP20/TOP15, el target histórico es y menos la media de las diez predicciones OOF archivadas de TOP20_ENET_BASE. El target topográfico es y menos la media de las diez predicciones OOF estrictas archivadas de Climate+History. Ambos targets se guardaron por parcela. No se sustituyeron por residuos de predicciones ajustadas sobre la propia etiqueta. Las etapas finales se reajustan con las 138 parcelas; el cambio entre bases cross-fitted y bases finales persiste. Esta receta final de consolidación no dispone de una evaluación independiente nueva: las OOF evalúan los procedimientos archivados, no garantizan el rendimiento de este ajuste particular ni de una nueva campaña.

## Resultados OOF compatibles

Métricas de OOF completas por repetición. Aleatoria promedia diez repeticiones sobre las mismas 138 parcelas. No se promedian errores de folds ni se evalúa el promedio de predicciones por parcela como si fuera la métrica original.

| Modelo | Protocolo | RMSE | MAE | R2 |
|---|---|---:|---:|---:|
| C-T3 | Aleatoria | .511582 | .374948 | .636069 |
| modelo TOP20/TOP15 | Aleatoria | .498127 | .358869 | .654933 |
| EQUAL3 | Aleatoria | .498159 | .360413 | .654931 |
| C-T3 | Perfil | .520604 | .391501 | .623166 |
| EQUAL3 | Perfil | .497859 | .371951 | .655375 |
| C-T3 | Municipal | .581259 | .460329 | .530242 |
| EQUAL3 | Municipal | .527660 | .387943 | .612881 |
| C-T3 | Espacial | .678778 | .530612 | .359394 |
| EQUAL3 | Espacial | .670948 | .507975 | .374088 |

modelo TOP20/TOP15 solo tiene OOF exactas compatibles aleatorias en esta entrega. No se inventan métricas por perfil, municipio o espacio ni se usa otro modelo como sustituto.

## Qué validación estadística se realizó

1. **5,000 remuestreos pareados por conglomerados**, semilla 2026. Para aleatoria y perfil, la unidad es el perfil climático (43 en TRAIN); municipal usa los nueve municipios, espacial los cinco bloques. Se conservan juntas las parcelas de un conglomerado y sus repeticiones; estas no se convierten en 1,380 muestras independientes.
2. Intervalos percentiles descriptivos del 95% para RMSE, MAE, sesgo, R2 y diferencias pareadas. Se emplean las mismas muestras para ambos modelos en cada contraste.
3. **Cambio de signo pareado por conglomerado de la diferencia de pérdida cuadrática**, después de promediar las pérdidas de cada parcela entre repeticiones. Se enumeran todos los signos para nueve municipios y cinco bloques; para 43 perfiles se usan 20,000 asignaciones y corrección Monte Carlo.
4. Ajuste **Holm para las seis comparaciones disponibles**: tres parejas aleatorias y C-T3/EQUAL3 en los otros tres protocolos.

La prueba se refiere a pérdida cuadrática media, no al p-valor de cada coeficiente Elastic Net ni a una prueba causal. El cambio de signos requiere una hipótesis de simetría/intercambiabilidad entre conglomerados; no es un experimento aleatorizado. El remuestreo es condicional a predicciones congeladas y omite incertidumbre de reentrenamiento y de selección de modelos. Los perfiles pueden conservar dependencia espacial entre sí. Holm cubre estas seis comparaciones, no toda la búsqueda histórica del proyecto.

### Diferencias pareadas

Delta RMSE = modelo A menos modelo B; positivo favorece B. Los intervalos son de la diferencia, no una comparación visual de solapamiento de intervalos individuales.

| Protocolo | A frente a B | Delta RMSE | Intervalo 95% | p pérdida cuadrática | p Holm |
|---|---|---:|---|---:|---:|
| Aleatoria | C-T3 − modelo TOP20/TOP15 | .013455 | [-.006221, .059848] | .235538 | .706615 |
| Aleatoria | C-T3 − EQUAL3 | .013423 | [-.002760, .052278] | .140043 | .683594 |
| Aleatoria | modelo TOP20/TOP15 − EQUAL3 | -.000032 | [-.015723, .013404] | .999850 | 1.000000 |
| Perfil | C-T3 − EQUAL3 | .022745 | [.003491, .064443] | .027749 | .166492 |
| Municipal | C-T3 − EQUAL3 | .053599 | [.000288, .164710] | .136719 | .683594 |
| Espacial | C-T3 − EQUAL3 | .007830 | [-.037135, .110794] | .687500 | 1.000000 |

**Ninguna comparación demuestra superioridad al nivel .05 después de Holm**, incluso bajo estas hipótesis exploratorias. Esto no prueba equivalencia. modelo TOP20/TOP15 y EQUAL3 están prácticamente empatados en aleatoria; la diferencia puntual entre sus RMSE es 0.000032 t/ha, aproximadamente 0.032 kg/ha.

Por perfil existe una señal favorable a EQUAL3 sin ajustar multiplicidad, pero no resiste Holm. El intervalo municipal bootstrap queda apenas por encima de cero mientras la prueba por signos no es significativa: son procedimientos con supuestos distintos y solo nueve conglomerados, no evidencias intercambiables. Con cinco bloques, el p bilateral exacto mínimo posible es .0625; la potencia espacial es muy limitada. Estas pruebas no sustituyen etiquetas de campañas o territorios independientes.

Los intervalos RMSE aleatorios descriptivos son C-T3 [.433771,.554838], modelo TOP20/TOP15 [.394055,.544650] y EQUAL3 [.396863,.543095]. No son intervalos del rendimiento de una parcela PRED.

Se guardan además métricas regionales y sensibilidades al omitir estados, municipios o folds, sin reajustar modelos. En zonas con una sola etiqueta o rendimiento constante, R2 es indefinido y se conserva como vacío; las advertencias `Mean of empty slice` del resumen corresponden a esos casos, no a predicciones ausentes.

## Las 59 predicciones

| Modelo | Media | Mínimo | Máximo |
|---|---:|---:|---:|
| C-T3 | 3.919944 | 2.487759 | 4.837781 |
| modelo TOP20/TOP15 | 3.902307 | 2.677401 | 5.173083 |
| EQUAL3 | 3.939851 | 2.779711 | 4.756990 |

Todas son finitas; no se aplicó clipping, redondeo para modelar ni correcciones municipales. El CSV conserva precisión numérica y descompone modelo TOP20/TOP15 en clima y sus dos correcciones, y EQUAL3 en sus componentes.

Desacuerdo medio máximo-mínimo entre ganadores: .181831 t/ha; máximo .672283. Casos con mayor diferencia:

| Parcela | Municipio | C-T3 | modelo TOP20/TOP15 | EQUAL3 | Dispersión |
|---|---|---:|---:|---:|---:|
| AGC_120 | Nanacamilpa de Mariano Arista | 3.478296 | 2.954079 | 3.626362 | .672283 |
| AGC_142 | Chignahuapan | 4.648608 | 5.173083 | 4.585098 | .587985 |
| AGC_003 | Singuilucan | 3.664839 | 3.100716 | 3.412237 | .564124 |
| AGC_129 | Singuilucan | 3.740793 | 3.265558 | 3.693516 | .475235 |
| AGC_118 | Singuilucan | 3.081090 | 2.677401 | 3.145974 | .468572 |

Una parcela PRED está fuera del rango marginal TRAIN de alguna entrada compact4; doce lo están respecto a alguna entrada de modelo TOP20/TOP15. Ninguna presenta valores faltantes en las entradas finales utilizadas. Los conteos dependen del número de variables y no son una comparación justa de incertidumbre entre arquitecturas; estar dentro de los rangos tampoco garantiza soporte conjunto. Se entregan las columnas exactas afectadas en `prediction_support.csv`.

## Recomendación y verificación

Conservar las tres salidas para revisión. C-T3 mantiene su ventaja de sencillez; EQUAL3 tiene mejores puntos estimados que C-T3 en los cuatro protocolos y modelo TOP20/TOP15 un resultado aleatorio casi idéntico a EQUAL3. Las pruebas actuales no justifican declarar un ganador estadístico único ni programar reglas por municipio a partir de estas predicciones.

Se validaron IDs, exclusión TRAIN/PRED, etiquetas y folds contra los archivos congelados. Pasaron cuatro pruebas, incluida la que comprueba que cinco conglomerados no permiten p bilateral exacto menor de .05. Se recargaron los modelos finales y las 177 predicciones ganadoras se reprodujeron exactamente. Los seis componentes finales no emitieron advertencias de ajuste; la optimización elegida del GPR convergió y no alcanzó límites. Se registraron advertencias operacionales de fragmentación de pandas e Intel/LLVM OpenMP, sin discrepancias de reproducción.

El primer intento se detuvo antes de ajustar o predecir por serialización de conteos numpy; quedó preservado como `v1_initial_unexecuted`. La versión v1 incluye la corrección a enteros Python, diseño congelado anterior a los ajustes y manifest completo. No se sobrescribió ningún ganador histórico ni se promovió un nuevo líder.

Modelos: `outputs/modeling/winner_predictions/v1/models/final_winners_train138.joblib`. Diseño, frecuencias de consenso, diagnósticos numéricos y reproducción: `audit/` y `frozen_design.json`. Scripts 411/412; utilidades en `src/winner_delivery.py`.
