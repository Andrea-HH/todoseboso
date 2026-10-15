"""Post-hoc diagnostics of frozen PLS models; no refitting."""
from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
import joblib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.experimental_pls import OUT,metrics
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'outputs/research/pls1867_diagnostics/v1'
DEST.mkdir(parents=True,exist_ok=True)
base=pd.read_csv(ROOT/'outputs/research/variable_inventory/v1/inventario_1557.csv')
extra=pd.read_csv(ROOT/'outputs/research/experimental_variable_inventory/v1/variables_adicionales.csv')
lookup=dict(zip(base.variable,base.fuente));lookup.update(dict(zip(extra.variable,extra.grupo)))
names=sorted(lookup,key=len,reverse=True)
def origin(c):
    if c in lookup:return c,lookup[c]
    for n in names:
        if c.startswith(n+'_'):return n,lookup[n]
    return c,'Sin atribución'
x=pd.read_parquet(OUT/'cache/train138_1867.parquet').set_index('ID_POLIGONO')
meta=pd.read_parquet(OUT/'cache/labels_and_metadata.parquet').set_index('ID_POLIGONO')
regs=pd.read_csv(OUT/'tables/fit_registry.csv');features=[];comps=[];rotations=[]
for r in regs.itertuples():
    pack=joblib.load(OUT/'models'/f'{r.protocol}_{r.repeat}_{r.fold}.joblib');m=pack['pls'];rep=pack['representation']
    ids=json.loads(r.train_ids);y=meta.loc[ids,'RENDIMIENTO_T_HA'].to_numpy();scores=m.x_scores_
    ssy=(scores*scores).sum(axis=0)*(m.y_loadings_[0]**2)
    w=m.x_weights_;norm=(w*w).sum(axis=0)
    vip=np.sqrt(len(rep.names)*((w*w)/norm @ ssy)/ssy.sum())
    co=m.coef_.reshape(-1)
    for n,v,c in zip(rep.names,vip,co):
        original,source=origin(n);features.append(dict(protocol=r.protocol,repeat=r.repeat,fold=r.fold,encoded=n,original=original,source=source,vip=float(v),coefficient=float(c)))
    for k in range(m.n_components):
        sign=1 if m.y_loadings_[0,k]>=0 else -1
        row=dict(protocol=r.protocol,repeat=r.repeat,fold=r.fold,component=k+1,training_correlation_y=float(np.corrcoef(scores[:,k]*sign,y)[0,1]),retained=len(rep.names),n_original_retained=len(set(origin(n)[0] for n in rep.names)))
        for c in ['compact_precip_total','compact_early_fraction','compact_concentration_hhi','S2_ndvi_month_05','TOPO_BASIC_elevation_mean','TOPO_BASIC_slope_mean']:
            row['correlation_'+c]=float(np.corrcoef(scores[:,k]*sign,x.loc[ids,c].to_numpy(float))[0,1])
        comps.append(row)
        idx=np.argsort(abs(w[:,k]))[-12:][::-1]
        for i in idx:rotations.append(dict(protocol=r.protocol,repeat=r.repeat,fold=r.fold,component=k+1,feature=rep.names[i],weight=float(w[i,k]*sign)))
