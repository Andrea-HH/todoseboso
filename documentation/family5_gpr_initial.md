> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# F5-00-C / F5-01 — Ejecución inicial controlada de GPR

## Resultado y alcance

GPR Matérn3/2 mejora algunos escenarios respecto al Elastic Net de idénticas variables, con costo espacial material. El resultado fortalece parcialmente una respuesta no lineal compacta y el aporte de NDVI dentro de esta familia; no demuestra superioridad universal. Se mantiene Champion sin cambios y se dejan F5-02–06 y F5-00-M sin ejecutar.

`frozen_execution_design.json` se escribió antes del primer ajuste. Se reutilizó `c_features_197_target_free.parquet`, 138 TRAIN y los65folds/particiones internas originales. PRED59 quedó sin predicciones ni etiquetas utilizadas. Se verificaron las fuentes protegidas del diseño y etapas anteriores antes de comenzar.

## Kernel, transformaciones y optimización

F5-00-C: tres variables de lluvia compacta, una longitud compartida. F5-01: mismas tres variables y `S2_ndvi_month_05`, con longitud NDVI independiente. ConstantKernel×GroupedMatern32+WhiteKernel; ν=1.5 fijo. Tres/cuatro parámetros libres respectivamente, salvo grupos no identificables por constantes de entrenamiento.

La clase GroupedMatern32 expone un parámetro por grupo: no se limita a iniciar tres longitudes independientes con el mismo valor. Para lluvia r² suma tres distancias escaladas y se divide entre3; NDVI usa su distancia aparte. Los gradientes respecto a log-longitud suman las derivadas de los ejes del grupo. Se verifican contra Matérn convencional expandido y diferencias finitas del kernel completo.

Se reutiliza ConditionalFeatures: mediana, media, desviación y descarte de constantes solo en train; piso NDVI0.05. Los ejes activos de cada bloque se dividen por√dimensión activa; con las matrices observadas reproduce √3 lluvia y1 NDVI. GPR normalize_y usa media y SD de Ytrain exclusivamente. Se conservan estadísticas y se restauran media, desviaciones y varianzas a t/ha y (t/ha)².

Límites congelados: amplitud[0.01,100], longitudes[0.2,20], varianza de ruido[0.001,2] en escalaYnormalizada; jitter1e−8; iniciales1/1/0.1; L-BFGS-B con dos reinicios adicionales, seed2026. Ningún rango fue ampliado. El optimizador usa los defaults de SciPy, con logs de terminación, gradiente, evaluaciones, tiempo y cada inicio. WhiteKernel es ruido estimado; jitter es estabilización numérica adicional.

No hay opción discreta nueva para elegir: las4particiones internas se ajustaron con la misma especificación para diagnóstico. Cada fit optimiza LML exclusivamente en su propio entrenamiento. La OOF interna no se usó para modificar kernel, límites, columnas ni criterios después de ver resultados. Los520ajustes internos se guardan por separado de130externos. Todos sus modelos/transformaciones/IDs y diagnósticos son reproducibles.

## Métricas y controles

C-T3 utiliza exactamente lluvia compacta3+MayNDVI y los mismos65folds. Se recuperaron sus modelos/OOF originales; replay diferencia máxima≤1e−12. No se volvió a seleccionar su regularización. Su procedimiento de selección interna original permanece como parte del control; GP usaLML, por lo que el contraste cambia familia de función/regularización, manteniendo las entradas y evaluación.

Primaria: métricas sobre138OOF completas de cada repetición, luego media de10repeticiones aleatorias. Perfil/municipio/espacio tienen una repetición cada uno. Sesgo=predicho−observado. Tablas porfold son diagnósticas y no sustituyen esa agregación.

