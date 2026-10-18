> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# K — Resumen para decisiones

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

Las comparaciones entre10 repeticiones y65 folds son descriptivas y correlacionadas. El margen .01t/ha de deterioro geográfico/MAE es exploratorio; no significancia estadística. No se modifica modelo TOP20/TOP15 ni se entrenan las59 parcelas sin etiqueta.

Próximo paso justificable si queda señal local pero falla transferencia: evaluar en etiquetas de regiones externas y estudiar soporte temático de clases. No se abren nuevas arquitecturas ni ensayos retrospectivos dentro de K.

Lectura de los resultados de esta versión:

Pendiente sola aporta una señal modesta frente a la media: RMSE aleatorio 0.8176 frente a 0.8560. La altitud mejora ligeramente ese resultado aleatorio, pero empeora la transferencia espacial; no fortalece de manera consistente el bloque topográfico.

El suelo tiene asociación predictiva propia: S1 logra 0.6822 y S2 0.5561 en aleatorio. S2 conserva unidades más específicas y predice mejor dentro de los datos disponibles, pero su RMSE espacial es 1.0782, peor que la media 1.0276. No se cambia retrospectivamente la representación primaria para favorecer ese resultado.

Combinar topografía y S1 mejora a cada bloque independiente en aleatorio y espacio; aun así, lluvia sola supera a estos modelos. Los controles aditivos y residuales de suelo no confirman una mejora incremental estable. Esto es compatible con redundancia regional con clima y con soporte insuficiente; no prueba irrelevancia agronómica del suelo.

K5, pendiente residual, es la candidata más equilibrada entre los correctores: mejora RMSE aleatorio, por perfil y espacial, y queda casi igual en municipal. Su MAE aleatorio empeora ligeramente. El control aditivo de pendiente conserva mejores resultados por perfil y municipio; la corrección residual ofrece una transferencia espacial mucho menos deteriorada. No hay una arquitectura que gane todos los objetivos.

Los dos estimadores Elastic Net siguen siendo lineales: sumar clima y corrector lineal no crea por sí mismo capacidad no lineal. Las diferencias provienen del ajuste por etapas, los objetivos cruzados, la regularización y eta; no de variables adicionales.

La señal favorable de K5 es pequeña y exploratoria. Justifica conservarla como candidata de RMSE para validación externa, sin declarar una mejora confirmada ni reemplazar modelo TOP20/TOP15. No cumple todos los criterios: el MAE por perfil aumenta .0114t/ha y el municipal .0122t/ha, por encima del margen exploratorio .01. K6 excede ligeramente el margen municipal de RMSE; K7/K8 no aportan una mejora geográficamente consistente. Ningún corrector cumple la pantalla completa de RMSE y MAE en todos los protocolos.

En Chignahuapan K5 reduce RMSE aleatorio .5764→.5685, pero eleva MAE .3896→.3969; por perfil, MAE .3863→.4092 y en espacial .3809→.4007. El beneficio en errores grandes no es una mejora uniforme por parcela. Las71 etiquetas locales pertenecen a los mismos OOF, no a una prueba independiente.

La reserva por discrepancia de clave de edición solo tiene una etiqueta: no permite inferencias firmes. Los buffers cartográficos son sensibilidades descriptivas, no errores probabilísticos de localización. Coeficientes residuales propuestos y aplicados (multiplicados por eta) se distinguen en tabla36.
