"""F5 design only: existing evidence, feature provenance and target-free redundancy."""
from pathlib import Path
import json,itertools,hashlib
import numpy as np
import pandas as pd
from src.family_4 import stage_c_models as c
from src.family_4 import stage_d_evidence as d

ROOT=c.ROOT;OUT=ROOT/'outputs/research/family_5/gpr_evidence_design/v1';ID=c.ID
HISTORY=['HIST_S2_ndvi_promedio_mean','HIST_S2_ndvi_promedio_std']
SLOPE='TOPO_BASIC_slope_mean'
CORE=c.COMPACT+[c.NDVI]
PRIMARY_SOURCES=[
 ('GaussianProcessRegressor, installed-version documentation','https://scikit-learn.org/1.7/modules/generated/sklearn.gaussian_process.GaussianProcessRegressor.html'),
 ('Gaussian processes guide','https://scikit-learn.org/1.7/modules/gaussian_process.html'),
 ('Matérn kernel','https://scikit-learn.org/1.7/modules/generated/sklearn.gaussian_process.kernels.Matern.html'),
 ('WhiteKernel','https://scikit-learn.org/1.7/modules/generated/sklearn.gaussian_process.kernels.WhiteKernel.html'),
 ('GPML chapter2: regression and means','https://gaussianprocess.org/gpml/chapters/RW2.pdf'),
 ('GPML chapter4: covariance functions','https://gaussianprocess.org/gpml/chapters/RW4.pdf'),
 ('GPML chapter5: marginal likelihood and model selection','https://gaussianprocess.org/gpml/chapters/RW5.pdf'),
 ('Duvenaud et al., Additive Gaussian Processes','https://arxiv.org/abs/1112.4394')]

def write_table(frame,name):frame.to_csv(OUT/'tables'/name,index=False)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def protect():
    if (OUT/'manifest.json').exists():raise FileExistsError('Completed F5 design immutable; use new version')
    for p in [OUT]+[OUT/x for x in ['audit','tables','report','figures']]:p.mkdir(parents=True,exist_ok=True)
    old=json.loads((d.OUT/'manifest.json').read_text());paths=set(ROOT/p for p in old['artifacts']);paths.add(d.OUT/'manifest.json')
    assert all(sha(ROOT/p)==digest for p,digest in old['artifacts'].items())
    for r in pd.read_csv(d.OUT/'audit/protected_inputs.csv').itertuples():
        path=ROOT/r.path;assert sha(path)==r.sha256;paths.add(path)
    paths.update(ROOT/r.path for r in pd.read_csv(d.OUT/'audit/read_only_input_provenance.csv').itertuples())
    for directory in [ROOT/'outputs/modeling/residual_signal_audit',ROOT/'data/processed/family_1/features',ROOT/'data/processed/family_1/g_temperature_signal/v1',ROOT/'data/processed/family_1/m_historical_multisensor/v1',ROOT/'data/processed/family_1/timeseries',ROOT/'data/processed/family_1/environment']:
        for p in directory.rglob('*'):
            if p.is_file() and p.suffix in ['.csv','.parquet','.json','.md']:paths.add(p)
    baseline=pd.DataFrame([dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(paths)])
    dest=OUT/'audit/protected_inputs.csv'
    if dest.exists():pd.testing.assert_frame_equal(pd.read_csv(dest),baseline)
    else:baseline.to_csv(dest,index=False)
    pd.DataFrame([dict(title=a,url=b,accessed='2026-10-12',type='primary documentation/research') for a,b in PRIMARY_SOURCES]).to_csv(OUT/'audit/technical_primary_sources.csv',index=False)

def data():
    a,t=c.load();full,_=c.b.e.f.load();extra=[x for x in full if x not in t];t=t.merge(full[[ID]+extra],on=ID,validate='one_to_one')
    f=pd.read_parquet(ROOT/'data/processed/family_1/features/family1_features_all.parquet');missing=[x for x in f if x not in t];t=t.merge(f[[ID]+missing],on=ID,validate='one_to_one')
    g=pd.read_parquet(ROOT/'data/processed/family_1/g_temperature_signal/v1/climate_candidates_197.parquet');missing=[x for x in g if x not in t];t=t.merge(g[[ID]+missing],on=ID,validate='one_to_one')
    assert len(t)==138 and t[ID].is_unique and set(HISTORY+CORE+[SLOPE])<=set(t)
    return a,t,f

