"""Frozen factorial base architecture ablations with R3 availability control."""
from pathlib import Path
import sys,json,time,hashlib,warnings
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.architecture_decomposition import OUT,DecompositionFactory,load_assets,load_design
from src.indicator_neighborhoods import OUT as INDICATORS,ReducedCorrection,REDUCTIONS
from src.geoc_bridge import OLD
REFERENCE=ROOT/'outputs/modeling/learned_r3_weight/v1'

def work(fi):
    path=OUT/'checkpoints'/f'{fi:02d}.joblib'
    if path.exists():return
    start=time.perf_counter();a=load_assets();cfg=load_design();t=a['a']['train'];y=a['y'];x=pd.read_parquet(INDICATORS/'cache/features_train138_target_free.parquet');assert x.ID_POLIGONO.tolist()==t.ID_POLIGONO.tolist();pro,re,fold,tr,va,inner=joblib.load(OLD/'cache/frozen65_splits.joblib')[fi];tr=np.asarray(tr);va=np.asarray(va);key=dict(protocol=pro,repeat=re,fold=fold);factory=DecompositionFactory(a,pro,pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO'),OUT/'cache'/f'{fi:02d}',tr,inner);oof={n:np.full(len(tr),np.nan) for n in cfg['recipes']};contexts=[];rows=[];selections=[];candidates=[];adjustments={};details=[];ledger=[]
    with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        for j,(c,d) in enumerate(inner):
            aa=tr[c];bb=tr[d];prediction=factory.predict(factory.fit(aa),bb)
            for n in cfg['recipes']:oof[n][d]=prediction[n]
            cv=factory.cv(aa);deep={n:np.full(len(aa),np.nan) for n in cfg['recipes']}
            for e,f in cv:
                fit=aa[e];held=aa[f];pp=factory.predict(factory.fit(fit),held)
                for n in cfg['recipes']:deep[n][f]=pp[n]
                ledger.append(dict(train=fit.tolist(),held=held.tolist(),excluded_inner=bb.tolist()))
            contexts.append(dict(aa=aa,where=d,base_oof=deep));print(f'Decompose fold{fi+1} inner{j+1}/{len(inner)} {time.perf_counter()-start:.1f}s',flush=True)
        outer_model=factory.fit(tr);external=factory.predict(outer_model,va);valid_query=np.isfinite(x.iloc[va][REDUCTIONS['R3']].to_numpy(float)).all(axis=1)
        for name,spec in cfg['recipes'].items():
            delta=np.full(len(tr),np.nan)
            for ctx in contexts:
                aa=ctx['aa'];d=ctx['where'];m=ReducedCorrection('R3').fit(x.iloc[aa],y[aa]-ctx['base_oof'][name]);dd=m.delta(x.iloc[tr[d]]);complete=np.isfinite(x.iloc[tr[d]][REDUCTIONS['R3']].to_numpy(float)).all(axis=1);delta[d]=dd*complete
            scores=[dict(strength=s,rmse=float(np.sqrt(np.mean((oof[name]+s*delta-y[tr])**2)))) for s in cfg['strengths']];best=min(scores,key=lambda v:(round(v['rmse'],12),v['strength']));m=ReducedCorrection('R3').fit(x.iloc[tr],y[tr]-oof[name]);actual=best['strength']*valid_query*m.delta(x.iloc[va]);assert np.isfinite(actual).all() and max(abs(actual))<=.25+1e-12;adjustments[name]=dict(corrector=m,strength=best['strength'],base_oof=oof[name]);selections.append(dict(**key,experiment=name+'_MASK',**best));candidates.extend(dict(**key,experiment=name+'_MASK',**s) for s in scores)
            for suffix,pred in [('_BASE',external[name]),('_MASK',external[name]+actual)]:rows.extend(dict(**key,experiment=name+suffix,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(p)) for i,p in zip(va,pred))
            route=outer_model['routes'][name]
            for i,w,dd in zip(va,route['gate'].weights(route['space'].transform(a['role_frame'].iloc[va])),actual):details.append(dict(**key,experiment=name+'_MASK',ID_POLIGONO=t.iloc[i].ID_POLIGONO,expert_weight=float(w),applied_delta=float(dd),gate_k=route['selection']['k'],internal_amplitude=outer_model['experts'][spec['local']]['amplitude'] if spec['internal']=='ON' else 0.))
        old=joblib.load(REFERENCE/'checkpoints'/f'{fi:02d}.joblib');refs=pd.DataFrame(old['predictions']);refs=refs[refs.experiment.isin(['CT3_BASE','CT3_MASK','J7_GLOBAL_GLOBAL'])];rows.extend(refs.to_dict('records'))
        for name,ref in [('FULL7_ON_RAW_BASE','SHARES_BASE'),('FULL7_ON_RAW_MASK','SHARES_MASK')]:
            old_rows=pd.DataFrame(old['predictions']);z=pd.DataFrame(rows);expected=old_rows[old_rows.experiment==ref].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy();actual=z[z.experiment==name].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy();np.testing.assert_allclose(actual,expected,atol=1e-12,rtol=0)
        assert all(not set(r['train'])&(set(r['held'])|set(va)|set(r.get('excluded_inner',[]))) for r in ledger+factory.ledger+factory.helper.ledger+factory.helper.role.ledger)
        joblib.dump(dict(base_model=outer_model,adjustments=adjustments,train_positions=tr,validation_positions=va),OUT/'models'/f'{fi:02d}.joblib',compress=3)
    joblib.dump(dict(predictions=rows,selection=selections,candidates=candidates,details=details,contexts=contexts,ledger=ledger+factory.ledger+factory.helper.ledger+factory.helper.role.ledger,logs=factory.logs+factory.helper.logs,seconds=time.perf_counter()-start,warnings=[dict(category=w.category.__name__,message=str(w.message)) for w in caught]),path,compress=3);print(f'Architecture {fi+1}/65 {pro} {time.perf_counter()-start:.1f}s',flush=True)

if __name__=='__main__':
    assert not (OUT/'execution_complete.json').exists();cfg=load_design();assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());start=time.perf_counter();joblib.Parallel(n_jobs=cfg['workers'],backend='loky')(joblib.delayed(work)(i) for i in range(65));packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(65)]
    for field in ['predictions','selection','candidates','details']:pd.DataFrame([dict(execution_index=i,**r) for i,p in enumerate(packs) for r in p[field]]).to_parquet(OUT/'tables'/f'{field}.parquet',index=False)
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());(OUT/'execution_complete.json').write_text(json.dumps(dict(status='complete',base_recipes=48,entries=99,outer_folds=65,seconds=time.perf_counter()-start,no_PRED=True,no_final138_fit=True),indent=2),encoding='utf-8')
