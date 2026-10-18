# Propósito del proyecto y correspondencia con los lineamientos

## Objetivo general

Desarrollar y validar una solución para estimar rendimiento de cebada en t/ha por parcela del ciclo 2025 del Reto AgroCebada FIRA 2026, utilizando138 parcelas con rendimiento conocido para construir y evaluar la receta que produzca las 59 estimaciones faltantes. Se busca precisión útil, explicación del modelo y límites claros de aplicación.

No se pretende que un ranking de experimentos sustituya la selección de una receta final. La discusión sobre productividad y financiamiento es una aplicación potencial; no hay validación de decisiones crediticias ni causalidad agronómica. Tener historia de covariables no equivale a tener varias campañas de rendimientos etiquetados.

## Fuente normativa local

Documento: [Lineamientos y Guía de Registro de Proyectos](../docs/guidelines/Lineamientos%20y%20Gui%CC%81a%20de%20Registro%20de%20Proyectos_.pdf), páginas 3–4. Esta matriz resume su contenido; no añade requisitos del comité. Los conteos197/138/59 y el ciclo 2025 proceden del proyecto y sus auditorías, no se atribuyen a esas páginas del PDF.

| Apartado solicitado | Límite indicado | Evidencia útil en el repo / estado |
|---|---|---|
| Introducción | 550 palabras | Problema, fuentes y contexto en README; redactar la versión final de plataforma |
| Justificación | 200 palabras | Utilidad de estimar productividad; evitar prometer eficacia financiera demostrada |
| Objetivos | 200 palabras | Objetivo anterior y README; adaptar a la receta finalmente elegida |
| Metodología | 700 palabras | [Registro de modelos](model_registry.md), [índice](experiment_index.md) y [evaluación](model_comparison_convention.md) |
| Resultados y discusión | 800 palabras | [Comparación reciente](four_architecture_explanation.md), fortalezas territoriales, complejidad, incertidumbre y selección exploratoria |
| Ciencia de datos e inclusión financiera | 300 palabras | Conectar productividad con evaluación/seguimiento de riesgo como uso potencial, sin validar aprobación automática |
| Conclusiones | 400 palabras | Derivadas de resultados ya presentados; seleccionar y nombrar la receta final |
| Enlace de implementación | Aplicación/interfaz/dashboard o video de máximo 5min | Este trabajo documental no acredita un enlace público funcional ni permisos del jurado; verificar antes del envío |
| Bibliografía | PDF | Citar fuentes técnicas y externas; las fuentes locales están en `docs/resources/`, excluidas de Git. Falta consolidar el PDF de entrega |
| Relación de prompts, finalidad y herramienta | Dentro de la transparencia solicitada en bibliografía | [Inventario de IA](ai_usage.md); registro recuperado parcial, con prompts literales disponibles y límites declarados |
| Anexos | PDF máximo 4cuartillas | Consolidar gráficos/tablas y parámetros de la receta final |
| Tabla obligatoria de predicciones | ID de parcela y rendimiento en ton/ha | Hay una [entrega histórica59](winner_predictions_statistical_validation.md). No sustituirla automáticamente por26/14: esos candidatos no tienen ajuste final138 ni nueva entrega59 en la última batería |

## Estado que debe comunicarse

El repositorio contiene investigación extensa y una entrega histórica de C-T3/Champion/EQUAL3. La decisión explícita actual del responsable selecciona Reference26 y Compact14 como champions: precisión y simplificación, respectivamente. Su [ruta reproducible](current_champions_reproduction.md) incluye C-T3 y B1, sin reentrenar L40; L40 sí permanece en las tablas comparativas como referencia externa fuerte. Esta selección no produce automáticamente un ajuste final138, nuevas59 predicciones ni publicación del reto. La receta de entrega, su archivo59 y el enlace demostrativo deben identificarse explícitamente al cerrar el proyecto.

No presentar un resultado OOF como error de 59 ni un banco nuevo de particiones sobre las mismas etiquetas como confirmación independiente. Las limitaciones de los modelos locales, la PCA transductiva de L40 y el soporte por municipio deben acompañar la interpretación.
