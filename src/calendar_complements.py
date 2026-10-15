"""Nested representation selection and honest cross-fitted residual targets."""
from pathlib import Path
import json,hashlib,warnings,time
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import KFold,GroupKFold
from sklearn.linear_model import Ridge
from sklearn.tree import DecisionTreeRegressor
from threadpoolctl import threadpool_limits
from src.calendar_expansion import BlockEstimator,metric
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/modeling/agronomic_calendar/complements/v1'
OLD=ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache'

def subcv(frame,pos,protocol,groups):
    if protocol=='random':return list(KFold(min(4,len(pos)),shuffle=True,random_state=2026).split(pos))
    g=groups.loc[frame.iloc[pos].ID_POLIGONO,protocol].to_numpy()
    if len(set(g))<2:raise ValueError('Insufficient groups: no random fallback')
    return list(GroupKFold(min(4,len(set(g)))).split(pos,groups=g))

class Corrector:
    def __init__(self,columns,kind,params):self.columns=columns;self.kind=kind;self.params=params
    def fit(self,x,residual):
        a=x[self.columns].to_numpy(float)
        self.medians_=np.array([np.median(v[np.isfinite(v)]) if np.isfinite(v).any() else 0. for v in a.T])
        a=np.where(np.isfinite(a),a,self.medians_)
        self.mean_=a.mean(axis=0);self.scale_=a.std(axis=0);self.scale_[self.scale_<1e-12]=1.
        z=(a-self.mean_)/self.scale_
        # Centered predictions cannot become an arbitrary regional intercept.
        r=np.asarray(residual)-np.mean(residual)
        self.model_=Ridge(alpha=self.params['alpha']*len(r),fit_intercept=False,solver='svd') if self.kind=='ridge' else DecisionTreeRegressor(random_state=2026,**self.params)
        self.model_.fit(z,r);self.offset_=float(np.mean(self.model_.predict(z)))
        return self
    def predict(self,x):
        a=x[self.columns].to_numpy(float);a=np.where(np.isfinite(a),a,self.medians_)
        return self.model_.predict((a-self.mean_)/self.scale_)-self.offset_

def tune(frame,y,pos,cv,cfg,cache,events):
    signature=hashlib.sha256(repr((tuple(pos),tuple((tuple(a),tuple(b)) for a,b in cv),cfg['representations'],cfg['en_grid'])).encode()).hexdigest()
    path=cache/(signature+'.joblib')
    if path.exists():return joblib.load(path)
    reps={};scores=[]
    for name,cols in cfg['representations'].items():
        candidates=[]
        for ci,params in enumerate(cfg['en_grid']):
            pred=np.full(len(pos),np.nan);seen=np.zeros(len(pos),int)
            for a,b in cv:
                assert not set(pos[a])&set(pos[b])
                m=BlockEstimator(cols,[],False,'EN',params).fit(frame.iloc[pos[a]],y[pos[a]])
                events.extend(m.warnings_);pred[b]=m.predict(frame.iloc[pos[b]]);seen[b]+=1
            assert (seen==1).all() and np.isfinite(pred).all()
            candidates.append(dict(candidate=ci,params=params,rmse=metric(y[pos],pred)['rmse']))
        best=min(candidates,key=lambda v:(round(v['rmse'],12),v['candidate']))
        m=BlockEstimator(cols,[],False,'EN',best['params']).fit(frame.iloc[pos],y[pos],audit=True);events.extend(m.warnings_)
        reps[name]=dict(model=m,params=best['params'],inner_rmse=best['rmse'])
        scores.extend(dict(representation=name,**v) for v in candidates)
    chosen=min(reps,key=lambda name:(round(reps[name]['inner_rmse'],12),list(reps).index(name)))
    pack=dict(representations=reps,chosen=chosen,train_positions=pos,scores=scores)
    joblib.dump(pack,path,compress=3);return pack

def honest_residual(frame,y,pos,cv,protocol,groups,cfg,cache,events):
    pred=np.full(len(pos),np.nan);seen=np.zeros(len(pos),int)
    for a,b in cv:
        tr=pos[a];va=pos[b]
        fit=tune(frame,y,tr,subcv(frame,tr,protocol,groups),cfg,cache,events)
        assert not set(fit['train_positions'])&set(va)
        pred[b]=fit['representations'][fit['chosen']]['model'].predict(frame.iloc[va]);seen[b]+=1
    assert (seen==1).all() and np.isfinite(pred).all()
    return y[pos]-pred

