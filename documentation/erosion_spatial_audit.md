# Auditoría espacial de la nueva capa de erosión

**Sí distingue una parte importante de las parcelas, también dentro del mismo perfil climático. Su soporte es regional, no una medición fina o actual de erosión en cada parcela.** No se ha probado todavía su aportación predictiva ni su relación con el rendimiento.

## Fuente y escala

INEGI, Conjunto de Datos de Erosión del Suelo 1:250,000 Serie I. Los metadatos locales señalan referencia 2013-11-29, verificación de campo 2009-01-05/2012-07-02 e insumos desde 2008. No describe directamente el estado de las parcelas en 2025.

El SHP de polígonos contiene 70,281 objetos nacionales; se recuperaron 356 en el rectángulo de estudio y 26 intersectan las parcelas. Se reparó una geometría inválida del subconjunto. Se utilizaron polígonos originales, transformación a UTM14N y áreas geométricas de intersección; no rasterización o aumento artificial de resolución.

El diccionario, página PDF26 (numeración impresa20), especifica 60,000m² como mínimo geométrico y restringe las unidades menores a100ha a erosión fuerte/extrema o antrópica. Las asociaciones requieren unidades de al menos250ha. No interpretar el mínimo excepcional de6ha como resolución uniforme parcelaria.

Entre las unidades realmente intersectadas, el área mínima es108.8ha y la mediana2,465.6ha; una unidad grande de SE se extiende mucho más allá del área de estudio. Las parcelas tienen mediana5.45ha, mínimo0.35ha y máximo64.26ha. La unidad cartográfica mediana es unas452 veces mayor que la parcela mediana. Estas áreas no equivalen a una resolución de píxel y no describen heterogeneidad interna.

## Cobertura y contraste

Las197 geometrías parcelarias están cubiertas completamente dentro de tolerancia numérica; no se detecta solapamiento de áreas relevante. Se encontraron12 claves intersectadas y11 dominantes. Son clases y asociaciones cartográficas, incluyendo una clave complementaria AH de asentamiento humano: no todas deben interpretarse como grados de erosión.

48/197 parcelas intersectan más de una unidad/categoría; 149 caen en una única unidad. En las138 parcelas etiquetadas hay33 mixtas y11 claves dominantes. En Chignahuapan,71 etiquetas se distribuyen en8 claves dominantes y17 parcelas son mixtas. Este contraste no depende exclusivamente de diferencias entre estados.

| Pares con igual perfil de lluvia | Pares | Distinta categoría dominante | Composición con distancia ≥10 puntos porcentuales |
|---|---:|---:|---:|
| TRAIN completo | 1,073 | 584 —54.4% | 670 —62.4% |
| Ambas en Chignahuapan | 934 | 543 —58.1% | 626 —67.0% |
| Resto de pares | 139 | 41 —29.5% | 44 —31.7% |
| Ambas a más de125m de límites temáticos | 407 | 155 —38.1% | 155 —38.1% |

La distancia de composición es la mitad de la suma de diferencias absolutas entre fracciones de clases, usando el área total de parcela. Distingue categorías y mezcla geométrica, no mide porcentaje de suelo efectivamente erosionado. Los pares comparten parcelas: no son1,073 observaciones independientes. “Resto” incluye todo par que no tenga ambas parcelas en Chignahuapan.

En Chignahuapan, incluso exigiendo que ambas parcelas estén a más de125m de los límites,149/330 pares —45.2%— tienen distinta categoría dominante. Por tanto, el contraste no proviene únicamente de pequeñas intersecciones cerca de bordes.

## Límites y puntos de campo

79/197 parcelas y55/138 TRAIN están a125m o menos de un límite temático. Se eliminaron fronteras internas entre polígonos de igual clase antes de medir distancias. Los125m son una sensibilidad cartográfica (0.5mm a escala1:250,000), **no una precisión posicional certificada** ni una regla automática de exclusión. No se eliminó ninguna parcela.

El archivo de puntos tiene5,292 sitios nacionales. Ninguno cae dentro de las197 parcelas. La distancia mínima de un punto a una parcela es845m; la mediana del punto más cercano es5.27km y el máximo12.25km. Sus variables de suelo/laboratorio no son mediciones parcelarias; asignarlas por vecino más cercano no vuelve fina la información.

## Variables que pueden derivarse

- Categoría cartográfica dominante y fracción de parcela cubierta por cada clave de unidad.
- Tipo, forma y grado dominante/secundario según diccionario, con N/A y desconocidos explícitos.
- Cobertura, mezcla de unidades y distancia a límite como calidad/soporte.

Ejemplo: HL2+HS1 combina erosión hídrica laminar moderada dominante y surcos leves secundarios. El símbolo no proporciona porcentajes relativos de esas dos afectaciones. Intersectar un polígono con70% de una parcela significa70% bajo esa **unidad cartográfica**, no70% de superficie dañada ni una pérdida cuantificada de suelo. SE significa “sin erosión evidente” en la cartografía de referencia; no garantiza ausencia en2025. AH no debe codificarse como erosión cero.

## Recomendación

La capa justifica un estudio acotado de señal física complementaria, especialmente dentro de los perfiles de Chignahuapan. Empezar con pocas categorías y asociaciones bien documentadas, comparar dentro de perfil y municipio, y conservar diagnóstico de límites y fecha. No entrenar automáticamente un corrector ni asumir que la diferenciación geométrica implica menor error. La relación con rendimiento y su generalización siguen sin evaluar.

Las59 geometrías PRED se usaron únicamente para auditar cobertura cartográfica; no se utilizaron rendimientos, no se seleccionaron modelos con ellas y no se generaron predicciones. Todos los conteos de contraste por perfil y evidencia para investigación corresponden a TRAIN.

## Artefactos

Se guardaron intersecciones, fracciones, soporte por parcela, pares de igual clima y metadatos. Cero ajustes o screening de rendimiento. El script verifica197 parcelas únicas y1,073 pares TRAIN; controles geométricos muestran cobertura mínima1−5.1e−13 y solapamiento máximo6.7e−16. Fuentes conservadas por hash.

- [Resumen numérico](../outputs/research/erosion_spatial_audit/v1/summary.json)
- [Soporte por parcela](../outputs/research/erosion_spatial_audit/v1/tables/parcel_support.csv)
- [Fracciones de categorías](../outputs/research/erosion_spatial_audit/v1/tables/category_composition.csv)
- [Comparaciones intraperfil](../outputs/research/erosion_spatial_audit/v1/tables/pair_support_summary.csv)
- [Mapa de clases dominantes](../outputs/research/erosion_spatial_audit/v1/figures/parcel_categories.png)
- [Script](../scripts/389_erosion_spatial_audit.py)
- [Diccionario original](../data/externo/erosion/DICCIONARIO%20DATOS%20EROSION.pdf)
- [Metadatos originales](../data/externo/erosion/METADATOS/meta.txt)
