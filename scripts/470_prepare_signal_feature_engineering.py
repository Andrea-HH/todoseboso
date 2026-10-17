"""Freeze three paired representation experiments and intercept-only controls."""
from pathlib import Path
import sys,json,hashlib
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.signal_feature_engineering import OUT,build_features
from src.geoc_reverse import GRID
from src.neighbor_signal_linear import OUT as PREVIOUS


def main():
    if (OUT/'frozen_design.json').exists():raise FileExistsError('Preserve frozen feature-engineering run')
    for name in ['cache','checkpoints','models','tables','audit','figures']:(OUT/name).mkdir(parents=True,exist_ok=True)
    t=pd.read_parquet(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet')
    ids=t.ID_POLIGONO.tolist();assert len(ids)==138 and len(set(ids))==138
    frame,blocks,dictionary,support,quality=build_features(ids)
    assert frame.ID_POLIGONO.tolist()==ids and not any('rendimiento' in c.lower() for c in frame)
    frame.to_parquet(OUT/'cache/features_train138_target_free.parquet',index=False);dictionary.to_csv(OUT/'tables/feature_dictionary.csv',index=False);support.to_csv(OUT/'tables/feature_support.csv',index=False)
    (OUT/'audit/input_quality.json').write_text(json.dumps(quality,indent=2),encoding='utf-8')
    protected=dict(json.loads((PREVIOUS/'frozen_design.json').read_text())['source_sha256'])
    sources=[ROOT/'src/signal_feature_engineering.py',Path(__file__),ROOT/'scripts/471_run_signal_feature_engineering.py',ROOT/'scripts/472_evaluate_signal_feature_engineering.py',ROOT/'tests/test_signal_feature_engineering.py',ROOT/'documentation/signal_feature_engineering_design.md',OUT/'cache/features_train138_target_free.parquet',ROOT/'data/processed/family_1/timeseries/sentinel_timeseries.parquet',ROOT/'data/processed/agronomic_calendar_set/v1/current_history_delta_197_target_free.parquet',ROOT/'outputs/modeling/experimental_pls1867/v1/cache/train138_1867.parquet',ROOT/'outputs/research/top10_difficult_parcels/v1/tables/top10_J7_random.csv',PREVIOUS/'tables/predictions.parquet']+sorted((PREVIOUS/'checkpoints').glob('*.joblib'))
    for f in sources:protected[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in protected.items())
    cfg=dict(status='frozen_before_training',exploratory=True,recipes={base+'_'+block:dict(base=base,block=block,columns=columns) for base in ['CT3','J7'] for block,columns in blocks.items()},blocks=blocks,grid=[dict(**p,amplitude=a) for p in GRID for a in [.25,.5]],null_candidate=dict(alpha=1.,l1_ratio=.9,amplitude=0.),intercept=True,cap_t_ha=.5,outer_folds=65,workers=8,primary_comparisons='Every recipe vs own exact external base; each engineered block vs matched raw block. SHIFT is an intercept-only calibration control. Holm across all declared tests.',nested_calibration='Original inner splits and frozen deeper protocol; exact cached crossfitted base calibration, no globally computed external OOF residuals used for fitting.',missing='Training medians only; no missingness predictors; no imputation before nonlinear deterministic summaries.',no_PRED=True,no_final138_fit=True,no_champion_change=True,no_automatic_combination=True,source_sha256=protected)
    (OUT/'frozen_design.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8');print('Frozen:',len(cfg['recipes']),'recipes, 65 folds,',len(frame.columns)-1,'cached deterministic descriptors.');print(support.groupby(support.feature.str.split('_').str[0]).missing_fraction.max().to_string())


if __name__=='__main__':main()
