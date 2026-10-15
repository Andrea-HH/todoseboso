"""Reviewable F5 documentation and descriptive figures; no model implementation."""
import json,re
import numpy as np
import pandas as pd
from . import gpr_evidence_design as g
from src.family_4.stage_c_final_report import md

def table(name):return pd.read_csv(g.OUT/'tables'/name)

def prose(text):
    # Readability of prose only; preserve exact column names and artifact paths.
    for a,b in {'MayNDVI':'NDVI de mayo','meanfold':'media de folds','porperfil':'por perfil','porfold':'por fold','porbaseline':'por baseline','bloque3':'bloque 3','outertrain':'outer-train','outervalidation':'outer-validation','innertrain':'inner-train','GPRexacto':'GPR exacto','GPRdirecto':'GPR directo','GPRresidual':'GPR residual','TRAIN':'TRAIN','NDVImedia':'NDVI media','NoGP':'No GP'}.items():text=text.replace(a,b)
    terms='observaciones|parcelas|etiquetas|perfiles|folds|particiones|repeticiones|columnas|variables|dimensiones|parámetros|hiperparámetros|entradas|capas|bloques|medias|medida|listas|años|meses|longitudes|reinicios|componentes|scores|por|de|para|con|solo|históricas|efectivas|son|se|TRAI[N]|PRED|OOF|Sentinel'
    text=re.sub(r'(?<=\d)(?=(?:'+terms+r')\b)', ' ',text)
    for a,b in [('no se entrena, optimiza, selecciona nuevas variables','no se entrenan modelos, no se optimizan hiperparámetros ni se seleccionan nuevas variables'),('alpiso','al piso'),('unde','un de'),('unmodelo','un modelo'),('uníndice','un índice'),('unkernel','un kernel'),('unmodelo','un modelo'),('elnúcleo','el núcleo'),('elkernel','el kernel'),('altrain','al train'),('alcontrol','al control'),('delbase','del base'),('enestaetapa','en esta etapa'),('dentro delperfil','dentro del perfil'),('solo alclima','solo al clima'),('laganancia','la ganancia'),('unranking','un ranking'),('unaúnica','una única'),('porseparado','por separado'),('mismo X','mismo X')]:text=text.replace(a,b)
    return text

def plots(t):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    corr=pd.read_csv(g.OUT/'tables/predictor_pearson_TRAIN138.csv',index_col=0)
    fields=g.CORE+[g.c.DTR]+g.HISTORY+[g.SLOPE,'CLIMATE_tmin_mean_mean','CLIMATE_tmax_mean_mean']
    labels=['Lluvia total','Fracción temprana','Concentración','NDVI mayo','SD DTR','NDVI histórico nivel','NDVI histórico estacionalidad','Pendiente media','Tmin media','Tmax media']
    fig,ax=plt.subplots(figsize=(11,9));im=ax.imshow(corr.loc[fields,fields],vmin=-1,vmax=1,cmap='coolwarm');ax.set_xticks(range(len(fields)),labels,rotation=55,ha='right');ax.set_yticks(range(len(fields)),labels)
    fig.colorbar(im,ax=ax,label='Correlación Pearson entre X, sin selección por Y');fig.suptitle('F5: redundancia descriptiva, 138 TRAIN; no predicciones GPR');fig.tight_layout();fig.savefig(g.OUT/'figures/candidate_redundancy.png',dpi=170);plt.close(fig)
    f=table('history_top15_frequencies.csv');f=f[f.baseline.eq('TOP20_ENET')].sort_values('frequency');fig,ax=plt.subplots(figsize=(11,8));ax.barh(f.feature.str.replace('HIST_S2_','',regex=False),f.frequency);ax.set(xlim=(0,1.05),xlabel='Frecuencia de inclusión en los 50 ajustes externos RS4');fig.suptitle('TOP15 de un universo de 16 columnas: frecuencia ≠ importancia independiente');fig.tight_layout();fig.savefig(g.OUT/'figures/history_selection_frequency.png',dpi=170);plt.close(fig)

