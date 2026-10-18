# Reproducibilidad, metadatos y límites

## Qué se puede hacer con un clon de Git

Leer código, diseños, particiones posicionales, documentación y prompts recuperados; inspeccionar el registro; ejecutar la verificación documental. No se puede reproducir entrenamiento uOOF sólo con Git porque datos, modelos y checkpoints se distribuyen aparte. Tampoco se puede inferir el error real de 59.

## Preparación

1. Revisar [entorno](../environments/README.md) e instalar dependencias compatibles. Las versiones publicadas son un inventario observado, no una instalación nueva certificada.
2. Obtener los insumos autorizados y conservar rutas y orden originales de las tablas. Consultar los hashes en `configs/` y el diseño local de la batería.
3. En el puente conL40, preparar los insumosC4/representación congelada procedentes de GeoC. El código local de Ridge se conserva en un snapshot, pero eso no elimina la dependencia de sus covariables para reconstruir el puente. `src/geoc_bridge.py` conserva la ubicación histórica relativa `../fira/GeoC`; adaptarla explícitamente si cambia el entorno.
4. Elegir una etapa del [índice](experiment_index.md) y su secuencia específica. No ejecutar masivamente scripts numerados.

## Qué se versionó ahora

Se exportaron diseñosJSON disponibles, su procedencia y hashes, y las 65 particiones externas con sus particiones internas inmediatas. También se conserva el banco81 que agrega16 splits97/41. Las copias son revisables y portables, mientras las fuentes locales congeladas se conservan sin sobrescribir. Se añadieron registro de modelos, inventarios y versiones de entorno.

Las especificaciones exportadas no son una nueva API de ejecución: los scripts históricos siguen leyendo sus rutas locales. No se afirma reconstrucción completa desde cero de todos los experimentos. Las configuraciones de formatos antiguos no cubiertas por el export siguen documentadas en sus módulos y diseños.

## Verificación y regeneración

```powershell
# Sin datos privados: enlaces principales, registros y metadatos
python scripts/520_validate_repository_documentation.py

# Sólo en el entorno original con fuentes locales: actualizar los exports
python scripts/519_export_research_metadata.py
```

Regenerar metadatos exige revisar el diff: un diseño ya congelado no debe sustituirse silenciosamente. Los hashes originales se conservan como procedencia; cambiar un archivo de código actual no invalida el hecho histórico de qué hash se congeló.

La [última batería](four_expert_combinations_reproduction.md) tiene pruebas y auditorías numéricas propias. La verificación documental no reemplaza esas pruebas ni vuelve a entrenar modelos. Algunas pruebas históricas requieren datos/outputs y no pueden ejecutarse en un clon público incompleto.

## Qué aún requiere cierre

- Confirmación externa con rendimientos nuevos para sostener superioridad fuera de las muestras exploradas.
- Elección y consolidación explícita de la receta final de entrega si se desea cambiar la entrega histórica.
- Una instalación nueva verificada y, si se necesita, empaquetado independiente de los artefactos históricos.
- Bibliografía/anexosPDF, enlace demostrativo y revisión humana de los requisitos de plataforma.
