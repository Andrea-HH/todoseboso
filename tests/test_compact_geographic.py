import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import Ridge
from src.compact_geographic import CompactRidge,NeighborResidual,support_factor,neighborhood
from src.ct3_residual_conditional.models import CORE

def test_batched_ridge_matches_sklearn_weighted_intercept():
    rng=np.random.default_rng(2026);frame=pd.DataFrame(rng.normal(size=(40,4)),columns=CORE);y=rng.normal(4,1,30)
    d=abs(np.arange(40)[:,None]-np.arange(40)[None,:]).astype(float)
    for power in [0.,1.]:
        p=dict(k=24,alpha=30.,power=power);m=CompactRidge(p).fit(frame.iloc[:30],y,np.arange(30));got=m.predict(frame.iloc[30:],np.arange(30,40),d)
        idx,near,w=neighborhood(d,np.arange(30),np.arange(30,40),24,power);z=m.preprocess.transform(frame.iloc[30:])
        expected=[Ridge(alpha=30).fit(m.x[i],y[i],sample_weight=ww).predict(zz[None,:])[0] for i,ww,zz in zip(idx,w,z)]
        np.testing.assert_allclose(got,expected,atol=1e-10,rtol=1e-10)

def test_neighbor_residual_constant_and_no_query_label_access():
    d=abs(np.arange(40)[:,None]-np.arange(40)[None,:]).astype(float)
    m=NeighborResidual(dict(k=24,power=1.)).fit(np.arange(30),np.full(30,2.))
    np.testing.assert_allclose(m.predict(np.arange(30,40),d),2.)
    with pytest.raises(ValueError):m.predict([0],d)

def test_support_shrinks_with_geographic_extrapolation():
    points=np.r_[np.arange(30),31.,1000.];d=abs(points[:,None]-points[None,:]);s=support_factor(d,np.arange(30),[30,31],24)
    assert 0<s[1]<s[0]<=1
