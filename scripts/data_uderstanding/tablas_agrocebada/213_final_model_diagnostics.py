"""RS7: diagnóstico final del campeón usando exclusivamente predicciones OOF congeladas."""
from pathlib import Path
import sys,json,warnings
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
import numpy as np,pandas as pd
import matplotlib.pyplot as plt,seaborn as sns
from scipy.stats import pearsonr,spearmanr,kendalltau
from sklearn.metrics import mean_squared_error,mean_absolute_error,median_absolute_error,r2_score,explained_variance_score
from sklearn.isotonic import IsotonicRegression
from sklearn.preprocessing import SplineTransformer
from sklearn.linear_model import Ridge
from statsmodels.nonparametric.smoothers_lowess import lowess
from family_1.stage4_modeling import load_xy,save_splits,ID,SEED,FEATURE_DIR
warnings.filterwarnings('ignore');sns.set_theme(style='whitegrid')
BASE=ROOT/'outputs/modeling/final_diagnostics/rs7';D={x:BASE/x for x in ['metrics','calibration','ranking','errors','uncertainty','segments','diagnostics','ensemble','figures','report']}
for p in D.values():p.mkdir(parents=True,exist_ok=True)
NBOOT=1000;NAMES={'M0_MEAN':'Mean baseline','M1_CLIMATE':'Climate TOP20 ENET','M2_CLIMATE_HISTORY':'Climate + History','M3_CHAMPION':'Champion','M4_PRECIP_HISTORY':'Precipitation + History'}
def ccc(y,p):
 return 2*np.cov(y,p,ddof=1)[0,1]/(np.var(y,ddof=1)+np.var(p,ddof=1)+(np.mean(y)-np.mean(p))**2)
