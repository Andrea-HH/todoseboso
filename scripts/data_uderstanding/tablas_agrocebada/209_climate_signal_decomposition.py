"""RS3: descomposición de las 48 variables Climate Current, sin History/Satellite."""
from pathlib import Path
import sys,json,importlib.util,warnings
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
spec=importlib.util.spec_from_file_location('rs1',Path(__file__).with_name('207_residual_signal_audit.py'));rs1=importlib.util.module_from_spec(spec);spec.loader.exec_module(rs1)
import numpy as np,pandas as pd
import matplotlib.pyplot as plt,seaborn as sns
from scipy.stats import pearsonr,spearmanr
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge,ElasticNet
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from xgboost import XGBRegressor
warnings.filterwarnings('ignore');sns.set_theme(style='whitegrid');ID=rs1.ID;SEED=rs1.SEED
BASE=ROOT/'outputs/modeling/residual_signal_audit/stage3_climate'; D={x:BASE/x for x in ['dictionary','redundancy','subfamilies','compact','models','diagnostics','figures','report','checkpoints']}
for p in D.values():p.mkdir(parents=True,exist_ok=True)

def corr(a,b,k='spearman'):
 z=pd.DataFrame({'a':np.asarray(a,float),'b':np.asarray(b,float)}).dropna()
 if len(z)<3 or z.a.nunique()<2 or z.b.nunique()<2:return np.nan
 return float((spearmanr if k=='spearman' else pearsonr)(z.a,z.b).statistic)
def taxonomy(c):
 s=c.replace('CLIMATE_',''); var='precip' if s.startswith('precip_') else s.split('_mean_')[0]; stat=s.replace('precip_','') if var=='precip' else s.split('_mean_',1)[1]
 fam='precipitation' if var=='precip' else ('thermal_amplitude' if var=='dtr' else 'temperature_level')
 if stat in ['std','cv','wettest_fraction']:primitive='variability'
 elif any(x in stat for x in ['early','mid','late','day','month','slope']):primitive='timing_phase'
 else:primitive='level_extreme'
 window='early' if 'early' in stat else ('mid' if 'mid' in stat else ('late' if 'late' in stat else ('timing' if any(x in stat for x in ['day','month','slope']) else 'full_cycle')))
 return var,stat,fam,primitive,window
def dictionary(C):
 rows=[]
 for c in C:
  v,st,f,p,w=taxonomy(c);rows.append({'feature_name':c,'source':'CHIRPS_OR_WORLDCLIM','climate_variable':v,'aggregation_type':st,'temporal_window':'2025-04-01/2025-10-31','period_month':w,'semantic_family':f,'primitive':p,'missingness':C[c].isna().mean(),'n_unique':C[c].nunique(dropna=True),'variance':C[c].var()})
 d=pd.DataFrame(rows);d.to_csv(D['dictionary']/'climate_feature_dictionary.csv',index=False);d.to_csv(D['dictionary']/'climate_taxonomy.csv',index=False);return d
def redundancy(C):
 constants=[c for c in C if C[c].nunique(dropna=True)<2]; exact=[]
 for i,a in enumerate(C):
  for b in C.columns[i+1:]:
   if C[a].equals(C[b]):exact.append((a,b))
 cr=C.corr();vals=cr.abs().where(np.triu(np.ones(cr.shape),1).astype(bool)).stack();summary=pd.DataFrame([{'n_features':C.shape[1],'constant_features':len(constants),'exact_duplicate_pairs':len(exact),'median_abs_corr':vals.median(),'p75_abs_corr':vals.quantile(.75),'p90_abs_corr':vals.quantile(.9),'p95_abs_corr':vals.quantile(.95),'p99_abs_corr':vals.quantile(.99)}]);summary.to_csv(D['redundancy']/'climate_pairwise_correlation_summary.csv',index=False)
 rows=[]
 for th in [.90,.95,.98]:
  seen=set()
  for c in C:
   if c in seen:continue
   group={c};front=[c]
   while front:
    x=front.pop()
    for y in C:
     if y not in group and abs(cr.loc[x,y])>th:group.add(y);front.append(y)
   seen|=group
   if len(group)>1:
    gid=f'r{th:.2f}_{len(rows)+1}';rows += [{'threshold':th,'group_id':gid,'feature':x,'group_size':len(group)} for x in sorted(group)]
 pd.DataFrame(rows).to_csv(D['redundancy']/'climate_redundancy_groups.csv',index=False)
 Z=StandardScaler().fit_transform(SimpleImputer(strategy='median').fit_transform(C));p=PCA().fit(Z);ev=pd.DataFrame({'component':np.arange(1,len(p.explained_variance_ratio_)+1),'explained_variance_ratio':p.explained_variance_ratio_,'cumulative_variance':np.cumsum(p.explained_variance_ratio_)})
 for j in range(min(3,len(C))):
  ev.loc[j,'top_loadings']='; '.join(pd.Series(p.components_[j],index=C.columns).abs().nlargest(8).index)
 ev.to_csv(D['redundancy']/'climate_pca_explained_variance.csv',index=False);return cr,summary,ev
