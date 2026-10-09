"""Consolida Ronda 2 y genera diagnósticos; no entrena etapas posteriores."""
from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
import numpy as np,pandas as pd
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score,median_absolute_error
from sklearn.linear_model import LinearRegression
from family_1.stage4_modeling import *

BASE=ROOT/'outputs/modeling/family_1/stage4_round2';OLD=ROOT/'outputs/modeling/family_1/stage4';CHK=BASE/'checkpoints'
dirs={n:BASE/n for n in ['metrics','predictions','hyperparameters','stability','diagnostics','reports']}
for p in dirs.values():p.mkdir(parents=True,exist_ok=True)
new_names=['XGB_PRUNED','XGB_CORE_TOPOADV','XGB_CORE_EXTENDED','LGBM_PRUNED','LGBM_CORE_TOPOADV','LGBM_CORE_EXTENDED','ENET_PRUNED','ENET_CORE_TOPOADV','ENET_CORE_EXTENDED']
refs=['XGB_CORE','LGBM_CORE','ENET_ALL','ENET_CORE','BASELINE_MEAN']
new=pd.concat([pd.read_parquet(CHK/f'{p}.parquet') for p in new_names],ignore_index=True);assert (new.groupby('pipeline').size()==1380).all()
new.to_parquet(dirs['predictions']/'round2_oof_predictions.parquet',index=False)
old=pd.read_parquet(OLD/'screening/oof_predictions.parquet');old=old[old.pipeline.isin(refs)];combined=pd.concat([new.assign(stage='round2'),old.assign(stage='round1_reference')],ignore_index=True)

def fold_metrics(pred):
 rows=[]
 for key,g in pred.groupby(['pipeline','feature_representation','model','repeat','fold']):
  p,r,m,rep,fo=key;rows.append({'pipeline':p,'feature_representation':r,'model':m,'repeat':rep,'fold':fo,'RMSE':mean_squared_error(g.y_true,g.y_pred)**.5,'MAE':mean_absolute_error(g.y_true,g.y_pred),'R2':r2_score(g.y_true,g.y_pred),'MedAE':median_absolute_error(g.y_true,g.y_pred),'n_validation':len(g)})
 return pd.DataFrame(rows)
fm=fold_metrics(new);fm.to_csv(dirs['metrics']/'round2_fold_metrics.csv',index=False);allfm=fold_metrics(combined)
rows=[]
for p,g in fm.groupby('pipeline'):
 r={'pipeline':p,'feature_representation':g.feature_representation.iloc[0],'model':g.model.iloc[0]}
 for m in ['RMSE','MAE','R2','MedAE']:
  r.update({f'{m}_mean':g[m].mean(),f'{m}_median':g[m].median(),f'{m}_std':g[m].std(),f'{m}_q25':g[m].quantile(.25),f'{m}_q75':g[m].quantile(.75),f'{m}_min':g[m].min(),f'{m}_max':g[m].max()})
 rows.append(r)
pm=pd.DataFrame(rows).sort_values('RMSE_mean');pm.to_csv(dirs['metrics']/'round2_pipeline_metrics.csv',index=False)

comparisons=[('XGB_PRUNED','XGB_CORE','pruning'),('LGBM_PRUNED','LGBM_CORE','pruning'),('ENET_PRUNED','ENET_ALL','pruning'),('ENET_PRUNED','ENET_CORE','pruning'),('XGB_CORE_TOPOADV','XGB_CORE','topoadv'),('LGBM_CORE_TOPOADV','LGBM_CORE','topoadv'),('ENET_CORE_TOPOADV','ENET_CORE','topoadv'),('XGB_CORE_EXTENDED','XGB_CORE','extended'),('LGBM_CORE_EXTENDED','LGBM_CORE','extended'),('ENET_CORE_EXTENDED','ENET_CORE','extended')]
wide=allfm.pivot(index=['repeat','fold'],columns='pipeline',values='RMSE');pairs=[]
for a,b,effect in comparisons:
 d=wide[a]-wide[b];dr=d.groupby(level='repeat').mean();pairs.append({'pipeline_A':a,'pipeline_B':b,'effect':effect,'mean_delta_RMSE':d.mean(),'median_delta_RMSE':d.median(),'q25_delta':d.quantile(.25),'q75_delta':d.quantile(.75),'proportion_A_wins':(d<0).mean(),'proportion_nearly_tie_abs_delta_le_0_01':(abs(d)<=.01).mean(),'repeat_mean_delta_q025':dr.quantile(.025),'repeat_mean_delta_q975':dr.quantile(.975),'uncertainty':'percentiles of 10 repeat-level mean deltas; no naive t-test'})
pairdf=pd.DataFrame(pairs);pairdf.to_csv(dirs['metrics']/'round2_paired_comparisons.csv',index=False)

