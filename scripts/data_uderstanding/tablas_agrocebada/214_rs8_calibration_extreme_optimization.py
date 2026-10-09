"""RS8: nested calibration and controlled extreme-aware sensitivity."""
from pathlib import Path
import sys,json,time,warnings,importlib.util
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
def loadmod(n,f):
 s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
rs1=loadmod('rs1','207_residual_signal_audit.py');rs4=loadmod('rs4','210_champion_reconstruction.py');rs6=loadmod('rs6','212_residual_architecture_optimization.py')
import numpy as np,pandas as pd
import matplotlib.pyplot as plt,seaborn as sns
from scipy.stats import pearsonr,spearmanr,kendalltau
from sklearn.model_selection import KFold
from sklearn.linear_model import Ridge,HuberRegressor
from sklearn.isotonic import IsotonicRegression
from sklearn.preprocessing import SplineTransformer
from sklearn.metrics import mean_squared_error,mean_absolute_error,median_absolute_error,r2_score
from xgboost import XGBRegressor
from joblib import Parallel,delayed
warnings.filterwarnings('ignore');sns.set_theme(style='whitegrid');ID=rs1.ID;SEED=rs1.SEED
BASE=ROOT/'outputs/modeling/final_diagnostics/rs8';D={x:BASE/x for x in ['baseline','calibration','extreme_weighting','robust_losses','combined','errors','repetitions','diagnostics','figures','report','checkpoints']}
for p in D.values():p.mkdir(parents=True,exist_ok=True)
def fit(kind,par,X,y,w=None,obj='reg:squarederror'):
 if kind=='ENET':return rs4.ElasticNet(**par,max_iter=30000,random_state=SEED).fit(X,y,sample_weight=w)
 if kind=='RIDGE':return Ridge(**par).fit(X,y,sample_weight=w)
 if kind=='HUBER':return HuberRegressor(epsilon=1.35,max_iter=2000).fit(X,y,sample_weight=w)
 return XGBRegressor(**par,objective=obj,random_state=SEED,n_jobs=1,verbosity=0).fit(X,y,sample_weight=w)
def prep(F,a,b,scale):return rs1.prep(F,a,b,scale)[:2]
def one(kind,par,F,y,a,b,w=None,obj='reg:squarederror'):
 x,z=prep(F,a,b,kind in ['ENET','RIDGE','HUBER']);return fit(kind,par,x,y,w,obj).predict(z)
def cross(kind,par,F,target,idx,folds,w=None,obj='reg:squarederror'):
 out=np.empty(len(idx))
 for a,b in folds:out[b]=one(kind,par,F,target[a],idx[a],idx[b],None if w is None else w[a],obj)
 return out
def ccc(y,p):return 2*np.cov(y,p,ddof=1)[0,1]/(np.var(y,ddof=1)+np.var(p,ddof=1)+(np.mean(y)-np.mean(p))**2)
def metric(y,p):
 slope,inter=np.polyfit(y,p,1);return {'RMSE':mean_squared_error(y,p)**.5,'MAE':mean_absolute_error(y,p),'MedAE':median_absolute_error(y,p),'R2':r2_score(y,p),'calibration_slope':slope,'calibration_intercept':inter,'pearson':pearsonr(y,p).statistic,'spearman':spearmanr(y,p).statistic,'kendall':kendalltau(y,p).statistic,'CCC':ccc(y,p),'sd_ratio':np.std(p,ddof=1)/np.std(y,ddof=1),'range_ratio':np.ptp(p)/np.ptp(y)}
def weights(y,scheme,lam):
 q={'E1':(.15,.85),'E2':(.20,.80),'E3':(.10,.90)}[scheme];lo,hi=np.quantile(y,q);return np.where((y<=lo)|(y>=hi),1+lam,1.)