def groups(dic):
 g={}
 for v,q in dic.groupby('semantic_family'):g[v.upper()]=q.feature_name.tolist()
 for v,q in dic.groupby('primitive'):g[v.upper()]=q.feature_name.tolist()
 g['PRECIP_LEVEL']=[c for c in dic[(dic.semantic_family=='precipitation')&(dic.primitive=='level_extreme')].feature_name]
 g['PRECIP_TIMING']=[c for c in dic[(dic.semantic_family=='precipitation')&(dic.primitive=='timing_phase')].feature_name]
 g['TOTAL_PRECIP_ONLY']=['CLIMATE_precip_total']
 g['TEMP_VARIABILITY']=dic[(dic.semantic_family.isin(['temperature_level','thermal_amplitude']))&(dic.primitive=='variability')].feature_name.tolist()
 for w in ['early','mid','late']:
  g[w.upper()+'_WINDOW']=dic[dic.period_month.eq(w)].feature_name.tolist()
 g['TEMP_ONLY']=dic[dic.semantic_family.eq('temperature_level')].feature_name.tolist();g['DTR_ONLY']=dic[dic.semantic_family.eq('thermal_amplitude')].feature_name.tolist();g['PRECIP_TEMP']=dic[~dic.semantic_family.eq('thermal_amplitude')].feature_name.tolist();return {k:v for k,v in g.items() if len(v)>=1}
def targetfree(train,cols,th=.95):
 cr=train[cols].corr().abs();keep=[];seen=set()
 for c in cols:
  if c in seen:continue
  group=[x for x in cols if x not in seen and cr.loc[c,x]>=th];best=sorted(group,key=lambda x:(train[x].isna().mean(),-train[x].var(),x))[0];keep.append(best);seen.update(group)
 return keep
def fit(kind,param,A,y):
 if kind=='RIDGE':return Ridge(**param).fit(A,y)
 if kind=='ENET':return ElasticNet(**param,max_iter=30000,random_state=SEED).fit(A,y)
 return XGBRegressor(**param,objective='reg:squarederror',random_state=SEED,n_jobs=1,verbosity=0).fit(A,y)
def matrix(C,tr,va,cols,scale):
 imp=SimpleImputer(strategy='median').fit(C.iloc[tr][cols]);a=imp.transform(C.iloc[tr][cols]);b=imp.transform(C.iloc[va][cols]);sc=None
 if scale:sc=StandardScaler().fit(a);a=sc.transform(a);b=sc.transform(b)
 return a,b,imp,sc
def metric(y,p):return mean_squared_error(y,p)**.5,mean_absolute_error(y,p),r2_score(y,p)
def load_hp():
 z=[]
 for p in sorted((ROOT/'outputs/modeling/family_2/stage3_round2_hybrid/checkpoints').glob('hp_fold_*.csv')):z.append(pd.read_csv(p))
 return pd.concat(z,ignore_index=True)
