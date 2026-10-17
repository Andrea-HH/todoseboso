"""Run frozen role swaps, nested gates and internal compact-route selection."""
from pathlib import Path
import sys,json,time,hashlib,warnings,importlib.util
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.geoc_bridge import OLD
from src.signal_role_allocation import RoleFactory,RoleSpace,predict_role
from src.conditional_local_phases import ExpertGate
spec=importlib.util.spec_from_file_location('runner437',ROOT/'scripts/437_run_geoc_signal_research.py');oldrunner=importlib.util.module_from_spec(spec);spec.loader.exec_module(oldrunner)
OUT=ROOT/'outputs/modeling/signal_role_allocation/v1';PREV=oldrunner.OUT


def load_assets():
    assets=oldrunner.load_assets();cfg=json.loads((OUT/'frozen_design.json').read_text());assets['variants']=cfg['variants'];assets['static']['MEAN']=np.zeros((197,1));t=assets['a']['train'];frame=assets['features197'].iloc[assets['a']['train_global']].reset_index(drop=True)
    joined=pd.concat([assets['core'].reset_index(drop=True),frame.drop(columns=[c for c in frame if c in assets['core']]),assets['physical'].drop(columns='ID_POLIGONO').reset_index(drop=True)],axis=1);assert not joined.columns.duplicated().any() and len(joined)==138
    assets['role_frame']=joined;return assets