| index | experiment | protocol | RMSE | MAE | bias | RMSE_sd_repeats | n | n_repeats |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | C-T3 | climate_profile | 0.52060 | 0.39150 | 0.00459 | nan | 138 | 1 |
| 1 | C-T3 | municipality | 0.58126 | 0.46033 | -0.02033 | nan | 138 | 1 |
| 2 | C-T3 | random | 0.51158 | 0.37495 | 0.00053 | 0.00600 | 138 | 10 |
| 3 | C-T3 | spatial | 0.67878 | 0.53061 | 0.19116 | nan | 138 | 1 |
| 4 | F5-00-C | climate_profile | 0.51885 | 0.36909 | -0.01200 | nan | 138 | 1 |
| 5 | F5-00-C | municipality | 0.55341 | 0.39887 | 0.04496 | nan | 138 | 1 |
| 6 | F5-00-C | random | 0.51530 | 0.36354 | 0.00556 | 0.00554 | 138 | 10 |
| 7 | F5-00-C | spatial | 0.79047 | 0.58996 | 0.27169 | nan | 138 | 1 |
| 8 | F5-01 | climate_profile | 0.49976 | 0.36237 | 0.00221 | nan | 138 | 1 |
| 9 | F5-01 | municipality | 0.54421 | 0.38894 | 0.02103 | nan | 138 | 1 |
| 10 | F5-01 | random | 0.50401 | 0.36156 | -0.00027 | 0.00561 | 138 | 10 |
| 11 | F5-01 | spatial | 0.73480 | 0.54194 | 0.28501 | nan | 138 | 1 |

Comparaciones pareadas: ΔRMSE/MAE=candidato−control (negativo favorece candidato); gananciaSSE=control−candidato (positivo favorece candidato). IDs/Y/protocolo/repetición/fold coinciden uno a uno.

| index | candidate | baseline | protocol | delta_RMSE | delta_MAE | SSE_gain | fraction_SE_improve | fraction_AE_improve |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | F5-00-C | C-T3 | climate_profile | -0.00175 | -0.02241 | 0.25151 | 0.56522 | 0.56522 |
| 1 | F5-00-C | C-T3 | municipality | -0.02784 | -0.06146 | 4.36008 | 0.64493 | 0.64493 |
| 2 | F5-00-C | C-T3 | random | 0.00371 | -0.01141 | -0.52566 | 0.56304 | 0.56304 |
| 3 | F5-00-C | C-T3 | spatial | 0.11169 | 0.05935 | -22.64544 | 0.46377 | 0.46377 |
| 4 | F5-01 | C-T3 | climate_profile | -0.02085 | -0.02913 | 2.93524 | 0.62319 | 0.62319 |
| 5 | F5-01 | C-T3 | municipality | -0.03705 | -0.07139 | 5.75456 | 0.69565 | 0.69565 |
| 6 | F5-01 | C-T3 | random | -0.00758 | -0.01339 | 1.06234 | 0.60725 | 0.60725 |
| 7 | F5-01 | C-T3 | spatial | 0.05602 | 0.01132 | -10.92770 | 0.55797 | 0.55797 |
| 8 | F5-01 | F5-00-C | climate_profile | -0.01909 | -0.00672 | 2.68373 | 0.48551 | 0.48551 |
| 9 | F5-01 | F5-00-C | municipality | -0.00921 | -0.00993 | 1.39449 | 0.52899 | 0.52899 |
| 10 | F5-01 | F5-00-C | random | -0.01129 | -0.00199 | 1.58800 | 0.50217 | 0.50217 |
| 11 | F5-01 | F5-00-C | spatial | -0.05567 | -0.04803 | 11.71773 | 0.67391 | 0.67391 |

En aleatoria, las diferencias SSE se resumen primero por repetición; influencia usa pérdida media por parcela entre las10repeticiones, no1380parcelas independientes. Las repeticiones/folds/modelos son dependientes. No se realizan pruebas masivas ni se interpretan estas diferencias como significancia confirmatoria.

## Heterogeneidad intraperfil

| index | experiment | protocol | n_pairs | n_profiles | n_parcels | equal_profile_RMSE | equal_profile_MAE | pair_weighted_RMSE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | C-T3 | climate_profile | 1073.00000 | 12.00000 | 107.00000 | 0.54789 | 0.40197 | 0.76338 |
| 3 | C-T3 | municipality | 1034.00000 | 12.00000 | 103.00000 | 0.52099 | 0.35217 | 0.76884 |
| 6 | C-T3 | random | 208.40000 | 8.60000 | 87.70000 | 0.58995 | 0.43574 | 0.77118 |
| 9 | C-T3 | spatial | 1007.00000 | 12.00000 | 106.00000 | 0.54015 | 0.38376 | 0.76754 |
| 12 | F5-00-C | climate_profile | 1073.00000 | 12.00000 | 107.00000 | 0.54299 | 0.37419 | 0.79926 |
| 15 | F5-00-C | municipality | 1034.00000 | 12.00000 | 103.00000 | 0.51890 | 0.32593 | 0.80606 |
| 18 | F5-00-C | random | 208.40000 | 8.60000 | 87.70000 | 0.61041 | 0.42761 | 0.80449 |
| 21 | F5-00-C | spatial | 1007.00000 | 12.00000 | 106.00000 | 0.53303 | 0.35413 | 0.80795 |
| 24 | F5-01 | climate_profile | 1073.00000 | 12.00000 | 107.00000 | 0.53183 | 0.37793 | 0.77366 |
| 27 | F5-01 | municipality | 1034.00000 | 12.00000 | 103.00000 | 0.53882 | 0.35505 | 0.81860 |
| 30 | F5-01 | random | 208.40000 | 8.60000 | 87.70000 | 0.60221 | 0.43936 | 0.78677 |
| 33 | F5-01 | spatial | 1007.00000 | 12.00000 | 106.00000 | 0.53190 | 0.36141 | 0.78903 |

