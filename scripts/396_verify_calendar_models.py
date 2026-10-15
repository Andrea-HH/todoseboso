"""Replay all sealed external models on TRAIN-heldout rows only."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
import joblib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=ROOT/'outputs/modeling/agronomic_calendar/v1'
path=OUT/'audit/model_replay.json'
if path.exists():raise FileExistsError('Preserve replay')
design=json.loads((OUT/'frozen_design.json').read_text())
for name,value in design['sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value
core=design['specs']['CAL00']['columns']
t=pd.read_parquet(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet',columns=['ID_POLIGONO',*core])
x=pd.read_parquet(ROOT/'data/processed/agronomic_calendar_set/v1/current_history_delta_197_target_free.parquet').set_index('ID_POLIGONO').reindex(t.ID_POLIGONO)
for col in core:x[col]=t[col].to_numpy()
p=pd.read_parquet(OUT/'tables/oof_predictions.parquet');models=0;values=0;maximum=0.
for source in sorted((OUT/'models').glob('*.joblib')):
    pack=joblib.load(source);r=pack['registry'];ids=pack['validation_ids']
    assert not set(ids)&set(pack['train_ids']) and len(pack['train_ids'])<138
    a=p[(p.experiment==r['experiment'])&(p.protocol==r['protocol'])&(p['repeat']==r['repeat'])&(p.fold==r['fold'])].set_index('ID_POLIGONO').reindex(ids)
    pred=pack['model'].predict(x.loc[ids]);error=float(np.max(abs(pred-a.y_pred)))
    assert error<1e-10;maximum=max(maximum,error);models+=1;values+=len(ids)
assert models==520 and values==14352
result=dict(models_replayed=models,heldout_predictions_replayed=values,max_absolute_difference=maximum,protected_hashes_unchanged=True,disjoint_train_validation=True,no_full138_fit=True,no_PRED=True)
path.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
