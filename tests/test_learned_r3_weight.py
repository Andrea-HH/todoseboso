import numpy as np
from src.learned_r3_weight import LearnedWeight

def test_weights_are_bounded_and_null_preserves_base():
    rng=np.random.default_rng(2026);z=rng.normal(size=(60,6));z[:,-1]=1;z[0,0]=np.nan;d=np.linspace(-.25,.25,60);r=.7*d+rng.normal(0,.1,60)
    for kind in ['MASK','CONSTANT','ASYM','LEARNED','LEARNED_ASYM']:
        m=LearnedWeight(kind).fit(z,r,d);w=m.predict(z,d);assert np.isfinite(w).all() and min(w)>=0 and max(w)<=1;assert max(abs(w*d))<=.25
        np.testing.assert_array_equal(LearnedWeight(kind,strength=0).fit(z,r,d).predict(z,d),np.zeros(60))

def test_asymmetry_and_small_sign_fallback():
    d=np.r_[np.full(30,.2),np.full(30,-.2)];r=np.r_[np.full(30,.2),np.zeros(30)];z=np.zeros((60,6));m=LearnedWeight('ASYM').fit(z,r,d);w=m.predict(z,d);assert w[:30].mean()>w[30:].mean()
    m=LearnedWeight('LEARNED_ASYM').fit(z[:10],r[:10],d[:10]);assert 'positive' in m.fallbacks

def test_mask_only_requires_history_and_has_no_response_threshold():
    z=np.zeros((5,6));z[::2,-1]=1;d=np.ones(5)*.2;m=LearnedWeight('MASK',strength=.5).fit(z,d,d);np.testing.assert_array_equal(m.predict(z,d),[.5,0,.5,0,.5])
