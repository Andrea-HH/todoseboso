"""CT3/26/14/B1 replay and cold refit from a narrow, local 26-input bundle.

No GeoC repository, C4/PCA20, L40 predictions or historical model caches are read.
Shared local-Ridge and cross-fitting implementations remain in this repository.
"""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.linear_model import ElasticNet
from src.base_distribution_correction import SimplifiedBases
from src.pruned_global_architecture import PrunedGlobalFactory
from src.indicator_neighborhoods import REDUCTIONS, ReducedCorrection
from src.ct3_residual_conditional.models import CORE, MeanBase
from src.four_expert_fast_tuner import tune_base_cached_repr
from src.family_4.conditional_response import ConditionalFeatures
from src.signal_role_allocation import predict_role
from src.local_ridge_sufficient_statistics import predict_local_ridge

MODELS=['CT3','Reference26','Compact14','B1']
LOCAL7=['sat_basic_hist__sentinel_2__ndvi_promedio__mean','sat_basic_hist__sentinel_2__ndvi_promedio__std',
        'emp_shape__y2025_planet_evi__turning_fraction','agro_pheno__y2025_planet_ndvi__jun_to_aug_delta',
        'sat_basic_2025__sentinel_2__ndwi_promedio__mean','sat_basic_2025__sentinel_2__ndwi_promedio__std',
        'topo_official__slope__mean']
LOCAL5=[c for c in LOCAL7 if 'planet' not in c]


def load_bundle(directory,verify_saved_models=True):
    directory=Path(directory)
    manifest=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
    for name,digest in manifest['files'].items():
        if not verify_saved_models and name.startswith('models/'):continue
        assert hashlib.sha256((directory/name).read_bytes()).hexdigest()==digest,name
    frame=pd.read_parquet(directory/'train138.parquet')
    groups=pd.read_csv(directory/'groups.csv').set_index('ID_POLIGONO')
    distance=np.load(directory/'distance.npy',allow_pickle=False)
    assert len(frame)==138 and frame.ID_POLIGONO.is_unique and distance.shape==(138,138)
    return frame,groups,distance,manifest


def raw_local(local,query,frame,distance):
    tr=np.asarray(local['train_positions'],int);q=np.asarray(query,int)
    assert not set(tr)&set(q)
    if len(tr)<3:return np.full(len(q),np.mean(local['targets']))
    z=local['representation'].transform(frame)
    return predict_local_ridge(z,distance,tr,q,local['targets'])


def predict_saved(pack,query,frame,distance):
    q=np.asarray(query,int);outer=pack['outer_experts'];raw=outer['raw']
    assert not set(pack['train_positions'])&set(q)
    c=raw['ct3'].predict(frame.iloc[q]);compact=raw['compact']
    cm=compact['ct3'].predict(frame.iloc[q])
    m=cm.copy() if compact['local'] is None else cm+compact['weight']*(raw_local(compact['local'],q,frame,distance)-cm)
    r=c.copy()
    if raw['shares'] is not None:
        e=raw['expert'];ep=raw_local(e['local'],q,frame,distance)
        if e['amplitude']:ep+=e['amplitude']*e['corrector'].predict(frame.iloc[q])
        s=raw['shares'];r=s['gate'].predict(s['space'].transform(frame.iloc[q]),c,ep)
    values=[m,r];complete=np.isfinite(frame.iloc[q][REDUCTIONS['R3']].to_numpy(float)).all(axis=1)
    for j in range(2):
        if outer['correctors'][j] is not None:
            values[j]=values[j]+outer['strengths'][j]*complete*outer['correctors'][j].delta(frame.iloc[q])
    m,r=values
    return dict(CT3=c,Reference26=r,Compact14=m,B1=c+pack['B1_weight']*(r-c))


def assets(frame,distance,geology):
    variants={name:dict(type='small',columns=columns,mode='raw',correction_columns=[],correction_atoms=[],legacy_variant=None)
              for name,columns in [('DROP_JOINT',LOCAL7),('NO_PLANET',LOCAL5)]}
    return dict(a=dict(train=frame,distance=distance,train_global=np.arange(len(frame))),
                y=frame.RENDIMIENTO_T_HA.to_numpy(),features197=frame,role_frame=frame,
                physical_definitions={'geologic_composition':geology},variants=variants)


class ColdBases(SimplifiedBases):
    """Same frozen recipes; explicitly bypass every historical cache lookup."""
    def ct3(self,tr):
        tr=np.asarray(tr);key=('cold_ct3',tuple(tr))
        if key in self.models:return self.models[key]
        t=self.a['a']['train'];y=self.a['y']
        try:cv=self.cv(tr)
        except ValueError:cv=None
        if cv is not None and any(not ConditionalFeatures(tuple(CORE)).fit(t.iloc[tr[c]]).support_.any() for c,d in cv):cv=None
        if cv is None:
            probe=ConditionalFeatures(tuple(CORE)).fit(t.iloc[tr])
            model=(MeanBase().fit(t.iloc[tr],y[tr]) if not probe.support_.any() else
                   Pipeline([('repr',ConditionalFeatures(tuple(CORE))),('model',ElasticNet(alpha=1.,l1_ratio=.5,max_iter=200000,random_state=2026))]).fit(t.iloc[tr],y[tr]))
        else:model,_,_=tune_base_cached_repr(t,y,tr,cv)
        self.models[key]=model
        return model
    def expert(self,tr,cv=None):
        tr=np.asarray(tr)
        try:cv=self.cv(tr) if cv is None else cv
        except ValueError:return dict(local=self.role.base(tr,'DROP_JOINT'),amplitude=0.,corrector=None,train_positions=tr)
        return self.role.fit(tr,'DROP_JOINT',cv)