def selection_audit():
    path=ROOT/'outputs/modeling/residual_signal_audit/stage4_champion_reconstruction/models/selected_hyperparameters.csv';z=pd.read_csv(path);rows=[];sets=[]
    for baseline,g in z.groupby('baseline'):
        values=g.history15_features.map(json.loads)
        for row in g.itertuples():sets.append(dict(baseline=baseline,repeat=row.repeat,fold=row.fold,history15_features=row.history15_features,climate_features=row.climate_features))
        universe=sorted(set(x for cols in values for x in cols))
        for column in universe:rows.append(dict(baseline=baseline,feature=column,n_selected=sum(column in x for x in values),n_outer=len(g),frequency=sum(column in x for x in values)/len(g),n_unique_sets=len(set(tuple(sorted(x)) for x in values)),selection='supervised abs Spearman with outertrain innerOOF climate residual; varies byfold',source=path.relative_to(ROOT).as_posix()))
    write_table(pd.DataFrame(rows),'history_top15_frequencies.csv');write_table(pd.DataFrame(sets),'history_top15_exact_fold_sets.csv')
    original=pd.read_csv(ROOT/'outputs/modeling/residual_signal_audit/stage3_climate/models/climate_feature_stability.csv');original.to_csv(OUT/'tables/climate_selection_stability_archived.csv',index=False)

def historical_metrics():
    # Preserve published aggregation and independently summarize existing OOF, without refitting.
    rows=[]
    sources=[('RS3','outputs/modeling/residual_signal_audit/stage3_climate/checkpoints/rs3_oof_predictions.parquet','experiment'),('RS4','outputs/modeling/residual_signal_audit/stage4_champion_reconstruction/predictions/oof_predictions.parquet','pipeline'),('RS6','outputs/modeling/residual_signal_audit/stage6_architecture_optimization/predictions/oof_predictions.parquet','architecture')]
    for stage,path,field in sources:
        z=pd.read_parquet(ROOT/path)
        for (exp,repeat),g in z.groupby([field,'repeat']):
            assert len(g)==138 and g[ID].nunique()==138
            rows.append(dict(stage=stage,experiment=exp,protocol='random',repeat=repeat,**d.metrics(g),source=path,aggregation='138 complete OOF per repetition; mean repetitions separately'))
    z=pd.DataFrame(rows);write_table(z,'historical_metrics_repeat_recomputed.csv');write_table(z.groupby(['stage','experiment','protocol','source']).agg(RMSE=('RMSE','mean'),MAE=('MAE','mean'),bias=('bias','mean'),n=('n','first'),n_repeats=('repeat','size')).reset_index(),'historical_metrics_oof_recomputed.csv')
    tablepaths=[('RS2','outputs/modeling/residual_signal_audit/stage2_history/compact_models/topk_history_metrics.csv'),('RS3','outputs/modeling/residual_signal_audit/stage3_climate/subfamilies/climate_subfamily_only_metrics.csv'),('RS3','outputs/modeling/residual_signal_audit/stage3_climate/subfamilies/climate_subfamily_ablation.csv'),('RS3','outputs/modeling/residual_signal_audit/stage3_climate/subfamilies/climate_temporal_window_metrics.csv'),('RS4','outputs/modeling/residual_signal_audit/stage4_champion_reconstruction/metrics/pipeline_metrics.csv'),('RS5','outputs/modeling/residual_signal_audit/stage5_second_residual_audit/winners/winner_subfamily_metrics.csv'),('RS5','outputs/modeling/residual_signal_audit/stage5_second_residual_audit/winners/winner_compact_metrics.csv')]
    for j,(stage,path) in enumerate(tablepaths):pd.read_csv(ROOT/path).to_csv(OUT/'tables'/f'archived_{j:02d}_{stage}.csv',index=False)
    names=[dict(requested_id='PRECIPITATION_ONLY_XGB',found_exact=False,resolved='ONLY_PRECIPITATION_XGB',reason='Exact requested spelling not found in repository CSV/MD/PY; RS3 source exactID retained, no assumed alias equality'),dict(requested_id='PRECIPITATION_XGB',found_exact=True,resolved='PRECIPITATION_XGB_BASE; PRECIPITATION_XGB_HISTORY15/24',reason='RS4 baseline identifier;10 climate precipitation summaries, not seven monthly raw values')]
    write_table(pd.DataFrame(names),'requested_identifier_resolution.csv')
    for directory in [ROOT/'outputs/modeling/family_1/rainfall_yield',ROOT/'outputs/modeling/family_1/g_temperature_signal',ROOT/'outputs/modeling/family_1/h_joint_climate_signal']:
        for path in directory.rglob('*model_comparison.csv'):
            name=path.relative_to(ROOT/'outputs/modeling').as_posix().replace('/','__');pd.read_csv(path).to_csv(OUT/'tables'/name,index=False)
    # Reuse D consolidated evidence rather than duplicate its diagnostic pipelines.
    for name in ['metrics_summary.csv','spatial_block_gains.csv','spatial_block_omission.csv','gain_concentration.csv','equal_profile_pair_metrics_summary.csv','final_evidence_matrix.csv']:
        pd.read_csv(d.OUT/'tables'/name).to_csv(OUT/'tables'/('D_'+name),index=False)

