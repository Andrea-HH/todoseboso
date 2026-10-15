"""Seven bounded geography variants on the original65 and GeoC16 banks."""
from pathlib import Path
import sys,json,hashlib,time,warnings
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import KFold
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.compact_geographic import CompactRidge,NeighborResidual,support_factor,GRID,KS,POWERS,WEIGHTS,ALPHAS,predict_bundle
from src.geoc_bridge import data,OLD,OUT as BRIDGE
from src.family_8.research import subcv
from src.ct3_residual_conditional.models import tune_base
OUT=ROOT/'outputs/modeling/compact_geography/v1'

def mse(y,p):return float(np.mean((y-p)**2))
def pick(candidates):return min(enumerate(candidates),key=lambda v:(round(v[1]['mse'],12),v[1].get('weight',1.),v[0]))[1]

def run(index):
    destination=OUT/'checkpoints'/f'{index:02d}.joblib'
    if destination.exists():return
    start=time.perf_counter();a=data();t=a['train'];y=t.RENDIMIENTO_T_HA.to_numpy();pos=a['train_global'];distance=a['distance'];groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO');logs=[];ledger=[]
    cache=OUT/'base_cache'/f'{index:02d}';cache.mkdir(parents=True,exist_ok=True)
    def tune(positions,cv):
        key=hashlib.sha256(repr((tuple(positions),tuple((tuple(c),tuple(d)) for c,d in cv))).encode()).hexdigest();file=cache/(key+'.joblib')
        if file.exists():return joblib.load(file)
        m,record,ww=tune_base(t,y,positions,cv);logs.extend(ww);joblib.dump(m,file,compress=3);return m
    with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always')
        if index<65:
            p=joblib.load(OLD/'cache/execution_plan.joblib')[index];pro=p['protocol'];repeat=p['repeat'];fold=p['fold'];tr=p['train_positions'];va=p['validation_positions'];local_index={int(v):i for i,v in enumerate(tr)}
            ct3=joblib.load(OLD/'base_cache'/f'{p["outer_base_key"]}.joblib')['model'];contexts=[];baseline=np.full(len(tr),np.nan)
            for item in p['inner']:
                aa=item['train_positions'];bb=item['validation_positions'];dest=np.array([local_index[int(v)] for v in bb]);bp=joblib.load(OLD/'base_cache'/f'{item["base_key"]}.joblib')['model'].predict(t.iloc[bb]);baseline[dest]=bp
                deep=np.full(len(aa),np.nan);mapping={int(v):i for i,v in enumerate(aa)}
                for ctx in item['residual_contexts']:
                    dd=ctx['held_positions'];b=joblib.load(OLD/'base_cache'/f'{ctx["base_key"]}.joblib');excluded=set(t.iloc[np.r_[dd,bb,va]].ID_POLIGONO)
                    assert not set(b['registry']['train_ids'])&excluded
                    deep[[mapping[int(v)] for v in dd]]=b['model'].predict(t.iloc[dd]);ledger.append(dict(n_train=len(b['registry']['train_ids']),n_excluded=len(excluded),exclusion_verified=True))
                assert np.isfinite(deep).all();contexts.append((aa,bb,dest,y[aa]-deep,bp))
        else:
            membership=pd.read_csv(BRIDGE/'cache/geoc_memberships.csv');split=sorted(membership.split_id.unique())[index-65];g=membership[membership.split_id==split];lookup={v:i for i,v in enumerate(t.ID_POLIGONO)}
            tr=np.array([lookup[v] for v in g[g.role=='pseudo_train'].ID_POLIGONO]);va=np.array([lookup[v] for v in g[g.role=='pseudo_target'].ID_POLIGONO]);pro='geoc_target_matched';repeat=int(split.rsplit('_',1)[1]);fold=1
            inner=list(KFold(4,shuffle=True,random_state=2026).split(tr));ct3=joblib.load(BRIDGE/'models'/f'{split}.joblib')['ct3'];contexts=[];baseline=np.full(len(tr),np.nan)
            for c,d in inner:
                aa=tr[c];bb=tr[d];cv=subcv(t,aa,'random',groups);mb=tune(aa,cv);bp=mb.predict(t.iloc[bb]);baseline[d]=bp;deep=np.full(len(aa),np.nan)
                for e,f in cv:
                    fit=aa[e];held=aa[f];assert not set(fit)&(set(held)|set(bb)|set(va));m=tune(fit,subcv(t,fit,'random',groups));deep[f]=m.predict(t.iloc[held]);ledger.append(dict(n_train=len(fit),n_excluded=len(set(held)|set(bb)|set(va)),exclusion_verified=True))
                assert np.isfinite(deep).all();contexts.append((aa,bb,d,y[aa]-deep,bp))
        assert not set(tr)&set(va) and np.isfinite(baseline).all()
        # Each representation and hyperparameter is evaluated on identical inner rows.
        local_candidates=[];blend_candidates=[dict(params=None,weight=0.,mse=mse(y[tr],baseline))];support_candidates=blend_candidates.copy();fixed=None
        for params in GRID:
            predictions=np.full(len(tr),np.nan);shrink=np.full(len(tr),np.nan)
            for aa,bb,dest,residual,bp in contexts:
                m=CompactRidge(params).fit(t.iloc[aa],y[aa],pos[aa]);predictions[dest]=m.predict(t.iloc[bb],pos[bb],distance);shrink[dest]=support_factor(distance,pos[aa],pos[bb],params['k'])
            local_candidates.append(dict(params=params,mse=mse(y[tr],predictions)))
            if params==dict(k=24,alpha=30.,power=1.):fixed=params
            for weight in WEIGHTS[1:]:
                blend_candidates.append(dict(params=params,weight=weight,mse=mse(y[tr],baseline+weight*(predictions-baseline))))
                support_candidates.append(dict(params=params,weight=weight,mse=mse(y[tr],baseline+weight*shrink*(predictions-baseline))))
        global_candidates=[]
        for alpha in ALPHAS:
            predictions=np.full(len(tr),np.nan)
            for aa,bb,dest,residual,bp in contexts:
                m=CompactRidge(dict(alpha=alpha),local=False).fit(t.iloc[aa],y[aa],pos[aa]);predictions[dest]=m.predict(t.iloc[bb],pos[bb],distance)
            global_candidates.append(dict(params=dict(alpha=alpha),mse=mse(y[tr],predictions)))
        residual_candidates=[dict(params=None,weight=0.,mse=mse(y[tr],baseline))];residual_support=residual_candidates.copy()
        for k in KS:
            for power in POWERS:
                params=dict(k=k,power=power);delta=np.full(len(tr),np.nan);shrink=np.full(len(tr),np.nan)
                for aa,bb,dest,residual,bp in contexts:
                    m=NeighborResidual(params).fit(pos[aa],residual);delta[dest]=m.predict(pos[bb],distance);shrink[dest]=support_factor(distance,pos[aa],pos[bb],k)
                for weight in WEIGHTS[1:]:
                    residual_candidates.append(dict(params=params,weight=weight,mse=mse(y[tr],baseline+weight*delta)))
                    residual_support.append(dict(params=params,weight=weight,mse=mse(y[tr],baseline+weight*shrink*delta)))
        choices=dict(GLOBAL_RIDGE4=pick(global_candidates),LOCAL_FIXED4=dict(params=fixed,mse=np.nan),LOCAL_TUNED4=pick(local_candidates),BLEND_LOCAL4=pick(blend_candidates),SUPPORT_BLEND4=pick(support_candidates),NN_RESIDUAL=pick(residual_candidates),NN_SUPPORT=pick(residual_support))
        variants={};targets=y[tr]-baseline;registry=[]
        for name,choice in choices.items():
            params=choice['params'];weight=choice.get('weight',1.);kind='direct' if name.startswith(('LOCAL','GLOBAL')) else ('blend' if 'BLEND' in name else 'residual');model=None
            if weight:
                model=NeighborResidual(params).fit(pos[tr],targets) if kind=='residual' else CompactRidge(params,local=name!='GLOBAL_RIDGE4').fit(t.iloc[tr],y[tr],pos[tr])
            variants[name]=dict(kind=kind,params=params,weight=weight,support='SUPPORT' in name,model=model)
            registry.append(dict(experiment=name,protocol=pro,repeat=repeat,fold=fold,params=params,weight=weight,inner_rmse=float(np.sqrt(choice['mse'])) if np.isfinite(choice['mse']) else None))
        pack=dict(ct3=ct3,variants=variants,train_positions=tr,validation_positions=va,targets=targets,ledger=ledger)
        predictions=predict_bundle(pack,t.iloc[va],pos[va],distance)
        rows=[dict(experiment=name,protocol=pro,repeat=repeat,fold=fold,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(v)) for name,values in predictions.items() for i,v in zip(va,values)]
        joblib.dump(pack,OUT/'models'/f'{index:02d}.joblib',compress=3)
    logs.extend(dict(category=w.category.__name__,message=str(w.message)) for w in captured)
    joblib.dump(dict(predictions=rows,registry=registry,warnings=logs,seconds=time.perf_counter()-start),destination,compress=3);print(f'compact geo {index+1}/81 {pro}',flush=True)

