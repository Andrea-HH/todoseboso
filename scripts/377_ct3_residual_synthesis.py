"""Interpret sealed controlled results, no refits or additional experiments."""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/modeling/ct3_residual_conditional/v1'
OUT=ROOT/'outputs/research/ct3_residual_conditional_synthesis/v1'
OUT.mkdir(parents=True,exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
manifest=json.loads((SOURCE/'manifest.json').read_text())
for p,h in manifest['artifacts'].items():assert sha(ROOT/p)==h
for r in pd.read_csv(SOURCE/'audit/reused_source_hashes.csv').itertuples():assert sha(ROOT/r.path)==r.sha256
metrics=pd.read_csv(SOURCE/'tables/metrics_summary.csv');local=pd.read_csv(SOURCE/'tables/intraprofile_summary.csv');amp=pd.read_csv(SOURCE/'tables/amplitude_summary.csv');paired=pd.read_csv(SOURCE/'tables/paired_metrics_summary.csv');omission=pd.read_csv(SOURCE/'tables/omission_sensitivity.csv');reg=pd.read_csv(SOURCE/'tables/corrector_registry.csv')
baseline=metrics[metrics.experiment.eq('M0')].set_index('protocol');loc0=local[local.experiment.eq('M0')&local.subset.eq('all')].set_index('protocol')
checks=[]
for name in metrics.experiment.unique():
    if name=='M0':continue
    m=metrics[metrics.experiment.eq(name)].set_index('protocol');l=local[local.experiment.eq(name)&local.subset.eq('all')].set_index('protocol')
    absolute=m[['RMSE','MAE']]-baseline[['RMSE','MAE']];bias=m.bias.abs()-baseline.bias.abs();lg=loc0[['pair_weighted_RMSE','equal_profile_RMSE']]-l[['pair_weighted_RMSE','equal_profile_RMSE']]
    local_both_gain=lg.min(axis=1).max();grouped_gain=(baseline.loc[['municipality','spatial'],'RMSE']-m.loc[['municipality','spatial'],'RMSE']).max()
    oo=omission[(omission.experiment==name)&(omission.reference=='M0')&omission.protocol.isin(['municipality','spatial'])]
    checks.append(dict(experiment=name,max_absolute_harm=float(absolute.max().max()),max_geographic_abs_bias_harm=float(bias.loc[['municipality','spatial']].max()),best_grouped_RMSE_gain=float(grouped_gain),best_local_gain_both_weights=float(local_both_gain),worst_local_harm_either_weight=float(-lg.min().min()),max_geographic_omission_RMSE_harm=float(oo.delta_RMSE.max()),passes_joint_exploratory_checks=bool((absolute.max().max()<=.01)&(bias.loc[['municipality','spatial']].max()<=.02)&(lg.min().min()>=-.01)&((grouped_gain>=.01)|(local_both_gain>=.01))&(oo.delta_RMSE.max()<=.01))))
pd.DataFrame(checks).to_csv(OUT/'joint_decision_checks.csv',index=False)
assert not any(r['passes_joint_exploratory_checks'] for r in checks)
rows=[
 ('H1','Señal residual lineal LAI','No respaldada como mejora estable','M1_LAI no mejora RMSE absoluto; λ0 en70%random,100%perfil,80%municipal/espacial; ganancias locales<.003t/ha'),
 ('H2','Árbol frente a lineal con mismas entradas','No hay ventaja general que justifique complejidad','M2_Z mejora municipal vsM1_Z, pero empeora espacial0.04664 y aleatoria0.00009; C_CONTEXT replica ganancia municipal'),
 ('H3','LAI dependiente del contexto','No respaldada en transferencia; interacción formal no evaluada','Los árbolesM2_Z agrupados no usanLAI; ocho divisiones LAI solo aleatorias; controles no aíslan interacción frente a aditividad'),
 ('H4','Diferenciación intraperfil','No resuelta por CART','M2_Z conserva exactamente diferenciasM0 enperfil/municipal/espacial; aleatoria empeora ambos pesos'),
 ('H5','Transferencia territorial','No cumple criterios conjuntos','M2_Z RMSEespacial.75252vs.67878; sesgo+.483vs+.191; daño persiste al omitir cualquier bloque'),
]
pd.DataFrame(rows,columns=['hypothesis','question','conclusion','evidence']).to_csv(OUT/'hypothesis_decisions.csv',index=False)
text='''# Corrección residual condicional sobre C-T3: resultados y decisión

Se aplicaron las correcciones al prompt y se ejecutaron exclusivamente cinco modelos, con65folds originales y sus particiones internas. Esta síntesis interpreta resultados sellados; no ajusta modelos adicionales. C-T3yChampion permanecen intactos, F8no se ejecutó, no hay modelo final138ni59PRED.

## Diseño ejecutado

M0 es C-T3 archivado. M1_LAI es Ridge sobre inicio del ascenso LAI. M1_Z y M2_Z utilizan las mismas entradas: LAI, fracción temprana, HHI y NDVI mayo. El primero es Ridge y el segundo CARTdepth1/2,leaf15/25. C_CONTEXT es el mismo CARTsinLAI. Amplitud0/.25/.5, corrección centradaTRAIN; no intercepto corrector. Se realizaron1,218contextos de base,55,909ajustes nuevos de base y3,783de correctores:59,692ajustes científicos. Se recuperaron65bases externas;8970OOF,260packs externos de corrector y1040modelos internos seleccionados. Tiempo principal20.7minutos.

Cada residuo excluye su etiqueta también del tuning de su base. La evaluación interna del corrector regenera sus propios targets dentro de ese entrenamiento, sin utilizar las OOFglobales como targets. Se conserva la selección originalC-T3por mediaRMSEfold; los correctores se seleccionan porOOFinterna completa. Preprocesamiento propio de cada entrenamiento y centrado de la corrección enTRAIN. El espacio de búsqueda y las reglas no se ampliaron al ver resultados.

## Resultados absolutos

| Modelo | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| C-T3 | 0.511582 | 0.520604 | 0.581259 | 0.678778 |
| Lineal LAI | 0.512339 | 0.520604 | 0.585073 | 0.682994 |
| Lineal Z completo | 0.511867 | 0.520384 | 0.581564 | 0.705885 |
| CART Z completo | 0.511960 | 0.518105 | 0.569840 | 0.752523 |
| CART contextual sin LAI | 0.511631 | 0.517972 | 0.569840 | 0.685526 |

RMSEen t/ha sobre138OOFpor repetición, luego media de10repeticiones aleatorias; no media deRMSEporfold. La ganancia municipal deCARTcompleto es.011419t/ha, pero es exactamente la del árbolsinLAI. El daño espacial es.073745t/ha frente aC-T3y.066997frente al controlcontextual. No atribuir la ganancia municipal aLAI.

## H1: LAI lineal

La corrección se desactiva en70%de folds aleatorios,100%porperfil y80%municipales/espaciales. No mejora ningúnRMSEabsoluto. Las diferencias intraperfil presentan ganancias pequeñas: RMSEequilibrado municipal.520989→.518354 y espacial.540147→.537460; ponderado por parejas solo.768841→.768643 y.767538→.767332. No alcanza el margen.01enambos pesos. La asociación local previa no se convirtió en utilidad incremental estable sobreC-T3.

## H2: arquitectura con información emparejada

CARTvsRidgeZgana municipal.011724y perfil.002279, pero pierde aleatoria.000092yespacial.046639t/ha. No hay ventaja territorial equilibrada que justifique el árbol. Los grids son conservadores y distintos por naturaleza, de modo que esto compara procedimientos congelados, no toda regresión lineal contra todo árbol.

## H3: contexto e interacción

Los árboles externos M2_Zporperfil,municipioyespacio no utilizanLAIen ninguna división. Solo aparecieron ocho divisionesLAIen los entrenamientos aleatorios. Allí se separaron281evaluaciones de parejas dentro de modelos activos:147con primera separaciónLAI y134contextual. El denominador de paresactivos no es toda la evidencia OOF, y las parejas son dependientes. No interpretar esos conteos como causalidad o porcentaje de error explicado.

El contexto sinLAIexplica completamente la ganancia municipal. AgregarLAIafecta también la selección interna aunque no aparezca en el árbol final; por eso no implica irrelevancia absoluta. Para demostrar interacción frente a efectos aditivos faltaría un control aditivo, que no se ejecutó. La hipótesis de una correcciónLAIcontextual transferible queda debilitada bajo esta batería.

## H4: diferencias intraperfil

CARTM2_Zno separó ninguna pareja elegible enperfil,municipal oespacial. SusRMSEdediferencias son exactamente los deM0: equilibrados.547885/.520989/.540147respectivamente. En aleatoria empeora equilibrado.589951→.592175 y ponderado.771183→.773070. Usar una arquitectura condicional no resolvió diferenciación entre parcelas; sus mejoras fueron de nivel de grupos.

## H5: regiones y concentración

Los bloques espaciales1y2, principalmenteChignahuapan, tenían sesgosM0de−.036903y−.119293. M2_Zañadió correcciones medias+.493339y+.567687, pasando a sesgos+.456436y+.448394. En el bloque3eligióλ0; el controlcontextual sí corrigió y bajóRMSE.909593→.668941. Es la diferencia espacial principal entreambos árboles.

El deterioroM2frente aM0persiste al omitir cualquiera de los cinco bloques:ΔRMSE+.0443a+.1113t/ha. No es un problema exclusivamente delbloque3. Al omitirChignahuapandel cálculo, se reduce a+.006228, lo que muestra concentración del daño en esa región; no equivale a reentrenar sin ella.

La ganancia municipal neta deSSEes1.813958;Chignahuapanaporta2.009290,aproximadamente111%del total, porque otras regiones compensan con deterioros. Son ajustes de nivel, no mejoras de diferencias intraperfil. El controlcontextual tampoco es un modelo territorial aceptado: su sesgo espacial sube+.191161→+.394607y al omitirbloque3suΔRMSEes+.111278.

## Desajuste crossfit/refit

Dentro del entrenamiento,Δ=base_full−base_crossfitpresentaSD.953y.978t/haen bloques1/2. Su correlación con el corrector aprendido es.919/.957. Estos diagnósticos apoyan la posibilidad de que el corrector esté capturando error de estimación o cambio de soporte de bases pequeñas, en vez de una señal parcelaria adicional transferible. Comparten datos y componentes algebraicos; no demuestran un mecanismo causal único.

Cross-fittingevitó fuga de etiquetas, pero no eliminó la diferencia entre bases pequeñas que generan residuos y la base reajustada usada al predecir. El centradoTRAINno evitó sesgo regional: sesgoespacialM2+.483249frente a+.191161deM0.

## Estabilidad y medición

Las hojas respetaron mínimos15/25; hay algunas hojas con un solo perfil, pese a tener muchas parcelas. El soporte por perfiles fue diagnóstico, no filtro externo. Las perturbacionesLAI no cambiaron predicciones de árboles agrupados porque esos árboles no usanLAI, no porque la medición sea robusta. En aleatoria, cambios de fechas llegaron a modificar la correcciónM2hasta.2147t/haen escenarios existentes; RidgeLAIhasta.2034enespacial. No se seleccionaron parámetros con perturbaciones ni errores externos.

Se conservaron reglas, umbrales, hojas, frecuencias deλ0, correcciones, perfiles conocidos/nuevos, errores por municipio/bloque/cuartil, omisiones y ganancias por parcela. No se eliminaron parcelas ni se alteraron las138etiquetas.

## Decisión

Ningún procedimiento cumple conjuntamente los márgenes prácticos congelados, las restricciones de sesgo y la estabilidad por omisiones. Detener esta batería de CARTcondicional sobreLAI; conservarC-T3yestos resultados como referencias. No aumentar profundidad, reducirhojas ni añadirSAVI/historia/pendiente para perseguir una mejora. La calibracióncontextual es una observación distinta, no un modelo listo para integrar. Si se reabre la línea, necesita una pregunta explícita sobre crossfit/refit o datos independientes, sin sustituir retrospectivamente la base.

No se rechazan todas las correcciones residuales o interacciones. La evidencia debilita esta especificación y la expectativa de convertir directamente la asociaciónLAIlocal en una mejora territorial. Se necesitan nuevas campañas/geografías y medición verificable para confirmación.

## Verificación

Diez pruebas pasaron:5unitarias,4integracióny1prueba del pipelinecompleto tras cambiar etiquetas externas. Esa prueba conservó exactamente predicciónbase,corrección,amplitud,predicciónfinal yparámetros; susrefitsocurrieron únicamente en almacenamiento temporal aislado. Un problemaACLdeltemporalpytest impidió su primera preparación y se resolvió usando un directorio propio delworkspace; no afectó ajustes científicos ni parámetros.

Convergencia:0advertencias de ajustes de base; se mantuvo la puerta original de detención anteConvergenceWarning. El runtime emitió avisosIntel/LLVMOpenMPregistrados aparte. Todos los260packsreprodujeron susOOFcon tolerancia1e−10. Hashesverifican entradas consumidas y modelos anteriores. Las10repeticiones y las parejas no son independientes; los márgenes.01no son significación estadística ni beneficio económico. Los mismos138casosse han investigado repetidamente: reproducibilidad no equivale a generalización.
'''
(OUT/'technical_findings.md').write_text(text,encoding='utf-8')
executive='''# Síntesis ejecutiva

La corrección residual mediante un árbol pequeño no produjo una mejora estable sobre C-T3 ni resolvió las diferencias entre parcelas de igual clima. Se ejecutaron los cinco modelos y controles autorizados con validación anidada, conservando la base.

El árbol completo mejoró el RMSE municipal de0.5813a0.5698, pero el árbol sinLAI obtuvo exactamente esa misma mejora. Espacialmente, el árbol completo empeoró de0.6788a0.7525. En las tres validaciones agrupadas no cambió ninguna diferencia intraperfil: corrigió niveles de grupos.

La corrección lineal deLAI se desactivó frecuentemente y no mejoró losRMSEabsolutos. Las mejoras locales fueron de pocas milésimas. Las correcciones espaciales grandes parecen relacionadas con el desajuste entre bases cross-fitted pequeñas y la base reajustada; es evidencia diagnóstica, no explicación causal concluida.

Recomendación: detener esta batería, conservar C-T3 y no ampliar retrospectivamente profundidad o variables. No se promovió Champion ni se generaron59PRED. Diez pruebas pasaron y se preservaron hashes. La investigación entrega resultados negativos útiles; no descarta todos los modelos residuales.
'''
(OUT/'executive_summary.md').write_text(executive,encoding='utf-8')
for r in pd.read_csv(SOURCE/'audit/protected_consumed_inputs.csv').itertuples():assert sha(ROOT/r.path)==r.sha256
artifacts={p.relative_to(ROOT).as_posix():sha(p) for p in OUT.iterdir() if p.is_file()}
(OUT/'manifest.json').write_text(json.dumps(dict(status='complete',new_fits=0,new_predictions=0,source_manifest_sha256=sha(SOURCE/'manifest.json'),script_sha256=sha(__file__),tests_passed=10,artifacts=artifacts),indent=2),encoding='utf-8')
doc=ROOT/'documentation/ct3_residual_conditional.md'
doc.write_text('# Corrección residual condicional sobre C-T3\n\n[Hallazgos y decisión](../outputs/research/ct3_residual_conditional_synthesis/v1/technical_findings.md), [síntesis ejecutiva](../outputs/research/ct3_residual_conditional_synthesis/v1/executive_summary.md).\n\n[Diseño aplicado](ct3_residual_conditional_design.md), [métricas](../outputs/modeling/ct3_residual_conditional/v1/tables/metrics_summary.csv), [OOF completas](../outputs/modeling/ct3_residual_conditional/v1/tables/oof_predictions.csv), [reglas](../outputs/modeling/ct3_residual_conditional/v1/tables/tree_rules.csv).\n\nLa ganancia municipal del árbol completo coincide con la del control sin LAI; su validación espacial empeora y no mejora diferencias intraperfil agrupadas. Se detiene la batería sin promover modelos. Diez pruebas pasaron. F8 y Champion intactos, sin ajuste final138 ni59PRED. Scripts376/377.\n',encoding='utf-8')
print('Synthesis complete: all four correctors fail joint exploratory acceptance')
