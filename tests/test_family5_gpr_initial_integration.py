import json
import joblib
import numpy as np
import pandas as pd
import pytest
from threadpoolctl import threadpool_limits
from src.family_5.gpr_initial import execution as e

@pytest.fixture(scope='module')
def context():
    _,t,splits=e.load();p=pd.read_parquet(e.OUT/'tables/oof_predictions.parquet');r=pd.read_csv(e.OUT/'tables/fit_registry.csv')
    return t,splits,p,r

@pytest.fixture(scope='module',autouse=True)
def native_threads():
    with threadpool_limits(limits=1):yield

def test_scope_and_prediction_universe(context):
    t,s,p,r=context
    assert set(p.experiment)=={'F5-00-C','F5-01','C-T3'} and len(p)==5382
    assert len(r)==650 and len(s)==65 and len(t)==138
    assert not p.duplicated(['experiment',e.ID,'protocol','repeat']).any()
    assert set(p[e.ID])==set(t[e.ID]) and np.isfinite(p[['y_true','y_pred']]).all().all()
    allfeatures=pd.read_parquet(e.c.PROC/'c_features_197_target_free.parquet')
    assert set(p[e.ID]).isdisjoint(set(allfeatures[e.ID])-set(t[e.ID]))
    assert not list(e.OUT.glob('*PRED*'))

def test_control_exactly_archived(context):
    old=pd.read_parquet(e.c.OUT/'tables/oof_predictions.parquet');old=old[old.experiment.eq('C-T3')]
    new=context[2];new=new[new.experiment.eq('C-T3')];key=[e.ID,'protocol','repeat','fold']
    for column in ['y_true','y_pred']:np.testing.assert_array_equal(old.set_index(key)[column].sort_index(),new.set_index(key)[column].sort_index())
    assert pd.read_csv(e.OUT/'audit/control_replay.csv').max_prediction_difference.max()<=1e-12

@pytest.mark.parametrize('experiment',['F5-00-C','F5-01'])
def test_every_outer_and_inner_fit_replays_training_only(context,experiment):
    t,s,p,r=context;inner=pd.read_parquet(e.OUT/'tables/inner_oof_predictions.parquet')
    for _,row in r[r.experiment.eq(experiment)].iterrows():
        ids=json.loads(row.train_ids);v_ids=json.loads(row.validation_ids);a=t.set_index(e.ID).loc[ids].reset_index();v=t.set_index(e.ID).loc[v_ids].reset_index()
        assert set(ids).isdisjoint(v_ids)
        stem=f'{experiment}_{row.protocol}_{int(row["repeat"])}_{int(row.fold)}_{row.context}_{int(row.inner_index)}'
        m=joblib.load(e.OUT/'models'/(stem+'.joblib'))
        predictions=p if row.context=='outer' else inner
        q=predictions[(predictions.experiment==experiment)&(predictions.protocol==row.protocol)&(predictions['repeat']==row['repeat'])&(predictions.fold==row.fold)]
        if row.context=='inner':q=q[q.inner_index.eq(row.inner_index)]
        q=q.set_index(e.ID).loc[v_ids];out=m.predict_components(v)
        np.testing.assert_allclose(out['prediction'],q.y_pred,atol=1e-12)
        np.testing.assert_allclose(out['predictive_sd'],q.predictive_sd,atol=1e-12)
        np.testing.assert_allclose(m.preprocess_.median_,np.nanmedian(a[list(m.columns)],axis=0),atol=1e-12)
        np.testing.assert_allclose(m.preprocess_.mean_,np.nanmean(a[list(m.columns)],axis=0),atol=1e-12)
        assert np.isclose(m.target_mean_,a[e.TARGET].mean()) and np.isclose(m.target_scale_,a[e.TARGET].std(ddof=0))
        assert m.selected_optimizer_converged_ and m.min_covariance_eigenvalue_>0
        assert len(m.optimizer_.records)==3 and np.isclose(min(x['negative_lml'] for x in m.optimizer_.records),-row.lml)

def test_inner_and_outer_frozen_partitions(context):
    t,s,p,r=context
    for protocol,repeat,fold,tr,va,inner in s:
        rows=r[(r.protocol==protocol)&(r['repeat']==repeat)&(r.fold==fold)]
        for row in rows.itertuples():
            atr=t.iloc[tr]
            aa=t.iloc[tr] if row.context=='outer' else atr.iloc[inner[row.inner_index][0]]
            vv=t.iloc[va] if row.context=='outer' else atr.iloc[inner[row.inner_index][1]]
            assert json.loads(row.train_ids)==aa[e.ID].tolist() and json.loads(row.validation_ids)==vv[e.ID].tolist()

