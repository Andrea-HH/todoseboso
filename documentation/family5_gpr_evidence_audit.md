> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# F5 — Auditoría transversal de evidencia para diseñar GPR

Estado: **propuesta para revisión; modelos F5 no ejecutados**. Se recuperan resultados originales y se realizan únicamente verificaciones de semántica, agregación OOF archivada y redundancia entre X. No se entrena, optimiza, selecciona nuevas variables mediante Y, ni predicen las 59 PRED. Toda señal identificada sigue siendo exploratoria sobre las mismas 138 etiquetas.

## Alcance y trazabilidad

138 TRAIN, 59 PRED, 197 parcelas; 43 perfiles etiquetados, 12 repetidos y 53 en el universo completo. Se revisan lluvia E1–E8, G/H y extensión PCR, RS1–RS6, Champion, J/K/L/M, Familias 2/3, screening1473, F4/F4-E y A–D. Se reutilizan inventario de 228 series históricas y diagnósticos D; no se duplican sus pipelines. `audit/protected_inputs.csv` registra fuentes y hashes; `audit/technical_primary_sources.csv` documenta bibliografía técnica.

El inventario anterior está en [Etapa D](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_d/tables/model_inventory.csv). Los archivos se identifican mediante rutas desde la raíz y hashes en el inventario F5. Familias2/3 no justificaron mayor complejidad funcional/estructural; esas conclusiones no prueban que todos los kernels fallen. Suelo/geología250k aportan descripciones, sin contribución incremental estable; no entran al núcleo inicial. La cartografía local50k suspendida no se reabre.

## A. Lluvia: señal fuerte, representación y agregación importan

RS3 `ONLY_PRECIPITATION_XGB` usa **10 resúmenes CLIMATE_precip_**, no siete valores mensuales. RS4 `PRECIPITATION_XGB` es la referencia reconstruida correspondiente. El nombre solicitado `PRECIPITATION_ONLY_XGB` no se encontró exactamente en CSV/MD/PY; se conserva esa limitación en `requested_identifier_resolution.csv`, sin inventar un alias validado.

RS3 mostró que total solo y timing solo pierden frente al bloque completo. La ventana temprana RS3 incluye cinco variables climáticas de abril–junio, no solamente `CLIMATE_precip_early_sum`; su mejor resultado no demuestra que un único acumulado sea suficiente. No hay ablación aislada que pruebe que ese acumulado, por sí mismo, sea la variable óptima para GPR.

Las cifras RS3/RS4 publicadas son medias de RMSE de folds y se preservan. Se recomputan también métricas sobre138 OOF completas por repetición, sin reentrenar:

| index | stage | experiment | protocol | source | RMSE | MAE | bias | n | n_repeats |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | RS3 | ONLY_PRECIPITATION_XGB | random | outputs/modeling/residual_signal_audit/stage3_climate/checkpoints/rs3_oof_predictions.parquet | 0.51312 | 0.36432 | 0.00936 | 138 | 10 |
| 9 | RS4 | PRECIPITATION_XGB_BASE | random | outputs/modeling/residual_signal_audit/stage4_champion_reconstruction/predictions/oof_predictions.parquet | 0.51312 | 0.36432 | 0.00936 | 138 | 10 |
| 11 | RS4 | PRECIPITATION_XGB_HISTORY15 | random | outputs/modeling/residual_signal_audit/stage4_champion_reconstruction/predictions/oof_predictions.parquet | 0.50114 | 0.36243 | -0.01117 | 138 | 10 |
| 14 | RS4 | TOP20_ENET_DIRECT_HISTORY24 | random | outputs/modeling/residual_signal_audit/stage4_champion_reconstruction/predictions/oof_predictions.parquet | 0.51517 | 0.37108 | 0.00060 | 138 | 10 |
| 15 | RS4 | TOP20_ENET_HISTORY15 | random | outputs/modeling/residual_signal_audit/stage4_champion_reconstruction/predictions/oof_predictions.parquet | 0.50111 | 0.35615 | -0.00632 | 138 | 10 |
| 17 | RS6 | A_CURRENT_CH_H_T | random | outputs/modeling/residual_signal_audit/stage6_architecture_optimization/predictions/oof_predictions.parquet | 0.49813 | 0.35887 | 0.00183 | 138 | 10 |

Los valores archivados de RS3 —incluidos total/timing/ventanas— permanecen en `archived_01_RS3.csv` y `archived_03_RS3.csv`. Una cifra distinta de la documentación puede deberse a agregación, no a cambio del modelo. RS6 Champion 0.486505 de mediafold y aproximadamente0.498127 de OOF completa son medidas diferentes.

