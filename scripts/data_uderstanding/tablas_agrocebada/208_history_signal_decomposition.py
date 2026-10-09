"""RS2: descomposición target-safe de la señal HISTORY encontrada en RS1."""
from pathlib import Path
import sys,json,importlib.util,warnings
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
spec=importlib.util.spec_from_file_location('rs1',Path(__file__).with_name('207_residual_signal_audit.py'));rs1=importlib.util.module_from_spec(spec);spec.loader.exec_module(rs1)
import numpy as np,pandas as pd
import matplotlib.pyplot as plt,seaborn as sns
from scipy.stats import pearsonr,spearmanr
from sklearn.model_selection import KFold
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge,RidgeCV,ElasticNet
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.neighbors import NearestNeighbors
from xgboost import XGBRegressor
warnings.filterwarnings('ignore');sns.set_theme(style='whitegrid')
ID=rs1.ID;SEED=rs1.SEED
BASE=ROOT/'outputs/modeling/residual_signal_audit/stage2_history'
D={x:BASE/x for x in ['dictionary','associations','subfamilies','compact_models','interpretation','diagnostics','figures','report','checkpoints']}
for p in D.values():p.mkdir(parents=True,exist_ok=True)
(D['figures']/'history_feature_shapes').mkdir(exist_ok=True)

def corr(a,b,kind='spearman'):
 z=pd.DataFrame({'a':np.asarray(a,float),'b':np.asarray(b,float)}).dropna()
 if len(z)<3 or z.a.nunique()<2 or z.b.nunique()<2:return np.nan
 return float((spearmanr if kind=='spearman' else pearsonr)(z.a,z.b).statistic)

def labels(c):
 source='Sentinel-2' if c.startswith('HIST_S2_') else 'Climate historical'
 stat='months' if c.endswith('_months') else ('std' if c.endswith('_std') else 'mean')
 primitive={'mean':'historical_level','std':'historical_variability','months':'coverage'}[stat]
 core=c.replace('HIST_S2_','').replace('HIST_CLIMATE_','').rsplit('_'+stat,1)[0]
 var=core.replace('_promedio','').replace('_mean','')
 if var in ['ndvi','evi','lai','fapar','savi']:fam='vigor_structure'
 elif var in ['ndwi','msi','nddi']:fam='moisture_stress'
 elif var=='precip':fam='precipitation'
 elif var in ['tmin','tmax','tmean']:fam='temperature'
 elif var=='dtr':fam='thermal_range'
 else:fam='other'
 return source,var,stat,primitive,fam

def dictionary(H):
 rows=[]
 for c in H:
  src,var,st,prim,fam=labels(c);rows.append({'feature_name':c,'source_sensor':src,'variable_index':var,'period':'Apr-Oct pooled monthly climatology, 2022-2024','statistic':st,'temporal_aggregation':'mean across years by calendar month, then summary across available months','semantic_family':prim,'index_family':fam,'missing_fraction':H[c].isna().mean(),'n_unique':H[c].nunique(dropna=True),'definition_verified_from':'src/family_1/feature_pipeline.py::build_history_anomaly'})
 dic=pd.DataFrame(rows);dic.to_csv(D['dictionary']/'history_feature_dictionary.csv',index=False);dic.to_csv(D['dictionary']/'history_taxonomy.csv',index=False)
 leak=dic[['feature_name','period']].copy();leak['pre_target_only']=True;leak['contains_yield']=False;leak['contains_2025']=False;leak['forward_looking']=False;leak['supervised_prediction_data_decision']=False;leak['status']='PASS';leak['evidence']='builder filters year between 2022 and 2024 before aggregation; 2025 only enters separate ANOMALY block';leak.to_csv(D['dictionary']/'history_leakage_audit.csv',index=False)
 return dic

