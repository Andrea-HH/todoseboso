"""Nested, bounded mixtures of four frozen expert recipes; no regional rules."""
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd
import joblib
from scipy.optimize import minimize
from scipy.spatial.distance import cdist
from src.architecture_decomposition import load_assets,local_sets,OUT as ARCH
from src.base_distribution_correction import SimplifiedBases
from src.pruned_global_architecture import PrunedGlobalFactory
from src.neighbor_signal_contrasts import JOINT
from src.geoc_signal_research import predict_base,SignalRepresentation
from src.signal_role_allocation import predict_role
from src.geoc_bridge import local_prediction,OLD
from src.indicator_neighborhoods import OUT as INDICATORS,REDUCTIONS,ReducedCorrection

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/modeling/four_expert_combinations/v1'
NAMES=['CT3','L40','Compact14','Reference26'];ROUTES=['NO_PLANET_OFF_GLOBAL','FULL7_ON_RAW']

def constant_weight(y,left,right):
    d=np.asarray(right)-left;energy=float(d@d)
    return float(np.clip(d@(np.asarray(y)-left)/energy,0,1)) if energy>1e-12 else 0.

class ConvexThree:
    def fit(self,p,y):
        p=np.asarray(p,float);y=np.asarray(y,float);prior=np.array([0.,1.,0.]);scale=max(float(np.mean(np.var(p,axis=1))),1e-8);penalty=.1*scale
        def objective(w):return np.mean((p@w-y)**2)+penalty*np.sum((w-prior)**2)
        r=minimize(objective,prior,method='SLSQP',bounds=[(0.,1.)]*3,constraints=[{'type':'eq','fun':lambda w:w.sum()-1}],options={'ftol':1e-12,'maxiter':500})
        if not r.success:raise RuntimeError(r.message)
        self.weights=np.maximum(r.x,0);self.weights/=self.weights.sum();self.optimizer_message=r.message;return self
    def predict(self,p):return np.asarray(p)@self.weights

class ConditionalBlend:
    """Fixed strong ridge, then clipped convex weight; no external tuning."""
    def fit(self,z,y,left,right):
        z=np.asarray(z,float);self.median=np.array([np.median(v[np.isfinite(v)]) if np.isfinite(v).any() else 0. for v in z.T]);z=np.where(np.isfinite(z),z,self.median);self.mean=z.mean(axis=0);self.scale=np.maximum(z.std(axis=0),1e-8);a=np.column_stack([np.ones(len(z)),np.clip((z-self.mean)/self.scale,-4,4)]);d=np.asarray(right)-left;energy=float(d@d);self.constant=constant_weight(y,left,right);prior=np.r_[self.constant,np.zeros(z.shape[1])]
        if energy<1e-12:self.beta=prior;self.condition=1.;return self
        penalty=10.*energy*np.diag([.1]+[1.]*z.shape[1]);design=d[:,None]*a;matrix=design.T@design+penalty;self.beta=np.linalg.solve(matrix,design.T@(np.asarray(y)-left)+penalty@prior);self.condition=float(np.linalg.cond(matrix));return self
    def weights(self,z):
        z=np.asarray(z,float);a=np.column_stack([np.ones(len(z)),np.clip((np.where(np.isfinite(z),z,self.median)-self.mean)/self.scale,-4,4)]);return np.clip(a@self.beta,0,1)
    def predict(self,z,left,right):return np.asarray(left)+self.weights(z)*(np.asarray(right)-left)