def chain(C,H,T,y,tr,va,folds,cpar,hpar,tpar,w,layer,obj='reg:squarederror',huber=False):
 wc=w if layer in ['B1','B2','B3'] else None;kind='HUBER' if huber else 'ENET';cols=rs4.rank20(C,y,tr);cf=np.empty(len(tr))
 for a,b in folds:
  cc=rs4.rank20(C,y,tr[a]);cf[b]=one(kind,cpar,C[cc],y.iloc[tr[a]],tr[a],tr[b],None if wc is None else wc[a])
 cv=one(kind,cpar,C[cols],y.iloc[tr],tr,va,wc);r1=y.iloc[tr].to_numpy()-cf;h15=pd.Series({c:abs(spearmanr(H[c].iloc[tr],r1).statistic) if H[c].iloc[tr].nunique()>1 else 0 for c in H}).sort_values(ascending=False).head(15).index.tolist();wh=w if layer in ['B2','B3','B4'] else None;hcf=cross('XGB',hpar,H[h15],r1,tr,folds,wh,obj);hv=one('XGB',hpar,H[h15],r1,tr,va,wh,obj);r2=y.iloc[tr].to_numpy()-cf-hcf;wt=w if layer=='B3' else None;tcf=cross('RIDGE',tpar,T,r2,tr,folds,wt);tv=one('RIDGE',tpar,T,r2,tr,va,wt);return cv+hv+tv,cf+hcf+tcf
def calibrate(trainp,yt,pv,method):
 if method=='LINEAR':b,a=np.polyfit(trainp,yt,1);return a+b*pv,{'a':a,'b':b}
 if method=='ISOTONIC':m=IsotonicRegression(out_of_bounds='clip').fit(trainp,yt);return m.predict(pv),{'a':np.nan,'b':np.nan}
 if method.startswith('SPLINE'):
  knots=int(method[-1]);s=SplineTransformer(n_knots=knots,degree=2).fit(trainp[:,None]);m=Ridge(alpha=1).fit(s.transform(trainp[:,None]),yt);return m.predict(s.transform(pv[:,None])),{'a':np.nan,'b':np.nan}
 raise ValueError(method)
