> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Cuartil difícil: qué diferencia las parcelas y el signo del error

Referencia J7_BOTH original, validación aleatoria OOF de diez repeticiones. Error=predicho−observado. No se cambió el modelo de rendimiento ni se aplicó una nueva corrección.

## Poblaciones diferentes

El cuartil de mayor dificultad contiene35parcelas,25.36% de138, seleccionadas por media de error cuadrático OOF. Su error RMS individual mínimo es0.49475t/ha. Concentran80.80% del error cuadrático. Son17sobreestimadas y18subestimadas; las otras103no pertenecen al cuartil difícil. El RMSE J7 es0.8681 en las35 y0.2467 en las103; esos resultados están condicionados a selección por error y no son una validación nueva. Los correspondientes R² son0.4222 y0.8786, con distintos rangos de Y y la misma advertencia de selección.

El cuartil de rendimiento observado bajo es otra población: Y≤3.2t/ha,36parcelas al conservar empates. Sólo12pertenecen al cuartil difícil. No se debe usar «rendimiento bajo» y «difícil de predecir» como sinónimos.

|Municipio|Total TRAIN|Difíciles|Fracción municipal|Sobreestimadas difíciles|Subestimadas difíciles|
|---|---:|---:|---:|---:|---:|
|Chignahuapan|71|19|26.8%|8|11|
|Calpulalpan|30|11|36.7%|5|6|
|Singuilucan|16|3|18.8%|3|0|
|Cuautepec de Hinojosa|5|1|20.0%|0|1|
|Nanacamilpa de Mariano Arista|1|1|100%|1|0|

Los demás municipios no aportan casos a este cuartil aleatorio. El100% de Nanacamilpa equivale a una sola observación, sin soporte para extrapolar una tasa. Chignahuapan reúne54.3% de difíciles y51.4% del total TRAIN: su concentración proporcional no es extraordinaria. Calpulalpan tiene una proporción mayor, aunque la muestra es pequeña.

## Dificultad general frente a103restantes

El grupo no comparte una única anomalía. En diferencias dentro de municipio destacan, de forma exploratoria:

- Nitrógeno cartografiado SoilGrids5–15cm y su resumen0–30cm. Efecto de rangos condicionado mayor en difíciles; las medianas globales son casi iguales (1.700vs1.696 para5–15cm). No se infiere una gran diferencia de dosis ni de nitrógeno medido, y no se interpreta causalmente.
- Forma de la distribución histórica del LAI (SD/rango mayor), curtosis del NDVI actual menor y menor agudeza del pico EVI Planet. Esto describe forma y persistencia de señales, no sólo su promedio.
- Distribución espacial de varios índices y dinámica de índices de humedad. Varias columnas altamente correlacionadas representan el mismo tipo de información.
- Población de la localidad más próxima: es contexto geográfico/social cartografiado; una asociación no demuestra un efecto de manejo y puede ser un proxy territorial.

El contraste intra-municipio dispone de tres municipios con≥2casos en cada grupo: Chignahuapan, Calpulalpan y Singuilucan. Dentro de perfil climático hay tres perfiles con ese soporte:4,24,38. No son resultados respaldados por todos los municipios o por los43perfiles TRAIN.

Las señales previamente nominadas en171/015 pierden fuerza al ampliar a35: TPI medio, cambio neto EVI Planet y pendiente media presentan efectos municipales difíciles/restantes de aproximadamente0.014,0.013 y0.040, respectivamente. La dinámica máxima de la brecha NDVI tiene efecto0.046. Son prácticamente nulos para detectar dificultad general. La dinámica de brecha sí ayuda descriptivamente a distinguir signos dentro del grupo difícil.

## Sobreestimación frente a subestimación: variables concretas

Las17sobreestimadas tienen rendimiento medio2.846t/ha y predicción media3.743: sesgo+0.896. Las18subestimadas tienen rendimiento medio4.607 y predicción media3.944: sesgo−0.664. La compresión de las predicciones hacia valores centrales explica el sentido general del error, pero Y observado no puede usarse para decidir la corrección de una parcela desconocida. Calpulalpan aporta sobreestimaciones en observaciones2.5y subestimaciones en3.5: el extremo debe interpretarse dentro de su contexto, no sólo en el rango global.

Medianas de cada grupo, en unidades de las columnas fuente:

|Variable|Sobreestimadas17|Subestimadas18|Patrón descriptivo|
|---|---:|---:|---|
|TOPO_BASIC_slope_min|0.7781|1.5292|Pendiente mínima menor en sobreestimadas|
|TOPO_BASIC_slope_mean|1.9045|2.8235|Pendiente media menor en sobreestimadas|
|S2_ndvi_derived_lower_gap_max|0.3790|0.3300|Brecha máxima medio−mínimo NDVI mayor en sobreestimadas|
|S2_ndvi_derived_lower_gap_max_growth_rate|0.0480|0.0312|Aumento máximo de esa brecha mayor en sobreestimadas|
|S2_msi_derived_upper_gap_normalized_auc|0.3067|0.2591|Brecha temporal MSI máximo−medio mayor en sobreestimadas|
|PLANET_ndvi_derived_range_std|0.1096|0.0861|Variación temporal del rango NDVI mayor en sobreestimadas|
|HIST_S2_ndvi_promedio_mean|0.2991|0.3100|NDVI histórico medio mayor en subestimadas|
|sat_basic_hist__sentinel_2__fapar_min__mean|0.1250|0.1384|Mínimos FAPAR históricos medios mayores en subestimadas|

