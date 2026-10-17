"""Recover packaging only: archived reference rows already carry an index field.

All 65 checkpoints are complete. Preserve the frozen training source and its
hash; use execution_index rather than overwriting the archived index metadata.
"""
from pathlib import Path
import sys,json,hashlib
import pandas as pd
import joblib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.difficult_case_signals import OUT


def main():
    if (OUT/'execution_complete.json').exists():raise FileExistsError('Preserve finalized run')
    cfg=json.loads((OUT/'frozen_design.json').read_text())
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(65)]
    assert len(list((OUT/'models').glob('*.joblib')))==65
    for field in ['predictions','selection','candidates']:
        frame=pd.DataFrame([dict(r,execution_index=i) for i,p in enumerate(packs) for r in p[field]])
        if field=='predictions':assert len(frame)==15*1794 and not frame.duplicated(['experiment','protocol','repeat','ID_POLIGONO']).any()
        frame.to_parquet(OUT/'tables'/f'{field}.parquet',index=False)
    (OUT/'audit/warnings.json').write_text(json.dumps([w for p in packs for w in p['warnings']],indent=2),encoding='utf-8')
    result=dict(status='complete',new_recipes=12,folds=65,sum_fold_seconds=sum(p['seconds'] for p in packs),protected_sources_unchanged=True,no_final138_fit=True,no_PRED=True,packaging_recovery='Original aggregation collided with archived reference index. Checkpoints unchanged; added distinct execution_index.',recovery_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (OUT/'execution_complete.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
