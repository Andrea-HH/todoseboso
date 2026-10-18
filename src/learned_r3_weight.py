"""Strongly regularized correction weights trained on nested OOF proposals."""
from pathlib import Path
import numpy as np
from scipy.spatial.distance import cdist
from src.indicator_neighborhoods import NumericSpace,REDUCTIONS
from src.base_distribution_correction import DistributionWeight

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/modeling/learned_r3_weight/v1'
R3=REDUCTIONS['R3']
FEATURES=['base_prediction','abs_delta','sign_delta','support_distance','local_deviation','history_complete']

class GateFeatures:
    def __init__(self,definitions):self.definitions=definitions
    def fit(self,f):
        self.reference=f.copy();self.valid=np.isfinite(f[R3].to_numpy(float)).all(axis=1);self.space=NumericSpace(R3).fit(f);self.z=self.space.transform(f);self.local=DistributionWeight('SATELLITE',24,self.definitions).fit(f);return self
    def transform(self,q,base,delta):
        dist=cdist(self.space.transform(q),self.z)/np.sqrt(max(self.z.shape[1],1));dist[:,~self.valid]=np.inf;dist[q.ID_POLIGONO.to_numpy()[:,None]==self.reference.ID_POLIGONO.to_numpy()[None,:]]=np.inf;nearest=dist.min(axis=1);nearest[~np.isfinite(nearest)]=np.nan;_,details=self.local.predict(q,True)
        complete=np.isfinite(q[R3].to_numpy(float)).all(axis=1)
        nearest[~complete]=np.nan
        return np.column_stack([base,abs(delta),np.sign(delta),nearest,[r['local_distance_squared'] for r in details],complete.astype(float)])

class LearnedWeight:
    def __init__(self,kind,penalty=1.,strength=1.):self.kind=kind;self.penalty=penalty;self.strength=strength
    def fit(self,z,residual,delta):
        z=np.asarray(z,float);r=np.asarray(residual,float);d=np.asarray(delta,float);self.median=np.array([np.median(c[np.isfinite(c)]) if np.isfinite(c).any() else 0. for c in z.T]);a=np.where(np.isfinite(z),z,self.median);self.mean=a.mean(axis=0);self.scale=np.maximum(a.std(axis=0),1e-8);self.beta={};self.fallbacks=[];energy=float(d@d);self.constant=float(np.clip(d@r/(1.1*energy),0,1)) if energy>1e-12 else 0.;a=np.column_stack([np.ones(len(z)),np.clip((a-self.mean)/self.scale,-4,4)])
        for name,use in [('positive',d>1e-8),('negative',d < -1e-8)] if self.kind in ['ASYM','LEARNED_ASYM'] else [('shared',np.ones(len(d),bool))]:
            if use.sum()<15 or float(d[use]@d[use])<1e-12:self.fallbacks.append(name);continue
            if self.kind=='ASYM':
                s=float(d[use]@d[use]);self.beta[name]=np.array([np.clip((d[use]@r[use]+self.penalty*s*self.constant)/(s*(1+self.penalty)),0,1)])
            elif self.kind.startswith('LEARNED'):
                design=d[use,None]*a[use];prior=np.r_[self.constant,np.zeros(z.shape[1])];penalty=np.diag([.1]+[1.]*z.shape[1])*self.penalty*float(d[use]@d[use]);self.beta[name]=np.linalg.solve(design.T@design+penalty,design.T@r[use]+penalty@prior)
        return self
    def predict(self,z,delta):
        z=np.asarray(z,float);d=np.asarray(delta,float)
        if self.kind=='MASK':return self.strength*(z[:,-1]>.5).astype(float)
        a=np.column_stack([np.ones(len(z)),np.clip((np.where(np.isfinite(z),z,self.median)-self.mean)/self.scale,-4,4)]);w=np.full(len(d),self.constant)
        for name,beta in self.beta.items():
            use=np.ones(len(d),bool) if name=='shared' else (d>1e-8 if name=='positive' else d < -1e-8);w[use]=beta[0] if self.kind=='ASYM' else np.clip(a[use]@beta,0,1)
        return self.strength*np.clip(w,0,1)