if __name__=='__main__':
    if (OUT/'execution_complete.json').exists():raise FileExistsError('Preserve complete version')
    for s in ['models','checkpoints','base_cache','tables','audit']:(OUT/s).mkdir(parents=True,exist_ok=True)
    sources=[Path(__file__),ROOT/'src/compact_geographic.py',BRIDGE/'cache/prepared.joblib',BRIDGE/'cache/geoc_memberships.csv',BRIDGE/'tables/oof_predictions.parquet',OLD/'cache/execution_plan.joblib',OLD/'cache/frozen65_splits.joblib',OLD/'cache/groups.csv',ROOT/'src/ct3_residual_conditional/models.py',ROOT/'src/family_4/conditional_response.py']
    sources+=list((OLD/'base_cache').glob('*.joblib'))+list((BRIDGE/'models').glob('*.joblib'))
    config=dict(scope='7 compact geographic variants, no PCA features, no new sources, no final138 fit or59 PRED',local_grid=GRID,global_alphas=ALPHAS,weights=WEIGHTS,residual_grid=[dict(k=k,power=p) for k in KS for p in POWERS],fixed_local=dict(k=24,alpha=30.,power=1.),preprocessing='Original ConditionalFeatures, train-only median/scale and NDVI floor; shared outer-training scaling for neighbors; Ridge intercept, alpha unnormalized sklearn. Original GeoC distance normalization retained, no mean-normalization of inverse-distance weights.',support='min(1, median TRAIN leave-one-out kth-neighbor distance / query kth-neighbor distance), clipped denominators1e-6; no labels, all support estimated in corresponding training; towardCT3 when low support',selection='joint local params and mixture/residual weight by complete inner OOF MSE, rounded12 tie smaller weight then predefined grid; no choice based on outer territorial metrics',validation='65 original outer/inner splits +16 original GeoC97/41; residual targets fully nested C-T3 tuning excludes held labels; new97/41 deep contexts reuse local deterministic4-fold random partitions',statistics='Exploratory fixed-OOF cluster bootstrap/signs, Holm against CT3 across7 variants x5 protocols; not independent confirmation',source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})
    f=OUT/'frozen_design.json'
    if f.exists():assert json.loads(f.read_text())==config
    else:f.write_text(json.dumps(config,indent=2),encoding='utf-8')
    joblib.Parallel(n_jobs=4,backend='loky')(joblib.delayed(run)(i) for i in range(81))
    packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(81)];pred=pd.DataFrame([r for p in packs for r in p['predictions']]);assert len(pred)==17150
    pred.to_parquet(OUT/'tables/new_oof_predictions.parquet',index=False);pred.to_csv(OUT/'tables/new_oof_predictions.csv',index=False)
    pd.DataFrame([r for p in packs for r in p['registry']]).to_parquet(OUT/'tables/registry.parquet',index=False)
    (OUT/'audit/warnings.json').write_text(json.dumps([r for p in packs for r in p['warnings']],indent=2),encoding='utf-8')
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in config['source_sha256'].items())
    (OUT/'execution_complete.json').write_text(json.dumps(dict(status='complete',new_oof=17150,new_predictors=567,warnings=sum(len(p['warnings']) for p in packs),protected_sources_unchanged=True),indent=2),encoding='utf-8')
