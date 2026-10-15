import itertools
import numpy as np
import pandas as pd
import pytest
from src.family_4.stage_b_objective import GroupObjectiveRegressor,intra_loss,objective_gradient,local_metrics,select_candidate
from src.family_4 import conditional_response as f

@pytest.mark.parametrize('sizes',[ [2],[3],[33,29],[1,2,3],[1,1,1],[33,1,29,2] ])
@pytest.mark.parametrize('constant',[False,True])
def test_pair_identity(sizes,constant):
    rng=np.random.default_rng(2026);groups=np.repeat(np.arange(len(sizes)),sizes)
    errors=groups.astype(float) if constant else rng.normal(size=len(groups))
    losses=[]
    for group in np.unique(groups):
        z=errors[groups==group]
        if len(z)>1:losses.append(np.mean([(x-y)**2 for x,y in itertools.combinations(z,2)]))
    np.testing.assert_allclose(intra_loss(errors,groups),np.mean(losses) if losses else 0,atol=1e-12)

def sample():
    rng=np.random.default_rng(17);X=pd.DataFrame(rng.normal(size=(40,3)),columns=['a','b','c']);y=4+X.to_numpy()@np.array([.7,-.2,.3])+rng.normal(0,.1,40);g=np.repeat(np.arange(10),4)
    return X,y,g

def test_lambda_zero_matches_conventional_elastic_net():
    X,y,g=sample();spec={'kind':'direct','cols':['a','b','c']}
    # Pipeline reference uses identical ConditionalFeatures but no rainfall columns.
    from sklearn.pipeline import Pipeline
    from sklearn.linear_model import ElasticNet
    ref=Pipeline([('repr',f.ConditionalFeatures(('a','b','c'))),('model',ElasticNet(alpha=.01,l1_ratio=.5,max_iter=200000,tol=1e-4,random_state=2026))]).fit(X,y)
    fit=GroupObjectiveRegressor(('a','b','c'),.01,.5,0).fit(X,y,g)
    np.testing.assert_allclose(fit.predict(X),ref.predict(X),atol=1e-10,rtol=0)
    assert fit.diagnostics_['converged']

def test_smooth_gradient_finite_difference():
    X,y,g=sample();x=X.to_numpy();beta=np.array([.2,.3,-.1]);intercept=3.8;alpha=.04;rho=.5;lam=.3
    def smooth(b,i):
        err=y-i-x@b
        return np.mean(err**2)+lam*intra_loss(err,g)+alpha*(1-rho)*np.sum(b*b)/2
    gi,gb=objective_gradient(x,y,g,beta,intercept,alpha,rho,lam);h=1e-6
    numeric=[]
    for j in range(3):
        plus=beta.copy();minus=beta.copy();plus[j]+=h;minus[j]-=h;numeric.append((smooth(plus,intercept)-smooth(minus,intercept))/(2*h))
    np.testing.assert_allclose(gb,numeric,atol=1e-8)
    np.testing.assert_allclose(gi,(smooth(beta,intercept+h)-smooth(beta,intercept-h))/(2*h),atol=1e-8)

def test_augmented_solution_against_closed_form_ridge():
    X,y,g=sample();fit=GroupObjectiveRegressor(('a','b','c'),.02,0,.3,tol=1e-12).fit(X,y,g)
    z=fit.preprocess_.transform(X);zc=z-z.mean(axis=0);yc=y-y.mean()
    from src.family_4.stage_b_objective import centered
    local,w,_=centered(zc,g);ly,_,_=centered(yc,g)
    h=zc.T@zc/len(y)+.3*local.T@(w[:,None]*local)+.02*np.eye(3)
    rhs=zc.T@yc/len(y)+.3*local.T@(w*ly)
    np.testing.assert_allclose(fit.coef_,np.linalg.solve(h,rhs),atol=1e-9)
    assert fit.diagnostics_['max_kkt_violation']<1e-8

def test_intercept_shift_permutation_singleton_and_missing_groups():
    X,y,g=sample();fit=GroupObjectiveRegressor(('a','b','c'),.01,.5,1,tol=1e-10).fit(X,y,g)
    shifted=GroupObjectiveRegressor(('a','b','c'),.01,.5,1,tol=1e-10).fit(X,y+10,g)
    np.testing.assert_allclose(shifted.coef_,fit.coef_,atol=1e-9)
    np.testing.assert_allclose(shifted.intercept_-fit.intercept_,10,atol=1e-9)
    order=np.random.default_rng(1).permutation(len(y))
    perm=GroupObjectiveRegressor(('a','b','c'),.01,.5,1,tol=1e-10).fit(X.iloc[order],y[order],g[order])
    np.testing.assert_allclose(perm.predict(X),fit.predict(X),atol=1e-8)
    solo=GroupObjectiveRegressor(('a','b','c'),.01,.5,1).fit(X,y,np.arange(len(y)))
    zero=GroupObjectiveRegressor(('a','b','c'),.01,.5,0).fit(X,y,g)
    np.testing.assert_allclose(solo.predict(X),zero.predict(X),atol=1e-10)
    assert solo.diagnostics_['effective_lambda']==0

def test_same_model_local_metric_and_explicit_fallback():
    y=np.array([0.,1.,3.,4.,6.,7.]);p=np.zeros(6);groups=np.array([0,0,0,1,1,1]);folds=np.array([0,0,1,1,1,0])
    metric=local_metrics(y,p,groups,folds)
    np.testing.assert_allclose(metric['local_rmse'],np.sqrt((1+4)/2))
    assert metric['n_pairs']==2 and metric['n_eligible_parcels']==4
    base=dict(lam=0,alpha=.1,rho=.5,rmse=.5,mae=.4,local_rmse=.6,**{k:v for k,v in metric.items() if k!='local_rmse'})
    new={**base,'lam':1,'local_rmse':.55,'rmse':.509,'mae':.409}
    assert select_candidate([base,new],base)[0]['lam']==1
    assert select_candidate([base,{**new,'mae':.411}],base)[0]['lam']==0
    poor={**base,'informative_folds':1}
    assert select_candidate([poor,new],poor)[1]=='insufficient_internal_local_support'
