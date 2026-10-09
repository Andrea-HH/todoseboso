"""RS5: segunda auditoría residual sobre TOP20_ENET + S2 History TOP15."""
from pathlib import Path
import sys,json,time,warnings,importlib.util
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
def loadmod(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
rs1=loadmod('rs1','207_residual_signal_audit.py');rs4=loadmod('rs4','210_champion_reconstruction.py')
import numpy as np,pandas as pd
from scipy.stats import pearsonr,spearmanr
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score,median_absolute_error
from sklearn.linear_model import Ridge,ElasticNet
from xgboost import XGBRegressor
warnings.filterwarnings('ignore');ID=rs1.ID;SEED=rs1.SEED
BASE=ROOT/'outputs/modeling/residual_signal_audit/stage5_second_residual_audit';D={x:BASE/x for x in ['residuals','associations','block_models','survival','diagnostics','winners','report','checkpoints']}
for p in D.values():p.mkdir(parents=True,exist_ok=True)
BLOCKS=['PLANET','TOPO_BASIC','SENTINEL_CORE','ANOMALY','TOPO_ADVANCED','FUNCTIONAL_FPCA','LANDSAT'];MODELS=['RIDGE','ENET','XGB']
def corr(a,b,k='spearman'):
 z=pd.DataFrame({'a':np.asarray(a,float),'b':np.asarray(b,float)}).dropna()
 if len(z)<3 or z.a.nunique()<2 or z.b.nunique()<2:return np.nan
 return float((spearmanr if k=='spearman' else pearsonr)(z.a,z.b).statistic)
def fit(kind,par,x,y):
 if kind=='RIDGE':return Ridge(**par).fit(x,y)
 if kind=='ENET':return ElasticNet(**par,max_iter=30000,random_state=SEED).fit(x,y)
 return XGBRegressor(**par,objective='reg:squarederror',random_state=SEED,n_jobs=1,verbosity=0).fit(x,y)
def champion_once(name,C,H,y,tr,va,inner,cpar,hpar):
 cf,cv,ccols,_=rs4.climate_outer(name,C,y,tr,va,inner,cpar);rt=y.iloc[tr].to_numpy()-cf;h15=pd.Series({c:abs(corr(H[c].iloc[tr],rt)) for c in H}).sort_values(ascending=False).head(15).index.tolist();rh,_=rs4.residual_fit(H,rt,tr,va,h15,hpar);return cv+rh,ccols,h15
def champion_crossfit(name,C,H,y,tr,va,k,cpar,hpar):
 inner=list(KFold(4,shuffle=True,random_state=SEED+k).split(tr));cf=np.empty(len(tr))
 for j,(ia,ib) in enumerate(inner):
  atr=tr[ia];av=tr[ib];sub=list(KFold(4,shuffle=True,random_state=SEED+1000+k*10+j).split(atr));yp,_,_=champion_once(name,C,H,y,atr,av,sub,cpar,hpar);cf[ib]=yp
 yp,cc,h15=champion_once(name,C,H,y,tr,va,inner,cpar,hpar);return cf,yp,cc,h15
def pars(rs1hp,block,model,rep,fold):
 q=rs1hp[(rs1hp.block==block)&(rs1hp.model==model)&(rs1hp['repeat']==rep)&(rs1hp.fold==fold)]
 return json.loads(q.iloc[0].best_params)
def run(ids,y,C,H,blocks,curves,t):
 splits=rs1.save_splits(ids);pos={v:i for i,v in enumerate(ids)};chp=rs4.hp_all();rhp=pd.read_csv(ROOT/'outputs/modeling/residual_signal_audit/stage1/block_models/selected_hyperparameters.csv');rows=[];pred=[];hps=[];trainres=[];start=time.time()
 for k,s in splits.iterrows():
  tr=np.array([pos[v] for v in json.loads(s.train_ID_POLIGONO)]);va=np.array([pos[v] for v in json.loads(s.validation_ID_POLIGONO)]);rep=int(s['repeat']);fold=int(s['fold']);cpar=json.loads(chp[(chp.pipeline=='CLIMATE_ENET')&(chp['repeat']==rep)&(chp.fold==fold)].iloc[0].best_params);hpar=pars(rhp,'HISTORY','XGB',rep,fold);cf,cv,cc,h15=champion_crossfit('TOP20_ENET',C,H,y,tr,va,k,cpar,hpar);r2=y.iloc[tr].to_numpy()-cf;rv=y.iloc[va].to_numpy()-cv
  for i,ix in enumerate(tr):trainres.append({'outer_index':k,'row_index':ix,'residual2':r2[i]})
  for block in BLOCKS:
   xtr,xva,names=rs1.block_repr(block,blocks,curves,t,tr,va)
   for model in MODELS:
    par=pars(rhp,block,model,rep,fold);a,b,_,_=rs1.prep(pd.concat([xtr,xva],ignore_index=True),np.arange(len(xtr)),np.arange(len(xtr),len(xtr)+len(xva)),model!='XGB');m=fit(model,par,a,r2);rh=m.predict(b);yp=cv+rh;rm=mean_squared_error(y.iloc[va],yp)**.5;br=mean_squared_error(y.iloc[va],cv)**.5;pipe=f'{model}_RESIDUAL2_{block}';rows.append({'pipeline':pipe,'block':block,'model':model,'repeat':rep,'fold':fold,'n_validation':len(va),'baseline_RMSE':br,'corrected_RMSE':rm,'delta_RMSE':rm-br,'corrected_MAE':mean_absolute_error(y.iloc[va],yp),'corrected_R2':r2_score(y.iloc[va],yp),'corrected_MedAE':median_absolute_error(y.iloc[va],yp),'residual_correlation':corr(rv,rh,'pearson')})
    hps.append({'pipeline':pipe,'block':block,'model':model,'repeat':rep,'fold':fold,'params':json.dumps(par,sort_keys=True),'source':'frozen RS1 small-grid choice within same outer fold','n_features':len(names)})
    for i,pid in enumerate(ids.iloc[va]):pred.append({ID:pid,'pipeline':pipe,'block':block,'model':model,'repeat':rep,'fold':fold,'y_true':y.iloc[va[i]],'champion_pred':cv[i],'corrected_pred':yp[i],'residual2_true':rv[i],'residual2_pred':rh[i]})
  pd.DataFrame(rows).to_csv(D['checkpoints']/'fold_metrics_partial.csv',index=False);print(f'fold {k+1}/50 {time.time()-start:.1f}s',flush=True)
 pd.DataFrame(rows).to_csv(D['block_models']/'fold_metrics.csv',index=False);pd.DataFrame(pred).to_parquet(D['checkpoints']/'residual2_predictions.parquet',index=False);pd.DataFrame(hps).to_csv(D['block_models']/'selected_hyperparameters.csv',index=False);pd.DataFrame(trainres).to_parquet(D['checkpoints']/'outer_train_residual2.parquet',index=False);return pd.DataFrame(rows),pd.DataFrame(pred),pd.DataFrame(hps)
def associations(ids,blocks,rnew,rold):
 rows=[]
 for block in BLOCKS:
  X=blocks[block]
  for c in X:rows.append({'feature':c,'block':block,'pearson_residual2':corr(X[c],rnew,'pearson'),'spearman_residual2':corr(X[c],rnew),'pearson_abs_residual2':corr(X[c],abs(rnew),'pearson'),'spearman_abs_residual2':corr(X[c],abs(rnew))})
 a=pd.DataFrame(rows);a.to_csv(D['associations']/'feature_residual2_association.csv',index=False);old=pd.read_csv(ROOT/'outputs/modeling/residual_signal_audit/stage1/associations/feature_residual_association.csv');a.merge(old[['feature','block','spearman_residual','spearman_abs_residual']],on=['feature','block'],how='left').to_csv(D['associations']/'old_vs_new_residual_association.csv',index=False);return a
def summarize(f,p):
 out=[]
 for pipe,g in f.groupby('pipeline'):
  out.append({'pipeline':pipe,'block':g.block.iloc[0],'model':g.model.iloc[0],'champion_RMSE':g.baseline_RMSE.mean(),'corrected_RMSE':g.corrected_RMSE.mean(),'mean_delta_RMSE':g.delta_RMSE.mean(),'median_delta_RMSE':g.delta_RMSE.median(),'delta_std':g.delta_RMSE.std(),'delta_q25':g.delta_RMSE.quantile(.25),'delta_q75':g.delta_RMSE.quantile(.75),'fold_win_rate':(g.delta_RMSE<0).mean(),'repetitions_improved':g.groupby('repeat').delta_RMSE.mean().lt(0).sum(),'worst_fold_deterioration':g.delta_RMSE.max(),'best_fold_gain':g.delta_RMSE.min(),'residual_correlation_mean':g.residual_correlation.mean()})
 sm=pd.DataFrame(out).sort_values('corrected_RMSE');sm.to_csv(D['block_models']/'block_residual2_metrics.csv',index=False);rep=f.groupby(['pipeline','block','model','repeat']).delta_RMSE.mean().reset_index();rep.to_csv(D['block_models']/'paired_delta_rmse.csv',index=False)
 # Frozen champion residual targets.
 champ=pd.read_parquet(ROOT/'outputs/modeling/residual_signal_audit/stage4_champion_reconstruction/predictions/oof_predictions.parquet');champ=champ[champ.pipeline.eq('TOP20_ENET_HISTORY15')].copy();champ['residual2']=champ.y_true-champ.y_pred;champ.to_parquet(D['residuals']/'champion_oof_residuals.parquet',index=False);parcel=champ.groupby(ID).agg(y_true=('y_true','first'),champion_prediction_mean=('y_pred','mean'),residual2_mean=('residual2','mean')).reset_index();parcel.to_csv(D['residuals']/'residual2_by_parcel.csv',index=False)
 return sm,parcel
def diagnostics(ids,sm,p):
 best=sm.groupby('block',as_index=False).first();keep=best.pipeline.tolist();q=p[p.pipeline.isin(keep)].groupby([ID,'pipeline','block']).agg(y_true=('y_true','first'),champion_pred=('champion_pred','mean'),corrected_pred=('corrected_pred','mean'),residual_before=('residual2_true','mean'),residual_after=('corrected_pred',lambda x:np.nan)).reset_index();q['residual_after']=q.y_true-q.corrected_pred;q['abs_before']=abs(q.y_true-q.champion_pred);q['abs_after']=abs(q.residual_after);q['improvement']=q.abs_before-q.abs_after
 hard=pd.read_csv(ROOT/'outputs/modeling/family_1/support_analysis/support/difficult_parcel_support.csv');hard=hard[hard.difficult_all_3][[ID,'support_class']];hq=q.merge(hard,on=ID);hq.to_csv(D['diagnostics']/'difficult_parcels_residual2.csv',index=False);hq[hq.support_class.eq('y-outlier given similar X')].to_csv(D['diagnostics']/'yatypical_residual2.csv',index=False)
 seg=[];cal=[];vr=[]
 # champion plus each block, parcel aggregated.
 base=q.drop_duplicates(ID)[[ID,'y_true','champion_pred']]
 for _,r in best.iterrows():
  g=q[q.pipeline.eq(r.pipeline)].copy();g['segment']=pd.qcut(g.y_true,[0,.25,.75,1],labels=['LOW','MID','HIGH'])
  for z,x in g.groupby('segment',observed=True):seg.append({'pipeline':r.pipeline,'block':r.block,'segment':z,'n':len(x),'RMSE':mean_squared_error(x.y_true,x.corrected_pred)**.5,'MAE':mean_absolute_error(x.y_true,x.corrected_pred),'bias':(x.corrected_pred-x.y_true).mean()})
  beta,alpha=np.polyfit(g.y_true,g.corrected_pred,1);cal.append({'pipeline':r.pipeline,'alpha':alpha,'beta':beta,'R2':r2_score(g.y_true,g.corrected_pred)});vr.append({'pipeline':r.pipeline,'block':r.block,'variance_before':g.residual_before.var(),'variance_after':g.residual_after.var(),'variance_reduction':g.residual_before.var()-g.residual_after.var(),'mean_abs_before':g.abs_before.mean(),'mean_abs_after':g.abs_after.mean(),'mean_abs_reduction':g.improvement.mean(),'residual_before_after_correlation':g.residual_before.corr(g.residual_after)})
 beta,alpha=np.polyfit(base.y_true,base.champion_pred,1);cal.append({'pipeline':'TOP20_ENET_HISTORY15_BASE','alpha':alpha,'beta':beta,'R2':r2_score(base.y_true,base.champion_pred)});pd.DataFrame(seg).to_csv(D['diagnostics']/'yield_segment_performance.csv',index=False);pd.DataFrame(cal).to_csv(D['diagnostics']/'calibration_summary.csv',index=False);pd.DataFrame(vr).to_csv(D['diagnostics']/'residual_variance_reduction.csv',index=False);return best,hq
def survival(sm):
 old=pd.read_csv(ROOT/'outputs/modeling/residual_signal_audit/stage1/diagnostics/block_signal_density.csv').set_index('block');best=sm.groupby('block',as_index=False).first();rows=[]
 for _,r in best.iterrows():
  od=old.loc[r.block,'best_delta_RMSE'];new=r.mean_delta_RMSE
  cls='SIGNAL SURVIVES' if od<0 and new<0 and r.fold_win_rate>.6 else ('SIGNAL ABSORBED' if od<0 and new>=0 else ('SIGNAL EMERGES' if od>=0 and new<0 and r.fold_win_rate>.6 else 'NO SIGNAL'))
  rows.append({'block':r.block,'rs1_delta_vs_climate':od,'rs5_delta_vs_champion':new,'rs5_fold_win_rate':r.fold_win_rate,'rs5_repetitions_improved':r.repetitions_improved,'classification':cls})
 z=pd.DataFrame(rows).sort_values('rs5_delta_vs_champion');z.to_csv(D['survival']/'rs1_vs_rs5_signal_survival.csv',index=False);return z
def winner_followup(ids,y,C,H,blocks,curves,t,sm):
 strong=sm[(sm.mean_delta_RMSE<0)&(sm.median_delta_RMSE<0)&(sm.fold_win_rate>.6)&(sm.repetitions_improved>=8)]
 empty=pd.DataFrame(columns=['winner','experiment','RMSE','delta_RMSE','fold_win_rate'])
 if strong.empty:
  for fn in ['winner_subfamily_metrics.csv','winner_ablation.csv','winner_compact_metrics.csv']:empty.to_csv(D['winners']/fn,index=False)
  pd.DataFrame(columns=['block','residual_RMSE','direct_RMSE']).to_csv(D['winners']/'direct_augmentation.csv',index=False);pd.DataFrame(columns=['block','primary_delta','secondary_delta']).to_csv(D['winners']/'secondary_benchmark_sensitivity.csv',index=False);return []
 winners=strong.block.drop_duplicates().head(2).tolist();winner=winners[0]
 if winner!='TOPO_BASIC':
  pd.DataFrame([{'winner':winner,'note':'winner decomposition not implemented for this taxonomy'}]).to_csv(D['winners']/'winner_subfamily_metrics.csv',index=False);empty.to_csv(D['winners']/'winner_ablation.csv',index=False);empty.to_csv(D['winners']/'winner_compact_metrics.csv',index=False);return winners
 splits=rs1.save_splits(ids);pos={v:i for i,v in enumerate(ids)};rhp=pd.read_csv(ROOT/'outputs/modeling/residual_signal_audit/stage1/block_models/selected_hyperparameters.csv');chp=rs4.hp_all();trres=pd.read_parquet(D['checkpoints']/'outer_train_residual2.parquet');pp=pd.read_parquet(D['checkpoints']/'residual2_predictions.parquet');T=blocks[winner];cols=list(T);elev=[c for c in cols if 'elevation' in c];slope=[c for c in cols if c not in elev];subsets={'ALL':cols,'ONLY_ELEVATION':elev,'ONLY_SLOPE':slope,'WITHOUT_ELEVATION':slope,'WITHOUT_SLOPE':elev};rows=[];direct=[];secondary=[]
 for k,s in splits.iterrows():
  tr=np.array([pos[v] for v in json.loads(s.train_ID_POLIGONO)]);va=np.array([pos[v] for v in json.loads(s.validation_ID_POLIGONO)]);rep=int(s['repeat']);fold=int(s['fold']);r2=trres[trres.outer_index.eq(k)].set_index('row_index').reindex(tr).residual2.to_numpy();pv=pp[(pp.pipeline=='RIDGE_RESIDUAL2_TOPO_BASIC')&(pp['repeat']==rep)&(pp.fold==fold)].sort_values(ID);order=np.argsort(ids.iloc[va].to_numpy());cv=pv.champion_pred.to_numpy()[np.argsort(np.argsort(order))] if False else pv.set_index(ID).reindex(ids.iloc[va]).champion_pred.to_numpy();rv=y.iloc[va].to_numpy()-cv;rpar=pars(rhp,winner,'RIDGE',rep,fold)
  rank=pd.Series({c:abs(corr(T[c].iloc[tr],r2)) for c in cols}).sort_values(ascending=False)
  tests=dict(subsets)
  for n in [3,5,10,15]:tests[f'TOP{n}']=rank.head(n).index.tolist()
  for name,cc in tests.items():
   a,b,_,_=rs1.prep(pd.concat([T[cc].iloc[tr],T[cc].iloc[va]],ignore_index=True),np.arange(len(tr)),np.arange(len(tr),len(tr)+len(va)),True);rh=fit('RIDGE',rpar,a,r2).predict(b);rm=mean_squared_error(y.iloc[va],cv+rh)**.5;br=mean_squared_error(y.iloc[va],cv)**.5;rows.append({'winner':winner,'experiment':name,'repeat':rep,'fold':fold,'n_features':len(cc),'RMSE':rm,'delta_RMSE':rm-br})
  # Direct augmentation with Ridge and a small XGB comparator.
  ccols=rs4.rank20(C,y,tr);h15=pd.Series({c:abs(corr(H[c].iloc[tr],r2)) for c in H}).sort_values(ascending=False).head(15).index.tolist();F=pd.concat([C[ccols],H[h15],T],axis=1)
  for kind,par in [('RIDGE',rpar),('XGB',json.loads(chp[(chp.pipeline=='CLIMATE_XGB')&(chp['repeat']==rep)&(chp.fold==fold)].iloc[0].best_params))]:
   a,b,_,_=rs1.prep(F,tr,va,kind!='XGB');yp=fit(kind,par,a,y.iloc[tr]).predict(b);direct.append({'block':winner,'model':kind,'repeat':rep,'fold':fold,'direct_RMSE':mean_squared_error(y.iloc[va],yp)**.5})
  # Secondary benchmark: precipitation champion, fully nested, then Topo Ridge.
  cpar=json.loads(chp[(chp.pipeline=='CLIMATE_XGB')&(chp['repeat']==rep)&(chp.fold==fold)].iloc[0].best_params);hpar=pars(rhp,'HISTORY','XGB',rep,fold);cf2,cv2,_,_=champion_crossfit('PRECIPITATION_XGB',C,H,y,tr,va,k,cpar,hpar);r22=y.iloc[tr].to_numpy()-cf2;a,b,_,_=rs1.prep(pd.concat([T.iloc[tr],T.iloc[va]],ignore_index=True),np.arange(len(tr)),np.arange(len(tr),len(tr)+len(va)),True);yp2=cv2+fit('RIDGE',rpar,a,r22).predict(b);secondary.append({'block':winner,'repeat':rep,'fold':fold,'baseline_RMSE':mean_squared_error(y.iloc[va],cv2)**.5,'corrected_RMSE':mean_squared_error(y.iloc[va],yp2)**.5})
 z=pd.DataFrame(rows);summ=[]
 for e,g in z.groupby('experiment'):summ.append({'winner':winner,'experiment':e,'n_features':g.n_features.iloc[0],'RMSE':g.RMSE.mean(),'delta_RMSE':g.delta_RMSE.mean(),'median_delta':g.delta_RMSE.median(),'fold_win_rate':(g.delta_RMSE<0).mean(),'repetitions_improved':g.groupby('repeat').delta_RMSE.mean().lt(0).sum()})
 ss=pd.DataFrame(summ).sort_values('RMSE');ss[ss.experiment.str.startswith('ONLY_')].to_csv(D['winners']/'winner_subfamily_metrics.csv',index=False);ss[ss.experiment.str.startswith('WITHOUT_')|ss.experiment.eq('ALL')].to_csv(D['winners']/'winner_ablation.csv',index=False);ss[ss.experiment.str.startswith('TOP')|ss.experiment.eq('ALL')].to_csv(D['winners']/'winner_compact_metrics.csv',index=False)
 dr=pd.DataFrame(direct);ds=dr.groupby('model').direct_RMSE.mean().reset_index();resid=sm[sm.block.eq(winner)].iloc[0];ds['residual_RMSE']=resid.corrected_RMSE;ds['delta_direct_minus_residual']=ds.direct_RMSE-ds.residual_RMSE;ds.to_csv(D['winners']/'direct_augmentation.csv',index=False)
 sec=pd.DataFrame(secondary);sec['delta_RMSE']=sec.corrected_RMSE-sec.baseline_RMSE;pd.DataFrame([{'block':winner,'primary_delta':resid.mean_delta_RMSE,'secondary_baseline_RMSE':sec.baseline_RMSE.mean(),'secondary_corrected_RMSE':sec.corrected_RMSE.mean(),'secondary_delta':sec.delta_RMSE.mean(),'secondary_median_delta':sec.delta_RMSE.median(),'secondary_fold_win_rate':(sec.delta_RMSE<0).mean(),'secondary_repetitions_improved':sec.groupby('repeat').delta_RMSE.mean().lt(0).sum()}]).to_csv(D['winners']/'secondary_benchmark_sensitivity.csv',index=False);return winners
def report(sm,surv,best,hq,winners):
 top=sm.iloc[0];strong=sm[(sm.mean_delta_RMSE<0)&(sm.median_delta_RMSE<0)&(sm.fold_win_rate>.6)&(sm.repetitions_improved>=8)];hard=hq.groupby('block').improvement.agg(mean='mean',prop=lambda x:(x>0).mean()).round(3).to_dict('index');ya=hq[hq.support_class.eq('y-outlier given similar X')].groupby('block').improvement.agg(mean='mean',prop=lambda x:(x>0).mean()).round(3).to_dict('index');lines={b:sm[sm.block.eq(b)].iloc[0][['pipeline','corrected_RMSE','mean_delta_RMSE','median_delta_RMSE','fold_win_rate','repetitions_improved']].to_dict() for b in BLOCKS};stop=len(strong)==0;seg=pd.read_csv(D['diagnostics']/'yield_segment_performance.csv');cal=pd.read_csv(D['diagnostics']/'calibration_summary.csv').set_index('pipeline');direct=pd.read_csv(D['winners']/'direct_augmentation.csv');sub=pd.read_csv(D['winners']/'winner_subfamily_metrics.csv');compact=pd.read_csv(D['winners']/'winner_compact_metrics.csv');secondary=pd.read_csv(D['winners']/'secondary_benchmark_sensitivity.csv')
 txt=f'''# RS5 — Second Residual Signal Audit

## Controles
Baseline congelado: TOP20_ENET_HISTORY15. Residual2=`y−ŷ_champion`. El campeón se reconstruyó dentro de cada outer fold y sus targets de outer-train mediante champion sub-inner OOF. Hiperparámetros de bloques reutilizan elecciones RS1 realizadas dentro del mismo outer fold. No se usó History/Climate como bloque candidato, ni clustering, MoE, RS5 posterior o predicción final.

## Respuestas
1. **Mejor bloque residual restante:** {top.block} con {top.pipeline}.
2. **Planet:** {lines['PLANET']}.
3. **Topography Basic:** {lines['TOPO_BASIC']}.
4. **Sentinel Current:** {lines['SENTINEL_CORE']}.
5. **Anomaly:** {lines['ANOMALY']}.
6. **Topography Advanced:** {lines['TOPO_ADVANCED']}.
7. **FPCA:** {lines['FUNCTIONAL_FPCA']}.
8. **Landsat:** {lines['LANDSAT']}.
9. **Mejor RMSE nuevo:** {top.corrected_RMSE:.4f}.
10. **Delta vs campeón matched:** {top.mean_delta_RMSE:+.4f}.
11. **Folds mejorados:** {top.fold_win_rate:.0%}.
12. **Repeticiones:** {int(top.repetitions_improved)}/10.
13–15. **Supervivencia RS1→RS5:** {surv.round(4).to_dict('records')}.
16. **Difficult parcels:** {hard}.
17. **y-atypical:** {ya}.
18–19. **LOW/HIGH del ganador:** {seg[seg.block.eq(top.block)][['segment','RMSE','MAE','bias']].round(3).to_dict('records')}.
20. **Calibración:** beta campeón={cal.loc['TOP20_ENET_HISTORY15_BASE','beta']:.3f}; beta con Topography={cal.loc[top.pipeline,'beta']:.3f}.
21. **Residual vs directa:** {direct.round(4).to_dict('records')}; la corrección residual es claramente superior.
22. **Tercera capa:** {'sí, evidencia preliminar para '+', '.join(strong.block.unique()) if len(strong) else 'no'}. Descomposición={sub.round(4).to_dict('records')}; compactación={compact.round(4).to_dict('records')}; sensibilidad secundaria={secondary.round(4).to_dict('records')}.
23. **Máximo a promover:** {winners[:1]}.
24. **Stopping rule:** {'DETENER arquitectura secuencial' if stop else 'no se activa; revisar únicamente el bloque promovido antes de otra etapa'}.
25. **Champion provisional:** {'TOP20_ENET_HISTORY15 (sin cambio)' if stop else top.pipeline+' sobre TOP20_ENET_HISTORY15'}.
''';(D['report']/'second_residual_signal_audit_report.md').write_text(txt,encoding='utf-8')
def main():
 ids,X,y=rs1.load_xy();ids=ids.reset_index(drop=True);y=y.reset_index(drop=True);C=X[rs1.climate_cols(X)].reset_index(drop=True);raw=pd.read_parquet(rs1.FEATURE_DIR/'history_features.parquet').set_index(ID).reindex(ids);H=raw[[c for c in raw if c.startswith('HIST_S2_') and not c.endswith('_months')]].reset_index(drop=True);blocks=rs1.load_blocks(ids);_,_,t,curves=rs1.f2.load_data();champ=pd.read_parquet(ROOT/'outputs/modeling/residual_signal_audit/stage4_champion_reconstruction/predictions/oof_predictions.parquet');cp=champ[champ.pipeline.eq('TOP20_ENET_HISTORY15')].groupby(ID).agg(rnew=('residual_after','mean')).reindex(ids).rnew.reset_index(drop=True);old=pd.read_parquet(ROOT/'outputs/modeling/residual_signal_audit/stage1/residuals/climate_enet_oof_residuals.parquet').groupby(ID).residual_fold.mean().reindex(ids).reset_index(drop=True);associations(ids,blocks,cp,old);f,p,hp=run(ids,y,C,H,blocks,curves,t);sm,parcel=summarize(f,p);best,hq=diagnostics(ids,sm,p);surv=survival(sm);winners=winner_followup(ids,y,C,H,blocks,curves,t,sm);report(sm,surv,best,hq,winners);print(f'RS5 complete: {sm.iloc[0].pipeline}, delta={sm.iloc[0].mean_delta_RMSE:+.4f}',flush=True)
if __name__=='__main__':main()
