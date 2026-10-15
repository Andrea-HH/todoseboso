"""F4-E: frozen additive contrasts after NDVI May; no residual stage or rescreening."""
from pathlib import Path
import json,hashlib,itertools
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import GridSearchCV
from . import conditional_response as f

ROOT,ID,TARGET,RAIN=f.ROOT,f.ID,f.TARGET,f.RAIN
OUT=ROOT/'outputs/modeling/family_4/conditional_yield_response/extensions/within_profile_complementarity/v1'
PROC=ROOT/'data/processed/family_4/conditional_yield_response/extensions/within_profile_complementarity/v1'
RISE='S2_lai_promedio_runup_start_day'
LAI='S2_lai_promedio_q10'
RELIEF='TOPO_ADV_local_relief_3x3_mean'
FAPAR='S2_fapar_promedio_q10'
EVI='S2_evi_month_05'
SLOPE='TOPO_BASIC_slope_q10'
SIN='TOPO_ADV_aspect_sin_mean'
COS='TOPO_ADV_aspect_cos_mean'
CANDIDATES=[f.NDVI,f.Q10,LAI,FAPAR,EVI,RISE,f.SAVI,RELIEF,SLOPE,SIN,COS]
SPECS={'F4-E2':dict(kind='direct',cols=[f.NDVI,RISE]),'F4-E3':dict(kind='direct',cols=[f.NDVI,RELIEF]),'F4-E4':dict(kind='direct',cols=[LAI])}
LABELS={f.NDVI:'NDVI mayo',f.Q10:'NDVI q10',LAI:'LAI q10',FAPAR:'FAPAR q10',EVI:'EVI mayo',RISE:'Inicio ascenso LAI',f.SAVI:'Duración ascenso SAVI',RELIEF:'Relieve local medio',SLOPE:'Pendiente q10',SIN:'Orientación seno',COS:'Orientación coseno'}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def load():
    d,t=f.load();features=pd.read_parquet(ROOT/'data/processed/family_1/features/family1_features_all.parquet')
    missing=[c for c in CANDIDATES if c not in d]
    d=d.merge(features[[ID]+missing],on=ID,validate='one_to_one')
    assert len(d)==197 and TARGET not in d and d[ID].is_unique
    t=f.lm.k.j.supervised_data(d,pd.read_csv(f.lm.k.j.MASTER))
    assert len(t)==138 and len(d)-len(t)==59 and d.climate_profile.nunique()==53
    return d,t

def within(frame,columns):
    counts=frame.groupby('climate_profile')[ID].transform('size')
    z=frame[counts>=2].copy()
    return z[columns]-z.groupby('climate_profile')[columns].transform('mean'),z

