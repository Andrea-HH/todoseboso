# Tres líneas sobre el local sin clima + corrector compacto

## Resultado y decisión

Se ejecutaron las tres fases autorizadas sobre los 65 folds originales. La mezcla de expertos condicionada por características físicas es la línea más prometedora de esta ejecución. Cambiar los vecinos de la base local y añadir una segunda corrección residual no ofrecen el mismo equilibrio.

El candidato `P1_BOTH_clusters` combina C-T3 con la combinación anterior mediante pesos aprendidos por clusters de textura/fase y geología. Su RMSE aleatorio es 0.4852, municipal 0.5847 y espacial 0.6811. Mantiene buena parte de la precisión de la combinación anterior y reduce considerablemente su deterioro territorial, quedando cerca de los valores puntuales de C-T3 en municipal/espacial. Esto no demuestra equivalencia ni superioridad estadística.

La mezcla por textura/fase sola obtiene el menor RMSE aleatorio de esta batería (0.4805) y perfil 0.4876, con más deterioro territorial. Ambos son candidatos exploratorios. No se declara nuevo Champion, no se ajusta modelo final ni se reemplazan las 59 predicciones.

## Qué se ejecutó y cómo se protegió la evaluación

Diseño previo: `documentation/conditional_local_phases_design.md`. Se conservaron las referencias, PCA20 no climático original, particiones externas e internas y grids compactos. No se añadieron fuentes, coordenadas o municipios al espacio físico. Textura y fase son categorías cartográficas; geología usa fracciones litológicas y distancias a estructuras. Pueden seguir funcionando como proxies territoriales y no se interpretan causalmente.

Se obtuvieron OOF de la combinación completa, no solo de su base local. Para entrenar un gate o segundo corrector dentro de un entrenamiento interno se regeneraron las OOF del experto completo únicamente allí, con su Elastic Net reajustado/seleccionado sin las etiquetas retenidas. C-T3 profundo se recuperó de caches congelados con exclusiones por ID verificadas. Una prueba cambia los rendimientos externos y verifica que la combinación ajustada no cambia.

El anidamiento agrupado profundo tiene poco soporte en algunos casos espaciales. Se fijó antes del ajuste retirar el corrector compacto y usar solo base local cuando no hay suficientes grupos para seleccionar otra vez su regularización, sin sustituir por validación aleatoria. Es un comportamiento explícito del pipeline en poco soporte, registrado en `audit/deep_fallbacks.csv`. Puede introducir desajuste entre los residuos de entrenamientos profundos pequeños y el experto externo más completo; debe considerarse al interpretar los metamodelos.

Los espacios físicos se reajustan dentro de cada entrenamiento. La base local conserva la PCA transductiva sobre las 197 X de la referencia: no es una evaluación inductiva para X desconocido. Se trabajó solo con los 138 rendimientos disponibles. Los folds ya informaron investigaciones anteriores: esta ejecución no es una confirmación independiente.

## Comparación principal: RMSE en t/ha

| Modelo | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| C-T3 | 0.5116 | 0.5206 | 0.5813 | 0.6788 |
| Local04D original, referencia | 0.4930 | 0.5031 | 0.7602 | 0.9794 |
| LEADER: local sin clima + corrector compacto | 0.4879 | 0.4971 | 0.6613 | 0.8026 |
| P1 mezcla con peso global aprendido | 0.4855 | 0.4991 | 0.6031 | 0.7038 |
| P1 clusters de textura/fase | 0.4805 | 0.4876 | 0.5929 | 0.7039 |
| P1 clusters de geología | 0.4853 | 0.4955 | 0.5839 | 0.6846 |
| P1 clusters de textura/fase + geología | 0.4852 | 0.4996 | 0.5847 | 0.6811 |
| P1 selector interno | 0.4838 | 0.4904 | 0.5818 | 0.7087 |
| P2 control geográfico emparejado | 0.5031 | 0.5088 | 0.7634 | 0.8917 |
| P2 vecinos físicos de geología | 0.5057 | 0.6090 | 0.7754 | 1.1500 |
| P2 vecinos mixtos de geología | 0.5043 | 0.5056 | 0.7367 | 0.8383 |
| P2 selector interno | 0.5061 | 0.5117 | 0.8876 | 0.9204 |
| P3 vecinos de textura/fase sobre residuos restantes | 0.4881 | 0.4952 | 0.6881 | 0.7717 |
| P3 selector interno | 0.4897 | 0.4977 | 0.6921 | 0.8501 |

