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
banco diferente. 

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


## Presentación para lectores con distintos conocimientos

La portada cuenta la historia de la predicción en lenguaje cotidiano. El
apartado «¿De dónde sale una estimación?» permite modificar, con números
**ficticios**, el peso del experto y la magnitud acotada de R3. El apartado
«Qué respaldan las pruebas» separa asociaciones estadísticas, ablaciones
reajustadas y contrastes pareados. Las preguntas al final aclaran las diferencias entre evaluación aleatoria,
espacial y las particiones de 97 parcelas para entrenar y 41 para evaluar.

Los nuevos recursos son:

- `site/preguntas.js`: controles accesibles de pesos sintéticos, asociaciones
  con p ajustada por Holm, protocolo de Reference25_NoHHI frente a Reference26,
  avisos de soporte por estado y cobertura/anchura de intervalos.
- `site/preguntas.css`: presentación de escritorio y móvil, sin scripts ni
  servicios externos.
- `site/data/new_research.json`: sólo **agregados públicos** de
  `results/core4_relevance/v1`, `results/reference26_component_evidence/v1`
  y `results/four_final_checks/v1`.
- `site/media/NoHHI_delta_RMSE.png`: la figura original del experimento sin
  HHI, reparada a partir del archivo PNG corrupto de upstream (restauración de
  un byte CR de la firma y comprobación CRC de sus cinco bloques).
- `scripts/check_new_research.py`: compara cifras e intervalos del sitio con
  los CSV y auditorías originales, incluyendo el archivo PNG; se ejecuta en CI.

### Qué se puede comunicar

- En la OLS diagnóstica ajustada por estado, lluvia total, proporción de
  lluvia temprana y NDVI mayo conservan asociación bajo Holm13; HHI no.
  Esta OLS **no** proporciona los coeficientes ni p-valores de Reference26.
- Ninguna retirada individual de C-T3 sobrevivió Holm en la familia de 24
  contrastes; los controles NDVI solo y media de entrenamiento sí reflejaron
  diferencia en ciertos protocolos.
- En las tres familias archivadas de arquitectura, 0 de 952 contrastes
  sobrevivieron el ajuste respectivo. No implica equivalencia ni ausencia de
  efectos: las etiquetas ya se habían reutilizado para elegir arquitecturas.
- Reference25_NoHHI mejora RMSE espacial `0.6333 → 0.5328` t/ha,
  pero empeora municipal `0.5752 → 0.5982`; los cuatro IC95% incluyen
  cero y los contrastes no superan Holm4. No reemplaza Reference26.
- De las 59 parcelas sin etiqueta, 11 tienen algún aviso de soporte (se
  pueden superponer). No se ha calculado su error porque Y no está disponible.
- Los intervalos aleatorios de cobertura nominal 90% logran ~92.9% de
  cobertura en validación con anchura media ~2.085 t/ha para Reference26.
  **No son intervalos garantizados para las 59 predicciones finales**.

Se conservan el núcleo histórico y todas las comparaciones anteriores; no
se modificaron los modelos, las 59 predicciones ni la selección de champions.
No se deben ofrecer los controles didácticos como inferencia real.

### Validación ampliada

```bash
python scripts/sync_story_data.py --check
python scripts/check_story_evidence.py
python scripts/check_new_research.py
python scripts/520_validate_repository_documentation.py
python -m unittest discover -s tests -p 'test_story_site.py'
python scripts/529_check_story_site.py
node --check site/app.js
node --check site/preguntas.js
```

Los resultados se versionan con sus protocolos originales. No agregar números
al sitio si su figura o su afirmación no pueden verificarse contra una tabla
pública concreta.

## Figuras estadísticas interactivas

El sitio usa SVG accesible sin Plotly ni dependencias CDN. El motor
`site/charts.js` y `site/charts.css` toman la tipografía y paleta de
las variables CSS de la página. Los gráficos permiten inspeccionar
cada valor con el cursor o mediante Tab y son desplazables en móvil.

- RMSE de cinco modelos: gráfico de puntos ordenado dentro de un protocolo.
- Ablaciones del núcleo climático: cinco puntos y RMSE original señalado.
- Corrección residual R3: cuatro pares de RMSE con y sin corrector.
- Mezcla con experto local: pesos de 0 a 100 por ciento por protocolo.
- Asociación climática: coeficientes firmados y valores p Holm separados;
  un valor p no se dibuja como una importancia predictiva.
- Sensibilidad sin HHI: diferencias, cuatro IC95 % publicados y línea cero.
- Cobertura: puntos de cobertura empírica frente al nivel nominal, con anchuras.
- Lluvia mensual: barras SVG con dos escenarios inventados de igual total.
- Distribución por región: medianas, percentiles 10/25/75/90 y grupos
  observados/estimados. Se coteja contra
  `results/reference26_distribution/v1/descriptive_global_state.csv`
  y **no** se reconstruye una ECDF sin observaciones individuales.

Se conservan las figuras originales PNG en desplegables, accesibles
para contrastar con los nuevos gráficos. Se señala expresamente cuando
el eje de puntos no comienza en cero: no se usan longitudes de barras
truncadas que exageren visualmente cambios pequeños.

Verificaciones nuevas:

```bash
python scripts/check_site_charts.py
node --check site/charts.js
node --test tests/test_svg_charts.cjs
```

Estas pruebas comprueban la coincidencia numérica de los agregados,
los intervalos de confianza, las cantidades representadas en los SVG,
los textos alternativos y la existencia de todos los elementos de la página.
No se entrenan modelos ni se publican las 59 predicciones individuales.
