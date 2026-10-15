import ast,json
import numpy as np
import pandas as pd
import pytest
from src.family_5 import gpr_evidence_design as g

@pytest.fixture(scope='module')
def context():return g.data()

def test_proposal_only():
    config=json.loads((g.OUT/'proposed_design.json').read_text())
    assert config['status']=='proposal_only_not_approved_for_execution'
    assert config['no_model_training'] and config['no_optimizer_called'] and config['no_final_prediction']
    assert not (g.OUT/'models').exists() and not (g.OUT/'predictions').exists()

def test_no_training_or_prediction_code():
    for path in (g.ROOT/'src/family_5').glob('*.py'):
        tree=ast.parse(path.read_text(encoding='utf8'))
        for n in ast.walk(tree):
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute):assert n.func.attr not in ['fit','fit_transform','fit_predict','predict','partial_fit','minimize']
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Name):assert n.func.id!='GaussianProcessRegressor'

def test_exact_candidates_and_no_territorial_identity(context):
    a,t,f=context;m=pd.read_csv(g.OUT/'tables/experimental_matrix.csv')
    prohibited={g.ID,g.c.TARGET,'longitude','latitude','Municipio','Estado','climate_profile','CONJUNTO'}
    for values in m['columns'].map(json.loads):assert set(values)<=set(t) and set(values).isdisjoint(prohibited)
    inventory=pd.read_csv(g.OUT/'tables/candidate_variable_inventory.csv');assert set(inventory.column)<=set(t)

def test_labels_and_hidden_y(context):
    a,t,f=context
    assert len(t)==138 and len(a)==197 and g.c.TARGET not in a
    assert len(set(a[g.ID])-set(t[g.ID]))==59
    assert not (g.OUT/'data').exists()

def test_semantic_verifications():
    a=json.loads((g.OUT/'audit/semantic_checks.json').read_text())
    for field in ['ndvi_may_exact','history_mean_exact','history_std_exact','DTR_exact','slope_alias_exact','no_y_used_for_feature_verification']:assert a[field]
    assert 'NOT interannual' in a['history_std_definition']

def test_historical_std_and_constants(context):
    _,t,f=context
    assert t.filter(regex=r'^HIST_S2_.*_months$').nunique().eq(1).all()
    np.testing.assert_allclose(t.slope_degrees,t[g.SLOPE],atol=1e-12)
    assert g.HISTORY==['HIST_S2_ndvi_promedio_mean','HIST_S2_ndvi_promedio_std']

def test_matrix_parameter_counts():
    m=pd.read_csv(g.OUT/'tables/experimental_matrix.csv').set_index('experiment')
    assert len(m)==8
    expected={'F5-00-C':3,'F5-00-M':3,'F5-01':4,'F5-02':5,'F5-03':5,'F5-04':5,'F5-05':7,'F5-06':6}
    assert m.n_kernel_hyperparameters.to_dict()==expected
    assert m.status.eq('proposed_for_review_NOT_EXECUTED').all()

def test_top15_recovered_exactly():
    sets=pd.read_csv(g.OUT/'tables/history_top15_exact_fold_sets.csv');freq=pd.read_csv(g.OUT/'tables/history_top15_frequencies.csv')
    assert len(sets)==150
    assert sets.history15_features.map(lambda x:len(json.loads(x))).eq(15).all()
    for r in freq.itertuples():
        z=sets[sets.baseline.eq(r.baseline)].history15_features.map(json.loads)
        assert sum(r.feature in x for x in z)==r.n_selected
    assert freq.groupby('baseline').feature.nunique().eq(16).all()

def test_archived_metrics_reaggregated():
    a=pd.read_csv(g.OUT/'tables/historical_metrics_repeat_recomputed.csv');b=pd.read_csv(g.OUT/'tables/historical_metrics_oof_recomputed.csv')
    assert a.n.eq(138).all()
    z=a.groupby(['stage','experiment']).RMSE.mean().reset_index().merge(b,on=['stage','experiment'])
    np.testing.assert_allclose(z.RMSE_x,z.RMSE_y,atol=1e-12)
    old=pd.read_csv(g.c.b.OUT/'tables/fixed_blend_metrics_repeat.csv') if (g.c.b.OUT/'tables/fixed_blend_metrics_repeat.csv').exists() else None
    r=b[b.experiment.eq('A_CURRENT_CH_H_T')].RMSE.iloc[0];assert np.isclose(r,.4981269,atol=1e-7)

def test_original_folds_and_labels(context):
    t=context[1];splits=g.c.b.e.f.lm.k.j.load_frozen_splits(t)[0]
    z=pd.read_parquet(g.ROOT/'outputs/modeling/residual_signal_audit/stage4_champion_reconstruction/predictions/oof_predictions.parquet')
    for exp,model in z.groupby('pipeline'):
        np.testing.assert_array_equal(model.y_true,model[g.ID].map(t.set_index(g.ID)[g.c.TARGET]))
        for protocol,r,f,tr,va,inner in splits:
            if protocol!='random':continue
            q=model[(model['repeat']==r)&(model.fold==f)];assert set(q[g.ID])==set(t.iloc[va][g.ID])

def test_covariate_redundancy_only_TRAIN(context):
    t=context[1];z=pd.read_csv(g.OUT/'tables/predictor_pearson_TRAIN138.csv',index_col=0)
    assert g.c.TARGET not in z and g.ID not in z
    np.testing.assert_allclose(z.loc[g.CORE,g.CORE],t[g.CORE].corr(),atol=1e-12)
    p=pd.read_csv(g.OUT/'tables/representation_geometry.csv');assert p.n.eq(138).all()

def test_source_temperature_correction():
    z=pd.read_csv(g.OUT/'tables/candidate_variable_inventory.csv')
    thermal=z[z.column.str.contains('tmin|tmax')|z.column.eq(g.c.DTR)]
    assert thermal.source.str.contains('CHIRTS-ERA5').all()

def test_previous_artifact_integrity():
    z=pd.read_csv(g.OUT/'audit/protected_inputs.csv')
    assert len(z)>5108
    for r in z.itertuples():assert g.sha(g.ROOT/r.path)==r.sha256,r.path
    previous=json.loads((g.d.OUT/'manifest.json').read_text())
    for p,h in previous['artifacts'].items():assert g.sha(g.ROOT/p)==h,p

def test_documents_and_primary_sources():
    reports=['evidence_audit.md','candidate_inventory.md','redundancy_analysis.md','technical_proposal.md','experimental_matrix.md','recommendation.md']
    for name in reports:assert (g.OUT/'report'/name).stat().st_size>500
    text=(g.OUT/'report/technical_proposal.md').read_text(encoding='utf8')
    assert 'suspendida' in text and 'cross-fitting' in text and 'WhiteKernel' in text
    assert 'https://scikit-learn.org/1.7/' in text and 'https://gaussianprocess.org/' in text
    assert len(list((g.OUT/'figures').glob('*.png')))==2
