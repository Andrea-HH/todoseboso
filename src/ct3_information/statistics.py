"""Descriptive statistics; no hypothesis tests or predictive yield models."""
import numpy as np
import pandas as pd

def variance_parts(values,groups):
    d=pd.DataFrame({'x':values,'g':groups}).replace([np.inf,-np.inf],np.nan).dropna()
    if not len(d):return dict(n=0,total_ss=0.,within_ss=0.,between_ss=0.,within_fraction=np.nan,contrasting_profiles=0,contrast_parcels=0)
    centered=d.x-d.groupby('g').x.transform('mean')
    total=float(((d.x-d.x.mean())**2).sum());within=float((centered**2).sum())
    sizes=d.groupby('g').size();ranges=d.groupby('g').x.agg(lambda z:float(z.max()-z.min()))
    tolerance=max(1.,float(d.x.abs().max()))*1e-10
    contrast=(sizes>=2)&(ranges>tolerance)
    return dict(n=len(d),total_ss=total,within_ss=within,between_ss=max(0.,total-within),within_fraction=within/total if total>1e-20 else np.nan,contrasting_profiles=int(contrast.sum()),contrast_parcels=int(sizes[contrast].sum()))

def category_contrasts(values,groups):
    d=pd.DataFrame({'x':values,'g':groups}).dropna()
    sizes=d.groupby('g').size();unique=d.groupby('g').x.nunique();mixed=(sizes>=2)&(unique>1)
    discord=[];pairtotal=0;pairdiff=0
    for _,z in d.groupby('g'):
        n=len(z)
        if n<2:continue
        counts=z.x.value_counts().to_numpy();pairs=n*(n-1)/2;different=(n*n-(counts*counts).sum())/2
        discord.append(different/pairs);pairtotal+=pairs;pairdiff+=different
    return dict(n=len(d),contrasting_profiles=int(mixed.sum()),contrast_parcels=int(sizes[mixed].sum()),discordance_pair_weighted=pairdiff/pairtotal if pairtotal else np.nan,discordance_equal_profile=float(np.mean(discord)) if discord else np.nan)

def residual_projection(core,z):
    """In-sample OLS descriptive residual, complete finite rows only."""
    core=np.asarray(core,float);z=np.asarray(z,float);valid=np.isfinite(z)&np.isfinite(core).all(axis=1)
    out=np.full(len(z),np.nan)
    if valid.sum()<=core.shape[1]+1:return out
    a=core[valid];sd=a.std(axis=0);sd=np.where(sd>1e-12,sd,1.)
    design=np.column_stack([np.ones(len(a)),(a-a.mean(axis=0))/sd])
    beta=np.linalg.lstsq(design,z[valid],rcond=1e-10)[0];out[valid]=z[valid]-design@beta
    return out

def cross_projection(train_core,train_z,valid_core,valid_z):
    """Fit E[Z|core] on train X only; no validation values/labels in fitting."""
    a=np.asarray(train_core,float);v=np.asarray(valid_core,float);z=np.asarray(train_z,float);q=np.asarray(valid_z,float)
    mean=a.mean(axis=0);sd=np.where(a.std(axis=0)>1e-12,a.std(axis=0),1.)
    design=np.column_stack([np.ones(len(a)),(a-mean)/sd]);vd=np.column_stack([np.ones(len(v)),(v-mean)/sd])
    supported=np.isfinite(z)
    if supported.sum()<=design.shape[1]:return np.full(len(q),np.nan)
    beta=np.linalg.lstsq(design[supported],z[supported],rcond=1e-10)[0]
    return np.where(np.isfinite(q),q-vd@beta,np.nan)

def correlation(a,b,weights=None):
    a=np.asarray(a,float);b=np.asarray(b,float);w=np.ones(len(a)) if weights is None else np.asarray(weights,float)
    good=np.isfinite(a)&np.isfinite(b)&np.isfinite(w)&(w>0);a=a[good];b=b[good];w=w[good]
    if len(a)<3:return np.nan
    w=w/w.sum();a=a-np.sum(w*a);b=b-np.sum(w*b)
    denom=np.sqrt(np.sum(w*a*a)*np.sum(w*b*b))
    return float(np.sum(w*a*b)/denom) if denom>1e-15 else np.nan

