"""Three controlled lines over the frozen nonclimatic Local + compact EN pipeline."""
from pathlib import Path
import hashlib,json
import numpy as np
import joblib
from scipy.spatial.distance import cdist
from sklearn.linear_model import Ridge
from sklearn.cluster import KMeans
from src.geoc_bridge import local_prediction
from src.geoc_reverse import correction_model,GRID,AMPLITUDES
from src.family_8.research import subcv
from src.physical_representation import PhysicalRepresentation
from src.physical_similarity import BlockRepresentation

SPACES={'TEXTURE':['soil_texture_phase'],'GEOLOGY':['geologic_composition','geologic_distances'],'BOTH':['soil_texture_phase','geologic_composition','geologic_distances']}


class PhysicalSpace:
    def __init__(self,name,definitions):self.name=name;self.definitions=definitions
    def fit(self,frame):
        self.models=[]
        for atom in SPACES[self.name]:
            spec=self.definitions[atom]
            if atom=='soil_texture_phase':
                m=BlockRepresentation(spec['columns'],1).fit(frame)
                # Categorical mismatch geometry; do not inflate rare class columns.
                self.models.append((atom,m))
            else:self.models.append((atom,PhysicalRepresentation(**spec,mode='summary',components=0).fit(frame)))
        return self
    def transform(self,frame):
        parts=[]
        for atom,m in self.models:
            if atom=='soil_texture_phase':z=(m._matrix(frame)-m.mean_)/np.sqrt(len(m.columns))
            else:z=m.transform(frame)
            parts.append(z)
        return np.column_stack(parts)/np.sqrt(len(parts))


def support_scale(z):
    if len(z)<2:return 1.
    d=cdist(z,z);np.fill_diagonal(d,np.inf);near=d.min(axis=1);positive=near[(near>1e-8)&np.isfinite(near)]
    return float(np.median(positive)) if len(positive) else 1.


def physical_distance(space,train,query,frame):
    z=space.transform(frame.iloc[train]);q=space.transform(frame.iloc[query]);return cdist(q,z)/support_scale(z)


def local_model(assets,tr,variant,k):
    name,_,mix=variant.partition(':');pack=dict(train_positions=np.asarray(tr),variant=variant,k=k,targets=assets['y'][tr].copy(),space=None)
    if name not in ['ORIGINAL','GEOGRAPHY']:
        pack['space']=PhysicalSpace(name,assets['definitions']).fit(assets['features'].iloc[tr])
    return pack


def predict_local(pack,query,assets):
    tr=pack['train_positions'];query=np.asarray(query);assert not set(tr)&set(query)
    if pack['variant']=='ORIGINAL':
        if len(tr)<3:return np.full(len(query),np.mean(pack['targets']))
        a=assets['a'];return local_prediction(a['x'],a['distance'],a['train_global'][tr],a['train_global'][query],pack['targets'])
    name,_,mix=pack['variant'].partition(':');geo=assets['geo'][np.ix_(query,tr)]
    train_geo=assets['geo'][np.ix_(tr,tr)].copy();np.fill_diagonal(train_geo,np.inf);scale=np.median(train_geo.min(axis=1));geo=geo/max(float(scale),1e-8)
    if name=='GEOGRAPHY':d=geo
    else:
        physical=physical_distance(pack['space'],tr,query,assets['features']);d=physical if mix=='physical' else .5*physical+.5*geo
    out=[];x=assets['scores']
    for j,q in enumerate(query):
        threshold=np.partition(d[j],min(pack['k'],len(tr))-1)[min(pack['k'],len(tr))-1];use=np.flatnonzero(d[j]<=threshold+1e-12);w=1/(d[j,use]+.25);w*=len(use)/w.sum()
        m=Ridge(alpha=30.,solver='svd').fit(x[tr[use]],pack['targets'][use],sample_weight=w);out.append(m.predict(x[[q]])[0])
    return np.asarray(out)


def predict_leader(pack,query,assets):
    p=predict_local(pack['local'],query,assets)
    if pack['amplitude']:p=p+pack['amplitude']*pack['corrector'].predict(assets['core'].iloc[query])
    return p


