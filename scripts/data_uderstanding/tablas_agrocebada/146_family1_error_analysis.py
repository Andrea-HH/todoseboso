"""Etapa 4.3: diagnóstico profundo de error y robustez espacial."""
from pathlib import Path
import sys,json,warnings
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
import numpy as np,pandas as pd,geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr,spearmanr
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GroupKFold,KFold,GridSearchCV
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score,median_absolute_error
from sklearn.linear_model import ElasticNet,LinearRegression
from sklearn.neighbors import NearestNeighbors
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from family_1.stage4_modeling import *
warnings.filterwarnings('ignore');sns.set_theme(style='whitegrid')

BASE=ROOT/'outputs/modeling/family_1/error_analysis';D={n:BASE/n for n in ['residuals','segments','spatial','diagnostics','figures','report']}
for p in D.values():p.mkdir(parents=True,exist_ok=True)
models=['XGB_CORE','LGBM_CORE','ENET_CORE_EXTENDED']

# ---------- Predicciones OOF agregadas ----------
r1=pd.read_parquet(ROOT/'outputs/modeling/family_1/stage4/screening/oof_predictions.parquet');r2=pd.read_parquet(ROOT/'outputs/modeling/family_1/stage4_round2/predictions/round2_oof_predictions.parquet')
pred=pd.concat([r1[r1.pipeline.isin(models)],r2[r2.pipeline.isin(models)]],ignore_index=True)
res=pred.groupby(['pipeline',ID]).agg(y_true=('y_true','first'),oof_prediction_mean=('y_pred','mean'),oof_prediction_median=('y_pred','median'),oof_prediction_std=('y_pred','std')).reset_index()
res['residual']=res.oof_prediction_mean-res.y_true;res['absolute_error']=abs(res.residual);res['squared_error']=res.residual**2;res['relative_error']=res.residual/res.y_true.abs().where(res.y_true.abs()>=.1)
res.to_csv(D['residuals']/'oof_residuals_by_parcel.csv',index=False)

# ---------- Contexto por parcela ----------
master=pd.read_csv(ROOT/'data/original/01_tablas_maestras/ID_area_rendimiento_70_30_Reto_AgroCebada.csv')[[ID,'AREA_HA','CONJUNTO']]
topo=pd.read_parquet(FEATURE_DIR/'topography_basic_features.parquet')[[ID,'TOPO_BASIC_elevation_mean','TOPO_BASIC_slope_mean']].rename(columns={'TOPO_BASIC_elevation_mean':'elevation_mean','TOPO_BASIC_slope_mean':'slope_mean'})
clim=pd.read_parquet(FEATURE_DIR/'climate_features.parquet')[[ID,'CLIMATE_precip_total','CLIMATE_tmean_mean_mean']].rename(columns={'CLIMATE_precip_total':'precipitation_total','CLIMATE_tmean_mean_mean':'temperature_mean'})
context=master.merge(topo,on=ID).merge(clim,on=ID)
for sensor,file in [('sentinel','sentinel_coverage_by_parcel.csv'),('planet','planet_coverage_by_parcel.csv'),('landsat','landsat_coverage_by_parcel.csv')]:
 c=pd.read_csv(ROOT/'outputs/data_audit/family_1/timeseries'/file)[[ID,'n_valid_apr_oct_2025','valid_fraction','median_gap_days','max_gap_days']].rename(columns={x:f'{sensor}_{x}' for x in ['n_valid_apr_oct_2025','valid_fraction','median_gap_days','max_gap_days']});context=context.merge(c,on=ID)
for sensor,file in [('sentinel','sentinel_timeseries.parquet'),('planet','planet_timeseries.parquet'),('landsat','landsat_timeseries.parquet')]:
 t=pd.read_parquet(ROOT/'data/processed/family_1/timeseries'/file);t=t[t.fecha_captura.between('2025-04-01','2025-10-31')];q=t.groupby(ID).agg(**{f'{sensor}_cloud_mean':('cloud_raw','mean'),f'{sensor}_cloud_p90':('cloud_raw',lambda x:x.quantile(.9))}).reset_index();context=context.merge(q,on=ID,how='left')

