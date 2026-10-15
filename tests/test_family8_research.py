import ast,json
import numpy as np,pandas as pd
from src.family_8 import research as e
def test_no_estimator_fit_predict_or_model_construction_in_research():
    forbidden={'ElasticNet','Ridge','CatBoostRegressor','XGBRegressor','GaussianProcessRegressor','GridSearchCV','StackingRegressor'}
    for p in (e.ROOT/'src/family_8').glob('*.py'):
        tree=ast.parse(p.read_text(encoding='utf8'))
        for node in ast.walk(tree):
            if not isinstance(node,ast.Call):continue
            if isinstance(node.func,ast.Attribute):assert node.func.attr not in {'fit','fit_transform','predict','predict_proba'}
            if isinstance(node.func,ast.Name):assert node.func.id not in forbidden
    cfg=json.loads((e.OUT/'proposed_design.json').read_text())
    assert cfg['actual_models_fitted']==0 and cfg['PRED_predictions'] is False
def test_complete_oof_reaggregation_and_known_control():
    z=pd.read_csv(e.OUT/'tables/archived_metrics_repeat_recomputed.csv')
    assert z.n.eq(138).all()
    m=pd.read_csv(e.OUT/'tables/archived_metrics_summary_recomputed.csv')
    a=m[(m.family=='F7')&(m.experiment=='C-T3')&(m.protocol=='municipality')]
    np.testing.assert_allclose(a.RMSE.iloc[0],.581258919,atol=1e-8)
    r=m.groupby(['family','experiment','protocol']).size();assert r.eq(1).all()
    gates=pd.read_csv(e.OUT/'tables/oof_compatibility_inventory.csv')
    assert gates.exact_outer_validation_ids.all() and gates.identical_targets.all()
def test_original_folds_nested_memberships_and_support():
    t,splits,groups=e.load();assert len(t)==138 and len(splits)==65
    checks=pd.read_csv(e.OUT/'tables/proposed_membership_exclusion_checks.csv')
    assert checks.excludes_outer_validation.all() and checks.excludes_inner_validation.all() and checks.excludes_residual_heldout.all()
    assert checks.n_tuning_folds.ge(2).all()
    support=json.loads((e.OUT/'audit/sample_support.json').read_text())
    assert support['n_climate_profiles']==43 and support['n_repeated_profiles']==12 and support['n_singleton_profiles']==31
    assert 0<=support['within_fraction']<=1
    ledger=pd.read_csv(e.OUT/'tables/historical_nested_provenance_checks.csv')
    assert ledger.disjoint_fit_heldout.all() and ledger.deeper_tuning_excludes_heldout.all()
def test_candidate_matrix_and_honest_scope():
    cfg=json.loads((e.OUT/'proposed_design.json').read_text())
    assert cfg['first']==['R0-B','R1'] and cfg['second_after_review']==['R2','C-V']
    assert cfg['lambda_grid']==[0,.25,.5]
    assert len(cfg['R2_CV_grid'])==6 and max(x['depth'] for x in cfg['R2_CV_grid'])==2
    assert cfg['no_ensemble_weights'] and cfg['no_region_specific_rule'] and cfg['no_target_quartile_gate']
    text=(e.OUT/'report/nested_crossfitting.md').read_text(encoding='utf8')
    assert 'r_CF(A_j)' in text and 'm_full-m_minusfold' in text and 'predicciones internas R0' in text
def test_pair_difference_calculation_and_sources_unchanged():
    frame=pd.DataFrame({e.ID:['a','b','c'],'fold':[1,1,2],'climate_profile':[1,1,1],'y_true':[1.,3.,5.],'y_pred':[2.,3.,5.]})
    z=e.pair_metrics(frame);assert z['n_pairs']==1 and z['n_parcels']==2
    np.testing.assert_allclose(z['equal_profile_RMSE'],1.)
    sources=pd.read_csv(e.OUT/'audit/verified_consumed_sources.csv')
    for row in sources.itertuples():assert e.sha(e.ROOT/row.path)==row.sha256
