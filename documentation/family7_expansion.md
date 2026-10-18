> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# F7 — Expansión controlada de CatBoost

Se ejecutaron exclusivamente E1 historia NDVI2, E2 pendiente media y E3 ambos, con el modelo CatBoost y las ocho configuraciones previamente congeladas. Cada variante seleccionó dentro de cuatro particiones internas de cada entrenamiento externo. F7-00/F7-01 y todos los controles se recuperaron sin ajustes ni cambios.

## Resultados completos OOF

| Modelo | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| F7-00 | 0.504874 | 0.515345 | 0.528223 | 0.642591 |
| F7-E1 | 0.512823 | 0.522021 | 0.544530 | 0.763684 |
| F7-E2 | 0.514374 | 0.520118 | 0.553412 | 0.671957 |
| F7-E3 | 0.519740 | 0.524171 | 0.563640 | 0.755083 |
| C-T3 | 0.511582 | 0.520604 | 0.581259 | 0.678778 |
| F5-01 | 0.504006 | 0.499759 | 0.544208 | 0.734797 |
| F6-E1 | 0.509249 | 0.506796 | 0.675872 | 0.741689 |
| F6-E2 | 0.508354 | 0.510588 | 0.662413 | 0.735425 |

RMSE t/ha: métricas sobre138 OOF completas por repetición; aleatoria promedia10 repeticiones. MAE y sesgo conservan idéntico procedimiento. Los resultados por fold sirven para diagnósticos y no reemplazan estas métricas. modelo TOP20/TOP15 solo se compara en los50 folds aleatorios compatibles, sin reconstrucción territorial. ID_POLIGONO es el identificador parcelario real del proyecto.

## Respuestas sobre bloques y complementariedad

### 1. ¿Historia NDVI2 mejora CatBoost compacto?

- climate_profile: ΔRMSE +0.006676, ΔMAE -0.000885, Δsesgo +0.019500.
- municipality: ΔRMSE +0.016307, ΔMAE +0.023032, Δsesgo +0.045237.
- random: ΔRMSE +0.007949, ΔMAE +0.009383, Δsesgo -0.008196.
- spatial: ΔRMSE +0.121093, ΔMAE +0.096125, Δsesgo +0.053391.
### 2. ¿Pendiente aporta información incremental?

- climate_profile: ΔRMSE +0.004773, ΔMAE +0.001551, Δsesgo +0.020964.
- municipality: ΔRMSE +0.025189, ΔMAE +0.032714, Δsesgo +0.026789.
- random: ΔRMSE +0.009500, ΔMAE +0.010496, Δsesgo -0.000054.
- spatial: ΔRMSE +0.029366, ΔMAE +0.015798, Δsesgo +0.032250.
### 3. ¿La combinación supera los modelos individuales?

- climate_profile: ΔRMSE +0.008826, ΔMAE +0.004041, Δsesgo +0.007639.
- municipality: ΔRMSE +0.035417, ΔMAE +0.053436, Δsesgo +0.027234.
- random: ΔRMSE +0.014866, ΔMAE +0.014756, Δsesgo -0.010196.
- spatial: ΔRMSE +0.112492, ΔMAE +0.087123, Δsesgo +0.059832.
- E3 vs F7-E1, climate_profile: ΔRMSE +0.002150, ΔMAE +0.004926.
- E3 vs F7-E1, municipality: ΔRMSE +0.019109, ΔMAE +0.030404.
- E3 vs F7-E1, random: ΔRMSE +0.006917, ΔMAE +0.005373.
- E3 vs F7-E1, spatial: ΔRMSE -0.008601, ΔMAE -0.009001.
- E3 vs F7-E2, climate_profile: ΔRMSE +0.004053, ΔMAE +0.002490.
- E3 vs F7-E2, municipality: ΔRMSE +0.010227, ΔMAE +0.020722.
- E3 vs F7-E2, random: ΔRMSE +0.005366, ΔMAE +0.004260.
- E3 vs F7-E2, spatial: ΔRMSE +0.083126, ΔMAE +0.071325.

Las ablaciones reajustadas son la evidencia incremental principal: cada representación se retunea internamente. Las importancias no sustituyen esta comparación. E3 es un modelo conjunto nuevo; no se suman ganancias E1/E2.

### 4. ¿Mejora la discriminación intraperfil?

