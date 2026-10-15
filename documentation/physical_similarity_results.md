# Exploración de fuentes y correcciones por semejanza física sobre C-T3

## Resultado principal

Se completó la exploración de fuentes disponibles y la primera batería congelada de modelado. Existe una señal complementaria interesante en geología, pero no se obtuvo una corrección que mejore de forma consistente los cuatro protocolos. No se declara un ganador ni se actualizan predicciones finales.

Los vecinos geológicos mejoran aleatoria, perfil y municipal, incluidas diferencias intraperfil, a costa de empeorar espacial. Los grupos geológicos ofrecen ganancias menores en esos tres protocolos y un deterioro espacial pequeño. Ridge geológico mejora municipal y espacial, pero pierde en aleatoria y su ganancia espacial depende especialmente del bloque 3. Ninguno supera la corrección por comparaciones múltiples de esta fase.

La selección interna entre todas las alternativas falla en transferencia espacial: no basta con tener una validación interna honesta para garantizar que permita seleccionar bien bajo un cambio fuerte de soporte físico.

## Qué datos se exploraron

La auditoría incluye el inventario canónico de 1,557 columnas, las carpetas originales/externas y sus documentos, ventanas temporales recientes, composición de erosión y fuentes SoilGrids/NPP previamente auditadas en GeoC. Es un censo de procedencia y preparación; no una reextracción completa ni una certificación nueva de cada archivo bruto.

| Bloque de modelado | Columnas retenidas | Lectura |
|---|---:|---|
| Relieve sin altitud | 81 | Descriptores continuos; no aspecto angular bruto |
| Altitud, sensibilidad separada | 11 | Excluida de combinaciones y selector general |
| Suelo INEGI | 28 | Composición, textura/fases y mezcla cartográfica |
| Geología | 13 | Diez fracciones de unidades y tres distancias a estructuras/fallas/fracturas |
| SoilGrids | 90 | Estimaciones externas de propiedades por profundidad |
| Erosión | 12 | Fracciones de clases cartográficas regionales |
| Satélites 2025 | 1,053 | Sentinel-2, Planet y Landsat; sin NDVI mayo directo |
| Historia/anomalías satelitales | 81 | Transformaciones existentes, no nuevas fuentes |
| NPP WaPOR 2025 | 11 | Productividad estimada, sin evapotranspiración |
| Ventanas satelitales 2025 | 40 | Ventanas agronómicas ya documentadas |
| Ventanas satelitales históricas | 40 | Medias históricas de ventanas comparables |

Son 1,460 columnas/representaciones retenidas, no 1,460 señales independientes ni un nuevo total global del proyecto. Las combinaciones balanceadas reutilizan estas columnas. Fisiografía se auditó pero no conservó contraste utilizable: las diferencias de fracciones dominantes eran redondeo de valores prácticamente uno. El nombre técnico `geology_physiography` conserva el plan de origen; la representación efectiva es geológica.

Hidrología no dispone de distancias o densidades válidas en la extracción actual; humedales solo tiene valores para dos parcelas. Se difirieron antes de ajustar resultados. Esto no demuestra irrelevancia agronómica: indica falta de soporte de los datos actuales. La auditoría inicial v1 queda intacta y sin entrenamientos; v2 registra esta corrección de cobertura antes de modelar.

ENA y rendimientos FIRA quedan como contexto. FIRA aporta la justificación de ventanas ya construidas, no fechas individuales observadas. Localidades y coordenadas no entran en correctores. El mapa RGB de agua subterránea requiere una representación física calibrada antes de tratarlo como propiedad medida. La documentación solo de Chignahuapan no ofrece cobertura comparable para esta prueba.

Las variables continuas distinguen muchas parcelas del mismo perfil, pero esto no prueba resolución real ni utilidad predictiva. Por ejemplo, suelo y geología incluyen distancias a límites que individualizan vectores aunque compartan clase. El archivo `audit/meaningful_composition_contrast.csv` separa diferencias composicionales de al menos diez puntos porcentuales del mero contraste numérico. Entre los 1,073 pares del mismo perfil, 40.6% tiene ese contraste en composición de suelo, 71.8% en geología y 62.4% en erosión. Son composiciones de categorías cartográficas, no diferencias químicas o de productividad. Los pares comparten parcelas y no son observaciones independientes. `audit/feature_ranges138.csv` documenta rangos, cuartiles, categorías y faltantes de las 1,460 entradas retenidas.

## Qué se ejecutó