Lluvia7, frente a total solo y alternativas agregadas, bajo los65 folds:

| index | experiment | protocol | RMSE_mean | MAE_mean |
| --- | --- | --- | --- | --- |
| 1 | E1_TOTAL_LINEAR | climate_profile | 0.84048 | 0.70039 |
| 4 | E3_MONTHLY_RIDGE | climate_profile | 0.53357 | 0.38585 |
| 5 | E4_SUMMARY_RIDGE | climate_profile | 0.54268 | 0.41358 |
| 7 | E5_DYNAMICS_RIDGE | climate_profile | 0.55235 | 0.42130 |
| 14 | E1_TOTAL_LINEAR | municipality | 1.01004 | 0.88483 |
| 17 | E3_MONTHLY_RIDGE | municipality | 0.68920 | 0.50464 |
| 18 | E4_SUMMARY_RIDGE | municipality | 0.63605 | 0.48387 |
| 20 | E5_DYNAMICS_RIDGE | municipality | 0.66996 | 0.51397 |
| 27 | E1_TOTAL_LINEAR | random | 0.75917 | 0.62497 |
| 30 | E3_MONTHLY_RIDGE | random | 0.52375 | 0.37157 |
| 31 | E4_SUMMARY_RIDGE | random | 0.53745 | 0.39892 |
| 33 | E5_DYNAMICS_RIDGE | random | 0.53889 | 0.39679 |
| 40 | E1_TOTAL_LINEAR | spatial | 0.91316 | 0.76889 |
| 43 | E3_MONTHLY_RIDGE | spatial | 0.78430 | 0.60607 |
| 44 | E4_SUMMARY_RIDGE | spatial | 1.17551 | 0.96745 |
| 46 | E5_DYNAMICS_RIDGE | spatial | 0.71065 | 0.55851 |

La representación compacta C total/fracción temprana/HHI con NDVI de mayo tiene la mejor evidencia municipal reciente. No es el mismo resumen que E4/H_S1: esos resultados no son intercambiables. C-T3 mejora municipio, con costo aleatorio y dependencia espacial del bloque 3; total solo no reemplaza la distribución temporal.

## B. Temperatura: diferenciación territorial no equivale a utilidad incremental

La fuente verificada de Tmin/Tmax es **CHIRTS-ERA5**, resolución0.05°, extracción fraccional canónica. El diccionario antiguo `CHIRPS_OR_WORLDCLIM` es genérico e inexacto; G ya lo corrigió mediante etiquetas deTIFF/LEEME en `report/source_audit.json`, preservando el archivo anterior. El inventarioF5 usa la fuente corregida, no atribuye temperatura aWorldClim.

| index | experiment | protocol | RMSE_mean | MAE_mean |
| --- | --- | --- | --- | --- |
| 1 | H1_RAIN | climate_profile | 0.54435 | 0.39035 |
| 2 | H2_TMIN | climate_profile | 0.58714 | 0.45089 |
| 3 | H3_TMAX | climate_profile | 0.54093 | 0.39826 |
| 5 | H5_RAIN_TMIN | climate_profile | 0.55703 | 0.40838 |
| 6 | H6_RAIN_TMAX | climate_profile | 0.54910 | 0.41325 |
| 15 | H1_RAIN | municipality | 0.69536 | 0.50022 |
| 16 | H2_TMIN | municipality | 1.04558 | 0.92624 |
| 17 | H3_TMAX | municipality | 1.16297 | 1.02911 |
| 19 | H5_RAIN_TMIN | municipality | 0.72078 | 0.54875 |
| 20 | H6_RAIN_TMAX | municipality | 0.76679 | 0.57075 |
| 29 | H1_RAIN | random | 0.52136 | 0.36946 |
| 30 | H2_TMIN | random | 0.58417 | 0.43631 |
| 31 | H3_TMAX | random | 0.53703 | 0.38697 |
| 33 | H5_RAIN_TMIN | random | 0.52205 | 0.37079 |
| 34 | H6_RAIN_TMAX | random | 0.52011 | 0.37184 |
| 43 | H1_RAIN | spatial | 0.73479 | 0.56199 |
| 44 | H2_TMIN | spatial | 0.76138 | 0.61022 |
| 45 | H3_TMAX | spatial | 1.29947 | 1.09164 |
| 47 | H5_RAIN_TMIN | spatial | 0.74515 | 0.59619 |
| 48 | H6_RAIN_TMAX | spatial | 0.96014 | 0.76463 |

