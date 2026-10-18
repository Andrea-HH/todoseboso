"""Execute bounded mixtures using honest internal predictions of all experts."""
from pathlib import Path
import sys,json,time,warnings,hashlib,os
os.environ.setdefault('OMP_NUM_THREADS','1');os.environ.setdefault('MKL_NUM_THREADS','1');os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.four_expert_combinations import OUT,ARCH,NAMES,ExpertFactory,SupportFeatures,fit_combinations,predict_combinations

def work(fi):
    path=OUT/'checkpoints'/f'{fi:02d}.joblib'
    if path.exists():return
    started=time.perf_counter();pro,re,fold,tr,va,inner=joblib.load(OUT/'frozen81_splits.joblib')[fi];tr=np.asarray(tr);va=np.asarray(va);key=dict(protocol=pro,repeat=re,fold=fold)
    with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always');factory=ExpertFactory(fi,'random' if pro=='fresh_97_41' else pro,tr,inner);y=factory.y;t=factory.t;oof=np.full((len(tr),4),np.nan);z={n:np.full((len(tr),4),np.nan) for n in ['B5','B6']};inner_models=[]
        for j,(c,d) in enumerate(inner):
            aa=tr[c];bb=tr[d];p=factory.full_fit(aa);oof[d]=factory.predict(p,bb);support=SupportFeatures(factory.a).fit(aa);features=support.transform(bb,oof[d])
            for n in z:z[n][d]=features[n]
            inner_models.append(dict(train_positions=aa,held_positions=bb,strengths=p['strengths'],candidates=p['candidates'],fallback=p['fallback']));print(f'Mix {fi+1}/81 inner{j+1}/{len(inner)} {time.perf_counter()-started:.1f}s',flush=True)
        assert np.isfinite(oof).all() and all(np.isfinite(v).all() for v in z.values());models=fit_combinations(oof,z,y[tr]);outer=factory.full_fit(tr);external=factory.predict(outer,va);support=SupportFeatures(factory.a).fit(tr);features=support.transform(va,external);predictions,weights=predict_combinations(models,external,features)
        parity=[]
        if fi<65:
            old=pd.read_parquet(ROOT/'outputs/research/four_leaders/v1/matched_oof.parquet');old=old[(old.protocol==pro)&(old['repeat']==re)&(old.fold==fold)]
            for j,n in enumerate(NAMES):
                expected=old[old.experiment==n].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy();diff=float(max(abs(expected-external[:,j])));assert diff<1e-12,(fi,n,diff);parity.append(dict(execution_index=fi,experiment=n,max_difference=diff))
        allpred={**dict(zip(NAMES,external.T)),**predictions};rows=[dict(**key,experiment=n,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(p)) for n,pp in allpred.items() for i,p in zip(va,pp)];details=[dict(**key,experiment=n,ID_POLIGONO=t.iloc[i].ID_POLIGONO,right_expert_weight=float(w)) for n,ww in weights.items() for i,w in zip(va,ww)]
        for j,n in enumerate(['CT3','Reference26','L40']):details.extend(dict(**key,experiment='B4',ID_POLIGONO=t.iloc[i].ID_POLIGONO,component=n,component_weight=float(models['B4'].weights[j])) for i in va)
        ledger=factory.ledger+factory.helper.ledger+factory.helper.role.ledger
        assert all(not set(r['train'])&(set(r['held'])|set(va)) for r in ledger)
        joblib.dump(dict(models=models,outer_experts=outer,support=support,train_positions=tr,validation_positions=va,features=features,external_expert_predictions=external,inner_expert_predictions=oof,inner_features=z,inner_models=inner_models),OUT/'models'/f'{fi:02d}.joblib',compress=3)
        joblib.dump(dict(predictions=rows,details=details,parity=parity,ledger=ledger,fallbacks=factory.fallbacks+factory.helper.logs,seconds=time.perf_counter()-started,warnings=[dict(category=w.category.__name__,message=str(w.message)) for w in caught]),path,compress=3)
    print(f'Mix completed {fi+1}/81 {pro} {time.perf_counter()-started:.1f}s',flush=True)

def main():
    cfg=json.loads((OUT/'frozen_design.json').read_text());assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());started=time.perf_counter();jobs=[int(sys.argv[1])] if len(sys.argv)>1 else list(range(81));joblib.Parallel(n_jobs=1 if len(jobs)==1 else cfg['workers'],backend='loky')(joblib.delayed(work)(fi) for fi in jobs)
    if len(jobs)==1:return
    packs=[joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib') for fi in range(81)]
    for field in ['predictions','details','parity']:pd.DataFrame([dict(execution_index=fi,**r) if 'execution_index' not in r else r for fi,p in enumerate(packs) for r in p[field]]).to_parquet(OUT/'tables'/f'{field}.parquet',index=False)
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items());(OUT/'execution_complete.json').write_text(json.dumps(dict(status='complete',folds=81,original_folds=65,fresh_splits=16,experiments=6,controls=4,seconds=time.perf_counter()-started,no_PRED=True,no_champion_change=True),indent=2));print('All81 folds complete',flush=True)
if __name__=='__main__':main()