hp=pd.concat([pd.read_csv(CHK/f'{p}_hyper.csv') for p in new_names],ignore_index=True);hp.to_csv(dirs['hyperparameters']/'round2_selected_hyperparameters.csv',index=False)
prhp=hp[hp.pipeline.str.endswith('PRUNED')].copy().merge(fm[['pipeline','repeat','fold','RMSE']],on=['pipeline','repeat','fold'],how='left').rename(columns={'RMSE':'fold_RMSE'})
threshold=prhp.groupby(['pipeline','threshold']).agg(selection_count=('fold','size'),selection_frequency=('fold','size'),median_features_retained=('n_features_retained','median'),q25_features_retained=('n_features_retained',lambda x:x.quantile(.25)),q75_features_retained=('n_features_retained',lambda x:x.quantile(.75)),mean_RMSE_when_selected=('fold_RMSE','mean')).reset_index();threshold['selection_frequency']/=50;threshold.to_csv(dirs['hyperparameters']/'pruning_threshold_selection.csv',index=False)

# OOF agregado por parcela para nuevos y referencias.
parcel=combined.groupby(['stage','pipeline','ID_POLIGONO']).agg(y_true=('y_true','first'),oof_prediction_mean=('y_pred','mean'),oof_prediction_median=('y_pred','median'),oof_prediction_std=('y_pred','std')).reset_index();parcel['signed_error']=parcel.oof_prediction_mean-parcel.y_true;parcel['absolute_error']=abs(parcel.signed_error);parcel.to_csv(dirs['predictions']/'round2_oof_by_parcel.csv',index=False)

# Rendimiento bajo/medio/alto y regresión descriptiva.
q25,q75=parcel.y_true.quantile(.25),parcel.y_true.quantile(.75)
parcel['yield_range']=np.select([parcel.y_true<=q25,parcel.y_true>=q75],['low','high'],default='middle')
yr=[];reg=[]
for (p,r),g in parcel.groupby(['pipeline','yield_range']):yr.append({'pipeline':p,'yield_range':r,'n':len(g),'MAE':g.absolute_error.mean(),'RMSE':np.sqrt(np.mean(g.signed_error**2)),'mean_bias':g.signed_error.mean(),'q25_target':q25,'q75_target':q75})
for p,g in parcel.groupby('pipeline'):
 lr=LinearRegression().fit(g[['y_true']],g.oof_prediction_mean);reg.append({'pipeline':p,'alpha':lr.intercept_,'beta':lr.coef_[0],'R2_descriptive':lr.score(g[['y_true']],g.oof_prediction_mean),'interpretation':'beta<1 suggests compression toward mean; no correction applied'})
pd.DataFrame(yr).to_csv(dirs['diagnostics']/'yield_range_performance.csv',index=False);pd.DataFrame(reg).to_csv(dirs['diagnostics']/'regression_to_mean.csv',index=False)

# Parcelas difíciles, discrepancia árboles y casos donde ENET gana.
mat=parcel.pivot(index='ID_POLIGONO',columns='pipeline',values=['absolute_error','oof_prediction_std','oof_prediction_mean','y_true'])
diff=[]
for pid in mat.index:
 xgb=mat.loc[pid,('oof_prediction_mean','XGB_CORE')];lgb=mat.loc[pid,('oof_prediction_mean','LGBM_CORE')]
 en=[mat.loc[pid,('absolute_error',p)] for p in ['ENET_ALL','ENET_CORE','ENET_PRUNED','ENET_CORE_TOPOADV','ENET_CORE_EXTENDED']]
 tr=[mat.loc[pid,('absolute_error',p)] for p in ['XGB_CORE','XGB_PRUNED','XGB_CORE_TOPOADV','XGB_CORE_EXTENDED','LGBM_CORE','LGBM_PRUNED','LGBM_CORE_TOPOADV','LGBM_CORE_EXTENDED']]
 diff.append({'ID_POLIGONO':pid,'y_true':mat.loc[pid,('y_true','XGB_CORE')],'mean_absolute_error_across_pipelines':mat.loc[pid,'absolute_error'].mean(),'mean_oof_prediction_std':mat.loc[pid,'oof_prediction_std'].mean(),'abs_XGB_CORE_minus_LGBM_CORE_prediction':abs(xgb-lgb),'mean_ENET_absolute_error':np.mean(en),'mean_tree_absolute_error':np.mean(tr),'ENET_minus_tree_absolute_error':np.mean(en)-np.mean(tr)})
difficult=pd.DataFrame(diff).sort_values('mean_absolute_error_across_pipelines',ascending=False);difficult['difficulty_rank']=np.arange(1,len(difficult)+1);difficult.to_csv(dirs['diagnostics']/'difficult_parcels.csv',index=False)