Tmin tiene estructura territorial y altitudinal descriptiva, pero no debe decirse que estado+altitud la explican completamente: correlaciones y separación no son una atribución causal ni una garantía de redundancia. Añadir siete Tmin no mejora de forma general H1. Tmax mejora RMSE aleatoria solo marginalmente, mientras empeora MAE y transferencia regional. La temperatura no subdivide los53 perfiles exactos de lluvia.

| index | experiment | protocol | RMSE_mean | MAE_mean |
| --- | --- | --- | --- | --- |
| 4 | H_EXT_CACHED_RAIN_PCR | climate_profile | 0.51750 | 0.37191 |
| 5 | H_EXT_RAIN_TMAX_PCR | climate_profile | 0.51639 | 0.37735 |
| 10 | H_EXT_CACHED_RAIN_PCR | municipality | 0.88405 | 0.60277 |
| 11 | H_EXT_RAIN_TMAX_PCR | municipality | 0.93796 | 0.64163 |
| 16 | H_EXT_CACHED_RAIN_PCR | random | 0.52380 | 0.37255 |
| 17 | H_EXT_RAIN_TMAX_PCR | random | 0.51617 | 0.36593 |
| 22 | H_EXT_CACHED_RAIN_PCR | spatial | 0.76978 | 0.56807 |
| 23 | H_EXT_RAIN_TMAX_PCR | spatial | 0.93078 | 0.77054 |

PCR lluvia+Tmax mejora ciertos resultados aleatorios/por perfil pero no municipal/espacial: reducir dimensiones no elimina los límites de transferencia. Los 98% de varianza térmica explicados por PCs describen X, no rendimiento.

DTRstd es una candidata térmica más concreta que Tmin para una sensibilidad compacta, por F4-S5/C-T1, pero **no** se presume beneficio con NDVI de mayo: C-T2/C-T4 no combinaron sus fortalezas lineales. DTRstd mide desviación muestral de siete medias mensuales Tmax−Tmin, no Tmax media. Su señal espacial depende del bloque 3. F5-02 probaría una interacción suave todavía hipotética.

## C. Vegetación2025: preservar la señal puntual correcta

`S2_ndvi_month_05`: Sentinel-2, media aritmética de observaciones válidas de `ndvi_promedio` de cada parcela durante mayo2025. Es una media temporal de promedios parcelarios suministrados; no máximo, q10, promedio abril–octubre ni NDVI de Planet. El código `src/family_1/m_satellite.py` genera el campo; `semantic_checks.json` verifica sus valores contra la serie nativa. No se conoce una regla universal que garantice la misma fase de cultivo en todas las parcelas.

F4-S1 usa lluvia7+NDVI de mayo, con imputación/escala solo de entrenamiento y piso NDVI0.05. Mejoró aleatoria/perfil/municipio frente a lluvia en la formulación evaluada; la mejora espacial general no es uniforme. El screening de NDVI solo fue inferior a lluvia: señal complementaria no significa predictor suficiente.

| index | experiment | protocol | RMSE | MAE |
| --- | --- | --- | --- | --- |
| 8 | C-H0M | climate_profile | 0.51777 | 0.38212 |
| 9 | C-H0M | municipality | 0.63945 | 0.47859 |
| 10 | C-H0M | random | 0.50945 | 0.36840 |
| 11 | C-H0M | spatial | 0.67244 | 0.52226 |
| 12 | C-T1 | climate_profile | 0.56029 | 0.40777 |
| 13 | C-T1 | municipality | 0.68540 | 0.51500 |
| 14 | C-T1 | random | 0.52412 | 0.37360 |
| 15 | C-T1 | spatial | 0.60047 | 0.44654 |
| 16 | C-T3 | climate_profile | 0.52060 | 0.39150 |
| 17 | C-T3 | municipality | 0.58126 | 0.46033 |
| 18 | C-T3 | random | 0.51158 | 0.37495 |
| 19 | C-T3 | spatial | 0.67878 | 0.53061 |
| 21 | F4-E2 | climate_profile | 0.53333 | 0.39454 |
| 22 | F4-E2 | municipality | 0.67500 | 0.49993 |
| 23 | F4-E2 | random | 0.50561 | 0.36368 |
| 24 | F4-E2 | spatial | 0.73845 | 0.57336 |
| 25 | F4-S1 | climate_profile | 0.52626 | 0.38889 |
| 26 | F4-S1 | municipality | 0.67110 | 0.49856 |
| 27 | F4-S1 | random | 0.50483 | 0.36411 |
| 28 | F4-S1 | spatial | 0.73904 | 0.57291 |

