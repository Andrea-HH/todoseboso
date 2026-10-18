# Metadatos versionados de investigación

`.gitattributes` fija LF para estos metadatos y preserva los bytes de los prompts originales. Así, los hashes no cambian únicamente por conversiones de fin de línea entre Windows y Linux.

Se separan especificaciones de los artefactos generados para que excluir `outputs/` no elimine también la trazabilidad del diseño. **Esta carpeta no reemplaza los artefactos históricos ni cambia las rutas de los pipelines.**

| Ruta | Contenido |
|---|---|
| `model_registry.json` | Nombres, alias, estados y rutas de los modelos principales |
| `experiments/*/v*/frozen_design.json` | Copias de los diseños JSON locales disponibles, con rutas de raíz convertidas a tokens |
| `experiments/manifest.json` | Ruta origen, hash original y hash de cada copia versionable |
| `validation/original65.json` |65 particiones externas e internas inmediatas, en posiciones enteras |
| `validation/original65_plus_fresh16.json` |Las65 anteriores y16 adicionales97/41, reportadas por separado |

Los tokens `${REPO_ROOT}` y `${GEOC_ROOT}` representan la raíz local del proyecto y la ubicación opcional del repositorioGeoC. Son documentación portable: los ejecutores históricos no los resuelven automáticamente. Los hashes de fuentes en los diseños describen el momento de congelación y no necesariamente el estado actual de un script modificado posteriormente.

Las posiciones son base0 y requieren **exactamente el orden original** de `train138.parquet`. Cada JSON incluye SHA256 del artefacto fuente, del dataset fuente y de la lista ordenada de IDs. Las posiciones internas son relativas a la lista de entrenamiento externo. No se publican IDs, rendimientos, coordenadas, predictores ni predicciones. No aplicar esas posiciones a una tabla reordenada. Los contextos recursivos más profundos de corrección se preservan en código y artefactos de contexto; no se declara que este export incluya todos ellos.

Las copias se generan con `python scripts/519_export_research_metadata.py` cuando están disponibles los artefactos locales. No se restauran `joblib` a partir de estosJSON automáticamente: un nuevo ejecutor necesitaría una adaptación explícita y pruebas de equivalencia. Los metadatos permiten revisar diseños y particiones en Git; no hacen autosuficiente un clon sin datos.

El export incluye los diseños encontrados bajo `outputs/modeling/*/v*/frozen_design.json`; no recupera todos los formatos de configuración antiguos ni acredita ejecución. Por ejemplo, `winner_predictions/v1_initial_unexecuted` es una configuración no ejecutada y no una segunda entrega. La evidencia y el estado deben leerse junto con los resultados y el registro.

Antes de versionar nuevosJSON, revisar que contengan sólo especificaciones y procedencia, nunca vectores objetivo, tablas privadas, credenciales o predicciones finales. No subir modelos ni saltar `.gitignore` con `git add -f`.
