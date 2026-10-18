# Banco adicional97/41 — comparación separada

**16 particiones:97 parcelas para entrenamiento y41 para evaluación en cada una**, reutilizando las mismas138 parcelas conocidas. RMSE, R², MAE y sesgo se calculan sobre las41 predicciones retenidas de cada partición y luego se promedian entre las16. No se concatenan como656 parcelas independientes ni se mezclan con las OOF completas de los65 folds originales.

Simula un conjunto de rendimientos faltantes con entrenamiento territorialmente representado. Es evidencia exploratoria complementaria, no validación territorial por municipio/bloque, muestra independiente ni error conocido de las59 PRED. Los mismos41 identificadores no tienen que repetirse entre particiones.

| Modelo | RMSE t/ha ↓ | R² ↑ | MAE t/ha ↓ | Sesgo predicho−observado |
|---|---|---|---|---|
| CT3 | 0.4918 | 0.6571 | 0.3642 | +0.0172 |
| L40 | 0.4893 | 0.6621 | 0.3552 | -0.0023 |
| Reference26 | 0.4625 | 0.6971 | 0.3387 | +0.0016 |
| Compact14 | 0.4661 | 0.6933 | 0.3398 | +0.0020 |
| B1 | 0.4622 | 0.6975 | 0.3373 | +0.0026 |
| B2 | 0.4657 | 0.6939 | 0.3392 | +0.0026 |
| B3 | 0.4710 | 0.6858 | 0.3440 | -0.0031 |
| B4 | 0.4688 | 0.6888 | 0.3414 | -0.0016 |
| B5 | 0.4624 | 0.6972 | 0.3374 | +0.0033 |
| B6 | 0.4706 | 0.6862 | 0.3436 | -0.0029 |

Reference26 y Compact14 son los champions actuales; C-T3 es control y L40 referencia externa. B1–B6 son sensibilidades, no champions adicionales. Las diferencias pequeñas no demuestran superioridad estadística. Este banco no se confunde con los checkpoints originales de GeoC, aunque utilicen también entrenamiento97/evaluación41.

[Fichas](../../../documentation/models/README.md) · [Diseño de mezclas](../../../documentation/four_expert_combinations_design.md) · [Particiones posicionales](../../../configs/validation/original65_plus_fresh16.json) · [CSV agregado](metrics.csv). La tabla omite modelos sin evaluación compatible disponible, como modelo histórico TOP20/TOP15 y EQUAL3 en este archivo; no se les atribuyen resultados por analogía.