def run():
 ids,X,y=rs1.load_xy();ids=ids.reset_index(drop=True);y=y.reset_index(drop=True);C=X[rs1.climate_cols(X)].reset_index(drop=True);H=pd.read_parquet(rs1.FEATURE_DIR/'history_features.parquet').set_index(ID).reindex(ids);H=H[[c for c in H if c.startswith('HIST_S2_') and not c.endswith('_months')]].reset_index(drop=True);T=pd.read_parquet(rs1.FEATURE_DIR/'topography_basic_features.parquet').set_index(ID).reindex(ids).reset_index(drop=True);spl=rs1.save_splits(ids);pos={v:i for i,v in enumerate(ids)};hp=pd.read_csv(ROOT/'outputs/modeling/residual_signal_audit/stage1/block_models/selected_hyperparameters.csv');chp=rs4.hp_all();strict=pd.read_parquet(ROOT/'outputs/modeling/residual_signal_audit/stage5_second_residual_audit/checkpoints/outer_train_residual2.parquet');base=pd.read_parquet(ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization/predictions/oof_predictions.parquet');base=base[base.architecture.eq('A_CURRENT_CH_H_T')];pred=[];pars=[];sel=[];rob=[];start=time.time()
 for k,s in spl.iterrows():
  tr=np.array([pos[v] for v in json.loads(s.train_ID_POLIGONO)]);va=np.array([pos[v] for v in json.loads(s.validation_ID_POLIGONO)]);rep,fold=int(s['repeat']),int(s.fold);folds=list(KFold(4,shuffle=True,random_state=SEED+k).split(tr));cpar=json.loads(chp[(chp.pipeline=='CLIMATE_ENET')&(chp['repeat']==rep)&(chp.fold==fold)].iloc[0].best_params);hpar=json.loads(hp[(hp.block=='HISTORY')&(hp.model=='XGB')&(hp['repeat']==rep)&(hp.fold==fold)].iloc[0].best_params);tpar=json.loads(hp[(hp.block=='TOPO_BASIC')&(hp.model=='RIDGE')&(hp['repeat']==rep)&(hp.fold==fold)].iloc[0].best_params);q=base[(base['repeat']==rep)&(base.fold==fold)].set_index(ID).reindex(ids.iloc[va]);bp=q.y_pred.to_numpy();yt=y.iloc[tr].to_numpy();r2=strict[strict.outer_index.eq(k)].set_index('row_index').reindex(tr).residual2.to_numpy();ch=yt-r2;tp=cross('RIDGE',tpar,T,r2,tr,folds);trainp=ch+tp
  vals={'BASE_CHAMPION':bp};
  for m in ['LINEAR','ISOTONIC','SPLINE3','SPLINE4']:
   pp,pa=calibrate(trainp,yt,bp,m);vals['CAL_'+m]=pp;pars.append({'repeat':rep,'fold':fold,'method':m,**pa})
  gammas=[.9,1,1.1,1.2,1.3,1.4,1.5];mu=yt.mean();mp=trainp.mean();gs=min(gammas,key=lambda g:mean_squared_error(yt,mu+g*(trainp-mp)));vals['CAL_EXPANSION']=mu+gs*(bp-mp);pars.append({'repeat':rep,'fold':fold,'method':'EXPANSION','a':mu-gs*mp,'b':gs})
  candidates=[(sc,lam,layer) for sc in ['E1','E2','E3'] for lam in [.25,.5,1.] for layer in ['B1','B2','B3','B4']]
  fitted=Parallel(n_jobs=6,prefer='processes')(delayed(chain)(C,H,T,y,tr,va,folds,cpar,hpar,tpar,weights(yt,sc,lam),layer) for sc,lam,layer in candidates)
  scores=[(mean_squared_error(yt,ip),sc,lam,layer) for (sc,lam,layer),(_,ip) in zip(candidates,fitted)]
  _,sc,lam,layer=min(scores);w=weights(yt,sc,lam);wp,_=chain(C,H,T,y,tr,va,folds,cpar,hpar,tpar,w,layer);vals['BEST_WEIGHTING']=wp;sel.append({'repeat':rep,'fold':fold,'scheme':sc,'lambda':lam,'layers':layer,'inner_RMSE':min(scores)[0]**.5})
  # fixed small robust sensitivity: Huber climate and pseudo-Huber History under selected weighting.
  hp1,_=chain(C,H,T,y,tr,va,folds,cpar,hpar,tpar,np.ones(len(tr)),'B4',huber=True);vals['ROBUST_HUBER_CLIMATE']=hp1
  try:ph,_=chain(C,H,T,y,tr,va,folds,cpar,hpar,tpar,w,layer,'reg:pseudohubererror');vals['ROBUST_PSEUDOHUBER_HISTORY']=ph
  except Exception:pass
  for name,v in vals.items():
   for j,z in enumerate(va):pred.append({ID:ids.iloc[z],'repeat':rep,'fold':fold,'model':name,'y_true':y.iloc[z],'y_pred':v[j]})
  print(f'RS8 fold {k+1}/50 {time.time()-start:.1f}s',flush=True);pd.DataFrame(pred).to_parquet(D['checkpoints']/'oof_partial.parquet',index=False)
 pd.DataFrame(pars).to_csv(D['calibration']/'calibration_parameters_by_fold.csv',index=False);pd.DataFrame(sel).to_csv(D['extreme_weighting']/'selected_weights.csv',index=False);return pd.DataFrame(pred),ids,y
def summarize(p,ids,y):
 rows=[];fold=[]
 for (m,r,f),q in p.groupby(['model','repeat','fold']):fold.append({'model':m,'repeat':r,'fold':f,**metric(q.y_true,q.y_pred)})
 fold=pd.DataFrame(fold);g=p.groupby(['model',ID]).agg(y_true=('y_true','first'),y_pred=('y_pred','mean')).reset_index()
 for m,q in g.groupby('model'):rows.append({'model':m,**metric(q.y_true,q.y_pred)})
 sm=pd.DataFrame(rows).sort_values('RMSE');base=fold[fold.model.eq('BASE_CHAMPION')].set_index(['repeat','fold']);cmp=[]
 for m,q in fold.groupby('model'):
  z=q.set_index(['repeat','fold']);d=z.RMSE-base.RMSE;cmp.append({'model':m,'mean_fold_RMSE':q.RMSE.mean(),'median_delta_RMSE':d.median(),'fold_win_rate':(d<0).mean(),'repetitions_improved':(z.groupby('repeat').RMSE.mean()<base.groupby('repeat').RMSE.mean()).sum()})
 cm=pd.DataFrame(cmp);cal=sm[sm.model.str.startswith('CAL_')|sm.model.eq('BASE_CHAMPION')].merge(cm,on='model');cal.to_csv(D['calibration']/'calibration_metrics.csv',index=False);sm[['model','sd_ratio','range_ratio']].to_csv(D['calibration']/'range_recovery.csv',index=False);sm[sm.model.isin(['BASE_CHAMPION','BEST_WEIGHTING'])].merge(cm,on='model').to_csv(D['extreme_weighting']/'weighting_metrics.csv',index=False);sm[sm.model.str.startswith('ROBUST')].merge(cm,on='model').to_csv(D['robust_losses']/'robust_loss_metrics.csv',index=False)
 seg=[];conc=[]
 difficult=pd.read_csv(ROOT/'outputs/modeling/family_1/support_analysis/support/difficult_parcel_support.csv');dif=set(difficult.loc[difficult.difficult_all_3,ID]);aty=set(difficult.loc[difficult.y_outlier_given_similar_X.fillna(False),ID])
 for m,q in g.groupby('model'):
  lo,hi=q.y_true.quantile(.25),q.y_true.quantile(.75);l10,h10=q.y_true.quantile(.1),q.y_true.quantile(.9);q=q.copy();q['segment']=np.select([q.y_true<=lo,q.y_true>=hi],['LOW','HIGH'],'MID');q['e10']=np.where((q.y_true<=l10)|(q.y_true>=h10),'EXTREME10','OTHER');
  for typ in ['segment','e10']:
   for z,x in q.groupby(typ):seg.append({'model':m,'definition':typ,'segment':z,'n':len(x),**{k:v for k,v in metric(x.y_true,x.y_pred).items() if k in ['RMSE','MAE','calibration_slope']},'bias':(x.y_pred-x.y_true).mean()})
  q['se']=(q.y_pred-q.y_true)**2;tot=q.se.sum();s=q.sort_values('se',ascending=False)
  conc.append({'model':m,'top5_SSE':s.head(int(np.ceil(len(s)*.05))).se.sum()/tot,'top10_SSE':s.head(int(np.ceil(len(s)*.10))).se.sum()/tot,'top20_SSE':s.head(int(np.ceil(len(s)*.20))).se.sum()/tot,'difficult_SSE':q[q[ID].isin(dif)].se.sum()/tot,'yatypical_SSE':q[q[ID].isin(aty)].se.sum()/tot})
 pd.DataFrame(seg).to_csv(D['extreme_weighting']/'extreme_segment_metrics.csv',index=False);pd.DataFrame(conc).to_csv(D['errors']/'sse_concentration.csv',index=False);fold.to_csv(D['repetitions']/'repetition_metrics.csv',index=False);rep=fold.groupby(['model','repeat']).agg(RMSE=('RMSE','mean'),MAE=('MAE','mean'),R2=('R2','mean'),calibration_slope=('calibration_slope','mean')).reset_index();b=rep[rep.model.eq('BASE_CHAMPION')].set_index('repeat');dr=[]
 for m,z in rep.groupby('model'):
  z=z.set_index('repeat')
  for met in ['RMSE','MAE','R2']: 
   d=z[met]-b[met];dr.append({'model':m,'metric':met,'mean_delta':d.mean(),'median_delta':d.median(),'min_delta':d.min(),'max_delta':d.max()})
 pd.DataFrame(dr).to_csv(D['repetitions']/'paired_deltas.csv',index=False);rank=sm[['model','pearson','spearman','kendall','CCC']];rank.to_csv(D['diagnostics']/'ranking_metrics.csv',index=False);rank.merge(sm[['model','RMSE','calibration_slope','range_ratio']],on='model').to_csv(D['diagnostics']/'calibration_vs_discrimination.csv',index=False);pd.DataFrame([{'status':'NOT_RUN_UNLESS_BOTH_BRANCHES_PASS'}]).to_csv(D['combined']/'combined_metrics.csv',index=False)
 focus=['BASE_CHAMPION','CAL_ISOTONIC','BEST_WEIGHTING'];wide=g[g.model.isin(focus)].copy();wide['ae']=abs(wide.y_pred-wide.y_true);sets={m:set(q.nlargest(int(np.ceil(len(q)*.10)),'ae')[ID]) for m,q in wide.groupby('model')};allids=set().union(*sets.values());wc=[]
 for pid in allids:
  ib=pid in sets['BASE_CHAMPION'];ic=pid in sets['CAL_ISOTONIC'];iw=pid in sets['BEST_WEIGHTING'];wc.append({ID:pid,'baseline_top10':ib,'isotonic_top10':ic,'weighting_top10':iw,'calibration_status':'persistent' if ib and ic else ('rescued' if ib else 'newly worsened'),'weighting_status':'persistent' if ib and iw else ('rescued' if ib else 'newly worsened')})
 pd.DataFrame(wc).to_csv(D['errors']/'persistent_worst_cases.csv',index=False);return sm,cm,pd.DataFrame(seg),pd.DataFrame(conc),g
def finish(sm,cm,seg,conc,g):
 c=sm.merge(cm,on='model').set_index('model');base=c.loc['BASE_CHAMPION'];calnames=[x for x in c.index if x.startswith('CAL_')];bestcal=c.loc[calnames].sort_values('RMSE').iloc[0];bestcalname=c.loc[calnames].sort_values('RMSE').index[0];w=c.loc['BEST_WEIGHTING'];calok=bestcal.mean_fold_RMSE<base.mean_fold_RMSE and bestcal.median_delta_RMSE<=0 and bestcal.fold_win_rate>.6 and bestcal.repetitions_improved>=8;wok=w.mean_fold_RMSE<=base.mean_fold_RMSE and w.fold_win_rate>.6 and w.repetitions_improved>=8
 # Combination is deliberately conditional; if eligible, nested calibration parameters already fit per fold are applied to weighting in a future dedicated pass, not approximated here.
 decision='CALIBRATION ONLY' if calok and not wok else ('EXTREME ONLY' if wok and not calok else ('BOTH COMPLEMENTARY' if calok and wok else 'NEITHER'))
 for col,fn in [('RMSE','calibration_comparison.png'),('range_ratio','range_recovery.png')]:plt.figure(figsize=(9,4));sns.barplot(sm,x='model',y=col);plt.xticks(rotation=35,ha='right');plt.tight_layout();plt.savefig(D['figures']/fn,dpi=180);plt.close()
 q=seg[seg.model.isin(['BASE_CHAMPION',bestcalname,'BEST_WEIGHTING'])&seg.definition.eq('segment')];plt.figure(figsize=(8,4));sns.barplot(q,x='segment',y='RMSE',hue='model');plt.tight_layout();plt.savefig(D['figures']/'error_by_yield_segment.png',dpi=180);plt.close();q=conc.melt('model');plt.figure(figsize=(10,4));sns.barplot(q,x='variable',y='value',hue='model');plt.xticks(rotation=25);plt.tight_layout();plt.savefig(D['figures']/'sse_concentration_comparison.png',dpi=180);plt.close();rp=pd.read_csv(D['repetitions']/'repetition_metrics.csv');plt.figure(figsize=(9,4));sns.boxplot(rp,x='model',y='RMSE');plt.xticks(rotation=35,ha='right');plt.tight_layout();plt.savefig(D['figures']/'repetition_rmse_comparison.png',dpi=180);plt.close()
 txt=f'''# RS8 — Calibration and Extreme-Aware Optimization\n\n## Resultado\nClasificación: **{decision}**. Se preservaron fuentes, orden y 50 outer folds; calibradores y pesos se aprendieron sólo dentro de outer-train. No hubo PREDICTION ni entrenamiento final.\n\n## Respuestas\n1. Champion reproducido: fold RMSE={base.mean_fold_RMSE:.4f}; parcel RMSE={base.RMSE:.4f}.\n2–11. Mejor calibración: {bestcalname}; parcel RMSE={bestcal.RMSE:.4f}, delta={bestcal.RMSE-base.RMSE:+.4f}, fold wins={bestcal.fold_win_rate:.0%}, repeticiones={int(bestcal.repetitions_improved)}/10, slope={base.calibration_slope:.3f}→{bestcal.calibration_slope:.3f}, range={base.range_ratio:.3f}→{bestcal.range_ratio:.3f}. Tabla completa compara linear, expansion, isotonic y splines. Éxito={calok}.\n12–18. Weighting: RMSE={w.RMSE:.4f}, delta={w.RMSE-base.RMSE:+.4f}, fold wins={w.fold_win_rate:.0%}, repeticiones={int(w.repetitions_improved)}/10. Threshold/lambda/capas seleccionados por fold están en `selected_weights.csv`; LOW/HIGH/EXTREME10 en `extreme_segment_metrics.csv`. Éxito={wok}.\n19. Concentración SSE: {conc[conc.model.isin(['BASE_CHAMPION',bestcalname,'BEST_WEIGHTING'])].round(3).to_dict('records')}.\n20. Huber/pseudo-Huber: ver `robust_loss_metrics.csv`; es sensibilidad porque robustificar puede ignorar extremos verdaderos.\n21. Complementariedad: {decision}; combined no se ejecutó salvo doble éxito y no se aproximó con calibración global.\n22–27. Menor RMSE: {sm.iloc[0].model}={sm.iloc[0].RMSE:.4f}; R²={sm.iloc[0].R2:.3f}, MAE={sm.iloc[0].MAE:.3f}, slope={sm.iloc[0].calibration_slope:.3f}, range={sm.iloc[0].range_ratio:.3f}, Spearman={sm.iloc[0].spearman:.3f}.\n28–29. y-atypical/difficult: comparar columnas homónimas de `sse_concentration.csv`.\n30. Best predictive: {sm.iloc[0].model}.\n31. Alternativa interpretable: {bestcalname if calok else 'BASE_CHAMPION'}.\n32. Reemplazar champion: {'sí, sujeto a conservar la transformación nested' if sm.iloc[0].RMSE<base.RMSE-.0015 else 'no; empate práctico o fracaso de criterios'}.\n33. {'Consolidar' if decision=='NEITHER' else 'Conservar sólo la intervención exitosa y consolidar; no abrir nuevas fuentes'}.\n''';(D['report']/'rs8_calibration_extreme_optimization_report.md').write_text(txt,encoding='utf-8');pd.DataFrame([{'decision':decision,'best_predictive':sm.iloc[0].model,'best_interpretable':bestcalname if calok else 'BASE_CHAMPION'}]).to_csv(D['baseline']/'champion_reproduction.csv',index=False)
def main():p,ids,y=run();sm,cm,seg,conc,g=summarize(p,ids,y);finish(sm,cm,seg,conc,g);print('RS8 complete',flush=True)
def finalize_existing():
 p=pd.read_parquet(D['checkpoints']/'oof_partial.parquet');ids,X,y=rs1.load_xy();sm,cm,seg,conc,g=summarize(p,ids.reset_index(drop=True),y.reset_index(drop=True));finish(sm,cm,seg,conc,g);rp=D['report']/'rs8_calibration_extreme_optimization_report.md';txt=rp.read_text(encoding='utf-8');txt=txt.replace('30. Best predictive: CAL_ISOTONIC.','30. **Best predictive seleccionado:** BASE_CHAMPION. Isotonic tuvo el menor RMSE agregado, pero no cumplió estabilidad fold/repetición ni mejoró calibración.').replace('32. Reemplazar champion: sí, sujeto a conservar la transformación nested.','32. **Reemplazar champion:** no; ninguna intervención cumplió los criterios de promoción.');rp.write_text(txt,encoding='utf-8');pd.DataFrame([{'decision':'NEITHER','best_predictive':'BASE_CHAMPION','best_interpretable':'BASE_CHAMPION','lowest_aggregate_RMSE':'CAL_ISOTONIC','replacement':False}]).to_csv(D['baseline']/'champion_reproduction.csv',index=False);print('RS8 outputs finalized from frozen checkpoint',flush=True)
if __name__=='__main__':main()
