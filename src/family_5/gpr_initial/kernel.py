"""Matérn 3/2 with exactly one free log length per declared dimension group."""
import numpy as np
from scipy.spatial.distance import cdist
from sklearn.gaussian_process.kernels import Kernel,Hyperparameter

class GroupedMatern32(Kernel):
    def __init__(self,length_scale=1.0,length_scale_bounds=(.2,20.),groups=(0,0,0)):
        self.length_scale=length_scale
        self.length_scale_bounds=length_scale_bounds
        self.groups=groups

    @property
    def hyperparameter_length_scale(self):
        return Hyperparameter('length_scale','numeric',self.length_scale_bounds,len(np.atleast_1d(self.length_scale)))

    def __call__(self,X,Y=None,eval_gradient=False):
        X=np.atleast_2d(np.asarray(X,dtype=float))
        if eval_gradient and Y is not None:raise ValueError('Gradient only supported for Y=None')
        Y=X if Y is None else np.atleast_2d(np.asarray(Y,dtype=float))
        groups=np.asarray(self.groups,dtype=int);ell=np.atleast_1d(np.asarray(self.length_scale,dtype=float))
        if X.shape[1]!=len(groups) or Y.shape[1]!=len(groups):raise ValueError('Kernel dimension/group mismatch')
        if not len(groups) or set(groups)!=set(range(len(ell))) or np.any(ell<=0):raise ValueError('Groups must cover each positive length scale exactly')
        distances=[]
        for j in range(len(ell)):
            mask=groups==j;distances.append(cdist(X[:,mask]/ell[j],Y[:,mask]/ell[j],metric='sqeuclidean'))
        squared=np.sum(distances,axis=0);r=np.sqrt(np.maximum(squared,0));exponential=np.exp(-np.sqrt(3.)*r)
        covariance=(1+np.sqrt(3.)*r)*exponential
        if not eval_gradient:return covariance
        if self.hyperparameter_length_scale.fixed:return covariance,np.empty((*covariance.shape,0))
        # Derivative with respect to log(ell_j), including every axis tied to j.
        gradient=np.stack([3*exponential*q for q in distances],axis=-1)
        return covariance,gradient

    def diag(self,X):return np.ones(len(X))
    def is_stationary(self):return True
    def __repr__(self):return f'GroupedMatern32(length_scale={np.atleast_1d(self.length_scale)}, groups={self.groups})'
