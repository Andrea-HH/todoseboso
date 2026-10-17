"""Strictly nested signal contrast rules over exact external J7 references."""
from pathlib import Path
import sys,json,time,hashlib,warnings
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.neighbor_signal_contrasts import OUT,JOINT,SIGNALS,load_assets,NestedJ7,NeighborContrasts,ContrastAdjustment
from src.geoc_bridge import OLD


def work(fi):
    dest=OUT/'checkpoints'/f'{fi:02d}.joblib'
    if dest.exists():return
    start=time.perf_counter();cfg=json.loads((OUT/'frozen_design.json').read_text());a=load_assets();t=a['a']['train'];y=a['y'];groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO');plan=joblib.load(OLD/'cache/execution_plan.joblib')[fi];tr=np.asarray(plan['train_positions']);va=np.asarray(plan['validation_positions']);inner=joblib.load(OLD/'cache/frozen65_splits.joblib')[fi][5];key={k:plan[k] for k in ['protocol','repeat','fold']};factory=NestedJ7(a,key['protocol'],groups,OUT/'cache'/f'{fi:02d}',JOINT/'cache'/f'{fi:02d}');pos=a['a']['train_global'];geo=a['a']['distance'][np.ix_(pos,pos)];signals=a['role_frame'][list(SIGNALS.values())].to_numpy(float);core=a['core'].to_numpy(float);oof_cache={};contrast_cache={};ledger=[];rows=[];candidates=[];selection=[];models={};details=[]
    def contrast(fit,query,kind,detail=False):
        tag=(tuple(fit),tuple(query),kind)
        if tag not in contrast_cache:
            m=NeighborContrasts(kind,24).fit(signals,core,geo,fit);z,record=m.transform(query,details=True);contrast_cache[tag]=(z,record,m)
        z,record,m=contrast_cache[tag]
        return (z,record,m) if detail else z
    def oof(fit,cv):
        tag=tuple(fit)
        if tag in oof_cache:return oof_cache[tag]
        bp=np.full(len(fit),np.nan);cp=bp.copy();zs={k:np.full((len(fit),6),np.nan) for k in ['GEO','COMPACT']}
        for c,d in cv:
            aa=fit[c];bb=fit[d];base=factory.fit(aa);bp[d],cp[d]=factory.predict(base,bb)
            for kind in zs:zs[kind][d]=contrast(aa,bb,kind)
            ledger.append(dict(train=aa.tolist(),held=bb.tolist(),kind='j7_crossfit_and_contrast'))
        assert np.isfinite(bp).all() and all(np.isfinite(z).all() for z in zs.values());oof_cache[tag]=(bp,cp,zs);return bp,cp,zs
    with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always');outer_oof,ct_oof,z_oof=oof(tr,inner);contexts=[]
        for c,d in inner:
            aa=tr[c];bb=tr[d];bp,cp,z=oof(aa,factory.cv(aa));contexts.append(dict(aa=aa,bb=bb,where=d,bp=bp,cp=cp,z=z))
        original=joblib.load(JOINT/'models'/f'{fi:02d}.joblib');assert np.array_equal(tr,original['train_positions']) and np.array_equal(va,original['validation_positions']);model=original['models']['J7_BOTH'];ct=original['ct3'].predict(t.iloc[va]);from src.signal_role_allocation import predict_role
        bp=model['gate'].predict(model['space'].transform(a['role_frame'].iloc[va]),ct,predict_role(original['experts'][model['variant']],va,a))
        expected=pd.read_parquet(JOINT/'tables/predictions.parquet');expected=expected[(expected.protocol==key['protocol'])&(expected['repeat']==key['repeat'])&(expected.fold==key['fold'])&expected.experiment.isin(['J7_BOTH','CT3'])];reference=expected[expected.experiment=='J7_BOTH'].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO];np.testing.assert_array_equal(bp,reference.y_pred.to_numpy());rows.extend(expected.drop(columns=['index'],errors='ignore').to_dict('records'))
        for name,r in cfg['recipes'].items():
            scores=[];kind=r['neighborhood'];use=r['use']
            for params in [cfg['null_candidate']]+cfg['grid']:
                pred=np.full(len(tr),np.nan)
                for context in contexts:
                    where=context['where'];m=ContrastAdjustment(use,**params).fit(context['z'][kind],y[context['aa']],context['bp'],context['cp']);pred[where]=m.predict(z_oof[kind][where],outer_oof[where],ct_oof[where])
                item=dict(**params,rmse=float(np.sqrt(np.mean((pred-y[tr])**2))));scores.append(item);candidates.append(dict(**key,experiment=name,**item))
            best=min(scores,key=lambda v:(round(v['rmse'],12),v['amplitude'],v['depth'],-v['leaf']));params={k:best[k] for k in ['depth','leaf','amplitude']};adjustment=ContrastAdjustment(use,**params).fit(z_oof[kind],y[tr],outer_oof,ct_oof);z,record,space=contrast(tr,va,kind,True);prediction=adjustment.predict(z,bp,ct);assert np.isfinite(prediction).all();models[name]=dict(adjustment=adjustment,contrast=space);selection.append(dict(**key,experiment=name,**best,fallback=adjustment.fallback));rows.extend(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(v)) for i,v in zip(va,prediction))
            for j,i in enumerate(va):details.append(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,base_prediction=float(bp[j]),ct3_prediction=float(ct[j]),prediction=float(prediction[j]),adjustment=float(prediction[j]-bp[j]),**record[j]))
        assert all(not set(row['train'])&(set(row['held'])|set(va)) for row in ledger+factory.ledger+factory.role.ledger)
        joblib.dump(dict(models=models,base_reference_index=fi,train_positions=tr,validation_positions=va),OUT/'models'/f'{fi:02d}.joblib',compress=3)
    joblib.dump(dict(predictions=rows,candidates=candidates,selection=selection,details=details,ledger=ledger+factory.ledger+factory.role.ledger,deep_support_logs=factory.logs,warnings=[dict(category=w.category.__name__,message=str(w.message)) for w in caught],seconds=time.perf_counter()-start),dest,compress=3);print(f'Contrasts {fi+1}/65 {key["protocol"]} {time.perf_counter()-start:.1f}s',flush=True)


if __name__=='__main__':
    if (OUT/'execution_complete.json').exists():raise FileExistsError('Preserve completed contrast run')
    cfg=json.loads((OUT/'frozen_design.json').read_text());assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());start=time.perf_counter();joblib.Parallel(n_jobs=8,backend='loky')(joblib.delayed(work)(i) for i in range(65));packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(65)]
    for field in ['predictions','selection','candidates']:pd.DataFrame([dict(r,execution_index=i) for i,p in enumerate(packs) for r in p[field]]).to_parquet(OUT/'tables'/f'{field}.parquet',index=False)
    (OUT/'audit/deep_support_logs.json').write_text(json.dumps([dict(r,execution_index=i) for i,p in enumerate(packs) for r in p['deep_support_logs']],indent=2),encoding='utf-8');(OUT/'audit/warnings.json').write_text(json.dumps([dict(r,execution_index=i) for i,p in enumerate(packs) for r in p['warnings']],indent=2),encoding='utf-8');assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());(OUT/'execution_complete.json').write_text(json.dumps(dict(status='complete',recipes=4,folds=65,seconds=time.perf_counter()-start,protected_sources_unchanged=True,no_PRED=True,no_final138_fit=True),indent=2),encoding='utf-8')
