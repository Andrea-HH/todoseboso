# Reducción de indicadores y correcciones por vecindario

## Qué se probó

Se conservaron las 65 particiones externas originales y las bases C-T3 y J7_BOTH. Se ejecutaron 34 recetas nuevas, 2,210 sistemas externos, sin entrenamiento final sobre 138 ni predicciones PRED59. Las métricas se calculan sobre OOF completas de cada repetición y luego se promedian; no se promedian RMSE de folds. Son comparaciones exploratorias sobre particiones ya utilizadas, no una confirmación independiente.

Antes de esta etapa, los indicadores temporales corregían o ponderaban globalmente: no definían vecinos satelitales. J7 ya contenía un experto de 24 vecinos geográficos y una mezcla física. Ese mecanismo original se conserva. Esta etapa agrega un segundo mecanismo de corrección, comparando vecinos geográficos, físicos y satelitales.

Distancias: GEO usa centroides; PHYSICAL usa textura/fase, geología y relieve (altitud, pendiente media y TPI); SATELLITE usa únicamente mínimo histórico de NDVI, mínimo histórico de FAPAR y persistencia del exceso de heterogeneidad NDVI (media–mínimo relativos) de 2025 frente a su propia historia. No es una distancia sobre todas las series satelitales. Las coordenadas no entran en las dos últimas distancias, aunque sus variables pueden reflejar geografía.

Se probaron k=8,16,24,48,72 y KMeans con 4/8 grupos. Se incluyen empates en la frontera, por lo que el número efectivo puede superar k. DIRECT ajusta Ridge local a residuos de la base generados dentro del entrenamiento. WEIGHT modula una corrección global R4 mediante un peso local continuo. Ambos comparten k/grupos y amplitud elegidos por el criterio interno DIRECT; WEIGHT no tiene una búsqueda interna propia. Amplitudes 0/.25/.5 y corrección final limitada a ±.25 t/ha.

## Resultados destacados

Cada celda indica **RMSE t/ha / R²**. Los nombres GLOBAL_Rn cuentan indicadores del corrector, no las variables totales de J7.

| Modelo | Aleatoria | Perfil | Municipal | Espacial |
|---|---|---|---|---|
| C-T3 | .5116 / .6361 | .5206 / .6232 | .5813 / .5302 | .6788 / .3594 |
| J7 original | .4864 / .6709 | .4890 / .6675 | .5808 / .5309 | .6808 / .3556 |
| J7 + global R9 | .4855 / .6722 | .4894 / .6670 | .5811 / .5306 | .6705 / .3750 |
| J7 + global R4 | .4755 / .6856 | .4765 / .6843 | .5782 / .5351 | .6615 / .3916 |
| J7 + global R3 | .4756 / .6854 | .4748 / .6865 | .5726 / .5442 | .6550 / .4035 |
| J7 + global R2 | .4802 / .6793 | .4802 / .6793 | .5746 / .5409 | .6528 / .4075 |
| J7 + PCA2 | .4795 / .6802 | .4840 / .6744 | .5787 / .5344 | .6929 / .3326 |
| J7 + vecinos satelitales DIRECT | .4725 / .6895 | .4745 / .6869 | .5767 / .5376 | .6536 / .4060 |
| J7 + vecinos físicos DIRECT | .4784 / .6817 | .4758 / .6852 | .5760 / .5387 | .6589 / .3964 |
| J7 + clusters geográficos WEIGHT | .4764 / .6844 | .4783 / .6820 | .5792 / .5335 | .6551 / .4034 |
| C-T3 + vecinos geográficos DIRECT | .4940 / .6606 | .5038 / .6471 | .5767 / .5375 | .6676 / .3803 |

R4 contiene mínimo histórico NDVI, mínimo histórico FAPAR, persistencia del exceso y pendiente mínima. R3 elimina FAPAR; R2 conserva persistencia y pendiente mínima. PCA2 transforma los nueve indicadores: requiere nueve entradas originales, no dos mediciones.

## Qué significa

La reducción dirigida resulta más útil que conservar los nueve indicadores. R3 presenta un compromiso sencillo y favorable en los cuatro protocolos. El vecindario satelital DIRECT obtiene el menor RMSE aleatorio de esta batería (.4725), pero frente a R3 la ganancia es pequeña: .0031 t/ha; empeora municipal en .0041 y mejora espacial en .0014. No hay evidencia para declarar imprescindible su complejidad adicional. PCA2 reduce dimensionalidad sin conservar necesariamente la señal útil para rendimiento y empeora espacial frente a J7.