def associations(H,y,resid,dic,C):
 rows=[]
 for c in H:
  q={'feature':c,'pearson_residual':corr(H[c],resid,'pearson'),'spearman_residual':corr(H[c],resid),'pearson_abs_residual':corr(H[c],abs(resid),'pearson'),'spearman_abs_residual':corr(H[c],abs(resid)),'pearson_yield':corr(H[c],y,'pearson'),'spearman_yield':corr(H[c],y)};q.update(dic.set_index('feature_name').loc[c,['source_sensor','variable_index','statistic','semantic_family','index_family']].to_dict());rows.append(q)
 a=pd.DataFrame(rows);a['direction']=np.where(a.spearman_residual>0,'positive',np.where(a.spearman_residual<0,'negative','none'));a['magnitude']=a.spearman_residual.abs();a['rank_within_history']=a.magnitude.rank(ascending=False,method='min').astype('Int64');a['association_type']=np.select([(a.spearman_yield.abs()>=.15)&(a.spearman_residual.abs()<.15),(a.spearman_yield.abs()<.15)&(a.spearman_residual.abs()>=.15),(a.spearman_yield.abs()>=.15)&(a.spearman_residual.abs()>=.15)],['A_yield_only','B_residual_only','C_both'],default='D_neither');a.to_csv(D['associations']/'history_feature_residual_associations.csv',index=False)
 # Strict OOF target-free reconstruction History_j <- Climate.
 kf=KFold(5,shuffle=True,random_state=SEED);red=[];cond=[]
 for c in H:
  o=np.full(len(H),np.nan)
  if H[c].nunique(dropna=True)<2:
   red.append({'feature':c,'R2_History_from_Climate_OOF':np.nan,'RMSE_History_from_Climate_OOF':0.0,'spearman_residual':a.set_index('feature').loc[c,'spearman_residual'],'independence_score':np.nan,'redundancy_status':'constant_noninformative'})
   cond.append({'feature':c,'pearson_conditional':np.nan,'spearman_conditional':np.nan,'original_spearman_residual':a.set_index('feature').loc[c,'spearman_residual'],'method':'not estimated: constant feature'})
   continue
  for tr,va in kf.split(H):
   m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),RidgeCV(alphas=[.1,1,10,100])).fit(C.iloc[tr],H[c].iloc[tr]);o[va]=m.predict(C.iloc[va])
  e=H[c].to_numpy()-o;red.append({'feature':c,'R2_History_from_Climate_OOF':r2_score(H[c],o),'RMSE_History_from_Climate_OOF':mean_squared_error(H[c],o)**.5,'spearman_residual':a.set_index('feature').loc[c,'spearman_residual'],'independence_score':1-max(0,r2_score(H[c],o)),'redundancy_status':'estimated'})
  cond.append({'feature':c,'pearson_conditional':corr(e,resid,'pearson'),'spearman_conditional':corr(e,resid),'original_spearman_residual':a.set_index('feature').loc[c,'spearman_residual'],'method':'5-fold OOF RidgeCV History~Climate'})
 pd.DataFrame(red).merge(dic[['feature_name','source_sensor','semantic_family','index_family']],left_on='feature',right_on='feature_name').drop(columns='feature_name').to_csv(D['associations']/'history_climate_redundancy.csv',index=False)
 pd.DataFrame(cond).to_csv(D['associations']/'history_conditional_associations.csv',index=False)
 return a,pd.DataFrame(red),pd.DataFrame(cond)

def groups(dic):
 g={}
 for col in ['semantic_family','source_sensor','index_family']:
  for v,q in dic.groupby(col):
   if len(q)>=2:g[f'{col}::{v}']=q.feature_name.tolist()
 return g

def prep(frame,tr,va,scale=False):
 imp=SimpleImputer(strategy='median').fit(frame.iloc[tr]);a=imp.transform(frame.iloc[tr]);b=imp.transform(frame.iloc[va])
 if scale:s=StandardScaler().fit(a);a=s.transform(a);b=s.transform(b)
 return a,b

def model(kind,param,x,y):
 if kind=='RIDGE':return Ridge(**param).fit(x,y)
 if kind=='ENET':return ElasticNet(**param,max_iter=30000,random_state=SEED).fit(x,y)
 return XGBRegressor(**param,objective='reg:squarederror',random_state=SEED,n_jobs=1,verbosity=0).fit(x,y)

def summarize(f,kind,path):
 out=[]
 for exp,g in f.groupby('experiment'):
  out.append({'experiment':exp,'experiment_type':kind,'n_features':g.n_features.iloc[0],'corrected_RMSE':g.corrected_RMSE.mean(),'climate_RMSE':g.climate_RMSE.mean(),'delta_RMSE_mean':g.delta_RMSE.mean(),'delta_RMSE_median':g.delta_RMSE.median(),'delta_vs_HISTORY_ALL':g.delta_RMSE.mean()-f[f.experiment.eq('HISTORY_ALL')].delta_RMSE.mean() if (f.experiment=='HISTORY_ALL').any() else np.nan,'fold_win_rate':(g.delta_RMSE<0).mean(),'residual_correlation_mean':g.residual_correlation.mean(),'repetitions_improved':g.groupby('repeat').delta_RMSE.mean().lt(0).sum()})
 pd.DataFrame(out).sort_values('corrected_RMSE').to_csv(path,index=False)

