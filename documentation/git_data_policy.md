# Archivos que se publican en Git

El repositorio conserva scripts, implementación, pruebas y documentación propia.
Los datos originales/externos/procesados (`data/`), los resultados generados
(`outputs/`), los documentos descargados de referencia (`docs/resources/`), los
modelos serializados, registros y cachés se mantienen fuera de Git mediante
`.gitignore`. Ignorarlos no borra los archivos locales.

Los scripts conservan sus rutas de entrada y salida. Para ejecutar el proyecto
en otra computadora se necesitan los datos por separado; clonar este repositorio
no descarga esos insumos, modelos ni resultados. Los informes propios dentro de
`documentation/` sí se pueden versionar. Sus enlaces a resultados locales
requieren disponer también de la carpeta `outputs/`.

No usar `git add -f` para incluir datos o artefactos ignorados. Antes de publicar,
revisar `git status` y `git diff --cached --stat`.
