"""Resume frozen six-mixture design with documented equivalent Ridge solver."""
from pathlib import Path
import sys,os,json,hashlib,time,importlib.util
os.environ.setdefault('OMP_NUM_THREADS','1');os.environ.setdefault('MKL_NUM_THREADS','1');os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import numpy as np
import pandas as pd
import joblib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.four_expert_combinations import OUT
def work(fi):
    from src.four_expert_fast_execution import activate
    activate();spec=importlib.util.spec_from_file_location('original504',ROOT/'scripts/504_run_four_expert_combinations.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.work(fi)
def main():
    cfg=json.loads((OUT/'frozen_design.json').read_text());amend=json.loads((OUT/'performance_amendment.json').read_text());assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in {**cfg['source_sha256'],**amend['source_sha256']}.items());started=time.perf_counter();jobs=[int(sys.argv[1])] if len(sys.argv)>1 else list(range(81));joblib.Parallel(n_jobs=1 if len(jobs)==1 else cfg['workers'],backend='loky')(joblib.delayed(work)(fi) for fi in jobs)
    if len(jobs)==1:return
    packs=[joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib') for fi in range(81)]
    for field in ['predictions','details','parity']:pd.DataFrame([dict(execution_index=fi,**r) if 'execution_index' not in r else r for fi,p in enumerate(packs) for r in p[field]]).to_parquet(OUT/'tables'/f'{field}.parquet',index=False)
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in {**cfg['source_sha256'],**amend['source_sha256']}.items());(OUT/'execution_complete.json').write_text(json.dumps(dict(status='complete',folds=81,original_folds=65,fresh_splits=16,experiments=6,controls=4,seconds=time.perf_counter()-started,no_PRED=True,no_champion_change=True,performance_only_amendment=True),indent=2));print('All81 folds complete',flush=True)
if __name__=='__main__':main()
