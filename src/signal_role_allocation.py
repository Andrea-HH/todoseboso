"""Nested role allocation with train-only representations and frozen local recipe."""
from pathlib import Path
import hashlib
import numpy as np
import joblib
from sklearn.pipeline import Pipeline
from sklearn.linear_model import ElasticNet
from sklearn.base import BaseEstimator,TransformerMixin
from src.geoc_signal_research import SignalFactory,SignalRepresentation,predict_base
from src.geoc_reverse import GRID,AMPLITUDES
from src.ct3_residual_conditional.models import CORE
from src.family_4.conditional_response import ConditionalFeatures
from src.physical_similarity import BlockRepresentation
from src.physical_representation import PhysicalRepresentation


class RoleSpace:
    def __init__(self,atoms,columns,definitions):self.atoms=list(atoms);self.columns=list(columns);self.definitions=definitions
    def fit(self,frame):
        self.models=[]
        for atom in self.atoms:
            spec=self.definitions[atom]
            m=BlockRepresentation(spec['columns'],1).fit(frame) if atom=='soil_texture_phase' else PhysicalRepresentation(**spec,mode='summary',components=0).fit(frame)
            self.models.append((atom,m))
        self.signal=SignalRepresentation(self.columns,'raw').fit(frame) if self.columns else None
        if self.signal:
            z=self.signal.transform(frame);self.norm=max(float(np.sqrt(np.mean(np.sum(z*z,axis=1)))),1e-8)
        return self
    def transform(self,frame):
        parts=[]
        for atom,m in self.models:
            parts.append((m._matrix(frame)-m.mean_)/np.sqrt(len(m.columns)) if atom=='soil_texture_phase' else m.transform(frame))
        if self.signal:parts.append(self.signal.transform(frame)/self.norm)
        return np.column_stack(parts)/np.sqrt(len(parts)) if parts else np.zeros((len(frame),1))


class CorrectionSpace(BaseEstimator,TransformerMixin):
    def __init__(self,columns,atoms,definitions):self.columns=columns;self.atoms=atoms;self.definitions=definitions
    def fit(self,X,y=None):
        self.core=ConditionalFeatures(tuple(CORE)+tuple(self.columns)).fit(X)
        self.physical=RoleSpace(self.atoms,[],self.definitions).fit(X) if self.atoms else None
        return self
    def transform(self,X):
        a=self.core.transform(X)
        return np.column_stack([a,self.physical.transform(X)]) if self.physical else a


def role_corrector(spec,params,assets):
    return Pipeline([('repr',CorrectionSpace(tuple(spec.get('correction_columns',[])),tuple(spec.get('correction_atoms',[])),assets['physical_definitions'])),('model',ElasticNet(**params,max_iter=200000,random_state=2026))])


def predict_role(pack,query,assets):
    p=predict_base(pack['local'],query,assets)
    if pack['amplitude']:p+=pack['amplitude']*pack['corrector'].predict(assets['role_frame'].iloc[query])
    return p


class RoleFactory(SignalFactory):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.pred_cache={}
    def local_predictions(self,tr,query,variant):
        spec=self.assets['variants'][variant];key=(tuple(tr),tuple(query),tuple(spec['columns']))
        if key not in self.pred_cache:self.pred_cache[key]=predict_base(self.base(tr,variant),query,self.assets)
        return self.pred_cache[key]
    def local_oof(self,tr,cv,variant):
        p=np.full(len(tr),np.nan)
        for c,d in cv:
            aa=tr[c];bb=tr[d];p[d]=self.local_predictions(aa,bb,variant);self.ledger.append(dict(train=aa.tolist(),held=bb.tolist(),kind='local'))
        assert np.isfinite(p).all();return p
    def fit(self,tr,variant,cv=None):
        tr=np.asarray(tr);cv=self.cv(tr) if cv is None else cv
        signature=hashlib.sha256(repr((tuple(tr),variant,tuple((tuple(c),tuple(d)) for c,d in cv))).encode()).hexdigest();path=self.directory/(signature+'.joblib')
        if path.exists():return joblib.load(path)
        spec=self.assets['variants'][variant];legacy=spec.get('legacy_variant')
        if legacy:
            oldkey=hashlib.sha256(repr((tuple(tr),legacy,tuple((tuple(c),tuple(d)) for c,d in cv))).encode()).hexdigest();old=self.reference_directory/(oldkey+'.joblib')
            if old.exists():
                pack=joblib.load(old);assert np.array_equal(pack['train_positions'],tr) and np.array_equal(pack['local']['targets'],self.assets['y'][tr]);pack['source_reference']=str(old)
                # Local variant can remain the frozen legacy name: its representation is serialized.
                joblib.dump(pack,path,compress=3);return pack
        inside=[];fallback=''
        try:
            for c,d in cv:
                aa=tr[c];bb=tr[d];deep=self.cv(aa)
                if any(len(aa[e])<3 for e,f in deep):raise ValueError('Fewer than three local training parcels')
                residual=self.assets['y'][aa]-self.local_oof(aa,deep,variant);bp=self.local_predictions(aa,bb,variant);inside.append((aa,bb,d,residual,bp))
        except ValueError as exc:
            if 'Insufficient groups' not in str(exc) and 'Fewer than three' not in str(exc):raise
            fallback=str(exc)
        local=self.base(tr,variant)
        if fallback:pack=dict(local=local,corrector=None,amplitude=0.,selection={},fallback=fallback,train_positions=tr)
        else:
            baseline=np.full(len(tr),np.nan)
            for aa,bb,d,res,bp in inside:baseline[d]=bp
            candidates=[dict(params=None,amplitude=0.,rmse=float(np.sqrt(np.mean((baseline-self.assets['y'][tr])**2))))]
            prepared=[]
            for aa,bb,d,res,bp in inside:
                rep=CorrectionSpace(tuple(spec.get('correction_columns',[])),tuple(spec.get('correction_atoms',[])),self.assets['physical_definitions']).fit(self.assets['role_frame'].iloc[aa]);prepared.append((d,res,rep.transform(self.assets['role_frame'].iloc[aa]),rep.transform(self.assets['role_frame'].iloc[bb])))
            for params in GRID:
                delta=np.full(len(tr),np.nan)
                for d,res,z,q in prepared:delta[d]=ElasticNet(**params,max_iter=200000,random_state=2026).fit(z,res).predict(q)
                for amp in AMPLITUDES[1:]:candidates.append(dict(params=params,amplitude=amp,rmse=float(np.sqrt(np.mean((baseline+amp*delta-self.assets['y'][tr])**2)))))
            best=min(candidates,key=lambda r:(round(r['rmse'],12),r['amplitude'],-r['params']['alpha'] if r['params'] else 0,r['params']['l1_ratio'] if r['params'] else 0));model=role_corrector(spec,best['params'],self.assets).fit(self.assets['role_frame'].iloc[tr],self.assets['y'][tr]-baseline) if best['amplitude'] else None
            pack=dict(local=local,corrector=model,amplitude=best['amplitude'],selection=best,fallback='',train_positions=tr)
        joblib.dump(pack,path,compress=3);return pack
    def oof(self,tr,cv=None,variant=None):
        tr=np.asarray(tr);cv=self.cv(tr) if cv is None else cv;p=np.full(len(tr),np.nan)
        for c,d in cv:
            aa=tr[c];bb=tr[d];pack=self.fit(aa,variant);p[d]=predict_role(pack,bb,self.assets);self.ledger.append(dict(train=aa.tolist(),held=bb.tolist(),kind='retuned_role_expert'))
        assert np.isfinite(p).all();return p
