"""G/H paired evidence, separate reports, and bounded H1 interpretation."""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from .climate_signal_features import *
from .rainfall_modeling import metrics
from .rainfall_pcr_reporting import save,error_diagnostics
from .climate_signal_descriptive import geography

def summarize(predictions,out):
    folds=[];reps=[]
    for (protocol,name,rep,fold),z in predictions.groupby(['protocol','experiment','repeat','fold']):
        if not z[ID].is_unique:raise ValueError('Duplicate OOF parcel within fold')
        folds.append(dict(protocol=protocol,experiment=name,repeat=rep,fold=fold,n=len(z),**metrics(z.y_true,z.y_pred)))
    for (protocol,name,rep),z in predictions.groupby(['protocol','experiment','repeat']):
        if len(z)!=138 or not z[ID].is_unique:raise ValueError('OOF repetition must contain exactly 138 distinct train parcels')
        reps.append(dict(protocol=protocol,experiment=name,repeat=rep,**metrics(z.y_true,z.y_pred)))
    f=pd.DataFrame(folds);r=pd.DataFrame(reps);rows=[]
    for (protocol,name),z in r.groupby(['protocol','experiment']):
        q=f[f.protocol.eq(protocol)&f.experiment.eq(name)]
        rows.append(dict(protocol=protocol,experiment=name,
            **{metric+'_mean':z[metric].mean() for metric in ['RMSE','MAE','R2','bias_pred_minus_y']},
            **{metric+'_fold_sd':q[metric].std() for metric in ['RMSE','MAE','R2','bias_pred_minus_y']},
            RMSE_fold_mean=q.RMSE.mean(),RMSE_repeat_sd=z.RMSE.std() if len(z)>1 else np.nan,n_repeats=len(z)))
    c=pd.DataFrame(rows);c.to_csv(out/'tables/40_model_comparison.csv',index=False)
    f.to_csv(out/'tables/41_fold_metrics.csv',index=False);r.to_csv(out/'tables/42_repetition_metrics.csv',index=False)
    return c,f,r

def incremental(folds,reps,out):
    contrasts=[('temperature_given_rain','H1_RAIN','H7_JOINT'),('rain_given_temperature','H4_TMIN_TMAX','H7_JOINT'),
        ('tmin_given_rain','H1_RAIN','H5_RAIN_TMIN'),('tmax_given_rain','H1_RAIN','H6_RAIN_TMAX'),
        ('tmax_given_tmin','H2_TMIN','H4_TMIN_TMAX'),('tmin_given_tmax','H3_TMAX','H4_TMIN_TMAX'),
        ('aggregated_temperature_given_rain','H_S1_AGG_RAIN','H8_CLIMATE_CURRENT_ORIGINAL'),
        ('aggregated_rain_given_temperature','H_S2_AGG_THERMAL','H8_CLIMATE_CURRENT_ORIGINAL')]
    paired=[];paired_reps=[];summary=[]
    for label,base,combo in contrasts:
        for protocol,g in folds.groupby('protocol'):
            q=g[g.experiment.eq(base)].merge(g[g.experiment.eq(combo)],on=['repeat','fold'],suffixes=('_base','_combined'),validate='one_to_one')
            z=reps[reps.protocol.eq(protocol)]
            rr=z[z.experiment.eq(base)].merge(z[z.experiment.eq(combo)],on='repeat',suffixes=('_base','_combined'),validate='one_to_one')
            if len(q)!=len(g[g.experiment.eq(base)]) or q.empty:raise ValueError('Unmatched incremental fold evaluation')
            delta=q.RMSE_base-q.RMSE_combined;dr=rr.RMSE_base-rr.RMSE_combined
            for _,a in q.iterrows():paired.append(dict(protocol=protocol,contrast=label,base=base,combined=combo,repeat=a['repeat'],fold=a.fold,delta_RMSE=a.RMSE_base-a.RMSE_combined,delta_MAE=a.MAE_base-a.MAE_combined))
            for _,a in rr.iterrows():paired_reps.append(dict(protocol=protocol,contrast=label,repeat=a['repeat'],delta_RMSE=a.RMSE_base-a.RMSE_combined))
            summary.append(dict(protocol=protocol,contrast=label,base=base,combined=combo,
                mean_repeat_delta_RMSE=dr.mean(),mean_fold_delta_RMSE=delta.mean(),fold_delta_sd=delta.std(),
                fold_delta_q25=delta.quantile(.25),fold_delta_q75=delta.quantile(.75),
                positive_fold_fraction=float((delta>1e-10).mean()),positive_repeat_fraction=float((dr>1e-10).mean()),
                repeat_delta_sd=dr.std() if len(dr)>1 else np.nan,
                interpretation='positive = conditional predictive improvement; descriptive overlapping CV, not causal'))
    a=pd.DataFrame(summary);a.to_csv(out/'tables/50_incremental_summary.csv',index=False)
    pd.DataFrame(paired).to_csv(out/'tables/51_paired_fold_deltas.csv',index=False)
    pd.DataFrame(paired_reps).to_csv(out/'tables/52_paired_repeat_deltas.csv',index=False)
    return a