def load_predictions(ids,y):
 r4=pd.read_parquet(ROOT/'outputs/modeling/residual_signal_audit/stage4_champion_reconstruction/predictions/oof_predictions.parquet');r6=pd.read_parquet(ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization/predictions/oof_predictions.parquet');maps={'M1_CLIMATE':'TOP20_ENET_BASE','M2_CLIMATE_HISTORY':'TOP20_ENET_HISTORY15','M4_PRECIP_HISTORY':'PRECIPITATION_XGB_HISTORY15'};parts=[]
 for name,pipe in maps.items():
  q=r4[r4.pipeline.eq(pipe)][[ID,'repeat','fold','y_true','y_pred']].copy();q['model']=name;parts.append(q)
 q=r6[r6.architecture.eq('A_CURRENT_CH_H_T')][[ID,'repeat','fold','y_true','y_pred']].copy();q['model']='M3_CHAMPION';parts.append(q)
 splits=save_splits(ids);pos={v:i for i,v in enumerate(ids)};rows=[]
 for _,s in splits.iterrows():
  tr=np.array([pos[v] for v in json.loads(s.train_ID_POLIGONO)]);va=np.array([pos[v] for v in json.loads(s.validation_ID_POLIGONO)]);mu=y.iloc[tr].mean()
  for ix in va:rows.append({ID:ids.iloc[ix],'repeat':int(s['repeat']),'fold':int(s['fold']),'y_true':y.iloc[ix],'y_pred':mu,'model':'M0_MEAN'})
 parts.append(pd.DataFrame(rows));return pd.concat(parts,ignore_index=True)
def aggregate(oof):
 g=oof.groupby(['model',ID]).agg(y_true=('y_true','first'),yhat_mean=('y_pred','mean'),yhat_sd=('y_pred','std'),yhat_min=('y_pred','min'),yhat_max=('y_pred','max'),yhat_iqr=('y_pred',lambda x:x.quantile(.75)-x.quantile(.25))).reset_index();g['yhat_range']=g.yhat_max-g.yhat_min;g['yhat_cv']=g.yhat_sd/g.yhat_mean.abs().where(g.yhat_mean.abs()>1e-8);g['residual']=g.yhat_mean-g.y_true;g['abs_error']=abs(g.residual);g['squared_error']=g.residual**2;return g
def summaries(oof,g):
 sy=g[g.model.eq('M3_CHAMPION')].y_true.std();yr=g[g.model.eq('M3_CHAMPION')].y_true.max()-g[g.model.eq('M3_CHAMPION')].y_true.min();mean_rmse=np.sqrt(np.mean((g[g.model.eq('M0_MEAN')].y_true-g[g.model.eq('M0_MEAN')].yhat_mean)**2));rows=[];cal=[];shr=[];rank=[]
 for m,q in g.groupby('model'):
  y=q.y_true.to_numpy();p=q.yhat_mean.to_numpy();rm=np.sqrt(np.mean((p-y)**2));beta,alpha=np.polyfit(y,p,1);b2,a2=np.polyfit(p,y,1);rows.append({'model':m,'label':NAMES[m],'RMSE':rm,'MAE':mean_absolute_error(y,p),'MedAE':median_absolute_error(y,p),'MSE':mean_squared_error(y,p),'bias':np.mean(p-y),'residual_sd':np.std(p-y,ddof=1),'NRMSE_SD':rm/sy,'NRMSE_RANGE':rm/yr,'MAE_over_SD_y':mean_absolute_error(y,p)/sy,'relative_RMSE_reduction_vs_mean':1-rm/mean_rmse,'R2_global':r2_score(y,p),'explained_variance':explained_variance_score(y,p),'pearson':pearsonr(y,p).statistic,'spearman':spearmanr(y,p).statistic,'kendall_tau':kendalltau(y,p).statistic,'CCC':ccc(y,p),'prediction_sd_ratio':np.std(p,ddof=1)/sy})
  cal.append({'model':m,'pred_on_true_intercept_alpha':alpha,'pred_on_true_slope_beta':beta,'pred_on_true_R2':r2_score(p,alpha+beta*y),'true_on_pred_intercept_a':a2,'true_on_pred_slope_b':b2,'ideal_slope':1.0});shr.append({'model':m,'shrinkage_ratio_sd_pred_over_sd_y':np.std(p,ddof=1)/sy,'range_ratio_pred_over_y':np.ptp(p)/np.ptp(y),'sd_y':sy,'sd_pred':np.std(p,ddof=1),'range_y':np.ptp(y),'range_pred':np.ptp(p)});rank.append({'model':m,'pearson':pearsonr(y,p).statistic,'spearman':spearmanr(y,p).statistic,'kendall_tau':kendalltau(y,p).statistic,'CCC':ccc(y,p)})
 sm=pd.DataFrame(rows).sort_values('RMSE');caldf=pd.DataFrame(cal);sm=sm.merge(caldf[['model','pred_on_true_slope_beta']],on='model',how='left').rename(columns={'pred_on_true_slope_beta':'calibration_slope_pred_on_true'});sm.to_csv(D['metrics']/'model_value_summary.csv',index=False);caldf.to_csv(D['calibration']/'calibration_summary.csv',index=False);pd.DataFrame(shr).to_csv(D['calibration']/'shrinkage_summary.csv',index=False);pd.DataFrame(rank).to_csv(D['ranking']/'ranking_metrics.csv',index=False)
 # fold R2 and repeated full-OOF metrics
 fr=[]
 for (m,r,f),q in oof.groupby(['model','repeat','fold']):fr.append({'model':m,'repeat':r,'fold':f,'R2':r2_score(q.y_true,q.y_pred)})
 fr=pd.DataFrame(fr);fr['R2_gt_0']=fr.R2>0;fr['R2_gt_025']=fr.R2>.25;fr['R2_gt_050']=fr.R2>.5;fr.to_csv(D['metrics']/'r2_by_fold.csv',index=False);fr.groupby('model').agg(median_fold_R2=('R2','median'),min_fold_R2=('R2','min'),max_fold_R2=('R2','max'),proportion_R2_gt_0=('R2_gt_0','mean'),proportion_R2_gt_025=('R2_gt_025','mean'),proportion_R2_gt_050=('R2_gt_050','mean')).reset_index().to_csv(D['metrics']/'r2_fold_summary.csv',index=False)
 rr=[]
 for (m,r),q in oof.groupby(['model','repeat']):rr.append({'model':m,'repeat':r,'RMSE':mean_squared_error(q.y_true,q.y_pred)**.5,'MAE':mean_absolute_error(q.y_true,q.y_pred),'R2':r2_score(q.y_true,q.y_pred)})
 rr=pd.DataFrame(rr);rep=rr.groupby('model').RMSE.agg(['mean','std','min','max',lambda x:x.quantile(.025),lambda x:x.quantile(.975)]).reset_index();rep.columns=['model','mean_RMSE','std_RMSE','min_RMSE','max_RMSE','empirical_q025','empirical_q975'];rep.to_csv(D['metrics']/'repeated_cv_summary.csv',index=False);rw=rr.pivot(index='repeat',columns='model',values='RMSE');pd.DataFrame({'comparison':['Champion minus Climate','Champion minus Climate+History'],'mean_paired_delta_RMSE':[(rw.M3_CHAMPION-rw.M1_CLIMATE).mean(),(rw.M3_CHAMPION-rw.M2_CLIMATE_HISTORY).mean()],'min_delta':[(rw.M3_CHAMPION-rw.M1_CLIMATE).min(),(rw.M3_CHAMPION-rw.M2_CLIMATE_HISTORY).min()],'max_delta':[(rw.M3_CHAMPION-rw.M1_CLIMATE).max(),(rw.M3_CHAMPION-rw.M2_CLIMATE_HISTORY).max()],'proportion_champion_better':[(rw.M3_CHAMPION<rw.M1_CLIMATE).mean(),(rw.M3_CHAMPION<rw.M2_CLIMATE_HISTORY).mean()]}).to_csv(D['metrics']/'paired_repetition_deltas.csv',index=False);sm[['model','RMSE','relative_RMSE_reduction_vs_mean','R2_global']].to_csv(D['metrics']/'relative_improvement.csv',index=False);return sm,fr,rr
def error_tables(g):
 dec=[];curve=[];rvp=[];conc=[];ext=[];unc=[]
 for m,q in g.groupby('model'):
  q=q.copy();q['decile']=pd.qcut(q.y_true,10,labels=[f'D{i}' for i in range(1,11)],duplicates='drop');q['uncertainty_quartile']=pd.qcut(q.yhat_sd,4,labels=['Q1','Q2','Q3','Q4'],duplicates='drop')
  for z,x in q.groupby('decile',observed=True):dec.append({'model':m,'decile':z,'n':len(x),'mean_y':x.y_true.mean(),'mean_yhat':x.yhat_mean.mean(),'bias':x.residual.mean(),'RMSE':np.sqrt(x.squared_error.mean()),'MAE':x.abs_error.mean(),'MedAE':x.abs_error.median()})
  for _,x in q.iterrows():curve.append({'model':m,ID:x[ID],'y_true':x.y_true,'yhat':x.yhat_mean,'residual_pred_minus_true':x.residual,'abs_residual':x.abs_error,'squared_residual':x.squared_error}) ;rvp.append({'model':m,ID:x[ID],'yhat':x.yhat_mean,'residual':x.residual,'abs_residual':x.abs_error})
  z=q.sort_values('squared_error',ascending=False);tot=z.squared_error.sum()
  for pct in [.05,.10,.20,.25]:conc.append({'model':m,'top_fraction':pct,'n_parcels':max(1,int(np.ceil(len(z)*pct))),'SSE_fraction':z.head(max(1,int(np.ceil(len(z)*pct)))).squared_error.sum()/tot})
  for label,mask in [('exclude_lowest_5pct',q.y_true>q.y_true.quantile(.05)),('exclude_highest_5pct',q.y_true<q.y_true.quantile(.95)),('exclude_both_5pct',q.y_true.between(q.y_true.quantile(.05),q.y_true.quantile(.95))),('exclude_top10pct_abs_error',q.abs_error<=q.abs_error.quantile(.90))]:ext.append({'model':m,'scenario':label,'n':mask.sum(),'RMSE':np.sqrt(q.loc[mask,'squared_error'].mean())})
  for z,x in q.groupby('uncertainty_quartile',observed=True):unc.append({'model':m,'uncertainty_quartile':z,'n':len(x),'mean_prediction_sd':x.yhat_sd.mean(),'RMSE':np.sqrt(x.squared_error.mean()),'MAE':x.abs_error.mean()})
 pd.DataFrame(dec).to_csv(D['errors']/'error_by_yield_decile.csv',index=False);pd.DataFrame(curve).to_csv(D['errors']/'residual_vs_yield.csv',index=False);pd.DataFrame(rvp).to_csv(D['errors']/'residual_vs_prediction.csv',index=False);pd.DataFrame(conc).to_csv(D['errors']/'error_concentration.csv',index=False);pd.DataFrame(ext).to_csv(D['errors']/'extreme_sensitivity.csv',index=False);pd.DataFrame(unc).to_csv(D['uncertainty']/'uncertainty_error_relationship.csv',index=False)
 return pd.DataFrame(dec),pd.DataFrame(conc),pd.DataFrame(unc)
def stability_segments(ids,g):
 champ=g[g.model.eq('M3_CHAMPION')].copy();support=pd.read_csv(ROOT/'outputs/modeling/family_1/support_analysis/support/difficult_parcel_support.csv').set_index(ID).reindex(ids);T=pd.read_parquet(FEATURE_DIR/'topography_basic_features.parquet').set_index(ID).reindex(ids);H=pd.read_parquet(FEATURE_DIR/'history_features.parquet').set_index(ID).reindex(ids);reg=pd.read_parquet(ROOT/'outputs/modeling/family_1/climate_regimes/stage1_discovery/memberships/climate_regime_memberships.parquet').set_index(ID).reindex(ids);aux=pd.DataFrame({ID:ids,'AREA_HA':support.AREA_HA.values,'precipitation_total':support.precipitation_total.values,'slope_mean':support.slope_mean.values,'relief':T.TOPO_BASIC_elevation_relief.values,'historical_vigor':H.HIST_S2_ndvi_promedio_mean.values,'historical_variability':H.HIST_S2_ndvi_promedio_std.values,'regime':reg.regime_hard.values,'difficult':support.difficult_all_3.values,'y_atypical':support.y_outlier_given_similar_X.values});c=champ.merge(aux,on=ID);c['prediction_sd_abs_error_pearson']=pearsonr(c.yhat_sd,c.abs_error).statistic;c['prediction_sd_abs_error_spearman']=spearmanr(c.yhat_sd,c.abs_error).statistic;c.to_csv(D['uncertainty']/'oof_prediction_stability.csv',index=False)
 rows=[]
 for variable in ['regime','slope_mean','relief','historical_vigor','historical_variability']:
  c['bin']=c[variable] if variable=='regime' else pd.qcut(c[variable],4,duplicates='drop')
  for z,x in c.groupby('bin',observed=True):
   beta=np.polyfit(x.y_true,x.yhat_mean,1)[0] if len(x)>2 else np.nan;rows.append({'variable':variable,'segment':str(z),'n':len(x),'RMSE':np.sqrt(x.squared_error.mean()),'MAE':x.abs_error.mean(),'bias':x.residual.mean(),'R2':r2_score(x.y_true,x.yhat_mean) if len(x)>2 else np.nan,'calibration_slope':beta})
 z=pd.DataFrame(rows);z[z.variable.eq('regime')].to_csv(D['segments']/'climate_regime_performance.csv',index=False);z[z.variable.isin(['slope_mean','relief'])].to_csv(D['segments']/'topography_segment_performance.csv',index=False);z[z.variable.str.startswith('historical')].to_csv(D['segments']/'history_segment_performance.csv',index=False)
 rel=[]
 for variable in ['yhat_mean','y_true','AREA_HA','precipitation_total','slope_mean','historical_vigor','yhat_sd']:
  q=c[[variable,'abs_error']].dropna();rel.append({'variable':variable,'n':len(q),'pearson_abs_error':pearsonr(q[variable],q.abs_error).statistic,'spearman_abs_error':spearmanr(q[variable],q.abs_error).statistic})
 pd.DataFrame(rel).to_csv(D['diagnostics']/'heteroscedasticity_relationships.csv',index=False)
 c['difficult']=c['difficult'].fillna(False).astype(bool);c['y_atypical']=c['y_atypical'].fillna(False).astype(bool);c['yield_decile']=pd.qcut(c.y_true,10,labels=[f'D{i}' for i in range(1,11)]);c['status']=np.select([c.difficult&c.abs_error.gt(c.abs_error.quantile(.75)),c.difficult&c.abs_error.le(c.abs_error.quantile(.5)),c.difficult&c.yhat_sd.gt(c.yhat_sd.quantile(.75)),c.difficult&((c.yield_decile=='D1')|(c.yield_decile=='D10'))],['persistent difficult','substantially improved','unstable prediction','extreme-y driven'],default='other');c[c.difficult].to_csv(D['diagnostics']/'difficult_parcels_final.csv',index=False);c[c.y_atypical].to_csv(D['diagnostics']/'yatypical_final.csv',index=False);return c
def ranking_bootstrap(g):
 rows=[]
 for m,q in g.groupby('model'):
  n=len(q)
  for frac in [.10,.20,.25]:
   k=int(np.ceil(n*frac))
   for side in ['top','bottom']:
    t=set(q.nlargest(k,'y_true')[ID] if side=='top' else q.nsmallest(k,'y_true')[ID]);p=set(q.nlargest(k,'yhat_mean')[ID] if side=='top' else q.nsmallest(k,'yhat_mean')[ID]);inter=len(t&p);rows.append({'model':m,'side':side,'fraction':frac,'k':k,'precision':inter/len(p),'recall':inter/len(t),'overlap':inter,'jaccard':inter/len(t|p)})
 pd.DataFrame(rows).to_csv(D['ranking']/'top_bottom_quantile_overlap.csv',index=False)
 rng=np.random.default_rng(SEED);br=[]
 for m,q in g.groupby('model'):
  y=q.y_true.to_numpy();p=q.yhat_mean.to_numpy()
  for b in range(NBOOT):
   ix=rng.integers(0,len(q),len(q));yy=y[ix];pp=p[ix];br.append({'model':m,'bootstrap':b,'RMSE':np.sqrt(np.mean((pp-yy)**2)),'MAE':np.mean(abs(pp-yy)),'R2':r2_score(yy,pp),'Spearman':spearmanr(yy,pp).statistic})
 pd.DataFrame(br).groupby('model').agg(['mean',lambda x:x.quantile(.025),lambda x:x.quantile(.975)]).to_csv(D['metrics']/'bootstrap_parcel_diagnostic.csv')
def opportunities(g):
 champ=g[g.model.eq('M3_CHAMPION')];y=champ.y_true.to_numpy();p=champ.yhat_mean.to_numpy();rows=[];beta,alpha=np.polyfit(p,y,1);pl=alpha+beta*p;rows.append({'candidate':'linear','apparent_RMSE_same_data':np.sqrt(np.mean((pl-y)**2)),'validation_status':'OPTIMISTIC descriptive only; requires nested calibration'});pi=IsotonicRegression(out_of_bounds='clip').fit_transform(p,y);rows.append({'candidate':'isotonic','apparent_RMSE_same_data':np.sqrt(np.mean((pi-y)**2)),'validation_status':'OPTIMISTIC descriptive only; requires nested calibration'});S=SplineTransformer(n_knots=4,degree=2).fit_transform(p.reshape(-1,1));ps=Ridge(alpha=1).fit(S,y).predict(S);rows.append({'candidate':'low_flex_spline','apparent_RMSE_same_data':np.sqrt(np.mean((ps-y)**2)),'validation_status':'OPTIMISTIC descriptive only; requires nested calibration'});pd.DataFrame(rows).to_csv(D['calibration']/'calibration_opportunity.csv',index=False)
 # Ensemble diversity only, no weights.
 wide=g.pivot(index=ID,columns='model',values='residual');rc=wide.corr();rc.to_csv(D['ensemble']/'final_model_residual_correlations.csv');op=[]
 for i,a in enumerate(rc):
  for b in rc.columns[i+1:]:op.append({'model_a':a,'model_b':b,'residual_correlation':rc.loc[a,b],'diversification_potential':'some' if rc.loc[a,b]<.95 else 'low','status':'no weights optimized'})
 pd.DataFrame(op).to_csv(D['ensemble']/'ensemble_opportunity.csv',index=False)
def figures(g,dec,conc,stab,sm):
 c=g[g.model.eq('M3_CHAMPION')];
 plt.figure(figsize=(6,5));sns.scatterplot(c,x='y_true',y='yhat_mean');lo=min(c.y_true.min(),c.yhat_mean.min());hi=max(c.y_true.max(),c.yhat_mean.max());plt.plot([lo,hi],[lo,hi],'k--');plt.tight_layout();plt.savefig(D['figures']/'true_vs_predicted.png',dpi=180);plt.close()
 beta,alpha=np.polyfit(c.y_true,c.yhat_mean,1);plt.figure(figsize=(6,5));plt.scatter(c.y_true,c.yhat_mean);xx=np.linspace(lo,hi);plt.plot(xx,xx,'k--');plt.plot(xx,alpha+beta*xx,'r-');plt.tight_layout();plt.savefig(D['figures']/'calibration_plot.png',dpi=180);plt.close()
 for fn,x in [('residual_vs_true.png','y_true'),('residual_vs_predicted.png','yhat_mean')]:
  plt.figure(figsize=(6,4));plt.scatter(c[x],c.residual);z=lowess(c.residual,c[x],frac=.4);plt.plot(z[:,0],z[:,1],'r-');plt.axhline(0,color='black');plt.tight_layout();plt.savefig(D['figures']/fn,dpi=180);plt.close()
 q=dec[dec.model.eq('M3_CHAMPION')];plt.figure(figsize=(8,4));sns.barplot(q,x='decile',y='RMSE');plt.tight_layout();plt.savefig(D['figures']/'error_by_yield_decile.png',dpi=180);plt.close();plt.figure(figsize=(6,4));sns.scatterplot(stab,x='yhat_sd',y='abs_error');plt.tight_layout();plt.savefig(D['figures']/'prediction_stability_vs_error.png',dpi=180);plt.close();plt.figure(figsize=(9,4));sns.barplot(sm,x='model',y='RMSE');plt.xticks(rotation=25);plt.tight_layout();plt.savefig(D['figures']/'stagewise_model_value.png',dpi=180);plt.close();q=conc[conc.model.eq('M3_CHAMPION')];plt.figure(figsize=(6,4));plt.plot(q.top_fraction,q.SSE_fraction,marker='o');plt.tight_layout();plt.savefig(D['figures']/'error_concentration.png',dpi=180);plt.close()
def report(sm,fr,rr,dec,conc,unc,stab):
 x=sm.set_index('model');c=x.loc['M3_CHAMPION'];cl=x.loc['M1_CLIMATE'];h=x.loc['M2_CLIMATE_HISTORY'];rank=pd.read_csv(D['ranking']/'top_bottom_quantile_overlap.csv');cal=pd.read_csv(D['calibration']/'calibration_summary.csv').set_index('model');shr=pd.read_csv(D['calibration']/'shrinkage_summary.csv').set_index('model');opp=pd.read_csv(D['calibration']/'calibration_opportunity.csv');ens=pd.read_csv(D['ensemble']/'ensemble_opportunity.csv');d=dec[dec.model.eq('M3_CHAMPION')];co=conc[conc.model.eq('M3_CHAMPION')];sd_p=stab.prediction_sd_abs_error_pearson.iloc[0];sd_s=stab.prediction_sd_abs_error_spearman.iloc[0];cf=fr[fr.model.eq('M3_CHAMPION')];pdeltas=pd.read_csv(D['metrics']/'paired_repetition_deltas.csv');total_sse=stab.squared_error.sum();dif=stab[stab.difficult];aty=stab[stab.y_atypical];dif_sse=dif.squared_error.sum()/total_sse if len(dif) else np.nan;aty_sse=aty.squared_error.sum()/total_sse if len(aty) else np.nan;middle=d[d.decile.isin(['D5','D6'])].RMSE.mean();extreme=d[d.decile.isin(['D1','D10'])].RMSE.mean();bott=[]
 if cal.loc['M3_CHAMPION','pred_on_true_slope_beta']<.8:bott.append('CALIBRATION-LIMITED')
 if d.iloc[[0,-1]].RMSE.mean()>d.iloc[3:7].RMSE.mean()*1.25:bott.append('EXTREME-LIMITED')
 if co[co.top_fraction.eq(.10)].SSE_fraction.iloc[0]>.35:bott.append('OUTLIER-LIMITED')
 if abs(sd_s)>.2:bott.append('VARIANCE-LIMITED')
 if c.spearman<.8:bott.append('INFORMATION-LIMITED')
 pd.DataFrame([{'classification':z,'evidence':'rule-based descriptive RS7 classification'} for z in bott]).to_csv(D['diagnostics']/'bottleneck_classification.csv',index=False);next_exp=['Nested linear calibration / variance expansion','Extreme-aware loss or sample weighting'][:2]
 txt=f'''# RS7 — Final Model Diagnostics & Improvement Direction

## Controles
Sólo predicciones OOF congeladas. Métricas globales usan el promedio de 10 OOF por parcela; métricas de folds/repeticiones conservan su nivel original. Las curvas de calibración candidatas son apparent/in-sample sobre OOF agregadas y NO constituyen performance válida. No se recalibró, reentrenó, promedió ni predijo PREDICTION.

## Respuestas
1–2. **R² global / variabilidad explicada:** {c.R2_global:.3f} / {c.explained_variance:.3f}.
3–4. **MAE / MedAE:** {c.MAE:.3f} / {c.MedAE:.3f} t/ha.
5. **RMSE respecto a SD(y):** {c.NRMSE_SD:.3f}; RMSE={c.RMSE:.3f}, SD(y)={c.RMSE/c.NRMSE_SD:.3f}.
6. **Reducción vs mean:** {c.relative_RMSE_reduction_vs_mean:.1%}.
7–9. **Pearson/Spearman/CCC:** {c.pearson:.3f}/{c.spearman:.3f}/{c.CCC:.3f}.
10. **Ranking:** cuantiles={rank[rank.model.eq('M3_CHAMPION')].round(3).to_dict('records')}.
11. **Calibration slope pred~true:** {cal.loc['M3_CHAMPION','pred_on_true_slope_beta']:.3f}.
12–13. **Shrinkage/rango:** SD ratio={shr.loc['M3_CHAMPION','shrinkage_ratio_sd_pred_over_sd_y']:.3f}; range ratio={shr.loc['M3_CHAMPION','range_ratio_pred_over_y']:.3f}.
14–16. **Error por decil:** {d[['decile','RMSE','bias']].round(3).to_dict('records')}; más difícil={d.loc[d.RMSE.idxmax(),'decile']}. Los extremos promedian RMSE={extreme:.3f} frente a {middle:.3f} en D5–D6: hay error dependiente del régimen del target, pero no una U suave porque D4 también es anómalamente difícil. Low es más difícil que High.
17. **Concentración SSE:** {co[['top_fraction','SSE_fraction']].round(3).to_dict('records')}.
18. **Difficult parcels:** {len(dif)} parcelas aportan {dif_sse:.1%} del SSE; por tanto {'sí siguen dominando' if dif_sse>.5 else 'no concentran por sí solas la mayoría'}.
19. **y-atypical:** {len(aty)} parcelas aportan {aty_sse:.1%} del SSE; siguen siendo {'desproporcionadamente problemáticas' if aty_sse>len(aty)/len(stab)*1.5 else 'proporcionales a su frecuencia'}.
20–21. **Prediction SD vs error:** Pearson={sd_p:.3f}, Spearman={sd_s:.3f}; {'proxy útil moderado' if abs(sd_s)>.2 else 'proxy débil'}.
22. **Top/bottom:** ver métricas de overlap/Jaccard en punto 10.
23. **Valor History:** RMSE {cl.RMSE:.3f}→{h.RMSE:.3f}; R² {cl.R2_global:.3f}→{h.R2_global:.3f}; slope {cal.loc['M1_CLIMATE','pred_on_true_slope_beta']:.3f}→{cal.loc['M2_CLIMATE_HISTORY','pred_on_true_slope_beta']:.3f}.
24–26. **Valor Topography:** RMSE {h.RMSE:.3f}→{c.RMSE:.3f}; MAE {h.MAE:.3f}→{c.MAE:.3f}; R² {h.R2_global:.3f}→{c.R2_global:.3f}; slope {cal.loc['M2_CLIMATE_HISTORY','pred_on_true_slope_beta']:.3f}→{cal.loc['M3_CHAMPION','pred_on_true_slope_beta']:.3f}. Mejora pequeña: gana en RMSE/R²/calibración, pero no en MAE. Comparación pareada por repetición: {pdeltas.round(4).to_dict('records')}; no es una superioridad amplia.
27. **Margen calibración:** {opp.round(3).to_dict('records')}; sólo justifica una prueba nested.
28. **Extreme-aware:** {'sí' if 'EXTREME-LIMITED' in bott else 'prioridad baja'}.
29. **Model averaging:** correlaciones={ens.round(3).to_dict('records')}; no optimizado.
30–31. **Cuello de botella:** {bott}.
32. **Máximo dos experimentos:** {next_exp}.
33. **Evaluación global:** el campeón explica ~{c.R2_global:.0%} de la variación OOF agregada y reduce RMSE {c.relative_RMSE_reduction_vs_mean:.0%} vs media; ranking útil, pero con compresión y dificultad en extremos. R² por fold: mediana={cf.R2.median():.3f}, {cf.R2_gt_0.mean():.0%}>0, {cf.R2_gt_025.mean():.0%}>0.25 y {cf.R2_gt_050.mean():.0%}>0.50. No se entrenó modelo final.
''';(D['report']/'final_model_diagnostics_report.md').write_text(txt,encoding='utf-8')
def main():
 ids,X,y=load_xy();ids=ids.reset_index(drop=True);y=y.reset_index(drop=True);oof=load_predictions(ids,y);g=aggregate(oof);sm,fr,rr=summaries(oof,g);dec,conc,unc=error_tables(g);stab=stability_segments(ids,g);ranking_bootstrap(g);opportunities(g);figures(g,dec,conc,stab,sm);report(sm,fr,rr,dec,conc,unc,stab);print(f"RS7 complete: champion aggregated RMSE={sm.set_index('model').loc['M3_CHAMPION','RMSE']:.4f}",flush=True)
if __name__=='__main__':main()
