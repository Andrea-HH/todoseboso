# Resultados vigentes — champions Reference26 y Compact14

**Los dos champions ya tienen ajuste final con138 rendimientos y59 predicciones generadas.** El modelo histórico TOP20/TOP15 y EQUAL3 son antecedentes; C-T3 es control y L40 benchmark externo. B1 es una sensibilidad, no un tercer champion.

| Presentación | Qué contiene | Cómo interpretarla |
|---|---|---|
| [Predicciones finales de26/14 y comparación59](current_champions_final/v1/README.md) | Distribución de las estimaciones y desacuerdos con C-T3, modelo histórico, EQUAL3 y L40 | Sin rendimientos verdaderos de59: no son errores ni R² de entrega |
| [Validación de los modelos actuales](current_champions/v1/README.md) | RMSE/R²/MAE, sesgo y residuos OOF de138 | Rendimiento bajo los cuatro protocolos originales; no rendimiento real de59 |
| [Banco adicional97/41](comparison_97_41/v1/README.md) |16 particiones con97 entrenamiento y41 evaluación | Mismas138 etiquetas; tabla separada, no confirmación independiente |
| [Relevancia de cuatro entradas C-T3](core4_relevance/v1/README.md) | Asociación y ablaciones reajustadas | Diagnóstico exploratorio; no significancia individual de26 entradas |
| [Evidencia por componente de26](reference26_component_evidence/v1/README.md) | Ablaciones históricas, interacciones y respaldo de funciones | Recuperación de experimentos existentes, con límites y faltantes |

Las predicciones por parcela, modelos, datos y OOF permanecen en `outputs/` y `data/`, excluidos de Git. Este directorio publica resúmenes agregados. Un clon sólo de Git no incluye los archivos privados.

[Fichas de los modelos](../documentation/models/README.md) · [Registro vigente](../documentation/model_registry.md).

[Cuatro investigaciones finales](four_final_checks/v1/README.md): reproducción limpia, soporte59, intervalos y sensibilidad completa sin HHI. No modifica los champions26/14.
