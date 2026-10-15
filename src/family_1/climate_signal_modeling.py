"""Small prespecified G/H Elastic Net ablations on existing frozen CV."""
import json,shutil,warnings
import numpy as np
import pandas as pd
import joblib
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import ElasticNet,LinearRegression
from sklearn.model_selection import GridSearchCV,GroupKFold,KFold
from sklearn.exceptions import ConvergenceWarning
from .climate_signal_features import *
from .rainfall_pcr import load_frozen_splits
from .rainfall_pcr_audit import REFERENCE

ALPHAS=[.01,.1,1.];L1=[.1,.5,.9]
COMPACT=[f'{v}_cycle_{s}' for v in ['tmin','tmax','tmean','dtr'] for s in ['mean','std','slope_per_day']]
ALIASES={'G0_MEAN':'H0_MEAN','G1_TMIN':'H2_TMIN','G2_TMAX':'H3_TMAX','G3_TMIN_TMAX':'H4_TMIN_TMAX'}

def specifications(original_columns,g_pca):
    specs={
        'G1_TMIN':('G',MIN,'enet'),'G2_TMAX':('G',MAX,'enet'),
        'G3_TMIN_TMAX':('G',TEMP,'enet'),'G4_TMEAN_DTR':('G',THERMAL['tmean']+THERMAL['dtr'],'enet'),
        'G5_COMPACT':('G',COMPACT,'enet'),
        'H1_RAIN':('H',RAIN,'enet'),'H5_RAIN_TMIN':('H',RAIN+MIN,'enet'),
        'H6_RAIN_TMAX':('H',RAIN+MAX,'enet'),'H7_JOINT':('H',JOINT,'enet'),
        'H8_CLIMATE_CURRENT_ORIGINAL':('H',original_columns,'original'),
        'H_S1_AGG_RAIN':('H',[c for c in original_columns if c.startswith('CLIMATE_precip_')],'enet'),
        'H_S2_AGG_THERMAL':('H',[c for c in original_columns if not c.startswith('CLIMATE_precip_')],'enet'),
        'H_S3_COMPACT_JOINT':('H',COMPACT+['CLIMATE_precip_total','CLIMATE_precip_std','CLIMATE_precip_late_sum'],'enet'),
        'H_S4_JOINT_PCR':('H',JOINT,'joint_pcr'),
        'H_S5_SEPARATE_PCR':('H',JOINT,'separate_pcr')}
    thermal=next(p for p in g_pca if p['name']=='Tmin_Tmax')
    if thermal['k95']<=4:specs['G6_THERMAL_PCR']=('G',TEMP,'thermal_pcr')
    return specs

def estimator(kind):
    pipe=Pipeline([('imputer',SimpleImputer(strategy='median')),('scaler',StandardScaler()),
        ('model',ElasticNet(max_iter=20000,random_state=2026))])
    grid={'model__alpha':ALPHAS,'model__l1_ratio':L1}
    if kind in ['thermal_pcr','joint_pcr']:
        limit=14 if kind=='thermal_pcr' else 21
        pipe=Pipeline([('imputer',SimpleImputer(strategy='median')),('scaler',StandardScaler()),
            ('pca',PCA(svd_solver='full')),('model',LinearRegression())])
        grid={'pca__n_components':[k for k in [1,2,4,7,10,14,21] if k<=limit]}
    elif kind=='separate_pcr':
        block=lambda:Pipeline([('imputer',SimpleImputer(strategy='median')),('scaler',StandardScaler()),('pca',PCA(n_components=.95,svd_solver='full'))])
        pipe=Pipeline([('blocks',ColumnTransformer([('rain',block(),RAIN),('thermal',block(),TEMP)])),('model',LinearRegression())])
        grid={'blocks__rain__pca__n_components':[.90,.95,.99],'blocks__thermal__pca__n_components':[.95]}
    return pipe,grid

def tune(X,y,inner,kind):
    pipe,grid=estimator(kind)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always',ConvergenceWarning)
        search=GridSearchCV(pipe,grid,cv=inner,scoring='neg_root_mean_squared_error',n_jobs=1,error_score='raise',return_train_score=False).fit(X,y)
    search.convergence_warning_count_=sum(issubclass(w.category,ConvergenceWarning) for w in caught)
    if search.convergence_warning_count_:raise ValueError('ElasticNet did not converge; do not silently use failed fits')
    return search

