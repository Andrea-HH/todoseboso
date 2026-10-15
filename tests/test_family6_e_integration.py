import json
import joblib,numpy as np,pandas as pd
from threadpoolctl import threadpool_limits
from src.family_6.expansion import execution as e
from src.family_6.expansion.reporting import metric_summary

def test_all_selected_models_replay_training_only_parameters():
    _,t,splits=e.load();index=t.set_index(e.ID,drop=False)
    with threadpool_limits(limits=1):
        for name in e.SPECS:
            for protocol,repeat,fold,tr,va,inner in splits:
                stem=f'{name}_{protocol}_{repeat}_{fold}';pack=joblib.load(e.OUT/'checkpoints'/f'{stem}.joblib')
                for context,fit in [('outer',pack['outer'])]+[(f'inner_{j}',p) for j,p in enumerate(pack['selected_inner'])]:
                    row=fit['registry'];a=index.loc[json.loads(row['train_ids'])];v=index.loc[json.loads(row['validation_ids'])]
                    model=joblib.load(e.OUT/'models'/f'{stem}_{context}.joblib')
                    np.testing.assert_allclose(model.predict(v),[r['y_pred'] for r in fit['predictions']],atol=1e-12,rtol=0)
                    np.testing.assert_allclose(model.preprocess_.median_,a[e.SPECS[name]['columns']].median(),atol=1e-12)
                    np.testing.assert_allclose(model.preprocess_.mean_,a[e.SPECS[name]['columns']].mean(),atol=1e-12)
                    np.testing.assert_allclose(model.training_y_,a[e.TARGET],atol=1e-12)
                    assert not set(a[e.ID])&set(v[e.ID]);assert len(model.forest_.estimators_)==384
                    assert not model.forest_.bootstrap and model.forest_.min_samples_leaf>=5

def test_inner_selection_and_original_context_memberships():
    _,t,splits=e.load()
    for name in e.SPECS:
        for protocol,repeat,fold,tr,va,inner in splits:
            a=t.iloc[tr];pack=joblib.load(e.OUT/'checkpoints'/f'{name}_{protocol}_{repeat}_{fold}.joblib');assert len(pack['inner'])==32
            scores=[]
            for candidate in range(8):
                fits=[p for p in pack['inner'] if p['registry']['candidate_index']==candidate];rmses=[]
                for j,fit in enumerate(fits):
                    it,iv=inner[j];row=fit['registry']
                    assert json.loads(row['train_ids'])==a.iloc[it][e.ID].tolist();assert json.loads(row['validation_ids'])==a.iloc[iv][e.ID].tolist()
                    np.testing.assert_allclose([r['y_true'] for r in fit['predictions']],a.iloc[iv][e.TARGET],atol=1e-12)
                    rmses.append(np.sqrt(np.mean([(r['y_pred']-r['y_true'])**2 for r in fit['predictions']])))
                scores.append(np.mean(rmses));np.testing.assert_allclose(scores[-1],pack['tuning'][candidate]['mean_inner_fold_RMSE'],atol=1e-12)
            assert pack['outer']['registry']['candidate_index']==min(range(8),key=lambda j:(round(scores[j],10),j))

def test_exact_reference_oof_and_aggregation():
    p=pd.read_parquet(e.OUT/'tables/oof_predictions.parquet');ref=pd.read_parquet(e.OUT/'tables/reference_oof.parquet')
    pd.testing.assert_frame_equal(p.iloc[:len(ref)][ref.columns].reset_index(drop=True),ref,check_dtype=False)
    original=pd.read_parquet(e.base.OUT/'tables/oof_predictions.parquet');original=original[original.experiment.isin(['F6-00','F6-01','C-T3','F5-01','CHAMPION'])].copy();original.experiment=original.experiment.replace({'F6-01':'F6-E0'})
    pd.testing.assert_frame_equal(ref,original)
    assert len(p)==13938
    for _,g in p.groupby(['experiment','protocol','repeat']):assert len(g)==138 and g[e.ID].nunique()==138
    _,m=metric_summary(p);a=pd.read_csv(e.OUT/'tables/metrics_summary.csv');key=['experiment','protocol']
    np.testing.assert_allclose(m.set_index(key)[['RMSE','MAE','bias']].sort_index(),a.set_index(key)[['RMSE','MAE','bias']].sort_index(),atol=1e-12)
    gate=pd.read_csv(e.OUT/'audit/E0_exact_replay_and_cache_equivalence.csv');assert len(gate)==65 and gate.minimal_cache_equals_original.all() and gate.max_prediction_difference.max()<=1e-12

def test_supported_effects_permutation_identifiability_and_error_decomposition():
    for name,column in [('effects_by_outer_fit.csv','local_difference'),('interactions_by_outer_fit.csv','mixed_local_difference')]:
        x=pd.read_csv(e.OUT/'tables'/name);valid=x[x.supported]
        assert (valid.n_supported>=5).all() and (valid.supported_fraction>=.8-1e-12).all()
        assert x.loc[~x.supported,column].isna().all()
    per=pd.read_csv(e.OUT/'tables/permutation_by_outer_fit.csv');dtr=per[per.experiment.eq('F6-E3')]
    assert len(dtr)==65 and dtr.permutation.eq(-1).all() and dtr.delta_MSE.isna().all()
    z=pd.read_csv(e.OUT/'tables/paired_fold_contributions.csv');np.testing.assert_allclose(z.SSE_gain,z.bias_squared_gain+z.error_variance_gain,atol=1e-10)
    leaf=pd.read_parquet(e.OUT/'tables/tree_leaves_support.parquet');assert leaf.n_leaf_samples.min()>=5

def test_frozen_sources_cache_splits_and_only_authorized_fits():
    cfg=json.loads((e.OUT/'frozen_design.json').read_text())
    for path,h in {**cfg['source_sha'],**cfg['cache_sha']}.items():assert e.base.design.sha(e.ROOT/path)==h
    for name in ['outer_and_inner_splits.csv','group_memberships.csv']:assert (e.OUT/'splits'/name).read_bytes()==(e.base.OUT/'splits'/name).read_bytes()
    reg=pd.read_csv(e.OUT/'tables/fit_registry.csv');assert len(reg)==6435 and set(reg.experiment)==set(e.SPECS)
    _,t,_=e.load();ids=set(t[e.ID]);assert reg.n_train.max()<138
    for row in reg.itertuples():assert set(json.loads(row.train_ids))<=ids and set(json.loads(row.validation_ids))<=ids
    assert cfg['no_PRED'] and cfg['no_final_training'] and cfg['no_E4_E5']
    for spec in e.SPECS.values():assert not set(spec['columns'])&{e.ID,e.TARGET,'climate_profile','Municipio','Estado'}
