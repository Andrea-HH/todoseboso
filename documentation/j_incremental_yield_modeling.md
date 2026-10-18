> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Sección J — Modelado incremental con topografía y edafología

Se ejecutaron J0–J5 y una sensibilidad J6 Top-3 con Elastic Net, 138 etiquetas y los 65 folds congelados de H. No se reemplazó el Champion ni se generaron predicciones finales para los 59 casos sin etiqueta. Las columnas efectivas y reglas se fijaron antes de entrenar en `configuration.json` y `report/pretraining_audit.md`.

## Reproducción y comparabilidad

J0 reproduce las 1794 predicciones OOF de H1: diferencia máxima 0, tolerancia 1e-8. La comparación se aprobó antes de ejecutar J1–J6. Algoritmo, α=[0.01,0.1,1], L1=[0.1,0.5,0.9], semilla2026 y particiones internas/externas son comunes. Imputación, columnas constantes, escalamiento y vocabulario Top3 se aprenden dentro de cada entrenamiento. Se mantienen las categorías raras; no se seleccionan usando frecuencia del universo completo.

**RMSE t/ha: métricas calculadas sobre cada repetición OOF completa y después promediadas**, no promedio de RMSE de folds:

| experiment | climate_profile | municipality | random | spatial |
| --- | --- | --- | --- | --- |
| J0_RAIN | 0.5444 | 0.6954 | 0.5214 | 0.7348 |
| J1_RAIN_SLOPE | 0.5130 | 0.6755 | 0.5154 | 0.9753 |
| J2_RAIN_TOPO | 0.5502 | 0.8725 | 0.5166 | 0.9035 |
| J3_RAIN_SOIL_GROUP | 0.5633 | 0.9139 | 0.5467 | 0.8932 |
| J4_RAIN_TOPO_SOIL | 0.5412 | 0.9018 | 0.5447 | 0.8711 |
| J5_RAIN_SOIL_FULL | 3.2519 | 0.8769 | 0.5535 | 0.9701 |
| J6_RAIN_SOIL_TOP3 | 3.2519 | 0.8769 | 0.5535 | 0.9701 |

`40_model_comparison.csv` incluye MAE, R², sesgo, desviación entre folds y repeticiones; 41/42 conservan ambos niveles. Los contrastes pareados de RMSE y MAE están en tablas 11–13: positivo=mejora. Los folds/repeticiones se solapan; proporciones de mejoras y dispersiones son diagnósticos, no pruebas independientes ni intervalos de confianza.

## Contribución incremental y decisión

Pendiente reduce RMSE aleatorio 0.52136→0.51542, por perfil 0.54435→0.51302 y municipal 0.69536→0.67549, pero espacial empeora 0.73479→0.97533. Por tanto, pendiente merece conservarse como señal local, sin transferencia espacial demostrada. Altitud adicional no resuelve este deterioro; las representaciones de suelo no mejoran el RMSE aleatorio de lluvia sola.

En aleatorio, el MAE de pendiente es mayor que el de lluvia sola aunque su RMSE sea menor; por eso la mejora no es uniforme entre métricas. La tabla de contrastes incluye ambas. No hay una variante que justifique integración general al Champion bajo los criterios predefinidos. La recomendación es conservar pendiente para investigación local/controlada y reservar suelo como contexto mientras no se resuelvan soporte y transferencia.

| experiment | random_RMSE_improvement | random_repeat_win_fraction | worst_grouped_RMSE_improvement | geographic_margin_pass | classification |
| --- | --- | --- | --- | --- | --- |
| J1_RAIN_SLOPE | 0.0059 | 0.9000 | -0.2405 | False | potential known-region use only; geographic transfer not demonstrated |
| J2_RAIN_TOPO | 0.0048 | 0.9000 | -0.1771 | False | potential known-region use only; geographic transfer not demonstrated |
| J3_RAIN_SOIL_GROUP | -0.0254 | 0.0000 | -0.2186 | False | no consistent incremental support under prespecified criteria |
| J4_RAIN_TOPO_SOIL | -0.0233 | 0.0000 | -0.2064 | False | no consistent incremental support under prespecified criteria |
| J5_RAIN_SOIL_FULL | -0.0321 | 0.0000 | -2.7075 | False | no consistent incremental support under prespecified criteria |
| J6_RAIN_SOIL_TOP3 | -0.0321 | 0.0000 | -2.7075 | False | no consistent incremental support under prespecified criteria |

