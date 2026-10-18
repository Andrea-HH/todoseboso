import numpy as np
from src.local_ridge_sufficient_statistics import predict_local_ridge
from src.geoc_local04d_snapshot import predict_weighted_local_ridge

def test_weighted_ridge_matches_original_with_ties_and_constant_columns():
    rng=np.random.default_rng(71)
    for n in [5,40,100]:
        x=rng.normal(size=(n+5,7));x[:,2]=1.;d=rng.uniform(.01,10,size=(n+5,n+5));d[-1,:5]=0.;observed=np.arange(n);query=np.arange(n,n+5);target=rng.normal(4,.6,n);y=np.full(n+5,np.nan);y[observed]=target
        expected=predict_weighted_local_ridge(x,d,y,observed,query,k=24,alpha=30.,distance_power=1.);actual=predict_local_ridge(x,d,observed,query,target);np.testing.assert_allclose(actual,expected,atol=1e-12,rtol=0)
