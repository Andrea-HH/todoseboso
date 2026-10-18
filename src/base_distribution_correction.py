"""Simpler bases and target-free, query-specific local-distribution weights."""
import numpy as np
import json
from pathlib import Path
from src.indicator_neighborhoods import NeighborhoodSpace,REDUCTIONS
from src.neighbor_signal_linear import ReuseNestedJ7
from src.signal_role_allocation import RoleSpace,predict_role
from src.geoc_signal_research import predict_base
from src.conditional_local_phases import ExpertGate

R3=REDUCTIONS['R3']

def load_design(directory):
    cfg=json.loads((Path(directory)/'frozen_design.json').read_text())
    amendment=Path(directory)/'amendment_01.json'
    if amendment.exists():cfg['source_sha256'].update(json.loads(amendment.read_text())['source_sha256'])
    return cfg

class DistributionWeight:
    def __init__(self,geometry,k,definitions):self.geometry=geometry;self.k=k;self.definitions=definitions
    def fit(self,f):
        self.space=NeighborhoodSpace(self.geometry,self.definitions).fit(f);self.values=f[R3].to_numpy(float);self.valid=np.isfinite(self.values).all(axis=1);self.space.valid &= self.valid
        self.scale=np.array([np.std(c[np.isfinite(c)]) if np.isfinite(c).any() else 0. for c in self.values.T]);self.scale=np.maximum(self.scale,1e-8);return self
    def predict(self,q,details=False):
        memberships=self.space.memberships(q,'KNN',self.k);values=q[R3].to_numpy(float);similar=[];records=[]
        for i,(indices,_) in enumerate(memberships):
            valid=len(indices)>=4 and np.isfinite(values[i]).all()
            if valid:
                ref=self.values[indices];median=np.median(ref,axis=0);mad=1.4826*np.median(abs(ref-median),axis=0);z=np.clip((values[i]-median)/np.maximum(mad,.25*self.scale),-6,6);distance=float(np.mean(z*z));s=float(np.exp(-.5*distance))
            else:distance=np.nan;s=0.
            similar.append(s);records.append(dict(support=bool(valid),similarity=s,novelty=1-s if valid else 0.,local_distance_squared=distance,neighbor_count=len(indices),neighbor_ids=self.space.ids[indices].tolist()))
        return (np.asarray(similar),records) if details else np.asarray(similar)
    def weights(self,q,use,details=False):
        s,records=self.predict(q,True);w=s if use=='SUPPORT' else np.array([r['novelty'] for r in records]);return (w,records) if details else w

class SimplifiedBases(ReuseNestedJ7):
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.predictions={};self.share_models={}
    def cv(self,tr):
        if hasattr(self,'original_outer_positions') and tuple(tr)==tuple(self.original_outer_positions):return self.original_outer_cv
        return super().cv(tr)
    def shares(self,tr):
        tr=np.asarray(tr);key=tuple(tr)
        if key in self.share_models:return self.share_models[key]
        try:cv=self.cv(tr)
        except ValueError:
            self.logs.append(dict(kind='shares_ct3_only_no_cv',positions=tr.tolist()));return None
        ct,ep=self.route_oof(tr,cv);frame=self.a['role_frame'];y=self.a['y'];atoms=['geologic_composition'];scores=[]
        for k in [4,8]:
            prediction=np.full(len(tr),np.nan)
            for c,d in cv:
                aa=tr[c];bb=tr[d]
                try:ac,ae=self.route_oof(aa)
                except ValueError:
                    prediction[d]=ct[d];self.logs.append(dict(kind='shares_inner_ct3_only',positions=aa.tolist()));continue
                s=RoleSpace(atoms,[],self.a['physical_definitions']).fit(frame.iloc[aa]);gate=ExpertGate('clusters',k).fit(s.transform(frame.iloc[aa]),y[aa],ac,ae);prediction[d]=gate.predict(s.transform(frame.iloc[bb]),ct[d],ep[d])
            scores.append((float(np.mean((prediction-y[tr])**2)),k))
        k=min(scores,key=lambda z:(round(z[0],12),z[1]))[1];space=RoleSpace(atoms,[],self.a['physical_definitions']).fit(frame.iloc[tr]);gate=ExpertGate('clusters',k).fit(space.transform(frame.iloc[tr]),y[tr],ct,ep);pack=dict(space=space,gate=gate,k=k);self.share_models[key]=pack;return pack
    def predict_all(self,tr,query):
        tr=np.asarray(tr);query=np.asarray(query);key=(tuple(tr),tuple(query))
        if key in self.predictions:return self.predictions[key]
        assert not set(tr)&set(query);ct=self.ct3(tr).predict(self.a['a']['train'].iloc[query]);expert=self.expert(tr);raw=predict_base(expert['local'],query,self.a);ep=predict_role(expert,query,self.a);shares=self.shares(tr);sp=ct.copy() if shares is None else shares['gate'].predict(shares['space'].transform(self.a['role_frame'].iloc[query]),ct,ep)
        result=dict(CT3=ct,RAW7=raw,EXPERT7=ep,EQUAL7=(ct+ep)/2,SHARES=sp);self.predictions[key]=result;self.ledger.append(dict(kind='simplified_base',train=tr.tolist(),held=query.tolist()));return result
