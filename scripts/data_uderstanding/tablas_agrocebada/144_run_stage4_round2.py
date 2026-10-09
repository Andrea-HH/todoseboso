"""Ejecuta exclusivamente los nueve pipelines autorizados de Ronda 2."""
from pathlib import Path
import sys,json,argparse,warnings,time
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
import numpy as np,pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import GridSearchCV,KFold
from sklearn.metrics import mean_squared_error
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor
from family_1.stage4_modeling import *
warnings.filterwarnings('ignore')

R2=ROOT/'outputs/modeling/family_1/stage4_round2';CHK=R2/'checkpoints';CHK.mkdir(parents=True,exist_ok=True)
PIPELINES=['XGB_PRUNED','XGB_CORE_TOPOADV','XGB_CORE_EXTENDED','LGBM_PRUNED','LGBM_CORE_TOPOADV','LGBM_CORE_EXTENDED','ENET_PRUNED','ENET_CORE_TOPOADV','ENET_CORE_EXTENDED']

def representations_round2(columns):
 base=representations(columns);core=base['CORE'];
 topo=[c for c in pd.read_parquet(FEATURE_DIR/'topography_advanced_features.parquet').columns if c!=ID and c in columns]
 ext=[c for c in pd.read_parquet(FEATURE_DIR/'sentinel_features_extended.parquet').columns if c!=ID and c in columns]
 return {'PRUNED':base['ALL'],'CORE_TOPOADV':list(dict.fromkeys(core+topo)),'CORE_EXTENDED':list(dict.fromkeys(core+ext))}

def spec(name):
 rep=name.split('_',1)[1];pruned=rep=='PRUNED';kind=name.split('_')[0]
 if kind=='XGB':
  model=XGBRegressor(random_state=SEED,n_jobs=1,objective='reg:squarederror');grid={'model__n_estimators':[150,300],'model__max_depth':[2,3],'model__learning_rate':[.03],'model__min_child_weight':[5,10],'model__subsample':[.8],'model__colsample_bytree':[.6],'model__reg_alpha':[.5],'model__reg_lambda':[5.]}
 elif kind=='LGBM':
  model=LGBMRegressor(random_state=SEED,verbosity=-1,n_jobs=1);grid={'model__n_estimators':[100,250],'model__num_leaves':[5,10],'model__learning_rate':[.03],'model__min_child_samples':[15,25],'model__subsample':[.8],'model__colsample_bytree':[.6],'model__reg_alpha':[.5],'model__reg_lambda':[2.]}
 else:
  model=ElasticNet(max_iter=20000,random_state=SEED);grid={'model__alpha':[.01,.1,1.0],'model__l1_ratio':[.1,.5,.9]}
 if pruned:
  cache=R2/'pipeline_cache'/name;cache.mkdir(parents=True,exist_ok=True)
  est=Pipeline([('pruner',CorrelationPruner(scale=kind=='ENET',dictionary_path=str(FEATURE_DIR/'family1_feature_dictionary.csv'))),('model',model)],memory=str(cache));grid['pruner__threshold']=[.90,.95,.98]
 elif kind=='ENET':est=Pipeline([('imputer',SimpleImputer(strategy='median')),('scaler',StandardScaler()),('model',model)])
 else:est=Pipeline([('imputer',SimpleImputer(strategy='median')),('model',model)])
 return rep,est,grid

def clean(params):return {k:(v.item() if isinstance(v,np.generic) else v) for k,v in params.items()}

def main(selected):
 ids,X,y=load_xy();reps=representations_round2(X.columns);splits=save_splits(ids);idx={v:i for i,v in enumerate(ids)}
 for name in selected:
  pred_path=CHK/f'{name}.parquet';done=pd.read_parquet(pred_path) if pred_path.exists() else pd.DataFrame();completed=set(zip(done.get('repeat',[]),done.get('fold',[])));rows=done.to_dict('records') if not done.empty else []
  hp_path=CHK/f'{name}_hyper.csv';stab_path=CHK/f'{name}_stability.parquet';hp=pd.read_csv(hp_path).to_dict('records') if hp_path.exists() else [];stab=pd.read_parquet(stab_path).to_dict('records') if stab_path.exists() else []
  rep,est,grid=spec(name);features=reps[rep];print(name,len(features),'features',flush=True)
  for k,s in splits.iterrows():
   if (s['repeat'],s['fold']) in completed:continue
   tr=np.array([idx[v] for v in json.loads(s.train_ID_POLIGONO)]);va=np.array([idx[v] for v in json.loads(s.validation_ID_POLIGONO)]);xt=X.iloc[tr][features];xv=X.iloc[va][features];yt=y.iloc[tr];yv=y.iloc[va]
   search=GridSearchCV(est,grid,scoring='neg_root_mean_squared_error',cv=KFold(4,shuffle=True,random_state=SEED+k),n_jobs=4 if name.startswith('ENET') else -1,refit=True,error_score='raise');start=time.time();search.fit(xt,yt);fit=search.best_estimator_;pr=np.asarray(fit.predict(xv)).ravel();pars=clean(search.best_params_)
   retained=features;removed=[]
   if rep=='PRUNED':retained=fit.named_steps['pruner'].retained_features_;removed=fit.named_steps['pruner'].removed_features_
   hp.append({'pipeline':name,'repeat':s['repeat'],'fold':s['fold'],'representation':rep,'best_params':json.dumps(pars),'threshold':pars.get('pruner__threshold',np.nan),'n_features_input':len(features),'n_features_retained':len(retained),'n_features_removed':len(removed),'retained_features':json.dumps(retained),'removed_features':json.dumps(removed),'elapsed_seconds':time.time()-start})
   for pid,truth,prediction in zip(ids.iloc[va],yv,pr):rows.append({'ID_POLIGONO':pid,'repeat':s['repeat'],'fold':s['fold'],'y_true':truth,'y_pred':prediction,'pipeline':name,'feature_representation':rep,'model':name.split('_')[0]})
   model=fit.named_steps['model']
   if name.startswith('ENET'):
    for f,c in zip(retained,np.asarray(model.coef_).ravel()):stab.append({'pipeline':name,'repeat':s['repeat'],'fold':s['fold'],'feature_name':f,'value':c,'selected':int(abs(c)>1e-12),'kind':'elasticnet_coefficient'})
   else:
    for f,v in zip(retained,model.feature_importances_):stab.append({'pipeline':name,'repeat':s['repeat'],'fold':s['fold'],'feature_name':f,'value':v,'selected':1,'kind':'tree_importance'})
   pd.DataFrame(rows).to_parquet(pred_path,index=False);pd.DataFrame(hp).to_csv(hp_path,index=False);pd.DataFrame(stab).to_parquet(stab_path,index=False)
   print(name,s['repeat'],s['fold'],'RMSE',round(mean_squared_error(yv,pr)**.5,4),'retained',len(retained),flush=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('pipelines',nargs='*');a=ap.parse_args();bad=set(a.pipelines)-set(PIPELINES)
 if bad:raise ValueError(bad)
 main(a.pipelines or PIPELINES)