F4-E2 añade inicio del mayor ascenso LAI: beneficio local pequeño, sin mejora global uniforme. LAI se calcula desde SAVI por la ecuaciónFIRA; no es otra fuente espectral. LAIq10 reemplazando NDVI de mayo deterioró municipios/espacio. EVI, FAPAR y resúmenes de estrés tienen asociaciones parciales variables, no justifican sustituir automáticamente NDVI de mayo. Duración SAVI y ascenso LAI usan información hasta octubre y no equivalen a fecha observada de siembra ni duración fenológica validada.

## D. Historia2022–2024: bloque residual sólido, subconjunto compacto hipotético

RS2 distinguió39 columnas históricas:24 Sentinel y15climáticas. RS4 restringió a Sentinel24, eliminó8`months` constantes y conservó16 variables efectivas. TOP15 se seleccionó dentro del outer-train con asociación al residuo climático generado mediante OOF interna.

**Semántica que requiere cuidado:** `HIST_S2_ndvi_promedio_mean` es la media de las siete medias históricas de mes calendario. Primero se promedian observaciones dentro de año/mes y luego los años2022–2024 para cada mes. `HIST_S2_ndvi_promedio_std` es la desviación muestral **entre esas siete medias mensuales históricas**; no variabilidad interanual. No permite identificar cuál año impulsó la señal. Los16nombres exactos y las150 listas por baseline/fold están en inventario y `history_top15_exact_fold_sets.csv`.

| index | baseline | feature | n_selected | n_outer | frequency | n_unique_sets | selection | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | CLIMATE_ENET | HIST_S2_ndvi_promedio_mean | 50 | 50 | 1.00000 | 13 | supervised abs Spearman with outer-train innerOOF climate residual; varies byfold | outputs/modeling/residual_signal_audit/stage4_champion_reconstruction/models/selected_hyperparameters.csv |
| 11 | CLIMATE_ENET | HIST_S2_ndvi_promedio_std | 50 | 50 | 1.00000 | 13 | supervised abs Spearman with outer-train innerOOF climate residual; varies byfold | outputs/modeling/residual_signal_audit/stage4_champion_reconstruction/models/selected_hyperparameters.csv |
| 26 | PRECIPITATION_XGB | HIST_S2_ndvi_promedio_mean | 50 | 50 | 1.00000 | 12 | supervised abs Spearman with outer-train innerOOF climate residual; varies byfold | outputs/modeling/residual_signal_audit/stage4_champion_reconstruction/models/selected_hyperparameters.csv |
| 27 | PRECIPITATION_XGB | HIST_S2_ndvi_promedio_std | 50 | 50 | 1.00000 | 12 | supervised abs Spearman with outer-train innerOOF climate residual; varies byfold | outputs/modeling/residual_signal_audit/stage4_champion_reconstruction/models/selected_hyperparameters.csv |
| 42 | TOP20_ENET | HIST_S2_ndvi_promedio_mean | 50 | 50 | 1.00000 | 11 | supervised abs Spearman with outer-train innerOOF climate residual; varies byfold | outputs/modeling/residual_signal_audit/stage4_champion_reconstruction/models/selected_hyperparameters.csv |
| 43 | TOP20_ENET | HIST_S2_ndvi_promedio_std | 50 | 50 | 1.00000 | 11 | supervised abs Spearman with outer-train innerOOF climate residual; varies byfold | outputs/modeling/residual_signal_audit/stage4_champion_reconstruction/models/selected_hyperparameters.csv |

Ambas columnas NDVI aparecen en50/50 folds de las tres bases, pero seleccionar15de16produce frecuencias altas por construcción; eso no prueba importancia individual. RS2 aporta asociación condicional e información no totalmente reconstruible desde clima: R² de reconstrucción0.259365(mean) y0.536457(std), Spearman condicional +0.178724/−0.184518, sujetos a la exploración retrospectiva. No se mide aquí un efecto causal.

RS4, cifras originales media de folds:

