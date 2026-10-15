# Selección acotada de representaciones físicas: diseño previo

Esta fase continúa la exploración física v2 y está informada por sus resultados externos. No es confirmación independiente. Se conserva C-T3 original, los 65 folds externos, sus particiones internas y los residuos profundos congelados. No se modifica ninguna fase anterior, Champion, final138 ni PRED59.

## Hipótesis y subbloques

Se separan catorce subbloques por definiciones físicas: pendiente; relieve local; posición topográfica; curvaturas; acumulación de flujo/humedad topográfica; composición geológica; distancias a estructuras/fallas/fracturas; composición de suelo INEGI; textura/fase física cartográfica; mezcla y límites cartográficos; propiedades físicas SoilGrids; propiedades químicas SoilGrids; erosión; altitud como sensibilidad individual.

Las combinaciones predefinidas son GEOLOGY (composición y distancias), TERRAIN (cinco subbloques de relieve), SOIL (cinco subbloques edafológicos) y PHYSICAL_ALL (todos salvo altitud). No se agregan fuentes ni coordenadas, municipios, clima o satélites al corrector. Algunas propiedades pueden seguir actuando como proxies territoriales. Suelo/erosión/geología cartográficos no son laboratorio ni efectos causales.

## Representaciones comparadas

Para cada subbloque se comparan variables originales, resumen físico y PCA de 1, 3, 5 y 8 componentes, limitado por dimensiones y tamaño del entrenamiento. No se blanquean componentes. La dimensión se elige por rendimiento residual interno, no por un porcentaje universal de varianza de X. Un resultado favorable no prueba optimalidad fuera de este grid.

Continuas: mediana/one-hot de entrenamiento, estandarización y normalización de norma RMS de entrenamiento. El resumen físico conserva medias y desviaciones por descriptor de relieve, fracción de pendiente >10, elevación media/std y propiedades SoilGrids ponderadas 0–30 cm. En distancias, resumen aplica log1p no negativo. Textura y mezcla usan su conjunto reducido ya documentado. Se conserva el esquema X-only de cobertura/alias heredado de v2, sin nuevas selecciones de variables por Y.

Composiciones: originales son proporciones sin escalar por clase. Resumen es raíz de proporciones, conservando todas las clases; no constituye agregación de grados de erosión ni mezcla de etiquetas incompatibles. PCA se ajusta sobre raíces centradas. No se divide por la desviación de clases ni por la norma RMS del bloque: así una clase rara no recibe un factor de escala arbitrariamente grande. Se conserva su soporte limitado y posibles clases inéditas; no se imputan propiedades físicas ausentes ni se recortan predicciones a posteriori. Las composiciones parciales heredadas no deben presentarse como una distancia Hellinger completa certificada.

Las combinaciones concatenan subbloques con factor 1/sqrt(B). Las continuas tienen norma RMS unitaria, las composiciones conservan escala acotada. No es igual varianza exacta entre bloques; es una regla fija que evita amplificar composiciones homogéneas. Todas las transformaciones se reajustan en cada entrenamiento externo e interno.

## Modelado y selección

Se conservan los tres correctores de v2: Ridge alfa normalizado 1, 0.1, 0.01; vecinos k12,24,48 con pesos 1/(d+0.25), incluyendo empates; K-means 4/8 grupos, cinco inicializaciones, contracción n/(n+20). Todos se centran y amplitud se selecciona entre 0,0.25,0.5. No se amplían grids al observar resultados.

Por cada representación física y familia se seleccionan modo, dimensión, parámetros y amplitud sobre OOF internas completas. Son 54 recetas de bloque/familia. Un selector general evalúa el procedimiento de elegir entre esas recetas dentro del entrenamiento, excluyendo altitud. Se añaden seis controles MODE que fijan el modo y eligen internamente bloque y familia: permiten comparar estrategias de representación sin escoger bloques sobre los resultados externos. Total: 61 recetas de corrección, más C-T3 recuperado.

Empates a 12 decimales favorecen amplitud menor, orden resumen/PCA1/PCA3/PCA5/PCA8/originales y orden de parámetros. Los selectores entre bloques usan el orden congelado de bloques y familias. No se interpreta la frecuencia de selección como importancia causal ni la selección interna como garantía de extrapolación.

Para cada entrenamiento interno, los targets correctores proceden de bases C-T3 profundas que excluyen los casos de residuo, validación interna y externa. Se comprueban sus IDs. La corrección externa se ajusta sobre los residuos cross-fitted del entrenamiento externo; el C-T3 externo permanece intacto.

## Evaluación y entregables

RMSE, MAE, sesgo, R² sobre OOF completas por repetición; aleatoria media diez repeticiones, no media de RMSE por fold. Diagnósticos intraperfil con igual peso por perfil y por par, errores regionales y bloques espaciales, omisiones sin reajustar, amplitudes, dimensiones/modos y mayores cambios por parcela. Se comparan los resultados archivados compatibles de v2 y Local04D. No se ejecuta GeoC97/41.

Inferencia exploratoria pareada, conglomerados por perfil/municipio/bloque espacial, 5,000 remuestras bootstrap y prueba de signos de pérdidas cuadráticas. Holm para las 61×4 comparaciones contra C-T3 de esta fase; no corrige toda la historia de investigación. Cinco bloques limitan la inferencia espacial. Las representaciones y modelos se evalúan con los mismos folds repetidamente usados: falta confirmación independiente.

Entregables en `outputs/modeling/physical_representation/v1`: configuración y hashes previos, subbloques, modelos y selecciones por fold, OOF, comparación de modos y dimensión, diagnósticos, pruebas de composición/inductividad y reproducción exacta. No se promueve un ganador automáticamente ni se generan predicciones finales nuevas.
