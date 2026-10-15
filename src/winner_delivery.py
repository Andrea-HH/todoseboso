"""Persistable final stages and paired fixed-OOF cluster diagnostics."""
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNet,Ridge
from xgboost import XGBRegressor

class FinalStage:
    def __init__(self,columns,kind,params):self.columns=list(columns);self.kind=kind;self.params=params
    def fit(self,x,y):
        self.imputer_=SimpleImputer(strategy='median').fit(x[self.columns]);z=self.imputer_.transform(x[self.columns])
        self.scaler_=None if self.kind=='XGB' else StandardScaler().fit(z)
        if self.scaler_ is not None:z=self.scaler_.transform(z)
        if self.kind=='ENET':self.model_=ElasticNet(**self.params,max_iter=30000,random_state=2026)
        elif self.kind=='RIDGE':self.model_=Ridge(**self.params)
        else:self.model_=XGBRegressor(**self.params,objective='reg:squarederror',random_state=2026,n_jobs=1,verbosity=0)
        self.model_.fit(z,y);return self
    def predict(self,x):
        z=self.imputer_.transform(x[self.columns])
        if self.scaler_ is not None:z=self.scaler_.transform(z)
        return self.model_.predict(z)

def cluster_weights(groups,draws=5000,seed=2026):
    unique,index=np.unique(np.asarray(groups).astype(str),return_inverse=True);g=len(unique)
    samples=np.random.default_rng(seed).integers(g,size=(draws,g))
    counts=np.zeros((draws,g),int)
    np.add.at(counts,(np.repeat(np.arange(draws),g),samples.ravel()),1)
    return counts[:,index],g

def sampled_metrics(y,pred,weights):
    y=np.asarray(y);pred=np.atleast_2d(pred);weights=np.asarray(weights);den=weights.sum(axis=1)
    errors=pred-y[None,:];sse=weights@(errors**2).T;absolute=weights@abs(errors).T
    ym=(weights@y)/den;tss=(weights@(y*y))-den*ym*ym
    r2=np.full_like(sse,np.nan);valid=tss>1e-12;r2[valid]=1-sse[valid]/tss[valid,None]
    return dict(rmse=np.sqrt(sse/den[:,None]).mean(axis=1),mae=(absolute/den[:,None]).mean(axis=1),bias=((weights@errors.T)/den[:,None]).mean(axis=1),r2=np.nanmean(r2,axis=1))

def paired_signflip(loss_difference,groups,seed=2026,draws=20000):
    groups=np.asarray(groups).astype(str);unique=np.unique(groups)
    sums=np.array([np.asarray(loss_difference)[groups==g].sum() for g in unique]);observed=float(abs(sums.sum()))
    if len(unique)<=16:
        bits=(np.arange(2**len(unique))[:,None]>>np.arange(len(unique)))&1
        values=abs((2*bits-1)@sums);p=float(np.mean(values>=observed-1e-12));exact=True
    else:
        signs=np.random.default_rng(seed).choice([-1,1],size=(draws,len(unique)))
        values=abs(signs@sums);p=float((1+np.sum(values>=observed-1e-12))/(draws+1));exact=False
    return dict(p_mse_signflip=p,n_clusters=len(unique),exact_sign_enumeration=exact,n_sign_assignments=len(values))

def holm(values):
    p=np.asarray(values,float);order=np.argsort(p);adjusted=np.empty_like(p)
    adjusted[order]=np.minimum(1,np.maximum.accumulate(p[order]*(len(p)-np.arange(len(p)))))
    return adjusted
