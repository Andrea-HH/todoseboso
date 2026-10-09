"""RS6: optimización acotada de arquitectura Climate/History/Topo (+Planet sensitivity)."""
from pathlib import Path
import sys,json,time,warnings,importlib.util
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
def loadmod(n,f):s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
rs1=loadmod('rs1','207_residual_signal_audit.py');rs4=loadmod('rs4','210_champion_reconstruction.py')
import numpy as np,pandas as pd
from scipy.stats import spearmanr
from sklearn.model_selection import KFold
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score,median_absolute_error
from xgboost import XGBRegressor
warnings.filterwarnings('ignore');ID=rs1.ID;SEED=rs1.SEED
BASE=ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization';D={x:BASE/x for x in ['metrics','predictions','stages','diagnostics','complexity','models','report','checkpoints']}
for p in D.values():p.mkdir(parents=True,exist_ok=True)
ARCH=['A_CURRENT_CH_H_T','B_REVERSED_CT_H','C1_JOINT_HT_RIDGE','C2_JOINT_HT_XGB','D_CH_T_H2','E1_CH_JOINT_TP_RIDGE','E2_CH_JOINT_TP_XGB']
def corr(a,b):
 z=pd.DataFrame({'a':np.asarray(a,float),'b':np.asarray(b,float)}).dropna();return float(spearmanr(z.a,z.b).statistic) if len(z)>2 and z.a.nunique()>1 and z.b.nunique()>1 else 0.
def fit(kind,par,x,y):
 if kind=='RIDGE':return Ridge(**par).fit(x,y)
 if kind=='ENET':return rs4.ElasticNet(**par,max_iter=30000,random_state=SEED).fit(x,y)
 return XGBRegressor(**par,objective='reg:squarederror',random_state=SEED,n_jobs=1,verbosity=0).fit(x,y)
def transform(F,tr,va,scale):return rs1.prep(F,tr,va,scale)[:2]
def pred_model(kind,par,F,target,tr,va):
 a,b=transform(F,tr,va,kind!='XGB');return fit(kind,par,a,target).predict(b)
def cross_pred(kind,par,F,target,tr,inner):
 out=np.empty(len(tr))
 for ia,ib in inner:out[ib]=pred_model(kind,par,F,target[ia],tr[ia],tr[ib])
 return out