class SupportFeatures:
    def __init__(self,a):self.a=a
    def fit(self,tr):
        self.tr=np.asarray(tr);self.pos=self.a['a']['train_global'];self.rep=SignalRepresentation(local_sets()['NO_PLANET']).fit(self.a['features197'].iloc[self.pos[self.tr]]);self.small=self.rep.transform(self.a['features197']);self.pca=self.a['a']['x'];self.y=self.a['y'][self.tr];return self
    def transform(self,q,p):
        q=np.asarray(q);dist=self.a['a']['distance'][np.ix_(self.pos[q],self.pos[self.tr])].copy();dist[q[:,None]==self.tr[None,:]]=np.inf;order=np.argsort(dist,axis=1,kind='stable')[:,:min(24,len(self.tr))];geo=np.take_along_axis(dist,order,axis=1);geo=np.mean(geo,axis=1);disp=np.std(self.y[order],axis=1)
        small=cdist(self.small[self.pos[q]],self.small[self.pos[self.tr]])/np.sqrt(self.small.shape[1]);pc=cdist(self.pca[self.pos[q]],self.pca[self.pos[self.tr]])/np.sqrt(self.pca.shape[1]);same=q[:,None]==self.tr[None,:];small[same]=np.inf;pc[same]=np.inf
        log=lambda x:np.log1p(np.maximum(x,0))
        return {'B5':np.column_stack([p[:,0],abs(p[:,3]-p[:,0]),log(geo),log(small.min(axis=1))]),'B6':np.column_stack([abs(p[:,1]-p[:,3]),log(geo),log(pc.min(axis=1)),disp])}