def audit():
    if (OUT/'manifest.json').exists():raise FileExistsError('Completed extension immutable')
    for p in [OUT,PROC]+[OUT/x for x in ['tables','audit','figures','models','checkpoints','splits','report']]:p.mkdir(parents=True,exist_ok=True)
    d,t=load()
    # Verify frozen Family 4 and recover its controls before exploring new candidates.
    previous=json.loads((f.OUT/'manifest.json').read_text());checks=[]
    for path,digest in previous['artifacts'].items():
        actual=sha(ROOT/path);checks.append(dict(path=path,sha256=digest,matches=actual==digest))
    assert all(x['matches'] for x in checks)
    pd.DataFrame(checks).to_csv(OUT/'audit/previous_family4_integrity.csv',index=False)
    controls=[]
    for old,name in [('J0_RAIN','F4-E0'),('F4-S1','F4-E1')]:
        path=f.lm.k.j.locations()[0]/'tables/02_oof_predictions.parquet' if old=='J0_RAIN' else f.OUT/'tables/oof_predictions.parquet'
        z=pd.read_parquet(path);z=z[z.experiment.eq(old)].copy();z['source_experiment']=old;z['experiment']=name
        assert len(z)==1794
        controls.append(z)
    pd.concat(controls,ignore_index=True).to_parquet(OUT/'tables/control_oof.parquet',index=False)
    dictionary=pd.read_csv(ROOT/'data/processed/family_1/features/family1_feature_dictionary.csv')
    entries=dictionary[dictionary.feature_name.isin(CANDIDATES)].copy()
    for col,idx in [(f.NDVI,'ndvi'),(EVI,'evi')]:
        entries=pd.concat([entries,pd.DataFrame([dict(feature_name=col,source='S2',sensor='S2',variable=idx+'_promedio',statistic='monthly_mean',window='2025-05-01/2025-05-31',description='Arithmetic mean of valid supplied parcel means; canonical M feature')])],ignore_index=True)
    entries['interpretation_reserve']=''
    entries.loc[entries.feature_name.eq(LAI),'interpretation_reserve']='Negative source values; supplied LAI index, physical scaling not established'
    entries.loc[entries.feature_name.eq(RISE),'interpretation_reserve']='Days since Apr1 at running minimum preceding maximal later rise; not emergence/planting'
    entries.loc[entries.feature_name.eq(RELIEF),'interpretation_reserve']='Mean parcel coverage-weighted max-minus-min elevation in3x3 DEM120m cells; meters,360m footprint'
    entries.loc[entries.feature_name.isin([SIN,COS]),'interpretation_reserve']='Mean sin/cos of raster aspect=atan2(-gx,gy); circular vector components; weak meaning on flat terrain'
    entries.to_csv(OUT/'audit/feature_dictionary.csv',index=False)
    d[[ID,'CONJUNTO','climate_profile']+RAIN+CANDIDATES].to_parquet(PROC/'features_197_target_free.parquet',index=False)
    # Descriptive association matrices: no predictive transformation is learned here.
    columns=CANDIDATES+[TARGET]
    w,eligible=within(t,columns)
    groups=t.groupby('climate_profile')[columns].mean()
    for method in ['pearson','spearman']:
        t[columns].corr(method=method).to_csv(OUT/'audit'/f'global_{method}.csv')
        w.corr(method=method).to_csv(OUT/'audit'/f'within_{method}.csv')
        groups.corr(method=method).to_csv(OUT/'audit'/f'between_profile_{method}.csv')
    t.groupby('climate_profile').size().rename('n').to_csv(OUT/'audit/profile_sizes.csv')
    decomp=[]
    for c in columns:
        z=t[[c,'climate_profile']].dropna();mean=z.groupby('climate_profile')[c].transform('mean');total=np.sum((z[c]-z[c].mean())**2);between=np.sum((mean-z[c].mean())**2)
        decomp.append(dict(feature=c,n=len(z),n_profiles=z.climate_profile.nunique(),total_ss=total,between_fraction=between/total,within_fraction=1-between/total,within_y_correlation=w[c].corr(w[TARGET]),between_mean_y_correlation=groups[c].corr(groups[TARGET]),n_within_parcels=len(eligible),n_within_profiles=eligible.climate_profile.nunique()))
    pd.DataFrame(decomp).to_csv(OUT/'audit/within_between_decomposition.csv',index=False)
    associations=[]
    scopes=[('all',t),('without_Chignahuapan',t[t.Municipio.ne('Chignahuapan')])]
    scopes += [('state:'+str(v),g) for v,g in t.groupby('Estado')]
    scopes += [('municipality:'+str(v),g) for v,g in t.groupby('Municipio')]
    scopes += [('leave_profile:'+str(v),t[t.climate_profile.ne(v)]) for v in t.climate_profile.unique()]
    for scope,z in scopes:
        ww,ee=within(z,columns)
        for a,b in itertools.combinations(columns,2):
            for level,data in [('global',z),('within',ww)]:
                valid=data[[a,b]].dropna()
                for method in ['pearson','spearman']:
                    correlation=valid[a].corr(valid[b],method=method) if len(valid)>2 and valid[a].std()>1e-12 and valid[b].std()>1e-12 else np.nan
                    associations.append(dict(scope=scope,level=level,a=a,b=b,method=method,correlation=correlation,n=len(valid),n_profiles=z.climate_profile.nunique() if level=='global' else ee.climate_profile.nunique()))
    pd.DataFrame(associations).to_csv(OUT/'audit/associations_by_scope.csv',index=False)
    partial=[]
    for scope,z in scopes:
        ww,ee=within(z,columns)
        for c in CANDIDATES:
            if c==f.NDVI:continue
            zz=ww[[f.NDVI,c,TARGET]].dropna()
            if len(zz)<5:continue
            design=np.column_stack([np.ones(len(zz)),zz[f.NDVI]])
            rx=zz[c].to_numpy()-design@np.linalg.lstsq(design,zz[c],rcond=None)[0]
            ry=zz[TARGET].to_numpy()-design@np.linalg.lstsq(design,zz[TARGET],rcond=None)[0]
            partial.append(dict(scope=scope,feature=c,n=len(zz),n_profiles=ee.climate_profile.nunique(),partial_within_correlation=pd.Series(rx).corr(pd.Series(ry)),feature_residual_y_correlation=pd.Series(rx).corr(zz[TARGET].reset_index(drop=True))))
    pd.DataFrame(partial).to_csv(OUT/'audit/partial_within_ndvi.csv',index=False)
    quality_audit(d)
    config=dict(candidates=CANDIDATES,specs=SPECS,controls={'F4-E0':'J0_RAIN','F4-E1':'F4-S1'},grid=f.GRID,primary_alternative=LAI,primary_relief=RELIEF,relief_choice='Coverage-weighted mean as representative local relief; not minimum/extreme chosen by predictive result',n_outer=65,n_train=138,n_prediction=59,retrospective=True,no_residual_stage=True,cutoff='2025-10-31',estimator='Same ConditionalFeatures and ElasticNet as frozen F4-S1; same grid and scaling',source_hashes={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'src/family_4/conditional_response.py',ROOT/'src/family_1/temporal_primitives.py',ROOT/'src/family_1/terrain_features.py']},audit_complete_before_fitting=True)
    p=OUT/'configuration.json'
    if p.exists():assert json.loads(p.read_text())==json.loads(json.dumps(config))
    else:p.write_text(json.dumps(config,indent=2),encoding='utf-8')
    _,table,assign=f.lm.k.j.load_frozen_splits(t);table.to_csv(OUT/'splits/outer_and_inner_splits.csv',index=False);assign.to_csv(OUT/'splits/group_memberships.csv')
    print('AUDIT COMPLETE; frozen E2,E3,E4; negative LAI source values documented',flush=True)

