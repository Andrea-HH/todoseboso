> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Acceso e inventario de señales puntuales de GeoC

Se confirmó acceso local de lectura a `C:/Users/narro/Desktop/semestre/fira/GeoC`. Las tablas por parcela y sus manifiestos están disponibles en `data/processed/features_v1`, `agronomic_features_v1` y `empirical_features_v1`. Contienen 197 filas y respectivamente 1,408, 351 y 336 columnas, incluyendo metadatos. No se suman esos tamaños como fuentes independientes ni como un nuevo total de variables.

Se rastrearon exactamente las 1,831 variables conservadas en el Local sin clima. Sus valores coinciden con el archivo auditado usado por el modelo, con tolerancia1e-10 y faltantes equivalentes. No se modificó GeoC. Los manifiestos originales proporcionan procedencia, entradas y fórmulas para muchas variables derivadas; algunas columnas base solo tienen una descripción genérica. No se inventaron unidades o significados biológicos cuando faltan, ni se verificaron externamente las referencias bibliográficas abreviadas suministradas por esos manifiestos.

## Entregables

- `outputs/research/geoc_variable_signal_audit/v1/catalogo_y_senales_GeoC.xlsx`: catálogo1831, asociaciones exploratorias y fuentes.
- `inventario_1831_geoc.csv`: definición, fórmula, entradas directas, ascendencia, fuentes raíz, advertencias, rangos/cuartiles en138, faltantes, asociaciones y representación PCA.
- `variables_1831_197_sin_target.parquet`: copia consolidada de los predictores de197 parcelas, sin rendimiento.
- `asociaciones_destacadas_exploratorias.csv`, `resumen_fuentes.csv`, configuración previa y manifiesto.
- Script reproducible: `scripts/435_geoc_variable_signal_audit.py`.

Estos archivos se guardan en `fira_nuria`, bajo outputs, que sigue excluido de Git. Las fuentes GeoC se consultan sin modificarlas. No se garantiza que todos los archivos brutos o servicios de origen estén completos por el solo hecho de disponer de estas tablas procesadas.

## Qué significa la primera revisión

Se calcularon asociaciones sobre los 138 rendimientos conocidos. Para C-T3 se promedian las diez predicciones OOF aleatorias de cada parcela y se obtiene un residuo por parcela. Las diez repeticiones no se tratan como diez muestras independientes. Se examina Spearman con rendimiento, Spearman con ese residuo y Pearson tras centrar predictor y residuo dentro del mismo perfil, usando casos completos para cada variable.

Las asociaciones responden preguntas distintas: relación con rendimiento absoluto, relación con lo que deja sin explicar C-T3 y contraste lineal dentro de perfiles. La última no equivale a un modelo condicional completo ni a mejora predictiva validada. Los estados/perfiles también se resumen con eta² descriptivo para advertir estructura territorial; no se usan esas asociaciones para ajustar un nuevo predictor.

| Variable | Spearman con residuo C-T3 | Pearson intraperfil con residuo | Lectura exploratoria |
|---|---:|---:|---|
| `sat_basic_hist__sentinel_2__srndi_std__min` | -0.225 | -0.276 | Señal histórica espectral; la definición biológica precisa requiere ampliar documentación base |
| `emp_shape__y2025_planet_evi__turning_fraction` | -0.225 | -0.075 | Frecuencia de cambios de signo entre pendientes mensuales; asociación global más clara que intraperfil |
| `soilgrids__nitrogen__30_60cm__std` | -0.203 | -0.155 | Estadística zonal de nitrógeno estimado a30–60cm, no medición de laboratorio parcelaria |
| `emp_distribution__hist_s2_fapar__mean_position_in_range` | -0.022 | -0.214 | Posición de la media histórica respecto al rango; posible contraste intraperfil débil que la asociación global no destaca |

Los signos negativos no significan que aumentar una propiedad reduzca causalmente el rendimiento: corresponden al residuo y a estas representaciones. Varias columnas son transformaciones redundantes o casi redundantes de una misma fuente. Por ejemplo, posición en el rango y asimetría pueden describir esencialmente un mismo contraste con signos opuestos; no deben contarse automáticamente como dos señales nuevas.

## Inferencia y límites

Se exploraron 1,820 variables con al menos100 valores finitos, al menos3 valores distintos y contraste intraperfil. Para cada una se centró predictor y residuo entre casos completos del perfil; se sumaron sus productos por conglomerado. Se enumeraron los 4,096 cambios de signo de los12 perfiles con varias parcelas y se aplicó Holm entre todas las pruebas elegibles. Ninguna queda por debajo de0.05 tras el ajuste.

Es una prueba exploratoria bajo una hipótesis de simetría/intercambiabilidad de signos entre conglomerados; perfiles pueden seguir siendo espacialmente dependientes. Los únicos12 conglomerados con contraste y la reutilización histórica de etiquetas limitan la interpretación. La ausencia de significancia no demuestra inutilidad: una variable puede ser no lineal, interactuar o aportar información compartida que estas asociaciones univariadas no detectan.

Las cargas y energías PCA del catálogo describen representación de X en PCA20. No son coeficientes sobre rendimiento ni importancia predictiva de Local04D. No existe un coeficiente único de cada variable para toda la regresión local, ya que cambia el vecindario y el ajuste por parcela.

Para hablar de aportación predictiva puntual se requieren ablaciones con reajuste dentro del entrenamiento, agrupación de variables correlacionadas y comparación de OOF pareadas. Permutar una sola columna cruda manteniendo un PCA/local congelado puede crear combinaciones irreales y no sustituye ese contraste. La prioridad es agrupar señales por origen y definición, separar proxies territoriales, y después evaluar los bloques reducidos sobre residuos de C-T3 o sobre pesos entre expertos, con controles equivalentes.

No se ajustaron modelos predictivos nuevos, no se seleccionaron variables para producción, no se usaron rendimientos PRED y no se alteraron las59 predicciones ni el Champion. Se verificaron hashes de las fuentes originales al finalizar.