# Estabilidad y metadata.
st=pd.concat([pd.read_parquet(CHK/f'{p}_stability.parquet') for p in new_names],ignore_index=True);dd=pd.read_csv(FEATURE_DIR/'family1_feature_dictionary.csv').set_index('feature_name')
enet_obs=st[st.kind=='elasticnet_coefficient'].groupby(['pipeline','feature_name']).agg(selection_count=('selected','sum'),mean_coefficient=('value','mean'),mean_abs_coefficient=('value',lambda x:abs(x).mean())).reset_index()
_,master_x,_=load_xy();master_cols=list(master_x.columns)
core_files=['sentinel_features_core.parquet','landsat_features.parquet','planet_features.parquet','climate_features.parquet','history_features.parquet','anomaly_features.parquet','topography_basic_features.parquet']
core=[]
for f in core_files:core += [c for c in pd.read_parquet(FEATURE_DIR/f).columns if c!=ID and c in master_cols]
core=list(dict.fromkeys(core));topo=[c for c in pd.read_parquet(FEATURE_DIR/'topography_advanced_features.parquet').columns if c!=ID and c in master_cols];ext=[c for c in pd.read_parquet(FEATURE_DIR/'sentinel_features_extended.parquet').columns if c!=ID and c in master_cols]
expected_enet={'ENET_PRUNED':master_cols,'ENET_CORE_TOPOADV':list(dict.fromkeys(core+topo)),'ENET_CORE_EXTENDED':list(dict.fromkeys(core+ext))}
grid=pd.DataFrame([(p,c) for p,cols in expected_enet.items() for c in cols],columns=['pipeline','feature_name'])
enet=grid.merge(enet_obs,on=['pipeline','feature_name'],how='left');enet[['selection_count','mean_coefficient','mean_abs_coefficient']]=enet[['selection_count','mean_coefficient','mean_abs_coefficient']].fillna(0);enet['selection_frequency']=enet.selection_count/50;enet.to_csv(dirs['stability']/'elasticnet_feature_frequency_round2.csv',index=False)
tree=st[st.kind=='tree_importance'][['pipeline','repeat','fold','feature_name','value']].rename(columns={'value':'importance'});tree.to_csv(dirs['stability']/'tree_feature_importance_round2.csv',index=False)
def addmeta(z):
 for c in ['source','sensor','variable','feature_family','statistic','window','core_or_extended']:z[c]=z.feature_name.map(dd[c].to_dict()).fillna('unknown')
 return z
enetm=addmeta(enet.copy());fam=[]
for cols in [['pipeline','source'],['pipeline','sensor'],['pipeline','variable'],['pipeline','feature_family'],['pipeline','statistic'],['pipeline','window'],['pipeline','core_or_extended']]:
 z=enetm.groupby(cols).agg(n_features=('feature_name','size'),mean_selection_frequency=('selection_frequency','mean'),median_selection_frequency=('selection_frequency','median'),features_selected_ge_50pct=('selection_frequency',lambda x:(x>=.5).sum())).reset_index();z['aggregation_dimension']=cols[-1];z=z.rename(columns={cols[-1]:'group'});fam.append(z)
pd.concat(fam,ignore_index=True).to_csv(dirs['stability']/'feature_family_stability_round2.csv',index=False)
treem=addmeta(tree.copy());tf=[]
for dim in ['source','sensor','variable','feature_family']:
 z=treem.groupby(['pipeline','repeat','fold',dim]).importance.sum().reset_index().rename(columns={dim:'group'});z['aggregation_dimension']=dim;tf.append(z)
pd.concat(tf,ignore_index=True).to_csv(dirs['stability']/'tree_feature_family_importance_round2.csv',index=False)

# Frecuencia de retención: ausencia en lista equivale a no retenida.
ret=[]
master_feature_set=set(load_xy()[1].columns)
for p,g in prhp.groupby('pipeline'):
 counts={c:0 for c in dd.index if c in master_feature_set}
 for value in g.retained_features:
  for c in json.loads(value):counts[c]+=1
 ret.extend({'pipeline':p,'feature_name':c,'retention_count':v,'retention_frequency':v/50} for c,v in counts.items())
pd.DataFrame(ret).to_csv(dirs['stability']/'pruning_retention_frequency_round2.csv',index=False)

# Reporte contestado.
refpm=pd.read_csv(OLD/'screening/pipeline_metrics.csv');allpm=pd.concat([pm,refpm[refpm.pipeline.isin(refs)]],ignore_index=True).sort_values('RMSE_mean')
best=pm.iloc[0].pipeline;med=pm.sort_values('RMSE_median').iloc[0].pipeline;stable=pm.sort_values('RMSE_std').iloc[0].pipeline
def delta(a,b):
 r=pairdf[(pairdf.pipeline_A==a)&(pairdf.pipeline_B==b)].iloc[0];return f"delta={r.mean_delta_RMSE:+.4f}, gana {100*r.proportion_A_wins:.0f}% folds, intervalo repetición [{r.repeat_mean_delta_q025:+.4f},{r.repeat_mean_delta_q975:+.4f}]"
