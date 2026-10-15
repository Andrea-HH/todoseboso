# K — Standalone and Residual Geographic–Edaphological Modeling

## K.1 — Representación congelada

S1 primaria: diez coberturas de unidades que mencionan grupos oficiales, conservadas en [0,1]; no son proporciones físicas de grupos asociados. S2 única sensibilidad: unidades con soporte de tres/cinco parcelas aprendido dentro de cada entrenamiento, más Other. S3 y S4 se describen sin buscar rendimiento. Auditoría y pruebas en [K.1](k1_edaphological_redesign.md). Sin modificación de E–J ni Champion.

## K.2/K.3 — Comparación controlada

RMSE t/ha, primero métricas en los 138 OOF completos de cada repetición, después promedio; no promedio de RMSE por fold.

| experiment | climate_profile | municipality | random | spatial |
| --- | --- | --- | --- | --- |
| J0_RAIN | 0.5444 | 0.6954 | 0.5214 | 0.7348 |
| J1_RAIN_SLOPE | 0.5130 | 0.6755 | 0.5154 | 0.9753 |
| J2_RAIN_TOPO | 0.5502 | 0.8725 | 0.5166 | 0.9035 |
| J3_RAIN_SOIL_GROUP | 0.5633 | 0.9139 | 0.5467 | 0.8932 |
| J4_RAIN_TOPO_SOIL | 0.5412 | 0.9018 | 0.5447 | 0.8711 |
| K0_MEAN | 0.9368 | 1.1518 | 0.8560 | 1.0276 |
| K1_SLOPE_ONLY | 0.9572 | 1.1029 | 0.8176 | 1.0039 |
| K2_TOPO_ONLY | 0.9771 | 1.1399 | 0.8105 | 1.0826 |
| K3_SOIL_ONLY | 0.7444 | 1.0343 | 0.6822 | 1.0347 |
| K3_SOIL_ONLY_ALT | 0.5759 | 0.8402 | 0.5561 | 1.0782 |
| K4_TOPO_SOIL | 0.6207 | 1.0172 | 0.6053 | 0.9447 |
| K5_RAIN_RESID_SLOPE | 0.5376 | 0.6961 | 0.5162 | 0.7139 |
| K6_RAIN_RESID_TOPO | 0.5407 | 0.7067 | 0.5175 | 0.7279 |
| K7_RAIN_RESID_SOIL | 0.5532 | 0.7410 | 0.5223 | 0.7344 |
| K8_RAIN_RESID_TOPO_SOIL | 0.5471 | 0.7142 | 0.5213 | 0.7339 |
| KA_RAIN_SLOPE_MATCHED | 0.5130 | 0.6826 | 0.5165 | 0.9643 |
| KA_RAIN_SOIL_STABLE | 0.5582 | 0.7326 | 0.5294 | 1.0027 |
| KA_RAIN_TOPO_MATCHED | 0.5502 | 0.8725 | 0.5171 | 0.8907 |
| KA_RAIN_TOPO_SOIL_STABLE | 0.5450 | 0.9055 | 0.5289 | 0.9671 |

Modelos independientes se comparan primariamente con K0, media aprendida en entrenamiento. Controles KA usan exactamente las mismas variables y escalas de suelo que los correctores K7/K8. KA_RAIN_SLOPE_MATCHED y KA_RAIN_TOPO_MATCHED aíslan arquitectura con la misma grilla K; J1/J2 siguen como referencia histórica. K agrega alpha .001 por coherencia con suelo sin z-score. Comparaciones pareadas y todos los parámetros en tablas 21/22 y 12/14.

Cada predicción climática externa reproduce J0 (tolerancia 1e-8). Los objetivos residuales son predicciones cruzadas únicamente dentro de outer-train; la selección climática de cada submodelo también excluye la etiqueta retenida. La validación interna evalúa el sistema completo con su propio cross-fitting más profundo. ETA=0,.25,.5,1 se elige internamente. Las divisiones profundas conservan perfiles/municipios/grupos espaciales; solo aleatorio usa KFold. Proveniencia de IDs en tabla16 y residuos cruzados en tabla15.

## Geografía, intraperfil y Chignahuapan

