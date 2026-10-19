# Registro de apoyo con inteligencia artificial

Para la entrega del Reto AgroCebada FIRA 2026, la guía solicita registrar los prompts utilizados, su propósito y la herramienta de IA generativa empleada. Completa y revisa este documento conforme avance el desarrollo. No debe reemplazar las referencias bibliográficas ni las fuentes de datos.

| Fecha | Herramienta | Prompt / instrucción relevante | Propósito y resultado | Revisión humana |
| --- | --- | --- | --- | --- |
| 2026-10-13 | ChatGPT | “Quiero desarrollar mi propuesta de frontend GeoCebada con el enfoque C: combinación de página web y dashboard. Ayúdame a empezar con los archivos separados, conservando sin cambios los de mi compañero y reutilizando las predicciones reales de Local04D.” | Definir el alcance de la propuesta visual separada. | Pendiente de completar. |
| 2026-10-13 | ChatGPT | “ME PARECE PERO PRIMERO AYUDAME A CREAR MI REPOSITORIO EN GITHUB CON LO NECESARIO” | Preparar estructura independiente, archivos estáticos, copias canónicas de CSV y herramienta de verificación. | Pendiente de completar. |

Añade aquí nuevas consultas relevantes y especifica qué decisiones de diseño y contenido fueron tomadas o corregidas por el equipo. Antes de publicar el proyecto, decide con el equipo qué información se adjuntará en la bibliografía/documentación oficial.

## Versión 2: interfaz y validación territorial

- Herramienta: ChatGPT (OpenAI).
- Solicitud: crear una versión visual AgroTech/Geoespacial con landing page y dashboard, y permitir ingresar nuevas parcelas exclusivamente de Hidalgo, Puebla y Tlaxcala.
- Uso: elaboración de HTML/CSS/JavaScript, validación geográfica con polígonos externos de referencia, pruebas unitarias de geometría y formularios sin inferencia inventada.
- Limitaciones: el módulo de nuevas parcelas produce solo un archivo JSON validado; no se ha integrado un backend real ni desplegado una API generalizable de Local04D.

## Nueva página de divulgación científica (17 de octubre de 2026)

- **Herramienta:** ChatGPT (OpenAI, GPT-6).
- **Solicitud:** «trae toda la informacion que tiene https://heri-espino.github.io/GeoC/#reto a mi pagina pero agregalo en otra hoja y manten los colores e info y mapa de mi pagina».
- **Propósito:** crear en el frontend independiente una nueva página «El reto» con explicación detallada y original del contenido científico publicado por el equipo; incorporar resultados numéricos y metodología verificables, añadir navegación a las otras cinco páginas y conservar intacto el visor satelital de la usuaria.
- **Fuentes consultadas:** `heri-espino/GeoC/website/index.html`, `website/README.md`, `website/data/checkpoint07_summary.csv`, `website/data/checkpoint08_summary.csv`, `website/data/checkpoint08_bootstrap.csv`.
- **Cambios técnicos:** HTML/CSS estático y navegación, sin acceso a rendimientos ocultos, sin modificar predicciones canónicas ni la geometría de las parcelas.
- **Revisión humana:** pendiente. El equipo debe verificar que la exposición y la atribución cumplan con las reglas del concurso antes de publicarla.

## Reorganización editorial en tres páginas (17 de octubre de 2026)

- **Herramienta:** ChatGPT (OpenAI, GPT-6).
- **Instrucción de la usuaria:** «la pestaña que dice el reto esta horrible, separa como el los tenia, en resultados , el reto, como se desarrollo la salucion».
- **Objetivo:** sustituir la página científica monolítica por tres capítulos navegables (reto, desarrollo de la solución y resultados) siguiendo la organización temática de la web del equipo, conservando el estilo de la plataforma independiente.
- **Cambios:** `reto.html` reducido al problema y fuentes; `solucion.html` con metodología y validación; `resultados.html` con métricas y anexos. Actualizados menús, tarjetas iniciales y pruebas de navegación. No se modificaron los modelos, datos canónicos ni geometrías.
- **Revisión del equipo:** pendiente de verificación visual y editorial antes de publicar.

## Unificación de la navegación editorial (17 de octubre de 2026)

- **Herramienta:** ChatGPT (OpenAI, GPT-6).
- **Solicitud:** igualar el formato de los enlaces «El reto», «Cómo se desarrolló» y «Resultados» con el menú del Dashboard.
- **Intervención:** navegación principal con desplegable accesible «Investigación», selección de capítulo activo, tratamiento móvil y unificación estética de la navegación secundaria en los tres capítulos. No se modificaron los resultados, los scripts del mapa ni los archivos de datos.
- **Revisión del equipo:** pendiente de comprobación visual en navegador.
