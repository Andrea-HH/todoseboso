import json
import joblib,numpy as np,pandas as pd
from threadpoolctl import threadpool_limits
from src.family_7.expansion import execution as e
from src.family_7.expansion.reporting import metric_summary
def test_selected_models_replay_and_original_inner_selection():
    _,t,splits=e.load();index=t.set_index(e.ID,drop=False)
    with threadpool_limits(limits=1):
        for name,spec in e.SPECS.items():
            for p,r,f,tr,va,inner in splits:
                stem=f'{name}_{p}_{r}_{f}';pack=joblib.load(e.OUT/'checkpoints'/f'{stem}.joblib');assert len(pack['inner'])==32
                scores=[];a=t.iloc[tr]
                for candidate in range(8):
                    fits=[x for x in pack['inner'] if x['registry']['candidate_index']==candidate];rmses=[]
                    for j,fit in enumerate(fits):
                        it,iv=inner[j];row=fit['registry']
                        assert json.loads(row['train_ids'])==a.iloc[it][e.ID].tolist()
                        assert json.loads(row['validation_ids'])==a.iloc[iv][e.ID].tolist()
                        rmses.append(np.sqrt(np.mean([(z['y_pred']-z['y_true'])**2 for z in fit['predictions']])))
                    scores.append(np.mean(rmses));np.testing.assert_allclose(scores[-1],pack['tuning'][candidate]['mean_inner_fold_RMSE'],atol=1e-12)
                assert pack['outer']['registry']['candidate_index']==min(range(8),key=lambda j:(round(scores[j],10),j))
                for context,fit in [('outer',pack['outer'])]+[(f'inner_{j}',fit) for j,fit in enumerate(pack['selected_inner'])]:
                    row=fit['registry'];aa=index.loc[json.loads(row['train_ids'])];v=index.loc[json.loads(row['validation_ids'])]
                    m=joblib.load(e.OUT/'models'/f'{stem}_{context}.joblib')
                    np.testing.assert_allclose(m.predict(v),[z['y_pred'] for z in fit['predictions']],atol=1e-12,rtol=0)
                    np.testing.assert_allclose(m.preprocess_.median_,aa[spec['columns']].median(),atol=1e-12)
                    np.testing.assert_allclose(m.preprocess_.mean_,aa[spec['columns']].mean(),atol=1e-12)
                    np.testing.assert_array_equal(m.training_y_,aa[e.TARGET])
                    assert not set(aa[e.ID])&set(v[e.ID]) and m.algorithm=='CatBoost'
                    assert m.parameters()['actual_trees']==m.params['iterations'] and not m.parameters()['external_eval_set']
def test_exact_references_complete_oof_and_metrics():
    p=pd.read_parquet(e.OUT/'tables/oof_predictions.parquet');ref=pd.read_parquet(e.OUT/'tables/reference_oof.parquet')
    pd.testing.assert_frame_equal(p.iloc[:len(ref)][ref.columns].reset_index(drop=True),ref.reset_index(drop=True),check_dtype=False)
    orig=pd.read_parquet(e.initial.OUT/'tables/oof_predictions.parquet');orig=orig[orig.experiment.isin(['F7-00','F7-01','C-T3','F5-01','CHAMPION'])]
    pd.testing.assert_frame_equal(ref[ref.experiment.isin(orig.experiment.unique())].reset_index(drop=True),orig.reset_index(drop=True))
    assert len(p)==17526
    for _,g in p.groupby(['experiment','protocol','repeat']):assert len(g)==138 and g[e.ID].nunique()==138
    _,m=metric_summary(p);z=pd.read_csv(e.OUT/'tables/metrics_summary.csv');key=['experiment','protocol']
    np.testing.assert_allclose(m.set_index(key)[['RMSE','MAE','bias']].sort_index(),z.set_index(key)[['RMSE','MAE','bias']].sort_index(),atol=1e-12)
    c=pd.read_csv(e.OUT/'tables/paired_fold_contributions.csv');np.testing.assert_allclose(c.SSE_gain,c.bias_squared_gain+c.error_variance_gain,atol=1e-10)
def test_scope_frozen_code_cache_and_folds():
    cfg=json.loads((e.OUT/'frozen_design.json').read_text())
    for p,h in {**cfg['source_sha'],**cfg['cache_sha']}.items():assert e.base.design.sha(e.ROOT/p)==h
    for f in ['outer_and_inner_splits.csv','group_memberships.csv']:assert (e.OUT/'splits'/f).read_bytes()==(e.initial.OUT/'splits'/f).read_bytes()
    reg=pd.read_csv(e.OUT/'tables/fit_registry.csv');assert len(reg)==6435 and set(reg.experiment)==set(e.SPECS) and reg.n_train.max()<138
    assert len(list((e.OUT/'models').glob('*.joblib')))==975
    assert cfg['no_PRED'] and cfg['no_final_training'] and cfg['no_XGB_fit'] and cfg['no_residual'] and cfg['no_ensemble']
    _,t,_=e.load();ids=set(t[e.ID])
    for row in reg.itertuples():assert set(json.loads(row.train_ids))<=ids and set(json.loads(row.validation_ids))<=ids
def test_effects_leaf_accounting_and_conditional_support():
    for f,c in [('effects_by_outer_fit.csv','local_difference'),('interactions_by_outer_fit.csv','mixed_local_difference')]:
        z=pd.read_csv(e.OUT/'tables'/f);q=z[z.supported]
        assert (q.n_supported>=5).all() and (q.supported_fraction>=.8-1e-12).all()
        assert z.loc[~z.supported,c].isna().all()
    p=pd.read_csv(e.OUT/'tables/permutation_by_outer_fit.csv');rain=p[p.block.eq('rain_compact3')]
    assert len(rain)==260 and rain.delta_MSE.isna().all()
    q=p[p.delta_MSE.notna()];assert (q.n_supported>=10).all() and (q.supported_fraction>=.8-1e-12).all()
    leaves=pd.read_parquet(e.OUT/'tables/tree_leaf_support.parquet')
    np.testing.assert_array_equal(leaves.n_routed_training,leaves.native_weight)
    _,t,splits=e.load();n={(p,r,f):len(tr) for p,r,f,tr,va,_ in splits}
    for key,g in leaves.groupby(['experiment','protocol','repeat','fold','tree']):assert g.n_routed_training.sum()==n[key[1:4]]
    cov=pd.read_csv(e.OUT/'tables/error_covariance_repeat.csv');assert cov.n.eq(138).all() and cov.error_correlation.between(-1,1).all()
