"""Reference26-only adapter preserving original nested recipes; no Compact14 fit.

Core dimensionality is configured explicitly by a worker process; no source or
frozen artifact is modified. Used to test removal ofHHI from both core consumers.
"""
from pathlib import Path
import numpy as np
from src.current_champions import ColdBases,assets
from src.signal_role_allocation import predict_role,RoleFactory,CorrectionSpace,role_corrector
from src.geoc_reverse import GRID,AMPLITUDES
from sklearn.linear_model import ElasticNet
from src.local_ridge_sufficient_statistics import predict_local_ridge
from src.indicator_neighborhoods import REDUCTIONS,ReducedCorrection


class ReferenceOnly:
    helper_type=ColdBases
    predict_expert=staticmethod(predict_role)
    def __init__(self,frame,groups,distance,geology,protocol,tr,inner,directory):
        self.frame=frame;self.y=frame.RENDIMIENTO_T_HA.to_numpy();self.a=assets(frame,distance,geology)
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
        self.helper=self.helper_type(self.a,protocol,groups,self.directory/'bases',self.directory/'empty_reference')
        self.helper.original_outer_positions=np.asarray(tr);self.helper.original_outer_cv=inner
        self.models={};self.predictions={};self.oof={};self.full={}
    def cv(self,tr):return self.helper.cv(np.asarray(tr))
    def raw_fit(self,tr):
        tr=np.asarray(tr);key=tuple(tr)
        if key not in self.models:
            shares=self.helper.shares(tr)
            self.models[key]=dict(ct3=self.helper.ct3(tr),shares=shares,expert=self.helper.expert(tr) if shares is not None else None,train_positions=tr)
        return self.models[key]
    def raw_predict(self,tr,q):
        tr=np.asarray(tr);q=np.asarray(q);assert not set(tr)&set(q);key=(tuple(tr),tuple(q))
        if key not in self.predictions:
            model=self.raw_fit(tr);p=model['ct3'].predict(self.frame.iloc[q])
            if model['shares'] is not None:
                e=self.predict_expert(model['expert'],q,self.a);s=model['shares'];p=s['gate'].predict(s['space'].transform(self.frame.iloc[q]),p,e)
            self.predictions[key]=p
        return self.predictions[key]
    def raw_oof(self,tr):
        tr=np.asarray(tr);key=tuple(tr)
        if key not in self.oof:
            p=np.full(len(tr),np.nan)
            for c,d in self.cv(tr):p[d]=self.raw_predict(tr[c],tr[d])
            assert np.isfinite(p).all();self.oof[key]=p
        return self.oof[key]
    def full_fit(self,tr):
        tr=np.asarray(tr);key=tuple(tr)
        if key in self.full:return self.full[key]
        raw=self.raw_fit(tr)
        try:cv=self.cv(tr)
        except ValueError:
            p=dict(raw=raw,corrector=None,strength=0.,train_positions=tr,candidates=[],fallback='Insufficient groups; R3 disabled')
            self.full[key]=p;return p
        oof=self.raw_oof(tr);delta=np.full(len(tr),np.nan)
        for c,d in cv:
            aa=tr[c];bb=tr[d]
            try:deep=self.raw_oof(aa)
            except ValueError:delta[d]=0.;continue
            complete=np.isfinite(self.frame.iloc[bb][REDUCTIONS['R3']].to_numpy(float)).all(axis=1)
            delta[d]=ReducedCorrection('R3').fit(self.frame.iloc[aa],self.y[aa]-deep).delta(self.frame.iloc[bb])*complete
        scores=[dict(strength=s,rmse=float(np.sqrt(np.mean((oof+s*delta-self.y[tr])**2)))) for s in [0.,.5,1.]]
        strength=min(scores,key=lambda v:(round(v['rmse'],12),v['strength']))['strength']
        corrector=ReducedCorrection('R3').fit(self.frame.iloc[tr],self.y[tr]-oof)
        p=dict(raw=raw,corrector=corrector,strength=strength,train_positions=tr,candidates=scores,fallback='')
        self.full[key]=p;return p
    def predict(self,pack,q):
        q=np.asarray(q);assert not set(pack['train_positions'])&set(q)
        raw=pack['raw'];p=raw['ct3'].predict(self.frame.iloc[q])
        if raw['shares'] is not None:
            e=self.predict_expert(raw['expert'],q,self.a);s=raw['shares'];p=s['gate'].predict(s['space'].transform(self.frame.iloc[q]),p,e)
        if pack['corrector'] is not None:
            complete=np.isfinite(self.frame.iloc[q][REDUCTIONS['R3']].to_numpy(float)).all(axis=1)
            p=p+pack['strength']*complete*pack['corrector'].delta(self.frame.iloc[q])
        return p


