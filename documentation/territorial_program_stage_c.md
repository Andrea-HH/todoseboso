# Etapa C — Agrupación parcial y representación climática para transferencia

La representación compacta de lluvia con NDVI mejora la validación municipal, pero su ventaja espacial depende de un bloque. Añadir DTR y NDVI a las siete lluvias no combina automáticamente las fortalezas de las dos señales. La jerarquía de interceptos no supera el control estadísticamente emparejado; las ganancias frente al Elastic Net archivado pertenecen principalmente al cambio de regularización.

Los resultados son exploratorios. Se ejecutó únicamente C, después de recuperar A/B y sus decisiones; D permanece sin ejecutar. No se utilizaron la pérdida intraperfil de B, la mezcla 50/50, geología, suelo, nuevos datos topográficos, otros índices, PCA, efectos de pendientes aleatorias ni nuevas interacciones.

## Universo, controles y diseño congelado

Se preservan 197 parcelas, 138 etiquetas TRAIN, 59 PRED sin Y utilizado, 53 perfiles exactos y 43 con etiquetas. Solo 12 perfiles tienen varias etiquetas. Se reutilizaron exactamente los 65 folds externos y sus particiones internas: 50 aleatorios, 5 por perfil, 5 municipales y 5 espaciales. La lista de modelos, transformaciones, grillas, soporte y criterios se congeló antes de ajustar modelos nuevos.

C-T0 reutiliza F4-S1; C-T1 reutiliza F4-S5. Ambos se reprodujeron ajustando sus parámetros archivados y transformaciones en los 130 entrenamientos externos, con tolerancia 1e-10 t/ha. C-H0 reutiliza C-T0 como referencia Elastic Net. Se guardaron 195 modelos de C-T2/T3/T4 y 130 de C-H0M/H1: 325 modelos nuevos y 14,352 predicciones OOF incluyendo tres referencias archivadas. No se entrenó un modelo final sobre todas las etiquetas ni se predijeron las 59 PRED.

La selección interna de C-T conserva la grilla original alpha={0.001,0.01,0.1,1} y l1_ratio={0.1,0.5,0.9}, criterio promedio de RMSE de folds internos. Se ajusta imputación mediana, escala y constantes en cada entrenamiento correspondiente. Las métricas externas se calculan sobre OOF completa por repetición y luego se promedian; no se reconstruyen a partir de media de RMSE de folds.

## C-T: representación y semántica

La matriz contiene: T0 siete lluvias+NDVI; T1 siete lluvias+DTR; T2 siete lluvias+NDVI+DTR; T3 lluvia compacta+NDVI; T4 lluvia compacta+NDVI+DTR. Todo es Elastic Net aditivo, con el mismo procedimiento y sin coordenadas/estado/municipio como predictores.

La representación compacta se congeló en tres cantidades:

1. Total P=sum(Apr,...,Oct), en mm.
2. Proporción temprana E=(Apr+May+Jun)/(P+epsilon), adimensional.
3. Concentración H=sum_m[(P_m/(P+epsilon))²], adimensional.

Epsilon=1e-6 mm, fijo; con todas las precipitaciones cero se obtienen tres ceros. Si falta un mes, los resúmenes deterministas permanecen no disponibles y solo se imputan dentro del entrenamiento. No se seleccionó julio o una ventana por su relación con Y. Los tres resúmenes tienen rango afín completo en TRAIN y no son redundantes linealmente, aunque pueden estar correlacionados. La compactación pierde detalles mensuales; no se interpreta como una descripción suficiente de fenología.

DTR es la columna original `CLIMATE_dtr_mean_std`: desviación temporal muestral, ddof=1, de Tmax−Tmin durante abril–octubre de 2025. Se reprodujo desde la serie mensual original sin sustituirla. No es Tmax media y es constante dentro del perfil. NDVI es el promedio suministrado de mayo. La ventana climática incluye hasta octubre y no corresponde a un pronóstico temprano disponible en mayo.

### Resultados de transferencia

RMSE t/ha:

| experiment | climate_profile | municipality | random | spatial |
| --- | --- | --- | --- | --- |
| C-T0 | 0.52626 | 0.67110 | 0.50483 | 0.73904 |
| C-T1 | 0.56029 | 0.68540 | 0.52412 | 0.60047 |
| C-T2 | 0.53369 | 0.65442 | 0.50638 | 0.75987 |
| C-T3 | 0.52060 | 0.58126 | 0.51158 | 0.67878 |
| C-T4 | 0.52618 | 0.60285 | 0.51375 | 0.67659 |

