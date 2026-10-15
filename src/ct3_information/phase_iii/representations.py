"""Train-isolated X transforms and reconstruction diagnostics, no Y interface."""
import numpy as np
import pandas as pd

def orth(a):
    if not a.size:return np.empty((a.shape[0],0))
    u,s,_=np.linalg.svd(a,full_matrices=False)
    keep=s>s.max()*max(a.shape)*np.finfo(float).eps if len(s) else []
    return u[:,keep]

def angles(a,b,k):
    a=orth(a[:,:k]);b=orth(b[:,:k]);k=min(k,a.shape[1],b.shape[1])
    if not k:return dict(k=0,overlap=np.nan,min_cosine=np.nan)
    cs=np.linalg.svd(a[:,:k].T@b[:,:k],compute_uv=False)
    return dict(k=k,overlap=float(np.mean(cs**2)),min_cosine=float(cs.min()))

class NumericRepresentation:
    def __init__(self,kind='pca',mode='total',scale='standard',k=5,hierarchical_groups=None,deduplicate=False):
        self.kind=kind;self.mode=mode;self.scale=scale;self.k=k;self.hierarchical_groups=hierarchical_groups;self.deduplicate=deduplicate
    def fit(self,z,core,profiles=None):
        if any(c in z for c in ['RENDIMIENTO_T_HA','y_true','y_pred','Estado','Municipio','ID_POLIGONO']):raise ValueError('Forbidden predictor field')
        if self.mode not in ['total','ct3_residual','within']:raise ValueError(self.mode)
        self.columns=list(z);raw=z.to_numpy(float).copy();raw[~np.isfinite(raw)]=np.nan
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',RuntimeWarning);self.medians=np.nanmedian(raw,axis=0)
        self.medians=np.nan_to_num(self.medians,nan=0.);raw=np.where(np.isfinite(raw),raw,self.medians)
        self.location=raw.mean(axis=0)
        sd=raw.std(axis=0) if self.scale=='standard' else np.quantile(raw,.75,axis=0)-np.quantile(raw,.25,axis=0)
        # Constant IQR does not imply a constant feature; fall back to SD, explicitly.
        self.scale_fallback=(sd<=1e-12)&(raw.std(axis=0)>1e-12)
        sd=np.where(sd>1e-12,sd,raw.std(axis=0));self.scales=np.where(sd>1e-12,sd,1.)
        a=(raw-self.location)/self.scales;self.active=raw.std(axis=0)>1e-12
        if self.deduplicate:
            used=[]
            unit=a/np.where(a.std(axis=0)>1e-12,a.std(axis=0),1.)
            for i in np.flatnonzero(self.active):
                if used and np.max(abs(unit[:,used].T@unit[:,i]/len(a)))>=.99999:self.active[i]=False
                else:used.append(i)
        c=np.asarray(core,float);assert np.isfinite(c).all()
        self.core_mean=c.mean(axis=0);self.core_scale=np.where(c.std(axis=0)>1e-12,c.std(axis=0),1.)
        cd=self._core_design(c);self.beta=np.linalg.lstsq(cd,a,rcond=1e-10)[0]
        self.profile_means={}
        if profiles is not None:
            for g in pd.unique(profiles):self.profile_means[g]=a[np.asarray(profiles)==g].mean(axis=0)
        if self.mode=='ct3_residual':b=a-cd@self.beta
        elif self.mode=='within':
            if profiles is None:raise ValueError('Within transformation requires training profiles')
            b=a-np.stack([self.profile_means[g] for g in profiles])
        else:b=a
        self.center=b.mean(axis=0);b=b-self.center
        mask=self.active&(b.std(axis=0)>1e-12)
        self.mask=mask;self.subgroups=[]
        if self.kind=='original':
            basis=np.eye(len(self.columns))[:,mask];ss=np.linalg.svd(b[:,mask],compute_uv=False);self.eigenvalues=ss*ss/max(1,len(b)-1);self.retained=basis.shape[1]
        elif self.kind=='hierarchical':
            if self.hierarchical_groups is None:raise ValueError('Hierarchy needs explicit groups')
            groups=self.hierarchical_groups
            first=[];sensors=[]
            for key in dict.fromkeys(groups):
                ix=[i for i,g in enumerate(groups) if g==key and mask[i]]
                if not ix:continue
                _,ss,v=np.linalg.svd(b[:,ix],full_matrices=False);power=ss*ss;rank=int((ss>ss.max()*max(b[:,ix].shape)*np.finfo(float).eps).sum())
                if not rank:continue
                kk=min(2,rank,int(np.searchsorted(np.cumsum(power)/power.sum(),.9)+1))
                stage=np.zeros((len(self.columns),kk));stage[ix]=v[:kk].T
                scores=b@stage;norm=np.sqrt(np.var(scores,axis=0).sum());stage/=max(norm,1e-12)
                first.append(stage);sensors.append(key[0]);self.subgroups.append(dict(group=str(key),columns=len(ix),components=kk))
            if first:
                for sensor in set(sensors):
                    count=sensors.count(sensor)
                    for i,s in enumerate(sensors):
                        if s==sensor:first[i]/=np.sqrt(count)
                self.first=np.column_stack(first);u,s,v=np.linalg.svd(b@self.first,full_matrices=False);basis=self.first@v.T;self.eigenvalues=s*s/max(1,len(b)-1)
            else:self.first=np.empty((len(self.columns),0));basis=self.first;self.eigenvalues=np.empty(0)
            self.retained=min(self.k,basis.shape[1])
        else:
            if mask.any():
                _,s,v=np.linalg.svd(b[:,mask],full_matrices=False);basis=np.zeros((len(self.columns),len(s)));basis[mask]=v.T;self.eigenvalues=s*s/max(1,len(b)-1)
            else:basis=np.empty((len(self.columns),0));self.eigenvalues=np.empty(0)
            self.retained=min(self.k,basis.shape[1])
        positive=self.eigenvalues>max(self.eigenvalues.max(initial=0)*max(b.shape)*np.finfo(float).eps,1e-20)
        self.rank=int(positive.sum()) if self.kind!='original' else int(np.linalg.matrix_rank(b[:,mask]))
        if self.kind!='original':self.retained=min(self.retained,self.rank)
        self.basis=basis[:,:self.retained]
        self.full_basis=basis[:,:self.rank]
        self.training_index=list(z.index)
        return self
    def _core_design(self,c):return np.column_stack([np.ones(len(c)),(c-self.core_mean)/self.core_scale])
    def raw_scaled(self,z):
        raw=z[self.columns].to_numpy(float);raw=np.where(np.isfinite(raw),raw,self.medians)
        return (raw-self.location)/self.scales
    def transformed_input(self,z,core,profiles=None):
        a=self.raw_scaled(z)
        if self.mode=='ct3_residual':a=a-self._core_design(np.asarray(core,float))@self.beta
        elif self.mode=='within':
            if profiles is None:raise ValueError('Within needs profile labels')
            a=a-np.stack([self.profile_means.get(g,np.zeros(len(self.columns))) for g in profiles])
        return a-self.center
    def transform(self,z,core,profiles=None):return self.transformed_input(z,core,profiles)@self.basis
    def set_k(self,k):
        if self.kind=='original':return self
        self.retained=min(k,self.rank);self.basis=self.full_basis[:,:self.retained];return self

