"""Twelve frozen exploratory signal additions: local versus residual placement."""
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
spec=importlib.util.spec_from_file_location('runner442',ROOT/'scripts/442_run_signal_role_allocation.py');previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
from src.difficult_case_signals import OUT,JOINT,load_assets
PREV=JOINT
UNUSED_ARCHIVES=['CT3','BASE12_BOTH','DROP_HISTORY_WATER','DROP_SOIL','GATE_ONLY_SHARES','MEAN_BOTH','PRIOR_BIGBOTH']


def work(fi):
    destination=OUT/'checkpoints'/f'{fi:02d}.joblib'
    if destination.exists():return
    start=time.perf_counter();cfg=json.loads((OUT/'frozen_design.json').read_text());assets=load_assets();t=assets['a']['train'];y=assets['y'];frame=assets['role_frame'];groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO');plan=joblib.load(OLD/'cache/execution_plan.joblib')[fi];tr=np.asarray(plan['train_positions']);va=np.asarray(plan['validation_positions']);inner=joblib.load(OLD/'cache/frozen65_splits.joblib')[fi][5];key={k:plan[k] for k in ['protocol','repeat','fold']};factory=RoleFactory(assets,key['protocol'],groups,OUT/'cache'/f'{fi:02d}',PREV/'cache'/f'{fi:02d}');contexts=[];lookup={int(v):i for i,v in enumerate(tr)};ct_oof=np.full(len(tr),np.nan);ct_ledger=[];rows=[];selection=[];models={};candidates=[]
    def base(k):return joblib.load(OLD/'base_cache'/f'{k}.joblib')
    ct3=base(plan['outer_base_key'])['model'];ct=ct3.predict(t.iloc[va]);assert not set(tr)&set(va)
    with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        for item in plan['inner']:
            aa=np.asarray(item['train_positions']);bb=np.asarray(item['validation_positions']);where=np.array([lookup[int(v)] for v in bb]);pack=base(item['base_key']);assert set(pack['registry']['train_ids'])==set(t.iloc[aa].ID_POLIGONO);ct_oof[where]=pack['model'].predict(t.iloc[bb]);mapping={int(v):i for i,v in enumerate(aa)};deep=np.full(len(aa),np.nan);deepcv=[]
            for context in item['residual_contexts']:
                dd=np.asarray(context['held_positions']);pack=base(context['base_key']);excluded=set(t.iloc[np.r_[dd,bb,va]].ID_POLIGONO);assert not set(pack['registry']['train_ids'])&excluded;hold=np.array([mapping[int(v)] for v in dd]);fit=np.array([j for j in range(len(aa)) if j not in set(hold)]);deep[hold]=pack['model'].predict(t.iloc[dd]);deepcv.append((fit,hold));ct_ledger.append(dict(base_key=context['base_key'],verified=True))
            assert np.isfinite(deep).all();contexts.append(dict(aa=aa,bb=bb,where=where,ct_oof=deep,deepcv=deepcv,expert_oof={}))
        oof={};experts={}
        for v in cfg['variants']:
            oof[v]=factory.oof(tr,inner,v)
            for context in contexts:context['expert_oof'][v]=factory.oof(context['aa'],context['deepcv'],v)
            experts[v]=factory.fit(tr,v,inner)
        for name,r in cfg['recipes'].items():
            v=r['variant'];scores=[]
            for k in cfg['gate_k']:
                prediction=np.full(len(tr),np.nan)
                for context in contexts:
                    s=RoleSpace(r['gate_atoms'],[],assets['physical_definitions']).fit(frame.iloc[context['aa']]);gate=ExpertGate('clusters',k).fit(s.transform(frame.iloc[context['aa']]),y[context['aa']],context['ct_oof'],context['expert_oof'][v]);prediction[context['where']]=gate.predict(s.transform(frame.iloc[context['bb']]),ct_oof[context['where']],oof[v][context['where']])
                assert np.isfinite(prediction).all();entry=dict(recipe=name,k=k,rmse=float(np.sqrt(np.mean((prediction-y[tr])**2))));scores.append(entry);candidates.append(entry)
            best=min(scores,key=lambda z:(round(z['rmse'],12),z['k']));space=RoleSpace(r['gate_atoms'],[],assets['physical_definitions']).fit(frame.iloc[tr]);gate=ExpertGate('clusters',best['k']).fit(space.transform(frame.iloc[tr]),y[tr],ct_oof,oof[v]);prediction=gate.predict(space.transform(frame.iloc[va]),ct,predict_role(experts[v],va,assets));assert np.isfinite(prediction).all();models[name]=dict(variant=v,space=space,gate=gate);selection.append(dict(**key,experiment=name,gate_k=best['k'],inner_rmse=best['rmse'],input_count=r['input_count'],expert_amplitude=experts[v]['amplitude']));rows.extend(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(value)) for i,value in zip(va,prediction))
        refs=pd.read_parquet(JOINT/'tables/predictions.parquet');refs=refs[(refs.protocol==key['protocol'])&(refs['repeat']==key['repeat'])&(refs.fold==key['fold'])&refs.experiment.isin(set(cfg['references'].values()))];assert len(refs)==3*len(va);rows.extend(refs.to_dict('records'));assert all(not set(e['train'])&(set(e['held'])|set(va)) for e in factory.ledger)
        joblib.dump(dict(experts=experts,models=models,ct3=ct3,train_positions=tr,validation_positions=va,ledger=factory.ledger,ct3_ledger=ct_ledger,reference_models_frozen=True),OUT/'models'/f'{fi:02d}.joblib',compress=3)
    joblib.dump(dict(predictions=rows,selection=selection,candidates=candidates,warnings=[dict(category=w.category.__name__,message=str(w.message)) for w in caught],seconds=time.perf_counter()-start),destination,compress=3);print(f'Joint {fi+1}/65 {key["protocol"]} {time.perf_counter()-start:.1f}s',flush=True)


if __name__=='__main__':
    if (OUT/'execution_complete.json').exists():raise FileExistsError('Preserve completed joint run')
    cfg=json.loads((OUT/'frozen_design.json').read_text());assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());start=time.perf_counter();joblib.Parallel(n_jobs=4,backend='loky')(joblib.delayed(work)(i) for i in range(65));packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(65)]
    for field in ['predictions','selection','candidates']:pd.DataFrame([dict(index=i,**r) for i,p in enumerate(packs) for r in p[field]]).to_parquet(OUT/'tables'/f'{field}.parquet',index=False)
    (OUT/'audit/warnings.json').write_text(json.dumps([w for p in packs for w in p['warnings']],indent=2),encoding='utf-8');assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());(OUT/'execution_complete.json').write_text(json.dumps(dict(status='complete',new_recipes=12,folds=65,seconds=time.perf_counter()-start,protected_sources_unchanged=True,no_final138_fit=True,no_PRED=True),indent=2),encoding='utf-8')
