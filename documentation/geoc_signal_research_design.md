# Señales que sostienen al experto GeoC y sustitución por representaciones pequeñas

Diseño congelado antes de resultados nuevos. Pregunta: qué familias sostienen el local sin clima + corrector compacto y qué parte puede recuperarse con variables interpretables, como corrección de C-T3 o como pesos entre expertos. Las etiquetas y folds ya guiaron investigaciones anteriores; no se presenta como confirmación independiente ni selección causal de variables.

## A: ablaciones con reajuste y controles de proximidad

Se agrupan raíces por procedencia y nombres de índices documentados: vegetación histórica/actual, proxies espectrales de agua históricos/actuales, otras señales satelitales/derivadas, SoilGrids, topografía, geometría/coordenadas y NPP. Se añade ablación de vigor mensual abril–junio, que se solapa deliberadamente con vigor actual. Todo predictor que descienda de una raíz del bloque se retira, incluidas interacciones mixtas. No son contribuciones aditivas independientes y pueden retirarse cantidades muy distintas de columnas. El grupo de otros índices no recibe una interpretación biológica inventada.

Para cada retirada se reconstruye PCA20 y se reajusta la combinación completa. La PCA de estas ablaciones conserva el uso transductivo de X197 de la referencia para aislar el bloque, sin Y. Se compara también la base local sola y un control de media ponderada de24 vecinos sin características, con/sin corrector compacto. Retirar coordenadas del PCA no elimina el uso de proximidad para seleccionar vecinos.

Se añade un control FULL_INDUCTIVE20: mismo inventario1831 y PCA20, pero imputación/escalado/PCA y escalado de scores ajustados dentro de cada entrenamiento. Así no se confunde reducción de columnas con un cambio en información X disponible. No se repite toda ablación bajo ambos esquemas; el alcance transductivo e inductivo se reporta por separado.

## B: 12 y30 variables fijadas por definición

SMALL12: media/std históricos de NDVI y MSI Sentinel-2; cambios de dirección del EVI Planet2025; cambio NDVI Planet junio–agosto; media/std NDWI Sentinel-22025; arcilla, densidad aparente y carbono orgánico SoilGrids ponderados0–30cm; pendiente media oficial.

EXPANDED30 añade NDVI mensual S2 abril/junio–octubre, media/std históricos FAPAR, seis propiedades SoilGrids0–30cm (N,CEC,pH,arena,fragmentos gruesos,limo), elevación media, std de pendiente, NPP total y momento del máximo de NPP. La lista exacta se guarda en el diseño y en el diccionario de30 variables. No incluye NDVI S2 mayo directo ni coordenadas. Estas elecciones están motivadas por definiciones y exploraciones anteriores; no son variables descubiertas mediante una selección nueva independiente de Y.

Se comparan originales estandarizadas y PCA3/5/8, limitada por rango numérico y tamaño del entrenamiento; los scores PCA vuelven a estandarizarse como en la representación local original. Todas las transformaciones pequeñas se ajustan dentro del entrenamiento aplicable. Base: Ridge geográfica24, alfa30 y pesos originales. Se reajusta Elastic Net compacto con el mismo grid12 y amplitud0/.25/.5. Se reportan las ocho recetas fijas y un selector de modo por conjunto, utilizando OOF internas de cada experto completo ya retuneado dentro de A_j. Alfa local no se optimiza: los resultados son para esta receta, no un óptimo universal.

## C: correcciones pequeñas sobre C-T3

Para cada conjunto12/30, Ridge residual con alfa normalizado1/.1/.01 y amplitud0/.25/.5; se selecciona modo y regularización sobre OOF internas completas. Los targets internos proceden de C-T3 profundo que excluye los casos retenidos. Comparadores: coordenadas como Ridge residual; estado/municipio como medias residuales de categoría con20 pseudoobservaciones y centrado. Una categoría nueva recibe corrección0. Las medias no se calculan con el fold externo.

## D: señales GeoC para distribuir confianza

Se conserva el experto completo y C-T3. Se prueba clusterizar cada conjunto12/30 en su representación original/PCA3/5/8, K4/8 y pesos contraídos como en la fase anterior. La referencia emparejada es la mezcla global aprendida, no simplemente superar el experto completo.

Controles de contexto: coordenadas con el mismo gate por clusters; estado y municipio con peso por categoría contraído mediante20 pseudoobservaciones. Una categoría inédita recibe el peso global de entrenamiento. Esto no garantiza acertar un municipio nuevo: expone el límite en lugar de asignarle una etiqueta aprendida con su target.

## E: reemplazar al experto grande manteniendo la mezcla

Se reemplaza el experto de1831 por cada conjunto12/30, usando el mismo gate físico BOTH (textura/fase y geología) y un control de mezcla global. Modo de representación y K del gate se seleccionan conjuntamente sobre OOF internas de la mezcla completa. Para cada candidato de representación fija, el experto dentro de A_j tiene EN retuneado solo allí; sus OOF de entrenamiento se regeneran con A_j menos D_k. No se selecciona modo mirando folds externos. La referencia es el gate BOTH o global con experto completo, según corresponda.

## Anidamiento, pruebas y límites

Se mantienen65 particiones externas e internas originales. Para gate/corrector se obtienen OOF honestas del experto completo y C-T3 dentro de cada entrenamiento. Se reutiliza en lectura el cache original compatible, con train IDs y protocolo exactos. Modelos nuevos se guardan en un directorio nuevo. Se conserva el fallback previamente definido: cuando el anidamiento agrupado no permite retunear el EN compacto, usar solo la base local; nunca cambiar a validación aleatoria. Se auditan esos contextos y el desajuste por tamaño de entrenamiento.

Se verifica reproducción del experto original y de su PCA. Pruebas de invariancia frente a etiquetas externas para el experto reducido completo, categorías nuevas, media geográfica y rango de PCA. Las representaciones y máscaras se fijan antes de entrenar. No hay nuevos screenings posteriores al resultado de ablaciones dentro de esta fase.

Métricas: RMSE, MAE, sesgo y R² sobre OOF completas por repetición; aleatoria media10 repeticiones, sin promedio de RMSE por fold. Se reportan errores por estado/municipio/bloque, diferencias intraperfil con ambos pesos, omisiones sin reajustar, ganancias por parcela, modos y pesos. Cada receta tiene un único contraste primario emparejado: bases locales con FULL_LOCAL, combinaciones con LEADER, correctores con C-T3, gates con mezcla global y sustituciones con la mezcla correspondiente del experto completo. Se aplicará Holm a esos contrastes×4 protocolos, bootstrap5000 por conglomerados y signos de pérdida cuadrática. Los intervalos son exploratorios de predicciones fijas; no corrigen búsqueda histórica, dependencia espacial residual ni incertidumbre total de reentrenamiento.

Las variables agronómicas derivadas son proxies; forma temporal no equivale a fechas observadas de siembra. Las ventanas tardías son retrospectivas. Un fallo de una ablación no identifica un efecto causal ni una única variable imprescindible; puede haber sustitutos correlacionados. Un resultado pequeño o regional no justifica promoción automática.

No se ejecuta GeoC97/41, no se modifica GeoC/Champion/archivos anteriores, no se ajusta final138 ni se generan nuevas59PRED. Entregables versionados en `outputs/modeling/geoc_signal_research/v1`; código436–438 y posteriores. Outputs sigue excluido de Git. No se hace push automáticamente.