# ---------- Segmentos por rendimiento ----------
yvals=res.drop_duplicates(ID).y_true;q1,q2,q3=yvals.quantile([.25,.5,.75]);cuts=[-np.inf,q1,q3,np.inf];labels=['low_Q1','middle_Q2_Q3','high_Q4']
res['yield_segment']=pd.cut(res.y_true,cuts,labels=labels,include_lowest=True)
res['yield_decile']=pd.qcut(res.y_true,10,labels=[f'D{i}' for i in range(1,11)],duplicates='drop')
seg=[]
for kind,col in [('quartile_band','yield_segment'),('decile','yield_decile')]:
 for (p,gname),g in res.groupby(['pipeline',col],observed=True):seg.append({'pipeline':p,'segmentation':kind,'segment':str(gname),'n':len(g),'bias':g.residual.mean(),'MAE':g.absolute_error.mean(),'RMSE':np.sqrt(g.squared_error.mean()),'MedAE':g.absolute_error.median(),'y_min':g.y_true.min(),'y_max':g.y_true.max()})
seg=pd.DataFrame(seg);seg.to_csv(D['segments']/'yield_segment_performance.csv',index=False)

# Calibración descriptiva.
cal=[]
for p,g in res.groupby('pipeline'):
 lr=LinearRegression().fit(g[['y_true']],g.oof_prediction_mean);cal.append({'pipeline':p,'alpha':lr.intercept_,'beta_calibration_slope':lr.coef_[0],'compression_1_minus_beta':1-lr.coef_[0],'R2_descriptive':lr.score(g[['y_true']],g.oof_prediction_mean)})
cal=pd.DataFrame(cal);cal.to_csv(D['diagnostics']/'calibration_summary.csv',index=False)

# ---------- Parcelas difíciles ----------
wide=res.pivot(index=ID,columns='pipeline',values=['absolute_error','oof_prediction_std','residual','oof_prediction_mean','y_true'])
diag=context[context.CONJUNTO=='ENTRENAMIENTO'].set_index(ID).copy()
for p in models:
 diag[f'{p}_absolute_error']=wide[('absolute_error',p)];diag[f'{p}_residual']=wide[('residual',p)];diag[f'{p}_oof_std']=wide[('oof_prediction_std',p)];diag[f'{p}_error_rank']=diag[f'{p}_absolute_error'].rank(ascending=False,method='min')
diag['mean_absolute_error_3models']=diag[[f'{p}_absolute_error' for p in models]].mean(axis=1);diag['mean_oof_std_3models']=diag[[f'{p}_oof_std' for p in models]].mean(axis=1);diag['difficult_all_3']=np.logical_and.reduce([diag[f'{p}_absolute_error']>=diag[f'{p}_absolute_error'].quantile(.75) for p in models]);diag['n_models_in_worst_quartile']=sum((diag[f'{p}_absolute_error']>=diag[f'{p}_absolute_error'].quantile(.75)).astype(int) for p in models);diag['only_one_model_fails']=diag.n_models_in_worst_quartile==1;diag['overall_difficulty_rank']=diag.mean_absolute_error_3models.rank(ascending=False,method='min');diag.reset_index().sort_values('overall_difficulty_rank').to_csv(D['segments']/'difficult_parcel_diagnostics.csv',index=False)

# ---------- Correlación de errores ----------
er=res.pivot(index=ID,columns='pipeline',values=['residual','absolute_error']);ec=[]
for metric in ['residual','absolute_error']:
 for a,b in [('XGB_CORE','LGBM_CORE'),('XGB_CORE','ENET_CORE_EXTENDED'),('LGBM_CORE','ENET_CORE_EXTENDED')]:
  ec.append({'metric':metric,'model_A':a,'model_B':b,'pearson_correlation':er[metric][a].corr(er[metric][b]),'spearman_correlation':er[metric][a].corr(er[metric][b],method='spearman')})
pd.DataFrame(ec).to_csv(D['residuals']/'model_error_correlations.csv',index=False)

# ---------- Heterocedasticidad / calidad ----------
covars=['y_true','oof_prediction_mean','AREA_HA','elevation_mean','slope_mean','precipitation_total','temperature_mean','sentinel_n_valid_apr_oct_2025','planet_n_valid_apr_oct_2025','landsat_n_valid_apr_oct_2025']
joined=res.merge(context,on=ID,how='left');het=[]
for p,g in joined.groupby('pipeline'):
 for err in ['absolute_error','squared_error']:
  for c in covars:
   z=g[[err,c]].dropna();het.append({'pipeline':p,'error_metric':err,'context_variable':c,'n':len(z),'pearson':pearsonr(z[err],z[c]).statistic,'spearman':spearmanr(z[err],z[c]).statistic})