Cada pareja proviene de un mismo ajuste externo y perfil climático. Igual peso por perfil evita que dos perfiles grandes dominen el diagnóstico; se conserva también ponderación por parejas y perspectivas dentro/fuera deChignahuapan. El soporte no es igual entre protocolos. Parejas solapadas no son réplicas independientes ni todas las posibles parejas son evaluables aleatoriamente por el mismo modelo.

F5-00-C no distingue medias de parcelas con lluvia compacta idéntica. WhiteKernel admite etiquetas distintas y regulariza la covarianza; no crea una característica parcelaria. NDVI permite diferencias condicionadas al clima y una respuesta no lineal, pero no necesariamente corrige todo el error local. Las tablas porperfil reportan n real y los dos perfiles dominantes; no se declara error irreducible.

NDVI no aporta una mejora local uniforme: frente aGPlluvia, mejoraRMSE de diferencias aleatoria/perfil/espacio, pero enmunicipal empeora0.518899→0.538821. Frente aC-T3, lasdiferencias empeoran aleatoria0.589951→0.602212 ymunicipal0.520989→0.538821, mientras mejoran perfil0.547885→0.531827 yespacio0.540147→0.531899. El RMSE ponderado porparejas sigue siendo peor queC-T3 enloscuatro protocolos. No debe describirse la reducción global como solución de la heterogeneidad dominante deChignahuapan.

## Transferencia y bloque espacial3

| index | baseline | fold | n | SSE_gain | delta_RMSE | delta_MAE | bias_candidate | bias_base | bias_squared_gain | error_variance_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 60 | C-T3 | 1 | 38 | -0.89047 | 0.02267 | -0.01306 | 0.00781 | -0.03690 | 0.04943 | -0.93990 |
| 61 | C-T3 | 2 | 37 | 0.35441 | -0.00843 | -0.02843 | 0.00482 | -0.11929 | 0.52568 | -0.17127 |
| 62 | C-T3 | 3 | 35 | -15.47776 | 0.21716 | 0.22484 | 1.01614 | 0.71820 | -18.08548 | 2.60773 |
| 63 | C-T3 | 4 | 18 | 4.56802 | -0.17882 | -0.21553 | 0.31617 | 0.57431 | 4.13759 | 0.43043 |
| 64 | C-T3 | 5 | 10 | 0.51810 | -0.08103 | -0.08792 | -0.23992 | -0.32783 | 0.49915 | 0.01895 |
| 125 | F5-00-C | 1 | 38 | 1.01603 | -0.02473 | -0.03208 | 0.00781 | -0.01745 | 0.00925 | 1.00678 |
| 126 | F5-00-C | 2 | 37 | 0.62553 | -0.01479 | -0.01429 | 0.00482 | -0.12744 | 0.60008 | 0.02545 |
| 127 | F5-00-C | 3 | 35 | 8.47559 | -0.10277 | -0.09842 | 1.01614 | 1.14724 | 9.92628 | -1.45068 |
| 128 | F5-00-C | 4 | 18 | 0.57757 | -0.02535 | 0.00021 | 0.31617 | 0.36430 | 0.58953 | -0.01196 |
| 129 | F5-00-C | 5 | 10 | 1.02301 | -0.14537 | -0.14392 | -0.23992 | -0.38383 | 0.89767 | 0.12533 |