| experiment | protocol | n | RMSE | MAE | bias |
| --- | --- | --- | --- | --- | --- |
| J0_RAIN | climate_profile | 71 | 0.5653 | 0.3862 | -0.0195 |
| J1_RAIN_SLOPE | climate_profile | 71 | 0.5559 | 0.4122 | -0.0401 |
| J2_RAIN_TOPO | climate_profile | 71 | 0.5598 | 0.4209 | -0.0217 |
| J3_RAIN_SOIL_GROUP | climate_profile | 71 | 0.5678 | 0.3806 | -0.0170 |
| J4_RAIN_TOPO_SOIL | climate_profile | 71 | 0.5526 | 0.3937 | -0.0194 |
| K0_MEAN | climate_profile | 71 | 0.8835 | 0.7773 | -0.6483 |
| K1_SLOPE_ONLY | climate_profile | 71 | 0.9531 | 0.8574 | -0.7353 |
| K2_TOPO_ONLY | climate_profile | 71 | 0.9615 | 0.8685 | -0.7646 |
| K3_SOIL_ONLY | climate_profile | 71 | 0.7289 | 0.5115 | -0.2125 |
| K3_SOIL_ONLY_ALT | climate_profile | 71 | 0.5780 | 0.4064 | -0.0450 |
| K4_TOPO_SOIL | climate_profile | 71 | 0.6222 | 0.4526 | -0.1427 |
| K5_RAIN_RESID_SLOPE | climate_profile | 71 | 0.5549 | 0.4092 | 0.0019 |
| K6_RAIN_RESID_TOPO | climate_profile | 71 | 0.5584 | 0.3980 | 0.0027 |
| K7_RAIN_RESID_SOIL | climate_profile | 71 | 0.5675 | 0.3921 | -0.0098 |
| K8_RAIN_RESID_TOPO_SOIL | climate_profile | 71 | 0.5597 | 0.3878 | -0.0099 |
| KA_RAIN_SLOPE_MATCHED | climate_profile | 71 | 0.5559 | 0.4122 | -0.0401 |
| KA_RAIN_SOIL_STABLE | climate_profile | 71 | 0.5683 | 0.3863 | 0.0016 |
| KA_RAIN_TOPO_MATCHED | climate_profile | 71 | 0.5598 | 0.4209 | -0.0217 |
| KA_RAIN_TOPO_SOIL_STABLE | climate_profile | 71 | 0.5540 | 0.4070 | -0.0276 |
| J0_RAIN | municipality | 71 | 0.5691 | 0.3748 | 0.0778 |
| J1_RAIN_SLOPE | municipality | 71 | 0.5555 | 0.3788 | 0.0494 |
| J2_RAIN_TOPO | municipality | 71 | 0.9355 | 0.8518 | -0.7555 |
| J3_RAIN_SOIL_GROUP | municipality | 71 | 0.9234 | 0.8099 | -0.6840 |
| J4_RAIN_TOPO_SOIL | municipality | 71 | 0.9008 | 0.7945 | -0.6771 |
| K0_MEAN | municipality | 71 | 1.2217 | 1.1423 | -1.0751 |
| K1_SLOPE_ONLY | municipality | 71 | 1.1743 | 1.0823 | -1.0273 |
| K2_TOPO_ONLY | municipality | 71 | 1.1796 | 1.1026 | -1.0435 |
| K3_SOIL_ONLY | municipality | 71 | 1.0427 | 0.9153 | -0.8008 |
| K3_SOIL_ONLY_ALT | municipality | 71 | 0.6620 | 0.4730 | -0.1475 |
| K4_TOPO_SOIL | municipality | 71 | 0.9347 | 0.8231 | -0.7278 |
| K5_RAIN_RESID_SLOPE | municipality | 71 | 0.5652 | 0.3910 | 0.1374 |
| K6_RAIN_RESID_TOPO | municipality | 71 | 0.5691 | 0.3748 | 0.0778 |
| K7_RAIN_RESID_SOIL | municipality | 71 | 0.6531 | 0.4561 | 0.2813 |
| K8_RAIN_RESID_TOPO_SOIL | municipality | 71 | 0.5795 | 0.3914 | 0.1796 |
| KA_RAIN_SLOPE_MATCHED | municipality | 71 | 0.5720 | 0.3874 | 0.1100 |
| KA_RAIN_SOIL_STABLE | municipality | 71 | 0.5936 | 0.3898 | 0.1151 |
| KA_RAIN_TOPO_MATCHED | municipality | 71 | 0.9355 | 0.8518 | -0.7555 |
| KA_RAIN_TOPO_SOIL_STABLE | municipality | 71 | 0.9355 | 0.8518 | -0.7555 |
| J0_RAIN | random | 71 | 0.5764 | 0.3896 | 0.0036 |
| J1_RAIN_SLOPE | random | 71 | 0.5638 | 0.4033 | -0.0058 |
| J2_RAIN_TOPO | random | 71 | 0.5658 | 0.4058 | -0.0064 |
| J3_RAIN_SOIL_GROUP | random | 71 | 0.5836 | 0.3944 | -0.0311 |
| J4_RAIN_TOPO_SOIL | random | 71 | 0.5756 | 0.4078 | -0.0455 |
| K0_MEAN | random | 71 | 0.7871 | 0.6736 | -0.5266 |
| K1_SLOPE_ONLY | random | 71 | 0.7613 | 0.6465 | -0.5118 |
| K2_TOPO_ONLY | random | 71 | 0.7486 | 0.6332 | -0.4821 |
| K3_SOIL_ONLY | random | 71 | 0.7004 | 0.4892 | -0.1677 |
| K3_SOIL_ONLY_ALT | random | 71 | 0.5877 | 0.4078 | -0.0276 |
| K4_TOPO_SOIL | random | 71 | 0.6142 | 0.4546 | -0.0989 |
| K5_RAIN_RESID_SLOPE | random | 71 | 0.5685 | 0.3969 | 0.0107 |
| K6_RAIN_RESID_TOPO | random | 71 | 0.5704 | 0.3965 | 0.0094 |
| K7_RAIN_RESID_SOIL | random | 71 | 0.5772 | 0.3902 | 0.0036 |
| K8_RAIN_RESID_TOPO_SOIL | random | 71 | 0.5736 | 0.3941 | 0.0066 |
| KA_RAIN_SLOPE_MATCHED | random | 71 | 0.5648 | 0.4042 | -0.0056 |
| KA_RAIN_SOIL_STABLE | random | 71 | 0.5791 | 0.3910 | -0.0080 |
| KA_RAIN_TOPO_MATCHED | random | 71 | 0.5661 | 0.4060 | -0.0064 |
| KA_RAIN_TOPO_SOIL_STABLE | random | 71 | 0.5705 | 0.4073 | -0.0183 |
| J0_RAIN | spatial | 71 | 0.5638 | 0.3809 | 0.0111 |
| J1_RAIN_SLOPE | spatial | 71 | 0.5589 | 0.4132 | -0.1044 |
| J2_RAIN_TOPO | spatial | 71 | 0.5765 | 0.4319 | -0.1758 |
| J3_RAIN_SOIL_GROUP | spatial | 71 | 0.6071 | 0.4363 | -0.1338 |
| J4_RAIN_TOPO_SOIL | spatial | 71 | 0.6472 | 0.5232 | -0.3402 |
| K0_MEAN | spatial | 71 | 0.9307 | 0.8295 | -0.7201 |
| K1_SLOPE_ONLY | spatial | 71 | 0.9483 | 0.8626 | -0.7522 |
| K2_TOPO_ONLY | spatial | 71 | 1.0103 | 0.9271 | -0.8385 |
| K3_SOIL_ONLY | spatial | 71 | 0.9238 | 0.7097 | -0.4431 |
| K3_SOIL_ONLY_ALT | spatial | 71 | 0.8329 | 0.6445 | -0.3481 |
| K4_TOPO_SOIL | spatial | 71 | 0.7921 | 0.6044 | -0.3545 |
| K5_RAIN_RESID_SLOPE | spatial | 71 | 0.5553 | 0.4007 | -0.0423 |
| K6_RAIN_RESID_TOPO | spatial | 71 | 0.5595 | 0.4019 | -0.0595 |
| K7_RAIN_RESID_SOIL | spatial | 71 | 0.5662 | 0.3780 | 0.0130 |
| K8_RAIN_RESID_TOPO_SOIL | spatial | 71 | 0.5934 | 0.4296 | 0.1832 |
| KA_RAIN_SLOPE_MATCHED | spatial | 71 | 0.5589 | 0.4132 | -0.1044 |
| KA_RAIN_SOIL_STABLE | spatial | 71 | 0.6945 | 0.5156 | 0.1917 |
| KA_RAIN_TOPO_MATCHED | spatial | 71 | 0.5935 | 0.4593 | -0.0010 |
| KA_RAIN_TOPO_SOIL_STABLE | spatial | 71 | 0.5687 | 0.4174 | -0.1582 |