MAE t/ha:

| experiment | climate_profile | municipality | random | spatial |
| --- | --- | --- | --- | --- |
| C-T0 | 0.38889 | 0.49856 | 0.36411 | 0.57291 |
| C-T1 | 0.40777 | 0.51500 | 0.37360 | 0.44654 |
| C-T2 | 0.39659 | 0.50769 | 0.36682 | 0.55926 |
| C-T3 | 0.39150 | 0.46033 | 0.37495 | 0.53061 |
| C-T4 | 0.39989 | 0.48638 | 0.37663 | 0.52054 |

T2 mejora RMSE municipal frente a T0, pero no MAE municipal y empeora RMSE espacial. Frente a T1, NDVI ayuda aleatoria/perfil/municipio, pero pierde la gran ventaja espacial de DTR. No existe una complementariedad general uniforme.

T3 mejora RMSE municipal 0.67110→0.58126 y MAE 0.49856→0.46033. Fuera de Chignahuapan, RMSE municipal baja 0.7769→0.5819; dentro empeora 0.5530→0.5807. Aleatoria empeora ligeramente RMSE 0.50483→0.51158 y MAE 0.36411→0.37495. El último deterioro supera el margen previo de 0.01 por aproximadamente 0.00085 t/ha; no se modifica retrospectivamente el margen ni se afirma equivalencia estadística.

T4 mejora frente a T2 completo, pero no supera T3 en municipio ni aleatoria. Su pequeña mejora espacial frente a T3 no justifica adoptar DTR automáticamente en el compacto. T1 sigue teniendo el menor RMSE espacial de estas cinco representaciones, con peores métricas aleatorias/por perfil que T0.

### Bloques y extrapolación

Se guardan SSE, n, RMSE/MAE por fold, pérdidas pareadas por parcela y exclusión descriptiva de cada bloque. La ganancia espacial de T3 frente a T0 se concentra en el bloque 3: su contribución de SSE es aproximadamente +15.55, mientras otros dos bloques deterioran. Sin ese bloque, T3 pasa a empeorar RMSE espacial en +0.0324 y MAE en +0.0219. La ventaja municipal de T3 mantiene menor RMSE al omitir cualquiera de los cinco folds, aunque el MAE no mejora en todas esas sensibilidades. Por tanto su ámbito más defendible es municipal, no transferencia espacial general.

La ganancia espacial de T1 también está dominada por el bloque 3: aproximadamente +33.85 SSE, con deterioros en los otros bloques salvo el 2. Esto acota la fortaleza térmica anterior. No se cambiaron particiones ni se eligieron regiones favorables para la conclusión.

Los indicadores de soporte usan solo X de outer-train: límites marginales de DTR/total/NDVI, proximidad dentro del 5% de rango y distancia al vecino de entrenamiento más próximo en escala estandarizada de esas tres variables. No activan modelos distintos ni usan Y. Estar dentro de los rangos marginales no garantiza soporte conjunto. Se conserva cada indicador por parcela junto con métricas de soporte, para distinguir las mejoras en interpolación/extrapolación. La caracterización regional y correlaciones entre DTR, lluvia y NDVI son descriptivas, no causales.

## C-H: controles estadísticos y modelo jerárquico

Los efectos fijos son idénticos en H0/H0M/H1: siete lluvias y NDVI. No se incluyó LAI en este primer contraste. H0 es el Elastic Net archivado; H0M es el control Gaussian GLS/Ridge sin varianza de perfil; H1 añade un intercepto aleatorio. **La comparación H1−H0M separa el efecto jerárquico; H0M−H0 cuantifica el cambio de regularización/ajuste.** Una mejora H1−H0 no puede atribuirse directamente a la jerarquía.

Modelo: y=A theta+Z u+epsilon, u_g~N(0,tau²), epsilon~N(0,sigma²), independientes bajo el modelo. La independencia de u respecto de clima es una hipótesis, no un hecho comprobado. La covarianza marginal es sigma² R, R_g=I+r·11', r=tau²/sigma². No se usan interceptos de grupo como efectos fijos libres.

Se utiliza blanqueo exacto de cada bloque, R_g^(-1/2)=I−[1−(1+n_g r)^(-1/2)]P_g, donde P_g proyecta sobre su media. El ajuste de efectos fijos minimiza ||W(y−A theta)||²/(2n)+alpha||beta||²/2, intercepto no penalizado, con solver Ridge estándar alpha_solver=n·alpha. Un procedimiento cerrado evita problemas de optimización iterativa, sin un sistema de inferencia complejo. H0M es exactamente r=0 en la misma formulación.