| index | candidate | baseline | protocol | omitted_fold | n | delta_RMSE | delta_MAE | SSE_gain | analysis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | F5-01 | C-T3 | spatial | 1 | 100 | 0.06546 | 0.02059 | -10.03723 | OOF aggregation sensitivity only; no refitting |
| 1 | F5-01 | C-T3 | spatial | 2 | 101 | 0.07438 | 0.02589 | -11.28212 | OOF aggregation sensitivity only; no refitting |
| 2 | F5-01 | C-T3 | spatial | 3 | 103 | -0.03944 | -0.06123 | 4.55005 | OOF aggregation sensitivity only; no refitting |
| 3 | F5-01 | C-T3 | spatial | 4 | 120 | 0.09163 | 0.04535 | -15.49572 | OOF aggregation sensitivity only; no refitting |
| 4 | F5-01 | C-T3 | spatial | 5 | 128 | 0.06139 | 0.01908 | -11.44580 | OOF aggregation sensitivity only; no refitting |
| 5 | F5-01 | C-T3 | municipality | 1 | 67 | -0.10231 | -0.09722 | 7.27584 | OOF aggregation sensitivity only; no refitting |
| 6 | F5-01 | C-T3 | municipality | 2 | 108 | -0.02697 | -0.07266 | 3.43650 | OOF aggregation sensitivity only; no refitting |
| 7 | F5-01 | C-T3 | municipality | 3 | 122 | -0.00923 | -0.04823 | 1.18856 | OOF aggregation sensitivity only; no refitting |
| 8 | F5-01 | C-T3 | municipality | 4 | 127 | -0.03516 | -0.06979 | 5.17098 | OOF aggregation sensitivity only; no refitting |
| 9 | F5-01 | C-T3 | municipality | 5 | 128 | -0.04071 | -0.08044 | 5.94639 | OOF aggregation sensitivity only; no refitting |
| 10 | F5-01 | F5-00-C | spatial | 1 | 100 | -0.06434 | -0.05409 | 10.70170 | OOF aggregation sensitivity only; no refitting |
| 11 | F5-01 | F5-00-C | spatial | 2 | 101 | -0.06684 | -0.06039 | 11.09220 | OOF aggregation sensitivity only; no refitting |
| 12 | F5-01 | F5-00-C | spatial | 3 | 103 | -0.02838 | -0.03090 | 3.24214 | OOF aggregation sensitivity only; no refitting |
| 13 | F5-01 | F5-00-C | spatial | 4 | 120 | -0.05949 | -0.05526 | 11.14016 | OOF aggregation sensitivity only; no refitting |
| 14 | F5-01 | F5-00-C | spatial | 5 | 128 | -0.05318 | -0.04054 | 10.69473 | OOF aggregation sensitivity only; no refitting |
| 15 | F5-01 | F5-00-C | municipality | 1 | 67 | -0.02310 | -0.02508 | 1.52043 | OOF aggregation sensitivity only; no refitting |
| 16 | F5-01 | F5-00-C | municipality | 2 | 108 | -0.01109 | -0.01147 | 1.39416 | OOF aggregation sensitivity only; no refitting |
| 17 | F5-01 | F5-00-C | municipality | 3 | 122 | -0.00550 | -0.00954 | 0.70548 | OOF aggregation sensitivity only; no refitting |
| 18 | F5-01 | F5-00-C | municipality | 4 | 127 | -0.00289 | 0.00043 | 0.41378 | OOF aggregation sensitivity only; no refitting |
| 19 | F5-01 | F5-00-C | municipality | 5 | 128 | -0.01085 | -0.01132 | 1.54410 | OOF aggregation sensitivity only; no refitting |

Se denomina sensibilidad de agregación OOF al omitir el fold/bloque. Se mantienen las mismas predicciones, sin ajustar otra vez. El análisis separa tamaño del bloque, sesgo cuadrático y dispersión de errores. Una región puede empeorar aunque el agregado mejore; el comportamiento deGP fuera del soporte y su retorno a una media constante son hipótesis interpretativas, no mecanismos causales demostrados. No se usa bloque3 como predictor ni regla de activación.

La pérdida espacial frente aC-T3 es−10.927704degananciaSSE; bloque3 aporta−15.477758, compensada por+4.550054 enlosdemás bloques. Omitir3 cambiaΔRMSE de+0.056018 a−0.039437. GP mejora3/5bloques espaciales. Las35parcelas delbloque3 están fuera de almenos un rango marginal autorizado de entrenamiento. Su Y medio3.028571t/ha se predice como4.044714; eltrain deeseajuste tiene media4.270291. Esto es compatible con extrapolación insuficiente de la configuración estacionaria/media constante, sin demostrar que una sola elección delkernel o de representación lo cause.

