"""Base simplification crossed with global or local-distribution-conditioned R3."""
from pathlib import Path
import sys,json,time,hashlib,warnings
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.base_distribution_correction import DistributionWeight,SimplifiedBases,load_design
from src.indicator_neighborhoods import OUT as SOURCE,ENGINEERING,CALIBRATION,ReducedCorrection
from src.neighbor_signal_contrasts import load_assets,JOINT
from src.geoc_bridge import OLD
OUT=ROOT/'outputs/modeling/base_distribution_correction/v1'
BASES=['CT3','RAW7','EXPERT7','EQUAL7','SHARES','J7']
NEWBASES=['RAW7','EXPERT7','EQUAL7','SHARES']

def work(fi):
    destination=OUT/'checkpoints'/f'{fi:02d}.joblib'
    if destination.exists():return
    start=time.perf_counter();cfg=load_design(OUT);assets=load_assets();t=assets['a']['train'];y=assets['y'];x=pd.read_parquet(SOURCE/'cache/features_train138_target_free.parquet');assert x.ID_POLIGONO.tolist()==t.ID_POLIGONO.tolist();pro,re,fold,tr,va,inner=joblib.load(OLD/'cache/frozen65_splits.joblib')[fi];tr=np.asarray(tr);va=np.asarray(va);key=dict(protocol=pro,repeat=re,fold=fold)
    groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO');factory=SimplifiedBases(assets,pro,groups,OUT/'cache'/f'{fi:02d}',JOINT/'cache'/f'{fi:02d}');factory.original_outer_positions=tr;factory.original_outer_cv=inner;old=joblib.load(CALIBRATION/'checkpoints'/f'{fi:02d}.joblib');eng=joblib.load(ENGINEERING/'checkpoints'/f'{fi:02d}.joblib');np.testing.assert_array_equal(old['calibration']['train_positions'],tr);oo={n:np.full(len(tr),np.nan) for n in NEWBASES};oo.update(CT3=old['calibration']['ct3_oof'],J7=old['calibration']['base_oof']);contexts=[];ledger=[];models={};selection=[];rows=[];candidates=[];details=[]
    with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        for j,(c,d) in enumerate(inner):
            aa=tr[c];bb=tr[d];pred=factory.predict_all(aa,bb)
            for n in NEWBASES:oo[n][d]=pred[n]
            np.testing.assert_allclose(pred['CT3'],oo['CT3'][d],atol=1e-12,rtol=0)
            cv=factory.cv(aa);base_oof={n:np.full(len(aa),np.nan) for n in NEWBASES}
            for e,f in cv:
                fit=aa[e];held=aa[f];deep=factory.predict_all(fit,held)
                for n in NEWBASES:base_oof[n][f]=deep[n]
                ledger.append(dict(train=fit.tolist(),held=held.tolist(),excluded_inner=bb.tolist()))
            saved=eng['contexts'][j];np.testing.assert_array_equal(saved['aa'],aa);np.testing.assert_array_equal(saved['where'],d);base_oof.update(saved['bases']);contexts.append(dict(aa=aa,where=d,bases=base_oof))
        outer=factory.predict_all(tr,va);references=pd.DataFrame(old['predictions']);references=references[references.experiment.isin(['CT3','J7_BOTH'])];external={n:outer[n] for n in NEWBASES}
        for n,ref in [('CT3','CT3'),('J7','J7_BOTH')]:external[n]=references[references.experiment==ref].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy()
        np.testing.assert_allclose(outer['CT3'],external['CT3'],atol=1e-12,rtol=0)
        for n in BASES:
            rows.extend(dict(**key,experiment=n+'_BASE',ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(p)) for i,p in zip(va,external[n]));assert np.isfinite(oo[n]).all()
        weights={};outer_weights={};weight_models={}
        for geometry in cfg['geometries']:
            for k in cfg['k_grid']:
                inner_weights={use:np.zeros(len(tr)) for use in cfg['uses']}
                for ctx in contexts:
                    space=DistributionWeight(geometry,k,cfg['definitions']).fit(x.iloc[ctx['aa']])
                    for use in cfg['uses']:inner_weights[use][ctx['where']]=space.weights(x.iloc[tr[ctx['where']]],use)
                space=DistributionWeight(geometry,k,cfg['definitions']).fit(x.iloc[tr]);weight_models[(geometry,k)]=space
                for use in cfg['uses']:weights[(geometry,k,use)]=inner_weights[use];outer_weights[(geometry,k,use)]=space.weights(x.iloc[va],use,True)
        for n in BASES:
            delta=np.full(len(tr),np.nan)
            for ctx in contexts:
                m=ReducedCorrection('R3').fit(x.iloc[ctx['aa']],y[ctx['aa']]-ctx['bases'][n]);delta[ctx['where']]=m.delta(x.iloc[tr[ctx['where']]])
            corrector=ReducedCorrection('R3').fit(x.iloc[tr],y[tr]-oo[n]);external_delta=corrector.delta(x.iloc[va]);models[n]=dict(corrector=corrector,base_oof=oo[n],candidate_oof=delta)
            for geometry,use in [('GLOBAL','GLOBAL')]+[(g,u) for g in cfg['geometries'] for u in cfg['uses']]:
                name=f'{n}_{geometry}_{use}';scores=[]
                for k in ([0] if geometry=='GLOBAL' else cfg['k_grid']):
                    w=1. if geometry=='GLOBAL' else weights[(geometry,k,use)]
                    for amp in cfg['amplitudes']:scores.append(dict(k=k,amplitude=amp,rmse=float(np.sqrt(np.mean((oo[n]+(amp/.5)*w*delta-y[tr])**2)))))
                best=min(scores,key=lambda z:(round(z['rmse'],12),z['amplitude'],-z['k']));selection.append(dict(**key,experiment=name,base=n,geometry=geometry,use=use,**best));candidates.extend(dict(**key,experiment=name,**z) for z in scores)
                w,record=(np.ones(len(va)),None) if geometry=='GLOBAL' else outer_weights[(geometry,best['k'],use)];actual=(best['amplitude']/.5)*w*external_delta;pred=external[n]+actual;assert np.isfinite(pred).all() and max(abs(actual))<=.25+1e-12;rows.extend(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(p)) for i,p in zip(va,pred))
                if record is not None:
                    for i,r,ww,dd in zip(va,record,w,actual):
                        assert set(r['neighbor_ids']).issubset(set(t.iloc[tr].ID_POLIGONO)) and not set(r['neighbor_ids'])&set(t.iloc[va].ID_POLIGONO);details.append(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,weight=float(ww),applied_delta=float(dd),**r))
        assert all(not set(r['train'])&(set(r['held'])|set(va)|set(r.get('excluded_inner',[]))) for r in ledger+factory.ledger+factory.role.ledger)
        # Freeze the outer base models needed to replay each new simpler architecture.
        base_pack=dict(ct3=factory.ct3(tr),expert=factory.expert(tr),shares=factory.shares(tr));joblib.dump(dict(bases=base_pack,correctors=models,weight_models=weight_models,train_positions=tr,validation_positions=va),OUT/'models'/f'{fi:02d}.joblib',compress=3)
    joblib.dump(dict(predictions=rows,selection=selection,candidates=candidates,details=details,contexts=contexts,ledger=ledger+factory.ledger+factory.role.ledger,logs=factory.logs,seconds=time.perf_counter()-start,warnings=[dict(category=w.category.__name__,message=str(w.message)) for w in caught]),destination,compress=3);print(f'Bases/distribution {fi+1}/65 {pro} {time.perf_counter()-start:.1f}s',flush=True)

if __name__=='__main__':
    assert not (OUT/'execution_complete.json').exists();cfg=load_design(OUT);assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());start=time.perf_counter();joblib.Parallel(n_jobs=cfg['workers'],backend='loky')(joblib.delayed(work)(fi) for fi in range(65));packs=[joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib') for fi in range(65)]
    for field in ['predictions','selection','candidates','details']:pd.DataFrame([dict(execution_index=i,**r) for i,p in enumerate(packs) for r in p[field]]).to_parquet(OUT/'tables'/f'{field}.parquet',index=False)
    (OUT/'warnings.json').write_text(json.dumps([dict(execution_index=i,**r) for i,p in enumerate(packs) for r in p['warnings']],indent=2),encoding='utf-8');assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());(OUT/'execution_complete.json').write_text(json.dumps(dict(status='complete',outer_folds=65,entries=48,seconds=time.perf_counter()-start,no_PRED=True,no_final138_fit=True),indent=2),encoding='utf-8')
