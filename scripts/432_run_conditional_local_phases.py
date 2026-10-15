"""Frozen three-phase nested exploration over Local nonclimatic + compact EN."""
from pathlib import Path
import sys,json,time,hashlib,warnings
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.geoc_bridge import data,OLD
from src.ct3_residual_conditional.models import CORE
from src.conditional_local_phases import SPACES,PhysicalSpace,LeaderFactory,predict_leader,predict_local,ExpertGate
from src.physical_similarity import ResidualCorrector,GRIDS,select_candidate
OUT=ROOT/'outputs/modeling/conditional_local_phases/v1'
REP=ROOT/'outputs/modeling/physical_representation/v1'
NC=ROOT/'outputs/modeling/nonclimatic_local/v1'
VARIANTS=['GEOGRAPHY']+[s+':'+m for s in SPACES for m in ['physical','mixed']]

def load_assets():
    a=data();rep=joblib.load(NC/'cache/representations.joblib');assert a['ids197']==rep['ids197'];a['x']=rep['scores']['nonclimatic'];t=a['train'];features=pd.read_parquet(REP/'cache/features138_target_free.parquet');assert features.ID_POLIGONO.tolist()==t.ID_POLIGONO.tolist();pos=a['train_global'];defs=json.loads((REP/'frozen_design.json').read_text())['atoms']
    return dict(a=a,y=t.RENDIMIENTO_T_HA.to_numpy(),core=t[CORE],features=features,definitions=defs,scores=a['x'][pos],geo=a['distance'][np.ix_(pos,pos)])

def prepare():
    if (OUT/'frozen_design.json').exists():raise FileExistsError('Preserve design')
    for p in ['cache','models','checkpoints','tables','audit','diagnostics']:(OUT/p).mkdir(parents=True,exist_ok=True)
    files=[Path(__file__),ROOT/'src/conditional_local_phases.py',ROOT/'src/physical_similarity.py',ROOT/'src/physical_representation.py',ROOT/'src/geoc_reverse.py',ROOT/'tests/test_conditional_local_phases.py',ROOT/'documentation/conditional_local_phases_design.md',REP/'frozen_design.json',REP/'cache/features138_target_free.parquet',NC/'cache/representations.joblib',NC/'tables/new_oof_predictions.parquet',OLD/'cache/execution_plan.joblib',OLD/'cache/frozen65_splits.joblib',OLD/'cache/groups.csv']+list((OLD/'base_cache').glob('*.joblib'))
    cfg=dict(phase1=dict(spaces=SPACES,global_gate=True,cluster_grid=[4,8],shrinkage_pseudo_n=20,support_grid=[0.,1.,3.],weight_bounds=[0.,1.]),phase2=dict(variants=VARIANTS,k_grid=[12,24,48],ridge_alpha=30.,weights='1/(distance+.25), normalized to sum to neighbor count; include all boundary ties; geographic control uses identical rule',distance='geographic and physical normalized by training nearest positive distance; mixed=.5 each',compact_corrector='same EN12 grid and amplitude0/.25/.5 as original; each k pipeline fully tuned inside each outer inner training; select k from complete honest internal OOF'),phase3=dict(spaces=SPACES,correctors=GRIDS,amplitudes=[0.,.25,.5],targets='Honest OOF errors of the entire original Local+compact EN, deep targets regenerated within inner training only'),fallback='For a leader training context unable to support grouped nested EN selection or fixed local >=3 parcels, retire compact EN and use fixed local only; never switch grouped to random; record every occurrence. For original local <3 training parcels, return training mean.',representation='Original leader retains archived transductive PCA20 on197X; physical spaces and distance normalizations refit on corresponding train; texture categorical onehot without rare-class variance scaling; geologic roots and standardized log structural distances; no admin/coords in physical spaces.',selection='Complete internal OOF MSE; ties grid order, then smaller correction amplitude; phase selectors use internal candidate scores, not external results.',evaluation='Same65 outer/frozen inner; exploratory follow-up informed by earlier folds, no independent confirmation; no GeoC97/41 in this phase; no final138 or PRED59.',recipes=26,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in dict.fromkeys(files)})
    (OUT/'frozen_design.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8');print('Frozen three phases:26 new recipes including three internal selectors')