class ColdExperts:
    """Nested original recipes for14/26, including own R3 selection."""
    def __init__(self,frame,groups,distance,geology,protocol,tr,inner,directory):
        self.frame=frame;self.y=frame.RENDIMIENTO_T_HA.to_numpy();self.a=assets(frame,distance,geology)
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
        self.helper=ColdBases(self.a,protocol,groups,self.directory/'bases',self.directory/'empty_reference')
        self.helper.original_outer_positions=np.asarray(tr);self.helper.original_outer_cv=inner
        self.compact=PrunedGlobalFactory(self.a,'NO_PLANET',protocol,groups,self.directory/'compact',tr,inner)
        self.compact.helper=self.helper
        self.raw_models={};self.raw_predictions={};self.oof={};self.full={}
    def cv(self,tr):return self.helper.cv(np.asarray(tr))
    def raw_fit(self,tr):
        tr=np.asarray(tr);key=tuple(tr)
        if key not in self.raw_models:
            shares=self.helper.shares(tr)
            self.raw_models[key]=dict(ct3=self.helper.ct3(tr),shares=shares,
                expert=self.helper.expert(tr) if shares is not None else None,
                compact=self.compact.fit(tr),train_positions=tr)
        return self.raw_models[key]
    def raw_predict(self,tr,q):
        tr=np.asarray(tr);q=np.asarray(q);assert not set(tr)&set(q);key=(tuple(tr),tuple(q))
        if key not in self.raw_predictions:
            p=self.raw_fit(tr);c=p['ct3'].predict(self.frame.iloc[q]);r=c.copy()
            if p['shares'] is not None:
                ep=predict_role(p['expert'],q,self.a);s=p['shares'];r=s['gate'].predict(s['space'].transform(self.frame.iloc[q]),c,ep)
            self.raw_predictions[key]=np.column_stack([self.compact.predict(p['compact'],q),r])
        return self.raw_predictions[key]
    def raw_oof(self,tr):
        tr=np.asarray(tr);key=tuple(tr)
        if key not in self.oof:
            values=np.full((len(tr),2),np.nan)
            for c,d in self.cv(tr):values[d]=self.raw_predict(tr[c],tr[d])
            assert np.isfinite(values).all();self.oof[key]=values
        return self.oof[key]
    def full_fit(self,tr):
        tr=np.asarray(tr);key=tuple(tr)
        if key in self.full:return self.full[key]
        raw=self.raw_fit(tr)
        try:cv=self.cv(tr)
        except ValueError:
            p=dict(raw=raw,correctors=[None,None],strengths=[0.,0.],train_positions=tr,candidates=[],fallback='Insufficient groups; R3 disabled')
            self.full[key]=p;return p
        oof=self.raw_oof(tr);delta=np.full_like(oof,np.nan)
        for c,d in cv:
            aa=tr[c];bb=tr[d]
            try:deep=self.raw_oof(aa)
            except ValueError:delta[d]=0.;continue
            complete=np.isfinite(self.frame.iloc[bb][REDUCTIONS['R3']].to_numpy(float)).all(axis=1)
            for j in range(2):delta[d,j]=ReducedCorrection('R3').fit(self.frame.iloc[aa],self.y[aa]-deep[:,j]).delta(self.frame.iloc[bb])*complete
        correctors=[];strengths=[];candidates=[]
        for j in range(2):
            scores=[dict(strength=s,rmse=float(np.sqrt(np.mean((oof[:,j]+s*delta[:,j]-self.y[tr])**2)))) for s in [0.,.5,1.]]
            strengths.append(min(scores,key=lambda v:(round(v['rmse'],12),v['strength']))['strength'])
            correctors.append(ReducedCorrection('R3').fit(self.frame.iloc[tr],self.y[tr]-oof[:,j]));candidates.append(scores)
        p=dict(raw=raw,correctors=correctors,strengths=strengths,train_positions=tr,candidates=candidates,fallback='')
        self.full[key]=p;return p
    def predict(self,p,q):
        pack=dict(outer_experts=p,train_positions=p['train_positions'],B1_weight=0.)
        out=predict_saved(pack,q,self.frame,self.a['a']['distance'])
        return np.column_stack([out['CT3'],out['Compact14'],out['Reference26']])


def refit_fold(frame,groups,distance,geology,record,directory):
    tr=np.array(record['train_positions']);va=np.array(record['validation_positions'])
    inner=[(np.array(i['train_relative_positions']),np.array(i['validation_relative_positions'])) for i in record['inner']]
    protocol='random' if record['protocol']=='fresh_97_41' else record['protocol']
    factory=ColdExperts(frame,groups,distance,geology,protocol,tr,inner,directory)
    oof=np.full((len(tr),3),np.nan)
    for j,(c,d) in enumerate(inner):
        print(f'  Internal expert refit {j+1}/{len(inner)}',flush=True)
        oof[d]=factory.predict(factory.full_fit(tr[c]),tr[d])
    c,m,r=oof.T;delta=r-c;energy=float(delta@delta)
    weight=float(np.clip(delta@(factory.y[tr]-c)/energy,0,1)) if energy>1e-12 else 0.
    pack=dict(outer_experts=factory.full_fit(tr),train_positions=tr,validation_positions=va,B1_weight=weight)
    assert all(not set(row['train'])&(set(row['held'])|set(va)) for row in factory.helper.ledger+factory.helper.role.ledger)
    return pack
