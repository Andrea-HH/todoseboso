# Tres fases: expertos condicionales, vecinos físicos y segunda corrección

Diseño congelado antes de entrenar. Se mantiene como referencia exacta el local sin clima + corrector compacto (LEADER) y C-T3. El primero es un candidato exploratorio, no un nuevo Champion promovido. No se modifican archivos previos, modelos finales ni las 59 predicciones.

## Información común y límites

Se reutilizan las 65 particiones externas y sus cuatro particiones internas congeladas. Físicas: textura/fase cartográfica de suelo y geología, separada en fracciones litológicas y distancias a estructuras/fallas/fracturas. No se agregan fuentes ni se ejecuta screening. La selección de esos bloques está informada por fases anteriores: no es confirmación independiente.

Espacios predefinidos: TEXTURE, GEOLOGY y BOTH. Textura/fase usa one-hot centrado sin dividir categorías raras por su desviación. Geología usa raíces de fracciones y log1p de distancias estandarizadas. Los subbloques se concatenan con factor 1/sqrt(B). Todo el espacio físico se reajusta en cada entrenamiento correspondiente. No entran coordenadas o identificadores administrativos al espacio físico, aunque puede retener estructura territorial. Las categorías cartográficas no son laboratorio ni efectos causales.

El Local original conserva su PCA20 transductivo sobre X de las 197, k24, alfa30 y pesos geográficos originales. Es la misma información X de la referencia; no una representación inductiva para X desconocido. Ningún rendimiento externo interviene en sus ajustes o selectores.

## Anidamiento del experto completo

Para entrenar pesos o una segunda corrección se necesitan OOF de toda la combinación: base local y Elastic Net compacto seleccionado internamente. No se reciclan residuos de la base local como si fueran residuos del experto completo.

Para evaluar en un fold externo E, el gate/corrector se selecciona en los B_j internos. Para entrenarlo dentro de A_j, se regeneran OOF del experto completo solo con A_j; cada entrenamiento A_j menos D_k vuelve a seleccionar su Elastic Net sin D_k, B_j o E. Se conserva su grid original de 12 combinaciones y amplitud 0,0.25,0.5. Las predicciones C-T3 profundas se recuperan de sus caches congelados y se verifican por IDs.

En espacial, algunos entrenamientos profundos tienen dos grupos. Seleccionar el corrector compacto con el mismo anidamiento requeriría subdividir un solo grupo. Se fija previamente fallback a base local sin corrector en esos contextos; nunca GroupKFold se sustituye por KFold aleatorio. También se retira el corrector si un ajuste local profundo tendría menos de tres observaciones; una base original con menos de tres devuelve media de entrenamiento. Cada caso se registra. Esto modifica el comportamiento en situaciones de poco soporte profundo, no la referencia externa con soporte suficiente. Sus diferencias de tamaño de entrenamiento pueden influir en los targets del metamodelo y se declaran como limitación.

## Fase1: mezcla de expertos

Predicción = C-T3 + w(x)*(LEADER-C-T3), con w entre 0 y 1. Se comparan:

- GLOBAL: ponderación global aprendida por mínimos cuadrados sobre OOF internas, acotada a [0,1].
- Clusters físicos: K-means4 u8, peso óptimo por grupo contraído hacia el global mediante 20 pseudoobservaciones y la diferencia cuadrática media de los expertos. Se limita el número de grupos a vectores distintos con tolerancia de redondeo1e-10.
- Soporte físico: w(x)=w_global/(1+gamma*d_min/escala), gamma0,1,3. Escala es la mediana de distancias positivas al vecino de entrenamiento más próximo, excluyendo self. Si no hay positivas, escala1. La fórmula prueba, sin presuponer su éxito, reducir confianza en LEADER lejos del soporte.

Se evalúan clusters y soporte en los tres espacios: siete recetas, más un selector interno entre ellas. Los pesos de cada entrenamiento interno se aprenden con OOF de expertos generadas solo allí. Los expertos aplicados a B_j se ajustan solo con A_j.

## Fase2: cambiar vecinos de la base

La regresión base sigue utilizando los mismos veinte componentes no climáticos. Cambia quién es vecino y su peso: geografía como control metodológicamente emparejado, distancia física sola y mezcla .5física+.5geográfica en cada espacio. Distancias se normalizan con soporte de entrenamiento; se incluyen todos los empates en el vecino k. Pesos 1/(distancia+.25), normalizados para sumar al número de vecinos efectivo; Ridge alfa30. Evita confundir cambios de unidades con cambios de penalización. Este control geográfico difiere de los pesos originales de Local04D y debe compararse con los vecinos nuevos antes de atribuir efectos a la distancia física.

k12,24,48 se selecciona dentro del entrenamiento. Para cada k se evalúa la combinación completa sobre OOF internas: cada experto A_j vuelve a seleccionar Elastic Net compacto usando solo A_j. El corrector se reentrena con residuos de su nueva base; no se reutiliza el corrector del Local original. Siete recetas más selector interno. No se vuelve a ajustar PCA20 de la referencia para aislar esta línea de arquitectura; el alcance sigue siendo transductivo.

## Fase3: segunda corrección del LEADER

Predicción = LEADER + lambda*f_físico, lambda0,.25,.5. Comparadores: Ridge, vecinos físicos y clusters con contracción, usando los grids de la fase física anterior: alfa normalizado1,.1,.01; k12,24,48; clusters4,8 con contracción n/(n+20). Las predicciones de correctores se centran por su media de entrenamiento; no se aprende desplazamiento global libre.

Los targets son y-OOF_LEADER, regenerados dentro de cada entrenamiento del corrector. Nueve recetas más selector interno. No se usan residuos del Champion ni etiquetas externas para aplicar correcciones por municipio o bloque.

## Selección, métricas y auditoría

Total26 recetas nuevas (incluidos tres selectores), más CT3 y LEADER recuperados/reproducidos. Parámetros se eligen por MSE sobre OOF internas completas; empates usan orden del grid y, en correctores, amplitud menor. El selector entre recetas usa MSE interno y nombre lexicográfico para desempatar. No se escoge un ganador por bloques externos ni se presenta su resultado como confirmación independiente.

RMSE, MAE, sesgo y R² sobre OOF completas por repetición; aleatoria media diez repeticiones. Diferencias intraperfil con igual peso de perfil y por pares; errores por estado/municipio/bloque espacial; omisiones sin reajustar; ganancias y deterioros por parcela; pesos, k, amplitudes y fallbacks. La referencia LEADER debe reproducirse por fold con diferencia <=1e-12.

Comparaciones exploratorias pareadas contra CT3 y LEADER: 26×2×4=208, bootstrap5000 por perfil/municipio/bloque y signos de pérdidas, Holm dentro de esta fase. Los pares/repeticiones son dependientes; solo cinco bloques espaciales limitan inferencia. No corrige la búsqueda histórica ni incertidumbre completa de reentrenamiento. Se valorará consistencia territorial antes que pequeñas ganancias aleatorias.

No se ejecuta el banco GeoC97/41, no se promueve Champion, no se ajusta final138 ni se generan PRED59. Entregables versionados bajo `outputs/modeling/conditional_local_phases/v1/`, scripts432 y posteriores, implementación `src/conditional_local_phases.py`. El cache anidado puede ser costoso, pero evita compartir etiquetas entre contextos incompatibles.