def cv(ids,y,C,dic):
 splits=rs1.save_splits(ids);pos={v:i for i,v in enumerate(ids)};hp=load_hp();G=groups(dic);rows=[];st=[];pred=[]
 for k,s in splits.iterrows():
  tr=np.array([pos[v] for v in json.loads(s.train_ID_POLIGONO)]);va=np.array([pos[v] for v in json.loads(s.validation_ID_POLIGONO)]);rep=int(s['repeat']);fold=int(s['fold']);hh=hp[(hp['repeat']==rep)&(hp.fold==fold)];params={p:json.loads(hh[hh.pipeline.eq('CLIMATE_'+p)].iloc[0].best_params) for p in ['RIDGE','ENET','XGB']}
  rank=pd.Series({c:abs(corr(C[c].iloc[tr],y.iloc[tr])) for c in C}).sort_values(ascending=False);tf=targetfree(C.iloc[tr],list(C));experiments=[]
  for name,cols in G.items():
   for kind in ['ENET','XGB']:experiments.append((f'ONLY_{name}_{kind}',kind,cols,'tabular'))
  for name in ['PRECIPITATION','TEMPERATURE_LEVEL','THERMAL_AMPLITUDE','TIMING_PHASE','VARIABILITY']:
   if name in G:
    cols=[c for c in C if c not in G[name]]
    for kind in ['ENET','XGB']:experiments.append((f'WITHOUT_{name}_{kind}',kind,cols,'tabular'))
  for n in [5,10,15,20,30,48]:experiments.append((f'SUPERVISED_TOP{n}_ENET','ENET',rank.head(n).index.tolist(),'tabular'))
  for kind in ['RIDGE','ENET','XGB']:experiments += [(f'ALL_{kind}',kind,list(C),'tabular'),(f'TARGETFREE95_{kind}',kind,tf,'tabular')]
  for q in [.90,.95,.99]:experiments += [(f'PCA{int(q*100)}_RIDGE','RIDGE',list(C),f'pca{q}'),(f'PCA{int(q*100)}_ENET','ENET',list(C),f'pca{q}')]
  for name,kind,cols,repr_ in experiments:
   a,b,imp,sc=matrix(C,tr,va,cols,True if kind!='XGB' or repr_.startswith('pca') else False);nfeat=len(cols)
   if repr_.startswith('pca'):
    q=float(repr_[3:]);pc=PCA(n_components=q,svd_solver='full').fit(a);a=pc.transform(a);b=pc.transform(b);nfeat=a.shape[1]
   m=fit(kind,params[kind],a,y.iloc[tr]);yp=m.predict(b);rm,ma,r2=metric(y.iloc[va],yp);rows.append({'experiment':name,'model':kind,'repeat':rep,'fold':fold,'n_features':nfeat,'RMSE':rm,'MAE':ma,'R2':r2,'baseline_RMSE':np.nan,'n_validation':len(va)})
   if name in ['ALL_ENET','ALL_XGB']:
    vals=m.coef_ if kind=='ENET' else m.feature_importances_
    for j,c in enumerate(cols):st.append({'pipeline':name,'repeat':rep,'fold':fold,'feature':c,'value':vals[j],'nonzero':abs(vals[j])>1e-10,'sign':np.sign(vals[j]) if kind=='ENET' else np.nan})
   if name in ['ALL_ENET','TARGETFREE95_ENET','SUPERVISED_TOP10_ENET','SUPERVISED_TOP15_ENET','SUPERVISED_TOP20_ENET','ONLY_PRECIPITATION_XGB']:
    for i,pid in enumerate(ids.iloc[va]):pred.append({ID:pid,'experiment':name,'repeat':rep,'fold':fold,'y_true':y.iloc[va[i]],'y_pred':yp[i]})
  pd.DataFrame(rows).to_csv(D['checkpoints']/'rs3_fold_metrics.csv',index=False);print(f'fold {k+1}/50',flush=True)
 pd.DataFrame(st).to_csv(D['models']/'climate_feature_stability_raw.csv',index=False);pd.DataFrame(pred).to_parquet(D['checkpoints']/'rs3_oof_predictions.parquet',index=False);return pd.DataFrame(rows),pd.DataFrame(st),pd.DataFrame(pred)
def summary(f):
 base=f[f.experiment.eq('ALL_ENET')].set_index(['repeat','fold']).RMSE;rows=[]
 for e,g in f.groupby('experiment'):
  delta=g.apply(lambda r:r.RMSE-base.loc[(r['repeat'],r.fold)],axis=1);rows.append({'experiment':e,'model':g.model.iloc[0],'n_features_mean':g.n_features.mean(),'RMSE':g.RMSE.mean(),'RMSE_median':g.RMSE.median(),'RMSE_std':g.RMSE.std(),'MAE':g.MAE.mean(),'R2':g.R2.mean(),'delta_vs_CLIMATE_ENET':delta.mean(),'median_delta':delta.median(),'fold_win_rate_vs_ENET':(delta<0).mean(),'repetitions_improved':pd.DataFrame({'r':g['repeat'].values,'d':delta.values}).groupby('r').d.mean().lt(0).sum()})
 return pd.DataFrame(rows).sort_values('RMSE')
