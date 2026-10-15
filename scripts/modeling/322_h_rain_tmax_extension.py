"""Run the small precipitation/Tmax extension within section H."""
import argparse,os,sys
from pathlib import Path
os.environ.setdefault('OMP_NUM_THREADS','1')
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from family_1.h_rain_tmax_extension import run
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='v1');a=parser.parse_args()
    if Path(a.run_id).name!=a.run_id or a.run_id in ['.','..']:parser.error('Simple run-id required')
    run(a.run_id)
