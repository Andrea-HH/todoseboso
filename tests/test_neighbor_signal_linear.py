import numpy as np
from src.neighbor_signal_linear import ContinuousAdjustment


def test_continuous_contrasts_are_zero_anchored_and_bounded():
    rng=np.random.default_rng(53);z=rng.normal(size=(80,6));base=np.full(80,4.);y=base+.3*z[:,0]-.2*z[:,1];m=ContinuousAdjustment(alpha=.001,l1_ratio=.5,amplitude=1.).fit(z,y,base,base)
    np.testing.assert_array_equal(m.predict(np.zeros((4,6)),np.full(4,4.),np.zeros(4)),np.full(4,4.))
    p=m.predict(z*1000,base,base);assert max(abs(p-base))<=.5+1e-12 and m.model.fit_intercept is False
    assert m.model.coef_[0]>0 and m.model.coef_[1]<0


def test_null_and_constant_contrasts_cannot_create_a_global_offset():
    z=np.ones((50,6));base=np.full(50,4.);y=np.full(50,2.)
    for amp in [0.,.5,1.]:
        m=ContinuousAdjustment(amplitude=amp).fit(z,y,base,base);np.testing.assert_array_equal(m.predict(z,base,base),base)