Cada RMSE procede de OOF completas por repetición; aleatoria es la media de diez repeticiones. No son promedios de RMSE por fold. El libro contiene todas las variantes, MAE, sesgo, R², pesos y selecciones. No se evaluó GeoC97/41 en esta fase, por lo que no se afirma superar allí el 0.4929 del candidato anterior.

## Fase1: distribuir la confianza funciona mejor que sumar otra corrección

La fórmula es:

`predicción = (1-w(z))*C-T3 + w(z)*(local_sin_clima + lambda*EN_compacto)`.

El peso entre cero y uno se aprende con OOF internas. Las predicciones de la mezcla están dentro del intervalo entre sus dos expertos; no introduce una extrapolación adicional entre ellos. Cada experto sí puede equivocarse fuera del soporte.

Se comparó peso global, peso por clusters con contracción de 20 pseudoobservaciones y peso que disminuye con distancia al soporte físico. Clusters4/8 y sensibilidad de soporte0/1/3 se eligieron internamente. Los clusters son específicos de cada entrenamiento; no son zonas agronómicas universales ni nombres de municipios codificados.

Con TEXTURE+GEOLOGY, el peso medio sobre la combinación anterior en las parcelas externas fue aproximadamente 67.4% en aleatoria, 69.9% por perfil, 5.2% municipal y 38.9% espacial. Son medias descriptivas de pesos por parcela y protocolo, no cuatro reglas elegidas manualmente ni pesos finales para las 59. Los pesos se aprendieron solo en entrenamiento y pueden variar entre cero y uno dentro de un mismo fold.

Frente a la mezcla global, `P1_BOTH_clusters` mejora los puntos municipal 0.6031→0.5847 y espacial 0.7038→0.6811; aleatoria cambia muy poco y perfil empeora ligeramente. Son comparaciones descriptivas de arquitectura, no contrastes independientes adicionales ni prueba de que los clusters sean superiores.

Su R² es 0.6725 aleatorio, 0.6530 por perfil, 0.5247 municipal y 0.3549 espacial. En espacial queda cerca del R²0.3594 de C-T3. Respecto a la combinación anterior, disminuyen tanto sesgo espacial (+0.4399→+0.2842) como dispersión del error. Frente a C-T3 todavía tiene más sesgo (+0.1912), compensado parcialmente por menor dispersión. Un RMSE parecido no implica los mismos errores.

## Concentración regional e intraperfil

La mejora espacial de BOTH-clusters frente al LEADER permanece al omitir cualquiera de los cinco bloques, sin reajustar. No se limita al bloque3. Sin embargo, sigue ligeramente peor que C-T3 en el agregado; omitir el bloque1 cambia el signo de esa pequeña diferencia, lo cual impide hablar de ventaja territorial uniforme.

La mejora municipal frente al LEADER se concentra más: al retirar un fold municipal, pasa de favorable a desfavorable. En Singuilucan, el RMSE baja de 1.3185 del LEADER a 0.9011, todavía por encima de 0.8677 de C-T3. En Chignahuapan cambia de 0.5605 a 0.5800, cerca de C-T30.5807; en Calpulalpan cambia de 0.4436 a 0.4799. La mezcla evita buena parte de una transferencia problemática, a costa de perder parte de las ventajas locales. No mejora todas las regiones.

No se resuelve de forma general la heterogeneidad intraperfil. Por ejemplo, BOTH-clusters aleatorio mejora RMSE de diferencias con igual peso de perfil frente a C-T3 (0.5900→0.5703), pero empeora ponderando por pares (0.7712→0.7765). Espacial muestra el mismo compromiso: 0.5401→0.5364 con igual peso y 0.7675→0.7697 por pares. No se atribuye al gate una explicación física universal de diferencias entre parcelas.

El selector completamente interno de P1 da 0.4838/0.4904/0.5818/0.7087. Es una evaluación del procedimiento de elegir gates, distinta de señalar retrospectivamente BOTH-clusters como candidato equilibrado. La ventaja puntual de un candidato escogido con estas OOF sigue siendo exploratoria.

