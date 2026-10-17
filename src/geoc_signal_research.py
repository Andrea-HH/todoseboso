"""Frozen-family ablations and inductive small representations over GeoC signals."""
from pathlib import Path
import hashlib
import numpy as np
import joblib
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from src.geoc_bridge import local_prediction
from src.geoc_reverse import correction_model,GRID,AMPLITUDES
from src.family_8.research import subcv
from src.conditional_local_phases import global_weight


class SignalRepresentation:
    def __init__(self,columns,mode='raw'):self.columns=list(columns);self.mode=mode
    def fit(self,frame):
        if set(self.columns)&{'ID_POLIGONO','RENDIMIENTO_T_HA','Estado','Municipio'}:raise ValueError('Target/ID in signal representation')
        x=frame[self.columns].to_numpy(float);self.medians_=np.array([np.median(v[np.isfinite(v)]) if np.isfinite(v).any() else 0. for v in x.T]);x=np.where(np.isfinite(x),x,self.medians_);self.mean_=x.mean(axis=0);self.scale_=x.std(axis=0);self.support_=self.scale_>1e-10;self.scale_[~self.support_]=1.;z=((x-self.mean_)/self.scale_)[:,self.support_];self.pca_=None;self.score_scale_=None
        if self.mode!='raw' and z.shape[1]:
            singular=np.linalg.svd(z,compute_uv=False);rank=int(np.sum(singular>max(singular[0]*1e-10,1e-12)));k=min(int(self.mode[3:]),z.shape[1],len(z)-1,max(rank,1));self.pca_=PCA(n_components=k,svd_solver='full').fit(z);z=self.pca_.transform(z);self.score_scale_=StandardScaler().fit(z)
        self.dimension_=z.shape[1] if z.shape[1] else 1;return self
    def transform(self,frame):
        x=frame[self.columns].to_numpy(float);x=np.where(np.isfinite(x),x,self.medians_);z=((x-self.mean_)/self.scale_)[:,self.support_]
        if not z.shape[1]:return np.zeros((len(frame),1))
        return self.score_scale_.transform(self.pca_.transform(z)) if self.pca_ is not None else z


def predict_base(local,query,assets):
    tr=local['train_positions'];query=np.asarray(query);assert not set(tr)&set(query)
    if len(tr)<3:return np.full(len(query),np.mean(local['targets']))
    if local['representation'] is None:x=assets['static'][local['variant']]
    else:x=local['representation'].transform(assets['features197'])
    a=assets['a'];return local_prediction(x,a['distance'],a['train_global'][tr],a['train_global'][query],local['targets'])


def predict_expert(pack,query,assets):
    pred=predict_base(pack['local'],query,assets)
    if pack['amplitude']:pred=pred+pack['amplitude']*pack['corrector'].predict(assets['core'].iloc[query])
    return pred


