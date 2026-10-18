# B1 — ficha del modelo

Estado vigente: 2026-10-18. Champions actuales: **Reference26 y Compact14**. [Índice de modelos](../README.md).

## Función y arquitectura

**Sensibilidad, no champion.** `B1 = C-T3 + a·(Reference26 − C-T3)`, con a limitado a [0,1]. Sus entradas son exactamente las 26 de Reference26; añadir un peso aprendido no añade una fuente, pero tampoco simplifica el sistema.

El peso minimiza pérdida cuadrática sobre predicciones honestas de validación interna, con los expertos recalibrados dentro del entrenamiento. No se escoge mirando el fold externo, por reglas municipales ni por el acuerdo con L40. Cada ajuste aprende su propio peso.

## Origen y evidencia

Surge de la [batería de mezclas B1–B6](../../four_expert_combinations_conclusions.md), motivada por complementariedad entre el comportamiento central de C-T3 y los extremos de 26. Véanse [diseño congelado](../../four_expert_combinations_design.md) y [resultados](../../four_expert_combinations_results.md). No es EQUAL3 ni una mezcla de L40.

## Ventajas y límites

Ofrece una interpolación interpretable entre dos predicciones y el menor RMSE municipal observado entre los cinco modelos de esta comparación. En aleatoria queda cerca de 26.

Pierde espacial frente a ambos champions y no reduce sus dependencias. La ventaja municipal no justifica sustituir26 globalmente. Pesos distintos entre entrenamientos pueden empeorar una métrica agregada aunque cada predicción sea convexa entre sus dos extremos. La selección histórica de muchas alternativas impide presentar esa ventaja como confirmación independiente.

## Inventario exacto de entradas

| # | Variable | Significado y ubicación |
|---|---|---|
| 1 | `compact_precip_total` | **Base C-T3.** Precipitación acumulada abril–octubre de 2025; cantidad de lluvia. |
| 2 | `compact_early_fraction` | **Base C-T3.** Fracción de lluvia abril–junio respecto al total abril–octubre; distribución temprana. |
| 3 | `compact_concentration_hhi` | **Base C-T3.** Suma de cuadrados de las participaciones mensuales; concentración temporal de lluvia. |
| 4 | `S2_ndvi_month_05` | **Base C-T3.** NDVI Sentinel-2 de mayo de 2025; estado de vegetación temprano. |
| 5 | `sat_basic_hist__sentinel_2__ndvi_promedio__mean` | **Experto local.** Media histórica de NDVI promedio Sentinel-2; abril–octubre, hasta 2024 según manifiesto GeoC. |
| 6 | `sat_basic_hist__sentinel_2__ndvi_promedio__std` | **Experto local.** Dispersión histórica de NDVI promedio Sentinel-2; abril–octubre, hasta 2024 según manifiesto GeoC. |
| 7 | `emp_shape__y2025_planet_evi__turning_fraction` | **Experto local.** Fracción de pendientes consecutivas que cambian de signo en los siete resúmenes mensuales EVI Planet, abril–octubre de 2025; forma empírica, no etapa fenológica observada. |
| 8 | `agro_pheno__y2025_planet_ndvi__jun_to_aug_delta` | **Experto local.** NDVI Planet de agosto menos NDVI de junio de 2025. |
| 9 | `sat_basic_2025__sentinel_2__ndwi_promedio__mean` | **Experto local.** Media de NDWI Sentinel-2 en 2025. |
| 10 | `sat_basic_2025__sentinel_2__ndwi_promedio__std` | **Experto local.** Dispersión de NDWI Sentinel-2 en 2025. |
| 11 | `topo_official__slope__mean` | **Experto local.** Pendiente topográfica media en grados; estadístico zonal de Pendiente_INEGI_CEM4_120m_grados.tif según manifiesto GeoC. |
| 12 | `base_centroid_lat` | **Vecindario.** Latitud del centroide: selección y ponderación de vecinos geográficos. |
| 13 | `base_centroid_lon` | **Vecindario.** Longitud del centroide: selección y ponderación de vecinos geográficos. |
| 14 | `geology_physiography::geo250_share__Q(B)` | **Compuerta física.** Proporción cartográfica de la categoría Q(B); entrada de la compuerta, no coeficiente directo de rendimiento. |
| 15 | `geology_physiography::geo250_share__Q(B-Bvb)` | **Compuerta física.** Proporción cartográfica de la categoría Q(B-Bvb); entrada de la compuerta, no coeficiente directo de rendimiento. |
| 16 | `geology_physiography::geo250_share__Q(Bvb)` | **Compuerta física.** Proporción cartográfica de la categoría Q(Bvb); entrada de la compuerta, no coeficiente directo de rendimiento. |
| 17 | `geology_physiography::geo250_share__Q(al)` | **Compuerta física.** Proporción cartográfica de la categoría Q(al); entrada de la compuerta, no coeficiente directo de rendimiento. |
| 18 | `geology_physiography::geo250_share__Ts(A)` | **Compuerta física.** Proporción cartográfica de la categoría Ts(A); entrada de la compuerta, no coeficiente directo de rendimiento. |
| 19 | `geology_physiography::geo250_share__Ts(B)` | **Compuerta física.** Proporción cartográfica de la categoría Ts(B); entrada de la compuerta, no coeficiente directo de rendimiento. |
| 20 | `geology_physiography::geo250_share__Ts(R)` | **Compuerta física.** Proporción cartográfica de la categoría Ts(R); entrada de la compuerta, no coeficiente directo de rendimiento. |
| 21 | `geology_physiography::geo250_share__Ts(R-Ta)` | **Compuerta física.** Proporción cartográfica de la categoría Ts(R-Ta); entrada de la compuerta, no coeficiente directo de rendimiento. |
| 22 | `geology_physiography::geo250_share__Ts(Ta)` | **Compuerta física.** Proporción cartográfica de la categoría Ts(Ta); entrada de la compuerta, no coeficiente directo de rendimiento. |
| 23 | `geology_physiography::geo250_share__Ts(Ti)` | **Compuerta física.** Proporción cartográfica de la categoría Ts(Ti); entrada de la compuerta, no coeficiente directo de rendimiento. |
| 24 | `I_history_ndvi_floor` | **Corrector final R3.** Media 2022–2024 de medias anuales de medianas mensuales de NDVI mínimo, mayo–octubre; exige tres años completos. |
| 25 | `I_gap_excess_persistence` | **Corrector final R3.** Persistencia del exceso positivo de la brecha relativa NDVI promedio−mínimo en mayo–octubre de 2025 frente a los mismos meses de 2022–2024: (suma z+)²/(6·suma z+²). Brecha normalizada por max(|NDVI promedio|,.1), limitada a [0,5]; piso de SD histórica .05 y z limitado a ±6. Cero si no hay exceso; faltante si falta soporte mensual. |
| 26 | `I_slope_min` | **Corrector final R3.** Pendiente mínima TOPO_BASIC_slope_min; contexto topográfico del corrector, no pendiente temporal de NDVI. |