def partial_correlation(y,z,core,weights=None):
    y=np.asarray(y,float);z=np.asarray(z,float);core=np.asarray(core,float)
    if core.ndim==1:core=core[:,None]
    w=np.ones(len(y)) if weights is None else np.asarray(weights,float)
    good=np.isfinite(y)&np.isfinite(z)&np.isfinite(core).all(axis=1)&(w>0)
    y=y[good];z=z[good];a=core[good];w=w[good]
    if len(y)<=a.shape[1]+2:return np.nan
    sd=a.std(axis=0);a=(a-a.mean(axis=0))/np.where(sd>1e-12,sd,1.)
    a=np.column_stack([np.ones(len(y)),a]);sw=np.sqrt(w)
    by=np.linalg.lstsq(a*sw[:,None],y*sw,rcond=1e-10)[0];bz=np.linalg.lstsq(a*sw[:,None],z*sw,rcond=1e-10)[0]
    return correlation(y-a@by,z-a@bz,w)

def within_association(frame,z,y,ndvi,groups,equal_profile=False):
    d=frame[[z,y,ndvi,groups]].replace([np.inf,-np.inf],np.nan).dropna().copy()
    sizes=d.groupby(groups).size();d=d[d[groups].isin(sizes[sizes>=2].index)]
    n=len(d);ng=d[groups].nunique()
    if not n:return dict(n=0,n_profiles=0,correlation=np.nan)
    g=d.groupby(groups);centered=d[[z,y,ndvi]]-g[[z,y,ndvi]].transform('mean')
    weights=1/g[z].transform('size').to_numpy() if equal_profile else np.ones(n)
    return dict(n=n,n_profiles=int(ng),correlation=partial_correlation(centered[y],centered[z],centered[[ndvi]],weights))

def pair_association(frame,z,y,ndvi,groups,model_group=None,equal_profile=False):
    """Descriptive partial pair association, never independent training samples."""
    fields=list(dict.fromkeys([z,y,ndvi,groups]+([model_group] if model_group else [])))
    d=frame[fields].replace([np.inf,-np.inf],np.nan).dropna(subset=[z,y,ndvi,groups])
    keys=[groups]+([model_group] if model_group else []);rows=[];parcel_ids=set()
    for _,g in d.groupby(keys):
        if len(g)<2:continue
        a=g[[z,y,ndvi]].to_numpy(float);ii,jj=np.triu_indices(len(g),1)
        for v in a[ii]-a[jj]:rows.append((g[groups].iloc[0],*v))
        parcel_ids.update(g.index)
    if not rows:return dict(n_pairs=0,n_parcels=0,n_profiles=0,correlation=np.nan)
    q=pd.DataFrame(rows,columns=['profile','z','y','ndvi'])
    w=1/q.groupby('profile').z.transform('size').to_numpy() if equal_profile else np.ones(len(q))
    return dict(n_pairs=len(q),n_parcels=len(parcel_ids),n_profiles=q.profile.nunique(),correlation=partial_correlation(q.y,q.z,q[['ndvi']],w))

def standardized_matrix(frame):
    x=frame.to_numpy(float);x[~np.isfinite(x)]=np.nan
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',RuntimeWarning);med=np.nanmedian(x,axis=0)
    x=np.where(np.isfinite(x),x,np.nan_to_num(med,nan=0.));sd=x.std(axis=0);keep=sd>1e-12
    return (x[:,keep]-x[:,keep].mean(axis=0))/sd[keep],keep

def spectral_summary(matrix):
    if not matrix.size:return dict(rank=0,effective_rank=0.,participation_rank=0.,components_90=0,components_95=0),np.empty(0),np.empty((0,matrix.shape[1]))
    _,s,v=np.linalg.svd(matrix,full_matrices=False);power=s*s;total=power.sum()
    p=power/total if total else power;positive=p[p>1e-15]
    row=dict(rank=int((s>s.max()*max(matrix.shape)*np.finfo(float).eps).sum()),effective_rank=float(np.exp(-np.sum(positive*np.log(positive)))),participation_rank=float(1/np.sum(p*p)),components_90=int(np.searchsorted(np.cumsum(p),.9)+1),components_95=int(np.searchsorted(np.cumsum(p),.95)+1))
    return row,s,v
