"""Exploratory comparator-gap closure; same variables, grids and frozen folds."""
from pathlib import Path
import sys,json,hashlib,time
import pandas as pd
import joblib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.calendar_execution import install_single_thread_scoring
MAIN=ROOT/'outputs/modeling/agronomic_calendar/expansion/v1'
OUT=ROOT/'outputs/modeling/agronomic_calendar/compact_spectral_addendum/v1'

def worker(i):
    install_single_thread_scoring()
    import src.calendar_expansion as e
    e.OUT=OUT
    return e.work_fold(i)

if __name__=='__main__':
    if (OUT/'manifest.json').exists():raise FileExistsError('Preserve addendum')
    for d in ['models','checkpoints','cache','tables','audit']:(OUT/d).mkdir(parents=True,exist_ok=True)
    cfg=json.loads((MAIN/'frozen_design.json').read_text());core=cfg['specs']['CAL00']['columns'];evi=[c for c in cfg['specs']['CAL08']['columns'] if c not in cfg['specs']['CAL04']['columns']];water=[c for c in cfg['specs']['CAL09']['columns'] if c not in cfg['specs']['CAL04']['columns']]
    cfg['specs']={
        'CMP_EVI':dict(columns=core+evi,history=[],description='compact4 + EVI four calendar windows'),
        'CMP_WATER':dict(columns=core+water,history=[],description='compact4 + NDWI/MSI four calendar windows'),
        'CMP_ALL':dict(columns=core+evi+water,history=[],description='compact4 + EVI/NDWI/MSI calendar windows')}
    cfg.update(addendum=True,exploratory_after_main_external_evaluation=True,reason='Close comparator gap: initial additions used weak CAL04 base. All three spectral hypotheses tested, not the externally best selected variant.',workers=6)
    cfg['sha256'][str(Path(__file__).relative_to(ROOT))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    frozen=OUT/'frozen_design.json'
    if frozen.exists():assert json.loads(frozen.read_text())==cfg
    else:frozen.write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    dest=OUT/'cache/features_train138.parquet'
    if not dest.exists():dest.write_bytes((MAIN/'cache/features_train138.parquet').read_bytes())
    start=time.perf_counter();joblib.Parallel(n_jobs=6)(joblib.delayed(worker)(i) for i in range(65))
    packs=[joblib.load(f) for f in sorted((OUT/'checkpoints').glob('*.joblib'))];assert len(packs)==390
    for field in ['registry','usage','tuning']:
        a=pd.DataFrame([r for p in packs for r in ([p[field]] if field=='registry' else p[field])])
        if field=='tuning':a['params']=a.params.map(json.dumps)
        a.to_parquet(OUT/'tables'/f'{field}.parquet',index=False)
    pred=pd.DataFrame([r for p in packs for r in p['predictions']]);assert len(pred)==10764
    pred.to_parquet(OUT/'tables/new_oof_predictions.parquet',index=False)
    ref=pd.read_parquet(MAIN/'tables/oof_predictions.parquet');ref=ref[ref.experiment.isin(['C-T3','F7-00','EN_CAL00','CB_CAL00'])]
    pd.concat([pred,ref],ignore_index=True).to_parquet(OUT/'tables/oof_predictions.parquet',index=False)
    for path,value in cfg['sha256'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==value
    (OUT/'audit/warnings.json').write_text(json.dumps([dict(experiment=p['registry']['experiment'],protocol=p['registry']['protocol'],repeat=p['registry']['repeat'],fold=p['registry']['fold'],**w) for p in packs for w in p['warnings']],indent=2),encoding='utf-8')
    manifest=dict(status='complete',outer_models=390,blocks=3,algorithms=['EN','CB'],new_predictions=len(pred),nominal_fits=sum(p['registry']['fits'] for p in packs),seconds=time.perf_counter()-start,exploratory_addendum=True,no_PRED=True,no_full138_fit=True,protected_hashes_unchanged=True,warnings=sum(len(p['warnings']) for p in packs))
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print(json.dumps(manifest,indent=2))
