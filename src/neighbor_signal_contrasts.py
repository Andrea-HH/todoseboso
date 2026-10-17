"""Train-only neighbor contrasts and small, shrunk conditional adjustments."""
from pathlib import Path
import hashlib,json
import numpy as np
import joblib
from sklearn.tree import DecisionTreeRegressor
from sklearn.pipeline import Pipeline
from sklearn.linear_model import ElasticNet
from src.difficult_case_signals import ROOT,JOINT,SIGNALS,load_assets as signal_assets
from src.ct3_residual_conditional.models import CORE,tune_base,MeanBase
from src.ct3_residual_conditional.execution import signature
from src.family_4.conditional_response import ConditionalFeatures
from src.family_8.research import subcv
from src.signal_role_allocation import RoleFactory,RoleSpace,predict_role
from src.conditional_local_phases import ExpertGate
from src.geoc_bridge import OLD

OUT=ROOT/'outputs/modeling/neighbor_signal_contrasts/v1'
VARIANT='DROP_JOINT'


def load_assets():
    a=signal_assets();a['variants']=json.loads((JOINT/'frozen_design.json').read_text())['variants'];return a


class NeighborContrasts:
    def __init__(self,kind,k=24):self.kind=kind;self.k=k
    def fit(self,signals,core,geography,positions):
        self.positions=np.asarray(positions,int).copy();self.signals=np.asarray(signals,float);self.core=np.asarray(core,float);self.geography=np.asarray(geography,float)
        x=self.signals[self.positions];self.medians=np.nanmedian(x,axis=0);x=np.where(np.isfinite(x),x,self.medians);self.scale=np.std(x,axis=0);self.scale=np.maximum(self.scale,1e-8)
        c=self.core[self.positions];self.core_median=np.nanmedian(c,axis=0);c=np.where(np.isfinite(c),c,self.core_median);self.core_mean=c.mean(axis=0);self.core_scale=np.maximum(c.std(axis=0),1e-8)
        return self
    def transform(self,query,details=False):
        query=np.asarray(query,int)
        if self.kind=='GEO':distance=self.geography[np.ix_(query,self.positions)].copy()
        else:
            q=np.where(np.isfinite(self.core[query]),self.core[query],self.core_median);r=np.where(np.isfinite(self.core[self.positions]),self.core[self.positions],self.core_median)
            distance=np.sqrt(np.sum(((q[:,None,:]-r[None,:,:])/self.core_scale)**2,axis=2))
        distance[query[:,None]==self.positions[None,:]]=np.inf
        ref=np.where(np.isfinite(self.signals[self.positions]),self.signals[self.positions],self.medians);q=np.where(np.isfinite(self.signals[query]),self.signals[query],self.medians);features=[];ledger=[]
        for j,i in enumerate(query):
            # Deterministic ID/position tie break, never using target or signal value.
            order=np.lexsort((self.positions,distance[j]));finite=order[np.isfinite(distance[j,order])];limit=distance[j,finite[min(self.k,len(finite))-1]] if len(finite) else -1
            use=finite[distance[j,finite]<=limit+1e-12]
            if not len(use):raise ValueError('No distinct reference neighbors')
            med=np.median(ref[use],axis=0);mad=1.4826*np.median(abs(ref[use]-med),axis=0);den=np.maximum(mad,.25*self.scale)
            local=np.clip((q[j]-med)/den,-6,6);global_delta=np.clip((q[j]-med)/self.scale,-6,6);features.append(np.r_[local,global_delta])
            if details:ledger.append(dict(position=int(i),neighbors=self.positions[use].tolist(),reference_medians=med.tolist(),reference_mad=mad.tolist(),local_z=local.tolist(),global_delta=global_delta.tolist(),neighbor_count=len(use),farthest_distance=float(distance[j,use[-1]])))
        z=np.asarray(features)
        return (z,ledger) if details else z