Enmunicipal, Singuilucan aporta4.566008de5.754563gananciaSSE global frente aC-T3. Al omitir ese fold, la gananciaRMSE sigue positiva0.009230, pero cae por debajo delmargen práctico0.01. ElmunicipioChignahuapan empeoraRMSE en0.018165 aunque mejoraMAE en0.047009. Por tanto, la evidencia municipal es favorable, con heterogeneidad regional y cambios de sesgo/dispersión.

## Influencia, mejoras y deterioros

| index | candidate | baseline | protocol | k | net_SSE_gain | top_positive_gain | fraction_net_gain | fraction_positive_gain | top_ids | bottom_gain | bottom_ids |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | F5-01 | C-T3 | climate_profile | 5 | 2.93524 | 2.16617 | 0.73799 | 0.28301 | ["AGC_001", "AGC_041", "AGC_119", "AGC_166", "AGC_138"] | -2.16537 | ["AGC_074", "AGC_127", "AGC_171", "AGC_123", "AGC_144"] |
| 4 | F5-01 | C-T3 | municipality | 5 | 5.75456 | 2.54129 | 0.44161 | 0.17593 | ["AGC_034", "AGC_001", "AGC_014", "AGC_185", "AGC_038"] | -5.06568 | ["AGC_127", "AGC_171", "AGC_024", "AGC_195", "AGC_026"] |
| 7 | F5-01 | C-T3 | random | 5 | 1.06234 | 2.08399 | 1.96169 | 0.40241 | ["AGC_001", "AGC_122", "AGC_041", "AGC_166", "AGC_138"] | -1.71377 | ["AGC_127", "AGC_074", "AGC_081", "AGC_171", "AGC_055"] |
| 10 | F5-01 | C-T3 | spatial | 5 | -10.92770 | 2.90309 | -0.26566 | 0.29329 | ["AGC_001", "AGC_166", "AGC_034", "AGC_041", "AGC_122"] | -5.67712 | ["AGC_123", "AGC_144", "AGC_054", "AGC_127", "AGC_046"] |
| 13 | F5-01 | F5-00-C | climate_profile | 5 | 2.68373 | 2.17909 | 0.81196 | 0.35246 | ["AGC_127", "AGC_171", "AGC_055", "AGC_049", "AGC_069"] | -1.37599 | ["AGC_015", "AGC_160", "AGC_172", "AGC_122", "AGC_035"] |
| 16 | F5-01 | F5-00-C | municipality | 5 | 1.39449 | 1.64417 | 1.17905 | 0.27258 | ["AGC_034", "AGC_009", "AGC_054", "AGC_171", "AGC_123"] | -2.41584 | ["AGC_127", "AGC_001", "AGC_122", "AGC_172", "AGC_015"] |
| 19 | F5-01 | F5-00-C | random | 5 | 1.58800 | 1.71684 | 1.08113 | 0.34969 | ["AGC_127", "AGC_171", "AGC_034", "AGC_049", "AGC_055"] | -1.08385 | ["AGC_172", "AGC_160", "AGC_162", "AGC_122", "AGC_035"] |
| 22 | F5-01 | F5-00-C | spatial | 5 | 11.71773 | 3.42852 | 0.29259 | 0.23000 | ["AGC_054", "AGC_123", "AGC_144", "AGC_055", "AGC_049"] | -1.93065 | ["AGC_015", "AGC_160", "AGC_035", "AGC_172", "AGC_047"] |

