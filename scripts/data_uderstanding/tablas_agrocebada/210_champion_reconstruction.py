"""RS4: reconstrucción leakage-safe de Climate refinado + Sentinel Historical."""
from pathlib import Path
import sys,json,importlib.util,warnings,time
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
spec=importlib.util.spec_from_file_location('rs1',Path(__file__).with_name('207_residual_signal_audit.py'));rs1=importlib.util.module_from_spec(spec);spec.loader.exec_module(rs1)
import numpy as np,pandas as pd
from scipy.stats import spearmanr
from sklearn.model_selection import KFold
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score,median_absolute_error
from xgboost import XGBRegressor
warnings.filterwarnings('ignore');ID=rs1.ID;SEED=rs1.SEED
BASE=ROOT/'outputs/modeling/residual_signal_audit/stage4_champion_reconstruction';D={x:BASE/x for x in ['metrics','predictions','residuals','diagnostics','models','sensitivity','report','checkpoints']}
for p in D.values():p.mkdir(parents=True,exist_ok=True)
BASELINES=['CLIMATE_ENET','PRECIPITATION_XGB','TOP20_ENET']
def hp_all():
 z=[]
 for p in sorted((ROOT/'outputs/modeling/family_2/stage3_round2_hybrid/checkpoints').glob('hp_fold_*.csv')):z.append(pd.read_csv(p))
 return pd.concat(z,ignore_index=True)
def prep(F,tr,va,scale):
 im=SimpleImputer(strategy='median').fit(F.iloc[tr]);a=im.transform(F.iloc[tr]);b=im.transform(F.iloc[va]);sc=None
 if scale:sc=StandardScaler().fit(a);a=sc.transform(a);b=sc.transform(b)
 return a,b
def fit(kind,par,x,y):
 if kind=='ENET':return ElasticNet(**par,max_iter=30000,random_state=SEED).fit(x,y)
 return XGBRegressor(**par,objective='reg:squarederror',random_state=SEED,n_jobs=1,verbosity=0).fit(x,y)
def rank20(C,y,idx,n=20):
 vals={c:abs(spearmanr(C[c].iloc[idx],y.iloc[idx]).statistic) if C[c].iloc[idx].nunique()>1 else 0 for c in C};return pd.Series(vals).sort_values(ascending=False).head(n).index.tolist()
def climate_outer(name,C,y,tr,va,inner,par):
 cf=np.empty(len(tr))
 if name=='PRECIPITATION_XGB':kind='XGB';outer_cols=[c for c in C if c.startswith('CLIMATE_precip_')]
 elif name=='CLIMATE_ENET':kind='ENET';outer_cols=list(C)
 else:kind='ENET';outer_cols=rank20(C,y,tr)
 for ia,ib in inner:
  atr=tr[ia];av=tr[ib];cols=rank20(C,y,atr) if name=='TOP20_ENET' else outer_cols;a,b=prep(C[cols],atr,av,kind=='ENET');cf[ib]=fit(kind,par,a,y.iloc[atr]).predict(b)
 a,b=prep(C[outer_cols],tr,va,kind=='ENET');m=fit(kind,par,a,y.iloc[tr]);return cf,m.predict(b),outer_cols,m
def residual_fit(H,yres,tr,va,cols,par):
 a,b=prep(H[cols],tr,va,False);m=fit('XGB',par,a,yres);return m.predict(b),m