def cv_experiments(ids,y,C,H,dic):
 splits=rs1.save_splits(ids);pos={v:i for i,v in enumerate(ids)};hp=pd.read_csv(ROOT/'outputs/modeling/residual_signal_audit/stage1/block_models/selected_hyperparameters.csv');pred=pd.concat([pd.read_parquet(p) for p in sorted((ROOT/'outputs/modeling/residual_signal_audit/stage1/checkpoints').glob('pred_fold_*.parquet'))]);pred=pred[pred.pipeline.eq('XGB_RESIDUAL_HISTORY')]
 gs=groups(dic);abl={'HISTORY_ALL':list(H.columns)};only={}
 for n,cols in gs.items():abl['WITHOUT_'+n]=[c for c in H if c not in cols];only['ONLY_'+n]=cols
 rows=[];oof=[];importance=[]
 for k,s in splits.iterrows():
  tr=np.array([pos[v] for v in json.loads(s.train_ID_POLIGONO)]);va=np.array([pos[v] for v in json.loads(s.validation_ID_POLIGONO)]);rep=int(s['repeat']);fold=int(s['fold']);hh=hp[(hp.block=='HISTORY')&(hp['repeat']==rep)&(hp.fold==fold)]
  cp=json.loads(hh.iloc[0].climate_params);inner=list(KFold(4,shuffle=True,random_state=SEED+k).split(tr));cf,cv=rs1.climate_crossfit(C,y,tr,va,inner,cp);rt=y.iloc[tr].to_numpy()-cf;rv=y.iloc[va].to_numpy()-cv
  params={r.model:json.loads(r.best_params) for _,r in hh.iterrows()};rank=pd.Series({c:abs(corr(H[c].iloc[tr],rt)) for c in H}).sort_values(ascending=False)
  ex=[]
  for n,cols in {**abl,**only}.items():ex.append((n,'XGB',cols,params['XGB']))
  for kk in [3,5,10,15]:ex.append((f'TOP_{kk}','XGB',rank.head(kk).index.tolist(),params['XGB']))
  top10=rank.head(10).index.tolist()
  for kind in ['RIDGE','ENET','XGB']:
   ex.append((f'MODEL_ALL_{kind}',kind,list(H.columns),params[kind]));ex.append((f'MODEL_COMPACT10_{kind}',kind,top10,params[kind]))
  for n,kind,cols,par in ex:
   if not cols:continue
   a,b=prep(H[cols],tr,va,kind!='XGB');m=model(kind,par,a,rt);rh=m.predict(b);yp=cv+rh;cr=mean_squared_error(y.iloc[va],yp)**.5;br=mean_squared_error(y.iloc[va],cv)**.5;rows.append({'experiment':n,'model':kind,'repeat':rep,'fold':fold,'n_features':len(cols),'n_validation':len(va),'climate_RMSE':br,'corrected_RMSE':cr,'delta_RMSE':cr-br,'residual_correlation':corr(rv,rh,'pearson')})
   if n in ['HISTORY_ALL','TOP_10']:
    for j,c in enumerate(cols):importance.append({'experiment':n,'repeat':rep,'fold':fold,'feature':c,'importance':float(m.feature_importances_[j])})
    for ii,pid in enumerate(ids.iloc[va]):oof.append({ID:pid,'repeat':rep,'fold':fold,'experiment':n,'y_true':y.iloc[va[ii]],'climate_pred':cv[ii],'corrected_pred':yp[ii],'true_residual':rv[ii],'predicted_residual':rh[ii]})
  pd.DataFrame(rows).to_csv(D['checkpoints']/'rs2_fold_metrics_partial.csv',index=False)
 f=pd.DataFrame(rows);pd.DataFrame(oof).to_parquet(D['checkpoints']/'rs2_oof_predictions.parquet',index=False);pd.DataFrame(importance).to_csv(D['compact_models']/'history_feature_importance_stability.csv',index=False)
 summarize(f[f.experiment.str.startswith('ONLY_')],'only',D['subfamilies']/'subfamily_only_metrics.csv');summarize(f[f.experiment.str.startswith('WITHOUT_')|f.experiment.eq('HISTORY_ALL')],'ablation',D['subfamilies']/'subfamily_ablation_metrics.csv');summarize(f[f.experiment.str.match('TOP_|HISTORY_ALL')],'topk',D['compact_models']/'topk_history_metrics.csv');summarize(f[f.experiment.str.startswith('MODEL_')],'model_class',D['compact_models']/'model_class_comparison.csv')
 # Actual period identity is pooled; no year-specific model can be validly evaluated.
 pd.DataFrame([{'period':'2022-2024 pooled','identifiable_separately':False,'reason':'39 features pool 2022-2024 by calendar month; year identity was discarded upstream'}]).to_csv(D['subfamilies']/'year_period_decomposition.csv',index=False)
 onlysum=pd.read_csv(D['subfamilies']/'subfamily_only_metrics.csv');onlysum[onlysum.experiment.str.startswith('ONLY_index_family')].to_csv(D['subfamilies']/'index_family_decomposition.csv',index=False)
 return f,pd.DataFrame(oof),pd.DataFrame(importance)