Chignahuapan: 71 etiquetas, subconjunto de los mismos OOF, sin modelo local ni evaluación independiente. Las diferencias entre parejas se atribuyen a variables solo cuando fueron evaluadas por el mismo modelo externo. Tabla27 identifica dispersión artificial sin mejora de error; tabla28 conserva pendiente, altitud y distancia composicional de cada pareja. La correlación residual/corrección en tabla25 procede exclusivamente de predicciones externas. Más dispersión no demuestra mejor predicción.

## Reservas edafológicas y soporte

Se conservan todas las predicciones, incluso negativas o extremas. Tabla33 verifica que las coberturas transformadas no excedan su rango natural, evitando el mecanismo z≈353 de J. Tabla32 define reservas por soporte EXCLUSIVAMENTE en entrenamiento. Tablas23/24 incluyen buffers cartográficos de50/125/250m, claves discrepantes, estados/municipios y rendimientos<3/>5; estos son diagnósticos y nunca predictores. Cartografía1:250000, sin interpretar como medición física parcelaria ni precisión probabilística.

## Criterios y benchmark

| experiment | random_RMSE_improvement | random_MAE_improvement | worst_grouped_RMSE_improvement | passes_geographic_margin | interpretation |
| --- | --- | --- | --- | --- | --- |
| J1_RAIN_SLOPE | 0.0059 | -0.0061 | -0.2405 | False | incremental vs rain; contextual J controls |
| J2_RAIN_TOPO | 0.0048 | -0.0073 | -0.1771 | False | incremental vs rain; contextual J controls |
| J3_RAIN_SOIL_GROUP | -0.0254 | -0.0171 | -0.2186 | False | incremental vs rain; contextual J controls |
| J4_RAIN_TOPO_SOIL | -0.0233 | -0.0250 | -0.2064 | False | incremental vs rain; contextual J controls |
| K0_MEAN | -0.3346 | -0.3846 | -0.4565 | False | incremental vs rain; contextual J controls |
| K1_SLOPE_ONLY | -0.2962 | -0.3303 | -0.4129 | False | standalone vs mean is primary |
| K2_TOPO_ONLY | -0.2892 | -0.3212 | -0.4445 | False | standalone vs mean is primary |
| K3_SOIL_ONLY | -0.1608 | -0.1453 | -0.3390 | False | standalone vs mean is primary |
| K3_SOIL_ONLY_ALT | -0.0347 | -0.0295 | -0.3434 | False | standalone vs mean is primary |
| K4_TOPO_SOIL | -0.0840 | -0.0823 | -0.3218 | False | standalone vs mean is primary |
| K5_RAIN_RESID_SLOPE | 0.0051 | -0.0019 | -0.0007 | True | incremental vs rain; contextual J controls |
| K6_RAIN_RESID_TOPO | 0.0038 | -0.0023 | -0.0114 | False | incremental vs rain; contextual J controls |
| K7_RAIN_RESID_SOIL | -0.0010 | -0.0004 | -0.0457 | False | incremental vs rain; contextual J controls |
| K8_RAIN_RESID_TOPO_SOIL | 0.0000 | -0.0018 | -0.0188 | False | incremental vs rain; contextual J controls |
| KA_RAIN_SLOPE_MATCHED | 0.0048 | -0.0070 | -0.2295 | False | incremental vs rain; contextual J controls |
| KA_RAIN_SOIL_STABLE | -0.0080 | -0.0050 | -0.2679 | False | incremental vs rain; contextual J controls |
| KA_RAIN_TOPO_MATCHED | 0.0042 | -0.0076 | -0.1771 | False | incremental vs rain; contextual J controls |
| KA_RAIN_TOPO_SOIL_STABLE | -0.0076 | -0.0160 | -0.2324 | False | incremental vs rain; contextual J controls |

