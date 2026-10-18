# Modelo histórico — TOP20 → TOP15 → topografía

**Estado: histórico. No es Reference26 ni Compact14, los dos champions actuales.** Identificador conservado: `A_CURRENT_CH_H_T`; alias antiguos `Champion` y `CHAMPION`. No se reasigna ese identificador a la receta de 26 entradas.

## Arquitectura y variables

Base climática Elastic Net con selección TOP20, corrección histórica XGBoost con selección TOP15 y corrección topográfica Ridge25. TOP20/TOP15 nombran cantidades de variables seleccionadas en su etapa, no conjuntos fijos universales ni componentes PCA. La selección se realiza con el entrenamiento correspondiente; las variables pueden cambiar entre folds. No es un modelo de 20+15 entradas fijas equivalente a 26/14.

## Origen, ventajas y limitaciones

Representa la etapa de integración secuencial clima → historia → topografía anterior a la investigación con expertos locales compactos. Permitió separar aportes incrementales y conserva una entrega histórica59. Su mayor número de fuentes y correcciones motivó comparaciones posteriores y simplificaciones; su antigua etiqueta de champion no implica que sea la elección vigente.

La lista concreta seleccionada corresponde a cada modelo guardado y a su auditoría histórica; no se inventa una lista única a partir de los nombres TOP20/TOP15. Véase [consolidación histórica](../../winner_predictions_statistical_validation.md) y [registro vigente](../../model_registry.md). Artefactos locales: `outputs/modeling/winner_predictions/v1/`. No se sobrescriben sus modelos ni sus predicciones. Las columnas históricas llamadas `Champion_t_ha` siguen correspondiendo a esta receta.