Las ventanas y agregaciones de las columnas heredadas se conservan tal como están en las tablas procesadas; su nombre no acredita por sí solo uniformidad de fechas entre sensores. Las tres fórmulas R3 se implementan en [temporal_indicator_weights.py](../../../src/temporal_indicator_weights.py). Las entradas derivadas y sus hashes constan en [el manifiesto de insumos](../../../configs/current_champions_inputs.json).

## Resultados compatibles y lectura

RMSE t/ha / R² / MAE t/ha. OOF completas por repetición y después promedio; mismos 65 folds, 138 parcelas.

| Aleatoria | Perfil climático | Municipal | Espacial |
|---|---|---|---|
| .4755 / .6856 / .3396 | .4839 / .6744 / .3408 | .5681 / .5513 / .4426 | .6813 / .3546 / .5388 |

Son resultados de validación exploratoria tras reutilización de etiquetas, no el error de las 59 desconocidas ni superioridad universal. Residuo = predicho − observado: positivo significa sobreestimación. El banco adicional 97/41 se interpreta por separado. No se presenta R² ajustado clásico para estas arquitecturas locales y calibradas.

## Archivos y reproducción

Implementación integrada: [src/current_champions.py](../../../src/current_champions.py). [Reproducción y alcance de la verificación](../../current_champions_reproduction.md). Entrada: `python scripts/521_current_champions.py replay`; reentrenamiento: subcomando `refit` según esa guía. Bundle privado: `data/processed/current_champions/v1/`; OOF: `outputs/research/current_champions/v1/`; [métricas públicas](../../../results/current_champions/v1/README.md). Las fichas no generan nuevos ajustes finales ni predicciones59.

## Comparación final59 disponible

Los champions26/14 ya tienen ajustes finales con138 y sus59 estimaciones se incorporaron a la comparación existente sin sobrescribir las anteriores. [Reporte de diferencias entre predicciones](../../../results/current_champions_final/v1/README.md). Archivo privado: `outputs/modeling/current_champions_final/v1/comparacion_predicciones59.xlsx`. Estas diferencias no son errores contra rendimientos observados.
