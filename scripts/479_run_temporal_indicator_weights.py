"""Fit continuous correction weights with strictly cross-fitted candidate deltas."""
from pathlib import Path
import sys,json,time,hashlib,warnings
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.temporal_indicator_weights import OUT,ENGINEERING,BASE_CALIBRATION,PARENTS,INDICATORS,FixedCorrection,ContinuousWeight


def work(fi):
    dest=OUT/'checkpoints'/f'{fi:02d}.joblib'
    if dest.exists():return
    start=time.perf_counter();cfg=json.loads((OUT/'frozen_design.json').read_text());t=pd.read_parquet(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet');x=pd.read_parquet(OUT/'cache/features_train138_target_free.parquet');assert x.ID_POLIGONO.tolist()==t.ID_POLIGONO.tolist();y=t.RENDIMIENTO_T_HA.to_numpy()
    plan=joblib.load(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/execution_plan.joblib')[fi];tr=np.asarray(plan['train_positions']);va=np.asarray(plan['validation_positions']);key={k:plan[k] for k in ['protocol','repeat','fold']}
    base_ck=joblib.load(BASE_CALIBRATION/'checkpoints'/f'{fi:02d}.joblib');inner_ck=joblib.load(ENGINEERING/'checkpoints'/f'{fi:02d}.joblib');np.testing.assert_array_equal(base_ck['calibration']['train_positions'],tr);assert not set(tr)&set(va)
    for rec in inner_ck['ledger']:assert not set(rec['train'])&(set(rec['held'])|set(va)|set(rec.get('excluded_inner',[])))
    oo={'J7':base_ck['calibration']['base_oof'],'CT3':base_ck['calibration']['ct3_oof']};refs=[r for r in base_ck['predictions'] if r['experiment'] in ['J7_BOTH','CT3']];rows=list(refs);models={};details=[];ledger=[];calibration=[]
    with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        for base,reference in [('CT3','CT3'),('J7','J7_BOTH')]:
            residual=y[tr]-oo[base];candidate_oof=np.full(len(tr),np.nan)
            for ctx in inner_ck['contexts']:
                aa=np.asarray(ctx['aa']);where=np.asarray(ctx['where']);bb=tr[where];assert not set(aa)&(set(bb)|set(va))
                m=FixedCorrection(PARENTS).fit(x.iloc[aa],y[aa]-ctx['bases'][base]);candidate_oof[where]=m.predict_delta(x.iloc[bb]);ledger.append(dict(base=base,train=aa.tolist(),held=bb.tolist(),outer_held=va.tolist()))
            assert np.isfinite(candidate_oof).all();calibration.append(dict(base=base,train_positions=tr,candidate_oof=candidate_oof,base_oof=oo[base]))
            candidate=FixedCorrection(PARENTS).fit(x.iloc[tr],residual);delta=candidate.predict_delta(x.iloc[va]);bp=pd.DataFrame(refs).query('experiment==@reference').set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy()
            for kind in ['C4_FIXED','C4_CONSTANT','C4_SHARED','C4_DIRECTIONAL','INDICATORS_DIRECT','C4_INDICATORS_DIRECT']:
                name=base+'_'+kind;weight=None;direct=None
                if kind=='C4_FIXED':w=np.ones(len(va));actual_delta=delta
                elif kind.startswith('C4_') and kind in ['C4_CONSTANT','C4_SHARED','C4_DIRECTIONAL']:
                    weight=ContinuousWeight(kind.replace('C4_','')).fit(x.iloc[tr],residual,candidate_oof);w=weight.predict_weight(x.iloc[va],delta);actual_delta=w*delta
                else:
                    columns=INDICATORS if kind=='INDICATORS_DIRECT' else PARENTS+INDICATORS;direct=FixedCorrection(columns).fit(x.iloc[tr],residual);actual_delta=direct.predict_delta(x.iloc[va]);w=np.full(len(va),np.nan)
                prediction=bp+actual_delta;assert np.isfinite(prediction).all() and max(abs(actual_delta))<=.25+1e-12
                if weight is not None:assert ((w>=0)&(w<=1)).all() and (actual_delta*delta>=-1e-12).all()
                models[name]=dict(candidate=candidate,weight=weight,direct=direct,base=base,kind=kind)
                for j,i in enumerate(va):
                    rows.append(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(prediction[j])))
                    details.append(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,base_prediction=bp[j],candidate_delta=delta[j],weight=w[j],applied_delta=actual_delta[j],actual_error_before=bp[j]-y[i],prediction=prediction[j]))
        joblib.dump(dict(models=models,train_positions=tr,validation_positions=va),OUT/'models'/f'{fi:02d}.joblib',compress=3)
    joblib.dump(dict(predictions=rows,details=details,ledger=ledger,calibration=calibration,source_ledger_count=len(inner_ck['ledger']),warnings=[dict(category=w.category.__name__,message=str(w.message)) for w in caught],seconds=time.perf_counter()-start),dest,compress=3);print(f'Weights {fi+1}/65 {key["protocol"]} {time.perf_counter()-start:.1f}s',flush=True)


if __name__=='__main__':
    if (OUT/'execution_complete.json').exists():raise FileExistsError('Preserve completed weight run')
    cfg=json.loads((OUT/'frozen_design.json').read_text());assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());start=time.perf_counter();joblib.Parallel(n_jobs=cfg['workers'],backend='loky')(joblib.delayed(work)(i) for i in range(65));packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(65)]
    for field in ['predictions','details']:pd.DataFrame([dict(execution_index=i,**r) for i,p in enumerate(packs) for r in p[field]]).to_parquet(OUT/'tables'/f'{field}.parquet',index=False)
    (OUT/'audit/warnings.json').write_text(json.dumps([dict(execution_index=i,**r) for i,p in enumerate(packs) for r in p['warnings']],indent=2),encoding='utf-8');assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    (OUT/'execution_complete.json').write_text(json.dumps(dict(status='complete',new_recipes=12,folds=65,seconds=time.perf_counter()-start,base_corrections_fixed=True,protected_sources_unchanged=True,no_PRED=True,no_final138_fit=True),indent=2),encoding='utf-8')
