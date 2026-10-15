"""Read-only F8 audit. No estimator construction, training or prediction calls."""
from pathlib import Path
import json,hashlib,re,itertools,shutil,joblib
import numpy as np,pandas as pd
from sklearn.model_selection import KFold,GroupKFold
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/research/family_8/residual_design/v1'
ID='ID_POLIGONO';TARGET='RENDIMIENTO_T_HA'
CORE=['compact_precip_total','compact_early_fraction','compact_concentration_hhi','S2_ndvi_month_05']
HISTORY=['HIST_S2_ndvi_promedio_mean','HIST_S2_ndvi_promedio_std'];SLOPE='TOPO_BASIC_slope_mean'
F7=ROOT/'outputs/modeling/family_7/expansion/v1'
SOURCES={}
def sha(p):
    digest=hashlib.sha256()
    with p.open('rb') as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()
def source(path):
    p=ROOT/path;SOURCES[p.relative_to(ROOT).as_posix()]=sha(p);return p
def save(x,name):x.to_csv(OUT/'tables'/name,index=False)
def read_config(path):return json.loads(source(path).read_text(encoding='utf8'))
def load():
    t=pd.read_parquet(source('outputs/modeling/family_7/expansion/v1/cache/train138_exact_features.parquet'))
    splits=joblib.load(source('outputs/modeling/family_7/expansion/v1/cache/frozen65_splits.joblib'))
    groups=pd.read_csv(source('outputs/modeling/family_7/expansion/v1/splits/group_memberships.csv')).set_index(ID)
    assert len(t)==138 and t[ID].is_unique and len(splits)==65
    return t,splits,groups
def subcv(t,positions,protocol,groups):
    if protocol=='random':return list(KFold(min(4,len(positions)),shuffle=True,random_state=2026).split(positions))
    g=groups.loc[t.iloc[positions][ID],protocol].to_numpy();k=min(4,len(set(g)))
    if k<2:raise ValueError('Insufficient groups; never substitute random CV')
    return list(GroupKFold(k).split(positions,groups=g))
