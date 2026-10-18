"""Train-only reductions and geographic/physical/satellite correction neighborhoods."""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from sklearn.cluster import KMeans
from src.temporal_indicator_weights import INDICATORS,FixedCorrection
from src.conditional_local_phases import PhysicalSpace

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/modeling/indicator_neighborhoods/v1'
PREVIOUS=ROOT/'outputs/modeling/temporal_indicator_weights/v1'
ENGINEERING=ROOT/'outputs/modeling/signal_feature_engineering/v1'
CALIBRATION=ROOT/'outputs/modeling/neighbor_signal_linear/v1'
R4=['I_history_ndvi_floor','I_history_fapar_floor','I_gap_excess_persistence','I_slope_min']
REDUCTIONS={'R9':INDICATORS,'R4':R4,'R3':[R4[0],R4[2],R4[3]],'R2':[R4[2],R4[3]],'PCA2':INDICATORS}
SATELLITE=R4[:3]
TERRAIN=['altitude_sensitivity::TOPO_BASIC_elevation_mean','relief::TOPO_BASIC_slope_mean','relief::TOPO_ADV_tpi_3x3_mean']
KGRID=[8,16,24,48,72]
CLUSTERS=[4,8]


class NumericSpace:
    def __init__(self,columns,pca=0):self.columns=list(columns);self.pca=pca
    def fit(self,f):
        x=f[self.columns].to_numpy(float);self.med=np.array([np.median(c[np.isfinite(c)]) if np.isfinite(c).any() else 0. for c in x.T]);x=np.where(np.isfinite(x),x,self.med);self.mean=x.mean(axis=0);self.scale=np.maximum(x.std(axis=0),1e-8);self.support=x.std(axis=0)>1e-8;self.model=None
        z=((x-self.mean)/self.scale)[:,self.support]
        if self.pca and z.shape[1] and len(z)>1:self.model=PCA(n_components=min(self.pca,z.shape[1],len(z)-1),svd_solver='full').fit(z)
        return self
    def transform(self,f):
        x=f[self.columns].to_numpy(float);z=((np.where(np.isfinite(x),x,self.med)-self.mean)/self.scale)[:,self.support]
        if self.model is not None:return self.model.transform(z)
        return z if z.shape[1] else np.zeros((len(f),1))


class ReducedCorrection:
    def __init__(self,reduction):self.reduction=reduction
    def fit(self,f,residual):
        cols=REDUCTIONS[self.reduction];self.space=NumericSpace(cols,2 if self.reduction=='PCA2' else 0).fit(f);z=self.space.transform(f);self.names=[f'Z{j}' for j in range(z.shape[1])];self.model=FixedCorrection(self.names).fit(pd.DataFrame(z,columns=self.names),residual);return self
    def delta(self,f):return self.model.predict_delta(pd.DataFrame(self.space.transform(f),columns=self.names))


def haversine(a,b):
    a=np.radians(np.asarray(a,float));b=np.radians(np.asarray(b,float));dlat=a[:,None,0]-b[None,:,0];dlon=a[:,None,1]-b[None,:,1];h=np.sin(dlat/2)**2+np.cos(a[:,None,0])*np.cos(b[None,:,0])*np.sin(dlon/2)**2
    return 6371.*2*np.arcsin(np.sqrt(np.clip(h,0,1)))