def metric(y,p):return {'RMSE':mean_squared_error(y,p)**.5,'MAE':mean_absolute_error(y,p),'R2':r2_score(y,p),'MedAE':median_absolute_error(y,p)}
def run(ids,y,C,H):
 splits=rs1.save_splits(ids);pos={v:i for i,v in enumerate(ids)};chp=hp_all();rhp=pd.read_csv(ROOT/'outputs/modeling/residual_signal_audit/stage1/block_models/selected_hyperparameters.csv');rows=[];pred=[];hps=[];start=time.time()
 for k,s in splits.iterrows():
  tr=np.array([pos[v] for v in json.loads(s.train_ID_POLIGONO)]);va=np.array([pos[v] for v in json.loads(s.validation_ID_POLIGONO)]);rep=int(s['repeat']);fold=int(s['fold']);inner=list(KFold(4,shuffle=True,random_state=SEED+k).split(tr));hrow=rhp[(rhp.block=='HISTORY')&(rhp.model=='XGB')&(rhp['repeat']==rep)&(rhp.fold==fold)].iloc[0];hpar=json.loads(hrow.best_params)
  for base in BASELINES:
   pipe='CLIMATE_XGB' if base=='PRECIPITATION_XGB' else 'CLIMATE_ENET';par=json.loads(chp[(chp.pipeline==pipe)&(chp['repeat']==rep)&(chp.fold==fold)].iloc[0].best_params);cf,cv,ccols,cm=climate_outer(base,C,y,tr,va,inner,par);rtrain=y.iloc[tr].to_numpy()-cf;hall=list(H);rankh=pd.Series({c:abs(spearmanr(H[c].iloc[tr],rtrain).statistic) if H[c].iloc[tr].nunique()>1 else 0 for c in H}).sort_values(ascending=False);h15=rankh.head(15).index.tolist()
   rh,hm=residual_fit(H,rtrain,tr,va,hall,hpar);rh15,_=residual_fit(H,rtrain,tr,va,h15,hpar);hy=cv+rh;hy15=cv+rh15
   variants=[(base+'_BASE','climate',cv,0),(base+'_HISTORY24','residual24',hy,24),(base+'_HISTORY15','residual15',hy15,15)]
   # Direct augmentation only for the two refined baselines, matched model class.
   if base!='CLIMATE_ENET':
    F=pd.concat([C[ccols],H],axis=1);kind='XGB' if base=='PRECIPITATION_XGB' else 'ENET';a,b=prep(F,tr,va,kind=='ENET');ypd=fit(kind,par,a,y.iloc[tr]).predict(b);variants.append((base+'_DIRECT_HISTORY24','direct24',ypd,24))
   bm=metric(y.iloc[va],cv)
   for name,arch,yp,nh in variants:
    mm=metric(y.iloc[va],yp);rows.append({'pipeline':name,'baseline':base,'architecture':arch,'repeat':rep,'fold':fold,'n_validation':len(va),**mm,'baseline_RMSE':bm['RMSE'],'delta_RMSE':mm['RMSE']-bm['RMSE']})
    for i,pid in enumerate(ids.iloc[va]):pred.append({ID:pid,'pipeline':name,'baseline':base,'architecture':arch,'repeat':rep,'fold':fold,'y_true':y.iloc[va[i]],'y_pred':yp[i],'baseline_pred':cv[i],'residual_before':y.iloc[va[i]]-cv[i],'residual_after':y.iloc[va[i]]-yp[i],'predicted_history_residual':yp[i]-cv[i]})
   hps.append({'repeat':rep,'fold':fold,'baseline':base,'climate_params':json.dumps(par,sort_keys=True),'history_xgb_params':json.dumps(hpar,sort_keys=True),'climate_features':json.dumps(ccols),'history15_features':json.dumps(h15)})
  pd.DataFrame(rows).to_csv(D['checkpoints']/'fold_metrics_partial.csv',index=False);print(f'fold {k+1}/50 in {time.time()-start:.1f}s',flush=True)
 f=pd.DataFrame(rows);p=pd.DataFrame(pred);f.to_csv(D['metrics']/'fold_metrics.csv',index=False);p.to_parquet(D['predictions']/'oof_predictions.parquet',index=False);pd.DataFrame(hps).to_csv(D['models']/'selected_hyperparameters.csv',index=False);return f,p,pd.DataFrame(hps)
