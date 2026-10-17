"""Paired raw/engineered blocks over exact CT3/J7, with nested residual calibration."""
from pathlib import Path
import sys,json,time,hashlib,warnings
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.signal_feature_engineering import OUT,EngineeringAdjustment
from src.neighbor_signal_contrasts import JOINT,load_assets
from src.neighbor_signal_linear import OUT as PREVIOUS,ReuseNestedJ7
from src.geoc_bridge import OLD


def work(fi):
    dest=OUT/'checkpoints'/f'{fi:02d}.joblib'
    if dest.exists():return
    start=time.perf_counter();cfg=json.loads((OUT/'frozen_design.json').read_text());a=load_assets();t=a['a']['train'];y=a['y'];x=pd.read_parquet(OUT/'cache/features_train138_target_free.parquet');assert x.ID_POLIGONO.tolist()==t.ID_POLIGONO.tolist()
    plan=joblib.load(OLD/'cache/execution_plan.joblib')[fi];tr=np.asarray(plan['train_positions']);va=np.asarray(plan['validation_positions']);inner=joblib.load(OLD/'cache/frozen65_splits.joblib')[fi][5];key={k:plan[k] for k in ['protocol','repeat','fold']}
    groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO');factory=ReuseNestedJ7(a,key['protocol'],groups,OUT/'cache'/f'{fi:02d}',JOINT/'cache'/f'{fi:02d}')
    saved=joblib.load(PREVIOUS/'checkpoints'/f'{fi:02d}.joblib');np.testing.assert_array_equal(saved['calibration']['train_positions'],tr)
    oo={'J7':saved['calibration']['base_oof'],'CT3':saved['calibration']['ct3_oof']};ledger=[];rows=[];candidates=[];selection=[];models={};contexts=[];checks=[]
    with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        for c,d in inner:
            aa=tr[c];bb=tr[d];cv=factory.cv(aa);bp=np.full(len(aa),np.nan);cp=bp.copy()
            for e,f in cv:
                fit=aa[e];held=aa[f];m=factory.fit(fit);bp[f],cp[f]=factory.predict(m,held);ledger.append(dict(train=fit.tolist(),held=held.tolist(),excluded_inner=bb.tolist()))
            assert np.isfinite(bp).all() and np.isfinite(cp).all();contexts.append(dict(aa=aa,where=d,bases={'J7':bp,'CT3':cp}))
        # Only original external OOF references are used for evaluation.
        refs=[r for r in saved['predictions'] if r['experiment'] in ['J7_BOTH','CT3']];rows.extend(refs)
        external={base:pd.DataFrame([r for r in refs if r['experiment']==name]).set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy() for base,name in [('J7','J7_BOTH'),('CT3','CT3')]}
        for name,r in cfg['recipes'].items():
            base=r['base'];scores=[]
            grid=[cfg['null_candidate']]+cfg['grid']
            if r['block']=='SHIFT':grid=[cfg['null_candidate']]+[dict(alpha=1.,l1_ratio=.9,amplitude=amp) for amp in [.25,.5]]
            for params in grid:
                pred=np.full(len(tr),np.nan)
                for ctx in contexts:
                    aa=ctx['aa'];where=ctx['where'];m=EngineeringAdjustment(r['block'],r['columns'],**params).fit(x.iloc[aa],y[aa],ctx['bases'][base]);pred[where]=m.predict(x.iloc[tr[where]],oo[base][where])
                item=dict(**params,rmse=float(np.sqrt(np.mean((pred-y[tr])**2))));scores.append(item);candidates.append(dict(**key,experiment=name,**item))
            best=min(scores,key=lambda v:(round(v['rmse'],12),v['amplitude'],-v['alpha'],-v['l1_ratio']));params={k:best[k] for k in ['alpha','l1_ratio','amplitude']}
            m=EngineeringAdjustment(r['block'],r['columns'],**params).fit(x.iloc[tr],y[tr],oo[base]);pred=m.predict(x.iloc[va],external[base]);assert np.isfinite(pred).all() and max(abs(pred-external[base]))<=.25+1e-12
            models[name]=m;selection.append(dict(**key,experiment=name,base=base,block=r['block'],**best,n_features=len(m.feature_names),n_active=int(m.support.sum()),n_nonzero=int(np.count_nonzero(m.model.coef_)) if m.model is not None else 0))
            rows.extend(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(v)) for i,v in zip(va,pred))
            checks.append(dict(experiment=name,null_rmse=float(scores[0]['rmse']),direct_base_rmse=float(np.sqrt(np.mean((oo[base]-y[tr])**2)))))
        assert all(not set(r['train'])&(set(r['held'])|set(va)|set(r.get('excluded_inner',[]))) for r in ledger+factory.ledger+factory.role.ledger)
        joblib.dump(dict(models=models,train_positions=tr,validation_positions=va),OUT/'models'/f'{fi:02d}.joblib',compress=3)
    joblib.dump(dict(predictions=rows,candidates=candidates,selection=selection,ledger=ledger+factory.ledger+factory.role.ledger,calibration_checks=checks,contexts=contexts,warm_hits=factory.warm_hits,support_logs=factory.logs,warnings=[dict(category=w.category.__name__,message=str(w.message)) for w in caught],seconds=time.perf_counter()-start),dest,compress=3)
    print(f'Engineering {fi+1}/65 {key["protocol"]} {time.perf_counter()-start:.1f}s',flush=True)


if __name__=='__main__':
    if (OUT/'execution_complete.json').exists():raise FileExistsError('Preserve completed engineering run')
    cfg=json.loads((OUT/'frozen_design.json').read_text());assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());start=time.perf_counter()
    joblib.Parallel(n_jobs=cfg['workers'],backend='loky')(joblib.delayed(work)(i) for i in range(65))
    packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(65)]
    for field in ['predictions','selection','candidates']:pd.DataFrame([dict(r,execution_index=i) for i,p in enumerate(packs) for r in p[field]]).to_parquet(OUT/'tables'/f'{field}.parquet',index=False)
    for field in ['warnings','support_logs']:(OUT/'audit'/f'{field}.json').write_text(json.dumps([dict(r,execution_index=i) for i,p in enumerate(packs) for r in p[field]],indent=2),encoding='utf-8')
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    (OUT/'execution_complete.json').write_text(json.dumps(dict(status='complete',recipes=len(cfg['recipes']),folds=65,seconds=time.perf_counter()-start,protected_sources_unchanged=True,no_PRED=True,no_final138_fit=True),indent=2),encoding='utf-8')
