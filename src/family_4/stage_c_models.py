"""Stage C only: frozen transfer contrasts first, then matched hierarchical controls."""
from pathlib import Path
import json,itertools
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import GridSearchCV
from . import stage_b_learning as b
from .stage_c_hierarchy import ProfileGaussianRidge

ROOT,ID,TARGET,RAIN=b.ROOT,b.ID,b.TARGET,b.RAIN
OUT=b.OUT.parent/'stage_c';PROC=b.PROC.parent/'stage_c'
NDVI=b.e.f.NDVI;DTR=b.e.f.DTR
COMPACT=['compact_precip_total','compact_early_fraction','compact_concentration_hhi']
T_SPECS={'C-T2':RAIN+[NDVI,DTR],'C-T3':COMPACT+[NDVI],'C-T4':COMPACT+[NDVI,DTR]}
RATIO=[0.,.1,.3,1.,3.]

def compact_features(frame):
    p=frame[RAIN].to_numpy(float)
    if np.nanmin(p)<0:raise ValueError('Negative rainfall incompatible with concentration shares')
    total=np.sum(p,axis=1);denom=total+1e-6;result=pd.DataFrame(index=frame.index)
    result[COMPACT[0]]=total;result[COMPACT[1]]=p[:,:3].sum(axis=1)/denom;result[COMPACT[2]]=np.sum((p/denom[:,None])**2,axis=1)
    return result

def load():
    d,_=b.e.f.load();d=d[[ID,'CONJUNTO','climate_profile','Municipio','Estado']+RAIN+[NDVI,DTR]].copy()
    d=pd.concat([d,compact_features(d)],axis=1)
    t=b.e.f.lm.k.j.supervised_data(d,pd.read_csv(b.e.f.lm.k.j.MASTER))
    assert len(d)==197 and len(t)==138 and TARGET not in d and d.climate_profile.nunique()==53
    return d,t

def freeze():
    if (OUT/'manifest.json').exists():raise FileExistsError('Completed Stage C immutable')
    assert json.loads((b.OUT/'manifest.json').read_text())['status']=='complete'
    for p in [OUT,PROC]+[OUT/x for x in ['audit','tables','models','checkpoints','figures','report','splits']]:p.mkdir(parents=True,exist_ok=True)
    d,t=load();splits,table,groups=b.e.f.lm.k.j.load_frozen_splits(t)
    config=dict(stage='C',stage_d=False,transfer_specs=T_SPECS,controls={'C-T0':'F4-S1','C-T1':'F4-S5','C-H0':'C-T0 EN reference'},hierarchical_fixed_columns=RAIN+[NDVI],matched_control='C-H0M Gaussian GLS/Ridge, variance ratio0',hierarchical_model='C-H1 same Gaussian GLS/Ridge, random intercept only; no random slopes',alpha=b.e.f.lm.k.ALPHA,l1_ratio=b.e.f.lm.k.L1,variance_ratio_grid=RATIO,h_selection='min mean innerfold RMSE; deterministic ties smaller ratio, stronger alpha',t_selection='original EN grid mean innerfold RMSE',compact_definition=dict(total='sum seven months, mm',early_fraction='(Apr+May+Jun)/(total+1e-6mm)',concentration='sum[(P_month/(total+1e-6mm))^2]',zero_rainfall='all summaries0; no month window selected byY',no_extra_july_feature=True),variance_formula='sigma2=ML whitened residual SSE/n at fitted fixed effects; tau2=ratio*sigma2',fixed_regularization='sklearnRidge(alpha=n*alpha); same in H0M and H1',intervals='90% Gaussian working posterior, fixed sigma/ratio/alpha; integrates conditional random-effect uncertainty and fixed-effect covariance; new profiles addtau2; excludes hyperparameter estimation uncertainty',tau_boundary='ratio0 exact matched no-random-effect model',source_hashes={str(p.relative_to(ROOT)):b.a.sha(p) for p in [Path(__file__),ROOT/'src/family_4/stage_c_hierarchy.py',ROOT/'src/family_4/conditional_response.py']},exploratory=True,no_new_territorial_predictors=True,no_stage_b_loss=True,no_blend=True,decision_margin=.01,support_limits='outertrain marginal min/max,near boundary within5% training range; standardized joint nearest training distance on DTR/total/NDVI; descriptive only')
    path=OUT/'frozen_design.json'
    if path.exists():assert json.loads(path.read_text())==json.loads(json.dumps(config))
    else:path.write_text(json.dumps(config,indent=2),encoding='utf8')
    d.to_parquet(PROC/'c_features_197_target_free.parquet',index=False);table.to_csv(OUT/'splits/outer_and_inner_splits.csv',index=False);groups.to_csv(OUT/'splits/group_memberships.csv')
    old=pd.read_parquet(b.e.f.OUT/'tables/oof_predictions.parquet');old=old[old.experiment.isin(['F4-S1','F4-S5'])].copy();old['source_experiment']=old.experiment;old.experiment=old.experiment.map({'F4-S1':'C-T0','F4-S5':'C-T1'})
    h0=old[old.experiment.eq('C-T0')].copy();h0.experiment='C-H0';old=pd.concat([old,h0],ignore_index=True)
    assert len(old)==3*1794
    old.to_parquet(OUT/'tables/archived_controls.parquet',index=False)
    # Audit, not replacement: DTR is the supplied temporal sample SD, not Tmax mean.
    monthly=pd.read_parquet(ROOT/'data/processed/family_1/environment/climate_monthly_timeseries.parquet')
    monthly=monthly[monthly.date_month.between('2025-04-01','2025-10-31')]
    recovered=monthly.groupby(ID).dtr_mean.std(ddof=1)
    assert np.allclose(d[DTR],d[ID].map(recovered),atol=1e-10)
    assert np.allclose(monthly.dtr_mean,monthly.tmax_mean-monthly.tmin_mean,atol=1e-10)
    for c in [DTR]+RAIN:assert d.groupby('climate_profile')[c].nunique().max()==1
    pd.DataFrame([dict(feature=c,definition=config['compact_definition'].get({'compact_precip_total':'total','compact_early_fraction':'early_fraction','compact_concentration_hhi':'concentration'}.get(c,''),'original supplied Apr-Oct2025 feature'),n_valid=d[c].notna().sum()) for c in RAIN+[NDVI,DTR]+COMPACT]).to_csv(OUT/'audit/feature_dictionary.csv',index=False)
    d[RAIN+[DTR,NDVI]+COMPACT].corr().to_csv(OUT/'audit/predictor_redundancy.csv')
    compact=t[COMPACT].to_numpy();rank=int(np.linalg.matrix_rank(np.column_stack([np.ones(len(t)),compact])));assert rank==4
    (OUT/'audit/semantic_audit.json').write_text(json.dumps(dict(n_labels=138,n_unlabelled=59,n_profiles_labelled=43,dtr_reproduced=True,dtr_ddof=1,window='Apr-Oct2025; NDVI May2025',compact_affine_rank=rank,compact_max_condition=float(np.linalg.cond((compact-compact.mean(axis=0))/compact.std(axis=0))),no_y_in_feature_construction=True),indent=2),encoding='utf8')
    return splits