def quality_audit(d):
    ts=pd.read_parquet(ROOT/'data/processed/family_1/timeseries/sentinel_timeseries.parquet')
    ts=ts[ts.fecha_captura.between('2025-04-01','2025-10-31')]
    rows=[];monthly=[];stability=[]
    for pid,g in ts.groupby(ID):
        for index in ['ndvi','lai','fapar','evi','savi']:
            col=index+'_promedio';valid=g.loc[g[col].notna(),['fecha_captura',col,'cloud_raw']].groupby('fecha_captura').mean().reset_index().sort_values('fecha_captura')
            dates=valid.fecha_captura;cloud=g.cloud_raw
            rows.append(dict(ID_POLIGONO=pid,index=index,n_valid_dates=len(valid),n_valid_months=dates.dt.month.nunique(),missing_fraction=g[col].isna().mean(),max_gap_days=dates.diff().dt.days.max(),median_gap_days=dates.diff().dt.days.median(),n_negative=int((valid[col]<0).sum()),mean_cloud=cloud.mean(),valid_cloud_corr=g[col].notna().astype(float).corr(cloud),insufficient=bool(len(valid)<4 or dates.dt.month.nunique()<4),max_month_fraction=dates.dt.month.value_counts(normalize=True).max()))
            for month in range(4,11):
                gm=g[g.fecha_captura.dt.month.eq(month)]
                monthly.append(dict(ID_POLIGONO=pid,index=index,month=month,n_valid=int(gm[col].count()),n_rows=len(gm),mean_cloud=gm.cloud_raw.mean(),valid_fraction=gm[col].notna().mean()))
            # Sensitivity of temporal q10 and LAI rise date, descriptive only. No feature overwrite.
            if index in ['ndvi','lai','fapar'] and len(valid)>=4:
                from src.family_1.temporal_primitives import extract_temporal_features
                full=extract_temporal_features(valid.fecha_captura,valid[col])
                for month in range(4,11):
                    z=valid[valid.fecha_captura.dt.month.ne(month)]
                    r=extract_temporal_features(z.fecha_captura,z[col])
                    stability.append(dict(ID_POLIGONO=pid,index=index,omitted_month=month,q10_delta=r['q10']-full['q10'],rise_start_delta=r['runup_start_day']-full['runup_start_day']))
    pd.DataFrame(rows).to_csv(OUT/'audit/temporal_quality_by_parcel.csv',index=False)
    pd.DataFrame(monthly).to_csv(OUT/'audit/temporal_monthly_support.csv',index=False)
    pd.DataFrame(stability).to_csv(OUT/'audit/temporal_omit_month_sensitivity.csv',index=False)
    import rasterio
    with rasterio.open(ROOT/'data/processed/family_1/terrain_surfaces/local_relief_3x3.tif') as r:
        topo=dict(crs=str(r.crs),resolution=list(r.res),neighborhood_cells=3,footprint_m=360,units='Elevation differences in meters; original CEM filename/documentation',circular_encoding='atan2(-gx,gy), then zonal mean of sine and cosine; no linear angle',flat_threshold_degrees=2)
    topo['n_slope_q10_lt2']=int((d[SLOPE]<2).sum())
    (OUT/'audit/topography_definition.json').write_text(json.dumps(topo,indent=2),encoding='utf-8')
    angle=d[[ID,SLOPE,SIN,COS]].copy();angle['resultant_length']=np.hypot(angle[SIN],angle[COS]);angle['near_flat']=angle[SLOPE]<2
    angle.to_csv(OUT/'audit/circular_orientation_support.csv',index=False)