Margen exploratorio .01t/ha para deterioro geográfico/MAE, sin prueba de significancia. Repeticiones y folds comparten observaciones: mejoras pequeñas no son confirmación independiente. Distinguir regiones conocidas, transferencia a nuevas regiones e intraperfil; no hay reemplazo automático del Champion.

Benchmark aleatorio compatible, sin reentrenar:

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

Champion y Climate Current son contextuales, con otros bloques y arquitecturas. No hay OOF Champion municipal/espacial comparable en esta auditoría; no se extrapola su superioridad a esos protocolos.

Todos los modelos K solo usan lluvia, pendiente, altitud o suelo según especificación; nunca temperatura, satélite, estado/municipio/localidad ni las59 etiquetas ocultas.

## Conclusiones de los resultados congelados

RMSE (t/ha), OOF completos por repetición; menor es mejor.

| Modelo | Aleatorio | Perfil | Municipal | Espacial |
| --- | --- | --- | --- | --- |
| K0_MEAN | 0.8560 | 0.9368 | 1.1518 | 1.0276 |
| K1_SLOPE_ONLY | 0.8176 | 0.9572 | 1.1029 | 1.0039 |
| K2_TOPO_ONLY | 0.8105 | 0.9771 | 1.1399 | 1.0826 |
| K3_SOIL_ONLY | 0.6822 | 0.7444 | 1.0343 | 1.0347 |
| K3_SOIL_ONLY_ALT | 0.5561 | 0.5759 | 0.8402 | 1.0782 |
| K4_TOPO_SOIL | 0.6053 | 0.6207 | 1.0172 | 0.9447 |
| J0_RAIN | 0.5214 | 0.5444 | 0.6954 | 0.7348 |
| J1_RAIN_SLOPE | 0.5154 | 0.5130 | 0.6755 | 0.9753 |
| KA_RAIN_SLOPE_MATCHED | 0.5165 | 0.5130 | 0.6826 | 0.9643 |
| KA_RAIN_TOPO_MATCHED | 0.5171 | 0.5502 | 0.8725 | 0.8907 |
| KA_RAIN_SOIL_STABLE | 0.5294 | 0.5582 | 0.7326 | 1.0027 |
| KA_RAIN_TOPO_SOIL_STABLE | 0.5289 | 0.5450 | 0.9055 | 0.9671 |
| K5_RAIN_RESID_SLOPE | 0.5162 | 0.5376 | 0.6961 | 0.7139 |
| K6_RAIN_RESID_TOPO | 0.5175 | 0.5407 | 0.7067 | 0.7279 |
| K7_RAIN_RESID_SOIL | 0.5223 | 0.5532 | 0.7410 | 0.7344 |
| K8_RAIN_RESID_TOPO_SOIL | 0.5213 | 0.5471 | 0.7142 | 0.7339 |

