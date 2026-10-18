> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Contrastes vecinales: conclusiones de la batería de árboles

Se completaron cuatro alternativas en las mismas 65 particiones. La utilidad más prometedora observada es moderar el peso del experto local; no hay una ganancia general demostrada ni se promueve un modelo. La alternativa continua solicitada después se evalúa por separado en `neighbor_signal_linear_results.md` y se sintetiza conjuntamente en `neighbor_signal_linear_conclusions.md`.

## Resultados

GEO_ATTENUATE obtiene RMSE/R² espacial 0.67489/0.36672 frente a 0.68081/0.35556 de J7. COMPACT_ATTENUATE obtiene 0.67556/0.36546 y mejora municipal a 0.57754/0.53623 frente a 0.58085/0.53090. Ambas empeoran ligeramente la aleatoria (0.48754 y 0.48770 frente a 0.48641). Ninguna domina los cuatro protocolos.

Las mejoras espaciales son pequeñas y principalmente del bloque 1: cambios de RMSE −0.02838 y −0.02868. Al omitir ese bloque, conservando predicciones y sin reajustar, la ventaja GEO queda en −0.000049 y COMPACT empeora +0.000884. El bloque 3 no cambia porque el ajuste final no tiene soporte suficiente para distinguir las rutas; el respaldo conserva J7. No se optimizó específicamente ningún bloque.

Los correctores residuales de árbol empeoran espacialmente: GEO_RESIDUAL 0.70957 y COMPACT_RESIDUAL 0.71521 frente a 0.68081. Aunque reducen el sesgo espacial medio, aumentan el error total: corregir el sesgo agregado no asegura reducir dispersión o RMSE. El corrector COMPACT sí mejora modestamente perfil y municipal, sin compensar ese deterioro. No se recomienda incorporarlos.

Ninguno de los 32 contrastes conserva significancia tras Holm. Los intervalos y resultados son exploratorios; pocos grupos territoriales y selección histórica de señales limitan las conclusiones.

## Las dos parcelas y la distribución de ganancias

En aleatoria las atenuaciones casi no cambian 015 y reducen el error de 171 en aproximadamente 0.004–0.005 t/ha: los errores siguen alrededor de +2 t/ha. Esto era un límite de la formulación: una mezcla entre J7 y CT3 no puede salir del rango de sus predicciones cuando ambos comparten el fallo. La corrección residual puede salir de ese rango, pero se limitó a ±0.5 t/ha y sus cambios no generalizaron bien.

Las ganancias espaciales de atenuación persisten al excluir 171/015 del cómputo, sin reajustar: −0.00545 y −0.00467 de RMSE. No dependen solo de esos casos, pero sí mucho del bloque 1. Los correctores residuales empeoran aún más sin esas dos parcelas. Los análisis de ganancias por parcela y omisiones se conservan completos en tablas.

La opción nula se eligió en 27/50 y 29/50 folds aleatorios para las atenuaciones COMPACT y GEO, y en 31/50 y 28/50 para los correctores respectivos. Seleccionar amplitud no nula no garantiza que el ajuste final sea aplicable: cuatro ajustes finales de atenuación tienen respaldo por insuficiente diferencia entre rutas (municipal índice 58 y espacial 62, para ambos vecindarios). Las reglas se contraen y acotan después del entrenamiento del árbol.

## ¿Sirven como alerta de error grande?

El máximo contraste absoluto no es un indicador general estable del error. En aleatoria, la AUC para identificar |error J7|>1 t/ha es 0.682 para COMPACT y 0.624 para GEO. Excluyendo 171/015 cae a 0.555 y 0.491. El MAE del quintil más anómalo, inicialmente 0.427/0.416 frente a 0.327/0.329 del resto, queda aproximadamente igual al resto al excluir esos dos casos.

En espacial no mejora esa lectura: AUC 0.501 para COMPACT y 0.558 para GEO, con correlaciones de rango negativas entre anomalía y error absoluto. No se justifica usar un umbral universal de contraste para asignar baja confianza o corregir hacia abajo. Los diagnósticos por estado y perfiles con n≥10 permiten ver heterogeneidad, sin convertir esas comparaciones en reglas regionales nuevas.

## Interpretación de las reglas y límites

Los árboles usan diferencias continuas; las reglas son la forma del estimador que relaciona esas diferencias con el ajuste. El campo `values` de `rules_by_fold.csv` contiene los valores finales contraídos y acotados por hoja. El texto `rule` exportado de sklearn muestra los valores previos a esa calibración: no deben leerse como pesos aplicados. El entregable conjunto añade `deployed_rules_by_fold.csv`, que traduce cada hoja al ajuste efectivamente aplicado.

No se incluyó un control independiente de atenuación global con igual regularización. Por ello, incluso la pequeña mejora espacial no permite atribuir una contribución única a los contrastes frente a una reducción global del peso local. Tampoco las frecuencias de corte son significancia individual ni causalidad.

Los respaldos conservadores de calibración profunda se completaron para matrices con cero predictores variables, tanto con un solo municipio como dentro de un fold interno. Se preservaron los diseños y fuentes iniciales y 48 checkpoints aleatorios, sin modificar los parámetros del experimento ni las referencias externas. La media del entrenamiento equivale a un modelo de intercepto cuando no hay predictores variables; si un CV interno no es viable se emplean los parámetros conservadores ya fijados. Nunca se sustituyó una validación territorial por aleatoria. Los cambios y contextos están registrados en `implementation_amendments` y `audit`.

Se conservan J7 y CT3 como referencias. Para la pregunta del usuario sobre contrastes como variables, la etapa continua sin intercepto constituye una comparación más directa que las reglas arbóreas. No hay modelo final138, PRED59, cambio del Champion ni push.
