"""Continuous zero-anchored signal contrasts, with read-only warm base caches."""
import hashlib
import numpy as np
import joblib
from sklearn.linear_model import ElasticNet
from src.neighbor_signal_contrasts import ROOT,OUT as TREE_OUT,NestedJ7,VARIANT
from src.ct3_residual_conditional.execution import signature

OUT=ROOT/'outputs/modeling/neighbor_signal_linear/v1'


class ContinuousAdjustment:
    def __init__(self,kind='LINEAR',alpha=1.,l1_ratio=.9,amplitude=0.):self.kind=kind;self.alpha=alpha;self.l1_ratio=l1_ratio;self.amplitude=amplitude
    def fit(self,z,y,base,ct):
        self.model=None;self.fallback='';self.scale=np.maximum(np.std(z,axis=0),1e-8);self.support=np.std(z,axis=0)>1e-8
        if not self.amplitude:return self
        if not self.support.any():self.fallback='constant_contrasts';return self
        self.model=ElasticNet(alpha=self.alpha,l1_ratio=self.l1_ratio,fit_intercept=False,max_iter=200000,random_state=2026).fit(z[:,self.support]/self.scale[self.support],np.asarray(y)-base)
        return self
    def predict(self,z,base,ct):
        if self.model is None:return np.asarray(base).copy()
        correction=np.clip(self.model.predict(z[:,self.support]/self.scale[self.support]),-.5,.5)
        return base+self.amplitude*correction


class ReuseNestedJ7(NestedJ7):
    """Reuse tree-experiment base contexts without writing to its cache."""
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.warm_directory=TREE_OUT/'cache'/self.directory.name;self.warm_hits={'ct3':0,'expert':0}
    def ct3(self,tr):
        tr=np.asarray(tr)
        try:cv=self.cv(tr)
        except ValueError:cv=None
        key=signature(tr,cv,self.protocol) if cv is not None else hashlib.sha256(repr(('fixed_single_group',tuple(tr),self.protocol)).encode()).hexdigest();tag=('ct3',key)
        if tag in self.models:return self.models[tag]
        path=self.warm_directory/(key+'.joblib')
        if path.exists():
            pack=joblib.load(path);np.testing.assert_array_equal(pack['train_positions'],tr);self.models[tag]=pack['model'];self.warm_hits['ct3']+=1;return pack['model']
        return super().ct3(tr)
    def expert(self,tr,cv=None):
        tr=np.asarray(tr)
        try:cv=self.cv(tr) if cv is None else cv
        except ValueError:return super().expert(tr,cv)
        key=hashlib.sha256(repr((tuple(tr),VARIANT,tuple((tuple(c),tuple(d)) for c,d in cv))).encode()).hexdigest();path=self.warm_directory/'role'/(key+'.joblib')
        if path.exists():
            pack=joblib.load(path);np.testing.assert_array_equal(pack['train_positions'],tr);np.testing.assert_array_equal(pack['local']['targets'],self.a['y'][tr]);self.warm_hits['expert']+=1;return pack
        return super().expert(tr,cv)
