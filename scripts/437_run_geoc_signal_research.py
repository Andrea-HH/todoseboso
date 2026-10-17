"""Frozen attribution, reduced experts, corrections and conditional gates."""
from pathlib import Path
import sys,json,time,hashlib,warnings
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.geoc_bridge import data,OLD
from src.geoc_signal_research import SignalFactory,SignalRepresentation,predict_base,predict_expert,CategoryGate,CategoryCorrection
from src.conditional_local_phases import ExpertGate,PhysicalSpace
from src.physical_similarity import ResidualCorrector,select_candidate
from src.ct3_residual_conditional.models import CORE
OUT=ROOT/'outputs/modeling/geoc_signal_research/v1';PREV=ROOT/'outputs/modeling/conditional_local_phases/v1';REP=ROOT/'outputs/modeling/physical_representation/v1'

def load_assets():
    cfg=json.loads((OUT/'frozen_design.json').read_text());a=data();rep=joblib.load(OUT/'cache/static_representations.joblib');assert a['ids197']==rep['ids197'];features=pd.read_parquet(OUT/'cache/features197_target_free.parquet');assert features.ID_POLIGONO.tolist()==a['ids197'];physical=pd.read_parquet(REP/'cache/features138_target_free.parquet');assert physical.ID_POLIGONO.tolist()==a['train'].ID_POLIGONO.tolist()
    return dict(a=a,y=a['train'].RENDIMIENTO_T_HA.to_numpy(),features197=features,core=a['train'][CORE],static=rep['static'],variants=cfg['variants'],physical=physical,physical_definitions=json.loads((REP/'frozen_design.json').read_text())['atoms'])