def work(fi):
    checkpoint=OUT/'checkpoints'/f'{fi:02d}.joblib'
    if checkpoint.exists():return
    start=time.perf_counter();cfg=json.loads((OUT/'frozen_design.json').read_text());assets=load_assets();t=assets['a']['train'];y=assets['y'];plan=joblib.load(OLD/'cache/execution_plan.joblib')[fi];tr=np.asarray(plan['train_positions']);va=np.asarray(plan['validation_positions']);inner=joblib.load(OLD/'cache/frozen65_splits.joblib')[fi][5];pro=plan['protocol'];groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO');factory=LeaderFactory(assets,pro,groups,OUT/'cache'/f'{fi:02d}');key=dict(protocol=pro,repeat=plan['repeat'],fold=plan['fold']);rows=[];selections=[];tuning=[];pipelines={};context=[];lookup={int(v):i for i,v in enumerate(tr)};ct_oof=np.full(len(tr),np.nan)
    def base(k):return joblib.load(OLD/'base_cache'/f'{k}.joblib')
    ct3=base(plan['outer_base_key'])['model'];ct=ct3.predict(t.iloc[va]);base_ledger=[]
    with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        leader=factory.fit(tr,cv=inner);leader_pred=predict_leader(leader,va,assets)
        previous=pd.read_parquet(NC/'tables/new_oof_predictions.parquet');expected=previous[(previous.experiment=='NONCLIM_PLUS_COMPACT_EN')&(previous.protocol==pro)&(previous['repeat']==key['repeat'])&(previous.fold==key['fold'])].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy();parity=float(np.max(abs(expected-leader_pred)));assert parity<1e-12
        leader_oof=factory.oof(tr,cv=inner)
        for item in plan['inner']:
            aa=np.asarray(item['train_positions']);bb=np.asarray(item['validation_positions']);where=np.array([lookup[int(v)] for v in bb]);pack=base(item['base_key']);assert set(pack['registry']['train_ids'])==set(t.iloc[aa].ID_POLIGONO);cb=pack['model'].predict(t.iloc[bb]);ct_oof[where]=cb;mapping={int(v):i for i,v in enumerate(aa)};deepct=np.full(len(aa),np.nan);deepcv=[]
            for ctx in item['residual_contexts']:
                dd=np.asarray(ctx['held_positions']);pack=base(ctx['base_key']);excluded=set(t.iloc[np.r_[dd,bb,va]].ID_POLIGONO);assert not set(pack['registry']['train_ids'])&excluded;hold=np.array([mapping[int(v)] for v in dd]);fit=np.array([j for j in range(len(aa)) if j not in set(hold)]);deepct[hold]=pack['model'].predict(t.iloc[dd]);deepcv.append((fit,hold));base_ledger.append(dict(base_key=ctx['base_key'],excluded_ids=sorted(excluded),verified=True))
            deep_leader=factory.oof(aa,cv=deepcv);context.append(dict(aa=aa,bb=bb,where=where,ct_oof=deepct,leader_oof=deep_leader,ct=cb,leader=leader_oof[where]))
        assert np.isfinite(ct_oof).all()
        spaces={name:PhysicalSpace(name,assets['definitions']).fit(assets['features'].iloc[tr]) for name in SPACES};zz={n:s.transform(assets['features'].iloc[tr]) for n,s in spaces.items()};qq={n:s.transform(assets['features'].iloc[va]) for n,s in spaces.items()};inners=[]
        for ctx in context:
            models={n:PhysicalSpace(n,assets['definitions']).fit(assets['features'].iloc[ctx['aa']]) for n in SPACES};inners.append({n:(m.transform(assets['features'].iloc[ctx['aa']]),m.transform(assets['features'].iloc[ctx['bb']])) for n,m in models.items()})
        def record(name,phase,pred,selection,model):
            assert np.isfinite(pred).all();rows.extend(dict(**key,experiment=name,phase=phase,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(v)) for i,v in zip(va,pred));selections.append(dict(**key,experiment=name,phase=phase,**selection));pipelines[name]=model
        # Phase1: convex expert gates learned on nested OOF experts only.
        candidates=[]
        specs=[('GLOBAL','global',[0])]+[(s,kind,cfg['phase1']['cluster_grid'] if kind=='clusters' else cfg['phase1']['support_grid']) for s in SPACES for kind in ['clusters','support']]
        for space,kind,grid in specs:
            scores=[]
            for param in grid:
                pred=np.full(len(tr),np.nan)
                for ctx,rep in zip(context,inners):
                    z,q=rep[space] if space!='GLOBAL' else (np.zeros((len(ctx['aa']),1)),np.zeros((len(ctx['bb']),1)));gate=ExpertGate(kind,param).fit(z,y[ctx['aa']],ctx['ct_oof'],ctx['leader_oof']);pred[ctx['where']]=gate.predict(q,ctx['ct'],ctx['leader'])
                scores.append(dict(param=param,mse=float(np.mean((pred-y[tr])**2))))
            best=min(enumerate(scores),key=lambda v:(round(v[1]['mse'],12),v[0]))[1];z,q=(zz[space],qq[space]) if space!='GLOBAL' else (np.zeros((len(tr),1)),np.zeros((len(va),1)));gate=ExpertGate(kind,best['param']).fit(z,y[tr],ct_oof,leader_oof);pred=gate.predict(q,ct,leader_pred);name='P1_'+space+'_'+kind;rec=dict(kind=kind,space=space,params=json.dumps(best['param']),inner_rmse=float(np.sqrt(best['mse'])),global_weight=gate.global_);record(name,1,pred,rec,dict(type='gate',gate=gate,space=spaces.get(space),leader=leader));candidates.append((best['mse'],name,pred,rec));tuning.extend(dict(**key,experiment=name,**r) for r in scores)
        win=min(candidates,key=lambda v:(round(v[0],12),v[1]));record('P1_SELECTOR',1,win[2],dict(**win[3],selected_variant=win[1]),dict(type='alias',name=win[1]))
        # Phase2: choose k using internally tuned complete local+compact pipelines.
        candidates=[]
        for variant in VARIANTS:
            scores=[]
            for k in cfg['phase2']['k_grid']:
                pred=factory.oof(tr,cv=inner,variant=variant,k=k);scores.append(dict(k=k,mse=float(np.mean((pred-y[tr])**2))))
            best=min(scores,key=lambda v:(round(v['mse'],12),v['k']));pack=factory.fit(tr,variant,best['k'],cv=inner);pred=predict_leader(pack,va,assets);name='P2_'+variant.replace(':','_');rec=dict(kind='local_compact',space=variant,params=json.dumps(dict(k=best['k'],compact=pack['selection'])),inner_rmse=float(np.sqrt(best['mse'])),amplitude=pack['amplitude']);record(name,2,pred,rec,dict(type='leader',leader=pack));candidates.append((best['mse'],name,pred,rec));tuning.extend(dict(**key,experiment=name,**r) for r in scores)
        win=min(candidates,key=lambda v:(round(v[0],12),v[1]));record('P2_SELECTOR',2,win[2],dict(**win[3],selected_variant=win[1]),dict(type='alias',name=win[1]))
        # Phase3: residuals of the entire original leader, not of its base alone.
        candidates=[]
        for space in SPACES:
            for kind,grid in GRIDS.items():
                deltas=[]
                for params in grid:
                    delta=np.full(len(tr),np.nan)
                    for ctx,rep in zip(context,inners):
                        z,q=rep[space];m=ResidualCorrector(kind,params).fit(z,y[ctx['aa']]-ctx['leader_oof']);delta[ctx['where']]=m.predict(q)
                    deltas.append(delta)
                best,records=select_candidate(y[tr],leader_oof,deltas,grid);amp=best['amplitude'];m=ResidualCorrector(kind,best['params']).fit(zz[space],y[tr]-leader_oof) if amp else None;pred=leader_pred+amp*m.predict(qq[space]) if amp else leader_pred.copy();name='P3_'+space+'_'+kind;rec=dict(kind=kind,space=space,params=json.dumps(best['params']),amplitude=amp,inner_rmse=float(np.sqrt(best['mse'])));record(name,3,pred,rec,dict(type='residual',leader=leader,space=spaces[space],model=m,amplitude=amp));candidates.append((best['mse'],name,pred,rec));tuning.extend(dict(**key,experiment=name,**r) for r in records)
        win=min(candidates,key=lambda v:(round(v[0],12),v[1]));record('P3_SELECTOR',3,win[2],dict(**win[3],selected_variant=win[1]),dict(type='alias',name=win[1]))
        record('CT3',0,ct,{},dict(type='ct3'));record('LEADER',0,leader_pred,{},dict(type='leader',leader=leader))
        assert len(pipelines)==28
        assert all(not set(entry['train'])&set(va) and not set(entry['train'])&set(entry['held']) for entry in factory.ledger)
        joblib.dump(dict(pipelines=pipelines,ct3=ct3,train_positions=tr,validation_positions=va,ledger=factory.ledger,ct3_ledger=base_ledger,fallbacks=factory.fallbacks,reference_max_difference=parity),OUT/'models'/f'{fi:02d}.joblib',compress=3)
    joblib.dump(dict(predictions=rows,selection=selections,tuning=tuning,warnings=[dict(category=w.category.__name__,message=str(w.message)) for w in caught],seconds=time.perf_counter()-start,fallbacks=len(factory.fallbacks)),checkpoint,compress=3);print(f'3phases {fi+1}/65 {pro} {time.perf_counter()-start:.1f}s',flush=True)

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    else:
        if (OUT/'execution_complete.json').exists():raise FileExistsError('Preserve completed run')
        cfg=json.loads((OUT/'frozen_design.json').read_text());assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in cfg['source_sha256'].items());start=time.perf_counter();joblib.Parallel(n_jobs=4,backend='loky')(joblib.delayed(work)(i) for i in range(65));packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(65)]
        for field in ['predictions','selection','tuning']:
            d=pd.DataFrame([r for q in packs for r in q[field]])
            if field=='tuning' and 'params' in d:d['params']=d.params.map(lambda v:json.dumps(v) if isinstance(v,dict) or v is None else str(v))
            d.to_parquet(OUT/'tables'/f'{field}.parquet',index=False)
        (OUT/'audit/warnings.json').write_text(json.dumps([r for q in packs for r in q['warnings']],indent=2),encoding='utf-8');assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in cfg['source_sha256'].items());(OUT/'execution_complete.json').write_text(json.dumps(dict(status='complete',folds=65,new_recipes=26,seconds=time.perf_counter()-start,warnings=sum(len(q['warnings']) for q in packs),protected_sources_unchanged=True,no_final138_fit=True,no_PRED=True),indent=2),encoding='utf-8')