def control_gate():
    _,t=load();rows=[]
    for protocol,repeat,fold,tr,va,inner in b.e.f.lm.k.j.load_frozen_splits(t)[0]:
        for name,source in [('C-T0','F4-S1'),('C-T1','F4-S5')]:
            pack=joblib.load(b.e.f.OUT/'models'/f'{source}_{protocol}_{repeat}_{fold}.joblib');old=pack['model'];cols=RAIN+[NDVI if name=='C-T0' else DTR]
            pipe=b.e.f.model({'kind':'direct','cols':cols[7:]})
            fitted=b.e.f.lm.k.strict_fit(pipe.set_params(model__alpha=old['model'].alpha,model__l1_ratio=old['model'].l1_ratio),t.iloc[tr][cols],t.iloc[tr][TARGET])
            diff=float(abs(fitted.predict(t.iloc[va][cols])-old.predict(t.iloc[va])).max());assert diff<=1e-10
            rows.append(dict(experiment=name,protocol=protocol,repeat=repeat,fold=fold,max_abs_difference=diff,source_model=str((b.e.f.OUT/'models'/f'{source}_{protocol}_{repeat}_{fold}.joblib').relative_to(ROOT))))
    pd.DataFrame(rows).to_csv(OUT/'audit/control_reproduction.csv',index=False);print('C-T controls reproduced:',len(rows),flush=True)

def fit_transfer(index):
    _,t=load();splits,_,_=b.e.f.lm.k.j.load_frozen_splits(t);protocol,repeat,fold,tr,va,inner=splits[index];a,v=t.iloc[tr],t.iloc[va]
    for name,columns in T_SPECS.items():
        dest=OUT/'checkpoints'/f'{name}_{protocol}_{repeat}_{fold}.joblib'
        if dest.exists():continue
        # ConditionalFeatures/ElasticNet precisely as archived, with declared columns.
        from sklearn.pipeline import Pipeline
        from sklearn.linear_model import ElasticNet
        pipe=Pipeline([('repr',b.e.f.ConditionalFeatures(tuple(columns))),('model',ElasticNet(max_iter=200000,random_state=2026))])
        search=b.e.f.lm.k.strict_fit(GridSearchCV(pipe,b.e.f.GRID,cv=inner,scoring='neg_root_mean_squared_error',n_jobs=1,error_score='raise'),a[columns],a[TARGET])
        model=search.best_estimator_;pred=model.predict(v[columns]);key=dict(experiment=name,protocol=protocol,repeat=repeat,fold=fold)
        rows=[{**key,ID:pid,'y_true':float(y),'y_pred':float(p)} for pid,y,p in zip(v[ID],v[TARGET],pred)]
        reg={**key,'params':json.dumps(search.best_params_),'inner_rmse':-search.best_score_,'train_ids':json.dumps(a[ID].tolist()),'validation_ids':json.dumps(v[ID].tolist())}
        co=[{**key,'feature':c,'coefficient':float(beta)} for c,beta in zip(model['repr'].get_feature_names_out(),model['model'].coef_)]
        joblib.dump(model,OUT/'models'/dest.name,compress=3);joblib.dump(dict(predictions=rows,registry=reg,coefficients=co,tuning=[{**key,'params':json.dumps(params),'inner_rmse':-score} for params,score in zip(search.cv_results_['params'],search.cv_results_['mean_test_score'])]),dest,compress=3)
    print('C-T FOLD',index+1,protocol,flush=True)