Once bloques individuales, tres combinaciones —físicos, dinámicos y ambos— y tres tipos de corrector por representación: Ridge, vecinos de características y grupos K-means con contracción hacia cero. Son 42 recetas y un selector interno, sobre los 65 folds originales. Las correcciones usan los residuos honestos de C-T3 y amplitud interna 0, 0.25 o 0.5.

Imputación, one-hot, escalado y PCA hasta cinco componentes por bloque se reajustan en cada entrenamiento. En combinaciones, cada bloque tiene igual norma cuadrática media esperada. La selección del esquema y alias utiliza X de las 138, sin Y: no se presenta como descubrimiento de esquema completamente ciego a X externo. No se usan coordenadas ni etiquetas administrativas como entradas. Las características temáticas aún pueden funcionar como proxies territoriales.

Las medias históricas no se mezclan simultáneamente con CURRENT y DELTA de la misma representación. El bloque de historia/anomalías maestro se conserva como sensibilidad existente. Los agregados satelitales pueden compartir información con NDVI mayo y responder al clima; se evalúa complementariedad predictiva condicionada a C-T3, no independencia física.

## Resultados comparables: RMSE en t/ha

| Modelo | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| C-T3 | 0.5116 | 0.5206 | 0.5813 | 0.6788 |
| Local04D original, referencia archivada | 0.4930 | 0.5031 | 0.7602 | 0.9794 |
| C-T3 + vecinos geológicos | 0.4983 | 0.5069 | 0.5713 | 0.7111 |
| C-T3 + grupos geológicos | 0.5084 | 0.5146 | 0.5771 | 0.6830 |
| C-T3 + Ridge geológico | 0.5554 | 0.5179 | 0.5706 | 0.6615 |
| C-T3 + grupos de suelo INEGI | 0.5092 | 0.5198 | 0.5767 | 0.6934 |
| C-T3 + grupos de erosión | 0.5085 | 0.5230 | 0.5810 | 0.6789 |
| C-T3 + vecinos físicos combinados | 0.5089 | 0.5191 | 0.5823 | 0.6837 |
| C-T3 + grupos físicos combinados | 0.5102 | 0.5176 | 0.5800 | 0.6935 |
| C-T3 + Ridge físico combinado | 0.5128 | 0.5732 | 0.6991 | 1.2590 |
| Selector de bloque/familia completamente interno | 0.5089 | 0.5215 | 0.5950 | 1.2651 |

Aleatoria es la media de diez métricas calculadas sobre OOF completas por repetición. Los otros protocolos utilizan sus OOF completas. No son medias de RMSE de fold. El libro incluye todas las recetas, MAE, sesgo, R², complejidad de entrada, amplitudes y selección por fold.

No se ejecutó el banco GeoC 97/41 en esta fase. Las comparaciones con Local04D se restringen a los protocolos originales compartidos: los vecinos geológicos se acercan al local en aleatoria/perfil y mejoran su transferencia territorial, pero no se ha demostrado que mejoren su desempeño en el banco de ocultamiento 97/41.

## Complementariedad intraperfil y regional

Los vecinos geológicos reducen el RMSE de diferencias intraperfil con ambas ponderaciones:

| Protocolo | C-T3, igual perfil / por pares | Corrección geológica, igual perfil / por pares |
|---|---:|---:|
| Aleatoria | 0.5900 / 0.7712 | 0.5766 / 0.7685 |
| Perfil | 0.5479 / 0.7634 | 0.5309 / 0.7452 |
| Municipal | 0.5210 / 0.7688 | 0.5145 / 0.7624 |
| Espacial | 0.5401 / 0.7675 | 0.5547 / 0.8192 |

Esto apoya una señal que diferencia parcelas climáticamente semejantes, sin resolver su transporte a zonas físicas menos representadas. En municipal, Chignahuapan pasa de 0.5807 a 0.5674; Almoloya de 0.3529 a 0.2974; Calpulalpan cambia poco y Singuilucan permanece igual por corrección seleccionada cero. La mejora municipal de vecinos geológicos sobrevive descriptivamente al omitir cualquiera de los cinco folds municipales, sin reajustar. Las celdas de municipios con una o pocas parcelas no sostienen conclusiones propias.

No usar coordenadas no elimina dependencia geográfica. En aleatoria, los vecinos geológicos asignan aproximadamente 71.9% de peso a parcelas del mismo municipio y 32.0% al mismo perfil. Los grupos geológicos también concentran regiones; el diagnóstico por entrenamiento registra esa concentración. No se interpreta como efecto causal de roca o falla.

En espacial, aproximadamente 72.5% de las parcelas tiene una distancia a soporte geológico superior al percentil 90 de la distancia al vecino más próximo dentro del entrenamiento. Es un diagnóstico en la representación aprendida, no una probabilidad calibrada de extrapolación ni una regla correctora.

