import numpy as np,pandas as pd,pytest
from src.family_7.expansion import execution as e
from src.family_7.models import CB_GRID,BoostModel
from src.family_7.expansion.diagnostics import conditional_permutation
def test_frozen_scope_and_adapter_restores():
    cfg=__import__('json').loads((e.initial.OUT/'frozen_design.json').read_text())
    assert e.SPECS==cfg['extensions_not_executed'] and CB_GRID==cfg['grids']['CatBoost']
    old=e.base.OUT,e.base.SPECS,e.base.load,e.base.TreeModel,e.base.GRID
    with pytest.raises(RuntimeError):
        with e.redirected_engine():
            assert e.base.TreeModel is BoostModel and e.base.GRID==CB_GRID
            raise RuntimeError()
    assert (e.base.OUT,e.base.SPECS,e.base.load,e.base.TreeModel,e.base.GRID)==old
    assert all(s['algorithm']=='CatBoost' for s in e.SPECS.values())
def test_joint_permutation_preserves_history_relationship():
    class Preprocess:
        def transform(self,x):return x[['h1','h2']].to_numpy()
    class Model:
        preprocess_=Preprocess();training_z_=np.tile(np.arange(20)[:,None],(1,2))*np.array([1,2])
        def predict(self,x):
            np.testing.assert_array_equal(x.h2,2*x.h1)
            return x.h1.to_numpy()
    v=pd.DataFrame({'h1':np.arange(20),'h2':2*np.arange(20),'climate_profile':['a']*20,e.TARGET:np.arange(20)})
    rows=conditional_permutation(Model(),v,['h1','h2'],np.arange(20),1)
    assert len(rows)==10 and all(r['n_supported']==20 for r in rows)
def test_permutation_support_gate_before_prediction():
    class Preprocess:
        def transform(self,x):return x[['a']].to_numpy()
    class Model:
        preprocess_=Preprocess();training_z_=np.arange(20)[:,None]
        def predict(self,x):raise AssertionError('No unsupported predictions')
    v=pd.DataFrame({'a':np.arange(20)+100,'climate_profile':['a']*20,e.TARGET:np.arange(20)})
    rows=conditional_permutation(Model(),v,['a'],np.arange(20),1)
    assert all(np.isnan(r['delta_MSE']) and r['n_supported']==0 for r in rows)
