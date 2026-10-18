# Compact14 — ficha del modelo

Estado vigente: 2026-10-18. Champions actuales: **Reference26 y Compact14**. [Índice de modelos](../README.md).

## Función y arquitectura

**Champion actual compacto.** Alias: NO_PLANET_OFF_GLOBAL_MASK.

`predicción = C-T3 + w·(Ridge_local5 − C-T3) + intensidad·soporte_R3·delta_R3`.

El Ridge local usa 24 vecinos geográficos, alpha30 y potencia1. Cinco señales describen el experto; dos coordenadas seleccionan vecinos. El peso convexo global w se aprende con predicciones internas fuera de muestra: no es un 50/50 fijo ni un peso por municipio. R3 conserva los tres indicadores, su máscara de disponibilidad, Elastic Net alpha .01/l1_ratio .5 y corrección máxima ±.25 t/ha con intensidad elegida internamente.

## Origen y análisis de simplificación

Parte de la arquitectura de 26 y de su [simplificación factorial](../../architecture_decomposition_conclusions.md). Quitar únicamente el corrector interno no mejoró el sistema completo. La combinación de retirar Planet, retirar el corrector interno y reemplazar la compuerta geológica por un peso global produjo una alternativa distinta, cercana a la referencia.

La reconstrucción podada independiente verificó las mismas predicciones en los 65 folds sin calibrar con las fuentes retiradas. Esto sustenta **14 entradas para calibración y predicción**, no sólo 14 columnas visibles al final. Véanse [implementación podada](../../../src/pruned_global_architecture.py) y [comparación posterior](../../four_leaders_comparison.md).

## Ventajas y límites

Elimina Planet, las diez proporciones geológicas, la agrupación de la compuerta y el corrector climático interno del experto. Reduce 46.2% de entradas respecto a 26, con pérdidas observadas pequeñas en RMSE. Mantiene Sentinel histórico, NDWI2025, pendiente y corrección R3. Su sesgo espacial es menor que el de 26.

No elimina geografía, historia ni topografía. Su error espacial y el comportamiento en el cuartil alto son peores que los de 26; menor sesgo no significa menor error total. Sigue siendo un sistema compuesto y no una única regresión de 14 coeficientes. No se ha demostrado equivalencia estadística con 26. El bundle conjunto contiene 26 columnas para servir ambos champions; eso no cambia las 14 dependencias de esta receta.

## Inventario exacto de entradas

| # | Variable | Significado y ubicación |
|---|---|---|
| 1 | `compact_precip_total` | **Base C-T3.** Precipitación acumulada abril–octubre de 2025; cantidad de lluvia. |
| 2 | `compact_early_fraction` | **Base C-T3.** Fracción de lluvia abril–junio respecto al total abril–octubre; distribución temprana. |
| 3 | `compact_concentration_hhi` | **Base C-T3.** Suma de cuadrados de las participaciones mensuales; concentración temporal de lluvia. |
| 4 | `S2_ndvi_month_05` | **Base C-T3.** NDVI Sentinel-2 de mayo de 2025; estado de vegetación temprano. |
| 5 | `sat_basic_hist__sentinel_2__ndvi_promedio__mean` | **Experto local.** Media histórica de NDVI promedio Sentinel-2; abril–octubre, hasta 2024 según manifiesto GeoC. |
| 6 | `sat_basic_hist__sentinel_2__ndvi_promedio__std` | **Experto local.** Dispersión histórica de NDVI promedio Sentinel-2; abril–octubre, hasta 2024 según manifiesto GeoC. |
| 7 | `sat_basic_2025__sentinel_2__ndwi_promedio__mean` | **Experto local.** Media de NDWI Sentinel-2 en 2025. |
| 8 | `sat_basic_2025__sentinel_2__ndwi_promedio__std` | **Experto local.** Dispersión de NDWI Sentinel-2 en 2025. |
| 9 | `topo_official__slope__mean` | **Experto local.** Pendiente topográfica media en grados; estadístico zonal de Pendiente_INEGI_CEM4_120m_grados.tif según manifiesto GeoC. |
| 10 | `base_centroid_lat` | **Vecindario.** Latitud del centroide: selección y ponderación de vecinos geográficos. |
| 11 | `base_centroid_lon` | **Vecindario.** Longitud del centroide: selección y ponderación de vecinos geográficos. |
| 12 | `I_history_ndvi_floor` | **Corrector final R3.** Media 2022–2024 de medias anuales de medianas mensuales de NDVI mínimo, mayo–octubre; exige tres años completos. |
| 13 | `I_gap_excess_persistence` | **Corrector final R3.** Persistencia del exceso positivo de la brecha relativa NDVI promedio−mínimo en mayo–octubre de 2025 frente a los mismos meses de 2022–2024: (suma z+)²/(6·suma z+²). Brecha normalizada por max(|NDVI promedio|,.1), limitada a [0,5]; piso de SD histórica .05 y z limitado a ±6. Cero si no hay exceso; faltante si falta soporte mensual. |
| 14 | `I_slope_min` | **Corrector final R3.** Pendiente mínima TOPO_BASIC_slope_min; contexto topográfico del corrector, no pendiente temporal de NDVI. |