| Modelo | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| F7-00 | 0.628178 | 0.543412 | 0.544684 | 0.584666 |
| F7-E1 | 0.617327 | 0.530309 | 0.557205 | 0.551925 |
| F7-E2 | 0.627345 | 0.551970 | 0.537168 | 0.541306 |
| F7-E3 | 0.621875 | 0.525901 | 0.547043 | 0.553272 |

RMSE de diferencias de rendimiento, igual peso por perfil, distinto del RMSE de rendimiento individual. Ponderación por pares, MAE, conteos y resultados dentro/fuera de Chignahuapan están separados. Solo se usan parejas del mismo modelo externo. Cada repetición aleatoria tiene soporte propio; promedios de conteos por repetición no son muestras independientes. Las tablas marcan soporte reducido si hay menos de10 parcelas o3 perfiles: dichos resultados son descriptivos y no conclusiones robustas.

- F7-E1: menor RMSE intraperfil de igual peso en 3/4 protocolos: random, climate_profile, spatial.
- F7-E2: menor RMSE intraperfil de igual peso en 3/4 protocolos: random, municipality, spatial.
- F7-E3: menor RMSE intraperfil de igual peso en 3/4 protocolos: random, climate_profile, spatial.

### 5. ¿Las ganancias territoriales son estables?

- F7-E1, municipality: al omitir Singuilucan, ΔRMSE +0.015147, ΔMAE +0.023641. Mejoran RMSE 1/5 folds y3/9 municipios; entre municipios de≥10 parcelas: 0/4.
- F7-E1, spatial: al omitir Singuilucan, ΔRMSE +0.135675, ΔMAE +0.111959. Mejoran RMSE 1/5 folds y2/9 municipios; entre municipios de≥10 parcelas: 1/4.
- F7-E2, municipality: al omitir Singuilucan, ΔRMSE +0.026066, ΔMAE +0.034903. Mejoran RMSE 0/5 folds y2/9 municipios; entre municipios de≥10 parcelas: 0/4.
- F7-E2, spatial: al omitir Singuilucan, ΔRMSE +0.034969, ΔMAE +0.021554. Mejoran RMSE 2/5 folds y5/9 municipios; entre municipios de≥10 parcelas: 2/4.
- F7-E3, municipality: al omitir Singuilucan, ΔRMSE +0.036736, ΔMAE +0.056375. Mejoran RMSE 0/5 folds y2/9 municipios; entre municipios de≥10 parcelas: 0/4.
- F7-E3, spatial: al omitir Singuilucan, ΔRMSE +0.126580, ΔMAE +0.100658. Mejoran RMSE 1/5 folds y2/9 municipios; entre municipios de≥10 parcelas: 1/4.

Todas las omisiones recalculan OOF sin reajustar. Las tablas incluyen cada municipio, estado y bloque; sesgo, SSE de sesgo versus dispersión y omisiones de1/5/10 beneficiarios. Se estudian Singuilucan/bloque4, Chignahuapan y bloque3 junto con el resto, sin optimizarlos. Mejorar un nivel regional no demuestra discriminación intraperfil ni generalización a años diferentes. Municipios con una a cinco parcelas requieren cautela.

### 6. ¿Los errores justifican una arquitectura combinada?

- F7-00 vs F7-E1: correlaciones medias por protocolo climate_profile=0.964, municipality=0.953, random=0.970, spatial=0.957.
- F7-00 vs F7-E2: correlaciones medias por protocolo climate_profile=0.983, municipality=0.968, random=0.981, spatial=0.984.
- F7-00 vs F7-E3: correlaciones medias por protocolo climate_profile=0.963, municipality=0.922, random=0.964, spatial=0.957.
- F7-E1 vs F7-E2: correlaciones medias por protocolo climate_profile=0.966, municipality=0.971, random=0.968, spatial=0.956.
- F7-E1 vs F7-E3: correlaciones medias por protocolo climate_profile=0.990, municipality=0.984, random=0.991, spatial=0.993.
- F7-E2 vs F7-E3: correlaciones medias por protocolo climate_profile=0.976, municipality=0.971, random=0.978, spatial=0.963.

