"""Reconstruct two compact existing configurations with unwanted inputs removed."""
from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.architecture_decomposition import OUT,load_assets,local_sets
from src.pruned_global_architecture import PrunedGlobalFactory
from src.indicator_neighborhoods import OUT as INDICATORS,REDUCTIONS,ReducedCorrection
from src.ct3_residual_conditional.models import CORE
from src.geoc_bridge import OLD

def work(fi):
    a_original=load_assets();t=a_original['a']['train'];y=a_original['y'];x=pd.read_parquet(INDICATORS/'cache/features_train138_target_free.parquet')[['ID_POLIGONO']+REDUCTIONS['R3']];pro,re,fold,tr,va,inner=joblib.load(OLD/'cache/frozen65_splits.joblib')[fi];tr=np.asarray(tr);va=np.asarray(va);groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO');ck=joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib');original=pd.DataFrame(ck['predictions']);checks=[]
    with threadpool_limits(limits=1):
        for variant in ['NO_PLANET','NDWI_SLOPE']:
            a=dict(a_original);a['a']=dict(a_original['a']);a['a']['train']=t[['ID_POLIGONO','RENDIMIENTO_T_HA']+list(CORE)].copy();a['features197']=a_original['features197'][['ID_POLIGONO']+local_sets()[variant]].copy();a.pop('role_frame',None);a.pop('static',None);assert not any('planet' in c.lower() or 'geo250' in c for c in a['features197'])
            if variant=='NDWI_SLOPE':assert not any('sat_basic_hist' in c for c in a['features197'])
            factory=PrunedGlobalFactory(a,variant,pro,groups,OUT/'pruned_cache'/variant/f'{fi:02d}',tr,inner);oof=np.full(len(tr),np.nan);delta=oof.copy()
            for c,d in inner:
                aa=tr[c];bb=tr[d];oof[d]=factory.predict(factory.fit(aa),bb);cv=factory.cv(aa);deep=np.full(len(aa),np.nan)
                for e,f in cv:deep[f]=factory.predict(factory.fit(aa[e]),aa[f])
                m=ReducedCorrection('R3').fit(x.iloc[aa],y[aa]-deep);delta[d]=m.delta(x.iloc[bb])*np.isfinite(x.iloc[bb][REDUCTIONS['R3']].to_numpy(float)).all(axis=1)
            scores=[(float(np.sqrt(np.mean((oof+s*delta-y[tr])**2))),s) for s in [0.,.5,1.]];strength=min(scores,key=lambda v:(round(v[0],12),v[1]))[1];model=factory.fit(tr);base=factory.predict(model,va);r3=ReducedCorrection('R3').fit(x.iloc[tr],y[tr]-oof);correction=strength*np.isfinite(x.iloc[va][REDUCTIONS['R3']].to_numpy(float)).all(axis=1)*r3.delta(x.iloc[va]);name=variant+'_OFF_GLOBAL'
            for suffix,pred in [('_BASE',base),('_MASK',base+correction)]:
                expected=original[original.experiment==name+suffix].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred.to_numpy();difference=float(max(abs(pred-expected)));assert difference<1e-12;checks.append(dict(execution_index=fi,experiment=name+suffix,max_difference=difference,Planet_inputs_removed=True,geology_inputs_removed=True,FULL7_hyperparameter_calibration_removed=True,raw_prediction_fields=14 if variant=='NO_PLANET' else 12))
            assert all(not set(r['train'])&(set(r['held'])|set(va)) for r in factory.ledger)
            path=OUT/'pruned_models'/variant;path.mkdir(parents=True,exist_ok=True);joblib.dump(dict(base=model,corrector=r3,strength=strength,train_positions=tr,validation_positions=va,required_local_columns=local_sets()[variant]),path/f'{fi:02d}.joblib',compress=3)
    return checks

if __name__=='__main__':
    rows=joblib.Parallel(n_jobs=4,backend='loky')(joblib.delayed(work)(fi) for fi in range(65));d=pd.DataFrame([r for group in rows for r in group]);d.to_csv(OUT/'audit/pruned_source_independence.csv',index=False);report=dict(status='complete',configurations_reproduced=2,folds=65,base_and_MASK_replays=len(d),max_difference=float(d.max_difference.max()),Planet_removed=True,geology_removed=True,no_FULL7_calibration=True,no_new_experiment_or_parameter_selection=True,no_PRED=True);(OUT/'pruned_delivery_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