def semantics(t,f):
    source=pd.read_parquet(ROOT/'data/processed/family_1/timeseries/sentinel_timeseries.parquet')
    may=source[(source.year==2025)&(source.month==5)].groupby(ID).ndvi_promedio.mean()
    np.testing.assert_allclose(t[c.NDVI],t[ID].map(may),atol=1e-12)
    pre=source[source.year.between(2022,2024)&source.month.between(4,10)].groupby([ID,'year','month']).ndvi_promedio.mean().groupby([ID,'month']).mean()
    recovered=pre.groupby(ID).agg(['mean','std']).reindex(f[ID]);np.testing.assert_allclose(f[HISTORY[0]],recovered['mean'],atol=1e-12);np.testing.assert_allclose(f[HISTORY[1]],recovered['std'],atol=1e-12)
    monthly=pd.read_parquet(ROOT/'data/processed/family_1/environment/climate_monthly_timeseries.parquet');monthly=monthly[monthly.date_month.between('2025-04-01','2025-10-31')];std=monthly.groupby(ID).dtr_mean.std(ddof=1)
    np.testing.assert_allclose(t[c.DTR],t[ID].map(std),atol=1e-12)
    np.testing.assert_allclose(t.slope_degrees,t[SLOPE],atol=1e-12)
    (OUT/'audit/semantic_checks.json').write_text(json.dumps(dict(n_train=138,n_prediction=59,n_profiles_all=53,n_profiles_train=43,ndvi_may_exact=True,ndvi_source='arithmetic mean of valid ndvi_promedio parcel observations in May2025, Sentinel',history_mean_exact=True,history_std_exact=True,history_std_definition='sampleSD across7 calendar-month historical means; NOT interannualSD',DTR_exact=True,DTR_definition='sampleSD of7monthly Tmax−Tmin means',slope_alias_exact=True,slope_aliases=['slope_degrees',SLOPE],no_y_used_for_feature_verification=True),indent=2),encoding='utf8')