def summarize(f,p):
 out=[]
 for pipe,g in f.groupby('pipeline'):
  out.append({'pipeline':pipe,'baseline':g.baseline.iloc[0],'architecture':g.architecture.iloc[0],'RMSE':g.RMSE.mean(),'RMSE_median':g.RMSE.median(),'RMSE_std':g.RMSE.std(),'MAE':g.MAE.mean(),'R2':g.R2.mean(),'MedAE':g.MedAE.mean(),'mean_delta_RMSE':g.delta_RMSE.mean(),'median_delta_RMSE':g.delta_RMSE.median(),'delta_std':g.delta_RMSE.std(),'delta_q25':g.delta_RMSE.quantile(.25),'delta_q75':g.delta_RMSE.quantile(.75),'fold_win_rate':(g.delta_RMSE<0).mean(),'repetitions_improved':g.groupby('repeat').delta_RMSE.mean().lt(0).sum()})
 sm=pd.DataFrame(out).sort_values('RMSE');sm.to_csv(D['metrics']/'pipeline_metrics.csv',index=False);sm[sm.architecture.str.startswith('residual')].to_csv(D['metrics']/'paired_incremental_history.csv',index=False)
 by=p.groupby([ID,'pipeline','baseline','architecture']).agg(y_true=('y_true','first'),oof_prediction=('y_pred','mean'),oof_prediction_std=('y_pred','std'),baseline_prediction=('baseline_pred','mean'),residual_before=('residual_before','mean'),residual_after=('residual_after','mean'),predicted_history_residual=('predicted_history_residual','mean')).reset_index();by['absolute_error']=abs(by.y_true-by.oof_prediction);by.to_csv(D['predictions']/'oof_by_parcel.csv',index=False);p.to_parquet(D['residuals']/'residuals_before_after_history.parquet',index=False)
 # residual correlations between matched baselines, before and after history.
 rc=[]
 for arch in ['climate','residual24']:
  q=by[by.architecture.eq(arch)].pivot(index=ID,columns='baseline',values='residual_after' if arch=='residual24' else 'residual_before')
  for i,a in enumerate(BASELINES):
   for b in BASELINES[i+1:]:rc.append({'stage':arch,'baseline_a':a,'baseline_b':b,'residual_correlation':q[a].corr(q[b]),'residual_variance_a':q[a].var(),'residual_variance_b':q[b].var(),'mean_absolute_residual_a':q[a].abs().mean(),'mean_absolute_residual_b':q[b].abs().mean()})
 pd.DataFrame(rc).to_csv(D['residuals']/'residual_correlation_summary.csv',index=False);return sm,by
