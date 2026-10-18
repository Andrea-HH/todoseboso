"""Same frozen worker, with equivalent Ridge and C-T3 preprocessing reuse."""
from pathlib import Path
import sys,os,json,hashlib,importlib.util
os.environ.setdefault('OMP_NUM_THREADS','1');os.environ.setdefault('MKL_NUM_THREADS','1');os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import joblib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.four_expert_combinations import OUT
def work(fi):
    from src.four_expert_fast_execution import activate as activate_ridge
    from src.four_expert_fast_tuner import activate as activate_tuner
    activate_ridge();activate_tuner();spec=importlib.util.spec_from_file_location('original504',ROOT/'scripts/504_run_four_expert_combinations.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.work(fi)
def main():
    for filename in ['frozen_design.json','performance_amendment.json','tuner_performance_amendment.json']:
        cfg=json.loads((OUT/filename).read_text());assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    scope=sys.argv[1] if len(sys.argv)>1 else 'all';jobs={'random':range(50),'territorial':range(50,65),'fresh':range(65,81),'all':range(81)}[scope];workers={'random':6,'territorial':2,'fresh':6,'all':6}[scope];joblib.Parallel(n_jobs=workers,backend='loky')(joblib.delayed(work)(i) for i in jobs)
if __name__=='__main__':main()
