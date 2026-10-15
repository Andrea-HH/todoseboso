"""Convex group-centered objective via exact Elastic Net augmented least squares."""
import numpy as np
from types import SimpleNamespace
from sklearn.base import BaseEstimator,RegressorMixin
from sklearn.linear_model import ElasticNet
from .conditional_response import ConditionalFeatures

def centered(values,groups):
    values=np.asarray(values,float);groups=np.asarray(groups)
    _,inverse,counts=np.unique(groups,return_inverse=True,return_counts=True)
    out=np.zeros_like(values);eligible=int((counts>=2).sum());mask=counts[inverse]>=2
    # Group sums scale with parcels/features, without enumerating pairs or dense n*n matrices.
    sums=np.zeros((len(counts),)+values.shape[1:]);np.add.at(sums,inverse,values)
    means=sums/counts if values.ndim==1 else sums/counts[:,None]
    out[mask]=values[mask]-means[inverse[mask]]
    weights=np.where(mask,2/np.maximum(counts[inverse]-1,1)/max(eligible,1),0.)
    return out,weights,eligible

def intra_loss(errors,groups):
    z,w,n=centered(errors,groups)
    return float(np.sum(w*z*z)) if n else 0.

def objective_gradient(X,y,groups,beta,intercept,alpha_joint,rho,lam):
    """Gradient of smooth J; L1 is excluded from this gradient."""
    error=np.asarray(y)-intercept-np.asarray(X)@beta
    z,w,_=centered(error,groups)
    gradient=-2*np.asarray(X).T@error/len(error)-2*lam*np.asarray(X).T@(w*z)+alpha_joint*(1-rho)*beta
    return -2*error.mean(),gradient

class GroupObjectiveRegressor(RegressorMixin,BaseEstimator):
    """alpha uses archive sklearn units; user's J has alpha_joint=2*alpha."""
    def __init__(self,columns=(),alpha=.01,l1_ratio=.5,lam=0.,tol=1e-4,max_iter=200000):
        self.columns=columns;self.alpha=alpha;self.l1_ratio=l1_ratio;self.lam=lam;self.tol=tol;self.max_iter=max_iter
    def fit(self,X,y,groups=None):
        if self.alpha<0 or not 0<=self.l1_ratio<=1 or self.lam<0:raise ValueError('Invalid convex objective parameters')
        y=np.asarray(y,float);groups=np.asarray(X['climate_profile'] if groups is None else groups)
        if len(groups)!=len(y):raise ValueError('Group labels must match training rows')
        self.preprocess_=ConditionalFeatures(tuple(self.columns)).fit(X)
        z=self.preprocess_.transform(X)
        # Exact unpenalized intercept: local differences annihilate the constant vector.
        self.x_mean_=z.mean(axis=0);self.y_mean_=y.mean();z=z-self.x_mean_;yc=y-self.y_mean_
        local_z,weights,n_groups=centered(z,groups);local_y,_,_=centered(yc,groups)
        n=len(y);effective_lam=self.lam if n_groups else 0.
        if effective_lam:
            factor=np.sqrt(n*effective_lam*weights)
            augmented=np.vstack([z,local_z*factor[:,None]])
            target=np.concatenate([yc,local_y*factor])
        else:augmented=z;target=yc
        m=len(target)
        # sklearn: SSE/(2m)+alpha_solver*penalty. Multiplying by 2m/n gives J.
        if self.alpha==0 or self.l1_ratio==0:
            # Exact quadratic limiting case, not an additional predictive candidate.
            ridge=n*self.alpha*(1-self.l1_ratio)
            beta=np.linalg.solve(augmented.T@augmented+ridge*np.eye(z.shape[1]),augmented.T@target) if ridge>0 else np.linalg.lstsq(augmented,target,rcond=None)[0]
            self.solver_=SimpleNamespace(coef_=beta,n_iter_=1,dual_gap_=0.)
        else:
            self.solver_=ElasticNet(alpha=self.alpha*n/m,l1_ratio=self.l1_ratio,fit_intercept=False,tol=self.tol,max_iter=self.max_iter,random_state=2026).fit(augmented,target)
        self.coef_=self.solver_.coef_;self.intercept_=self.y_mean_-self.x_mean_@self.coef_
        if not np.isfinite(self.coef_).all():raise ValueError('Nonfinite solution')
        error=y-self.predict(X);gi,gb=objective_gradient(self.preprocess_.transform(X),y,groups,self.coef_,self.intercept_,2*self.alpha,self.l1_ratio,effective_lam)
        l1=2*self.alpha*self.l1_ratio;active=abs(self.coef_)>1e-10
        kkt=np.where(active,abs(gb+l1*np.sign(self.coef_)),np.maximum(abs(gb)-l1,0))
        penalty=2*self.alpha*(self.l1_ratio*abs(self.coef_).sum()+(1-self.l1_ratio)*np.sum(self.coef_**2)/2)
        self.diagnostics_=dict(n_train=n,n_augmented=m,n_eligible_train_profiles=n_groups,requested_lambda=self.lam,effective_lambda=effective_lam,alpha_archive=self.alpha,alpha_joint=2*self.alpha,alpha_solver=self.alpha*n/m,n_iter=int(self.solver_.n_iter_),dual_gap_solver=float(self.solver_.dual_gap_),dual_gap_joint=float(self.solver_.dual_gap_*2*m/n),native_gap_tolerance=float(self.tol*np.mean(target**2)),max_kkt_violation=float(max(abs(gi),kkt.max(initial=0))),global_loss=float(np.mean(error**2)),intra_loss=intra_loss(error,groups),penalty=float(penalty),joint_objective=float(np.mean(error**2)+effective_lam*intra_loss(error,groups)+penalty),intercept_gradient=float(gi),converged=bool(self.solver_.n_iter_<self.max_iter and self.solver_.dual_gap_<=self.tol*np.mean(target**2)*1.05+1e-10))
        if not self.diagnostics_['converged']:raise ValueError('Unverified optimizer convergence')
        return self
    def predict(self,X):return self.preprocess_.transform(X)@self.coef_+self.intercept_