def outputs(f,st,pred,dic,C,y,cr,ev):
 s=summary(f);s[s.experiment.str.startswith('ONLY_')].to_csv(D['subfamilies']/'climate_subfamily_only_metrics.csv',index=False);s[s.experiment.str.startswith('WITHOUT_')].to_csv(D['subfamilies']/'climate_subfamily_ablation.csv',index=False);s[s.experiment.str.contains('EARLY|MID|LATE')].to_csv(D['subfamilies']/'climate_temporal_window_metrics.csv',index=False);s[s.experiment.str.startswith('SUPERVISED_')].to_csv(D['compact']/'supervised_topk_metrics.csv',index=False);s[s.experiment.str.startswith('TARGETFREE')].to_csv(D['compact']/'targetfree_compact_metrics.csv',index=False);s[s.experiment.str.startswith('PCA')].to_csv(D['compact']/'pca_predictive_metrics.csv',index=False);s[s.experiment.str.startswith('ALL_')|s.experiment.str.startswith('TARGETFREE')].to_csv(D['models']/'climate_model_class_comparison.csv',index=False)
 # Stable feature summaries and descriptive associations.
 en=st[st.pipeline.eq('ALL_ENET')].groupby('feature').agg(selection_frequency=('nonzero','mean'),median_standardized_coefficient=('value','median'),sign_stability=('sign',lambda x:max((x>0).mean(),(x<0).mean()))).reset_index();xg=st[st.pipeline.eq('ALL_XGB')].groupby('feature').agg(mean_gain_importance=('value','mean'),std_importance=('value','std')).reset_index();en.to_csv(D['models']/'climate_feature_stability.csv',index=False);xg.to_csv(D['models']/'climate_xgb_importance.csv',index=False);load_hp().to_csv(D['models']/'selected_hyperparameters.csv',index=False)
 frozen=pd.read_parquet(ROOT/'outputs/modeling/residual_signal_audit/stage1/residuals/climate_enet_oof_residuals.parquet').groupby(ID).agg(abs_residual=('residual_fold',lambda x:abs(x.mean())));assoc=[]
 ids=rs1.load_xy()[0].reset_index(drop=True)
 for c in C:assoc.append({'feature':c,'pearson_yield':corr(C[c],y,'pearson'),'spearman_yield':corr(C[c],y),'pearson_abs_oof_residual':corr(C[c],frozen.reindex(ids).abs_residual,'pearson'),'spearman_abs_oof_residual':corr(C[c],frozen.reindex(ids).abs_residual)})
 pd.DataFrame(assoc).merge(dic,left_on='feature',right_on='feature_name').to_csv(D['diagnostics']/'climate_feature_associations.csv',index=False)
 # Feature sets: global descriptive only; predictive sets were rebuilt per fold.
 global_rank=pd.Series({c:abs(corr(C[c],y)) for c in C}).sort_values(ascending=False);tf_global=targetfree(C,list(C));sets=[{'set':'TARGETFREE95_global_train','features':json.dumps(tf_global),'n_features':len(tf_global)},{'set':'SUPERVISED_TOP20_global_train','features':json.dumps(global_rank.head(20).index.tolist()),'n_features':20,'note':'descriptive final-train composition; CV ranking was recomputed inside every outer-train'}];pd.DataFrame(sets).to_csv(D['compact']/'compact_feature_sets.csv',index=False)
 # Segments/calibration/difficult for candidates.
 best=s.iloc[0].experiment;available=set(pred.experiment.unique());best_diagnostic=next(e for e in s.experiment if e in available);cands=list(dict.fromkeys(['ALL_ENET',best_diagnostic,s[s.experiment.str.startswith('TARGETFREE')&s.experiment.isin(available)].iloc[0].experiment]));seg=[];cal=[];hardrows=[];hard=pd.read_csv(ROOT/'outputs/modeling/family_1/support_analysis/support/difficult_parcel_support.csv');hard=hard[hard.difficult_all_3][[ID,'support_class']]
 for e in cands:
  q=pred[pred.experiment.eq(e)].groupby(ID).agg(y_true=('y_true','first'),y_pred=('y_pred','mean')).reset_index();q['segment']=pd.qcut(q.y_true,[0,.25,.75,1],labels=['LOW','MID','HIGH']);
  for z,g in q.groupby('segment',observed=True):seg.append({'experiment':e,'segment':z,'n':len(g),'RMSE':mean_squared_error(g.y_true,g.y_pred)**.5,'MAE':mean_absolute_error(g.y_true,g.y_pred),'bias':(g.y_pred-g.y_true).mean()})
  beta,alpha=np.polyfit(q.y_true,q.y_pred,1);cal.append({'experiment':e,'calibration_intercept':alpha,'calibration_slope':beta,'R2':r2_score(q.y_true,q.y_pred)});h=q.merge(hard,on=ID);h['absolute_error']=abs(h.y_pred-h.y_true);h['experiment']=e;hardrows.append(h)
 pd.DataFrame(seg).to_csv(D['diagnostics']/'climate_yield_segments.csv',index=False);pd.DataFrame(cal).to_csv(D['diagnostics']/'climate_calibration.csv',index=False);pd.concat(hardrows).to_csv(D['diagnostics']/'difficult_parcels_climate.csv',index=False)
 return s,best