def pars(hp,block,model,rep,fold):return json.loads(hp[(hp.block==block)&(hp.model==model)&(hp['repeat']==rep)&(hp.fold==fold)].iloc[0].best_params)
def metric(y,p):return {'RMSE':mean_squared_error(y,p)**.5,'MAE':mean_absolute_error(y,p),'R2':r2_score(y,p),'MedAE':median_absolute_error(y,p)}
def run(ids,y,C,H,T,P):
 splits=rs1.save_splits(ids);pos={v:i for i,v in enumerate(ids)};chp=rs4.hp_all();hp=pd.read_csv(ROOT/'outputs/modeling/residual_signal_audit/stage1/block_models/selected_hyperparameters.csv');strict=pd.read_parquet(ROOT/'outputs/modeling/residual_signal_audit/stage5_second_residual_audit/checkpoints/outer_train_residual2.parquet');rs5p=pd.read_parquet(ROOT/'outputs/modeling/residual_signal_audit/stage5_second_residual_audit/checkpoints/residual2_predictions.parquet');rows=[];pred=[];stage=[];hps=[];start=time.time()
 for k,s in splits.iterrows():
  tr=np.array([pos[v] for v in json.loads(s.train_ID_POLIGONO)]);va=np.array([pos[v] for v in json.loads(s.validation_ID_POLIGONO)]);rep=int(s['repeat']);fold=int(s['fold']);inner=list(KFold(4,shuffle=True,random_state=SEED+k).split(tr));cpar=json.loads(chp[(chp.pipeline=='CLIMATE_ENET')&(chp['repeat']==rep)&(chp.fold==fold)].iloc[0].best_params);hpar=pars(hp,'HISTORY','XGB',rep,fold);tpar=pars(hp,'TOPO_BASIC','RIDGE',rep,fold)
  cf,cv,cc,_=rs4.climate_outer('TOP20_ENET',C,y,tr,va,inner,cpar);r1=y.iloc[tr].to_numpy()-cf;h15=pd.Series({c:abs(corr(H[c].iloc[tr],r1)) for c in H}).sort_values(ascending=False).head(15).index.tolist();hv=pred_model('XGB',hpar,H[h15],r1,tr,va);hcf=cross_pred('XGB',hpar,H[h15],r1,tr,inner);chv=cv+hv;r2_simple=y.iloc[tr].to_numpy()-cf-hcf
  # Strict nested residual2 and frozen CH validation from RS5.
  r2=strict[strict.outer_index.eq(k)].set_index('row_index').reindex(tr).residual2.to_numpy();q=rs5p[(rs5p.pipeline=='RIDGE_RESIDUAL2_TOPO_BASIC')&(rs5p['repeat']==rep)&(rs5p.fold==fold)].set_index(ID).reindex(ids.iloc[va]);chv=q.champion_pred.to_numpy()
  # A: current champion.
  tv=pred_model('RIDGE',tpar,T,r2,tr,va);A=chv+tv
  # B: Climate -> Topo -> History.
  t1v=pred_model('RIDGE',tpar,T,r1,tr,va);t1cf=cross_pred('RIDGE',tpar,T,r1,tr,inner);rB=y.iloc[tr].to_numpy()-cf-t1cf;hb=pred_model('XGB',hpar,H[h15],rB,tr,va);B=cv+t1v+hb
  # C: joint H+T on r1.
  J=pd.concat([H[h15],T],axis=1);C1=cv+pred_model('RIDGE',tpar,J,r1,tr,va);C2=cv+pred_model('XGB',hpar,J,r1,tr,va)
  # D: second conservative History pass after A.
  tcf=cross_pred('RIDGE',tpar,T,r2,tr,inner);r3=r2-tcf;h2=dict(hpar);h2.update({'n_estimators':max(75,int(hpar.get('n_estimators',150)//2)),'max_depth':1,'learning_rate':min(.02,hpar.get('learning_rate',.03)),'reg_lambda':max(15,hpar.get('reg_lambda',10))});Dpred=A+pred_model('XGB',h2,H[h15],r3,tr,va)
  # E: after History, joint Topo+Planet.
  TP=pd.concat([T,P],axis=1);E1=chv+pred_model('RIDGE',tpar,TP,r2,tr,va);E2=chv+pred_model('XGB',hpar,TP,r2,tr,va)
  vals={'A_CURRENT_CH_H_T':A,'B_REVERSED_CT_H':B,'C1_JOINT_HT_RIDGE':C1,'C2_JOINT_HT_XGB':C2,'D_CH_T_H2':Dpred,'E1_CH_JOINT_TP_RIDGE':E1,'E2_CH_JOINT_TP_XGB':E2}
  for name,yp in vals.items():
   mm=metric(y.iloc[va],yp);rows.append({'architecture':name,'repeat':rep,'fold':fold,'n_validation':len(va),**mm})
   for i,pid in enumerate(ids.iloc[va]):pred.append({ID:pid,'architecture':name,'repeat':rep,'fold':fold,'y_true':y.iloc[va[i]],'y_pred':yp[i],'residual':y.iloc[va[i]]-yp[i]})
  stage_defs={'A_CURRENT_CH_H_T':[('CLIMATE',cv),('CLIMATE_HISTORY',chv),('FINAL',A)],'B_REVERSED_CT_H':[('CLIMATE',cv),('CLIMATE_TOPO',cv+t1v),('FINAL',B)],'C1_JOINT_HT_RIDGE':[('CLIMATE',cv),('FINAL',C1)],'C2_JOINT_HT_XGB':[('CLIMATE',cv),('FINAL',C2)],'D_CH_T_H2':[('CLIMATE',cv),('CLIMATE_HISTORY',chv),('CLIMATE_HISTORY_TOPO',A),('FINAL',Dpred)],'E1_CH_JOINT_TP_RIDGE':[('CLIMATE',cv),('CLIMATE_HISTORY',chv),('FINAL',E1)],'E2_CH_JOINT_TP_XGB':[('CLIMATE',cv),('CLIMATE_HISTORY',chv),('FINAL',E2)]}
  for name,seq in stage_defs.items():
   for order,(label,yp) in enumerate(seq,1):stage.append({'architecture':name,'repeat':rep,'fold':fold,'stage_order':order,'stage':label,'RMSE':mean_squared_error(y.iloc[va],yp)**.5,'residual_variance':np.var(y.iloc[va].to_numpy()-yp,ddof=1),'var_y':np.var(y.iloc[va],ddof=1)})
  hps.append({'repeat':rep,'fold':fold,'climate_params':json.dumps(cpar,sort_keys=True),'history_params':json.dumps(hpar,sort_keys=True),'topography_params':json.dumps(tpar,sort_keys=True),'history2_params':json.dumps(h2,sort_keys=True),'climate_features':json.dumps(cc),'history_features':json.dumps(h15)})
  pd.DataFrame(rows).to_csv(D['checkpoints']/'fold_metrics_partial.csv',index=False);print(f'fold {k+1}/50 {time.time()-start:.1f}s',flush=True)
 f=pd.DataFrame(rows);p=pd.DataFrame(pred);st=pd.DataFrame(stage);f.to_csv(D['checkpoints']/'fold_metrics.csv',index=False);p.to_parquet(D['predictions']/'oof_predictions.parquet',index=False);st.to_csv(D['stages']/'stagewise_fold_values.csv',index=False);pd.DataFrame(hps).to_csv(D['models']/'selected_hyperparameters.csv',index=False);return f,p,st
def summarize(f,p,st):
 base=f[f.architecture.eq('A_CURRENT_CH_H_T')].set_index(['repeat','fold']).RMSE;rows=[]
 for a,g in f.groupby('architecture'):
  d=g.apply(lambda r:r.RMSE-base.loc[(r['repeat'],r.fold)],axis=1);rows.append({'architecture':a,'RMSE':g.RMSE.mean(),'median_RMSE':g.RMSE.median(),'std_RMSE':g.RMSE.std(),'MAE':g.MAE.mean(),'R2':g.R2.mean(),'MedAE':g.MedAE.mean(),'mean_delta_vs_A':d.mean(),'median_delta_vs_A':d.median(),'delta_q25':d.quantile(.25),'delta_q75':d.quantile(.75),'fold_win_rate_vs_A':(d<0).mean(),'repetitions_improved':pd.DataFrame({'r':g['repeat'].values,'d':d.values}).groupby('r').d.mean().lt(0).sum(),'worst_deterioration':d.max(),'best_gain':d.min()})
 sm=pd.DataFrame(rows).sort_values('RMSE');sm.to_csv(D['metrics']/'architecture_metrics.csv',index=False);sm.to_csv(D['metrics']/'paired_vs_current_champion.csv',index=False);rep=f.groupby(['architecture','repeat']).agg(mean_RMSE=('RMSE','mean'),std_RMSE=('RMSE','std')).reset_index();rep.to_csv(D['metrics']/'repetition_metrics.csv',index=False)
 by=p.groupby([ID,'architecture']).agg(y_true=('y_true','first'),oof_prediction=('y_pred','mean'),prediction_std=('y_pred','std'),residual=('residual','mean')).reset_index();by['absolute_error']=abs(by.residual);by.to_csv(D['predictions']/'oof_by_parcel.csv',index=False)
 sr=st.groupby(['architecture','stage_order','stage']).agg(mean_RMSE=('RMSE','mean'),mean_residual_variance=('residual_variance','mean'),mean_y_variance=('var_y','mean')).reset_index();sr.to_csv(D['stages']/'stagewise_rmse.csv',index=False);sr[['architecture','stage_order','stage','mean_residual_variance','mean_y_variance']].to_csv(D['stages']/'stagewise_residual_variance.csv',index=False);src=[]
 for a,g in sr.groupby('architecture'):
  g=g.sort_values('stage_order');prev=None
  for _,r in g.iterrows():src.append({'architecture':a,'stage':r.stage,'mean_RMSE':r.mean_RMSE,'incremental_RMSE_change':np.nan if prev is None else r.mean_RMSE-prev});prev=r.mean_RMSE
 pd.DataFrame(src).to_csv(D['stages']/'source_contribution.csv',index=False);return sm,by,sr
def diagnostics(sm,by):
 hard=pd.read_csv(ROOT/'outputs/modeling/family_1/support_analysis/support/difficult_parcel_support.csv');hard=hard[hard.difficult_all_3][[ID,'support_class']];q=by.merge(hard,on=ID);base=q[q.architecture.eq('A_CURRENT_CH_H_T')].set_index(ID).absolute_error
 q['improvement_vs_A']=q.apply(lambda r:base.loc[r[ID]]-r.absolute_error,axis=1);q.to_csv(D['diagnostics']/'difficult_parcels_architectures.csv',index=False);q[q.support_class.eq('y-outlier given similar X')].to_csv(D['diagnostics']/'yatypical_architectures.csv',index=False);seg=[];cal=[]
 for a,g in by.groupby('architecture'):
  g=g.copy();g['segment']=pd.qcut(g.y_true,[0,.25,.75,1],labels=['LOW','MID','HIGH'])
  for z,x in g.groupby('segment',observed=True):seg.append({'architecture':a,'segment':z,'n':len(x),'RMSE':mean_squared_error(x.y_true,x.oof_prediction)**.5,'MAE':mean_absolute_error(x.y_true,x.oof_prediction),'bias':(x.oof_prediction-x.y_true).mean()})
  beta,alpha=np.polyfit(g.y_true,g.oof_prediction,1);cal.append({'architecture':a,'intercept':alpha,'slope':beta,'R2':r2_score(g.y_true,g.oof_prediction)})
 pd.DataFrame(seg).to_csv(D['diagnostics']/'yield_segment_performance.csv',index=False);pd.DataFrame(cal).to_csv(D['diagnostics']/'calibration_summary.csv',index=False);wide=by.pivot(index=ID,columns='architecture',values='residual');wide.corr().to_csv(D['diagnostics']/'residual_correlations.csv')
 comp={'A_CURRENT_CH_H_T':(3,20+15+25,3,20),'B_REVERSED_CT_H':(3,60,3,20),'C1_JOINT_HT_RIDGE':(2,60,2,12),'C2_JOINT_HT_XGB':(2,60,2,18),'D_CH_T_H2':(4,60,4,28),'E1_CH_JOINT_TP_RIDGE':(3,60+len(pd.read_parquet(rs1.FEATURE_DIR/'planet_features.parquet').columns)-1,3,20),'E2_CH_JOINT_TP_XGB':(3,60+len(pd.read_parquet(rs1.FEATURE_DIR/'planet_features.parquet').columns)-1,3,26)};cr=[]
 for _,r in sm.iterrows():
  ns,nf,nm,nh=comp[r.architecture];cr.append({'pipeline':r.architecture,'number_of_stages':ns,'number_of_features':nf,'number_of_models':nm,'number_of_tuned_hyperparameters':nh,'training_time_relative':'very_high' if ns>=4 or 'E2' in r.architecture else ('high' if ns>=3 else 'medium'),'RMSE':r.RMSE,'practical_tie_vs_A':abs(r.mean_delta_vs_A)<.0015})
 pd.DataFrame(cr).to_csv(D['complexity']/'architecture_complexity.csv',index=False);return q
def report(sm,by,sr,hard):
 get=lambda a:sm.set_index('architecture').loc[a];best=sm.iloc[0];eligible=sm[(sm.mean_delta_vs_A<0)&(sm.median_delta_vs_A<=0)&(sm.fold_win_rate_vs_A>.6)&(sm.repetitions_improved>=8)];selected=eligible.iloc[0] if len(eligible) else get('A_CURRENT_CH_H_T');selected_name=selected['architecture'] if 'architecture' in selected.index else selected.name;comp=pd.read_csv(D['complexity']/'architecture_complexity.csv');pars=comp[comp.practical_tie_vs_A].sort_values(['number_of_stages','number_of_features']).iloc[0];cal=pd.read_csv(D['diagnostics']/'calibration_summary.csv').set_index('architecture');h=hard.groupby('architecture').agg(mean_abs_error=('absolute_error','mean'),median_abs_error=('absolute_error','median'),prop_improved=('improvement_vs_A',lambda x:(x>0).mean()),largest_gain=('improvement_vs_A','max'),largest_deterioration=('improvement_vs_A','min')).round(3);ya=hard[hard.support_class.eq('y-outlier given similar X')].groupby('architecture').improvement_vs_A.mean().round(3).to_dict();seg=pd.read_csv(D['diagnostics']/'yield_segment_performance.csv');rc=pd.read_csv(D['diagnostics']/'residual_correlations.csv',index_col=0)
 txt=f'''# RS6 — Residual Architecture Optimization

## Controles
Sólo siete arquitecturas predefinidas, mismos 50 outer folds e inner 4-fold. Residuales de cada capa se generaron cross-fitted dentro de outer-train; A reutiliza residual2 nested de RS5 para reproducibilidad. Sin nuevas fuentes salvo la sensibilidad conjunta Topography+Planet, sin clustering, MoE, entrenamiento final o PREDICTION.

## Respuestas
1. **Reproducción A:** RMSE={get('A_CURRENT_CH_H_T').RMSE:.4f}.
2–3. **Orden:** A={get('A_CURRENT_CH_H_T').RMSE:.4f}; B Topo→History={get('B_REVERSED_CT_H').RMSE:.4f}, delta={get('B_REVERSED_CT_H').mean_delta_vs_A:+.4f}.
4–5. **Joint H+T:** Ridge={get('C1_JOINT_HT_RIDGE').RMSE:.4f}; XGB={get('C2_JOINT_HT_XGB').RMSE:.4f}; secuencial A={get('A_CURRENT_CH_H_T').RMSE:.4f}.
6. **History2:** RMSE={get('D_CH_T_H2').RMSE:.4f}, delta={get('D_CH_T_H2').mean_delta_vs_A:+.4f}, wins={get('D_CH_T_H2').fold_win_rate_vs_A:.0%}; {'no conservar' if abs(get('D_CH_T_H2').mean_delta_vs_A)<.001 or get('D_CH_T_H2').fold_win_rate_vs_A<=.6 else 'considerar'}.
7. **Planet conjunto:** E1 Ridge={get('E1_CH_JOINT_TP_RIDGE').RMSE:.4f}; E2 XGB={get('E2_CH_JOINT_TP_XGB').RMSE:.4f}.
8–11. **Menor RMSE:** {best.architecture}={best.RMSE:.4f}; delta={best.mean_delta_vs_A:+.4f}; wins={best.fold_win_rate_vs_A:.0%}; repeticiones={int(best.repetitions_improved)}/10.
12. **Difficult parcels:** {h.to_dict('index')}.
13. **y-atypical mean gain vs A:** {ya}.
14–15. **LOW/HIGH del mejor:** {seg[seg.architecture.eq(best.architecture)][['segment','RMSE','MAE','bias']].round(3).to_dict('records')}.
16. **Mejor calibración:** {cal.slope.sub(1).abs().idxmin()}, slope={cal.loc[cal.slope.sub(1).abs().idxmin(),'slope']:.3f}.
17. **Menor complejidad en empate práctico:** {pars.pipeline}.
18. **Practical ties |Δ|<0.0015:** {comp[comp.practical_tie_vs_A].pipeline.tolist()}; residuales corr>0.98={[(a,b,round(rc.loc[a,b],3)) for i,a in enumerate(rc) for b in rc.columns[i+1:] if rc.loc[a,b]>.98]}.
19. **Best performance:** {selected_name}, RMSE={selected.RMSE:.4f}.
20. **Best parsimonious:** {pars.pipeline}, RMSE={pars.RMSE:.4f}.
21. **¿Mantener secuencial actual?** {'sí' if selected_name=='A_CURRENT_CH_H_T' else 'no; sustituir sólo si la alternativa satisface toda la regla'}.
22. **Consolidación final:** técnicamente lista con máximo estas dos candidatas; no se ejecutó entrenamiento final.
''';(D['report']/'residual_architecture_optimization_report.md').write_text(txt,encoding='utf-8')
def main():
 ids,X,y=rs1.load_xy();ids=ids.reset_index(drop=True);y=y.reset_index(drop=True);C=X[rs1.climate_cols(X)].reset_index(drop=True);hist=pd.read_parquet(rs1.FEATURE_DIR/'history_features.parquet').set_index(ID).reindex(ids);H=hist[[c for c in hist if c.startswith('HIST_S2_') and not c.endswith('_months')]].reset_index(drop=True);T=pd.read_parquet(rs1.FEATURE_DIR/'topography_basic_features.parquet').set_index(ID).reindex(ids).reset_index(drop=True);P=pd.read_parquet(rs1.FEATURE_DIR/'planet_features.parquet').set_index(ID).reindex(ids).reset_index(drop=True);f,p,st=run(ids,y,C,H,T,P);sm,by,sr=summarize(f,p,st);hard=diagnostics(sm,by);report(sm,by,sr,hard);print(f'RS6 complete: {sm.iloc[0].architecture}, RMSE={sm.iloc[0].RMSE:.4f}',flush=True)
if __name__=='__main__':main()