def fit_fold(index):
    _,t=load();splits,_,_=f.lm.k.j.load_frozen_splits(t);protocol,repeat,fold,tr,va,inner=splits[index]
    a,b=t.iloc[tr],t.iloc[va]
    # Replay the archived E1 control on exactly these held-out IDs.
    old=joblib.load(f.OUT/'models'/f'F4-S1_{protocol}_{repeat}_{fold}.joblib')['model']
    expected=old.predict(b)
    controls=pd.read_parquet(OUT/'tables/control_oof.parquet');ref=controls[(controls.experiment=='F4-E1')&(controls.protocol==protocol)&(controls['repeat']==repeat)&(controls.fold==fold)].set_index(ID).loc[b[ID]]
    assert np.allclose(expected,ref.y_pred,atol=1e-10,rtol=0)
    for name,spec in SPECS.items():
        dest=OUT/'checkpoints'/f'{name}_{protocol}_{repeat}_{fold}.joblib'
        if dest.exists():continue
        cols=RAIN+spec['cols']
        search=f.lm.k.strict_fit(GridSearchCV(f.model(spec),f.GRID,cv=inner,scoring='neg_root_mean_squared_error',n_jobs=1,error_score='raise'),a[cols],a[TARGET])
        model=search.best_estimator_;pred=model.predict(b[cols]);key=dict(experiment=name,protocol=protocol,repeat=repeat,fold=fold)
        pack=dict(predictions=[{**key,ID:pid,'y_true':float(y),'y_pred':float(yp),'outer_model_id':f'{name}_{protocol}_{repeat}_{fold}'} for pid,y,yp in zip(b[ID],b[TARGET],pred)],registry={**key,'params':json.dumps(search.best_params_),'inner_rmse':-search.best_score_,'train_ids':json.dumps(a[ID].tolist()),'validation_ids':json.dumps(b[ID].tolist()),'effective_features':json.dumps(model['repr'].get_feature_names_out().tolist())},tuning=[{**key,'params':json.dumps(params),'inner_rmse':-score} for params,score in zip(search.cv_results_['params'],search.cv_results_['mean_test_score'])],coefficients=f.lm.coefficient_rows(model,key,a))
        joblib.dump(model,OUT/'models'/dest.name,compress=3);joblib.dump(pack,dest,compress=3)
    print('F4-E FOLD',index+1,protocol,repeat,fold,flush=True)

def run(workers=3):
    audit()
    joblib.Parallel(n_jobs=workers,backend='loky',inner_max_num_threads=1)(joblib.delayed(fit_fold)(i) for i in range(65))
    _,t=load();splits,_,_=f.lm.k.j.load_frozen_splits(t)
    packs=[joblib.load(OUT/'checkpoints'/f'{name}_{p}_{r}_{fold}.joblib') for p,r,fold,*_ in splits for name in SPECS]
    for field in ['registry','tuning','coefficients']:
        rows=[row for pack in packs for row in (pack[field] if isinstance(pack[field],list) else [pack[field]])]
        pd.DataFrame(rows).to_csv(OUT/'tables'/f'{field}.csv',index=False)
    p=pd.DataFrame([row for pack in packs for row in pack['predictions']]);controls=pd.read_parquet(OUT/'tables/control_oof.parquet')
    controls['outer_model_id']=controls.experiment+'_'+controls.protocol+'_'+controls['repeat'].astype(str)+'_'+controls.fold.astype(str)
    p=pd.concat([p,controls],ignore_index=True);assert len(p)==5*1794
    p.to_parquet(OUT/'tables/oof_predictions.parquet',index=False)
    analyze()

