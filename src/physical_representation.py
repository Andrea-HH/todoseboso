"""Training-only alternatives to fixed PCA5 for physical residual correction."""
import numpy as np
from sklearn.decomposition import PCA
from src.physical_similarity import BlockRepresentation


class PhysicalRepresentation:
    def __init__(self, columns, summary, composition=False, mode='raw', components=5):
        self.columns=list(columns);self.summary=list(summary);self.composition=composition;self.mode=mode;self.components=components

    def _raw(self,frame):
        a=self.encoder_._matrix(frame)
        if self.composition:
            # Map shares, not lab percentages. Preserve zeros and unseen training classes.
            if np.any(a < -1e-7) or np.any(a > 1+1e-7):raise ValueError('Invalid composition share')
            a=np.clip(a,0,1)
            return a if self.mode=='raw' else np.sqrt(a)
        if self.mode=='summary':
            for i,c in enumerate(self.used_columns_):
                if 'distance_' in c:a[:,i]=np.log1p(np.maximum(a[:,i],0))
        return a

    def fit(self,frame):
        self.used_columns_=self.summary if self.mode=='summary' else self.columns
        self.encoder_=BlockRepresentation(self.used_columns_,components=1).fit(frame)
        a=self._raw(frame);self.mean_=a.mean(axis=0)
        self.scale_=np.ones(a.shape[1]) if self.composition else a.std(axis=0)
        self.scale_[self.scale_<1e-8]=1.
        z=(a-self.mean_)/self.scale_;self.pca_=None
        if self.mode.startswith('pca') and np.sum(np.var(z,axis=0))>1e-12:
            k=min(self.components,z.shape[1],len(z)-1)
            self.pca_=PCA(n_components=k,svd_solver='full').fit(z);z=self.pca_.transform(z)
        # No division by the frequency/variance of composition classes.
        self.norm_=1. if self.composition else max(float(np.sqrt(np.mean(np.sum(z*z,axis=1)))),1e-8)
        self.dimension_=z.shape[1];self.explained_=float(self.pca_.explained_variance_ratio_.sum()) if self.pca_ is not None else 1.
        return self

    def transform(self,frame):
        z=(self._raw(frame)-self.mean_)/self.scale_
        if self.pca_ is not None:z=self.pca_.transform(z)
        return z/self.norm_


MODES=[('summary',0),('pca1',1),('pca3',3),('pca5',5),('pca8',8),('raw',0)]
