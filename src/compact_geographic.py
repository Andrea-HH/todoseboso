"""Compact4 local Ridge and honest neighbor-residual corrections."""
import numpy as np
from sklearn.linear_model import Ridge
from src.family_4.conditional_response import ConditionalFeatures
from src.ct3_residual_conditional.models import CORE

KS=[24,36,12]
ALPHAS=[100.,30.,10.,1.]
POWERS=[0.,1.]
WEIGHTS=[0.,.25,.5]
GRID=[dict(k=k,alpha=alpha,power=power) for k in KS for alpha in ALPHAS for power in POWERS]

def neighborhood(distance,observed,query,k,power):
    observed=np.asarray(observed,int);query=np.asarray(query,int)
    if set(observed)&set(query):raise ValueError('Query labels must be excluded from reference neighbors')
    d=distance[np.ix_(query,observed)];count=min(int(k),len(observed));indices=np.argsort(d,axis=1)[:,:count]
    near=np.take_along_axis(d,indices,axis=1)
    weights=np.ones_like(near) if power==0 else 1/(near+1e-6)**power
    return indices,near,weights

def support_factor(distance,observed,query,k):
    observed=np.asarray(observed,int);query=np.asarray(query,int)
    if len(observed)<2:return np.zeros(len(query))
    train=distance[np.ix_(observed,observed)].copy();np.fill_diagonal(train,np.inf)
    count=min(k,len(observed)-1);typical=float(np.median(np.sort(train,axis=1)[:,count-1]))
    test=np.sort(distance[np.ix_(query,observed)],axis=1)[:,min(k,len(observed))-1]
    return np.minimum(1.,typical/np.maximum(test,1e-6))

class CompactRidge:
    def __init__(self,params,local=True):self.params=params;self.local=local
    def fit(self,frame,target,positions):
        self.positions=np.asarray(positions,int);self.target=np.asarray(target,float)
        self.preprocess=ConditionalFeatures(tuple(CORE)).fit(frame)
        self.x=self.preprocess.transform(frame)
        if not self.local:
            self.model=Ridge(alpha=self.params['alpha']).fit(self.x,self.target)
        return self
    def predict(self,frame,query,distance):
        z=self.preprocess.transform(frame)
        if not self.local:return self.model.predict(z)
        idx,near,w=neighborhood(distance,self.positions,query,self.params['k'],self.params['power'])
        x=self.x[idx];y=self.target[idx];s=w.sum(axis=1)
        mx=np.einsum('qki,qk->qi',x,w)/s[:,None];my=np.einsum('qk,qk->q',y,w)/s
        xc=x-mx[:,None,:];yc=y-my[:,None]
        gram=np.einsum('qki,qk,qkj->qij',xc,w,xc);rhs=np.einsum('qki,qk,qk->qi',xc,w,yc)
        gram+=self.params['alpha']*np.eye(x.shape[2])[None,:,:]
        beta=np.linalg.solve(gram,rhs[:,:,None])[:,:,0]
        return np.einsum('qi,qi->q',z-mx,beta)+my

class NeighborResidual:
    def __init__(self,params):self.params=params
    def fit(self,positions,residual):self.positions=np.asarray(positions,int);self.residual=np.asarray(residual,float);return self
    def predict(self,query,distance):
        idx,near,w=neighborhood(distance,self.positions,query,self.params['k'],self.params['power'])
        return (self.residual[idx]*w).sum(axis=1)/w.sum(axis=1)

def predict_bundle(pack,frame,query,distance):
    baseline=pack['ct3'].predict(frame);result={}
    for name,b in pack['variants'].items():
        if b['kind']=='direct':result[name]=b['model'].predict(frame,query,distance)
        elif b['weight']==0:result[name]=baseline.copy()
        else:
            raw=b['model'].predict(frame,query,distance) if b['kind']=='blend' else b['model'].predict(query,distance)
            delta=raw-baseline if b['kind']=='blend' else raw
            support=support_factor(distance,b['model'].positions,query,b['params']['k']) if b['support'] else 1.
            result[name]=baseline+b['weight']*support*delta
    return result
