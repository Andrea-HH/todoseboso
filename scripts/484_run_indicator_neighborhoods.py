"""Select neighbor count/strength internally; paired direct and weight roles."""
from pathlib import Path
import sys,json,time,hashlib,warnings
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.indicator_neighborhoods import OUT,ENGINEERING,CALIBRATION,REDUCTIONS,ReducedCorrection,LocalCorrection


def work(fi):
    dest=OUT/'checkpoints'/f'{fi:02d}.joblib'
    if dest.exists():return
    start=time.perf_counter();cfg=json.loads((OUT/'frozen_design.json').read_text());t=pd.read_parquet(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet');x=pd.read_parquet(OUT/'cache/features_train138_target_free.parquet');assert x.ID_POLIGONO.tolist()==t.ID_POLIGONO.tolist();y=t.RENDIMIENTO_T_HA.to_numpy();plan=joblib.load(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/execution_plan.joblib')[fi];tr=np.asarray(plan['train_positions']);va=np.asarray(plan['validation_positions']);key={k:plan[k] for k in ['protocol','repeat','fold']};old=joblib.load(CALIBRATION/'checkpoints'/f'{fi:02d}.joblib');source=joblib.load(ENGINEERING/'checkpoints'/f'{fi:02d}.joblib');np.testing.assert_array_equal(old['calibration']['train_positions'],tr)
    for rec in source['ledger']:assert not set(rec['train'])&(set(rec['held'])|set(va)|set(rec.get('excluded_inner',[])))
    refs=[r for r in old['predictions'] if r['experiment'] in ['CT3','J7_BOTH']];rows=list(refs);models={};selections=[];candidates=[];details=[];calibrations=[]
    with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        for base,ref in [('CT3','CT3'),('J7','J7_BOTH')]:
            bp=old['calibration']['ct3_oof' if base=='CT3' else 'base_oof'];residual=y[tr]-bp;external=pd.DataFrame(refs).query('experiment==@ref').set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy();r4_oof=None
            for reduction in REDUCTIONS:
                delta=np.full(len(tr),np.nan)
                for ctx in source['contexts']:
                    aa=np.asarray(ctx['aa']);d=np.asarray(ctx['where']);assert not set(aa)&(set(tr[d])|set(va));m=ReducedCorrection(reduction).fit(x.iloc[aa],y[aa]-ctx['bases'][base]);delta[d]=m.delta(x.iloc[tr[d]])
                assert np.isfinite(delta).all()
                if reduction=='R4':r4_oof=delta.copy()
                scores=[dict(amplitude=amp,rmse=float(np.sqrt(np.mean((bp+(amp/.5)*delta-y[tr])**2)))) for amp in cfg['amplitudes']];best=min(scores,key=lambda z:(round(z['rmse'],12),z['amplitude']));name=base+'_GLOBAL_'+reduction;model=ReducedCorrection(reduction).fit(x.iloc[tr],residual);pred=external+(best['amplitude']/.5)*model.delta(x.iloc[va]);models[name]=dict(mode='GLOBAL',model=model,amplitude=best['amplitude']);selections.append(dict(**key,experiment=name,mode='GLOBAL',reduction=reduction,param=0,**best));candidates.extend(dict(**key,experiment=name,**r) for r in scores);rows.extend(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(p)) for i,p in zip(va,pred))
            assert r4_oof is not None;calibrations.append(dict(base=base,train_positions=tr,candidate_oof=r4_oof,base_oof=bp))
            for mode in ['KNN','CLUSTER']:
                for geometry in ['GEO','PHYSICAL','SATELLITE']:
                    params=cfg['k_grid' if mode=='KNN' else 'cluster_grid'];scores=[]
                    for param in params:
                        delta=np.full(len(tr),np.nan)
                        for ctx in source['contexts']:
                            aa=np.asarray(ctx['aa']);d=np.asarray(ctx['where']);m=LocalCorrection(geometry,mode,param,cfg['definitions']).fit(x.iloc[aa],y[aa]-ctx['bases'][base]);delta[d]=m.predict(x.iloc[tr[d]],'DIRECT',.5)
                        assert np.isfinite(delta).all()
                        for amp in cfg['amplitudes']:scores.append(dict(param=param,amplitude=amp,rmse=float(np.sqrt(np.mean((bp+(amp/.5)*delta-y[tr])**2)))))
                    best=min(scores,key=lambda z:(round(z['rmse'],12),z['amplitude'],-z['param'] if mode=='KNN' else z['param']));model=LocalCorrection(geometry,mode,best['param'],cfg['definitions']).fit(x.iloc[tr],residual,r4_oof)
                    for use in ['DIRECT','WEIGHT']:
                        name=f'{base}_{mode}_{geometry}_{use}';delta,record=model.predict(x.iloc[va],use,best['amplitude'],True);pred=external+delta;assert np.isfinite(pred).all() and max(abs(delta))<=.25+1e-12;models[name]=dict(mode=mode,model=model,use=use,amplitude=best['amplitude']);selections.append(dict(**key,experiment=name,mode=mode,geometry=geometry,use=use,**best));rows.extend(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(p)) for i,p in zip(va,pred));candidates.extend(dict(**key,experiment=name,**r) for r in scores)
                        details.extend(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,base_prediction=external[j],prediction=pred[j],**record[j]) for j,i in enumerate(va))
        joblib.dump(dict(models=models,train_positions=tr,validation_positions=va),OUT/'models'/f'{fi:02d}.joblib',compress=3)
    joblib.dump(dict(predictions=rows,models_selected=selections,candidates=candidates,details=details,calibration=calibrations,source_ledger_count=len(source['ledger']),warnings=[dict(category=w.category.__name__,message=str(w.message)) for w in caught],seconds=time.perf_counter()-start),dest,compress=3);print(f'Neighborhoods {fi+1}/65 {key["protocol"]} {time.perf_counter()-start:.1f}s',flush=True)


if __name__=='__main__':
    if (OUT/'execution_complete.json').exists():raise FileExistsError('Preserve completed neighborhood run')
    cfg=json.loads((OUT/'frozen_design.json').read_text());assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());start=time.perf_counter();joblib.Parallel(n_jobs=cfg['workers'],backend='loky')(joblib.delayed(work)(i) for i in range(65));packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(65)]
    for field in ['predictions','models_selected','candidates','details']:pd.DataFrame([dict(execution_index=i,**r) for i,p in enumerate(packs) for r in p[field]]).to_parquet(OUT/'tables'/f'{field}.parquet',index=False)
    (OUT/'audit/warnings.json').write_text(json.dumps([dict(execution_index=i,**r) for i,p in enumerate(packs) for r in p['warnings']],indent=2),encoding='utf-8');assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());(OUT/'execution_complete.json').write_text(json.dumps(dict(status='complete',recipes=34,outer_folds=65,seconds=time.perf_counter()-start,protected_sources_unchanged=True,no_PRED=True,no_final138_fit=True),indent=2),encoding='utf-8')
