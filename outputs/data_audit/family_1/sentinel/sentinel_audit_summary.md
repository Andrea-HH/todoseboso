# Auditoría Sentinel-2 — Familia 1, Etapa 1

Generado: 2026-10-02T12:14:18-06:00

## Archivos encontrados

- Dataset Básico original: `data\original\01_tablas_maestras\Conjunto_datos_BASICO_AgroCebada2026.csv`
- Sentinel procesado existente: `data\processed\01_tablas_maestras\sentinel.csv`
- Maestro de parcelas, área y rendimiento: `data\original\01_tablas_maestras\ID_area_rendimiento_70_30_Reto_AgroCebada.csv`
- Geometrías: `data\original\02_conjunto_70_30\Parcelas_Reto_AGC_CONJUNTO.shp`

La auditoría usa como fuente canónica las filas `sensor == Sentinel-2` del Dataset Básico original. El CSV procesado se conserva sólo como contraste; no se sobrescribió ningún archivo fuente.

## Estructura real

- Dimensión Sentinel original: **59,040 filas × 96 columnas**.
- Parcelas únicas: **197**.
- Periodo: **2022-01-01 a 2025-12-31**.
- Índices base detectados: **23**.
- Estadísticos espaciales: `promedio`, `std`, `min` y `max`.
- Nubosidad: `porcentaje_nubosidad`, expresada como porcentaje según el nombre/documentación.
- Las unidades específicas de los índices no están declaradas en el CSV; deben consultarse en el diccionario de índices.

## Parcelas

- ENTRENAMIENTO: **138**.
- PREDICCION: **59**.
- Parcelas maestras ausentes en Sentinel: **0** (ninguna).
- Parcelas Sentinel ausentes en maestro: **0** (ninguna).

## Cobertura temporal

- Observaciones por parcela: mínimo **298**, mediana **300**, máximo **301**.
- Abril–octubre 2025: mínimo **50**, máximo **51** por parcela.
- La observación preliminar de aproximadamente 297–302 observaciones se **confirma con precisión como 298–301** en el archivo original.
- La tabla completa por parcela y el resumen min/Q1/mediana/media/Q3/max/std se guardan por separado.

## Integridad

- Fechas inválidas: **0**.
- Filas implicadas en duplicados exactos: **0**.
- Filas implicadas en claves parcela-fecha duplicadas: **0**.
- Máximo de registros para una clave parcela-fecha: **1**.
- Retrocesos de fecha dentro de parcela en el orden original: **31089**.
- No se eliminó ningún registro.

## Índices y missingness

- Columnas completamente vacías en Sentinel original: **4**: vi6t_promedio, vi6t_std, vi6t_max, vi6t_min.
- Filas parcialmente disponibles dentro de cuartetos mean/std/min/max, sumadas por índice: **0**.
- Violaciones completas de `min <= promedio <= max` o `std >= 0`, sumadas por índice: **0**.
- Los valores marcados como raros usan sólo una regla descriptiva de 3×IQR; no fueron eliminados ni declarados erróneos.

## Nubosidad

- Media global: **29.19%**; mediana: **0.00%**.
- Media abril–octubre 2025: **32.49%**; mediana: **0.00%**.
- Filas con nubosidad 100%: **14,163**; de ellas, **14,163** tienen todos los índices utilizables ausentes.
- Filas con nubosidad menor que 100% y algún índice utilizable ausente: **4**.
- No se aplicó ningún umbral. `sentinel_cloud_sensitivity.csv` cuantifica el costo de 10, 20, 30, 40, 50 y 70% para todo el periodo y para el ciclo 2025, global y por conjunto.

## TRAIN vs PREDICTION

La comparación se realizó sin usar el valor del rendimiento. Se compararon cobertura, nubosidad, missingness y rangos de todos los índices. Los resultados están en `sentinel_train_prediction_comparison.csv`; cualquier diferencia debe evaluarse como posible cambio de distribución antes del modelado, no como criterio automático de exclusión.

## Problemas y discrepancias detectados

1. “Observaciones repetidas” no equivale necesariamente a duplicados: esta auditoría distingue múltiples fechas por parcela de claves parcela-fecha repetidas.
2. El Dataset Básico conserva columnas que pueden estar 100% vacías para Sentinel; el CSV procesado tiene 92 columnas frente a 96 del original.
3. Nubosidad está concentrada en valores extremos, por lo que no debe asumirse que funciona como una variable continua ordinaria.
4. Las unidades y rangos físicos válidos de cada índice no están codificados en el CSV.

## Decisiones pendientes

1. Definir el umbral de nubosidad mediante sensibilidad de cobertura y validación posterior; no fijarlo por intuición.
2. Decidir si una fila con nubosidad alta pero índices presentes se conserva, se marca o se excluye.
3. Confirmar con el diccionario los rangos físicos y unidades antes de clasificar extremos como errores.
4. Definir el corte temporal de predicción dentro de abril–octubre de 2025.
5. Elegir una estrategia de representación de missingness antes de construir features.

## Recomendaciones para la etapa siguiente

- Mantener una fila por parcela-fecha durante la construcción de series.
- Conservar nubosidad y flags de disponibilidad junto a cada observación.
- Calcular features individuales sin target antes del CV; ajustar imputación, selección supervisada y escalamiento dentro de cada fold.
- Reutilizar exactamente los mismos splits persistidos para las tres familias.
- No mezclar todavía Sentinel con otros sensores hasta definir alineación y sesgos.
