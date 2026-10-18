> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Set histórico y actual guiado por calendarios FIRA

## Alcance

Representación por parcela y año, con Sentinel como base satelital y el mismo clima mensual canónico del proyecto. Años2022,2023,2024,2025. No se leyeron rendimientos, no se entrenaron modelos ni se generaron predicciones PRED. Las197 geometrías/identificadores conservan atributos disponibles; los diagnósticos de variación y redundancia se limitan a los138 TRAIN. No se modificaron modelo TOP20/TOP15, F5, F6, C-T3 ni sus folds.

El diseño y hashes de los15 PDF y las dos tablas temporales se escriben antes de construir las variables en `outputs/research/agronomic_calendar_set/v1/frozen_design.json`. Este set es una propuesta representacional exploratoria informada por documentos; su valor predictivo sigue sin evaluar.

## Calendario: referencias, no fechas observadas

Los informes FIRA describen tratamiento de semilla/preparación en abril y siembra usual mayo–junio. Sierra Norte2021 menciona cosecha septiembre–diciembre; Hidalgo2022 octubre–diciembre; Tlaxcala2023 septiembre–noviembre. Los documentos no proporcionan calendarios parcelarios ni una cartografía independiente que identifique qué paquete se aplicó. Por ello se utiliza una rejilla común para todos los estados y años, evitando introducir etiquetas alta/media productividad o reglas regionales inferidas a partir de Y:

|Ventana|Meses|Interpretación admitida|
|---|---|---|
|pre_apr|Abril|Ventana previa al periodo habitual de siembra; puede incluir tratamiento de semilla y vegetación previa|
|sowing_may_jun|Mayo–junio|Ventana regional de siembra; no garantiza siembra en ambas fechas ni establecimiento efectivo|
|post_jul_aug|Julio–agosto|Intervalo posterior; no se etiqueta como floración/llenado sin observación independiente|
|late_sep_oct|Septiembre–octubre|Intervalo tardío disponible dentro del corte; puede coincidir con cosecha en algunos casos|

El corte principal es31 de octubre del año correspondiente para conservar comparabilidad con las representaciones previas abril–octubre. No representa cosecha completa cuando el calendario llega a noviembre/diciembre. No se incorporaron esos meses a la matriz principal. Las variables tardías no están disponibles para un pronóstico en mayo/junio. La fecha de adquisición no garantiza disponibilidad operativa inmediata del producto.

FIRA2026 no se utiliza para definir conocimiento específico de2025: su inclusión entre los documentos auditados no autoriza usar cotizaciones, precios ni resultados posteriores. Las ventanas comunes están sustentadas por documentos anteriores. Aplicarlas a2022–2024 constituye una extracción retrospectiva homogénea; no demuestra que cada parcela se sembrara con cebada esos años. Una evaluación de decisiones realmente tomadas en2022 requeriría congelar documentos disponibles en esa fecha.

## Variables

Se generan37 variables anuales:25 satelitales y12 climáticas.

**Sentinel:** NDVI, EVI, NDWI, MSI y desviación espacial de NDVI en cada una de las cuatro ventanas:20 variables. Se calcula primero la mediana de observaciones de cada mes y después el promedio con igual peso por mes. La desviación espacial proviene del resumen por imagen original; no se recalcula a partir de píxeles ni equivale a incertidumbre estadística. Las tres diferencias de NDVI entre ventanas consecutivas describen cambios de señal. El mes de máximo NDVI y el rango estacional usan medianas mensuales mayo–octubre, con al menos cuatro meses disponibles; empates eligen el mes más temprano. No se interpretan automáticamente como fecha de siembra, floración o cosecha. El indicador de máximo en mayo/octubre se conserva como soporte, por posible censura en los bordes.

**Clima:** precipitación acumulada, Tmax y Tmin medias en cada ventana:12 variables. Temperaturas ponderadas por días calendario; precipitación como suma de los acumulados mensuales. No se inventan datos diarios, rachas secas, heladas, días de calor extremo ni grados-día reales. Reagrupar la misma celda climática no aumenta resolución espacial. Los índices satelitales pueden ayudar a describir respuesta local, pero no son medidas directas de manejo o estrés hídrico cuantificado.

No se fusionaron Planet/Landsat: Sentinel es la base solicitada y la misma fuente se mantiene para historia y presente. No se agregan costos, rendimientos probables ni clases de productividad FIRA como predictores.

## Historia y presente

Se conserva el panel anual completo,788 filas:197parcelas×4años. La representación ancha tiene148 columnas numéricas:37CURRENT2025,37HIST_MEAN2022–2024,37HIST_SD y37DELTA2025−HIST_MEAN. La SD histórica usa ddof1. Se requieren tres valores anuales disponibles para cada resumen histórico y delta; no se completa con menos años ni con valores2025.

La referencia de tres años no es climatología normal de largo plazo. SD indica variabilidad entre tres años, no precisión de la media ni intervalo predictivo. HIST_SD del mes de pico es variación de meses de máximo entre años. La comparación histórica puede reflejar cultivo distinto, rotación, cobertura, manejo y procesamiento, además del ambiente.

