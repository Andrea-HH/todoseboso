# L40 — ficha del modelo

Estado vigente: 2026-10-18. Champions actuales: **Reference26 y Compact14**. [Índice de modelos](../README.md).

## Función y arquitectura

**Benchmark fuerte del equipo, procedente de GeoC; no champion actual de fira_nuria.** Alias Local04D / LOCAL04D. Representación C4 de **2,082 variables originales**, imputación, estandarización y PCA20; Ridge local ponderado con 24 vecinos geográficos, alpha30 y potencia1. Cada consulta ajusta una regresión en su vecindario.

Los veinte componentes son combinaciones de las entradas originales, **no veinte variables originales seleccionadas**. Los centroides determinan vecinos. C4 integra características base, agronómicas y empíricas derivadas de series por parcela; la PCA conserva ejes de variabilidad conjunta, no una lista de veinte señales agronómicas significativas.

## Variables y trazabilidad

La receta conserva la representación C4 original de GeoC. El [inventario completo de 2,082 entradas](variables_C4_2082.csv) contiene nombre, capa, fuente, modo y descripción original: **1,397 base, 350 agronómicas y 335 empíricas**. Se reconstruyó aplicando la función original de selección y el filtro de columnas no vacías/no constantes a las tablas locales originales, sin ajustar PCA ni leer rendimientos. La [procedencia y hashes](inventory_provenance.json) y el [script de reconstrucción](../../../scripts/525_inventory_l40_inputs.py) permiten revisar el procedimiento.

Este catálogo no se sustituye por el de 1,831 señales no climáticas: corresponde a otra variante. Las descripciones genéricas del manifiesto se conservan como tales; no se inventan fórmulas ausentes. Reconstruir los nombres a partir de las fuentes locales actuales no reaudita cada transformación original ni certifica de nuevo las cargas históricas de PCA.

El [puente y su auditoría](../../geoc_bridge_results.md), el [inventario de señales GeoC](../../geoc_variable_signal_audit.md) y la [comparación compatible](../../four_leaders_comparison.md) distinguen esas representaciones. No se atribuye importancia puntual o causal a variables originales a partir de veinte componentes sin analizar cargas y ablaciones.

## Origen y protocolo

Es el modelo fuerte de la investigación del compañero, previo al puente entre repositorios. Su representación PCA se ajustó con X de las 197 parcelas, sin rendimientos ocultos: es un planteamiento transductivo. La evaluación compatible de fira_nuria conserva esa representación y reconstruye la receta local con exclusión de etiquetas externas. No equivale a una PCA inductiva reentrenada únicamente en cada fold.

## Ventajas y límites

Fuerte bajo particiones aleatorias y con vecinos territoriales representados; conserva ventajas locales en Almoloya y Cuautepec. Motivó estudiar separación de clima y señales complementarias y el experto local que antecedió a 26/14.

Pierde claramente en validación municipal y espacial de los 65 folds, con R² espacial negativo. Dependencia de vecindarios, C4 y representación transductiva; no es una receta compacta de veinte mediciones. Los resultados .4819 y .4957 de otros bancos no se mezclan con esta tabla. Se conserva la copia existente de sus 59 estimaciones; no se reentrena aquí ni se conoce su error real en esas parcelas.

## Resultados compatibles y lectura

RMSE t/ha / R² / MAE t/ha. OOF completas por repetición y después promedio; mismos 65 folds, 138 parcelas.

| Aleatoria | Perfil climático | Municipal | Espacial |
|---|---|---|---|
| .4930 / .6619 / .3526 | .5031 / .6481 / .3479 | .7602 / .1964 / .5991 | .9794 / −.3337 / .7434 |

### Banco adicional97/41 — resultado separado

| RMSE t/ha | R² | MAE t/ha | Sesgo predicho−observado |
|---|---|---|---|
| 0.4893 | 0.6621 | 0.3552 | -0.0023 |

Media de las métricas de **16 particiones**, cada una con97 parcelas para entrenar y41 para evaluar. Reutiliza las mismas138 parcelas; no es muestra independiente ni error de las59 PRED. Se conserva separado de los cuatro protocolos anteriores. [Comparación completa y procedencia](../../../results/comparison_97_41/v1/README.md).

Son resultados de validación exploratoria tras reutilización de etiquetas, no el error de las 59 desconocidas ni superioridad universal. Residuo = predicho − observado: positivo significa sobreestimación. El banco adicional 97/41 se interpreta por separado. No se presenta R² ajustado clásico para estas arquitecturas locales y calibradas.

## Archivos y reproducción

Implementación del puente: [src/geoc_bridge.py](../../../src/geoc_bridge.py). Artefactos privados: `outputs/modeling/geoc_bridge/v1/`; copia de estimaciones finales en `outputs/research/geoc_bridge_audit/v1/predictions59_aligned_descriptive.csv`, columna `Local04D_t_ha`, cuando los artefactos locales están presentes. Esa copia no es un ajuste nuevo ni una entrega validada con sus rendimientos.

## Comparación final59 disponible

Los champions26/14 ya tienen ajustes finales con138 y sus59 estimaciones se incorporaron a la comparación existente sin sobrescribir las anteriores. [Reporte de diferencias entre predicciones](../../../results/current_champions_final/v1/README.md). Archivo privado: `outputs/modeling/current_champions_final/v1/comparacion_predicciones59.xlsx`. Estas diferencias no son errores contra rendimientos observados.