def work(fi):
    dest=OUT/'checkpoints'/f'{fi:02d}.joblib'
    if dest.exists():return
    start=time.perf_counter();cfg=json.loads((OUT/'frozen_design.json').read_text());assets=load_assets();t=assets['a']['train'];y=assets['y'];pos=assets['a']['train_global'];frame=assets['features197'];groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO');plan=joblib.load(OLD/'cache/execution_plan.joblib')[fi];tr=np.asarray(plan['train_positions']);va=np.asarray(plan['validation_positions']);inner=joblib.load(OLD/'cache/frozen65_splits.joblib')[fi][5];key=dict(protocol=plan['protocol'],repeat=plan['repeat'],fold=plan['fold']);factory=SignalFactory(assets,key['protocol'],groups,OUT/'cache'/f'{fi:02d}',PREV/'cache'/f'{fi:02d}');contexts=[];lookup={int(v):i for i,v in enumerate(tr)};ct_oof=np.full(len(tr),np.nan);rows=[];selection=[];models={};experts={};ct_ledger=[]
    def base(k):return joblib.load(OLD/'base_cache'/f'{k}.joblib')
    ct3=base(plan['outer_base_key'])['model'];ct=ct3.predict(t.iloc[va])
    def record(name,pred,model,info=None):
        assert np.isfinite(pred).all();models[name]=model;selection.append(dict(**key,experiment=name,**(info or {})));rows.extend(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(v)) for i,v in zip(va,pred))
    with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        for item in plan['inner']:
            aa=np.asarray(item['train_positions']);bb=np.asarray(item['validation_positions']);where=np.array([lookup[int(v)] for v in bb]);pack=base(item['base_key']);assert set(pack['registry']['train_ids'])==set(t.iloc[aa].ID_POLIGONO);ct_oof[where]=pack['model'].predict(t.iloc[bb]);mapping={int(v):i for i,v in enumerate(aa)};deep=np.full(len(aa),np.nan);deepcv=[]
            for ctx in item['residual_contexts']:
                dd=np.asarray(ctx['held_positions']);pack=base(ctx['base_key']);excluded=set(t.iloc[np.r_[dd,bb,va]].ID_POLIGONO);assert not set(pack['registry']['train_ids'])&excluded;hold=np.array([mapping[int(v)] for v in dd]);fit=np.array([j for j in range(len(aa)) if j not in set(hold)]);deep[hold]=pack['model'].predict(t.iloc[dd]);deepcv.append((fit,hold));ct_ledger.append(dict(base_key=ctx['base_key'],verified=True))
            assert np.isfinite(deep).all();contexts.append(dict(aa=aa,bb=bb,where=where,ct_oof=deep,deepcv=deepcv,expert_oof={}))
        full=factory.fit(tr,'FULL',inner);experts['FULL']=full;lp=predict_expert(full,va,assets);ref=pd.read_parquet(PREV/'tables/predictions.parquet');expected=ref[(ref.experiment=='LEADER')&(ref.protocol==key['protocol'])&(ref['repeat']==key['repeat'])&(ref.fold==key['fold'])].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy();parity=float(np.max(abs(lp-expected)));assert parity<1e-12
        variants=['FULL']+[v for v,s in cfg['variants'].items() if s['type']=='small'];outer_oof={}
        for v in variants:
            outer_oof[v]=factory.oof(tr,inner,v)
            for ctx in contexts:ctx['expert_oof'][v]=factory.oof(ctx['aa'],ctx['deepcv'],v)
            if v!='FULL':experts[v]=factory.fit(tr,v,inner)
        for v,s in cfg['variants'].items():
            if s['type'] not in ['static','inductive_control'] or v=='FULL':continue
            pack=factory.fit(tr,v,inner);experts[v]=pack
            record('A_'+v+'_LOCAL',predict_base(pack['local'],va,assets),dict(type='local',expert=v),dict(n_input=len(s['columns'])))
            record('A_'+v+'_COMPACT',predict_expert(pack,va,assets),dict(type='expert',expert=v),dict(n_input=len(s['columns']),amplitude=pack['amplitude'],params=json.dumps(pack['selection'])))
        for bundle in cfg['bundles']:
            scores=[]
            for mode in cfg['modes']:
                v=bundle+'_'+mode;pack=experts[v];pred=predict_expert(pack,va,assets)
                record('B_'+v+'_LOCAL',predict_base(pack['local'],va,assets),dict(type='local',expert=v),dict(n_input=len(cfg['bundles'][bundle]),mode=mode))
                record('B_'+v+'_COMPACT',pred,dict(type='expert',expert=v),dict(n_input=len(cfg['bundles'][bundle]),mode=mode,amplitude=pack['amplitude'],params=json.dumps(pack['selection'])))
                scores.append((float(np.mean((outer_oof[v]-y[tr])**2)),v,pred))
            win=min(scores,key=lambda z:(round(z[0],12),cfg['modes'].index(cfg['variants'][z[1]]['mode'])));record('B_'+bundle+'_SELECTOR',win[2],dict(type='expert',expert=win[1]),dict(selected_variant=win[1],inner_rmse=float(np.sqrt(win[0]))))
        # Precompute continuous representations: no Y enters these transforms.
        rep_cache={}
        def space(label,mode,fit,query):
            if label in ['STATE','MUNICIPALITY']:
                vals=t.Estado.to_numpy(str) if label=='STATE' else t.Municipio.to_numpy(str);return None,vals[fit],vals[query]
            k=(label,mode,tuple(fit))
            if k not in rep_cache:
                cols=cfg['bundles'][label] if label in cfg['bundles'] else ['base_centroid_lat','base_centroid_lon'];rep_cache[k]=SignalRepresentation(cols,mode).fit(frame.iloc[pos[fit]])
            rep=rep_cache[k];return rep,rep.transform(frame.iloc[pos[fit]]),rep.transform(frame.iloc[pos[query]])
        labels=list(cfg['bundles'])+['STATE','MUNICIPALITY','COORDINATES']
        for label in labels:
            modes=cfg['modes'] if label in cfg['bundles'] else ['raw'];category=label in ['STATE','MUNICIPALITY'];candidates=[];parameters=[];deltas=[]
            for mode in modes:
                for alpha in ([None] if category else [1.,.1,.01]):
                    delta=np.full(len(tr),np.nan)
                    for ctx in contexts:
                        _,z,q=space(label,mode,ctx['aa'],ctx['bb']);target=y[ctx['aa']]-ctx['ct_oof'];m=CategoryCorrection().fit(z,target) if category else ResidualCorrector('ridge',dict(alpha=alpha)).fit(z,target);delta[ctx['where']]=m.predict(q)
                    deltas.append(delta);parameters.append(dict(mode=mode,alpha=alpha))
            best,_=select_candidate(y[tr],ct_oof,deltas,parameters);mode=best['params']['mode'] if best['params'] else modes[0];rep,z,q=space(label,mode,tr,va);amp=best['amplitude'];m=None
            if amp:m=CategoryCorrection().fit(z,y[tr]-ct_oof) if category else ResidualCorrector('ridge',dict(alpha=best['params']['alpha'])).fit(z,y[tr]-ct_oof)
            pred=ct+amp*m.predict(q) if amp else ct.copy();record('C_CORRECT_'+label,pred,dict(type='correction',representation=rep,category=label if category else None,model=m,amplitude=amp),dict(mode=mode,amplitude=amp,params=json.dumps(best['params']),inner_rmse=float(np.sqrt(best['mse']))))
            for mode in modes:
                for k in ([None] if category else [4,8]):
                    pred=np.full(len(tr),np.nan)
                    for ctx in contexts:
                        _,z,q=space(label,mode,ctx['aa'],ctx['bb']);gate=CategoryGate().fit(z,y[ctx['aa']],ctx['ct_oof'],ctx['expert_oof']['FULL']) if category else ExpertGate('clusters',k).fit(z,y[ctx['aa']],ctx['ct_oof'],ctx['expert_oof']['FULL']);pred[ctx['where']]=gate.predict(q,ct_oof[ctx['where']],outer_oof['FULL'][ctx['where']])
                    candidates.append(dict(mode=mode,k=k,mse=float(np.mean((pred-y[tr])**2))))
            best=min(enumerate(candidates),key=lambda z:(round(z[1]['mse'],12),z[0]))[1];rep,z,q=space(label,best['mode'],tr,va);gate=CategoryGate().fit(z,y[tr],ct_oof,outer_oof['FULL']) if category else ExpertGate('clusters',best['k']).fit(z,y[tr],ct_oof,outer_oof['FULL']);record('D_GATE_'+label,gate.predict(q,ct,lp),dict(type='gate',expert='FULL',representation=rep,category=label if category else None,gate=gate),dict(mode=best['mode'],params=json.dumps(best),inner_rmse=float(np.sqrt(best['mse']))))
        # Same physical BOTH gate, now swapping the 1831-feature expert for small experts.
        physical_outer=PhysicalSpace('BOTH',assets['physical_definitions']).fit(assets['physical'].iloc[tr]);z=physical_outer.transform(assets['physical'].iloc[tr]);q=physical_outer.transform(assets['physical'].iloc[va]);phys_inner=[]
        for ctx in contexts:
            p=PhysicalSpace('BOTH',assets['physical_definitions']).fit(assets['physical'].iloc[ctx['aa']]);phys_inner.append((p.transform(assets['physical'].iloc[ctx['aa']]),p.transform(assets['physical'].iloc[ctx['bb']])))
        for bundle in cfg['bundles']:
            for kind in ['BOTH','GLOBAL']:
                candidates=[]
                for mode in cfg['modes']:
                    v=bundle+'_'+mode
                    for k in ([4,8] if kind=='BOTH' else [0]):
                        pred=np.full(len(tr),np.nan)
                        for ctx,(zz,qq) in zip(contexts,phys_inner):
                            if kind=='GLOBAL':zz=np.zeros((len(ctx['aa']),1));qq=np.zeros((len(ctx['bb']),1))
                            gate=ExpertGate('clusters' if kind=='BOTH' else 'global',k).fit(zz,y[ctx['aa']],ctx['ct_oof'],ctx['expert_oof'][v]);pred[ctx['where']]=gate.predict(qq,ct_oof[ctx['where']],outer_oof[v][ctx['where']])
                        candidates.append(dict(variant=v,k=k,mse=float(np.mean((pred-y[tr])**2))))
                best=min(enumerate(candidates),key=lambda p:(round(p[1]['mse'],12),p[0]))[1];v=best['variant'];zz,qq=(z,q) if kind=='BOTH' else (np.zeros((len(tr),1)),np.zeros((len(va),1)));gate=ExpertGate('clusters' if kind=='BOTH' else 'global',best['k']).fit(zz,y[tr],ct_oof,outer_oof[v]);pred=gate.predict(qq,ct,predict_expert(experts[v],va,assets));record('E_REDUCED_'+bundle+'_'+kind,pred,dict(type='reduced_gate',expert=v,physical=physical_outer if kind=='BOTH' else None,gate=gate),dict(selected_variant=v,params=json.dumps(best),inner_rmse=float(np.sqrt(best['mse']))))
        record('CT3',ct,dict(type='ct3'));record('LEADER',lp,dict(type='expert',expert='FULL'));record('FULL_LOCAL',predict_base(full['local'],va,assets),dict(type='local',expert='FULL'))
        assert set(models)-{'CT3','LEADER','FULL_LOCAL'}==set(cfg['references'])
        for name,oldname in [('P1_GLOBAL','P1_GLOBAL_global'),('P1_BOTH','P1_BOTH_clusters'),('P1_TEXTURE','P1_TEXTURE_clusters')]:
            g=ref[(ref.experiment==oldname)&(ref.protocol==key['protocol'])&(ref['repeat']==key['repeat'])&(ref.fold==key['fold'])].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO];rows.extend(dict(**key,experiment=name,ID_POLIGONO=i,y_true=float(yv),y_pred=float(pv)) for i,yv,pv in zip(g.index,g.y_true,g.y_pred))
        assert all(not set(e['train'])&(set(e['held'])|set(va)) for e in factory.ledger)
        joblib.dump(dict(experts=experts,models=models,ct3=ct3,train_positions=tr,validation_positions=va,ledger=factory.ledger,ct3_ledger=ct_ledger,reference_difference=parity),OUT/'models'/f'{fi:02d}.joblib',compress=3)
    joblib.dump(dict(predictions=rows,selection=selection,warnings=[dict(category=w.category.__name__,message=str(w.message)) for w in caught],seconds=time.perf_counter()-start),dest,compress=3);print(f'GeoC signals {fi+1}/65 {key["protocol"]} {time.perf_counter()-start:.1f}s',flush=True)

if __name__=='__main__':
    if (OUT/'execution_complete.json').exists():raise FileExistsError('Preserve completed models')
    cfg=json.loads((OUT/'frozen_design.json').read_text());assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in cfg['source_sha256'].items());start=time.perf_counter();joblib.Parallel(n_jobs=4,backend='loky')(joblib.delayed(work)(i) for i in range(65));packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(65)]
    for field in ['predictions','selection']:pd.DataFrame([r for p in packs for r in p[field]]).to_parquet(OUT/'tables'/f'{field}.parquet',index=False)
    (OUT/'audit/warnings.json').write_text(json.dumps([r for p in packs for r in p['warnings']],indent=2),encoding='utf-8');assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in cfg['source_sha256'].items());(OUT/'execution_complete.json').write_text(json.dumps(dict(status='complete',folds=65,recipes=cfg['recipes'],seconds=time.perf_counter()-start,warnings=sum(len(p['warnings']) for p in packs),protected_sources_unchanged=True,no_final138_fit=True,no_PRED=True),indent=2),encoding='utf-8')