El margen 0.01t/ha es operativo exploratorio. La clasificación de transferencia exige ausencia de deterioros superiores al margen en perfil, municipio y espacio; mejora aleatoria por sí sola no basta. J3/J4 son las pruebas compactas principales; J5 prueba detalle y dimensionalidad. Antes de integración debe considerarse también soporte de categorías, sesgos extremos, diferenciación intraperfil y reservas cartográficas, sin declarar automáticamente ganador.

## Diferenciación dentro de clima idéntico

Las tablas 15–18 separan dispersión de todas las predicciones OOF de la dispersión de parcelas evaluadas por **el mismo modelo externo**. En aleatorio, parcelas del mismo perfil pueden caer en folds distintos: esa dispersión no acredita valor de nuevas variables. Bajo el protocolo por perfil, todas las parcelas del perfil se evalúan con el mismo ajuste. Correlación observada/predicha se informa solo con al menos cinco etiquetas y variación no nula. Se comparan diferencias de Y entre pares evaluados por el mismo modelo; estas observaciones pareadas tampoco son independientes.

| protocol | experiment | pair_difference_MAE | pair_difference_RMSE |
| --- | --- | --- | --- |
| climate_profile | J0_RAIN | 0.5504 | 0.7993 |
| climate_profile | J1_RAIN_SLOPE | 0.5476 | 0.7764 |
| climate_profile | J2_RAIN_TOPO | 0.5538 | 0.7809 |
| climate_profile | J3_RAIN_SOIL_GROUP | 0.5590 | 0.8063 |
| climate_profile | J4_RAIN_TOPO_SOIL | 0.5553 | 0.7827 |
| climate_profile | J5_RAIN_SOIL_FULL | 0.8906 | 2.2923 |
| climate_profile | J6_RAIN_SOIL_TOP3 | 0.8906 | 2.2923 |
| municipality | J0_RAIN | 0.5579 | 0.8061 |
| municipality | J1_RAIN_SLOPE | 0.5534 | 0.7916 |
| municipality | J2_RAIN_TOPO | 0.5541 | 0.7873 |
| municipality | J3_RAIN_SOIL_GROUP | 0.5742 | 0.8288 |
| municipality | J4_RAIN_TOPO_SOIL | 0.5631 | 0.8079 |
| municipality | J5_RAIN_SOIL_FULL | 0.5590 | 0.7981 |
| municipality | J6_RAIN_SOIL_TOP3 | 0.5590 | 0.7981 |
| random | J0_RAIN | 0.5503 | 0.8045 |
| random | J1_RAIN_SLOPE | 0.5517 | 0.7861 |
| random | J2_RAIN_TOPO | 0.5539 | 0.7879 |
| random | J3_RAIN_SOIL_GROUP | 0.5561 | 0.8089 |
| random | J4_RAIN_TOPO_SOIL | 0.5604 | 0.7962 |
| random | J5_RAIN_SOIL_FULL | 0.5706 | 0.8145 |
| random | J6_RAIN_SOIL_TOP3 | 0.5706 | 0.8145 |
| spatial | J0_RAIN | 0.5597 | 0.8080 |
| spatial | J1_RAIN_SLOPE | 0.5572 | 0.7820 |
| spatial | J2_RAIN_TOPO | 0.5559 | 0.7840 |
| spatial | J3_RAIN_SOIL_GROUP | 0.5586 | 0.8102 |
| spatial | J4_RAIN_TOPO_SOIL | 0.5510 | 0.7827 |
| spatial | J5_RAIN_SOIL_FULL | 0.5663 | 0.7976 |
| spatial | J6_RAIN_SOIL_TOP3 | 0.5663 | 0.7976 |

`10_errors_with_geography.parquet` conserva error por parcela, fold, repetición, protocolo, perfil, municipio e incertidumbre, más cambio pareado de error absoluto frente a J0. Los extremos son categorías descriptivas fijadas antes de entrenar: Y<3, 3<=Y<=5 y Y>5t/ha; no se usaron para seleccionar modelos.

## Chignahuapan y reservas cartográficas

Hay 71 etiquetas locales; sus errores se extraen de las mismas predicciones OOF, sin ajuste local independiente. I encontró aproximadamente 85.8% de SS local dentro de sus perfiles; ello no implicaba que esa variación pudiera predecirse con suelo/topografía. RMSE local comparable:

