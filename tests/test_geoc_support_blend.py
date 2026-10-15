import numpy as np
from src.geoc_support_blend import blend,choose

def test_convex_limits_and_zero_support_fallback():
    a=np.array([3.,4.,5.]);b=np.array([5.,3.,4.])
    np.testing.assert_array_equal(blend(a,b,0,np.ones(3)),a)
    np.testing.assert_array_equal(blend(a,b,1,np.zeros(3)),a)
    np.testing.assert_array_equal(blend(a,b,1,np.ones(3)),b)
    p=blend(a,b,.75,[0,.5,1]);assert np.all(p>=np.minimum(a,b)) and np.all(p<=np.maximum(a,b))

def test_ties_prefer_ct3_and_train_target_selects_weight():
    a=np.array([3.,4.,5.]);b=np.array([4.,5.,6.])
    assert choose(a,a,b,np.ones(3))[0]==0
    assert choose(b,a,b,np.ones(3))[0]==1
    assert choose(a,a,b,np.zeros(3))[0]==0
