# Inventario de uso de inteligencia artificial generativa

## Propósito y alcance

Los [lineamientos del reto](../docs/guidelines/Lineamientos%20y%20Gui%CC%81a%20de%20Registro%20de%20Proyectos_.pdf), página 4, piden una relación de los prompts utilizados, su propósito y la herramienta empleada. Este registro documenta la asistencia de IA recuperable en el desarrollo de este repositorio y permite preparar esa relación para la bibliografía de entrega. No sustituye las fuentes técnicas, las referencias de datos ni la revisión del equipo.

**Herramienta identificable en esta conversación: Codex, asistente de IA generativa.** No se reconstruye una versión histórica de modelo, fecha, temperatura, configuración o número de tokens sin evidencia. Los textos adjuntos fueron proporcionados por el usuario; el registro no atribuye su autoría original a una persona o modelo distinto. No hay evidencia suficiente aquí para declarar uso o ausencia de IA en el otro repositorioGeoC o por todos los integrantes del equipo.

Registro recuperado al2026-10-18: **41 prompts**,21 adjuntos originales y20 mensajes literales de la conversación, indexados en [ai/README.md](ai/README.md) y [prompt_inventory.csv](ai/prompt_inventory.csv). Incluye la selección explícita de26/14 y la solicitud de reproducción sinL40. Los adjuntos se conservan byte por byte conSHA256; los mensajes son transcripciones del texto disponible. Ningún resumen redactado ahora se presenta como un prompt original.

## En qué se utilizó la asistencia

La IA generativa asistió al desarrollo. Las recetas predictivas descritas (Elastic Net, Ridge, GPR, CatBoost, PCA y mezclas) no utilizan un modelo de lenguaje para producir el rendimiento de una parcela. No confundir aprendizaje automático predictivo con IA generativa ni atribuir al asistente una fuente de datos agrícolas.

| Actividad | Uso de IA observable | Evidencia o resultado que debe acompañarlo |
|---|---|---|
| Diseño metodológico | Formular controles, ablaciones, validación territorial y límites de búsqueda | PromptsP001–P021 y documentos de diseño/decisión; una petición no acredita entrenamiento |
| Ingeniería de variables | Proponer y programar resúmenes de clima, ventanas temporales, historia y contrastes | Código de extracción, diccionarios y auditorías de soporte; no tratar un índice derivado como medición nueva |
| Implementación y depuración | Escribir/revisar scripts, modelos, kernels, correctores, pruebas y reutilización de contextos | Código versionado, pruebas y auditorías numéricas de cada batería; no existe trazabilidad por línea para todo el historial |
| Ejecución asistida | Lanzar scripts locales y examinar sus resultados dentro de alcances pedidos | OOF, checkpoints, registros de convergencia y auditorías; el texto generado por el asistente no sustituye esos artefactos |
| Comparación e interpretación | Explicar métricas, residuos, geografía, complejidad y límites | Tablas calculadas sobre OOF compatibles y documentos de resultados; interpretaciones no causales |
| Documentación y entrega | Redactar síntesis, tablas, instrucciones e índices; organizar el inventario | Archivos de documentación, registro y metadatos; revisar correspondencia con el modelo realmente entregado |

El asistente puede producir código que calcula una métrica; **el valor válido debe proceder de su ejecución verificable**, no de una cifra inventada en la respuesta. En la última comparación se verificó alineación de casos, convenciones de signo y reproducción de las métricas. Esas verificaciones son específicas y no certifican retrospectivamente cada etapa antigua.

## Cómo leer las evidencias

- Cada fila indica propósito, herramienta receptora, fuente, texto literal, huella y documento relacionado.
- Una solicitud puede incluir experimentos pospuestos. Por ejemplo, el promptF8 se relaciona con una auditoría/propuesta cuyo documento declara que no se ejecutóF8.
- Los mensajes breves «ejecuta», «continúa» y similares dependen de contexto. Sus extractos no constituyen por sí solos una especificación reproducible; consultar el diseño y los resultados citados.
- Documentos relacionados permiten localizar la investigación, pero no demuestran que todo su contenido fuera generado por un prompt aislado. No se dispone de un mapa completo prompt→línea de código.
- Las correcciones, pruebas y decisiones deben conservar su procedencia. Una explicación favorable no autoriza automáticamente un cambio del Champion o predicciones59.

## Límites del registro recuperado

Este inventario **no es una exportación completa del historial de conversaciones**. No contiene todos los seguimientos, respuestas, llamadas de herramientas, prompts de sistema/desarrollador ni modificaciones manuales. No se rellenan esos huecos con prompts reconstruidos. Las fechas históricas y modelos no verificados figuran como no recuperados.

Se conservaron los originales accesibles y mensajes seleccionados del contexto disponible. El texto de los prompts refleja intenciones y restricciones del momento; no debe convertirse retrospectivamente en evidencia de un experimento ejecutado o una regla general. La lista debe revisarse por el equipo antes de presentarla como declaración final de uso de IA, especialmente si hubo otras herramientas o conversaciones.

Este trabajo de organización no prueba disponibilidad de un PDF de bibliografía ya consolidado ni cumplimiento formal completo de la plataforma. La relaciónCSV y los textos permiten preparar un anexo verificable; la bibliografía de datos y métodos sigue siendo necesaria.

## Mantenimiento

Para nuevos usos, añadir una entrada con texto original o extracto explícitamente marcado, herramienta, versión sólo si consta, fecha conocida, finalidad, archivos afectados, verificaciones y resultado. No registrar credenciales, rendimientos privados o conversaciones ajenas sin autorización. El export519 depende de los adjuntos locales originales para regenerar este inventario; las copias versionadas ya pueden leerse y verificarse sin acceso a esos adjuntos.


## 2026-10-18 · Sitio editorial independiente en GitHub Pages

Una solicitud posterior del usuario pidió crear en este fork una web que narre
el recorrido C-T3 → Reference26/Compact14, reutilizando sólo el lenguaje visual
del antiguo sitio GeoCebada. **Herramienta:** ChatGPT (asistencia generativa en
HTML, CSS, JavaScript, pruebas de sincronía y workflow Pages).
**Entrada verificable:** solicitud en conversación de crear la página de forma
independiente y el relato del modelo transmitido por el equipo; contraste con
la ficha Reference26, Compact14, CT3 y tablas agregadas de este repositorio.
**Salidas:** website/index.html, website/styles.css, website/app.js,
website/data/, website/README.md, scripts/529_check_story_site.py y
.github/workflows/publish_story_pages.yml.

No se generaron rendimientos nuevos ni se entrenó el modelo para el sitio.
Los datos de lluvia y vecinos del simulador son sintéticos; las métricas
proceden de CSV públicos versionados, no de una ejecución nueva. Esta nueva
solicitud **no forma parte del inventario recuperado de 41 prompts históricos**;
se documenta separadamente y requiere revisión humana antes de su uso en la
entrega final.
