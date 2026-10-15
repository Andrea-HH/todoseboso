"""Explicit exploratory answers based on frozen OOF; no combination selection."""
import json
import numpy as np,pandas as pd
from . import execution as e
def write(summary):
    protocols=['random','climate_profile','municipality','spatial'];m=summary.set_index(['experiment','protocol'])
    paired=pd.read_csv(e.OUT/'tables/expansion_paired_summary.csv')
    intra=pd.read_csv(e.OUT/'tables/intraprofile_metrics_summary.csv');intra=intra[intra.scope.eq('all')].set_index(['experiment','protocol'])
    decision=dict(executed=list(e.SPECS),no_champion_promotion=True,no_ensemble=True,no_residual=True,no_final_training=True,no_PRED=True,statistical_superiority_claimed=False,answers=[])
    lines=['# F7 — Expansión controlada de CatBoost','',
        'Se ejecutaron exclusivamente E1 historia NDVI2, E2 pendiente media y E3 ambos, con el modelo CatBoost y las ocho configuraciones previamente congeladas. Cada variante seleccionó dentro de cuatro particiones internas de cada entrenamiento externo. F7-00/F7-01 y todos los controles se recuperaron sin ajustes ni cambios.','',
        '## Resultados completos OOF','',
        '| Modelo | Aleatoria | Perfil | Municipal | Espacial |','|---|---:|---:|---:|---:|']
    for name in ['F7-00',*e.SPECS,'C-T3','F5-01','F6-E1','F6-E2']:
        lines.append('| '+name+' | '+' | '.join(f'{m.loc[(name,p),"RMSE"]:.6f}' for p in protocols)+' |')
    lines+=['','RMSE t/ha: métricas sobre138 OOF completas por repetición; aleatoria promedia10 repeticiones. MAE y sesgo conservan idéntico procedimiento. Los resultados por fold sirven para diagnósticos y no reemplazan estas métricas. Champion solo se compara en los50 folds aleatorios compatibles, sin reconstrucción territorial. ID_POLIGONO es el identificador parcelario real del proyecto.','',
        '## Respuestas sobre bloques y complementariedad','']
    for name,question in [('F7-E1','1. ¿Historia NDVI2 mejora CatBoost compacto?'),('F7-E2','2. ¿Pendiente aporta información incremental?'),('F7-E3','3. ¿La combinación supera los modelos individuales?')]:
        lines+=['### '+question,'']
        z=paired[(paired.candidate==name)&(paired.baseline=='F7-00')]
        answer=dict(experiment=name,deltas_vs_core=z[['protocol','delta_RMSE','delta_MAE','delta_bias']].to_dict('records'))
        for row in z.itertuples():lines.append(f'- {row.protocol}: ΔRMSE {row.delta_RMSE:+.6f}, ΔMAE {row.delta_MAE:+.6f}, Δsesgo {row.delta_bias:+.6f}.')
        if name=='F7-E3':
            for b in ['F7-E1','F7-E2']:
                zz=paired[(paired.candidate==name)&(paired.baseline==b)]
                for row in zz.itertuples():lines.append(f'- E3 vs {b}, {row.protocol}: ΔRMSE {row.delta_RMSE:+.6f}, ΔMAE {row.delta_MAE:+.6f}.')
        decision['answers'].append(answer)
    lines+=['','Las ablaciones reajustadas son la evidencia incremental principal: cada representación se retunea internamente. Las importancias no sustituyen esta comparación. E3 es un modelo conjunto nuevo; no se suman ganancias E1/E2.','']
    lines+=['### 4. ¿Mejora la discriminación intraperfil?','',
        '| Modelo | Aleatoria | Perfil | Municipal | Espacial |','|---|---:|---:|---:|---:|']
    for name in ['F7-00',*e.SPECS]:lines.append('| '+name+' | '+' | '.join(f'{intra.loc[(name,p),"equal_profile_RMSE"]:.6f}' for p in protocols)+' |')
    lines+=['','RMSE de diferencias de rendimiento, igual peso por perfil, distinto del RMSE de rendimiento individual. Ponderación por pares, MAE, conteos y resultados dentro/fuera de Chignahuapan están separados. Solo se usan parejas del mismo modelo externo. Cada repetición aleatoria tiene soporte propio; promedios de conteos por repetición no son muestras independientes. Las tablas marcan soporte reducido si hay menos de10 parcelas o3 perfiles: dichos resultados son descriptivos y no conclusiones robustas.','']
    for name in e.SPECS:
        better=[p for p in protocols if intra.loc[(name,p),'equal_profile_RMSE']<intra.loc[('F7-00',p),'equal_profile_RMSE']]
        lines.append(f'- {name}: menor RMSE intraperfil de igual peso en {len(better)}/4 protocolos: {", ".join(better) if better else "ninguno"}.')
    lines+=['','### 5. ¿Las ganancias territoriales son estables?','']
    regions=pd.read_csv(e.OUT/'tables/region_omission_summary.csv')
    folds=pd.read_csv(e.OUT/'tables/fold_omission_sensitivity.csv')
    counts=pd.read_csv(e.OUT/'tables/territorial_improvement_counts.csv')
    for name in e.SPECS:
        for p in ['municipality','spatial']:
            q=regions[(regions.candidate==name)&(regions.protocol==p)&regions.omitted_region.eq('Singuilucan')&regions.omitted_type.eq('Municipio')]
            row=q.iloc[0];c=counts[(counts.experiment==name)&(counts.protocol==p)].iloc[0]
            lines.append(f'- {name}, {p}: al omitir Singuilucan, ΔRMSE {row.delta_RMSE:+.6f}, ΔMAE {row.delta_MAE:+.6f}. Mejoran RMSE {int(c.folds_RMSE_improve)}/{int(c.n_folds)} folds y{int(c.municipalities_RMSE_improve)}/{int(c.n_municipalities)} municipios; entre municipios de≥10 parcelas: {int(c.municipalities_ge10_RMSE_improve)}/{int(c.municipalities_ge10)}.')
    lines+=['','Todas las omisiones recalculan OOF sin reajustar. Las tablas incluyen cada municipio, estado y bloque; sesgo, SSE de sesgo versus dispersión y omisiones de1/5/10 beneficiarios. Se estudian Singuilucan/bloque4, Chignahuapan y bloque3 junto con el resto, sin optimizarlos. Mejorar un nivel regional no demuestra discriminación intraperfil ni generalización a años diferentes. Municipios con una a cinco parcelas requieren cautela.','',
        '### 6. ¿Los errores justifican una arquitectura combinada?','']
    cov=pd.read_csv(e.OUT/'tables/error_covariance_repeat.csv')
    for (a,b),g in cov.groupby(['model_a','model_b']):
        lines.append(f'- {a} vs {b}: correlaciones medias por protocolo '+', '.join(f'{p}={gg.error_correlation.mean():.3f}' for p,gg in g.groupby('protocol'))+'.')
    lines+=['','Correlaciones, covarianzas poblacionales, sesgo y dirección común de errores se conservan por repetición, sin mezclar10 repeticiones como1380 parcelas independientes. El análisis por cuartil del error del núcleo es posterior al ajuste: una relación entre ganancia y error base tiene acoplamiento algebraico y no valida un gate predictivo. Los casos donde historia/pediente ayudan y donde ambos perjudican son descriptivos; no se entrena un selector por parcela, no se calculan pesos óptimos, ni se entrega un resultado de ensemble o stacking.','',
        '### 7. Base y posibles correctores','',
        'La recomendación debe distinguir el control compacto F7-00 de señales locales que puedan corregir sus errores. Las correlaciones por sí solas no justifican una combinación; se requiere mejora incremental territorial y/o intraperfil y suficiente soporte. Un residual futuro usaría cross-fitting del núcleo dentro de cada entrenamiento correspondiente y regularización de amplitud que incluya corrección cero, seleccionada solo internamente. No utilizaría residuos OOF globales como targets, ni el Champion como fuente de targets. Aquí no se ejecuta ninguna combinación.','',
        '## Interpretabilidad','',
        'Historia2 se permuta conjuntamente, lluvia3 conjuntamente, MayNDVI y pendiente por separado, condicionando al mismo perfil de validación. Se exige soporte del entrenamiento para las combinaciones generadas y mínimo10 parcelas respaldadas; no se fabrica importancia cero cuando el efecto no es identificable. El radio en espacio preprocesado es empírico y no garantiza soporte causal; el cambio de dimensiones cambia ese espacio entre variantes. Ablación reajustada y permutación condicionada responden preguntas distintas.','']
    support=pd.read_csv(e.OUT/'tables/ALE_support_by_fit.csv')
    for (name,c),g in support.groupby(['experiment','feature']):
        if c not in e.CORE:lines.append(f'- ALE completa {name}, {c}: {int(g.full_ALE_supported.sum())}/{len(g)} ajustes respaldados.')
    lines+=['','Donde no hay ALE completa respaldada se muestran diferencias locales y no se unen huecos. Interacciones predefinidas incluyen lluvia–NDVI, NDVI–historia, lluvia–pendiente e historia–pendiente. Son diferencias mixtas de cuatro esquinas respaldadas, no causas. PredictionValuesChange, frecuencia de niveles compartidos y estabilidad de umbrales son descriptivos; una variable muy utilizada puede perjudicar validación. Las hojas reales, incluidas vacías y pequeñas, se registran porque SymmetricTree no impone mínimo de observaciones mediante min_data_in_leaf.','',
        '## Síntesis de decisión: las siete preguntas','',
        '1. **Historia NDVI2 no mejora el modelo directo compacto:** RMSE empeora en los cuatro protocolos. Hay señales locales bajo ponderación igual por perfil y fuera de Chignahuapan, pero no compensan el coste absoluto, especialmente espacial. La leve reducción de MAE por perfil no constituye una mejora global.','',
        '2. **Pendiente ofrece una señal intraperfil parcial, no ganancia predictiva global directa:** su RMSE absoluto también empeora en los cuatro protocolos. Es la extensión menos costosa espacialmente y mejora diferencias espaciales al dar igual peso a perfiles, pero perjudica la ponderación global por parejas.','',
        '3. **E3 no combina eficazmente ambas señales:** empeora frente al núcleo en todos los RMSE; es peor que E1 y E2 en aleatoria, perfil y municipal. Espacialmente mejora un poco a E1, pero es claramente peor que E2. No hay evidencia de sinergia predictiva global.','',
        '4. **La respuesta intraperfil depende de la ponderación y del territorio:** E1/E3 mejoran RMSE de igual peso en aleatoria, perfil y espacial; E2 en aleatoria, municipal y espacial. Sin embargo, las tres empeoran RMSE y MAE ponderados por parejas en los cuatro protocolos. En espacial, fuera de Chignahuapan, tanto igual peso como por parejas mejoran; dentro de Chignahuapan se deterioran. Este último contraste dispone de62 parcelas pero solo2 perfiles, frente a43 parcelas/10 perfiles fuera. No constituye una regla geográfica de modelado.','',
        '5. **No hay una ganancia absoluta estable que dependa solamente de Singuilucan:** los deterioros municipal/espacial frente a F7-00 persisten al excluir Singuilucan o Chignahuapan. Historia y E3 mejoran bloque4, pero empeoran los otros cuatro; pendiente mejora bloques2/4 y empeora1/3/5. En bloque3 el sesgo pasa de0.734682 a0.999336 con historia,0.838679 con pendiente y0.986276 con E3. El deterioro espacial de historia/E3 es principalmente de sesgo regional, no una mejora general trasladada al resto.','',
        '6. **Hay casos complementarios, pero poca diversidad global para justificar promediar estos modelos:** las correlaciones espaciales de errores núcleo–E1/E2/E3 son0.957/0.984/0.957 y E1–E3 es0.993. En spatial, E1 y E2 mejoran conjuntamente20.3% de parcelas; historia sola13.0%, pendiente sola26.1%, ninguno40.6%. E3 mejora solo16.7% del subconjunto beneficiado exclusivamente por pendiente, por lo que no preserva bien esa fortaleza. No se ha probado un ensemble; correlación alta tampoco demuestra imposibilidad matemática de toda combinación.','',
        '7. **Conservar F7-00 compact4 como base de esta familia, sin promoción.** No usar E1/E2/E3 completos como correctores listos para sumar. Si se autoriza una próxima investigación, priorizar una corrección de pendiente pequeña, con contracción y foco metodológico intraperfil, y reservar historia2 como sensibilidad secundaria. El núcleo debe generar targets residuales mediante cross-fitting exclusivamente dentro de cada entrenamiento. El corrector y su amplitud —incluido cero— se seleccionarán internamente; la ponderación de perfiles y el soporte requieren diseño previo, sin gates municipales ni reglas regionales. Revisar antes los resultados de F4/Etapas B–C sobre objetivos intraperfil para evitar duplicar arquitecturas. Preferir este contraste acotado a stacking/promedio de las extensiones completas; ninguno se ejecuta ahora.','',
        'Los deterioros municipales de F6-E no desaparecen con CatBoost. Aunque afectan a menos parcelas que en Extra Trees, persisten muchas de las mismas:48.6% de todas las parcelas se deterioran con historia en ambas familias y54.3% con pendiente. Cada incremento se mide contra el núcleo de su propia arquitectura. Superar los RMSE municipales absolutos de F6-E1/E2 no demuestra que los bloques hayan ayudado a CatBoost.','',
        'Las variables se utilizan de manera frecuente pese al deterioro: en espacial historia mean/std entra en aproximadamente38%/35% de árboles de E1 y pendiente en31% de E2. Los umbrales medianos históricos rondan0.30/0.13; pendiente muestra umbrales variables entre entrenamientos. Esto describe particiones aprendidas, no causalidad ni estabilidad de una recomendación agronómica. El soporte de ALE completas es escaso. Permutación espacial de historia E3 no es identificable con el gate establecido; en municipal ningún bloque adicional alcanza soporte, lo que no equivale a irrelevancia.','',
        'El resultado debilita que CatBoost directo, con esta búsqueda y muestra, pueda integrar las señales locales sin coste territorial. Conserva la hipótesis de señal intraperfil fuera de perfiles dominantes, pero no demuestra un corrector residual útil ni irrelevancia agronómica de historia o pendiente. No permite rechazar todos los CatBoost ni todas las arquitecturas jerárquicas.','',
        '## Límites y cierre','',
        'Se detiene tras las tres ablaciones, sin nuevos predictores, nuevos screenings, XGBoost reajustado, límites ampliados, ensemble, stacking, residuos, modelo final,59 PRED o promoción del Champion. Todas las comparaciones y recomendaciones son exploratorias sobre etiquetas y folds reutilizados; no se afirma superioridad estadística.','']
    (e.OUT/'report/synthesis.md').write_text('\n'.join(lines),encoding='utf8')
    decision.update(recommendation='retain_F7-00; stop direct expansion; propose bounded internally-crossfitted slope correction only after review',history_direct_improves=False,slope_direct_improves=False,joint_synergy_demonstrated=False,intraprofile_signal='partial equal-profile/outside-Chignahuapan; global pair-weighted deterioration',ensemble_justified_as_next_execution=False,proposed_base='F7-00 compact4',proposed_primary_correction='slope small/shrunk, not full E2 predictions',proposed_secondary_sensitivity='history NDVI2 only after reviewing primary correction',no_region_specific_rules=True)
    (e.OUT/'report/decision.json').write_text(json.dumps(decision,indent=2),encoding='utf8')
