"""Stage B only: frozen objective contrasts plus separate archived fixed ensemble."""
from pathlib import Path
import json,itertools
import joblib
import numpy as np
import pandas as pd
from . import within_profile_complementarity as e
from . import territorial_stage_a as a
from .stage_b_objective import GroupObjectiveRegressor,local_metrics,select_candidate

ROOT,ID,TARGET,RAIN=e.ROOT,e.ID,e.TARGET,e.RAIN
OUT=a.OUT.parent/'stage_b';PROC=a.PROC.parent/'stage_b'
LAM=[0.,.1,.3,1.]
MODELS={'B0':RAIN+[e.f.NDVI],'B1':RAIN+[e.f.NDVI],'B2':RAIN+[e.f.NDVI,e.RISE],'B3':RAIN+[e.f.NDVI,e.RISE]}

def load():
    d,t=e.load();columns=list(dict.fromkeys(RAIN+[e.f.NDVI,e.RISE]))
    return d[[ID,'CONJUNTO','climate_profile','Municipio','Estado']+columns],t[[ID,TARGET,'climate_profile','Municipio','Estado']+columns]

def freeze():
    if (OUT/'manifest.json').exists():raise FileExistsError('Completed Stage B immutable')
    assert json.loads((a.OUT/'manifest.json').read_text())['status']=='complete'
    for p in [OUT,PROC]+[OUT/x for x in ['audit','tables','models','checkpoints','figures','report','splits']]:p.mkdir(parents=True,exist_ok=True)
    d,t=load();splits,table,groups=e.f.lm.k.j.load_frozen_splits(t)
    assert len(t)==138 and len(d)==197 and TARGET not in d
    config=dict(models=MODELS,lambda_grid=LAM,alpha_archive=e.f.lm.k.ALPHA,l1_ratio=e.f.lm.k.L1,alpha_joint_mapping='alpha_joint=2*alpha_archive; alpha_solver=alpha_archive*n/n_augmented',global_loss='SSE/n',intra_loss='mean eligible profiles of2/(n_g-1)*centered_error_SSE',intercept_penalized=False,solver='sklearn ElasticNet exact augmented least squares, no pair expansion',solver_tol=1e-4,max_iter=200000,control_prediction_tolerance=1e-8,delta_rmse=.01,delta_mae=.01,selection='min profile-balanced same-inner-model pairRMSE subject to global complete-innerOOF RMSE and MAE <= conventional baseline+.01',anchor='lambda0 original hyperparameters selected by mean inner-foldRMSE; historical configuration reproduced',fallback='lambda0 historical anchor if fewer than2 evaluable profiles, fewer than2 informative innerfolds or <10% eligible validation parcels, or no positive lambda feasible',tie='localRMSE rounded1e-10; smallerlambda, largeralpha, smallerrho',singleton='global loss only; no eligible trainingprofiles => effective lambda0',fixed_blend_weights=[.5,.5],no_new_features=True,no_stage_c=True,exploratory=True,source_sha={str(p.relative_to(ROOT)):a.sha(p) for p in [Path(__file__),ROOT/'src/family_4/stage_b_objective.py',ROOT/'src/family_4/conditional_response.py']})
    path=OUT/'frozen_design.json'
    if path.exists():assert json.loads(path.read_text())==json.loads(json.dumps(config))
    else:path.write_text(json.dumps(config,indent=2),encoding='utf8')
    table.to_csv(OUT/'splits/outer_and_inner_splits.csv',index=False);groups.to_csv(OUT/'splits/group_memberships.csv')
    d.to_parquet(PROC/'b_features_197_target_free.parquet',index=False)
    p=pd.read_parquet(e.OUT/'tables/oof_predictions.parquet');p=p[p.experiment.isin(['F4-E1','F4-E2'])].copy();p['source_experiment']=p.experiment;p['experiment']=p.experiment.map({'F4-E1':'B0','F4-E2':'B2'})
    assert len(p)==3588
    p.to_parquet(OUT/'tables/control_oof.parquet',index=False)
    return splits

def archived(name,protocol,repeat,fold):
    path=e.f.OUT/'models'/f'F4-S1_{protocol}_{repeat}_{fold}.joblib' if name=='B0' else e.OUT/'models'/f'F4-E2_{protocol}_{repeat}_{fold}.joblib'
    pack=joblib.load(path)
    return pack['model'] if name=='B0' else pack,path

def implementation_gate():
    """All 130 lambda0 controls replay before new external candidate metrics exist."""
    _,t=load();splits,_,_=e.f.lm.k.j.load_frozen_splits(t);rows=[]
    for protocol,repeat,fold,tr,va,inner in splits:
        for name in ['B0','B2']:
            old,path=archived(name,protocol,repeat,fold);alpha=old['model'].alpha;rho=old['model'].l1_ratio
            model=e.f.lm.k.strict_fit(GroupObjectiveRegressor(tuple(MODELS[name]),alpha,rho,0),t.iloc[tr],t.iloc[tr][TARGET])
            diff=float(abs(model.predict(t.iloc[va])-old.predict(t.iloc[va])).max())
            if diff>1e-8:raise ValueError(f'lambda0 control failure {name}/{protocol}/{fold}: {diff}')
            rows.append(dict(experiment=name,protocol=protocol,repeat=repeat,fold=fold,max_abs_prediction_difference=diff,source_model=str(path.relative_to(ROOT)),**model.diagnostics_))
            joblib.dump(model,OUT/'models'/f'implementation_{name}_{protocol}_{repeat}_{fold}.joblib',compress=3)
    pd.DataFrame(rows).to_csv(OUT/'audit/lambda0_implementation_replay.csv',index=False)
    (OUT/'audit/solver_gate.json').write_text(json.dumps(dict(passed=True,n_controls=len(rows),max_abs_difference=max(x['max_abs_prediction_difference'] for x in rows),tolerance=1e-8),indent=2),encoding='utf8')
    print('lambda0 gate passed:',len(rows),'controls',flush=True)

