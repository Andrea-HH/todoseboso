"""Phase III X-only execution, fixed hypotheses and preservation audit."""
from pathlib import Path
import hashlib,json,time,platform
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
from ..research import ROOT,CORE,RAIN
from ..statistics import correlation,variance_parts
from .representations import NumericRepresentation,angles,evaluate
from src.family_1.temporal_primitives import extract_temporal_features

OUT=ROOT/'outputs/research/ct3_incremental_information/phase_iii/v1'
DYNAMICS=['S2_lai_promedio_runup_start_day','S2_savi_promedio_runup_duration']
RELATED=DYNAMICS+['S2_ndvi_promedio_runup_start_day','S2_ndvi_promedio_runup_duration','S2_lai_promedio_runup_duration','S2_savi_promedio_runup_start_day']
TERRAIN=['TOPO_BASIC_elevation_mean','TOPO_BASIC_slope_mean','TOPO_ADV_local_relief_3x3_mean','TOPO_ADV_tpi_3x3_mean','TOPO_ADV_plan_curvature_mean','TOPO_ADV_profile_curvature_mean','TOPO_ADV_flow_accumulation_log1p_mean','TOPO_ADV_twi_mean']

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

class ReadOnlyInputs:
    def __init__(self):self.hashes={}
    def path(self,p):
        p=ROOT/p if not Path(p).is_absolute() else Path(p);self.hashes[p.relative_to(ROOT).as_posix()]=sha(p);return p
    def parquet(self,p,columns=None):return pd.read_parquet(self.path(p),columns=columns)
    def csv(self,p):return pd.read_csv(self.path(p))
    def verify_manifest(self,p):
        manifest=json.loads(self.path(p).read_text(encoding='utf-8'));assert manifest['status']=='complete'
        for path,h in manifest['artifacts'].items():assert sha(self.path(path))==h,path
        return manifest
    def verify(self):
        for p,h in self.hashes.items():assert sha(ROOT/p)==h,p

