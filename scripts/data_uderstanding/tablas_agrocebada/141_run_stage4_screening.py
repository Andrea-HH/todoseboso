"""Ronda 1 de Etapa 4 con nested CV y checkpoints por pipeline."""
from pathlib import Path
import sys,json,argparse,warnings,time
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
import numpy as np,pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,RobustScaler
from sklearn.linear_model import ElasticNet,Ridge
from sklearn.cross_decomposition import PLSRegression
from sklearn.decomposition import PCA
from sklearn.model_selection import GridSearchCV,KFold
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score,median_absolute_error
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor
from catboost import CatBoostRegressor
from family_1.stage4_modeling import *
warnings.filterwarnings('ignore')

PIPELINES=['BASELINE_MEAN','ENET_CORE','ENET_ALL','PLS_CORE','PLS_ALL','PCR_CORE','PCR_ALL','LOCAL_PCA_RIDGE','LGBM_CORE','LGBM_ALL','XGB_CORE','CAT_CORE']

def spec(name):
 rep='ALL' if name.endswith('_ALL') or name=='LOCAL_PCA_RIDGE' else 'CORE'
 if name.startswith('ENET'):
  est=Pipeline([('imputer',SimpleImputer(strategy='median')),('scaler',StandardScaler()),('model',ElasticNet(max_iter=20000,random_state=SEED))])
  grid={'model__alpha':[.01,.1,1.0],'model__l1_ratio':[.1,.5,.9]}
  if name=='ENET_CORE':grid['scaler']=[StandardScaler(),RobustScaler()]
 elif name.startswith('PLS'):
  est=Pipeline([('imputer',SimpleImputer(strategy='median')),('scaler',StandardScaler()),('model',PLSRegression(scale=False,max_iter=1000))]);grid={'model__n_components':[2,5,10]}
  if name=='PLS_CORE':grid['scaler']=[StandardScaler(),RobustScaler()]
 elif name.startswith('PCR'):
  est=Pipeline([('imputer',SimpleImputer(strategy='median')),('scaler',StandardScaler()),('pca',PCA(svd_solver='randomized',random_state=SEED)),('model',Ridge())]);grid={'pca__n_components':[5,10,20],'model__alpha':[.1,1,10]}
 elif name=='LOCAL_PCA_RIDGE':
  est=Pipeline([('community',CommunityPCA()),('model',Ridge())]);grid={'community__threshold':[.97,.98],'community__variance':[.90,.95],'model__alpha':[1,10]}
 elif name.startswith('LGBM'):
  est=Pipeline([('imputer',SimpleImputer(strategy='median')),('model',LGBMRegressor(random_state=SEED,verbosity=-1,n_jobs=1))]);grid={'model__n_estimators':[100,250],'model__num_leaves':[5,10],'model__learning_rate':[.03],'model__min_child_samples':[15,25],'model__subsample':[.8],'model__colsample_bytree':[.6],'model__reg_alpha':[.5],'model__reg_lambda':[2.]}
 elif name.startswith('XGB'):
  est=Pipeline([('imputer',SimpleImputer(strategy='median')),('model',XGBRegressor(random_state=SEED,n_jobs=1,objective='reg:squarederror'))]);grid={'model__n_estimators':[150,300],'model__max_depth':[2,3],'model__learning_rate':[.03],'model__min_child_weight':[5,10],'model__subsample':[.8],'model__colsample_bytree':[.6],'model__reg_alpha':[.5],'model__reg_lambda':[5.]}
 elif name.startswith('CAT'):
  est=Pipeline([('imputer',SimpleImputer(strategy='median')),('model',CatBoostRegressor(random_seed=SEED,verbose=False,thread_count=-1,loss_function='RMSE',allow_writing_files=False))]);grid={'model__iterations':[25,50],'model__depth':[3],'model__learning_rate':[.05],'model__l2_leaf_reg':[10]}
 else: return rep,None,None
 return rep,est,grid

def clean_params(params):
 return {k:(v.__class__.__name__ if hasattr(v,'get_params') else v.item() if isinstance(v,np.generic) else v) for k,v in params.items()}