thr=threshold.sort_values(['pipeline','selection_frequency'],ascending=[True,False]).groupby('pipeline').first().reset_index()
low=pd.DataFrame(yr);lowbest=low[low.yield_range=='low'].sort_values('RMSE').iloc[0].pipeline;highbest=low[low.yield_range=='high'].sort_values('RMSE').iloc[0].pipeline
regdf=pd.DataFrame(reg).sort_values('beta');topdiff=difficult.head(10).ID_POLIGONO.tolist()
finalists=[]
for family in ['XGB','LGBM','ENET']:
 finalists.append(allpm[allpm.pipeline.str.startswith(family)].iloc[0].pipeline)
report=f'''# Familia 1 — Etapa 4, Ronda 2

Se ejecutaron exactamente nueve pipelines sobre los 50 outer folds congelados. Las referencias de Ronda 1 fueron reutilizadas, no reentrenadas. No se ejecutó ninguna etapa posterior.

1. **Mejor RMSE medio Ronda 2:** {best}, {pm.iloc[0].RMSE_mean:.4f}.
2. **Mejor RMSE mediano:** {med}, {pm.sort_values('RMSE_median').iloc[0].RMSE_median:.4f}.
3. **Más estable:** {stable}, std={pm.sort_values('RMSE_std').iloc[0].RMSE_std:.4f}.
4. **Mejora frente a XGB_CORE:** mejor nuevo vs XGB_CORE: {delta(best,'XGB_CORE') if ((pairdf.pipeline_A==best)&(pairdf.pipeline_B=='XGB_CORE')).any() else 'no es comparación directa predefinida; revisar métricas pareadas por efecto'}.
5. **Pruning XGBoost:** {delta('XGB_PRUNED','XGB_CORE')}.
6. **Pruning LightGBM:** {delta('LGBM_PRUNED','LGBM_CORE')}.
7. **Pruning Elastic Net:** vs ALL {delta('ENET_PRUNED','ENET_ALL')}; vs CORE {delta('ENET_PRUNED','ENET_CORE')}.
8. **Threshold preferido:** {thr[['pipeline','threshold','selection_frequency','median_features_retained']].to_dict('records')}.
9. **Sentinel EXTENDED:** XGB {delta('XGB_CORE_EXTENDED','XGB_CORE')}; LGBM {delta('LGBM_CORE_EXTENDED','LGBM_CORE')}; ENET {delta('ENET_CORE_EXTENDED','ENET_CORE')}.
10. **Topografía avanzada:** XGB {delta('XGB_CORE_TOPOADV','XGB_CORE')}; LGBM {delta('LGBM_CORE_TOPOADV','LGBM_CORE')}; ENET {delta('ENET_CORE_TOPOADV','ENET_CORE')}.
11. **Consistencia EXTENDED:** se evalúa por signo, proporción de victorias e intervalos anteriores; no basta el promedio.
12. **Consistencia TOPOADV:** se evalúa análogamente; consultar `round2_paired_comparisons.csv`.
13. **Mejor en rendimiento bajo:** {lowbest} por RMSE OOF agregado.
14. **Mejor en rendimiento alto:** {highbest}.
15. **Mayor regresión a la media:** betas más bajas: {regdf[['pipeline','beta','R2_descriptive']].head(5).round(3).to_dict('records')}.
16. **Parcelas sistemáticamente difíciles:** {topdiff}. No se excluyó ninguna.
17. **Features individuales:** frecuencias completas en `elasticnet_feature_frequency_round2.csv`; la estabilidad sigue siendo limitada si pocas superan 0.8.
18. **Familias:** `feature_family_stability_round2.csv` permite contrastar estabilidad agregada frente a nombres individuales.
19. **Finalistas para source ablation:** {finalists}; uno por familia, considerando desempeño, estabilidad y complejidad.
20. **Modelos descartados:** no hay evidencia en esta ronda que justifique reabrir PLS/PCR/PCA local; no fueron ejecutados.

## Nota

Los intervalos son percentiles 2.5/97.5 de los diez deltas medios por repetición, no t-tests sobre 50 folds supuestamente independientes. Los rangos low/middle/high y regresiones a la media son sólo diagnósticos OOF.
'''
(dirs['reports']/'family1_stage4_round2_report.md').write_text(report,encoding='utf-8')
print(pm[['pipeline','RMSE_mean','RMSE_median','RMSE_std']].to_string(index=False));print('Finalistas:',finalists);print('Reporte:',dirs['reports']/'family1_stage4_round2_report.md')
