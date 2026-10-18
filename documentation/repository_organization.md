# Organización documental y de versionado

Reorganización documental al2026-10-18. No mueve experimentos ni modifica modelos, hiperparámetros, rendimientos,OOF o predicciones59. Conserva el historial y añade puntos de entrada para revisión.

## Cambios

- README principal centrado en el propósito del reto y las condiciones del conjunto197/138/59.
- Mapa de documentación e índice de investigación, con distinción entre diseño, ejecución, interpretación y entrega.
- Registro humano/JSON de modelos: Champion histórico, controles, candidatos26/14, sensibilidades y entregas históricas59.
- Copias de diseñosJSON disponibles y particiones posicionales en `configs/`, separadas de datos y resultados ignorados.
- Inventario de versiones del entorno y dependencias observadas, con límite explícito de instalación no verificada desde cero.
- Relación de uso de IA y prompts recuperados, separando evidencia literal, contexto faltante y resultados verificables.
- Limpieza del seguimiento de cachés compiladas, conservando los archivos locales y la regla de ignore.

## Qué queda deliberadamente igual

Las rutas `data/` y `outputs/` siguen excluidas deGit. Los ejecutores históricos siguen consumiendo sus archivos locales: no se reemplaza su configuración interna por los nuevosJSON portables sin una adaptación y prueba específicas. Se conserva la numeración de scripts y la carpeta heredada `data_uderstanding`; cambiarla puede afectar referencias y no es necesario para aclarar el proyecto.

Los documentos antiguos no se reescriben para afirmar que26 era el Champion cuando se entregaron C-T3/Champion/EQUAL3. Una recomendación reciente y una entrega previa pueden coexistir si sus estados están identificados.

## Comprobaciones y operación

`python scripts/520_validate_repository_documentation.py` revisa enlaces documentales principales, registro, hashes de copias/prompts y particiones. No carga datasets ni entrena. El export519 genera inventarios desde las fuentes locales y debe revisarse antes de aceptar cambios sobre configuraciones congeladas.

ParaGit se preparan sólo documentación, código auxiliar y metadatos permitidos. Retirar52 archivos compilados del seguimiento no borra sus copias locales. No se hace commit ni push como parte de esta organización. El conjunto exacto de cambios debe revisarse con `git diff --cached --stat` antes de publicar.