def diagnostics(sm,by):
 hard=pd.read_csv(ROOT/'outputs/modeling/family_1/support_analysis/support/difficult_parcel_support.csv');hard=hard[hard.difficult_all_3][[ID,'support_class']];q=by.merge(hard,on=ID);q.to_csv(D['diagnostics']/'difficult_parcels_champion.csv',index=False);q[q.support_class.eq('y-outlier given similar X')].to_csv(D['diagnostics']/'yatypical_champion.csv',index=False)
 seg=[];cal=[]
 for pipe,g in by.groupby('pipeline'):
  g=g.copy();g['segment']=pd.qcut(g.y_true,[0,.25,.75,1],labels=['LOW','MID','HIGH'])
  for z,x in g.groupby('segment',observed=True):seg.append({'pipeline':pipe,'segment':z,'n':len(x),'RMSE':mean_squared_error(x.y_true,x.oof_prediction)**.5,'MAE':mean_absolute_error(x.y_true,x.oof_prediction),'bias':(x.oof_prediction-x.y_true).mean()})
  beta,alpha=np.polyfit(g.y_true,g.oof_prediction,1);cal.append({'pipeline':pipe,'alpha':alpha,'beta':beta,'R2_calibration':r2_score(g.y_true,g.oof_prediction)})
 pd.DataFrame(seg).to_csv(D['diagnostics']/'yield_segment_performance.csv',index=False);pd.DataFrame(cal).to_csv(D['diagnostics']/'calibration_summary.csv',index=False)
 direct=sm[sm.architecture.isin(['residual24','direct24'])][['baseline','architecture','pipeline','RMSE','mean_delta_RMSE','fold_win_rate','repetitions_improved']];direct.to_csv(D['sensitivity']/'direct_vs_residual_augmentation.csv',index=False);hist=sm[sm.architecture.isin(['residual24','residual15'])][['baseline','architecture','pipeline','RMSE','mean_delta_RMSE','fold_win_rate','repetitions_improved']];hist.to_csv(D['sensitivity']/'history_24_vs_top15.csv',index=False)
 # Complexity uses fitted feature dimensions and tuned parameter counts.
 rows=[]
 for _,r in sm.iterrows():
  nc={'CLIMATE_ENET':48,'PRECIPITATION_XGB':10,'TOP20_ENET':20}[r.baseline];nh=16 if 'HISTORY24' in r.pipeline else (15 if 'HISTORY15' in r.pipeline else (16 if 'DIRECT' in r.pipeline else 0));kind='XGB' if r.baseline=='PRECIPITATION_XGB' else 'ENET';npar=8 if kind=='XGB' else 2;npar+=8 if r.architecture.startswith('residual') else 0;rows.append({'pipeline':r.pipeline,'climate_features':nc,'history_features':nh,'total_features':nc+nh,'tuned_hyperparameters_approx':npar,'training_cost_relative':'high' if r.architecture.startswith('residual') or r.baseline=='PRECIPITATION_XGB' else 'low'})
 pd.DataFrame(rows).to_csv(D['models']/'model_complexity.csv',index=False);return q