def feasibility():
    t,splits,groups=load();profile=t.groupby('climate_profile')[TARGET].agg(n='size',mean='mean',sd='std',min='min',max='max').reset_index()
    profile['n_pairs']=profile.n*(profile.n-1)//2;save(profile,'profile_support.csv')
    y=t[TARGET].to_numpy();means=t.groupby('climate_profile')[TARGET].transform('mean').to_numpy()
    within=float(np.sum((y-means)**2));total=float(np.sum((y-y.mean())**2));pairs=int(profile.n_pairs.sum())
    support=dict(n_labels=138,n_climate_profiles=len(profile),n_repeated_profiles=int(profile.n.ge(2).sum()),n_singleton_profiles=int(profile.n.eq(1).sum()),n_parcels_repeated=int(profile.loc[profile.n.ge(2),'n'].sum()),n_pairs=pairs,n_municipalities=t.Municipio.nunique(),n_states=t.Estado.nunique(),within_profile_TSS=within,total_TSS=total,within_fraction=within/total,between_fraction=1-within/total,Chignahuapan_n=int(t.Municipio.eq('Chignahuapan').sum()),Chignahuapan_profiles=t.loc[t.Municipio.eq('Chignahuapan'),'climate_profile'].nunique(),warning='Descriptive full TRAIN means only; never operational targets or validation-dependent transforms')
    (OUT/'audit/sample_support.json').write_text(json.dumps(support,indent=2),encoding='utf8')
    stages=[];contexts={};guards=[]
    def tune_context(pos,cv,p,r,f,label):
        signature=(tuple(t.iloc[pos][ID]),p,tuple((tuple(a),tuple(b)) for a,b in cv))
        contexts[signature]=dict(n=len(pos),cv_folds=len(cv),fit_count=12*len(cv)+1)
        for a,b in cv:
            train=pos[a];held=pos[b];assert not set(train)&set(held)
            rows=t.iloc[train];raw=rows[CORE[:3]].to_numpy(float)
            stages.append(dict(protocol=p,repeat=r,fold=f,level=label,n_train=len(train),n_validation=len(held),n_profiles=rows.climate_profile.nunique(),n_groups=rows[ID].map(groups[p]).nunique() if p!='random' else len(train),n_varying_rain3=int((np.nanstd(raw,axis=0)>1e-12).sum()),n_varying_compact4=int((np.nanstd(rows[CORE].to_numpy(float),axis=0)>1e-12).sum()),n_varying_slope=int(rows[SLOPE].nunique()>1)))
    for p,r,f,tr,va,inner in splits:
        assert not set(tr)&set(va);tune_context(tr,inner,p,r,f,'base_outer_selection')
        for j,(a,b) in enumerate(inner):
            aa=tr[a];bb=tr[b];assert not set(aa)&set(bb)
            cv=subcv(t,aa,p,groups);tune_context(aa,cv,p,r,f,'inner_base_selection_and_residual_crossfit')
            for c,d in cv:
                aaa=aa[c];ddd=aa[d];deeper=subcv(t,aaa,p,groups)
                tune_context(aaa,deeper,p,r,f,'deep_base_tuning_excludes_residual_heldout')
                assert not set(aaa)&set(ddd) and not set(aaa)&set(bb) and not set(aaa)&set(va)
                guards.append(dict(protocol=p,repeat=r,fold=f,outer_inner=j,n_train=len(aaa),n_residual_heldout=len(ddd),excludes_outer_validation=True,excludes_inner_validation=True,excludes_residual_heldout=True,n_tuning_folds=len(deeper)))
    z=pd.DataFrame(stages);save(z,'proposed_nested_training_sizes.csv');save(pd.DataFrame(guards),'proposed_membership_exclusion_checks.csv')
    save(z.groupby(['protocol','level']).agg(n_contexts=('fold','size'),n_train_min=('n_train','min'),n_train_median=('n_train','median'),n_train_max=('n_train','max'),n_groups_min=('n_groups','min'),n_all_rain_constant=('n_varying_rain3',lambda x:(x==0).sum()),n_all_compact4_constant=('n_varying_compact4',lambda x:(x==0).sum())).reset_index(),'nested_feasibility_summary.csv')
    cost=dict(unique_base_tuning_contexts=len(contexts),base_EN_fits_upper_without_existing_cache=sum(c['fit_count'] for c in contexts.values()),R1_corrector_fits=65*(3*4+1),R2_corrector_fits=65*(6*4+1),C_V_corrector_fits=65*(6*4+1),lambda_adds_no_model_fits=True,actual_new_fits=0,existing_context_reuse='only identical dataset, features, preprocessing, CV, grid, seed and exclusion provenance; cached outer C-T3 reusable, not globally chosen parameters in inner evaluation')
    (OUT/'audit/proposed_compute_budget.json').write_text(json.dumps(cost,indent=2),encoding='utf8')
    return support,cost
def metrics(frame):
    error=frame.y_pred.to_numpy()-frame.y_true.to_numpy();return dict(n=len(frame),RMSE=float(np.sqrt(np.mean(error**2))),MAE=float(abs(error).mean()),bias=float(error.mean()))
def pair_metrics(frame):
    stats={};parcel_ids=set()
    for (fold,profile),g in frame.groupby(['fold','climate_profile']):
        n=len(g)
        if n<2:continue
        error=g.y_pred.to_numpy()-g.y_true.to_numpy();diff=error[:,None]-error[None,:];tri=diff[np.triu_indices(n,1)]
        d=stats.setdefault(profile,[0.,0.,0]);d[0]+=float(tri@tri);d[1]+=float(abs(tri).sum());d[2]+=len(tri);parcel_ids.update(g[ID])
    if not stats:return dict(n_pairs=0,n_profiles=0,n_parcels=0,equal_profile_RMSE=np.nan,pair_weighted_RMSE=np.nan,equal_profile_MAE=np.nan,pair_weighted_MAE=np.nan)
    a=np.array(list(stats.values()))
    return dict(n_pairs=int(a[:,2].sum()),n_profiles=len(stats),n_parcels=len(parcel_ids),equal_profile_RMSE=float(np.sqrt(np.mean(a[:,0]/a[:,2]))),pair_weighted_RMSE=float(np.sqrt(a[:,0].sum()/a[:,2].sum())),equal_profile_MAE=float(np.mean(a[:,1]/a[:,2])),pair_weighted_MAE=float(a[:,1].sum()/a[:,2].sum()))
