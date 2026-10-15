"""Execute K.1 and freeze feature policies before any K prediction fitting."""
from pathlib import Path
import sys,argparse,os
os.environ.setdefault('OMP_NUM_THREADS','1')
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from src.family_1.k_geographic_edaphological import audit
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-id',default='v1');a=p.parse_args()
    if Path(a.run_id).name!=a.run_id or a.run_id in ['.','..']:p.error('Simple run ID required')
    audit(a.run_id)
