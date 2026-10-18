"""Freeze eight temporal indicators, one physical context and six architectures/base."""
from pathlib import Path
import sys,json,hashlib
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.temporal_indicator_weights import OUT,ENGINEERING,BASE_CALIBRATION,build_features,PARENTS,INDICATORS,ALPHA,L1_RATIO,AMPLITUDE


def main():
    if (OUT/'frozen_design.json').exists():raise FileExistsError('Preserve temporal weight design')
    for name in ['cache','checkpoints','models','tables','audit','figures']:(OUT/name).mkdir(parents=True,exist_ok=True)
    t=pd.read_parquet(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet');ids=t.ID_POLIGONO.tolist();assert len(ids)==138 and len(set(ids))==138
    x,dictionary,support,monthly,monthly_support,quality=build_features(ids);assert x.ID_POLIGONO.tolist()==ids
    x.to_parquet(OUT/'cache/features_train138_target_free.parquet',index=False);dictionary.to_csv(OUT/'tables/indicator_dictionary.csv',index=False);support.to_csv(OUT/'tables/feature_support.csv',index=False);monthly.to_parquet(OUT/'cache/sentinel_monthly_inputs.parquet',index=False);monthly_support.to_parquet(OUT/'cache/monthly_support.parquet',index=False);(OUT/'audit/input_quality.json').write_text(json.dumps(quality,indent=2),encoding='utf-8')
    recipes={base+'_'+kind:dict(base=base,kind=kind) for base in ['CT3','J7'] for kind in ['C4_FIXED','C4_CONSTANT','C4_SHARED','C4_DIRECTIONAL','INDICATORS_DIRECT','C4_INDICATORS_DIRECT']}
    protected=dict(json.loads((ENGINEERING/'frozen_design.json').read_text())['source_sha256'])
    sources=[ROOT/'src/temporal_indicator_weights.py',Path(__file__),ROOT/'scripts/479_run_temporal_indicator_weights.py',ROOT/'scripts/480_evaluate_temporal_indicator_weights.py',ROOT/'tests/test_temporal_indicator_weights.py',ROOT/'documentation/temporal_indicator_weights_design.md',ROOT/'data/processed/family_1/timeseries/sentinel_timeseries.parquet',ROOT/'data/processed/family_1/timeseries/planet_timeseries.parquet',OUT/'cache/features_train138_target_free.parquet',ENGINEERING/'tables/predictions.parquet',ROOT/'outputs/research/difficult_quartile/v1/tables/parcel_groups.csv',ROOT/'outputs/research/difficult_quartile/v1/delivery_audit.json',ROOT/'documentation/difficult_quartile_conclusions.md']+sorted((ENGINEERING/'checkpoints').glob('*.joblib'))+sorted((BASE_CALIBRATION/'checkpoints').glob('*.joblib'))
    for f in sources:protected[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
    cfg=dict(status='frozen_before_weight_training',exploratory=True,recipes=recipes,parent_columns=PARENTS,indicator_columns=INDICATORS,corrector=dict(alpha=ALPHA,l1_ratio=L1_RATIO,amplitude=AMPLITUDE,pre_amplitude_cap=.5),weight=dict(intercept_penalty=.1,slope_penalty=1.,minimum_route_support=15,bounds=[0,1],input_z_cap=6,fallback='constant shrinkage from training-only crossfitted candidate'),hyperparameters='All fixed in advance, not chosen on outer folds. Internal splits generate crossfitted corrections for fitting weights.',outer_folds=65,workers=8,no_auto_combinations=True,no_PRED=True,no_final138_fit=True,no_champion_change=True,source_sha256=protected)
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in protected.items());(OUT/'frozen_design.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Frozen12 recipes over65folds;8temporal indicators+minimum slope; fixed hyperparameters.');print(support.to_string(index=False))


if __name__=='__main__':main()
