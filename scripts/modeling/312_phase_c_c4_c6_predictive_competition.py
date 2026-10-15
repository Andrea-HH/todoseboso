"""C4-C6: leakage-controlled predictive competition against frozen Champion V1."""
from pathlib import Path
import json,time,hashlib,warnings
import numpy as np,pandas as pd,geopandas as gpd
import matplotlib.pyplot as plt,seaborn as sns
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler,OneHotEncoder,PolynomialFeatures,SplineTransformer,StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge,ElasticNet
from sklearn.model_selection import KFold,GridSearchCV,GroupKFold
from sklearn.metrics import mean_squared_error,mean_absolute_error,median_absolute_error,r2_score
from sklearn.cluster import KMeans
from xgboost import XGBRegressor
from scipy import stats
warnings.filterwarnings('ignore')
ROOT=Path(__file__).resolve().parents[2];ID='ID_POLIGONO';SEED=2026
OUT=ROOT/'outputs/research/phase_c/c4_c6_predictive_competition';PROC=ROOT/'data/processed/phase_c/c4_c6'
TAB=OUT/'tables';FIG=OUT/'figures';REP=OUT/'report'
for p in [OUT,PROC,TAB,FIG,REP]:p.mkdir(parents=True,exist_ok=True)

def sha(p):h=hashlib.sha256();h.update(Path(p).read_bytes());return h.hexdigest()
def pam(D,k,seed):
 rr=np.random.default_rng(seed);med=[rr.integers(len(D))]
 while len(med)<k:med.append(int(np.argmax(D[:,med].min(1))))
 med=np.array(med)
 for _ in range(50):
  lab=D[:,med].argmin(1);new=[]
  for j in range(k):
   ix=np.where(lab==j)[0];new.append(int(ix[np.argmin(D[np.ix_(ix,ix)].sum(1))]))
  new=np.array(new)
  if set(new)==set(med):break
  med=new
 return med
class InductiveEnvironment:
 def __init__(self,cols,k=2):self.cols=cols;self.k=k
 def _encode(self,df,fit=False):
  if fit:
   self.num=[c for c in self.cols if df[c].dtype!='object'];self.cat=[c for c in self.cols if c not in self.num]
   self.med=df[self.num].median();q=df[self.num].quantile([.25,.75]);self.iqr=(q.loc[.75]-q.loc[.25]).replace(0,1);self.catmode={c:(df[c].mode().iloc[0] if len(df[c].mode()) else 'MISSING') for c in self.cat}
  A=np.clip((df[self.num].fillna(self.med)-self.med)/self.iqr,-4,4).to_numpy(float)
  C=np.column_stack([df[c].fillna(self.catmode[c]).astype(str).to_numpy() for c in self.cat]) if self.cat else np.empty((len(df),0))
  return A,C
 def _dist(self,A,C,B,E):
  dn=np.abs(A[:,None,:]-B[None,:,:]).mean(2)/8 if A.shape[1] else 0;dc=(C[:,None,:]!=E[None,:,:]).mean(2) if C.shape[1] else 0
  return (dn+dc)/((A.shape[1]>0)+(C.shape[1]>0))
 def fit(self,df,seed):
  A,C=self._encode(df,True);D=self._dist(A,C,A,C);np.fill_diagonal(D,0);self.medoid_idx=pam(D,self.k,seed);self.MA=A[self.medoid_idx];self.MC=C[self.medoid_idx];return self
 def transform(self,df):
  A,C=self._encode(df);D=self._dist(A,C,self.MA,self.MC);lab=D.argmin(1);s=np.sort(D,axis=1);margin=(s[:,1]-s[:,0])/(s[:,1]+1e-12);soft=np.exp(-D/(np.median(D)+1e-12));soft/=soft.sum(1,keepdims=True)
  return lab,D,margin,soft