def partition_signature(groups):
    return {frozenset(np.flatnonzero(np.asarray(groups)==g)) for g in np.unique(groups)}

def validation_splits(train,out):
    splits,table,groups=load_frozen_splits(train)
    # Original source-contribution inner folds must match byte-for-byte ID ordering.
    for idx,(protocol,rep,fold,tr,va,inner) in enumerate(splits[:50]):
        original=list(KFold(4,shuffle=True,random_state=2026+idx).split(tr))
        if not all(np.array_equal(a[1],b[1]) for a,b in zip(original,inner)):raise ValueError('Original inner assignments differ')
    membership=pd.read_csv(paths('H',out.name)[0]/'tables/06_profile_memberships.csv').set_index(ID).loc[train[ID]]
    old=groups.loc[train[ID],'climate_profile'].to_numpy();joint=membership.joint.to_numpy()
    equal=partition_signature(old)==partition_signature(joint)
    rows=[]
    if not equal:
        for fold,(tr,va) in enumerate(GroupKFold(5).split(train,groups=joint),1):
            inner=list(GroupKFold(4).split(train.iloc[tr],groups=joint[tr]))
            splits.append(('joint_profile',1,fold,tr,va,inner))
            rows.append(dict(protocol='joint_profile',repeat=1,fold=fold,train_ID_POLIGONO=json.dumps(train.iloc[tr][ID].tolist()),validation_ID_POLIGONO=json.dumps(train.iloc[va][ID].tolist()),inner_validation_ID_POLIGONO=json.dumps([train.iloc[tr].iloc[v][ID].tolist() for _,v in inner]),seed=2026))
    if rows:table=pd.concat([table,pd.DataFrame(rows)],ignore_index=True)
    table.to_csv(out/'splits/outer_and_inner_splits.csv',index=False)
    groups.assign(joint_profile=joint).to_csv(out/'splits/group_memberships.csv')
    (out/'splits/profile_protocol_definition.json').write_text(json.dumps(dict(
        climate_profile='existing rainfall complete-link groups from Jan2022–Oct2025, <=.01 mm coordinate difference',
        joint_profile='exact 21-value Apr-Oct2025 rain+Tmin+Tmax profile',
        joint_partition_equal_existing_rain_partition=equal,
        policy='If identical membership partitions, existing folds serve both definitions; otherwise separate named joint_profile protocol added'),indent=2),encoding='utf-8')
    return splits

def cached_original(out,train):
    source=ROOT/'outputs/modeling/family_1/source_contribution'
    p=pd.read_parquet(source/'predictions/source_oof_predictions.parquet')
    p=p[p.pipeline.eq('ENET_CLIMATE_ONLY')][[ID,'repeat','fold','y_true','y_pred']].copy()
    if set(p[ID])!=set(train[ID]) or len(p)!=1380:raise ValueError('Original Climate Current cache incomplete')
    p['protocol']='random';p['experiment']='H8_CLIMATE_CURRENT_ORIGINAL'
    hp=pd.read_csv(source/'checkpoints/ENET_CLIMATE_ONLY_hyper.csv')
    p.to_parquet(out/'tables/30_original_climate_current_random_cached.parquet',index=False)
    hp.to_csv(out/'tables/30_original_climate_current_hyperparameters.csv',index=False)
    return p,hp

