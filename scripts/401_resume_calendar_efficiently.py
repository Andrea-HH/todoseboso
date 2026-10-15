"""Resume frozen candidates with equivalent single-thread scoring only."""
from pathlib import Path
import sys,time,json,hashlib,importlib
import joblib
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.calendar_execution import install_single_thread_scoring,work_fold_single_thread
from src.calendar_expansion import OUT

if __name__=='__main__':
    if (OUT/'manifest.json').exists():raise FileExistsError('Preserve completed version')
    m=importlib.import_module('scripts.397_calendar_expansion')
    cfg=json.loads((OUT/'frozen_design.json').read_text())
    for path,sha in cfg['sha256'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha
    model=joblib.load(OUT/'models/CB_CAL00_00.joblib');v=model['model'];x=pd.read_parquet(OUT/'cache/features_train138.parquet').set_index('ID_POLIGONO').loc[model['validation_ids']]
    before=v.predict(x);importance=v.model_.get_feature_importance()
    install_single_thread_scoring();after=v.predict(x);importance_after=v.model_.get_feature_importance()
    np.testing.assert_array_equal(before,after);np.testing.assert_array_equal(importance,importance_after)
    good=0;quarantine=[]
    for f in (OUT/'checkpoints').glob('*.joblib'):
        try:joblib.load(f);good+=1
        except Exception:f.rename(f.with_suffix('.incomplete'));quarantine.append(f.name)
    audit=dict(reason='CatBoost post-fit importance/scoring defaulted to all cores despite training thread_count1; use single-thread scoring to avoid nested oversubscription',changes_to_training_parameters=False,changes_to_candidates=False,changes_to_selection=False,workers=6,retained_checkpoints=good,quarantined=quarantine,max_prediction_difference=float(abs(before-after).max()),max_importance_difference=float(abs(importance-importance_after).max()),overlay_sha256=hashlib.sha256((ROOT/'src/calendar_execution.py').read_bytes()).hexdigest())
    (OUT/'audit/single_thread_scoring.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    print('Equivalent scoring verified; resuming',good,'checkpoints',flush=True)
    start=time.perf_counter();joblib.Parallel(n_jobs=6,backend='loky')(joblib.delayed(work_fold_single_thread)(i) for i in range(65));m.finish(time.perf_counter()-start)