class ExpertFactory:
    """Rebuild exact expert recipes at every meta-training level."""
    def __init__(self,fi,protocol,tr,inner):
        self.fi=fi;self.a=load_assets();self.t=self.a['a']['train'];self.y=self.a['y'];self.x=pd.read_parquet(INDICATORS/'cache/features_train138_target_free.parquet');assert self.x.ID_POLIGONO.tolist()==self.t.ID_POLIGONO.tolist();groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO');self.directory=OUT/'cache'/f'{fi:02d}';self.directory.mkdir(parents=True,exist_ok=True)
        self.helper=SimplifiedBases(self.a,protocol,groups,self.directory,JOINT/'cache'/f'{fi:02d}');self.helper.original_outer_positions=np.asarray(tr);self.helper.original_outer_cv=inner;self.compact=PrunedGlobalFactory(self.a,'NO_PLANET',protocol,groups,self.directory/'compact',tr,inner);self.compact.helper=self.helper;self.raw_cache={};self.raw_models={};self.oof_cache={};self.full_models={};self.ledger=[];self.fallbacks=[]
        if fi<65:
            ck=joblib.load(ARCH/'checkpoints'/f'{fi:02d}.joblib');pack=joblib.load(ARCH/'models'/f'{fi:02d}.joblib');self.archived_outer=pack
            def seed(train,held,value):self.raw_cache[(tuple(train),tuple(held))]=np.asarray(value)
            for c,d in inner:seed(np.asarray(tr)[c],np.asarray(tr)[d],np.column_stack([pack['adjustments'][r]['base_oof'][d] for r in ROUTES]))
            for ctx in ck['contexts']:
                aa=ctx['aa'];self.oof_cache[tuple(aa)]=np.column_stack([ctx['base_oof'][r] for r in ROUTES])
                for c,d in self.cv(aa):seed(aa[c],aa[d],self.oof_cache[tuple(aa)][d])
            self.oof_cache[tuple(tr)]=np.column_stack([pack['adjustments'][r]['base_oof'] for r in ROUTES])
    def cv(self,tr):return self.helper.cv(np.asarray(tr))
    def raw_fit(self,tr):
        tr=np.asarray(tr);key=tuple(tr)
        if key in self.raw_models:return self.raw_models[key]
        ct=self.helper.ct3(tr);shares=self.helper.shares(tr);expert=self.helper.expert(tr) if shares is not None else None;compact=self.compact.fit(tr);p=dict(ct3=ct,shares=shares,expert=expert,compact=compact,train_positions=tr);self.raw_models[key]=p;return p
    def raw_predict(self,tr,q):
        tr=np.asarray(tr);q=np.asarray(q);assert not set(tr)&set(q);key=(tuple(tr),tuple(q))
        if key not in self.raw_cache:
            p=self.raw_fit(tr);ct=p['ct3'].predict(self.t.iloc[q]);r=ct.copy()
            if p['shares'] is not None:
                ep=predict_role(p['expert'],q,self.a);s=p['shares'];r=s['gate'].predict(s['space'].transform(self.a['role_frame'].iloc[q]),ct,ep)
            self.raw_cache[key]=np.column_stack([self.compact.predict(p['compact'],q),r])
        self.ledger.append(dict(kind='raw',train=tr.tolist(),held=q.tolist()));return self.raw_cache[key]
    def raw_oof(self,tr):
        tr=np.asarray(tr);key=tuple(tr)
        if key not in self.oof_cache:
            oof=np.full((len(tr),2),np.nan)
            for c,d in self.cv(tr):oof[d]=self.raw_predict(tr[c],tr[d])
            assert np.isfinite(oof).all();self.oof_cache[key]=oof
        return self.oof_cache[key]
    def full_fit(self,tr):
        tr=np.asarray(tr);key=tuple(tr)
        if key in self.full_models:return self.full_models[key]
        path=self.directory/('experts_'+hashlib.sha256(repr(key).encode()).hexdigest()+'.joblib')
        if path.exists():p=joblib.load(path);np.testing.assert_array_equal(p['train_positions'],tr);self.full_models[key]=p;return p
        raw=self.raw_fit(tr)
        try:cv=self.cv(tr)
        except ValueError:
            p=dict(raw=raw,correctors=[None,None],strengths=[0.,0.],train_positions=tr,candidates=[],fallback='Insufficient groups; R3 disabled');self.fallbacks.append(p['fallback']);self.full_models[key]=p;return p
        oof=self.raw_oof(tr);delta=np.full_like(oof,np.nan)
        for c,d in cv:
            aa=tr[c];bb=tr[d]
            try:deep=self.raw_oof(aa)
            except ValueError:delta[d]=0.;self.fallbacks.append('Insufficient deep groups; R3 calibration delta zero');continue
            for j in range(2):
                correction=ReducedCorrection('R3').fit(self.x.iloc[aa],self.y[aa]-deep[:,j]);delta[d,j]=correction.delta(self.x.iloc[bb])*np.isfinite(self.x.iloc[bb][REDUCTIONS['R3']].to_numpy(float)).all(axis=1)
        correctors=[];strengths=[];candidates=[]
        for j in range(2):
            scores=[dict(strength=s,rmse=float(np.sqrt(np.mean((oof[:,j]+s*delta[:,j]-self.y[tr])**2)))) for s in [0.,.5,1.]];strengths.append(min(scores,key=lambda v:(round(v['rmse'],12),v['strength']))['strength']);correctors.append(ReducedCorrection('R3').fit(self.x.iloc[tr],self.y[tr]-oof[:,j]));candidates.append(scores)
        p=dict(raw=raw,correctors=correctors,strengths=strengths,train_positions=tr,candidates=candidates,fallback='');joblib.dump(p,path,compress=3);self.full_models[key]=p;return p
    def predict(self,p,q):
        q=np.asarray(q);tr=p['train_positions'];assert not set(tr)&set(q);ct=p['raw']['ct3'].predict(self.t.iloc[q]);a=self.a['a'];loc=local_prediction(a['x'],a['distance'],a['train_global'][tr],a['train_global'][q],self.y[tr]);raw=self.raw_predict(tr,q).copy();complete=np.isfinite(self.x.iloc[q][REDUCTIONS['R3']].to_numpy(float)).all(axis=1)
        for j in range(2):
            if p['correctors'][j] is not None:raw[:,j]+=p['strengths'][j]*complete*p['correctors'][j].delta(self.x.iloc[q])
        self.ledger.append(dict(kind='full_experts',train=tr.tolist(),held=q.tolist()));return np.column_stack([ct,loc,raw])

def fit_combinations(p,z,y):
    c,l,m,r=p.T;models={n:constant_weight(y,left,right) for n,left,right in [('B1',c,r),('B2',c,m),('B3',r,l)]};models['B4']=ConvexThree().fit(p[:,[0,3,1]],y);models['B5']=ConditionalBlend().fit(z['B5'],y,c,r);models['B6']=ConditionalBlend().fit(z['B6'],y,r,l);return models

def predict_combinations(models,p,z):
    c,l,m,r=p.T;out={'B1':c+models['B1']*(r-c),'B2':c+models['B2']*(m-c),'B3':r+models['B3']*(l-r),'B4':models['B4'].predict(p[:,[0,3,1]]),'B5':models['B5'].predict(z['B5'],c,r),'B6':models['B6'].predict(z['B6'],r,l)};weights={'B1':np.full(len(p),models['B1']),'B2':np.full(len(p),models['B2']),'B3':np.full(len(p),models['B3']),'B5':models['B5'].weights(z['B5']),'B6':models['B6'].weights(z['B6'])};return out,weights