def run_models(run_id):
    gout,gproc=paths('G',run_id);hout,hproc=paths('H',run_id)
    if not (hout/'descriptive_complete.json').exists():raise ValueError('Complete G and H descriptive phases first')
    if (hout/'manifest.json').exists():raise FileExistsError('Completed run immutable; use new run-id')
    verify_snapshot(gout)
    frame=pd.read_parquet(gproc/'climate_candidates_197.parquet');original,original_cols=climate_current()
    frame=frame.merge(original,on=ID,validate='one_to_one');train=supervised_data(frame,pd.read_csv(MASTER))
    splits=validation_splits(train,hout)
    for n in ['outer_and_inner_splits.csv','group_memberships.csv','profile_protocol_definition.json']:shutil.copy2(hout/'splits'/n,gout/'splits'/n)
    g_pca=json.loads((gout/'report/exploratory_pca_summary.json').read_text(encoding='utf-8'))
    specs=specifications(original_cols,g_pca)
    config=dict(hypothesis='H1 thermal complementarity to precipitation',seed=2026,
        primary_algorithm='original Climate Current ElasticNet',alpha_grid=ALPHAS,l1_ratio_grid=L1,
        imputation='median within train',scaling='StandardScaler within train',selection='mean inner-fold RMSE; ties first grid entry',
        specs={k:dict(section=s,columns=c,kind=t) for k,(s,c,t) in specs.items()},
        aliases=ALIASES,thermal_PCR_gate='descriptive thermal k95<=4; no use of Y',
        PCR_role='limited secondary OLS sensitivity, distinct from primary ENET ablations',
        grouped_h8='original 48-feature specification refitted only for new grouped protocols',
        primary_metrics='mean of each complete 138-parcel OOF repetition; prior mean-fold metrics separate',
        no_later_than_october_2025=True,hidden_y_used=False,geography_topography_satellite_predictors=False)
    for out in [gout,hout]:
        file=out/'configuration.json'
        if file.exists() and json.loads(file.read_text(encoding='utf-8'))!=config:raise ValueError('Checkpoint configuration changed')
        file.write_text(json.dumps(config,indent=2),encoding='utf-8')
    cache,hp=cached_original(hout,train)
    base=pd.read_parquet(REFERENCE/'tables/02_oof_predictions.parquet');base=base[base.experiment.eq('E0_MEAN')].copy()
    base['experiment']='H0_MEAN';base=base[[ID,'protocol','repeat','fold','y_true','y_pred','experiment']]
    # No previous model retraining: baseline and random original Climate Current cached.
    predictions=[base,cache];registry=[];tuning=[];coefficients=[]
    ordered=sorted(specs,key=lambda n:(specs[n][0]!='G',n))
    for name in ordered:
        section,cols,kind=specs[name];out=gout if section=='G' else hout
        print(f'{section} START {name}: {len(cols)} columns, {len(splits)} folds',flush=True)
        rows=[]
        for idx,(protocol,rep,fold,tr,va,inner) in enumerate(splits):
            if kind=='original' and protocol=='random':
                q=cache[(cache['repeat']==rep)&(cache.fold==fold)].set_index(ID).loc[train.iloc[va][ID]]
                if not np.allclose(q.y_true,train.iloc[va][TARGET]):raise ValueError('Cached targets incompatible')
                par=json.loads(hp[(hp['repeat']==rep)&(hp.fold==fold)].iloc[0].best_params)
                registry.append(dict(protocol=protocol,experiment=name,repeat=rep,fold=fold,columns=json.dumps(cols),parameters=json.dumps(par),n_train=len(tr),n_validation=len(va),status='cached original predictions; no refit',n_selected_features=48))
                continue
            key=dict(protocol=protocol,experiment=name,repeat=rep,fold=fold)
            checkpoint=out/'checkpoints'/f'{protocol}_{rep:02d}_{fold:02d}_{name}.joblib'
            if checkpoint.exists():pack=joblib.load(checkpoint)
            else:
                search=tune(train.iloc[tr][cols],train.iloc[tr][TARGET],inner,'enet' if kind=='original' else kind)
                model=search.best_estimator_;pred=model.predict(train.iloc[va][cols])
                pack={'predictions':[{**key,ID:pid,'y_true':float(y),'y_pred':float(p)} for pid,y,p in zip(train.iloc[va][ID],train.iloc[va][TARGET],pred)],
                    'registry':{**key,'columns':json.dumps(cols),'parameters':json.dumps(search.best_params_),
                        'n_train':len(tr),'n_validation':len(va),'inner_RMSE':float(-search.best_score_),
                        'convergence_warnings':search.convergence_warning_count_,'status':'fit inside train',
                        'n_selected_features':int(np.sum(abs(model.named_steps['model'].coef_)>1e-10)),
                        'selected_K':int(model.named_steps['pca'].n_components_) if 'pca' in model.named_steps else np.nan},
                    'tuning':[{**key,'parameters':json.dumps(p),'inner_RMSE':float(-score),'rank':int(rank)} for p,score,rank in zip(search.cv_results_['params'],search.cv_results_['mean_test_score'],search.cv_results_['rank_test_score'])],
                    'coefficients':[]}
                if 'scaler' in model.named_steps and 'pca' not in model.named_steps:
                    for c,b in zip(cols,model.named_steps['model'].coef_):pack['coefficients'].append({**key,'feature':c,'standardized_coefficient':float(b)})
                joblib.dump(model,out/'models'/f'{protocol}_{rep:02d}_{fold:02d}_{name}.joblib',compress=3)
                joblib.dump(pack,checkpoint,compress=3)
            rows.extend(pack['predictions']);registry.append(pack['registry']);tuning.extend(pack['tuning']);coefficients.extend(pack['coefficients'])
            if (idx+1)%10==0 or idx==len(splits)-1:print(f'{name} {idx+1}/{len(splits)}',flush=True)
        if rows:predictions.append(pd.DataFrame(rows))
    all_p=pd.concat(predictions,ignore_index=True)
    # Add joint-profile baseline only if a new protocol was required.
    for protocol,rep,fold,tr,va,inner in splits:
        if protocol=='joint_profile':
            b=train.iloc[va];all_p=pd.concat([all_p,pd.DataFrame({ID:b[ID], 'y_true':b[TARGET],'y_pred':train.iloc[tr][TARGET].mean(),'protocol':protocol,'repeat':rep,'fold':fold,'experiment':'H0_MEAN'})],ignore_index=True)
    gnames=[n for n in specs if specs[n][0]=='G']
    g=all_p[all_p.experiment.isin(gnames)].copy()
    b=all_p[all_p.experiment.eq('H0_MEAN')].copy();b['experiment']='G0_MEAN';g=pd.concat([g,b],ignore_index=True)
    h=all_p[~all_p.experiment.str.startswith('G')].copy()
    for old,new in ALIASES.items():
        if old=='G0_MEAN':continue
        q=g[g.experiment.eq(old)].copy();q['experiment']=new;h=pd.concat([h,q],ignore_index=True)
    r=pd.DataFrame(registry);t=pd.DataFrame(tuning);co=pd.DataFrame(coefficients)
    for section,out,p in [('G',gout,g),('H',hout,h)]:
        p.to_parquet(out/'tables/31_oof_individual.parquet',index=False)
        p.to_csv(out/'tables/31_oof_individual.csv',index=False)
        mask=r.experiment.str.startswith(section);r[mask].to_csv(out/'tables/32_experiment_registry.csv',index=False)
        t[t.experiment.str.startswith(section)].to_csv(out/'tables/33_inner_tuning.csv',index=False)
        co[co.experiment.str.startswith(section)].to_csv(out/'tables/34_standardized_coefficients.csv',index=False)
    (hout/'tables/35_reused_g_models.json').write_text(json.dumps(ALIASES,indent=2),encoding='utf-8')
    from .climate_signal_reporting import finish
    finish(run_id,train,g,h,config)
    verify_snapshot(gout)
    write_manifests(run_id)
    print('G/H complete; previous protected artifacts unchanged',flush=True)

def write_manifests(run_id):
    """Capture final reports and verification products without self-referential hashes."""
    import platform,importlib.metadata
    sources=list((ROOT/'src/family_1').glob('climate_signal*.py'))+list((ROOT/'scripts/modeling').glob('31[678]_*.py'))
    sources+=list((ROOT/'tests').glob('test_climate_signal*.py'))
    documentation=ROOT/'documentation/g_h_climate_signal_exploration.md'
    if documentation.exists():sources.append(documentation)
    gout,_=paths('G',run_id);hout,_=paths('H',run_id)
    for section,out in [('G',gout),('H',hout)]:
        proc=paths(section,run_id)[1]
        m=dict(status='complete',section=section,train_n=138,all_n=197,hidden_y_used=False,original_results_unchanged=True,python=platform.python_version(),
            packages={p:importlib.metadata.version(p) for p in ['numpy','pandas','scikit-learn','geopandas','rasterio']},
            source_hashes={str(p.relative_to(ROOT)):sha(p) for p in sources},
            artifacts={str(p.relative_to(ROOT)):sha(p) for p in list(out.rglob('*'))+list(proc.rglob('*')) if p.is_file() and 'checkpoints' not in p.parts and p.name!='manifest.json'})
        (out/'manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