def fold(fi):
    dest=OUT/'checkpoints'/f'{fi:02d}.joblib'
    if dest.exists():return
    cfg=json.loads((OUT/'frozen_design.json').read_text());frame=pd.read_parquet(OUT/'features_train138.parquet')
    y=frame.RENDIMIENTO_T_HA.to_numpy();groups=pd.read_csv(ROOT/'outputs/modeling/family_7/expansion/v1/splits/group_memberships.csv').set_index('ID_POLIGONO')
    protocol,repeat,foldid,tr,va,inner=joblib.load(OLD/'frozen65_splits.joblib')[fi]
    cache=OUT/'context_cache'/f'{fi:02d}';cache.mkdir(parents=True,exist_ok=True)
    events=[];start=time.perf_counter();records=[];registry=[];models={};tuning=[]
    def save_prediction(name,pred):
        records.extend(dict(experiment=name,protocol=protocol,repeat=repeat,fold=foldid,ID_POLIGONO=frame.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(v)) for i,v in zip(va,pred))
    with threadpool_limits(limits=1):
        base=tune(frame,y,tr,inner,cfg,cache,events)
        for name,pack in base['representations'].items():
            save_prediction(name,pack['model'].predict(frame.iloc[va]))
            registry.append(dict(experiment=name,representation=name,params=pack['params'],inner_rmse=pack['inner_rmse'],n_selected=int(pack['model'].used_.sum())))
        selected=base['representations'][base['chosen']]['model'];basepred=selected.predict(frame.iloc[va]);save_prediction('SELECTED_BASE',basepred)
        # Every inner correction target is generated by a separately tuned base
        # whose fitting and tuning sets exclude the target observation.
        contexts=[]
        for a,b in inner:
            aa=tr[a];bb=tr[b];cv=subcv(frame,aa,protocol,groups)
            fit=tune(frame,y,aa,cv,cfg,cache,events)
            res=honest_residual(frame,y,aa,cv,protocol,groups,cfg,cache,events)
            bp=fit['representations'][fit['chosen']]['model'].predict(frame.iloc[bb])
            contexts.append((aa,bb,res,bp))
        residual=honest_residual(frame,y,tr,inner,protocol,groups,cfg,cache,events)
        for name,spec in cfg['corrections'].items():
            candidates=[dict(amplitude=0.,params={},rmse=None)]
            for params in spec['grid']:
                p=np.full(len(tr),np.nan);delta=np.full(len(tr),np.nan)
                for (a,b),(aa,bb,res,bp) in zip(inner,contexts):
                    m=Corrector(spec['columns'],spec['kind'],params).fit(frame.iloc[aa],res)
                    p[b]=bp;delta[b]=m.predict(frame.iloc[bb])
                if candidates[0]['rmse'] is None:candidates[0]['rmse']=metric(y[tr],p)['rmse']
                for amp in [.25,.5]:candidates.append(dict(amplitude=amp,params=params,rmse=metric(y[tr],p+amp*delta)['rmse']))
            best=min(enumerate(candidates),key=lambda v:(round(v[1]['rmse'],12),v[1]['amplitude'],v[0]))[1]
            m=None
            if best['amplitude']:
                m=Corrector(spec['columns'],spec['kind'],best['params']).fit(frame.iloc[tr],residual)
                prediction=basepred+best['amplitude']*m.predict(frame.iloc[va])
            else:prediction=basepred.copy()
            assert np.isfinite(prediction).all();save_prediction(name,prediction)
            models[name]=dict(model=m,amplitude=best['amplitude'])
            registry.append(dict(experiment=name,representation=base['chosen'],**best))
            tuning.extend(dict(experiment=name,**v) for v in candidates)
        joblib.dump(dict(base=base,corrections=models,train_positions=tr,validation_positions=va),OUT/'models'/f'{fi:02d}.joblib',compress=3)
    joblib.dump(dict(predictions=records,registry=registry,tuning=tuning,warnings=events,seconds=time.perf_counter()-start,protocol=protocol,repeat=repeat,fold=foldid),dest,compress=3)
    print(f'{fi+1}/65 {protocol} {time.perf_counter()-start:.1f}s base={base["chosen"]}',flush=True)
