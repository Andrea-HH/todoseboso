"""Freeze Section J design before fitting any yield model."""
from pathlib import Path
import argparse,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from src.family_1.j_incremental_yield import audit
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-id',default='v1');a=p.parse_args()
    if Path(a.run_id).name!=a.run_id or a.run_id in ['.','..']:p.error('Simple run-id required')
    audit(a.run_id)