def work(fi):
    dest=OUT/'checkpoints'/f'{fi:02d}.joblib'
    if dest.exists():return
    started=time.perf_counter();cfg=json.loads((OUT/'frozen_design.json').read_text());assets=load_assets();t=assets['a']['train'];y=assets['y'];frame=assets['role_frame'];groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO');plan=joblib.load(OLD/'cache/execution_plan.joblib')[fi];tr=np.asarray(plan['train_positions']);va=np.asarray(plan['validation_positions']);inner=joblib.load(OLD/'cache/frozen65_splits.joblib')[fi][5];key={k:plan[k] for k in ['protocol','repeat','fold']};factory=RoleFactory(assets,key['protocol'],groups,OUT/'cache'/f'{fi:02d}',PREV/'cache'/f'{fi:02d}');rows=[];models={};selection=[];contexts=[];lookup={int(v):i for i,v in enumerate(tr)};ct_oof=np.full(len(tr),np.nan);ct_ledger=[]
    def ctpack(k):return joblib.load(OLD/'base_cache'/f'{k}.joblib')
    ct3=ctpack(plan['outer_base_key'])['model'];ct=ct3.predict(t.iloc[va]);assert not set(tr)&set(va)
    with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        for item in plan['inner']:
            aa=np.asarray(item['train_positions']);bb=np.asarray(item['validation_positions']);where=np.array([lookup[int(v)] for v in bb]);pack=ctpack(item['base_key']);assert set(pack['registry']['train_ids'])==set(t.iloc[aa].ID_POLIGONO);ct_oof[where]=pack['model'].predict(t.iloc[bb]);mapping={int(v):i for i,v in enumerate(aa)};deep=np.full(len(aa),np.nan);deepcv=[]
            for ctx in item['residual_contexts']:
                dd=np.asarray(ctx['held_positions']);pack=ctpack(ctx['base_key']);excluded=set(t.iloc[np.r_[dd,bb,va]].ID_POLIGONO);assert not set(pack['registry']['train_ids'])&excluded;hold=np.array([mapping[int(v)] for v in dd]);fit=np.array([j for j in range(len(aa)) if j not in set(hold)]);deep[hold]=pack['model'].predict(t.iloc[dd]);deepcv.append((fit,hold));ct_ledger.append(dict(base_key=ctx['base_key'],verified=True))
            assert np.isfinite(deep).all();contexts.append(dict(aa=aa,bb=bb,where=where,ct_oof=deep,deepcv=deepcv,expert_oof={}))
        outer_oof={};experts={}
        for v in cfg['variants']:
            outer_oof[v]=factory.oof(tr,inner,v)
            for ctx in contexts:ctx['expert_oof'][v]=factory.oof(ctx['aa'],ctx['deepcv'],v)
            experts[v]=factory.fit(tr,v,inner)
        candidates=[];external={};space_cache={}
        def space(atoms,cols,fit,query):
            k=(tuple(atoms),tuple(cols),tuple(fit))
            if k not in space_cache:space_cache[k]=RoleSpace(atoms,cols,assets['physical_definitions']).fit(frame.iloc[fit])
            s=space_cache[k];return s,s.transform(frame.iloc[fit]),s.transform(frame.iloc[query])
        def record(name,pred,model,info):
            assert np.isfinite(pred).all();models[name]=model;selection.append(dict(**key,experiment=name,**info));rows.extend(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(p)) for i,p in zip(va,pred))
        for name,recipe in cfg['recipes'].items():
            v=recipe['variant'];atoms=recipe['gate_atoms'];cols=recipe['gate_columns'];local_candidates=[]
            for k in (cfg['gate_k'] if atoms or cols else [0]):
                internal=np.full(len(tr),np.nan)
                for ctx in contexts:
                    _,z,q=space(atoms,cols,ctx['aa'],ctx['bb']);gate=ExpertGate('clusters' if k else 'global',k).fit(z,y[ctx['aa']],ctx['ct_oof'],ctx['expert_oof'][v]);internal[ctx['where']]=gate.predict(q,ct_oof[ctx['where']],outer_oof[v][ctx['where']])
                assert np.isfinite(internal).all();candidate=dict(recipe=name,k=k,rmse=float(np.sqrt(np.mean((internal-y[tr])**2))),input_count=recipe['input_count']);candidates.append(candidate);local_candidates.append(candidate)
            best=min(local_candidates,key=lambda c:(round(c['rmse'],12),c['k']));s,z,q=space(atoms,cols,tr,va);gate=ExpertGate('clusters' if best['k'] else 'global',best['k']).fit(z,y[tr],ct_oof,outer_oof[v]);ep=predict_role(experts[v],va,assets);pred=gate.predict(q,ct,ep);external[name]=pred
            record(name,pred,dict(variant=v,space=s,gate=gate),dict(selected_recipe=name,gate_k=best['k'],inner_rmse=best['rmse'],input_count=recipe['input_count'],expert_amplitude=experts[v]['amplitude']))
        for name,compact in [('SELECT_MIN_RMSE',False),('SELECT_COMPACT_001',True)]:
            minimum=min(c['rmse'] for c in candidates);allowed=[c for c in candidates if c['rmse']<=minimum+(cfg['selector_tolerance_rmse'] if compact else 1e-12)]
            best=min(allowed,key=lambda c:(c['input_count'] if compact else 0,round(c['rmse'],12),list(cfg['recipes']).index(c['recipe']),c['k']));recipe=cfg['recipes'][best['recipe']];v=recipe['variant'];s,z,q=space(recipe['gate_atoms'],recipe['gate_columns'],tr,va);gate=ExpertGate('clusters' if best['k'] else 'global',best['k']).fit(z,y[tr],ct_oof,outer_oof[v]);pred=gate.predict(q,ct,predict_role(experts[v],va,assets));record(name,pred,dict(variant=v,space=s,gate=gate),dict(selected_recipe=best['recipe'],gate_k=best['k'],inner_rmse=best['rmse'],input_count=best['input_count'],expert_amplitude=experts[v]['amplitude']))
        prev=pd.read_parquet(PREV/'tables/predictions.parquet');subset=prev[(prev.protocol==key['protocol'])&(prev['repeat']==key['repeat'])&(prev.fold==key['fold'])]
        raw_expected=subset[subset.experiment=='B_SMALL12_raw_COMPACT'].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy();parity=float(np.max(abs(predict_role(experts['FULL12'],va,assets)-raw_expected)));assert parity<1e-12
        record('CT3',ct,dict(ct3=True),{})
        for name,old in [('PRIOR_SMALL12','E_REDUCED_SMALL12_BOTH'),('PRIOR_BIGBOTH','P1_BOTH'),('PRIOR_EXPERT','LEADER')]:
            g=subset[subset.experiment==old].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO];rows.extend(dict(**key,experiment=name,ID_POLIGONO=i,y_true=float(yv),y_pred=float(pv)) for i,yv,pv in zip(g.index,g.y_true,g.y_pred))
        assert all(not set(e['train'])&(set(e['held'])|set(va)) for e in factory.ledger)
        joblib.dump(dict(experts=experts,models=models,ct3=ct3,train_positions=tr,validation_positions=va,ledger=factory.ledger,ct3_ledger=ct_ledger,reference_difference=parity),OUT/'models'/f'{fi:02d}.joblib',compress=3)
    joblib.dump(dict(predictions=rows,selection=selection,candidates=candidates,warnings=[dict(category=w.category.__name__,message=str(w.message)) for w in caught],seconds=time.perf_counter()-started),dest,compress=3);print(f'Roles {fi+1}/65 {key["protocol"]} {time.perf_counter()-started:.1f}s',flush=True)


if __name__=='__main__':
    if (OUT/'execution_complete.json').exists():raise FileExistsError('Preserve completed role experiment')
    cfg=json.loads((OUT/'frozen_design.json').read_text());assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());start=time.perf_counter();joblib.Parallel(n_jobs=4,backend='loky')(joblib.delayed(work)(i) for i in range(65));packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(65)]
    for field in ['predictions','selection','candidates']:pd.DataFrame([r if field!='candidates' else dict(index=i,**r) for i,p in enumerate(packs) for r in p[field]]).to_parquet(OUT/'tables'/f'{field}.parquet',index=False)
    (OUT/'audit/warnings.json').write_text(json.dumps([w for p in packs for w in p['warnings']],indent=2),encoding='utf-8');assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());(OUT/'execution_complete.json').write_text(json.dumps(dict(status='complete',folds=65,new_recipes=30,seconds=time.perf_counter()-start,protected_sources_unchanged=True,no_final138_fit=True,no_PRED=True),indent=2),encoding='utf-8')