class ContrastAdjustment:
    """Additive residual tree or attenuation towards CT3; both include null."""
    def __init__(self,kind,depth=1,leaf=25,amplitude=0.):self.kind=kind;self.depth=depth;self.leaf=leaf;self.amplitude=amplitude
    def fit(self,z,y,base,ct):
        self.tree=None;self.values={};self.fallback=''
        if not self.amplitude:return self
        if len(y)<2*self.leaf:self.fallback='insufficient_leaf_support';return self
        residual=np.asarray(y)-base
        if self.kind=='RESIDUAL':
            self.tree=DecisionTreeRegressor(max_depth=self.depth,min_samples_leaf=self.leaf,random_state=2026).fit(z,residual)
            labels=self.tree.apply(z)
            for label in np.unique(labels):
                use=labels==label;self.values[int(label)]=float(np.clip(residual[use].sum()/(use.sum()+20),-.5,.5))
        else:
            delta=np.asarray(base)-ct;weights=delta**2;valid=abs(delta)>1e-6
            if valid.sum()<2*self.leaf or weights.sum()<1e-10:self.fallback='insufficient_route_difference';return self
            ratio=(np.asarray(y)[valid]-ct[valid])/delta[valid]
            self.tree=DecisionTreeRegressor(max_depth=self.depth,min_samples_leaf=self.leaf,random_state=2026).fit(z[valid],ratio,sample_weight=weights[valid]);labels=self.tree.apply(z);prior=20*float(weights.mean())
            for label in np.unique(labels):
                use=labels==label;self.values[int(label)]=float(np.clip((delta[use]@(np.asarray(y)[use]-ct[use])+prior)/(weights[use].sum()+prior),0,1))
        return self
    def predict(self,z,base,ct):
        if self.tree is None:return np.asarray(base).copy()
        value=np.array([self.values[int(v)] for v in self.tree.apply(z)])
        if self.kind=='RESIDUAL':return base+self.amplitude*value
        attenuation=1+self.amplitude*(value-1);return ct+attenuation*(base-ct)


