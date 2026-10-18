"""Paired base ablations with reusable nested component fits and train-only PCA."""
from pathlib import Path
import json
import copy
import numpy as np
from sklearn.decomposition import PCA
from src.base_distribution_correction import SimplifiedBases
from src.neighbor_signal_contrasts import load_assets as original_assets,JOINT
from src.signal_role_allocation import RoleSpace,role_corrector
from src.geoc_signal_research import predict_base
from src.conditional_local_phases import ExpertGate,global_weight
from src.local_ridge_sufficient_statistics import predict_local_ridge

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/modeling/architecture_decomposition/v1'

def load_design():
    cfg=json.loads((OUT/'frozen_design.json').read_text());path=OUT/'performance_amendment.json'
    if path.exists():
        amendment=json.loads(path.read_text());cfg['workers']=amendment['workers'];cfg['source_sha256'].update(amendment['source_sha256'])
    return cfg

def local_sets():
    full=json.loads((JOINT/'frozen_design.json').read_text())['variants']['DROP_JOINT']['columns'];h=full[:2];p=full[2:4];w=full[4:6];s=full[6:]
    return dict(FULL7=full,NO_HISTORY=[c for c in full if c not in h],NO_PLANET=[c for c in full if c not in p],NO_NDWI=[c for c in full if c not in w],NO_SLOPE=[c for c in full if c not in s],HISTORY_SLOPE=h+s,PLANET_SLOPE=p+s,NDWI_SLOPE=w+s)

def load_assets():
    a=original_assets()
    for name,columns in local_sets().items():a['variants'][name]=dict(type='small',columns=columns,mode='raw',correction_columns=[],correction_atoms=[],legacy_variant=None)
    return a

class GeologySpace:
    def __init__(self,kind,definitions):self.kind=kind;self.definitions=definitions
    def fit(self,f):
        self.pca=None
        if self.kind!='GLOBAL':
            self.original=RoleSpace(['geologic_composition'],[],self.definitions).fit(f)
            if self.kind=='PCA2':self.pca=PCA(n_components=min(2,len(f)-1,10),svd_solver='full').fit(self.original.transform(f))
        return self
    def transform(self,f):
        if self.kind=='GLOBAL':return np.zeros((len(f),1))
        z=self.original.transform(f);return self.pca.transform(z) if self.pca is not None else z

