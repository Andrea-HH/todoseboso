"""Read-only synthesis of archived OOF; no estimator construction or predictive fitting."""
import json,itertools
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from . import stage_c_models as c

ROOT=c.ROOT;ID=c.ID;TARGET=c.TARGET
OUT=c.OUT.parent/'stage_d';KEY=[ID,'protocol','repeat','fold']
BASE='F4-S1'
PAIRS=[('FIXED_50_50','CHAMPION'),('C-T3',BASE),('C-T1',BASE),('C-H0M',BASE),('F4-E2',BASE),('C-T3','C-H0M')]

def save(frame,name):
    path=OUT/'tables'/name
    if path.suffix=='.parquet':frame.to_parquet(path,index=False)
    else:frame.to_csv(path,index=False)

def metrics(g):
    error=g.y_pred.to_numpy()-g.y_true.to_numpy()
    return dict(n=len(g),SSE=float(error@error),MSE=float(np.mean(error**2)),RMSE=float(np.sqrt(np.mean(error**2))),MAE=float(np.mean(abs(error))),bias=float(np.mean(error)))

def freeze():
    if (OUT/'manifest.json').exists():raise FileExistsError('Completed D immutable')
    for name in ['audit','tables','figures','report']: (OUT/name).mkdir(parents=True,exist_ok=True)
    paths=set()
    for old in [c.b.a.OUT,c.b.OUT,c.OUT,c.b.e.OUT,c.b.e.f.OUT]:
        m=json.loads((old/'manifest.json').read_text())
        for path,digest in m['artifacts'].items():
            p=ROOT/path;assert c.b.a.sha(p)==digest,path;paths.add(p)
        paths.add(old/'manifest.json')
    # Freeze historical evidence, configurations, scripts and fitted Champion artifacts too.
    for directory in [ROOT/'outputs/modeling/family_1',ROOT/'outputs/modeling/family_2',ROOT/'outputs/modeling/family_3',ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization',ROOT/'outputs/research/family_1/variable_strength_screening/v1',ROOT/'documentation',ROOT/'src',ROOT/'scripts']:
        for p in directory.rglob('*'):
            if not p.is_file() or '__pycache__' in p.parts or 'stage_d' in p.name:continue
            if p.suffix in ['.md','.json','.csv','.parquet','.py'] or 'stage6_architecture_optimization' in p.parts:paths.add(p)
    paths.add(Path(c.b.e.f.lm.k.j.MASTER))
    frozen=pd.DataFrame([dict(path=p.relative_to(ROOT).as_posix(),sha256=c.b.a.sha(p),bytes=p.stat().st_size) for p in sorted(paths)])
    path=OUT/'audit/protected_inputs.csv'
    if path.exists():pd.testing.assert_frame_equal(pd.read_csv(path),frozen)
    else:frozen.to_csv(path,index=False)
    design=dict(stage='D',new_model_training=False,final_training=False,scope='archived OOF evidence only',comparisons=PAIRS,primary_aggregation='complete OOF138 per repeat, then mean repeats',influence='mean losses per parcel across repetitions; descriptive omission only',pairs='same external model within profile; equal profile weighting; no iid inference',block3='descriptive support and existing heldout predictions; no activation rule',case_audit='top10% absolute errors per model/protocol; recurrence and sign descriptive',support='archived C support on total rainfall/DTR/NDVI, not full Champion support',practical_margin_status='prospective proposal must be approved before newY; existing0.01 margin retained for retrospective C interpretation',source_sha={str(p.relative_to(ROOT)):c.b.a.sha(p) for p in [Path(__file__)]})
    (OUT/'frozen_design.json').write_text(json.dumps(design,indent=2),encoding='utf8')

def load():
    d,t=c.load();full,_=c.b.e.f.load()
    extra=[x for x in full if x not in t]
    t=t.merge(full[[ID]+extra],on=ID,validate='one_to_one')
    for name in ['geology_full_composition_197','geology_attributes_197']:
        t=t.merge(pd.read_parquet(c.b.a.PROC/(name+'.parquet')),on=ID,validate='one_to_one')
    splits,_,_=c.b.e.f.lm.k.j.load_frozen_splits(t)
    block={t.iloc[i][ID]:fold for protocol,repeat,fold,tr,va,inner in splits if protocol=='spatial' for i in va}
    t['spatial_block']=t[ID].map(block);assert t.spatial_block.notna().all()
    cols=['experiment']+KEY+['y_true','y_pred']
    p=pd.read_parquet(c.OUT/'tables/oof_predictions.parquet');p=p[p.experiment.isin(['C-T0','C-T1','C-T3','C-H0M'])][cols].copy();p.experiment=p.experiment.replace({'C-T0':BASE})
    e=pd.read_parquet(c.b.e.OUT/'tables/oof_predictions.parquet');p=pd.concat([p,e[e.experiment.eq('F4-E2')][cols]],ignore_index=True)
    b=pd.read_parquet(c.b.OUT/'tables/oof_predictions.parquet');p=pd.concat([p,b[b.experiment.isin(['B2','B3'])][cols]],ignore_index=True)
    mix=pd.read_parquet(c.b.OUT/'tables/fixed_blend_oof.parquet');p=pd.concat([p,mix[mix.experiment.ne('F4_S1')][cols]],ignore_index=True)
    assert not p.duplicated(['experiment']+KEY).any()
    assert np.array_equal(p[ID].map(t.set_index(ID)[TARGET]).to_numpy(),p.y_true.to_numpy())
    for (exp,protocol,repeat,fold),g in p.groupby(['experiment','protocol','repeat','fold']):
        match=[s for s in splits if s[:3]==(protocol,repeat,fold)];assert len(match)==1
        assert set(g[ID])==set(t.iloc[match[0][4]][ID])
    return d,t,p,splits

def inventory():
    roots=[ROOT/'outputs/modeling'/f for f in ['family_1','family_2','family_3']]+[ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization',c.b.e.f.OUT,c.b.e.OUT,c.b.OUT]
    rows=[];artifact=[];seen=set()
    for directory in roots:
        for path in directory.rglob('*'):
            if not path.is_file() or path in seen or path.suffix not in ['.md','.json','.csv','.parquet']:continue
            if path.name.endswith('oof_predictions.parquet') or path.name in ['10_k2_oof_predictions.parquet','11_k_oof_predictions.parquet','fixed_blend_oof.parquet']:
                seen.add(path);z=pd.read_parquet(path)
                name=next((x for x in ['experiment','pipeline','model','architecture'] if x in z),None)
                if name is None or not {ID,'y_true','y_pred','repeat','fold'}.issubset(z):continue
                if 'protocol' not in z:z['protocol']='random'
                base=path.parent.parent;config=next(iter(base.glob('*configuration.json')),None)
                if config is None and (base/'frozen_design.json').exists():config=base/'frozen_design.json'
                cfg=json.loads(config.read_text(encoding='utf8')) if config else {}
                specs=cfg.get('specs',{})
                for exp,g in z.groupby(name):
                    spec=specs.get(exp)
                    if base==c.OUT:
                        spec={'C-T0':dict(kind='direct_EN',columns=c.RAIN+[c.NDVI]),'C-T1':dict(kind='direct_EN',columns=c.RAIN+[c.DTR]),**{x:dict(kind='direct_EN',columns=y) for x,y in c.T_SPECS.items()},'C-H0':dict(kind='direct_EN',columns=c.RAIN+[c.NDVI]),'C-H0M':dict(kind='Gaussian_Ridge',columns=c.RAIN+[c.NDVI],ratio=0),'C-H1':dict(kind='Gaussian_GLS_Ridge',columns=c.RAIN+[c.NDVI],random_effect='profile_intercept',ratio_grid=c.RATIO)}.get(exp,spec)
                    if base==c.b.OUT:spec=cfg.get('models',{}).get(exp,spec)
                    if base.name=='stage3_round1':
                        signals={'SOF_NDVI':['ndvi'],'SOF_SAVI':['savi'],'SOF_NDWI':['ndwi'],'SOF_DSWI4':['dswi4'],'SOF_VIGOR':['ndvi','savi'],'SOF_MOISTURE':['ndwi','dswi4']}.get(exp,['ndvi','savi','ndwi','dswi4'])
                        spec=dict(kind='scalar_on_function' if str(exp).startswith('SOF') else 'FPCA_scores_regression',signals=signals,representation='joint_PCA' if str(exp).endswith('JOINT') else 'per_index',source='scripts/data_uderstanding/tablas_agrocebada/203_family2_round1.py',window='Apr-Oct2025',selection='4fold innerCV; FPCA/scaling/penalty fit within training')
                    if base.name=='stage3_round2_hybrid':
                        spec=dict(kind='climate_plus_scalar_on_function' if exp=='CLIMATE_SOF_ALL4' else 'climate_plus_FPCA' if 'FPCA' in exp else 'climate_only_matched',climate='48ClimateCurrent features',functional_signals=['ndvi','savi','ndwi','dswi4'] if ('FPCA' in exp or exp=='CLIMATE_SOF_ALL4') else [],source='scripts/data_uderstanding/tablas_agrocebada/204_family2_round2_hybrid.py',selection='4fold innerCV, pooled inner OOF RMSE, matched controls')
                    if base.name=='f3_2_structural_climate_conditioning':
                        structural={'M0_CLIMATE':'Frozen TOP20 EN climate','M1_A1_ADDITIVE':'M0 + Ridge A1 PCA3','M2_A1_INTERACTION':'M0 + Ridge A1 PCA3,4climate moderators,12interactions','M3_E3_ADDITIVE':'M0 + Ridge E3 PCA3','M4_E3_INTERACTION':'M0 + Ridge E3 PCA3,4climate moderators,12interactions'}
                        spec=dict(description=structural.get(exp,'Archived F3 specification'),source='scripts/modeling/304_f3_2_structural_climate_conditioning.py',specification_table='outputs/modeling/family_3/f3_2_structural_climate_conditioning/specifications/model_specifications.csv')
                    if str(exp)=='A_CURRENT_CH_H_T':spec=dict(kind='sequential_residual',layers=['Climate TOP20 selected within fold ElasticNet','Sentinel history residual XGB','topography residual Ridge'],source='outputs/modeling/residual_signal_audit/stage6_architecture_optimization/report/residual_architecture_optimization_report.md',no_geographic_equivalent=True)
                    model_dirs=[base/'models',base/'checkpoints']
                    n_models=sum(sum(1 for f in md.glob('*') if f.is_file() and str(exp) in f.name) for md in model_dirs if md.exists())
                    rows.append(dict(model_id=exp,family_stage=base.relative_to(ROOT).as_posix(),specification_json=json.dumps(spec,ensure_ascii=False) if spec is not None else 'See source specification / registry; not recovered from config',variables_json=json.dumps(spec,ensure_ascii=False) if spec is not None else 'See archived specification and source inventory',window='Apr-Oct2025 for current inputs; NDVI May; history and static sources per source configuration',regularization=json.dumps({k:v for k,v in cfg.items() if any(x in k for x in ['grid','alpha','l1','eta','lambda'])},ensure_ascii=False),selection='archived internal CV per configuration/source; no D fitting',protocols=';'.join(sorted(g.protocol.unique())),n_oof=len(g),n_ids=g[ID].nunique(),individual_predictions=True,n_model_files_found=n_models,fold_keys='ID_POLIGONO,protocol,repeat,fold',oof_path=path.relative_to(ROOT).as_posix(),oof_sha256=c.b.a.sha(path),configuration_path=config.relative_to(ROOT).as_posix() if config else '',warning='Historical aggregation may be meanfold; D paired candidates require exact compatibility; exploratory reused labels',previous_decision='See evidence matrix and archived report; no retrospective reselection'))
            if ('report' in path.parts or path.name=='configuration.json') and path.suffix in ['.md','.json']:
                artifact.append(dict(path=path.relative_to(ROOT).as_posix(),kind='report/configuration',sha256=c.b.a.sha(path)))
    inv=pd.DataFrame(rows).drop_duplicates(['model_id','oof_path'])
    # Retain exact source experiment IDs; comparison aliases are explicitly separate.
    inv['version']='archived path; v1 where present; hashes identify precise content'
    inv['metrics_available']='individual OOF y_true/y_pred; archived metric tables listed in protected inputs'
    inv['mathematical_specification']='See specification_json and frozen source; direct linear EN/Ridge or base+cross-fitted correction according to kind'
    inv['models_available']=inv.n_model_files_found.gt(0)
    inv['fold_identifiers']='Explicit repeat/fold per OOF row; protocol present or original50fold random-only'
    inv['internal_selection_reference']=inv.configuration_path.where(inv.configuration_path.ne(''),inv.family_stage+'/ source scripts and specification tables')
    save(inv,'model_inventory.csv')
    save(pd.DataFrame(artifact).drop_duplicates('path'),'background_artifact_inventory.csv')

def comparability(p):
    rows=[];rep=[]
    for (exp,protocol,repeat),g in p.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g[ID].nunique()==138
        rep.append(dict(experiment=exp,protocol=protocol,repeat=repeat,**metrics(g)))
    for candidate,baseline in PAIRS:
        a=p[p.experiment.eq(candidate)];b=p[p.experiment.eq(baseline)]
        for protocol in sorted(set(a.protocol)&set(b.protocol)):
            aa=a[a.protocol.eq(protocol)];bb=b[b.protocol.eq(protocol)]
            z=aa.merge(bb,on=KEY,validate='one_to_one',suffixes=('','_base'))
            assert len(z)==len(aa)==len(bb) and np.array_equal(z.y_true,z.y_true_base)
            rows.append(dict(candidate=candidate,baseline=baseline,protocol=protocol,n_oof=len(z),n_unique_ids=z[ID].nunique(),n_repeats=z['repeat'].nunique(),exact_keys=True,identical_y=True,independent_evaluation='archived outerfold provenance, training IDs disjoint; no new fitting',aggregation='OOF complete per repeat'))
    save(pd.DataFrame(rows),'comparability.csv');r=pd.DataFrame(rep);save(r,'metrics_repeat.csv')
    summary=r.groupby(['experiment','protocol']).agg(n_parcels=('n','first'),n_repeats=('repeat','size'),RMSE=('RMSE','mean'),RMSE_sd_repeats=('RMSE','std'),MAE=('MAE','mean'),bias=('bias','mean'),MSE=('MSE','mean')).reset_index()
    save(summary,'metrics_summary.csv')
    for label,mask in [('random',summary.protocol.eq('random')),('geographic',summary.protocol.ne('random'))]:save(summary[mask],f'metrics_{label}_compatible.csv')
    return summary

def blocks(t,p):
    fields=c.RAIN+c.COMPACT+[c.DTR,c.NDVI,TARGET,'altitude_m','slope_degrees']+[x for x in t if x.startswith('soil_map_share_mentions_group_') or x.startswith('geo250_share__')]
    desc=[];composition=[];smd=[]
    for block,g in t.groupby('spatial_block'):
        composition.append(dict(block=block,n=len(g),n_profiles=g.climate_profile.nunique(),municipalities=json.dumps(g.Municipio.value_counts().to_dict(),ensure_ascii=False),states=json.dumps(g.Estado.value_counts().to_dict(),ensure_ascii=False),profiles=json.dumps(g.climate_profile.value_counts().to_dict()),n_Chignahuapan=int(g.Municipio.eq('Chignahuapan').sum())))
        for f in fields:
            a=g[f].dropna();desc.append(dict(block=block,feature=f,n=len(a),mean=a.mean(),std=a.std(ddof=1),min=a.min(),q10=a.quantile(.1),q25=a.quantile(.25),median=a.median(),q75=a.quantile(.75),q90=a.quantile(.9),max=a.max()))
    for f in fields:
        a=t.loc[t.spatial_block.eq(3),f].dropna();b=t.loc[t.spatial_block.ne(3),f].dropna();den=np.sqrt((a.var()+b.var())/2)
        smd.append(dict(feature=f,n_block3=len(a),n_rest=len(b),SMD=(a.mean()-b.mean())/den if den>1e-12 and len(a)>1 and len(b)>1 else np.nan,block3_min=a.min(),block3_max=a.max(),rest_min=b.min(),rest_max=b.max(),n_block3_outside_rest_range=int(((a<b.min())|(a>b.max())).sum()),warning='Y differences descriptive; no variable selection or causal attribution'))
    save(pd.DataFrame(composition),'block_composition.csv');save(pd.DataFrame(desc),'block_covariate_distributions.csv');save(pd.DataFrame(smd),'block3_standardized_differences.csv');save(t,'labelled_parcel_context.parquet')
    support=pd.read_csv(c.OUT/'tables/validation_predictor_support.csv');support=support[support.protocol.eq('spatial')].merge(t[[ID,'spatial_block']],on=ID,validate='one_to_one');save(support,'spatial_support.csv')
    fm=[];gains=[];omit=[];biasparts=[]
    q=p[p.protocol.eq('spatial')]
    for (exp,fold),g in q.groupby(['experiment','fold']):fm.append(dict(experiment=exp,block=fold,**metrics(g),q10_error=(g.y_pred-g.y_true).quantile(.1),median_error=(g.y_pred-g.y_true).median(),q90_error=(g.y_pred-g.y_true).quantile(.9)))
    for exp in ['C-T1','C-T3','C-H0M','F4-E2']:
        z=q[q.experiment.eq(exp)].merge(q[q.experiment.eq(BASE)],on=KEY,validate='one_to_one',suffixes=('','_base'))
        z['gain']=(z.y_true-z.y_pred_base)**2-(z.y_true-z.y_pred)**2
        for block,g in z.groupby('fold'):
            gains.append(dict(candidate=exp,baseline=BASE,block=block,n=len(g),sse_gain=g.gain.sum(),gain_per_parcel=g.gain.mean(),fraction_net_sse_gain=g.gain.sum()/z.gain.sum(),parcel_fraction=len(g)/len(z),baseline_sse=((g.y_true-g.y_pred_base)**2).sum(),candidate_sse=((g.y_true-g.y_pred)**2).sum(),baseline_bias=(g.y_pred_base-g.y_true).mean(),candidate_bias=(g.y_pred-g.y_true).mean()))
            e0=(g.y_pred_base-g.y_true).to_numpy();e1=(g.y_pred-g.y_true).to_numpy()
            biasgain=len(g)*(e0.mean()**2-e1.mean()**2);spreadgain=len(g)*(e0.var(ddof=0)-e1.var(ddof=0))
            biasparts.append(dict(candidate=exp,block=block,n=len(g),sse_gain=g.gain.sum(),bias_squared_gain=biasgain,error_variance_gain=spreadgain,fraction_gain_from_bias=biasgain/g.gain.sum() if abs(g.gain.sum())>1e-12 else np.nan))
        for block in range(1,6):
            g=z[z.fold.ne(block)];a=metrics(g);b=metrics(g.rename(columns={'y_pred':'discard','y_pred_base':'y_pred'}))
            omit.append(dict(candidate=exp,baseline=BASE,omitted_block=block,n=len(g),delta_RMSE=a['RMSE']-b['RMSE'],delta_MAE=a['MAE']-b['MAE'],sse_gain=g.gain.sum(),analysis='OOF aggregation sensitivity; no retraining'))
    save(pd.DataFrame(fm),'spatial_block_errors.csv');save(pd.DataFrame(gains),'spatial_block_gains.csv');save(pd.DataFrame(omit),'spatial_block_omission.csv');save(pd.DataFrame(biasparts),'block_bias_variance_decomposition.csv')
    z=q.pivot(index=ID,columns='experiment',values='y_pred').join(t.set_index(ID)[[TARGET,'spatial_block']]);base=(z[TARGET]-z[BASE])**2
    z['gain_T1']=base-(z[TARGET]-z['C-T1'])**2;z['gain_T3']=base-(z[TARGET]-z['C-T3'])**2
    save(z.reset_index(),'spatial_parcel_gain_overlap.csv')
    overlap=[]
    for scope,g in [('block3',z[z.spatial_block.eq(3)]),('all',z)]:
        overlap.append(dict(scope=scope,n=len(g),both_improve=int(((g.gain_T1>0)&(g.gain_T3>0)).sum()),T1_only=int(((g.gain_T1>0)&(g.gain_T3<=0)).sum()),T3_only=int(((g.gain_T1<=0)&(g.gain_T3>0)).sum()),neither=int(((g.gain_T1<=0)&(g.gain_T3<=0)).sum()),gain_correlation=g.gain_T1.corr(g.gain_T3)))
    save(pd.DataFrame(overlap),'spatial_gain_overlap_summary.csv')

def influence(t,p):
    losses=[];stats=[];concentration=[];omissions=[];subgroups=[]
    context=t.set_index(ID)[['Municipio','Estado','climate_profile','spatial_block']]
    for candidate,baseline in PAIRS:
        a=p[p.experiment.eq(candidate)];b=p[p.experiment.eq(baseline)];z=a.merge(b,on=KEY,suffixes=('','_base'),validate='one_to_one')
        z['SE_base']=(z.y_true-z.y_pred_base)**2;z['SE_candidate']=(z.y_true-z.y_pred)**2;z['AE_base']=abs(z.y_true-z.y_pred_base);z['AE_candidate']=abs(z.y_true-z.y_pred);z['SE_gain']=z.SE_base-z.SE_candidate;z['AE_gain']=z.AE_base-z.AE_candidate
        z=z.join(context,on=ID);z['candidate']=candidate;z['baseline']=baseline;losses.append(z)
        # Equal parcel identity; repeated predictions are averaged losses, never averaged predictions.
        parcel=z.groupby(['protocol',ID])[['SE_base','SE_candidate','AE_base','AE_candidate','SE_gain','AE_gain']].mean().reset_index().join(context,on=ID)
        for protocol,g in parcel.groupby('protocol'):
            for loss in ['SE_gain','AE_gain']:
                x=g[loss];stats.append(dict(candidate=candidate,baseline=baseline,protocol=protocol,loss=loss,n_parcels=len(g),sum_gain=x.sum(),mean_gain=x.mean(),median=x.median(),q10=x.quantile(.1),q25=x.quantile(.25),q75=x.quantile(.75),q90=x.quantile(.9),fraction_improve=(x>1e-12).mean(),fraction_worsen=(x<-1e-12).mean()))
            net=g.SE_gain.sum();positive=g.loc[g.SE_gain>0,'SE_gain'].sum()
            ordered=g.sort_values('SE_gain',ascending=False)
            for k in [1,5,10]:
                top=ordered.head(k);bottom=ordered.tail(k)
                concentration.append(dict(candidate=candidate,baseline=baseline,protocol=protocol,k=k,net_gain=net,positive_gain=positive,top_gain=top.SE_gain.sum(),top_fraction_net=top.SE_gain.sum()/net if abs(net)>1e-12 else np.nan,top_fraction_positive=top.SE_gain.sum()/positive if positive else np.nan,bottom_gain=bottom.SE_gain.sum(),top_ids=json.dumps(top[ID].tolist()),bottom_ids=json.dumps(bottom[ID].tolist())))
                for order,removed in [('largest_gain',top),('largest_baseline_error',g.nlargest(k,'SE_base'))]:
                    kept=g[~g[ID].isin(removed[ID])]
                    omissions.append(dict(candidate=candidate,baseline=baseline,protocol=protocol,order=order,k=k,n_remaining=len(kept),pooled_delta_RMSE=np.sqrt(kept.SE_candidate.mean())-np.sqrt(kept.SE_base.mean()),delta_MAE=kept.AE_candidate.mean()-kept.AE_base.mean(),net_gain=kept.SE_gain.sum(),removed_ids=json.dumps(removed[ID].tolist()),aggregation='RMS of mean parcel losses; distinct from primary mean-repeat RMSE; no retraining'))
            for field in ['Municipio','climate_profile']:
                for group,h in g.groupby(field):subgroups.append(dict(candidate=candidate,baseline=baseline,protocol=protocol,group_type=field,group=group,n_parcels=len(h),mean_SE_gain=h.SE_gain.mean(),sum_SE_gain=h.SE_gain.sum(),mean_AE_gain=h.AE_gain.mean(),fraction_improve=(h.SE_gain>0).mean()))
    allz=pd.concat(losses,ignore_index=True);save(allz,'paired_losses.parquet')
    save(pd.DataFrame(stats),'paired_loss_summary.csv');save(pd.DataFrame(concentration),'gain_concentration.csv');save(pd.DataFrame(omissions),'parcel_omission_sensitivity.csv');save(pd.DataFrame(subgroups),'paired_subgroup_gains.csv')
    diagnostic=p[p.experiment.ne('B2')].join(context,on=ID).copy();diagnostic['error']=diagnostic.y_pred-diagnostic.y_true;diagnostic['AE']=abs(diagnostic.error);diagnostic['SE']=diagnostic.error**2
    diagnostic['large_error']=diagnostic.groupby(['experiment','protocol','repeat']).AE.transform(lambda x:x>=x.quantile(.9))
    case=diagnostic.groupby(ID).agg(n_records=('error','size'),n_models=('experiment','nunique'),n_protocols=('protocol','nunique'),large_error_fraction=('large_error','mean'),positive_error_fraction=('error',lambda x:(x>0).mean()),mean_error=('error','mean'),mean_AE=('AE','mean'),max_AE=('AE','max'),mean_SE=('SE','mean'),error_sd=('error','std'))
    # Also equal-weight model/protocol summaries so ten repeats do not dominate case interpretation.
    unit=diagnostic.groupby([ID,'experiment','protocol']).agg(mean_error=('error','mean'),mean_AE=('AE','mean'),large_error_fraction=('large_error','mean')).reset_index()
    balanced=unit.groupby(ID).agg(balanced_mean_AE=('mean_AE','mean'),balanced_large_error_fraction=('large_error_fraction','mean'),n_model_protocol_units=('mean_AE','size'),same_sign_unit_fraction=('mean_error',lambda x:max((x>0).mean(),(x<0).mean())))
    case=case.join(balanced).join(context);case['classification']=np.where((case.balanced_large_error_fraction>=.5)&(case.same_sign_unit_fraction>=.8),'recurrent_large_same_sign',np.where(case.balanced_large_error_fraction>=.5,'large_variable_sign','other_or_model_compensation'))
    support=pd.read_csv(c.OUT/'tables/validation_predictor_support.csv');outside=support[[f+'_support' for f in [c.DTR,c.COMPACT[0],c.NDVI]]].eq('outside').any(axis=1);support['outside_any']=outside
    case=case.join(support.groupby(ID).outside_any.mean().rename('archived_C_support_outside_fraction'))
    case['independent_label_error_evidence']='not established; verify records and harvested area before attributing cause'
    case['verification_priority']='field/document audit; not observation exclusion'
    save(case.sort_values(['balanced_large_error_fraction','balanced_mean_AE'],ascending=False).reset_index(),'persistent_case_audit.csv');save(unit,'case_model_protocol_details.csv')

def local(t,p):
    rows=[];summaries=[];profiledesc=[]
    for scope,g in [('all_labels',t),('Chignahuapan',t[t.Municipio.eq('Chignahuapan')])]:
        overall=g[TARGET].mean();means=g.groupby('climate_profile')[TARGET].transform('mean');ss=((g[TARGET]-overall)**2).sum();within=((g[TARGET]-means)**2).sum();between=((means-overall)**2).sum()
        summaries.append(dict(scope=scope,n=len(g),n_profiles=g.climate_profile.nunique(),SS_total=ss,SS_within=within,SS_between=between,fraction_within=within/ss,fraction_between=between/ss,interpretation='descriptive label decomposition; not explained predictive variance or causal contribution'))
    for profile,g in t.groupby('climate_profile'):
        if len(g)<2:continue
        for scope,h in [('full_profile',g),('Chignahuapan_only',g[g.Municipio.eq('Chignahuapan')])]:
            if len(h)<2:continue
            profiledesc.append(dict(profile=profile,scope=scope,n=len(h),n_possible_pairs=len(h)*(len(h)-1)//2,y_mean=h[TARGET].mean(),y_variance=h[TARGET].var(ddof=1),y_min=h[TARGET].min(),y_max=h[TARGET].max(),ndvi_mean=h[c.NDVI].mean(),ndvi_sd=h[c.NDVI].std(),ndvi_min=h[c.NDVI].min(),ndvi_max=h[c.NDVI].max()))
    q=p.merge(t[[ID,'climate_profile','Municipio']],on=ID,validate='many_to_one')
    dispersion=[]
    for (exp,protocol,repeat,profile),g in q.groupby(['experiment','protocol','repeat','climate_profile']):
        if len(g)>=2:dispersion.append(dict(experiment=exp,protocol=protocol,repeat=repeat,profile=profile,n=len(g),y_sd=g.y_true.std(),prediction_sd=g.y_pred.std(),prediction_range=g.y_pred.max()-g.y_pred.min()))
    for (exp,protocol,repeat,fold,profile),g in q.groupby(['experiment','protocol','repeat','fold','climate_profile']):
        for scope,h in [('full_profile',g),('Chignahuapan_only',g[g.Municipio.eq('Chignahuapan')]),('outside_Chignahuapan',g[g.Municipio.ne('Chignahuapan')])]:
            if len(h)<2:continue
            arr=h[[ID,'y_true','y_pred']].to_numpy()
            for a,b in itertools.combinations(arr,2):rows.append(dict(experiment=exp,protocol=protocol,repeat=repeat,fold=fold,profile=profile,scope=scope,id_a=a[0],id_b=b[0],observed_difference=float(a[1]-b[1]),predicted_difference=float(a[2]-b[2]),pair_error=float((a[2]-b[2])-(a[1]-b[1]))))
    pairs=pd.DataFrame(rows);save(pairs,'same_model_pair_errors.parquet')
    pm=[]
    for key,g in pairs.groupby(['experiment','protocol','repeat','profile','scope']):pm.append(dict(zip(['experiment','protocol','repeat','profile','scope'],key),n_pairs=len(g),n_parcels=len(set(g.id_a)|set(g.id_b)),pair_RMSE=np.sqrt(np.mean(g.pair_error**2)),pair_MAE=abs(g.pair_error).mean()))
    pm=pd.DataFrame(pm);save(pm,'profile_pair_metrics_repeat.csv');save(pm.groupby(['experiment','protocol','profile','scope']).mean(numeric_only=True).reset_index(),'profile_pair_metrics_summary.csv')
    eq=pm.groupby(['experiment','protocol','repeat','scope']).agg(n_profiles=('profile','size'),mean_pair_MSE=('pair_RMSE',lambda x:np.mean(x*x)),equal_profile_MAE=('pair_MAE','mean')).reset_index();eq['equal_profile_RMSE']=np.sqrt(eq.mean_pair_MSE)
    save(eq,'equal_profile_pair_metrics_repeat.csv');save(eq.groupby(['experiment','protocol','scope']).mean(numeric_only=True).reset_index(),'equal_profile_pair_metrics_summary.csv')
    save(pd.DataFrame(summaries),'yield_within_between_decomposition.csv');save(pd.DataFrame(profiledesc),'repeated_profile_description.csv');save(pd.DataFrame(dispersion),'profile_prediction_dispersion.csv')

def run():
    freeze();inventory();d,t,p,splits=load();save(p,'compatible_oof.parquet');summary=comparability(p);blocks(t,p);influence(t,p);local(t,p)
    pd.read_csv(c.OUT/'tables/interval_calibration_summary.csv').to_csv(OUT/'tables/archived_interval_calibration.csv',index=False)
    municipal=pd.read_csv(c.OUT/'tables/transfer_leave_one_block_out.csv');municipal=municipal[municipal.protocol.eq('municipality')&municipal.candidate.eq('C-T3')].copy();municipal.baseline=BASE;save(municipal,'municipal_fold_omission_archived.csv')
    print('D archived diagnostics complete; no predictive fitting',flush=True)
    from .stage_d_reporting import build
    build(t,p,summary)
