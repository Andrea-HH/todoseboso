# Contexto externo del rendimiento: FIRA y ENA

Auditoría descriptiva, 14 de octubre de 2026. No se ajustaron modelos ni se generaron predicciones PRED. Se verificó la coincidencia de los 138 rendimientos del cache con la tabla original.

## Qué contienen los cuatro documentos FIRA

Archivos en `docs/resources/rendimientoshistoricosfira/`. Todos corresponden a PV2022, tecnología Temporal-mejorada-fertilizada y modalidad Tradicional.

|Archivo|Estado y zona|Etiqueta dentro del documento|Rendimiento probable, t/ha|
|---|---|---|---:|
|hidalgo22agenciashidalgo.pdf|Hidalgo, Agencias Hidalgo|CEBADA ALTA PRODUCTIVIDAD|3.50|
|puebla22altorendimiento.pdf|Puebla, Sierra Norte Puebla|CEBADA ALTA PRODUCTIVIDAD|5.50|
|puebla22cebadasinclasificacion.pdf|Puebla, Agencia Teziutlan|CEBADA|3.00|
|tlaxacla22altaprod.pdf|Tlaxcala, Agencias De Tlaxcala|CEBADA|4.00|

No aparece una categoría explícita de productividad media. El nombre del archivo de Tlaxcala no reproduce la etiqueta interior. Los valores son rendimientos probables de referencias de costos y paquetes regionales, no medias observadas de todas las parcelas del estado. La etiqueta alta productividad no define aquí un umbral universal: Hidalgo alta tiene 3.5 y Tlaxcala sin esa etiqueta tiene 4.0. No es válido asignar categoría a nuestras parcelas por cercanía de su rendimiento a esas referencias ni promediar los dos paquetes de Puebla sin conocer sus ponderaciones y poblaciones.

La última página contiene otra fuente y otro año: SIAP al 2020, cebada grano sin clasificar. Sus rendimientos estatales impresos son Hidalgo 2.04, Puebla 3.31 y Tlaxcala 2.56 t/ha. No deben atribuirse a FIRA2022. La fecha de actualización del portal tampoco cambia esos años de referencia.

## ENA2025 frente a nuestras parcelas

Fuente oficial conservada: https://www.inegi.org.mx/contenidos/programas/ena/2025/tabulados/ena2025_agr01.xlsx

Se calculó rendimiento como producción / superficie cosechada, no sembrada. La tabla consultada publica cebada para Hidalgo y Tlaxcala; no para Puebla. La ausencia no significa producción cero. El cociente nacional es 2.1283 t/ha.

|Estado|Parcelas|Media simple propia|Media propia ponderada por área de parcela|Cociente ENA|Diferencia simple propia − ENA|
|---|---:|---:|---:|---:|---:|
|Hidalgo|36|3.7625|3.8696|1.6468|+2.1157|
|Puebla|71|4.4773|4.3587|No publicado en tabla consultada|No calculable|
|Tlaxcala|31|2.9839|2.9726|2.0063|+0.9775|

Las diferencias relativas son +128.47% y +48.72%, respectivamente. La ponderación propia usa AREA_HA, no una superficie cosechada certificada ni ponderadores de encuesta. Las parcelas no constituyen una muestra probabilística estatal: Puebla se concentra en Chignahuapan y Tlaxcala casi completamente en Calpulalpan. Por tanto, ni siquiera ponderar por área garantiza representatividad estatal.

ENA combina ciclos agrícolas y observaciones/estimaciones de cosecha; la ficha describe siembras de octubre2024–septiembre2025 y cosechas hasta marzo2026. No es una comparación perfectamente emparejada con las parcelas2025, ni controla riego/temporal, tecnología, variedades, selección o condiciones locales.

La hoja de precisión reporta CV de superficie cosechada y producción: Hidalgo 27.24% y 26.22%; Tlaxcala 39.44% y 35.87%. Según su leyenda, son precisión moderada y baja, respectivamente. Esos CV no son el CV del rendimiento derivado. No se construyó un intervalo para el cociente sin la covarianza necesaria. No se afirma significancia estadística de las diferencias.

## Consecuencias para el modelado

Las referencias documentan que la población de parcelas puede diferir considerablemente del agregado estatal. No prueban errores en los targets, pertenencia al paquete de alta productividad ni cambio climático.

Un promedio externo podría plantearse como referencia o prior con contracción, después de armonizar ciclo, régimen, territorio y definición. No justifica desplazar automáticamente C-T3 hacia ENA ni sumar una corrección estatal fija. Con estos datos, tal corrección podría acercar las predicciones a una población distinta. Cualquier calibración posterior debería aprenderse y evaluarse dentro de los entrenamientos, compararse con C-T3 y con una corrección contraída, y conservar evaluación territorial.

## Reproducibilidad

Script: `scripts/390_fira_ena_yield_context.py`.

Resultados: `outputs/research/fira_ena_yield_context/v1/`: inventario FIRA, resumen por estado, comparación ENA, archivo oficial, textos extraídos y hashes de fuentes. Cero ajustes y cero inferencias PRED. El script protege las versiones completadas contra sobrescritura.
