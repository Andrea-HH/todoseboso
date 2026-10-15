import json
import joblib,numpy as np,pandas as pd
from threadpoolctl import threadpool_limits
from src.family_6 import execution as e
from src.family_6.reporting import metric_summary

def test_saved_selected_models_and_train_only_transforms():
    _,t,splits=e.load();index=t.set_index(e.ID,drop=False);decision=json.loads((e.OUT/'report/continuation_decision.json').read_text())
    with threadpool_limits(limits=1):
        for name in decision['executed']:
            for protocol,repeat,fold,tr,va,inner in splits:
                stem=f'{name}_{protocol}_{repeat}_{fold}';pack=joblib.load(e.OUT/'checkpoints'/f'{stem}.joblib')
                contexts=[('outer',pack['outer'])]+[(f'inner_{j}',p) for j,p in enumerate(pack['selected_inner'])]
                for context,fit in contexts:
                    reg=fit['registry'];a=index.loc[json.loads(reg['train_ids'])];v=index.loc[json.loads(reg['validation_ids'])]
                    model=joblib.load(e.OUT/'models'/f'{stem}_{context}.joblib')
                    np.testing.assert_allclose(model.predict(v),[r['y_pred'] for r in fit['predictions']],atol=1e-12,rtol=0)
                    np.testing.assert_allclose(model.preprocess_.median_,a[e.SPECS[name]['columns']].median(),atol=1e-12)
                    np.testing.assert_allclose(model.training_y_,a[e.TARGET],atol=1e-12)
                    assert not set(a[e.ID])&set(v[e.ID]);assert len(model.forest_.estimators_)==384

def test_candidate_selection_and_original_inner_memberships():
    _,t,splits=e.load();decision=json.loads((e.OUT/'report/continuation_decision.json').read_text())
    for name in decision['executed']:
        for protocol,repeat,fold,tr,va,inner in splits:
            a=t.iloc[tr];pack=joblib.load(e.OUT/'checkpoints'/f'{name}_{protocol}_{repeat}_{fold}.joblib');assert len(pack['inner'])==32
            scores=[]
            for candidate in range(8):
                ps=[p for p in pack['inner'] if p['registry']['candidate_index']==candidate];rmse=[]
                for j,p in enumerate(ps):
                    reg=p['registry'];it,iv=inner[j]
                    assert json.loads(reg['train_ids'])==a.iloc[it][e.ID].tolist();assert json.loads(reg['validation_ids'])==a.iloc[iv][e.ID].tolist()
                    np.testing.assert_allclose([r['y_true'] for r in p['predictions']],a.iloc[iv][e.TARGET],atol=1e-12)
                    rmse.append(np.sqrt(np.mean([(r['y_pred']-r['y_true'])**2 for r in p['predictions']])))
                scores.append(np.mean(rmse));np.testing.assert_allclose(scores[-1],pack['tuning'][candidate]['mean_inner_fold_RMSE'],atol=1e-12)
            expected=min(range(8),key=lambda j:(round(scores[j],10),j));assert pack['outer']['registry']['candidate_index']==expected

def test_oof_coverage_controls_metrics_and_gate():
    p=pd.read_parquet(e.OUT/'tables/oof_predictions.parquet');ref=pd.read_parquet(e.OUT/'tables/reference_oof.parquet')
    pd.testing.assert_frame_equal(p.iloc[:len(ref)][ref.columns].reset_index(drop=True),ref,check_dtype=False)
    for _,g in p.groupby(['experiment','protocol','repeat']):assert len(g)==138 and g[e.ID].nunique()==138
    _,expected=metric_summary(p);actual=pd.read_csv(e.OUT/'tables/metrics_summary.csv')
    key=['experiment','protocol'];a=expected.set_index(key);b=actual.set_index(key)
    np.testing.assert_allclose(a[['RMSE','MAE','bias']].sort_index(),b[['RMSE','MAE','bias']].sort_index(),atol=1e-12)
    decision=json.loads((e.OUT/'report/continuation_decision.json').read_text())
    for row in decision['criteria']:
        passed=row['municipal_RMSE_gain']>=.01 and row['max_RMSE_MAE_harm']<=.01 and row['municipal_improving_folds']>=3 and row['max_space_omission_RMSE_harm']<=.01
        assert row['passes']==passed
    assert decision['run_predefined_ablations']==any(r['passes'] for r in decision['criteria'])
    if not decision['run_predefined_ablations']:assert set(p[p.experiment.str.startswith('F6-')].experiment)=={'F6-00','F6-01'}

def test_bias_variance_identity_sources_and_no_PRED():
    q=pd.read_csv(e.OUT/'tables/paired_fold_contributions.csv');np.testing.assert_allclose(q.SSE_gain,q.bias_squared_gain+q.error_variance_gain,atol=1e-10)
    cfg=json.loads((e.OUT/'frozen_design.json').read_text())
    for path,h in cfg['source_sha'].items():assert e.design.sha(e.ROOT/path)==h
    assert cfg['no_PRED'] and cfg['no_final_training']
    registry=pd.read_csv(e.OUT/'tables/fit_registry.csv');_,t,_=e.load();ids=set(t[e.ID])
    assert registry.n_train.max()<138
    for row in registry.itertuples():assert set(json.loads(row.train_ids))<=ids and set(json.loads(row.validation_ids))<=ids