| experiment | climate_profile | municipality | random | spatial |
| --- | --- | --- | --- | --- |
| J0_RAIN | 0.5653 | 0.5691 | 0.5764 | 0.5638 |
| J1_RAIN_SLOPE | 0.5559 | 0.5555 | 0.5638 | 0.5589 |
| J2_RAIN_TOPO | 0.5598 | 0.9355 | 0.5658 | 0.5765 |
| J3_RAIN_SOIL_GROUP | 0.5678 | 0.9234 | 0.5836 | 0.6071 |
| J4_RAIN_TOPO_SOIL | 0.5526 | 0.9008 | 0.5756 | 0.6472 |
| J5_RAIN_SOIL_FULL | 0.8631 | 0.9090 | 0.5931 | 0.6254 |
| J6_RAIN_SOIL_TOP3 | 0.8631 | 0.9090 | 0.5931 | 0.6254 |

La tabla 25 informa número de etiquetas, RMSE, MAE y sesgo para Chignahuapan, otras regiones, extremos y reservas. Se mantienen **todas** las parcelas en evaluación. Los estratos 50/125/250m son escenarios cartográficos, no probabilidades de exactitud. Las dos claves UM con diferencia lo/hu entre vector y E1402 permanecen identificadas; no se sustituyen calificadores. Un estrato pequeño no ofrece evidencia robusta. No se perturbaron límites ni se fabricaron fracciones: Top3 frente a grupos/composición completa es la sensibilidad de representación justificada.

Las tablas 26/27 detallan específicamente perfiles de Chignahuapan y perfiles con variación cartográfica >5pp, con soporte de cada comparación. Las tablas 28/29 conservan diferencias pareadas de RMSE, MAE y sesgo absoluto por estrato: permite comprobar si una mejora ocurre cerca de límites o también lejos de ellos, sin usar esos estratos para escoger parámetros.

Diagnóstico aleatorio: diferencias positivas favorecen el candidato; N cuenta etiquetas únicas, no repeticiones independientes.

| experiment_candidate | stratum | n | delta_RMSE | delta_MAE | absolute_bias_improvement |
| --- | --- | --- | --- | --- | --- |
| J1_RAIN_SLOPE | away_boundary_125m | 76 | 0.0124 | -0.0024 | 0.0063 |
| J1_RAIN_SLOPE | high_gt5 | 10 | 0.0569 | 0.0485 | 0.0485 |
| J1_RAIN_SLOPE | low_lt3 | 14 | 0.0088 | -0.0093 | -0.0093 |
| J1_RAIN_SLOPE | near_boundary_125m | 62 | -0.0022 | -0.0107 | 0.0163 |
| J3_RAIN_SOIL_GROUP | away_boundary_125m | 76 | -0.0134 | -0.0095 | 0.0067 |
| J3_RAIN_SOIL_GROUP | high_gt5 | 10 | -0.0503 | -0.0571 | -0.0571 |
| J3_RAIN_SOIL_GROUP | low_lt3 | 14 | -0.0826 | -0.0923 | -0.0923 |
| J3_RAIN_SOIL_GROUP | near_boundary_125m | 62 | -0.0404 | -0.0264 | 0.0070 |
| J4_RAIN_TOPO_SOIL | away_boundary_125m | 76 | -0.0014 | -0.0107 | 0.0046 |
| J4_RAIN_TOPO_SOIL | high_gt5 | 10 | -0.0244 | -0.0330 | -0.0330 |
| J4_RAIN_TOPO_SOIL | low_lt3 | 14 | -0.0863 | -0.1185 | -0.1185 |
| J4_RAIN_TOPO_SOIL | near_boundary_125m | 62 | -0.0501 | -0.0425 | 0.0076 |

Los grupos de suelo deterioran RMSE tanto lejos como cerca de límites, con mayor deterioro cerca; no hay una mejora general escondida al excluir parcelas inciertas. La pendiente mejora el sesgo de los rendimientos altos (10 etiquetas), pero no el de los bajos (14), y su mejora local en Chignahuapan no se extiende al conjunto espacial completo. El estrato de discrepancia entre claves tiene solo una etiqueta: no permite conclusiones robustas.

Las fracciones describen unidades oficiales 1:250000 y las coberturas de grupos describen unidades que mencionan el grupo; no porcentajes físicos del suelo asociado. Se preservan 13 unidades con menos de cinco etiquetas y dos exclusivas de predicción como información auditada, sin utilizarlas para filtrar globalmente. La tabla 21 registra unidades ausentes en entrenamiento externo que aparecen en evaluación. Top3 aprende etiquetas nominales dentro del fold, pondera por cobertura y conserva resto y masa desconocida; no convierte claves o puestos en números continuos.