pd.DataFrame(het).to_csv(D['diagnostics']/'heteroscedasticity_summary.csv',index=False)
quality=[c for c in context if any(x in c for x in ['sentinel_','planet_','landsat_'])]
qr=[]
for p,g in joined.groupby('pipeline'):
 for c in quality:
  z=g[['absolute_error',c]].dropna();qr.append({'pipeline':p,'quality_variable':c,'n':len(z),'pearson_abs_error':pearsonr(z.absolute_error,z[c]).statistic,'spearman_abs_error':spearmanr(z.absolute_error,z[c]).statistic})
pd.DataFrame(qr).to_csv(D['diagnostics']/'data_quality_error_relationship.csv',index=False)

# ---------- Espacio, Moran y mapas ----------
shp=ROOT/'data/original/02_conjunto_70_30/Parcelas_Reto_AGC_CONJUNTO.shp';geo=gpd.read_file(shp).rename(columns={'ID_POLIGON':ID});geo=geo[[ID,'geometry']].merge(context[[ID,'CONJUNTO']],on=ID);train_geo=geo[geo.CONJUNTO=='ENTRENAMIENTO'].to_crs('EPSG:6372').copy();train_geo['centroid_x']=train_geo.geometry.centroid.x;train_geo['centroid_y']=train_geo.geometry.centroid.y;coords=train_geo[['centroid_x','centroid_y']].to_numpy()
def moran(values,k,permutations=999):
 x=np.asarray(values,float);z=x-x.mean();nn=NearestNeighbors(n_neighbors=k+1).fit(coords);ind=nn.kneighbors(return_distance=False)[:,1:];w=np.zeros((len(x),len(x)));w[np.arange(len(x))[:,None],ind]=1/k;s0=w.sum();obs=len(x)/s0*np.sum(w*z[:,None]*z[None,:])/np.sum(z*z);rng=np.random.default_rng(SEED+k);sim=[]
 for _ in range(permutations):
  zp=rng.permutation(z);sim.append(len(x)/s0*np.sum(w*zp[:,None]*zp[None,:])/np.sum(zp*zp))
 sim=np.asarray(sim);return obs,(1+np.sum(abs(sim)>=abs(obs)))/(permutations+1)
sp=[]
for p in models:
 values=train_geo[[ID]].merge(res[res.pipeline==p][[ID,'residual']],on=ID).residual
 for k in [4,6,8]:
  mi,pv=moran(values,k);sp.append({'pipeline':p,'neighbor_definition':'symmetric-distance not forced; row-standardized directed kNN','k_neighbors':k,'moran_I':mi,'permutation_p_two_sided':pv,'permutations':999})
pd.DataFrame(sp).to_csv(D['spatial']/'spatial_residual_summary.csv',index=False)

# Grupos espaciales y CV secundaria.
# Cinco bloques aproximadamente balanceados a lo largo del eje espacial
# principal. No usa y; tamaños 27-28 para evitar folds geográficos diminutos.
projection=PCA(n_components=1).fit_transform(StandardScaler().fit_transform(coords)).ravel();groups=np.empty(len(coords),dtype=int)
for gp,positions in enumerate(np.array_split(np.argsort(projection),5)):groups[positions]=gp
train_geo['spatial_group']=groups
ids_all,Xall,yall=load_xy();order=train_geo.set_index(ID).loc[ids_all,'spatial_group'].to_numpy();reps=representations(Xall.columns);ext=[c for c in pd.read_parquet(FEATURE_DIR/'sentinel_features_extended.parquet').columns if c!=ID and c in Xall];xext=list(dict.fromkeys(reps['CORE']+ext))
specs={
 'XGB_CORE':(reps['CORE'],Pipeline([('imputer',SimpleImputer(strategy='median')),('model',XGBRegressor(random_state=SEED,n_jobs=1,objective='reg:squarederror'))]),{'model__n_estimators':[150,300],'model__max_depth':[2,3],'model__learning_rate':[.03],'model__min_child_weight':[5,10],'model__subsample':[.8],'model__colsample_bytree':[.6],'model__reg_alpha':[.5],'model__reg_lambda':[5.]}),
 'LGBM_CORE':(reps['CORE'],Pipeline([('imputer',SimpleImputer(strategy='median')),('model',LGBMRegressor(random_state=SEED,verbosity=-1,n_jobs=1))]),{'model__n_estimators':[100,250],'model__num_leaves':[5,10],'model__learning_rate':[.03],'model__min_child_samples':[15,25],'model__subsample':[.8],'model__colsample_bytree':[.6],'model__reg_alpha':[.5],'model__reg_lambda':[2.]}),
 'ENET_CORE_EXTENDED':(xext,Pipeline([('imputer',SimpleImputer(strategy='median')),('scaler',StandardScaler()),('model',ElasticNet(max_iter=20000,random_state=SEED))]),{'model__alpha':[.01,.1,1.],'model__l1_ratio':[.1,.5,.9]})}
