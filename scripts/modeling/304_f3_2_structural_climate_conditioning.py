"""F3.2 nested structural climate conditioning, M0-M4 only."""
from pathlib import Path
import sys,json,time,warnings,importlib.util
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
def loadmod(n,f):
 s=importlib.util.spec_from_file_location(n,ROOT/'scripts/data_uderstanding/tablas_agrocebada'/f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
rs1=loadmod('rs1','207_residual_signal_audit.py');rs4=loadmod('rs4','210_champion_reconstruction.py')
import numpy as np,pandas as pd
import matplotlib.pyplot as plt,seaborn as sns
from scipy.stats import pearsonr,spearmanr,kendalltau
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error,mean_absolute_error,median_absolute_error,r2_score
warnings.filterwarnings('ignore');sns.set_theme(style='whitegrid');ID=rs1.ID;SEED=rs1.SEED
BASE=ROOT/'outputs/modeling/family_3/f3_2_structural_climate_conditioning';D={x:BASE/x for x in ['specifications','folds','predictions','metrics','comparisons','coefficients','errors','figures','report','checkpoints']}
for p in D.values():p.mkdir(parents=True,exist_ok=True)
A1=['HIST_S2_ndvi_promedio_mean','HIST_S2_ndvi_promedio_std','HIST_S2_ndwi_promedio_mean','HIST_S2_msi_promedio_mean','HIST_S2_nddi_promedio_mean','HIST_S2_nddi_promedio_std','TOPO_BASIC_elevation_mean','TOPO_BASIC_elevation_relief','TOPO_BASIC_slope_mean','TOPO_BASIC_slope_iqr','TOPO_BASIC_pct_area_slope_gt_10']
MODS=['CLIMATE_precip_early_sum','CLIMATE_tmin_mean_slope','CLIMATE_tmax_mean_peak_day','CLIMATE_dtr_mean_std'];ALPHAS=[.1,1,10,100,1000]
class Struct:
 def __init__(self,blocks):self.blocks=blocks;self.cols=sum(blocks.values(),[])
 def fit(self,d):
  self.imp=SimpleImputer(strategy='median').fit(d[self.cols]);z=self.imp.transform(d[self.cols]);self.sc=StandardScaler().fit(z);self.sc.scale_[self.sc.scale_<1e-8]=1;self.w=np.concatenate([np.repeat(1/np.sqrt(len(v)),len(v)) for v in self.blocks.values()]) if len(self.blocks)>1 else np.ones(len(self.cols));self.pca=PCA(3,random_state=SEED).fit(self.sc.transform(z)*self.w);return self
 def transform(self,d):return self.pca.transform(self.sc.transform(self.imp.transform(d[self.cols]))*self.w)
def ccc(y,p):return 2*np.cov(y,p,ddof=1)[0,1]/(np.var(y,ddof=1)+np.var(p,ddof=1)+(np.mean(y)-np.mean(p))**2)
def design(Z,C,interaction,sc=None,fit=False):
 if not interaction:return Z,None
 if fit:sc=StandardScaler().fit(C)
 Q=sc.transform(C);return np.column_stack([Z,Q]+[Q[:,i:i+1]*Z for i in range(Q.shape[1])]),sc
def climate_strict_inner(C,y,outer_tr,ia,ib,cpar,seed):
 ga=outer_tr[ia];gb=outer_tr[ib];ii=list(KFold(4,shuffle=True,random_state=seed).split(ga));cf,cv,_,_=rs4.climate_outer('TOP20_ENET',C,y,ga,gb,ii,cpar);return cf,cv
def select_alpha(C,S,y,tr,inner,cpar,interaction):
 losses={a:[] for a in ALPHAS}
 for j,(ia,ib) in enumerate(inner):
  cf,pb=climate_strict_inner(C,y,tr,ia,ib,cpar,SEED+100+j);st=Struct(S).fit(SDATA.iloc[tr[ia]]);Za=st.transform(SDATA.iloc[tr[ia]]);Zb=st.transform(SDATA.iloc[tr[ib]]);Xa,sc=design(Za,C.iloc[tr[ia]][MODS],interaction,fit=True);Xb,_=design(Zb,C.iloc[tr[ib]][MODS],interaction,sc=sc);r=y.iloc[tr[ia]].to_numpy()-cf;target=y.iloc[tr[ib]].to_numpy()
  for a in ALPHAS:losses[a].append(mean_squared_error(target,pb+Ridge(alpha=a).fit(Xa,r).predict(Xb)))
 return min(ALPHAS,key=lambda a:np.mean(losses[a]))
def metric(y,p):
 slope,inter=np.polyfit(y,p,1);return {'RMSE':mean_squared_error(y,p)**.5,'MAE':mean_absolute_error(y,p),'MedAE':median_absolute_error(y,p),'R2':r2_score(y,p),'Pearson':pearsonr(y,p).statistic,'Spearman':spearmanr(y,p).statistic,'Kendall':kendalltau(y,p).statistic,'CCC':ccc(y,p),'calibration_slope':slope,'range_ratio':np.ptp(p)/np.ptp(y),'bias':np.mean(p-y)}
def run():
 global SDATA
 ids,X,y=rs1.load_xy();ids=ids.reset_index(drop=True);y=y.reset_index(drop=True);C=X[rs1.climate_cols(X)].reset_index(drop=True);h=pd.read_parquet(rs1.FEATURE_DIR/'history_features.parquet').set_index(ID).reindex(ids).reset_index();b=pd.read_parquet(rs1.FEATURE_DIR/'topography_basic_features.parquet').set_index(ID).reindex(ids).reset_index();a=pd.read_parquet(rs1.FEATURE_DIR/'topography_advanced_features.parquet').set_index(ID).reindex(ids).reset_index();SDATA=h.merge(b,on=ID).merge(a,on=ID);hist=[c for c in h if c.startswith('HIST_S2_') and not c.endswith('_months')];basic=[c for c in b if c.startswith('TOPO_BASIC_')];adv=[c for c in a if c.startswith('TOPO_ADV_')];specs={'A1':{'compact':A1},'E3':{'sentinel':hist,'basic':basic,'advanced':adv}};spl=rs1.save_splits(ids);pos={v:i for i,v in enumerate(ids)};chp=rs4.hp_all();pred=[];fmet=[];coef=[];hyp=[];start=time.time()
 for k,s in spl.iterrows():
  tr=np.array([pos[v] for v in json.loads(s.train_ID_POLIGONO)]);va=np.array([pos[v] for v in json.loads(s.validation_ID_POLIGONO)]);rep,fold=int(s['repeat']),int(s.fold);inner=list(KFold(4,shuffle=True,random_state=SEED+k).split(tr));cpar=json.loads(chp[(chp.pipeline=='CLIMATE_ENET')&(chp['repeat']==rep)&(chp.fold==fold)].iloc[0].best_params);cf,cv,cvars,_=rs4.climate_outer('TOP20_ENET',C,y,tr,va,inner,cpar);vals={'M0_CLIMATE':cv};r=y.iloc[tr].to_numpy()-cf
  for sn,blocks in specs.items():
   st=Struct(blocks).fit(SDATA.iloc[tr]);Za=st.transform(SDATA.iloc[tr]);Zv=st.transform(SDATA.iloc[va])
   for inter in [False,True]:
    model={'A1':('M2_A1_INTERACTION' if inter else 'M1_A1_ADDITIVE'),'E3':('M4_E3_INTERACTION' if inter else 'M3_E3_ADDITIVE')}[sn];alpha=select_alpha(C,blocks,y,tr,inner,cpar,inter);Xa,sc=design(Za,C.iloc[tr][MODS],inter,fit=True);Xv,_=design(Zv,C.iloc[va][MODS],inter,sc=sc);rr=Ridge(alpha=alpha).fit(Xa,r);vals[model]=cv+rr.predict(Xv);names=[f'{sn}_F{i}' for i in range(1,4)] if not inter else [f'{sn}_F{i}' for i in range(1,4)]+MODS+[f'{m}×{sn}_F{i}' for m in MODS for i in range(1,4)]
    for n,v in zip(names,rr.coef_):coef.append({'model':model,'repeat':rep,'fold':fold,'term':n,'coefficient':v})
    hyp.append({'model':model,'repeat':rep,'fold':fold,'ridge_alpha':alpha,'climate_params':json.dumps(cpar,sort_keys=True),'climate_features':json.dumps(cvars),'structural_features':json.dumps(st.cols),'n_incremental_terms':len(names)})
  for name,p in vals.items():
   mm=metric(y.iloc[va],p);fmet.append({'model':name,'repeat':rep,'fold':fold,'n':len(va),**mm})
   for j,z in enumerate(va):pred.append({ID:ids.iloc[z],'model':name,'repeat':rep,'fold':fold,'y_true':y.iloc[z],'y_pred':p[j]})
  pd.DataFrame(pred).to_parquet(D['checkpoints']/'oof_partial.parquet',index=False);print(f'F3.2 fold {k+1}/50 {time.time()-start:.1f}s',flush=True)
 pd.DataFrame(fmet).to_csv(D['folds']/'fold_metrics.csv',index=False);pd.DataFrame(pred).to_parquet(D['predictions']/'oof_predictions.parquet',index=False);pd.DataFrame(coef).to_csv(D['coefficients']/'ridge_coefficients_by_fold.csv',index=False);pd.DataFrame(hyp).to_csv(D['folds']/'selected_hyperparameters.csv',index=False);pd.DataFrame([{'model':'M0','spec':'Frozen TOP20 ENET climate reference'},{'model':'M1','spec':'M0 + Ridge(A1 PCA3)'},{'model':'M2','spec':'M0 + Ridge(A1 PCA3 + 4 climate moderators + 12 interactions)'},{'model':'M3','spec':'M0 + Ridge(E3 PCA3)'},{'model':'M4','spec':'M0 + Ridge(E3 PCA3 + 4 climate moderators + 12 interactions)'}]).to_csv(D['specifications']/'model_specifications.csv',index=False);pd.DataFrame({'moderator':MODS,'selection':'predefined conceptual subset of frozen Climate TOP20 universe'}).to_csv(D['specifications']/'interaction_variables.csv',index=False);return pd.DataFrame(pred),pd.DataFrame(fmet)
def analyze(p,f):
 # Add frozen Champion for exact paired benchmark.
 ch=pd.read_parquet(ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization/predictions/oof_predictions.parquet');ch=ch[ch.architecture.eq('A_CURRENT_CH_H_T')][[ID,'repeat','fold','y_true','y_pred']].copy();ch['model']='CHAMPION_V1';p=pd.concat([p,ch],ignore_index=True);fm=[]
 for (m,r,fo),q in p.groupby(['model','repeat','fold']):fm.append({'model':m,'repeat':r,'fold':fo,**metric(q.y_true,q.y_pred)})
 fm=pd.DataFrame(fm);g=p.groupby(['model',ID]).agg(y_true=('y_true','first'),y_pred=('y_pred','mean')).reset_index();summary=[]
 for m,q in g.groupby('model'):summary.append({'model':m,'fold_mean_RMSE':fm[fm.model.eq(m)].RMSE.mean(),'fold_sd_RMSE':fm[fm.model.eq(m)].RMSE.std(),'aggregated_OOF_RMSE':mean_squared_error(q.y_true,q.y_pred)**.5,**{k:v for k,v in metric(q.y_true,q.y_pred).items() if k!='RMSE'}})
 sm=pd.DataFrame(summary).sort_values('fold_mean_RMSE');sm.to_csv(D['metrics']/'model_metrics.csv',index=False);base=fm[fm.model.eq('M0_CLIMATE')].set_index(['repeat','fold']);pairs=[]
 comps=[('M1_A1_ADDITIVE','M0_CLIMATE'),('M2_A1_INTERACTION','M1_A1_ADDITIVE'),('M3_E3_ADDITIVE','M0_CLIMATE'),('M4_E3_INTERACTION','M3_E3_ADDITIVE'),('M3_E3_ADDITIVE','M1_A1_ADDITIVE'),('M4_E3_INTERACTION','M2_A1_INTERACTION')]+[(m,'CHAMPION_V1') for m in ['M1_A1_ADDITIVE','M2_A1_INTERACTION','M3_E3_ADDITIVE','M4_E3_INTERACTION']]
 rng=np.random.default_rng(SEED);boot=[]
 for a,b in comps:
  A=fm[fm.model.eq(a)].set_index(['repeat','fold']);B=fm[fm.model.eq(b)].set_index(['repeat','fold']);d=A.RMSE-B.RMSE;ra=A.groupby('repeat').RMSE.mean()-B.groupby('repeat').RMSE.mean();ga=g[g.model.eq(a)].set_index(ID);gb=g[g.model.eq(b)].set_index(ID);loss=(ga.y_pred-ga.y_true)**2-(gb.y_pred-gb.y_true)**2
  for z in range(2000):ix=rng.integers(0,len(loss),len(loss));boot.append({'comparison':f'{a} vs {b}','bootstrap':z,'mean_squared_loss_delta':loss.iloc[ix].mean()})
  pairs.append({'candidate':a,'reference':b,'mean_fold_delta_RMSE':d.mean(),'median_fold_delta_RMSE':d.median(),'fold_win_rate':(d<0).mean(),'repetition_mean_delta':ra.mean(),'repetitions_improved':(ra<0).sum(),'parcel_mean_squared_loss_delta':loss.mean()})
 pair=pd.DataFrame(pairs);pair.to_csv(D['comparisons']/'paired_comparisons.csv',index=False);bb=pd.DataFrame(boot).groupby('comparison').mean_squared_loss_delta.agg(['mean',lambda x:x.quantile(.025),lambda x:x.quantile(.975)]).reset_index();bb.columns=['comparison','mean_delta','q025','q975'];bb.to_csv(D['comparisons']/'parcel_bootstrap_loss_differences.csv',index=False)
 # Segments, concentration, difficult diagnostics.
 support=pd.read_csv(ROOT/'outputs/modeling/family_1/support_analysis/support/difficult_parcel_support.csv');dif=set(support.loc[support.difficult_all_3,ID]);aty=set(support.loc[support.y_outlier_given_similar_X.fillna(False),ID]);seg=[];conc=[]
 for m,q in g.groupby('model'):
  q=q.copy();q['segment']=pd.qcut(q.y_true,[0,.25,.75,1],labels=['LOW','MID','HIGH']);q['decile']=pd.qcut(q.y_true,10,labels=[f'D{i}' for i in range(1,11)]);q['se']=(q.y_pred-q.y_true)**2
  for typ in ['segment','decile']:
   for z,x in q.groupby(typ,observed=True):seg.append({'model':m,'type':typ,'group':z,'n':len(x),'RMSE':np.sqrt(x.se.mean()),'MAE':np.mean(abs(x.y_pred-x.y_true)),'bias':np.mean(x.y_pred-x.y_true)})
  z=q.sort_values('se',ascending=False);conc.append({'model':m,'top10_SSE':z.head(int(np.ceil(len(z)*.1))).se.sum()/z.se.sum(),'difficult_SSE':q[q[ID].isin(dif)].se.sum()/q.se.sum(),'yatypical_SSE':q[q[ID].isin(aty)].se.sum()/q.se.sum(),'difficult_MAE':np.mean(abs(q.loc[q[ID].isin(dif),'y_pred']-q.loc[q[ID].isin(dif),'y_true'])),'yatypical_MAE':np.mean(abs(q.loc[q[ID].isin(aty),'y_pred']-q.loc[q[ID].isin(aty),'y_true']))})
 pd.DataFrame(seg).to_csv(D['errors']/'segment_decile_errors.csv',index=False);pd.DataFrame(conc).to_csv(D['errors']/'error_concentration.csv',index=False);p.to_parquet(D['predictions']/'oof_predictions_with_champion.parquet',index=False);coef=pd.read_csv(D['coefficients']/'ridge_coefficients_by_fold.csv');cs=coef.groupby(['model','term']).coefficient.agg(['mean','std',lambda x:(np.sign(x)==np.sign(x.mean())).mean()]).reset_index();cs.columns=['model','term','mean_coefficient','std_coefficient','sign_stability'];cs.to_csv(D['coefficients']/'coefficient_stability.csv',index=False);figures(sm,pair,pd.DataFrame(seg),pd.DataFrame(conc));report(sm,pair,bb,pd.DataFrame(seg),pd.DataFrame(conc),cs);return sm
def figures(sm,pair,seg,conc):
 plt.figure(figsize=(9,4));sns.barplot(sm,x='model',y='fold_mean_RMSE');plt.xticks(rotation=30,ha='right');plt.tight_layout();plt.savefig(D['figures']/'01_model_rmse.png',dpi=180);plt.close();plt.figure(figsize=(9,4));sns.barplot(pair,x='candidate',y='mean_fold_delta_RMSE',hue='reference');plt.axhline(0,color='black');plt.xticks(rotation=30,ha='right');plt.tight_layout();plt.savefig(D['figures']/'02_paired_deltas.png',dpi=180);plt.close();q=seg[(seg.type=='segment')&seg.model.str.startswith('M')];plt.figure(figsize=(9,4));sns.barplot(q,x='group',y='RMSE',hue='model');plt.tight_layout();plt.savefig(D['figures']/'03_segment_rmse.png',dpi=180);plt.close();plt.figure(figsize=(9,4));sns.barplot(conc,x='model',y='top10_SSE');plt.xticks(rotation=30,ha='right');plt.tight_layout();plt.savefig(D['figures']/'04_sse_concentration.png',dpi=180);plt.close()
def report(sm,pair,boot,seg,conc,cs):
 x=sm.set_index('model');P=pair.set_index(['candidate','reference'])
 def g(a,b):return P.loc[(a,b)]
 m1=g('M1_A1_ADDITIVE','M0_CLIMATE');m2=g('M2_A1_INTERACTION','M1_A1_ADDITIVE');m3=g('M3_E3_ADDITIVE','M0_CLIMATE');m4=g('M4_E3_INTERACTION','M3_E3_ADDITIVE');best=sm.iloc[0];inter=cs[cs.model.str.contains('INTERACTION')&cs.term.str.contains('CLIMATE_')&cs.term.str.contains('_F')].sort_values('sign_stability',ascending=False).head(12)
 txt=f'''# F3.2 — Structural Climate Conditioning\n\n## Protocolo\nMismos 50 outer folds (5×10), inner 4-fold. Climate TOP20 ENET se reconstruyó por fold con parámetros congelados. Los correctores usaron residuos climáticos cross-fitted; PCA, imputación, escalamiento, balanceo y Ridge se ajustaron dentro de train. Interacciones predefinidas: 4 moderadores × 3 factores = 12 productos, con efectos principales. Sin PREDICTION, GMM expertos ni tuning climático.\n\n## Resultados comparables\n```\n{sm.round(4).to_string(index=False)}\n```\n\nFold RMSE y aggregated OOF RMSE se reportan por separado. Champion congelado: fold={x.loc['CHAMPION_V1','fold_mean_RMSE']:.4f}, agregado={x.loc['CHAMPION_V1','aggregated_OOF_RMSE']:.4f}.\n\n## Hipótesis\n- **M1 vs M0, aditivo A1:** Δfold={m1.mean_fold_delta_RMSE:+.4f}, wins={m1.fold_win_rate:.0%}, repeticiones={int(m1.repetitions_improved)}/10.\n- **M2 vs M1, interacción A1:** Δfold={m2.mean_fold_delta_RMSE:+.4f}, wins={m2.fold_win_rate:.0%}, repeticiones={int(m2.repetitions_improved)}/10.\n- **M3 vs M0, aditivo E3:** Δfold={m3.mean_fold_delta_RMSE:+.4f}, wins={m3.fold_win_rate:.0%}, repeticiones={int(m3.repetitions_improved)}/10.\n- **M4 vs M3, interacción E3:** Δfold={m4.mean_fold_delta_RMSE:+.4f}, wins={m4.fold_win_rate:.0%}, repeticiones={int(m4.repetitions_improved)}/10.\n- **E3 vs A1:** aditivo Δ={g('M3_E3_ADDITIVE','M1_A1_ADDITIVE').mean_fold_delta_RMSE:+.4f}; interacción Δ={g('M4_E3_INTERACTION','M2_A1_INTERACTION').mean_fold_delta_RMSE:+.4f}.\n\n## Interacciones\nMayor estabilidad de signo: {inter[['model','term','mean_coefficient','sign_stability']].round(3).to_dict('records')}. Coeficientes regularizados son asociaciones, no efectos causales. Evidencia H2 requiere mejora frente al aditivo, no sólo frente a M0.\n\n## Errores\nSegmentos: {seg[(seg.type=='segment')].round(3).to_dict('records')}. Concentración: {conc.round(3).to_dict('records')}. Bootstrap por parcelas de diferencias de pérdida: {boot.round(4).to_dict('records')}; no trata folds como iid.\n\n## Respuestas\n1. Estructura añade información sólo si M1/M3 muestran delta negativo consistente.\n2. Interacción existe predictivamente sólo si M2<M1 o M4<M3 de forma repetida.\n3. A1 vs E3 queda cuantificado bajo arquitecturas idénticas.\n4. La estabilidad de términos está en `coefficient_stability.csv`; no interpretar términos aislados sin ganancia OOF.\n5. Calibración, rango, extremos y SSE están en tablas anteriores.\n6. Mejor resultado={best.model}; fold RMSE={best.fold_mean_RMSE:.4f}. Competencia con Champion requiere delta robusto, no empate accidental.\n7. Mixture-of-experts sólo se justifica si la interacción gana claramente al aditivo; de lo contrario, no avanzar.\n\n## Decisión\n{'Existe señal para revisar el experimento mínimo de memberships, sin ejecutarlo todavía.' if (m2.mean_fold_delta_RMSE<-.0015 and m2.repetitions_improved>=8) or (m4.mean_fold_delta_RMSE<-.0015 and m4.repetitions_improved>=8) else 'No hay evidencia suficiente para mixture-of-experts; conservar la mejor arquitectura simple y detener expansión.'}\n''';(D['report']/'f3_2_structural_climate_conditioning_report.md').write_text(txt,encoding='utf-8')
def main():p,f=run();analyze(p,f);print('F3.2 complete',flush=True)
def finalize_existing():
 p=pd.read_parquet(D['predictions']/'oof_predictions.parquet');f=pd.read_csv(D['folds']/'fold_metrics.csv');analyze(p,f);print('F3.2 finalized from frozen OOF',flush=True)
if __name__=='__main__':main()