def archived(path,family,namecol='experiment',predcol='y_pred'):
    paths=[path] if isinstance(path,str) else path
    z=pd.concat([pd.read_parquet(source(p)) for p in paths],ignore_index=True)
    if namecol!='experiment':z=z.rename(columns={namecol:'experiment'})
    if predcol!='y_pred':z=z.rename(columns={predcol:'y_pred'})
    if 'protocol' not in z:z['protocol']='random'
    z['family']=family;z['source_oof']=' | '.join(paths)
    return z
def collect_archives():
    frames=[]
    rs='outputs/modeling/residual_signal_audit/'
    for family,path,col,pr in [('RS1',[p.relative_to(ROOT).as_posix() for p in sorted((ROOT/rs/'stage1/checkpoints').glob('pred_fold_*.parquet'))],'pipeline','corrected_pred'),('RS2',rs+'stage2_history/checkpoints/rs2_oof_predictions.parquet','experiment','corrected_pred'),('RS3',rs+'stage3_climate/checkpoints/rs3_oof_predictions.parquet','experiment','y_pred'),('RS4',rs+'stage4_champion_reconstruction/predictions/oof_predictions.parquet','pipeline','y_pred'),('RS5',rs+'stage5_second_residual_audit/checkpoints/residual2_predictions.parquet','pipeline','corrected_pred'),('RS6',rs+'stage6_architecture_optimization/predictions/oof_predictions.parquet','architecture','y_pred')]:frames.append(archived(path,family,col,pr))
    for family,path in [('J','outputs/modeling/family_1/j_incremental_geographic_edaphological_yield/v1/tables/02_oof_predictions.parquet'),('K','outputs/modeling/family_1/k_standalone_residual_geographic_edaphological/v1/tables/11_k_oof_predictions.parquet'),('L','outputs/modeling/family_1/l_multiblock_representation/v1/tables/10_oof_predictions.parquet'),('M','outputs/modeling/family_1/m_historical_multisensor/v1/tables/10_oof_predictions.parquet'),('F4','outputs/modeling/family_4/conditional_yield_response/v1/tables/oof_predictions.parquet'),('F4-E','outputs/modeling/family_4/conditional_yield_response/extensions/within_profile_complementarity/v1/tables/oof_predictions.parquet'),('B','outputs/research/family_4/territorial_intraprofile_program/v1/stage_b/tables/oof_predictions.parquet'),('C','outputs/research/family_4/territorial_intraprofile_program/v1/stage_c/tables/oof_predictions.parquet'),('F5-S1','outputs/modeling/family_5/gpr_s1/v1/tables/oof_predictions.parquet'),('F6','outputs/modeling/family_6/bagging/v1/tables/oof_predictions.parquet'),('F6-E','outputs/modeling/family_6/expansion/v1/tables/oof_predictions.parquet'),('F7','outputs/modeling/family_7/expansion/v1/tables/oof_predictions.parquet')]:frames.append(archived(path,family))
    return frames
def recompute(frames):
    t,splits,groups=load();lookup=t.set_index(ID)[TARGET];splitmap={(p,r,f):set(t.iloc[v][ID]) for p,r,f,tr,v,inner in splits};rows=[];pairs=[];inventory=[]
    for frame in frames:
        family=frame.family.iloc[0]
        # Recovered controls are catalogued with original source family, not
        # falsely represented as additional trained architectures.
        for name,g in frame.groupby('experiment'):
            gate=[]
            for (p,r,f),h in g.groupby(['protocol','repeat','fold']):
                assert set(h[ID])==splitmap[(p,r,f)],(family,name,p,r,f)
                np.testing.assert_allclose(h.y_true,lookup.reindex(h[ID]),atol=1e-12)
                gate.append(dict(protocol=p,repeat=r,fold=f,n=len(h)))
            for (p,r),h in g.groupby(['protocol','repeat']):
                assert len(h)==138 and h[ID].is_unique
                rows.append(dict(family=family,experiment=name,protocol=p,repeat=r,**metrics(h)))
                joined=h[[ID,'fold','y_true','y_pred']].merge(t[[ID,'climate_profile']],on=ID,validate='many_to_one')
                pairs.append(dict(family=family,experiment=name,protocol=p,repeat=r,**pair_metrics(joined)))
            inventory.append(dict(family=family,experiment=name,source_oof=g.source_oof.iloc[0],n_oof=len(g),n_unique_ids=g[ID].nunique(),n_folds=len(gate),protocols=' | '.join(sorted(g.protocol.unique())),exact_outer_validation_ids=True,identical_targets=True))
    r=pd.DataFrame(rows);ip=pd.DataFrame(pairs);save(r,'archived_metrics_repeat_recomputed.csv');save(ip,'archived_intraprofile_repeat_recomputed.csv')
    save(r.groupby(['family','experiment','protocol']).agg(RMSE=('RMSE','mean'),MAE=('MAE','mean'),bias=('bias','mean'),n=('n','first'),n_repeats=('repeat','size')).reset_index(),'archived_metrics_summary_recomputed.csv')
    save(ip.groupby(['family','experiment','protocol']).mean(numeric_only=True).reset_index(),'archived_intraprofile_summary_recomputed.csv');save(pd.DataFrame(inventory),'oof_compatibility_inventory.csv')
    return pd.DataFrame(inventory)
