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

Las especificaciones y la procedencia recuperadas se versionan por separado en
[`configs/`](../configs/README.md): diseñosJSON, hashes, registro de modelos y
particiones expresadas como posiciones, sin rendimientos ni matrices. Esto no
cambia el `.gitignore`, no copia los datos a Git y no convierte el clon en una
distribución autosuficiente de los experimentos. Las copias no sobrescriben sus
fuentes locales congeladas.

`results/current_champions/` publica exclusivamente métricas y auditorías agregadas
deC-T3,26,14 yB1. No contiene registros individuales, rendimientos,OOF ni modelos.
El bundle reproducible de26 entradas permanece en `data/processed/current_champions/`
y sus predicciones por parcela en `outputs/research/current_champions/`, ambos
excluidos. L40 queda fuera de esa entrega actual, conservando su historial.

La documentación propia incluye un [inventario de IA generativa](ai_usage.md) y
prompts textuales recuperados, con procedencia y límites. Revisar su contenido
antes de publicar, igual que cualquier documento propio. Los archivos compilados
`__pycache__/` y `*.pyc` no pertenecen al repositorio; retirar su seguimiento no
requiere borrarlos del disco.

No usar `git add -f` para incluir datos o artefactos ignorados. Antes de publicar,
revisar `git status` y `git diff --cached --stat`.