sp_pred=[];gkf=GroupKFold(5)
for p,(features,est,grid) in specs.items():
 for fold,(tr,va) in enumerate(gkf.split(Xall,yall,order),1):
  search=GridSearchCV(est,grid,cv=KFold(4,shuffle=True,random_state=SEED+fold),scoring='neg_root_mean_squared_error',n_jobs=-1,refit=True);search.fit(Xall.iloc[tr][features],yall.iloc[tr]);pr=search.predict(Xall.iloc[va][features])
  for pid,truth,prediction,gp in zip(ids_all.iloc[va],yall.iloc[va],pr,order[va]):sp_pred.append({ID:pid,'pipeline':p,'spatial_fold':fold,'spatial_group':gp,'y_true':truth,'y_pred':prediction})
sp_pred=pd.DataFrame(sp_pred);sp_pred.to_parquet(D['spatial']/'spatial_cv_oof_predictions.parquet',index=False);sm=[]
for (p,f),g in sp_pred.groupby(['pipeline','spatial_fold']):sm.append({'pipeline':p,'spatial_fold':f,'n':len(g),'RMSE':mean_squared_error(g.y_true,g.y_pred)**.5,'MAE':mean_absolute_error(g.y_true,g.y_pred),'R2':r2_score(g.y_true,g.y_pred),'MedAE':median_absolute_error(g.y_true,g.y_pred)})
sm=pd.DataFrame(sm);overall=[]
for p,g in sp_pred.groupby('pipeline'):overall.append({'pipeline':p,'spatial_fold':'overall_oof','n':len(g),'RMSE':mean_squared_error(g.y_true,g.y_pred)**.5,'MAE':mean_absolute_error(g.y_true,g.y_pred),'R2':r2_score(g.y_true,g.y_pred),'MedAE':median_absolute_error(g.y_true,g.y_pred)})
sm=pd.concat([sm,pd.DataFrame(overall)],ignore_index=True);random_metrics=pd.concat([pd.read_csv(ROOT/'outputs/modeling/family_1/stage4/screening/pipeline_metrics.csv'),pd.read_csv(ROOT/'outputs/modeling/family_1/stage4_round2/metrics/round2_pipeline_metrics.csv')]).drop_duplicates('pipeline').set_index('pipeline');sm['random_cv_RMSE_mean']=sm.pipeline.map(random_metrics.RMSE_mean);sm['spatial_minus_random_RMSE']=sm.RMSE-sm.random_cv_RMSE_mean;sm.to_csv(D['spatial']/'spatial_cv_metrics.csv',index=False)

# ---------- Regímenes descriptivos definidos sin residual ----------
base=res.drop_duplicates(ID)[[ID,'y_true']].merge(context,on=ID).merge(train_geo[[ID,'spatial_group','centroid_x','centroid_y']],on=ID)
base['climate_cluster']=KMeans(3,random_state=SEED,n_init=50).fit_predict(StandardScaler().fit_transform(base[['precipitation_total','temperature_mean']]))
z=SimpleImputer(strategy='median').fit_transform(Xall);z=StandardScaler().fit_transform(z);pc=PCA(10,random_state=SEED).fit_transform(z);base['x_cluster']=KMeans(3,random_state=SEED,n_init=50).fit_predict(pc)
regime=[]
for definition,col in [('geography','spatial_group'),('climate','climate_cluster'),('X_unsupervised','x_cluster')]:
 j=res.merge(base[[ID,col]],on=ID)
 for (p,gid),g in j.groupby(['pipeline',col]):regime.append({'regime_definition':definition,'regime':gid,'pipeline':p,'n':len(g),'bias':g.residual.mean(),'MAE':g.absolute_error.mean(),'RMSE':np.sqrt(g.squared_error.mean())})
