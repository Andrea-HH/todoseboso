"""Fixed meta-regularization sensitivities using original nested OOF proposals."""
from pathlib import Path
import sys,json,time,hashlib,warnings
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.learned_r3_weight import OUT,GateFeatures,LearnedWeight
from src.learned_r3_protocol import load_design
from src.indicator_neighborhoods import OUT as INDICATORS
from src.geoc_bridge import OLD
PRIOR=ROOT/'outputs/modeling/base_distribution_correction/v1';BASES=['CT3','J7','SHARES']

def work(fi):
    destination=OUT/'checkpoints'/f'{fi:02d}.joblib'
    if destination.exists():return
    start=time.perf_counter();cfg=load_design();t=pd.read_parquet(OLD/'cache/train138.parquet');y=t.RENDIMIENTO_T_HA.to_numpy();x=pd.read_parquet(INDICATORS/'cache/features_train138_target_free.parquet');assert x.ID_POLIGONO.tolist()==t.ID_POLIGONO.tolist();pro,re,fold,tr,va,inner=joblib.load(OLD/'cache/frozen65_splits.joblib')[fi];tr=np.asarray(tr);va=np.asarray(va);key=dict(protocol=pro,repeat=re,fold=fold);old=joblib.load(PRIOR/'models'/f'{fi:02d}.joblib');ck=joblib.load(PRIOR/'checkpoints'/f'{fi:02d}.joblib');np.testing.assert_array_equal(tr,old['train_positions']);np.testing.assert_array_equal(va,old['validation_positions']);references=pd.DataFrame(ck['predictions']);references=references[references.experiment.isin([b+s for b in BASES for s in ['_BASE','_GLOBAL_GLOBAL','_SATELLITE_SUPPORT']])];rows=references.to_dict('records');models={};selection=[];candidates=[];details=[];ledger=[]
    with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always');final_space=GateFeatures(cfg['definitions']).fit(x.iloc[tr]);feature_spaces=[]
        for ctx,(c,d) in zip(ck['contexts'],inner):
            aa=np.asarray(ctx['aa']);np.testing.assert_array_equal(aa,tr[c]);np.testing.assert_array_equal(ctx['where'],d);assert not set(aa)&(set(tr[d])|set(va));feature_spaces.append(GateFeatures(cfg['definitions']).fit(x.iloc[aa]));ledger.append(dict(train=aa.tolist(),held=tr[d].tolist(),excluded=va.tolist()))
        for rec in ck['ledger']:assert not set(rec['train'])&(set(rec['held'])|set(va)|set(rec.get('excluded_inner',[])))
        for b in BASES:
            bp=old['correctors'][b]['base_oof'];delta=old['correctors'][b]['candidate_oof'];corrector=old['correctors'][b]['corrector'];z=np.full((len(tr),6),np.nan)
            for ctx,space in zip(ck['contexts'],feature_spaces):
                d=ctx['where'];z[d]=space.transform(x.iloc[tr[d]],bp[d],delta[d])
            external=references[references.experiment==b+'_BASE'].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy();external_delta=corrector.delta(x.iloc[va]);external_z=final_space.transform(x.iloc[va],external,external_delta)
            for variant,spec in cfg['recipes'].items():
                kind=spec['kind'];scores=[]
                for strength in ([0.,.5,1.] if kind=='MASK' else [1.]):
                    m=LearnedWeight(kind,spec['penalty'],strength).fit(z,y[tr]-bp,delta);prediction=bp+m.predict(z,delta)*delta;scores.append(dict(penalty=spec['penalty'],strength=strength,rmse=float(np.sqrt(np.mean((prediction-y[tr])**2)))))
                best=min(scores,key=lambda z:(round(z['rmse'],12),z['strength']));model=LearnedWeight(kind,best['penalty'],best['strength']).fit(z,y[tr]-bp,delta);w=model.predict(external_z,external_delta);actual=w*external_delta;assert np.isfinite(actual).all() and max(abs(actual))<=.25+1e-12 and np.all((w>=0)&(w<=1));name=b+'_'+variant;models[name]=dict(weight=model,corrector=corrector,base=b,features_oof=z,base_oof=bp,candidate_oof=delta);selection.append(dict(**key,experiment=name,base=b,kind=kind,selection_basis='inner_R3_OOF' if kind=='MASK' else 'fixed_prespecified_penalty_meta_fit',**best));candidates.extend(dict(**key,experiment=name,**s) for s in scores);rows.extend(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(p)) for i,p in zip(va,external+actual));details.extend(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,base_prediction=float(external[j]),candidate_delta=float(external_delta[j]),weight=float(w[j]),applied_delta=float(actual[j]),features=external_z[j].tolist()) for j,i in enumerate(va))
        joblib.dump(dict(models=models,feature_space=final_space,train_positions=tr,validation_positions=va),OUT/'models'/f'{fi:02d}.joblib',compress=3)
    joblib.dump(dict(predictions=rows,selection=selection,candidates=candidates,details=details,ledger=ledger,logs=[],seconds=time.perf_counter()-start,warnings=[dict(category=w.category.__name__,message=str(w.message)) for w in caught]),destination,compress=3);print(f'Fixed learned weights {fi+1}/65 {pro} {time.perf_counter()-start:.1f}s',flush=True)

if __name__=='__main__':
    assert not (OUT/'execution_complete.json').exists();cfg=load_design();assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());start=time.perf_counter();joblib.Parallel(n_jobs=cfg['workers'],backend='loky')(joblib.delayed(work)(i) for i in range(65));packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(65)]
    for field in ['predictions','selection','candidates','details']:pd.DataFrame([dict(execution_index=i,**r) for i,p in enumerate(packs) for r in p[field]]).to_parquet(OUT/'tables'/f'{field}.parquet',index=False)
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());(OUT/'execution_complete.json').write_text(json.dumps(dict(status='complete',new_recipes=24,outer_systems=1560,seconds=time.perf_counter()-start,no_PRED=True,no_final138_fit=True),indent=2),encoding='utf-8')
