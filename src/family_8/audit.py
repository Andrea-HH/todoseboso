"""Exact residual targets and provenance classes; recover archived specifications."""
import json,ast
import numpy as np
import pandas as pd
from . import research as e
def literals(path,name):
    p=e.source(path);tree=ast.parse(p.read_text(encoding='utf8'))
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets):
            try:return ast.literal_eval(node.value)
            except (ValueError,TypeError):return None
    return None
def build(inventory):
    rows=[]
    def add(family,name,base,base_inputs,trainpred,target,corrector_inputs,algorithm,combination,regularization,validation,risk,novelty,source,category='residual'):
        match=inventory[(inventory.family==family)&(inventory.experiment==name)]
        rows.append(dict(family=family,experiment=name,category=category,base_model=base,base_inputs_json=json.dumps(base_inputs,ensure_ascii=False),base_train_predictions=trainpred,exact_residual_target=target,corrector_inputs_json=json.dumps(corrector_inputs,ensure_ascii=False),corrector_algorithm=algorithm,combination=combination,regularization=regularization,validation_provenance=validation,leakage_or_identifiability_risk=risk,difference_vs_F8=novelty,code_source=source,oof_source=match.source_oof.iloc[0] if len(match) else '',protocols=match.protocols.iloc[0] if len(match) else 'not executed',status='archived evaluated' if len(match) else 'descriptive/suspended'))
    rain=['rain_'+m+'_2025' for m in ['apr','may','jun','jul','aug','sep','oct']]
    strict='65 outer + original4 inner; regenerate/tune base within each inner training and deeper residual crossfit subset; preprocessing per fit'
    jcfg=e.read_config('outputs/modeling/family_1/j_incremental_geographic_edaphological_yield/v1/configuration.json')
    for name,columns in jcfg['specs'].items():
        add('J',name,'direct ElasticNet',columns,'none','y (direct)',[],'none','direct (additive inputs, not residual)','alpha .01,.1,1;rho .1,.5,.9','65 frozen nested direct','direct addition not residual and raw soil scaling can destabilize rare units','J0 is actual K5 reference; J1 slope direct control, different from F8 compact4','src/family_1/j_incremental_yield.py','direct_control')
    oldrisk='Outer validation labels excluded; outer-selected parameters reused within cross-fitting/inner residual targets; not certified as fully nested hyperparameter/selector pipeline'
    for family in ['RS1','RS2','RS3','RS4','RS5','RS6']:
        source=f'scripts/data_uderstanding/tablas_agrocebada/{dict(RS1="207_residual_signal_audit.py",RS2="208_history_signal_decomposition.py",RS3="209_climate_signal_decomposition.py",RS4="210_champion_reconstruction.py",RS5="211_second_residual_audit.py",RS6="212_residual_architecture_optimization.py")[family]}'
        e.source(source)
        for name in inventory.loc[inventory.family.eq(family),'experiment']:
            if family=='RS3':
                add(family,name,'ENET/XGB direct climate subfamily','ClimateCurrent48 or exact named subsets; precipitation-only=10 summaries, not compact3','none','y (direct)',[], 'none','direct prediction','archived climate parameters; subset representations not fully retuned','random50 only',oldrisk,'not an F8 residual; same kernel/model name does not imply same inputs',source,'direct_control');continue
            if family=='RS1':
                block=name.split('_RESIDUAL_')[-1];alg=name.split('_')[0]
                base='ClimateCurrent48 ElasticNet';bx='48 current climate summaries';tp='inner4 crossfit with climate params tuned on outer-train reused';target='y_train - climate_inner_crossfit';cx=block;combine='base + corrector';reg='archived Ridge/ENET/XGB grid, lambda=1';validation='random50; residual tuning predicts globally generated outer-train residuals in inner folds'
            elif family=='RS2':
                base='ClimateCurrent48 ElasticNet';bx='48 current climate summaries';tp='same RS1 climate crossfit and outer parameters';target='y_train - climate_inner_crossfit';cx='historical family, selected TOPk or WITHOUT/ONLY subset named '+name;alg='XGBoost or named linear variant';combine='base + history correction';reg='RS1 history params reused; TOPk ranking on outer residual target';validation='random50; historical decomposition, not new strict nested pipeline'
            elif family=='RS4':
                base='precip10 XGB / Current48 EN / climate TOP20 EN according to prefix';bx='TOP20 ranked separately in subtraining; precipitation10, not compact3';tp='inner4 base crossfit, archived outer climate hyperparameters reused';target='y_train - climate_crossfit' if 'HISTORY' in name and 'DIRECT' not in name else 'y (direct or base control)';cx='Sentinel history16 effective fields; per-fold TOP15 where named' if 'HISTORY' in name else [];alg='XGBoost' if 'HISTORY' in name and 'DIRECT' not in name else 'none (direct/base)';combine='base + history correction' if alg=='XGBoost' else 'direct';reg='archive history params, lambda=1';validation='random50 only; TOP20 refiltered in subtraining, TOP15 chosen on outer residuals'
            elif family=='RS5':
                base='climate TOP20 ElasticNet + historyTOP15 XGB';bx='Current48 selector20 + History16 selector15';tp='crossfit both stages with reranking; climate/history params reused from outer';target='y_train - crossfitted(climate + history)';cx=name.split('RESIDUAL2_')[-1];alg=name.split('_')[0];combine='base + second residual correction';reg='RS1 block params reused; lambda=1';validation='random50 only; second-residual targets precede topographic final stage'
            else:
                base='TOP20 EN; sequential/joint stages depend on architecture';bx='climate TOP20 + historyTOP15 + topo basic14; Planet sensitivity for E';tp='A uses RS5 second residual; B/C/D/E reuse parameters and some selectors/targets generated on wider outer-train';target='A: y - CF(climate+history); B: y-climateCF-topoCF; C: y-climateCF; D: second residual-topoCF; E: second residual';cx=name;alg='XGB/Ridge by stage';combine='A C->H->T; B C->T->H; C jointH,T; D H2; E jointT,Planet';reg='archived Ridge/XGB; extra historical pass capped shallow/strong L2; lambda=1';validation='random50 only; seven fixed architectures, not full strict recursive retuning'
            add(family,name,base,bx,tp,target,cx,alg,combine,reg,validation,oldrisk,'different base/features and honesty: not compact4 + slope Ridge / slope+May CatBoost',source)
    for family,directory in [('K','k_standalone_residual_geographic_edaphological'),('L','l_multiblock_representation'),('M','m_historical_multisensor')]:
        cfg=e.read_config(f'outputs/modeling/family_1/{directory}/v1/configuration.json')
        for name,spec in cfg['specs'].items():
            residual=name.startswith(('K5_','K6_','K7_','K8_')) if family=='K' else spec.get('kind')=='residual'
            bx=rain if family=='K' or (isinstance(spec,dict) and spec.get('base')=='rain') else 'Current48 climate';cx=spec if family=='K' else spec.get('blocks',[])
            add(family,name,'J0 rain7 EN / Current48 EN' if family!='K' else 'J0 rain7 ElasticNet',bx,'deeper individually retuned base crossfit; each heldout excluded from base HP selection' if residual else 'none','y - base_CV_within_corresponding_training' if residual else 'y (direct/standalone)',cx,'ElasticNet corrector; PCA1/2/4 where configured' if residual else 'none','base+eta*g' if residual else 'direct','alpha .001,.01,.1,1;rho .1,.5,.9;eta0,.25,.5,1' if residual else 'archived direct grid',strict if residual else '65 nested direct folds','corrector interacts with base refit mismatch; many reused-label comparisons; support limits remain','K5 is closest slope residual ancestor but rain7 base/EN correction; L/M broader soil/topography/history/multisensor blocks; F8 changes matched core and optional honest CatBoost, not a new residual principle',f'src/family_1/{"k_geographic_edaphological" if family=="K" else "lm_multiblock"}.py','residual' if residual else 'direct_control')
    cx={'F4-S2':[e.CORE[-1]],'F4-S3':['S2_ndvi_promedio_q10'],'F4-S4':['S2_savi_promedio_runup_duration'],'F4-S6':['CLIMATE_dtr_mean_std'],'F4-A':['slope_degrees','rain_total','slope*rain_total'],'F4-B':[e.CORE[-1],'rain_total','NDVI*rain_total'],'F4-C':[e.CORE[-1],'base_expected_y','NDVI*expected_y'],'F4-D':['slope_degrees','soil_map_share_mentions_group_VR','slope*soil'],'F4-G1':['slope_degrees spline3knots degree2']}
    for name in inventory.loc[inventory.family.eq('F4'),'experiment']:
        res=name in cx
        add('F4',name,'rain7 ElasticNet',rain,'verified read-only L/K full and inner base contexts' if res else 'none','y-base honest CF' if res else 'y',cx.get(name,rain+([e.CORE[-1]] if name=='F4-S1' else ['DTRstd'])),'ElasticNet' if res else 'none','base+eta*g' if res else 'direct','EN12 grid and eta0,.25,.5,1; spline fixed3knots; soil support gate',strict,'1473-feature prior screening and reused138 labels; expected_y uses CF train vs refitted validation inputs','F4-A/G1 closely precede slope correction; F4-S2 already May residual but on rain7 base; no compact4 slope+May CatBoost tested here','src/family_4/conditional_response.py','residual' if res else 'direct_control')
    for name in inventory.loc[inventory.family.eq('F4-E'),'experiment']:
        add('F4-E',name,'direct rain7 + MayNDVI','rain7, MayNDVI; LAI rise/relief named','none','y (direct)',[], 'none','direct','EN12 nested','65 frozen nested direct','within-profile descriptive partial associations are not corrector targets','direct contrasts, no residual correction','src/family_4/within_profile_complementarity.py','direct_control')
    for name in ['B0','B1','B2','B3']:
        add('B',name,'ElasticNet group objective','rain7+MayNDVI; B2/3 add LAI rise','none; jointly fitted global/centered target objective','y plus within-profile centered y via augmented loss, not OOF residual',[],'none','single fitted predictor','local loss weight0,.1,.3,1; ENalpha .001,.01,.1,1 and rho .1,.5,.9; constrained absolute inner error','65 frozen; selection local pair metric subject to global inner RMSE/MAE<=anchor+.01','lambda0 can still select different HP and damage territory; centered labels full TRAIN not valid unseen targets','F8 keeps primary absolute objective and base fixed algorithm; cannot simply repeat B objective under another name','src/family_4/stage_b_learning.py','transformed_objective')
    for name in inventory.loc[inventory.family.eq('C'),'experiment']:
        hierarchy=name in ['C-H0M','C-H1']
        add('C',name,'GaussianGLS/Ridge' if hierarchy else 'ElasticNet',rain+[e.CORE[-1]] if hierarchy else ('compact3+May' if name=='C-T3' else 'rain7/compact3+May/DTR by spec'),'joint fit; profile BLUP uses training residuals' if name=='C-H1' else 'none','joint y under GLS whitening; BLUP from training y - fixed level, not OOF corrector targets' if name=='C-H1' else 'y', ['training profile random intercept'] if name=='C-H1' else [],'Gaussian random intercept' if name=='C-H1' else 'none','fixed prediction+profile u; unseen u=0' if name=='C-H1' else 'direct','ratio0,.1,.3,1,3; GaussianRidge alpha=n*alpha' if name=='C-H1' else 'Gaussian Ridge alpha=n*alpha, ratio0' if name=='C-H0M' else 'EN12 original', '65 nested; H1 matched ratio0 control','new profile has no learned intercept; same-profile differences cancel u; not parcel causal effect','repeat hierarchy / group-mean correction is redundant; compact4 C-T3 is exact proposed R0 archive','src/family_4/stage_c_models.py','hierarchical' if hierarchy else 'direct_control')
    add('F5-S1','F5-S1-C','Ridge deterministic linear mean',e.CORE,'IN-SAMPLE fitted trend, intentionally a GP mean model','y - Ridge_train.predict(X_train)',e.CORE,'grouped Matern3/2 GP','trend+GP residual mean','linear alpha .001,.01,.1,1 inner-selected; original bounded LML kernel','65 outer; whole mean+GP selected within inner4','not OOF residual targets; plug-in mean uncertainty omitted; legitimate evaluated mean formulation, not F8 crossfit residual','neither DotProduct nor cross-fitted F8; repeating compact4 Ridge+GP is redundant','src/family_5/gpr_s1/models.py','in_sample_mean_GP')
    for family in ['F5-S1','F6','F6-E','F7']:
        for name in inventory.loc[inventory.family.eq(family),'experiment']:
            if name=='F5-S1-C':continue
            add(family,name,'direct or recovered reference','declared archived representation (see source configuration)','none','y (direct)',[],'none','direct','frozen original grids','65 except Champion random50','high training usage/correlated direct errors do not establish residual utility','direct compact4/extensions controls; do not fit averaged existing predictions as correction',f'src/family_{family[1]}/'+('gpr_s1/models.py' if family=='F5-S1' else 'expansion/execution.py' if family in ['F6-E','F7'] else 'execution.py'),'direct_or_recovered_control')
    add('L','L8','full Champion','C->H->T','not available as fully recursive honest contexts','global Champion OOF residuals: descriptive only',[], 'none','not fitted','none','suspended/descriptive','cannot use global archived residual as new supervised target','do not resurrect L8 without new architecture authorization','src/family_1/l_representation.py','suspended')
    add('F4','F4-S7','K5 slope residual','rain7+existing slope correction','whole K5 nested contexts not verified for requested second residual','not constructed',[], 'none','not fitted','none','suspended','would need genuine complete-base contexts','not a ready F8 target cache','src/family_4/conditional_response.py','suspended')
    out=pd.DataFrame(rows)
    out['target_transform_convention']=np.where(out.category.eq('transformed_objective'),'training-only centered targets / augmented objective',np.where(out.category.eq('hierarchical'),'training-only GLS whitening; H1 conditional random intercept, H0M ratio0',np.where(out.family.eq('F5-S1')&out.experiment.str.startswith('F5'),'training-only GP target normalization; S1-C first subtracts in-sample trend','native y or native cross-fitted residual; input scaling/PCA does not itself imply target transformation')))
    absolute=pd.read_csv(e.OUT/'tables/archived_metrics_summary_recomputed.csv');local=pd.read_csv(e.OUT/'tables/archived_intraprofile_summary_recomputed.csv')
    out['absolute_metrics_by_protocol_json']=[json.dumps(absolute[(absolute.family==r.family)&(absolute.experiment==r.experiment)].drop(columns=['family','experiment']).to_dict('records')) for r in out.itertuples()]
    out['intraprofile_metrics_by_protocol_json']=[json.dumps(local[(local.family==r.family)&(local.experiment==r.experiment)].drop(columns=['family','experiment','repeat']).to_dict('records')) for r in out.itertuples()]
    e.save(out,'residual_architecture_audit.csv')
    # Exact grids and selectors remain visible, not vague algorithm names.
    for name,path in [('K','outputs/modeling/family_1/k_standalone_residual_geographic_edaphological/v1/configuration.json'),('L','outputs/modeling/family_1/l_multiblock_representation/v1/configuration.json'),('M','outputs/modeling/family_1/m_historical_multisensor/v1/configuration.json'),('B','outputs/research/family_4/territorial_intraprofile_program/v1/stage_b/frozen_design.json')]:
        if (e.ROOT/path).exists():shutil_copy(e.source(path),e.OUT/'audit'/f'archived_{name}_configuration.json')
    original=e.source('outputs/research/family_4/territorial_intraprofile_program/v1/stage_d/tables/model_inventory.csv');shutil_copy(original,e.OUT/'audit/earlier_full_project_model_inventory.csv')
    # Historical provenance verifies disjointness where logs are actually present.
    checks=[]
    for directory,file in [('k_standalone_residual_geographic_edaphological','16_crossfit_provenance.csv'),('l_multiblock_representation','14_crossfit_provenance.csv'),('m_historical_multisensor','14_crossfit_provenance.csv')]:
        path=f'outputs/modeling/family_1/{directory}/v1/tables/{file}';z=pd.read_csv(e.source(path))
        for row in z.to_dict('records'):
            train=set(json.loads(row['fit_ids']));held=set(json.loads(row['heldout_ids']));assert not train&held
            value=row.get('inner_folds')
            if not isinstance(value,str):value=row.get('tuning_folds','[]')
            tuning=json.loads(value)
            assert tuning,'Missing deeper tuning provenance'
            for a,b in tuning:assert not set(a)&set(b) and set(a)|set(b)<=train and not (set(a)|set(b))&held
        checks.append(dict(family=directory,n_records=len(z),disjoint_fit_heldout=True,deeper_tuning_excludes_heldout=True,source=path,limit='verifies membership provenance; source/manifest also needed for algorithm/grid fidelity'))
    e.save(pd.DataFrame(checks),'historical_nested_provenance_checks.csv')
    registries=[]
    for name in ['RS3_climate_source_actual_hyperparameters.csv','RS4_actual_selected_hyperparameters.csv','RS5_residual_source_actual_hyperparameters.csv','RS6_actual_selected_hyperparameters.csv']:
        path='outputs/modeling/family_6/bagging/v1/audit/'+name
        p=e.source(path);shutil_copy(p,e.OUT/'audit'/name)
        z=pd.read_csv(p)
        registries.append(dict(file=name,n_records=len(z),columns_json=json.dumps(z.columns.tolist()),use='actual per-fold parameters/selectors; static architecture row references this registry'))
    e.save(pd.DataFrame(registries),'exact_archived_parameter_registry_index.csv')
    blocks=literals('scripts/data_uderstanding/tablas_agrocebada/207_residual_signal_audit.py','BLOCK_FILES')
    import pyarrow.parquet as pq
    bx=[]
    for name,file in blocks.items():
        path='data/processed/family_1/features/'+file;p=e.source(path)
        columns=[c for c in pq.read_schema(p).names if c not in [e.ID,'__index_level_0__']]
        bx.append(dict(block=name,raw_feature_columns_json=json.dumps(columns),n_raw_columns=len(columns),source=path,role='raw block schema, not claim that constants survive each fitted transform'))
    e.save(pd.DataFrame(bx),'exact_prior_predictor_blocks.csv')
    for family,path in [('RS2','outputs/modeling/residual_signal_audit/stage2_history/dictionary/history_feature_dictionary.csv'),('RS3','outputs/modeling/residual_signal_audit/stage3_climate/dictionary/climate_feature_dictionary.csv'),('F5','outputs/research/family_5/gpr_evidence_design/v1/tables/candidate_variable_inventory.csv')]:shutil_copy(e.source(path),e.OUT/'audit'/f'{family}_variable_dictionary.csv')
    usage=pd.read_csv(e.source('outputs/modeling/family_6/expansion/v1/tables/feature_usage_stability.csv'))
    e.save(usage[(usage.experiment=='F6-E3')&usage.feature.eq('CLIMATE_dtr_mean_std')],'verified_F6_DTR_usage_without_incremental_gain.csv')
    for label,path in [('F7_initial','outputs/modeling/family_7/boosting/v1/report/decision.json'),('F7_expansion','outputs/modeling/family_7/expansion/v1/report/decision.json'),('F5_S1','outputs/modeling/family_5/gpr_s1/v1/report/decision.json')]:shutil_copy(e.source(path),e.OUT/'audit'/f'verified_{label}_decision.json')
def shutil_copy(a,b):
    import shutil
    shutil.copyfile(a,b)
