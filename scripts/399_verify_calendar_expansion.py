"""Replay archived expansion models on their original heldout TRAIN rows."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.calendar_expansion import OUT

def replay(fi):
    from src.calendar_execution import install_single_thread_scoring
    install_single_thread_scoring()
    x=pd.read_parquet(OUT/'cache/features_train138.parquet').set_index('ID_POLIGONO')
    maximum=0.;n=0;models=0
    with threadpool_limits(limits=1):
        for f in sorted((OUT/'checkpoints').glob(f'*_{fi:02d}.joblib')):
            pack=joblib.load(f);m=joblib.load(OUT/'models'/f.name);r=pack['registry'];ids=m['validation_ids']
            assert not set(ids)&set(m['train_ids']) and len(m['train_ids'])<138
            expected=pd.DataFrame(pack['predictions']).set_index('ID_POLIGONO').loc[ids,'y_pred'].to_numpy()
            actual=m['model'].predict(x.loc[ids]);error=float(np.max(abs(actual-expected)));assert error<1e-10
            maximum=max(maximum,error);n+=len(ids);models+=1
    return models,n,maximum

if __name__=='__main__':
    dest=OUT/'audit/replay.json'
    if dest.exists():raise FileExistsError('Preserve replay')
    cfg=json.loads((OUT/'frozen_design.json').read_text())
    for path,sha in cfg['sha256'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha
    results=joblib.Parallel(n_jobs=4)(joblib.delayed(replay)(i) for i in range(65))
    result=dict(models=sum(a[0] for a in results),predictions=sum(a[1] for a in results),max_absolute_difference=max(a[2] for a in results),protected_hashes_unchanged=True,disjoint_train_validation=True,no_full138_fit=True,no_PRED=True)
    assert result['models']==2210 and result['predictions']==60996
    dest.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
