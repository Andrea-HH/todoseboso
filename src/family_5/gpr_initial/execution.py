"""Execute only approved F5-00-C/F5-01 and recover the exact archived C-T3."""
from pathlib import Path
import json,time,traceback
import joblib
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from threadpoolctl import threadpool_limits
from src.family_4 import stage_c_models as c
from src.family_5 import gpr_evidence_design as design
from .model import CompactGPR,OPT

ROOT=c.ROOT;ID=c.ID;TARGET=c.TARGET
OUT=ROOT/'outputs/modeling/family_5/gpr_initial/v1'
SPECS={'F5-00-C':c.COMPACT,'F5-01':c.COMPACT+[c.NDVI]}

def load():
    features=pd.read_parquet(c.PROC/'c_features_197_target_free.parquet')
    t=c.b.e.f.lm.k.j.supervised_data(features,pd.read_csv(c.b.e.f.lm.k.j.MASTER))
    assert len(t)==138 and len(features)==197 and TARGET not in features
    return features,t,c.b.e.f.lm.k.j.load_frozen_splits(t)[0]

def freeze():
    if (OUT/'manifest.json').exists():raise FileExistsError('Completed F5 initial run immutable')
    for name in ['audit','tables','models','checkpoints','figures','report','splits']:(OUT/name).mkdir(parents=True,exist_ok=True)
    proposed=json.loads((design.OUT/'proposed_design.json').read_text());p=proposed['optimizer_future']
    for k in ['n_restarts_optimizer','seed','amplitude_bounds','length_bounds','noise_variance_bounds','initial_amplitude','initial_length','initial_noise_variance','jitter']:
        assert json.loads(json.dumps(OPT[k]))==p[k],k
    paths={ROOT/r.path:r.sha256 for r in pd.read_csv(design.OUT/'audit/protected_inputs.csv').itertuples()}
    manifest=json.loads((design.OUT/'manifest.json').read_text())
    paths.update({ROOT/p:h for p,h in manifest['artifacts'].items()});paths[design.OUT/'manifest.json']=design.sha(design.OUT/'manifest.json')
    protected=[]
    for path,digest in paths.items():assert design.sha(path)==digest;protected.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=digest))
    pd.DataFrame(protected).to_csv(OUT/'audit/protected_inputs.csv',index=False)
    fit_sources=[Path(__file__),Path(__file__).with_name('model.py'),Path(__file__).with_name('kernel.py'),ROOT/'src/family_4/conditional_response.py']
    frozen=dict(authorized_experiments=SPECS,control='C-T3 archived/replayed; compact3+MayNDVI identical',n_outer=65,n_inner_per_outer=4,n_labels=138,n_unlabelled=59,optimizer=OPT,kernel='Constant*GroupedMatern32+WhiteKernel; nu1.5fixed; no other kernel',normalization='existing ConditionalFeatures train medians/scales with NDVI floor.05; active block axes divided sqrt(active dimensioncount); GPR.normalize_y trainonly',inner_role='four frozen diagnostic fits per outer/spec; no discrete hyperparameter/spec selection authorized; LML optimization only within each fit training',intervals='90% observational Gaussian plug-in, WhiteKernel variance included; latent SD separately; no hyperparameter/domain uncertainty',aggregation='complete138 OOF per repeat; then mean repeats; no meanfold substitution',selection_guard=dict(municipal_RMSE_gain=.01,max_other_RMSE_MAE_harm=.01,municipal_improving_folds_min=3,note='approved exploratory proposal; not economic margin or statistical significance'),no_final_training=True,no_PRED_predictions=True,no_F5_02_06=True,source_sha={p.relative_to(ROOT).as_posix():design.sha(p) for p in fit_sources},exploratory=True)
    config=OUT/'frozen_execution_design.json'
    if config.exists():assert json.loads(config.read_text())==json.loads(json.dumps(frozen))
    else:config.write_text(json.dumps(frozen,indent=2),encoding='utf8')
    _,t,splits=load();_,table,groups=c.b.e.f.lm.k.j.load_frozen_splits(t);table.to_csv(OUT/'splits/outer_and_inner_splits.csv',index=False);groups.to_csv(OUT/'splits/group_memberships.csv')
    controls=pd.read_parquet(c.OUT/'tables/oof_predictions.parquet');controls=controls[controls.experiment.eq('C-T3')].copy();assert len(controls)==1794
    controls.to_parquet(OUT/'tables/control_oof.parquet',index=False)
    gate=[]
    for protocol,repeat,fold,tr,va,inner in splits:
        model=joblib.load(c.OUT/'models'/f'C-T3_{protocol}_{repeat}_{fold}.joblib');v=t.iloc[va]
        q=controls[(controls.protocol==protocol)&(controls['repeat']==repeat)&(controls.fold==fold)].set_index(ID).loc[v[ID]]
        diff=float(abs(model.predict(v)-q.y_pred).max());assert diff<=1e-12
        gate.append(dict(protocol=protocol,repeat=repeat,fold=fold,n=len(v),max_prediction_difference=diff,source=(c.OUT/'models'/f'C-T3_{protocol}_{repeat}_{fold}.joblib').relative_to(ROOT).as_posix()))
    pd.DataFrame(gate).to_csv(OUT/'audit/control_replay.csv',index=False)
    print('Frozen F5 scope;65 C-T3 controls exactly replayed; no additional experiments',flush=True)

