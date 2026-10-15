import numpy as np,pandas as pd,pytest
from src.family_7 import execution as e
from src.family_7.models import BoostModel,GRIDS
from src.family_6.expansion.diagnostics import supported_effect

def test_scope_and_adapter_restoration():
    old=e.base.OUT,e.base.SPECS,e.base.TreeModel,e.base.GRID,e.base.load
    with pytest.raises(RuntimeError):
        with e.redirected_engine('CatBoost'):
            assert e.base.TreeModel is BoostModel and e.base.GRID==GRIDS['CatBoost']
            raise RuntimeError()
    assert (e.base.OUT,e.base.SPECS,e.base.TreeModel,e.base.GRID,e.base.load)==old
    assert set(e.SPECS)=={'F7-00','F7-01'}
    assert all(s['algorithm']=='CatBoost' for s in e.EXTENSIONS.values())
    for spec in e.SPECS.values():assert spec['columns']==e.CORE
    for grid in GRIDS.values():assert len(grid)==8

@pytest.mark.parametrize('algorithm',['CatBoost','XGBoost'])
def test_train_only_preprocessing_repeated_rows_and_native_scale(algorithm):
    x=pd.DataFrame({'a':[0,0,1,1,2,2,np.nan,3]*3,'b':[.1,.1,.2,.2,.3,.3,.4,.5]*3,'ignored':np.arange(24)})
    y=4+x.a.fillna(1).to_numpy()*.1
    params=GRIDS[algorithm][0].copy()
    if algorithm=='CatBoost':params['iterations']=5
    else:params['n_estimators']=5
    m=BoostModel(['a','b'],algorithm,params).fit(x,y)
    np.testing.assert_allclose(m.preprocess_.median_,x[['a','b']].median())
    yp=m.predict(x);assert np.isfinite(yp).all();np.testing.assert_allclose(yp[0],yp[1])
    changed=x.copy();changed.ignored=1e9;np.testing.assert_allclose(m.predict(changed),yp)
    before=m.preprocess_.mean_.copy();changed.a=1e8;m.predict(changed)
    np.testing.assert_array_equal(m.preprocess_.mean_,before)
    assert m.parameters()['actual_trees']==5 and not m.parameters()['external_eval_set']
    assert 3<yp.mean()<6

def test_support_gate_before_any_prediction():
    class Model:
        class Preprocess:
            def transform(self,x):return x[['a']].to_numpy()
        preprocess_=Preprocess();training_z_=np.arange(10)[:,None]
        def predict(self,x):raise AssertionError('Unsupported points must never be predicted')
    q=supported_effect(Model(),pd.DataFrame({'a':np.arange(10)}),['a'],[100],[101],1)
    assert not q['supported'] and np.isnan(q['effect'])
