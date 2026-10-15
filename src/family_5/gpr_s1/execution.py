"""Frozen, bounded S1 sensitivities with full-pipeline inner Ridge selection."""
import json,time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from threadpoolctl import threadpool_limits
from src.family_5.gpr_initial import execution as old
from src.family_5.gpr_initial.model import CompactGPR,OPT
from .models import RbfGPR,LinearMeanGPR,ALPHAS
ROOT=old.ROOT;ID=old.ID;TARGET=old.TARGET;load=old.load
OUT=ROOT/'outputs/modeling/family_5/gpr_s1/v1'
CORE=old.SPECS['F5-01'];RAIN=[f'rain_{m}_2025' for m in ['apr','may','jun','jul','aug','sep','oct']]
SPECS={'F5-S1-A':CORE,'F5-S1-B':RAIN+[old.c.NDVI],'F5-S1-C':CORE}

def freeze():
    if (OUT/'manifest.json').exists():raise FileExistsError('Completed S1 is immutable')
    for name in ['audit','tables','models','checkpoints','figures','report','splits']:(OUT/name).mkdir(parents=True,exist_ok=True)
    m=json.loads((old.OUT/'manifest.json').read_text())
    protected=pd.read_csv(old.OUT/'audit/protected_inputs.csv').to_dict('records')
    protected += [dict(path=p,sha256=h) for p,h in m['artifacts'].items()]
    protected.append(dict(path=(old.OUT/'manifest.json').relative_to(ROOT).as_posix(),sha256=old.design.sha(old.OUT/'manifest.json')))
    for r in protected:assert old.design.sha(ROOT/r['path'])==r['sha256'],r['path']
    pd.DataFrame(protected).drop_duplicates('path').to_csv(OUT/'audit/protected_inputs.csv',index=False)
    frozen=dict(specs=SPECS,optimizer=OPT,linear_alphas=ALPHAS,linear_penalty='n_train*alpha; unpenalized intercept',linear_selection='mean of four frozen inner-fold full-pipeline RMSE; rounded10 ties strongest alpha',linear_mean='deterministic plug-in Ridge; within-training fitted residuals; not DotProduct or Champion residual targets',intervals='90% observation GP+White; C conditional on fitted linear coefficients; no trend-parameter or hyperparameter uncertainty',normalization='original ConditionalFeatures and active block sqrt-dimension weighting; train-only GP target normalization (residual target for C)',outer_folds=65,expected_fits=1755,no_PRED=True,exploratory_outer_comparisons=True,source_sha={p.relative_to(ROOT).as_posix():old.design.sha(p) for p in [Path(__file__),Path(__file__).with_name('models.py'),ROOT/'src/family_5/gpr_initial/model.py',ROOT/'src/family_5/gpr_initial/kernel.py',ROOT/'src/family_4/conditional_response.py']})
    path=OUT/'frozen_execution_design.json'
    if path.exists():assert json.loads(path.read_text())==json.loads(json.dumps(frozen))
    else:path.write_text(json.dumps(frozen,indent=2),encoding='utf8')
    _,t,_=load();_,table,groups=old.c.b.e.f.lm.k.j.load_frozen_splits(t)
    table.to_csv(OUT/'splits/outer_and_inner_splits.csv',index=False);groups.to_csv(OUT/'splits/group_memberships.csv')
    pd.read_parquet(old.OUT/'tables/oof_predictions.parquet').to_parquet(OUT/'tables/reference_oof.parquet',index=False)

def stem(name,p,r,f,context,j,alpha):return f'{name}_{p}_{r}_{f}_{context}_{j}_a{alpha}'