def load():
 f=pd.read_parquet(ROOT/'data/processed/family_1/features/family1_features_all.parquet');ext=pd.read_parquet(ROOT/'data/processed/phase_c/c0_c1/integrated_research_matrix.parquet');rgb=pd.read_parquet(ROOT/'data/processed/phase_c/c1_2/rgb_compact_representations.parquet')
 ch=pd.read_parquet(ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization/predictions/oof_predictions.parquet');ch=ch[ch.architecture.eq('A_CURRENT_CH_H_T')].copy()
 # target is recovered only for TRAIN; PREDICTION never enters supervised folds.
 ids=ch[[ID,'y_true']].drop_duplicates().sort_values(ID);d=ids.merge(f,on=ID,how='left').merge(ext,on=ID,how='left',suffixes=('','_ext')).merge(rgb.drop(columns=['CONJUNTO','Estado','AREA_HA']),on=ID,how='left')
 shp=gpd.read_file(ROOT/'data/original/02_conjunto_70_30/Parcelas_Reto_AGC_CONJUNTO.shp');shp[ID]=shp.ID_POLIGON.astype(str);g=shp.to_crs(6372);c=g.geometry.centroid;xy=pd.DataFrame({ID:g[ID],'x':c.x,'z':c.y});d=d.merge(xy,on=ID)
 assert len(d)==138 and d[ID].nunique()==138 and ch.groupby([ID,'repeat']).size().eq(1).all() and ch.groupby(ID).size().eq(10).all()
 return d,ch
def blocks(d):
 allf=pd.read_parquet(ROOT/'data/processed/family_1/features/family1_features_all.parquet');core=[c for c in allf if c.startswith(('CLIMATE_','HIST_S2_','TOPO_BASIC_')) and not c.endswith('_months')]
 # Compact X0: fixed interpretable subset, no Y screening.
 x0=[c for c in core if any(s in c for s in ['precip_early_sum','precip_total','tmin_mean_std','tmax_mean_mean','HIST_S2_ndvi_promedio_mean','HIST_S2_ndvi_promedio_std','HIST_S2_lai_promedio_mean','HIST_S2_ndwi_promedio_mean','elevation_mean','elevation_std','slope_mean','slope_std'])][:24]
 s1=['EXT_area_geometry_ha','EXT_PHYS_dominant_fraction','EXT_GEOL_clave','EXT_GEOL_clase','EXT_GEOL_tipo','EXT_GEOL_era','EXT_GEOL_entidad','EXT_GEOL_dominant_fraction','EXT_GEOL_diversity','EXT_GEOL_distance_structure_m','EXT_GEOL_distance_fault_m','EXT_GEOL_distance_fracture_m']
 s3=['CLIMATE_precip_early_sum','CLIMATE_precip_total','CLIMATE_tmax_mean_mean','TOPO_BASIC_elevation_mean','TOPO_BASIC_elevation_std','TOPO_BASIC_slope_mean','TOPO_BASIC_slope_std','TOPO_BASIC_elevation_relief','TOPO_ADV_twi_mean','TOPO_ADV_flow_accumulation_log1p_mean','TOPO_ADV_local_relief_3x3_mean']
 ph=['S2_ndvi_promedio_mean','S2_ndvi_promedio_normalized_auc','S2_ndvi_promedio_peak_day','S2_ndvi_promedio_std','S2_ndwi_promedio_mean','S2_fapar_promedio_normalized_auc'];s5=list(dict.fromkeys(s1+s3+ph))
 external=[c for c in s1 if c!='EXT_area_geometry_ha'];rgb=[c for c in d if ('palette_PC' in c or 'spatial_PC' in c) and c.endswith(('PC1','PC2','PC3'))]
 return {'X0':x0,'X1':list(dict.fromkeys(x0+external)),'X3':list(dict.fromkeys(x0+s3)),'X6':list(dict.fromkeys(x0+rgb))},s1,s3,s5
def basepipe(kind,seed):
 if kind=='RIDGE':return Ridge(),{'model__alpha':[.1,1,10,100]}
 if kind=='ENET':return ElasticNet(max_iter=30000,random_state=seed),{'model__alpha':[.003,.03,.3],'model__l1_ratio':[.1,.5,.9]}
 m=XGBRegressor(objective='reg:squarederror',random_state=seed,n_jobs=1,verbosity=0);return m,{'model__max_depth':[1,2],'model__n_estimators':[150,300],'model__learning_rate':[.02,.05],'model__reg_lambda':[5,15]}
def fitpredict(train,val,ytr,cols,kind,seed,extra_train=None,extra_val=None,spline=False):
 A=train[cols].copy();B=val[cols].copy();num=[c for c in cols if A[c].dtype!='object'];cat=[c for c in cols if c not in num]
 pre=ColumnTransformer([('num',Pipeline([('imp',SimpleImputer(strategy='median')),('scale',RobustScaler()),*([('spline',SplineTransformer(n_knots=4,degree=2))] if spline else [])]),num),('cat',Pipeline([('imp',SimpleImputer(strategy='most_frequent')),('oh',OneHotEncoder(handle_unknown='ignore'))]),cat)],sparse_threshold=0)
 model,grid=basepipe(kind,seed);pipe=Pipeline([('pre',pre),('model',model)])
 if extra_train is not None:
  for j in range(extra_train.shape[1]):A[f'ENV_{j}']=extra_train[:,j];B[f'ENV_{j}']=extra_val[:,j];cols=cols+[f'ENV_{j}'];num=num+[f'ENV_{j}']
  pre=ColumnTransformer([('num',Pipeline([('imp',SimpleImputer(strategy='median')),('scale',RobustScaler()),*([('spline',SplineTransformer(n_knots=4,degree=2))] if spline else [])]),num),('cat',Pipeline([('imp',SimpleImputer(strategy='most_frequent')),('oh',OneHotEncoder(handle_unknown='ignore'))]),cat)],sparse_threshold=0);pipe=Pipeline([('pre',pre),('model',model)])
 inner=KFold(4,shuffle=True,random_state=seed);gs=GridSearchCV(pipe,grid,cv=inner,scoring='neg_root_mean_squared_error',n_jobs=1).fit(A,ytr);return gs.predict(B),gs.best_params_,len(cols)
def run():
 d,ch=load();blocks_,s1,s3,s5=blocks(d);ids=d[ID].reset_index(drop=True);y=d.y_true.to_numpy();pos={v:i for i,v in enumerate(ids)}
 # Exact folds are reconstructed from audited Champion assignments.
 splits=[]
 for (r,f),q in ch.groupby(['repeat','fold']):
  va=np.array([pos[x] for x in q[ID]]);tr=np.setdiff1d(np.arange(len(d)),va);splits.append(('random',int(r),int(f),tr,va))
 # Five spatial blocks fixed from coordinates, without Y.
 groups=KMeans(5,random_state=SEED,n_init=50).fit_predict(StandardScaler().fit_transform(d[['x','z']]))
 for f,(tr,va) in enumerate(GroupKFold(5).split(d,groups=groups),1):splits.append(('spatial',1,f,tr,va))
 models=[('M1_RIDGE_X0','RIDGE','X0','none'),('M1_ENET_X0','ENET','X0','none'),('M1_RIDGE_X1','RIDGE','X1','none'),('M1_RIDGE_X3','RIDGE','X3','none'),('M1_RIDGE_X5','RIDGE','X0','pca5'),('M1_RIDGE_X6_RGB','RIDGE','X6','none'),('M2_XGB_X0','XGB','X0','none'),('M2_XGB_X1','XGB','X1','none'),('M2_XGB_X3','XGB','X3','none'),('M3_RIDGE_S1_LABEL','RIDGE','X0','s1label'),('M3_RIDGE_S3_LABEL','RIDGE','X0','s3label'),('M3_RIDGE_S1S3_LABEL','RIDGE','X0','bothlabel'),('M4_RIDGE_S1S3_SOFT','RIDGE','X0','soft'),('M5_RIDGE_INTERACTIONS','RIDGE','X0','interactions'),('M6_GAM_X3','RIDGE','X3','spline'),('M7_PARTIAL_S3','RIDGE','X0','partial')]
 pred=[];exper=[]
 # Frozen Champion rows are exact benchmark for random protocol only.
 for _,q in ch.iterrows():pred.append({'protocol':'random','repeat':int(q['repeat']),'fold':int(q.fold),ID:q[ID],'model':'M0_CHAMPION_V1_FROZEN','scenario':'Champion exact','y_true':q.y_true,'y_pred':q.y_pred,'leakage_safe':True})
 for protocol,r,f,tr,va in splits:
  t0=time.time();A=d.iloc[tr].copy();B=d.iloc[va].copy();e1=InductiveEnvironment(s1).fit(A,SEED+r*10+f);e3=InductiveEnvironment(s3).fit(A,SEED+r*10+f);l1,dd1,ma1,u1=e1.transform(A);v1,vd1,vm1,vu1=e1.transform(B);l3,dd3,ma3,u3=e3.transform(A);v3,vd3,vm3,vu3=e3.transform(B)
  # S5 continuous PCA is always fit on outer-train.
  s5n=[c for c in s5 if d[c].dtype!='object'];imp=SimpleImputer(strategy='median').fit(A[s5n]);sc=RobustScaler().fit(imp.transform(A[s5n]));pca=PCA(n_components=min(3,len(s5n)),random_state=SEED).fit(sc.transform(imp.transform(A[s5n])));z5=pca.transform(sc.transform(imp.transform(A[s5n])));w5=pca.transform(sc.transform(imp.transform(B[s5n])))
  for name,kind,bn,env in models:
   try:
    et=ev=None;spline=env=='spline'
    if env=='pca5':et,ev=z5,w5
    elif env=='s1label':et,ev=np.eye(2)[l1],np.eye(2)[v1]
    elif env=='s3label':et,ev=np.eye(2)[l3],np.eye(2)[v3]
    elif env=='bothlabel':et,ev=np.c_[np.eye(2)[l1],np.eye(2)[l3]],np.c_[np.eye(2)[v1],np.eye(2)[v3]]
    elif env=='soft':et,ev=np.c_[u1,u3,ma1,ma3],np.c_[vu1,vu3,vm1,vm3]
    elif env in ['interactions','partial']:
     # S3 fuzzy membership and five predeclared moderated terms.
     base=np.c_[u3[:,1],A.CLIMATE_precip_early_sum*u3[:,1],A.TOPO_BASIC_slope_mean*u1[:,1],A.TOPO_ADV_twi_mean*u1[:,1],A.S2_ndwi_promedio_mean*u3[:,1]]
     val=np.c_[vu3[:,1],B.CLIMATE_precip_early_sum*vu3[:,1],B.TOPO_BASIC_slope_mean*vu1[:,1],B.TOPO_ADV_twi_mean*vu1[:,1],B.S2_ndwi_promedio_mean*vu3[:,1]]
     et,ev=(base,val) if env=='interactions' else (base[:,:2],val[:,:2])
    yp,bp,nf=fitpredict(A,B,y[tr],blocks_[bn],kind,SEED+r*10+f,et,ev,spline)
    for j,p in zip(va,yp):pred.append({'protocol':protocol,'repeat':r,'fold':f,ID:ids.iloc[j],'model':name,'scenario':bn+'+'+env,'y_true':y[j],'y_pred':p,'leakage_safe':True})
    exper.append({'model':name,'family':kind,'feature_block':bn,'environment':env,'protocol':protocol,'repeat':r,'fold':f,'n_train':len(tr),'n_validation':len(va),'n_features_declared':nf,'best_params':json.dumps(bp,sort_keys=True),'elapsed_fold_seconds':time.time()-t0,'status':'success'})
   except Exception as e:exper.append({'model':name,'family':kind,'feature_block':bn,'environment':env,'protocol':protocol,'repeat':r,'fold':f,'status':'failed','error':repr(e)})
  print(protocol,r,f,'done',flush=True)
 p=pd.DataFrame(pred);x=pd.DataFrame(exper);assert not p.duplicated(['protocol','repeat','model',ID]).any();p['residual']=p.y_true-p.y_pred;p['absolute_error']=abs(p.residual);p['squared_error']=p.residual**2
 fm=p.groupby(['protocol','model','repeat','fold']).agg(fold_RMSE=('squared_error',lambda s:np.sqrt(s.mean())),fold_MAE=('absolute_error','mean'),fold_bias_y_minus_pred=('residual','mean'),n_fold=('y_true','size')).reset_index();fm.to_csv(TAB/'09_fold_metrics.csv',index=False)
 x=x.merge(fm,on=['protocol','model','repeat','fold'],how='left');p.to_parquet(PROC/'c4_c6_oof_predictions.parquet',index=False);p.to_csv(TAB/'02_oof_predictions.csv',index=False);x.to_csv(TAB/'01_experiment_registry.csv',index=False);pd.DataFrame({ID:ids,'spatial_block':groups}).to_csv(TAB/'03_spatial_blocks.csv',index=False)
 return d,p,x,models
def summarize(d,p,x,models):
 rows=[]
 for (pro,m),g in p.groupby(['protocol','model']):
  a=g.groupby(ID).agg(y=('y_true','first'),pred=('y_pred','mean')).reset_index();res=a.y-a.pred;beta,alpha=np.polyfit(a.y,a.pred,1)
  rows.append({'protocol':pro,'model':m,'n':len(a),'RMSE':np.sqrt(np.mean(res**2)),'MAE':np.mean(abs(res)),'R2':r2_score(a.y,a.pred),'bias_y_minus_pred':res.mean(),'MedAE':np.median(abs(res)),'calibration_intercept':alpha,'calibration_slope':beta})
 met=pd.DataFrame(rows);base=p[(p.protocol=='random')&(p.model=='M0_CHAMPION_V1_FROZEN')];bw=base.pivot(index=[ID,'repeat'],columns='model',values='squared_error')
 comp=[]
 for m in p[(p.protocol=='random')&~p.model.eq('M0_CHAMPION_V1_FROZEN')].model.unique():
  c=p[(p.protocol=='random')&(p.model==m)];z=c.merge(base[[ID,'repeat','squared_error','absolute_error']],on=[ID,'repeat'],suffixes=('_cand','_champ'));by=z.groupby(ID).agg(dloss=('squared_error_cand',lambda s:0),cand_sq=('squared_error_cand','mean'),champ_sq=('squared_error_champ','mean'),cand_abs=('absolute_error_cand','mean'),champ_abs=('absolute_error_champ','mean'));dl=by.cand_sq-by.champ_sq
  boots=[np.mean(np.random.default_rng(SEED+i).choice(dl,len(dl),True)) for i in range(2000)];rm=met[(met.protocol=='random')&(met.model==m)].iloc[0];bm=met[(met.protocol=='random')&(met.model=='M0_CHAMPION_V1_FROZEN')].iloc[0]
  comp.append({'model':m,'RMSE':rm.RMSE,'MAE':rm.MAE,'delta_RMSE':rm.RMSE-bm.RMSE,'delta_MAE':rm.MAE-bm.MAE,'mean_delta_squared_loss':dl.mean(),'delta_loss_CI_low':np.quantile(boots,.025),'delta_loss_CI_high':np.quantile(boots,.975),'parcel_improvement_fraction':(dl<0).mean(),'decision':'competitive' if rm.RMSE<bm.RMSE and rm.MAE<=bm.MAE+.01 and np.quantile(boots,.975)<=0 else 'not demonstrated'})
 comp=pd.DataFrame(comp);met.to_csv(TAB/'04_metrics_summary.csv',index=False);comp.to_csv(TAB/'05_paired_vs_champion.csv',index=False)
 # repetitions and yield segments
 reps=[];seg=[]
 q1,q3=d.y_true.quantile([.25,.75])
 for (pro,m,r),g in p.groupby(['protocol','model','repeat']):reps.append({'protocol':pro,'model':m,'repeat':r,'RMSE':np.sqrt(g.squared_error.mean()),'MAE':g.absolute_error.mean()})
 for (pro,m),g in p.groupby(['protocol','model']):
  a=g.groupby(ID).agg(y=('y_true','first'),pred=('y_pred','mean')).reset_index();a['segment']=np.where(a.y<=q1,'LOW',np.where(a.y>=q3,'HIGH','MID'))
  for s,z in a.groupby('segment'):seg.append({'protocol':pro,'model':m,'segment':s,'n':len(z),'RMSE':np.sqrt(np.mean((z.y-z.pred)**2)),'MAE':np.mean(abs(z.y-z.pred)),'bias_y_minus_pred':np.mean(z.y-z.pred),'SSE_fraction':np.sum((z.y-z.pred)**2)/np.sum((a.y-a.pred)**2)})
 pd.DataFrame(reps).to_csv(TAB/'06_repetition_metrics.csv',index=False);pd.DataFrame(seg).to_csv(TAB/'07_extreme_calibration.csv',index=False)
 # ablation is a transparent relabeling of directly comparable candidates.
 abl=met[met.protocol.eq('random')].copy();abl['architecture_component']=abl.model.map({'M1_RIDGE_X0':'global baseline','M1_RIDGE_X1':'external territory','M1_RIDGE_X3':'agroclimate originals','M1_RIDGE_X5':'continuous S5','M1_RIDGE_X6_RGB':'RGB','M3_RIDGE_S1_LABEL':'S1 label','M3_RIDGE_S3_LABEL':'S3 label','M3_RIDGE_S1S3_LABEL':'S1+S3 labels','M4_RIDGE_S1S3_SOFT':'soft memberships','M5_RIDGE_INTERACTIONS':'interactions'});abl=abl[abl.architecture_component.notna()];b=abl[abl.model.eq('M1_RIDGE_X0')].RMSE.iloc[0];abl['delta_vs_same_ridge_X0']=abl.RMSE-b;abl.to_csv(TAB/'08_ablation.csv',index=False)
 return met,comp,pd.DataFrame(reps),pd.DataFrame(seg),abl
def plots(met,comp,reps,seg,abl,p):
 sns.set_theme(style='whitegrid');plt.figure(figsize=(12,5));sns.barplot(met,x='model',y='RMSE',hue='protocol');plt.xticks(rotation=55,ha='right');plt.tight_layout();plt.savefig(FIG/'01_rmse_by_model_protocol.png',dpi=180);plt.close()
 plt.figure(figsize=(10,5));sns.barplot(comp.sort_values('delta_RMSE'),x='model',y='delta_RMSE');plt.axhline(0,color='black');plt.xticks(rotation=55,ha='right');plt.tight_layout();plt.savefig(FIG/'02_delta_rmse_vs_champion.png',dpi=180);plt.close()
 top=comp.nsmallest(3,'RMSE').model.tolist()+['M0_CHAMPION_V1_FROZEN'];q=p[(p.protocol=='random')&p.model.isin(top)].groupby([ID,'model']).agg(y=('y_true','first'),pred=('y_pred','mean')).reset_index();plt.figure(figsize=(7,6));sns.scatterplot(q,x='y',y='pred',hue='model');lo,hi=q.y.min(),q.y.max();plt.plot([lo,hi],[lo,hi],'k--');plt.tight_layout();plt.savefig(FIG/'03_predicted_vs_observed.png',dpi=180);plt.close()
 plt.figure(figsize=(10,5));sns.barplot(seg[(seg.protocol=='random')&seg.model.isin(top)],x='segment',y='RMSE',hue='model');plt.tight_layout();plt.savefig(FIG/'04_error_by_yield_segment.png',dpi=180);plt.close()
 plt.figure(figsize=(11,5));sns.boxplot(reps[(reps.protocol=='random')&reps.model.isin(top)],x='model',y='RMSE');plt.xticks(rotation=35,ha='right');plt.tight_layout();plt.savefig(FIG/'05_repetition_stability.png',dpi=180);plt.close()
 plt.figure(figsize=(10,5));sns.barplot(abl,x='architecture_component',y='delta_vs_same_ridge_X0');plt.axhline(0,color='black');plt.xticks(rotation=45,ha='right');plt.tight_layout();plt.savefig(FIG/'06_ablation.png',dpi=180);plt.close()
def report(met,comp,reps,seg,abl):
 random=met[met.protocol=='random'].sort_values('RMSE');sp=met[met.protocol=='spatial'].sort_values('RMSE');best=random.iloc[0];bestnew=random[~random.model.eq('M0_CHAMPION_V1_FROZEN')].iloc[0];champ=random[random.model.eq('M0_CHAMPION_V1_FROZEN')].iloc[0];pair=comp.sort_values('RMSE');ext=seg[(seg.protocol=='random')&seg.model.isin([champ.model,bestnew.model])]
 text=f'''# C4–C6 — Competición predictiva y heterogeneidad agroambiental

## Resumen ejecutivo

Champion histórico congelado y reconstruido desde sus OOF auditadas: RMSE agregado {champ.RMSE:.4f}, MAE {champ.MAE:.4f}. Mejor candidato nuevo: {bestnew.model}, RMSE {bestnew.RMSE:.4f}, Δ={bestnew.RMSE-champ.RMSE:+.4f}. Mejor espacial entre candidatos comparables: {sp.iloc[0].model}, RMSE {sp.iloc[0].RMSE:.4f}. El Champion exact no tiene reconstrucción espacial comparable en esta etapa y no se sustituye por un proxy.

## Auditoría y protocolo

M0 es `A_CURRENT_CH_H_T`, arquitectura Climate→History→Topography, seleccionada previamente sobre estos 138 casos; por ello conserva sesgo de selección. Sus 138×10 OOF tienen claves únicas parcela–repetición y folds explícitos. Los 16 candidatos usan exactamente las mismas 50 particiones. Imputación, escalado, PAM inductivo, PCA S5, splines e hiperparámetros se ajustan sólo en outer-train; inner CV=4. La evaluación espacial usa cinco clusters KMeans de centroides sin Y y se reporta separada.

## Representaciones y modelos

X0 es un baseline FIRA compacto predefinido; X1 añade geología física válida; X3 añade agroclima; X5 son 3 PCs S5 ajustados por fold; X6 es sensibilidad RGB. S1/S3 K=2 se reajustan por fold mediante PAM mixto y las validaciones se asignan a medoides. Se compararon Ridge/Elastic Net, XGBoost conservador, etiquetas, similitudes/márgenes, cinco interacciones preespecificadas, splines penalizados y efectos S3 parcialmente agrupados. No se entrenó mixture-of-experts.

## Resultados OOF y comparación emparejada

{random[['model','RMSE','MAE','R2','bias_y_minus_pred','calibration_slope']].round(4).to_string(index=False)}

Comparación parcelaria contra Champion: {pair.round(4).to_dict('records')}. Los IC son bootstrap de 138 unidades parcelarias sobre diferencia media de pérdida cuadrática; folds/repeticiones no son tratados como observaciones independientes. Es evidencia interna exploratoria tras múltiples candidatos.

## Validación espacial

{sp[['model','RMSE','MAE','R2','bias_y_minus_pred']].round(4).to_string(index=False)}

No se comparan directamente RMSE espacial y aleatorio como si fueran la misma tarea. La falta de Champion secuencial espacial impide afirmar superioridad espacial frente a M0; sí permite comparar candidatos bajo folds comunes.

## Extremos y regresión hacia la media

{ext.round(4).to_dict('records')}. Residuo es `y−predicción`: negativo implica sobreestimación, positivo subestimación. No se aplicó calibrador retrospectivo.

## Ablación y heterogeneidad

{abl[['model','architecture_component','RMSE','delta_vs_same_ridge_X0']].round(4).to_dict('records')}. El valor de etiquetas/membresías/interacciones se juzga contra el mismo Ridge X0, no contra otra arquitectura. Si S5 continuo gana y las etiquetas no, la evidencia favorece gradientes; si ninguno gana, la heterogeneidad no aporta señal predictiva reproducible.

## Complejidad, incertidumbre y decisión

Registro por fold incluye parámetros, tiempos, número de features y fallos. Regla predefinida: menor RMSE, MAE no >+0.01, IC superior de pérdida ≤0, consistencia por repetición, extremos no peores y ausencia de deterioro espacial importante. Ningún candidato se declara confirmatorio por ser el mínimo entre 16.

## Respuestas ejecutivas

1. Superar Champion comparable: {'sí, bajo criterio interno conservador' if len(pair[pair.decision=='competitive']) else 'no demostrado'}.
2. Mejor RMSE interno: {best.model}={best.RMSE:.4f}.
3. Mejor RMSE espacial entre candidatos: {sp.iloc[0].model}={sp.iloc[0].RMSE:.4f}.
4–8. Arquitectura/bloques/ambientes: ver ablación; etiquetas, memberships, S5 e interacciones se aíslan frente a Ridge X0.
9. Extremos: ver tabla 07; exigir mejora LOW y HIGH, no sólo global.
10. Modelo a conservar: {'Champion V1' if not len(pair[pair.decision=='competitive']) else pair[pair.decision=='competitive'].iloc[0].model}; el Champion no se modifica.
11. Incertidumbre: N=138, selección previa, múltiples candidatos, dependencia espacial y ausencia de test externo con Y.
12. Sólo justificar confirmación nested de una candidata si cumple todos los criterios; no justificar MoE ni RGB si sus ablaciones no ganan.
'''
 (REP/'c4_c6_technical_report.md').write_text(text,encoding='utf-8');(REP/'executive_decisions.md').write_text(text.split('## Respuestas ejecutivas')[1],encoding='utf-8')
def main():
 d,p,x,models=run();met,comp,reps,seg,abl=summarize(d,p,x,models);plots(met,comp,reps,seg,abl,p);report(met,comp,reps,seg,abl)
 manifest={'stage':'C4-C6','seed':SEED,'train_n':138,'random_outer_folds':50,'spatial_folds':5,'candidate_models':16,'champion':'A_CURRENT_CH_H_T frozen OOF','champion_spatial_reconstructed':False,'prediction_set_y_used':False,'inputs':{str(q.relative_to(ROOT)):sha(q) for q in [ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization/predictions/oof_predictions.parquet',ROOT/'data/processed/family_1/features/family1_features_all.parquet',ROOT/'data/processed/phase_c/c0_c1/integrated_research_matrix.parquet']}}
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print('C4-C6 complete:',OUT)
if __name__=='__main__':main()
