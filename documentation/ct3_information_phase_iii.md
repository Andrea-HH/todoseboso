# Fase III: representaciones condicionadas a C-T3

[Informe e interpretación revisada](../outputs/research/ct3_incremental_information/phase_iii/v2/representation_report.md).

[Catálogo](../outputs/research/ct3_incremental_information/phase_iii/v2/representation_catalog.csv), [comparación](../outputs/research/ct3_incremental_information/phase_iii/v2/block_comparison.csv), [estabilidad](../outputs/research/ct3_incremental_information/phase_iii/v2/stability_analysis.csv).

[Fase IV: diseño sin ejecutar](../outputs/research/ct3_incremental_information/phase_iii/v2/phase_iv_design.md).

La versión v1 conserva cálculos y controles; v2 aclara contraste climático inducido y sensibilidad temporal, sin nuevos ajustes. Scripts374/375. Cero rendimiento usado en representación, cero nuevos modelos de rendimiento, cero59PRED.

Las composiciones cartográficas completas se transformaron mediante raíces de proporciones, con ceros conservados. El escalado posterior por columna cambia la ponderación de esa geometría; las PCA resultantes no preservan una distancia Hellinger pura. Esta transformación no convierte las unidades cartográficas en propiedades físicas medidas. Véase la [referencia metodológica de Legendre y Gallagher](https://pubmed.ncbi.nlm.nih.gov/28547606/).

La reducción y sus porcentajes describen varianza y reconstrucción de X, no rendimiento explicado. Las transformaciones de una futura validación deben reajustarse dentro del entrenamiento, conforme a la [documentación de prevención de fuga](https://scikit-learn.org/1.7/common_pitfalls.html).
