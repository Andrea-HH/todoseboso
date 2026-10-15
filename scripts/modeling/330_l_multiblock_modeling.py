from pathlib import Path
import sys,argparse,os
os.environ.setdefault('OMP_NUM_THREADS','1');os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from src.family_1.l_representation import run
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-id',default='v1');p.add_argument('--workers',type=int,default=3);a=p.parse_args()
    if Path(a.run_id).name!=a.run_id or a.run_id in ['.','..']:p.error('Simple run ID required')
    run(a.run_id,a.workers)
