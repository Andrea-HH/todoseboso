"""Integration check: held-out targets cannot change a cold fold's predictions."""
from pathlib import Path
import os
import sys
os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('MKL_NUM_THREADS','1')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import importlib.util
import json
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from src.current_champions import load_bundle,refit_fold,predict_saved,MODELS


def main():
    spec=importlib.util.spec_from_file_location('current_runner',ROOT/'scripts/521_current_champions.py')
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    bundle=ROOT/'data/processed/current_champions/v1_inputs_only'
    out=ROOT/'outputs/research/current_champions/v1/exclusion_check'
    assert not (bundle/'models').exists()
    runner.restrict_inputs(bundle,out)
    frame,groups,distance,manifest=load_bundle(bundle,verify_saved_models=False)
    fold=json.loads((bundle/'splits.json').read_text(encoding='utf-8'))['folds'][60]
    query=np.array(fold['validation_positions'])
    altered=frame.copy()
    altered.loc[query,'RENDIMIENTO_T_HA']+=1000.
    # No alteration is written to a dataset or used as a training target.
    with threadpool_limits(limits=1):
        pack=refit_fold(altered,groups,distance,manifest['geology'],fold,out/'cold_cache')
        pred=predict_saved(pack,query,altered,distance)
    expected=pd.read_parquet(bundle/'expected_oof.parquet')
    differences={}
    for m in MODELS:
        previous=expected[(expected.execution_index==60)&(expected.experiment==m)].set_index('ID_POLIGONO').loc[frame.iloc[query].ID_POLIGONO]
        differences[m]=float(np.max(np.abs(pred[m]-previous.y_pred.to_numpy())))
        assert differences[m]<1e-10,(m,differences[m])
    report=dict(status='passed',execution_index=60,models=MODELS,maximum_prediction_differences=differences,
        test='Outer held-out targets changed only in memory; cold training predictions unchanged.',
        actual_dataset_modified=False,no_saved_models_in_bundle=True,restricted_file_io=True,
        scope='One spatial fold; complements cross-fitting provenance, not an exhaustive leakage proof for all possible changes.')
    runner.dump(ROOT/'results/current_champions/v1/held_out_target_invariance.json',report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