| index | candidate | baseline | protocol | n_removed | n_remaining | delta_RMSE_pooled_mean_loss | delta_MAE | SSE_gain | removed_ids | analysis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | F5-01 | C-T3 | climate_profile | 5 | 133 | -0.00582 | -0.01731 | 0.76907 | ["AGC_001", "AGC_041", "AGC_119", "AGC_166", "AGC_138"] | Descriptive influential-case omission; meanparcel losses, not primary meanrepeat RMSE |
| 4 | F5-01 | C-T3 | municipality | 5 | 133 | -0.02231 | -0.06191 | 3.21327 | ["AGC_034", "AGC_001", "AGC_014", "AGC_185", "AGC_038"] | Descriptive influential-case omission; meanparcel losses, not primary meanrepeat RMSE |
| 7 | F5-01 | C-T3 | random | 5 | 133 | 0.00784 | -0.00430 | -1.02165 | ["AGC_001", "AGC_122", "AGC_041", "AGC_166", "AGC_138"] | Descriptive influential-case omission; meanparcel losses, not primary meanrepeat RMSE |
| 10 | F5-01 | C-T3 | spatial | 5 | 133 | 0.07595 | 0.02447 | -13.83079 | ["AGC_001", "AGC_166", "AGC_034", "AGC_041", "AGC_122"] | Descriptive influential-case omission; meanparcel losses, not primary meanrepeat RMSE |
| 13 | F5-01 | F5-00-C | climate_profile | 5 | 133 | -0.00417 | 0.00073 | 0.50465 | ["AGC_127", "AGC_171", "AGC_055", "AGC_049", "AGC_069"] | Descriptive influential-case omission; meanparcel losses, not primary meanrepeat RMSE |
| 16 | F5-01 | F5-00-C | municipality | 5 | 133 | 0.00189 | -0.00167 | -0.24968 | ["AGC_034", "AGC_009", "AGC_054", "AGC_171", "AGC_123"] | Descriptive influential-case omission; meanparcel losses, not primary meanrepeat RMSE |
| 19 | F5-01 | F5-00-C | random | 5 | 133 | 0.00108 | 0.00366 | -0.12883 | ["AGC_127", "AGC_171", "AGC_034", "AGC_049", "AGC_055"] | Descriptive influential-case omission; meanparcel losses, not primary meanrepeat RMSE |
| 22 | F5-01 | F5-00-C | spatial | 5 | 133 | -0.04258 | -0.03923 | 8.28921 | ["AGC_054", "AGC_123", "AGC_144", "AGC_055", "AGC_049"] | Descriptive influential-case omission; meanparcel losses, not primary meanrepeat RMSE |

`parcel_gains_*.csv` conserva138IDs por protocolo, sus ganancias/pérdidas y municipio/perfil. Los top positivos y negativos se incluyen conIDs. Las fracciones de neto pueden superar100% por compensación de deterioros; con neto negativo no describen concentración de una mejora. El análisis de omitir beneficiarios es descriptivo y no elimina ninguna etiqueta/OOF original ni se usa para recalcular un ranking favorable.

La ganancia municipal frente aC-T3 se distribuye mejor que la aleatoria:96/138parcelas mejoranSE; top5explican44.16%delneto y omitirlos mantieneRMSE−0.022305. Enaleatoria top5explican196.17%delneto y omitirlos lo revierte; las138parcelas siguen intactas enOOF. El pequeño beneficioNDVI frente aGPlluvia enmunicipal/aleatoria también revierte al omitir top5beneficiarios; enespacio sí persiste. Estas son reservas de estabilidad, no argumentos para quitar observaciones.

## Intervalos y soporte

| index | experiment | protocol | stratum | n | coverage | mean_width | mean_predictive_sd | mean_latent_sd | mean_noise_variance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | F5-00-C | climate_profile | all | 138.00000 | 0.92029 | 1.77856 | 0.54064 | 0.21900 | 0.24217 |
| 2 | F5-00-C | climate_profile | new_profile | 138.00000 | 0.92029 | 1.77856 | 0.54064 | 0.21900 | 0.24217 |
| 4 | F5-00-C | municipality | all | 138.00000 | 0.90580 | 1.79304 | 0.54504 | 0.31465 | 0.19637 |
| 6 | F5-00-C | municipality | known_profile | 43.00000 | 0.90698 | 1.49505 | 0.45446 | 0.21706 | 0.16061 |
| 7 | F5-00-C | municipality | new_profile | 95.00000 | 0.90526 | 1.92791 | 0.58604 | 0.35883 | 0.21255 |
| 9 | F5-00-C | random | all | 138.00000 | 0.91594 | 1.70343 | 0.51781 | 0.14090 | 0.24564 |
| 11 | F5-00-C | random | known_profile | 105.50000 | 0.90902 | 1.68157 | 0.51116 | 0.12281 | 0.24517 |
| 12 | F5-00-C | random | new_profile | 32.50000 | 0.93897 | 1.77330 | 0.53904 | 0.19921 | 0.24699 |
| 14 | F5-00-C | spatial | all | 138.00000 | 0.85507 | 2.09178 | 0.63585 | 0.38210 | 0.23952 |
| 16 | F5-00-C | spatial | known_profile | 37.00000 | 0.91892 | 1.68391 | 0.51187 | 0.19868 | 0.22146 |
| 17 | F5-00-C | spatial | new_profile | 101.00000 | 0.83168 | 2.24119 | 0.68127 | 0.44929 | 0.24614 |
| 19 | F5-01 | climate_profile | all | 138.00000 | 0.92029 | 1.72038 | 0.52296 | 0.20687 | 0.22829 |
| 21 | F5-01 | climate_profile | new_profile | 138.00000 | 0.92029 | 1.72038 | 0.52296 | 0.20687 | 0.22829 |
| 23 | F5-01 | municipality | all | 138.00000 | 0.88406 | 1.70816 | 0.51924 | 0.29946 | 0.17905 |
| 25 | F5-01 | municipality | known_profile | 43.00000 | 0.90698 | 1.47447 | 0.44821 | 0.23942 | 0.14243 |
| 26 | F5-01 | municipality | new_profile | 95.00000 | 0.87368 | 1.81394 | 0.55140 | 0.32663 | 0.19563 |
| 28 | F5-01 | random | all | 138.00000 | 0.92464 | 1.65643 | 0.50352 | 0.14424 | 0.23066 |
| 30 | F5-01 | random | known_profile | 105.50000 | 0.93372 | 1.64121 | 0.49889 | 0.13189 | 0.23025 |
| 31 | F5-01 | random | new_profile | 32.50000 | 0.89474 | 1.70466 | 0.51818 | 0.18391 | 0.23180 |
| 33 | F5-01 | spatial | all | 138.00000 | 0.92754 | 2.10515 | 0.63992 | 0.39106 | 0.22588 |
| 35 | F5-01 | spatial | known_profile | 37.00000 | 0.94595 | 1.66682 | 0.50668 | 0.19926 | 0.21500 |
| 36 | F5-01 | spatial | new_profile | 101.00000 | 0.92079 | 2.26573 | 0.68873 | 0.46132 | 0.22986 |