Correlaciones, covarianzas poblacionales, sesgo y dirección común de errores se conservan por repetición, sin mezclar10 repeticiones como1380 parcelas independientes. El análisis por cuartil del error del núcleo es posterior al ajuste: una relación entre ganancia y error base tiene acoplamiento algebraico y no valida un gate predictivo. Los casos donde historia/pediente ayudan y donde ambos perjudican son descriptivos; no se entrena un selector por parcela, no se calculan pesos óptimos, ni se entrega un resultado de ensemble o stacking.

### 7. Base y posibles correctores

La recomendación debe distinguir el control compacto F7-00 de señales locales que puedan corregir sus errores. Las correlaciones por sí solas no justifican una combinación; se requiere mejora incremental territorial y/o intraperfil y suficiente soporte. Un residual futuro usaría cross-fitting del núcleo dentro de cada entrenamiento correspondiente y regularización de amplitud que incluya corrección cero, seleccionada solo internamente. No utilizaría residuos OOF globales como targets, ni el modelo TOP20/TOP15 como fuente de targets. Aquí no se ejecuta ninguna combinación.

## Interpretabilidad

Historia2 se permuta conjuntamente, lluvia3 conjuntamente, MayNDVI y pendiente por separado, condicionando al mismo perfil de validación. Se exige soporte del entrenamiento para las combinaciones generadas y mínimo10 parcelas respaldadas; no se fabrica importancia cero cuando el efecto no es identificable. El radio en espacio preprocesado es empírico y no garantiza soporte causal; el cambio de dimensiones cambia ese espacio entre variantes. Ablación reajustada y permutación condicionada responden preguntas distintas.

- ALE completa F7-E1, HIST_S2_ndvi_promedio_mean: 1/65 ajustes respaldados.
- ALE completa F7-E1, HIST_S2_ndvi_promedio_std: 0/65 ajustes respaldados.
- ALE completa F7-E2, TOPO_BASIC_slope_mean: 0/65 ajustes respaldados.
- ALE completa F7-E3, HIST_S2_ndvi_promedio_mean: 2/65 ajustes respaldados.
- ALE completa F7-E3, HIST_S2_ndvi_promedio_std: 1/65 ajustes respaldados.
- ALE completa F7-E3, TOPO_BASIC_slope_mean: 1/65 ajustes respaldados.

Donde no hay ALE completa respaldada se muestran diferencias locales y no se unen huecos. Interacciones predefinidas incluyen lluvia–NDVI, NDVI–historia, lluvia–pendiente e historia–pendiente. Son diferencias mixtas de cuatro esquinas respaldadas, no causas. PredictionValuesChange, frecuencia de niveles compartidos y estabilidad de umbrales son descriptivos; una variable muy utilizada puede perjudicar validación. Las hojas reales, incluidas vacías y pequeñas, se registran porque SymmetricTree no impone mínimo de observaciones mediante min_data_in_leaf.

## Síntesis de decisión: las siete preguntas

1. **Historia NDVI2 no mejora el modelo directo compacto:** RMSE empeora en los cuatro protocolos. Hay señales locales bajo ponderación igual por perfil y fuera de Chignahuapan, pero no compensan el coste absoluto, especialmente espacial. La leve reducción de MAE por perfil no constituye una mejora global.

2. **Pendiente ofrece una señal intraperfil parcial, no ganancia predictiva global directa:** su RMSE absoluto también empeora en los cuatro protocolos. Es la extensión menos costosa espacialmente y mejora diferencias espaciales al dar igual peso a perfiles, pero perjudica la ponderación global por parejas.

3. **E3 no combina eficazmente ambas señales:** empeora frente al núcleo en todos los RMSE; es peor que E1 y E2 en aleatoria, perfil y municipal. Espacialmente mejora un poco a E1, pero es claramente peor que E2. No hay evidencia de sinergia predictiva global.

4. **La respuesta intraperfil depende de la ponderación y del territorio:** E1/E3 mejoran RMSE de igual peso en aleatoria, perfil y espacial; E2 en aleatoria, municipal y espacial. Sin embargo, las tres empeoran RMSE y MAE ponderados por parejas en los cuatro protocolos. En espacial, fuera de Chignahuapan, tanto igual peso como por parejas mejoran; dentro de Chignahuapan se deterioran. Este último contraste dispone de62 parcelas pero solo2 perfiles, frente a43 parcelas/10 perfiles fuera. No constituye una regla geográfica de modelado.

