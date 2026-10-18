# AgroCebada FIRA 2026 · fira_nuria

**El propósito del proyecto es desarrollar y validar un modelo que estime el rendimiento de cebada, en toneladas por hectárea, para las parcelas sin rendimiento conocido del Reto AgroCebada FIRA 2026.** La investigación de variables y algoritmos sirve para elegir y explicar esa solución; no es un objetivo independiente ni una búsqueda del menor error sin considerar su uso.

Trabajamos con **197 parcelas de Hidalgo, Puebla y Tlaxcala**, ciclo 2025: **138 con rendimiento conocido** para desarrollo y validación, y **59 por estimar**. Integramos señales climáticas, satelitales, históricas, topográficas y cartográficas. El rendimiento de las 59 no está disponible: el error reportado corresponde a validación de las 138, no al resultado real de la entrega.

La finalidad práctica es apoyar la estimación de productividad y aportar información para decisiones agropecuarias y financieras. Este estudio no valida un sistema automático de otorgamiento de crédito, una relación causal agronómica ni la transferencia a cualquier región o año.

## Propósito y entregables según los lineamientos

Los [lineamientos del reto](docs/guidelines/Lineamientos%20y%20Gui%CC%81a%20de%20Registro%20de%20Proyectos_.pdf), páginas 3–4, piden explicar fuentes, preparación, variables, metodología, resultados, limitaciones y utilidad para el sector. También solicitan una demostración práctica, bibliografía, transparencia sobre IA generativa y una tabla final de identificador y rendimiento predicho por parcela. El README orienta la lectura; no reemplaza esos entregables ni acredita que el proyecto esté publicado.

Objetivos de trabajo:

1. Construir características comparables por parcela y auditar su soporte espacial y temporal.
2. Evaluar modelos con exclusión de etiquetas y selección interna de hiperparámetros.
3. Comparar precisión, errores grandes, complejidad y estabilidad territorial.
4. Seleccionar explícitamente la receta final, producir sus 59 estimaciones y explicar sus límites.

La [matriz de entregables y evidencia](documentation/project_scope_and_guidelines.md) distingue lo disponible de lo pendiente.

## Qué modelo es cuál y cuál es su estado

**Champion es un nombre histórico de una receta, no una promoción automática del experimento más reciente.** Un candidato con mejores OOF no equivale a un modelo final autorizado ni a una predicción ya entregada. El estado detallado y las rutas están en el [registro de modelos](documentation/model_registry.md) y su [versión estructurada](configs/model_registry.json).

| Modelo | Qué hace | Estado y motivo de conservarlo |
|---|---|---|
| **C-T3 / CT3** | Elastic Net global con lluvia total, fracción temprana, concentración mensual y NDVI de mayo | Control compacto de 4 entradas; tiene ajuste final y59 predicciones en la entrega histórica |
| **Champion histórico** `A_CURRENT_CH_H_T` | Base climática Elastic Net, corrección histórica XGBoost y corrección topográfica Ridge | Referencia histórica; tiene entrega59. No es el modelo26 |
| **EQUAL3** | Promedio fijo C-T3 + GPR F5-01 + CatBoost F7-00 | Ensamble histórico con entrega59; no es B1 ni mezcla con L40 |
| **L40 / Local04D** | PCA20 de C4 de 2082 variables y Ridge local con 24 vecinos geográficos | Benchmark importado de GeoC y reproducido aquí; útil para estudiar interpolación y transferencia |
| **Reference26** | C-T3 + experto local7, compuerta geológica y corrector R3 | Referencia recomendada de precisión en la comparación reciente de estos cuatro; no promoción formal ni ajuste final138 en esa batería |
| **Compact14** | C-T3 + experto local5, peso global y R3; sin Planet ni compuerta geológica | Alternativa de menor dependencia de fuentes, con desempeño próximo a 26 |
| **B1** | Mezcla aprendida internamente entre C-T3 y26 | Sensibilidad: pequeña ventaja municipal, deterioro espacial; no recomendada para sustituir26 |
| **F5/F6/F7 y otras variantes** | GPR, bagging, boosting, correcciones y ablaciones | Investigación y controles; ver el índice. La propuesta F8 no prueba una ejecución F8 |

Las14/26 son **entradas derivadas**, no números de coeficientes globales; los20 componentes de L40 no son20 variables originales. Todas esas arquitecturas requieren sus insumos para construir la representación.

## Comparación reciente compatible