def candidate_inventory(t):
    dictionary=pd.read_csv(ROOT/'data/processed/family_1/features/family1_feature_dictionary.csv').set_index('feature_name')
    cols=c.RAIN+c.COMPACT+[x for x in t if x.startswith('CLIMATE_precip_')]+[c.DTR,'CLIMATE_tmin_mean_mean','CLIMATE_tmax_mean_mean']+[x for x in t if x.startswith('tmin_') and x.endswith('_2025')]+[x for x in t if x.startswith('tmax_') and x.endswith('_2025')]
    cols += [c.NDVI,c.b.e.f.Q10,c.b.e.RISE,c.b.e.LAI,c.b.e.FAPAR,c.b.e.EVI,c.b.e.f.SAVI]+[x for x in t if x.startswith('HIST_S2_')]+[x for x in t if x.startswith('TOPO_BASIC_')]+[c.b.e.RELIEF,'TOPO_ADV_twi_mean','TOPO_ADV_tpi_3x3_mean','TOPO_ADV_plan_curvature_mean']
    # All columns come from previous matrices. No screening or features constructed here.
    cols=list(dict.fromkeys(cols));rows=[]
    freq=pd.read_csv(OUT/'tables/history_top15_frequencies.csv');histred=pd.read_csv(ROOT/'outputs/modeling/residual_signal_audit/stage2_history/associations/history_climate_redundancy.csv').set_index('feature');cond=pd.read_csv(ROOT/'outputs/modeling/residual_signal_audit/stage2_history/associations/history_conditional_associations.csv').set_index('feature')
    for col in cols:
        if col not in t:continue
        meta=dictionary.loc[col].to_dict() if col in dictionary.index else {}
        role='Reserve: no stable incremental benefit established'
        experiments='See source_dictionary / D evidence matrix';association='descriptive association does not establish causal or incremental signal';increment='not established for this exact individual column';risk='correlated proxies; retrospective selection';artifact='documentation/territorial_program_stage_d.md';stability='see archived protocols; no GPR stability measured'
        if col in c.RAIN or col.startswith('CLIMATE_precip_') or col in c.COMPACT:
            experiments='RS3/RS4, rainfallE1-E8, H1, C-T0/T1/T3/T4';artifact='outputs/modeling/residual_signal_audit/stage3_climate/subfamilies/climate_subfamily_only_metrics.csv; outputs/research/family_4/territorial_intraprofile_program/v1/stage_c/tables/metrics_summary.csv';association='strong block prediction; total alone weaker than temporal vector';increment='C-T3 compact + MayNDVI municipal benefit; compact rainfall alone not validated as same configuration';risk='mean=total/7; early+mid+late=total; std/cv and fractions overlap';role='Primary rain compact3; raw7 matched representation control;10RS summaries inventory only';stability='compact benefit municipal; spatial dependsblock3; no universal representation winner'
        if col==c.NDVI:
            role='Primary parcel signal, preserve exact May2025 variable';experiments='screening1473,F4-S1,F4-E1/E2,C-T0/T3';association='within-profile association persists with equalprofile/nonChignahuapan diagnostics';increment='S1 additive improves random/profile/municipal relative rain; local discrimination, not sole predictor superiority';artifact='documentation/family4_e_decision_summary.md; outputs/modeling/family_4/conditional_yield_response/v1/tables/oof_predictions.parquet';risk='date not necessarily same phenological stage; correlated indices';stability='138labels,65folds; exploratory discovery on reusedY'
        elif col==c.DTR:
            role='Conditional thermal sensitivity F5-02; not assumed useful when NDVI included';experiments='screening,F4-S5,C-T1/T2/T4,D';association='regional signature, constant within exactprofile';increment='S5 spatial benefit, but T2/T4 do not combine NDVI benefit consistently';artifact='outputs/research/family_4/territorial_intraprofile_program/v1/stage_d/tables/spatial_block_gains.csv';risk='correlated seasonal/rain/state structure; not meanTmax';stability='spatial improvement primarilyblock3; weak random/municipal'
        elif 'tmin' in col or 'tmax' in col:
            role='Territorial descriptive reserve; do not add7Tmin to initialkernel';experiments='G1/G2,H5/H6,H_EXT_RAIN_TMAX_PCR';association='structured climate geography; does not split identical rainfall profiles';increment='Tmin doesnot improve general H; Tmax marginal random RMSE with MAE/regional costs';artifact='outputs/modeling/family_1/h_joint_climate_signal/v1/tables/40_model_comparison.csv';risk='collinearity, sharedgeographicgrid, morekernel axes';stability='H regional deterioration; PCR not general remedy'
        elif col.startswith('HIST_S2_'):
            role='F5-03 fixed NDVImean/std hypothesis' if col in HISTORY else 'Archive broad history16 pool; exclude coverage constants; no globalTop15 freeze'
            experiments='RS2,RS4 History15/24,RS6';artifact='outputs/modeling/residual_signal_audit/stage4_champion_reconstruction/models/selected_hyperparameters.csv; src/family_1/feature_pipeline.py'
            association=f"conditional Spearman={cond.loc[col,'spearman_conditional']:.8g}; climate reconstruction R2={histred.loc[col,'R2_History_from_Climate_OOF']:.8g}" if col in cond.index and col in histred.index else 'not archived for individual column'
            increment='Sentinel historical16 block improves residualXGB; this exact2column subset not proven';risk='indices correlated; std is seasonal of historical meanmonths, not year-to-year variability';stability='; '.join(f"{r.baseline}:{r.n_selected}/{r.n_outer} selected" for r in freq[freq.feature.eq(col)].itertuples()) or 'constantcoverage; no useful variation'
        elif col.startswith('TOPO'):
            role='F5-04 fixed slope_mean hypothesis' if col==SLOPE else 'Reserve: redundancy/scale; do not import25dims into ARD'
            experiments='RS1,RS5/RS6,K5,F4-E3,territorialA';artifact='outputs/modeling/residual_signal_audit/stage5_second_residual_audit/winners/winner_subfamily_metrics.csv; documentation/k_decision_summary.md';association='blockterrain/slope has conditional modest signal; individual importance not ablation';increment='slope14block survives RS5; mean-only exact subset hypothesis; TWI/relief no incremental stable evidence';risk='quantiles correlated; DEM120m; derivedhydrology not measuredwater';stability='RS5 slope block8/10 repeats; geography K costs; variablewise effect unproven'
        elif col in [c.b.e.RISE,c.b.e.LAI,c.b.e.FAPAR,c.b.e.EVI,c.b.e.f.Q10,c.b.e.f.SAVI]:
            role='Optional later local dynamic control; not initial replacement for MayNDVI';experiments='screening,F4-S3/S4,F4-E2/E4';artifact='documentation/family4_e_decision_summary.md';association='some localpartial associations; spectral redundancy';increment='E2 LAIrise modest local improvement; LAIq10 replacement harmsgeography';risk='LAI from SAVI; summaries AprOct not Mayavailable; rise not observedplanting';stability='E2 smalllocal signal; E4 municipality/spatial poor'
        window=meta.get('window','Apr-Oct2025' if not col.startswith('TOPO') else 'STATIC')
        if col==c.NDVI:window='2025-05-01/2025-05-31'
        if col.startswith('HIST_'):window='Apr-Oct2022-2024 pooled by calendar month'
        source=meta.get('source','existingG/C/M derivedmatrix')
        transform=meta.get('description',meta.get('statistic','see semantic_checks and existing feature source'))
        if col in c.RAIN:source='Existing precipitation parcel monthly matrix; CHIRPS';window=col.replace('rain_','').replace('_2025','2025 calendar month');transform='supplied parcel-weighted precipitation mean for this calendar month, mm; existing extraction'
        if col in c.COMPACT:
            source='Existing StageC summaries of seven monthly rain columns';transform={'compact_precip_total':'sum(PApr..POct), mm','compact_early_fraction':'(PApr+PMay+PJun)/(sum7P+1e-6mm)','compact_concentration_hhi':'sum[(Pm/(sum7P+1e-6mm))^2]'}[col]
        if col==c.NDVI:source='Sentinel-2 ndvi_promedio supplied parcel observations';transform='arithmetic mean of finite observations in calendar May2025; not temporal q10 or AprOct mean'
        if col.startswith('HIST_S2_'):
            source='Sentinel-2 supplied *_promedio, 2022-2024';transform='Within-year/month observation mean, then average years for each calendar month; '+('sampleSD across7 historical monthly means ddof1, NOT interannualSD' if col.endswith('_std') else 'average of7 historical monthly means' if col.endswith('_mean') else 'count of valid historical calendar months; all7, constant')
        if col==c.DTR:source='CHIRTS-ERA5 canonical Tmin/Tmax parcel monthly means, verified G audit';transform='sampleSD across7 Apr-Oct2025 monthly means of Tmax-Tmin; ddof1; degreesC'
        if col in ['CLIMATE_tmin_mean_mean','CLIMATE_tmax_mean_mean']:source='CHIRTS-ERA5 canonical parcel monthly temperature, verified G audit'
        if col.startswith(('tmin_','tmax_')) and col.endswith('_2025'):source='CHIRTS-ERA5 canonical temperature parcel monthly matrix';window='2025 calendar month '+col.split('_')[1];transform='supplied monthly parcel-weighted temperature mean; degreesC'
        rows.append(dict(column=col,source=source,period=window,information_family='history' if col.startswith('HIST') else 'topography' if col.startswith('TOPO') else 'vegetation2025' if col.startswith('S2') else 'climate2025',transformation=transform,experiments=experiments,association_or_prediction=association,incremental_evidence=increment,stability=stability,redundancy_risk=risk,recommended_F5_role=role,artifact=artifact,n_labels_valid=int(t[col].notna().sum()),n_unique=int(t[col].nunique())))
    write_table(pd.DataFrame(rows),'candidate_variable_inventory.csv')
    return cols