## Fase2: cambiar vecinos no mejora esta receta

Se cambió la distancia de selección de vecinos, conservando los veinte componentes no climáticos como predictores Ridge. Cada k12/24/48 se evaluó como combinación completa con su Elastic Net reajustado internamente. Se incluyeron empates físicos completos para no diferenciar vectores idénticos por orden de filas.

Los pesos nuevos se normalizaron para separar distancia y escala de penalización, con alfa30 fijo. Por ello el control geográfico P2 no es idéntico al Local original: ya obtiene peores resultados antes de añadir distancia física. Frente a ese control, algunas mezclas físicas/geográficas mejoran municipal o espacial, pero ninguna receta P2 mejora el RMSE del LEADER en los cuatro protocolos.

El selector P2 da errores municipales/espaciales 0.8876/0.9204. No hay motivo para promoverlo. El resultado debilita la sustitución de vecinos con esta representación, ponderación y alfa, no toda posible regresión local física. No se abrió una búsqueda retrospectiva de penalizaciones para rescatarlo.

## Fase3: segunda corrección no se sostiene

Los correctores usan residuos del experto completo, generados con anidamiento propio. Se probaron Ridge, vecinos y grupos contraídos en tres espacios, con posibilidad de corrección cero. No se usaron residuos externos ni errores medios municipales como targets.

Hay ganancias parciales: vecinos de textura/fase baja espacial 0.8026→0.7717, pero empeora municipal 0.6613→0.6881. El selector P3 empeora los cuatro RMSE frente al LEADER. La evidencia no favorece añadir otra capa residual física a esta combinación ahora.

## Inferencia, auditoría y recomendación

Se realizaron 208 comparaciones exploratorias contra C-T3 y LEADER, bootstrap por conglomerados con 5,000 remuestras, cambios de signo de pérdidas cuadráticas y ajuste Holm dentro de esta fase. Ninguna queda significativa tras el ajuste. Las medias de RMSE, intervalos sin ajuste y pruebas de pérdida no deben mezclarse para afirmar superioridad. Solo cinco bloques espaciales limitan la resolución inferencial. No se corrige toda la búsqueda histórica ni la incertidumbre completa de reentrenamiento.

Recomendación: priorizar únicamente la línea de mezcla, con dos candidatos ya definidos: BOTH-clusters para equilibrio territorial y TEXTURE-clusters para mayor precisión aleatoria/perfil. Conservar C-T3 como referencia simple y territorial. Detener por ahora la expansión de vecinos físicos y segunda corrección. Antes de promover, congelar la receta y buscar evidencia adicional de estabilidad con particiones previamente fijadas y, preferentemente, rendimientos nuevos de otro ciclo o territorio. Repartir nuevamente las mismas 138 parcelas no equivale a disponer de una muestra externa independiente.

Se guardaron 26 recetas nuevas (incluidos tres selectores), 46,644 OOF nuevas y 3,588 OOF de referencias; 65 contenedores de modelos y el cache de expertos anidados. La ejecución de ajustes duró aproximadamente 22.8 minutos. Pasaron tres pruebas, incluyendo invariancia frente a etiquetas externas y fallback agrupado. Los detalles de reproducción exacta, exclusiones y fallbacks están en `manifest.json` y `audit/`.

Se registraron cuatro advertencias del entorno OpenMP y ninguna advertencia de convergencia en el registro de ajuste. Se mantuvieron OMP_NUM_THREADS y MKL_NUM_THREADS en1. La primera invocación de pruebas encontró un directorio temporal de Windows sin permisos; se repitieron exitosamente en un directorio temporal nuevo dentro del workspace, sin borrar archivos existentes.

Entregables: `outputs/modeling/conditional_local_phases/v1/resultados_tres_fases.xlsx`, tablas OOF, modelos, selecciones, pesos por parcela, intraperfil, errores regionales, omisiones y contrastes. Código: `src/conditional_local_phases.py`, scripts432/433/434 y pruebas correspondientes. Se conservan versiones anteriores. `outputs/` sigue excluido de Git; estos artefactos están en disco local.

No se modificaron Champion, C-T3 ni resultados anteriores; no se entrenó modelo final sobre138, no se generaron nuevas PRED59 y no se hizo push de esta fase.