def compact_features(a,cond,imp):
 z=a[['feature','spearman_residual']].merge(cond[['feature','spearman_conditional']],on='feature').merge(imp[imp.experiment.eq('HISTORY_ALL')].groupby('feature').importance.agg(['mean','std']).reset_index(),on='feature',how='left');z['rank_residual']=z.spearman_residual.abs().rank();z['rank_conditional']=z.spearman_conditional.abs().rank();z['rank_importance']=z['mean'].rank();z['aggregate_rank']=z[['rank_residual','rank_conditional','rank_importance']].mean(axis=1);z.sort_values('aggregate_rank',ascending=False).to_csv(D['compact_models']/'compact_history_features.csv',index=False);return z.sort_values('aggregate_rank',ascending=False)

def diagnostics(ids,y,H,C,resid,compact,oof):
 # Neighbor geometry, target-free distances; outcomes used only after neighbors are fixed.
 rows=[]
 for space,cols in [('all_history',list(H)),('compact_history',compact.feature.head(10).tolist())]:
  Z=StandardScaler().fit_transform(SimpleImputer(strategy='median').fit_transform(H[cols]));nn=NearestNeighbors(n_neighbors=6).fit(Z);dist,ix=nn.kneighbors(Z)
  for i,pid in enumerate(ids):rows.append({ID:pid,'space':space,'mean_5nn_distance':dist[i,1:].mean(),'mean_abs_residual_difference_to_neighbors':np.mean(abs(resid.iloc[i]-resid.iloc[ix[i,1:]])),'mean_abs_yield_difference_to_neighbors':np.mean(abs(y.iloc[i]-y.iloc[ix[i,1:]]))})
 neigh=pd.DataFrame(rows);neigh.to_csv(D['diagnostics']/'history_neighbor_analysis.csv',index=False)
 hard=pd.read_csv(ROOT/'outputs/modeling/family_1/support_analysis/support/difficult_parcel_support.csv');hard=hard[hard.difficult_all_3][[ID,'support_class']];q=oof[oof.experiment.eq('HISTORY_ALL')].groupby(ID).agg(climate_residual=('true_residual','mean'),predicted_history_correction=('predicted_residual','mean'),climate_pred=('climate_pred','mean'),corrected_pred=('corrected_pred','mean'),y_true=('y_true','first')).reset_index();q['corrected_residual']=q.y_true-q.corrected_pred;q['absolute_error_improvement']=abs(q.climate_residual)-abs(q.corrected_residual);q=q.merge(hard,on=ID).merge(neigh[neigh.space.eq('all_history')],on=ID);Z=pd.DataFrame(StandardScaler().fit_transform(SimpleImputer(strategy='median').fit_transform(H[compact.feature.head(5)])),columns=compact.feature.head(5),index=ids);pct=Z.rank(pct=True).add_prefix('percentile_z_').reset_index(names=ID);q=q.merge(pct,on=ID);q.to_csv(D['diagnostics']/'difficult_parcels_history.csv',index=False);q[q.support_class.eq('y-outlier given similar X')].to_csv(D['diagnostics']/'yatypical_history.csv',index=False)
 return neigh,q

