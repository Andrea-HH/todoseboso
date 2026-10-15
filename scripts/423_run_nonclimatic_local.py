"""Fixed nonclimatic local base and both honest correction directions."""
from pathlib import Path
import sys,json,hashlib,warnings,time
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import KFold
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.geoc_bridge import data,OLD,OUT as BRIDGE,local_prediction
from src.geoc_reverse import evaluate,GRID,AMPLITUDES
from src.family_8.research import subcv
from src.ct3_residual_conditional.models import tune_base
from src.compact_geographic import neighborhood
OUT=ROOT/'outputs/modeling/nonclimatic_local/v1'

def work(index):
    destination=OUT/'checkpoints'/f'{index:02d}.joblib'
    if destination.exists():return
    start=time.perf_counter();a=data();scores=joblib.load(OUT/'cache/representations.joblib');assert a['ids197']==scores['ids197'];a['x']=scores['scores']['nonclimatic'];t=a['train'];pos=a['train_global'];y=t.RENDIMIENTO_T_HA.to_numpy();distance=a['distance'];groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO');logs=[];ledger=[]
    def tune(positions,cv):
        key=hashlib.sha256(repr((tuple(positions),tuple((tuple(c),tuple(d)) for c,d in cv))).encode()).hexdigest();previous=ROOT/'outputs/modeling/compact_geography/v1/base_cache'/f'{index:02d}'/(key+'.joblib')
        if previous.exists():return joblib.load(previous)
        path=OUT/'base_cache'/f'{index:02d}'/(key+'.joblib');path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():return joblib.load(path)
        m,record,ww=tune_base(t,y,positions,cv);logs.extend(ww);joblib.dump(m,path,compress=3);return m
    with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always')
        if index<65:
            plan=joblib.load(OLD/'cache/execution_plan.joblib')[index];tr=plan['train_positions'];va=plan['validation_positions'];pro=plan['protocol'];repeat=plan['repeat'];fold=plan['fold'];inner=joblib.load(OLD/'cache/frozen65_splits.joblib')[index][5];ct3=joblib.load(OLD/'base_cache'/f'{plan["outer_base_key"]}.joblib')['model'];contexts=[];lookup={int(v):i for i,v in enumerate(tr)};cf=np.full(len(tr),np.nan)
            for item in plan['inner']:
                aa=item['train_positions'];bb=item['validation_positions'];where=np.array([lookup[int(v)] for v in bb]);bp=joblib.load(OLD/'base_cache'/f'{item["base_key"]}.joblib')['model'].predict(t.iloc[bb]);cf[where]=bp;deep=np.full(len(aa),np.nan);mapping={int(v):i for i,v in enumerate(aa)}
                for ctx in item['residual_contexts']:
                    dd=ctx['held_positions'];pack=joblib.load(OLD/'base_cache'/f'{ctx["base_key"]}.joblib');excluded=set(t.iloc[np.r_[dd,bb,va]].ID_POLIGONO);assert not set(pack['registry']['train_ids'])&excluded;deep[[mapping[int(v)] for v in dd]]=pack['model'].predict(t.iloc[dd]);ledger.append(dict(base_key=ctx['base_key'],excluded_ids=sorted(excluded),verified=True))
                assert np.isfinite(deep).all();contexts.append((aa,bb,where,y[aa]-deep,bp))
        else:
            memberships=pd.read_csv(BRIDGE/'cache/geoc_memberships.csv');split=sorted(memberships.split_id.unique())[index-65];g=memberships[memberships.split_id==split];lookup={v:i for i,v in enumerate(t.ID_POLIGONO)};tr=np.array([lookup[v] for v in g[g.role=='pseudo_train'].ID_POLIGONO]);va=np.array([lookup[v] for v in g[g.role=='pseudo_target'].ID_POLIGONO]);pro='geoc_target_matched';repeat=int(split.rsplit('_',1)[1]);fold=1;inner=list(KFold(4,shuffle=True,random_state=2026).split(tr));ct3=joblib.load(BRIDGE/'models'/f'{split}.joblib')['ct3'];contexts=[];cf=np.full(len(tr),np.nan)
            for c,d in inner:
                aa=tr[c];bb=tr[d];cv=subcv(t,aa,'random',groups);m=tune(aa,cv);bp=m.predict(t.iloc[bb]);cf[d]=bp;deep=np.full(len(aa),np.nan)
                for e,f in cv:
                    fit=aa[e];held=aa[f];assert not set(fit)&(set(held)|set(bb)|set(va));m=tune(fit,subcv(t,fit,'random',groups));deep[f]=m.predict(t.iloc[held]);ledger.append(dict(train_positions=fit.tolist(),excluded_positions=np.r_[held,bb,va].tolist(),verified=True))
                assert np.isfinite(deep).all();contexts.append((aa,bb,d,y[aa]-deep,bp))
        assert np.isfinite(cf).all() and not set(tr)&set(va)
        # CT3 base + local model of honest CT3 residuals.
        delta=np.full(len(tr),np.nan)
        for aa,bb,where,residual,bp in contexts:delta[where]=local_prediction(a['x'],distance,pos[aa],pos[bb],residual)
        scores_forward=[float(np.mean((cf+amp*delta-y[tr])**2)) for amp in AMPLITUDES];ai=min(range(3),key=lambda i:(round(scores_forward[i],12),AMPLITUDES[i]));amp=AMPLITUDES[ai];residual_target=y[tr]-cf
        ct=ct3.predict(t.iloc[va]);forward=ct+amp*local_prediction(a['x'],distance,pos[tr],pos[va],residual_target) if amp else ct.copy()
        # Local nonclimatic base + newly estimated compact4 EN residual model.
        reverse=evaluate(a,tr,va,inner,'random' if pro=='geoc_target_matched' else pro,groups)
        safe=local_prediction(scores['scores']['safe_with_climate'],distance,pos[tr],pos[va],y[tr])
        indices,near,weights=neighborhood(distance,pos[tr],pos[va],24,1.)
        mean=(y[tr][indices]*weights).sum(axis=1)/weights.sum(axis=1)
        predictions=dict(NONCLIM_LOCAL=reverse['baseline'],CT3_PLUS_NONCLIM=forward,NONCLIM_PLUS_COMPACT_EN=reverse['prediction'],SAFE_CLIMATE_LOCAL=safe,GEO_MEAN24=mean)
        rows=[dict(experiment=name,protocol=pro,repeat=repeat,fold=fold,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(v)) for name,values in predictions.items() for i,v in zip(va,values)]
        registry=dict(protocol=pro,repeat=repeat,fold=fold,forward_amplitude=amp,forward_inner_rmse=float(np.sqrt(min(scores_forward))),reverse_amplitude=reverse['selection']['amplitude'],reverse_params=reverse['selection']['params'],reverse_inner_rmse=reverse['selection']['rmse'],seconds=time.perf_counter()-start)
        joblib.dump(dict(ct3=ct3,reverse=reverse,forward_amplitude=amp,forward_residual_target=residual_target,train_positions=tr,validation_positions=va,ledger=ledger),OUT/'models'/f'{index:02d}.joblib',compress=3)
    logs.extend(dict(category=w.category.__name__,message=str(w.message)) for w in captured)
    joblib.dump(dict(predictions=rows,registry=registry,warnings=logs),destination,compress=3);print(f'nonclimatic {index+1}/81 {pro}',flush=True)