def redundancy(t,cols):
    z=t[cols];corr=z.corr();corr.to_csv(OUT/'tables/predictor_pearson_TRAIN138.csv')
    support=t.groupby('climate_profile')[ID].transform('size')>=2
    local=z.loc[support]-t.loc[support].groupby('climate_profile')[cols].transform('mean');local.corr().to_csv(OUT/'tables/predictor_within_profile_pearson.csv')
    rows=[]
    for a,b in itertools.combinations(cols,2):
        rr=corr.loc[a,b]
        if np.isfinite(rr) and abs(rr)>=.9:
            valid=t[[a,b]].dropna();affine=np.linalg.matrix_rank(np.column_stack([np.ones(len(valid)),valid[a],valid[b]]))<3
            rows.append(dict(a=a,b=b,pearson=rr,n=len(valid),exact_affine_rank_deficiency=affine,interpretation='TRAIN covariate diagnostic; not proof no incremental signal; noY ranking'))
    write_table(pd.DataFrame(rows),'high_redundancy_pairs.csv')
    geometry=[]
    for name,columns in [('rain7',c.RAIN),('compact3',c.COMPACT),('core4',CORE),('core_history6',CORE+HISTORY),('core_slope5',CORE+[SLOPE]),('history16',[x for x in cols if x.startswith('HIST_S2') and not x.endswith('_months')])]:
        x=t[columns].to_numpy(float);x=np.where(np.isfinite(x),x,np.nanmedian(x,axis=0));sd=x.std(axis=0);x=(x-x.mean(axis=0))/np.maximum(sd,1e-12);s=np.linalg.svd(x,compute_uv=False);geometry.append(dict(representation=name,n=138,n_variables=len(columns),rank=np.linalg.matrix_rank(x),condition_number=s.max()/s.min() if s.min()>1e-12 else np.inf,n_distinct_vectors=np.unique(x,axis=0).shape[0],note='descriptive TRAIN geometry; no model fitted; no new predictive PCA'))
    write_table(pd.DataFrame(geometry),'representation_geometry.csv')