class NeighborhoodSpace:
    def __init__(self,kind,definitions):self.kind=kind;self.definitions=definitions
    def fit(self,f):
        self.frame=f.copy();self.ids=f.ID_POLIGONO.to_numpy();self.valid=np.isfinite(f[SATELLITE].to_numpy(float)).all(axis=1) if self.kind=='SATELLITE' else np.ones(len(f),bool)
        if self.kind=='GEO':self.lat=float(f.base_centroid_lat.mean())
        elif self.kind=='SATELLITE':self.numeric=NumericSpace(SATELLITE).fit(f[self.valid] if self.valid.any() else f)
        else:self.physical=PhysicalSpace('BOTH',self.definitions).fit(f);self.terrain=NumericSpace(TERRAIN).fit(f);z=self.terrain.transform(f);self.terrain_norm=max(float(np.sqrt(np.mean(np.sum(z*z,axis=1)))),1e-8)
        self.z=self.transform(f)
        d=self.distances(f)[np.ix_(self.valid,self.valid)]
        if len(d)>1:
            np.fill_diagonal(d,np.inf);positive=np.min(d,axis=1);positive=positive[(positive>1e-8)&np.isfinite(positive)];self.distance_scale=float(np.median(positive)) if len(positive) else 1.
        else:self.distance_scale=1.
        return self
    def transform(self,f):
        if self.kind=='GEO':return np.column_stack([f.base_centroid_lat.to_numpy()*111.32,f.base_centroid_lon.to_numpy()*111.32*np.cos(np.radians(self.lat))])
        if self.kind=='SATELLITE':return self.numeric.transform(f)
        # Equal weight to the existing physical geometry and the new terrain block.
        return np.column_stack([self.physical.transform(f),self.terrain.transform(f)/self.terrain_norm])/np.sqrt(2)
    def distances(self,q):
        return haversine(q[['base_centroid_lat','base_centroid_lon']].to_numpy(),self.frame[['base_centroid_lat','base_centroid_lon']].to_numpy()) if self.kind=='GEO' else cdist(self.transform(q),self.z)
    def fit_clusters(self,n):
        z=self.z[self.valid];self.cluster=None
        if len(z):
            k=min(n,len(np.unique(np.round(z,10),axis=0)));self.cluster=KMeans(n_clusters=max(1,k),n_init=5,max_iter=100,random_state=2026).fit(z)
            self.labels=np.full(len(self.frame),-1,int);self.labels[self.valid]=self.cluster.labels_
        return self
    def memberships(self,q,mode,param):
        d=self.distances(q)/max(self.distance_scale,1e-8);validq=np.isfinite(q[SATELLITE].to_numpy(float)).all(axis=1) if self.kind=='SATELLITE' else np.ones(len(q),bool);result=[]
        labels=self.cluster.predict(self.transform(q)) if mode=='CLUSTER' and self.cluster is not None else None
        for i in range(len(q)):
            available=self.valid&(self.ids!=q.ID_POLIGONO.iloc[i])
            if not validq[i] or not available.any() or (mode=='CLUSTER' and labels is None):result.append((np.array([],int),np.array([])));continue
            if mode=='CLUSTER':use=np.flatnonzero(available&(self.labels==labels[i]));w=np.ones(len(use))
            else:
                indices=np.flatnonzero(available);n=min(param,len(indices));threshold=np.partition(d[i,indices],n-1)[n-1];use=indices[d[i,indices]<=threshold+1e-12];w=1/(d[i,use]+.25)
            if len(w):w=w/w.sum()
            result.append((use,w))
        return result


class LocalCorrection:
    def __init__(self,kind,mode,param,definitions):self.kind=kind;self.mode=mode;self.param=param;self.definitions=definitions
    def fit(self,f,residual,candidate_oof=None):
        self.frame=f.copy();self.residual=np.asarray(residual,float);self.global_model=ReducedCorrection('R4').fit(f,residual);self.numeric=NumericSpace(R4).fit(f);self.z=self.numeric.transform(f);self.geometry=NeighborhoodSpace(self.kind,self.definitions).fit(f)
        if self.mode=='CLUSTER':self.geometry.fit_clusters(self.param)
        self.candidate=np.asarray(candidate_oof,float) if candidate_oof is not None else None
        if self.candidate is not None:
            den=float(self.candidate@self.candidate);self.global_weight=float(np.clip(self.candidate@self.residual/(1.1*den),0,1)) if den>1e-12 else 0.;self.prior=20*float(np.mean(self.candidate**2))
        return self
    def predict(self,q,use='DIRECT',strength=.5,details=False):
        candidate=self.global_model.delta(q);global_residual=candidate/.5;zq=self.numeric.transform(q);members=self.geometry.memberships(q,self.mode,self.param);deltas=[];records=[]
        for i,(indices,w) in enumerate(members):
            effective=1/float(w@w) if len(w) else 0.;fallback=not len(indices)
            if use=='DIRECT':
                if len(indices)>=4:
                    model=Ridge(alpha=30.,solver='svd').fit(self.z[indices],self.residual[indices],sample_weight=w*len(indices));local=float(model.predict(zq[[i]])[0]);rho=effective/(effective+20);raw=rho*local+(1-rho)*global_residual[i]
                else:raw=global_residual[i];fallback=True
                delta=strength*float(np.clip(raw,-.5,.5));weight=np.nan
            else:
                if len(indices) and self.candidate is not None:
                    ww=w*effective;den=float(np.sum(ww*self.candidate[indices]**2))+self.prior;num=float(np.sum(ww*self.candidate[indices]*self.residual[indices]))+self.prior*self.global_weight;weight=float(np.clip(num/den,0,1)) if den>1e-12 else self.global_weight
                else:weight=self.global_weight
                weight*=strength/.5;delta=weight*candidate[i]
            deltas.append(delta)
            if details:records.append(dict(neighbor_ids=self.frame.iloc[indices].ID_POLIGONO.tolist(),neighbor_weights=w.tolist(),neighbor_count=len(indices),effective_neighbor_count=effective,fallback_global=fallback,weight=weight,candidate_delta=candidate[i],applied_delta=delta))
        return (np.asarray(deltas),records) if details else np.asarray(deltas)
