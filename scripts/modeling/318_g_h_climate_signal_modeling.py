"""G/H controlled modeling after descriptive phases 316 and 317."""
import os,sys,argparse
from pathlib import Path
os.environ.setdefault('OMP_NUM_THREADS','1')
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from family_1.climate_signal_modeling import run_models
from family_1.climate_signal_features import paths
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-id',default='v1');p.add_argument('--phase',choices=['model','all'],default='model');a=p.parse_args()
    if Path(a.run_id).name!=a.run_id or a.run_id in ['.','..']:p.error('Simple run-id required')
    if a.phase=='all':
        from family_1.climate_signal_descriptive import prepare_g,prepare_h
        if not (paths('G',a.run_id)[0]/'descriptive_complete.json').exists():prepare_g(a.run_id)
        if not (paths('H',a.run_id)[0]/'descriptive_complete.json').exists():prepare_h(a.run_id)
    run_models(a.run_id)