if __name__=='__main__':
    if (OUT/'execution_complete.json').exists():raise FileExistsError('Preserve completed phase')
    assert (OUT/'feature_audit_complete.json').exists()
    paths=[Path(__file__),ROOT/'src/nonclimatic_local.py',ROOT/'src/geoc_reverse.py',ROOT/'src/geoc_bridge.py',ROOT/'src/geoc_local04d_snapshot.py',ROOT/'src/ct3_residual_conditional/models.py',ROOT/'src/family_4/conditional_response.py',OUT/'cache/representations.joblib',OUT/'feature_policy_frozen.json',OUT/'feature_audit_complete.json',BRIDGE/'cache/prepared.joblib',BRIDGE/'cache/geoc_memberships.csv',OLD/'cache/execution_plan.joblib',OLD/'cache/frozen65_splits.joblib',OLD/'cache/groups.csv']+list((OLD/'base_cache').glob('*.joblib'))+list((BRIDGE/'models').glob('*.joblib'))+list((ROOT/'outputs/modeling/compact_geography/v1/base_cache').rglob('*.joblib'))
    cfg=dict(variants=['NONCLIM_LOCAL','CT3_PLUS_NONCLIM','NONCLIM_PLUS_COMPACT_EN','SAFE_CLIMATE_LOCAL','GEO_MEAN24'],local_parameters=dict(k=24,alpha=30,power=1,pca20=True),nonclimatic_features=json.loads((OUT/'feature_audit_complete.json').read_text()),forward_amplitudes=AMPLITUDES,reverse_grid=GRID,reverse_amplitudes=AMPLITUDES,selection='complete internal OOF errors, no external selection; forward ties rounded12 smaller amplitude; reverse ties existing frozen reverse rule',representation='X-only PCA20 of all197, same transductive information as Local04D; not independent of climate response nor induction to unknown X',controls='Original Local04D and CT3 archives; SAFE_CLIMATE_LOCAL filters nonclimate exclusions but retains climate; GEO_MEAN24 tests neighborhood without PCA',statistics='Exploratory paired cluster bootstrap/signs, Holm support3 primary models versus CT3/Local04D over5 protocols=30 comparisons; structural controls descriptive, no target screening',no_new_final_fit=True,no_new_PRED=True,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    path=OUT/'frozen_design.json'
    if path.exists():assert json.loads(path.read_text())==cfg
    else:path.write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    joblib.Parallel(n_jobs=4,backend='loky')(joblib.delayed(work)(i) for i in range(81))
    packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(81)];p=pd.DataFrame([r for q in packs for r in q['predictions']]);assert len(p)==12250
    p.to_parquet(OUT/'tables/new_oof_predictions.parquet',index=False);p.to_csv(OUT/'tables/new_oof_predictions.csv',index=False);pd.DataFrame([q['registry'] for q in packs]).to_parquet(OUT/'tables/registry.parquet',index=False)
    (OUT/'audit/warnings.json').write_text(json.dumps([r for q in packs for r in q['warnings']],indent=2),encoding='utf-8')
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in cfg['source_sha256'].items())
    (OUT/'execution_complete.json').write_text(json.dumps(dict(status='complete',new_oof=12250,new_external_predictors=405,warnings=sum(len(q['warnings']) for q in packs),protected_sources_preserved=True),indent=2),encoding='utf-8')