def fit_one(name,p,r,f,context,j,a,v,alpha=0.):
    key=dict(experiment=name,protocol=p,repeat=r,fold=f,context=context,inner_index=j,selection_alpha=alpha)
    s=stem(name,p,r,f,context,j,alpha);path=OUT/'checkpoints'/f'{s}.joblib'
    if path.exists():return joblib.load(path)
    model=RbfGPR(tuple(CORE)) if name=='F5-S1-A' else CompactGPR(tuple(SPECS[name])) if name=='F5-S1-B' else LinearMeanGPR(tuple(CORE),alpha)
    model.fit(a,a[TARGET]);pieces=model.predict_components(v);params=model.parameters()
    z=model.transform(v);distance=cdist(z,model.training_z_).min(axis=1)
    outside=(v[SPECS[name]].lt(a[SPECS[name]].min()-1e-10)|v[SPECS[name]].gt(a[SPECS[name]].max()+1e-10)).any(axis=1).to_numpy()
    rows=[]
    for i,(pid,y) in enumerate(zip(v[ID],v[TARGET])):
        rows.append({**key,ID:pid,'y_true':float(y),'y_pred':float(pieces['prediction'][i]),**{k:float(pieces[k][i]) for k in ['predictive_sd','latent_sd','noise_variance','lower','upper']},'profile_known':bool(v.iloc[i].climate_profile in set(a.climate_profile)),'outside_marginal_support':bool(outside[i]),'nearest_training_distance_z':distance[i],'training_y_mean':float(a[TARGET].mean()),'linear_prediction':float(pieces.get('linear_prediction',np.repeat(a[TARGET].mean(),len(v)))[i]),'gp_correction':float(pieces.get('gp_correction',pieces['prediction']-a[TARGET].mean())[i])})
    reg={**key,**{k:json.dumps(value) if isinstance(value,(list,dict)) else value for k,value in params.items()},'n_train':len(a),'n_validation':len(v),'train_ids':json.dumps(a[ID].tolist()),'validation_ids':json.dumps(v[ID].tolist()),'model_path':(OUT/'models'/f'{s}.joblib').relative_to(ROOT).as_posix()}
    pack=dict(predictions=rows,registry=reg,optimizer=[{**key,'restart':i,**record} for i,record in enumerate(model.optimizer_.records)])
    joblib.dump(model,OUT/'models'/f'{s}.joblib',compress=3);joblib.dump(pack,path,compress=3)
    return pack

def fit_fold(index):
    _,t,splits=load();p,r,f,tr,va,inner=splits[index];a,v=t.iloc[tr],t.iloc[va]
    with threadpool_limits(limits=1):
        for name in SPECS:
            alphas=ALPHAS if name=='F5-S1-C' else (0.,)
            scores=[]
            for alpha in alphas:
                packs=[fit_one(name,p,r,f,'inner',j,a.iloc[it],a.iloc[iv],alpha) for j,(it,iv) in enumerate(inner)]
                score=np.mean([np.sqrt(np.mean([(x['y_pred']-x['y_true'])**2 for x in pack['predictions']])) for pack in packs])
                scores.append(dict(experiment=name,protocol=p,repeat=r,fold=f,alpha=alpha,mean_inner_fold_RMSE=score))
            alpha=min(scores,key=lambda x:(round(x['mean_inner_fold_RMSE'],10),-x['alpha']))['alpha']
            fit_one(name,p,r,f,'outer',-1,a,v,alpha)
            for score in scores:score['selected']=score['alpha']==alpha
            pd.DataFrame(scores).to_csv(OUT/'checkpoints'/f'tuning_{name}_{p}_{r}_{f}.csv',index=False)
    print(f'S1 {index+1}/65 {p} repeat{r} fold{f}',flush=True)

def collect():
    packs=[joblib.load(path) for path in sorted((OUT/'checkpoints').glob('*.joblib'))];assert len(packs)==1755
    reg=pd.DataFrame([p['registry'] for p in packs]);reg.to_csv(OUT/'tables/fit_registry.csv',index=False)
    tuning=pd.concat([pd.read_csv(path) for path in (OUT/'checkpoints').glob('tuning*.csv')]);tuning.to_csv(OUT/'tables/inner_selection.csv',index=False)
    pred=pd.DataFrame([r for p in packs for r in p['predictions']]);outer=pred[pred.context.eq('outer')];assert len(outer)==5382
    inner=pred[pred.context.eq('inner')].merge(tuning[tuning.selected][['experiment','protocol','repeat','fold','alpha']],left_on=['experiment','protocol','repeat','fold','selection_alpha'],right_on=['experiment','protocol','repeat','fold','alpha'])
    inner.to_parquet(OUT/'tables/inner_oof_predictions.parquet',index=False);pred[pred.context.eq('inner')].to_parquet(OUT/'tables/all_inner_candidates.parquet',index=False)
    p=pd.concat([pd.read_parquet(OUT/'tables/reference_oof.parquet'),outer],ignore_index=True);assert len(p)==10764
    p.to_parquet(OUT/'tables/oof_predictions.parquet',index=False)
    pd.DataFrame([r for pack in packs for r in pack['optimizer']]).to_json(OUT/'tables/optimizer_starts.json',orient='records',indent=2)
    return p

def run(workers=3):
    freeze();start=time.perf_counter()
    joblib.Parallel(n_jobs=workers,backend='loky',inner_max_num_threads=1)(joblib.delayed(fit_fold)(i) for i in range(65))
    p=collect();(OUT/'audit/wall_seconds.txt').write_text(str(time.perf_counter()-start))
    from .reporting import build
    build(p)