class DecompositionFactory:
    def __init__(self,a,protocol,groups,directory,outer_positions,outer_cv):
        self.a=a;self.protocol=protocol;self.helper=SimplifiedBases(a,protocol,groups,directory,JOINT/'cache'/Path(directory).name);self.helper.original_outer_positions=outer_positions;self.helper.original_outer_cv=outer_cv;self.raw_models={};self.raw_predictions={};self.experts={};self.component_cache={};self.space_cache={};self.route_models={};self.gate_templates={};self.ledger=[];self.logs=[]
    def cv(self,tr):return self.helper.cv(tr)
    def raw(self,tr,query,variant):
        tr=np.asarray(tr);query=np.asarray(query);key=(tuple(tr),variant)
        if key not in self.raw_models:self.raw_models[key]=self.helper.role.base(tr,variant)
        pk=(key,tuple(query))
        if pk not in self.raw_predictions:
            assert not set(tr)&set(query);local=self.raw_models[key]
            if len(tr)<3:value=np.full(len(query),self.a['y'][tr].mean())
            else:
                xx=local['representation'].transform(self.a['features197']);value=predict_local_ridge(xx,self.a['a']['distance'],self.a['a']['train_global'][tr],self.a['a']['train_global'][query],self.a['y'][tr])
            self.raw_predictions[pk]=value;self.ledger.append(dict(train=tr.tolist(),held=query.tolist(),kind='raw_local'))
        return self.raw_predictions[pk]
    def expert(self,tr,variant):
        tr=np.asarray(tr);key=(tuple(tr),variant)
        if key in self.experts:return self.experts[key]
        full=self.helper.expert(tr)
        if variant=='FULL7':pack=full
        else:
            local_key=(tuple(tr),variant)
            if local_key not in self.raw_models:self.raw_models[local_key]=self.helper.role.base(tr,variant)
            amplitude=full['amplitude'];corrector=None
            if amplitude:
                cv=self.cv(tr);oof=np.full(len(tr),np.nan)
                for c,d in cv:oof[d]=self.raw(tr[c],tr[d],variant)
                params={k:full['corrector'].named_steps['model'].get_params()[k] for k in ['alpha','l1_ratio']};corrector=role_corrector(self.a['variants'][variant],params,self.a).fit(self.a['role_frame'].iloc[tr],self.a['y'][tr]-oof)
            pack=dict(local=self.raw_models[local_key],amplitude=amplitude,corrector=corrector,train_positions=tr,hyperparameter_source='FULL7 same training context')
        self.experts[key]=pack;return pack
    def component_predictions(self,tr,query):
        ct=self.helper.ct3(tr).predict(self.a['a']['train'].iloc[query]);out={}
        for variant in local_sets():
            e=self.expert(tr,variant);raw=predict_base(e['local'],query,self.a) if variant=='FULL7' else self.raw(tr,query,variant);corrected=raw.copy()
            if e['amplitude']:corrected+=e['amplitude']*e['corrector'].predict(self.a['role_frame'].iloc[query])
            out[(variant,'OFF')]=raw;out[(variant,'ON')]=corrected
        self.ledger.append(dict(train=np.asarray(tr).tolist(),held=np.asarray(query).tolist(),kind='component_predictions'));return ct,out
    def components(self,tr):
        tr=np.asarray(tr);key=tuple(tr)
        if key in self.component_cache:return self.component_cache[key]
        cv=self.cv(tr);ct=np.full(len(tr),np.nan);ep={(v,c):np.full(len(tr),np.nan) for v in local_sets() for c in ['OFF','ON']}
        for a,b in cv:
            cc,ee=self.component_predictions(tr[a],tr[b]);ct[b]=cc
            for k,value in ee.items():ep[k][b]=value
        assert np.isfinite(ct).all() and all(np.isfinite(v).all() for v in ep.values());self.component_cache[key]=(ct,ep);return ct,ep
    def space(self,tr,kind):
        key=(tuple(tr),kind)
        if key not in self.space_cache:self.space_cache[key]=GeologySpace(kind,self.a['physical_definitions']).fit(self.a['role_frame'].iloc[tr])
        return self.space_cache[key]
    def gate(self,key,z,y,ct,ep,k):
        if k==0:return ExpertGate('global',0).fit(z,y,ct,ep)
        if key not in self.gate_templates:self.gate_templates[key]=ExpertGate('clusters',k).fit(z,y,ct,ep)
        g=copy.copy(self.gate_templates[key]);g.global_=global_weight(y,ct,ep);labels=g.model_.labels_;delta=ep-ct;prior=20*float(np.mean(delta**2));g.weights_=np.full(g.model_.n_clusters,g.global_)
        for label in range(g.model_.n_clusters):
            use=labels==label;den=float(np.sum(delta[use]**2))+prior;g.weights_[label]=np.clip((delta[use]@(y[use]-ct[use])+prior*g.global_)/den,0,1) if den>1e-12 else g.global_
        return g
    def fit(self,tr):
        tr=np.asarray(tr);key=tuple(tr)
        if key in self.route_models:return self.route_models[key]
        try:cv=self.cv(tr)
        except ValueError:
            pack=dict(ct3=self.helper.ct3(tr),experts={},routes={},train_positions=tr,fallback=True);self.logs.append(dict(kind='no_groups_route_ct3',positions=tr.tolist()));self.route_models[key]=pack;return pack
        ct,ep=self.components(tr);contexts=[]
        for c,d in cv:
            aa=tr[c]
            try:ac,ae=self.components(aa)
            except ValueError:contexts.append((aa,d,None,None));continue
            contexts.append((aa,d,ac,ae))
        routes={};frame=self.a['role_frame'];y=self.a['y']
        for variant in local_sets():
            for correction in ['OFF','ON']:
                for kind in ['RAW','PCA2','GLOBAL']:
                    choices=[]
                    for k in ([0] if kind=='GLOBAL' else [4,8]):
                        prediction=np.full(len(tr),np.nan)
                        for aa,d,ac,ae in contexts:
                            if ac is None:prediction[d]=ct[d];continue
                            s=self.space(aa,kind);g=self.gate((tuple(aa),kind,k),s.transform(frame.iloc[aa]),y[aa],ac,ae[(variant,correction)],k);prediction[d]=g.predict(s.transform(frame.iloc[tr[d]]),ct[d],ep[(variant,correction)][d])
                        choices.append(dict(k=k,rmse=float(np.sqrt(np.mean((prediction-y[tr])**2)))))
                    best=min(choices,key=lambda v:(round(v['rmse'],12),v['k']));s=self.space(tr,kind);g=self.gate((tuple(tr),kind,best['k']),s.transform(frame.iloc[tr]),y[tr],ct,ep[(variant,correction)],best['k']);routes[variant+'_'+correction+'_'+kind]=dict(space=s,gate=g,variant=variant,correction=correction,selection=best,candidates=choices)
        pack=dict(ct3=self.helper.ct3(tr),experts={v:self.expert(tr,v) for v in local_sets()},routes=routes,train_positions=tr,fallback=False);self.route_models[key]=pack;return pack
    def predict(self,pack,query):return predict_routes(pack,query,self.a)

def predict_routes(pack,query,a):
    query=np.asarray(query);assert not set(pack['train_positions'])&set(query);ct=pack['ct3'].predict(a['a']['train'].iloc[query]);ep={}
    if pack['fallback']:return {v+'_'+c+'_'+g:ct.copy() for v in local_sets() for c in ['OFF','ON'] for g in ['RAW','PCA2','GLOBAL']}
    for variant,e in pack['experts'].items():
        raw=predict_base(e['local'],query,a);corrected=raw.copy()
        if e['amplitude']:corrected+=e['amplitude']*e['corrector'].predict(a['role_frame'].iloc[query])
        ep[(variant,'OFF')]=raw;ep[(variant,'ON')]=corrected
    return {name:r['gate'].predict(r['space'].transform(a['role_frame'].iloc[query]),ct,ep[(r['variant'],r['correction'])]) for name,r in pack['routes'].items()}