class LeaderFactory:
    def __init__(self,assets,protocol,groups,directory):
        self.assets=assets;self.protocol=protocol;self.groups=groups;self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True);self.local_cache={};self.ledger=[];self.fallbacks=[]
    def cv(self,tr):return subcv(self.assets['a']['train'],np.asarray(tr),self.protocol,self.groups)
    def local_oof(self,tr,cv,variant,k):
        key=(tuple(tr),tuple((tuple(a),tuple(b)) for a,b in cv),variant,k)
        if key in self.local_cache:return self.local_cache[key]
        pred=np.full(len(tr),np.nan)
        for c,d in cv:
            aa=np.asarray(tr)[c];bb=np.asarray(tr)[d];p=local_model(self.assets,aa,variant,k);pred[d]=predict_local(p,bb,self.assets);self.ledger.append(dict(train=aa.tolist(),held=bb.tolist(),kind='fixed_local'))
        assert np.isfinite(pred).all();self.local_cache[key]=pred;return pred
    def fit(self,tr,variant='ORIGINAL',k=24,cv=None):
        tr=np.asarray(tr);cv=self.cv(tr) if cv is None else cv
        signature=hashlib.sha256(repr((tuple(tr),variant,k,tuple((tuple(c),tuple(d)) for c,d in cv))).encode()).hexdigest();path=self.directory/(signature+'.joblib')
        if path.exists():return joblib.load(path)
        inside=[];fallback=''
        try:
            for c,d in cv:
                aa=tr[c];bb=tr[d];deep=self.cv(aa)
                if any(len(aa[e])<3 for e,f in deep):raise ValueError('Fewer than three local training parcels')
                residual=self.assets['y'][aa]-self.local_oof(aa,deep,variant,k);bp=predict_local(local_model(self.assets,aa,variant,k),bb,self.assets);inside.append((aa,bb,d,residual,bp))
        except ValueError as exc:
            if 'Insufficient groups' not in str(exc) and 'Fewer than three' not in str(exc):raise
            fallback=str(exc)
        base=local_model(self.assets,tr,variant,k)
        if fallback:
            pack=dict(local=base,corrector=None,amplitude=0.,selection=dict(params=None,amplitude=0.,rmse=np.nan),fallback=fallback,train_positions=tr);self.fallbacks.append(dict(train=tr.tolist(),variant=variant,k=k,reason=fallback))
        else:
            baseline=np.full(len(tr),np.nan)
            for aa,bb,where,res,bp in inside:baseline[where]=bp
            candidates=[dict(params=None,amplitude=0.,rmse=float(np.sqrt(np.mean((baseline-self.assets['y'][tr])**2))))]
            for params in GRID:
                delta=np.full(len(tr),np.nan)
                for aa,bb,where,res,bp in inside:delta[where]=correction_model(params).fit(self.assets['core'].iloc[aa],res).predict(self.assets['core'].iloc[bb])
                for amp in AMPLITUDES[1:]:candidates.append(dict(params=params,amplitude=amp,rmse=float(np.sqrt(np.mean((baseline+amp*delta-self.assets['y'][tr])**2)))))
            best=min(candidates,key=lambda r:(round(r['rmse'],12),r['amplitude'],-r['params']['alpha'] if r['params'] else 0,r['params']['l1_ratio'] if r['params'] else 0));m=None
            if best['amplitude']:m=correction_model(best['params']).fit(self.assets['core'].iloc[tr],self.assets['y'][tr]-baseline)
            pack=dict(local=base,corrector=m,amplitude=best['amplitude'],selection=best,fallback='',train_positions=tr)
        joblib.dump(pack,path,compress=3);return pack
    def oof(self,tr,cv=None,variant='ORIGINAL',k=24):
        tr=np.asarray(tr);cv=self.cv(tr) if cv is None else cv;pred=np.full(len(tr),np.nan)
        for c,d in cv:
            aa=tr[c];bb=tr[d];pack=self.fit(aa,variant,k);assert not set(pack['train_positions'])&set(bb);pred[d]=predict_leader(pack,bb,self.assets);self.ledger.append(dict(train=aa.tolist(),held=bb.tolist(),kind='fully_tuned_leader'))
        assert np.isfinite(pred).all();return pred


def global_weight(y,ct,leader):
    delta=leader-ct;den=float(delta@delta)
    return float(np.clip(delta@(y-ct)/den,0,1)) if den>1e-12 else 0.


class ExpertGate:
    def __init__(self,kind,param):self.kind=kind;self.param=param
    def fit(self,z,y,ct,leader):
        self.global_=global_weight(y,ct,leader);self.z_=z;self.scale_=support_scale(z)
        if self.kind=='clusters':
            k=min(self.param,len(np.unique(np.round(z,10),axis=0)));self.model_=KMeans(n_clusters=max(1,k),n_init=5,random_state=2026).fit(z);labels=self.model_.labels_;delta=leader-ct;prior=20*float(np.mean(delta**2));self.weights_=np.full(self.model_.n_clusters,self.global_)
            for label in range(self.model_.n_clusters):
                ix=labels==label;den=float(np.sum(delta[ix]**2))+prior
                self.weights_[label]=np.clip((delta[ix]@(y[ix]-ct[ix])+prior*self.global_)/den,0,1) if den>1e-12 else self.global_
        return self
    def weights(self,q):
        if self.kind=='clusters':return self.weights_[self.model_.predict(q)]
        if self.kind=='support':return self.global_/(1+self.param*cdist(q,self.z_).min(axis=1)/self.scale_)
        return np.full(len(q),self.global_)
    def predict(self,q,ct,leader):
        w=self.weights(q);assert np.all((w>=0)&(w<=1));return ct+w*(leader-ct)