La pendiente/topografía y el suelo como modelos independientes se valoran frente a la media K0. La comparación contra lluvia mide otra pregunta; un buen modelo independiente no garantiza señal incremental.

K1_SLOPE_ONLY: mejora RMSE frente a K0 aleatoria/perfil/municipal/espacial = +0.0384, -0.0205, +0.0490, +0.0237 t/ha. Esto describe capacidad predictiva propia en estos protocolos, no causalidad.
K2_TOPO_ONLY: mejora RMSE frente a K0 aleatoria/perfil/municipal/espacial = +0.0455, -0.0403, +0.0120, -0.0550 t/ha. Esto describe capacidad predictiva propia en estos protocolos, no causalidad.
K3_SOIL_ONLY: mejora RMSE frente a K0 aleatoria/perfil/municipal/espacial = +0.1738, +0.1924, +0.1175, -0.0070 t/ha. Esto describe capacidad predictiva propia en estos protocolos, no causalidad.
K4_TOPO_SOIL: mejora RMSE frente a K0 aleatoria/perfil/municipal/espacial = +0.2507, +0.3161, +0.1347, +0.0829 t/ha. Esto describe capacidad predictiva propia en estos protocolos, no causalidad.
K3_SOIL_ONLY_ALT: mejora RMSE frente a K0 aleatoria/perfil/municipal/espacial = +0.2999, +0.3609, +0.3116, -0.0506 t/ha. Esto describe capacidad predictiva propia en estos protocolos, no causalidad.