def fit_hierarchy(index):
    _,t=load();splits,_,_=b.e.f.lm.k.j.load_frozen_splits(t);protocol,repeat,fold,tr,va,inner=splits[index];a,v=t.iloc[tr],t.iloc[va];columns=RAIN+[NDVI]
    for name,ratios in [('C-H0M',[0.]),('C-H1',RATIO)]:
        dest=OUT/'checkpoints'/f'{name}_{protocol}_{repeat}_{fold}.joblib'
        if dest.exists():continue
        candidates=[]
        for alpha,ratio in itertools.product(b.e.f.lm.k.ALPHA,ratios):
            scores=[]
            for itr,iva in inner:
                aa,bb=a.iloc[itr],a.iloc[iva];model=ProfileGaussianRidge(tuple(columns),alpha,ratio).fit(aa,aa[TARGET]);pred=model.predict(bb)
                scores.append(np.sqrt(np.mean((bb[TARGET].to_numpy()-pred)**2)))
            candidates.append(dict(alpha=alpha,ratio=ratio,inner_rmse=float(np.mean(scores))))
        chosen=min(candidates,key=lambda r:(round(r['inner_rmse'],10),r['ratio'],-r['alpha']))
        model=ProfileGaussianRidge(tuple(columns),chosen['alpha'],chosen['ratio']).fit(a,a[TARGET]);pieces=model.predict_components(v);key=dict(experiment=name,protocol=protocol,repeat=repeat,fold=fold)
        rows=[{**key,ID:pid,'y_true':float(y),'y_pred':float(pieces['prediction'][j]),**{field:float(pieces[field][j]) if field not in ['profile_known','n_training_profile'] else bool(pieces[field][j]) if field=='profile_known' else int(pieces[field][j]) for field in ['fixed_prediction','random_effect','profile_known','n_training_profile','predictive_sd','lower','upper']}} for j,(pid,y) in enumerate(zip(v[ID],v[TARGET]))]
        registry={**key,**chosen,**model.diagnostics_,'train_ids':json.dumps(a[ID].tolist()),'validation_ids':json.dumps(v[ID].tolist())}
        co=[{**key,'feature':c,'coefficient':float(beta)} for c,beta in zip(model.preprocess_.get_feature_names_out(),model.coef_)]
        effects=[{**key,'profile':int(group),'effect':info['effect'],'n_train':info['n_train'],'posterior_variance':info['posterior_variance']} for group,info in model.groups_.items()]
        joblib.dump(model,OUT/'models'/dest.name,compress=3);joblib.dump(dict(predictions=rows,registry=registry,coefficients=co,tuning=[{**key,**c} for c in candidates],effects=effects),dest,compress=3)
    print('C-H FOLD',index+1,protocol,flush=True)

def collect(names,label):
    _,t=load();splits,_,_=b.e.f.lm.k.j.load_frozen_splits(t)
    packs=[joblib.load(OUT/'checkpoints'/f'{name}_{p}_{r}_{f}.joblib') for p,r,f,*_ in splits for name in names]
    p=pd.DataFrame([row for pack in packs for row in pack['predictions']]);p.to_parquet(OUT/'tables'/f'{label}_new_oof.parquet',index=False)
    for field in ['registry','coefficients','tuning','effects']:
        rows=[row for pack in packs if field in pack for row in (pack[field] if isinstance(pack[field],list) else [pack[field]])]
        if rows:pd.DataFrame(rows).to_csv(OUT/'tables'/f'{label}_{field}.csv',index=False)
    return p

def run(workers=3):
    freeze();control_gate()
    joblib.Parallel(n_jobs=workers,backend='loky',inner_max_num_threads=1)(joblib.delayed(fit_transfer)(i) for i in range(65))
    transfer=collect(list(T_SPECS),'transfer')
    from . import stage_c_reporting
    stage_c_reporting.transfer_audit(transfer)
    # Only after transfer diagnostics, fit matched control and random-intercept model.
    joblib.Parallel(n_jobs=workers,backend='loky',inner_max_num_threads=1)(joblib.delayed(fit_hierarchy)(i) for i in range(65))
    hierarchy=collect(['C-H0M','C-H1'],'hierarchy')
    allp=pd.concat([pd.read_parquet(OUT/'tables/archived_controls.parquet'),transfer,hierarchy],ignore_index=True);assert len(allp)==8*1794
    allp.to_parquet(OUT/'tables/oof_predictions.parquet',index=False);stage_c_reporting.build(allp)
