"""Gaussian random-intercept GLS/Ridge with train-only BLUP and exact block whitening."""
import numpy as np
from scipy.stats import norm
from sklearn.base import BaseEstimator,RegressorMixin
from sklearn.linear_model import Ridge
from .conditional_response import ConditionalFeatures

def whiten(values,groups,ratio):
    values=np.asarray(values,float);groups=np.asarray(groups)
    _,inverse,counts=np.unique(groups,return_inverse=True,return_counts=True)
    sums=np.zeros((len(counts),)+values.shape[1:]);np.add.at(sums,inverse,values)
    means=sums/counts if values.ndim==1 else sums/counts[:,None]
    adjustment=1-1/np.sqrt(1+counts[inverse]*ratio)
    return values-means[inverse]*(adjustment if values.ndim==1 else adjustment[:,None])

class ProfileGaussianRidge(RegressorMixin,BaseEstimator):
    """Variance ratio CV-regularized; Gaussian plug-in intervals integrate new profile variance."""
    def __init__(self,columns=(),alpha=.01,ratio=0.):
        self.columns=columns;self.alpha=alpha;self.ratio=ratio
    def fit(self,X,y):
        if self.alpha<=0 or self.ratio<0:raise ValueError('Positive fixed-effect regularization and nonnegative variance ratio required')
        y=np.asarray(y,float);groups=X.climate_profile.to_numpy()
        self.preprocess_=ConditionalFeatures(tuple(self.columns)).fit(X)
        z=self.preprocess_.transform(X);n=len(y)
        design=np.column_stack([np.ones(n),z]);wd=whiten(design,groups,self.ratio);wy=whiten(y,groups,self.ratio)
        v=wd[:,0];zx=wd[:,1:];denom=v@v
        cx=zx-v[:,None]*(v@zx/denom);cy=wy-v*(v@wy/denom)
        self.ridge_=Ridge(alpha=n*self.alpha,fit_intercept=False,solver='cholesky').fit(cx,cy)
        self.coef_=self.ridge_.coef_;self.intercept_=float((v@wy-v@zx@self.coef_)/denom)
        self.theta_=np.r_[self.intercept_,self.coef_]
        residual=y-design@self.theta_;wr=whiten(residual,groups,self.ratio)
        self.sigma2_=float(max(wr@wr/n,1e-12));self.tau2_=self.ratio*self.sigma2_
        precision=wd.T@wd+np.diag(np.r_[0.,np.repeat(n*self.alpha,z.shape[1])])
        self.cov_theta_=self.sigma2_*np.linalg.inv(precision)
        self.groups_={}
        for group in np.unique(groups):
            mask=groups==group;ng=int(mask.sum());k=self.ratio/(1+ng*self.ratio)
            self.groups_[group]=dict(n_train=ng,effect=float(k*residual[mask].sum()),posterior_variance=self.sigma2_*self.ratio/(1+ng*self.ratio),sum_design=design[mask].sum(axis=0),conditional_multiplier=k)
        self.training_groups_=groups.copy()
        _,counts=np.unique(groups,return_counts=True)
        marginal_ll=-.5*(n*np.log(2*np.pi*self.sigma2_)+np.log1p(counts*self.ratio).sum()+wr@wr/self.sigma2_)
        gradient=precision@self.theta_-wd.T@wy
        self.diagnostics_=dict(alpha=self.alpha,variance_ratio=self.ratio,sigma2=self.sigma2_,tau2=self.tau2_,icc=self.ratio/(1+self.ratio),n_train=n,n_profiles_train=len(counts),n_repeated_profiles_train=int((counts>=2).sum()),precision_condition=np.linalg.cond(precision),normal_equation_residual=float(abs(gradient).max()),marginal_loglikelihood=float(marginal_ll),variance_floor_used=bool(wr@wr/n<1e-12),tau_boundary=bool(self.ratio==0),fixed_effect_regularization='Gaussian GLS/Ridge, alpha_solver=n*alpha, intercept free',variance_estimation='ratio selected internally; sigma2=whitened residual SSE/n, conditional ML plug-in',converged=bool(np.isfinite(self.theta_).all() and abs(gradient).max()<1e-7))
        if not self.diagnostics_['converged']:raise ValueError('Unstable Gaussian normal equations')
        return self
    def predict_components(self,X,coverage=.9):
        z=self.preprocess_.transform(X);design=np.column_stack([np.ones(len(X)),z]);fixed=design@self.theta_
        effects=np.zeros(len(X));variance=np.zeros(len(X));known=np.zeros(len(X),bool);sizes=np.zeros(len(X),int)
        for i,group in enumerate(X.climate_profile):
            info=self.groups_.get(group);h=design[i].copy()
            if info is not None:
                known[i]=True;sizes[i]=info['n_train'];effects[i]=info['effect']
                h-=info['conditional_multiplier']*info['sum_design']
                variance[i]=self.sigma2_+info['posterior_variance']+h@self.cov_theta_@h
            else:variance[i]=self.sigma2_+self.tau2_+h@self.cov_theta_@h
        sd=np.sqrt(np.maximum(variance,0));mean=fixed+effects;quantile=norm.ppf((1+coverage)/2)
        return dict(prediction=mean,fixed_prediction=fixed,random_effect=effects,profile_known=known,n_training_profile=sizes,predictive_sd=sd,lower=mean-quantile*sd,upper=mean+quantile*sd)
    def predict(self,X):return self.predict_components(X)['prediction']
