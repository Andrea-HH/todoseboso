"""Approved exact GPR only; training-only existing preprocessing and bounded LML."""
import time,warnings
import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel,WhiteKernel
from sklearn.exceptions import ConvergenceWarning
from src.family_4.conditional_response import ConditionalFeatures,NDVI
from .kernel import GroupedMatern32

OPT=dict(n_restarts_optimizer=2,seed=2026,amplitude_bounds=(.01,100.),length_bounds=(.2,20.),noise_variance_bounds=(.001,2.),initial_amplitude=1.,initial_length=1.,initial_noise_variance=.1,jitter=1e-8)

class RecordedOptimizer:
    def __init__(self):self.records=[]
    def __call__(self,objective,initial_theta,bounds):
        start=time.perf_counter();result=minimize(objective,initial_theta,method='L-BFGS-B',jac=True,bounds=bounds)
        self.records.append(dict(initial_theta=np.asarray(initial_theta).tolist(),final_theta=result.x.tolist(),negative_lml=float(result.fun),success=bool(result.success),status=int(result.status),message=str(result.message),iterations=int(result.nit),function_evaluations=int(result.nfev),gradient_max_abs=float(abs(result.jac).max()),seconds=time.perf_counter()-start))
        if not result.success:warnings.warn(f'L-BFGS-B status{result.status}: {result.message}',ConvergenceWarning)
        return result.x,result.fun

class CompactGPR:
    def __init__(self,columns):self.columns=columns
    def fit(self,X,y):
        start=time.perf_counter();y=np.asarray(y,dtype=float)
        if len(X)!=len(y) or not np.isfinite(y).all():raise ValueError('Finite supervised training labels required')
        self.preprocess_=ConditionalFeatures(tuple(self.columns)).fit(X)
        names=self.preprocess_.get_feature_names_out().tolist()
        if not names:raise ValueError('No varying predictors; suspend this fit, do not invent a representation')
        # Drop constant axes using the established train-only transform; retain only identified groups.
        declared=[1 if name==NDVI else 0 for name in names];active=sorted(set(declared));mapping={old:j for j,old in enumerate(active)}
        self.groups_=tuple(mapping[j] for j in declared);self.group_names_=['NDVI' if j else 'rain' for j in active]
        self.block_weights_=np.array([1/np.sqrt(declared.count(j)) for j in declared])
        z=self.preprocess_.transform(X)*self.block_weights_;self.training_z_=z.copy();self.training_names_=names
        self.training_profiles_=X.climate_profile.to_numpy().copy() if 'climate_profile' in X else None
        self.optimizer_=RecordedOptimizer()
        kernel=ConstantKernel(OPT['initial_amplitude'],OPT['amplitude_bounds'])*GroupedMatern32(np.repeat(OPT['initial_length'],len(active)),OPT['length_bounds'],self.groups_)+WhiteKernel(OPT['initial_noise_variance'],OPT['noise_variance_bounds'])
        self.gp_=GaussianProcessRegressor(kernel=kernel,alpha=OPT['jitter'],optimizer=self.optimizer_,n_restarts_optimizer=OPT['n_restarts_optimizer'],normalize_y=True,random_state=OPT['seed'])
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter('always');self.gp_.fit(z,y)
        self.warnings_=[dict(category=w.category.__name__,message=str(w.message)) for w in captured]
        if not np.isfinite(self.gp_.log_marginal_likelihood_value_):raise ValueError('Nonfinite optimized LML')
        self.target_mean_=float(np.asarray(self.gp_._y_train_mean));self.target_scale_=float(np.asarray(self.gp_._y_train_std))
        self.noise_variance_=float(self.gp_.kernel_.k2.noise_level)*self.target_scale_**2
        theta=self.gp_.kernel_.theta;bounds=self.gp_.kernel_.bounds
        self.bound_hits_=[];dimension=0
        for hp in self.gp_.kernel_.hyperparameters:
            if hp.fixed:continue
            for j in range(hp.n_elements):
                side='lower' if abs(theta[dimension]-bounds[dimension,0])<=1e-5 else 'upper' if abs(theta[dimension]-bounds[dimension,1])<=1e-5 else ''
                if side:self.bound_hits_.append(dict(parameter=hp.name,index=j,side=side,value=float(np.exp(theta[dimension]))))
                dimension+=1
        matrix=self.gp_.kernel_(z)+OPT['jitter']*np.eye(len(z));self.covariance_condition_=float(np.linalg.cond(matrix))
        self.min_covariance_eigenvalue_=float(np.linalg.eigvalsh(matrix).min())
        if self.min_covariance_eigenvalue_<=0 or not np.isfinite(self.covariance_condition_):raise ValueError('Invalid GP training covariance')
        best=min(self.optimizer_.records,key=lambda r:r['negative_lml']);self.selected_optimizer_converged_=best['success']
        self.fit_seconds_=time.perf_counter()-start
        return self
    def transform(self,X):return self.preprocess_.transform(X)*self.block_weights_
    def predict_components(self,X):
        z=self.transform(X);mean,sd=self.gp_.predict(z,return_std=True)
        predictive_variance=sd**2;latent=predictive_variance-self.noise_variance_
        if np.min(latent)<-1e-8*max(1,self.target_scale_**2):raise ValueError('Latent/observational variance decomposition inconsistent')
        latent=np.maximum(latent,0);q=norm.ppf(.95)
        return dict(prediction=mean,predictive_sd=sd,latent_sd=np.sqrt(latent),noise_variance=np.repeat(self.noise_variance_,len(z)),lower=mean-q*sd,upper=mean+q*sd)
    def predict(self,X):return self.gp_.predict(self.transform(X))
    def parameters(self):
        return dict(amplitude=float(self.gp_.kernel_.k1.k1.constant_value),length_scales=dict(zip(self.group_names_,np.atleast_1d(self.gp_.kernel_.k1.k2.length_scale).tolist())),noise_variance_standardized=float(self.gp_.kernel_.k2.noise_level),noise_variance_t_ha_squared=self.noise_variance_,jitter_standardized=OPT['jitter'],target_mean=self.target_mean_,target_scale=self.target_scale_,n_kernel_parameters=len(self.gp_.kernel_.theta),lml=float(self.gp_.log_marginal_likelihood_value_),covariance_condition=self.covariance_condition_,min_covariance_eigenvalue=self.min_covariance_eigenvalue_,selected_optimizer_converged=self.selected_optimizer_converged_,n_optimizer_starts=len(self.optimizer_.records),bound_hits=self.bound_hits_,warnings=self.warnings_,seconds=self.fit_seconds_,kernel_repr=str(self.gp_.kernel_),active_features=self.training_names_)