def report(sm,hard):
 get=lambda x:sm.set_index('pipeline').loc[x];a1=get('CLIMATE_ENET_HISTORY24');a2=get('PRECIPITATION_XGB_HISTORY24');a3=get('TOP20_ENET_HISTORY24');best=sm.iloc[0];compact=get('PRECIPITATION_XGB_HISTORY15');hs=hard.groupby('pipeline').absolute_error.mean();orig=abs(a1.mean_delta_RMSE);pv=hard.pivot(index=ID,columns='pipeline',values='absolute_error');hybrids=['CLIMATE_ENET_HISTORY24','PRECIPITATION_XGB_HISTORY24','TOP20_ENET_HISTORY24'];baseof={x:x.replace('_HISTORY24','_BASE') for x in hybrids};hard_gain={x:{'mean_MAE':round(hs[x],3),'proportion_improved':round((pv[x]<pv[baseof[x]]).mean(),3)} for x in hybrids};ya=hard[hard.support_class.eq('y-outlier given similar X')].pivot(index=ID,columns='pipeline',values='absolute_error');ya_gain={x:{'mean_MAE':round(ya[x].mean(),3),'proportion_improved':round((ya[x]<ya[baseof[x]]).mean(),3)} for x in hybrids};seg=pd.read_csv(D['diagnostics']/'yield_segment_performance.csv');cal=pd.read_csv(D['diagnostics']/'calibration_summary.csv').set_index('pipeline');direct=pd.read_csv(D['sensitivity']/'direct_vs_residual_augmentation.csv');hist=pd.read_csv(D['sensitivity']/'history_24_vs_top15.csv')
 txt=f'''# RS4 — Champion Reconstruction

## Controles
Mismos 50 outer folds (5×10) e inner CV 4-fold. Los targets residuales de outer-train se generaron con predicciones inner-OOF; TOP20 se re-rankeó dentro de cada inner-train. El bloque fuente Sentinel Historical tiene 24 columnas pre-2025; se excluyeron sus 8 `months` constantes, dejando 16 variables efectivas. No se usó Planet, Topography, clustering, MoE, RS5 ni predicción final.

## Respuestas
1. **Reproducción original:** CLIMATE_ENET+History24 RMSE={a1.RMSE:.4f}, frente a ~0.4941 esperado.
2. **Precipitation+History:** RMSE={a2.RMSE:.4f}; delta matched={a2.mean_delta_RMSE:+.4f}; wins={a2.fold_win_rate:.0%}; repeticiones={int(a2.repetitions_improved)}/10.
3. **TOP20+History:** RMSE={a3.RMSE:.4f}; delta matched={a3.mean_delta_RMSE:+.4f}; wins={a3.fold_win_rate:.0%}; repeticiones={int(a3.repetitions_improved)}/10.
4. **Mejor total:** {best.pipeline}, RMSE={best.RMSE:.4f}.
5. **Valor incremental post-refinamiento:** {'sí' if a2.mean_delta_RMSE<0 and a2.fold_win_rate>.6 else 'débil/no robusto'} para precipitación; {'sí' if a3.mean_delta_RMSE<0 and a3.fold_win_rate>.6 else 'débil/no robusto'} para TOP20.
6. **Ganancia History conservada:** precipitación={abs(a2.mean_delta_RMSE)/orig:.1%}; TOP20={abs(a3.mean_delta_RMSE)/orig:.1%} de la ganancia original (magnitud, sólo si delta negativo).
7. **Folds:** original={a1.fold_win_rate:.0%}, precip={a2.fold_win_rate:.0%}, TOP20={a3.fold_win_rate:.0%}.
8. **Repeticiones:** original={int(a1.repetitions_improved)}, precip={int(a2.repetitions_improved)}, TOP20={int(a3.repetitions_improved)} de 10.
9. **Errores compartidos:** `residual_correlation_summary.csv` compara antes/después y reducción de varianza/|residual|.
10. **Difficult parcels:** {hard_gain}.
11. **y-atypical:** {ya_gain}.
12. **LOW/MID/HIGH del campeón:** {seg[seg.pipeline.eq(best.pipeline)][['segment','RMSE','MAE','bias']].round(3).to_dict('records')}; no se usaron segmentos para selección.
13. **Calibración:** beta base TOP20={cal.loc['TOP20_ENET_BASE','beta']:.3f}; beta campeón={cal.loc[best.pipeline,'beta']:.3f}; History reduce compresión, aunque beta permanece <1.
14. **Residual vs directa:** {direct.round(4).to_dict('records')}.
15. **Necesidad del bloque completo efectivo:** {hist.round(4).to_dict('records')}.
16. **TOP15:** iguala prácticamente a las 16 variables efectivas y es ligeramente mejor en TOP20/Precipitation; diferencia mínima, por lo que se favorece como opción compacta.
17. **Best performance:** {best.pipeline}.
18. **Best compact:** {compact.name}, RMSE={compact.RMSE:.4f}.
19. **Benchmark RS5 recomendado:** {best.pipeline}; mantener {compact.name} como alternativa compacta.
20. **Preparación para RS5:** sí desde el punto de vista técnico, pero RS5 no fue iniciado.
''';(D['report']/'champion_reconstruction_report.md').write_text(txt,encoding='utf-8')
def main():
 ids,X,y=rs1.load_xy();ids=ids.reset_index(drop=True);y=y.reset_index(drop=True);C=X[rs1.climate_cols(X)].reset_index(drop=True);raw=pd.read_parquet(rs1.FEATURE_DIR/'history_features.parquet').set_index(ID).reindex(ids);H=raw[[c for c in raw if c.startswith('HIST_S2_') and not c.endswith('_months')]].reset_index(drop=True);assert H.shape[1]==16,'Expected 16 nonconstant Sentinel historical variables';f,p,hp=run(ids,y,C,H);sm,by=summarize(f,p);hard=diagnostics(sm,by);report(sm,hard);print(f'RS4 complete: {sm.iloc[0].pipeline}, RMSE={sm.iloc[0].RMSE:.4f}',flush=True)
if __name__=='__main__':main()
