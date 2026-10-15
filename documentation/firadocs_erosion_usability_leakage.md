# Usabilidad y fuga de información: FIRA y erosión

Auditoría descriptiva del 14 de octubre de 2026. Se examinaron los 15 PDF de `docs/resources/firadocs`, incluidos resumen, memoria de cálculo, comentarios y sensibilidades. Textos, inventario, metadatos de creación y hashes conservados en `outputs/research/firadocs_leakage_audit/v1`. No se entrenaron modelos.

## FIRA: contenido y alcance

|Referencia|Rendimiento probable t/ha|
|---|---:|
|Hidalgo alta productividad 2022|3.5|
|Hidalgo 2023; altiplano media 2024, con y sin seguro a la inversión; altiplano 2025 y 2026|3.5 en cada documento|
|Puebla Sierra Norte alta 2021 / 2022 / 2023|5.0 / 5.5 / 5.5|
|Puebla Teziutlán 2021 / 2022 / 2023|3.5 / 3.0 / 3.0|
|Puebla altiplano alta 2024|4.5|
|Tlaxcala 2022 / 2023|4.0 / 4.0|

Los documentos contienen calendario de siembra/cosecha, operaciones, cantidades de semilla y fertilizantes, productos, costos, jornales, financiamiento, seguro, renta, rendimiento/precio/ingreso probables, equilibrio y sensibilidades económicas. Son paquetes de referencia, no 15 parcelas independientes ni una serie homogénea de rendimientos observados.

Ahora sí existe media productividad explícita: Hidalgo2024, con y sin seguro, zona ALTIPLANO MEDIA PRODUCTIVIDAD. Los comentarios abarcan Hidalgo, Tlaxcala y Puebla. Puebla2024 alta comprende municipios de Puebla e Hidalgo; Hidalgo2025/2026 contempla cuatro estados. La etiqueta estatal del archivo no define una frontera de aplicación.

Puebla Sierra Norte2021 menciona proveedores de Heineken en Chignahuapan; 2022 especifica El Paredón, Chignahuapan y variedades Prunella, Brennus y Josefa. Teziutlán2022/2023 corresponde a productores de Cuyoaco, no a nuestras parcelas de Chignahuapan. El encabezado del archivo Puebla alta2023 dice CEBADA, pero sus comentarios sí describen alta productividad. El archivo Hidalgo2023 se llama GMF, mientras el interior dice TMF. Se debe usar el contenido, no inferir por nombre.

## Qué puede usarse y qué riesgo tiene

1. **Contexto agronómico y ventanas temporales:** utilizable para formular hipótesis o ventanas predefinidas. El calendario recomendado no es la fecha real de cada parcela. Si se eligen ventanas mirando los errores externos, el resultado posterior será exploratorio.
2. **Dosis, labores y costos de referencia:** extraíbles como características del paquete. No se pueden atribuir como manejo observado a cada parcela sin un vínculo independiente que confirme qué paquete se aplicó. Repetir un mismo valor por estado añade contexto territorial, no mediciones individuales. Los precios nominales no son comparables entre años sin armonización.
3. **Rendimiento probable histórico:** no es fuga automática si es externo, anterior al momento de predicción y asignado por reglas independientes del target. Es una referencia informada por rendimientos, no una variable física independiente. No hay prueba de que los datos de origen estén libres de solapamiento con nuestros productores. Su publicación y disponibilidad deben documentarse.
4. **Fuga circular:** elegir alta/media según el rendimiento observado de la parcela y luego usar el rendimiento probable del paquete para predecirla incorpora el target en el predictor. Elegir el paquete que minimiza errores externos también contamina la evaluación.
5. **Dependencias aritméticas:** ingreso probable = rendimiento probable × precio. Costo unitario y utilidad también incorporan el rendimiento supuesto. En Hidalgo2022 la memoria usa 3.5 toneladas para el flete; Tlaxcala2023 usa 4 toneladas en acarreo, igual que su rendimiento probable. No tratarlos como señales independientes. Si fueran ingresos o tonelajes reales de la misma cosecha, podrían revelar directamente el target; aquí reflejan supuestos externos, no evidencia de fuga de nuestras etiquetas.
6. **Tiempo:** excluir FIRA2026 de un pronóstico retrospectivo2025. Sus comentarios usan el precio basePV2025 y cotizaciones2026; metadatos de creación mayo2026. Hidalgo2025 tiene metadatos de marzo2025 y cotizaciones de febrero: candidato temporalmente compatible, pero los metadatos no certifican fecha de publicación ni ausencia de revisiones. Los documentos2021–2024 son candidatos históricos, sujetos a verificar disponibilidad.
7. **Sensibilidades:** mínimos, máximos y tablas de utilidad son escenarios. No son intervalos empíricos de rendimiento ni observaciones adicionales para aumentar la muestra. Las variantes de seguro tampoco son rendimientos independientes.

## Erosión

Se reutilizó la auditoría espacial y los metadatos/diccionario originales documentados en `documentation/erosion_spatial_audit.md`. Capa INEGI1:250000 SerieI, referencia2013, campo2009–2012. Su asociación por intersección geométrica no necesita rendimientos: no se identificó una vía de fuga del target2025 en esta derivación. Para un pronóstico histórico estricto se conserva además evidencia de disponibilidad de la versión antes del corte.

Variables defendibles: tipo/forma/grado y asociaciones dominantes/secundarias según diccionario, clase dominante y fracciones geométricas por clave. Cobertura, mezcla y distancia a límites describen soporte/calidad. AH no es erosión cero y SE no garantiza ausencia de erosión2025. No imponer orden numérico a toda clave compuesta sin una semántica explícita.

Hay contraste real en el mapa: 11 clases dominantes en TRAIN; 33/138 parcelas intersectan varias unidades. Entre 1073 pares con igual perfil de lluvia, 54.4% tienen distinta clase dominante. En Chignahuapan son 58.1%; a más de125m del límite temático persiste 45.2%. Los pares no son independientes y esto no demuestra asociación con rendimiento.

El soporte es regional: mediana de unidad intersectada2465.6ha frente a parcela5.45ha. Ningún punto de campo cae en las parcelas. Las fracciones indican cobertura de unidades cartográficas, no porcentaje real de suelo erosionado. La capa puede codificar ubicación y funcionar bien en particiones aleatorias sin transferir a otra región: eso es dependencia espacial o cambio de distribución, no por sí mismo fuga del target.

Extraer atributos fijos por intersección antes de los folds es admisible si no depende de Y ni selecciona modelos con PRED. Imputación aprendida, agrupación por relación con rendimiento, target encoding, selección, ajuste de correcciones y regularización deben ocurrir dentro de cada entrenamiento y sus particiones internas. No usar medias de rendimiento por unidad calculadas con todos los138 ni elegir categorías después de consultar los errores del fold externo. Las59 geometrías PRED ya usadas para cobertura no justifican usarlas para decidir modelos.

## Recomendación

Priorizar una representación pequeña de erosión como sensibilidad física sobre C-T3, con ablación frente a pendiente/suelo existentes, soporte intraperfil y evaluación municipal/espacial original. No se afirma mejora predictiva y no se ejecutó esta sensibilidad.

FIRA merece primero una tabla de paquetes y correspondencia territorial/manejo independiente del target. Usarlo ahora para interpretar calendarios y diferencias de población. No introducir decenas de costos ni asignar rendimientos altos/medios por estado o por cercanía al Y observado. Un prior externo sería un experimento separado, con regla y fecha congeladas, no una corrección automática.
