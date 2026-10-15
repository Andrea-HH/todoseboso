"""Restricted RBF and deterministic Ridge-mean sensitivities; original F5 is read-only."""
import time,warnings
import numpy as np
from scipy.spatial.distance import cdist
from sklearn.linear_model import Ridge
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel,WhiteKernel
from src.family_4.conditional_response import ConditionalFeatures,NDVI
from src.family_5.gpr_initial.kernel import GroupedMatern32
from src.family_5.gpr_initial.model import CompactGPR,RecordedOptimizer,OPT

ALPHAS=(.001,.01,.1,1.)

class GroupedRBF(GroupedMatern32):
    def __call__(self,X,Y=None,eval_gradient=False):
        X=np.atleast_2d(np.asarray(X,float))
        if eval_gradient and Y is not None:raise ValueError('Gradient only for Y=None')
        Y=X if Y is None else np.atleast_2d(np.asarray(Y,float))
        groups=np.asarray(self.groups,int);ell=np.atleast_1d(np.asarray(self.length_scale,float))
        if X.shape[1]!=len(groups) or Y.shape[1]!=len(groups):raise ValueError('Kernel dimension/group mismatch')
        if not len(groups) or set(groups)!=set(range(len(ell))) or (ell<=0).any():raise ValueError('Invalid declared groups')
        distances=[cdist(X[:,groups==j]/ell[j],Y[:,groups==j]/ell[j],metric='sqeuclidean') for j in range(len(ell))]
        covariance=np.exp(-.5*np.sum(distances,axis=0))
        if not eval_gradient:return covariance
        if self.hyperparameter_length_scale.fixed:return covariance,np.empty((*covariance.shape,0))
        return covariance,np.stack([covariance*q for q in distances],axis=-1)
    def __repr__(self):return f'GroupedRBF(length_scale={np.atleast_1d(self.length_scale)}, groups={self.groups})'

def preprocessing(columns,X):
    pre=ConditionalFeatures(tuple(columns)).fit(X);names=pre.get_feature_names_out().tolist()
    if not names:raise ValueError('No varying predictors')
    declared=[1 if name==NDVI else 0 for name in names];active=sorted(set(declared));mapping={old:j for j,old in enumerate(active)}
    groups=tuple(mapping[j] for j in declared);weights=np.array([1/np.sqrt(declared.count(j)) for j in declared])
    return pre,names,groups,weights,['NDVI' if j else 'rain' for j in active]

