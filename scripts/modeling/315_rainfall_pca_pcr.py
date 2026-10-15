"""E8 phased runner using existing rainfall artifacts and exact frozen splits."""
import argparse
import os
os.environ.setdefault('OMP_NUM_THREADS','1')
from pathlib import Path
import sys
import json
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
import geopandas as gpd
from family_1.rainfall_audit import SHAPE,sha
from family_1.rainfall_pcr_audit import REFERENCE,FEATURES,DICTIONARY,load_data,audit_predictors,diagnose_profiles

def main(run_id,phase):
    out=ROOT/'outputs/modeling/family_1/rainfall_yield/e8'/run_id
    if phase in ('audit','all'):
        out.mkdir(parents=True,exist_ok=False)
        for directory in ('tables','figures','report','models','splits','checkpoints'):(out/directory).mkdir()
        protected=list(REFERENCE.rglob('*'))+list(FEATURES.parent.iterdir())
        protected += list((ROOT/'src/family_1').glob('rainfall_*.py'))
        # Protect E0–E7 data/results and the immutable Champion input artifacts.
        champion=ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization'
        protected += [champion/'predictions/oof_predictions.parquet',champion/'models/selected_hyperparameters.csv']
        snapshot={str(p.relative_to(ROOT)):sha(p) for p in protected if p.is_file() and not p.name.startswith('rainfall_pcr')}
        (out/'protected_inputs.json').write_text(json.dumps(snapshot,indent=2),encoding='utf-8')
        matrix,train=load_data()
        geo=gpd.read_file(SHAPE).rename(columns={'ID_POLIGON':'ID_POLIGONO'}).to_crs(6372)
        result=audit_predictors(out)
        result.update(diagnose_profiles(matrix,train,geo,out))
        (out/'audit_manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print('E8 audit:',result,flush=True)
    if phase in ('model','all'):
        from family_1.rainfall_pcr import run
        run(out)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--run-id',default='v1')
    parser.add_argument('--phase',choices=['audit','model','all'],default='all')
    args=parser.parse_args()
    if Path(args.run_id).name!=args.run_id or args.run_id in ('.','..'):parser.error('Simple run-id required')
    main(args.run_id,args.phase)
