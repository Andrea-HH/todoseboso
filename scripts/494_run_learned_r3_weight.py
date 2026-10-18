"""Nested correction proposals for learned and asymmetric R3 weights."""
from pathlib import Path
import sys,json,time,hashlib,warnings
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.learned_r3_weight import OUT,GateFeatures,LearnedWeight
from src.base_distribution_correction import SimplifiedBases
from src.indicator_neighborhoods import OUT as INDICATORS,ReducedCorrection
from src.neighbor_signal_contrasts import load_assets,JOINT
from src.geoc_bridge import OLD
PRIOR=ROOT/'outputs/modeling/base_distribution_correction/v1'
BASES=['CT3','J7','SHARES']

def work(fi):
    destination=OUT/'checkpoints'/f'{fi:02d}.joblib'
    if destination.exists():return
    start=time.perf_counter();cfg=json.loads((OUT/'frozen_design.json').read_text());a=load_assets();t=a['a']['train'];y=a['y'];x=pd.read_parquet(INDICATORS/'cache/features_train138_target_free.parquet');assert x.ID_POLIGONO.tolist()==t.ID_POLIGONO.tolist();pro,re,fold,tr,va,inner=joblib.load(OLD/'cache/frozen65_splits.joblib')[fi];tr=np.asarray(tr);va=np.asarray(va);key=dict(protocol=pro,repeat=re,fold=fold);old=joblib.load(PRIOR/'models'/f'{fi:02d}.joblib');ck=joblib.load(PRIOR/'checkpoints'/f'{fi:02d}.joblib');np.testing.assert_array_equal(tr,old['train_positions']);np.testing.assert_array_equal(va,old['validation_positions']);references=pd.DataFrame(ck['predictions']);references=references[references.experiment.isin([b+s for b in BASES for s in ['_BASE','_GLOBAL_GLOBAL','_SATELLITE_SUPPORT']])];rows=references.to_dict('records');factory=SimplifiedBases(a,pro,pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO'),OUT/'cache'/f'{fi:02d}',JOINT/'cache'/f'{fi:02d}');factory.original_outer_positions=tr;factory.original_outer_cv=inner;ledger=[];logs=[];pred_cache={};contexts=[];models={};selection=[];candidates=[];details=[]
    def predict(fit,held,excluded):
        fit=np.asarray(fit);held=np.asarray(held);assert not set(fit)&(set(held)|set(excluded)|set(va));tag=(tuple(fit),tuple(held))
        if tag not in pred_cache:
            p=factory.predict_all(fit,held)
            try:factory.cv(fit)
            except ValueError:p['J7']=p['CT3'].copy();logs.append(dict(kind='J7_ct3_fallback_single_group',train=fit.tolist()))
            else:p['J7']=factory.predict(factory.fit(fit),held)[0]
            pred_cache[tag]={b:p[b] for b in BASES}
        ledger.append(dict(train=fit.tolist(),held=held.tolist(),excluded=excluded.tolist()));return pred_cache[tag]
    with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        for j,(c,d) in enumerate(inner):
            aa=tr[c];bb=tr[d];saved=ck['contexts'][j];np.testing.assert_array_equal(aa,saved['aa']);np.testing.assert_array_equal(d,saved['where']);cv=factory.cv(aa);candidate={b:np.full(len(aa),np.nan) for b in BASES};z_a={b:np.full((len(aa),6),np.nan) for b in BASES}
            for e,f in cv:
                fit=aa[e];held=aa[f];base_oof={b:np.full(len(fit),np.nan) for b in BASES}
                try:deep=factory.cv(fit)
                except ValueError:
                    logs.append(dict(kind='candidate_zero_no_group_cv',train=fit.tolist(),held=held.tolist()));proposal={b:np.zeros(len(held)) for b in BASES}
                else:
                    for u,v in deep:
                        pp=predict(fit[u],fit[v],np.r_[held,bb])
                        for b in BASES:base_oof[b][v]=pp[b]
                    proposal={b:ReducedCorrection('R3').fit(x.iloc[fit],y[fit]-base_oof[b]).delta(x.iloc[held]) for b in BASES}
                feature_space=GateFeatures(cfg['definitions']).fit(x.iloc[fit])
                for b in BASES:
                    assert np.isfinite(proposal[b]).all();candidate[b][f]=proposal[b];z_a[b][f]=feature_space.transform(x.iloc[held],saved['bases'][b][f],proposal[b])
            contexts.append(dict(train=aa,where=d,base_oof={b:saved['bases'][b] for b in BASES},candidate_oof=candidate,features_oof=z_a))
            print(f'Weights fold{fi+1} inner{j+1}/{len(inner)}',flush=True)
        final_space=GateFeatures(cfg['definitions']).fit(x.iloc[tr]);external={b:references[references.experiment==b+'_BASE'].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy() for b in BASES}
        for b in BASES:
            bp=old['correctors'][b]['base_oof'];delta=old['correctors'][b]['candidate_oof'];corrector=old['correctors'][b]['corrector'];z=np.full((len(tr),6),np.nan)
            for ctx in contexts:
                d=ctx['where'];features=GateFeatures(cfg['definitions']).fit(x.iloc[ctx['train']]);z[d]=features.transform(x.iloc[tr[d]],bp[d],delta[d])
            external_delta=corrector.delta(x.iloc[va]);external_z=final_space.transform(x.iloc[va],external[b],external_delta)
            for kind,grid in cfg['recipes'].items():
                scores=[]
                for params in grid:
                    pred=np.full(len(tr),np.nan)
                    for ctx in contexts:
                        aa=ctx['train'];d=ctx['where'];m=LearnedWeight(kind,**params).fit(ctx['features_oof'][b],y[aa]-ctx['base_oof'][b],ctx['candidate_oof'][b]);w=m.predict(z[d],delta[d]);pred[d]=bp[d]+w*delta[d]
                    scores.append(dict(**params,rmse=float(np.sqrt(np.mean((pred-y[tr])**2)))))
                best=min(scores,key=lambda z:(round(z['rmse'],12),z['strength'],-z['penalty']));params={k:best[k] for k in ['penalty','strength']};model=LearnedWeight(kind,**params).fit(z,y[tr]-bp,delta);w=model.predict(external_z,external_delta);actual=w*external_delta;assert np.isfinite(actual).all() and max(abs(actual))<=.25+1e-12 and np.all((w>=0)&(w<=1));name=b+'_'+kind;models[name]=dict(weight=model,corrector=corrector,base=b);selection.append(dict(**key,experiment=name,base=b,kind=kind,**best));candidates.extend(dict(**key,experiment=name,**s) for s in scores);rows.extend(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(p)) for i,p in zip(va,external[b]+actual));details.extend(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,base_prediction=float(external[b][j]),candidate_delta=float(external_delta[j]),weight=float(w[j]),applied_delta=float(actual[j]),features=external_z[j].tolist()) for j,i in enumerate(va));models[name]['features_oof']=z
        assert all(not set(r['train'])&(set(r['held'])|set(va)|set(r.get('excluded',[]))) for r in ledger)
        assert all(not set(r['train'])&(set(r['held'])|set(va)) for r in factory.ledger+factory.role.ledger)
        joblib.dump(dict(models=models,feature_space=final_space,train_positions=tr,validation_positions=va),OUT/'models'/f'{fi:02d}.joblib',compress=3)
    joblib.dump(dict(predictions=rows,selection=selection,candidates=candidates,details=details,contexts=contexts,ledger=ledger,logs=logs+factory.logs,seconds=time.perf_counter()-start,warnings=[dict(category=w.category.__name__,message=str(w.message)) for w in caught]),destination,compress=3);print(f'Learned weights {fi+1}/65 {pro} {time.perf_counter()-start:.1f}s',flush=True)

if __name__=='__main__':
    assert not (OUT/'execution_complete.json').exists();cfg=json.loads((OUT/'frozen_design.json').read_text());assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());start=time.perf_counter();joblib.Parallel(n_jobs=cfg['workers'],backend='loky')(joblib.delayed(work)(i) for i in range(65));packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(65)]
    for field in ['predictions','selection','candidates','details']:pd.DataFrame([dict(execution_index=i,**r) for i,p in enumerate(packs) for r in p[field]]).to_parquet(OUT/'tables'/f'{field}.parquet',index=False)
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());(OUT/'execution_complete.json').write_text(json.dumps(dict(status='complete',new_recipes=15,outer_systems=975,seconds=time.perf_counter()-start,no_PRED=True,no_final138_fit=True),indent=2),encoding='utf-8')