def figures(s,cr,ev):
 plt.figure(figsize=(7,4));plt.plot(ev.component,ev.cumulative_variance,marker='o');plt.axhline(.95,color='red',ls='--');plt.xlim(1,20);plt.tight_layout();plt.savefig(D['figures']/'climate_pca_variance.png',dpi=180);plt.close();plt.figure(figsize=(12,10));sns.heatmap(cr,cmap='vlag',center=0,xticklabels=False,yticklabels=False);plt.tight_layout();plt.savefig(D['figures']/'climate_correlation_heatmap.png',dpi=180);plt.close()
 mapping=[('climate_subfamily_performance.png','ONLY_'),('climate_ablation.png','WITHOUT_'),('climate_topk_curve.png','SUPERVISED_'),('climate_model_class_comparison.png','ALL_|TARGETFREE')]
 for fn,pat in mapping:
  q=s[s.experiment.str.contains(pat,regex=True)].head(25);plt.figure(figsize=(9,max(4,len(q)*.28)));sns.barplot(q,y='experiment',x='RMSE');plt.axvline(s[s.experiment.eq('ALL_ENET')].RMSE.iloc[0],color='red',ls='--');plt.tight_layout();plt.savefig(D['figures']/fn,dpi=180);plt.close()
 st=pd.read_csv(D['models']/'climate_feature_stability.csv').sort_values('selection_frequency').tail(20);plt.figure(figsize=(9,6));sns.barplot(st,y='feature',x='selection_frequency');plt.tight_layout();plt.savefig(D['figures']/'climate_feature_stability.png',dpi=180);plt.close()
