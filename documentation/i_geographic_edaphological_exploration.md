> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Sección I — Exploración geográfica, topográfica y edafológica condicionada al clima

Se construyó una representación cartográfica de suelo para las 197 parcelas usando el vector oficial nacional INEGI Serie III, WRB 2014, escala 1:250000. No se entrenó ningún modelo de rendimiento, no se generaron predicciones para los 59 casos ocultos y se preservaron E–H y el modelo TOP20/TOP15 mediante hashes.

## Auditoría edafológica y productos A–D

La descarga oficial incluye polígonos, CRS original ITRF92 Lambert, metadatos y diccionario versión 4. La carta E1402 impresa es edición 2025 y el vector nacional edición 2024: comparten Serie III, WRB2014 y cobertura temporal 2021; no se afirma equivalencia geométrica exacta entre ambos productos. `02_unit_legend_audit.csv` registra claves encontradas en el texto de E1402. El vector oficial se usa como fuente explícita independiente: no se reconstruyen límites a partir de colores.

De las 22 claves intersectadas, 20 aparecen exactamente en el texto de E1402. `UMlep-lo+RGdy+LPdy/2` y `UMlep-lo+RGdy+LPli/2` aparecen en la carta con `hu` en lugar de `lo`. Es una diferencia temática entre ediciones, no una equivalencia corregida automáticamente: la variable `soil_share_key_not_found_in_E1402_text` conserva la cobertura afectada. Estas parcelas requieren reserva adicional para interpretar calificadores y validación contra la fuente que se quiera adoptar en modelado. Los grupos de las asociaciones coinciden; no se afirma que las propiedades sean intercambiables.

Se filtraron 128 polígonos próximos al área. Hay 22 claves cartográficas intersectadas y 252 intersecciones. Cobertura mínima 1.000000000, máxima 1.000000000; 50 parcelas cruzan unidades. Se agregan polígonos de igual clave tras comprobar igualdad de atributos, sin eliminar intersecciones pequeñas. Las áreas usan LAEA local de igual área, no grados ni áreas originales del DBF.

88 parcelas tienen alguna superficie a menos de 125 m de un límite temático. Buffers de 50/125/250m son escenarios de sensibilidad equivalentes a 0.2/0.5/1mm a escala, **no estimaciones de exactitud**. El número de unidades y las fracciones expresan heterogeneidad cartográfica; el mapa no mide heterogeneidad física parcelaria. No se trasladan análisis de laboratorio de los reversos ni se derivan pH, infiltración o retención cuantitativa.

La geometría derivada se recorta con margen de 2km para procesar únicamente el área de interés. `49_boundary_aoi_edge_check.csv` comprueba, para las 197 parcelas, que el borde artificial del recorte está más lejos que el límite temático más cercano; no determina distancias ni los buffers de sensibilidad.

La matriz longitudinal conserva todas las intersecciones y atributos. La matriz ancha conserva todas las claves. Ausencia verificada=0; se comprueba cobertura completa antes de usar ceros. `soil_mixed_share=1-dominant_share`; entropía `-sum(q*ln(q))`, con q normalizada únicamente sobre cobertura cartográfica válida; el faltante se conserva por separado. Los empates se resuelven por clave lexicográfica, sin depender del orden de geometrías.

Grupos y calificadores se recuperan de campos oficiales, no de estimaciones RGB. `soil_map_share_mentions_*` es cobertura de unidades que **mencionan** un atributo, no fracción física de cada suelo asociado. Las menciones de grupos pueden sumar más de uno. `N` indica atributo ausente en la nomenclatura, no propiedad física medida; `N/A` no aplicable. El diccionario y los nombres oficiales se guardan junto a la leyenda.

Top-N por parcela se evaluó desde N=1 hasta todas las unidades presentes; N=4 conserva toda la composición observada. También se conservaron variantes globales por frecuencia, superficie y cobertura media; los órdenes se calculan separadamente. `22_topn_comparison.csv` mide cobertura, omisiones, categorías eliminadas y pérdidas de diferenciación de todas las parejas e intraperfil a tolerancias 1/5/10 pp. Cada N tiene matriz y tabla de omisiones. No se usó Y para escoger N. La referencia provisional sigue siendo la matriz completa; Top-N es una alternativa auditable, no un ganador predictivo.

Aplicando un criterio descriptivo explícito —cobertura total >=99%, omisión máxima por parcela <=5% y cero pérdidas de diferenciación a TV>5pp— el menor Top-N admisible es N=3: cobertura 99.978%, omisión máxima 1.332%. El criterio utiliza exclusivamente coberturas y diferenciación, sin rendimiento. N=2 conserva mucha cobertura total, pero concentra una pérdida elevada en una parcela; por eso la media no basta. Los identificadores de Top-N se mantienen como categorías, no como números continuos, y el restante conserva la omisión visible.

## Geografía, localidades y diagnóstico integrado E–F