Las ventanas y agregaciones de las columnas heredadas se conservan tal como están en las tablas procesadas; su nombre no acredita por sí solo uniformidad de fechas entre sensores. Las tres fórmulas R3 se implementan en [temporal_indicator_weights.py](../../../src/temporal_indicator_weights.py). Las entradas derivadas y sus hashes constan en [el manifiesto de insumos](../../../configs/current_champions_inputs.json).

## Resultados compatibles y lectura

RMSE t/ha / R² / MAE t/ha. OOF completas por repetición y después promedio; mismos 65 folds, 138 parcelas.

| Aleatoria | Perfil climático | Municipal | Espacial |
|---|---|---|---|
| .4773 / .6832 / .3399 | .4793 / .6805 / .3336 | .5755 / .5395 / .4468 | .6431 / .4250 / .5140 |

### Banco adicional97/41 — resultado separado

| RMSE t/ha | R² | MAE t/ha | Sesgo predicho−observado |
|---|---|---|---|
| 0.4661 | 0.6933 | 0.3398 | +0.0020 |

Media de las métricas de **16 particiones**, cada una con97 parcelas para entrenar y41 para evaluar. Reutiliza las mismas138 parcelas; no es muestra independiente ni error de las59 PRED. Se conserva separado de los cuatro protocolos anteriores. [Comparación completa y procedencia](../../../results/comparison_97_41/v1/README.md).

Son resultados de validación exploratoria tras reutilización de etiquetas, no el error de las 59 desconocidas ni superioridad universal. Residuo = predicho − observado: positivo significa sobreestimación. El banco adicional 97/41 se interpreta por separado. No se presenta R² ajustado clásico para estas arquitecturas locales y calibradas.

## Archivos y reproducción

Implementación integrada: [src/current_champions.py](../../../src/current_champions.py). [Reproducción y alcance de la verificación](../../current_champions_reproduction.md). Entrada: `python scripts/521_current_champions.py replay`; reentrenamiento: subcomando `refit` según esa guía. Bundle privado: `data/processed/current_champions/v1/`; OOF: `outputs/research/current_champions/v1/`; [métricas públicas](../../../results/current_champions/v1/README.md). Las fichas no generan nuevos ajustes finales ni predicciones59.

## Comparación final59 disponible

Los champions26/14 ya tienen ajustes finales con138 y sus59 estimaciones se incorporaron a la comparación existente sin sobrescribir las anteriores. [Reporte de diferencias entre predicciones](../../../results/current_champions_final/v1/README.md). Archivo privado: `outputs/modeling/current_champions_final/v1/comparacion_predicciones59.xlsx`. Estas diferencias no son errores contra rendimientos observados.