def local_metrics(y,p,groups,folds):
    """Same-model validation pairs; profile-weighted MSE after fold-segment pooling."""
    y=np.asarray(y);p=np.asarray(p);groups=np.asarray(groups);folds=np.asarray(folds)
    losses={};eligible_ids=set();n_pairs=0;informative_folds=set()
    for fold in np.unique(folds):
        for group in np.unique(groups[folds==fold]):
            mask=(folds==fold)&(groups==group);n=int(mask.sum())
            if n<2:continue
            err=y[mask]-p[mask];mse=2*np.sum((err-err.mean())**2)/(n-1);pairs=n*(n-1)//2
            total,count=losses.get(group,(0.,0));losses[group]=(total+pairs*mse,count+pairs)
            n_pairs+=pairs;eligible_ids.update(np.flatnonzero(mask));informative_folds.add(int(fold))
    return dict(local_rmse=float(np.sqrt(np.mean([total/count for total,count in losses.values()]))) if losses else np.nan,n_profiles=len(losses),n_pairs=n_pairs,n_eligible_parcels=len(eligible_ids),eligible_fraction=len(eligible_ids)/len(y),informative_folds=len(informative_folds))

def select_candidate(records,baseline,delta=.01):
    """Anchor conventional lambda0; constrained local choice with explicit support fallback."""
    support=baseline['n_profiles']>=2 and baseline['informative_folds']>=2 and baseline['eligible_fraction']>=.1
    if not support:return baseline,'insufficient_internal_local_support'
    feasible=[r for r in records if r['rmse']<=baseline['rmse']+delta+1e-12 and r['mae']<=baseline['mae']+delta+1e-12 and np.isfinite(r['local_rmse'])]
    if not any(r['lam']>0 for r in feasible):return baseline,'no_positive_lambda_feasible'
    # Ties at 1e-10 t/ha are numerical equivalence, then smaller lambda/stronger penalty.
    best=min(feasible,key=lambda r:(round(r['local_rmse'],10),r['lam'],-r['alpha'],r['rho']))
    return best,'constrained_local_selection'
