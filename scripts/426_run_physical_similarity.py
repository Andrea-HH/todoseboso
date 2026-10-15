"""Frozen block/family ablations and fully internal selector over honest C-T3 residuals."""
from pathlib import Path
import sys,json,time,warnings,hashlib
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.geoc_bridge import data,OLD
from src.physical_similarity import BlockRepresentation,ResidualCorrector,neighbor_weights,select_candidate
OUT=ROOT/'outputs/modeling/physical_similarity/v2'

def work(fi):
    checkpoint=OUT/'checkpoints'/f'{fi:02d}.joblib'
    if checkpoint.exists():return
    started=time.perf_counter();cfg=json.loads((OUT/'frozen_design.json').read_text());t=data()['train'];x=pd.read_parquet(OUT/'cache/features138_target_free.parquet');assert x.ID_POLIGONO.tolist()==t.ID_POLIGONO.tolist()
    y=t.RENDIMIENTO_T_HA.to_numpy();plan=joblib.load(OLD/'cache/execution_plan.joblib')[fi];tr=np.asarray(plan['train_positions']);va=np.asarray(plan['validation_positions']);lookup={int(v):i for i,v in enumerate(tr)};assert not set(tr)&set(va)
    key=dict(protocol=plan['protocol'],repeat=plan['repeat'],fold=plan['fold']);contexts=[];ledger=[];cf=np.full(len(tr),np.nan)
    def base(k):return joblib.load(OLD/'base_cache'/f'{k}.joblib')
    for item in plan['inner']:
        aa=np.asarray(item['train_positions']);bb=np.asarray(item['validation_positions']);where=np.array([lookup[int(v)] for v in bb]);b=base(item['base_key']);assert set(b['registry']['train_ids'])==set(t.iloc[aa].ID_POLIGONO)
        bp=b['model'].predict(t.iloc[bb]);cf[where]=bp;deep=np.full(len(aa),np.nan);mapping={int(v):i for i,v in enumerate(aa)}
        for ctx in item['residual_contexts']:
            dd=ctx['held_positions'];b=base(ctx['base_key']);excluded=set(t.iloc[np.r_[dd,bb,va]].ID_POLIGONO);assert not set(b['registry']['train_ids'])&excluded
            deep[[mapping[int(v)] for v in dd]]=b['model'].predict(t.iloc[dd]);ledger.append(dict(base_key=ctx['base_key'],excluded_ids=sorted(excluded),verified=True))
        assert np.isfinite(deep).all();contexts.append(dict(aa=aa,bb=bb,where=where,residual=y[aa]-deep,bp=bp))
    assert np.isfinite(cf).all()
    ct3=base(plan['outer_base_key'])['model'];baseline=ct3.predict(t.iloc[va]);residual=y[tr]-cf
    rows=[];selection=[];tuning=[];models={};support=[];groupdiagnostics=[];candidates=[]
    with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        # Atomic representations fitted independently in each applicable training set.
        outer={b:BlockRepresentation(cols).fit(x.iloc[tr]) for b,cols in cfg['blocks'].items()}
        outer_train={b:m.transform(x.iloc[tr]) for b,m in outer.items()};outer_valid={b:m.transform(x.iloc[va]) for b,m in outer.items()}
        inner=[]
        for ctx in contexts:
            aa=ctx['aa'];bb=ctx['bb'];reps={b:BlockRepresentation(cols).fit(x.iloc[aa]) for b,cols in cfg['blocks'].items()}
            inner.append(dict(train={b:m.transform(x.iloc[aa]) for b,m in reps.items()},valid={b:m.transform(x.iloc[bb]) for b,m in reps.items()}))
        def stack(parts,atoms):return np.column_stack([parts[b] for b in atoms])/np.sqrt(len(atoms))
        for spec,atoms in cfg['specs'].items():
            z=stack(outer_train,atoms);q=stack(outer_valid,atoms)
            # Physical neighbors use no coordinates; administrative metadata below are diagnostic only.
            w,d=neighbor_weights(z,q,24)
            sameprofile=(t.iloc[va].climate_profile.to_numpy()[:,None]==t.iloc[tr].climate_profile.to_numpy()[None,:])
            samemun=(t.iloc[va].Municipio.to_numpy()[:,None]==t.iloc[tr].Municipio.to_numpy()[None,:])
            # Reference nearest training support, excluding self, on this training representation.
            _,dt=neighbor_weights(z,z,1);np.fill_diagonal(dt,np.inf);cut=float(np.quantile(dt.min(axis=1),.9))
            for j,i in enumerate(va):support.append(dict(**key,spec=spec,ID_POLIGONO=t.iloc[i].ID_POLIGONO,nearest_distance=float(d[j].min()),training_nn_q90=cut,outside_nn90=bool(d[j].min()>cut),same_profile_neighbor_weight=float(w[j]@sameprofile[j]),same_municipality_neighbor_weight=float(w[j]@samemun[j]),effective_neighbors=float(1/np.sum(w[j]**2))))
            for kind,grid in cfg['grids'].items():
                name=spec+'__'+kind;deltas=[]
                for params in grid:
                    delta=np.full(len(tr),np.nan)
                    for ctx,rep in zip(contexts,inner):
                        zz=stack(rep['train'],atoms);qq=stack(rep['valid'],atoms)
                        model=ResidualCorrector(kind,params).fit(zz,ctx['residual']);delta[ctx['where']]=model.predict(qq)
                    assert np.isfinite(delta).all();deltas.append(delta)
                best,scores=select_candidate(y[tr],cf,deltas,grid);amp=best['amplitude'];model=None
                if amp:model=ResidualCorrector(kind,best['params']).fit(z,residual);pred=baseline+amp*model.predict(q)
                else:pred=baseline.copy()
                record=dict(**key,experiment=name,spec=spec,kind=kind,amplitude=amp,params=json.dumps(best['params']),inner_rmse=float(np.sqrt(best['mse'])),n_components=z.shape[1],n_inputs=sum(len(cfg['blocks'][b]) for b in atoms))
                selection.append(record);models[name]=dict(model=model,amplitude=amp,atoms=atoms,selection=best)
                candidates.append(dict(name=name,spec=spec,kind=kind,best=best,prediction=pred))
                tuning.extend(dict(**key,experiment=name,**r) for r in scores)
                rows.extend(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(v)) for i,v in zip(va,pred))
                if kind=='groups' and model is not None:
                    labels=model.model_.labels_
                    for label in np.unique(labels):
                        ix=tr[labels==label];counts=t.iloc[ix].Estado.value_counts();mun=t.iloc[ix].Municipio.value_counts()
                        groupdiagnostics.append(dict(**key,experiment=name,group=int(label),n=len(ix),dominant_state=str(counts.index[0]),dominant_state_fraction=float(counts.iloc[0]/len(ix)),dominant_municipality_fraction=float(mun.iloc[0]/len(ix)),n_profiles=int(t.iloc[ix].climate_profile.nunique()),correction_before_amplitude=float(model.values_[label]-model.center_)))
        # Altitude is a separately reported sensitivity, not allowed in the omnibus selection.
        eligible=[c for c in candidates if c['spec']!='altitude_sensitivity']
        winner=min(eligible,key=lambda c:(round(c['best']['mse'],12),c['best']['amplitude'],list(cfg['specs']).index(c['spec']),list(cfg['grids']).index(c['kind'])))
        rows.extend(dict(**key,experiment='INTERNAL_SELECTOR',ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(v)) for i,v in zip(va,winner['prediction']))
        selection.append(dict(**key,experiment='INTERNAL_SELECTOR',spec=winner['spec'],kind=winner['kind'],amplitude=winner['best']['amplitude'],params=json.dumps(winner['best']['params']),inner_rmse=float(np.sqrt(winner['best']['mse'])),selected_variant=winner['name']))
        rows.extend(dict(**key,experiment='CT3',ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(v)) for i,v in zip(va,baseline))
        joblib.dump(dict(representations=outer,correctors=models,ct3=ct3,train_positions=tr,validation_positions=va,residual_targets=residual,ledger=ledger,selected_variant=winner['name']),OUT/'models'/f'{fi:02d}.joblib',compress=3)
    logs=[dict(category=w.category.__name__,message=str(w.message)) for w in caught]
    joblib.dump(dict(predictions=rows,selection=selection,tuning=tuning,support=support,group_diagnostics=groupdiagnostics,warnings=logs,seconds=time.perf_counter()-started),checkpoint,compress=3)
    print(f'physical {fi+1}/65 {key["protocol"]}: {len(candidates)} block/family models + internal selector; {time.perf_counter()-started:.1f}s',flush=True)

if __name__=='__main__':
    if (OUT/'execution_complete.json').exists():raise FileExistsError('Preserve complete run')
    cfg=json.loads((OUT/'frozen_design.json').read_text());assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in cfg['source_sha256'].items())
    started=time.perf_counter()
    joblib.Parallel(n_jobs=4,backend='loky')(joblib.delayed(work)(fi) for fi in range(65))
    packs=[joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib') for fi in range(65)]
    for key in ['predictions','selection','tuning','support','group_diagnostics']:
        d=pd.DataFrame([r for q in packs for r in q[key]])
        if key=='tuning':d['params']=d.params.map(lambda v:json.dumps(v))
        d.to_parquet(OUT/'tables'/f'{key}.parquet',index=False)
    logs=[r for q in packs for r in q['warnings']];(OUT/'audit/warnings.json').write_text(json.dumps(logs,indent=2),encoding='utf-8')
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in cfg['source_sha256'].items())
    (OUT/'execution_complete.json').write_text(json.dumps(dict(status='complete',folds=65,models_per_fold=len(cfg['specs'])*3+1,seconds=time.perf_counter()-started,warnings=len(logs),protected_sources_unchanged=True,no_new_final_fit=True,no_PRED=True),indent=2),encoding='utf-8')