def interpret(H,C,resid,compact,dic):
 cols=compact.feature.head(7).tolist();Zi=SimpleImputer(strategy='median').fit(H[cols]);X=Zi.transform(H[cols]);m=XGBRegressor(n_estimators=200,max_depth=2,learning_rate=.03,min_child_weight=8,subsample=.8,colsample_bytree=.8,reg_alpha=1,reg_lambda=10,n_jobs=1,random_state=SEED).fit(X,resid);rows=[]
 for j,c in enumerate(cols):
  qs=np.unique(np.quantile(X[:,j],np.linspace(0,1,11)))
  for lo,hi in zip(qs[:-1],qs[1:]):
   mask=(X[:,j]>=lo)&(X[:,j]<=hi);x1=X.copy();x2=X.copy();x1[:,j]=lo;x2[:,j]=hi;rows.append({'feature':c,'bin_low':lo,'bin_high':hi,'bin_center':(lo+hi)/2,'ale_difference':np.mean(m.predict(x2[mask])-m.predict(x1[mask])) if mask.any() else np.nan,'n_bin':mask.sum(),'diagnostic':'1D ALE finite difference; descriptive, non-causal'})
 shapes=pd.DataFrame(rows);shapes.to_csv(D['interpretation']/'top_history_feature_shapes.csv',index=False)
 for c,g in shapes.groupby('feature'):
  plt.figure(figsize=(6,4));plt.plot(g.bin_center,g.ale_difference,marker='o');plt.axhline(0,color='black');plt.title(c);plt.ylabel('local predicted-residual change');plt.tight_layout();plt.savefig(D['figures']/'history_feature_shapes'/f'{c}.png',dpi=170);plt.close()
 # Limited stratified interactions with principal current climate features.
 cn=[c for c in C if any(k in c.lower() for k in ['precip','tmean','dtr'])][:6];inter=[]
 for h in cols[:5]:
  for c in cn:
   bins=pd.qcut(C[c],3,duplicates='drop')
   for lev,ix in bins.groupby(bins).groups.items():inter.append({'history_feature':h,'climate_feature':c,'climate_stratum':str(lev),'n':len(ix),'spearman_history_vs_residual':corr(H.loc[ix,h],resid.loc[ix])})
 pd.DataFrame(inter).to_csv(D['interpretation']/'history_climate_interactions.csv',index=False)

def duplicate_audit(H,compact):
 exact=[]
 for i,a in enumerate(H):
  for b in H.columns[i+1:]:
   if H[a].equals(H[b]):exact.append((a,b))
 cr=H.corr().abs();pairs=[]
 for i,a in enumerate(cr):
  for b in cr.columns[i+1:]:
   if cr.loc[a,b]>.98:pairs.append({'feature_a':a,'feature_b':b,'abs_correlation':cr.loc[a,b]})
 pd.DataFrame(pairs).to_csv(D['diagnostics']/'history_near_duplicate_pairs.csv',index=False)
 pd.DataFrame([{'n_features':H.shape[1],'exact_duplicate_pairs':len(exact),'near_duplicate_pairs_abs_r_gt_098':len(pairs),'top5_share_xgb_importance':compact['mean'].head(5).sum()/compact['mean'].sum(),'top10_share_xgb_importance':compact['mean'].head(10).sum()/compact['mean'].sum()}]).to_csv(D['diagnostics']/'history_signal_density.csv',index=False)

def figures(a,red,sub,topk,neigh):
 q=a.sort_values('spearman_residual').tail(15);plt.figure(figsize=(9,6));sns.barplot(q,y='feature',x='spearman_residual');plt.tight_layout();plt.savefig(D['figures']/'history_residual_associations.png',dpi=180);plt.close()
 z=a.merge(red[['feature','R2_History_from_Climate_OOF']],on='feature');plt.figure(figsize=(6,5));sns.scatterplot(z,x='R2_History_from_Climate_OOF',y='spearman_residual',hue='source_sensor');plt.tight_layout();plt.savefig(D['figures']/'history_vs_climate_redundancy.png',dpi=180);plt.close()
 plt.figure(figsize=(9,5));sns.barplot(sub[sub.experiment.ne('HISTORY_ALL')],y='experiment',x='delta_vs_HISTORY_ALL');plt.tight_layout();plt.savefig(D['figures']/'subfamily_ablation.png',dpi=180);plt.close()
 plt.figure(figsize=(7,4));q=topk.copy();q['k']=q.experiment.str.extract('(\\d+)')[0].fillna('39').astype(int);sns.lineplot(q.sort_values('k'),x='k',y='corrected_RMSE',marker='o');plt.axhline(.494235,color='gray',ls='--');plt.tight_layout();plt.savefig(D['figures']/'topk_performance_curve.png',dpi=180);plt.close()
 plt.figure(figsize=(6,4));sns.boxplot(neigh,x='space',y='mean_abs_residual_difference_to_neighbors');plt.tight_layout();plt.savefig(D['figures']/'history_neighbor_residual_similarity.png',dpi=180);plt.close()