def main(selected):
 ids,X,y=load_xy(); reps=representations(X.columns); splits=save_splits(ids); id_to_i={v:i for i,v in enumerate(ids)}
 for name in selected:
  path=STAGE/f'screening/checkpoints/{name}.parquet'
  done=pd.read_parquet(path) if path.exists() else pd.DataFrame(); completed=set(zip(done.get('repeat',[]),done.get('fold',[]))); rows=[] if done.empty else done.to_dict('records')
  rep,est,grid=spec(name); features=reps[rep]; print(name,rep,len(features),'features',flush=True)
  hp=[]; stability=[]; communities=[]
  hp_path=STAGE/f'screening/checkpoints/{name}_hyper.csv'; stab_path=STAGE/f'screening/checkpoints/{name}_stability.csv'; com_path=STAGE/f'screening/checkpoints/{name}_communities.csv'
  if hp_path.exists():hp=pd.read_csv(hp_path).to_dict('records')
  if stab_path.exists():stability=pd.read_csv(stab_path).to_dict('records')
  if com_path.exists():communities=pd.read_csv(com_path).to_dict('records')
  for k,s in splits.iterrows():
   key=(s['repeat'],s['fold'])
   if key in completed:continue
   tr=np.array([id_to_i[v] for v in json.loads(s.train_ID_POLIGONO)]);va=np.array([id_to_i[v] for v in json.loads(s.validation_ID_POLIGONO)])
   xt=X.iloc[tr][features];xv=X.iloc[va][features];yt=y.iloc[tr];yv=y.iloc[va];start=time.time()
   if name=='BASELINE_MEAN': pred=np.repeat(yt.mean(),len(va));best={};fit=None
   else:
    inner=KFold(n_splits=4,shuffle=True,random_state=SEED+k)
    search=GridSearchCV(est,grid,scoring='neg_root_mean_squared_error',cv=inner,n_jobs=1 if name.startswith('CAT') else -1,refit=True,error_score='raise')
    search.fit(xt,yt);pred=np.asarray(search.predict(xv)).reshape(-1);best=clean_params(search.best_params_);fit=search.best_estimator_
   hp.append({'pipeline':name,'repeat':s['repeat'],'fold':s['fold'],'feature_representation':rep,'best_params':json.dumps(best),'elapsed_seconds':time.time()-start})
   for pid,truth,pr in zip(ids.iloc[va],yv,pred):rows.append({'ID_POLIGONO':pid,'repeat':s['repeat'],'fold':s['fold'],'y_true':truth,'y_pred':pr,'pipeline':name,'feature_representation':rep,'model':name.split('_')[0]})
   if fit is not None:
    model=fit.named_steps['model']
    if name.startswith('ENET'):
     coef=np.asarray(model.coef_).ravel()
     for f,c in zip(features,coef):stability.append({'pipeline':name,'repeat':s['repeat'],'fold':s['fold'],'item':f,'selected':int(abs(c)>1e-12),'value':c,'kind':'elasticnet_coefficient'})
    elif name.startswith(('PLS','PCR')):
     nc=best.get('model__n_components',best.get('pca__n_components'))
     stability.append({'pipeline':name,'repeat':s['repeat'],'fold':s['fold'],'item':'n_components','selected':1,'value':nc,'kind':'component_selection'})
    elif name=='LOCAL_PCA_RIDGE':
     cp=fit.named_steps['community'];
     for r in cp.metadata_:communities.append({'pipeline':name,'repeat':s['repeat'],'fold':s['fold'],**r})
     stability.append({'pipeline':name,'repeat':s['repeat'],'fold':s['fold'],'item':'n_components_total','selected':1,'value':sum(r['n_components'] for r in cp.metadata_),'kind':'component_selection'})
    elif hasattr(model,'feature_importances_'):
     for f,v in zip(features,model.feature_importances_):stability.append({'pipeline':name,'repeat':s['repeat'],'fold':s['fold'],'item':f,'selected':1,'value':v,'kind':'tree_importance'})
   pd.DataFrame(rows).to_parquet(path,index=False);pd.DataFrame(hp).to_csv(hp_path,index=False)
   if stability:pd.DataFrame(stability).to_csv(stab_path,index=False)
   if communities:pd.DataFrame(communities).to_csv(com_path,index=False)
   print(name,s['repeat'],s['fold'],'RMSE',round(mean_squared_error(yv,pred)**.5,4),flush=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('pipelines',nargs='*');a=ap.parse_args();bad=set(a.pipelines)-set(PIPELINES)
 if bad:raise ValueError(f'Pipelines desconocidos: {bad}')
 main(a.pipelines or PIPELINES)