def fit_one(name,protocol,repeat,fold,context,inner_index,a,v):
    key=dict(experiment=name,protocol=protocol,repeat=repeat,fold=fold,context=context,inner_index=inner_index)
    stem=f'{name}_{protocol}_{repeat}_{fold}_{context}_{inner_index}';checkpoint=OUT/'checkpoints'/(stem+'.joblib')
    if checkpoint.exists():return joblib.load(checkpoint)
    model=CompactGPR(tuple(SPECS[name])).fit(a,a[TARGET]);pieces=model.predict_components(v);params=model.parameters()
    z=model.transform(v);nearest=cdist(z,model.training_z_).min(axis=1);raw=a[SPECS[name]]
    outside=(v[SPECS[name]].lt(raw.min()-1e-10)|v[SPECS[name]].gt(raw.max()+1e-10)).any(axis=1).to_numpy()
    known=v.climate_profile.isin(a.climate_profile).to_numpy()
    rows=[]
    for i,(pid,y) in enumerate(zip(v[ID],v[TARGET])):
        rows.append({**key,ID:pid,'y_true':float(y),'y_pred':float(pieces['prediction'][i]),**{x:float(pieces[x][i]) for x in ['predictive_sd','latent_sd','noise_variance','lower','upper']},'profile_known':bool(known[i]),'outside_marginal_support':bool(outside[i]),'nearest_training_distance_z':float(nearest[i])})
    registry={**key,**{k:value if not isinstance(value,(list,dict)) else json.dumps(value) for k,value in params.items()},'n_train':len(a),'n_validation':len(v),'n_train_profiles':a.climate_profile.nunique(),'n_unique_training_predictors':len(np.unique(model.training_z_,axis=0)),'train_ids':json.dumps(a[ID].tolist()),'validation_ids':json.dumps(v[ID].tolist()),'preprocess_medians':json.dumps(model.preprocess_.median_.tolist()),'preprocess_means':json.dumps(model.preprocess_.mean_.tolist()),'preprocess_scales':json.dumps(model.preprocess_.scale_.tolist())}
    pack=dict(predictions=rows,registry=registry,optimizer=[{**key,'restart':j,**r} for j,r in enumerate(model.optimizer_.records)])
    joblib.dump(model,OUT/'models'/(stem+'.joblib'),compress=3);joblib.dump(pack,checkpoint,compress=3)
    return pack

def fit_fold(index):
    _,t,splits=load();protocol,repeat,fold,tr,va,inner=splits[index];a,v=t.iloc[tr],t.iloc[va]
    with threadpool_limits(limits=1):
        try:
            for name in SPECS:
                for j,(itr,iva) in enumerate(inner):fit_one(name,protocol,repeat,fold,'inner',j,a.iloc[itr],a.iloc[iva])
                fit_one(name,protocol,repeat,fold,'outer',-1,a,v)
        except Exception:
            (OUT/'audit'/f'failure_fold_{index}.txt').write_text(traceback.format_exc(),encoding='utf8');raise
    print(f'F5 FOLD {index+1}/65 {protocol} repeat{repeat} fold{fold}',flush=True)

def collect():
    _,t,splits=load();packs=[]
    for protocol,repeat,fold,*_ in splits:
        for name in SPECS:
            for context,j in [('outer',-1)]+[('inner',j) for j in range(4)]:packs.append(joblib.load(OUT/'checkpoints'/f'{name}_{protocol}_{repeat}_{fold}_{context}_{j}.joblib'))
    predictions=pd.DataFrame([r for pack in packs for r in pack['predictions']]);outer=predictions[predictions.context.eq('outer')];assert len(outer)==3588
    controls=pd.read_parquet(OUT/'tables/control_oof.parquet');allp=pd.concat([controls,outer],ignore_index=True);assert len(allp)==5382
    allp.to_parquet(OUT/'tables/oof_predictions.parquet',index=False);predictions[predictions.context.eq('inner')].to_parquet(OUT/'tables/inner_oof_predictions.parquet',index=False)
    pd.DataFrame([pack['registry'] for pack in packs]).to_csv(OUT/'tables/fit_registry.csv',index=False)
    pd.DataFrame([r for pack in packs for r in pack['optimizer']]).to_json(OUT/'tables/optimizer_starts.json',orient='records',indent=2)
    return allp

def run(workers=3):
    freeze();start=time.perf_counter()
    joblib.Parallel(n_jobs=workers,backend='loky',inner_max_num_threads=1)(joblib.delayed(fit_fold)(i) for i in range(65))
    p=collect();(OUT/'audit/total_fit_wall_seconds.txt').write_text(str(time.perf_counter()-start),encoding='utf8')
    from .reporting import build
    build(p)