class NestedJ7:
    """Recover frozen components; retune missing inner contexts using training only.

    Deeper calibration can reach one territorial group: CT3 then uses the fixed
    conservative alpha=1,l1_ratio=.5, and the local expert has no corrector.
    An uncalibratable inner physical gate predicts CT3, not a random-CV substitute.
    External J7 remains the exact saved reference.
    """
    def __init__(self,a,protocol,groups,directory,reference):
        self.a=a;self.protocol=protocol;self.groups=groups;self.directory=Path(directory);self.reference=Path(reference);self.directory.mkdir(parents=True,exist_ok=True);self.role=RoleFactory(a,protocol,groups,self.directory/'role',self.reference);self.models={};self.routes={};self.logs=[];self.ledger=[]
    def cv(self,tr):return subcv(self.a['a']['train'],np.asarray(tr),self.protocol,self.groups)
    def expert(self,tr,cv=None):
        tr=np.asarray(tr)
        try:cv=self.cv(tr) if cv is None else cv
        except ValueError:
            self.logs.append(dict(kind='expert_local_only',positions=tr.tolist()));return dict(local=self.role.base(tr,VARIANT),amplitude=0.,corrector=None,train_positions=tr)
        key=hashlib.sha256(repr((tuple(tr),VARIANT,tuple((tuple(c),tuple(d)) for c,d in cv))).encode()).hexdigest();old=self.reference/(key+'.joblib')
        if old.exists():
            p=joblib.load(old);np.testing.assert_array_equal(p['train_positions'],tr);np.testing.assert_array_equal(p['local']['targets'],self.a['y'][tr]);return p
        return self.role.fit(tr,VARIANT,cv)
    def ct3(self,tr):
        tr=np.asarray(tr);t=self.a['a']['train']
        try:cv=self.cv(tr)
        except ValueError:cv=None
        unsupported_inner_cv=False
        if cv is not None and any(not ConditionalFeatures(tuple(CORE)).fit(t.iloc[tr[c]]).support_.any() for c,d in cv):
            cv=None;unsupported_inner_cv=True
        key=signature(tr,cv,self.protocol) if cv is not None else hashlib.sha256(repr(('fixed_single_group',tuple(tr),self.protocol)).encode()).hexdigest()
        tag=('ct3',key)
        if tag in self.models:return self.models[tag]
        old=OLD/'base_cache'/f'{key}.joblib';path=self.directory/(key+'.joblib')
        if old.exists():
            p=joblib.load(old);assert set(p['registry']['train_ids'])==set(t.iloc[tr].ID_POLIGONO);model=p['model']
        elif path.exists():model=joblib.load(path)['model']
        else:
            if cv is None:
                probe=ConditionalFeatures(tuple(CORE)).fit(t.iloc[tr])
                if not probe.support_.any():
                    model=MeanBase().fit(t.iloc[tr],self.a['y'][tr]);self.logs.append(dict(kind='ct3_mean_zero_features',positions=tr.tolist()))
                else:
                    model=Pipeline([('repr',ConditionalFeatures(tuple(CORE))),('model',ElasticNet(alpha=1.,l1_ratio=.5,max_iter=200000,random_state=2026))]).fit(t.iloc[tr],self.a['y'][tr]);self.logs.append(dict(kind='ct3_fixed_unsupported_cv' if unsupported_inner_cv else 'ct3_fixed_single_group',positions=tr.tolist()))
            else:model,_,_=tune_base(t,self.a['y'],tr,cv)
            joblib.dump(dict(model=model,train_positions=tr),path,compress=3)
        self.models[tag]=model;return model
    def route_oof(self,tr,cv=None):
        tr=np.asarray(tr);cv=self.cv(tr) if cv is None else cv;key=tuple(tr)
        if key in self.routes:return self.routes[key]
        ct=np.full(len(tr),np.nan);ep=ct.copy()
        for c,d in cv:
            fit=tr[c];held=tr[d];assert not set(fit)&set(held);ct[d]=self.ct3(fit).predict(self.a['a']['train'].iloc[held]);ep[d]=predict_role(self.expert(fit),held,self.a);self.ledger.append(dict(train=fit.tolist(),held=held.tolist(),kind='component_crossfit'))
        assert np.isfinite(ct).all() and np.isfinite(ep).all();self.routes[key]=(ct,ep);return ct,ep
    def fit(self,tr):
        tr=np.asarray(tr);key=('j7',tuple(tr))
        if key in self.models:return self.models[key]
        cv=self.cv(tr);ct,ep=self.route_oof(tr,cv);frame=self.a['role_frame'];y=self.a['y'];atoms=['soil_texture_phase','geologic_composition','geologic_distances'];scores=[]
        for k in [4,8]:
            pred=np.full(len(tr),np.nan)
            for c,d in cv:
                aa=tr[c];bb=tr[d]
                try:ac,ae=self.route_oof(aa)
                except ValueError:
                    pred[d]=ct[d];self.logs.append(dict(kind='inner_gate_ct3_only',positions=aa.tolist()));continue
                s=RoleSpace(atoms,[],self.a['physical_definitions']).fit(frame.iloc[aa]);g=ExpertGate('clusters',k).fit(s.transform(frame.iloc[aa]),y[aa],ac,ae);pred[d]=g.predict(s.transform(frame.iloc[bb]),ct[d],ep[d])
            scores.append((float(np.mean((pred-y[tr])**2)),k))
        k=min(scores,key=lambda v:(round(v[0],12),v[1]))[1];space=RoleSpace(atoms,[],self.a['physical_definitions']).fit(frame.iloc[tr]);gate=ExpertGate('clusters',k).fit(space.transform(frame.iloc[tr]),y[tr],ct,ep);pack=dict(ct3=self.ct3(tr),expert=self.expert(tr),space=space,gate=gate,train_positions=tr);self.models[key]=pack;return pack
    def predict(self,pack,query):
        query=np.asarray(query);assert not set(pack['train_positions'])&set(query);ct=pack['ct3'].predict(self.a['a']['train'].iloc[query]);ep=predict_role(pack['expert'],query,self.a);base=pack['gate'].predict(pack['space'].transform(self.a['role_frame'].iloc[query]),ct,ep);return base,ct
