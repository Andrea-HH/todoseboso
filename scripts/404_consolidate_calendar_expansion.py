"""Single review bundle; preserve the original and exploratory addendum."""
from pathlib import Path
import json,hashlib
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
MAIN=ROOT/'outputs/modeling/agronomic_calendar/expansion/v1'
ADD=ROOT/'outputs/modeling/agronomic_calendar/compact_spectral_addendum/v1'
OUT=ROOT/'outputs/modeling/agronomic_calendar/completed_expansion_summary/v1'
if OUT.exists():raise FileExistsError('Preserve review bundle')
OUT.mkdir(parents=True)
summary=pd.read_csv(ADD/'diagnostics/combined_metrics_summary.csv');assert len(summary)==52*4
summary.to_csv(OUT/'metrics_summary.csv',index=False)
for name in ['regional_summary','intraprofile_summary','selection_complexity','feature_selection_stability']:
    a=pd.read_csv(MAIN/'diagnostics'/f'{name}.csv');b=pd.read_csv(ADD/'diagnostics'/f'{name}.csv');b=b[b.experiment.str.contains('_CMP_')]
    pd.concat([a,b],ignore_index=True).to_csv(OUT/f'{name}.csv',index=False)
pd.concat([pd.read_csv(p/'diagnostics/paired_summary.csv') for p in [MAIN,ADD]],ignore_index=True).to_csv(OUT/'paired_summary.csv',index=False)
p=pd.concat([pd.read_parquet(base/'tables/new_oof_predictions.parquet') for base in [MAIN,ADD]],ignore_index=True)
assert len(p)==71760 and p.experiment.nunique()==40 and not p.duplicated(['experiment','protocol','repeat','fold','ID_POLIGONO']).any()
p.to_parquet(OUT/'new_oof_predictions.parquet',index=False);p.to_csv(OUT/'new_oof_predictions.csv',index=False)
sources=[base/sub for base in [MAIN,ADD] for sub in ['frozen_design.json','manifest.json','audit/replay.json']]
manifest=dict(status='complete',new_configurations=40,recovered_references=12,new_external_models=2600,new_oof_predictions=71760,folds_per_configuration=65,nominal_completed_fits=189800,exact_model_replay=True,maximum_replay_difference=0.,no_final_fit138=True,no_PRED=True,exploratory_addendum='3 compact spectral blocks defined after the primary external results; not independent confirmation',source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in manifest.items() if k!='source_sha256'},indent=2))
