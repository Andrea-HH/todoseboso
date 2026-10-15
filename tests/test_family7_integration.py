import json
import joblib,numpy as np,pandas as pd
from threadpoolctl import threadpool_limits
from src.family_7 import execution as e
from src.family_7.reporting import metric_summary
from src.family_7.models import GRIDS

def test_selected_models_replay_and_training_only_transforms():
    _,t,splits=e.load();index=t.set_index(e.ID,drop=False)
    with threadpool_limits(limits=1):
        for name,spec in e.SPECS.items():
            for p,r,f,tr,va,inner in splits:
                stem=f'{name}_{p}_{r}_{f}';pack=joblib.load(e.OUT/'checkpoints'/f'{stem}.joblib')
                for context,fit in [('outer',pack['outer'])]+[(f'inner_{j}',fit) for j,fit in enumerate(pack['selected_inner'])]:
                    row=fit['registry'];a=index.loc[json.loads(row['train_ids'])];v=index.loc[json.loads(row['validation_ids'])]
                    m=joblib.load(e.OUT/'models'/f'{stem}_{context}.joblib')
                    np.testing.assert_allclose(m.predict(v),[x['y_pred'] for x in fit['predictions']],atol=1e-12,rtol=0)
                    np.testing.assert_allclose(m.preprocess_.median_,a[spec['columns']].median(),atol=1e-12)
                    np.testing.assert_allclose(m.preprocess_.mean_,a[spec['columns']].mean(),atol=1e-12)
                    np.testing.assert_allclose(m.training_y_,a[e.TARGET],atol=1e-12)
                    assert not set(a[e.ID])&set(v[e.ID])
                    expected=m.params.get('iterations',m.params.get('n_estimators'))
                    assert m.parameters()['actual_trees']==expected and not m.parameters()['external_eval_set']

def test_original_inner_partitions_and_selection():
    _,t,splits=e.load()
    for name in e.SPECS:
        for p,r,f,tr,va,inner in splits:
            a=t.iloc[tr];pack=joblib.load(e.OUT/'checkpoints'/f'{name}_{p}_{r}_{f}.joblib');assert len(pack['inner'])==32
            scores=[]
            for candidate in range(8):
                fits=[fit for fit in pack['inner'] if fit['registry']['candidate_index']==candidate];rmses=[]
                for j,fit in enumerate(fits):
                    it,iv=inner[j];row=fit['registry']
                    assert json.loads(row['train_ids'])==a.iloc[it][e.ID].tolist()
                    assert json.loads(row['validation_ids'])==a.iloc[iv][e.ID].tolist()
                    np.testing.assert_allclose([x['y_true'] for x in fit['predictions']],a.iloc[iv][e.TARGET])
                    rmses.append(np.sqrt(np.mean([(x['y_pred']-x['y_true'])**2 for x in fit['predictions']])))
                scores.append(np.mean(rmses));np.testing.assert_allclose(scores[-1],pack['tuning'][candidate]['mean_inner_fold_RMSE'],atol=1e-12)
            assert pack['outer']['registry']['candidate_index']==min(range(8),key=lambda j:(round(scores[j],10),j))

def test_reference_integrity_and_complete_repeat_aggregation():
    p=pd.read_parquet(e.OUT/'tables/oof_predictions.parquet');ref=pd.read_parquet(e.OUT/'tables/reference_oof.parquet')
    original=pd.read_parquet(e.expansion.OUT/'tables/oof_predictions.parquet')
    original=original[original.experiment.isin(['C-T3','F5-01','F6-E0','CHAMPION'])]
    # Cache intentionally drops the pandas row index; immutable scientific keys,
    # values and row order are compared exactly after normalizing that metadata.
    pd.testing.assert_frame_equal(ref.reset_index(drop=True),original.reset_index(drop=True))
    pd.testing.assert_frame_equal(p.iloc[:len(ref)][ref.columns].reset_index(drop=True),ref.reset_index(drop=True),check_dtype=False)
    assert len(p)==10350
    for _,g in p.groupby(['experiment','protocol','repeat']):assert len(g)==138 and g[e.ID].nunique()==138
    _,m=metric_summary(p);a=pd.read_csv(e.OUT/'tables/metrics_summary.csv');key=['experiment','protocol']
    np.testing.assert_allclose(m.set_index(key)[['RMSE','MAE','bias']].sort_index(),a.set_index(key)[['RMSE','MAE','bias']].sort_index(),atol=1e-12)
    contributions=pd.read_csv(e.OUT/'tables/paired_fold_contributions.csv')
    np.testing.assert_allclose(contributions.SSE_gain,contributions.bias_squared_gain+contributions.error_variance_gain,atol=1e-10)

def test_frozen_hashes_and_only_two_authorized_experiments():
    cfg=json.loads((e.OUT/'frozen_design.json').read_text())
    for path,h in {**cfg['source_sha'],**cfg['cache_sha']}.items():assert e.base.design.sha(e.ROOT/path)==h
    for name in ['outer_and_inner_splits.csv','group_memberships.csv']:
        assert (e.OUT/'splits'/name).read_bytes()==(e.expansion.OUT/'splits'/name).read_bytes()
    reg=pd.read_csv(e.OUT/'tables/fit_registry.csv');assert len(reg)==4290 and set(reg.experiment)==set(e.SPECS)
    assert reg.n_train.max()<138
    assert len(list((e.OUT/'models').glob('*.joblib')))==650
    assert len(list((e.OUT/'checkpoints').glob('*.joblib')))==130
    assert cfg['no_extension_fits'] and cfg['no_PRED'] and cfg['no_final_training']
    _,t,_=e.load();ids=set(t[e.ID])
    for row in reg.itertuples():assert set(json.loads(row.train_ids))<=ids and set(json.loads(row.validation_ids))<=ids

def test_supported_effects_conditional_permutation_and_leaf_accounting():
    for filename,column in [('effects_by_outer_fit.csv','local_difference'),('interactions_by_outer_fit.csv','mixed_local_difference')]:
        q=pd.read_csv(e.OUT/'tables'/filename);valid=q[q.supported]
        assert (valid.n_supported>=5).all() and (valid.supported_fraction>=.8-1e-12).all()
        assert q.loc[~q.supported,column].isna().all()
    q=pd.read_csv(e.OUT/'tables/permutation_by_outer_fit.csv');rain=q[q.block.eq('rain_compact3')]
    assert len(rain)==130 and rain.permutation.eq(-1).all() and rain.delta_MSE.isna().all()
    leaves=pd.read_parquet(e.OUT/'tables/tree_leaf_support.parquet')
    reg=pd.read_csv(e.OUT/'tables/fit_registry.csv');reg=reg[reg.context.eq('outer')].set_index(['experiment','protocol','repeat','fold'])
    for key,g in leaves.groupby(['experiment','protocol','repeat','fold','tree']):
        assert g.n_routed_training.sum()==reg.loc[key[:4],'n_train']
        if key[0]=='F7-00':np.testing.assert_allclose(g.n_routed_training,g.native_weight,atol=1e-8)
    partitions=pd.read_parquet(e.OUT/'tables/tree_partitions.parquet');assert set(partitions.feature)<=set(e.CORE)