def matrix():
    rows=[
      ('F5-00-C',1,c.COMPACT,'Rain compact3','Matérn3/2 isotropic + White',3,'Constant trainingmean','Does nonlinear compact rain improve simple climate baseline?','Rain3 EN matchedcontrol; rainfallE controls contextual','65 originalfolds','Low,3kernel parameters','Diagnostic rain-only ablation, not standalone universal promotion'),
      ('F5-00-M',2,c.RAIN,'Rain monthly7','Matérn3/2 isotropic + White',3,'Constant trainingmean','Check temporal information lost by compact3','F5-00-C and J0 monthly EN','65 originalfolds','Low; samekernel parametercount,7inputs','Representation decision insideinnerCV only if used downstream; never by outerwinner'),
      ('F5-01',1,CORE,'Rain compact3 + MayNDVI','Matérn3/2 groupedARD: rain3 tied, NDVI separate + White',4,'Constant trainingmean','Smooth nonlinear rain/vegetation response beyond C-T3 EN','C-T3 exactinput EN; F4-S1 broaderreference; Champion randomonly','65 originalfolds','Low-moderate,4kernel parameters','First primaryGPR; predeclared practical gain and territorial/local cost checks'),
      ('F5-02',3,CORE+[c.DTR],'F5-01 + SD_DTR','Matérn3/2 groupedARD: rain/NDVI/DTR + White',5,'Constant trainingmean','Can GP use thermal signal that additiveT4 failed to combine?','F5-01; C-T4 matchedinput EN','65 originalfolds','Moderate,5parameters','Conditional on core viability; benefit must survive omissionblock3; not presumed positive'),
      ('F5-03',4,CORE+HISTORY,'Fixedcore + historyNDVI mean/std','Matérn3/2 groupedARD: rain/NDVI/history2 + White',5,'Constant trainingmean','Compact historical parcel signature, distinct from currentMay','F5-01; matchedEN exactsame6columns; RS4 residualblock contextual','65 originalfolds','Moderate;5parameters,6inputs','History2subset is hypothesis; require incremental/local benefit without regional deterioration'),
      ('F5-04',5,CORE+[SLOPE],'Fixedcore + slope_mean','Matérn3/2 groupedARD: rain/NDVI/slope + White',5,'Constant trainingmean','Smooth conditional slope effect; exactmean-only subset hypothesis','F5-01; matchedEN same5inputs; K5 contextual','65 originalfolds','Moderate;5parameters','No automatic promotion from RS5 slope14 evidence; groupedoutcomes decisive'),
      ('F5-05',6,CORE+HISTORY+[SLOPE],'Fixed agroclimate/history/topography blocks','aA M3/2(A)+aH M3/2(H)+aT M3/2(T)+White; one length perblock',7,'Constant trainingmean','Explicitly additive corrections vs joint compactkernel','JointMatérn same7columns with5parameters; F5-03/F5-04','65 originalfolds','Moderate-high;7parameters; customcolumn kernel reuse future','Only if blockhypotheses survive; isolate architecture with samefeatures/preprocessing'),
      ('F5-06',7,CORE+HISTORY+[SLOPE],'Cross-fitted residual correction','Matérn3/2 groupedARD rain/NDVI/history/slope + White',6,'Fixed externalbase C-T3; residualmean trainonly','Does independent residualGP outperform directGP with sameobservedX?','NestedC-T3 base,eta0control; sameX directGPR; Champion variant SUSPENDED','65 originalfolds forC-T3; no geographicChampion invented','High: rebuilding bases insideinner and subinnerfolds dominates','Do not use globalChampionOOF as trainingtarget; Champion extension blocked until full3layer nestedbase verified')]
    z=pd.DataFrame(rows,columns=['experiment','priority','columns','representation','kernel','n_kernel_hyperparameters','mean','hypothesis','baseline','validation','relative_cost','continuation_or_discard'])
    z['columns']=z['columns'].map(json.dumps);z['status']='proposed_for_review_NOT_EXECUTED';z['new_PRED_predictions']=False
    write_table(z,'experimental_matrix.csv')
    design=dict(status='proposal_only_not_approved_for_execution',first_recommended='F5-01',primary_kernel='Matern nu1.5 grouped rainfall/NDVI scales',matched_prerequisite='F5-00-C rainfall-only ablation',no_model_training=True,no_optimizer_called=True,no_final_prediction=True,no_new_labels=True,proposed_matrix=z.to_dict('records'),primary_representation=CORE,history_pair=HISTORY,topography_column=SLOPE,nu_fixed=True,optional_same_core_sensitivities=['RBF groupedARD4parameters','Matern nu1.5 pervariableARD6parameters'],main_objective='municipal generalization vs exactinput C-T3, with random/profile/spatial/local cost diagnostics',proposed_margin_t_ha=.01,margin_status='review proposal, practicalthreshold not established from economics',optimizer_future=dict(method='bounded L-BFGS-B LML within corresponding train',n_restarts_optimizer=2,seed=2026,amplitude_bounds=[.01,100],length_bounds=[.2,20],noise_variance_bounds=[.001,2],initial_amplitude=1,initial_length=1,initial_noise_variance=.1,jitter=1e-8),all_transformations='training median, mean/std, NDVIfloor.05; divide blockvectors by sqrt(numberfeatures), no fit on outervalidation orPRED',coordinate_or_identity_predictors=[],champion_residual_status='suspended pending full3layer nestedbase reconstruction, L8 precedent; cachedresidual2 insufficient',folds_source='outputs/research/family_4/territorial_intraprofile_program/v1/stage_c/splits/outer_and_inner_splits.csv')
    (OUT/'proposed_design.json').write_text(json.dumps(design,indent=2),encoding='utf8');return z

def run():
    protect();a,t,f=data();selection_audit();historical_metrics();semantics(t,f);cols=candidate_inventory(t);redundancy(t,cols);m=matrix()
    from .gpr_design_reporting import build
    build(t,m)
    print('F5 evidence/design only ready; no GPR training, optimization or predictions',flush=True)