La geometría tiene estado y municipio; no localidad. Los CSV externos contienen puntos, nombres y códigos, sin límites de localidad ni fecha/CRS documentados. Se interpretan las coordenadas decimales como WGS84 con esta reserva explícita. Se mide proximidad al centroide en EPSG6372 y se conserva CVEGEO, fuente, distancia y segundo vecino. La regla «cercano y separado» exige distancia <=1km y margen al segundo >=250m: es confianza en la referencia de proximidad, **no pertenencia administrativa**. La auditoría compara nombre/distancia con la extracción previa de fase C; añade identidad y reservas sin reemplazarla.

Chignahuapan contiene 100 parcelas (50.8% de la muestra), 71 etiquetadas (51.4% del entrenamiento), 15 perfiles y 6 unidades. Su rango de altitud es 305.8m y de pendiente 9.11 grados. La tabla territorial incluye estados, municipios y referencias de localidad; estadísticos de Y solo se muestran con >=5 observaciones. No se extrapolan estas concentraciones a todo un estado o al país.

En las parcelas etiquetadas de Chignahuapan, 14.2% de SS de Y se encuentra entre sus perfiles y 85.8% dentro. El resultado es regional y descriptivo; las demás regiones se comparan en `47_regional_y_variance.csv` solamente con soporte de al menos cinco etiquetas.

La auditoría de fase C encontró dos procedimientos distintos: `EXT_LOC_distance_any_m` mide distancia mínima desde el **polígono** parcelario al punto, aunque su diccionario la describía como centroide; el nombre cercano se había obtenido desde el centroide. Se conservan ambos campos previos, sin modificar aquel procesamiento. I explicita la distancia desde el centroide usada para identificar el punto de referencia y su segundo vecino. La diferencia máxima entre distancias es 589.58m y responde a esos procedimientos distintos. Hay 11 referencias cercanas cuyo municipio difiere del municipio real de la parcela: proximidad no significa pertenencia.

## Variación entre/dentro de perfiles G

Se reutiliza la asignación exacta de 53 perfiles de H. Se informan rangos, medias y desviaciones de altitud y pendiente, geografía, suelo y rendimiento observado por perfil. Elevación y pendiente provienen de la extracción CEM4 de 120m. Sus versiones centradas en 197 parcelas son descriptivas y objetivo-libres; las asociaciones con Y centran **ambas variables en las 138 etiquetadas**, evitando usar la media de Y o asignar etiquetas al conjunto de predicción.

De 2136 parejas con clima idéntico, 1587 se distinguen por altitud >25m o pendiente >1 grado; 863 por distancia de variación total de composición >0.05; 863 por alguna cobertura de atributo >5pp; 1661 por topografía o suelo. De las diferenciadas por suelo, 158 están fuera del escenario de reserva de límites y 705 requieren reserva. Hay 12 perfiles con diferenciación cartográfica de suelo. Las tolerancias son filtros descriptivos de sensibilidad, **no certificación de diferencias físicas**; se guardan también escenarios 10m/0.5°/1pp y 50m/2°/10pp. No se cuentan cambios infinitesimales como evidencia.

Variación composicional entre perfiles: 73.3% de la inercia euclídea de la composición cerrada. Se describen proporciones dependientes; los ID de unidad no se correlacionan como números. La comparación de perfiles próximos usa distancia geográfica y variación total de sus composiciones medias, con todos los pares conservados.

Para Y, SS total=99.253032, entre=73.897219, dentro=25.355813. La proporción entre perfiles es 74.5% y dentro 25.5%. Es una partición descriptiva, no contribución causal del clima ni mejora predictiva. Las asociaciones globales, intraperfil y locales de Chignahuapan están en `37_descriptive_associations_138.csv`. Las categorías se describen con soporte >=5; contrastes intraperfil requieren >=3 casos por cada categoría y no se interpretan como significancia.

Asociaciones topográficas observadas (correlaciones descriptivas, sin selección de predictores por Y):

| feature | scope | global_pearson | within_profile_pearson |
| --- | --- | --- | --- |
| altitude_m | all_labeled | 0.2896 | 0.0414 |
| altitude_m | Chignahuapan_labeled | 0.2020 | 0.0386 |
| slope_degrees | all_labeled | 0.3106 | 0.2317 |
| slope_degrees | Chignahuapan_labeled | 0.3241 | 0.2471 |

La relación global de altitud con Y se debilita considerablemente al comparar dentro del mismo clima; parte de su asociación global puede corresponder a estructura geográfica entre perfiles. La pendiente conserva mayor asociación intraperfil y muestra un patrón local semejante en Chignahuapan. Esto justifica estudiar altitud y pendiente por separado, sin declarar causalidad, significancia ni mejora predictiva. El soporte local depende de pocos perfiles repetidos y se informa en las tablas.

## Viabilidad de variables H

