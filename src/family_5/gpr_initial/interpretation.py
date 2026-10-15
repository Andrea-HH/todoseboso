"""Scientific interpretation of the approved initial GPR contrast only."""
import json
import pandas as pd
from . import execution as e
from src.family_4.stage_c_final_report import md

def read(name):return pd.read_csv(e.OUT/'tables'/name)

def write(summary):
    paired=read('paired_metrics_summary.csv');local=read('intraprofile_metrics_summary.csv');folds=read('paired_fold_contributions.csv');omit=read('fold_omission_sensitivity.csv');concentration=read('gain_concentration.csv');removed=read('influential_parcel_omission.csv');coverage=read('interval_coverage_summary.csv');kernel=read('kernel_parameter_diagnostics.csv');outer=kernel[kernel.context.eq('outer')]
    difference=paired[(paired.candidate=='F5-01')&paired.baseline.eq('C-T3')].set_index('protocol')
    municipal_gain=-difference.loc['municipality','delta_RMSE'];harm=difference.loc[['random','climate_profile','spatial'],['delta_RMSE','delta_MAE']].max().max()
    nmunicipal=int(((folds.candidate=='F5-01')&(folds.baseline=='C-T3')&(folds.protocol=='municipality')&(folds.delta_RMSE<0)).sum())
    primary_pass=bool(municipal_gain>=.01);guard_pass=bool(harm<=.01);distribution_pass=nmunicipal>=3
    decision=dict(municipal_gain_t_ha=municipal_gain,primary_municipal_practical_gain_pass=primary_pass,other_global_RMSE_MAE_harm_max=harm,other_global_cost_guard_pass=guard_pass,municipal_folds_improving=nmunicipal,municipal_distribution_guard_pass=distribution_pass,promote_champion=False,overall_acceptance=bool(primary_pass and guard_pass and distribution_pass),next_recommendation='review a bounded representation/kernel sensitivity before historical blocks; do not execute it automatically',reason='municipal/profile/random strengths coexist with spatial deterioration',limits='exploratory reused138Y; no independent confirmation; sensitivity/intervals descriptive')
    (e.OUT/'report/decision.json').write_text(json.dumps(decision,indent=2),encoding='utf8')
    cmetric=summary.set_index(['experiment','protocol']);numbers=lambda exp,p: cmetric.loc[(exp,p),'RMSE']
    synopsis=f'''# F5 inicial — Síntesis para decisiones

**F5-01 aporta una mejora municipal y por perfil frente a C-T3, pero empeora la transferencia espacial. No se propone un nuevo Champion.**

{md(summary[['experiment','protocol','RMSE','MAE','bias','n','n_repeats']])}

La RMSE municipal baja {numbers('C-T3','municipality'):.6f}→{numbers('F5-01','municipality'):.6f} t/ha, una mejora de {municipal_gain:.6f}. También mejora aleatoria y por perfil. En espacio aumenta {numbers('C-T3','spatial'):.6f}→{numbers('F5-01','spatial'):.6f}: excede el margen congelado 0.01 t/ha de deterioro.

NDVI mayo contribuye positivamente frente a F5-00-C en los cuatro RMSE globales. Su ganancia municipal adicional es menor que 0.01 t/ha, aunque las demás diferencias y los errores intraperfil permiten evaluar su papel con mayor detalle. No se concluye que NDVI solo sea suficiente ni que discrimine parcelas con vectores de entrada idénticos.

Su aporte local es desigual: en municipal, RMSE de diferencias con igual peso por perfil pasa de0.518899 en lluviaGP sola a0.538821 conNDVI; también supera0.520989 deC-T3. En aleatoria, F5-01 mejora frente aGPlluvia, pero empeora diferencias frente aC-T3. Una mejor predicción del nivel regional no garantiza mejor diferenciación parcelaria.

El costo espacial se concentra en el bloque3: allí F5-01 tiene sesgo+1.016142t/ha frente a+0.718204 deC-T3. Al omitirlo solo de la agregaciónOOF, F5-01 mejoraRMSE en0.039437t/ha. En municipal mejora3/5folds; omitir suscinco principales beneficiarios conserva una gananciaRMSE de0.022305t/ha. En aleatoria, omitir loscinco principales beneficiarios revierte la mejoraRMSE frente aC-T3: esa ganancia pequeña es más frágil.

La prueba principal municipal {'cumple' if primary_pass else 'no cumple'} el margen de ganancia; la guarda global de costo {'cumple' if guard_pass else 'no cumple'}; {nmunicipal}/5 folds municipales mejoran RMSE. La aceptación conjunta es {decision['overall_acceptance']}. Una mejora agregada no demuestra beneficio para la mayoría de parcelas ni estabilidad entre todas las regiones.

**Recomendación:** conservar F5-01 como candidato exploratorio municipal y continuar únicamente mediante revisión de una sensibilidad acotada de representación/kernel que investigue el deterioro espacial. Posponer bloques históricos hasta entender ese límite. No ampliar automáticamente F5 ni modificar Champion. La suavidad conjunta recibe apoyo parcial; su extrapolación espacial bajo media constante no ofrece una ventaja general. No se rechaza la representación compacta —el control C-T3 sigue siendo útil— ni todos los Gaussian Processes.

Intervalos90%: cobertura y amplitud por protocolo/perfil conocido/nuevo están en el reporte técnico. Son Gaussian plug-in, con parámetros estimados y ruido observado; no garantías de calibración bajo cambio de dominio. Las omisiones de bloques/casos reutilizan las mismas OOF, sin reentrenamiento.

Se ejecutaron únicamente F5-00-C y F5-01: 130 ajustes externos y 520 diagnósticos internos sobre las particiones originales. C-T3 se recuperó y reprodujo exactamente en sus 65 folds. No se ajustó un modelo final sobre138 ni se predijeron las59PRED. Las cifras son OOF completa por repetición y luego media de repeticiones; no media de RMSE por fold.
'''
    technical=f'''# F5-00-C / F5-01 — Ejecución inicial controlada de GPR

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

{md(summary)}

Comparaciones pareadas: ΔRMSE/MAE=candidato−control (negativo favorece candidato); gananciaSSE=control−candidato (positivo favorece candidato). IDs/Y/protocolo/repetición/fold coinciden uno a uno.

{md(paired[['candidate','baseline','protocol','delta_RMSE','delta_MAE','SSE_gain','fraction_SE_improve','fraction_AE_improve']])}

En aleatoria, las diferencias SSE se resumen primero por repetición; influencia usa pérdida media por parcela entre las10repeticiones, no1380parcelas independientes. Las repeticiones/folds/modelos son dependientes. No se realizan pruebas masivas ni se interpretan estas diferencias como significancia confirmatoria.

## Heterogeneidad intraperfil

{md(local[local.scope.eq('all')][['experiment','protocol','n_pairs','n_profiles','n_parcels','equal_profile_RMSE','equal_profile_MAE','pair_weighted_RMSE']])}

Cada pareja proviene de un mismo ajuste externo y perfil climático. Igual peso por perfil evita que dos perfiles grandes dominen el diagnóstico; se conserva también ponderación por parejas y perspectivas dentro/fuera deChignahuapan. El soporte no es igual entre protocolos. Parejas solapadas no son réplicas independientes ni todas las posibles parejas son evaluables aleatoriamente por el mismo modelo.

F5-00-C no distingue medias de parcelas con lluvia compacta idéntica. WhiteKernel admite etiquetas distintas y regulariza la covarianza; no crea una característica parcelaria. NDVI permite diferencias condicionadas al clima y una respuesta no lineal, pero no necesariamente corrige todo el error local. Las tablas porperfil reportan n real y los dos perfiles dominantes; no se declara error irreducible.

NDVI no aporta una mejora local uniforme: frente aGPlluvia, mejoraRMSE de diferencias aleatoria/perfil/espacio, pero enmunicipal empeora0.518899→0.538821. Frente aC-T3, lasdiferencias empeoran aleatoria0.589951→0.602212 ymunicipal0.520989→0.538821, mientras mejoran perfil0.547885→0.531827 yespacio0.540147→0.531899. El RMSE ponderado porparejas sigue siendo peor queC-T3 enloscuatro protocolos. No debe describirse la reducción global como solución de la heterogeneidad dominante deChignahuapan.

## Transferencia y bloque espacial3

{md(folds[(folds.protocol.eq('spatial'))&folds.candidate.eq('F5-01')][['baseline','fold','n','SSE_gain','delta_RMSE','delta_MAE','bias_candidate','bias_base','bias_squared_gain','error_variance_gain']])}

{md(omit[omit.candidate.eq('F5-01')])}

Se denomina sensibilidad de agregación OOF al omitir el fold/bloque. Se mantienen las mismas predicciones, sin ajustar otra vez. El análisis separa tamaño del bloque, sesgo cuadrático y dispersión de errores. Una región puede empeorar aunque el agregado mejore; el comportamiento deGP fuera del soporte y su retorno a una media constante son hipótesis interpretativas, no mecanismos causales demostrados. No se usa bloque3 como predictor ni regla de activación.

La pérdida espacial frente aC-T3 es−10.927704degananciaSSE; bloque3 aporta−15.477758, compensada por+4.550054 enlosdemás bloques. Omitir3 cambiaΔRMSE de+0.056018 a−0.039437. GP mejora3/5bloques espaciales. Las35parcelas delbloque3 están fuera de almenos un rango marginal autorizado de entrenamiento. Su Y medio3.028571t/ha se predice como4.044714; eltrain deeseajuste tiene media4.270291. Esto es compatible con extrapolación insuficiente de la configuración estacionaria/media constante, sin demostrar que una sola elección delkernel o de representación lo cause.

Enmunicipal, Singuilucan aporta4.566008de5.754563gananciaSSE global frente aC-T3. Al omitir ese fold, la gananciaRMSE sigue positiva0.009230, pero cae por debajo delmargen práctico0.01. ElmunicipioChignahuapan empeoraRMSE en0.018165 aunque mejoraMAE en0.047009. Por tanto, la evidencia municipal es favorable, con heterogeneidad regional y cambios de sesgo/dispersión.

## Influencia, mejoras y deterioros

{md(concentration[(concentration.candidate=='F5-01')&concentration.k.eq(5)])}

{md(removed[(removed.candidate=='F5-01')&removed.n_removed.eq(5)])}

`parcel_gains_*.csv` conserva138IDs por protocolo, sus ganancias/pérdidas y municipio/perfil. Los top positivos y negativos se incluyen conIDs. Las fracciones de neto pueden superar100% por compensación de deterioros; con neto negativo no describen concentración de una mejora. El análisis de omitir beneficiarios es descriptivo y no elimina ninguna etiqueta/OOF original ni se usa para recalcular un ranking favorable.

La ganancia municipal frente aC-T3 se distribuye mejor que la aleatoria:96/138parcelas mejoranSE; top5explican44.16%delneto y omitirlos mantieneRMSE−0.022305. Enaleatoria top5explican196.17%delneto y omitirlos lo revierte; las138parcelas siguen intactas enOOF. El pequeño beneficioNDVI frente aGPlluvia enmunicipal/aleatoria también revierte al omitir top5beneficiarios; enespacio sí persiste. Estas son reservas de estabilidad, no argumentos para quitar observaciones.

## Intervalos y soporte

{md(coverage[coverage.stratum.isin(['all','known_profile','new_profile'])][['experiment','protocol','stratum','n','coverage','mean_width','mean_predictive_sd','mean_latent_sd','mean_noise_variance']])}

Intervalos90% de observaciones futuras bajo elmodelo Gaussian plug-in. predictivesd incorpora varianza de ruidoWhiteKernel; latentsd se obtiene restando esa varianza después de desnormalizar. Ambas se guardan enOOF. El jitter de entrenamiento no se suma como nuevo ruido observacional.

Se omite incertidumbre de hiperparámetros/selección, error de covariables/etiquetas, dependencia de residuos y cambio de dominio. Cobertura alta con intervalo amplio no implica predicción mejor. No se recalibraron intervalos ni se implementó conformal. Para conocida/nueva clasificación se usan perfiles presentes en train exclusivamente como diagnóstico, nunca como entrada delkernel.

F5-01 tiene cobertura90%nominal observada92.4638%aleatoria,92.0290%porperfil,88.4058%municipal y92.7536%espacial. Enperfiles nuevos municipales es87.3684%. Laamplitud espacial media es2.105152t/ha frente a1.656434enaleatoria. Bloque3 alcanza97.1429%de cobertura conamplitud3.226445t/ha pese al alto sesgo de la media: la cobertura no demuestra que laspredicciones puntuales sean adecuadas allí.

Rangos marginales y distancia altrain se calculan sobre lasvariables autorizadas y con suescala de entrenamiento. Estar dentro de losrangos no garantiza soporte conjunto ni intercambiabilidad territorial. Unkernel estacionario con media constante puede volver a la media al alejarse de losdatos; susintervalos no garantizan cobertura bajo esa situación.

## Diagnósticos de optimización y ejecución

{md(outer.groupby(['experiment','protocol']).agg(n_models=('lml','size'),mean_lml=('lml','mean'),mean_rain_length=('rain_length','mean'),mean_ndvi_length=('ndvi_length','mean'),n_bound_hits=('n_bound_hits','sum'),n_warnings=('n_warnings','sum'),optimizer_converged_fraction=('selected_optimizer_converged','mean'),max_covariance_condition=('covariance_condition','max'),fit_seconds=('seconds','sum')))}

Loslogs completos están en `fit_registry.csv` y `optimizer_starts.json`:650fits,1950inicios. Los parámetros en límites y las advertencias de proximidad se reportan sin ampliar rangos. La covarianza positiva y predicciones finitas se verifican para cada modelo. LML no se compara entre distintos train/tamaños como métrica de generalización.

El entorno emitió una advertencia de threadpoolctl por coexistencia de runtimes Intel/LLVM OpenMP. Se conserva en `audit/runtime_environment_note.txt`. La ejecución Windows terminó sin crashes/deadlocks observados; esta advertencia de entorno se separa de convergencia numérica delGP. Se limitó BLAS a un hilo porworker y se usaron3workers deCPU, sin agentes adicionales.

## Decisión y alcance de la hipótesis

Ganancia práctica municipal0.01: {primary_pass}; costo máximo global0.01: {guard_pass}; mejora en≥3/5foldsmunicipales: {distribution_pass} ({nmunicipal}/5). Aceptación conjunta: {decision['overall_acceptance']}. Estos márgenes y guardas son exploratorios, no un test de significancia ni utilidad económica validada.

No se promueve Champion. NDVI tiene contribución positiva global frente aGPlluvia sola; se inspeccionan además sus costos locales y distribución porperfil. La representación compacta no queda rechazada porque el control con lasmismasvariables mantiene fortalezas. El resultado cuestiona una mejora general de la configuraciónMatérn agrupada/media constante, especialmente su extrapolación espacial, mientras respalda ventajas municipales/porperfil. No rechazaRBF, otras escalas/medias ni toda la familiaGP; esas opciones todavía no se ejecutaron.

Próximo paso recomendado: **revisión de sensibilidad acotada de representación/kernel antes de añadir historia**. Conservar estosresultados como referencia y estudiar si el costo espacial proviene de métrica agrupada, suavidad o media fuera delsoporte. No ajustar nuevoskernels ni límites enestaentrega. No hay evidencia suficiente para avanzar automáticamente aF5-03–06.

## Reproducción e integridad

`python scripts/349_family5_gpr_initial.py` ejecuta exclusivamente elalcance aprobado y recupera checkpoints idénticos; `350_family5_gpr_initial_finalize.py` verificará pruebas/hashes y cerrará losartefactos. Después delmanifiesto final, la versión queda protegida contra sobrescritura. No se alteraron F5 diseño ni etapas previas. No hay entrenamiento definitivo sobre138ni59predicciones finales.
'''
    names=['global_RMSE.png','global_MAE.png','intraprofile_errors.png','kernel_hyperparameters.png','interval_coverage.png','spatial_block_gains.png','fold_omission_sensitivity.png','gain_concentration.png','random_prediction_scatter.png']
    technical+='\n\n## Figuras\n\n'+'\n\n'.join(f'![{name}](../figures/{name})' for name in names)
    for name,document,text in [('technical_report.md','family5_gpr_initial.md',technical),('decision_summary.md','family5_gpr_initial_decision.md',synopsis)]:
        (e.OUT/'report'/name).write_text(text,encoding='utf8')
        (e.ROOT/'documentation'/document).write_text(text.replace('../figures/','../'+(e.OUT/'figures').relative_to(e.ROOT).as_posix()+'/'),encoding='utf8')