No existe un k universal. Entre los folds aleatorios activos de J7, GEO selecciona k72 en 37/50; PHYSICAL k72 en 29/50; SATELLITE selecciona k8 en 21/50, k24 en 17/50 y k16 en 8/50. En espacial SATELLITE reparte los cinco folds entre k8,16,24,48; PHYSICAL utiliza k48 en tres de sus cuatro folds activos. Estos conteos describen selección interna, no una prueba de superioridad de k. Los grupos satelitales 4/8 tampoco dominan consistentemente a vecinos ni al corrector global.

La disponibilidad histórica limita la geometría satelital: 29/138 parcelas no tienen completos sus tres indicadores. Se excluyen como referencias de esa distancia y reciben respaldo global cuando son consultas; no se eliminaron sus rendimientos ni sus filas de la evaluación. Un resultado etiquetado SATELLITE mezcla correcciones locales y respaldos globales.

En aleatoria, las referencias satelitales están a 23.46 km de media, frente a 15.42 km para físicas y 10.07 km para geográficas. Sólo 31.9% de las referencias satelitales pertenecen al mismo municipio y 10.7% al mismo perfil (geográficas: 60.8% y 25.5%). Son vecindarios distintos, aunque esto no demuestra independencia de la geografía. PCA2 conserva aproximadamente 49.7% de varianza estandarizada de los nueve indicadores (46.7–51.8% entre folds), lo que ayuda a entender su pérdida de información.

## Distribución y límites de las ganancias

En aleatoria, J7 satelital DIRECT mejora el error absoluto de aproximadamente 51.4% de las parcelas. Su ganancia agregada se concentra en las 35 difíciles definidas previamente: fuera de ellas el RMSE aumenta .0043 t/ha; para R3 aumenta .0059. No es una mejora uniforme, aunque municipal y espacial siguen mejorando al omitir esas 35 solamente del cálculo.

La ganancia espacial de R3 y del vecindario satelital persiste al omitir cualquiera de los cinco bloques del cálculo, sin reajustar. Sin embargo, ambos deterioran Almoloya/bloque5: RMSE aproximadamente .3621→.5859 para R3 y →.5844 para satelital DIRECT. Mejorar el agregado no resuelve la estabilidad territorial. En los bloques 3/4 sí hay mejoras; no se optimizó específicamente ninguno.

En diferencias entre parcelas del mismo perfil con soporte dentro del mismo fold, el RMSE con igual peso por perfil pasa en aleatoria de .5777 (J7) a .5697 (R3) y .5632 (satelital). En municipal pasa de .5257 a .5262 y .5303: la mejora intraperfil tampoco es universal. Son errores de diferencias entre pares, no RMSE del rendimiento individual; no deben compararse directamente con la tabla principal.

Se realizaron 208 contrastes pareados con ajuste Holm. Ninguno alcanza .05 tras el ajuste. Los intervalos territoriales son amplios y existen únicamente cinco bloques espaciales y nueve municipios; la ausencia de significancia no demuestra equivalencia. La auditoría de modelos y cálculos queda separada de la interpretación predictiva.

## Recomendación

Conservar como candidatos exploratorios R3 global por parsimonia y SATELLITE DIRECT para contrastar si merece la complejidad local. Mantener R2 como sensibilidad sencilla. No promover automáticamente ninguno. Una siguiente confirmación debe congelar estos candidatos y comprobar estabilidad territorial con evaluación independiente; no elegir k con los resultados externos de esta batería. La evidencia actual favorece simplificar los indicadores antes de añadir otra capa de agrupación.

Los archivos `tables/active_selection_counts.csv` y `active_neighbor_diagnostics_summary.csv` separan elecciones activas de correcciones apagadas. El Excel y `indicator_neighborhoods_results.md` incluyen las 40 entradas evaluadas (34 nuevas y seis referencias), MAE, sesgo, regiones, intraperfil, omisiones y distribución por parcela. Diseño: `indicator_neighborhoods_design.md`. Scripts reproducibles: 483–486; módulo: `src/indicator_neighborhoods.py`.