RMSE en t/ha / R². Mismos65 folds externos y138 rendimientos; métricas sobre OOF completas por repetición y después promedio. Esta tabla compara candidatos, no el error desconocido de las 59.

| Modelo | Aleatoria | Perfil climático | Municipal | Espacial |
|---|---|---|---|---|
| C-T3 | .5116 / .6361 | .5206 / .6232 | .5813 / .5302 | .6788 / .3594 |
| L40 | .4930 / .6619 | .5031 / .6481 | .7602 / .1964 | .9794 / −.3337 |
| Reference26 | .4748 / .6865 | .4774 / .6831 | .5752 / .5400 | .6333 / .4423 |
| Compact14 | .4773 / .6832 | .4793 / .6805 | .5755 / .5395 | .6431 / .4250 |
| B1 | .4755 / .6856 | .4839 / .6744 | .5681 / .5513 | .6813 / .3546 |

La diferencia 26–14 es pequeña; no demuestra equivalencia estadística ni justifica por sí sola toda la complejidad adicional. L40 mantiene ventajas locales, pero transfiere peor en estos protocolos territoriales. La recomendación reciente es26 como referencia de precisión y14 como alternativa operativa; no se presenta como el ganador absoluto de todos los experimentos históricos. Véanse la [explicación de arquitecturas y residuos](documentation/four_architecture_explanation.md) y la [conclusión de las mezclas](documentation/four_expert_combinations_conclusions.md).

La evaluación es exploratoria después de amplia reutilización de las mismas etiquetas. El banco adicional97/41 se conserva separado: cambia las particiones, no aporta rendimientos independientes. L40 mantiene una PCA transductiva sobre 197 X, sin etiquetas ocultas; no equivale a ajustar esa representación sólo con cada entrenamiento externo.

## Cómo leer y reproducir

Empieza por el [mapa de documentación](documentation/README.md), el [índice de experimentos](documentation/experiment_index.md) y las [convenciones de evaluación](documentation/model_comparison_convention.md).

Clonar el repositorio **no descarga los datos, los modelos ni las predicciones**. Antes de ejecutar hacen falta los insumos locales y los artefactos previos que indique cada receta. Consulta [entorno y dependencias](environments/README.md) y [reproducibilidad y versionado](documentation/reproducibility.md).

```powershell
# Desde la raíz, con Python y los insumos locales disponibles:
python scripts/520_validate_repository_documentation.py

# Sólo con los resultados OOF anteriores disponibles; no entrena:
python scripts/518_explain_four_architectures.py
```

La [reproducción de las últimas combinaciones](documentation/four_expert_combinations_reproduction.md) distingue preparación, ejecutor vigente, verificaciones y entrega. No ejecutes todos los scripts en orden numérico: hay análisis, propuestas, ejecutores alternativos y etapas que dependen de resultados históricos.

## Estructura y política de publicación

| Ruta | Contenido | Git |
|---|---|---|
| `src/` | Implementación de variables, modelos y validación | Sí |
| `scripts/` | Preparación, ejecución, auditoría y entrega por etapa | Sí |
| `tests/` | Pruebas de implementaciones e integridad | Sí |
| `configs/` | Registro, especificaciones exportadas, particiones posicionales y procedencia | Sí; sin rendimientos ni matrices |
| `environments/` | Versiones observadas y límites de instalación | Sí |
| `documentation/` | Documentación propia, índices, resultados interpretados e inventario de IA | Sí |
| `docs/guidelines/` | Lineamientos y diccionarios proporcionados | Sí |
| `docs/resources/` | Referencias externas descargadas | No |
| `data/` | Datos originales, externos y procesados | No |
| `outputs/` | Modelos, OOF, predicciones, figuras y checkpoints | No |

Los enlaces a `outputs/` funcionan con la copia local de artefactos; no estarán disponibles en un clon que sólo tenga Git. La [política de datos](documentation/git_data_policy.md) explica esta separación. Se conserva la numeración histórica y no se mueven los experimentos para evitar romper sus rutas.

## Uso de inteligencia artificial generativa

Se utilizó asistencia de IA en diseño y revisión de experimentos, programación, interpretación de resultados y documentación. El [inventario de IA generativa](documentation/ai_usage.md) contiene prompts recuperables, finalidad, herramienta, fuentes y límites de trazabilidad. Distingue solicitudes de ejecuciones y no atribuye a una IA mediciones, datos o validaciones que deban sustentarse con artefactos. Este inventario complementa la bibliografía; no la sustituye.