Alpha conserva cuatro valores predefinidos; r se regulariza mediante grilla {0,0.1,0.3,1,3}, seleccionada exclusivamente por RMSE interno. Empates priorizan r menor y mayor alpha. No se presenta r como un estimador ML continuo identificado: es un hiperparámetro de varianza elegido por CV. Sigma² se estima por SSE blanqueado/n, ML condicional plug-in en los efectos fijos ajustados; tau²=r sigma². La razón tau²/(tau²+sigma²)=r/(1+r) describe ese modelo, no variación causal explicada. No se amplió la grilla al observar resultados.

Para documentar incertidumbre de efectos fijos se utiliza la formulación Gaussiana de trabajo equivalente a la penalización, beta|sigma,alpha~N(0,sigma²/(n alpha) I), con intercepto plano. Su covarianza condicional es sigma²[A'R^-1 A+n alpha D]^-1. Alpha incluye sensibilidad de regularización predefinida; las escalas del prior se expresan en t/ha por unidad de predictor estandarizado. Sigma/r/alpha se mantienen en sus estimaciones plug-in: los intervalos no integran incertidumbre de selección o estimación de varianzas y no son inferencia bayesiana completa.

### Predicción conocida y nueva

Para un perfil presente en entrenamiento, uhat_g=r/(1+n_g r)·sum_g(y−A thetahat), calculado exclusivamente con sus etiquetas de entrenamiento. La varianza condicional de u, dada theta e hiperparámetros, es sigma² r/(1+n_g r). Su relación con la incertidumbre de theta se conserva usando el vector predictivo ajustado h=a_new−[r/(1+n_g r)]sum_g(a_train).

Para un perfil nuevo, uhat=0. La varianza predictiva añade sigma²+tau² además de la covarianza de efectos fijos. No se actualiza u con Y retenido. Los intervalos Gaussianos nominales de 90% son de trabajo y requieren evaluar cobertura OOF. En r=0 se recupera exactamente el control sin interceptos aleatorios.

Para dos parcelas con el mismo perfil y el mismo modelo externo, el intercepto de grupo y la contribución climática compartida se cancelan. La diferencia predicha es gamma·(NDVI_i−NDVI_j). La jerarquía puede modificar gamma durante el ajuste, pero desplazar el nivel de perfil no produce por sí solo diferenciación parcelaria. Esta identidad se verificó numéricamente.

### Resultados emparejados

| experiment | climate_profile | municipality | random | spatial |
| --- | --- | --- | --- | --- |
| C-H0 | 0.52626 | 0.67110 | 0.50483 | 0.73904 |
| C-H0M | 0.51777 | 0.63945 | 0.50945 | 0.67244 |
| C-H1 | 0.51873 | 0.63945 | 0.51341 | 0.69096 |

| experiment | climate_profile | municipality | random | spatial |
| --- | --- | --- | --- | --- |
| C-H0 | 0.38889 | 0.49856 | 0.36411 | 0.57291 |
| C-H0M | 0.38212 | 0.47859 | 0.36840 | 0.52226 |
| C-H1 | 0.38390 | 0.47859 | 0.37102 | 0.54290 |

H1 no supera H0M en RMSE global de ningún protocolo: empeora aleatoria y espacial, empata municipio y pierde ligeramente por perfil. H0M tiene mejores métricas regionales que H0, lo que respalda investigar regularización L2 sencilla antes de atribuir ventajas a estructura jerárquica.

Predicciones condicionales y marginales sobre sus subconjuntos compatibles:

| experiment | protocol | stratum | n | RMSE | MAE |
| --- | --- | --- | --- | --- | --- |
| C-H0M | climate_profile | new_profile | 138.00000 | 0.51777 | 0.38212 |
| C-H0M | municipality | known_profile | 43.00000 | 0.49239 | 0.35596 |
| C-H0M | municipality | new_profile | 95.00000 | 0.69587 | 0.53409 |
| C-H0M | random | known_profile | 105.50000 | 0.50402 | 0.35431 |
| C-H0M | random | new_profile | 32.50000 | 0.52703 | 0.41445 |
| C-H0M | spatial | known_profile | 37.00000 | 0.51847 | 0.34001 |
| C-H0M | spatial | new_profile | 101.00000 | 0.72065 | 0.58903 |
| C-H1 | climate_profile | new_profile | 138.00000 | 0.51873 | 0.38390 |
| C-H1 | municipality | known_profile | 43.00000 | 0.49239 | 0.35596 |
| C-H1 | municipality | new_profile | 95.00000 | 0.69587 | 0.53409 |
| C-H1 | random | known_profile | 105.50000 | 0.50674 | 0.35608 |
| C-H1 | random | new_profile | 32.50000 | 0.53481 | 0.41978 |
| C-H1 | spatial | known_profile | 37.00000 | 0.50742 | 0.33238 |
| C-H1 | spatial | new_profile | 101.00000 | 0.74700 | 0.62003 |

En aleatoria hay en promedio 105.5 parcelas de perfiles conocidos y 32.5 de perfiles nuevos. Por perfil, todas las 138 son nuevas; en municipio, 43 conocidas/95 nuevas; en espacio, 37/101. Estos escenarios no son intercambiables. H1 tampoco mejora el nivel medio de perfil de forma general frente a H0M; se conservan errores por perfil y RMSE de medias.

R=0 se seleccionó en 36/50 ajustes aleatorios, 4/5 por perfil, 5/5 municipales y 3/5 espaciales. Esto no prueba que no exista heterogeneidad real; indica falta de utilidad estable de la estructura bajo este modelo y datos. Solo 12 grupos repetidos, con dos dominantes, ofrecen soporte limitado para separar sigma²/tau² y efectos climáticos entre grupos. Las estimaciones de varianza quedan condicionadas a regularización/grilla y son sensibles al entrenamiento; no hay identificación convincente de un componente aleatorio no nulo general.

Cobertura de intervalos de H1, nominal 90%:

| protocol | stratum | n | coverage | mean_width |
| --- | --- | --- | --- | --- |
| climate_profile | new_profile | 138.00000 | 0.89130 | 1.65079 |
| municipality | known_profile | 43.00000 | 0.93023 | 1.47268 |
| municipality | new_profile | 95.00000 | 0.77895 | 1.75069 |
| random | known_profile | 105.50000 | 0.92989 | 1.60595 |
| random | new_profile | 32.50000 | 0.84313 | 1.69220 |
| spatial | known_profile | 37.00000 | 0.94595 | 1.58342 |
| spatial | new_profile | 101.00000 | 0.93069 | 2.67615 |

La cobertura de nuevos perfiles municipales es aproximadamente 77.9%, pese al nominal 90%; no deben declararse calibrados. La cobertura espacial nueva alcanza aproximadamente 93.1% con amplitud media 2.68 t/ha, más amplia. Una cobertura alta obtenida con mayor ancho no es automáticamente una mejor herramienta operacional. El método reconoce varianza de perfiles nuevos, pero no elimina cambio de dominio ni incertidumbre de hiperparámetros omitida.

## Diferencias parcelarias y decisiones

RMSE de diferencias con igual peso por perfil, pares del mismo modelo externo:

| experiment | climate_profile | municipality | random | spatial |
| --- | --- | --- | --- | --- |
| C-H0 | 0.54417 | 0.52701 | 0.58920 | 0.53877 |
| C-H0M | 0.53846 | 0.52070 | 0.59062 | 0.53069 |
| C-H1 | 0.53852 | 0.52070 | 0.59033 | 0.53046 |
| C-T0 | 0.54417 | 0.52701 | 0.58920 | 0.53877 |
| C-T1 | 0.54299 | 0.51890 | 0.61041 | 0.53303 |
| C-T2 | 0.53758 | 0.52059 | 0.59056 | 0.53924 |
| C-T3 | 0.54789 | 0.52099 | 0.58995 | 0.54015 |
| C-T4 | 0.54533 | 0.52392 | 0.58794 | 0.53971 |

Se mantienen soporte por parcela/perfil/parejas y perspectiva sin Chignahuapan. Las parejas solapadas y los cinco bloques no son réplicas independientes. Q1/Q4, municipio/estado, distribución de predicciones, coeficientes y parámetros están en tablas. No se usaron esos diagnósticos para redefinir candidatos.

| model | decision | reason |
| --- | --- | --- |
| C-T2 | no conservar como alternativa general | añadir DTR a T0 no mantiene transferencia espacial; añadir NDVI a T1 pierde su ventaja espacial |
| C-T3 | candidato exploratorio municipal | mejora municipal y MAE, pero ventaja espacial depende del bloque3; MAE aleatoria excede ligeramente margen0.01 |
| C-T4 | conservar solo como contraste de compactación | mejora frente a T2, pero DTR no supera la versión compacta sencilla T3 de forma general |
| C-H0M | conservar control regularizado no jerárquico | parte de mejora regional frente a EN pertenece a L2/ajuste emparejado, no a efectos de perfil |
| C-H1 | descartar complejidad jerárquica bajo este diseño | ratio frecuentemente0; no supera control emparejado en métricas globales, con varianza débilmente identificada |

## Respuestas de la Etapa C

1. Agrupación parcial: no hay mejora general sobre el control matched, incluso para perfiles conocidos aleatorios.
2. Perfiles nuevos: no se conserva una ventaja jerárquica; municipio empata porque r=0 y espacio nuevo empeora.
3. Nivel o diferencias: cambios de nivel no demuestran diferenciación; las mejoras frente a EN pertenecen principalmente a regularización.
4. Varianza: con 12 grupos repetidos y mucha selección de r=0, no se identifica de forma convincente un componente general no nulo.
5. DTR/NDVI: sí describen escalas distintas, pero T2 no reúne una ventaja predictiva uniforme.
6. Bloques: la principal mejora espacial térmica y compacta depende del bloque 3; no es robusta a omitirlo.
7. Compactación: T3 mejora especialmente municipio; su mejora espacial tiene una limitación regional fuerte.
8. Chignahuapan: T3/T4 mejoran o mantienen algunos errores aleatorios/espaciales pero empeoran municipio local; las ganancias municipales son mayores fuera.
9. Fuera: T3 reduce notablemente RMSE municipal fuera de Chignahuapan; H1 no ofrece una mejora general en perfiles nuevos.
10. Validación independiente: priorizar la representación compacta T3 para transferencia municipal y el control L2 simple como comparación parsimoniosa; conservar T1 solo para comprobar si su fortaleza espacial se repite en otras regiones. No promover jerarquía ni un ganador universal.

## Reproducción y límites

`python scripts/344_stage_c_transfer_and_hierarchy.py` ejecuta C-T y su auditoría antes de C-H. Los modelos, transformaciones, controles, CV interna, IDs, coeficientes, grupos/effectos, varianzas y componentes predictivos quedan versionados. No se suspendió por problemas numéricos: las ecuaciones normales y matrices positivas se verifican; la limitación principal es empírica e identificabilidad de varianzas.

Todas las conclusiones siguen siendo exploratorias por reutilización de las mismas 138 etiquetas. Nuevas campañas/regiones son necesarias para confirmación independiente. Las fuentes y los resultados anteriores se verifican por SHA-256. Etapa D no se ejecutó y no se cambió Champion, mezcla, A/B, familias anteriores ni etiquetas.


## Figuras

![hierarchy_MAE.png](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_c/figures/hierarchy_MAE.png)

![hierarchy_RMSE.png](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_c/figures/hierarchy_RMSE.png)

![hierarchy_variances.png](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_c/figures/hierarchy_variances.png)

![interval_coverage.png](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_c/figures/interval_coverage.png)

![local_differences.png](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_c/figures/local_differences.png)

![spatial_block_contributions.png](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_c/figures/spatial_block_contributions.png)

![transfer_MAE.png](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_c/figures/transfer_MAE.png)

![transfer_RMSE.png](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_c/figures/transfer_RMSE.png)

## Integridad final y sensibilidad de perfiles dominantes

13 pruebas matemáticas y de integración pasaron. Se reprodujeron los 325 modelos nuevos y los controles originales. La siguiente sensibilidad utiliza exclusivamente la disponibilidad de perfiles 4/24 en los entrenamientos externos ya congelados; es descriptiva y está confundida con composición territorial del fold. No constituye un experimento causal de eliminar perfiles ni motivó cambios de modelos.

| experiment | protocol | dominant_profiles_available | n_models | mean_ratio | mean_tau2 | mean_sigma2 |
| --- | --- | --- | --- | --- | --- | --- |
| C-H0M | climate_profile | True | 5 | 0.00000 | 0.00000 | 0.22898 |
| C-H0M | municipality | True | 5 | 0.00000 | 0.00000 | 0.22164 |
| C-H0M | random | True | 50 | 0.00000 | 0.00000 | 0.22708 |
| C-H0M | spatial | True | 5 | 0.00000 | 0.00000 | 0.24815 |
| C-H1 | climate_profile | True | 5 | 0.02000 | 0.00385 | 0.22724 |
| C-H1 | municipality | True | 5 | 0.00000 | 0.00000 | 0.22164 |
| C-H1 | random | True | 50 | 0.06600 | 0.01332 | 0.22376 |
| C-H1 | spatial | True | 5 | 0.66000 | 0.10767 | 0.21395 |