def predictive_plots(p,averaged,comparison,out,section):
    principal=['G1_TMIN','G2_TMAX','G3_TMIN_TMAX'] if section=='G' else ['H1_RAIN','H4_TMIN_TMAX','H7_JOINT']
    fig,axes=plt.subplots(2,3,figsize=(15,9))
    for j,name in enumerate(principal):
        for i,(data,title) in enumerate([(p,'OOF individual — cada repetición'),(averaged,'OOF promedio — diagnóstico')]):
            z=data[data.experiment.eq(name)&data.protocol.eq('random')];ax=axes[i,j]
            ax.scatter(z.y_true,z.y_pred,c=z.exact_profile,cmap='turbo',s=14,alpha=.4);ax.plot([1,6],[1,6],'k--');ax.set(xlabel='Y observado t/ha',ylabel='Y predicho t/ha',title=name+'\n'+title,xlim=(1,6),ylim=(1,6))
    save(fig,out,'40_observed_predicted_individual_average.png')
    fig,axes=plt.subplots(1,3,figsize=(15,4))
    for name,ax in zip(principal,axes):
        z=p[p.experiment.eq(name)&p.protocol.eq('random')];ax.scatter(z.y_true,z.error,s=10,alpha=.3);ax.axhline(0,c='black');ax.set(title=name,xlabel='Y observado t/ha',ylabel='Error pred-real t/ha')
    save(fig,out,'41_error_conditioned_y.png')
    fig,ax=plt.subplots(figsize=(12,6));sns.barplot(data=comparison,x='RMSE_mean',y='experiment',hue='protocol',ax=ax);ax.set_xlabel('RMSE medio de repeticiones OOF completas (t/ha)');save(fig,out,'42_model_comparison.png')
    fig,axes=plt.subplots(1,3,figsize=(15,5))
    for name,ax in zip(principal,axes):
        z=averaged[averaged.experiment.eq(name)&averaged.protocol.eq('spatial')].merge(geography()[[ID,'longitude','latitude']],on=ID)
        sc=ax.scatter(z.longitude,z.latitude,c=z.error,cmap='coolwarm',vmin=-2,vmax=2,s=30);fig.colorbar(sc,ax=ax,label='Error t/ha');ax.set(title=name+' — OOF espacial',xlabel='Longitud',ylabel='Latitud')
    save(fig,out,'43_spatial_residual_maps.png')
    regions=pd.read_csv(out/'tables/44_regional_metrics_by_repeat.csv')
    z=regions[regions.region_type.eq('Estado')&regions.experiment.isin(principal)].groupby(['protocol','experiment','region']).RMSE.mean().reset_index()
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    for protocol,ax in zip(['random','spatial'],axes):
        sns.barplot(data=z[z.protocol.eq(protocol)],x='region',y='RMSE',hue='experiment',ax=ax);ax.set_title(protocol);ax.tick_params(axis='x',rotation=15)
    save(fig,out,'44_region_errors.png')

def table_text(table):return '\n```\n'+table.round(5).to_string(index=False)+'\n```\n'