def centered_groups(a,profiles):
    out=np.zeros_like(a)
    for g in pd.unique(profiles):
        ix=np.asarray(profiles)==g;out[ix]=a[ix]-a[ix].mean(axis=0)
    return out

def retention(a,reconstructed,profiles):
    a=a-a.mean(axis=0);reconstructed=reconstructed-reconstructed.mean(axis=0)
    wa=centered_groups(a,profiles);wr=centered_groups(reconstructed,profiles)
    sizes=pd.Series(profiles).value_counts();weights=np.array([1/sizes[g] if sizes[g]>=2 else 0 for g in profiles])
    def ratio(x,r,w=None):
        w=np.ones(len(x)) if w is None else w;total=np.sum(w[:,None]*x*x)
        return float(1-np.sum(w[:,None]*(x-r)**2)/total) if total>1e-16 else np.nan
    return dict(total_reconstruction_fraction=ratio(a,reconstructed),within_reconstruction_fraction=ratio(wa,wr),within_reconstruction_equal_profile=ratio(wa,wr,weights))

def evaluate(rep,z,core,profiles,dominant,municipalities):
    a=rep.transformed_input(z,core,profiles);t=rep.transform(z,core,profiles)
    decoder=np.linalg.lstsq(t,a,rcond=1e-10)[0] if t.shape[1] else np.empty((0,a.shape[1]));hat=t@decoder
    raw=rep.raw_scaled(z);cd=rep._core_design(np.asarray(core,float));rz=raw-cd@np.linalg.lstsq(cd,raw,rcond=1e-10)[0];rt=t-cd@np.linalg.lstsq(cd,t,rcond=1e-10)[0]
    rhat=rt@np.linalg.lstsq(rt,rz,rcond=1e-10)[0] if rt.shape[1] else np.zeros_like(rz)
    result=retention(a,hat,profiles);result.update({f'CT3_residual_{k}':v for k,v in retention(rz,rhat,profiles).items()})
    counts=pd.Series(profiles).value_counts();contrast=[];parcels=0
    for g in counts[counts>=2].index:
        ix=np.asarray(profiles)==g
        if t.shape[1] and np.max(np.ptp(t[ix],axis=0))>1e-9:contrast.append(g);parcels+=int(ix.sum())
    wt=centered_groups(t,profiles);wa=centered_groups(a,profiles);denom=float(np.sum(wa*wa))
    result.update(dimensions=rep.retained,rank=rep.rank,n=len(z),contrasting_profiles=len(contrast),contrast_parcels=parcels,dominant_within_energy_fraction=float(np.sum(wt[np.isin(profiles,dominant)]**2)/np.sum(wt**2)) if np.sum(wt**2)>1e-16 else np.nan)
    outside=np.asarray(municipalities)!='Chignahuapan';oc=[];op=0
    for g in pd.unique(np.asarray(profiles)[outside]):
        ix=outside&(np.asarray(profiles)==g)
        if ix.sum()>=2 and t.shape[1] and np.max(np.ptp(t[ix],axis=0))>1e-9:oc.append(g);op+=int(ix.sum())
    result.update(outside_contrasting_profiles=len(oc),outside_contrast_parcels=op)
    if rep.eigenvalues.sum()>0:
        p=rep.eigenvalues/rep.eigenvalues.sum();pp=p[p>1e-15];result.update(components_90=int(np.searchsorted(p.cumsum(),.9)+1),components_95=int(np.searchsorted(p.cumsum(),.95)+1),effective_rank=float(np.exp(-np.sum(pp*np.log(pp)))))
    else:result.update(components_90=0,components_95=0,effective_rank=0.)
    return result,t
