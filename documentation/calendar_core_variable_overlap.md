# Exploracion de predictores: C-T3 y EN_CAL02

Analisis descriptivo de las 138 parcelas TRAIN, sin ajustar modelos predictivos ni seleccionar variables. Script: `scripts/406_explore_calendar_core_variables.py`. Tablas: `outputs/research/calendar_core_variable_overlap/v1/`. Se conserva la ponderacion por parcela y una sensibilidad con igual peso a cada uno de los 43 perfiles del cache TRAIN utilizado. Las medias de NDVI y rendimiento por perfil en esta sensibilidad describen diferencias entre perfiles, no relaciones intraperfil. No incluye PRED.

## Entradas y equivalencias

C-T3 tiene tres resumenes de lluvia abril-octubre y NDVI de mayo. EN_CAL02 tiene cuatro lluvias por ventanas (abril, mayo-junio, julio-agosto, septiembre-octubre), cuatro Tmax medias ponderadas por dias en esas ventanas y el mismo NDVI. La union contiene 12 columnas, al compartir exactamente NDVI.

- Total compacto = suma de las cuatro lluvias: diferencia numerica maxima 2.27e-13 mm.
- Fraccion temprana = (lluvia abril + lluvia mayo-junio)/(total + 1e-6): diferencia maxima 1.67e-16.
- HHI compacto = suma de cuadrados de las siete fracciones mensuales. Las cuatro ventanas no permiten reconstruirlo en general, porque pierden la distribucion dentro de cada bimestre.
- La fraccion temprana es una transformacion no lineal de las ventanas; aunque no incorpora una nueva medicion, puede ser una base funcional util para un modelo lineal.
- Total y ventanas tienen una dependencia lineal exacta. La matriz estandarizada de 12 columnas tiene rango 11. Esto no implica 11 fuentes independientes; existen otras correlaciones fuertes y dependencias no lineales.

## Redundancia

Correlacion Pearson por parcela: total con lluvia mayo-junio .907, julio-agosto .973, septiembre-octubre .920. Julio-agosto y septiembre-octubre .967. La correlacion fraccion temprana-Tmax abril es .888: temperatura y distribucion de lluvia no son bloques independientes. Dando igual peso por perfil, las cuatro primeras correlaciones son .932, .976, .946 y .976; el solapamiento no se explica solamente por repetir parcelas del mismo clima.

Las Tmax no duplican exactamente las lluvias, pero su margen observado entre parcelas es estrecho: abril 25.734-26.218 C; mayo-junio 23.841-24.773; julio-agosto 22.608-23.635; septiembre-octubre 21.748-22.736. Diferencias pequenas pueden actuar como indicadores geograficos; no inferir sensibilidad agronomica causal o transferencia fuera del soporte.

## Asociaciones marginales con rendimiento

| Variable | Pearson por parcela | Igual peso por perfil |
|---|---:|---:|
| Total lluvia | -.469 | -.546 |
| Fraccion temprana | -.614 | -.534 |
| HHI mensual | -.697 | -.667 |
| NDVI mayo | .558 | .597 |
| Lluvia mayo-junio | -.682 | -.714 |
| Tmax abril | -.633 | -.636 |
| Tmax mayo-junio | .203 | .176 |

Estas asociaciones son descriptivas, no significancia estadistica ni efecto incremental. La asociacion negativa lluvia-rendimiento no demuestra perjuicio causal de la lluvia: mezcla territorios, perfiles y posibles diferencias de manejo. Tampoco es un R2 validado. Como indicio de correlacion entre predictores, lluvia abril tiene correlacion marginal negativa (-.524), pero efecto estandarizado mediano positivo (+.513) en los ajustes aleatorios archivados de EN_CAL02; el signo condicional responde al conjunto de predictores.

## Diferenciacion intraperfil

Hay 43 vectores climaticos distintos en este conjunto TRAIN; 12 perfiles tienen multiples parcelas. Ninguna de las 11 variables climaticas de la union varia dentro de esos perfiles. NDVI mayo varia en los 12 y tiene 130 valores distintos entre las 138 parcelas. Agregar estas ventanas o Tmax cambia la representacion entre perfiles, pero no crea resolucion climatica entre parcelas del mismo perfil. NDVI distinto tampoco garantiza rendimiento predecible distinto.

## Seleccion archivada, sin nuevos ajustes

En los 50 folds aleatorios de EN_CAL02, lluvia abril, lluvia mayo-junio, Tmax abril, Tmax mayo-junio y NDVI mayo tienen coeficiente no nulo en el 100%. Las demas aparecen en 56-70%. Esto describe estabilidad dentro de EN_CAL02, no la supervivencia en una union aun no entrenada, ni prueba de utilidad independiente.

## Implicacion para una union futura

Evitar interpretar las 12 columnas como 12 aportaciones nuevas. La lluvia total puede omitirse como dependencia lineal exacta si se conservan las cuatro ventanas. Fraccion temprana y HHI plantean una pregunta diferente: si sus transformaciones ayudan al modelo lineal. Conservar un control que permita distinguir ese efecto de agregar Tmax. Cualquier ajuste de Elastic Net, seleccion de columnas o comparacion predictiva requiere el protocolo anidado congelado; esta exploracion no elige una combinacion ganadora. Los coeficientes y sus signos pueden repartirse o cambiar entre predictores correlacionados.
