# GeoCebada — historia de los modelos (GitHub Pages)

Presentación narrativa estática, en español, diseñada para explicar **el camino
C-T3 → experto local → mezcla geológica → corrector R3 → Reference26**,
con una comparación reproducible de las arquitecturas Reference26, Compact14,
B1, L40/Local04D y C-T3.

El micrositio se aloja en `site/`, sin npm, librerías remotas, recopilación de
visitas ni servicios predictivos. Es independiente de las matrices privadas,
las 59 estimaciones y los modelos `joblib` originales. No se han modificado
modelos, documentación histórica ni el resultado de la competición.

## Probarlo localmente

Desde la raíz del repositorio:

```bash
python scripts/sync_story_data.py --check
python -m unittest discover -s tests -p 'test_story_site.py'
python -m http.server 8000 --directory site
```

Abrir <http://localhost:8000/>. No abrir vía `file://`, porque el gráfico
comparativo carga `data/results.json` con `fetch`.

## Métricas y su procedencia

`site/data/results.json` se regenera exclusivamente con fuentes agregadas
públicas de este repositorio:

- `results/comparison_97_41/v1/metrics.csv` — 16 particiones 97/41.
- `results/current_champions/v1/metrics.csv` — resultados del banco original de
  65 folds (50 aleatorios, 5 perfiles climáticos, 5 municipales, 5 espaciales).
- La fila `L40 / Local04D` de la tabla «Comparación reciente compatible»
  en `README.md` — comparador externo en los cuatro protocolos originales.

No hay datos falsos ni estimaciones de las 59 parcelas en `site/data`.
Se calculan y muestran las métricas promediadas por protocolo, **no** una
RMSE conjunta entre experimentos diferentes. Referencias26 y14 son champions
según la decisión del proyecto, aunque B1 alcance un RMSE marginalmente menor
en algunos protocolos. La narrativa no atribuye causalidad a los predictores.

Si cambian las fuentes agregadas, hacer:

```bash
python scripts/sync_story_data.py --write
python scripts/sync_story_data.py --check
```

`--check` forma parte de CI. Las demos de lluvia y vecindarios usan datos
**sintéticos y expresamente rotulados** y no ajustan modelos ni consultan
información parcelaria.

## Publicación

`.github/workflows/publish_story.yml` valida el sitio en las propuestas
(pull requests) y, tras integrar los cambios en `main`, sube **únicamente**
`site/` a GitHub Pages. También admite ejecución manual. En
**Settings → Pages → Build and deployment**, seleccionar **GitHub Actions**
como fuente de publicación. GitHub Pages debe estar habilitado para este fork;
si no lo está, la validación puede pasar aunque el despliegue falle hasta
activarlo.

La URL esperada del proyecto, una vez desplegado y activado Pages, es:

`https://heri-espino.github.io/todoseboso/`

Se preserva el subdirectorio del proyecto usando todas las rutas relativas.
No se ejecuta entrenamiento, Python científico, generación de imágenes,
PDFs, trabajos pesados ni publicación de resultados individuales en CI.

## Contrato científico

Para cambios en arquitectura o copy revisar las fichas y resultados:

- `documentation/models/Reference26/README.md`
- `documentation/models/Compact14/README.md`
- `documentation/models/CT3/README.md`
- `documentation/current_champions_reproduction.md`
- `documentation/model_comparison_convention.md`

Expresiones como “la geología decide” significan mezcla predictiva aprendida,
no una intervención causal. Los valores ilustrativos siempre deben conservar
su etiqueta sintética. La web no compara 0.4625 con la RMSE 0.481936 de un
banco diferente. LOOCV 138-fold de modelos pares aún no está ejecutado.

## Sincronización del 18 de octubre de 2026: interpretabilidad

La sección «¿Qué señales realmente aportan?» usa tres CSV agregados versionados y
controlados por `python scripts/check_story_evidence.py`:

- `results/core4_relevance/v1/metrics.csv`: retirar por separado las cuatro
  entradas de C-T3 y volver a ajustar, en cuatro protocolos distintos;
- `results/reference26_component_evidence/v1/architecture_metrics.csv`:
  Reference26 con y sin el bloque R3;
- `results/reference26_component_evidence/v1/component_weights.csv`:
  peso medio aprendido del experto local en Reference26.

La copia pública `site/data/evidence.json` se audita por coincidencia numérica
con cada fuente. No incluye rendimientos por parcela, localizaciones ni modelos.
Las ablaciones de C-T3 no son importancias individuales dentro de Reference26.

- HHI no demuestra un aporte robusto: quitarlo mejora el RMSE del protocolo
  espacial de C-T3; no justifica retirarlo de Reference26 sin reajustarlo.
- R3 mejora el RMSE descriptivo en los cuatro protocolos originales, pero eso
  no prueba que sus tres indicadores sean indispensables por separado.
- El peso del experto cambia según el protocolo; no se fija por municipio.
- Holm corrige las comparaciones examinadas, no la selección histórica.

## Dos implementaciones de página preservadas

El fork ya tenía dos presentaciones estáticas: `site/` y `website/`.
El publicador **canónico** es `.github/workflows/publish_story.yml`: monta
`site/` en la raíz y conserva `website/` en `/alternate/`. El segundo workflow
`publish_story_pages.yml` valida la presentación alternativa, sin otro deploy.
No se eliminó ni reescribió el trabajo paralelo.

GitHub Pages se debe activar desde Settings → Pages → Build and deployment →
GitHub Actions. Intentar habilitar Pages desde un workflow falló por permisos;
la web no se considera publicada hasta observar un deploy exitoso.

Validación:

```bash
python scripts/sync_story_data.py --check
python scripts/check_story_evidence.py
python -m unittest discover -s tests -p test_story_site.py
python scripts/529_check_story_site.py
node --check site/app.js
```
