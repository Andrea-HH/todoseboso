"""Bounded reverse correction, preserving all earlier bridge artifacts."""
from pathlib import Path
import sys,json,hashlib,time,warnings
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import KFold
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.geoc_bridge import data,OLD,OUT as BRIDGE
from src.geoc_reverse import evaluate,GRID,AMPLITUDES
OUT=BRIDGE/'reverse/v1'

def work(index):
    destination=OUT/'checkpoints'/f'{index:02d}.joblib'
    if destination.exists():return
    a=data();t=a['train'];groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO')
    if index<65:
        protocol,repeat,fold,tr,va,inner=joblib.load(OLD/'cache/frozen65_splits.joblib')[index];cv_protocol=protocol
    else:
        memberships=pd.read_csv(BRIDGE/'cache/geoc_memberships.csv');split=sorted(memberships.split_id.unique())[index-65];g=memberships[memberships.split_id==split]
        pos={v:i for i,v in enumerate(t.ID_POLIGONO)};tr=np.array([pos[v] for v in g[g.role=='pseudo_train'].ID_POLIGONO]);va=np.array([pos[v] for v in g[g.role=='pseudo_target'].ID_POLIGONO])
        protocol='geoc_target_matched';repeat=int(split.rsplit('_',1)[1]);fold=1;inner=list(KFold(4,shuffle=True,random_state=2026).split(tr));cv_protocol='random'
    start=time.perf_counter()
    with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always');pack=evaluate(a,tr,va,inner,cv_protocol,groups)
    rows=[dict(experiment='LOCAL_PLUS_COMPACT_EN',protocol=protocol,repeat=repeat,fold=fold,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(t.iloc[i].RENDIMIENTO_T_HA),y_pred=float(v)) for i,v in zip(va,pack['prediction'])]
    registry=dict(protocol=protocol,repeat=repeat,fold=fold,amplitude=pack['selection']['amplitude'],params=pack['selection']['params'],inner_rmse=pack['selection']['rmse'],seconds=time.perf_counter()-start,warnings=[dict(category=w.category.__name__,message=str(w.message)) for w in captured])
    joblib.dump(pack,OUT/'models'/f'{index:02d}.joblib',compress=3);joblib.dump(dict(predictions=rows,registry=registry),destination,compress=3)
    print(f'reverse {index+1}/81 {protocol}',flush=True)

if __name__=='__main__':
    if (OUT/'execution_complete.json').exists():raise FileExistsError('Preserve complete version')
    for s in ['models','checkpoints','tables','audit']:(OUT/s).mkdir(parents=True,exist_ok=True)
    files=[BRIDGE/'cache/prepared.joblib',BRIDGE/'cache/geoc_memberships.csv',BRIDGE/'tables/oof_predictions.parquet',OLD/'cache/frozen65_splits.joblib',OLD/'cache/groups.csv',ROOT/'src/geoc_reverse.py',ROOT/'src/geoc_bridge.py',ROOT/'src/geoc_local04d_snapshot.py',ROOT/'src/family_4/conditional_response.py',Path(__file__)]
    cfg=dict(base='Frozen Local04D, k24 alpha30 power1 PCA20 transductive197',corrector='Elastic Net on four original CT3 predictors; re-estimated for local residual targets, not original CT3 coefficients',grid=GRID,amplitudes=AMPLITUDES,selection='complete inner OOF RMSE; rounded12 tie smaller amplitude then stronger alpha, smaller l1ratio',intercept='standard ElasticNet intercept allowed, as in direct CT3; no regional rules',validation='65 original folds plus16 original97/41 masks; Local04D residual targets crossfitted with same-protocol inner subpartitions, no external labels in targets or selection',limitations='fixed-prediction exploratory analysis, reused labels, crossfit/refit base size mismatch; direction contrast also changes corrector architecture and grid, not a pure causal direction experiment',no_GeoC_change=True,no_new_PRED=True,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    f=OUT/'frozen_design.json'
    if f.exists():assert json.loads(f.read_text())==cfg
    else:f.write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    joblib.Parallel(n_jobs=4,backend='loky')(joblib.delayed(work)(i) for i in range(81))
    packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(81)]
    p=pd.DataFrame([r for q in packs for r in q['predictions']]);assert len(p)==2450
    p.to_parquet(OUT/'tables/new_oof_predictions.parquet',index=False);p.to_csv(OUT/'tables/new_oof_predictions.csv',index=False)
    pd.DataFrame([q['registry'] for q in packs]).to_parquet(OUT/'tables/registry.parquet',index=False)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in cfg['source_sha256'].items())
    (OUT/'execution_complete.json').write_text(json.dumps(dict(status='evaluation_complete',new_oof=2450,new_external_predictors=81,protected_sources_unchanged=True,warnings=sum(len(q['registry']['warnings']) for q in packs)),indent=2),encoding='utf-8')