def build(t,matrix):
    candidate=table('candidate_variable_inventory.csv');geometry=table('representation_geometry.csv');freq=table('history_top15_frequencies.csv');hist=table('historical_metrics_oof_recomputed.csv');rs4=table('archived_04_RS4.csv');dmetrics=table('D_metrics_summary.csv')
    gh=pd.read_csv(g.ROOT/'outputs/modeling/family_1/h_joint_climate_signal/v1/tables/40_model_comparison.csv');rain=pd.read_csv(g.ROOT/'outputs/modeling/family_1/rainfall_yield/v1/tables/05_model_comparison.csv');pcr=pd.read_csv(g.ROOT/'outputs/modeling/family_1/h_joint_climate_signal/extensions/rain_tmax/v1/tables/40_model_comparison.csv')
    plots(t)
    audit=f'''# F5 — Auditoría transversal de evidencia para diseñar GPR

Estado: **propuesta para revisión; modelos F5 no ejecutados**. Se recuperan resultados originales y se realizan únicamente verificaciones de semántica, agregación OOF archivada y redundancia entre X. No se entrena, optimiza, selecciona nuevas variables mediante Y, ni predicen las 59 PRED. Toda señal identificada sigue siendo exploratoria sobre las mismas 138 etiquetas.

## Alcance y trazabilidad

138 TRAIN, 59 PRED, 197 parcelas; 43 perfiles etiquetados, 12 repetidos y 53 en el universo completo. Se revisan lluvia E1–E8, G/H y extensión PCR, RS1–RS6, Champion, J/K/L/M, Familias 2/3, screening1473, F4/F4-E y A–D. Se reutilizan inventario de 228 series históricas y diagnósticos D; no se duplican sus pipelines. `audit/protected_inputs.csv` registra fuentes y hashes; `audit/technical_primary_sources.csv` documenta bibliografía técnica.

El inventario anterior está en [Etapa D](../../../../family_4/territorial_intraprofile_program/v1/stage_d/tables/model_inventory.csv). Los archivos se identifican mediante rutas desde la raíz y hashes en el inventario F5. Familias2/3 no justificaron mayor complejidad funcional/estructural; esas conclusiones no prueban que todos los kernels fallen. Suelo/geología250k aportan descripciones, sin contribución incremental estable; no entran al núcleo inicial. La cartografía local50k suspendida no se reabre.

## A. Lluvia: señal fuerte, representación y agregación importan

RS3 `ONLY_PRECIPITATION_XGB` usa **10 resúmenes CLIMATE_precip_**, no siete valores mensuales. RS4 `PRECIPITATION_XGB` es la referencia reconstruida correspondiente. El nombre solicitado `PRECIPITATION_ONLY_XGB` no se encontró exactamente en CSV/MD/PY; se conserva esa limitación en `requested_identifier_resolution.csv`, sin inventar un alias validado.

RS3 mostró que total solo y timing solo pierden frente al bloque completo. La ventana temprana RS3 incluye cinco variables climáticas de abril–junio, no solamente `CLIMATE_precip_early_sum`; su mejor resultado no demuestra que un único acumulado sea suficiente. No hay ablación aislada que pruebe que ese acumulado, por sí mismo, sea la variable óptima para GPR.

Las cifras RS3/RS4 publicadas son medias de RMSE de folds y se preservan. Se recomputan también métricas sobre138OOF completas por repetición, sin reentrenar:

{md(hist[hist.experiment.isin(['ONLY_PRECIPITATION_XGB','ONLY_TOTAL_PRECIP_ONLY_XGB','ONLY_PRECIP_TIMING_XGB','ONLY_EARLY_WINDOW_XGB','PRECIPITATION_XGB_BASE','PRECIPITATION_XGB_HISTORY15','TOP20_ENET_HISTORY15','TOP20_ENET_DIRECT_HISTORY24','A_CURRENT_CH_H_T'])])}

Los valores archivados de RS3 —incluidos total/timing/ventanas— permanecen en `archived_01_RS3.csv` y `archived_03_RS3.csv`. Una cifra distinta de la documentación puede deberse a agregación, no a cambio del modelo. RS6 Champion 0.486505 de mediafold y aproximadamente0.498127 de OOF completa son medidas diferentes.

Lluvia7, frente a total solo y alternativas agregadas, bajo los65folds:

{md(rain[rain.experiment.isin(['E1_TOTAL_LINEAR','E3_MONTHLY_RIDGE','E4_SUMMARY_RIDGE','E5_DYNAMICS_RIDGE'])][['experiment','protocol','RMSE_mean','MAE_mean']])}

La representación compacta C total/fracción temprana/HHI con MayNDVI tiene la mejor evidencia municipal reciente. No es el mismo resumen que E4/H_S1: esos resultados no son intercambiables. C-T3 mejora municipio, con costo aleatorio y dependencia espacial del bloque3; total solo no reemplaza la distribución temporal.

## B. Temperatura: diferenciación territorial no equivale a utilidad incremental

La fuente verificada de Tmin/Tmax es **CHIRTS-ERA5**, resolución0.05°, extracción fraccional canónica. El diccionario antiguo `CHIRPS_OR_WORLDCLIM` es genérico e inexacto; G ya lo corrigió mediante etiquetas deTIFF/LEEME en `report/source_audit.json`, preservando el archivo anterior. El inventarioF5 usa la fuente corregida, no atribuye temperatura aWorldClim.

{md(gh[gh.experiment.isin(['H1_RAIN','H2_TMIN','H3_TMAX','H5_RAIN_TMIN','H6_RAIN_TMAX'])][['experiment','protocol','RMSE_mean','MAE_mean']])}

Tmin tiene estructura territorial y altitudinal descriptiva, pero no debe decirse que estado+altitud la explican completamente: correlaciones y separación no son una atribución causal ni una garantía de redundancia. Añadir siete Tmin no mejora de forma general H1. Tmax mejora RMSE aleatoria solo marginalmente, mientras empeora MAE y transferencia regional. La temperatura no subdivide los53perfiles exactos de lluvia.

{md(pcr[pcr.experiment.isin(['H_EXT_CACHED_RAIN_PCR','H_EXT_RAIN_TMAX_PCR'])][['experiment','protocol','RMSE_mean','MAE_mean']])}

PCR lluvia+Tmax mejora ciertos resultados aleatorios/porperfil pero no municipal/espacial: reducir dimensiones no elimina los límites de transferencia. Los 98% de varianza térmica explicados por PCs describen X, no rendimiento.

DTRstd es una candidata térmica más concreta que Tmin para una sensibilidad compacta, por F4-S5/C-T1, pero **no** se presume beneficio con MayNDVI: C-T2/C-T4 no combinaron sus fortalezas lineales. DTRstd mide desviación muestral de siete medias mensuales Tmax−Tmin, no Tmax media. Su señal espacial depende del bloque3. F5-02 probaría una interacción suave todavía hipotética.

## C. Vegetación2025: preservar la señal puntual correcta

`S2_ndvi_month_05`: Sentinel-2, media aritmética de observaciones válidas de `ndvi_promedio` de cada parcela durante mayo2025. Es una media temporal de promedios parcelarios suministrados; no máximo, q10, promedio abril–octubre ni NDVI de Planet. El código `src/family_1/m_satellite.py` genera el campo; `semantic_checks.json` verifica sus valores contra la serie nativa. No se conoce una regla universal que garantice la misma fase de cultivo en todas las parcelas.

F4-S1 usa lluvia7+MayNDVI, con imputación/escala solo de entrenamiento y piso NDVI0.05. Mejoró aleatoria/perfil/municipio frente a lluvia en la formulación evaluada; la mejora espacial general no es uniforme. El screening de NDVI solo fue inferior a lluvia: señal complementaria no significa predictor suficiente.

{md(dmetrics[dmetrics.experiment.isin(['F4-S1','F4-E2','C-T3','C-T1','C-H0M'])][['experiment','protocol','RMSE','MAE']])}

F4-E2 añade inicio del mayor ascenso LAI: beneficio local pequeño, sin mejora global uniforme. LAI se calcula desde SAVI por la ecuaciónFIRA; no es otra fuente espectral. LAIq10 reemplazando MayNDVI deterioró municipios/espacio. EVI, FAPAR y resúmenes de estrés tienen asociaciones parciales variables, no justifican sustituir automáticamente MayNDVI. Duración SAVI y ascenso LAI usan información hasta octubre y no equivalen a fecha observada de siembra ni duración fenológica validada.

## D. Historia2022–2024: bloque residual sólido, subconjunto compacto hipotético

RS2 distinguió39columnas históricas:24Sentinel y15climáticas. RS4 restringió a Sentinel24, eliminó8`months` constantes y conservó16variables efectivas. TOP15 se seleccionó dentro del outertrain con asociación al residuo climático generado mediante OOF interna.

**Semántica que requiere cuidado:** `HIST_S2_ndvi_promedio_mean` es la media de las siete medias históricas de mes calendario. Primero se promedian observaciones dentro de año/mes y luego los años2022–2024 para cada mes. `HIST_S2_ndvi_promedio_std` es la desviación muestral **entre esas siete medias mensuales históricas**; no variabilidad interanual. No permite identificar cuál año impulsó la señal. Los16nombres exactos y las150listas porbaseline/fold están en inventario y `history_top15_exact_fold_sets.csv`.

{md(freq[freq.feature.isin(g.HISTORY)])}

Ambas columnas NDVI aparecen en50/50folds de las tres bases, pero seleccionar15de16produce frecuencias altas por construcción; eso no prueba importancia individual. RS2 aporta asociación condicional e información no totalmente reconstruible desde clima: R² de reconstrucción0.259365(mean) y0.536457(std), Spearman condicional +0.178724/−0.184518, sujetos a la exploración retrospectiva. No se mide aquí un efecto causal.

RS4, cifras originales meanfold:

{md(rs4[['pipeline','baseline','architecture','RMSE','MAE','mean_delta_RMSE','fold_win_rate','repetitions_improved']])}

La historia residual mejoró consistentemente diez repeticiones frente a bases refinadas; la adición directa no conservó igual ganancia. RS1 tuvo una pequeña mejora directa con otra base/especificación, por lo que no corresponde decir que historia directa nunca ayuda. La conclusión depende de arquitectura y baseline. M usa otras anomalías/referencias mensuales: no es el mismo bloque HIST_S2 deRS4.

La mejora regional del bloque histórico en esas50particiones aleatorias no demuestra discriminación intraperfil ni transferencia municipal. No hay una ablación pareada suficiente que pruebe que el subconjunto NDVIhist mean/std recupera toda la ganancia de History16. Se propone ese par como **hipótesis compacta**, sin presentarlo como la mejor selección establecida ni importarle métricas del bloque completo.

## E. Topografía y territorio

RS5/RS6: corrección Ridge del bloqueTOPO_BASIC25 produjo una mejora pequeña aleatoria sobre clima+historia. La subfamilia slope14 conservó más utilidad que elevation11; no se demostró el mismo beneficio para cada estadístico individual. El mean-only deF5-04 es una hipótesis de reducción dimensional, no una ablación ya ganada. `slope_degrees` y `TOPO_BASIC_slope_mean` son numéricamente idénticos; se verifican como alias.

K5 slope residual mejora algunos RMSE pero no todos los MAE/territorios; su adición directa puede extrapolar peor. RelieveF4-E3 no mejoró la perspectiva local/general y TWI/TPI/curvaturaA siguen descriptivos. No sustituir esas mediciones deDEM por identidad de municipio, ni inferir agua disponible a partir deTWI. No entran coordenadas, estado, municipio, ID deperfil o categorías geológicas al kernel inicial.

## Clasificación de evidencia y contradicciones

Señal sólida dentro del ámbito evaluado: lluvia temporal y MayNDVI complementario; historiaSentinel como bloque residual aleatorio; slope básico como corrección pequeña aleatoria. Señal principalmente territorial: Tmin/Tmax, DTR y ciertas clases suelo/geología. Hipótesis compactas nuevas: historiaNDVI2, pendiente media1 y respuesta no lineal GP. No demostrado: beneficio universal de temperatura, de múltiples índices actuales, FPCA/PCA como mejora general ni de kernels más complejos.

Los estudios J–M y A–D imponen reservas de escala, soporte, geografía y concentración. Las ganancias espacialT1/T3 se distribuyen entre muchas parcelas del bloque3, pero dependen de esa región; enD omitirbloque3 revierteT3. La pérdida intraperfil y el intercepto jerárquico no justificaron complejidad general. Ninguna validación actual es confirmación independiente del descubrimiento de variables.

En F5 no se reabre screening ni se elige globalmente una lista por importanciaXGB. El inventario diferencia evidencia de bloque, columna, corrección y asociación. El diseño usa un núcleo compacto previo y exige controles con las mismas columnas para separar algoritmo/representación.
'''
    redundancy=f'''# F5 — Redundancia, soporte e identificabilidad

Se calcularon únicamente relaciones entre covariables existentes de138TRAIN. No se empleó Y para nuevos rankings, se usó PRED para seleccionar ni se ajustaron regresiones de reconstrucción nuevas. Las asociaciones conY citadas proceden de artefactos anteriores. `predictor_pearson_TRAIN138.csv` y `predictor_within_profile_pearson.csv` conservan las matrices; `high_redundancy_pairs.csv` identifica pares |r|≥0.9, criterio descriptivo, no eliminación supervisada automática.

{md(geometry)}

Lluvia7 contiene43vectores exactos entre etiquetas. Clima solo siempre asignará la misma media a parcelas con el mismo X; añadirWhiteKernel facilita el ruido/solución numérica, pero no aporta un predictor parcelario. No deduplicar observaciones conYdiferentes ni tratarlas como una única etiqueta sin un modelo explícito de agregación. MayNDVI/historia/pendiente pueden distinguir algunas parcelas, sin asegurar que resuelvan el residuo.

Redundancias deterministas: precip_mean=total/7; early+mid+late=total; precip_cv=std/mean, cuando no hay degeneración. C fracción temprana incorpora early/total y HHI concentración: no son una rotación lineal de meses ni información nueva de otra fuente. Evitar sumar resúmenes redundantes y meses sin una ablación planificada.

Históricos: cobertura`months`=7 en el bloqueSentinel, sin variación útil;mean/std no indican variabilidad interanual. NDVI/EVI/SAVI/LAI/FAPAR pueden repetir estructura de verdor. QueLAI deriveSAVI no significa correlación1 luego de agregaciones no lineales: media de transformación no es transformación de media. No usar bajas correlaciones aisladas como garantía de información incremental.

{md(candidate[candidate.column.isin(g.HISTORY+g.CORE+[g.SLOPE,g.c.DTR])][['column','period','incremental_evidence','stability','redundancy_risk']])}

Topografía: alias pendiente media exacto; estadísticas de elevación/pendiente correlacionadas y fuentes con escalaDEM120m. Elegir una media paraF5 es una restricción estructural hipotética, no prueba de suficiencia. La matriz de correlación global puede ocultar relaciones regionales; la matriz centrada porperfil usa solo perfiles repetidos para describir X. Variables climáticas constantes dentro delperfil producen varianza local0 y correlaciones indefinidas, no asociación local negativa ni ausencia de importancia regional.

Colinealidad enGP: distintos repartos de longitudes pueden inducir distancias similares; ARD no es un selector causal ni una prueba de relevancia. Nuestra restricción propuesta comparte longitud porbloque, excluye duplicados y normaliza dimensiones de bloque. No eliminar ejes automáticamente por correlación para después afirmar evaluación independiente.

![Redundancia candidata](../figures/candidate_redundancy.png)

![Selección histórica](../figures/history_selection_frequency.png)
'''
    proposal='''# F5 — Propuesta técnica para revisión

No se ha implementado ni entrenado un estimadorGPR. Se mantienen los65folds y sus particiones internas originales; las59PRED no participan como etiquetas. El diseño constituye una hipótesis nueva sobre representaciones anteriores, todavía exploratoria.

## Modelo y núcleo

y=m(X)+f(X)+ε, f~GP(0,k), ε~N(0,σn²). Se propone GPR exacto:138observaciones permiten un sistema pequeño; los costos crecen con refits/selección interna y con reconstrucción residual, no solo con el tamaño de un único kernel. Las fórmulas de regresión/media y su interpretación se fundamentan en [GPML, capítulo2](https://gaussianprocess.org/gpml/chapters/RW2.pdf). Esta viabilidad computacional no implica capacidad de generalización.

Primer núcleo: (compact_precip_total,compact_early_fraction,compact_concentration_hhi,S2_ndvi_month_05). Reutiliza exactamente C-T3: suma de7lluvias, fracciónabril–junio conepsilon1e−6mm, HHI mensual, MayNDVI exacto. No importamos automáticamente TOP20Climate/History15/TOPO25 delChampion.

Primer kernel Matérnν=3/2, νfijo. r²=||zP−zP′||²/(3ℓP²)+(zV−zV′)²/ℓV²; ksignal=a(1+√3r)exp(−√3r). Hay4hiperparámetros dekernel: amplituda, longitudesℓP/ℓV y varianza de ruido. Matérn permite elegir suavidad;RBF corresponde a una hipótesis más suave. νno se optimiza continuamente en la implementación de referencia. [DocumentaciónMatérn](https://scikit-learn.org/1.7/modules/generated/sklearn.gaussian_process.kernels.Matern.html).

Este kernel conjunto permite respuestas no aditivas suaves de lluvia/vegetación; no demuestra interacciones agronómicas. Longitud separada porvariable en el núcleo4elevaría a6losparámetros y se reserva como sensibilidad acotada. La escala de lluvia se comparte en3variables, evitando7longitudes mensuales más otras de historia/terreno. El número de parámetros propuesto es una restricción de diseño, no un umbral estadístico universal para n138.

## Comparaciones de kernels acotadas

Primario:Matérn3/2 con escalas porbloque. SensibilidadRBF sobre las mismas columnas y grupos; sensibilidadARD4variables solo para el mismo núcleo si la fase principal resulta viable. Una eventual elección entre estas especificaciones debe hacerse medianteCVinterna, nunca por el menorRMSE externo. No añadirMatérn5/2, combinaciones deν, rationalquadratic, nuevos bloques o pesos después de verOOF.

F5-05: k=kA(A,A′)+kH(H,H′)+kT(T,T′)+σn²I;A=lluvia3+MayNDVI,H=histNDVImean/std,T=pendiente_media. Cada término tiene una amplitud y una longitud:7parámetros, incluido ruido. El control conjunto debe usar **los mismos3bloques y normalización**, con3longitudes,1amplitud y1ruido=5parámetros. Así se contrasta estructura aditiva/junta; el control no es el kernel deF5-01 ampliado con un reparto distinto de longitudes.

Sumas y productos de kernels admiten covarianzas válidas; productos de funcionesGP no implican una funciónGP. [GPML, capítulo4](https://gaussianprocess.org/gpml/chapters/RW4.pdf). Separar funciones aditivas facilita interpretar contribuciones, pero no las vuelve causales ni necesariamente identificables cuando bloques se correlacionan. [Duvenaud etal., AdditiveGaussianProcesses](https://arxiv.org/abs/1112.4394).

Interacción limitada alternativa conceptual: kP+kV+aPV·kP·kV, longitudesP/V compartidas entre términos,3amplitudes+2longitudes+ruido=6parámetros. Se documenta para evaluar la hipótesis; no se añade a la batería primaria ni se ejecuta. F5-01 ya permite interacción conjunta sin construir productos de columnas adicionales.

## Escala, faltantes y media

Imputación mediana y escalado solo en cada entrenamiento. PisoNDVI0.05 como C; demás desviaciones con guarda1e−12 y constantes descartadas con registro. Dividir vector de cada bloque por√d limita que un bloque gane peso solo por tener más columnas. No escalar usando197parcelas. NormalizarY con media/desviación del entrenamiento correspondiente y restaurar unidades t/ha. Si un bloque es constante, registrar el kernel reducido efectivo, no reportar longitudes no identificables como relevancia.

Media inicial constante, con estadísticas deY de entrenamiento. Enscikit-learn, normalize_y centra/escalaY, no ajusta una media lineal. SuGPR optimiza el kernel por log-marginal-likelihood. [GuíaGP](https://scikit-learn.org/1.7/modules/gaussian_process.html). Una media lineal fija por entrenamiento podría conservar tendencia fuera del soporte, pero requiere controlar su ajuste/regularización: se deja para una fase posterior, evitando duplicar ahora núcleo/kernel/media.

UnDotProduct sumado alkernel representa una contribución lineal aleatoria a la covarianza, no la misma media lineal determinista. Media externaC-T3 aparece solo enF5-06 residual. Fuera del soporte, unkernel estacionario con covarianza decreciente vuelve hacia la media previa; no extrapola automáticamente una tendencia agrícola. Este comportamiento debe evaluarse especialmente en el bloque3; no se supone queGP resolverá la sobreestimación regional.

## Optimización futura limitada y diagnósticos

Propuesta: L-BFGS-B, uninicio fijo y2reinicios con seed2026; LML dentro del entrenamiento que corresponda. SobreYestandarizado: amplitud[0.01,100], longitud[0.2,20], ruido[0.001,2], inicios1/1/0.1 y jitter1e−8. Son límites e inicios propuestos para revisión, sin búsqueda ni ajuste ejecutados. Una longitud óptima en el límite debe declararse, no ampliar el rango retrospectivamente sin nueva versión.

El API permite bounds y reinicios; `alpha` yWhiteKernel son distintos. [GaussianProcessRegressor1.7](https://scikit-learn.org/1.7/modules/generated/sklearn.gaussian_process.GaussianProcessRegressor.html). La LML puede tener óptimos locales e intercambiar longitud corta/ruido alto o bajo; mayorLML no garantizaRMSEgeográfico menor. [GPML, capítulo5](https://gaussianprocess.org/gpml/chapters/RW5.pdf).

Registrar porfit: parámetros, LML, límites tocados, avisos deloptimizador, condición deK, fallasCholesky, jitterreal, tiempo, ntrain/perfiles, convergencia entre reinicios y dispersión de predicciones. No descartar automáticamente etiquetas ni usar errores para cambiarlas. Si la representación induce degeneración, suspender ese candidato y documentar la causa antes de crear otra formulación.

## Ruido, duplicados e incertidumbre

WhiteKernel modela varianza residual independiente; jitter pequeño estabiliza la diagonal numéricamente, no reemplaza ruido observacional. [WhiteKernel](https://scikit-learn.org/1.7/modules/generated/sklearn.gaussian_process.kernels.WhiteKernel.html). Mantener observaciones con climaigual yYdistinto: la media condicionada solo alclima coincide, yWhiteKernel absorbe discrepancias sin crear discriminación parcelaria. Dependencia de manejo/perfil no observado puede violar ese supuesto de ruido; los protocolos grupales lo ponen a prueba.

Reportar porseparado incertidumbre latente y predictiva deY: conWhiteKernel, la varianza devuelta puede incluir el ruido delkernel; identificar exactamente implementación/unidades. Para unkernel homoscedástico, varlatente=varpredictiva−σn², después de desnormalizar; `alpha` como jitter de entrenamiento no se añade automáticamente a la incertidumbre de una nueva observación. Verificar estas identidades matemáticamente en la futura implementación.

Intervalos plug-in omiten incertidumbre de selección/hiperparámetros, errores deX/Y y cambio de dominio. Evaluar cobertura90%, ancho y sesgo porperfil conocido/nuevo, municipio y bloque, sin asumir calibración. AntecedenteH1:77.9%de cobertura municipal nueva y mayorancho espacial. GPR no convierte ese problema en una garantía. La incertidumbre residual condicionada albase tampoco integra la incertidumbre ni covarianza deerror delbase.

## GPR residual: trazabilidad antes de complejidad

F5-06 propone primero C-T3 como media externa reproducible, usando exclusivamente cross-fitting interno. Dentro de outertrainA, para cada innertrainAi/validaciónBi: seleccionar y ajustarbase solo conAi; generar residuos deAi con sub-cross-fitting que no acceda aBi; ajustarGP a esosresiduos; sumar baseAi(Bi)+GPAi(Bi) y evaluarBi. Repetir íntegramente por opción interna. Una vez seleccionada configuración, generar residuosOOF internos deA conbases ajustadas sin cada heldout interno, ajustarbasefinal conA yGP con esosresiduos, evaluarouterVsinYusado. Mantener los65folds externos y lasparticiones internas disponibles; subparticiones adicionales requeridas se congelarán en la futura implementación.

No entrenar elGP con residuosglobalesOOF delChampion: sus predictores deoutertrain pueden haber vistoYdeoutervalidation u otro heldout relevante. Tampoco ajustar un corrector a residuosin-sample. No reutilizar los hiperparámetros delbase escogidos conBi al construir una predicción honesta deBi durante selección interna.

La variante sobreChampion completo permanece **suspendida para ejecución**: es necesario reconstruir sus3capas, ranking y selección de manera anidada hasta elnivel de entrenamiento delGP. RS5 `outer_train_residual2.parquet` corresponde albase clima+historia previo a la tercera corrección; no es suficiente para elChampionfinal. L8/F4-S7 ya documentaron este límite. No se propone un sustituto diferente bajo elnombreChampion. El coste mayor de esta variante es reconstruirbase, no resolverK de138.

## Validación y criterios propuestos

Reutilizar exactamente65folds y losIDs/innerpartitions congelados. Champion ymezcla solo se comparan donde hayOOFaleatoria compatible; no generar una validación geográfica ficticia. Métrica primaria:138OOFporrepetición, después media de10repeticiones;municipal/perfil/espacial porseparado. Conservar misma llave(ID,Y,protocolo,repeat,fold). Históricosmeanfold y métricas nuevasOOFno se juntan enunranking.

Primer objetivo propuesto: transferencia municipal deF5-01 frente aC-T3, conerror aleatorio/perfil/espacial e intraperfil como costos explícitos. Margen práctico tentativo0.01t/ha, para revisión: buscar≥0.01de mejoraRMSEmunicipal y no deteriorarRMSE/MAEdeotros escenarios más de0.01frente alcontrol comparable; mantener también F4-S1 como referencia de costo original. Este margen no tiene validación económica ni significancia estadística demostrada.

Exigir distribución de ganancias pormunicipio/bloque, sensibilidad de agregación alomitir cadafold, conservación de casosinfluyentes y proporción de mejoras. Almenos3/5folds municipales conganancia sería una guarda de estabilidad propuesta, no una prueba con cinco réplicas independientes. Si unbeneficio espacial se revierte alomitirbloque3, conservarlo solo como hipótesis regional. Diferencias locales: parejas del mismo ajuste externo, igualpeso porperfil y soporte real, sin pseudorreplicación.

No elegir“mejor núcleo anterior”usandoOOF externa. F5-03/04/05 se anclan al núcleo fijoF5-01. Si después se desea elegir representaciónmensual/compacta oDTR, la regla de selección completa debe estar dentro deCVinterna y evaluarse como otro procedimiento predefinido, no heredar globalmente unganador.

Escalado, medias, ranking, PCA eventualmente propuesto, parámetrosbase yGP se ajustan solo altrain pertinente. No se creaPCApredictiva enestaetapa. Las59PRED no eligen representaciones, hiperparámetros ni criterios. Nuevasetiquetas/regiones/campañas siguen necesarias para confirmación.
'''
    recommendation='''# F5 — Recomendación para la primera ejecución futura

**Primer candidato: F5-01, GPR exacto Matérn3/2 con lluvia compacta + NDVI Sentinel de mayo2025.** Cuatroentradas, cuatrohiperparámetros dekernel: amplitud, longitud de lluvia compartida, longitud NDVI y ruido. Mantener C-T3ElasticNet como control de idénticas variables y F5-00-Ccomo ablación de lluvia. No sustituir MayNDVI por uníndice anual ni comenzar con History15+TOPO25.

La evidencia más clara para esta elección es representacional: C-T3 tuvo la mayor ventaja municipal reciente con unnúcleo compacto, yMayNDVI aporta contraste parcelario dentro de perfiles dondeclima no distingue. La hipótesis nueva es que una respuesta suave conjunta pueda aprovechar mejor esas entradas que unmodelo lineal. **No tenemos resultados GPR que respalden superioridad.**

Prioridad siguiente: control mensualF5-00-M para vigilar pérdida de información temporal; después sensibilidadDTR, sin asumir que se combinará conNDVI. Cambiar Tmin de la propuesta original porDTR es una decisión de prioridad basada enG/H/F4/C, no una afirmación de que Tmin sea agronómicamenteirrelevante. Tmin permanece eninventario/reserva, sin añadir siete dimensiones al primerGP.

Historia: conservar todos los16nombres efectivos ylistasTOP15porfold como evidencia, pero probar elparNDVIhist nivel/estacionalidad solo como hipótesiscompacta. Su beneficio individual no equivale aldelbloqueresidualRS4. Topografía: comenzar, si corresponde, porpendiente_media; su utilidad conGPRdirecto tampoco estádemostrada.

Kernels aditivos yGP residual vienen después de controles simples. La variante residualsobreChampion permanece suspendida hasta disponer de reconstrucción honesta de sus3capas para cada entrenamientointerno. ElbaseC-T3es la opción residual verificable propuesta.

No se ejecutó ninguno de estos experimentos, no se llamó aloptimizador y no se generaron predicciones finales. La matriz y losmárgenes son una propuesta para revisión. Si se acepta la estructura, el siguiente trabajo será implementar una primera comparación acotadaF5-01/F5-00-C/C-T3 sobrelos65folds, con pruebas dekernel/ruido/cross-validation y sin abrir labatería completa automáticamente.
'''
    inventory_doc='# F5 — Inventario de variables candidatas\n\nLos11campossolicitados y elsoporte porcolumna se encuentran en [candidate_variable_inventory.csv](../tables/candidate_variable_inventory.csv). Incluye los16camposhistóricos efectivos, cobertura constante, lluvia7/10/3, variables térmicas, vegetación ytopografía. No es una nueva selección supervisada.\n\n'+md(candidate[candidate.column.isin(g.CORE+g.HISTORY+[g.SLOPE,g.c.DTR])])
    matrixdoc='# F5 — Matriz experimental propuesta, sin ejecutar\n\nOcho filas corresponden a siete familias numeradas: F5-00 tiene controles compacto y mensual. Todas permanecen propuestas para revisión. RBF/ARD se documentan como sensibilidades acotadas del mismo núcleo, no una expansión automática.\n\n'+md(matrix)
    reports=[('evidence_audit.md','family5_gpr_evidence_audit.md',audit),('candidate_inventory.md','family5_gpr_candidate_inventory.md',inventory_doc),('redundancy_analysis.md','family5_gpr_redundancy.md',redundancy),('technical_proposal.md','family5_gpr_technical_proposal.md',proposal),('experimental_matrix.md','family5_gpr_experimental_matrix.md',matrixdoc),('recommendation.md','family5_gpr_recommendation.md',recommendation)]
    for name,doc,text in reports:
        text=prose(text)
        (g.OUT/'report'/name).write_text(text,encoding='utf8')
        document=text.replace('../figures/','../'+(g.OUT/'figures').relative_to(g.ROOT).as_posix()+'/').replace('../tables/candidate_variable_inventory.csv','../'+(g.OUT/'tables/candidate_variable_inventory.csv').relative_to(g.ROOT).as_posix()).replace('../../../../family_4/','../outputs/research/family_4/')
        (g.ROOT/'documentation'/doc).write_text(document,encoding='utf8')
    print('F5 six documentary deliverables ready',flush=True)
