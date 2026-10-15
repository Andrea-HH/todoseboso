"""H joint descriptive exploration; requires audited G."""
import os,sys,argparse
from pathlib import Path
os.environ.setdefault('OMP_NUM_THREADS','1')
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from family_1.climate_signal_descriptive import prepare_h
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-id',default='v1');a=p.parse_args()
    if Path(a.run_id).name!=a.run_id or a.run_id in ['.','..']:p.error('Simple run-id required')
    prepare_h(a.run_id)
