"""Standalone OFF/GLOBAL fit: no geological gate or FULL7 hyperparameter calibration."""
import numpy as np
from src.base_distribution_correction import SimplifiedBases
from src.geoc_signal_research import predict_base
from src.conditional_local_phases import global_weight

class PrunedGlobalFactory:
    def __init__(self,a,variant,protocol,groups,directory,outer,inner):
        self.a=a;self.variant=variant;self.helper=SimplifiedBases(a,protocol,groups,directory,directory);self.helper.original_outer_positions=outer;self.helper.original_outer_cv=inner;self.models={};self.raw={};self.ledger=[]
    def cv(self,tr):return self.helper.cv(tr)
    def raw_model(self,tr):
        key=tuple(tr)
        if key not in self.raw:self.raw[key]=self.helper.role.base(np.asarray(tr),self.variant)
        return self.raw[key]
    def fit(self,tr):
        tr=np.asarray(tr);key=tuple(tr)
        if key in self.models:return self.models[key]
        model=dict(ct3=self.helper.ct3(tr),local=None,weight=0.,train_positions=tr)
        try:cv=self.cv(tr)
        except ValueError:self.models[key]=model;return model
        ct=np.full(len(tr),np.nan);raw=ct.copy()
        for c,d in cv:
            aa=tr[c];bb=tr[d];ct[d]=self.helper.ct3(aa).predict(self.a['a']['train'].iloc[bb]);raw[d]=predict_base(self.raw_model(aa),bb,self.a);self.ledger.append(dict(train=aa.tolist(),held=bb.tolist()))
        assert np.isfinite(ct).all() and np.isfinite(raw).all();model['weight']=global_weight(self.a['y'][tr],ct,raw);model['local']=self.raw_model(tr);self.models[key]=model;return model
    def predict(self,model,query):
        assert not set(model['train_positions'])&set(query);ct=model['ct3'].predict(self.a['a']['train'].iloc[query])
        if model['local'] is None:return ct
        raw=predict_base(model['local'],query,self.a);return ct+model['weight']*(raw-ct)