def inputs():
    if OUT.exists():raise FileExistsError('Completed or partial version exists; use a new version')
    for sub in ['audit','figures','representations']:(OUT/sub).mkdir(parents=True,exist_ok=True)
    reader=ReadOnlyInputs()
    reader.verify_manifest('outputs/research/ct3_incremental_information/v1/manifest.json')
    reader.verify_manifest('outputs/research/ct3_incremental_information/interpretation/v1/manifest.json')
    for name in ['ct3_incremental_information_findings.md','family4_e_decision_summary.md','territorial_program_stage_b_decision.md','territorial_program_stage_c_decision.md','family7_expansion.md','experimental_pls1867.md','family8_recommendation.md']:
        reader.path('documentation/'+name)  # Previous evidence justifies blocks; no statistics with Y enter fitting.
    master=reader.parquet('data/processed/family_1/features/family1_features_all.parquet').set_index('ID_POLIGONO')
    c=reader.parquet('data/processed/family_4/territorial_intraprofile_program/v1/stage_c/c_features_197_target_free.parquet',columns=['ID_POLIGONO','CONJUNTO','climate_profile','Municipio','Estado']+CORE+RAIN).set_index('ID_POLIGONO')
    assert len(master)==len(c)==197 and master.index.is_unique and set(master.index)==set(c.index)
    master=master.reindex(c.index)
    train_ids=c.index[c.CONJUNTO.eq('ENTRENAMIENTO')];assert len(train_ids)==138 and c.CONJUNTO.eq('PREDICCION').sum()==59
    original_ids=reader.parquet('outputs/modeling/experimental_pls1867/v1/cache/train138_1867.parquet',columns=['ID_POLIGONO']).ID_POLIGONO
    train_ids=pd.Index(original_ids);assert set(train_ids)==set(c.index[c.CONJUNTO.eq('ENTRENAMIENTO')])
    fd=reader.csv('data/processed/family_1/features/family1_feature_dictionary.csv').drop_duplicates('feature_name');fd=fd[fd.feature_name.isin(master)]
    s2=fd[(fd.source=='S2')&(fd.sensor=='S2')];planet=fd[(fd.source=='PLANET')&(fd.sensor=='PLANET')]
    assert len(s2)==764 and len(planet)==277
    organization=pd.concat([s2,planet]).copy();organization['physical_index']=organization.variable.str.split('_').str[0]
    organization.to_csv(OUT/'audit/satellite_feature_organization.csv',index=False)
    groups=[tuple(row) for row in organization[['sensor','physical_index','window','feature_family']].to_numpy()]
    joined=s2.feature_name.tolist()+planet.feature_name.tolist();assert joined==organization.feature_name.tolist()
    monthly=reader.parquet('data/processed/family_1/h_joint_climate_signal/v1/joint_monthly_197.parquet').set_index('ID_POLIGONO').reindex(c.index)
    soil=reader.parquet('data/processed/family_1/i_climate_conditioned_geographic_edaphological/v1/soil_full_composition.parquet').set_index('ID_POLIGONO').reindex(c.index)
    geo=reader.parquet('data/processed/family_4/territorial_intraprofile_program/v1/stage_a/geology_full_composition_197.parquet').set_index('ID_POLIGONO').reindex(c.index)
    for d in [soil,geo]:assert np.isfinite(d.to_numpy(float)).all() and (d.to_numpy(float)>=0).all();np.testing.assert_allclose(d.sum(axis=1),1,atol=1e-9)
    soil.attrs['physical_support']='mutually exclusive full map units,250k; Hellinger sqrt shares, no pseudocount or renormalization'
    geo.attrs['physical_support']='mutually exclusive full geological units incl UNKNOWN,250k; Hellinger sqrt shares'
    original=reader.parquet('data/processed/family_1/i_climate_conditioned_geographic_edaphological/v1/integrated_diagnostic_197.parquet',columns=['ID_POLIGONO']+[f'soil_map_share_mentions_group_{g}' for g in ['AN','CM','DU','LP','LV','PH','PL','RG','UM','VR']]).set_index('ID_POLIGONO').reindex(c.index)
    hcols=[k for k in master if k.startswith(('HIST_S2_ndvi_','ANOM_S2_ndvi_'))]
    hcols=[k for k in hcols if 'unstable' not in k]  # Support flag remains metadata, not a continuous index.
    climate=monthly[[k for k in monthly if k.startswith(('rain_','tmin_','tmax_'))]]
    blocks={
      'dynamics_original':master[DYNAMICS],
      'dynamics_related':master[RELATED],
      'sentinel_current':master[s2.feature_name.tolist()],
      'planet_current':master[planet.feature_name.tolist()],
      'satellite_joint':master[joined],
      'history_ndvi2':master[['HIST_S2_ndvi_promedio_mean','HIST_S2_ndvi_promedio_std']],
      'history_anomaly_ndvi':master[hcols],
      'terrain_continuous':master[TERRAIN],
      'soil_groups_original':original,
      'soil_units_hellinger':np.sqrt(soil).rename(columns=lambda k:'sqrt_soil_'+k),
      'geology_units_hellinger':np.sqrt(geo).rename(columns=lambda k:'sqrt_geo_'+k),
      'climate_monthly_between':climate,
    }
    assert not any(any(k in d for k in ['RENDIMIENTO_T_HA','y_true','y_pred','Estado','Municipio']) for d in blocks.values())
    np.testing.assert_allclose(c[CORE[0]],c[RAIN].sum(axis=1),atol=1e-10)
    assert c.climate_profile.nunique()==53 and c.loc[train_ids].climate_profile.nunique()==43
    dominant=c.loc[train_ids][c.loc[train_ids].Municipio.eq('Chignahuapan')].groupby('climate_profile').size().nlargest(2).index.tolist()
    splits=joblib.load(reader.path('outputs/modeling/family_7/boosting/v1/cache/frozen65_splits.joblib'));assert len(splits)==65
    prior=reader.csv('outputs/research/ct3_incremental_information/v1/phase_i/variable_audit.csv')
    cfg=dict(phase='III',no_Y=True,no_predictive_fits=True,no_F8=True,no_PRED_predictions=True,scopes=['138','197_descriptive_transductive'],modes=['total','ct3_residual','within_descriptive'],component_variants=[2,5,'90pct','95pct'],bootstrap_profile_draws=12,seed=2026,scale_sensitivity='IQR with documented SD fallback',deduplication='absolute observed correlation>=.99999 on training X only',hierarchy='sensor/index/window/family; first-stage min(2,k90); subgroup unit trace and sensor unit trace; second PCA',composition='sqrt shares Hellinger, closed mutual exclusive map unit compositions only; not overlapping mentions',temporal_sensitivity='omit each calendar month;4 random20pct deletions; deterministic2026; no interpolation',classification='technical A/B/C by support/stability/interpretability, no aggregate score, no outcome metrics',blocks={k:list(v.columns) for k,v in blocks.items()},source_sha={p.relative_to(ROOT).as_posix():sha(p) for p in Path(__file__).parent.glob('*.py')},dependencies=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__),previous_counts='197/138/59;53/43profiles; source organization764S2current+277Planet; no1867 rebuild')
    (OUT/'frozen_design.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    return reader,blocks,c,train_ids,groups,dominant

def all_representations(blocks,meta,train_ids,hgroups,dominant):
    catalog=[];comparison=[];spectra=[];loadings=[];stability=[];rng=np.random.default_rng(2026);base_models={}
    for scope,ids in [('138',train_ids),('197_descriptive_transductive',meta.index)]:
        m=meta.loc[ids];core=m[CORE];profiles=m.climate_profile.to_numpy();municip=m.Municipio.to_numpy()
        for block,zfull in blocks.items():
            z=zfull.loc[ids];original=block in ['dynamics_original','history_ndvi2','soil_groups_original']
            kinds=['original'] if original else ['pca']
            if block=='satellite_joint':kinds+=['hierarchical']
            for kind in kinds:
                for mode in ['total','ct3_residual','within']:
                    if kind=='original' and mode!='total':continue
                    key=f'{block}__{kind}__{mode}'
                    rep=NumericRepresentation(kind=kind,mode=mode,k=len(z.columns),hierarchical_groups=hgroups if kind=='hierarchical' else None).fit(z,core,profiles)
                    if rep.eigenvalues.sum()>0:
                        power=rep.eigenvalues/rep.eigenvalues.sum();variants=sorted(set([min(2,rep.rank),min(5,rep.rank),int(np.searchsorted(power.cumsum(),.9)+1),int(np.searchsorted(power.cumsum(),.95)+1)]))
                        for i,val in enumerate(power):spectra.append(dict(scope=scope,representation=key,component=i+1,variance_fraction=float(val)))
                    else:variants=[0]
                    if kind=='original':variants=[rep.retained]
                    for k in variants:
                        rep.set_k(k);results,scores=evaluate(rep,z,core,profiles,dominant,municip)
                        identifier=key+f'__k{rep.retained}';comparison.append(dict(scope=scope,representation=identifier,block=block,kind=kind,mode=mode,**results))
                        for j in range(rep.retained):
                            ix=np.argsort(abs(rep.basis[:,j]))[-6:][::-1]
                            for i in ix:loadings.append(dict(scope=scope,representation=identifier,dimension=j+1,variable=z.columns[i],weight=float(rep.basis[i,j])))
                    baseline_k=min(5,rep.rank) if kind!='original' else rep.retained;rep.set_k(baseline_k)
                    score=rep.transform(z,core,profiles)
                    # Scores are descriptive only; never saved as future fixed inductive inputs.
                    if scope=='138':
                        base_models[key]=rep
                        frame=pd.DataFrame(score,index=ids,columns=[f'dim_{i+1}' for i in range(score.shape[1])]);frame.index.name='ID_POLIGONO'
                        frame.to_parquet(OUT/'representations'/f'{key}_scores138_descriptive.parquet')
                        catalog.append(dict(representation=key,block=block,kind=kind,mode=mode,input_dimensions=z.shape[1],baseline_dimensions=rep.retained,rank=rep.rank,definition='original indicators' if kind=='original' else ('SVD/PCA of standardized X; linear-core residual or profile centering explicitly separate'),source='existing verified feature matrices; see frozen_design and consumed hashes',support='Apr–Oct2025; static maps/DEM or2022–24history as block dictates',composition='Hellinger sqrt of exclusive units' if 'hellinger' in block else 'none; original overlapping soil mentions are not PCA inputs',inductive_policy='refit imputation/scales/core projection/components on corresponding training only; within group unseen fallback=global training mean; descriptive scores prohibited as frozen model inputs',quality_caveat='LAI scale/phenology unverified; map250k not parcel precision; no Y used'))
                        # Same feature metric when comparing rescaled loadings.
                        cases=[('omit_dominant',np.flatnonzero(~np.isin(profiles,dominant)),'standard',False),('omit_Chignahuapan',np.flatnonzero(municip!='Chignahuapan'),'standard',False),('robust_IQR',np.arange(len(z)),'robust',False),('deduplicate',np.arange(len(z)),'standard',True)]
                        if kind!='original':
                            ids_profiles=pd.unique(profiles)
                            for b in range(12):
                                draws=rng.choice(ids_profiles,len(ids_profiles),replace=True);idx=np.concatenate([np.flatnonzero(profiles==g) for g in draws]);cases.append((f'profile_bootstrap_{b}',idx,'standard',False))
                        for case,idx,scale,dedup in cases:
                            alt=NumericRepresentation(kind,mode,scale,baseline_k,hgroups if kind=='hierarchical' else None,dedup).fit(z.iloc[idx],core.iloc[idx],profiles[idx])
                            common=alt.basis*(rep.scales/alt.scales)[:,None]
                            row=angles(rep.basis,common,baseline_k);row.update(representation=key,case=case,n_rows=len(idx),base_k=baseline_k,alternative_k=alt.retained,rank=alt.rank,scale=scale,removed_near_duplicates=int(rep.active.sum()-alt.active.sum()) if dedup else 0,scale_IQR_fallbacks=int(alt.scale_fallback.sum()),support='X-only resampling; not independent inference')
                            stability.append(row)
    pd.DataFrame(catalog).to_csv(OUT/'representation_catalog.csv',index=False)
    pd.DataFrame(comparison).to_csv(OUT/'block_comparison.csv',index=False)
    pd.DataFrame(stability).to_csv(OUT/'stability_analysis.csv',index=False)
    pd.DataFrame(spectra).to_csv(OUT/'audit/eigenspectra.csv',index=False)
    pd.DataFrame(loadings).to_csv(OUT/'audit/top_loading_interpretation.csv',index=False)
    return pd.DataFrame(catalog),pd.DataFrame(comparison),pd.DataFrame(stability)

def dynamic_relations(blocks,meta,train_ids):
    raw=blocks['dynamics_original'].join(meta[CORE[-1]])
    rows=[]
    for scope,ids in [('138',train_ids),('197_descriptive_transductive',meta.index)]:
        d=raw.loc[ids];m=meta.loc[ids]
        for label,mask in [('all',np.ones(len(d),bool)),('outside_Chignahuapan',m.Municipio.ne('Chignahuapan').to_numpy())]:
            a=d.loc[mask];g=m.loc[mask,'climate_profile'];w=a-a.groupby(g).transform('mean')
            for i in range(3):
                for j in range(i+1,3):rows.append(dict(scope=scope,subset=label,a=d.columns[i],b=d.columns[j],pearson=correlation(a.iloc[:,i],a.iloc[:,j]),within_pearson=correlation(w.iloc[:,i],w.iloc[:,j]),n=len(a)))
    pd.DataFrame(rows).to_csv(OUT/'audit/dynamics_redundancy.csv',index=False)

def temporal_sensitivity(reader,blocks,meta):
    rows=[];coverage=[];rng=np.random.default_rng(2026)
    for sensor,path,variables in [('S2','data/processed/family_1/timeseries/sentinel_timeseries.parquet',['ndvi_promedio','lai_promedio','savi_promedio']),('PLANET','data/processed/family_1/timeseries/planet_timeseries.parquet',['ndvi_promedio'])]:
        ts=reader.parquet(path,columns=['ID_POLIGONO','fecha_captura']+variables);ts.fecha_captura=pd.to_datetime(ts.fecha_captura);ts=ts[ts.fecha_captura.between('2025-04-01','2025-10-31')]
        for pid,g in ts.groupby('ID_POLIGONO'):
            for var in variables:
                z=g[['fecha_captura',var]].dropna().groupby('fecha_captura',as_index=False)[var].mean().sort_values('fecha_captura');gap=z.fecha_captura.diff().dt.days
                base=extract_temporal_features(z.fecha_captura,z[var]);month=z.fecha_captura.dt.month
                coverage.append(dict(sensor=sensor,ID_POLIGONO=pid,index=var,n_dates=len(z),n_months=month.nunique(),max_gap_days=gap.max(),median_gap_days=gap.median(),negative_observations=int((z[var]<0).sum())))
                wanted=['runup_start_day'] if var=='lai_promedio' else (['runup_duration'] if var=='savi_promedio' else ['q10','normalized_auc'])
                for stat in wanted:
                    col=f'{sensor}_{var}_{stat}'
                    if sensor=='S2' and stat in ['runup_start_day','runup_duration']:
                        expected=blocks['dynamics_original'].loc[pid,col];assert abs(base[stat]-expected)<1e-10
                pert=[(f'omit_month_{m}',np.flatnonzero(month.to_numpy()!=m)) for m in range(4,11)]
                for r in range(4):pert.append((f'drop20pct_{r}',np.sort(rng.choice(len(z),max(2,int(np.floor(.8*len(z)))),replace=False))))
                for case,idx in pert:
                    alt=extract_temporal_features(z.fecha_captura.iloc[idx],z[var].iloc[idx])
                    for stat in wanted:rows.append(dict(sensor=sensor,ID_POLIGONO=pid,index=var,statistic=stat,case=case,baseline=base[stat],perturbed=alt[stat],absolute_change=abs(alt[stat]-base[stat]),n_remaining=len(idx)))
    pd.DataFrame(coverage).to_csv(OUT/'audit/temporal_coverage.csv',index=False)
    pd.DataFrame(rows).to_csv(OUT/'audit/temporal_sensitivity.csv',index=False)

def run():
    start=time.perf_counter()
    reader,blocks,meta,train_ids,groups,dominant=inputs();print('PhaseIII identity/hashes verified; X-only blocks frozen',flush=True)
    with threadpool_limits(limits=1):
        cat,comp,stable=all_representations(blocks,meta,train_ids,groups,dominant);print('X-only representations/stability complete',flush=True)
        dynamic_relations(blocks,meta,train_ids);temporal_sensitivity(reader,blocks,meta);print('Temporal sensitivities complete',flush=True)
    from .reporting import build
    build(cat,comp,stable,dominant)
    reader.verify();pd.DataFrame([dict(path=p,sha256=h) for p,h in reader.hashes.items()]).to_csv(OUT/'audit/consumed_hashes.csv',index=False)
    cfg=json.loads((OUT/'frozen_design.json').read_text())
    for p,h in cfg['source_sha'].items():assert sha(ROOT/p)==h
    artifacts={p.relative_to(ROOT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file()}
    (OUT/'manifest.json').write_text(json.dumps(dict(status='complete',phase='III',yield_values_used=0,new_yield_models=0,PRED_predictions=0,F8_executed=False,source_inputs_verified=len(reader.hashes),wall_seconds=time.perf_counter()-start,artifacts=artifacts),indent=2),encoding='utf-8')
    print('COMPLETE',time.perf_counter()-start,flush=True)
