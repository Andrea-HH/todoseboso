# CT3 — ficha del modelo

Estado vigente: 2026-10-18. Champions actuales: **Reference26 y Compact14**. [Índice de modelos](../README.md).

## Función y arquitectura

**Control compacto, no champion actual.** Elastic Net global sobre cuatro entradas. La imputación y estandarización se ajustan con el entrenamiento correspondiente. La selección interna compara alpha [.001,.01,.1,1] y l1_ratio [.1,.5,.9]. No tiene experto local ni compuerta ni corrección R3.

## Origen y evidencia

La exploración de lluvia y temperatura y las representaciones compactas llevaron al núcleo de tres resúmenes de lluvia más NDVI de mayo. Se conserva como C-T3 en las investigaciones de información incremental y residual; F5, F6 y F7 reutilizan esas cuatro entradas para aislar el efecto de arquitectura. Véanse [exploración de clima](../../h_rain_tmax_extension.md), [investigación C-T3](../../ct3_residual_conditional.md) y [comparación de líderes](../../four_leaders_comparison.md). Estas son etapas de procedencia; no se atribuye su selección a un único p-valor.

## Ventajas y límites

Cuatro entradas, un modelo global y bajo costo operativo. Es la referencia más fácil de explicar y conserva buena proporción de errores moderados. En la comparación de líderes, su proporción espacial dentro de ±.5 t/ha supera la de 26, aunque 26 reduce más los errores grandes. No domina toda la distribución del error.

La forma global lineal limita interacciones y diferenciación entre parcelas con valores idénticos. Comprime extremos. El R² global incorpora diferencias entre regiones y no implica el mismo poder explicativo dentro de cada estado. Tampoco es un modelo exclusivamente climático: incluye NDVI.

## Inventario exacto de entradas

| # | Variable | Significado y ubicación |
|---|---|---|
| 1 | `compact_precip_total` | **Base C-T3.** Precipitación acumulada abril–octubre de 2025; cantidad de lluvia. |
| 2 | `compact_early_fraction` | **Base C-T3.** Fracción de lluvia abril–junio respecto al total abril–octubre; distribución temprana. |
| 3 | `compact_concentration_hhi` | **Base C-T3.** Suma de cuadrados de las participaciones mensuales; concentración temporal de lluvia. |
| 4 | `S2_ndvi_month_05` | **Base C-T3.** NDVI Sentinel-2 de mayo de 2025; estado de vegetación temprano. |

Las ventanas y agregaciones de las columnas heredadas se conservan tal como están en las tablas procesadas; su nombre no acredita por sí solo uniformidad de fechas entre sensores. Las tres fórmulas R3 se implementan en [temporal_indicator_weights.py](../../../src/temporal_indicator_weights.py). Las entradas derivadas y sus hashes constan en [el manifiesto de insumos](../../../configs/current_champions_inputs.json).

## Resultados compatibles y lectura

RMSE t/ha / R² / MAE t/ha. OOF completas por repetición y después promedio; mismos 65 folds, 138 parcelas.

| Aleatoria | Perfil climático | Municipal | Espacial |
|---|---|---|---|
| .5116 / .6361 / .3749 | .5206 / .6232 / .3915 | .5813 / .5302 / .4603 | .6788 / .3594 / .5306 |

Son resultados de validación exploratoria tras reutilización de etiquetas, no el error de las 59 desconocidas ni superioridad universal. Residuo = predicho − observado: positivo significa sobreestimación. El banco adicional 97/41 se interpreta por separado. No se presenta R² ajustado clásico para estas arquitecturas locales y calibradas.

## Archivos y reproducción

Implementación integrada: [src/current_champions.py](../../../src/current_champions.py). [Reproducción y alcance de la verificación](../../current_champions_reproduction.md). Entrada: `python scripts/521_current_champions.py replay`; reentrenamiento: subcomando `refit` según esa guía. Bundle privado: `data/processed/current_champions/v1/`; OOF: `outputs/research/current_champions/v1/`; [métricas públicas](../../../results/current_champions/v1/README.md). Las fichas no generan nuevos ajustes finales ni predicciones59.

## Comparación final59 disponible

Los champions26/14 ya tienen ajustes finales con138 y sus59 estimaciones se incorporaron a la comparación existente sin sobrescribir las anteriores. [Reporte de diferencias entre predicciones](../../../results/current_champions_final/v1/README.md). Archivo privado: `outputs/modeling/current_champions_final/v1/comparacion_predicciones59.xlsx`. Estas diferencias no son errores contra rendimientos observados.
