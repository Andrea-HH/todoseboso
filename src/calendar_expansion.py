"""Frozen block expansion: nested ElasticNet and conservative CatBoost."""
from pathlib import Path
import json,time,warnings
import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import ElasticNet
from catboost import CatBoostRegressor
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/modeling/agronomic_calendar/expansion/v1'
BASE=ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache'

class BlockEstimator:
    def __init__(self,columns,history,indicators,algorithm,params):
        self.columns=list(columns);self.history=list(history);self.indicators=indicators;self.algorithm=algorithm;self.params=params.copy()
    def _raw(self,frame):
        x=frame[self.columns].to_numpy(float);bad=~np.isfinite(x);z=np.where(bad,self.medians_,x)
        return np.column_stack([z,bad[:,self.indicator_positions_].astype(float)]) if self.indicator_positions_ else z
    def fit(self,frame,y,audit=False):
        self.warnings_=[];x=frame[self.columns].to_numpy(float)
        self.medians_=np.array([np.median(v[np.isfinite(v)]) if np.isfinite(v).any() else 0. for v in x.T])
        self.indicator_positions_=[i for i,c in enumerate(self.columns) if c.startswith(('HIST_MEAN_','DELTA_'))] if self.indicators else []
        self.names_=self.columns+[self.columns[i]+'__missing' for i in self.indicator_positions_]
        self.is_history_=np.array([c in self.history for c in self.columns]+[True]*len(self.indicator_positions_))
        a=self._raw(frame);self.mean_=a.mean(axis=0);self.scale_=a.std(axis=0);self.scale_[self.scale_<1e-12]=1.
        z=(a-self.mean_)/self.scale_;self.support_=np.std(z,axis=0)>1e-12
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            if self.algorithm=='EN':
                self.gamma_=self.params['gamma'];self.weights_=np.where(self.is_history_,self.gamma_,1.)
                self.model_=ElasticNet(alpha=self.params['alpha'],l1_ratio=self.params['l1_ratio'],max_iter=100000,tol=1e-7,selection='cyclic').fit(z*self.weights_,np.asarray(y))
            else:
                self.gamma_=1.;self.weights_=np.ones(z.shape[1]);fw=np.where(self.is_history_[self.support_],.5,1.).tolist()
                self.model_=CatBoostRegressor(loss_function='RMSE',grow_policy='SymmetricTree',boosting_type='Plain',bootstrap_type='No',random_strength=0,border_count=64,leaf_estimation_iterations=1,allow_writing_files=False,thread_count=1,random_seed=2026,verbose=False,feature_weights=fw,**self.params).fit(z[:,self.support_],np.asarray(y))
        self.warnings_=[dict(category=w.category.__name__,message=str(w.message)) for w in caught]
        if not audit:return self
        if self.algorithm=='EN':
            self.effects_=self.model_.coef_*self.weights_;self.used_=abs(self.effects_)>1e-10
            self.split_counts_=np.zeros(len(self.names_),int)
        else:
            importance=self.model_.get_feature_importance(type='PredictionValuesChange');self.used_=np.zeros(len(self.names_),bool);self.used_[self.support_]=importance>0
            self.effects_=np.full(len(self.names_),np.nan);self.split_counts_=np.zeros(len(self.names_),int)
            # JSON splits give actual usage; importance is not used as a causal effect.
            import tempfile
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'model.json';self.model_.save_model(str(path),format='json');trees=json.loads(path.read_text())['oblivious_trees']
            counts=np.zeros(int(self.support_.sum()),int)
            for tree in trees:
                for split in tree.get('splits') or []:
                    if split['split_type']=='FloatFeature':counts[split['float_feature_index']]+=1
            self.split_counts_[self.support_]=counts;self.used_=self.split_counts_>0
        return self
    def predict(self,frame):
        z=(self._raw(frame)-self.mean_)/self.scale_
        return self.model_.predict(z*self.weights_ if self.algorithm=='EN' else z[:,self.support_])