Los signos de estos ocho contrastes se conservan al comparar dentro de municipio y dentro de perfil. Pendiente mínima tiene Cliff delta sobre−sub de−0.605dentro de municipio y−0.511dentro de perfil; brecha máxima NDVI+0.561/+0.700; variación temporal rango NDVI+0.571/+0.483. Esto caracteriza asociaciones de rangos, no diferencias causales ni porcentajes de área afectada.

El soporte condicionado sobre/subestima se reduce a dos municipios (Chignahuapan8vs11,Calpulalpan5vs6) y tres perfiles (4:2vs5;24:4vs4;38:3vs2). Las medianas de la tabla son globales; los efectos condicionados no se deducen sólo restando esas medianas.

No aparece una separación clara por textura dominante: textura2en12/17sobreestimadas y13/18subestimadas; textura3en5/17y5/18. La faseN está en12/17y12/18. Otras fases tienen celdas pequeñas. TPI medio tampoco separa consistentemente el signo; la pendiente y ciertas representaciones de heterogeneidad lo hacen mejor descriptivamente.

Heterogeneidad óptica, extremos de índices y mínimos pueden reflejar vegetación, suelo expuesto, bordes de parcela, máscara y calidad de observación; no prueban enfermedad, estrés hídrico, humedales ni manejo. El archivo fuente y las descripciones originales acompañan el inventario.

## ¿Se pueden clasificar antes de conocer el rendimiento?

Se ajustaron130clasificadores diagnósticos: PHYSICAL210columnas candidatas y ALL_SIGNALS3486, con selección de hasta6dentro de entrenamiento, logística conservadora fija y65folds. Las etiquetas internas se derivan de residuos J7cross-fitted dentro de cada entrenamiento y su propio percentil75; no se entrenó usando el grupo global de35. Por ello el soporte externo es33.2difíciles en promedio aleatorio,34por perfil y26municipal/espacial.

|Protocolo|AUC detectar difíciles, PHYSICAL|AUC distinguir sobre/sub dentro de difíciles, PHYSICAL|
|---|---:|---:|
|Aleatoria|0.534|0.451|
|Perfil climático|0.522|0.723|
|Municipal|0.503|0.526|
|Espacial|0.515|0.771|

AUC0.5es la referencia sin discriminación. Las aparentes ventajas direccionales no son estables: en espacial sólo hay24sobreestimadas difíciles y2subestimadas. La decisión de tres clases no identifica ninguna de esas dos subestimadas (recall0). AUC direccional condicionada a saber que una parcela es difícil no equivale a identificar automáticamente esa situación.

La balanced accuracy de tres clases PHYSICAL es0.311/0.407/0.411/0.281, frente a1/3del control que siempre predice la clase mayoritaria. Su precisión aleatoria para sobre/subestimadas difíciles es aproximadamente10%, y sensibilidad aproximadamente19–21%. ALL_SIGNALS tampoco ofrece una solución: AUC detección0.479/0.414/0.368/0.166. No se recomienda invertir esos scores tras ver resultados: sería otra decisión retrospectiva.

Las variables seleccionadas cambian entre protocolos. En aleatoria PHYSICAL selecciona con frecuencia proporciones/unidades cartográficas de suelo, limo y calificadores de mapa; ALL_SIGNALS añade forma histórica NDVI/LAI y varios índices mensuales. Esa frecuencia no demuestra utilidad, como muestran las métricas externas. Las asociaciones de errores no sobreviven BH0.05en las pruebas marginales de miles de variables; las pruebas tampoco incorporan toda la dependencia espacial ni búsqueda histórica. No se declara ninguna variable «significativa» como descubrimiento confirmado.

## Si la pregunta se refería al cuartil de menor rendimiento

Para las36parcelas con Y≤3.2t/ha aparecen descriptivamente menor carbono orgánico SoilGrids superficial, diferencias del gradiente vertical de pH y carbono, y mayor variabilidad temporal del NDVI máximo. Ejemplos: SOC5–15cm13.12vs15.42; gradiente pH0–30menos30–60cm−0.25vs−0.20; SD temporal NDVI máximo0.2425vs0.2036. Se conserva contraste intra-municipio/perfil en tablas, con soporte limitado. Ésta es asociación con Y bajo, no con error elevado; muchos contrastes globales reflejan diferencias regionales ya capturadas por el modelo.

## Decisión y entregables

El grupo difícil no es un único tipo de parcela ni una simple clase de suelo. Separar signos evita cancelar señales: las subestimadas muestran, en varios descriptores, historia de vegetación más elevada y menor heterogeneidad temporal; las sobreestimadas muestran mayor heterogeneidad y menor pendiente. Son hipótesis descriptivas para comparar representaciones, no reglas listas para desplegar. La clasificación evaluada no justifica usar estos patrones para activar ni dimensionar una corrección de rendimiento. Se conservan J7/CT3 y no se modifican Champion ni PRED59.

El Excel contiene los35IDs, las tablas numéricas/categóricas completas, diferencias por parcela respecto a municipio/perfil, soporte, modelos de clasificación y estabilidad. Los perfiles pequeños o con variables constantes no se presentan como outliers continuos. El inventario por parcela usa hasta12variables no redundantes por ámbito, con n≥12,≥5valores distintos e IQR positivo; conserva percentiles y cercas descriptivas incluyendo la parcela focal.

Scripts474–477y src/difficult_quartile.py. Se documentó y corrigió una etiqueta de familia: la palabra slope en un índice temporal no es pendiente del terreno. La primera ejecución está preservada bajo audit/initial_family_label_attempt; no se inspeccionaron métricas externas de clasificación antes de corregir. Se verificó que ALL_SIGNALS y PRIOR no cambiaran numéricamente. Cuatro pruebas automatizadas y replay de130modelos; sin nuevo ajuste final138 ni predicciones59.