Estas148 columnas son un inventario de representaciones, no148 señales independientes. CURRENT=HIST_MEAN+DELTA. No introducir automáticamente las tres juntas ni asumir que una expansión dimensional mejorará una muestra de138. Se preservan matrices y diccionarios para elegir bloques previamente definidos en una etapa de modelado posterior.

## Calidad y fuga

Se reutilizan valores finitos de la tabla Sentinel canónica, sin interpolación, imputación ni filtro nuevo de nubosidad seleccionado después de observar resultados. En la fuente las adquisiciones con nubosidad100 no tienen NDVI válido. La ausencia de ese caso no certifica que todos los valores restantes estén libres de contaminación. Se conserva nubosidad media de adquisiciones, conteo válido por variable, meses cubiertos, mínimo de observaciones por mes y máximo hueco temporal incluyendo bordes de ventana. La matriz de soporte no es automáticamente un bloque predictor: puede codificar patrones de observación regionales.

Una ventana requiere al menos una observación válida en cada mes. Si falta un mes, la variable quedaNaN; no se acorta silenciosamente. Una ventana completa con una sola observación mensual puede seguir teniendo soporte débil, que queda señalado. Los meses con ausencia de vegetación no se eliminan por considerarlos poco productivos.

La construcción determinista utiliza exclusivamente X, fechas y documentos, por lo que puede prepararse antes de los folds. Imputación, escalado, selección, PCA/PLS y cualquier ajuste posterior se aprenderán dentro del entrenamiento correspondiente. No se modifica la resolución de satélite ni clima. No se emplean targets de años anteriores: se extraen X históricos, no se crean observaciones adicionales con el rendimiento2025 repetido.

## Próxima etapa propuesta, sin ejecutar

### Verificación descriptiva realizada

Las37 variables2025 tienen cobertura100% en las138 parcelas TRAIN. Esto significa presencia de observaciones suficientes según la regla de construcción, no calidad óptica perfecta: el mínimo de observaciones válidas por mes de una ventana tiene mediana5 y mínimo1 en2025.

En TRAIN existen43 perfiles climáticos,12 con al menos dos parcelas. Las20 variables satelitales de ventanas, los3 cambios y el rango estacional presentan variación en los12 perfiles repetidos; el mes de máximo varía en8. Ninguna de las12 variables climáticas actuales varía dentro de esos perfiles. Se demuestra capacidad de diferenciar X, no capacidad de explicar las diferencias de Y.

La cobertura histórica es desigual: la peor variable anual tiene80.4% de cobertura TRAIN en2022,100% en2023 y97.1% en2024. Los resúmenes que requieren los tres años pueden tener hasta21.0% de faltantes. Se conservanNaN y conteos, sin imputar. El máximo faltante corresponde a las representaciones, no implica que21% de todas las celdas estén ausentes.

Existe redundancia sustancial con los inventarios anteriores: varios acumulados climáticos son iguales y la correlación absoluta mediana de cada nueva variable climática con su representación previa más próxima es aproximadamente0.999999. Para las25 satelitales es0.853; algunas también son muy redundantes, como MSI/NDWI de abril con cuantiles previos. Por tanto, no se presentan las37 variables como descubrimientos independientes. La consistencia entre años y ventanas, la historia de su forma estacional y las desviaciones son la hipótesis representacional a evaluar.

Las tres pruebas automatizadas verifican exclusión de2025 de la referencia histórica, exigencia de los tres años, propagación de meses faltantes, peso igual por mes frente a distinta frecuencia de imágenes, acumulación de lluvia y exclusión de noviembre. Pasaron sin fallos. Los artefactos no contienen infinitos ni columnas de rendimiento.

Comparar primero un bloque climático de ventanas contra lluvia compact3 manteniendo algoritmo, splits y selección interna; después un bloque Sentinel acotado que preserve el control NDVI mayo; finalmente historia y/o desviaciones mediante ablaciones. Mantener los65folds y particiones internas congelados. No presentar la mejor representación elegida entre resultados externos como confirmación independiente.

Medir si el satélite conserva variación dentro de perfil y municipio, y si esa variación explica errores OOF: son preguntas diferentes. Reportar validación municipal y espacial además de aleatoria/perfil. No se afirma que este nuevo set mejore C-T3.

## Artefactos

- `data/processed/agronomic_calendar_set/v1/annual_features_2022_2025.parquet`: panel anual.
- `current_history_delta_197_target_free.parquet` y CSV: representación ancha.
- `annual_feature_dictionary.csv` y `representation_dictionary.csv`: fórmulas, unidades y ventanas.
- `satellite_support.parquet`: cobertura y soporte por parcela, año y variable.
- `historical_valid_year_counts.csv`: soporte de las referencias históricas.
- `monthly_inputs_apr_oct.parquet`: medianas satelitales y clima originales por mes.
- `outputs/research/agronomic_calendar_set/v1/`: diseño, hashes, manifiesto, cobertura TRAIN, variación intraperfil y proximidad a representaciones existentes. La correlación descriptiva con variables previas no es selección predictiva.
- `scripts/391_build_agronomic_calendar_set.py`, `src/agronomic_calendar_features.py`, `tests/test_agronomic_calendar_features.py`.