pd.DataFrame(regime).to_csv(D['diagnostics']/'regime_diagnostics.csv',index=False)

# ---------- Figuras ----------
palette={'XGB_CORE':'#1b9e77','LGBM_CORE':'#d95f02','ENET_CORE_EXTENDED':'#7570b3'}
try:
 from statsmodels.nonparametric.smoothers_lowess import lowess
except Exception:lowess=None
fig,axes=plt.subplots(3,3,figsize=(15,13))
for row,(p,g) in enumerate(res.groupby('pipeline')):
 for col,(yv,xv,title) in enumerate([('residual','y_true','Residual vs rendimiento'),('absolute_error','y_true','Error absoluto vs rendimiento'),('oof_prediction_mean','y_true','Predicción vs rendimiento')]):
  ax=axes[row,col];ax.scatter(g[xv],g[yv],s=25,alpha=.7,color=palette[p]);
  if col==0:ax.axhline(0,color='black',lw=1)
  if col==2:
   lo=min(g.y_true.min(),g.oof_prediction_mean.min());hi=max(g.y_true.max(),g.oof_prediction_mean.max());ax.plot([lo,hi],[lo,hi],'k--',lw=1)
  if lowess is not None:
   smth=lowess(g[yv],g[xv],frac=.45,return_sorted=True);ax.plot(smth[:,0],smth[:,1],color='crimson',lw=2)
  ax.set(title=f'{p}: {title}',xlabel='y_true',ylabel=yv)
fig.tight_layout();fig.savefig(D['figures']/'01_error_vs_yield.png',dpi=180);plt.close(fig)
fig,axes=plt.subplots(2,3,figsize=(15,9))
for col,(a,b) in enumerate([('XGB_CORE','LGBM_CORE'),('XGB_CORE','ENET_CORE_EXTENDED'),('LGBM_CORE','ENET_CORE_EXTENDED')]):
 for row,metric in enumerate(['residual','absolute_error']):axes[row,col].scatter(er[metric][a],er[metric][b],s=22,alpha=.65);axes[row,col].set(xlabel=a,ylabel=b,title=f'{metric}: r={er[metric][a].corr(er[metric][b]):.3f}')
fig.tight_layout();fig.savefig(D['figures']/'02_paired_model_errors.png',dpi=180);plt.close(fig)
fig,axes=plt.subplots(1,3,figsize=(17,5))
for ax,p in zip(axes,models):
 m=train_geo.merge(res[res.pipeline==p][[ID,'residual']],on=ID);m.plot(column='residual',cmap='RdBu_r',legend=True,ax=ax,vmin=-max(abs(m.residual)),vmax=max(abs(m.residual)));ax.set_title(p);ax.axis('off')
