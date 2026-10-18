# Comparación de predicciones finales de 59 parcelas

Se incorporaron **Reference26 y Compact14**, champions actuales, a la comparación existente de C-T3, Champion histórico TOP20/TOP15, EQUAL3 y L40. Los valores anteriores se conservaron sin reentrenar sus modelos. El archivo original permanece intacto.

Las dos recetas actuales se consolidaron con los 138 rendimientos conocidos, KFold interno4 con shuffle y semilla2026, mismos hiperparámetros y lógica de calibración congelados. La selección y los residuos internos usan sólo entrenamiento. No se seleccionaron variantes por sus predicciones59 ni por acuerdo con L40. C-T3 interno se reajusta como parte nativa de la receta; la comparación conserva el C-T3 final histórico y entrega el nuevo por separado.

## Diferencias entre predicciones

Estos números son **desacuerdos**, no RMSE/MAE contra rendimientos reales. No se conoce cuál modelo acierta más en las59 y el rango entre modelos no es un intervalo predictivo.

| A | B | Media A−B t/ha | Diferencia absoluta media t/ha | Máxima diferencia absoluta |
|---|---|---|---|---|
| CT3_t_ha | Reference26_t_ha | -0.0365 | 0.1324 | 0.4476 |
| CT3_t_ha | Compact14_t_ha | -0.0302 | 0.1307 | 0.4384 |
| Historical_TOP20_TOP15_t_ha | Reference26_t_ha | -0.0541 | 0.1441 | 0.4944 |
| Historical_TOP20_TOP15_t_ha | Compact14_t_ha | -0.0479 | 0.1342 | 0.4795 |
| EQUAL3_t_ha | Reference26_t_ha | -0.0166 | 0.1135 | 0.4582 |
| EQUAL3_t_ha | Compact14_t_ha | -0.0103 | 0.1182 | 0.5292 |
| Local04D_t_ha | Reference26_t_ha | -0.0121 | 0.1010 | 0.3054 |
| Local04D_t_ha | Compact14_t_ha | -0.0059 | 0.1037 | 0.2401 |
| Reference26_t_ha | Compact14_t_ha | 0.0063 | 0.0376 | 0.1054 |

## Archivos

Los detalles por parcela y municipio son privados, bajo `outputs/modeling/current_champions_final/v1/`: `comparacion_predicciones59.xlsx`, `predictions59_comparison.csv`, dos archivos individuales de champions, desacuerdos regionales, soporte y modelo final. Git conserva sólo resúmenes sin identificadores. [Fichas de modelos](../../../documentation/models/README.md).

Soporte completo para R3: 51/59 parcelas. La corrección final se desactiva donde falta soporte, siguiendo la receta original.

## Interpretación de las diferencias

- Reference26 frente a CT3_t_ha: diferencia firmada media champion−referencia **+0.0365 t/ha**, diferencia absoluta media **0.1324 t/ha**.
- Reference26 frente a Local04D_t_ha: diferencia firmada media champion−referencia **+0.0121 t/ha**, diferencia absoluta media **0.1010 t/ha**.
- Compact14 frente a CT3_t_ha: diferencia firmada media champion−referencia **+0.0302 t/ha**, diferencia absoluta media **0.1307 t/ha**.
- Compact14 frente a Local04D_t_ha: diferencia firmada media champion−referencia **+0.0059 t/ha**, diferencia absoluta media **0.1037 t/ha**.

Por estado (diferencia firmada champion−referencia / diferencia absoluta media):

| Estado | Champion | Frente a | Media firmada | Absoluta media | n |
|---|---|---|---|---|---|
| Hidalgo | Reference26_t_ha | CT3_t_ha | +0.0055 | 0.1588 | 15 |
| Puebla | Reference26_t_ha | CT3_t_ha | +0.0316 | 0.0988 | 29 |
| Tlaxcala | Reference26_t_ha | CT3_t_ha | +0.0769 | 0.1709 | 15 |
| Hidalgo | Compact14_t_ha | CT3_t_ha | -0.0109 | 0.1289 | 15 |
| Puebla | Compact14_t_ha | CT3_t_ha | +0.0269 | 0.1058 | 29 |
| Tlaxcala | Compact14_t_ha | CT3_t_ha | +0.0778 | 0.1807 | 15 |
| Hidalgo | Reference26_t_ha | Local04D_t_ha | -0.0434 | 0.0878 | 15 |
| Puebla | Reference26_t_ha | Local04D_t_ha | +0.0180 | 0.0956 | 29 |
| Tlaxcala | Reference26_t_ha | Local04D_t_ha | +0.0562 | 0.1246 | 15 |
| Hidalgo | Compact14_t_ha | Local04D_t_ha | -0.0599 | 0.1130 | 15 |
| Puebla | Compact14_t_ha | Local04D_t_ha | +0.0134 | 0.0841 | 29 |
| Tlaxcala | Compact14_t_ha | Local04D_t_ha | +0.0571 | 0.1324 | 15 |

Las diferencias pueden descomponerse en la mezcla entre C-T3 y el experto y la corrección R3: `champion_prediction_components.csv` verifica que esos componentes reconstruyen exactamente las predicciones. Esto explica el cálculo; no demuestra efectos causales de variables. Los desacuerdos por municipio y las parcelas con mayor separación están en el Excel privado.

La recalibración nativa de C-T3 difiere de su consolidación histórica en **0.0473 t/ha de diferencia absoluta media**. Por ello, la diferencia champion−C-T3 histórico incluye tanto la nueva calibración de la base como las capas complementarias; no debe atribuirse por completo al experto o a R3. El Excel conserva ambas versiones y los componentes usan la base nativa.

No se adoptó un nuevo modelo ni se cambiaron pesos según esta comparación. Las métricas de validación de138 permanecen intactas y siguen siendo la evidencia de desempeño. No se calculan residuos, R² o errores sobre las59.
