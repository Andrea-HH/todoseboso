"""Real-data parity and performance amendment before using faster execution."""
from pathlib import Path
import sys,json,hashlib,time
import numpy as np
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.four_expert_combinations import OUT,load_assets,local_sets
from src.four_expert_fast_execution import ORIGINAL,equivalent_weighted_local_ridge
from src.geoc_signal_research import SignalRepresentation
def main():
    a=load_assets();aa=a['a'];pos=aa['train_global'];plan=joblib.load(OUT/'frozen81_splits.joblib');checks=[]
    with threadpool_limits(limits=1):
        for fi in [0,13,50,55,60,65,72,80]:
            _,_,_,tr,va,inner=plan[fi]
            for cols in [local_sets()['FULL7'],local_sets()['NO_PLANET']]:
                rep=SignalRepresentation(cols).fit(a['features197'].iloc[pos[tr]]);x=rep.transform(a['features197'])
                for matrix in [x,aa['x']]:
                    y=np.full(len(matrix),np.nan);y[pos[tr]]=a['y'][tr];begin=time.perf_counter();one=ORIGINAL(matrix,aa['distance'],y,pos[tr],pos[va],k=24,alpha=30.,distance_power=1.);slow=time.perf_counter()-begin;begin=time.perf_counter();two=equivalent_weighted_local_ridge(matrix,aa['distance'],y,pos[tr],pos[va],k=24,alpha=30.,distance_power=1.);fast=time.perf_counter()-begin;difference=float(np.max(abs(one-two)));assert difference<1e-12;checks.append(dict(execution_index=fi,dimensions=matrix.shape[1],max_difference=difference,original_seconds=slow,fast_seconds=fast))
    files=[ROOT/'src/four_expert_fast_execution.py',ROOT/'src/local_ridge_sufficient_statistics.py',ROOT/'scripts/507_run_four_expert_fast.py',ROOT/'scripts/508_verify_four_expert_fast.py'];cfg=dict(reason='Avoid repeated per-query sklearn Ridge setup; exact same weighted primal/dual solve, intercept, alpha, k and tie ordering',no_recipe_or_grid_change=True,parity_checks=len(checks),max_difference=max(r['max_difference'] for r in checks),existing_checkpoints_retained=sorted(p.name for p in (OUT/'checkpoints').glob('*.joblib')),original_total_seconds=sum(r['original_seconds'] for r in checks),fast_total_seconds=sum(r['fast_seconds'] for r in checks),source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files});(OUT/'performance_amendment.json').write_text(json.dumps(cfg,indent=2));(OUT/'audit/fast_parity.json').write_text(json.dumps(checks,indent=2));print(json.dumps({k:v for k,v in cfg.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
