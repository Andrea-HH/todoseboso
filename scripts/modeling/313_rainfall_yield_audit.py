"""Read-only rainfall audit. Refuses to overwrite a previous audit."""
import argparse
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from family_1.rainfall_audit import audit

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--run-id', default='v1')
    args = p.parse_args()
    if Path(args.run_id).name != args.run_id or args.run_id in ('.','..'):
        p.error('run-id must be a simple directory name')
    result = audit(ROOT/'outputs/data_audit/family_1/rainfall_yield'/args.run_id)
    print({k:v for k,v in result.items() if k!='inputs'})
    if not result['passed']: raise SystemExit('Audit failed; modeling must stop')