def test_primary_metrics_and_repeat_aggregation(context):
    p=context[2];m=pd.read_csv(e.OUT/'tables/metrics_repeat.csv');summary=pd.read_csv(e.OUT/'tables/metrics_summary.csv')
    assert m.n.eq(138).all()
    for r in m.itertuples():
        q=p[(p.experiment==r.experiment)&(p.protocol==r.protocol)&(p['repeat']==r.repeat)];err=q.y_pred-q.y_true
        assert np.isclose(np.sqrt(np.mean(err**2)),r.RMSE) and np.isclose(np.mean(abs(err)),r.MAE) and np.isclose(err.mean(),r.bias)
    z=m.groupby(['experiment','protocol']).RMSE.mean().reset_index().merge(summary,on=['experiment','protocol'])
    np.testing.assert_allclose(z.RMSE_x,z.RMSE_y,atol=1e-12)

def test_variance_decomposition_and_interval_noise(context):
    q=context[2];q=q[q.experiment.ne('C-T3')]
    np.testing.assert_allclose(q.predictive_sd**2,q.latent_sd**2+q.noise_variance,atol=1e-12)
    assert (q.noise_variance>0).all() and (q.upper>=q.lower).all()

def test_sse_contributions_and_fold_omission():
    losses=pd.read_parquet(e.OUT/'tables/paired_parcel_losses.parquet');folds=pd.read_csv(e.OUT/'tables/paired_fold_contributions.csv');omit=pd.read_csv(e.OUT/'tables/fold_omission_sensitivity.csv')
    np.testing.assert_allclose(folds.SSE_gain,folds.bias_squared_gain+folds.error_variance_gain,atol=1e-10)
    for key,g in folds.groupby(['candidate','baseline','protocol','repeat']):
        z=losses[(losses.candidate==key[0])&(losses.baseline==key[1])&(losses.protocol==key[2])&(losses['repeat']==key[3])]
        assert np.isclose(g.SSE_gain.sum(),z.SE_gain.sum())
    for r in omit.itertuples():
        z=losses[(losses.candidate==r.candidate)&(losses.baseline==r.baseline)&(losses.protocol==r.protocol)&losses.fold.ne(r.omitted_fold)]
        assert len(z)==r.n and np.isclose(z.SE_gain.sum(),r.SSE_gain)
        assert np.isclose(np.sqrt(z.SE.mean())-np.sqrt(z.SE_base.mean()),r.delta_RMSE)

def test_pairs_same_model_and_climate_only_identical_predictions(context):
    pairs=pd.read_parquet(e.OUT/'tables/same_model_pair_errors.parquet');p=context[2].set_index(['experiment',e.ID,'protocol','repeat','fold'])
    z=pairs[pairs.experiment.eq('F5-00-C')];assert abs(z.predicted_difference).max()<1e-10
    for row in pairs.iloc[::max(1,len(pairs)//100)].itertuples():
        a=p.loc[(row.experiment,row.id_a,row.protocol,row.repeat,row.fold)];b=p.loc[(row.experiment,row.id_b,row.protocol,row.repeat,row.fold)]
        assert np.isclose((a.y_pred-b.y_pred)-(a.y_true-b.y_true),row.pair_error)
    summary=pd.read_csv(e.OUT/'tables/intraprofile_metrics_repeat.csv');assert summary.n_profiles.max()<=12

def test_frozen_bounds_and_sources_unchanged(context):
    config=json.loads((e.OUT/'frozen_execution_design.json').read_text())
    for path,digest in config['source_sha'].items():assert e.design.sha(e.ROOT/path)==digest,path
    assert config['optimizer']['n_restarts_optimizer']==2 and config['optimizer']['length_bounds']==[.2,20.]
    assert config['no_F5_02_06'] and set(config['authorized_experiments'])==set(e.SPECS)
    starts=json.loads((e.OUT/'tables/optimizer_starts.json').read_text());assert len(starts)==1950

def test_prior_hashes_unchanged():
    z=pd.read_csv(e.OUT/'audit/protected_inputs.csv')
    for r in z.itertuples():assert e.design.sha(e.ROOT/r.path)==r.sha256,r.path

def test_decision_guard_and_no_champion_promotion():
    decision=json.loads((e.OUT/'report/decision.json').read_text())
    p=pd.read_csv(e.OUT/'tables/paired_metrics_summary.csv');q=p[(p.candidate=='F5-01')&p.baseline.eq('C-T3')].set_index('protocol')
    assert np.isclose(decision['municipal_gain_t_ha'],-q.loc['municipality','delta_RMSE'])
    assert not decision['promote_champion']
    assert decision['overall_acceptance']==(decision['primary_municipal_practical_gain_pass'] and decision['other_global_cost_guard_pass'] and decision['municipal_distribution_guard_pass'])

def test_figures_and_documentation_traceable():
    text=(e.OUT/'report/technical_report.md').read_text(encoding='utf8')
    for path in (e.OUT/'figures').glob('*.png'):assert path.name in text and path.stat().st_size>1000
    assert len(list((e.OUT/'figures').glob('*.png')))==9
    assert 'sin ajustar otra vez' in text and 'no garantías' in (e.OUT/'report/decision_summary.md').read_text(encoding='utf8')
