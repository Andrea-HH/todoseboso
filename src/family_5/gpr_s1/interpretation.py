"""Shared-support diagnostics and exploratory interpretation of restricted S1."""
import json
import joblib
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr
from . import execution as e

def write(summary):
    _,t,splits=e.load();p=pd.read_parquet(e.OUT/'tables/oof_predictions.parquet');rows=[]
    for protocol,repeat,fold,tr,va,inner in splits:
        a,v=t.iloc[tr],t.iloc[va]
        ref=joblib.load(e.old.OUT/'models'/f'F5-01_{protocol}_{repeat}_{fold}_outer_-1.joblib')
        common=cdist(ref.transform(v),ref.training_z_).min(axis=1)
        for exp in p.experiment.unique():
            g=p[(p.experiment==exp)&(p.protocol==protocol)&(p['repeat']==repeat)&(p.fold==fold)].set_index(e.ID).loc[v[e.ID]].copy()
            g['common_core_distance']=common;g['training_y_mean']=a[e.TARGET].mean();g['prediction_minus_train_mean']=g.y_pred-g.training_y_mean;g['observed_minus_train_mean']=g.y_true-g.training_y_mean
            g['error']=g.y_pred-g.y_true;g['absolute_error']=abs(g.error)
            if exp in e.SPECS:
                path=next((e.OUT/'models').glob(f'{exp}_{protocol}_{repeat}_{fold}_outer_-1_*.joblib'))
                model=joblib.load(path);gp=model.residual_gp_ if exp=='F5-S1-C' else model
                ell=np.atleast_1d(gp.gp_.kernel_.k1.k2.length_scale)[np.asarray(gp.groups_)]
                g['nearest_distance_optimized_kernel']=cdist(gp.transform(v)/ell,gp.training_z_/ell).min(axis=1)
                g['gp_prior_mean']=gp.target_mean_
                g['gp_deviation_from_prior']=abs(g.gp_correction-gp.target_mean_) if exp=='F5-S1-C' else abs(g.y_pred-gp.target_mean_)
            elif exp in ['F5-01','F5-00-C']:
                gp=ref if exp=='F5-01' else joblib.load(e.old.OUT/'models'/f'{exp}_{protocol}_{repeat}_{fold}_outer_-1.joblib')
                ell=np.atleast_1d(gp.gp_.kernel_.k1.k2.length_scale)[np.asarray(gp.groups_)]
                g['nearest_distance_optimized_kernel']=cdist(gp.transform(v)/ell,gp.training_z_/ell).min(axis=1)
                g['gp_prior_mean']=gp.target_mean_;g['gp_deviation_from_prior']=abs(g.y_pred-gp.target_mean_)
            rows.append(g.reset_index())
    q=pd.concat(rows,ignore_index=True);q.to_parquet(e.OUT/'tables/common_support_return_to_mean.parquet',index=False)
    diagnostics=[]
    for keys,g in q.groupby(['experiment','protocol','repeat','fold']):
        diagnostics.append(dict(zip(['experiment','protocol','repeat','fold'],keys))|dict(n=len(g),training_y_mean=g.training_y_mean.iloc[0],prediction_mean=g.y_pred.mean(),observed_mean=g.y_true.mean(),bias=g.error.mean(),error_variance=g.error.var(ddof=0),distance_mean=g.common_core_distance.mean(),prediction_deviation_mean=abs(g.prediction_minus_train_mean).mean(),observed_deviation_mean=abs(g.observed_minus_train_mean).mean(),distance_abs_error_spearman=spearmanr(g.common_core_distance,g.absolute_error).statistic,distance_prediction_deviation_spearman=spearmanr(g.common_core_distance,abs(g.prediction_minus_train_mean)).statistic))
    d=pd.DataFrame(diagnostics);d.to_csv(e.OUT/'tables/support_bias_dispersion_by_fold.csv',index=False)
    q.groupby(['experiment','protocol','repeat','fold'])[['nearest_distance_optimized_kernel','gp_deviation_from_prior','linear_prediction','gp_correction']].mean().reset_index().to_csv(e.OUT/'tables/kernel_support_and_trend_by_fold.csv',index=False)
    trend=[]
    for keys,g in q[q.experiment.eq('F5-S1-C')].groupby(['protocol','repeat','fold']):
        error=g.linear_prediction-g.y_true
        trend.append(dict(zip(['protocol','repeat','fold'],keys))|dict(n=len(g),trend_only_RMSE=np.sqrt(np.mean(error**2)),combined_RMSE=np.sqrt(np.mean(g.error**2)),trend_only_bias=error.mean(),combined_bias=g.error.mean(),gp_correction_mean=g.gp_correction.mean(),note='component of already-fitted C; no separate fitting or model selection'))
    pd.DataFrame(trend).to_csv(e.OUT/'tables/linear_mean_component_diagnostic.csv',index=False)
    # Identical shared-core support bins enable comparison despite 8-D monthly representation.
    bins=[]
    for keys,g in q.groupby(['experiment','protocol','repeat']):
        g=g.copy();g['support_bin']=pd.qcut(g.common_core_distance.rank(method='first'),4,labels=False)
        for b,h in g.groupby('support_bin'):
            bins.append(dict(zip(['experiment','protocol','repeat'],keys))|dict(bin=int(b),n=len(h),distance_min=h.common_core_distance.min(),distance_max=h.common_core_distance.max(),RMSE=np.sqrt(np.mean(h.error**2)),bias=h.error.mean(),prediction_deviation=abs(h.prediction_minus_train_mean).mean(),observed_deviation=abs(h.observed_minus_train_mean).mean()))
    pd.DataFrame(bins).to_csv(e.OUT/'tables/common_support_quartiles.csv',index=False)
    # Omitting actual municipalities, rather than only municipal folds, uses unchanged OOF.
    omissions=[]
    for x in e.SPECS:
        for base in ['F5-01','C-T3']:
            for protocol in ['spatial','municipality']:
                z=q[(q.experiment==x)&(q.protocol==protocol)].merge(q[(q.experiment==base)&(q.protocol==protocol)][[e.ID,'y_pred']],on=e.ID,suffixes=('','_base'),validate='one_to_one').merge(t[[e.ID,'Municipio']],on=e.ID)
                for municipality in z.Municipio.unique():
                    h=z[z.Municipio.ne(municipality)];er=h.y_pred-h.y_true;eb=h.y_pred_base-h.y_true
                    omissions.append(dict(candidate=x,baseline=base,protocol=protocol,omitted_municipality=municipality,n=len(h),delta_RMSE=np.sqrt(np.mean(er**2))-np.sqrt(np.mean(eb**2)),delta_MAE=abs(er).mean()-abs(eb).mean(),refit=False))
    pd.DataFrame(omissions).to_csv(e.OUT/'tables/municipality_omission_sensitivity.csv',index=False)
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(13,5))
    for exp in ['F5-01',*e.SPECS]:
        h=q[(q.experiment==exp)&(q.protocol=='spatial')]
        axes[0].scatter(h.common_core_distance,h.error,s=10,alpha=.45,label=exp)
        z=d[(d.experiment==exp)&(d.protocol=='spatial')];axes[1].plot(z.fold,z.bias,marker='o',label=exp)
    axes[0].set(xlabel='Distancia al soporte común compact3 + NDVI',ylabel='Error (t/ha)');axes[1].set(xlabel='Bloque espacial',ylabel='Sesgo (t/ha)')
    for ax in axes:ax.axhline(0,color='black',lw=.7);ax.legend(fontsize=8)
    fig.tight_layout();fig.savefig(e.OUT/'figures/support_and_spatial_bias.png',dpi=170);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(15,5))
    base=q[(q.experiment=='F5-01')&(q.protocol=='spatial')][[e.ID,'y_pred']]
    for ax,exp in zip(axes,e.SPECS):
        h=q[(q.experiment==exp)&(q.protocol=='spatial')].merge(base,on=e.ID,suffixes=('','_base'),validate='one_to_one')
        sc=ax.scatter(h.y_pred_base,h.y_pred,c=h.fold,cmap='tab10',s=18)
        lo=min(h.y_pred.min(),h.y_pred_base.min());hi=max(h.y_pred.max(),h.y_pred_base.max())
        ax.plot([lo,hi],[lo,hi],color='black',lw=.7);ax.set(xlabel='Predicci?n F5-01 (t/ha)',ylabel='Predicci?n sensibilidad (t/ha)',title=exp)
    fig.colorbar(sc,ax=axes.tolist(),label='Bloque espacial');fig.savefig(e.OUT/'figures/spatial_prediction_comparison.png',dpi=170,bbox_inches='tight');plt.close(fig)
    render(summary)

