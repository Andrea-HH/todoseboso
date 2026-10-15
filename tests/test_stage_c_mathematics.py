import numpy as np
import pandas as pd
from src.family_4 import stage_c_models as c
from src.family_4.stage_c_hierarchy import ProfileGaussianRidge,whiten

def sample():
    rng=np.random.default_rng(8);X=pd.DataFrame(rng.normal(size=(40,3)),columns=['a','b','c']);X['climate_profile']=np.repeat(np.arange(10),4)
    y=4+X[['a','b','c']].to_numpy()@np.array([.4,-.2,.1])+np.repeat(rng.normal(0,.3,10),4)+rng.normal(0,.1,40)
    return X,y

def test_whitener_matches_block_covariance_inverse():
    X,y=sample();g=X.climate_profile.to_numpy();r=.3;V=np.eye(len(y))+r*(g[:,None]==g[None,:])
    A=X[['a','b','c']].to_numpy();W=whiten(np.eye(len(y)),g,r)
    np.testing.assert_allclose(W.T@W,np.linalg.inv(V),atol=1e-12)
    np.testing.assert_allclose(whiten(A,g,r),W@A,atol=1e-12)
    np.testing.assert_allclose(whiten(A,g,0),A,atol=0)

def test_zero_variance_exact_matched_ridge_and_gaussian_equations():
    from sklearn.linear_model import Ridge
    X,y=sample();m=ProfileGaussianRidge(('a','b','c'),.01,0).fit(X,y)
    z=m.preprocess_.transform(X);reference=Ridge(alpha=len(y)*.01).fit(z,y)
    np.testing.assert_allclose(m.predict(X),reference.predict(z),atol=1e-12)
    assert m.tau2_==0 and all(v['effect']==0 for v in m.groups_.values())
    assert m.diagnostics_['converged']

def test_general_gls_solution_matches_direct_regularized_normal_equations():
    X,y=sample();m=ProfileGaussianRidge(('a','b','c'),.01,1).fit(X,y);z=m.preprocess_.transform(X)
    A=np.column_stack([np.ones(len(X)),z]);g=X.climate_profile.to_numpy();V=np.eye(len(y))+(g[:,None]==g[None,:]);inverse=np.linalg.inv(V)
    ref=np.linalg.solve(A.T@inverse@A+np.diag([0]+[len(y)*.01]*3),A.T@inverse@y)
    np.testing.assert_allclose(m.theta_,ref,atol=1e-12)

def test_known_new_profiles_and_random_intercept_cancellation():
    X,y=sample();m=ProfileGaussianRidge(('a','b','c'),.01,1).fit(X,y)
    v=X.iloc[:2].copy();known=m.predict_components(v)
    assert known['profile_known'].all()
    np.testing.assert_allclose(np.diff(known['prediction']),np.diff(known['fixed_prediction']),atol=1e-12)
    v['climate_profile']=999;new=m.predict_components(v)
    assert not new['profile_known'].any() and (new['random_effect']==0).all()
    np.testing.assert_allclose(new['prediction'],new['fixed_prediction'],atol=0)
    h=np.column_stack([np.ones(len(v)),m.preprocess_.transform(v)])
    expected=m.sigma2_+m.tau2_+np.einsum('ij,jk,ik->i',h,m.cov_theta_,h)
    np.testing.assert_allclose(new['predictive_sd']**2,expected,atol=1e-12)
    v['y_true']=1e9;v['Estado']='changed';v['longitude']=1e9
    np.testing.assert_array_equal(m.predict(v),new['prediction'])

def test_singleton_partial_pooling_and_row_permutation():
    X,y=sample();X.climate_profile=np.arange(len(X));m=ProfileGaussianRidge(('a','b','c'),.1,.3).fit(X,y)
    assert all(v['n_train']==1 for v in m.groups_.values())
    order=np.random.default_rng(1).permutation(len(X));other=ProfileGaussianRidge(('a','b','c'),.1,.3).fit(X.iloc[order],y[order])
    np.testing.assert_allclose(m.predict(X),other.predict(X),atol=1e-12)

def test_compact_formula_zero_rain_and_dtr_semantics():
    z=pd.DataFrame([[0.]*7,[1.]*7,[1,2,3,4,5,6,7]],columns=c.RAIN)
    compact=c.compact_features(z)
    assert np.isfinite(compact.to_numpy()).all() and (compact.iloc[0]==0).all()
    np.testing.assert_allclose(compact.iloc[1,0],7)
    np.testing.assert_allclose(compact.iloc[1,1],3/(7+1e-6))
    np.testing.assert_allclose(compact.iloc[1,2],7/(7+1e-6)**2)
    d,_=c.load();assert c.TARGET not in d and len(d)==197
    assert d.groupby('climate_profile')[c.DTR].nunique().max()==1