def fit_fold(index):
    _,t=load();splits,_,_=e.f.lm.k.j.load_frozen_splits(t);protocol,repeat,fold,tr,va,inner=splits[index]
    train,valid=t.iloc[tr],t.iloc[va]
    for name,control in [('B1','B0'),('B3','B2')]:
        dest=OUT/'checkpoints'/f'{name}_{protocol}_{repeat}_{fold}.joblib'
        if dest.exists():continue
        old,_=archived(control,protocol,repeat,fold);anchorparams=(old['model'].alpha,old['model'].l1_ratio)
        records=[];train_fit_logs=[]
        for alpha,rho,lam in itertools.product(e.f.lm.k.ALPHA,e.f.lm.k.L1,LAM):
            pred=np.full(len(train),np.nan);folds=np.full(len(train),-1);foldrmse=[]
            for j,(itr,iva) in enumerate(inner):
                aa,bb=train.iloc[itr],train.iloc[iva]
                fit=e.f.lm.k.strict_fit(GroupObjectiveRegressor(tuple(MODELS[name]),alpha,rho,lam),aa,aa[TARGET])
                pred[iva]=fit.predict(bb);folds[iva]=j
                foldrmse.append(float(np.sqrt(np.mean((pred[iva]-bb[TARGET])**2))))
                train_fit_logs.append(dict(alpha=alpha,rho=rho,lam=lam,inner_fold=j,**fit.diagnostics_))
            assert np.isfinite(pred).all() and (folds>=0).all()
            error=train[TARGET].to_numpy()-pred
            records.append(dict(alpha=alpha,rho=rho,lam=lam,rmse=float(np.sqrt(np.mean(error**2))),mae=float(abs(error).mean()),mean_fold_rmse=float(np.mean(foldrmse)),**local_metrics(train[TARGET],pred,train.climate_profile,folds)))
        anchor=next(r for r in records if r['lam']==0 and (r['alpha'],r['rho'])==anchorparams)
        # Verify original global selection is reproducible, without outer-label access.
        zero=[r for r in records if r['lam']==0];minimum=min(r['mean_fold_rmse'] for r in zero)
        assert anchor['mean_fold_rmse']<=minimum+1e-8
        chosen,reason=select_candidate(records,anchor)
        fitted=e.f.lm.k.strict_fit(GroupObjectiveRegressor(tuple(MODELS[name]),chosen['alpha'],chosen['rho'],chosen['lam']),train,train[TARGET])
        pred=fitted.predict(valid);key=dict(experiment=name,protocol=protocol,repeat=repeat,fold=fold)
        rows=[{**key,ID:pid,'y_true':float(y),'y_pred':float(yp),'outer_model_id':f'{name}_{protocol}_{repeat}_{fold}'} for pid,y,yp in zip(valid[ID],valid[TARGET],pred)]
        params={**key,**chosen,'selection_reason':reason,'anchor_rmse':anchor['rmse'],'anchor_mae':anchor['mae'],'train_ids':json.dumps(train[ID].tolist()),'validation_ids':json.dumps(valid[ID].tolist()),**fitted.diagnostics_}
        co=[{**key,'feature':c,'coefficient':float(b)} for c,b in zip(fitted.preprocess_.get_feature_names_out(),fitted.coef_)]
        joblib.dump(fitted,OUT/'models'/dest.name,compress=3)
        joblib.dump(dict(predictions=rows,registry=params,inner=[{**key,**r,'feasible':r['rmse']<=anchor['rmse']+.01+1e-12 and r['mae']<=anchor['mae']+.01+1e-12} for r in records],coefficients=co,convergence=[{**key,**r} for r in train_fit_logs]),dest,compress=3)
    print('STAGE B FOLD',index+1,protocol,repeat,fold,flush=True)

def run(workers=3):
    splits=freeze()
    if not (OUT/'audit/solver_gate.json').exists():implementation_gate()
    assert json.loads((OUT/'audit/solver_gate.json').read_text())['passed']
    joblib.Parallel(n_jobs=workers,backend='loky',inner_max_num_threads=1)(joblib.delayed(fit_fold)(i) for i in range(65))
    packs=[joblib.load(OUT/'checkpoints'/f'{name}_{protocol}_{repeat}_{fold}.joblib') for protocol,repeat,fold,*_ in splits for name in ['B1','B3']]
    for field in ['registry','inner','coefficients','convergence']:
        rows=[row for pack in packs for row in (pack[field] if isinstance(pack[field],list) else [pack[field]])]
        pd.DataFrame(rows).to_csv(OUT/'tables'/f'{field}.csv',index=False)
    p=pd.DataFrame([row for pack in packs for row in pack['predictions']]);p=pd.concat([pd.read_parquet(OUT/'tables/control_oof.parquet'),p],ignore_index=True)
    assert len(p)==7176;p.to_parquet(OUT/'tables/oof_predictions.parquet',index=False)
    from . import stage_b_reporting
    stage_b_reporting.build()