def fast_local(local,q,a):
    tr=np.asarray(local['train_positions']);q=np.asarray(q);assert not set(tr)&set(q)
    if len(tr)<3:return np.full(len(q),np.mean(local['targets']))
    x=local['representation'].transform(a['features197'])
    return predict_local_ridge(x,a['a']['distance'],a['a']['train_global'][tr],a['a']['train_global'][q],local['targets'])


def fast_role(pack,q,a):
    p=fast_local(pack['local'],q,a)
    if pack['amplitude']:p+=pack['amplitude']*pack['corrector'].predict(a['role_frame'].iloc[q])
    return p


class FastRoleFactory(RoleFactory):
    def local_predictions(self,tr,query,variant):
        key=(tuple(tr),tuple(query),tuple(self.assets['variants'][variant]['columns']))
        if key not in self.pred_cache:self.pred_cache[key]=fast_local(self.base(tr,variant),query,self.assets)
        return self.pred_cache[key]
    def fit(self,tr,variant,cv=None):
        # Same RoleFactory fit, keeping transient inner models in memory instead
        # of repeatedly serializing them; final external models remain saved.
        tr=np.asarray(tr);cv=self.cv(tr) if cv is None else cv
        spec=self.assets['variants'][variant];inside=[];fallback=''
        try:
            for c,d in cv:
                aa=tr[c];bb=tr[d];deep=self.cv(aa)
                if any(len(aa[e])<3 for e,f in deep):raise ValueError('Fewer than three local training parcels')
                residual=self.assets['y'][aa]-self.local_oof(aa,deep,variant)
                bp=self.local_predictions(aa,bb,variant);inside.append((aa,bb,d,residual,bp))
        except ValueError as exc:
            if 'Insufficient groups' not in str(exc) and 'Fewer than three' not in str(exc):raise
            fallback=str(exc)
        local=self.base(tr,variant)
        if fallback:return dict(local=local,corrector=None,amplitude=0.,selection={},fallback=fallback,train_positions=tr)
        baseline=np.full(len(tr),np.nan)
        for aa,bb,d,res,bp in inside:baseline[d]=bp
        candidates=[dict(params=None,amplitude=0.,rmse=float(np.sqrt(np.mean((baseline-self.assets['y'][tr])**2))))]
        prepared=[]
        for aa,bb,d,res,bp in inside:
            rep=CorrectionSpace(tuple(spec.get('correction_columns',[])),tuple(spec.get('correction_atoms',[])),self.assets['physical_definitions']).fit(self.assets['role_frame'].iloc[aa])
            prepared.append((d,res,rep.transform(self.assets['role_frame'].iloc[aa]),rep.transform(self.assets['role_frame'].iloc[bb])))
        for params in GRID:
            delta=np.full(len(tr),np.nan)
            for d,res,z,q in prepared:delta[d]=ElasticNet(**params,max_iter=200000,random_state=2026).fit(z,res).predict(q)
            for amp in AMPLITUDES[1:]:candidates.append(dict(params=params,amplitude=amp,rmse=float(np.sqrt(np.mean((baseline+amp*delta-self.assets['y'][tr])**2)))))
        best=min(candidates,key=lambda r:(round(r['rmse'],12),r['amplitude'],-r['params']['alpha'] if r['params'] else 0,r['params']['l1_ratio'] if r['params'] else 0))
        model=role_corrector(spec,best['params'],self.assets).fit(self.assets['role_frame'].iloc[tr],self.assets['y'][tr]-baseline) if best['amplitude'] else None
        return dict(local=local,corrector=model,amplitude=best['amplitude'],selection=best,fallback='',train_positions=tr)


class FastBases(ColdBases):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.role=FastRoleFactory(self.a,self.protocol,self.groups,self.directory/'role',self.reference)
        self.expert_memo={}
    def expert(self,tr,cv=None):
        key=(tuple(tr),None if cv is None else tuple((tuple(a),tuple(b)) for a,b in cv))
        if key not in self.expert_memo:self.expert_memo[key]=super().expert(tr,cv)
        return self.expert_memo[key]
    def route_oof(self,tr,cv=None):
        tr=np.asarray(tr);cv=self.cv(tr) if cv is None else cv;key=tuple(tr)
        if key in self.routes:return self.routes[key]
        ct=np.full(len(tr),np.nan);ep=ct.copy()
        for c,d in cv:
            fit=tr[c];held=tr[d];assert not set(fit)&set(held)
            ct[d]=self.ct3(fit).predict(self.a['a']['train'].iloc[held]);ep[d]=fast_role(self.expert(fit),held,self.a)
            self.ledger.append(dict(train=fit.tolist(),held=held.tolist(),kind='component_crossfit'))
        assert np.isfinite(ct).all() and np.isfinite(ep).all();self.routes[key]=(ct,ep);return ct,ep


class FastReferenceOnly(ReferenceOnly):
    helper_type=FastBases
    predict_expert=staticmethod(fast_role)
