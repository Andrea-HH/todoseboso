# Correcciones de C-T3 por semejanza física: diseño antes del entrenamiento

## Preguntas

¿Pueden parcelas físicamente semejantes compartir errores de C-T3 aunque no sean vecinas geográficas? ¿La señal procede del entorno estático o del comportamiento satelital? ¿Las correcciones explican diferencias intraperfil y transfieren a territorios excluidos?

Se mantiene C-T3 original como base. No se añaden coordenadas, estado, municipio ni códigos administrativos a correctores. Las categorías de suelo, geología y erosión son atributos temáticos, aunque pueden actuar como proxies regionales; se diagnosticará esa concentración. Compartir píxel climático no elimina toda la dependencia geográfica.

## Auditoría y fuentes

Se recorre el inventario canónico de 1,557 columnas y sus fuentes originales/externas, las representaciones temporales recientes, las composiciones geológicas y de erosión, y las fuentes SoilGrids/NPP ya auditadas en GeoC. No se confunden nombres de variables con fuentes independientes. Se conserva el inventario completo y se seleccionan familias por procedencia, sin asociaciones con rendimiento.

Bloques estáticos: relieve sin elevación ni aspecto angular bruto; suelo INEGI; geología y fisiografía; SoilGrids; erosión. Altitud se mantiene como sensibilidad individual y queda fuera de las combinaciones y del selector general.

Bloques dinámicos: satélites 2025, historia/anomalías satelitales, NPP WaPOR 2025, ventanas satelitales 2025 y sus medias históricas. Se excluye NDVI mayo directo porque ya pertenece a C-T3; los agregados y otros sensores pueden conservar información correlacionada. No se afirma independencia de la señal climática ni del NDVI. Las ventanas tardías son retrospectivas: no se validan como predicción temprana.

El inventario v1, sin entrenamientos, detectó que hidrología no tiene distancias/densidades válidas en la extracción disponible y humedales solo tiene valores para dos parcelas. Se conserva esa auditoría y se congela v2 antes del primer ajuste de resultados. No se imputan estas fuentes como ausencia de agua; se difieren. Se descartan columnas con menos de 50% de cobertura X y constantes a tolerancia 1e-10. La revisión de esquema y alias utiliza X de las 138 parcelas, sin Y: no es un descubrimiento de esquema completamente ciego a X externo.

ENA y rendimientos FIRA se reservan como contexto, no como atributos físicos parcelarios. FIRA informa las ventanas ya construidas, sin asignar fechas de siembra individuales. Localidades se excluye de esta hipótesis; el mapa RGB de agua subterránea no se interpreta como propiedad calibrada. La documentación exclusiva de Chignahuapan no produce un predictor con cobertura comparable. No se reextraen ni reinterpretan fuentes brutas nuevas.

Suelo y erosión 1:250k describen unidades regionales; fracciones de intersección no son mediciones químicas ni porcentajes de erosión efectiva. SoilGrids es una estimación externa, no laboratorio parcelario. La geometría numérica única de una parcela tampoco prueba resolución física ni información predictiva útil.

## Representación y batería congelada

Cada bloque: mediana/one-hot, eliminación de constantes, estandarización, PCA de hasta cinco componentes y normalización a norma cuadrática media unitaria. Todo se reajusta exclusivamente dentro del entrenamiento aplicable. Categorías nuevas no generan columnas adicionales. Se mantienen las varianzas relativas de los componentes; no se blanquean. Los porcentajes de PCA describen X, no rendimiento.

Se comparan los once bloques disponibles y tres combinaciones predefinidas: físicos balanceados, dinámicos balanceados y todos los anteriores sin altitud. Cada combinación concatena representaciones atómicas con igual peso esperado por bloque. Escalar columnas cambia la geometría de las composiciones; estas distancias no son Hellinger puras.

Tres correctores por representación:

- Ridge sin intercepto, penalización n_train por alfa, alfa en 1, 0.1, 0.01.
- Vecinos por distancia euclídea en características, k en 12, 24, 48; pesos 1/(distancia+0.25). Todos los empates de frontera se incluyen para no separar vectores idénticos arbitrariamente.
- K-means con 4 u 8 grupos, cinco inicializaciones, semilla 2026; corrección de grupo igual a suma de residuos centrados dividida entre n_grupo+20. Es una contracción hacia cero.

Todos los correctores se centran por su predicción media de entrenamiento. Amplitud 0, 0.25 o 0.5. No se aprende un desplazamiento global libre ni reglas específicas por región. Se ajusta una familia de modelos de grupos; los grupos concretos varían entre entrenamientos y no deben etiquetarse como zonas agronómicas universales.

El mínimo MSE sobre OOF internas completas elige parámetros y amplitud; empates a 12 decimales favorecen amplitud cero/menor y después orden del grid. Además, INTERNAL_SELECTOR elige bloque y familia con esas mismas OOF internas; excluye la sensibilidad de altitud. Sus resultados externos evalúan el procedimiento de búsqueda, no un ganador escogido retrospectivamente.

## Anidamiento y evaluación

Se conservan los 65 folds y sus particiones internas. Para entrenar un corrector dentro de una partición interna, sus targets son residuos de C-T3 generados por las bases profundas congeladas, sin las etiquetas internas ni externas retenidas. El ajuste externo usa residuos cross-fitted del entrenamiento externo y la base externa original. Se verifica cada exclusión contra los IDs de los modelos archivados.

Las métricas se calculan sobre OOF completas por repetición, con media de diez repeticiones en aleatoria. Se reportan RMSE, MAE, sesgo y R², errores por estado/municipio/bloque espacial, diferencias intraperfil con dos ponderaciones y ganancias por parcela. Las omisiones de regiones recalculan métricas sin reajustar.

Se estudia el soporte físico del entrenamiento y la proporción de vecinos del mismo perfil/municipio como diagnóstico, sin usarlos para predecir o elegir amplitud. La concentración administrativa de grupos no demuestra causalidad. Se comparan también las referencias archivadas Local04D y la fase sin clima, con evaluación compatible.

La batería por bloque es exploratoria. Se harán contrastes pareados con conglomerados y Holm para las comparaciones con C-T3 de esta fase; no se corrige toda la búsqueda histórica. Con cinco bloques espaciales la resolución inferencial es limitada. Los mismos folds han informado muchas investigaciones: no se declarará confirmación independiente ni superioridad no demostrada.

No se ejecuta el banco GeoC 97/41 en esta primera batería: se prioriza la transferencia sobre los cuatro protocolos originales. Competir con Local04D en ese banco requeriría una evaluación posterior separada.

## Decisión y límites

Una mejora pequeña aleatoria no compensa automáticamente deterioro municipal/espacial. Se valoran ambos pesos intraperfil, frecuencia de corrección cero, dispersión de ganancias y sensibilidad a omitir regiones. No hay regla de promoción automática. Se podrá recomendar una prueba más compacta y específica si existe un patrón coherente, sin ejecutarla en esta fase.

Entregables en `outputs/modeling/physical_similarity/v2`: diseño/hash de entradas, auditoría de fuentes y columnas, modelos por fold, OOF, selecciones internas, soporte y grupos, comparaciones y reporte. La auditoría inicial v1 queda intacta y sin modelos.

No se modifica Champion/C-T3/GeoC ni resultados anteriores; no se ajusta un modelo final sobre las 138 ni se generan nuevas predicciones PRED.
