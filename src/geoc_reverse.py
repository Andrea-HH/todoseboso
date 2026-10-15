"""Reverse residual formulation: fixed Local04D plus compact4 Elastic Net."""
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.linear_model import ElasticNet
from src.family_4.conditional_response import ConditionalFeatures
from src.ct3_residual_conditional.models import CORE
from src.geoc_bridge import local_prediction
from src.family_8.research import subcv

GRID=[dict(alpha=a,l1_ratio=l) for a in [.001,.01,.1,1.] for l in [.1,.5,.9]]
AMPLITUDES=[0.,.25,.5]

def correction_model(params):
    return Pipeline([('repr',ConditionalFeatures(tuple(CORE))),('model',ElasticNet(**params,max_iter=200000,random_state=2026))])

def local_residuals(a,tr,cv):
    y=a['train'].RENDIMIENTO_T_HA.to_numpy();pred=np.full(len(tr),np.nan);seen=np.zeros(len(tr),int)
    for c,d in cv:
        assert not set(tr[c])&set(tr[d])
        pred[d]=local_prediction(a['x'],a['distance'],a['train_global'][tr[c]],a['train_global'][tr[d]],y[tr[c]]);seen[d]+=1
    assert (seen==1).all() and np.isfinite(pred).all()
    return y[tr]-pred

def evaluate(a,tr,va,inner,protocol,groups):
    t=a['train'];y=t.RENDIMIENTO_T_HA.to_numpy();pos=a['train_global'];inside=[];membership=[]
    assert not set(tr)&set(va)
    for c,d in inner:
        aa=tr[c];bb=tr[d];cv=subcv(t,aa,protocol,groups)
        for e,f in cv:
            assert not set(aa[e])&(set(aa[f])|set(bb)|set(va))
            membership.append(dict(fit_positions=aa[e].tolist(),residual_positions=aa[f].tolist(),inner_validation=bb.tolist(),external_validation=va.tolist()))
        residual=local_residuals(a,aa,cv)
        baseline=local_prediction(a['x'],a['distance'],pos[aa],pos[bb],y[aa])
        inside.append((aa,bb,d,residual,baseline))
    baseline_inner=np.full(len(tr),np.nan)
    for aa,bb,d,res,bp in inside:baseline_inner[d]=bp
    candidates=[dict(params=None,amplitude=0.,rmse=float(np.sqrt(np.mean((baseline_inner-y[tr])**2))))]
    for params in GRID:
        delta=np.full(len(tr),np.nan)
        for aa,bb,d,res,bp in inside:
            m=correction_model(params).fit(t.iloc[aa],res);delta[d]=m.predict(t.iloc[bb])
        for amplitude in AMPLITUDES[1:]:candidates.append(dict(params=params,amplitude=amplitude,rmse=float(np.sqrt(np.mean((baseline_inner+amplitude*delta-y[tr])**2)))))
    # Equal scores prefer no correction, stronger alpha and smaller l1_ratio.
    best=min(candidates,key=lambda c:(round(c['rmse'],12),c['amplitude'],-c['params']['alpha'] if c['params'] else 0,c['params']['l1_ratio'] if c['params'] else 0))
    base=local_prediction(a['x'],a['distance'],pos[tr],pos[va],y[tr]);model=None;targets=None
    if best['amplitude']:
        targets=local_residuals(a,tr,inner);model=correction_model(best['params']).fit(t.iloc[tr],targets)
        prediction=base+best['amplitude']*model.predict(t.iloc[va])
    else:prediction=base.copy()
    return dict(model=model,selection=best,tuning=candidates,train_positions=tr,validation_positions=va,residual_targets=targets,prediction=prediction,baseline=base,membership=membership)
