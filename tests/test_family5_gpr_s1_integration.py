import json
import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from src.family_5.gpr_s1 import execution as e

def test_exact_reference_oof_and_complete_outer_coverage():
    p=pd.read_parquet(e.OUT/'tables/oof_predictions.parquet');ref=pd.read_parquet(e.old.OUT/'tables/oof_predictions.parquet')
    pd.testing.assert_frame_equal(p.iloc[:len(ref)][ref.columns].reset_index(drop=True),ref,check_dtype=False)
    assert len(p)==10764
    for _,g in p.groupby(['experiment','protocol','repeat']):assert len(g)==138 and g[e.ID].nunique()==138
    _,t,splits=e.load()
    for protocol,repeat,fold,tr,va,inner in splits:
        for x in ['F5-01','F5-00-C','C-T3']:
            path=e.old.c.OUT/'models'/f'C-T3_{protocol}_{repeat}_{fold}.joblib' if x=='C-T3' else e.old.OUT/'models'/f'{x}_{protocol}_{repeat}_{fold}_outer_-1.joblib'
            model=joblib.load(path);v=t.iloc[va]
            q=p[(p.experiment==x)&(p.protocol==protocol)&(p['repeat']==repeat)&(p.fold==fold)].set_index(e.ID).loc[v[e.ID]]
            with threadpool_limits(limits=1):np.testing.assert_allclose(model.predict(v),q.y_pred,atol=1e-12,rtol=0)
        for x in e.SPECS:
            q=p[(p.experiment==x)&(p.protocol==protocol)&(p['repeat']==repeat)&(p.fold==fold)]
            assert set(q[e.ID])==set(t.iloc[va][e.ID])
            assert not set(q[e.ID])&set(t.iloc[tr][e.ID])

def test_all_model_replays_and_train_only_transformations():
    _,t,_=e.load();indexed=t.set_index(e.ID,drop=False)
    registry=pd.read_csv(e.OUT/'tables/fit_registry.csv');assert len(registry)==1755
    with threadpool_limits(limits=1):
        for row in registry.itertuples():
            a=indexed.loc[json.loads(row.train_ids)];v=indexed.loc[json.loads(row.validation_ids)]
            model=joblib.load(e.ROOT/row.model_path)
            pack=joblib.load(e.OUT/'checkpoints'/e.Path(row.model_path).name)
            np.testing.assert_allclose(model.predict(v),[r['y_pred'] for r in pack['predictions']],atol=1e-12,rtol=0)
            np.testing.assert_allclose(model.preprocess_.median_,a[list(e.SPECS[row.experiment])].median().to_numpy(),atol=1e-12)
            gp=model.residual_gp_ if row.experiment=='F5-S1-C' else model
            target=a[e.TARGET].to_numpy()
            if row.experiment=='F5-S1-C':target=target-model.linear_.predict(model.transform(a))
            np.testing.assert_allclose(gp.target_mean_,target.mean(),atol=1e-12)
            np.testing.assert_allclose(gp.target_scale_,target.std(),atol=1e-12)
            assert not set(a[e.ID])&set(v[e.ID])

def test_inner_selection_is_full_pipeline_and_fixed():
    tuning=pd.read_csv(e.OUT/'tables/inner_selection.csv');registry=pd.read_csv(e.OUT/'tables/fit_registry.csv')
    inner=pd.read_parquet(e.OUT/'tables/all_inner_candidates.parquet')
    for keys,g in tuning.groupby(['experiment','protocol','repeat','fold']):
        for row in g.itertuples():
            h=inner[(inner.experiment==keys[0])&(inner.protocol==keys[1])&(inner['repeat']==keys[2])&(inner.fold==keys[3])&(inner.selection_alpha==row.alpha)]
            rmses=[np.sqrt(np.mean((v.y_pred-v.y_true)**2)) for _,v in h.groupby('inner_index')]
            assert len(rmses)==4
            np.testing.assert_allclose(np.mean(rmses),row.mean_inner_fold_RMSE,atol=1e-12)
        expected=min(g.to_dict('records'),key=lambda x:(round(x['mean_inner_fold_RMSE'],10),-x['alpha']))['alpha']
        assert g[g.selected].alpha.iloc[0]==expected
        h=registry[(registry.experiment==keys[0])&(registry.protocol==keys[1])&(registry['repeat']==keys[2])&(registry.fold==keys[3])&(registry.context=='outer')]
        assert h.selection_alpha.iloc[0]==expected
        if keys[0]=='F5-S1-C':assert set(g.alpha)==set(e.ALPHAS)

def test_bias_variance_decomposition_and_frozen_sources():
    z=pd.read_csv(e.OUT/'tables/paired_fold_contributions.csv')
    np.testing.assert_allclose(z.SSE_gain,z.bias_squared_gain+z.error_variance_gain,atol=1e-10)
    cfg=json.loads((e.OUT/'frozen_execution_design.json').read_text())
    for path,digest in cfg['source_sha'].items():assert e.old.design.sha(e.ROOT/path)==digest
    assert cfg['no_PRED'] and cfg['expected_fits']==1755