## Coeficientes y redundancia

Tablas 19/20: estabilidad de coeficientes, frecuencias de signo/no-cero y correlaciones de características en TRAIN. La composición completa suma uno y sus columnas dependen del intercepto; Elastic Net tiene penalización L2 estrictamente positiva, que estabiliza esa colinealidad. Los grupos pueden sumar más de uno. El signo depende de regularización y variables incluidas; no mide un efecto causal ni una propiedad de infiltración, pH o laboratorio.

J5 y Top3 presentan un fracaso de estabilidad por perfil: RMSE cercano a 3.25t/ha. En un ajuste externo, `PHpdn-ph+VRpe/2` aparece con pequeñas fracciones en entrenamiento y cobertura alta en evaluación; su valor estandarizado llega a aproximadamente 353 y su contribución a una predicción es cercana a −14.66t/ha. Se conservan las predicciones negativas y todos los errores, sin recortarlos ni cambiar la búsqueda después de observar el resultado. `30_extrapolation_screen.csv` inspecciona los modelos guardados para identificar este tipo de falta de soporte. Un esquema Top3 ponderado no resuelve el problema porque preserva casi las mismas coberturas.

Esto limita **esta representación y pipeline**, no demuestra que el suelo carezca de influencia agronómica. La regularización y la eliminación de columnas constantes no garantizan estabilidad frente a una columna casi ausente en entrenamiento y abundante fuera. Si se reconsidera el suelo completo, primero habría que predefinir otra sensibilidad con soporte mínimo/agrupación aprendida dentro de cada entrenamiento, conservar masa desconocida y volver a evaluar exactamente los mismos protocolos. Esa sensibilidad no se ejecutó ni se utilizó para rescatar resultados de J.

## Contexto de Familia 1 y Champion

Las predicciones del Champion fueron compatibles por ID, repetición y fold con J0 aleatorio. Se recalculan RMSE/MAE/R²/sesgo sobre las mismas OOF completas:

| experiment | RMSE | MAE | R2 | bias_pred_minus_y |
| --- | --- | --- | --- | --- |
| A_CURRENT_CH_H_T | 0.4981 | 0.3589 | 0.6549 | 0.0018 |
| H8_CLIMATE_CURRENT_ORIGINAL | 0.5200 | 0.3693 | 0.6240 | 0.0002 |
| J0_RAIN | 0.5214 | 0.3695 | 0.6220 | -0.0016 |
| J1_RAIN_SLOPE | 0.5154 | 0.3756 | 0.6306 | -0.0026 |
| J2_RAIN_TOPO | 0.5166 | 0.3768 | 0.6289 | -0.0028 |
| J3_RAIN_SOIL_GROUP | 0.5467 | 0.3866 | 0.5843 | 0.0025 |
| J4_RAIN_TOPO_SOIL | 0.5447 | 0.3944 | 0.5874 | -0.0005 |
| J5_RAIN_SOIL_FULL | 0.5535 | 0.3951 | 0.5738 | -0.0019 |
| J6_RAIN_SOIL_TOP3 | 0.5535 | 0.3951 | 0.5738 | -0.0019 |

Climate Current usa el bloque climático original completo; Champion incorpora selección climática y correcciones residuales satelitales/topográficas. Cambian características y arquitectura: sus diferencias no se atribuyen exclusivamente a suelo o topografía. Se reutilizan resultados existentes y no se refitan esos benchmarks. No se extrapola este contraste contextual aleatorio a protocolos geográficos que no tienen predicciones comparables del Champion.

## Productos y siguiente decisión

Matrices objetivo-libres en `data/processed/family_1/j_incremental_geographic_edaphological_yield/v1`, modelos por fold, búsqueda interna, OOF, métricas, errores, diagnósticos locales/intraperfil, incertidumbre y coeficientes en esta carpeta. Figuras muestran RMSE por protocolo, diferencias respecto de J0, observado/predicho, errores espaciales, perfiles, Chignahuapan y límites. Scripts 325 (auditoría) y 326 (ejecución) continúan la numeración existente.

Las clasificaciones operativas son evidencia para una investigación posterior, no un nuevo ganador. Si las mejoras no sobreviven retención municipal/espacial o se concentran en categorías/parcelas inciertas, conservar la variable como señal local/contexto. Una integración residual al Champion y las interacciones lluvia–suelo requieren un experimento separado, pequeño y validado, no se ejecutan en J.