Intervalos90% de observaciones futuras bajo elmodelo Gaussian plug-in. predictivesd incorpora varianza de ruidoWhiteKernel; latentsd se obtiene restando esa varianza después de desnormalizar. Ambas se guardan enOOF. El jitter de entrenamiento no se suma como nuevo ruido observacional.

Se omite incertidumbre de hiperparámetros/selección, error de covariables/etiquetas, dependencia de residuos y cambio de dominio. Cobertura alta con intervalo amplio no implica predicción mejor. No se recalibraron intervalos ni se implementó conformal. Para conocida/nueva clasificación se usan perfiles presentes en train exclusivamente como diagnóstico, nunca como entrada delkernel.

F5-01 tiene cobertura90%nominal observada92.4638%aleatoria,92.0290%porperfil,88.4058%municipal y92.7536%espacial. Enperfiles nuevos municipales es87.3684%. Laamplitud espacial media es2.105152t/ha frente a1.656434enaleatoria. Bloque3 alcanza97.1429%de cobertura conamplitud3.226445t/ha pese al alto sesgo de la media: la cobertura no demuestra que laspredicciones puntuales sean adecuadas allí.

Rangos marginales y distancia altrain se calculan sobre lasvariables autorizadas y con suescala de entrenamiento. Estar dentro de losrangos no garantiza soporte conjunto ni intercambiabilidad territorial. Unkernel estacionario con media constante puede volver a la media al alejarse de losdatos; susintervalos no garantizan cobertura bajo esa situación.

## Diagnósticos de optimización y ejecución

| experiment | protocol | n_models | mean_lml | mean_rain_length | mean_ndvi_length | n_bound_hits | n_warnings | optimizer_converged_fraction | max_covariance_condition | fit_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F5-00-C | climate_profile | 5 | -109.60368 | 1.77437 | nan | 0 | 0 | 1.00000 | 295.85715 | 0.40674 |
| F5-00-C | municipality | 5 | -112.09389 | 2.03099 | nan | 0 | 0 | 1.00000 | 604.08142 | 0.41486 |
| F5-00-C | random | 50 | -108.34057 | 1.73376 | nan | 0 | 0 | 1.00000 | 322.09585 | 17.32092 |
| F5-00-C | spatial | 5 | -111.14753 | 1.97381 | nan | 0 | 0 | 1.00000 | 509.31344 | 0.44028 |
| F5-01 | climate_profile | 5 | -107.22604 | 3.06685 | 6.60602 | 0 | 0 | 1.00000 | 939.36554 | 0.65617 |
| F5-01 | municipality | 5 | -109.44963 | 3.69220 | 7.14376 | 0 | 0 | 1.00000 | 1311.40235 | 0.71272 |
| F5-01 | random | 50 | -105.78333 | 2.89933 | 6.43502 | 0 | 0 | 1.00000 | 934.07076 | 25.20444 |
| F5-01 | spatial | 5 | -108.72991 | 3.77878 | 7.17322 | 0 | 0 | 1.00000 | 1163.56780 | 0.74008 |

