"""Freeze six mixtures and fresh partition sensitivity before training."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import joblib
from sklearn.model_selection import KFold
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.four_expert_combinations import OUT,ARCH,OLD
def main():
    assert not (OUT/'frozen_design.json').exists()
    for sub in ['tables','models','checkpoints','cache','audit','figures']:(OUT/sub).mkdir(parents=True,exist_ok=True)
    plan=joblib.load(OLD/'cache/frozen65_splits.joblib');rng=np.random.default_rng(20261017)
    for re in range(1,17):
        order=rng.permutation(138);tr=np.sort(order[:97]);va=np.sort(order[97:]);inner=list(KFold(4,shuffle=True,random_state=2026).split(tr));plan.append(('fresh_97_41',re,1,tr,va,inner))
    joblib.dump(plan,OUT/'frozen81_splits.joblib')
    sources=[ROOT/'src/four_expert_combinations.py',ROOT/'scripts/503_prepare_four_expert_combinations.py',ROOT/'scripts/504_run_four_expert_combinations.py',ROOT/'scripts/505_evaluate_four_expert_combinations.py',ROOT/'tests/test_four_expert_combinations.py',ROOT/'documentation/four_expert_combinations_design.md',OUT/'frozen81_splits.joblib',OLD/'cache/frozen65_splits.joblib',OLD/'cache/train138.parquet',ROOT/'outputs/modeling/geoc_bridge/v1/cache/prepared.joblib',ARCH/'delivery_audit.json',ARCH/'tables/oof_residuals.parquet']
    sources+=list((ARCH/'models').glob('*.joblib'))+list((ARCH/'checkpoints').glob('*.joblib'))
    cfg=dict(status='frozen',experiments={'B1':'CT3 + constant*(Reference26-CT3)','B2':'CT3 + constant*(Compact14-CT3)','B3':'Reference26 + constant*(L40-Reference26)','B4':'convex CT3/Reference26/L40, ridge .1*mean across-expert variance; prior Reference26','B5':'conditional CT3/Reference26','B6':'conditional Reference26/L40'},conditional_penalty=10.,intercept_penalty_multiplier=.1,weight_bounds=[0,1],conditional_features={'B5':['CT3_prediction','absolute_disagreement','log1p_mean_geo_k24_distance','log1p_nearest_standardized_local5_distance'],'B6':['absolute_disagreement','log1p_mean_geo_k24_distance','log1p_nearest_PCA20_distance','geographic_k24_training_y_std']},constant_weights='continuous constrained least squares on honest internal OOF',hyperparameter_search='none; meta penalties frozen, experts preserve original grids',original_folds=65,fresh_sensitivity_splits=16,fresh_seed=20261017,fresh_warning='New partitions, same outcomes already explored; not independent confirmation',fallback='Original expert single-group fallbacks; R3 off when no CV, zero candidate correction where deeper groups unavailable',metrics='OOF-complete per repeat, then mean; fresh41-case splits reported separately',workers=6,no_PRED=True,no_final138_fit=True,no_champion_change=True,exploratory=True,source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources})
    (OUT/'frozen_design.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8');print('Frozen six mixtures, four controls, 65 original folds +16 new97/41 sensitivity splits.')
if __name__=='__main__':main()
