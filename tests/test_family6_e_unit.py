import numpy as np,pandas as pd
from src.family_6 import execution as base
from src.family_6.expansion import execution as e

def test_adapter_restores_original_engine_on_exception():
    before=base.OUT,base.SPECS,base.load
    try:
        with e.redirected_engine():
            assert base.OUT==e.OUT and base.SPECS==e.SPECS and base.load==e.load
            raise RuntimeError('intentional restoration check')
    except RuntimeError:pass
    assert (base.OUT,base.SPECS,base.load)==before

def test_authorized_blocks_and_original_regularization():
    assert set(e.SPECS)=={'F6-E1','F6-E2','F6-E3'}
    assert [len(e.SPECS[k]['columns']) for k in e.SPECS]==[6,5,5]
    assert e.GRID==base.GRID and e.N_TREES==384 and e.SEED==2026
    assert e.BLOCKS['F6-E1']==['HIST_S2_ndvi_promedio_mean','HIST_S2_ndvi_promedio_std']

class Identity:
    def transform(self,X):return X[['a','b']].to_numpy(float)

class KnownModel:
    def __init__(self,X):self.preprocess_=Identity();self.training_z_=self.preprocess_.transform(X);self.n_predictions=0
    def predict(self,X):self.n_predictions+=1;return X.a.to_numpy()*X.b.to_numpy()

def test_corner_support_rejects_before_predicting():
    from src.family_6.expansion.diagnostics import supported_effect,support_radius
    X=pd.DataFrame([(a,b) for a in np.arange(8.) for b in np.arange(8.)],columns=['a','b']);m=KnownModel(X)
    radius=support_radius(m);np.testing.assert_allclose(radius,1.)
    result=supported_effect(m,X,['a','b'],[0,0],[100,100],radius)
    assert not result['supported'] and np.isnan(result['effect']) and m.n_predictions==0
    result=supported_effect(m,X,['a','b'],[0,0],[1,1],radius)
    assert result['supported'];np.testing.assert_allclose(result['effect'],1.)

def test_history_joint_permutation_and_constant_profile_limit():
    from src.family_6.expansion.diagnostics import conditional_block_permutation
    X=pd.DataFrame({'a':np.arange(20.),'b':2*np.arange(20.),'climate_profile':np.repeat([0,1],10),e.TARGET:np.arange(20.)})
    class PairModel:
        def predict(self,X):
            np.testing.assert_allclose(X.b,2*X.a)
            return X.a.to_numpy()
    z=conditional_block_permutation(PairModel(),X,['a','b'],X.a.to_numpy())
    assert len(z)==10 and all(r['delta_MSE']>=0 for r in z)
    X['a']=X.climate_profile;X['b']=2*X.a
    z=conditional_block_permutation(PairModel(),X,['a','b'],X.a.to_numpy())
    assert z[0]['permutation']==-1 and np.isnan(z[0]['delta_MSE'])