def analyze():
    d,t=load();p=pd.read_parquet(OUT/'tables/oof_predictions.parquet')
    q=pd.read_csv(ROOT/'outputs/research/family_1/soil_yield_quartile_analysis/v1/parcel_quartiles.csv')[[ID,'quartile']]
    p=p.merge(d[[ID,'climate_profile','Estado','Municipio']+CANDIDATES],on=ID,validate='many_to_one').merge(q,on=ID,validate='many_to_one')
    baseline=p[p.experiment.eq('F4-E1')][[ID,'protocol','repeat','fold','y_pred']].rename(columns={'y_pred':'base_pred'})
    p=p.merge(baseline,on=[ID,'protocol','repeat','fold'],validate='many_to_one');p['increment']=p.y_pred-p.base_pred
    metrics=[];pairrows=[];dispersion=[]
    for (exp,protocol,repeat),g in p.groupby(['experiment','protocol','repeat']):
        masks={'all':np.ones(len(g),bool),'Chignahuapan':g.Municipio.eq('Chignahuapan'),'without_Chignahuapan':g.Municipio.ne('Chignahuapan')}
        masks.update({x:g.quartile.eq(x) for x in ['Q1','Q2','Q3','Q4']})
        masks.update({'municipality:'+str(v):g.Municipio.eq(v) for v in g.Municipio.unique()})
        masks.update({'state:'+str(v):g.Estado.eq(v) for v in g.Estado.unique()})
        for scope,mask in masks.items():
            z=g[mask]
            if len(z):metrics.append(dict(experiment=exp,protocol=protocol,repeat=repeat,stratum=scope,n=len(z),**f.lm.k.metrics(z.y_true,z.y_pred)))
        for (profile,fold),z in g.groupby(['climate_profile','fold']):
            if len(z)<2:continue
            z=z.sort_values(ID);a,b=np.triu_indices(len(z),1)
            observed=z.y_true.to_numpy()[a]-z.y_true.to_numpy()[b];predicted=z.y_pred.to_numpy()[a]-z.y_pred.to_numpy()[b];base=z.base_pred.to_numpy()[a]-z.base_pred.to_numpy()[b]
            for i,jj,dy,dp,db in zip(a,b,observed,predicted,base):pairrows.append(dict(experiment=exp,protocol=protocol,repeat=repeat,fold=fold,profile=profile,id_a=z[ID].iloc[i],id_b=z[ID].iloc[jj],observed_difference=dy,predicted_difference=dp,base_difference=db,pair_error=dy-dp,base_error=dy-db,Chignahuapan=bool(z.Municipio.iloc[i]=='Chignahuapan' or z.Municipio.iloc[jj]=='Chignahuapan')))
            dispersion.append(dict(experiment=exp,protocol=protocol,repeat=repeat,fold=fold,profile=profile,n=len(z),observed_sd=z.y_true.std(),predicted_sd=z.y_pred.std(),increment_sd=z.increment.std()))
    m=pd.DataFrame(metrics);m.to_csv(OUT/'tables/metrics_repeat.csv',index=False)
    m.groupby(['experiment','protocol','stratum'])[['n','RMSE','MAE','R2','bias_pred_minus_y']].mean().reset_index().to_csv(OUT/'tables/metrics_summary.csv',index=False)
    base=m[m.experiment.eq('F4-E1')]
    paired=m.merge(base,on=['protocol','repeat','stratum'],suffixes=('','_base'),validate='many_to_one')
    paired['delta_RMSE']=paired.RMSE-paired.RMSE_base;paired['delta_MAE']=paired.MAE-paired.MAE_base
    paired.to_csv(OUT/'tables/paired_repeat.csv',index=False)
    paired.groupby(['experiment','protocol','stratum']).agg(delta_RMSE=('delta_RMSE','mean'),delta_MAE=('delta_MAE','mean'),fraction_improving=('delta_RMSE',lambda x:(x<0).mean())).reset_index().to_csv(OUT/'tables/paired_summary.csv',index=False)
    pp=pd.DataFrame(pairrows);pp.to_parquet(OUT/'tables/same_model_pairs.parquet',index=False)
    pd.DataFrame(dispersion).to_csv(OUT/'tables/profile_dispersion.csv',index=False)
    rows=[];profiles=[]
    for scope in ['all','without_Chignahuapan']:
        sub=pp if scope=='all' else pp[~pp.Chignahuapan]
        for (exp,protocol,repeat),g in sub.groupby(['experiment','protocol','repeat']):
            z=g.groupby('profile').agg(mse=('pair_error',lambda x:np.mean(x*x)),mae=('pair_error',lambda x:abs(x).mean()),base_mse=('base_error',lambda x:np.mean(x*x)),base_mae=('base_error',lambda x:abs(x).mean()),n_pairs=('pair_error','size'))
            rows.append(dict(experiment=exp,protocol=protocol,repeat=repeat,scope=scope,n_pairs=len(g),n_profiles=len(z),n_parcels=len(set(g.id_a)|set(g.id_b)),pair_RMSE=np.sqrt(np.mean(g.pair_error**2)),pair_MAE=abs(g.pair_error).mean(),pair_bias=g.pair_error.mean(),difference_correlation=g.observed_difference.corr(g.predicted_difference) if g.predicted_difference.std()>1e-12 else np.nan,equal_profile_RMSE=np.sqrt(z.mse.mean()),equal_profile_MAE=z.mae.mean(),equal_profile_base_RMSE=np.sqrt(z.base_mse.mean()),fraction_profiles_improving=(z.mse<z.base_mse-1e-12).mean()))
            for profile,zz in z.iterrows():profiles.append(dict(experiment=exp,protocol=protocol,repeat=repeat,scope=scope,profile=profile,**zz.to_dict(),delta_RMSE=np.sqrt(zz.mse)-np.sqrt(zz.base_mse)))
    rows=pd.DataFrame(rows);rows.to_csv(OUT/'tables/pair_metrics_repeat.csv',index=False)
    rows.groupby(['experiment','protocol','scope']).mean(numeric_only=True).reset_index().to_csv(OUT/'tables/pair_metrics_summary.csv',index=False)
    pd.DataFrame(profiles).to_csv(OUT/'tables/paired_profile_metrics.csv',index=False)
    co=pd.read_csv(OUT/'tables/coefficients.csv')
    co.groupby(['experiment','protocol','feature']).agg(n_present=('coefficient','size'),mean_coef=('coefficient','mean'),sd_coef=('coefficient','std'),positive_fraction=('coefficient',lambda x:(x>1e-10).mean()),negative_fraction=('coefficient',lambda x:(x< -1e-10).mean()),nonzero_frequency=('nonzero','mean')).reset_index().to_csv(OUT/'tables/coefficient_stability.csv',index=False)
    p.to_parquet(OUT/'tables/errors_with_geography.parquet',index=False)
    support_diagnostics(p,t)
    from . import within_profile_reporting as reporting
    reporting.build()