| index | pipeline | baseline | architecture | RMSE | MAE | mean_delta_RMSE | fold_win_rate | repetitions_improved |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | TOP20_ENET_HISTORY15 | TOP20_ENET | residual15 | 0.48955 | 0.35617 | -0.01570 | 0.76000 | 10 |
| 1 | TOP20_ENET_HISTORY24 | TOP20_ENET | residual24 | 0.48963 | 0.35628 | -0.01562 | 0.78000 | 10 |
| 2 | PRECIPITATION_XGB_HISTORY15 | PRECIPITATION_XGB | residual15 | 0.49027 | 0.36246 | -0.01248 | 0.76000 | 10 |
| 3 | PRECIPITATION_XGB_HISTORY24 | PRECIPITATION_XGB | residual24 | 0.49095 | 0.36297 | -0.01180 | 0.76000 | 10 |
| 4 | CLIMATE_ENET_HISTORY24 | CLIMATE_ENET | residual24 | 0.49423 | 0.35964 | -0.01591 | 0.80000 | 10 |
| 5 | CLIMATE_ENET_HISTORY15 | CLIMATE_ENET | residual15 | 0.49467 | 0.35994 | -0.01548 | 0.80000 | 10 |
| 6 | PRECIPITATION_XGB_BASE | PRECIPITATION_XGB | climate | 0.50275 | 0.36445 | 0.00000 | 0.00000 | 0 |
| 7 | TOP20_ENET_BASE | TOP20_ENET | climate | 0.50525 | 0.36654 | 0.00000 | 0.00000 | 0 |
| 8 | TOP20_ENET_DIRECT_HISTORY24 | TOP20_ENET | direct24 | 0.50527 | 0.37111 | 0.00003 | 0.54000 | 6 |
| 9 | PRECIPITATION_XGB_DIRECT_HISTORY24 | PRECIPITATION_XGB | direct24 | 0.50902 | 0.38187 | 0.00627 | 0.44000 | 3 |
| 10 | CLIMATE_ENET_BASE | CLIMATE_ENET | climate | 0.51015 | 0.37094 | 0.00000 | 0.00000 | 0 |

La historia residual mejoró consistentemente diez repeticiones frente a bases refinadas; la adición directa no conservó igual ganancia. RS1 tuvo una pequeña mejora directa con otra base/especificación, por lo que no corresponde decir que historia directa nunca ayuda. La conclusión depende de arquitectura y baseline. M usa otras anomalías/referencias mensuales: no es el mismo bloque HIST_S2 deRS4.

La mejora regional del bloque histórico en esas50 particiones aleatorias no demuestra discriminación intraperfil ni transferencia municipal. No hay una ablación pareada suficiente que pruebe que el subconjunto NDVIhist mean/std recupera toda la ganancia de History16. Se propone ese par como **hipótesis compacta**, sin presentarlo como la mejor selección establecida ni importarle métricas del bloque completo.

## E. Topografía y territorio

RS5/RS6: corrección Ridge del bloqueTOPO_BASIC25 produjo una mejora pequeña aleatoria sobre clima+historia. La subfamilia slope14 conservó más utilidad que elevation11; no se demostró el mismo beneficio para cada estadístico individual. El mean-only deF5-04 es una hipótesis de reducción dimensional, no una ablación ya ganada. `slope_degrees` y `TOPO_BASIC_slope_mean` son numéricamente idénticos; se verifican como alias.

K5 slope residual mejora algunos RMSE pero no todos los MAE/territorios; su adición directa puede extrapolar peor. RelieveF4-E3 no mejoró la perspectiva local/general y TWI/TPI/curvaturaA siguen descriptivos. No sustituir esas mediciones deDEM por identidad de municipio, ni inferir agua disponible a partir deTWI. No entran coordenadas, estado, municipio, ID deperfil o categorías geológicas al kernel inicial.

## Clasificación de evidencia y contradicciones

Señal sólida dentro del ámbito evaluado: lluvia temporal y NDVI de mayo complementario; historiaSentinel como bloque residual aleatorio; slope básico como corrección pequeña aleatoria. Señal principalmente territorial: Tmin/Tmax, DTR y ciertas clases suelo/geología. Hipótesis compactas nuevas: historiaNDVI2, pendiente media1 y respuesta no lineal GP. No demostrado: beneficio universal de temperatura, de múltiples índices actuales, FPCA/PCA como mejora general ni de kernels más complejos.

Los estudios J–M y A–D imponen reservas de escala, soporte, geografía y concentración. Las ganancias espacialT1/T3 se distribuyen entre muchas parcelas del bloque 3, pero dependen de esa región; enD omitirbloque 3 revierteT3. La pérdida intraperfil y el intercepto jerárquico no justificaron complejidad general. Ninguna validación actual es confirmación independiente del descubrimiento de variables.

En F5 no se reabre screening ni se elige globalmente una lista por importanciaXGB. El inventario diferencia evidencia de bloque, columna, corrección y asociación. El diseño usa un núcleo compacto previo y exige controles con las mismas columnas para separar algoritmo/representación.