La comparación de arquitectura usa controles KA con idénticas variables, escalas, penalizaciones y folds. J permanece como referencia histórica.

K5_RAIN_RESID_SLOPE: mejora sobre lluvia (aleatorio/perfil/municipal/espacial) +0.0051, +0.0068, -0.0007, +0.0209 t/ha; mejora MAE aleatoria -0.0019; 100% de repeticiones mejora RMSE. Frente al control aditivo comparable: +0.0003, -0.0245, -0.0135, +0.2504.
K6_RAIN_RESID_TOPO: mejora sobre lluvia (aleatorio/perfil/municipal/espacial) +0.0038, +0.0036, -0.0114, +0.0069 t/ha; mejora MAE aleatoria -0.0023; 90% de repeticiones mejora RMSE. Frente al control aditivo comparable: -0.0004, +0.0095, +0.1657, +0.1628.
K7_RAIN_RESID_SOIL: mejora sobre lluvia (aleatorio/perfil/municipal/espacial) -0.0010, -0.0089, -0.0457, +0.0003 t/ha; mejora MAE aleatoria -0.0004; 50% de repeticiones mejora RMSE. Frente al control aditivo comparable: +0.0070, +0.0049, -0.0085, +0.2682.
K8_RAIN_RESID_TOPO_SOIL: mejora sobre lluvia (aleatorio/perfil/municipal/espacial) +0.0000, -0.0028, -0.0188, +0.0009 t/ha; mejora MAE aleatoria -0.0018; 70% de repeticiones mejora RMSE. Frente al control aditivo comparable: +0.0076, -0.0021, +0.1914, +0.2332.

El control eta=0 reproduce lluvia en cada fold. Una menor degradación que J no equivale a mejora sobre lluvia; el ajuste interno puede rechazar una corrección, pero no garantiza transferencia externa.

La inestabilidad numérica de coberturas estandarizadas se eliminó por construcción: todas las cuotas de suelo utilizadas quedan entre0y1. Permanecen falta de soporte y cambios geográficos: RG/UM tienen una etiqueta cada uno; las unidades raras se agrupan solo en S2 y la cartografía mantiene reservas1:250000. No se recortan rendimientos ni se eliminan parcelas.

Intraperfil y Chignahuapan: tablas27–29/35 usan parejas evaluadas por un mismo modelo externo; Chignahuapan es un subconjunto de71 etiquetas y no constituye validación independiente. Tabla25 mide correlaciones de correcciones fuera de muestra. Aumentar dispersión sin disminuir errores no justifica integración.

Las comparaciones entre10 repeticiones y65 folds son descriptivas y correlacionadas. El margen .01t/ha de deterioro geográfico/MAE es exploratorio; no significancia estadística. No se modifica Champion ni se entrenan las59 parcelas sin etiqueta.

Próximo paso justificable si queda señal local pero falla transferencia: evaluar en etiquetas de regiones externas y estudiar soporte temático de clases. No se abren nuevas arquitecturas ni ensayos retrospectivos dentro de K.

Lectura de los resultados de esta versión:

Pendiente sola aporta una señal modesta frente a la media: RMSE aleatorio 0.8176 frente a 0.8560. La altitud mejora ligeramente ese resultado aleatorio, pero empeora la transferencia espacial; no fortalece de manera consistente el bloque topográfico.

El suelo tiene asociación predictiva propia: S1 logra 0.6822 y S2 0.5561 en aleatorio. S2 conserva unidades más específicas y predice mejor dentro de los datos disponibles, pero su RMSE espacial es 1.0782, peor que la media 1.0276. No se cambia retrospectivamente la representación primaria para favorecer ese resultado.