def support_diagnostics(p,t):
    quality=pd.read_csv(OUT/'audit/temporal_quality_by_parcel.csv');rows=[];sums=[]
    splits,_,_=f.lm.k.j.load_frozen_splits(t)
    for protocol,repeat,fold,tr,va,_ in splits:
        z=p[(p.protocol==protocol)&(p['repeat']==repeat)&(p.fold==fold)].copy()
        for index in ['ndvi','lai']:
            counts=quality[quality['index'].eq(index)].set_index(ID).n_valid_dates
            cut=np.quantile(counts.loc[t.iloc[tr][ID]],.25)
            z['support']=np.where(z[ID].map(counts)<=cut,'low','higher')
            for (exp,band),g in z.groupby(['experiment','support']):sums.append(dict(experiment=exp,protocol=protocol,repeat=repeat,fold=fold,index=index,support=band,n=len(g),sse=np.sum((g.y_pred-g.y_true)**2),sae=np.sum(abs(g.y_pred-g.y_true)),training_count_q25=cut))
    sums=pd.DataFrame(sums);sums.to_csv(OUT/'tables/support_fold_sums.csv',index=False)
    z=sums.groupby(['experiment','protocol','repeat','index','support'])[['n','sse','sae']].sum().reset_index();z['RMSE']=np.sqrt(z.sse/z.n);z['MAE']=z.sae/z.n
    z.to_csv(OUT/'tables/support_repeat.csv',index=False)
    z.groupby(['experiment','protocol','index','support'])[['n','RMSE','MAE']].mean().reset_index().to_csv(OUT/'tables/support_summary.csv',index=False)
