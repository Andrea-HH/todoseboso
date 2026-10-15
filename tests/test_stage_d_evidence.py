import ast,json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from src.family_4 import stage_d_evidence as d
from src.family_4 import stage_c_models as c

@pytest.fixture(scope='module')
def context():
    return d.load()

def table(name):return pd.read_csv(d.OUT/'tables'/name)

def test_identity_labels(context):
    _,t,p,_=context
    np.testing.assert_array_equal(p.y_true,p[d.ID].map(t.set_index(d.ID)[d.TARGET]))

def test_identity_parcels(context):
    a,t,p,_=context
    assert len(a)==197 and len(t)==138 and set(p[d.ID])==set(t[d.ID])

def test_hidden_labels_unused(context):
    a,t,p,_=context
    assert d.TARGET not in a and len(set(a[d.ID])-set(t[d.ID]))==59
    assert set(p[d.ID]).isdisjoint(set(a[d.ID])-set(t[d.ID]))

def test_folds_preserved(context):
    _,t,p,splits=context
    assert len(splits)==65
    for exp,g in p.groupby('experiment'):
        for protocol,r,f,tr,va,inner in splits:
            q=g[(g.protocol==protocol)&(g['repeat']==r)&(g.fold==f)]
            if len(q):assert set(q[d.ID])==set(t.iloc[va][d.ID]) and set(t.iloc[tr][d.ID]).isdisjoint(q[d.ID])

def test_exact_pair_compatibility():
    z=table('comparability.csv')
    assert z.exact_keys.all() and z.identical_y.all() and z.n_unique_ids.eq(138).all()

def test_archived_C_metrics_reproduced():
    new=table('metrics_summary.csv');old=pd.read_csv(c.OUT/'tables/metrics_summary.csv');old=old[old.stratum.eq('all')]
    new=new.copy();new.experiment=new.experiment.replace({d.BASE:'C-T0'})
    z=new.merge(old,on=['experiment','protocol'],suffixes=('','_old'))
    assert len(z)==16
    for f in ['RMSE','MAE']:np.testing.assert_allclose(z[f],z[f+'_old'],atol=1e-12)

def test_primary_aggregation():
    a=table('metrics_repeat.csv');b=table('metrics_summary.csv')
    assert a.n.eq(138).all()
    z=a.groupby(['experiment','protocol']).RMSE.mean().reset_index().merge(b,on=['experiment','protocol'])
    np.testing.assert_allclose(z.RMSE_x,z.RMSE_y,atol=1e-12)

def test_sse_correct(context):
    p=context[2]
    for _,g in p.groupby(['experiment','protocol','repeat']):
        m=d.metrics(g);assert np.isclose(m['SSE'],np.sum((g.y_true-g.y_pred)**2))
        assert np.isclose(m['SSE'],m['n']*m['RMSE']**2)

def test_sum_block_gains():
    z=table('spatial_block_gains.csv');loss=pd.read_parquet(d.OUT/'tables/paired_losses.parquet')
    for exp,g in z.groupby('candidate'):
        q=loss[(loss.candidate==exp)&(loss.baseline==d.BASE)&(loss.protocol=='spatial')]
        assert np.isclose(g.sse_gain.sum(),q.SE_gain.sum())
    b=table('block_bias_variance_decomposition.csv');np.testing.assert_allclose(b.sse_gain,b.bias_squared_gain+b.error_variance_gain,atol=1e-12)

def test_omission_uses_archived_predictions(context):
    p=context[2];z=table('spatial_block_omission.csv')
    for _,r in z.iterrows():
        g=p[(p.protocol=='spatial')&p.fold.ne(r.omitted_block)]
        a=d.metrics(g[g.experiment==r.candidate]);b=d.metrics(g[g.experiment==r.baseline])
        assert a['n']==r.n and np.isclose(a['RMSE']-b['RMSE'],r.delta_RMSE)