f=pd.DataFrame(features);f.to_csv(DEST/'feature_vip_coefficients_by_fold.csv',index=False)
f['absolute_coefficient']=abs(f.coefficient)
rank=f.groupby(['protocol','encoded','original','source']).agg(n_folds=('vip','size'),mean_vip=('vip','mean'),mean_absolute_coefficient=('absolute_coefficient','mean'),mean_coefficient=('coefficient','mean'),positive_fraction=('coefficient',lambda v:float((v>0).mean()))).reset_index()
rank.to_csv(DEST/'feature_summary.csv',index=False)
component=pd.DataFrame(comps);component.to_csv(DEST/'component_correlations.csv',index=False)
pd.DataFrame(rotations).to_csv(DEST/'component_top_weights_by_fold.csv',index=False)
fg=f.assign(vip_squared=f.vip**2).groupby(['protocol','repeat','fold','source']).agg(vip_squared_sum=('vip_squared','sum'),columns=('vip','size'),mean_vip_squared=('vip_squared','mean')).reset_index()
fg['vip_mass_share']=fg.vip_squared_sum/fg.groupby(['protocol','repeat','fold']).vip_squared_sum.transform('sum')
fs=fg.groupby(['protocol','source'])[['vip_mass_share','mean_vip_squared','columns']].mean().reset_index();fs.to_csv(DEST/'source_summary.csv',index=False)
p=pd.read_parquet(OUT/'tables/oof_predictions.parquet').merge(meta.reset_index()[['ID_POLIGONO','Estado','Municipio']],on='ID_POLIGONO')
p['error']=p.y_pred-p.y_true;p['abs_error']=abs(p.error);p['squared_error']=p.error**2
labels=meta.RENDIMIENTO_T_HA;cuts=labels.quantile([.25,.5,.75]).values
p['target_quartile']=np.searchsorted(cuts,p.y_true,side='left')+1
q=[]
for (pro,re,quart),g in p.groupby(['protocol','repeat','target_quartile']):q.append(dict(protocol=pro,repeat=re,quartile=quart,n=len(g),**metrics(g.y_true,g.y_pred)))
q=pd.DataFrame(q).groupby(['protocol','quartile'])[['n','rmse','mae','bias']].mean().reset_index();q.to_csv(DEST/'target_quartile_metrics.csv',index=False)
dist=[]
for (pro,re),g in p.groupby(['protocol','repeat']):
    dist.append(dict(protocol=pro,repeat=re,median_absolute_error=g.abs_error.median(),p90_absolute_error=g.abs_error.quantile(.9),max_absolute_error=g.abs_error.max(),fraction_over_1=float((g.abs_error>1).mean()),fraction_over_half=float((g.abs_error>.5).mean())))
pd.DataFrame(dist).groupby('protocol').mean(numeric_only=True).drop(columns='repeat').to_csv(DEST/'error_distribution.csv')
cases=p.groupby(['protocol','ID_POLIGONO','Estado','Municipio']).agg(y_true=('y_true','first'),y_pred=('y_pred','mean'),mean_abs_error=('abs_error','mean'),mean_error=('error','mean')).reset_index();cases.to_csv(DEST/'case_errors.csv',index=False)
regional=[]
refs=pd.read_parquet(OUT/'cache/reference_oof.parquet');ref=refs[refs.experiment.eq('C-T3')]
paired=p.merge(ref,on=['protocol','repeat','fold','ID_POLIGONO'],suffixes=('_pls','_ct3'),validate='one_to_one')
for (pro,re),g in paired.groupby(['protocol','repeat']):
    regions=[('all',np.ones(len(g),dtype=bool))]
    if pro=='spatial': regions +=[(f'omit_block_{k}',g.fold.ne(k).to_numpy()) for k in sorted(g.fold.unique())]
    for label,keep in regions:
        a=g.loc[keep];ea=(a.y_pred_pls-a.y_true_pls).to_numpy();eb=(a.y_pred_ct3-a.y_true_ct3).to_numpy()
        regional.append(dict(protocol=pro,repeat=re,subset=label,n=len(a),rmse_pls=float(np.sqrt(np.mean(ea**2))),rmse_ct3=float(np.sqrt(np.mean(eb**2))),delta_rmse=float(np.sqrt(np.mean(ea**2))-np.sqrt(np.mean(eb**2))),fraction_improved=float((abs(ea)<abs(eb)).mean()),bias_squared_pls=float(ea.mean()**2),error_variance_pls=float(ea.var())))
pd.DataFrame(regional).to_csv(DEST/'paired_and_block_omissions.csv',index=False)
print('original retained min/max',component.n_original_retained.min(),component.n_original_retained.max())
print('TOP RANDOM VIP');print(rank[rank.protocol.eq('random')].sort_values('mean_vip',ascending=False).head(14)[['encoded','source','mean_vip','mean_coefficient']].to_string(index=False))
print('COMPONENT CORRELATIONS');print(component.groupby(['protocol','component']).mean(numeric_only=True).filter(regex='correlation').round(3).to_string())
print('QUARTILES');print(q.round(3).to_string(index=False))
print('DISTRIBUTION');print(pd.DataFrame(dist).groupby('protocol').mean().round(3).to_string())
print('SPATIAL WORST');print(cases[cases.protocol.eq('spatial')].nlargest(6,'mean_abs_error').to_string(index=False))
print('PAIRED');print(pd.DataFrame(regional).groupby(['protocol','subset']).mean(numeric_only=True).round(3).to_string())