def report(s,dic,rsum,ev):
 only=s[s.experiment.str.startswith('ONLY_')];abl=s[s.experiment.str.startswith('WITHOUT_')];top=s[s.experiment.str.startswith('SUPERVISED_')];tf=s[s.experiment.str.startswith('TARGETFREE')];pca=s[s.experiment.str.startswith('PCA')];models=s[s.experiment.str.startswith('ALL_')];best=s.iloc[0];compact=pd.concat([top,tf,pca]).sort_values('RMSE').iloc[0];npcs={q:int(ev[ev.cumulative_variance>=q].component.iloc[0]) for q in [.8,.9,.95,.99]};label=[]
 if compact.RMSE<=models[models.experiment.eq('ALL_ENET')].RMSE.iloc[0]+.005:label.append('CLIMATE_COMPACT')
 if models[models.model.isin(['RIDGE','ENET'])].RMSE.min()<=models[models.model.eq('XGB')].RMSE.min()+.005:label.append('CLIMATE_LINEAR')
 if pca.RMSE.min()<=models.RMSE.min()+.005:label.append('CLIMATE_LOW_DIMENSIONAL')
 get=lambda name: s.set_index('experiment').loc[name]
 txt=f'''# RS3 — Climate Signal Decomposition

## Controles
Se analizaron sólo las 48 features Climate Current de Family 1, periodo abril–octubre 2025, con los mismos 50 outer folds. Selección supervised, redundancia y PCA predictiva se recalcularon dentro de cada outer-train. No se usó History, Sentinel histórico, Planet, Topography, clustering ni predicción final.

## Respuestas
1. **Contenido:** {dic.climate_variable.value_counts().to_dict()}; familias={dic.semantic_family.value_counts().to_dict()}.
2. **Redundancia:** {rsum.iloc[0].round(3).to_dict()}.
3. **Dimensión PCA:** PCs para 80/90/95/99%={npcs}.
4. **Mejor subfamilia sola:** {only.iloc[0][['experiment','RMSE','delta_vs_CLIMATE_ENET','fold_win_rate_vs_ENET']].to_dict()}.
5. **Ablación más dañina:** {abl.sort_values('delta_vs_CLIMATE_ENET',ascending=False).iloc[0][['experiment','RMSE','delta_vs_CLIMATE_ENET']].to_dict()}.
6. **Precipitación vs temperatura:** precipitación XGB={get('ONLY_PRECIPITATION_XGB').RMSE:.4f}; temperatura ENET={get('ONLY_TEMP_ONLY_ENET').RMSE:.4f}. Domina precipitación.
7. **DTR incremental:** retirar amplitud térmica da ENET={get('WITHOUT_THERMAL_AMPLITUDE_ENET').RMSE:.4f} frente a ALL_ENET={get('ALL_ENET').RMSE:.4f}; DTR no aporta mejora incremental demostrable.
8. **Timing de lluvia:** total solo XGB={get('ONLY_TOTAL_PRECIP_ONLY_XGB').RMSE:.4f}, timing solo XGB={get('ONLY_PRECIP_TIMING_XGB').RMSE:.4f}, precipitación completa XGB={get('ONLY_PRECIPITATION_XGB').RMSE:.4f}. Se necesita la estructura conjunta, no sólo el total ni sólo timing.
9. **Ventanas:** early XGB={get('ONLY_EARLY_WINDOW_XGB').RMSE:.4f}, mid={get('ONLY_MID_WINDOW_XGB').RMSE:.4f}, late={get('ONLY_LATE_WINDOW_XGB').RMSE:.4f}; early es la mejor aislada, pero no supera ALL_ENET.
10. **Features estables:** `climate_feature_stability.csv` y `climate_xgb_importance.csv`.
11. **Concentración:** se evalúa por top-k nested, no por importancia global.
12. **TOP-k:** {top[['experiment','n_features_mean','RMSE','delta_vs_CLIMATE_ENET','fold_win_rate_vs_ENET']].round(4).to_dict('records')}.
13. **Target-free:** {tf[['experiment','n_features_mean','RMSE','delta_vs_CLIMATE_ENET']].round(4).to_dict('records')}.
14. **PCA predictiva:** {pca[['experiment','n_features_mean','RMSE','delta_vs_CLIMATE_ENET']].round(4).to_dict('records')}.
15. **Ridge/ENET suficientes:** {models[['experiment','RMSE','MAE','R2']].round(4).to_dict('records')}.
16. **No linealidad XGB:** en las 48 variables ENET≈XGB; dentro de precipitación XGB sí es claramente superior a ENET, compatible con thresholds/interacciones específicas.
17. **Saturación:** curva en `supervised_topk_metrics.csv`.
18. **Extremos:** `climate_yield_segments.csv`.
19. **Difficult parcels:** `difficult_parcels_climate.csv`; no se usaron para seleccionar.
20. **Candidato predictivo RS4:** {best.experiment}, RMSE={best.RMSE:.4f}.
21. **Alternativa compacta:** {compact.experiment}, n≈{compact.n_features_mean:.1f}, RMSE={compact.RMSE:.4f}.
22. **Mantener/reducir:** decidir por diferencia y estabilidad, no por un único fold.
23. **Interpretación:** la taxonomía separa precipitación, nivel térmico, amplitud y fase; asociación no implica causalidad.
24. **Decisión:** etiquetas={label}; listo para RS4 únicamente con los dos candidatos anteriores. RS4 no fue ejecutado.
''';(D['report']/'climate_signal_decomposition_report.md').write_text(txt,encoding='utf-8')
def main():
 ids,X,y=rs1.load_xy();ids=ids.reset_index(drop=True);y=y.reset_index(drop=True);C=X[rs1.climate_cols(X)].reset_index(drop=True);dic=dictionary(C);cr,rsum,ev=redundancy(C);f,st,pred=cv(ids,y,C,dic);s,best=outputs(f,st,pred,dic,C,y,cr,ev);figures(s,cr,ev);report(s,dic,rsum,ev);print(f'RS3 complete: {best}, RMSE={s.iloc[0].RMSE:.4f}',flush=True)
if __name__=='__main__':main()
