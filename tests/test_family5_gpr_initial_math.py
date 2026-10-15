import numpy as np
import pandas as pd
import pytest
from scipy.spatial.distance import cdist
from sklearn.base import clone
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel,WhiteKernel,Matern
from threadpoolctl import threadpool_limits
from src.family_4 import stage_c_models as c
from src.family_5.gpr_initial.kernel import GroupedMatern32
from src.family_5.gpr_initial.model import CompactGPR,OPT

@pytest.fixture(scope='module',autouse=True)
def native_threads():
    with threadpool_limits(limits=1):yield

def sample():
    rng=np.random.default_rng(91);X=pd.DataFrame(rng.normal(size=(24,3)),columns=c.COMPACT);X[c.NDVI]=rng.uniform(.1,.3,24);X['climate_profile']=np.repeat(np.arange(6),4)
    y=3+.4*X[c.COMPACT[0]].to_numpy()+.15*np.sin(X[c.COMPACT[1]])+1.2*X[c.NDVI]+rng.normal(0,.1,24)
    return X,np.asarray(y)

@pytest.fixture(scope='module')
def fitted():
    X,y=sample();return X,y,CompactGPR(tuple(c.COMPACT+[c.NDVI])).fit(X,y)

def test_grouped_covariance_matches_matern_expanded_axes():
    X=sample()[0][c.COMPACT+[c.NDVI]].to_numpy();grouped=GroupedMatern32(np.array([.7,1.6]),groups=(0,0,0,1))
    ref=Matern(np.array([.7,.7,.7,1.6]),nu=1.5)
    np.testing.assert_allclose(grouped(X),ref(X),atol=1e-12)
    assert grouped.n_dims==2 and clone(grouped).groups==(0,0,0,1)
    np.testing.assert_array_equal(grouped.diag(X),np.ones(len(X)))

def test_grouped_gradient_sums_tied_axis_derivatives():
    X=sample()[0][c.COMPACT+[c.NDVI]].to_numpy();kernel=GroupedMatern32(np.array([.7,1.6]),groups=(0,0,0,1))
    _,grad=kernel(X,eval_gradient=True);_,ref=Matern(np.array([.7,.7,.7,1.6]),nu=1.5)(X,eval_gradient=True)
    np.testing.assert_allclose(grad[:,:,0],ref[:,:,:3].sum(axis=2),atol=1e-10)
    np.testing.assert_allclose(grad[:,:,1],ref[:,:,3],atol=1e-10)

def test_complete_kernel_gradient_finite_difference():
    X=sample()[0][c.COMPACT+[c.NDVI]].to_numpy();kernel=ConstantKernel(1.4)*GroupedMatern32(np.array([.7,1.6]),groups=(0,0,0,1))+WhiteKernel(.2)
    _,gradient=kernel(X,eval_gradient=True);theta=kernel.theta
    for j in range(len(theta)):
        step=np.zeros_like(theta);step[j]=1e-6
        numerical=(kernel.clone_with_theta(theta+step)(X)-kernel.clone_with_theta(theta-step)(X))/2e-6
        np.testing.assert_allclose(numerical,gradient[:,:,j],atol=2e-9,rtol=1e-5)

def test_white_noise_repeated_predictors_and_positive_covariance():
    X=np.zeros((5,3));signal=ConstantKernel(1.4)*GroupedMatern32(np.array([.7]),groups=(0,0,0));kernel=signal+WhiteKernel(.2)
    np.testing.assert_allclose(kernel(X)-kernel(X,X),.2*np.eye(5),atol=1e-12)
    assert np.linalg.eigvalsh(kernel(X)).min()>.199999
    gp=GaussianProcessRegressor(kernel=kernel,optimizer=None,alpha=1e-8,normalize_y=True).fit(X,np.arange(5,dtype=float))
    mean,sd=gp.predict(X[:2],return_std=True)
    np.testing.assert_allclose(mean[0],mean[1]);np.testing.assert_allclose(sd[0],sd[1])

def test_train_only_scaling_group_weighting_and_y_normalization(fitted):
    X,y,m=fitted
    np.testing.assert_allclose(m.preprocess_.median_,np.median(X[list(m.columns)],axis=0))
    np.testing.assert_allclose(m.preprocess_.mean_,X[list(m.columns)].mean())
    np.testing.assert_allclose(m.block_weights_,[1/np.sqrt(3)]*3+[1])
    assert m.groups_==(0,0,0,1) and m.gp_.kernel_.n_dims==4
    assert np.isclose(m.target_mean_,y.mean()) and np.isclose(m.target_scale_,y.std())
    altered=X.copy();altered.loc[:,m.columns[0]]+=1e4;m.predict(altered)
    np.testing.assert_allclose(m.preprocess_.mean_,X[list(m.columns)].mean())

def test_inverse_target_scale_and_observational_intervals(fitted):
    X,y,m=fitted;v=X.iloc[:4];z=m.transform(v);K=m.gp_.kernel_(z,m.training_z_)
    normalized=K@m.gp_.alpha_;np.testing.assert_allclose(m.predict(v),normalized*m.target_scale_+m.target_mean_,atol=1e-12)
    out=m.predict_components(v)
    np.testing.assert_allclose(out['predictive_sd']**2,out['latent_sd']**2+out['noise_variance'],atol=1e-12)
    assert np.all(out['upper']>=out['prediction']) and np.all(out['lower']<=out['prediction'])

def test_recorded_optimizer_respects_frozen_bounds_and_three_starts(fitted):
    m=fitted[-1];assert len(m.optimizer_.records)==3 and OPT['n_restarts_optimizer']==2
    theta=m.gp_.kernel_.theta;bounds=m.gp_.kernel_.bounds
    assert np.all(theta>=bounds[:,0]-1e-10) and np.all(theta<=bounds[:,1]+1e-10)
    assert all(np.isfinite(r['negative_lml']) for r in m.optimizer_.records)

def test_metadata_never_changes_predictions(fitted):
    X,y,m=fitted;altered=X.copy();altered['climate_profile']=999;altered['Municipio']='other';altered[c.TARGET]=999
    np.testing.assert_allclose(m.predict(X),m.predict(altered),atol=0)

def test_kernel_rejects_misdeclared_groups():
    with pytest.raises(ValueError):GroupedMatern32([1,1],groups=(0,0,0))(np.zeros((4,3)))
    with pytest.raises(ValueError):GroupedMatern32([1],groups=(0,0,0))(np.zeros((4,4)))
