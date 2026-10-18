> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Representaciones físicas y dimensión seleccionada internamente

## Decisión

Se completó la batería autorizada. La representación importa: separar subbloques y revisar las composiciones evita repetir el extremo predictivo de la fase anterior, pero no produce un corrector que mejore consistentemente los cuatro protocolos. Se conserva C-T3 sin cambios ni nuevas predicciones PRED.

Dos candidatos exploratorios merecen seguimiento: textura/fase física cartográfica con vecinos, y grupos geológicos. El primero mejora espacial, municipal y aleatoria, con ligera pérdida por perfil; el segundo mejora aleatoria, perfil y municipal con pequeña pérdida espacial. Ninguna mejora supera el ajuste Holm de esta fase. La selección general entre todos los candidatos sigue sin resolver la transferencia espacial.

## Diseño ejecutado

Diseño previo: `documentation/physical_representation_design.md`. No se revisaron parámetros después de observar resultados. Son 14 subbloques: pendiente (14 columnas), relieve local (10), posición topográfica (12), curvatura (24), flujo/humedad del terreno (21), composición geológica (10), distancias geológicas (3), composición de suelo (20), textura/fase física (2), mezcla/límites de suelo (6), propiedades físicas SoilGrids (50), propiedades químicas SoilGrids (40), erosión (12) y altitud (11). Altitud se conserva solo como sensibilidad individual.

Cuatro combinaciones predefinidas: GEOLOGY, TERRAIN, SOIL y PHYSICAL_ALL, esta última sin altitud. No se añadieron datos nuevos, coordenadas, estados, municipios, clima ni satélites al corrector. El esquema hereda la auditoría X-only de las 138 de la fase anterior: no es una selección de esquema totalmente ciega a los predictores externos, aunque todas las transformaciones numéricas se reajustan dentro del entrenamiento correspondiente.

Cada bloque/familia selecciona entre variables originales, resúmenes físicos y PCA de hasta 1, 3, 5 u 8 componentes. Dimensión, parámetros y amplitud se seleccionan sobre OOF internas completas. Se conservan Ridge, vecinos físicos y grupos contraídos con los grids anteriores y amplitudes 0/0.25/0.5. Son 54 recetas bloque/familia, un selector general y seis controles que fijan el modo y eligen internamente bloque/familia: 61 recetas.

Los resúmenes retienen medias/desviaciones del terreno, pendiente >10 y propiedades SoilGrids 0–30 cm. Las distancias se comparan también en log1p. Las composiciones se usan como proporciones o raíces, sin división por frecuencia/desviación de cada clase ni norma RMS del bloque. PCA usa raíces centradas, sin blanqueo. En composiciones, “resumen” significa raíces sin PCA, no una agrupación inventada de clases. Las comparaciones entre controles de modo combinan esas decisiones con las transformaciones continuas; no aíslan un efecto causal único de PCA.

Se mantuvieron los 65 folds externos originales, las particiones internas y los residuos honestos profundos de C-T3. No se ejecutó GeoC97/41 ni un ajuste final sobre 138. Esta fase fue informada por resultados anteriores y no constituye confirmación independiente.

## Resultados principales: RMSE t/ha

| Modelo | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| C-T3 | 0.5116 | 0.5206 | 0.5813 | 0.6788 |
| Local04D, referencia archivada | 0.4930 | 0.5031 | 0.7602 | 0.9794 |
| C-T3 + vecinos de textura/fase física | 0.5087 | 0.5237 | 0.5748 | 0.6535 |
| C-T3 + grupos de textura/fase física | 0.5084 | 0.5209 | 0.5728 | 0.6761 |
| C-T3 + grupos geológicos combinados | 0.5091 | 0.5124 | 0.5640 | 0.6833 |
| C-T3 + vecinos de composición geológica | 0.5091 | 0.5221 | 0.5852 | 0.7331 |
| C-T3 + vecinos de distancias geológicas | 0.5036 | 0.5162 | 0.5776 | 0.7384 |
| C-T3 + vecinos geológicos combinados | 0.4985 | 0.5126 | 0.5911 | 0.7336 |
| C-T3 + Ridge físico combinado | 0.5139 | 0.5264 | 0.5756 | 0.6970 |
| Selector interno completo | 0.5091 | 0.5197 | 0.5906 | 0.7579 |