Loslogs completos están en `fit_registry.csv` y `optimizer_starts.json`:650fits,1950inicios. Los parámetros en límites y las advertencias de proximidad se reportan sin ampliar rangos. La covarianza positiva y predicciones finitas se verifican para cada modelo. LML no se compara entre distintos train/tamaños como métrica de generalización.

El entorno emitió una advertencia de threadpoolctl por coexistencia de runtimes Intel/LLVM OpenMP. Se conserva en `audit/runtime_environment_note.txt`. La ejecución Windows terminó sin crashes/deadlocks observados; esta advertencia de entorno se separa de convergencia numérica delGP. Se limitó BLAS a un hilo porworker y se usaron3workers deCPU, sin agentes adicionales.

## Decisión y alcance de la hipótesis

Ganancia práctica municipal0.01: True; costo máximo global0.01: False; mejora en≥3/5foldsmunicipales: True (3/5). Aceptación conjunta: False. Estos márgenes y guardas son exploratorios, no un test de significancia ni utilidad económica validada.

No se promueve Champion. NDVI tiene contribución positiva global frente aGPlluvia sola; se inspeccionan además sus costos locales y distribución porperfil. La representación compacta no queda rechazada porque el control con lasmismasvariables mantiene fortalezas. El resultado cuestiona una mejora general de la configuraciónMatérn agrupada/media constante, especialmente su extrapolación espacial, mientras respalda ventajas municipales/porperfil. No rechazaRBF, otras escalas/medias ni toda la familiaGP; esas opciones todavía no se ejecutaron.

Próximo paso recomendado: **revisión de sensibilidad acotada de representación/kernel antes de añadir historia**. Conservar estosresultados como referencia y estudiar si el costo espacial proviene de métrica agrupada, suavidad o media fuera delsoporte. No ajustar nuevoskernels ni límites enestaentrega. No hay evidencia suficiente para avanzar automáticamente aF5-03–06.

## Reproducción e integridad

`python scripts/349_family5_gpr_initial.py` ejecuta exclusivamente elalcance aprobado y recupera checkpoints idénticos; `350_family5_gpr_initial_finalize.py` verificará pruebas/hashes y cerrará losartefactos. Después delmanifiesto final, la versión queda protegida contra sobrescritura. No se alteraron F5 diseño ni etapas previas. No hay entrenamiento definitivo sobre138ni59predicciones finales.


## Figuras

![global_RMSE.png](../outputs/modeling/family_5/gpr_initial/v1/figures/global_RMSE.png)

![global_MAE.png](../outputs/modeling/family_5/gpr_initial/v1/figures/global_MAE.png)

![intraprofile_errors.png](../outputs/modeling/family_5/gpr_initial/v1/figures/intraprofile_errors.png)

![kernel_hyperparameters.png](../outputs/modeling/family_5/gpr_initial/v1/figures/kernel_hyperparameters.png)

![interval_coverage.png](../outputs/modeling/family_5/gpr_initial/v1/figures/interval_coverage.png)

![spatial_block_gains.png](../outputs/modeling/family_5/gpr_initial/v1/figures/spatial_block_gains.png)

![fold_omission_sensitivity.png](../outputs/modeling/family_5/gpr_initial/v1/figures/fold_omission_sensitivity.png)

![gain_concentration.png](../outputs/modeling/family_5/gpr_initial/v1/figures/gain_concentration.png)

![random_prediction_scatter.png](../outputs/modeling/family_5/gpr_initial/v1/figures/random_prediction_scatter.png)

## Verificación final

Pasaron22pruebas matemáticas y de integración, incluido replay de los650modelos externos/internos y los65controles C-T3. Se verificaron5529archivos anteriores protegidos y hashes delcódigo de ajuste congelado. Los1950inicios deoptimización pertenecen exclusivamente a lasdosconfiguraciones autorizadas; todaslas650soluciones seleccionadas convergieron y lascovarianzas fueron positivas. No se ajustó unmodelo final con138Y ni se generaron59predicciones PRED. Los tiempos reales porfit y laaproximación de duración paralela están en `audit/execution_timing.json`. No se ejecutaronF5-02–06, F5-00-M u otrokernel.