| Familia | Situación provisional | Justificación |
|---|---|---|
| Altitud y pendiente continuas | Lista para prueba controlada | Extracción existente, cobertura completa, variación intraperfil; distinta información geomorfológica, sin inferir temperatura local. |
| Composición completa de unidades | Utilizable con reservas | Cobertura validada y todas las categorías preservadas, pero escala 1:250000, dependencia geográfica y bordes inciertos. |
| Atributos y limitantes cartográficos | Utilizable con reservas | Interpretables, 45 coberturas; revisar redundancia, códigos poco frecuentes y asociaciones múltiples. |
| Top-N por parcela / global | Utilizable con reservas | Pérdidas cuantificadas sin Y; identidad categórica separada del porcentaje. Ajustar selección futura dentro de entrenamiento de cada fold. |
| Localidades y coordenadas | Requiere validación adicional como predictor | Útiles para diagnóstico/particiones; puntos cercanos no prueban pertenencia y la muestra es concentrada. |
| RGB de suelo, laboratorio asignado por cercanía y propiedades hidrológicas inventadas | No recomendable | No hay correspondencia parcelaria validada ni estimación física respaldada. |

`40_feature_viability_dependence.csv` cuantifica variación, redundancia con topografía y dependencia de estado/municipio/localidad; `41_unit_train_prediction_support.csv` identifica categorías exclusivas de predicción y escaso soporte. No hay selección por RMSE en I.

`45_representation_dimension_differentiation.csv` compara dimensionalidad, columnas variables y distinciones globales/intraperfil de unidades y atributos; usa métricas explícitas distintas para composición y menciones. `46_category_heterogeneity.csv` informa probabilidad de desacuerdo categórico global e intraperfil. Las representaciones de grupos mantienen interpretación pero pueden perder variación de calificadores y textura; no se seleccionan solo por producir más distinciones.

| representation | n_columns | nonconstant_columns | within_profile_pairs_distinguished_5pp |
| --- | --- | --- | --- |
| full_units | 22 | 22 | 863 |
| attribute_coverages | 45 | 45 | 863 |
| group | 10 | 10 | 833 |
| qualifier | 26 | 26 | 863 |
| texture | 3 | 3 | 659 |
| surface_limit | 1 | 1 | 8 |
| physical_phase | 5 | 5 | 796 |

Hay 2 unidades solo en predicción y 13 unidades con menos de cinco parcelas de entrenamiento. Esas categorías no tienen evidencia suficiente para ajustar efectos individuales sin regularización/agrupación validada. La representación completa de atributos puede tener más columnas que la composición de unidades: «por atributos» no significa automáticamente compacta. Se conservan matrices separadas de grupos, calificadores, textura y limitantes para evaluar esa reducción explícitamente.

Como primer bloque compacto de suelo para una prueba posterior, las diez coberturas de unidades que mencionan grupos conservan 833 de 863 distinciones intraperfil a la tolerancia de 5pp, frente a 22 columnas de unidades. Es una reducción interpretable con pérdida explícita, no un ganador predictivo. Los 45 atributos juntos no reducen dimensionalidad; los calificadores tienen además la discrepancia entre ediciones señalada. Las limitantes químicas no aportan variación cartográfica en esta muestra (`N`), por lo que no se inventan indicadores químicos continuos.

## Propuesta posterior I — no ejecutada

Comparar solo lluvia, lluvia+altitud/pendiente, lluvia+suelo y lluvia+ambos. Mantener la misma lluvia, algoritmo base y folds congelados de E–H para atribuir incrementos; contrastar los resultados con Climate Current y modelo TOP20/TOP15 respetando sus arquitecturas y métrica. Preprocesamiento, selección por frecuencia, codificación y cualquier ajuste se aprenden dentro de cada entrenamiento interno; categorías nuevas tienen tratamiento explícito. No usar centrados calculados con las 197 parcelas como entrada aprendida a validación.

Usar RMSE, MAE, R², sesgo y diferencias pareadas por fold, con validación aleatoria, por perfil, municipal y espacial. La integración requerirá mejora reproducible más allá del error de comparación, ausencia de deterioro material preespecificado en protocolos geográficos y soporte de categorías. Definir antes de ejecutar margen de no inferioridad de 0.01t/ha en RMSE y evaluar intervalos mediante repeticiones o grupos independientes, sin tratar folds correlacionados como muestras independientes. Si mejora aleatoria y empeora municipal/espacial, registrar asociación local sin generalización demostrada. Interacciones lluvia–suelo se estudiarían después, con unas pocas hipótesis respaldadas y soporte suficiente.

## Visualizaciones y reproducibilidad

Se guardan mapas territoriales, de localidades cercanas, perfiles, suelo oficial y dominancia; composiciones, unidades por parcela, concentración, topografía y suelo intraperfil, descomposición de Y, comparación Top-N y potencial de diferenciación. `interactive/profile_explorer.html` es autónomo y permite elegir los 53 perfiles, consultar referencias territoriales, topografía, unidad dominante, reservas de límites y Y observado. La simbología es descriptiva.

Ejecutar scripts 323 (suelo oficial) y 324 (exploración) desde la raíz. Fuente nueva en `data/externo/suelo/inegi_serie_iii_794551118313`; derivados en `data/processed/family_1/i_climate_conditioned_geographic_edaphological/v1`; tablas, figuras y manifiestos en `outputs/research/family_1/i_climate_conditioned_geographic_edaphological/v1`. SHA256 del archivo oficial y de insumos protegidos permiten auditar trazabilidad. Los apartados de productos son internos a Sección I.