## Por qué no promover Ridge ni el selector

Ridge geológico reduce el RMSE espacial de 0.6788 a 0.6615, pero al omitir el bloque 3 la diferencia cambia a +0.0069 frente a C-T3: su ventaja agregada depende de ese bloque. Además, el sesgo espacial global aumenta de +0.1912 a +0.2883; disminuye la dispersión de errores, no el sesgo global. En aleatoria su RMSE sube a 0.5554.

El selector interno elige Ridge físico combinado para el bloque espacial 2. Allí su RMSE es 2.1329, frente a 0.5725 de C-T3. La descomposición del modelo fijo encuentra que la representación de erosión alcanza norma máxima 21.14 tras la normalización por bloque; su contribución media antes de amplitud es -2.5021 t/ha. Con amplitud 0.5, ese término aporta aproximadamente -1.25 t/ha de corrección media, parcialmente compensada por otros bloques.

Esta es extrapolación de una representación y una corrección lineal, no evidencia de que erosión realmente cause una pérdida de ese tamaño. El escalado de fracciones raras y el cambio de soporte son una hipótesis técnica a examinar. No se recortaron predicciones, cambiaron escalas ni ajustaron reglas tras observar el fold externo. Vecinos y grupos tienen respuestas acotadas por los residuos del entrenamiento y evitan ese mecanismo lineal particular, sin garantizar mejor predicción.

## Evidencia estadística y límites

Se realizaron 172 contrastes pareados exploratorios contra C-T3, bootstrap por conglomerados con 5,000 remuestras y cambios de signo de pérdidas cuadráticas. Se agrupa por perfil, municipio o bloque espacial según protocolo y se aplica Holm a esta fase. Ninguna comparación queda significativa tras ese ajuste. Los intervalos bootstrap sin ajuste y los p de pruebas de pérdidas responden a resúmenes distintos; no se combinan para declarar superioridad.

Con cinco bloques espaciales, el mínimo p bilateral exacto es 0.0625. La inferencia depende de predicciones fijas, no incorpora toda la variabilidad de reentrenamiento, no corrige la búsqueda histórica completa y los perfiles pueden seguir siendo espacialmente dependientes. Estos folds ya guiaron decisiones previas: no representan confirmación independiente.

## Recomendación

Conservar C-T3. Continuar solo de forma acotada con la hipótesis geológica: separar composición litológica de distancias a estructuras y estudiar una corrección contraída o acotada, con reglas fijadas antes de cualquier nuevo ajuste. Los grupos geológicos son el compromiso exploratorio más equilibrado de esta rama, con ganancias pequeñas; los vecinos aportan la evidencia intraperfil más clara, pero su deterioro espacial impide promoverlos.

La siguiente prueba debería contrastar si el beneficio viene de semejanza litológica o de un proxy territorial, y reducir la dependencia del escalado de clases raras. No conviene repetir una búsqueda extensa entre todos los bloques ni usar el selector actual para predicciones finales. Estos resultados no rechazan otras representaciones físicas ni toda corrección residual. No se ejecutó esa fase posterior.

## Reproducción y entregables

Diseño previo: `documentation/physical_similarity_design.md`. Scripts 425–428 y `src/physical_similarity.py`; pruebas en `tests/test_physical_similarity.py`. Orden: pruebas, 425, 426, 427 y 428. Los scripts protegen versiones ya completadas; para una reproducción desde cero se debe crear una versión nueva conservando configuración y hashes, sin sobrescribir estos artefactos.

Cuatro pruebas pasaron. Se guardaron 77,142 OOF nuevas de correcciones y 1,794 OOF de referencia C-T3, 65 contenedores de modelos por fold y las selecciones internas. La reproducción de todas las predicciones archivadas tuvo diferencia máxima cero. Se verificaron 1,018 contextos de exclusión de residuos y los hashes de fuentes protegidas.

El registro recoge cuatro advertencias del entorno OpenMP; no hubo fallo de ejecución ni advertencias de convergencia registradas. Se ejecutó con OMP_NUM_THREADS y MKL_NUM_THREADS iguales a uno. No se oculta esa advertencia ni se confunde con el problema predictivo de extrapolación.

Carpeta: `outputs/modeling/physical_similarity/v2/`. Libro: `resultados_semejanza_fisica.xlsx`. Auditoría por fuente/columna, soporte, grupos, errores regionales, omisiones y mayores cambios están en `audit/`, `tables/` y `diagnostics/`. No se modificaron modelos o resultados anteriores, no se entrenó un modelo final sobre 138 y no se generaron nuevas predicciones para las 59 parcelas.
