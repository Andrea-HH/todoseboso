import numpy as np
from sklearn.gaussian_process.kernels import RBF
from sklearn.base import clone
from threadpoolctl import threadpool_limits
from tests.test_family5_gpr_initial_math import sample
from src.family_5.gpr_s1.models import GroupedRBF,LinearMeanGPR,RbfGPR,preprocessing
from src.family_5.gpr_initial import execution as e

def test_rbf_covariance_and_gradient():
    X=sample()[0][e.SPECS['F5-01']].to_numpy();k=GroupedRBF(np.array([.7,1.6]),groups=(0,0,0,1))
    ref=RBF([.7,.7,.7,1.6]);cov,grad=k(X,eval_gradient=True);rc,rg=ref(X,eval_gradient=True)
    np.testing.assert_allclose(cov,rc,atol=1e-12)
    np.testing.assert_allclose(grad[:,:,0],rg[:,:,:3].sum(axis=2),atol=1e-12)
    np.testing.assert_allclose(grad[:,:,1],rg[:,:,3],atol=1e-12)
    assert clone(k).n_dims==2
    assert np.linalg.eigvalsh(cov).min()>-1e-12

def test_training_transforms_noise_duplicates_and_inverse_scale():
    X,y=sample()
    with threadpool_limits(limits=1):
        m=RbfGPR(tuple(e.SPECS['F5-01'])).fit(X,y)
        z=m.predict_components(X.iloc[[0,0]])
        assert z['prediction'][0]==z['prediction'][1]
        np.testing.assert_allclose(z['predictive_sd']**2-z['latent_sd']**2,z['noise_variance'])
        np.testing.assert_allclose(m.predict(X),m.gp_.predict(m.transform(X)))
        means=m.preprocess_.mean_.copy();m.predict(X*2);np.testing.assert_array_equal(means,m.preprocess_.mean_)

def test_deterministic_trend_and_residual_inverse_transform():
    X,y=sample()
    with threadpool_limits(limits=1):
        m=LinearMeanGPR(tuple(e.SPECS['F5-01']),.1).fit(X,y)
        z=m.predict_components(X);trend=m.linear_.predict(m.transform(X));res=m.residual_gp_.predict_components(X)
        np.testing.assert_allclose(z['prediction'],trend+res['prediction'])
        np.testing.assert_allclose(z['lower'],trend+res['lower'])
        np.testing.assert_array_equal(z['predictive_sd'],res['predictive_sd'])
        np.testing.assert_allclose(m.residual_gp_.gp_._y_train_mean,np.mean(y-trend),atol=1e-12)
        assert m.linear_.alpha==len(X)*.1
        assert 'DotProduct' not in str(m.residual_gp_.gp_.kernel_)

def test_balanced_monthly_block():
    X,y=sample();cols=[f'rain_{i}' for i in range(7)]
    for i,c in enumerate(cols):X[c]=np.arange(len(X))**(1+i/10)
    pre,names,groups,w,gn=preprocessing(cols+[e.c.NDVI],X)
    np.testing.assert_allclose(w[:7],1/np.sqrt(7));assert w[-1]==1
    assert groups==(0,0,0,0,0,0,0,1)
