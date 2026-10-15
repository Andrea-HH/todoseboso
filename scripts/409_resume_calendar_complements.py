"""Resume frozen statistical design using audited X-transform memoization."""
from pathlib import Path
import sys,json,hashlib,time,importlib
import numpy as np
import pandas as pd
import joblib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.calendar_complements_execution import CachedEN,run_fold
from src.calendar_expansion import BlockEstimator
from src.calendar_complements import OUT

if __name__=='__main__':
    runner=importlib.import_module('scripts.407_calendar_complements');cfg=runner.prepare()
    x=pd.read_parquet(OUT/'features_train138.parquet');cols=cfg['representations']['UNION11']
    maximum=0.
    for params in cfg['en_grid']:
        a=BlockEstimator(cols,[],False,'EN',params).fit(x.iloc[:80],x.RENDIMIENTO_T_HA.iloc[:80].to_numpy(),audit=True)
        b=CachedEN(cols,[],False,'EN',params).fit(x.iloc[:80],x.RENDIMIENTO_T_HA.iloc[:80].to_numpy(),audit=True)
        for left,right in [(a.predict(x.iloc[80:100]),b.predict(x.iloc[80:100])),(a.model_.coef_,b.model_.coef_), (a.scale_,b.scale_)]:
            delta=float(np.max(abs(left-right)));maximum=max(maximum,delta);assert delta==0.
    audit=dict(description='Memoize identical X-only preprocessing keyed by column list and global row indices; same fixed dataframe in each worker, no label caching.',maximum_difference=maximum,configurations_checked=16,existing_checkpoints=len(list((OUT/'checkpoints').glob('*.joblib'))),execution_source_sha256=hashlib.sha256((ROOT/'src/calendar_complements_execution.py').read_bytes()).hexdigest())
    (OUT/'audit/execution_memoization.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    # Interrupted writes, if any, are quarantined rather than consumed/deleted.
    quarantine=OUT/'audit/interrupted_writes'
    for p in list((OUT/'context_cache').rglob('*.joblib'))+list((OUT/'checkpoints').glob('*.joblib')):
        try:joblib.load(p)
        except Exception:
            target=quarantine/p.relative_to(OUT);target.parent.mkdir(parents=True,exist_ok=True);p.replace(target)
    start=time.perf_counter()
    joblib.Parallel(n_jobs=4,backend='loky')(joblib.delayed(run_fold)(i) for i in range(65))
    packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(65)]
    p=pd.DataFrame([r for a in packs for r in a['predictions']]);assert len(p)==11*1794
    for name in ['predictions','registry','tuning']:
        pd.DataFrame([dict(protocol=a['protocol'],repeat=a['repeat'],fold=a['fold'],**r) if name!='predictions' else r for a in packs for r in a[name]]).to_parquet(OUT/'tables'/f'{name}.parquet',index=False)
    assert all(runner.sha(ROOT/s)==h for s,h in cfg['sha256'].items())
    (OUT/'audit/warnings.json').write_text(json.dumps([r for a in packs for r in a['warnings']],indent=2),encoding='utf-8')
    (OUT/'execution_complete.json').write_text(json.dumps(dict(new_configurations=11,external_folds=65,new_oof=len(p),seconds_last_segment=time.perf_counter()-start,warnings=sum(len(a['warnings']) for a in packs),protected_sources_unchanged=True),indent=2),encoding='utf-8')
