import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import KFold
from src.four_expert_fast_tuner import CORE,ORIGINAL,tune_base_cached_repr

@pytest.mark.parametrize('all_nan',[False,True])
def test_grid_preprocessing_reuse_preserves_scores_selection_and_predictions(all_nan):
    rng=np.random.default_rng(31);frame=pd.DataFrame(rng.normal(size=(54,4)),columns=CORE);frame.loc[::7,CORE[0]]=np.nan
    if all_nan:frame[CORE[3]]=np.nan
    y=rng.normal(size=54);tr=np.arange(43);cv=list(KFold(4,shuffle=True,random_state=2026).split(tr));a,ar,al=ORIGINAL(frame,y,tr,cv);b,br,bl=tune_base_cached_repr(frame,y,tr,cv)
    assert ar['params']==br['params'] and ar['fit_count']==br['fit_count'];np.testing.assert_allclose(ar['candidate_mean_rmse'],br['candidate_mean_rmse'],atol=1e-14,rtol=0);np.testing.assert_allclose(a.predict(frame),b.predict(frame),atol=1e-12,rtol=0);assert al==bl

def test_constant_core_mean_fallback_unchanged():
    frame=pd.DataFrame(np.ones((20,4)),columns=CORE);y=np.arange(20.);tr=np.arange(15);cv=list(KFold(3).split(tr));a,ar,al=ORIGINAL(frame,y,tr,cv);b,br,bl=tune_base_cached_repr(frame,y,tr,cv);np.testing.assert_array_equal(a.predict(frame),b.predict(frame));assert ar['fallback']==br['fallback'] and al==bl