Combinar topografía y S1 mejora a cada bloque independiente en aleatorio y espacio; aun así, lluvia sola supera a estos modelos. Los controles aditivos y residuales de suelo no confirman una mejora incremental estable. Esto es compatible con redundancia regional con clima y con soporte insuficiente; no prueba irrelevancia agronómica del suelo.

K5, pendiente residual, es la candidata más equilibrada entre los correctores: mejora RMSE aleatorio, por perfil y espacial, y queda casi igual en municipal. Su MAE aleatorio empeora ligeramente. El control aditivo de pendiente conserva mejores resultados por perfil y municipio; la corrección residual ofrece una transferencia espacial mucho menos deteriorada. No hay una arquitectura que gane todos los objetivos.

Los dos estimadores Elastic Net siguen siendo lineales: sumar clima y corrector lineal no crea por sí mismo capacidad no lineal. Las diferencias provienen del ajuste por etapas, los objetivos cruzados, la regularización y eta; no de variables adicionales.

La señal favorable de K5 es pequeña y exploratoria. Justifica conservarla como candidata de RMSE para validación externa, sin declarar una mejora confirmada ni reemplazar Champion. No cumple todos los criterios: el MAE por perfil aumenta .0114t/ha y el municipal .0122t/ha, por encima del margen exploratorio .01. K6 excede ligeramente el margen municipal de RMSE; K7/K8 no aportan una mejora geográficamente consistente. Ningún corrector cumple la pantalla completa de RMSE y MAE en todos los protocolos.

En Chignahuapan K5 reduce RMSE aleatorio .5764→.5685, pero eleva MAE .3896→.3969; por perfil, MAE .3863→.4092 y en espacial .3809→.4007. El beneficio en errores grandes no es una mejora uniforme por parcela. Las71 etiquetas locales pertenecen a los mismos OOF, no a una prueba independiente.

La reserva por discrepancia de clave de edición solo tiene una etiqueta: no permite inferencias firmes. Los buffers cartográficos son sensibilidades descriptivas, no errores probabilísticos de localización. Coeficientes residuales propuestos y aplicados (multiplicados por eta) se distinguen en tabla36.

## Figuras

RMSE por protocolo

![RMSE por protocolo](../outputs/modeling/family_1/k_standalone_residual_geographic_edaphological/v1/figures/01_RMSE_protocol.png)

MAE por protocolo

![MAE por protocolo](../outputs/modeling/family_1/k_standalone_residual_geographic_edaphological/v1/figures/01_MAE_protocol.png)

Mejoras y deterioros frente a lluvia

![Mejoras y deterioros frente a lluvia](../outputs/modeling/family_1/k_standalone_residual_geographic_edaphological/v1/figures/02_delta_against_rain.png)

Arquitectura aditiva y residual con variables y grillas idénticas

![Arquitectura aditiva y residual con variables y grillas idénticas](../outputs/modeling/family_1/k_standalone_residual_geographic_edaphological/v1/figures/03_additive_vs_residual.png)

Predicciones OOF aleatorias promediadas solo para descripción

![Predicciones OOF aleatorias promediadas solo para descripción](../outputs/modeling/family_1/k_standalone_residual_geographic_edaphological/v1/figures/04_observed_estimated.png)

Correcciones aplicadas por parcela

![Correcciones aplicadas por parcela](../outputs/modeling/family_1/k_standalone_residual_geographic_edaphological/v1/figures/05_corrections_parcel.png)

Chignahuapan, subconjunto de los mismos OOF

![Chignahuapan, subconjunto de los mismos OOF](../outputs/modeling/family_1/k_standalone_residual_geographic_edaphological/v1/figures/06_chignahuapan.png)

Reserva por proximidad a límites125m

![Reserva por proximidad a límites125m](../outputs/modeling/family_1/k_standalone_residual_geographic_edaphological/v1/figures/07_boundary_near125m.png)

Mejora intraperfil con un mismo modelo externo

![Mejora intraperfil con un mismo modelo externo](../outputs/modeling/family_1/k_standalone_residual_geographic_edaphological/v1/figures/08_intraprofile.png)

Errores según soporte aprendido en entrenamiento

![Errores según soporte aprendido en entrenamiento](../outputs/modeling/family_1/k_standalone_residual_geographic_edaphological/v1/figures/09_soil_support.png)