5. **No hay una ganancia absoluta estable que dependa solamente de Singuilucan:** los deterioros municipal/espacial frente a F7-00 persisten al excluir Singuilucan o Chignahuapan. Historia y E3 mejoran bloque4, pero empeoran los otros cuatro; pendiente mejora bloques2/4 y empeora1/3/5. En bloque3 el sesgo pasa de0.734682 a0.999336 con historia,0.838679 con pendiente y0.986276 con E3. El deterioro espacial de historia/E3 es principalmente de sesgo regional, no una mejora general trasladada al resto.

6. **Hay casos complementarios, pero poca diversidad global para justificar promediar estos modelos:** las correlaciones espaciales de errores núcleo–E1/E2/E3 son0.957/0.984/0.957 y E1–E3 es0.993. En spatial, E1 y E2 mejoran conjuntamente20.3% de parcelas; historia sola13.0%, pendiente sola26.1%, ninguno40.6%. E3 mejora solo16.7% del subconjunto beneficiado exclusivamente por pendiente, por lo que no preserva bien esa fortaleza. No se ha probado un ensemble; correlación alta tampoco demuestra imposibilidad matemática de toda combinación.

7. **Conservar F7-00 compact4 como base de esta familia, sin promoción.** No usar E1/E2/E3 completos como correctores listos para sumar. Si se autoriza una próxima investigación, priorizar una corrección de pendiente pequeña, con contracción y foco metodológico intraperfil, y reservar historia2 como sensibilidad secundaria. El núcleo debe generar targets residuales mediante cross-fitting exclusivamente dentro de cada entrenamiento. El corrector y su amplitud —incluido cero— se seleccionarán internamente; la ponderación de perfiles y el soporte requieren diseño previo, sin gates municipales ni reglas regionales. Revisar antes los resultados de F4/Etapas B–C sobre objetivos intraperfil para evitar duplicar arquitecturas. Preferir este contraste acotado a stacking/promedio de las extensiones completas; ninguno se ejecuta ahora.

Los deterioros municipales de F6-E no desaparecen con CatBoost. Aunque afectan a menos parcelas que en Extra Trees, persisten muchas de las mismas:48.6% de todas las parcelas se deterioran con historia en ambas familias y54.3% con pendiente. Cada incremento se mide contra el núcleo de su propia arquitectura. Superar los RMSE municipales absolutos de F6-E1/E2 no demuestra que los bloques hayan ayudado a CatBoost.

Las variables se utilizan de manera frecuente pese al deterioro: en espacial historia mean/std entra en aproximadamente38%/35% de árboles de E1 y pendiente en31% de E2. Los umbrales medianos históricos rondan0.30/0.13; pendiente muestra umbrales variables entre entrenamientos. Esto describe particiones aprendidas, no causalidad ni estabilidad de una recomendación agronómica. El soporte de ALE completas es escaso. Permutación espacial de historia E3 no es identificable con el gate establecido; en municipal ningún bloque adicional alcanza soporte, lo que no equivale a irrelevancia.

El resultado debilita que CatBoost directo, con esta búsqueda y muestra, pueda integrar las señales locales sin coste territorial. Conserva la hipótesis de señal intraperfil fuera de perfiles dominantes, pero no demuestra un corrector residual útil ni irrelevancia agronómica de historia o pendiente. No permite rechazar todos los CatBoost ni todas las arquitecturas jerárquicas.

## Límites y cierre

Se detiene tras las tres ablaciones, sin nuevos predictores, nuevos screenings, XGBoost reajustado, límites ampliados, ensemble, stacking, residuos, modelo final,59 PRED o promoción del modelo TOP20/TOP15. Todas las comparaciones y recomendaciones son exploratorias sobre etiquetas y folds reutilizados; no se afirma superioridad estadística.


## Verificación

Siete pruebas pasaron: ámbito y restauración del adaptador, permutación conjunta y soporte antes de predicción, replay de975 modelos, entrenamiento exclusivo,65 particiones y selección interna originales, referencias/OOF/métricas, hojas y efectos respaldados. Se conservaron 13827 hashes anteriores.195 modelos externos y6240 ajustes internos;6435 ajustes científicos,17526 filas OOF con controles. Advertencias de ajuste: 0. No modelos combinados, residuos, modelo final ni59 PRED.
