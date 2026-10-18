"""Freeze and run65-fold25-input sensitivity; process-local core configuration."""
from pathlib import Path
import os
import sys
for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[name]='1'
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import argparse
import hashlib
import json
import time
import warnings
import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

OUT=ROOT/'outputs/research/four_final_checks/v1'
PUB=ROOT/'results/four_final_checks/v1'


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def freeze():
    design=dict(date='2026-10-18',models_unchanged=['Reference26','Compact14'],sensitivity='Reference25_NoHHI',
        remove='compact_concentration_hhi from both CT3 and local-expert internal EN, physically absent from input frame',
        outer_folds=65,inner='Original frozen partitions; deeper original group rules and seed2026',
        unchanged='local7, k24, alpha30, inverse geography, geology10 K4/8, EN grids, R3 alpha.01/l1.5 clamp±.25 and intensity0/.5/1',
        tests='Original26 adapter parity on random fold0 and spatial63 before evaluating sensitivity; grouped paired MSE signs with Holm4',
        no_new_final_model=True,no_new_PRED_predictions=True,
        support='Target-free geometry, training-only feature distances, missing R3,26/14 disagreement; descriptive flags, not error probabilities',
        intervals='Nominal80/90 split conformal of saved models, disjoint halves of each external validation fold; rotate halves, no own-label calibration; random primary, grouped protocol diagnostics use calibration labels from excluded territory and do not certify strict transfer',
        group_intervals='Secondary calibration by whole climate profiles with maximum residual per profile; infinite radius if finite-sample rank exceeds available calibration groups',
        interval_limit='No guaranteed interval attached to final138 point model; calibration/evaluation of heldout models only; exchangeability and historical selection remain limitations',
        operational='Freeze final model and files by SHA; subprocess isolated replay from local inputs; source-only clean environment installation limitation explicit',
        selection='No model promotion or hyperparameter changes based on outer results',
        code_sha256={name:hashlib.sha256((ROOT/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for name in ['src/reference26_only.py','src/current_champions.py','scripts/535_no_hhi_reference26.py']})
    path=OUT/'frozen_design.json'
    if path.exists():assert json.loads(path.read_text(encoding='utf-8'))==design
    else:dump(path,design)
    dump(ROOT/'configs/four_final_checks/v1/frozen_design.json',design)
    print('Design frozen: four audits;65-fold sensitivity, no promotion or new final predictions.',flush=True)


def worker(folds,mode,fast=False):
    from src.ct3_residual_conditional.models import CORE
    if mode=='no_hhi':CORE[:]=[c for c in CORE if c!='compact_concentration_hhi']
    from src.current_champions import load_bundle
    from src.reference26_only import ReferenceOnly,FastReferenceOnly
    factory_type=FastReferenceOnly if fast else ReferenceOnly
    frame,groups,distance,manifest=load_bundle(ROOT/'data/processed/current_champions/v1',verify_saved_models=False)
    if mode=='no_hhi':
        frame=frame.drop(columns='compact_concentration_hhi')
        assert len(CORE)==3 and 'compact_concentration_hhi' not in frame
    plan=json.loads((ROOT/'data/processed/current_champions/v1/splits.json').read_text(encoding='utf-8'))['folds']
    expected=pd.read_parquet(ROOT/'data/processed/current_champions/v1/expected_oof.parquet')
    for ix in folds:
        directory=OUT/(mode+'_memory' if fast else mode)/f'{ix:02d}'
        if (directory/'complete.json').exists():print(f'{mode} {ix}: already complete',flush=True);continue
        started=time.perf_counter();record=plan[ix]
        tr=np.asarray(record['train_positions']);va=np.asarray(record['validation_positions'])
        inner=[(np.asarray(a['train_relative_positions']),np.asarray(a['validation_relative_positions'])) for a in record['inner']]
        with warnings.catch_warnings(record=True) as caught,threadpool_limits(limits=1):
            warnings.simplefilter('always')
            factory=factory_type(frame,groups,distance,manifest['geology'],record['protocol'],tr,inner,directory/'cache')
            pack=factory.full_fit(tr);prediction=factory.predict(pack,va)
            ledger=factory.helper.ledger+factory.helper.role.ledger
            assert all(not set(row['train'])&(set(row['held'])|set(va)) for row in ledger)
            comparison=expected[(expected.execution_index==ix)&(expected.experiment=='Reference26')].set_index('ID_POLIGONO').loc[frame.iloc[va].ID_POLIGONO]
            if mode=='control':np.testing.assert_allclose(prediction,comparison.y_pred.to_numpy(),rtol=0,atol=1e-10)
            rows=[]
            for position,value in zip(va,prediction):
                a=frame.iloc[position]
                rows.append(dict(execution_index=ix,protocol=record['protocol'],repeat=record['repeat'],fold=record['fold'],experiment='Reference25_NoHHI' if mode=='no_hhi' else 'Reference26_adapter_control',ID_POLIGONO=a.ID_POLIGONO,Estado=a.Estado,Municipio=a.Municipio,climate_profile=a.climate_profile,y_true=float(a.RENDIMIENTO_T_HA),y_pred=float(value)))
            pd.DataFrame(rows).to_parquet(directory/'oof.parquet',index=False)
            joblib.dump(pack,directory/'model.joblib',compress=3)
            logs=[dict(category=w.category.__name__,message=str(w.message)) for w in caught]
            if any(w['category']=='ConvergenceWarning' for w in logs):raise RuntimeError('Convergence warning; inspect logs before accepting')
            if fast and (OUT/mode/f'{ix:02d}/oof.parquet').exists():
                previous=pd.read_parquet(OUT/mode/f'{ix:02d}/oof.parquet').set_index('ID_POLIGONO').loc[frame.iloc[va].ID_POLIGONO].y_pred.to_numpy()
                np.testing.assert_allclose(prediction,previous,rtol=0,atol=1e-10)
            dump(directory/'complete.json',dict(index=ix,mode=mode,fast_equivalent_solver=fast,seconds=time.perf_counter()-started,outer_train=len(tr),outer_held=len(va),core=list(CORE),R3_strength=pack['strength'],gate_k=pack['raw']['shares']['k'] if pack['raw']['shares'] is not None else None,ledger_records=len(ledger),exclusions_passed=True,warnings=logs,maximum_difference_vs26=float(np.max(abs(prediction-comparison.y_pred.to_numpy())))))
        print(f'{mode} fold{ix} {record["protocol"]}: complete in{time.perf_counter()-started:.1f}s',flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['freeze','worker']);parser.add_argument('--folds',default='0');parser.add_argument('--mode',choices=['control','no_hhi'],default='no_hhi');parser.add_argument('--fast',action='store_true');args=parser.parse_args()
    if args.command=='freeze':freeze()
    else:worker([int(s) for s in args.folds.split(',')],args.mode,args.fast)


if __name__=='__main__':main()
