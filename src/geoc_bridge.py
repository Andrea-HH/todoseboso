"""Controlled CT3/Local04D comparison on frozen splits and honest residuals."""
from pathlib import Path
import json,time
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
from threadpoolctl import threadpool_limits
from src.geoc_local04d_snapshot import haversine_distance_matrix,normalized_distance_matrix,predict_weighted_local_ridge
from src.ct3_residual_conditional.models import tune_base
ROOT=Path(__file__).resolve().parents[1]
GEO=ROOT.parent/'fira/GeoC'
OLD=ROOT/'outputs/modeling/ct3_residual_conditional/v1'
OUT=ROOT/'outputs/modeling/geoc_bridge/v1'

def local_prediction(x,d,observed,query,target):
    observed=np.asarray(observed,int);query=np.asarray(query,int)
    assert not set(observed)&set(query) and len(observed)==len(target)
    y=np.full(len(x),np.nan);y[observed]=np.asarray(target,float)
    return predict_weighted_local_ridge(x,d,y,observed,query,k=24,alpha=30.,distance_power=1.)

def data():
    return joblib.load(OUT/'cache/prepared.joblib')

def fold(fi):
    path=OUT/'checkpoints'/f'original_{fi:02d}.joblib'
    if path.exists():return
    start=time.perf_counter();a=data();t=a['train'];x=a['x'];d=a['distance'];pos=a['train_global'];y=t.RENDIMIENTO_T_HA.to_numpy()
    plan=joblib.load(OLD/'cache/execution_plan.joblib')[fi];tr=plan['train_positions'];va=plan['validation_positions'];index={int(v):j for j,v in enumerate(tr)}
    def base(key):return joblib.load(OLD/'base_cache'/f'{key}.joblib')['model']
    with threadpool_limits(limits=1):
        ctmodel=base(plan['outer_base_key']);ct=ctmodel.predict(t.iloc[va]);loc=local_prediction(x,d,pos[tr],pos[va],y[tr])
        cfin=np.full(len(tr),np.nan);lin=np.full(len(tr),np.nan);rin=np.full(len(tr),np.nan);ledger=[]
        for item in plan['inner']:
            aa=item['train_positions'];bb=item['validation_positions'];bpos=[index[int(i)] for i in bb]
            cfin[bpos]=base(item['base_key']).predict(t.iloc[bb]);lin[bpos]=local_prediction(x,d,pos[aa],pos[bb],y[aa])
            deep=np.full(len(aa),np.nan);mapping={int(v):i for i,v in enumerate(aa)}
            for ctx in item['residual_contexts']:
                held=ctx['held_positions'];deep[[mapping[int(v)] for v in held]]=base(ctx['base_key']).predict(t.iloc[held])
                ledger.append(dict(base_key=ctx['base_key'],residual_target_positions=held.tolist(),excluded_external_positions=va.tolist(),excluded_inner_positions=bb.tolist()))
            assert np.isfinite(deep).all()
            rin[bpos]=local_prediction(x,d,pos[aa],pos[bb],y[aa]-deep)
        assert np.isfinite(np.column_stack([cfin,lin,rin])).all()
        losses=[float(np.sqrt(np.mean(((1-w)*cfin+w*lin-y[tr])**2))) for w in [0,.25,.5,.75,1]]
        wi=min(range(5),key=lambda i:(round(losses[i],12),i));weight=[0,.25,.5,.75,1][wi]
        scores=[float(np.sqrt(np.mean((cfin+amp*rin-y[tr])**2))) for amp in [0,.25,.5]]
        ai=min(range(3),key=lambda i:(round(scores[i],12),i));amp=[0,.25,.5][ai]
        targets=y[tr]-cfin;raw=local_prediction(x,d,pos[tr],pos[va],targets) if amp else np.zeros(len(va))
        predictions=dict(CT3=ct,LOCAL04D=loc,FIXED50=(ct+loc)/2,INNER_BLEND=(1-weight)*ct+weight*loc,RESIDUAL_LOCAL=ct+amp*raw)
        rows=[dict(experiment=name,protocol=plan['protocol'],repeat=plan['repeat'],fold=plan['fold'],ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(v)) for name,values in predictions.items() for i,v in zip(va,values)]
        pack=dict(ct3=ctmodel,train_positions=tr,validation_positions=va,residual_targets=targets,blend_local_weight=weight,residual_amplitude=amp,blend_inner_rmse=losses,residual_inner_rmse=scores,ledger=ledger)
        joblib.dump(pack,OUT/'models'/f'original_{fi:02d}.joblib',compress=3)
        joblib.dump(dict(predictions=rows,selection=dict(protocol=plan['protocol'],repeat=plan['repeat'],fold=plan['fold'],local_weight=weight,residual_amplitude=amp,seconds=time.perf_counter()-start)),path,compress=3)
    print(f'original {fi+1}/65 {plan["protocol"]}',flush=True)

def target_matched(splitid):
    path=OUT/'checkpoints'/f'{splitid}.joblib'
    if path.exists():return
    a=data();t=a['train'];pos=a['train_global'];index={pid:i for i,pid in enumerate(t.ID_POLIGONO)}
    membership=pd.read_csv(OUT/'cache/geoc_memberships.csv');m=membership[membership.split_id==splitid]
    trainids=m[m.role=='pseudo_train'].ID_POLIGONO.tolist();testids=m[m.role=='pseudo_target'].ID_POLIGONO.tolist()
    tr=np.array([index[v] for v in trainids]);va=np.array([index[v] for v in testids]);assert len(tr)==97 and len(va)==41 and not set(tr)&set(va)
    y=t.RENDIMIENTO_T_HA.to_numpy();cv=list(KFold(4,shuffle=True,random_state=2026).split(tr))
    with threadpool_limits(limits=1):
        model,registry,logs=tune_base(t,y,tr,cv);ct=model.predict(t.iloc[va]);loc=local_prediction(a['x'],a['distance'],pos[tr],pos[va],y[tr])
    rows=[dict(experiment=name,protocol='geoc_target_matched',repeat=int(splitid.rsplit('_',1)[1]),fold=1,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(v)) for name,values in [('CT3',ct),('LOCAL04D',loc),('FIXED50',(ct+loc)/2)] for i,v in zip(va,values)]
    joblib.dump(dict(ct3=model,train_positions=tr,validation_positions=va,registry=registry,warnings=logs),OUT/'models'/f'{splitid}.joblib',compress=3)
    joblib.dump(dict(predictions=rows),path,compress=3);print(splitid,flush=True)
