# Registro de modelos y estados

**Lectura vigente:** champions Reference26 y Compact14. [Fichas completas de los cinco modelos](models/README.md) · [Estado de la documentación histórica](model_status_history.md).

Estado documental al2026-10-18. Fuente estructurada: [configs/model_registry.json](../configs/model_registry.json). Las rutas de artefactos bajo `outputs/` son locales y no se publican en Git. Este registro orienta nombres y estados; no altera modelos ni decisiones históricas.

## Convención de estado

**Champions actuales: Reference26 y Compact14**, por selección explícita del responsable. C-T3 es el control y B1 la sensibilidad. L40 se conserva en la comparación como benchmark externo fuerte; queda fuera del reentrenamiento propio. Consultar la [etapa vigente](../configs/current_stage.json), la [reproducción](current_champions_reproduction.md) y los [resultados](../results/current_champions/v1/README.md). La selección no genera automáticamente ajustes finales138 ni predicciones59.

- **Champion actual:** receta seleccionada explícitamente para esta etapa; Reference26 y Compact14. No implica nuevo ajuste final ni nuevas59.
- **Control:** referencia reproducible para comparar, independientemente de que también tenga entrega histórica.
- **Champion histórico:** identificador conservado de una receta seleccionada en una etapa anterior.
- **Candidato experimental:** receta evaluada con OOF; no implica ajuste final ni autorización para generar59.
- **Entrega histórica59:** existe documentación de ajuste final y estimaciones; no acredita envío al comité ni conocer el error real de 59.
- **Propuesta:** documento de diseño; no se interpreta como ejecución.

## Modelos principales y ubicaciones

| Identificador / alias | Composición y papel | Código / documentación | Artefactos locales | Estado |
|---|---|---|---|---|
| C-T3 / CT3 | Elastic Net sobre compact4: total de lluvia, fracción temprana, HHI y NDVI mayo | [`src/ct3_residual_conditional/models.py`](../src/ct3_residual_conditional/models.py), [evaluación](ct3_residual_conditional.md) | `outputs/modeling/ct3_residual_conditional/v1/`; entrega en `outputs/modeling/winner_predictions/v1/` | Control; entrega histórica59 |
| Champion / `A_CURRENT_CH_H_T` | Clima TOP20 Elastic Net + historia TOP15 XGBoost + topografía Ridge 25; selecciones por entrenamiento | [Consolidación y entrega](winner_predictions_statistical_validation.md) | `outputs/modeling/winner_predictions/v1/` | Champion histórico; entrega59; no confundir con26 |
| EQUAL3 | Promedio fijo de C-T3, GPR F5-01 y CatBoost F7-00 | [Entrega histórica](winner_predictions_statistical_validation.md) | `outputs/modeling/winner_predictions/v1/` | Ensamble histórico con59 |
| F5-01 | GPR Matérn3/2 por bloques de lluvia compacta y NDVI mayo | [`src/family_5/`](../src/family_5/), [decisión](family5_gpr_initial_decision.md), [sensibilidadS1](family5_gpr_s1.md) | Rutas específicas en los informesF5 | Experimento; también componente deEQUAL3 |
| F7-00 | CatBoost directo compact4; extensiones E1–E3 son otras recetas | [`src/family_7/`](../src/family_7/), [F7](family7_boosting.md), [expansión](family7_expansion.md) | Rutas específicas en informesF7 y entrega histórica | Experimento; también componente deEQUAL3 |
| L40 / Local04D / LOCAL04D | PCA20 de C4(2082) + Ridge local24 vecinos geográficos, alpha30,potencia1 | [`src/geoc_local04d_snapshot.py`](../src/geoc_local04d_snapshot.py), [`src/geoc_bridge.py`](../src/geoc_bridge.py), [puente](geoc_bridge_results.md) | `outputs/modeling/geoc_bridge/v1/`; covariables/artefactos de GeoC requeridos para preparar el puente | Benchmark externo fuerte del equipo; incluido en las tablas, excluido del reentrenamiento propio. Se conserva la auditoría original |
| Reference26 / `FULL7_ON_RAW_MASK` / `SHARES_MASK` en la línea anterior | CT3 + local7 con corrección interna + compuerta geológica + R3 con máscara | [`src/current_champions.py`](../src/current_champions.py), [reproducción](current_champions_reproduction.md) | `outputs/research/current_champions/v1/`; resultados agregados en `results/current_champions/v1/` | **Champion actual de precisión**; con ajuste final138 y59 predicciones |
| Compact14 / `NO_PLANET_OFF_GLOBAL_MASK` | CT3 + local5 sin Planet ni corrección interna + peso global + R3 | [`src/current_champions.py`](../src/current_champions.py), [reproducción](current_champions_reproduction.md) | Misma raíz reproducible y resultados agregados | **Champion actual compacto**; con ajuste final138 y59 predicciones |
| B1 | CT3+a(Reference26−CT3), a aprendido con OOF internas | [`src/four_expert_combinations.py`](../src/four_expert_combinations.py), [conclusión](four_expert_combinations_conclusions.md) | `outputs/modeling/four_expert_combinations/v1/` | Sensibilidad; no recomendada para sustituir26 |
| B2–B6 | Otras mezclas constantes/condicionales entreCT3,14,26,L40 | [Diseño](four_expert_combinations_design.md), [resultados](four_expert_combinations_results.md) | `outputs/modeling/four_expert_combinations/v1/` | Batería exploratoria terminada; ninguna promoción automática |

## Qué significa la selección actual

La anterior recomendación de 26/14 ya fue adoptada como selección de champions por el responsable del proyecto. El módulo ejecutable actual es `src/current_champions.py`. Los diseños y conclusiones originales describen el momento de su evaluación y permanecen como procedencia.

Entre los cuatro candidatos explicados,26 ofrece el mejor equilibrio de RMSE y transferencia;14 reduce fuentes con pérdida pequeña. No se afirma que26 sea el mínimo RMSE de todo el historial: existen sensibilidades con ventajas puntuales y otros compromisos. B1 mejora municipal, pero pierde espacial. L40 conserva fortalezas regionales y sirve como benchmark.

Las etiquetas coloquiales «experto9», «experto10», «J7» y «J7 BOTH» pertenecen a etapas anteriores. No deben reasignarse a 26/14 por parecido de nombre: consultar sus [diagnósticos originales](j7_both_residual_audit.md), el [reparto de señales](signal_role_allocation_results.md) y las recetas congeladas. Un número puede contar entradas finales, calibración o componentes distintos.

## Reglas para actualizar el registro

Toda nueva entrada debe indicar receta exacta, fuentes, protocolo, evidencia, estado y ruta. Promover un líder o generar una nueva entrega59 requiere una decisión explícita distinta de redactar una recomendación. Las métricas deben incluir RMSE/R², casos y agregación; una carpeta `frozen_design.json` por sí sola no acredita ejecución. No sobrescribir nombres históricos para hacer parecer que su entrega corresponde a una arquitectura nueva.

**Etapa posterior de predicción final:** [26/14 incorporados a la comparación59](../results/current_champions_final/v1/README.md). Los modelos y resultados históricos se conservan.