class RbfGPR(CompactGPR):
    """Reuse original prediction/variance/registry interfaces, change covariance only."""
    def fit(self,X,y):
        start=time.perf_counter();y=np.asarray(y,float)
        if len(X)!=len(y) or not np.isfinite(y).all():raise ValueError('Finite labels required')
        self.preprocess_,self.training_names_,self.groups_,self.block_weights_,self.group_names_=preprocessing(self.columns,X)
        z=self.preprocess_.transform(X)*self.block_weights_;self.training_z_=z.copy()
        self.training_profiles_=X.climate_profile.to_numpy().copy() if 'climate_profile' in X else None
        self.optimizer_=RecordedOptimizer()
        kernel=ConstantKernel(OPT['initial_amplitude'],OPT['amplitude_bounds'])*GroupedRBF(np.repeat(OPT['initial_length'],len(self.group_names_)),OPT['length_bounds'],self.groups_)+WhiteKernel(OPT['initial_noise_variance'],OPT['noise_variance_bounds'])
        self.gp_=GaussianProcessRegressor(kernel=kernel,alpha=OPT['jitter'],optimizer=self.optimizer_,n_restarts_optimizer=OPT['n_restarts_optimizer'],normalize_y=True,random_state=OPT['seed'])
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter('always');self.gp_.fit(z,y)
        self.warnings_=[dict(category=w.category.__name__,message=str(w.message)) for w in captured]
        if not np.isfinite(self.gp_.log_marginal_likelihood_value_):raise ValueError('Nonfinite LML')
        self.target_mean_=float(np.asarray(self.gp_._y_train_mean));self.target_scale_=float(np.asarray(self.gp_._y_train_std));self.noise_variance_=float(self.gp_.kernel_.k2.noise_level)*self.target_scale_**2
        theta=self.gp_.kernel_.theta;bounds=self.gp_.kernel_.bounds;self.bound_hits_=[];dimension=0
        for hp in self.gp_.kernel_.hyperparameters:
            if hp.fixed:continue
            for j in range(hp.n_elements):
                side='lower' if abs(theta[dimension]-bounds[dimension,0])<=1e-5 else 'upper' if abs(theta[dimension]-bounds[dimension,1])<=1e-5 else ''
                if side:self.bound_hits_.append(dict(parameter=hp.name,index=j,side=side,value=float(np.exp(theta[dimension]))))
                dimension+=1
        matrix=self.gp_.kernel_(z)+OPT['jitter']*np.eye(len(z));self.covariance_condition_=float(np.linalg.cond(matrix));self.min_covariance_eigenvalue_=float(np.linalg.eigvalsh(matrix).min())
        if self.min_covariance_eigenvalue_<=0:raise ValueError('Non-positive GP covariance')
        self.selected_optimizer_converged_=min(self.optimizer_.records,key=lambda r:r['negative_lml'])['success'];self.fit_seconds_=time.perf_counter()-start
        return self

class LinearMeanGPR:
    """Plug-in deterministic Ridge trend, GP on within-training fitted residuals.

    Selection evaluates the whole pipeline in frozen inner folds. This is an
    estimated GP mean, not a Champion residual learner, DotProduct covariance,
    universal-kriging likelihood fit or cross-fitted residual-target model.
    """
    def __init__(self,columns,alpha):self.columns=columns;self.alpha=alpha
    def fit(self,X,y):
        start=time.perf_counter();y=np.asarray(y,float)
        pre,names,groups,weights,groupnames=preprocessing(self.columns,X);z=pre.transform(X)*weights
        self.linear_=Ridge(alpha=len(X)*self.alpha,fit_intercept=True,solver='cholesky').fit(z,y)
        residual=y-self.linear_.predict(z)
        self.residual_gp_=CompactGPR(tuple(self.columns)).fit(X,residual)
        np.testing.assert_allclose(z,self.residual_gp_.training_z_,atol=1e-12)
        self.preprocess_=self.residual_gp_.preprocess_;self.training_z_=self.residual_gp_.training_z_;self.block_weights_=self.residual_gp_.block_weights_
        self.optimizer_=self.residual_gp_.optimizer_;self.training_names_=names
        self.original_target_mean_=float(y.mean());self.original_target_scale_=float(y.std());self.fit_seconds_=time.perf_counter()-start
        return self
    def transform(self,X):return self.residual_gp_.transform(X)
    def predict_components(self,X):
        out=self.residual_gp_.predict_components(X);linear=self.linear_.predict(self.transform(X));correction=out['prediction'].copy()
        for key in ['prediction','lower','upper']:out[key]=out[key]+linear
        out['linear_prediction']=linear;out['gp_correction']=correction
        return out
    def predict(self,X):return self.linear_.predict(self.transform(X))+self.residual_gp_.predict(X)
    def parameters(self):
        result=self.residual_gp_.parameters();result.update(linear_alpha=self.alpha,linear_alpha_solver=len(self.training_z_)*self.alpha,linear_intercept=float(self.linear_.intercept_),linear_coefficients=dict(zip(self.training_names_,self.linear_.coef_.tolist())),original_target_mean=self.original_target_mean_,original_target_scale=self.original_target_scale_,seconds=self.fit_seconds_,interval_condition='trend estimated and then held fixed; no linear-parameter uncertainty included')
        return result
