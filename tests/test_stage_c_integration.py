import json
import joblib
import numpy as np
import pandas as pd
import pytest
from src.family_4 import stage_c_models as c

@pytest.fixture(scope='module')
def data():
    d,t=c.load()
    return d,t,c.b.e.f.lm.k.j.load_frozen_splits(t)[0],pd.read_parquet(c.OUT/'tables/oof_predictions.parquet')

def test_target_free_and_complete_oof(data):
    d,t,splits,p=data
    assert c.TARGET not in d and len(d)==197 and len(t)==138 and len(splits)==65
    assert len(p)==14352 and p.experiment.nunique()==8
    assert set(p[c.ID])==set(t[c.ID])
    assert not p.duplicated(['experiment','protocol','repeat',c.ID]).any()
    assert np.isfinite(p[['y_true','y_pred']]).all().all()

@pytest.mark.parametrize('experiment',list(c.T_SPECS)+['C-H0M','C-H1'])
def test_every_saved_model_replays_with_training_only_preprocessing(data,experiment):
    d,t,splits,p=data
    for protocol,repeat,fold,tr,va,inner in splits:
        a,v=t.iloc[tr],t.iloc[va]
        m=joblib.load(c.OUT/'models'/f'{experiment}_{protocol}_{repeat}_{fold}.joblib')
        q=p[(p.experiment==experiment)&(p.protocol==protocol)&(p['repeat']==repeat)&(p.fold==fold)].set_index(c.ID).loc[v[c.ID]]
        np.testing.assert_allclose(m.predict(v),q.y_pred,atol=1e-12)
        pre=m['repr'] if experiment in c.T_SPECS else m.preprocess_
        np.testing.assert_allclose(pre.median_,np.nanmedian(a[list(pre.cols)],axis=0),atol=1e-12)
        assert set(a[c.ID]).isdisjoint(v[c.ID])
        if experiment.startswith('C-H'):
            pieces=m.predict_components(v)
            known=v.climate_profile.isin(a.climate_profile).to_numpy()
            np.testing.assert_array_equal(pieces['profile_known'],known)
            assert (pieces['random_effect'][~known]==0).all()
            assert m.diagnostics_['converged'] and m.alpha in c.b.e.f.lm.k.ALPHA and m.ratio in c.RATIO
            assert np.linalg.eigvalsh(m.cov_theta_).min()>-1e-12
            for group in v.climate_profile.unique():
                idx=np.flatnonzero(v.climate_profile.to_numpy()==group)
                np.testing.assert_allclose(np.diff(pieces['prediction'][idx]),np.diff(pieces['fixed_prediction'][idx]),atol=1e-12)
        for it,iv in inner:
            assert set(a.iloc[it][c.ID]).isdisjoint(a.iloc[iv][c.ID])

def test_controls_and_frozen_sources(data):
    p=data[-1]
    old=pd.read_parquet(c.b.e.f.OUT/'tables/oof_predictions.parquet')
    keys=['protocol','repeat','fold',c.ID]
    for name,source in [('C-T0','F4-S1'),('C-T1','F4-S5'),('C-H0','F4-S1')]:
        q=p[p.experiment==name].set_index(keys).sort_index()
        z=old[old.experiment==source].set_index(keys).sort_index()
        np.testing.assert_array_equal(q.y_pred,z.y_pred)
    config=json.loads((c.OUT/'frozen_design.json').read_text())
    assert all(c.b.a.sha(c.ROOT/path)==digest for path,digest in config['source_hashes'].items())
    assert pd.read_csv(c.OUT/'audit/control_reproduction.csv').max_abs_difference.max()<=1e-10
