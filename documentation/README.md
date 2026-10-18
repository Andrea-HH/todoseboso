# Mapa de documentación

**Lectura vigente:** champions Reference26 y Compact14. [Fichas completas de los cinco modelos](models/README.md) · [Estado de la documentación histórica](model_status_history.md).

Esta carpeta reúne la documentación propia. `../docs/guidelines/` conserva los lineamientos/diccionarios; `../docs/resources/` contiene fuentes externas locales excluidas de Git. Los documentos históricos conservan su fecha, alcance y nombres: no todos describen el estado actual del proyecto.

## Ruta de lectura

**Etapa vigente: Reference26 y Compact14 son los champions actuales.** La [reproducción actual](current_champions_reproduction.md) incluye también C-T3 y B1, excluyeL40 y no requiereGeoC tras preparar el bundle. Los [resultados agregados](../results/current_champions/v1/README.md) están versionados. Los informes antiguos conservan su alcance histórico.

1. [Propósito y entregables](project_scope_and_guidelines.md): qué solución se quiere producir y cómo se relaciona con los lineamientos.
2. [Registro de modelos](model_registry.md): nombres, funciones, estados y ubicaciones; diferencia entre modelo histórico TOP20/TOP15 y candidatos recientes.
3. [Índice de experimentos](experiment_index.md): etapas, evidencia y puntos de entrada.
4. [Convenciones de comparación](model_comparison_convention.md): RMSE/R², OOF y protocolos compatibles.
5. [Explicación26/14/B1/L40](four_architecture_explanation.md): arquitectura, métricas, residuos y predicciones comparables.
6. [Reproducibilidad](reproducibility.md), [entorno](../environments/README.md) y [política Git](git_data_policy.md).
7. [Uso de IA generativa](ai_usage.md): transparencia, prompts y límites del registro.

## Qué significa cada documento

| Tipo | Qué acredita | Qué no acredita |
|---|---|---|
| `*design*`, `*proposal*`, `*plan*` | Alcance y configuración propuestos o congelados | Que todos sus experimentos se hayan ejecutado |
| `*results*`, auditorías y tablas de OOF | Resultados para el protocolo identificado | Error real de las 59 ni transferencia a cualquier región |
| `*conclusions*`, `*decision*`, `*recommendation*` | Interpretación y decisión de esa etapa | Promoción automática del Champion o autorización de otra batería |
| Entrega final con ajuste138 y predicciones59 | Una receta consolidada y sus estimaciones | Conocer el error de 59 sin sus rendimientos |

## Entradas recomendadas por tema

| Tema | Lectura |
|---|---|
| Objetivo y distribución de rendimientos | [Target](target_analysis.md), [diagnóstico R²](r2_residual_diagnosis.md) |
| Clima y C-T3 | [Lluvia](rainfall_yield_modeling.md), [lluvia+Tmax](h_rain_tmax_extension.md), [residual condicional](ct3_residual_conditional.md) |
| Suelo, topografía y territorio | [I](i_geographic_edaphological_exploration.md), [K](k_decision_summary.md), [representación física](physical_representation_results.md) |
| Modelos GPR y árboles | [F5](family5_gpr_initial_decision.md), [F6](family6_expansion.md), [F7](family7_expansion.md), [propuesta F8](family8_recommendation.md) |
| Comparación con GeoC | [Puente L40](geoc_bridge_results.md), [procedencia de variables](geoc_variable_signal_audit.md) |
| Simplificación y mezclas recientes | [Descomposición](architecture_decomposition_conclusions.md), [mezclas](four_expert_combinations_conclusions.md) |
| Predicciones históricas59 | [C-T3/modelo TOP20/TOP15/EQUAL3](winner_predictions_statistical_validation.md) |

El [inventario de archivos](inventories/repository_files.csv) permite localizar scripts, módulos, pruebas y documentos por ruta y descripción. Es un inventario de archivos, **no un conteo de modelos**: un script puede entrenar muchos ajustes y un diseño puede no haberse ejecutado.
