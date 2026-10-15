import numpy as np
import pytest
from src.geoc_bridge import local_prediction
from src.geoc_local04d_snapshot import haversine_distance_matrix,normalized_distance_matrix

def test_local_targets_only_come_from_observed_and_constant_is_preserved():
    x=np.random.default_rng(2026).normal(size=(30,20));d=abs(np.arange(30)[:,None]-np.arange(30)[None,:]).astype(float)
    p=local_prediction(x,d,np.arange(25),np.arange(25,30),np.full(25,3.5))
    np.testing.assert_allclose(p,3.5)
    with pytest.raises(AssertionError):local_prediction(x,d,np.arange(25),[0],np.ones(25))

def test_geographic_scale_is_x_only_and_distance_is_symmetric():
    d=haversine_distance_matrix([19.,19.01,19.03],[-98.,-98.,-98.])
    np.testing.assert_allclose(d,d.T);np.testing.assert_allclose(np.diag(d),0)
    normal,scale=normalized_distance_matrix(d,reference_positions=[0,1,2])
    assert scale>0;np.testing.assert_allclose(normal*scale,d)