def metric(y,p):
    y=np.asarray(y);e=np.asarray(p)-y;den=np.sum((y-y.mean())**2)
    return dict(rmse=float(np.sqrt(np.mean(e**2))),mae=float(np.mean(abs(e))),bias=float(e.mean()),r2=float(1-np.sum(e**2)/den) if den>1e-14 else np.nan)

def work_fold(fi):
    config=json.loads((OUT/'frozen_design.json').read_text());t=pd.read_parquet(BASE/'train138.parquet')
    x=pd.read_parquet(OUT/'cache/features_train138.parquet');assert x.ID_POLIGONO.tolist()==t.ID_POLIGONO.tolist()
    protocol,repeat,fold,tr,va,inner=joblib.load(BASE/'frozen65_splits.joblib')[fi];y=t.RENDIMIENTO_T_HA.to_numpy()
    assert not set(tr)&set(va) and set(tr)|set(va)==set(range(138))
    start=time.perf_counter();fits=0
    with threadpool_limits(limits=1):
        for block,spec in config['specs'].items():
            for algorithm in ['EN','CB']:
                checkpoint=OUT/'checkpoints'/f'{algorithm}_{block}_{fi:02d}.joblib'
                if checkpoint.exists():continue
                grid=config['en_grid'] if algorithm=='EN' else config['cb_grid']
                if algorithm=='EN':
                    grid=[dict(**params,gamma=g) for params in grid for g in ([0.,.25,.5,1.] if spec['history'] else [1.])]
                scores=[];logs=[];candidate_start=time.perf_counter()
                for ci,params in enumerate(grid):
                    pred=np.full(len(tr),np.nan);seen=np.zeros(len(tr),int)
                    for a,b in inner:
                        assert not set(a)&set(b) and set(a)|set(b)==set(range(len(tr)))
                        model=BlockEstimator(spec['columns'],spec['history'],spec.get('indicators',False),algorithm,params).fit(x.iloc[tr[a]],y[tr[a]])
                        pred[b]=model.predict(x.iloc[tr[b]]);seen[b]+=1;logs.extend(model.warnings_);fits+=1
                    assert (seen==1).all() and np.isfinite(pred).all()
                    scores.append(dict(candidate=ci,params=params,**metric(y[tr],pred)))
                best=min(scores,key=lambda r:(round(r['rmse'],12),r['candidate']))
                model=BlockEstimator(spec['columns'],spec['history'],spec.get('indicators',False),algorithm,best['params']).fit(x.iloc[tr],y[tr],audit=True);fits+=1;logs.extend(model.warnings_)
                prediction=model.predict(x.iloc[va]);assert np.isfinite(prediction).all()
                key=dict(experiment=algorithm+'_'+block,algorithm=algorithm,block=block,protocol=protocol,repeat=repeat,fold=fold)
                registry=dict(**key,n_input=len(spec['columns']),n_design=len(model.names_),n_selected=int(model.used_.sum()),n_selected_history=int((model.used_&model.is_history_).sum()),n_train=len(tr),params=json.dumps(best['params']),inner_rmse=best['rmse'],seconds=time.perf_counter()-candidate_start,warnings=len(logs),fits=len(grid)*len(inner)+1)
                records=[dict(**key,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(v)) for i,v in zip(va,prediction)]
                usage=[dict(**key,feature=f,used=bool(u),history=bool(h),effect_standardized=float(e),split_count=int(n)) for f,u,h,e,n in zip(model.names_,model.used_,model.is_history_,model.effects_,model.split_counts_)]
                joblib.dump(dict(model=model,train_ids=t.iloc[tr].ID_POLIGONO.tolist(),validation_ids=t.iloc[va].ID_POLIGONO.tolist(),registry=registry),OUT/'models'/f'{algorithm}_{block}_{fi:02d}.joblib',compress=3)
                joblib.dump(dict(predictions=records,registry=registry,usage=usage,tuning=[dict(**key,**r,selected=r is best) for r in scores],warnings=logs),checkpoint,compress=3)
    print(f'FOLD {fi+1}/65 {protocol} complete {round(time.perf_counter()-start,1)}s',flush=True)
    return fits