class SignalFactory:
    """Same compact-corrector selection, with a representation fit per local training."""
    def __init__(self,assets,protocol,groups,directory,reference_directory):
        self.assets=assets;self.protocol=protocol;self.groups=groups;self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True);self.reference_directory=Path(reference_directory);self.base_cache={};self.ledger=[]
    def cv(self,tr):return subcv(self.assets['a']['train'],np.asarray(tr),self.protocol,self.groups)
    def base(self,tr,variant):
        tr=np.asarray(tr);key=(tuple(tr),variant)
        if key not in self.base_cache:
            spec=self.assets['variants'][variant];rep=None
            if spec['type'] in ['small','inductive_control']:rep=SignalRepresentation(spec['columns'],spec['mode']).fit(self.assets['features197'].iloc[self.assets['a']['train_global'][tr]])
            self.base_cache[key]=dict(variant=variant,train_positions=tr,targets=self.assets['y'][tr].copy(),representation=rep)
        return self.base_cache[key]
    def local_oof(self,tr,cv,variant):
        p=np.full(len(tr),np.nan)
        for c,d in cv:
            aa=tr[c];bb=tr[d];p[d]=predict_base(self.base(aa,variant),bb,self.assets);self.ledger.append(dict(train=aa.tolist(),held=bb.tolist(),kind='local'))
        assert np.isfinite(p).all();return p
    def fit(self,tr,variant='FULL',cv=None):
        tr=np.asarray(tr);cv=self.cv(tr) if cv is None else cv;signature=hashlib.sha256(repr((tuple(tr),variant,tuple((tuple(c),tuple(d)) for c,d in cv))).encode()).hexdigest();path=self.directory/(signature+'.joblib')
        if path.exists():return joblib.load(path)
        if variant=='FULL':
            oldkey=hashlib.sha256(repr((tuple(tr),'ORIGINAL',24,tuple((tuple(c),tuple(d)) for c,d in cv))).encode()).hexdigest();old=self.reference_directory/(oldkey+'.joblib')
            if old.exists():
                p=joblib.load(old);assert np.array_equal(p['train_positions'],tr);pack=dict(local=self.base(tr,variant),corrector=p['corrector'],amplitude=p['amplitude'],selection=p['selection'],fallback=p['fallback'],train_positions=tr,source_reference=str(old));joblib.dump(pack,path,compress=3);return pack
        inside=[];fallback=''
        try:
            for c,d in cv:
                aa=tr[c];bb=tr[d];deep=self.cv(aa)
                if any(len(aa[e])<3 for e,f in deep):raise ValueError('Fewer than three local training parcels')
                residual=self.assets['y'][aa]-self.local_oof(aa,deep,variant);bp=predict_base(self.base(aa,variant),bb,self.assets);inside.append((aa,bb,d,residual,bp))
        except ValueError as exc:
            if 'Insufficient groups' not in str(exc) and 'Fewer than three' not in str(exc):raise
            fallback=str(exc)
        base=self.base(tr,variant)
        if fallback:pack=dict(local=base,corrector=None,amplitude=0.,selection=dict(params=None,amplitude=0.,rmse=np.nan),fallback=fallback,train_positions=tr)
        else:
            baseline=np.full(len(tr),np.nan)
            for aa,bb,where,res,bp in inside:baseline[where]=bp
            candidates=[dict(params=None,amplitude=0.,rmse=float(np.sqrt(np.mean((baseline-self.assets['y'][tr])**2))))]
            for params in GRID:
                delta=np.full(len(tr),np.nan)
                for aa,bb,where,res,bp in inside:delta[where]=correction_model(params).fit(self.assets['core'].iloc[aa],res).predict(self.assets['core'].iloc[bb])
                for amp in AMPLITUDES[1:]:candidates.append(dict(params=params,amplitude=amp,rmse=float(np.sqrt(np.mean((baseline+amp*delta-self.assets['y'][tr])**2)))))
            best=min(candidates,key=lambda r:(round(r['rmse'],12),r['amplitude'],-r['params']['alpha'] if r['params'] else 0,r['params']['l1_ratio'] if r['params'] else 0));m=correction_model(best['params']).fit(self.assets['core'].iloc[tr],self.assets['y'][tr]-baseline) if best['amplitude'] else None
            pack=dict(local=base,corrector=m,amplitude=best['amplitude'],selection=best,fallback='',train_positions=tr)
        joblib.dump(pack,path,compress=3);return pack
    def oof(self,tr,cv=None,variant='FULL'):
        tr=np.asarray(tr);cv=self.cv(tr) if cv is None else cv;p=np.full(len(tr),np.nan)
        for c,d in cv:
            aa=tr[c];bb=tr[d];pack=self.fit(aa,variant);p[d]=predict_expert(pack,bb,self.assets);self.ledger.append(dict(train=aa.tolist(),held=bb.tolist(),kind='expert'))
        assert np.isfinite(p).all();return p


class CategoryGate:
    def fit(self,categories,y,ct,expert):
        self.global_=global_weight(y,ct,expert);delta=expert-ct;prior=20*float(np.mean(delta**2));self.values_={}
        for value in np.unique(categories):
            ix=categories==value;den=float(delta[ix]@delta[ix])+prior;self.values_[value]=float(np.clip((delta[ix]@(y[ix]-ct[ix])+prior*self.global_)/den,0,1)) if den>1e-12 else self.global_
        return self
    def weights(self,categories):return np.array([self.values_.get(v,self.global_) for v in categories])
    def predict(self,categories,ct,expert):return ct+self.weights(categories)*(expert-ct)


class CategoryCorrection:
    def fit(self,categories,residual):
        r=np.asarray(residual)-np.mean(residual);self.values_={v:float(r[categories==v].sum()/(np.sum(categories==v)+20)) for v in np.unique(categories)};center=float(np.mean([self.values_[v] for v in categories]));self.values_={v:x-center for v,x in self.values_.items()};return self
    def predict(self,categories):return np.array([self.values_.get(v,0.) for v in categories])