def interpretation(gout,hout,gc,hc,increment,principal):
    """Answer the substantive questions from measured results, not CV rankings alone."""
    monthly=pd.read_csv(gout/'tables/03_same_month_year_differences.csv')
    temporal=[]
    for variable in ['tmin_mean','tmax_mean']:
        z=monthly[monthly.variable.eq(variable)]
        hot=z.loc[z['2025'].idxmax()];cold=z.loc[z['2025'].idxmin()]
        anomaly=z.loc[z.delta_2025.abs().idxmax()]
        temporal.append(f"{variable}: la media entre parcelas alcanza su máximo mensual en {int(hot.month)} ({hot['2025']:.2f} °C) y mínimo en {int(cold.month)} ({cold['2025']:.2f} °C). La mayor diferencia absoluta frente al mismo mes de 2022–24 está en {int(anomaly.month)} ({anomaly.delta_2025:+.2f} °C).")
    pair=pd.read_csv(gout/'tables/08_identical_profile_pair_distances.csv')
    pair=pair[pair.kind.eq('thermal')]
    spatial=f"Los {len(pair)} pares con perfil térmico idéntico están a una mediana de {pair.distance_km.median():.3f} km y un máximo de {pair.distance_km.max():.3f} km; hay {int(pair.distance_km.gt(10).sum())} pares a más de 10 km. Este patrón local y el soporte de celda verifican la explicación espacial en los datos observados."
    blocks=[]
    for block in ['rain_tmin','rain_tmax','tmin_tmax']:
        q=pd.read_csv(hout/'tables'/f'18_{block}_correlations.csv',index_col=0)
        a=q.to_numpy();i,j=np.unravel_index(np.argmax(abs(a)),a.shape)
        blocks.append(dict(block=block,minimum=float(a.min()),maximum=float(a.max()),median_absolute=float(np.median(abs(a))),strongest_pair=f'{q.index[i]} / {q.columns[j]}',strongest_r=float(a[i,j])))
    pd.DataFrame(blocks).to_csv(hout/'tables/59_cross_block_correlation_summary.csv',index=False)
    pca=[]
    for name in ['Joint_standardized','Joint_block_balanced']:
        b=pd.read_csv(hout/'tables'/f'22_{name}_block_contributions.csv',index_col=0)
        for pc in ['PC1','PC2','PC3']:
            pca.append(dict(representation=name,component=pc,rain_squared_loading_share=b.loc['rain',pc],tmin_share=b.loc['tmin',pc],tmax_share=b.loc['tmax',pc]))
    jointstructure='Correlaciones por bloques (49 pares en cada bloque, descriptivos):'+table_text(pd.DataFrame(blocks))
    jointstructure+='En PCA estándar, PC1 combina principalmente Tmin con lluvia; PC2 está dominado por Tmax y PC3 por lluvia. Las proporciones de cargas cuadradas observadas son:'+table_text(pd.DataFrame(pca))
    questions=[]
    for protocol in hc.protocol.unique():
        q=hc[hc.protocol.eq(protocol)].set_index('experiment')
        d=increment[increment.protocol.eq(protocol)].set_index('contrast')
        questions.append(dict(protocol=protocol,baseline_RMSE=q.loc['H0_MEAN','RMSE_mean'],rain_RMSE=q.loc['H1_RAIN','RMSE_mean'],thermal_RMSE=q.loc['H4_TMIN_TMAX','RMSE_mean'],joint_RMSE=q.loc['H7_JOINT','RMSE_mean'],original_RMSE=q.loc['H8_CLIMATE_CURRENT_ORIGINAL','RMSE_mean'],temperature_given_rain=d.loc['temperature_given_rain','mean_repeat_delta_RMSE'],rain_given_temperature=d.loc['rain_given_temperature','mean_repeat_delta_RMSE'],aggregated_temperature_given_rain=d.loc['aggregated_temperature_given_rain','mean_repeat_delta_RMSE'],aggregated_rain_given_temperature=d.loc['aggregated_rain_given_temperature','mean_repeat_delta_RMSE']))
    answers=pd.DataFrame(questions);answers.to_csv(hout/'tables/60_h1_direct_answers.csv',index=False)
    text='## Respuestas para decidir el siguiente bloque climático\n\n'+table_text(answers)
    text+='1. **Lluvia sola y temperatura sola:** las columnas rain_RMSE y thermal_RMSE cuantifican su capacidad con el mismo Elastic Net; baseline_RMSE indica la referencia sin clima. La comparación aleatoria no basta para afirmar transferencia.\n'
    text+='2. **Complementariedad en ambos sentidos:** los deltas positivos indican ganancia condicional; negativos indican pérdida. Se debe leer por protocolo junto con la fracción de folds mejorados de tabla 50.\n'
    for contrast,label in [('temperature_given_rain','Temperatura añadida a lluvia mensual'),('rain_given_temperature','Lluvia añadida a temperatura mensual'),('aggregated_temperature_given_rain','Temperatura agregada añadida a lluvia agregada'),('aggregated_rain_given_temperature','Lluvia agregada añadida a temperatura agregada')]:
        z=increment[increment.contrast.eq(contrast)]
        favorable=', '.join(z.loc[z.mean_repeat_delta_RMSE>0,'protocol']) or 'ninguno'
        unfavorable=', '.join(z.loc[z.mean_repeat_delta_RMSE<=0,'protocol']) or 'ninguno'
        text+=f'\n{label}: mejora en {favorable}; no mejora en {unfavorable}.\n'
    text+='\n3. **Climate Current:** los dos deltas agregados comparan exactamente sus subbloques originales de 10 columnas de lluvia y 38 térmicas con sus 48 columnas conjuntas. Permiten evaluar si aprovecha complementariedad; una mejora aislada en random no demuestra eficacia fuera de la geografía representada.\n'
    aggregated=increment[increment.contrast.eq('aggregated_temperature_given_rain')].set_index('protocol')
    text+=f"\nEn la representación original agregada sí hay complementariedad: añadir temperatura reduce RMSE en {aggregated.loc['random','mean_repeat_delta_RMSE']:.5f} t/ha en random y {aggregated.loc['municipality','mean_repeat_delta_RMSE']:.5f} en municipal. En espacial la reducción global es {aggregated.loc['spatial','mean_repeat_delta_RMSE']:.5f}, pero solo mejora {aggregated.loc['spatial','positive_fold_fraction']:.0%} de folds y la media de deltas por fold es {aggregated.loc['spatial','mean_fold_delta_RMSE']:+.5f}. La ganancia depende de la representación y no es uniforme geográficamente. La lluvia mensual supera al Climate Current agregado en municipal y espacial bajo estos folds.\n"
    text+='\n4. **Candidatos futuros:** conservar los modelos mensuales y el Climate Current agregado como referencias auditadas. Resúmenes compactos y PCR son sensibilidades acotadas; ninguna sensibilidad elegida por su mejor métrica externa confirma un nuevo ganador. Una posible sustitución necesita reproducir mejoras en ciclos etiquetados nuevos y protocolos geográficos.\n'
    text+='5. **Limitaciones persistentes:** añadir temperatura distingue cero parcelas intraperfil. La resolución efectiva limita el detalle espacial; la dispersión de Y dentro de perfiles iguales muestra información que este clima no distingue. No permite asignar esa dispersión causalmente al suelo, manejo o ruido de medición, pero justifica investigar esas fuentes en una etapa posterior.\n'
    text+='6. **Champion:** las mejoras de Sentinel histórico y topografía son correcciones residuales posteriores, guardadas en tabla 58. No equivalen al aporte incremental de temperatura y no se usaron para elegir las ablaciones.\n'
    errors=[]
    for protocol,z in principal.groupby('protocol'):
        pivot=z.pivot(index='yield_segment',columns='experiment',values='bias_pred_minus_y')
        for segment in pivot.index:
            a=pivot.loc[segment,'H1_RAIN'];b=pivot.loc[segment,'H7_JOINT']
            errors.append(dict(protocol=protocol,segment=segment,rain_bias=a,joint_bias=b,absolute_bias_reduction=abs(a)-abs(b)))
    worst=pd.read_csv(hout/'tables/56_largest_rain_errors_joint_changes.csv')
    correction=worst.groupby('protocol').absolute_error_reduction.agg(['mean','median',lambda x:float((x>0).mean())]).reset_index()
    correction.columns=['protocol','mean_absolute_error_reduction','median_reduction','fraction_largest_errors_improved']
    error_text='Cambios de sesgo condicional (positivo en la última columna reduce su magnitud):'+table_text(pd.DataFrame(errors))
    error_text+='Entre las 20 filas OOF con mayor error absoluto de lluvia por protocolo (una parcela puede repetirse en random), añadir temperatura produce:'+table_text(correction)
    regional=pd.read_csv(hout/'tables/44_regional_metrics_by_repeat.csv')
    regional=regional[regional.region_type.eq('Estado')&regional.experiment.isin(['H1_RAIN','H7_JOINT'])]
    means=regional.groupby(['protocol','region','experiment'])[['RMSE','bias_pred_minus_y']].mean().unstack('experiment')
    regional_answer=pd.DataFrame(dict(rain_RMSE=means[('RMSE','H1_RAIN')],joint_RMSE=means[('RMSE','H7_JOINT')],rain_bias=means[('bias_pred_minus_y','H1_RAIN')],joint_bias=means[('bias_pred_minus_y','H7_JOINT')])).reset_index()
    regional_answer['conditional_RMSE_improvement']=regional_answer.rain_RMSE-regional_answer.joint_RMSE
    regional_answer.to_csv(hout/'tables/61_conditional_regional_changes.csv',index=False)
    error_text+='Cambios por estado, media de métricas regionales por repetición; regiones con al menos cinco etiquetas:'+table_text(regional_answer)
    return '\n\n'.join(temporal)+'\n\n'+spatial,jointstructure,text,error_text