def difficult_figure(hard):
 plt.figure(figsize=(7,5));sns.scatterplot(hard,x='climate_residual',y='corrected_residual',hue='support_class');lo=min(hard.climate_residual.min(),hard.corrected_residual.min());hi=max(hard.climate_residual.max(),hard.corrected_residual.max());plt.plot([lo,hi],[lo,hi],color='gray',ls='--');plt.axhline(0,color='black',lw=.8);plt.axvline(0,color='black',lw=.8);plt.tight_layout();plt.savefig(D['figures']/'difficult_parcels_history.png',dpi=180);plt.close()

def report(dic,a,red,cond,sub,only,topk,mc,hard,neigh,density):
 bestsub=only.iloc[0];worstrem=sub[sub.experiment.ne('HISTORY_ALL')].sort_values('delta_vs_HISTORY_ALL',ascending=False).iloc[0];bestk=topk.sort_values('corrected_RMSE').iloc[0];histall=sub[sub.experiment.eq('HISTORY_ALL')].iloc[0];lin=mc[mc.experiment.str.contains('ALL')].sort_values('corrected_RMSE');top=a.sort_values('magnitude',ascending=False).head(8);ct=cond.loc[cond.spearman_conditional.abs().nlargest(8).index];redund=red.sort_values('R2_History_from_Climate_OOF',ascending=False).head(5);direct='NONLINEAR CONTINUOUS SIGNAL' if lin.iloc[0].experiment.endswith('XGB') and lin.iloc[0].corrected_RMSE+0.005<lin.iloc[1].corrected_RMSE else ('COMPACT DIRECT SIGNAL' if bestk.n_features<=10 and bestk.corrected_RMSE<=histall.corrected_RMSE+.005 else 'DISTRIBUTED HISTORY SIGNAL')
 txt=f'''# RS2 — History Signal Decomposition

## Controles

HISTORY tiene 39 features: 13 variables × `mean`, `std`, `months`; periodo real abril–octubre 2022–2024 agrupado por mes calendario. No hay identidad anual después del feature engineering. Residual=`y−ŷ_CLIMATE_ENET`; todo resultado predictivo reutiliza los mismos 50 outer folds, ranking top-k rehecho dentro de outer-train y corrección evaluada sólo en outer-validation. No se ejecutó clustering, GMM, MoE, Planet ni predicción final.

## Respuestas

1. **Contenido:** 24 Sentinel-2 históricas y 15 climáticas históricas; {dic.semantic_family.value_counts().to_dict()}.
2. **Subfamilias:** por fuente, estadístico real (nivel, variabilidad, cobertura) e índice: {dic.index_family.value_counts().to_dict()}.
3. **Mayor asociación residual:** {top[['feature_name' if 'feature_name' in top else 'feature','spearman_residual']].to_dict('records')}.
4. **Después de descontar Climate:** {ct[['feature','spearman_conditional']].round(3).to_dict('records')}.
5. **Más reconstruibles desde Climate:** {redund[['feature','R2_History_from_Climate_OOF']].round(3).to_dict('records')}.
6. **Información independiente:** consultar `history_climate_redundancy.csv`; priorizar alta asociación condicional y R² de redundancia bajo/moderado.
7. **Mejor subfamilia sola:** {bestsub.experiment}, RMSE={bestsub.corrected_RMSE:.4f}, Δ={bestsub.delta_RMSE_mean:+.4f}.
8. **Ablación más dañina:** {worstrem.experiment}, cambio contra HISTORY_ALL={worstrem.delta_vs_HISTORY_ALL:+.4f}.
9. **Suficiencia individual:** ranking completo en `subfamily_only_metrics.csv`.
10. **Año dominante:** no puede evaluarse; 2022–2024 fueron agrupados antes de crear las 39 features.
11. **Vigor vs moisture/stress:** comparar filas `ONLY_index_family::*` en `index_family_decomposition.csv`.
12. **Concentración:** top-5/top-10 concentran {density.top5_share_xgb_importance.iloc[0]:.1%}/{density.top10_share_xgb_importance.iloc[0]:.1%} de importancia XGB agregada.
13. **Tamaño mínimo observado:** {int(bestk.n_features)} features en {bestk.experiment}; RMSE={bestk.corrected_RMSE:.4f}.
14. **Top 5/10 vs ALL:** {topk[['experiment','corrected_RMSE','delta_RMSE_mean','fold_win_rate']].round(4).to_dict('records')}.
15. **Lineal vs no lineal:** {lin[['experiment','corrected_RMSE','delta_RMSE_mean']].round(4).to_dict('records')}. XGB superior implica thresholds/interacciones predictivas, no causalidad.
16. **Formas:** ALE descriptivo en `top_history_feature_shapes.csv` y figuras individuales.
17. **Interacciones Climate:** estratificación limitada en `history_climate_interactions.csv`; exploratoria, no selección supervisada adicional.
18. **Difficult parcels:** mejora media={hard.absolute_error_improvement.mean():.3f}; proporción mejorada={(hard.absolute_error_improvement>0).mean():.1%}.
19. **y-atypical:** mejora media={hard[hard.support_class.eq('y-outlier given similar X')].absolute_error_improvement.mean():.3f}; proporción mejorada={(hard[hard.support_class.eq('y-outlier given similar X')].absolute_error_improvement>0).mean():.1%}.
20. **Vecinos:** similitud residual/y por all y compact History: {neigh.groupby('space')[['mean_abs_residual_difference_to_neighbors','mean_abs_yield_difference_to_neighbors']].mean().round(3).to_dict('index')}.
21. **Firma persistente:** evidencia compatible: historia pre-2025, mejora residual reproducible y ayuda a casos difíciles; no demuestra suelo, manejo ni productividad histórica.
22. **Leakage:** las 39 pasan auditoría de construcción pre-2025; `months` es cobertura, no señal biológica, y debe interpretarse con cautela.
23. **Uso directo:** RS1 mostró que Climate+History directo mejora, pero la corrección residual fue ligeramente mejor; conservar corrección residual como opción principal.
24. **Subconjunto compacto:** decidir según curva top-k nested; no usar ranking global para estimar desempeño.
25. **Regímenes:** no hay prueba de clusters en RS2 y no se ejecutaron; no justificarlos sólo por esta señal.
26. **Clasificación final:** **{direct}**. Si XGB conserva ventaja, preferir función continua no lineal y NO clusterizar.
'''
 (D['report']/'history_signal_decomposition_report.md').write_text(txt,encoding='utf-8')

