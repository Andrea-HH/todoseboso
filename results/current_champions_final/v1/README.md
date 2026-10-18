# Resultados finales — Reference26 y Compact14

**Esta presentación corresponde a las59 predicciones finales de los dos champions actuales**, ajustados con los138 rendimientos conocidos. Incluye como referencias las estimaciones anteriores de C-T3, modelo histórico TOP20/TOP15, EQUAL3 y L40, preservadas sin cambios. No se promovió otro champion ni se eligieron pesos por acuerdo entre estas predicciones.

## Evidencia de validación de los champions

Estas métricas son OOF de las138 parcelas conocidas, **no errores de las59**. Son los65 folds originales:50 aleatorios,5 por perfil,5 municipales y5 espaciales. Aleatoria promedia métricas de10 OOF completas, no RMSE de folds.

| Modelo | Protocolo | RMSE t/ha | R² | MAE t/ha |
|---|---|---|---|---|
| Reference26 | random | 0.4748 | 0.6865 | 0.3396 |
| Reference26 | climate_profile | 0.4774 | 0.6831 | 0.3342 |
| Reference26 | municipality | 0.5752 | 0.5400 | 0.4491 |
| Reference26 | spatial | 0.6333 | 0.4423 | 0.5004 |
| Compact14 | random | 0.4773 | 0.6832 | 0.3399 |
| Compact14 | climate_profile | 0.4793 | 0.6805 | 0.3336 |
| Compact14 | municipality | 0.5755 | 0.5395 | 0.4468 |
| Compact14 | spatial | 0.6431 | 0.4250 | 0.5140 |

El resultado97/41 de26 (.4625 RMSE/.6971 R²) y14 (.4661/.6933) pertenece a [otra tabla de evaluación](../../comparison_97_41/v1/README.md), sobre las mismas etiquetas. Los residuos regionales y las auditorías OOF están en [validación actual](../../current_champions/v1/README.md).

## Qué predicen para las59

Estadísticos descriptivos en t/ha, no residuos ni intervalos de error:

| Champion | Parcelas | Media | Desviación | Mínimo | Mediana | Máximo |
|---|---|---|---|---|---|---|
| Reference26 | 59 | 3.9564 | 0.6976 | 2.7598 | 4.3489 | 4.8196 |
| Compact14 | 59 | 3.9502 | 0.6855 | 2.7686 | 4.3170 | 4.8113 |

## Diferencias con otras predicciones

Diferencia absoluta media: cercanía entre estimaciones, **no MAE contra rendimiento verdadero**. El rango entre modelos no es un intervalo predictivo.

| A | B | Diferencia absoluta media, t/ha | Máxima diferencia absoluta |
|---|---|---|---|
| CT3_t_ha | Reference26_t_ha | 0.1324 | 0.4476 |
| CT3_t_ha | Compact14_t_ha | 0.1307 | 0.4384 |
| Historical_TOP20_TOP15_t_ha | Reference26_t_ha | 0.1441 | 0.4944 |
| Historical_TOP20_TOP15_t_ha | Compact14_t_ha | 0.1342 | 0.4795 |
| EQUAL3_t_ha | Reference26_t_ha | 0.1135 | 0.4582 |
| EQUAL3_t_ha | Compact14_t_ha | 0.1182 | 0.5292 |
| Local04D_t_ha | Reference26_t_ha | 0.1010 | 0.3054 |
| Local04D_t_ha | Compact14_t_ha | 0.1037 | 0.2401 |
| Reference26_t_ha | Compact14_t_ha | 0.0376 | 0.1054 |

[Todos los pares y correlaciones](pairwise_disagreement.csv) · [Distribuciones de los seis modelos](prediction_distributions.csv). Los estados, municipios y parcelas con mayor desacuerdo están en el Excel privado.

## Cómo se obtuvieron y comprobaron

Las recetas congeladas se consolidaron con138 etiquetas y KFold interno4, shuffle y semilla2026. Las entradas PRED se incorporaron después de ajustar. Se verificó paridad de las26 variables reconstruidas en las138 conocidas y geometría congelada exacta. Las predicciones se reprodujeron desde el modelo guardado y no cambiaron al alterar etiquetas ficticias PRED sólo en memoria. El registro de exclusión interna se verificó.

R3 dispone de soporte completo en51/59; en las otras se desactiva. La base C-T3 recalibrada nativamente difiere de su consolidación histórica en0.0473t/ha de diferencia absoluta media. El Excel conserva ambas: la diferencia champion−C-T3 histórico incluye esa recalibración, además de las capas complementarias.

La descomposición por parcela comprueba la suma de C-T3, mezcla local, corrector interno y ajuste R3. Es explicación del cálculo, no atribución causal. Se registró una advertencia ambiental OpenMP; el ajuste y las comprobaciones terminaron, sin advertencias de convergencia registradas. [Auditoría](prediction_audit.json) · [Procedencia de la generación](provenance.json). Las métricas de validación previas permanecen intactas.

## Archivos finales locales

| Archivo | Contenido |
|---|---|
| [Reference26_predictions59.csv](../../../outputs/modeling/current_champions_final/v1/Reference26_predictions59.csv) | 59 ID y rendimientos del champion26 |
| [Compact14_predictions59.csv](../../../outputs/modeling/current_champions_final/v1/Compact14_predictions59.csv) | 59 ID y rendimientos del champion14 |
| [comparacion_predicciones59.xlsx](../../../outputs/modeling/current_champions_final/v1/comparacion_predicciones59.xlsx) | Comparación de seis modelos, regiones, soporte y componentes |
| [predictions59_comparison.csv](../../../outputs/modeling/current_champions_final/v1/predictions59_comparison.csv) | Tabla conjunta; ambas versiones C-T3 explícitas |
| [champion_prediction_components.csv](../../../outputs/modeling/current_champions_final/v1/champion_prediction_components.csv) | Descomposición verificada de26/14 |
| [prediction_scatter59.png](../../../outputs/modeling/current_champions_final/v1/prediction_scatter59.png) | Gráficas de desacuerdo por estado |

Estos enlaces requieren la copia local: `outputs/` no se sube a Git. Su existencia no acredita envío al comité. Todavía no conocemos el error de las59.

[Ficha26](../../../documentation/models/Reference26/README.md) · [Ficha14](../../../documentation/models/Compact14/README.md) · [Índice de resultados](../../README.md). Generación reproducible: `scripts/526_current_champions_final59.py`; descomposición: `scripts/527_finalize_prediction_comparison.py`; esta presentación se regenera con `scripts/532_refresh_results_readmes.py` sin entrenar modelos.

[Descriptivos de26:59 estimaciones frente a138 rendimientos, por estado y municipio](../../reference26_distribution/v1/README.md).
