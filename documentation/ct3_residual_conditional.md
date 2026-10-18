> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Corrección residual condicional sobre C-T3

[Hallazgos y decisión](../outputs/research/ct3_residual_conditional_synthesis/v1/technical_findings.md), [síntesis ejecutiva](../outputs/research/ct3_residual_conditional_synthesis/v1/executive_summary.md).

[Diseño aplicado](ct3_residual_conditional_design.md), [métricas](../outputs/modeling/ct3_residual_conditional/v1/tables/metrics_summary.csv), [OOF completas](../outputs/modeling/ct3_residual_conditional/v1/tables/oof_predictions.csv), [reglas](../outputs/modeling/ct3_residual_conditional/v1/tables/tree_rules.csv).

La ganancia municipal del árbol completo coincide con la del control sin LAI; su validación espacial empeora y no mejora diferencias intraperfil agrupadas. Se detiene la batería sin promover modelos. Diez pruebas pasaron. F8 y modelo TOP20/TOP15 intactos, sin ajuste final138 ni59PRED. Scripts376/377.