def source_scan():
    rows=[]
    for base in ['src','scripts/data_uderstanding/tablas_agrocebada']:
        for p in (ROOT/base).rglob('*.py'):
            if 'family_8' in p.parts:continue
            lines=p.read_text(encoding='utf8',errors='replace').splitlines()
            hits=[(i+1,line.strip()[:260]) for i,line in enumerate(lines) if re.search(r'resid|crossfit|cross.fit|demean|centered|target_transform|TransformedTarget',line,re.I)]
            if hits:
                source(p.relative_to(ROOT).as_posix())
                rows += [dict(path=p.relative_to(ROOT).as_posix(),line=i,excerpt=line,classification='search locator; manual source audit determines whether predictive residual or descriptive/feature centering') for i,line in hits]
    save(pd.DataFrame(rows),'residual_and_transformed_target_source_scan.csv')
def run():
    if (OUT/'manifest.json').exists():raise FileExistsError('Completed F8 research immutable')
    for d in ['audit','tables','report','figures']:(OUT/d).mkdir(parents=True,exist_ok=True)
    m=read_config('outputs/modeling/family_7/expansion/v1/manifest.json')
    protected=pd.read_csv(source('outputs/modeling/family_7/expansion/v1/audit/protected_inputs.csv')).to_dict('records')+[dict(path=p,sha256=h) for p,h in m['artifacts'].items()]
    protected.append(dict(path=F7.relative_to(ROOT).as_posix()+'/manifest.json',sha256=sha(F7/'manifest.json')))
    pd.DataFrame(protected).drop_duplicates('path').to_csv(OUT/'audit/protected_inputs.csv',index=False)
    # This read-only research does not load or mutate archived model files.
    # Carry their prior sealed hashes; verify all actually consumed sources
    # against that chain at completion rather than re-reading every old model.
    source_scan();support,cost=feasibility();frames=collect_archives();inventory=recompute(frames)
    from .audit import build
    build(inventory)
    from .reporting import build as reports
    reports(support,cost,frames)
    expected={row['path'].replace('\\','/'):row['sha256'] for row in protected}
    verification=[]
    for path,h in SOURCES.items():
        assert sha(ROOT/path)==h,path
        if path in expected:assert h==expected[path],path
        verification.append(dict(path=path,sha256=h,verified_unchanged_during_F8=True,matches_inherited_hash=path in expected))
    pd.DataFrame(verification).to_csv(OUT/'audit/verified_consumed_sources.csv',index=False)
    (OUT/'audit/protection_scope.json').write_text(json.dumps(dict(inherited_protected_files=len(expected),verified_consumed_sources=len(verification),scope='all sources consumed by this research rehashed; inherited unused model/raw hashes carried without reopening; all writes restricted to new F8 version and new F8 documentation',new_model_fits=0),indent=2),encoding='utf8')
    pd.DataFrame([dict(path=p,sha256=h,use='read-only source/evidence; never new training or PRED') for p,h in SOURCES.items()]).to_csv(OUT/'audit/source_inventory.csv',index=False)
    print('F8 research generated; zero new model fits; proposal only',flush=True)