Aleatoria promedia diez métricas calculadas sobre OOF completas por repetición; las demás utilizan OOF completas. No se promedian RMSE por fold. MAE, sesgo, R², errores regionales y amplitudes están en los archivos completos.

Las recetas destacadas se identifican exploratoriamente a partir de resultados externos. No se presenta su selección como validación independiente. El resultado del selector general es la evaluación del procedimiento de búsqueda interna; no valida la promoción retrospectiva de uno de sus competidores.

## Qué aprendemos sobre la dimensión

Los controles MODE fijan una estrategia y seleccionan bloque y corrector internamente:

| Estrategia | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| Resumen físico | 0.5104 | 0.5196 | 0.5929 | 0.7518 |
| PCA hasta 1 | 0.5075 | 0.5198 | 0.5862 | 0.7044 |
| PCA hasta 3 | 0.5049 | 0.5118 | 0.5710 | 0.7476 |
| PCA hasta 5 | 0.5059 | 0.5207 | 0.5803 | 0.7644 |
| PCA hasta 8 | 0.5070 | 0.5215 | 0.5941 | 0.7375 |
| Originales | 0.5059 | 0.5264 | 0.5828 | 0.7352 |

PCA5 no era una elección universalmente óptima. PCA3 obtiene mejores puntos que PCA5 en los cuatro protocolos de estos controles, pero sigue empeorando espacial frente a C-T3. PCA1 tiene el menor error espacial de los controles de modo y aun así pierde frente a C-T3. Conservar más componentes o todas las variables tampoco resuelve el problema.

La cantidad efectiva se limita por dimensión y tamaño del entrenamiento. En combinaciones se usa el mismo tope por subbloque; no se exploró el producto cartesiano de cantidades distintas para cada subbloque. Los resúmenes y PCA seleccionados describen una búsqueda acotada, no el óptimo global de las señales físicas. La varianza explicada guardada en `components_by_fold.csv` corresponde a X, no al rendimiento.

## Textura/fase física: mejora espacial con límites

Este candidato añade dos campos cartográficos a la base de cuatro variables. Son categorías de textura dominante y fase física dominante, no mediciones de laboratorio ni dos variables continuas con orden numérico. Se codifican dentro del entrenamiento y se comparan representaciones. Existen siete combinaciones observadas: frecuencias 54, 1, 4, 20, 15, 21 y 23. Algunas tienen poco soporte; los vecinos incluyen todos los empates físicos y no separan arbitrariamente vectores iguales.

Vecinos de textura/fase reduce el RMSE espacial 0.0253 t/ha y MAE de 0.5306 a 0.5180; R² aumenta de 0.3594 a 0.4062. Su sesgo global espacial apenas cambia: +0.1912 a +0.1891; la mejora agregada procede principalmente de menor dispersión de errores.

Por bloque espacial, el RMSE de C-T3 frente al corrector es: bloque1 0.5054/0.5581; bloque2 0.5725/0.5856; bloque3 0.9096/0.8123; bloque4 0.7990/0.7039; bloque5 0.3602/0.4896. Hay mejoras importantes en 3 y 4, y deterioro en 1, 2 y 5. Al omitir el bloque3, la diferencia global se vuelve +0.0101 en contra del corrector. La mejora municipal tampoco sobrevive a todas las omisiones de folds.

Además, su RMSE intraperfil espacial empeora bajo ambas ponderaciones: igual perfil 0.5401 a 0.5426 y por pares 0.7675 a 0.7993. Por tanto, no es evidencia de una solución robusta a la heterogeneidad intraperfil espacial: puede corregir niveles compartidos de algunos grupos físicos/regionales. No se infiere causalidad ni se añaden reglas por bloque.

## Geología: separar composición y distancias cambia la interpretación

Las distancias geológicas por sí solas recuperan una parte de la mejora aleatoria y por perfil observada antes; las fracciones litológicas por sí solas dan ganancias menores con vecinos. Ninguna ofrece transferencia espacial favorable. La separación debilita interpretar el beneficio anterior como efecto demostrado de la composición de roca: distancias y semejanza territorial también intervienen. No permite cuantificar causalmente la contribución de cada señal.