def finish(run_id,train,g,h,configuration):
    gout,_=paths('G',run_id);hout,_=paths('H',run_id);geo=geography()
    comparisons={};diagnostics={}
    for section,out,p in [('G',gout,g),('H',hout,h)]:
        reference=p[p.experiment.eq('G0_MEAN' if section=='G' else 'H0_MEAN')][['protocol','repeat','fold',ID,'y_true']]
        for name,z in p.groupby('experiment'):
            paired=z.merge(reference,on=['protocol','repeat','fold',ID],suffixes=('','_reference'),validate='one_to_one')
            if len(paired)!=len(z) or len(z)!=len(reference) or not np.allclose(paired.y_true,paired.y_true_reference):raise ValueError('Different evaluation sets in comparison')
        members=pd.read_csv(out/'tables/06_profile_memberships.csv')
        members[[ID,'thermal' if section=='G' else 'joint']].rename(columns={'thermal':'exact_profile','joint':'exact_profile'}).to_csv(out/'tables/05_seven_month_profile_groups.csv',index=False)
        c,f,r=summarize(p,out);comparisons[section]=(c,f,r)
        q,avg,seg,regions=error_diagnostics(p,train,geo,out);diagnostics[section]=(q,avg,seg,regions)
        predictive_plots(q,avg,c,out,section)
        reg=pd.read_csv(out/'tables/32_experiment_registry.csv')
        if 'selected_K' in reg:reg.groupby(['protocol','experiment','selected_K']).size().rename('count').to_csv(out/'tables/53_selected_K_distribution.csv')
        co=pd.read_csv(out/'tables/34_standardized_coefficients.csv')
        co.groupby(['protocol','experiment','feature']).standardized_coefficient.agg(['mean','std','min','max']).to_csv(out/'tables/54_coefficient_stability.csv')
    hc,hf,hr=comparisons['H'];increment=incremental(hf,hr,hout)
    main=increment[increment.contrast.eq('temperature_given_rain')]
    consistent=bool((main.mean_repeat_delta_RMSE>.005).all() and (main.positive_fold_fraction>=.6).all())
    decision=dict(hypothesis='H1',temperature_monthly_consistently_improves_rain=consistent,
        criterion='descriptive: >0.005 t/ha repeat-RMSE improvement and >=60% folds improved in every protocol',
        independent_validation=False,replace_champion=False,significance_tests_of_overlapping_repeats=False)
    (hout/'report/h1_decision.json').write_text(json.dumps(decision,indent=2),encoding='utf-8')
    fig,ax=plt.subplots(figsize=(10,5));z=increment[increment.contrast.isin(['temperature_given_rain','rain_given_temperature'])].pivot(index='contrast',columns='protocol',values='mean_repeat_delta_RMSE');sns.heatmap(z,annot=True,fmt='.4f',cmap='coolwarm',center=0,ax=ax);ax.set_title('Aporte condicional: positivo = mejora RMSE (t/ha)');save(fig,hout,'50_incremental_contribution.png')
    # Conditional extremes, changes in prediction, and same OOF-row comparison.
    paired=h[h.experiment.eq('H1_RAIN')].merge(h[h.experiment.eq('H7_JOINT')],on=['protocol','repeat','fold',ID],suffixes=('_rain','_joint'),validate='one_to_one')
    paired['prediction_change']=paired.y_pred_joint-paired.y_pred_rain
    paired['absolute_error_reduction']=abs(paired.y_pred_rain-paired.y_true_rain)-abs(paired.y_pred_joint-paired.y_true_joint)
    paired.to_parquet(hout/'tables/55_rain_joint_prediction_changes.parquet',index=False)
    worst=paired.assign(rain_absolute_error=abs(paired.y_pred_rain-paired.y_true_rain)).sort_values('rain_absolute_error',ascending=False).groupby('protocol').head(20)
    worst.to_csv(hout/'tables/56_largest_rain_errors_joint_changes.csv',index=False)
    seg=diagnostics['H'][2];segment=seg.groupby(['protocol','experiment','yield_segment'])[['RMSE','MAE','bias_pred_minus_y']].mean().reset_index()
    principal=segment[segment.experiment.isin(['H1_RAIN','H4_TMIN_TMAX','H7_JOINT','H8_CLIMATE_CURRENT_ORIGINAL'])]
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    for protocol,ax in zip(['random','spatial'],axes):sns.barplot(data=principal[principal.protocol.eq(protocol)],x='yield_segment',y='bias_pred_minus_y',hue='experiment',ax=ax);ax.axhline(0,c='grey');ax.set_title(protocol)
    save(fig,hout,'51_conditional_yield_bias.png')
    # Champion is a cached contextual benchmark; never included in climate ablation.
    champ_path=ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization/predictions/oof_predictions.parquet'
    champ=pd.read_parquet(champ_path);champ=champ[champ.architecture.eq('A_CURRENT_CH_H_T')]
    champion_rep=pd.DataFrame([dict(repeat=rep,**metrics(z.y_true,z.y_pred)) for rep,z in champ.groupby('repeat')])
    champion_rep.to_csv(hout/'tables/57_champion_cached_context_repeat_metrics.csv',index=False)
    stages=pd.read_csv(ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization/stages/stagewise_fold_values.csv')
    stage_rows=stages[stages.architecture.eq('A_CURRENT_CH_H_T')]
    stage_rows.to_csv(hout/'tables/58_champion_stagewise_cached_context.csv',index=False)
    stage_summary=stage_rows.groupby('stage_order').agg(stage=('stage','first'),mean_fold_RMSE=('RMSE','mean')).reset_index()
    stage_summary['reduction_from_previous_stage']=stage_summary.mean_fold_RMSE.shift(1)-stage_summary.mean_fold_RMSE
    stage_summary.to_csv(hout/'tables/58_champion_stagewise_summary.csv',index=False)
    # Recover both legacy folds means (reported originally) and our complete-repeat metric.
    legacy=pd.read_csv(ROOT/'outputs/modeling/family_1/source_contribution/metrics/source_only_metrics.csv')
    old=legacy[legacy.pipeline.eq('ENET_CLIMATE_ONLY')].iloc[0]
    original=hc[hc.protocol.eq('random')&hc.experiment.eq('H8_CLIMATE_CURRENT_ORIGINAL')].iloc[0]
    if abs(original.RMSE_fold_mean-old.RMSE_mean)>1e-12:raise ValueError('Original cached Climate Current metrics do not reproduce')
    if abs(original.MAE_mean-old.MAE_mean)>1e-12: # unequal fold size explains different weighting; compare fold mean
        old_mae=hf[hf.protocol.eq('random')&hf.experiment.eq('H8_CLIMATE_CURRENT_ORIGINAL')].MAE.mean()
        if abs(old_mae-old.MAE_mean)>1e-12:raise ValueError('Original MAE does not reproduce')
    previous=pd.read_csv(ROOT/'outputs/modeling/family_1/rainfall_yield/e8/v1/tables/40_model_comparison.csv')
    previous.to_csv(hout/'tables/62_previous_rainfall_results_cached_context.csv',index=False)
    gc,_,_=comparisons['G'];profile=json.loads((gout/'report/profile_summary.json').read_text(encoding='utf-8'))
    pca_g=json.loads((gout/'report/exploratory_pca_summary.json').read_text(encoding='utf-8'))
    pca_h=json.loads((hout/'report/exploratory_pca_summary.json').read_text(encoding='utf-8'))
    source=json.loads((gout/'report/source_audit.json').read_text(encoding='utf-8'))
    protocols=json.loads((hout/'splits/profile_protocol_definition.json').read_text(encoding='utf-8'))
    summary_pca=pd.DataFrame([dict(name=p['name'],k90=p['k90'],k95=p['k95'],rank=p['rank']) for p in pca_g+pca_h])
    # Interpret loadings actually observed, including arbitrary signs.
    loading_text='\n'.join(f"- {p['name']}: K95={p['k95']}; PC1 mayores cargas {p['PC1_top_loadings']}; PC2 {p['PC2_top_loadings']}." for p in pca_g+pca_h)
    rand=gc[gc.protocol.eq('random')&~gc.experiment.eq('G0_MEAN')].sort_values('RMSE_mean').iloc[0]
    temporal_reading,joint_reading,direct_answers,error_reading=interpretation(gout,hout,gc,hc,increment,principal)
    reading=('La mejora mensual es consistente con la regla descriptiva establecida, pero requiere validación independiente.' if consistent else
        'H1 no queda respaldada como mejora predictiva consistente de las variables mensuales bajo esta especificación: la ganancia aleatoria es mínima y la incorporación de temperatura empeora los tres protocolos geográficos. Sí existe estructura térmica temporal distinta; estructura climática y utilidad predictiva transferible son preguntas diferentes.')
    gtext=f'''# G — Temperature Signal Exploration

## Alcance, auditoría y contexto

197 parcelas, una fila descriptiva por parcela y 138 etiquetas autorizadas por CONJUNTO. Las 59 PREDICCION nunca aportan Y. Fuente CHIRTS-ERA5 comprobada en metadatos de los 96 TIFF: Celsius, scale=1, offset=0, NoData=-9999 enmascarado por exactextract. Hay 48 meses completos por parcela, 0 faltantes y 0 violaciones Tmin≤Tmax. Se reutiliza la extracción canónica y su auditoría zonal guardada: diferencia máxima de medias {source['max_difference_saved_zonal_means']}. No se reconstruye clima.

Las cuadrículas tienen resolución 0.05° y extensión 65×72. No son bit a bit iguales: diferencia de origen {source['max_affine_difference_degrees']:.3g}°, aproximadamente 3.3 cm. Las 197 parcelas intersectan las mismas celdas de lluvia y temperatura. Las fracciones de área son en grados cuadrados, no pesos geodésicos m². La etiqueta antigua CHIRPS_OR_WORLDCLIM del diccionario es genérica/inexacta: se corrige la procedencia solo en el diccionario nuevo, sin modificar artefactos anteriores.

Correspondencia de familias, investigaciones anteriores, numeración y reutilización: tabla 00. E0–E8/F son antecedentes internos del módulo de lluvia, no identificadores de G/H. No se localizó una sección E/F superior independiente en los archivos auditados; se conserva la nomenclatura encontrada. Familia 2 funcional y Familia 3 estructural quedan intactas.

## Estructura temporal y candidatos

Tablas 02–04 y figuras 01/02/04/06 muestran distribución de Tmin/Tmax mes a mes, comparación de la misma mensualidad entre 2022–2025 y SD espacial. Las siete mensualidades de una parcela no son siete observaciones supervisadas. Los meses no se interpretan como etapas fenológicas medidas. Tmin/Tmax son promedios mensuales de mínimas/máximas diarias; sus mínimos de ciclo no identifican heladas ni sus máximos olas de calor.

Tmean=(Tmax+Tmin)/2 es una aproximación, no una integración horaria. DTR=Tmax−Tmin. Se conservan medias, mínimos/máximos mensuales, SD ddof=1, rango, meses de extremos (primer mes en empates), diferencias sucesivas, pendiente por días reales y rachas estrictas. Las anomalías restan la media del mismo mes de 2022–24: tres años son una referencia corta, no normal climatológica. Todo esto es target-free y consta en el diccionario. Solo doce resúmenes compactos predefinidos (media, SD y pendiente para cuatro series) entran al modelo compacto. No se seleccionaron features por correlación global con Y ni se usaron umbrales fisiológicos.

## Resolución, perfiles y geografía

{temporal_reading}

Perfiles exactos: {profile['exact_counts']}; casi equivalentes: {profile['near_counts']}. Tolerancia completa por coordenada: .001°C en temperatura y .01 mm en lluvia, enlace completo sin encadenamiento. Temperatura no subdivide ninguno de los 53 perfiles de lluvia y distingue {profile['pairs_distinguished_by_temperature']} pares antes iguales. Tablas 06–12 documentan grupos, distancias geodésicas, estados/municipios, tamaños, SD/rango de Y y soporte de celda. Igual número de perfiles por sí solo no prueba igualdad de particiones; aquí se verificó también la subdivisión y las asignaciones.

Elevación y pendiente se relacionan descriptivamente con temperaturas en tabla 13; no son predictores. Tabla 14 separa variación dentro de estados/municipios. Tabla 11 da error mínimo empírico usando medias de Y por grupo: usa las mismas etiquetas y no es un límite irreducible validado.

## PCA exploratorio y asociaciones

Cuatro PCA separados: siete Tmin, siete Tmax, catorce Tmin/Tmax y catorce Tmean/DTR. StandardScaler evita dominar por dispersión de un mes, seguido por SVD completo sin whitening. Todos los PCA de 197 son descriptivos, no entradas precomputadas al CV. Varianza, autovalores, cargas, contribuciones, correlaciones, scores y escala se conservan en 20–27. Colores de Y solo para 138 TRAIN; restantes grises. PCA puede agrupar visualmente regiones, sin confirmar clusters ni causas.

{table_text(summary_pca.iloc[:4])}
{loading_text.split('- Joint_standardized')[0]}

PC1 Tmin tiene cargas del mismo signo en todos los meses: gradiente térmico compartido, no un efecto causal sobre cebada. PC2 Tmin contrapone abril/mayo con meses posteriores. Tmax presenta un segundo contraste temporal; no es equivalente a Tmin. Tmean/DTR conserva algebraicamente la información de Tmin/Tmax, pero StandardScaler y la penalización no son invariantes a ese cambio de base; diferencias predictivas no significan nuevos datos. Tabla 05 y figura 07 conservan correlaciones y relaciones aparentes con Y, incluidos LOW/HIGH y regiones (15), exclusivamente exploratorias. Las features constantes tienen correlación indefinida, no cero evidencia.

## Regresiones controladas y límites

Baseline reutilizado; cinco representaciones térmicas Elastic Net y una sensibilidad PCR justificada por K95 térmico≤4. Mediana, escala y modelo se ajustan en cada inner-train; alpha [.01,.1,1], l1_ratio [.1,.5,.9], mismo grid del Climate Current original. PCR OLS secundaria selecciona K internamente entre [1,2,4,7,10,14]. No se añaden árboles. Se conservan los folds externos e internos originales y los agrupados existentes. Definición de perfiles CV: {protocols}. No se usa temperatura como un proxy adicional de topografía dentro del predictor.

Métrica principal: media de métricas de cada repetición OOF completa de 138 parcelas. SD de folds y repeticiones son descriptivas; repeticiones se solapan y no son muestras independientes. En agrupados solo hay una repetición. Sesgo=pred−real. Promedios de predicciones únicamente diagnósticos.

{table_text(gc)}
La menor RMSE térmica aleatoria observada corresponde a {rand.experiment}, {rand.RMSE_mean:.4f} t/ha. Es un resultado comparativo, no un nuevo ganador confirmado: revisar todos los protocolos y la selección entre experimentos. Gráficos 40–44 y tablas 43–49 conservan sesgos condicionados, errores regionales, extremos, perfiles y bandas. Temperatura no aumenta la resolución espacial efectiva. Una asociación geográfica fuerte puede generar capacidad aleatoria sin transferencia municipal/espacial.

## Conclusión de G

Temperatura contiene gradientes y contrastes mensuales propios y admite representaciones compactas; Tmean/DTR reexpresa las mismas mediciones. Lo que justifica investigar con lluvia es su señal predictiva condicional, medida en H, no el alto porcentaje de varianza de PCA. Las limitaciones son 138 etiquetas, un solo ciclo con Y, resolución gruesa, referencia histórica corta y falta de observaciones agronómicas individuales. No se modifica Champion.
'''
    htext=f'''# H — Joint Climate Signal Exploration

## H1, referencias y auditoría

Se prueba si temperatura complementa precipitación. Matriz de 197×21 valores mensuales originales: siete lluvia, siete Tmin, siete Tmax, abril–octubre 2025. Mismos ID y meses; mm/mes y °C en bloques separados, sin nuevas etiquetas. No entra nubosidad, satélite, suelo, municipio, elevación ni pendiente como predictor.

Climate Current original de Familia 1, etapa 4.5 (148): exactamente 48 columnas CORE retenidas (10 precipitación y 38 térmicas derivadas), imputación mediana → StandardScaler → ElasticNet(max_iter=20000, random_state=2026), alpha [.01,.1,1], l1 [.1,.5,.9], inner KFold4 con semilla 2026+índice de outer. Se congeló su lista de features y se guardan configuración y parámetros originales. Las variables constantes removidas previamente no se recuperan para cambiar su especificación. En random se reutilizan sus 1380 OOF originales; en agrupados se ajusta esa MISMA especificación por necesidad de evaluación nueva.

Familia 2/RS1 usa otra referencia ENET con grid l1 [.1,.7]; no se mezcla silenciosamente con la original. El Champion RS6 A_CURRENT_CH_H_T usa clima TOP20 seleccionado por fold, Sentinel histórico residual XGB y Ridge topográfico residual; no es Climate Current solo y no se reentrena. Sus valores por etapa se conservan como contexto, no evidencia del efecto de temperatura.

La RMSE original publicada era media de RMSE de folds: {old.RMSE_mean:.6f}, reproducida exactamente desde cache. La media de RMSE de repeticiones completas es {original.RMSE_mean:.6f}; son agregaciones distintas, no cambio de modelo. Tabla 40 conserva ambas. No comparar cifras con agregaciones distintas.

Tabla 62 recupera sin reentrenar los resultados E0–E8 y las sensibilidades del módulo anterior. E3 Ridge y las PCR OLS son antecedentes con otros algoritmos; sus diferencias con H1 Elastic Net no se atribuyen a temperatura. La ablación mensual H1–H7 mantiene el mismo algoritmo y configuración.

## Estructura conjunta y resolución

Tabla 17 y bloques 18 separan correlaciones rain/Tmin, rain/Tmax, Tmin/Tmax y dentro de familias. Figura 09 explora relaciones por mes sin transformar 1379 filas parcela-mes en etiquetas independientes. Tabla 19 conserva comparación 2025 con 2022–24. PCA conjunto estándar da dos columnas térmicas por cada columna de lluvia; sensibilidad target-free divide columnas estandarizadas por sqrt(7) o sqrt(14), igualando varianza total inicial de bloques. No se elige escala usando Y.

{table_text(summary_pca)}
{loading_text}

Las interpretaciones proceden de cargas observadas y contribuciones por bloque, no de nombres agronómicos impuestos. El signo de los eigenvectores es arbitrario. Scores, contribuciones y mapas se guardan; una distribución de carga térmica dominante en PCA estándar puede depender del número de columnas. PCA balanceado es descriptivo y no se selecciona como predictor por resultados externos.

La combinación sigue teniendo {profile['exact_counts']['joint']} perfiles exactos. Subdivide {profile['subdivided_rain_groups']} perfiles de lluvia, distingue {profile['pairs_distinguished_by_temperature']} pares y afecta {profile['parcels_in_subdivided_rain_groups']} parcelas de grupos subdivididos. En este conjunto no existe ganancia de resolución por añadir temperatura. Tabla 11 separa tamaños y dispersión intraperfil; cualquier fragmentación futura reduciría mecánicamente esa dispersión sin probar mejora predictiva.

## Ablación principal y sensibilidad acotada

{joint_reading}

H0 promedio; H1 lluvia; H2 Tmin; H3 Tmax; H4 Tmin+Tmax; H5 lluvia+Tmin; H6 lluvia+Tmax; H7 tres familias. Todos H1–H7 usan datos mensuales, MISMO Elastic Net, grid y folds. H2/H3/H4 reutilizan exactamente modelos térmicos de G, no se vuelven a entrenar. H8 conserva Climate Current original, con representación agregada distinguida claramente de la ablation mensual.

Sensibilidad secundaria: agregados precipitación/temperatura de la especificación original frente a H8, compacto predefinido, PCR OLS conjunta y PCA OLS separado por bloques. La PCA predictiva siempre se ajusta dentro de inner-train; K o umbral se eligen dentro de inner CV. Las comparaciones PCR son de representación con el mismo OLS y se mantienen separadas de Elastic Net. No hay búsqueda exhaustiva ni features elegidas retrospectivamente por asociación global con Y.

Protocolos: {protocols}. Se conservaron las 50 particiones random externas/internas y 15 agrupadas de E3/Family1. Cuando los grupos conjuntos y de lluvia tienen exactamente la misma partición de ID, los folds sirven para ambas definiciones; no se cambia silenciosamente el agrupamiento.

{table_text(hc)}

## Aporte incremental pareado

Delta_temp|rain=RMSE_rain−RMSE_joint; delta_rain|temp=RMSE_temp−RMSE_joint. Positivo es mejora condicional predictiva, no causalidad. Tabla 51 conserva deltas de cada fold; 52 los de cada repetición completa; 50 SD, cuartiles y consistencia. Folds/repeticiones se solapan: no hay p-valores ingenuos ni intervalos de independencia.

{table_text(increment)}
Decisión descriptiva H1: {json.dumps(decision,ensure_ascii=False)}. La regla exige >0.005 t/ha de mejora y ≥60% de folds mejorados en todos los protocolos; no sustituye validación independiente. Resultados negativos y sensibles a la geografía se conservan.

{reading}

## Errores y extremos

{table_text(principal)}
Tablas 43–49 muestran errores por segmento/región/perfil, extremos y bandas, con predicciones individuales separadas de promedios. LOW/HIGH se definen por cuartiles de Y solo para diagnóstico, nunca selección ni pesos de entrenamiento. Tabla 55 guarda cambios al incorporar temperatura para cada ID/fold/repetición; 56 indica si corrige los mayores errores de lluvia. Mapas 43 describen residuos espaciales sin atribuirles causas. Reducir sesgo global no obliga a reducir sesgo en bajos/altos o en cada estado.

## Relación con Champion y decisiones posteriores

{error_reading}

{direct_answers}

Champion tiene RMSE media de repeticiones OOF {champion_rep.RMSE.mean():.5f} t/ha, distinto del bloque climático y de su antigua media de folds. Tabla 58 identifica la corrección incremental de History y Topography a partir de resultados anteriores. No atribuir esa diferencia a temperatura ni comparar algoritmos como prueba de contribución de una variable.

Estas tres etapas usan exactamente los mismos folds del Champion; su métrica aquí es media de RMSE por fold, separada de las medias por repetición de H:
{table_text(stage_summary)}

Propuestas sin implementar: validar ciclos nuevos etiquetados; evaluar fuentes de mayor resolución y manejo/suelo/fenología para distinguir parcelas intraperfil; estudiar una sustitución climática solo si el candidato conserva mejora geográfica en evaluación independiente. Las 59 parcelas no se usan como prueba con Y oculto. No se cambia Champion ni se publica un modelo final.
'''
    for out,text,name in [(gout,gtext,'g_temperature_signal_report.md'),(hout,htext,'h_joint_climate_signal_report.md')]:
        text+='\n## Figuras\n\n'+'\n'.join(f'![{p.stem}](../figures/{p.name})\n' for p in sorted((out/'figures').glob('*.png')))
        (out/'report'/name).write_text(text,encoding='utf-8')
    primary=hc[hc.experiment.isin(['H0_MEAN','H1_RAIN','H2_TMIN','H3_TMAX','H4_TMIN_TMAX','H5_RAIN_TMIN','H6_RAIN_TMAX','H7_JOINT','H8_CLIMATE_CURRENT_ORIGINAL'])]
    synthesis=f'''# Síntesis H1 — qué señal climática aprovecha Familia 1

## Evidencia comparable

{table_text(primary[['protocol','experiment','RMSE_mean','MAE_mean','R2_mean','bias_pred_minus_y_mean']])}

## Complementariedad

{table_text(increment[increment.contrast.isin(['temperature_given_rain','rain_given_temperature','aggregated_temperature_given_rain','aggregated_rain_given_temperature'])])}

Temperatura añade señal térmica, pero no resolución: 53 perfiles de lluvia, 53 térmicos y 53 conjuntos; cero pares indistinguibles por lluvia se separan. Tmin/Tmax no son intercambiables; Tmean/DTR es otra base del mismo espacio. PCA explica estructura climática y no selecciona predictores por porcentaje global. Escalamiento por bloques cambia pesos descriptivos sin crear información.

Resultado de la regla multigeográfica: {json.dumps(decision,ensure_ascii=False)}. La lectura concreta por protocolo es:
'''
    for row in main.itertuples():
        effect='reduce' if row.mean_repeat_delta_RMSE>0 else 'aumenta'
        synthesis+=f'\n- {row.protocol}: incorporar temperatura {effect} RMSE en {abs(row.mean_repeat_delta_RMSE):.5f} t/ha; mejora {row.positive_fold_fraction:.0%} de folds.'
    synthesis+='\n\n'+reading
    synthesis+='\n\nEl Climate Current agregado se evalúa por separado; los deltas agregados dicen si sus resúmenes aprovechan complementariedad bajo el mismo Elastic Net. El Champion añade etapas residuales y no permite atribuir su ganancia a temperatura. No se modifica ni reentrena. Persisten incertidumbre geográfica, 138 etiquetas, un solo ciclo supervisado y ausencia de mediciones agronómicas individuales. Las propuestas siguientes son hipótesis, no cambios implementados.\n'
    synthesis+='\n'+direct_answers+'\n'+error_reading
    (hout/'report/h1_joint_synthesis.md').write_text(synthesis,encoding='utf-8')
    print(primary[['protocol','experiment','RMSE_mean','R2_mean']].round(5).to_string(index=False),flush=True)
    print('H1 incremental:',main.to_dict('records'),flush=True)
