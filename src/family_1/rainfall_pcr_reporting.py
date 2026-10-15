"""E8 PCA structure, paired OOF comparisons and parcel-information limits."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from .rainfall_features import ID
from .rainfall_modeling import metrics,TARGET
from .rainfall_pcr_audit import MONTHLY,REFERENCE

def save(fig,out,name):
    fig.savefig(out/'figures'/name,dpi=160,bbox_inches='tight');plt.close(fig)

def exploratory_figures(matrix,train,geo,info,out,proc,shape_extension):
    sns.set_theme(style='whitegrid')
    variance=info['variance'];loadings=info['loadings'];scores=info['scores']
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    axes[0].plot(range(1,8),variance.eigenvalue,'o-');axes[0].set(xlabel='Componente',ylabel='Autovalor',title='Scree PCA estandarizado — 197 parcelas')
    axes[1].plot(range(1,8),variance.cumulative_variance,'o-');axes[1].axhline(.95,color='grey',ls='--');axes[1].set(xlabel='K',ylabel='Fracción acumulada',ylim=(0,1.03))
    save(fig,out,'20_scree_and_cumulative.png')
    fig,ax=plt.subplots(figsize=(8,6));sns.heatmap(loadings,vmin=-1,vmax=1,cmap='coolwarm',annot=True,fmt='.2f',ax=ax)
    ax.set_title('Eigenvectores: columnas PC, filas meses');save(fig,out,'21_loading_heatmap.png')
    fig,ax=plt.subplots(figsize=(7,6));ax.scatter(scores.PC1,scores.PC2,s=20,alpha=.5)
    factor=float(max(scores.PC1.abs().max(),scores.PC2.abs().max())*.65)
    for month,row in loadings.iterrows():
        x,y=row.PC1*factor,row.PC2*factor;ax.annotate('',xy=(x,y),xytext=(0,0),arrowprops=dict(arrowstyle='->',color='firebrick'))
        ax.text(x,y,month[5:8],fontsize=9,color='firebrick')
    ax.set(xlabel='Score PC1',ylabel='Score PC2',title=f'Biplot; eigenvectores ×{factor:.2f} solo para visualización')
    save(fig,out,'22_biplot_PC1_PC2.png')
    regional=scores.merge(geo[[ID,'Estado','Municipio']],on=ID,validate='one_to_one')
    for field,name in [('Estado','23_PC_by_state.png'),('Municipio','24_PC_by_municipality.png')]:
        fig,ax=plt.subplots(figsize=(9,6));sns.scatterplot(data=regional,x='PC1',y='PC2',hue=field,s=40,alpha=.7,ax=ax)
        ax.legend(bbox_to_anchor=(1.02,1),loc='upper left',fontsize=8);ax.set_title('PCA descriptivo de precipitación absoluta');save(fig,out,name)
    labeled=scores.merge(train[[ID,TARGET]],on=ID,validate='one_to_one')
    hidden=scores[~scores[ID].isin(train[ID])]
    fig,ax=plt.subplots(figsize=(8,6));ax.scatter(hidden.PC1,hidden.PC2,c='lightgrey',s=20,label='59 sin Y')
    sc=ax.scatter(labeled.PC1,labeled.PC2,c=labeled[TARGET],cmap='viridis',s=35);fig.colorbar(sc,ax=ax,label='Rendimiento observado t/ha — 138 TRAIN')
    ax.set(xlabel='PC1',ylabel='PC2',title='Color Y descriptivo; no selecciona K');ax.legend();save(fig,out,'25_PC_by_observed_y_train_only.png')
    mapped=geo.merge(scores,on=ID);centroids=mapped.geometry.centroid
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    for pc,ax in zip(['PC1','PC2'],axes):
        sc=ax.scatter(centroids.x,centroids.y,c=mapped[pc],cmap='coolwarm',s=20);fig.colorbar(sc,ax=ax,label=f'Score {pc}')
        ax.set(xlabel='Este EPSG:6372 (m)',ylabel='Norte (m)')
    save(fig,out,'26_PC_score_maps.png')
    if shape_extension:
        from .rainfall_pcr import HelmertShares
        from sklearn.decomposition import PCA
        shares=matrix[MONTHLY].div(matrix[MONTHLY].sum(axis=1),axis=0)
        shares.to_csv(out/'tables/29_monthly_shares_descriptive.csv',index=False)
        contrast=HelmertShares().fit_transform(matrix[MONTHLY]);pca=PCA(n_components=6,svd_solver='full').fit(contrast)
        pd.DataFrame({'component':range(1,7),'variance_fraction':pca.explained_variance_ratio_,
            'cumulative':np.cumsum(pca.explained_variance_ratio_)}).to_csv(out/'tables/29_shape_exploratory_variance.csv',index=False)
        s=pca.transform(contrast)
        result=pd.DataFrame(s,columns=[f'ShapePC{i}' for i in range(1,7)]);result.insert(0,ID,matrix[ID])
        result.to_parquet(proc/'exploratory_shape_scores_197.parquet',index=False)
        pca_month_loadings=pca.components_@HelmertShares().fit(matrix[MONTHLY]).basis_
        pd.DataFrame(pca_month_loadings.T,index=MONTHLY,columns=[f'ShapePC{i}' for i in range(1,7)]).to_csv(out/'tables/29_shape_month_loadings.csv')
        fig,axes=plt.subplots(1,2,figsize=(11,4));axes[0].plot(range(1,7),pca.explained_variance_ratio_,'o-');axes[0].set(xlabel='Shape PC',ylabel='Varianza relativa')
        axes[1].scatter(result.ShapePC1,result.ShapePC2,s=20);axes[1].set(xlabel='Shape PC1',ylabel='Shape PC2');save(fig,out,'27_shape_exploration.png')

def comparison_tables(predictions,out):
    folds=[];reps=[]
    for (protocol,name,rep,fold),g in predictions.groupby(['protocol','experiment','repeat','fold']):
        folds.append(dict(protocol=protocol,experiment=name,repeat=rep,fold=fold,n=len(g),**metrics(g.y_true,g.y_pred)))
    for (protocol,name,rep),g in predictions.groupby(['protocol','experiment','repeat']):
        if len(g)!=138 or not g[ID].is_unique:raise ValueError('Each OOF repetition must evaluate the same 138 parcels once')
        reps.append(dict(protocol=protocol,experiment=name,repeat=rep,**metrics(g.y_true,g.y_pred)))
    folds=pd.DataFrame(folds);reps=pd.DataFrame(reps);summary=[]
    for (protocol,name),g in reps.groupby(['protocol','experiment']):
        f=folds[folds.protocol.eq(protocol)&folds.experiment.eq(name)]
        summary.append(dict(protocol=protocol,experiment=name,
            **{metric+'_mean':g[metric].mean() for metric in ['RMSE','MAE','R2','bias_pred_minus_y']},
            **{metric+'_fold_sd':f[metric].std() for metric in ['RMSE','MAE','R2','bias_pred_minus_y']},
            RMSE_repeat_sd=g.RMSE.std() if len(g)>1 else np.nan,n_repeats=len(g)))
    summary=pd.DataFrame(summary)
    base=summary[summary.experiment.eq('E3_MONTHLY_RIDGE')][['protocol','RMSE_mean']].rename(columns={'RMSE_mean':'E3_Ridge_RMSE'})
    summary=summary.merge(base,on='protocol');summary['delta_RMSE_vs_E3_Ridge']=summary.RMSE_mean-summary.E3_Ridge_RMSE
    paired=[]
    for (protocol,name),g in folds.groupby(['protocol','experiment']):
        b=folds[folds.protocol.eq(protocol)&folds.experiment.eq('E3_MONTHLY_RIDGE')]
        joined=g.merge(b,on=['repeat','fold'],suffixes=('_candidate','_ridge'))
        diff=joined.RMSE_candidate-joined.RMSE_ridge
        paired.append(dict(protocol=protocol,experiment=name,mean_paired_fold_delta_RMSE=diff.mean(),
            fold_win_fraction=float((diff<-1e-10).mean()),fold_tie_fraction=float((diff.abs()<=1e-10).mean()),
            paired_delta_q25=diff.quantile(.25),paired_delta_q75=diff.quantile(.75)))
    summary=summary.merge(pd.DataFrame(paired),on=['protocol','experiment'])
    summary.to_csv(out/'tables/40_model_comparison.csv',index=False)
    folds.to_csv(out/'tables/41_fold_metrics.csv',index=False);reps.to_csv(out/'tables/42_repetition_metrics.csv',index=False)
    return summary,folds,reps

def error_diagnostics(p,train,geo,out):
    profiles=pd.read_csv(out/'tables/05_seven_month_profile_groups.csv')
    q=p.merge(profiles,on=ID,validate='many_to_one').merge(geo[[ID,'Estado','Municipio']],on=ID,validate='many_to_one')
    q['error']=q.y_pred-q.y_true;q['absolute_error']=abs(q.error)
    low,high=train[TARGET].quantile([.25,.75]);q['yield_segment']=np.where(q.y_true<=low,'LOW',np.where(q.y_true>=high,'HIGH','MID'))
    segments=[];regions=[]
    for (protocol,name,rep,segment),g in q.groupby(['protocol','experiment','repeat','yield_segment']):
        segments.append(dict(protocol=protocol,experiment=name,repeat=rep,yield_segment=segment,n=len(g),**metrics(g.y_true,g.y_pred)))
    for (protocol,name,rep),g in q.groupby(['protocol','experiment','repeat']):
        for field in ['Estado','Municipio']:
            for region,z in g.groupby(field):
                if len(z)>=5:regions.append(dict(protocol=protocol,experiment=name,repeat=rep,region_type=field,region=region,n=len(z),**metrics(z.y_true,z.y_pred)))
    segments=pd.DataFrame(segments);regions=pd.DataFrame(regions)
    segments.to_csv(out/'tables/43_yield_segment_metrics_by_repeat.csv',index=False)
    regions.to_csv(out/'tables/44_regional_metrics_by_repeat.csv',index=False)
    by_profile=q.groupby(['protocol','experiment','exact_profile']).agg(n_individual_oof=(ID,'size'),n_parcels=(ID,'nunique'),
        mean_error=('error','mean'),error_sd=('error','std'),MAE=('absolute_error','mean'),
        RMSE=('error',lambda s:np.sqrt(np.mean(s**2))),prediction_sd=('y_pred','std'),y_sd=('y_true','std')).reset_index()
    by_profile.to_csv(out/'tables/45_error_by_profile_individual_oof.csv',index=False)
    # A single averaged prediction per parcel is exported separately for graph diagnostics.
    averaged=q.groupby(['protocol','experiment',ID]).agg(y_true=('y_true','first'),y_pred=('y_pred','mean'),
        exact_profile=('exact_profile','first'),Estado=('Estado','first'),Municipio=('Municipio','first')).reset_index()
    averaged['error']=averaged.y_pred-averaged.y_true
    averaged.to_parquet(out/'tables/46_oof_averaged_diagnostic.parquet',index=False)
    q.groupby(['protocol','experiment',ID]).agg(mean_prediction=('y_pred','mean'),prediction_repeat_sd=('y_pred','std'),
        min_prediction=('y_pred','min'),max_prediction=('y_pred','max'),n_repeats=('repeat','nunique')).to_csv(out/'tables/47_prediction_stability_by_parcel.csv')
    severe=q.sort_values('absolute_error',ascending=False).groupby(['protocol','experiment'],group_keys=False).head(10)
    severe.to_csv(out/'tables/48_largest_individual_oof_errors.csv',index=False)
    collision=[]
    for (protocol,name),g in averaged.groupby(['protocol','experiment']):
        from .rainfall_pcr_audit import bounded_groups
        band=bounded_groups(g[['y_pred']],.01)
        collision.append(dict(protocol=protocol,experiment=name,n_prediction_bands_001tha=len(np.unique(band)),
            n_exact_climate_profiles=g.exact_profile.nunique(),
            mean_within_exact_profile_prediction_range=g.groupby('exact_profile').y_pred.agg(lambda s:s.max()-s.min()).mean()))
    pd.DataFrame(collision).to_csv(out/'tables/49_prediction_band_comparison.csv',index=False)
    return q,averaged,segments,regions

def predictive_figures(p,average,comparison,segments,registry,out):
    principal=['E3_MONTHLY_RIDGE','E8_PCR','E8_PCA_RIDGE']
    fig,axes=plt.subplots(2,3,figsize=(15,9))
    for j,name in enumerate(principal):
        for i,(data,title) in enumerate([(p,'OOF individuales'),(average,'OOF promedio por parcela')]):
            q=data[data.protocol.eq('random')&data.experiment.eq(name)];ax=axes[i,j]
            ax.scatter(q.y_true,q.y_pred,c=q.exact_profile,cmap='turbo',vmin=1,vmax=53,s=14,alpha=.45)
            ax.plot([1,6],[1,6],'k--');ax.set(xlabel='Observado (t/ha)',ylabel='Predicho (t/ha)',xlim=(1,6),ylim=(1,6),title=name+'\n'+title)
    fig.tight_layout();save(fig,out,'40_observed_predicted_individual_and_average.png')
    fig,axes=plt.subplots(2,3,figsize=(15,8))
    for j,name in enumerate(principal):
        q=p[p.protocol.eq('random')&p.experiment.eq(name)]
        axes[0,j].scatter(q.y_pred,q.error,s=12,alpha=.25);axes[0,j].axhline(0,color='black');axes[0,j].set(title=name,xlabel='Predicción OOF (t/ha)',ylabel='Error pred − real',ylim=(-3,3))
        axes[1,j].hist(q.error,bins=np.linspace(-3,3,31),alpha=.8);axes[1,j].set(xlabel='Error OOF (t/ha)',ylabel='Frecuencia (10 predicciones/parcelaria)')
    fig.tight_layout();save(fig,out,'41_individual_oof_residuals_and_errors.png')
    fig,ax=plt.subplots(figsize=(11,5));sns.barplot(data=comparison[comparison.experiment.isin(['E0_MEAN','E3_MONTHLY_LINEAR']+principal+['E8_SHAPE_PCR','E8_TOTAL_SHAPE_RIDGE'])],x='RMSE_mean',y='experiment',hue='protocol',ax=ax)
    ax.set_xlabel('RMSE medio por repetición completa (t/ha)');save(fig,out,'42_model_comparison.png')
    fixed=comparison[comparison.experiment.str.match(r'E8_PCR_K[1-7]$')].copy();fixed['K']=fixed.experiment.str[-1].astype(int)
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    for protocol,g in fixed.groupby('protocol'):
        axes[0].plot(g.K,g.RMSE_mean,'o-',label=protocol);axes[1].plot(g.K,g.bias_pred_minus_y_mean,'o-',label=protocol)
    axes[0].set(xlabel='K fijo — diagnóstico, no selección con outer Y',ylabel='RMSE OOF (t/ha)');axes[0].legend()
    axes[1].set(xlabel='K',ylabel='Sesgo pred − real (t/ha)');axes[1].axhline(0,color='grey');save(fig,out,'43_fixed_K_performance_and_bias.png')
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    selected=registry[registry.experiment.isin(['E8_PCR','E8_PCA_RIDGE'])]
    for name,ax in zip(['E8_PCR','E8_PCA_RIDGE'],axes):
        counts=selected[selected.experiment.eq(name)].groupby(['protocol','selected_K']).size().rename('fold_count').reset_index()
        sns.barplot(data=counts,x='selected_K',y='fold_count',hue='protocol',ax=ax);ax.set_title(name+' selección interna')
    save(fig,out,'44_selected_K_stability.png')
    means=segments.groupby(['protocol','experiment','yield_segment']).bias_pred_minus_y.mean().reset_index()
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    for protocol,ax in zip(['random','spatial'],axes):
        sns.barplot(data=means[means.protocol.eq(protocol)&means.experiment.isin(principal)],x='yield_segment',y='bias_pred_minus_y',hue='experiment',ax=ax)
        ax.axhline(0,color='grey');ax.set_title(protocol);ax.set_ylabel('Sesgo pred − real (t/ha)')
    save(fig,out,'45_extreme_yield_bias.png')
    fig,axes=plt.subplots(1,3,figsize=(15,4))
    for name,ax in zip(principal,axes):
        q=p[p.protocol.eq('random')&p.experiment.eq(name)];ax.scatter(q.y_true,q.error,s=12,alpha=.25)
        ax.axhline(0,color='grey');ax.set(title=name,xlabel='Y observado (t/ha)',ylabel='Error OOF (t/ha)',ylim=(-3,3))
    save(fig,out,'46_error_conditioned_on_yield.png')

def finish(matrix,train,geo,info,frames,out,shape_extension):
    new=frames['predictions'];prior=pd.read_parquet(REFERENCE/'tables/02_oof_predictions.parquet')
    prior=prior[prior.experiment.isin(['E0_MEAN','E1_TOTAL_LINEAR','E3_MONTHLY_LINEAR','E3_MONTHLY_RIDGE'])]
    # Compare exact ID/repeat/fold/target coverage before concatenating cached E3.
    reference=prior[prior.experiment.eq('E3_MONTHLY_RIDGE')][['protocol','repeat','fold',ID,'y_true']]
    for name,g in new.groupby('experiment'):
        paired=g.merge(reference,on=['protocol','repeat','fold',ID],suffixes=('','_reference'),validate='one_to_one')
        if len(paired)!=len(reference) or len(g)!=len(reference) or not np.allclose(paired.y_true,paired.y_true_reference):
            raise ValueError(f'E8 evaluation rows incompatible with E3: {name}')
    all_predictions=pd.concat([prior,new],ignore_index=True)
    all_predictions.to_parquet(out/'tables/39_comparison_oof_individual.parquet',index=False)
    comparison,folds,reps=comparison_tables(all_predictions,out)
    p,average,segments,regions=error_diagnostics(all_predictions,train,geo,out)
    predictive_figures(p,average,comparison,segments,frames['registry'],out)
    co=frames['coefficients'].groupby(['protocol','experiment','month']).coefficient_t_ha_per_mm.agg(['mean','std','min','max'])
    co.to_csv(out/'tables/50_month_coefficient_stability.csv')
    counts=frames['registry'].groupby(['protocol','experiment','selected_K']).size().rename('outer_fold_count').reset_index()
    counts.to_csv(out/'tables/51_selected_K_distribution.csv',index=False)
    frames['fold_pc'].groupby(['protocol','component']).agg(mean_variance=('variance_fraction','mean'),
        variance_sd=('variance_fraction','std'),mean_abs_training_y_correlation=('training_y_correlation',lambda s:s.abs().mean()),
        mean_loading_cosine=('absolute_loading_cosine','mean'),minimum_loading_cosine=('absolute_loading_cosine','min')).to_csv(out/'tables/52_component_variance_association_stability.csv')
    # Decision is deliberately across protocols, with descriptive paired evidence.
    main=comparison[comparison.experiment.isin(['E8_PCR','E8_PCA_RIDGE'])]
    decisions=[]
    for name,g in main.groupby('experiment'):
        random=g[g.protocol.eq('random')].iloc[0]
        consistent=bool((g.delta_RMSE_vs_E3_Ridge<-.005).all() and (g.fold_win_fraction>=.6).all())
        decisions.append(dict(experiment=name,consistent_superiority=consistent,
            random_delta_RMSE=float(random.delta_RMSE_vs_E3_Ridge),
            decision='exploratory consistent candidate; still no independent test' if consistent else 'no consistent superiority across protocols'))
    decision={'primary_models':decisions,'winner_not_selected_from_fixed_K_outer_metrics':True,'independent_test_available':False}
    (out/'report/decision.json').write_text(json.dumps(decision,indent=2),encoding='utf-8')
    transform_dictionary=pd.DataFrame([
        dict(transform='StandardScaler absolute',formula='Z_m=(P_m-mu_train_m)/sigma_train_m; variance ddof=0; zero variance scale=1',units='dimensionless',fit_scope='inner-train/outer-train; descriptive separate 197',warning='No target or held-out values used'),
        dict(transform='PCA',formula='PC_k=(Z-mean_train_Z) dot eigenvector_k; full SVD, no whitening',units='standardized score',fit_scope='each inner/outer train',warning='Signs arbitrary; high climate variance need not predict Y'),
        dict(transform='component contribution',formula='v_mk^2; sum_m v_mk^2=1',units='fraction',fit_scope='descriptive or training PCA separately',warning='Not causal importance or unique predictive contribution'),
        dict(transform='PCR',formula='Y=intercept+sum_k gamma_k PC_k; K chosen in inner CV',units='t/ha',fit_scope='train only',warning='Truncation discards orthogonal climate directions'),
        dict(transform='PCA Ridge',formula='argmin_gamma sum((Y-pred)^2)+alpha*sum(gamma^2); unpenalized intercept',units='t/ha',fit_scope='K and alpha inner CV',warning='For K=7 orthogonal rotation is equivalent to standardized monthly Ridge'),
        dict(transform='monthly shares',formula='S_m=P_m/sum_j P_j; six coordinates H S with H Helmert, H H^T=I, H 1=0',units='fraction',fit_scope='per parcel deterministic; downstream PCA train only',warning='sum S=1; Euclidean analysis is not Aitchison/log-ratio PCA; zero total invalid, zeros otherwise retained'),
        dict(transform='shape centering',formula='H S - mean_train(H S); no coordinate-wise rescaling',units='fraction score',fit_scope='inner/outer train',warning='Preserves Euclidean distances in simplex tangent; composition limitations remain'),
        dict(transform='total plus shape',formula='standardized sum(P) + K shape PCs -> Ridge; K in 1..6, alpha existing grid',units='t/ha',fit_scope='all within inner train',warning='One bounded secondary sensitivity, not a transform search')])
    transform_dictionary.to_csv(out/'tables/53_transformation_dictionary.csv',index=False)
    diagnostic=json.loads((out/'report/profile_diagnostic.json').read_text(encoding='utf-8'))
    variance=info['variance'];k90=int(np.searchsorted(variance.cumulative_variance,.90)+1)
    region= pd.read_csv(out/'tables/28_pc_geographic_structure.csv')
    loadings=info['loadings'];interpretations=[]
    for pc in ['PC1','PC2','PC3']:
        vector=loadings[pc];positive=vector[vector>.15].index.tolist();negative=vector[vector<-.15].index.tolist()
        interpretations.append(f'{pc}: cargas positivas {positive}; negativas {negative}. '+
            ('Contraste temporal entre esos meses.' if positive and negative else 'Dirección mayormente conjunta; revisar correlaciones con meses y total antes de llamarla intensidad.'))
    component_total=info['scores'].set_index(ID).join(matrix.set_index(ID)[MONTHLY].sum(axis=1).rename('total')).corr()['total'].drop('total')
    component_total.rename('correlation_with_cycle_total').to_csv(out/'tables/54_PC_total_correlations.csv')
    lowvariance=pd.read_csv(out/'tables/27_exploratory_pc_y_associations.csv')
    lowvariance=lowvariance.merge(variance,on='component')
    selected_metrics=comparison[comparison.experiment.isin(['E0_MEAN','E3_MONTHLY_LINEAR','E3_MONTHLY_RIDGE','E8_PCR','E8_PCA_RIDGE','E8_SHAPE_PCR','E8_TOTAL_SHAPE_RIDGE'])]
    selected_segments=segments[segments.experiment.isin(['E3_MONTHLY_RIDGE','E8_PCR','E8_PCA_RIDGE'])].groupby(['protocol','experiment','yield_segment'])[['RMSE','MAE','bias_pred_minus_y']].mean()
    report=f'''# E8_RAINFALL_PCA_PCR — reporte técnico

## 1. Alcance y auditoría

Se consumen las siete columnas CHIRPS auditadas de abril–octubre 2025. Matriz descriptiva 197×7, unidad supervisada 138 parcelas; 59 PREDICCION nunca aportan Y. E0–E7/F, Champion y sus resultados se conservaron byte a byte (protected_inputs.json). El catálogo 00–04 verifica columnas efectivas, fórmula, algoritmo y fuente; los integrales se identifican por separado y no entran a E8. No se reconstruye clima ni se mezclan temperatura, índices, topografía o municipio como predictores.

## 2. Predicciones repetidas y límite de información

Hay {diagnostic['exact_seven_month_profiles']} perfiles exactos y {diagnostic['near_seven_month_profiles_001mm']} casi equivalentes a 0.01 mm por mes. Un mismo Ridge da rango intraperfil exactamente {diagnostic['fixed_model_max_within_exact_profile_prediction_range']} t/ha. Los perfiles distintos también pueden proyectarse a predicciones próximas: tabla 10; una regresión transforma siete números en un escalar. No es evidencia automática de sobreajuste.

Las gráficas anteriores tienen Y observado en x: {diagnostic['distinct_observed_y']} valores distintos para 138 parcelas, máximo {diagnostic['max_observed_y_multiplicity']} repeticiones de un mismo Y. Esas repeticiones producen bandas verticales de valores observados. Los modelos por fold son funciones diferentes, por lo que OOF de parcelas idénticas no necesariamente coincide; promediar diez repeticiones reduce y altera dispersión. Figuras 01/40 separan individuales de promedios y tablas 07/49 cuantifican ambos.

La mínima RMSE empírica de una función constante por perfil exacto es {diagnostic['empirical_exact_profile_constant_prediction_RMSE_floor']:.4f} t/ha. Usa las mismas etiquetas para asignar las medias: identidad descriptiva, no límite irreducible poblacional ni evaluación validada. PCA determinista conserva igualdad de vectores y no aporta nuevas observaciones para distinguir rendimientos intrapíxel.

## 3. PCA exploratorio separado

Se estandariza cada mes con media y SD poblacional ddof=0 porque sus dispersión/rangos en mm difieren; evita que junio domine solo por escala. Autovalores PCA usan divisor n−1. Meses con varianza cero: {info['zero_variance_months']}; rango estandarizado {info['standardized_matrix_rank']}. Eigenvectores, contribuciones cuadradas y correlaciones son objetos diferentes (tablas 21–23). Scores y pipeline de 197 se guardan como descriptivos; ningún predictor supervisado lee esos scores.

{k90} componentes alcanzan 90% y {info['k95']} alcanzan 95% de varianza climática:
```
{variance.round(6).to_string(index=False)}
```
Interpretaciones derivadas de cargas, con signo arbitrario:
{chr(10).join(interpretations)}

Correlación con total del ciclo:
```
{component_total.round(4).to_string()}
```
La geografía se examina con colores, mapas y fracción de varianza entre grupos (tabla 28). Agrupación visual por municipio puede reflejar lluvia compartida; no demuestra que municipio sea predictor permitido ni que el PCA generalice a otra región. No se identifica un componente causal ni una fase fenológica observada.

## 4. PCR y PCA + Ridge: validación anidada

Se restauran exactamente 65 folds externos y sus listas internas guardadas de E3, incluyendo GroupKFold interno agrupado. Cada inner-train ajusta StandardScaler, PCA y regresión. K=1..7 se elige por RMSE interno; alpha usa [0.1,1,10,100,1000]. Refitting usa solo outer-train y outer-validation entra una vez para evaluar. PCA utiliza full SVD sin whitening. No se selecciona K mirando resultados externos de los siete controles fijos.

PCR trunca direcciones y ajusta OLS; PCA+Ridge permite truncar y además contraer coeficientes. Con siete PCs completos, la rotación ortogonal conserva OLS (rango completo) y la penalización L2 de Ridge. La equivalencia K7/OLS se verificó en cada fold, diferencia máxima {frames['equivalence'].max_K7_OLS_prediction_difference.max():.3g} t/ha; tabla 35 y prueba sintética automatizada. No se presenta el PCA completo como una fuente de información nueva.

K seleccionados:
```
{counts[counts.experiment.isin(['E8_PCR','E8_PCA_RIDGE'])].to_string(index=False)}
```
Los coeficientes se devuelven a t/ha por mm sin depender del signo de PCs (tabla 34). Las cargas de folds se alinean por máxima similitud absoluta a las descriptivas únicamente DESPUÉS del ajuste, para interpretación; nunca se usan para transformar datos predictivos. La condición del diseño de scores y la estabilidad de cargas están en 31/33/52; ortogonalidad elimina correlación entre scores en train, pero baja varianza puede mantener mala condición y descartarla puede perder señal.

## 5. Desempeño fuera de muestra y estabilidad

Las métricas principales promedian métricas de cada repetición completa, sobre exactamente las mismas parcelas por protocolo. Sesgo=pred−real. Las SD entre folds/repeticiones y diferencias pareadas están en 40–42; los folds se solapan y no son 50 réplicas independientes. En protocolos agrupados solo hay una repetición: no se inventa SD entre repeticiones.

```
{selected_metrics[['protocol','experiment','RMSE_mean','MAE_mean','R2_mean','bias_pred_minus_y_mean','RMSE_fold_sd','RMSE_repeat_sd','delta_RMSE_vs_E3_Ridge','fold_win_fraction']].round(4).to_string(index=False)}
```
Decisión explícita:
```
{json.dumps(decision,indent=2,ensure_ascii=False)}
```
No se afirma superioridad por un porcentaje alto de varianza climática. La regla descriptiva exige mejora RMSE >0.005 t/ha y ≥60% de folds ganados en TODOS los protocolos; aun si pasa requiere prueba independiente. Las discrepancias entre aleatorio, perfiles, municipio y bloques espaciales son resultados, no motivos para cambiar las particiones.

## 6. Componentes de baja varianza y rendimiento

Correlaciones descriptivas PC–Y sobre las 138 etiquetas (PCA global exploratorio, NO usadas para elegir K):
```
{lowvariance[['component','explained_variance','pearson_y','spearman_y']].round(5).to_string(index=False)}
```
Tablas 32/33/52 conservan validación interna y asociación PC–Y de cada train. Figura 43 muestra RMSE y sesgo de K=1..7, a modo diagnóstico. Conservar mucho porcentaje climático puede todavía eliminar direcciones que distinguen rendimiento; la curva externa no sustituye selección interna ni se usa para escoger un ganador post hoc.

## 7. Extremos, regiones y bandas

Métricas por segmento de Y, medias por repetición (no entrenamiento):
```
{selected_segments.round(4).to_string()}
```
LOW/HIGH usan Q25/Q75 de los 138 Y solamente para describir errores, sin selección ni pesos de entrenamiento. Tablas 44/45/48 guardan regiones con ≥5 parcelas, dispersión por perfil y errores extremos. Figuras 41/45/46 separan sesgo bajo/alto, residuos y heterogeneidad condicionada al rendimiento. La dispersión de predicciones entre repeticiones está en 47. Que haya menos bandas puede significar diferencias de modelos o eliminación de señal, nunca creación de información intraperfil.

## 8. Separar cantidad y distribución temporal

Extensión activada: {shape_extension}, por regla CLIMÁTICA declarada antes de mirar resultados predictivos: ≤4 componentes para 95% y totales positivos. Se estudia solo una representación acotada: S=P/sum(P), seis contrastes ortonormales Helmert que excluyen la dirección estructural de suma uno; PCA Euclidiano centrado sin rescalar coordenadas. Retiene valores cero, rechaza total cero, sin añadir pseudocuentas ni elegir log-ratios por búsqueda. Es PCA de la distribución relativa en el subespacio del simplex, no PCA log-ratio/Aitchison: su interpretación depende de geometría Euclidiana y no satisface todas las propiedades composicionales.

E8_SHAPE_PCR usa forma solamente; E8_TOTAL_SHAPE_RIDGE combina total estandarizado con 1..6 PCs de forma y elige K/alpha dentro del mismo inner CV. E1_TOTAL_LINEAR permite comparar cantidad sola, E8_PCR lluvia absoluta y estos dos forma/cantidad. No se introducen siete proporciones dependientes en una regresión sin reconocer la restricción. Tablas 29 y diccionario 53 documentan esa construcción; los scores globales de forma son descriptivos y no se suministran al CV.

## 9. Respuestas y límites de decisión

1. K90/K95: {k90}/{info['k95']}; la estructura temporal se interpreta con cargas observadas arriba.
2. La información geográfica se cuantifica en tabla 28; no se presume intensidad general si las cargas contrastan meses.
3. K por fold se conserva en 31/51, seleccionados internamente, no por un umbral de varianza global.
4–5. La comparación aleatoria, espacial y municipal y sus diferencias exactas constan en tabla 40 y decisión anterior: no se declara superioridad inconsistente.
6. Extremos se juzgan contra E3 bajo las mismas OOF (43/45), no con ajuste en entrenamiento.
7. Perfiles exactamente iguales permanecen indistinguibles por la representación; las bandas se distinguen de repeticiones de Y y agregación OOF.
8. Menor K reduce correlación y dimensión; 43 y 52 muestran si sacrifica capacidad predictiva o estabilidad. Mucha varianza explicada no equivale a mucho rendimiento explicado.
9. Para separar rendimientos intraperfil hacen falta fuentes independientes con resolución parcelaria: manejo, variedad, suelo, riego y fenología de campo, o lluvia de resolución superior. Validar esas fuentes en módulos posteriores y en otros ciclos etiquetados; no añadirlas retrospectivamente a E8.

Solo hay un ciclo con Y y 138 parcelas. Asociaciones no causales; hay confusión geográfica y optimismo al comparar varios experimentos. PCA no crea datos ni arregla automáticamente extremos. El experimento es retrospectivo a octubre 2025 y no evalúa pronóstico anticipado. Los resultados favorables y negativos se mantienen juntos. Ningún modelo sustituye Champion ni E3 automáticamente.

## Figuras

'''
    report+='\n'.join(f'![{file.stem}](../figures/{file.name})\n' for file in sorted((out/'figures').glob('*.png')))
    (out/'report/e8_technical_report.md').write_text(report,encoding='utf-8')
    write_interpretation(out)
    print(selected_metrics[['protocol','experiment','RMSE_mean','R2_mean','delta_RMSE_vs_E3_Ridge']].round(5).to_string(index=False),flush=True)
    return decision


def write_interpretation(out):
    """Answer the nine scientific questions from saved OOF, without model selection."""
    out=Path(out)
    c=pd.read_csv(out/'tables/40_model_comparison.csv')
    k=pd.read_csv(out/'tables/51_selected_K_distribution.csv')
    v=pd.read_csv(out/'tables/20_exploratory_variance.csv')
    segments=pd.read_csv(out/'tables/43_yield_segment_metrics_by_repeat.csv')
    s=segments.groupby(['protocol','experiment','yield_segment'])[['RMSE','MAE','bias_pred_minus_y']].mean()
    stability=pd.read_csv(out/'tables/47_prediction_stability_by_parcel.csv')
    profiles=pd.read_csv(out/'tables/05_seven_month_profile_groups.csv')
    from .rainfall_pcr_audit import load_data
    matrix,train=load_data()
    import geopandas as gpd
    from .rainfall_audit import SHAPE
    geo=gpd.read_file(SHAPE).rename(columns={'ID_POLIGON':ID})
    base=matrix[[ID]].merge(profiles,on=ID).merge(geo[[ID,'Estado','Municipio']],on=ID)
    base=base.merge(train[[ID,TARGET]],on=ID,how='left')
    census=base.groupby('exact_profile').agg(n_parcels=(ID,'size'),n_labeled=(TARGET,'count'),
        n_states=('Estado','nunique'),n_municipalities=('Municipio','nunique'),
        y_sd=(TARGET,'std'),y_min=(TARGET,'min'),y_max=(TARGET,'max')).reset_index()
    census['y_range']=census.y_max-census.y_min
    errors=pd.read_csv(out/'tables/45_error_by_profile_individual_oof.csv')
    individual=errors.merge(census,on='exact_profile',suffixes=('_evaluated','_all'),validate='many_to_one')
    individual['prediction_type']='individual fold OOF (repeats retained)'
    avg=pd.read_parquet(out/'tables/46_oof_averaged_diagnostic.parquet')
    avg['absolute_error']=abs(avg.y_pred-avg.y_true)
    averaged=avg.groupby(['protocol','experiment','exact_profile']).agg(
        prediction_sd=('y_pred','std'),MAE=('absolute_error','mean')).reset_index().merge(census,on='exact_profile')
    averaged['prediction_type']='mean OOF per parcel (diagnostic only)'
    pd.concat([individual,averaged],ignore_index=True).to_csv(out/'tables/55_profile_census_and_oof_dispersion.csv',index=False)
    lines=['# E8: interpretación de los resultados y nueve respuestas','',
        'Estas conclusiones usan las mismas 138 parcelas y las particiones congeladas de E3. '
        'No seleccionan un modelo nuevo mediante los controles externos de K fijo.','',
        f'1. **Dimensión climática.** Dos componentes explican {v.cumulative_variance.iloc[1]:.2%} '
        f'y tres {v.cumulative_variance.iloc[2]:.2%} de la variación estandarizada de lluvia. '
        'Ese umbral describe el clima y no garantiza preservar información de rendimiento.','',
        '2. **Patrones temporales.** Las cargas observadas de PC1 son positivas de abril a septiembre '
        'y débiles/negativas en octubre: resume variación conjunta de los primeros seis meses. '
        'PC2 contrapone octubre (positivo) con abril/mayo (negativos), un contraste tardío–temprano. '
        'PC3 contrapone abril/mayo/octubre con junio/septiembre. PC4 contrapone especialmente abril '
        'con mayo: solo explica 2.20% de varianza climática, pero su asociación descriptiva con Y '
        '(Pearson −0.285, Spearman −0.441) advierte contra eliminarlo por ese porcentaje. '
        'Los signos son convencionales y estas asociaciones no son efectos causales.','',
        '3. **Selección interna por fold.** Distribución de K (conteos, no porcentajes de varianza):','',
        '```',k[k.experiment.isin(['E8_PCR','E8_PCA_RIDGE','E8_SHAPE_PCR','E8_TOTAL_SHAPE_RIDGE'])].to_string(index=False),'```','']
    for number,protocol,title in [(4,'random','Validación aleatoria'),(5,'municipality','Transferencia municipal'),(5,'spatial','Transferencia espacial')]:
        rows=c[c.protocol.eq(protocol)&c.experiment.isin(['E3_MONTHLY_RIDGE','E8_PCR','E8_PCA_RIDGE','E8_SHAPE_PCR','E8_TOTAL_SHAPE_RIDGE'])]
        lines.extend([f'{number}. **{title}.** RMSE y cambio contra Ridge mensual, en t/ha:','',
            '```',rows[['experiment','RMSE_mean','delta_RMSE_vs_E3_Ridge','fold_win_fraction']].round(5).to_string(index=False),'```',''])
    lines.extend(['6. **Rendimientos extremos.** Cambios en RMSE/MAE y sesgo respecto a E3; '
        'un cambio negativo en RMSE/MAE favorece PCR. El sesgo positivo indica sobreestimación.',''])
    extreme=[]
    for protocol in ['random','climate_profile','municipality','spatial']:
        for segment in ['LOW','HIGH']:
            b=s.loc[(protocol,'E3_MONTHLY_RIDGE',segment)]
            for name in ['E8_PCR','E8_PCA_RIDGE']:
                a=s.loc[(protocol,name,segment)]
                extreme.append(dict(protocol=protocol,experiment=name,segment=segment,
                    delta_RMSE=a.RMSE-b.RMSE,delta_MAE=a.MAE-b.MAE,
                    candidate_bias=a.bias_pred_minus_y,reference_bias=b.bias_pred_minus_y))
    extremes=pd.DataFrame(extreme);extremes.to_csv(out/'tables/56_extreme_changes_vs_E3.csv',index=False)
    verdict=[]
    for protocol in ['random','climate_profile','municipality','spatial']:
        r=c[c.protocol.eq(protocol)&c.experiment.eq('E8_PCR')].iloc[0]
        word='aumenta' if r.delta_RMSE_vs_E3_Ridge>0 else 'reduce'
        verdict.append(f'PCR {word} RMSE {abs(r.delta_RMSE_vs_E3_Ridge):.5f} t/ha en {protocol}.')
    lines.extend([' '.join(verdict),
        'El cambio aleatorio es prácticamente nulo; la mejora espacial es pequeña y gana solo '
        '2 de 5 folds, con mayor dispersión. El deterioro municipal es claro. '
        'Por ello no hay superioridad consistente ni mejora robusta de transferencia.',''])
    geography=pd.read_csv(out/'tables/28_pc_geographic_structure.csv')
    pc2=geography[geography.component.eq('PC2')].set_index('region').descriptive_between_group_variance_fraction
    lines.extend([f'**Estructura geográfica:** {pc2["Municipio"]:.1%} de la varianza '
        f'descriptiva de PC2 corresponde a diferencias entre municipios y {pc2["Estado"]:.1%} '
        'entre estados. Es un contraste temporal fuertemente geográfico en estas parcelas; '
        'no implica causalidad ni predicción independiente fuera de esas regiones.',''])
    lines.extend(['```',extremes.round(4).to_string(index=False),'```','',
        'No hay una corrección automática de extremos: evaluar ambos segmentos y cada protocolo, '
        'sin convertir una mejora local en una afirmación general.','',
        'En aleatorio, PCR conserva la sobreestimación de Y bajos (+0.409 t/ha) y '
        'la subestimación de Y altos (−0.365 t/ha); los cambios de RMSE extremos '
        'son muy pequeños. En espacial mejora ambos segmentos, pero todavía '
        'sobreestima los bajos +1.090 t/ha. En municipal empeora el RMSE de ambos '
        'extremos: no se eliminó el problema.','',
        '7. **Bandas y resolución.** Persisten 53 perfiles exactos entre 197 parcelas. '
        'Una transformación determinista conserva su igualdad y no distingue sus rendimientos individuales. '
        'También existen valores de Y repetidos (bandas verticales con observado en x) y colisiones '
        'de predicciones entre perfiles diferentes. Tabla 55 reúne el censo de cada perfil, rango y SD de Y, '
        'SD de predicciones y MAE, separando OOF individuales de promedios. Los promedios son diagnósticos.','',
        '8. **Estabilidad frente a pérdida de información.** Los scores son ortogonales en entrenamiento; '
        'esto reduce multicolinealidad, pero no obliga a mejorar la predicción. Comparación de la SD '
        'entre folds, entre repeticiones y de la predicción de una misma parcela:',''])
    for name in ['E3_MONTHLY_RIDGE','E8_PCR','E8_PCA_RIDGE']:
        r=c[c.protocol.eq('random')&c.experiment.eq(name)].iloc[0]
        z=stability[stability.protocol.eq('random')&stability.experiment.eq(name)]
        lines.append(f'- {name}: SD RMSE folds={r.RMSE_fold_sd:.4f}; '
            f'SD RMSE repeticiones={r.RMSE_repeat_sd:.4f}; SD media predicción parcelaria={z.prediction_repeat_sd.mean():.4f} t/ha.')
    fixed=c[c.protocol.eq('random')&c.experiment.isin(['E8_PCR_K3','E8_PCR_K4'])]
    lines.extend(['','Controles externos descriptivos (no usados para elegir K):','',
        '```',fixed[['experiment','RMSE_mean']].round(5).to_string(index=False),'```','',
        'El control K=3 empeora claramente frente a K=4 aunque conserve 97.2% '
        'de la varianza climática. Las cargas dominantes son estables en CV aleatoria '
        '(coseno medio PC1–PC4 >0.995), pero K seleccionado varía y las direcciones '
        'cambian más al retirar municipios o bloques espaciales. La SD de RMSE entre '
        'repeticiones no disminuye para PCR: no hay una ganancia global de estabilidad.','',
        '9. **Fuentes adicionales.** Para diferenciar parcelas de un mismo perfil hacen falta '
        'observaciones independientes: manejo, variedad, suelo, riego, fenología o lluvia con mayor '
        'resolución espacial. Es una motivación para experimentos posteriores, no autorización para '
        'mezclar esas variables en E8. Hace falta validar nuevos ciclos y regiones.','',
        'La separación cantidad/forma se evaluó con seis contrastes Helmert, respetando la suma uno '
        'y conservando ceros mensuales. Es geometría Euclidiana del simplex, no log-ratio; '
        'sus resultados de transferencia están arriba. Se conserva cualquier deterioro. '
        'La decisión global está en decision.json: diferencias pequeñas o inconsistentes no '
        'establecen superioridad ni sustituyen Champion.',''])
    shape=c[c.experiment.eq('E8_TOTAL_SHAPE_RIDGE')]
    if (shape.delta_RMSE_vs_E3_Ridge>0).all():
        lines.extend(['**Resultado negativo de cantidad + forma:** el modelo combinado empeora '
            'RMSE frente a Ridge mensual en los cuatro protocolos. Separar ambas representaciones '
            'no mejoró la transferencia en este experimento. Forma sola tampoco ofrece una '
            'mejora consistente; sus resultados espaciales se conservan arriba.',''])
    lines.extend(['![Errores regionales OOF](../figures/47_regional_error_comparison.png)',''])
    (out/'report/e8_interpretation.md').write_text('\n'.join(lines),encoding='utf-8')
    report=out/'report/e8_technical_report.md'
    text=report.read_text(encoding='utf-8')
    link='[Interpretación explícita de las nueve preguntas](e8_interpretation.md)'
    if link not in text:report.write_text(text+'\n'+link+'\n',encoding='utf-8')
    regions=pd.read_csv(out/'tables/44_regional_metrics_by_repeat.csv')
    regions=regions[regions.region_type.eq('Estado')&regions.experiment.isin(['E3_MONTHLY_RIDGE','E8_PCR','E8_PCA_RIDGE'])]
    means=regions.groupby(['protocol','experiment','region']).RMSE.mean().reset_index()
    fig,axes=plt.subplots(1,2,figsize=(13,5))
    for protocol,ax in zip(['random','spatial'],axes):
        sns.barplot(data=means[means.protocol.eq(protocol)],x='region',y='RMSE',hue='experiment',ax=ax)
        ax.set_title(protocol+' — estados con al menos 5 parcelas');ax.set_ylabel('RMSE OOF (t/ha)');ax.tick_params(axis='x',rotation=20)
    save(fig,out,'47_regional_error_comparison.png')