def test_repetition_losses_grouped_per_parcel():
    a=pd.read_parquet(d.OUT/'tables/paired_losses.parquet');b=table('paired_loss_summary.csv')
    for _,r in b.iterrows():
        z=a[(a.candidate==r.candidate)&(a.baseline==r.baseline)&(a.protocol==r.protocol)].groupby(d.ID)[r.loss].mean()
        assert len(z)==138 and np.isclose(z.mean(),r.mean_gain)

def test_pairs_same_model_without_pseudoreplication(context):
    a=pd.read_parquet(d.OUT/'tables/same_model_pair_errors.parquet');p=context[2].set_index(['experiment']+d.KEY)
    assert (a.id_a!=a.id_b).all()
    for row in a.iloc[::max(1,len(a)//100)].itertuples():
        for pid in [row.id_a,row.id_b]:assert (row.experiment,pid,row.protocol,row.repeat,row.fold) in p.index
    m=table('equal_profile_pair_metrics_repeat.csv');assert m.n_profiles.max()<=12

def test_protocols_separated():
    a=table('metrics_random_compatible.csv');b=table('metrics_geographic_compatible.csv')
    assert a.protocol.eq('random').all() and b.protocol.ne('random').all()
    assert not b.experiment.isin(['CHAMPION','FIXED_50_50']).any()

def test_influential_observations_retained(context):
    a=table('gain_concentration.csv');p=context[2]
    for ids in a.top_ids:
        assert set(json.loads(ids)).issubset(set(p[d.ID]))
    assert table('persistent_case_audit.csv')[d.ID].nunique()==138

def test_prior_integrity():
    a=pd.read_csv(d.OUT/'audit/protected_inputs.csv')
    assert len(a)>2434
    for r in a.itertuples():assert c.b.a.sha(d.ROOT/r.path)==r.sha256,r.path

def test_champion_unchanged_and_archived_alias(context):
    p=pd.read_parquet(c.b.OUT/'tables/fixed_blend_oof.parquet')
    q=context[2];cols=d.KEY+['y_true','y_pred']
    for exp in ['CHAMPION','FIXED_50_50']:
        pd.testing.assert_frame_equal(q[q.experiment.eq(exp)][cols].sort_values(d.KEY).reset_index(drop=True),p[p.experiment.eq(exp)][cols].sort_values(d.KEY).reset_index(drop=True))
    source=pd.read_parquet(d.ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization/predictions/oof_predictions.parquet');source=source[source.architecture.eq('A_CURRENT_CH_H_T')].copy();source['protocol']='random'
    pd.testing.assert_frame_equal(q[q.experiment.eq('CHAMPION')][cols].sort_values(d.KEY).reset_index(drop=True),source[cols].sort_values(d.KEY).reset_index(drop=True))

def test_no_estimator_training_in_stage_D():
    for path in (d.ROOT/'src/family_4').glob('stage_d*.py'):
        tree=ast.parse(path.read_text(encoding='utf8'))
        for node in ast.walk(tree):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):assert node.func.attr not in ['fit','fit_predict','fit_transform','partial_fit','predict','predict_proba']
    assert not (d.OUT/'models').exists()

def test_traceability_of_tables_figures():
    text=(d.OUT/'report/technical_report.md').read_text(encoding='utf8')
    assert len(list((d.OUT/'figures').glob('*.png')))==12
    for path in (d.OUT/'figures').glob('*.png'):assert path.name in text and path.stat().st_size>1000
    assert (d.OUT/'tables/model_inventory.csv').exists()

def test_reports_consistent():
    technical=(d.OUT/'report/technical_report.md').read_text(encoding='utf8');executive=(d.OUT/'report/executive_summary.md').read_text(encoding='utf8')
    for word in ['0.581','0.671','0.493','0.498']:assert word in technical and word in executive
    for text in [technical,executive]:assert '138' in text and 'Champion' in text and 'bloque' in text and 'no' in text.lower()

def test_support_limits_explicit():
    z=table('spatial_support.csv');assert len(z)==138
    assert z[c.DTR+'_support'].isin(['outside','near_boundary','interior']).all()
    text=(d.OUT/'report/technical_report.md').read_text(encoding='utf8')
    assert 'no garantiza' in text and 'no equivale' in text