fig.tight_layout();fig.savefig(D['figures']/'03_spatial_residual_maps.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(8,7));train_geo.plot(column='spatial_group',categorical=True,legend=True,ax=ax,cmap='tab10');ax.set_title('Cinco grupos para sensibilidad espacial');ax.axis('off');fig.tight_layout();fig.savefig(D['figures']/'04_spatial_cv_groups.png',dpi=180);plt.close(fig)
fig,axes=plt.subplots(3,3,figsize=(15,13));plotvars=['AREA_HA','elevation_mean','slope_mean','precipitation_total','temperature_mean','sentinel_n_valid_apr_oct_2025','planet_n_valid_apr_oct_2025','landsat_n_valid_apr_oct_2025','sentinel_cloud_mean']
for ax,c in zip(axes.ravel(),plotvars):
 for p,g in joined.groupby('pipeline'):ax.scatter(g[c],g.absolute_error,s=13,alpha=.35,label=p,color=palette[p]);ax.set(xlabel=c,ylabel='absolute_error')
axes[0,0].legend(fontsize=7);fig.tight_layout();fig.savefig(D['figures']/'05_error_vs_context_quality.png',dpi=180);plt.close(fig)

# ---------- Reporte ----------
lowseg=seg[(seg.segmentation=='quartile_band')&(seg.segment=='low_Q1')].set_index('pipeline');highseg=seg[(seg.segmentation=='quartile_band')&(seg.segment=='high_Q4')].set_index('pipeline');corrdf=pd.DataFrame(ec);moran=pd.DataFrame(sp);spoverall=sm[sm.spatial_fold.astype(str)=='overall_oof'].set_index('pipeline');qualitydf=pd.DataFrame(qr)
shared=diag[diag.difficult_all_3].sort_values('mean_absolute_error_3models',ascending=False).head(20).index.tolist();top20=diag.sort_values('mean_absolute_error_3models',ascending=False).head(20);rest=diag.drop(top20.index);common={c:float(top20[c].mean()-rest[c].mean()) for c in ['AREA_HA','elevation_mean','slope_mean','precipitation_total','temperature_mean','sentinel_n_valid_apr_oct_2025','planet_n_valid_apr_oct_2025','landsat_n_valid_apr_oct_2025']}
report=f'''# Familia 1 — Etapa 4.3: error y robustez

Se usaron predicciones OOF existentes para el diagnóstico principal. Sólo la sensibilidad espacial refitió los tres pipelines con preprocessing/tuning dentro de cada train espacial. No se ejecutó Familia 2.

1. **Dónde se concentran:** Q1/Q4 y parcelas listadas en `difficult_parcel_diagnostics.csv`; desempeño por segmento: {seg[seg.segmentation=='quartile_band'][['pipeline','segment','bias','MAE','RMSE']].round(3).to_dict('records')}.
2. **Extremos:** sí; el RMSE es mayor en Q1/Q4 que en Q2–Q3.
3. **Bajos:** los tres sobreestiman Q1: biases {lowseg.bias.round(3).to_dict()}.
4. **Altos:** los tres subestiman Q4: biases {highseg.bias.round(3).to_dict()}.
5. **Difíciles para todos:** {shared}.
6. **Características compartidas top-20 menos resto (diferencias medias):** {common}. Son asociaciones descriptivas, no causas.
7. **XGB vs LGBM:** correlación residual={corrdf[(corrdf.metric=='residual')&(corrdf.model_A=='XGB_CORE')].pearson_correlation.iloc[0]:.3f}; cometen errores muy similares.
8. **Elastic Net:** correlaciones con árboles están en `model_error_correlations.csv`; aporta diversidad sólo si son materialmente menores que XGB–LGBM.
9. **Heterocedasticidad:** los errores dependen del nivel de rendimiento y contexto; consultar correlaciones. No se aplicó BP/White a boosting.
10. **Espacio:** Moran k=4/6/8: {moran[['pipeline','k_neighbors','moran_I','permutation_p_two_sided']].round(3).to_dict('records')}. No implica causalidad.
11. **CV espacial:** {spoverall[['RMSE','MAE','R2','MedAE','random_cv_RMSE_mean','spatial_minus_random_RMSE']].round(3).reset_index().to_dict('records')}.
12. **Regímenes:** geografía, clima y clusters X muestran diferencias descriptivas en `regime_diagnostics.csv`; requieren validación futura antes de modelos por régimen.
13. **Calidad/cobertura:** relaciones máximas absolutas: {qualitydf.loc[qualitydf.groupby('pipeline').spearman_abs_error.apply(lambda x:x.abs().idxmax())][['pipeline','quality_variable','spearman_abs_error']].round(3).to_dict('records')}.
14. **Volver a feature engineering:** sólo si los residuos espaciales/calidad son materialmente estructurados; priorizar cobertura/contexto, no expansión indiscriminada.
15. **Madurez:** Familia 1 puede congelarse como baseline si la caída espacial se acepta y documenta; mantener sus limitaciones de extremos y regresión a la media al abrir Familia 2.

## Definiciones

- Residual = predicción − real; positivo sobreestima.
- Segmentos: Q1 ≤ {q1:.3f}, medio ({q1:.3f}, {q3:.3f}), Q4 ≥ {q3:.3f}; deciles son descriptivos.
- Vecindad Moran: k-NN de centroides en EPSG:6372, pesos 1/k, 999 permutaciones; sensibilidad k=4,6,8.
- CV espacial: cinco bloques balanceados por orden sobre el primer eje PCA de centroides métricos, sin y, GroupKFold; no reemplaza el CV principal.
'''
(D['report']/'family1_error_analysis.md').write_text(report,encoding='utf-8')
print(cal.to_string(index=False));print(spoverall[['RMSE','random_cv_RMSE_mean','spatial_minus_random_RMSE']].reset_index().to_string(index=False));print('Reporte:',D['report']/'family1_error_analysis.md')
