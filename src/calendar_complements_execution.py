"""Execution-only memoization of identical X preprocessing, no Y caching."""
from collections import OrderedDict
import warnings
import numpy as np
from sklearn.linear_model import ElasticNet
from src.calendar_expansion import BlockEstimator

TRANSFORMS=OrderedDict()
PREDICTORS=OrderedDict()

class CachedEN(BlockEstimator):
    def fit(self,frame,y,audit=False):
        assert self.algorithm=='EN' and not self.history and not self.indicators
        self.cache_key_=(tuple(self.columns),tuple(frame.index))
        if self.cache_key_ not in TRANSFORMS:
            x=frame[self.columns].to_numpy(float)
            medians=np.array([np.median(v[np.isfinite(v)]) if np.isfinite(v).any() else 0. for v in x.T])
            a=np.where(np.isfinite(x),x,medians);mean=a.mean(axis=0);scale=a.std(axis=0);scale[scale<1e-12]=1.
            z=(a-mean)/scale
            TRANSFORMS[self.cache_key_]=(medians,mean,scale,z,np.std(z,axis=0)>1e-12)
            if len(TRANSFORMS)>256:TRANSFORMS.popitem(last=False)
        self.medians_,self.mean_,self.scale_,z,self.support_=TRANSFORMS[self.cache_key_]
        self.indicator_positions_=[];self.names_=self.columns.copy();self.is_history_=np.zeros(len(self.columns),bool)
        self.gamma_=self.params['gamma'];self.weights_=np.ones(len(self.columns))
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            self.model_=ElasticNet(alpha=self.params['alpha'],l1_ratio=self.params['l1_ratio'],max_iter=100000,tol=1e-7,selection='cyclic').fit(z*self.weights_,np.asarray(y))
        self.warnings_=[dict(category=w.category.__name__,message=str(w.message)) for w in caught]
        if audit:
            self.effects_=self.model_.coef_*self.weights_;self.used_=abs(self.effects_)>1e-10;self.split_counts_=np.zeros(len(self.names_),int)
        return self
    def predict(self,frame):
        key=(self.cache_key_,tuple(frame.index))
        if key not in PREDICTORS:
            PREDICTORS[key]=(self._raw(frame)-self.mean_)/self.scale_
            if len(PREDICTORS)>2048:PREDICTORS.popitem(last=False)
        return self.model_.predict(PREDICTORS[key]*self.weights_)

def run_fold(index):
    import src.calendar_complements as task
    task.BlockEstimator=CachedEN
    return task.fold(index)