Los grupos geológicos combinados son más equilibrados: municipal 0.5640 frente a 0.5813 de C-T3 y MAE 0.4297 frente a 0.4603. La ganancia municipal sobrevive descriptivamente a omitir cualquiera de los cinco folds municipales. En espacial quedan en 0.6833, ligeramente peor que 0.6788.

Hay un contraste relevante: grupos geológicos mejoran las diferencias intraperfil espaciales bajo ambos pesos (igual perfil 0.5401 a 0.5295; pares 0.7675 a 0.7096), pero aumenta el sesgo espacial global de +0.1912 a +0.3487. Capturar diferencias relativas no garantiza acertar los niveles absolutos. No se corrige ese sesgo con la media del fold externo: sería utilizar etiquetas de evaluación.

## Extrapolación y advertencias

No se reprodujo el extremo del Ridge físico anterior en bloque2: RMSE pasa de 2.1329 en aquella receta a 0.6251 en la nueva, con C-T3 en 0.5725. La prueba unitaria verifica que una clase composicional ausente en entrenamiento no recibe una división por una varianza minúscula. Cambiaron también subbloques, ponderación y selección dimensional; no se atribuye toda la diferencia a un único cambio de escalado.

El selector general mejora frente a su versión anterior (espacial 1.2651 a 0.7579), pero sigue por detrás de C-T3. Seleccionar internamente sigue siendo necesario, sin garantizar buena selección ante cambio territorial.

Se registraron 107 advertencias durante los ajustes: 103 de K-means por obtener menos grupos distintos que los solicitados ante puntos duplicados o numéricamente equivalentes, y cuatro del entorno por coexistencia de bibliotecas OpenMP. No se alteró el número de grupos ni se reejecutó el grid después de ver resultados. Las advertencias de K-means no equivalen a 103 fallos de predicción, pero impiden interpretar literalmente cada solicitud de ocho grupos como ocho regímenes distintos. Todos los resultados guardados son finitos y se reproducen exactamente. El registro por fold se conserva en los checkpoints.

## Inferencia y recomendación

Son 244 contrastes exploratorios contra C-T3, con bootstrap por conglomerados de 5,000 remuestras, cambios de signo de pérdidas y Holm dentro de esta fase. No hay comparaciones significativas después del ajuste. En particular, la diferencia espacial de textura/fase tiene intervalo bootstrap [-0.0851, +0.0496] t/ha. Cinco bloques limitan fuertemente la inferencia espacial. Las predicciones son fijas, las repeticiones/pares son dependientes y no se corrige toda la búsqueda histórica.

Recomendación: conservar C-T3 y cerrar la expansión amplia de representaciones físicas. Si se continúa, reducir a dos hipótesis previamente fijadas: textura/fase física con corrección contraída y grupos geológicos para diferencias relativas. Exigir estabilidad al retirar regiones y una evaluación independiente adecuada antes de promoverlas. No seguir aumentando automáticamente componentes, bloques o algoritmos. Estos resultados no rechazan todas las señales físicas ni demuestran superioridad de un candidato.

## Entregables y reproducción

Carpeta `outputs/modeling/physical_representation/v1/`; libro `resultados_representacion_fisica.xlsx`. Diseño/hash, subbloques, modelos por fold, todas las selecciones/tuning y OOF se conservan. Scripts: 429 preparar/ejecutar, 430 sintetizar y 431 auditar/entregar sin reajustes; implementación `src/physical_representation.py`; siete pruebas de la implementación nueva y del corrector reutilizado pasaron.

Se generaron 109,434 OOF nuevas de correcciones más 1,794 de C-T3 recuperado. Son 65 contenedores de modelos externos, no un entrenamiento final. La auditoría verifica exclusiones de residuos, integridad de fuentes y reproducción de predicciones. Los detalles finales están en `manifest.json`. La ejecución de modelos duró aproximadamente 201 segundos, además de síntesis y auditoría.

No se modificaron resultados anteriores, Champion, C-T3 ni GeoC. No se entrenó un modelo final sobre las 138 ni se generaron nuevas predicciones para las 59 parcelas.