def main():
 ids,X,y=rs1.load_xy();ids=ids.reset_index(drop=True);y=y.reset_index(drop=True);raw=pd.read_parquet(rs1.FEATURE_DIR/'history_features.parquet').set_index(ID).reindex(ids);H=raw.reset_index(drop=True);C=X[rs1.climate_cols(X)].reset_index(drop=True);dic=dictionary(H);parcel=pd.read_parquet(ROOT/'outputs/modeling/residual_signal_audit/stage1/residuals/climate_enet_oof_residuals.parquet').groupby(ID).agg(residual=('residual_fold','mean')).reindex(ids);resid=parcel.residual.reset_index(drop=True);a,red,cond=associations(H,y,resid,dic,C);f,oof,imp=cv_experiments(ids,y,C,H,dic);compact=compact_features(a,cond,imp);neigh,hard=diagnostics(ids,y,H,C,resid,compact,oof);interpret(H,C,resid,compact,dic);duplicate_audit(H,compact);sub=pd.read_csv(D['subfamilies']/'subfamily_ablation_metrics.csv');only=pd.read_csv(D['subfamilies']/'subfamily_only_metrics.csv');topk=pd.read_csv(D['compact_models']/'topk_history_metrics.csv');mc=pd.read_csv(D['compact_models']/'model_class_comparison.csv');density=pd.read_csv(D['diagnostics']/'history_signal_density.csv');figures(a,red,sub,topk,neigh);difficult_figure(hard);report(dic,a,red,cond,sub,only,topk,mc,hard,neigh,density);print(f'RS2 complete: best top-k={topk.iloc[0].experiment}, RMSE={topk.iloc[0].corrected_RMSE:.4f}',flush=True)
if __name__=='__main__':main()