def markdown(frame):
    columns=['Modelo']+list(frame.columns)
    return '\n'.join(['| '+' | '.join(columns)+' |','| '+' | '.join(['---']*len(columns))+' |']+['| '+str(i)+' | '+' | '.join(f'{x:.6f}' for x in row)+' |' for i,row in frame.iterrows()])

def render(summary):
    lines=['# F5-S1 — Representación, suavidad y extrapolación','', 'Evaluación exploratoria de tres sensibilidades previamente congeladas, sobre las mismas 65 particiones y 138 rendimientos. Ninguna variante se selecciona mediante resultados espaciales; no hay promoción de Champion ni predicciones de las 59 parcelas.', '', '## RMSE OOF (t/ha)', '', markdown(summary.pivot(index='experiment',columns='protocol',values='RMSE').round(6)), '', '## Método e incertidumbre', '', 'Métricas calculadas sobre las 138 OOF de cada repetición; aleatoria resume las diez repeticiones. Los resultados por fold son diagnósticos y no reemplazan esta agregación. A cambia solo Matérn 3/2 por RBF. B sustituye compact3 por siete lluvias mensuales, escaladas dentro de entrenamiento y divididas por √7. C ajusta Ridge con penalización n·α, intercepto libre y α∈{0.001,0.01,0.1,1}; selecciona por RMSE medio de cuatro folds internos del pipeline completo y reajusta tendencia y GP usando únicamente entrenamiento externo.', '', 'La media lineal C es determinista estimada, no un kernel DotProduct: este último define covarianza aleatoria, otra distribución y otra inferencia. Los residuos de C se calculan dentro del mismo entrenamiento de la tendencia; no provienen del Champion ni de validación. El GP normaliza sus residuos dentro de entrenamiento. Esto también cambia la unidad cruda de los límites de amplitud y ruido, aunque conserva exactamente los límites estandarizados originales.', '', 'Los intervalos son gaussianos observacionales de 90%, incluyen WhiteKernel y excluyen incertidumbre de hiperparámetros y cambio de dominio. C además omite incertidumbre de los coeficientes de la tendencia. Cobertura observada y amplitud se reportan por separado: mayor cobertura con intervalos más anchos no demuestra mejor calibración.', '', 'Las distancias nativas de B y compact3 tienen distinta dimensión; la comparación entre modelos utiliza además un soporte común transformado por el F5-01 archivado del mismo fold, sin reajustarlo. El acercamiento a la media se examina mediante desviaciones predichas y observadas respecto de la media de entrenamiento. Son diagnósticos descriptivos, no una demostración causal de extrapolación.', '', 'Las omisiones de bloques, municipios y parcelas recalculan métricas de OOF existentes; no eliminan observaciones de los ajustes. Pares intraperfil se restringen a predicciones del mismo ajuste externo. Sus perfiles tienen igual peso, pero pocos perfiles repetidos y pares dependientes limitan las conclusiones. No se declara superioridad estadística.']
    (e.OUT/'report/synthesis.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    from .decision import append
    append()
