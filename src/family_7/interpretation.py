"""Exploratory architecture decision; no extension training or automatic promotion."""
import json
import pandas as pd,numpy as np
from . import execution as e
def write(summary):
    lookup=summary.set_index(['experiment','protocol'])
    rows=[]
    for name in e.SPECS:
        for baseline in ['C-T3','F5-01','F6-E0']:
            for protocol in ['random','climate_profile','municipality','spatial']:
                rows.append(dict(candidate=name,baseline=baseline,protocol=protocol,delta_RMSE=lookup.loc[(name,protocol),'RMSE']-lookup.loc[(baseline,protocol),'RMSE'],delta_MAE=lookup.loc[(name,protocol),'MAE']-lookup.loc[(baseline,protocol),'MAE']))
    pd.DataFrame(rows).to_csv(e.OUT/'tables/decision_evidence.csv',index=False)
    omissions=pd.read_csv(e.OUT/'tables/fold_omission_sensitivity.csv')
    evidence=[]
    for name in e.SPECS:
        z=pd.DataFrame(rows);z=z[(z.candidate==name)&(z.baseline=='C-T3')]
        o=omissions[(omissions.candidate==name)&(omissions.baseline=='C-T3')]
        evidence.append(dict(experiment=name,improving_RMSE_protocols=int((z.delta_RMSE<0).sum()),
            max_delta_RMSE=float(z.delta_RMSE.max()),max_delta_MAE=float(z.delta_MAE.max()),
            municipal_delta_RMSE=float(z[z.protocol.eq('municipality')].delta_RMSE.iloc[0]),
            spatial_delta_RMSE=float(z[z.protocol.eq('spatial')].delta_RMSE.iloc[0]),
            max_territorial_omission_delta_RMSE=float(o.delta_RMSE.max())))
    decision=dict(executed=list(e.SPECS),extensions_executed=False,extension_algorithm_frozen='CatBoost',
        recommendation='continue_controlled_CatBoost_ablations_after_review; no automatic execution',evidence=evidence,champion_promoted=False,
        residual_recommendation='defer until E1-E3: compact C-T3 baseline plus internally cross-fitted, shrunk CatBoost complementary correction; proposal only',statistical_superiority_claimed=False,
        no_final_training=True,no_PRED=True)
    (e.OUT/'report/decision.json').write_text(json.dumps(decision,indent=2),encoding='utf8')
    protocols=['random','climate_profile','municipality','spatial']
    lines=['# F7 — Primera ejecución: CatBoost y XGBoost directos','',
        'Se ejecutaron únicamente F7-00 y F7-01. E1–E3 permanecen predefinidas para CatBoost y requieren revisión. Las comparaciones son exploratorias sobre etiquetas y folds reutilizados; no constituyen confirmación independiente ni superioridad estadística.','',
        '## Rendimiento OOF','',
        '| Modelo | Aleatoria | Perfil | Municipal | Espacial |','|---|---:|---:|---:|---:|']
    for name in ['F7-00','F7-01','C-T3','F5-01','F6-E0']:
        lines.append('| '+name+' | '+' | '.join(f'{lookup.loc[(name,p),"RMSE"]:.6f}' for p in protocols)+' |')
    lines+=['','RMSE en t/ha: cada repetición tiene138 OOF completas; aleatoria promedia diez repeticiones. MAE, sesgo y diferencias pareadas están en las tablas. Champion solo se compara en aleatoria, con RMSE OOF completa '+f'{lookup.loc[("CHAMPION","random"),"RMSE"]:.6f}'+'. No se reconstruye evaluación territorial del Champion.','',
        '## Arquitectura y transferencia','']
    for item in evidence:
        lines.append(f"- {item['experiment']}: ΔRMSE vs C-T3 municipal {item['municipal_delta_RMSE']:+.6f}, espacial {item['spatial_delta_RMSE']:+.6f}; mejora RMSE en {item['improving_RMSE_protocols']}/4 protocolos. Mayor ΔRMSE al omitir un fold territorial: {item['max_territorial_omission_delta_RMSE']:+.6f}. Estas omisiones solo recalculan OOF, sin reajustar.")
    regional=pd.read_csv(e.OUT/'tables/region_omission_summary.csv')
    regional=regional[(regional.candidate=='F7-00')&(regional.baseline=='C-T3')&(regional.omitted_type=='Municipio')&(regional.omitted_region=='Singuilucan')]
    contribution=pd.read_csv(e.OUT/'tables/paired_fold_contributions.csv')
    contribution=contribution[(contribution.candidate=='F7-00')&(contribution.baseline=='C-T3')]
    local=pd.read_csv(e.OUT/'tables/intraprofile_metrics_summary.csv');local=local[local.scope.eq('all')].set_index(['experiment','protocol'])
    space=contribution[contribution.protocol.eq('spatial')];municipal=contribution[contribution.protocol.eq('municipality')]
    decision['regional_limitations']=dict(spatial_block4_fraction_net_SSE_gain=float(space[space.fold.eq(4)].SSE_gain.iloc[0]/space.SSE_gain.sum()),municipal_Singuilucan_fraction_net_SSE_gain=float(municipal[municipal.fold.eq(3)].SSE_gain.iloc[0]/municipal.SSE_gain.sum()),Singuilucan_omission=regional[['protocol','n','delta_RMSE','delta_MAE']].to_dict('records'),intraprofile_equal_profile_RMSE_delta_CT3={p:float(local.loc[('F7-00',p),'equal_profile_RMSE']-local.loc[('C-T3',p),'equal_profile_RMSE']) for p in protocols})
    (e.OUT/'report/decision.json').write_text(json.dumps(decision,indent=2),encoding='utf8')
    lines+=['','## Concentración territorial y explicación de la mejora','',
        f"CatBoost mejora agregados municipales y espaciales frente a los tres controles, pero las ganancias no están territorialmente equilibradas. Singuilucan (16 parcelas; fold municipal3) aporta {decision['regional_limitations']['municipal_Singuilucan_fraction_net_SSE_gain']:.1%} de la ganancia municipal neta de SSE frente a C-T3. El bloque espacial4, con16 de Singuilucan y2 de otros municipios, aporta {decision['regional_limitations']['spatial_block4_fraction_net_SSE_gain']:.1%} de la ganancia espacial neta. Un porcentaje superior a100% significa que otras regiones compensan parte de esa mejora con deterioros; no es una proporción de parcelas."]
    for row in regional.itertuples():lines.append(f'Al excluir Singuilucan solo del cálculo OOF {row.protocol}, ΔRMSE vs C-T3 = {row.delta_RMSE:+.6f}, ΔMAE = {row.delta_MAE:+.6f}, con{row.n} parcelas restantes. No se reajusta ningún modelo.')
    lines+=['','CatBoost empeora RMSE de Chignahuapan en municipal y espacial, aunque su MAE municipal mejora. Excluir Hidalgo completo revierte también la ganancia espacial frente a C-T3. Las localidades con una a cinco parcelas tienen soporte reducido y no sostienen conclusiones municipales firmes.','',
        'El problema espacial no se resuelve simplemente en bloque3: CatBoost conserva sesgo positivo0.734682 frente a0.718204 de C-T3 en ese bloque, y XGBoost tiene un deterioro importante allí. La ganancia principal de CatBoost surge en el bloque4; sin ese bloque su ΔRMSE espacial es solo−0.001010 y su MAE empeora ligeramente.','',
        f"En municipal, la ganancia SSE de CatBoost {municipal.SSE_gain.sum():.6f} se descompone en mejora de sesgos por fold {municipal.bias_squared_gain.sum():.6f} y deterioro de dispersión {municipal.error_variance_gain.sum():.6f}. En espacial: ganancia SSE {space.SSE_gain.sum():.6f}, parte de sesgo {space.bias_squared_gain.sum():.6f}, parte de dispersión {space.error_variance_gain.sum():.6f}. Es una descomposición descriptiva de los errores, no una prueba causal del mecanismo.",
        '', 'Omitir las cinco parcelas con mayores ganancias conserva ventaja RMSE municipal y espacial; omitir las diez la revierte. La mejora por perfil es pequeña y se revierte al retirar incluso la parcela con mayor ganancia. Los casos permanecen en todos los ajustes y evaluaciones principales; estas omisiones solo diagnostican concentración.','',
        '## Diferencias entre parcelas del mismo clima','',
        '| Modelo | Aleatoria | Perfil | Municipal | Espacial |','|---|---:|---:|---:|---:|']
    for name in ['F7-00','F7-01','C-T3','F5-01','F6-E0']:
        lines.append('| '+name+' | '+' | '.join(f'{local.loc[(name,p),"equal_profile_RMSE"]:.6f}' for p in protocols)+' |')
    lines+=['','La tabla mide RMSE de diferencias entre parcelas, con igual peso por perfil, y no es RMSE de rendimiento individual. CatBoost empeora respecto a C-T3 en aleatoria, municipal y espacial; XGBoost empeora en los cuatro. Las ganancias agregadas municipales no prueban que estos modelos distingan mejor parcelas con clima idéntico. La lluvia compacta es constante dentro de perfil; en esta etapa MayNDVI es el único diferenciador intraperfil. Historia y pendiente podrían añadir variación local, pero ese beneficio aún no se ha probado en boosting.','',
        '## Interpretabilidad y límites','']
    effects=pd.read_csv(e.OUT/'tables/ALE_support_by_fit.csv')
    for (name,feature),g in effects.groupby(['experiment','feature']):lines.append(f'- ALE completo {name}, {feature}: {int(g.full_ALE_supported.sum())}/{len(g)} fits respaldados.')
    lines+=['','Las figuras distinguen diferencias locales respaldadas de curvas ALE completas. No se interpolan huecos sin soporte. Las interacciones lluvia–NDVI son diferencias locales mixtas de cuatro esquinas, no causas ni un screening abierto. Las interacciones con historia/pendiente se difieren porque esas variables aún no entran a modelos.','',
        'HHI concentra gran parte de PredictionValuesChange de CatBoost y de la ganancia de XGBoost, con medianas de umbral próximas a0.18. Ello describe una partición climática fuerte, potencialmente vinculada a territorio; no demuestra que cambiar concentración cause un rendimiento diferente. No hay ALE completa respaldada para HHI ni total de lluvia. MayNDVI tiene respuestas locales positivas más pronunciadas en el cuartil inferior con CatBoost; XGBoost las concentra más arriba, pero el soporte en el cuartil superior es escaso. No se afirma monotonicidad global.','',
        'Las interacciones respaldadas cubren151/585 celdas HHI–NDVI,277/585 temprana–NDVI y236/585 total–NDVI por algoritmo. Mezclan entrenamientos superpuestos y no son585 réplicas independientes. La permutación condicional de MayNDVI incrementa MSE en promedio donde es identificable, con efecto de MAE inconsistente para CatBoost. Uso frecuente no garantiza mejora intraperfil ni aporte incremental frente a un boosting de lluvia sola, que aquí no fue ajustado.','',
        'La permutación de lluvia3 es conjunta y condicionada al perfil: al ser constante en ese perfil, su utilidad no es identificable por esta permutación. Esto no equivale a irrelevancia. MayNDVI se evalúa solo con pares/clases suficientes dentro del perfil y no controla todas las demás variables. Frecuencia de partición, PredictionValuesChange de CatBoost y ganancia media de XGBoost son medidas descriptivas diferentes; no se comparan como escalas equivalentes ni importancia causal. Hojas simétricas pueden estar vacías o tener pocas observaciones, pese a L2; el soporte real se registra.','',
        'Pares intraperfil usan solo parcelas evaluadas por el mismo modelo externo, con resultados de igual peso por perfil y ponderación por pares. Su soporte puede ser reducido fuera de Chignahuapan. No se entregan intervalos predictivos de boosting: ni variación entre árboles ni dispersión de OOF proporciona cobertura calibrada.','',
        '## Próximo paso','',
        'Recomiendo continuar, tras revisión, con las ablaciones acotadas CatBoost E1/E2/E3 ya predefinidas. La razón metodológica es que árboles simétricos regularizados pueden corregir sesgos regionales mejor que Extra Trees con compact4, pero aún fallan en la discriminación intraperfil. Historia NDVI2 y pendiente introducen variación dentro de perfiles que la lluvia no ofrece; las ablaciones deben comprobar si esa variación reduce errores locales sin perder los beneficios municipales. Esta es una hipótesis pendiente, no garantía de que los complementos mejoren. No recomiendo expandir XGBoost usando su RMSE municipal aislado: por perfil y espacial empeora frente a C-T3.','',
        'La evidencia apoya capacidad no lineal para corregir ciertos niveles regionales; debilita la hipótesis de superioridad general o mejora homogénea intraperfil del boosting compacto. No descarta otras regularizaciones o todos los modelos de boosting. Los límites se mantienen:300 árboles seleccionados con frecuencia y poca profundidad son resultados de una búsqueda acotada, no evidencia de óptimo global. No se amplían tras ver las OOF.','',
        'El próximo residual propuesto, después de revisar las ablaciones, es una base C-T3 compacta más una corrección CatBoost pequeña sobre MayNDVI, historia NDVI2 y pendiente, con amplitud de corrección que pueda elegirse como cero mediante validación interna. Los targets de corrección deben generarse por cross-fitting del núcleo exclusivamente dentro de cada entrenamiento correspondiente; cada evaluación interna debe repetir la construcción sin ver sus etiquetas de validación. Posteriormente se reajusta el núcleo sobre todo ese entrenamiento y se suma la corrección. Esa construcción difiere de usar residuos ajustados sobre las mismas filas, de residuos OOF globales y de corregir el Champion. Se propone para preservar una tendencia lineal y estudiar señales locales; no se presupone mejor extrapolación y no se ejecuta ahora.','',
        'La ejecución se detiene aquí para revisión antes de E1–E3. CatBoost se asignó antes de las OOF, y cualquier cambio posterior de algoritmo motivado por resultados externos se documentará como exploratorio. No se ejecuta residual, no se promueve champion y no se generan59 PRED.','',
        'Fuentes técnicas: [CatBoost: parameter tuning](https://catboost.ai/docs/en/concepts/parameter-tuning), [XGBoost: parameters](https://xgboost.readthedocs.io/en/stable/parameter.html).','']
    (e.OUT/'report/synthesis.md').write_text('\n'.join(lines),encoding='utf8')
