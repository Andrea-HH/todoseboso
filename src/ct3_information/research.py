"""Phases I–II only; immutable references and descriptive associations."""
from pathlib import Path
import json,hashlib,time
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
from .statistics import variance_parts,category_contrasts,residual_projection,cross_projection,partial_correlation,within_association,pair_association,standardized_matrix,spectral_summary,correlation

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/research/ct3_incremental_information/v1'
CORE=['compact_precip_total','compact_early_fraction','compact_concentration_hhi','S2_ndvi_month_05']
RAIN=[f'rain_{m}_2025' for m in ['apr','may','jun','jul','aug','sep','oct']]
BLOCKS={
 'vegetation_dynamics':['S2_lai_promedio_runup_start_day','S2_savi_promedio_runup_duration'],
 'vegetation_state_controls':['S2_ndvi_promedio_q10','S2_lai_promedio_q10'],
 'terrain':['TOPO_BASIC_slope_mean','TOPO_ADV_local_relief_3x3_mean'],
 'history_ndvi2':['HIST_S2_ndvi_promedio_mean','HIST_S2_ndvi_promedio_std'],
 'soil_cartographic_groups':[f'soil_map_share_mentions_group_{g}' for g in ['AN','CM','DU','LP','LV','PH','PL','RG','UM','VR']],
 'geology_diversity':['geo250_composition_entropy'],
 'climate_regional_controls':[f'tmax_{m}_2025' for m in ['apr','may','jun','jul','aug','sep','oct']]+['CLIMATE_dtr_mean_std','dtr_change_aug_sep','tmean_change_sep_oct'],
}
JUSTIFICATION={
 'vegetation_dynamics':'F4-E: small local LAI complement; SAVI duration descriptive partial signal, not new screening.',
 'vegetation_state_controls':'F4-E redundant/unstable state contrasts; negative/conceptual controls, not candidates selected by new Y ranking.',
 'terrain':'J/K/F6/F7: slope localized benefits with territorial harm; relief is prior negative control.',
 'history_ndvi2':'F6/F7: local/spatial complements but municipal damage; same two frozen descriptors.',
 'soil_cartographic_groups':'J/K/L and soil quartiles: broad cartographic overlap and regional confounding; conditioned diagnosis only.',
 'geology_diversity':'Stage A: variation within dominant profiles but weak partial evidence; entropy of existing250k source only.',
 'climate_regional_controls':'G/H and PLS: high VIP can encode regional temporal structure; explicitly test absence of intraprofile contrast.',
}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

class Inputs:
    def __init__(self):self.hashes={}
    def path(self,p):
        p=ROOT/p if not Path(p).is_absolute() else Path(p)
        self.hashes[p.relative_to(ROOT).as_posix()]=sha(p);return p
    def csv(self,p):return pd.read_csv(self.path(p))
    def parquet(self,p):return pd.read_parquet(self.path(p))
    def text(self,p):return self.path(p).read_text(encoding='utf-8')
    def verify(self):
        for p,h in self.hashes.items():assert sha(ROOT/p)==h,p

def prepare(inputs):
    if OUT.exists():raise FileExistsError('Use a new version; this research output already exists')
    for folder in ['audit','phase_i','phase_ii','figures','report']: (OUT/folder).mkdir(parents=True,exist_ok=True)
    a=inputs.csv('outputs/research/variable_inventory/v1/inventario_1557.csv')
    b=inputs.csv('outputs/research/experimental_variable_inventory/v1/variables_adicionales.csv')
    assert len(a)==1557 and len(b)==310 and not set(a.variable)&set(b.variable)
    canonical=inputs.parquet('data/processed/family_4/territorial_intraprofile_program/v1/stage_c/c_features_197_target_free.parquet')
    ref=inputs.parquet('outputs/modeling/family_7/boosting/v1/cache/train138_exact_features.parquet')
    master=inputs.csv('data/original/01_tablas_maestras/ID_area_rendimiento_70_30_Reto_AgroCebada.csv')
    assert len(canonical)==197 and canonical.ID_POLIGONO.is_unique
    assert len(ref)==138 and ref.ID_POLIGONO.is_unique
    pd.testing.assert_series_equal(ref.RENDIMIENTO_T_HA.reset_index(drop=True),ref.ID_POLIGONO.map(master.set_index('ID_POLIGONO').RENDIMIENTO_T_HA).reset_index(drop=True),check_names=False)
    ids=canonical.ID_POLIGONO;matrix=pd.DataFrame(index=pd.Index(ids,name='ID_POLIGONO'));paths={}
    for r in a.itertuples():paths.setdefault(r.tabla_procesada,[]).append(r.variable)
    for r in b.itertuples():paths.setdefault(r.tablas.split('; ')[0],[]).append(r.variable)
    for path,cols in paths.items():
        d=inputs.parquet(path).set_index('ID_POLIGONO');assert d.index.is_unique and set(ids)<=set(d.index),path
        matrix=matrix.join(d[cols].reindex(ids))
    names=list(a.variable)+list(b.variable);matrix=matrix[names];assert matrix.shape==(197,1867)
    train=matrix.loc[ref.ID_POLIGONO];meta=canonical.set_index('ID_POLIGONO').loc[ref.ID_POLIGONO,['climate_profile','Municipio','Estado']].copy();meta['RENDIMIENTO_T_HA']=ref.RENDIMIENTO_T_HA.to_numpy()
    assert (meta.drop(columns='RENDIMIENTO_T_HA').reset_index(drop=True)==ref[['climate_profile','Municipio','Estado']]).all().all()
    for c in CORE:np.testing.assert_allclose(train[c],ref[c],atol=1e-12)
    np.testing.assert_allclose(matrix[CORE[0]],matrix[RAIN].sum(axis=1),rtol=0,atol=1e-10)
    np.testing.assert_allclose(matrix[CORE[1]],matrix[RAIN[:3]].sum(axis=1)/(matrix[CORE[0]]+1e-6),atol=1e-12)
    np.testing.assert_allclose(matrix[CORE[2]],((matrix[RAIN].to_numpy()/(matrix[CORE[0]].to_numpy()+1e-6)[:,None])**2).sum(axis=1),atol=1e-12)
    gp=canonical.set_index('ID_POLIGONO').climate_profile
    assert gp.nunique()==53 and meta.climate_profile.nunique()==43
    assert matrix[RAIN].groupby(gp).nunique().max().max()==1
    assert matrix[RAIN].drop_duplicates().shape[0]==53
    sizes=meta.groupby('climate_profile').size();assert (sizes>=2).sum()==12 and (sizes==1).sum()==31 and sizes[sizes>=2].sum()==107
    dominant=meta[meta.Municipio.eq('Chignahuapan')].groupby('climate_profile').size().nlargest(2).index.tolist()
    assert sorted(meta[meta.Municipio.eq('Chignahuapan')].groupby('climate_profile').size().nlargest(2).tolist())==[29,33]
    splits=joblib.load(inputs.path('outputs/modeling/family_7/boosting/v1/cache/frozen65_splits.joblib'))
    groups=inputs.csv('outputs/modeling/family_7/boosting/v1/splits/group_memberships.csv').set_index('ID_POLIGONO').loc[ref.ID_POLIGONO]
    oof=inputs.parquet('outputs/research/family_4/territorial_intraprofile_program/v1/stage_c/tables/oof_predictions.parquet');oof=oof[oof.experiment.eq('C-T3')].copy();assert len(oof)==1794
    outer_audit=[]
    for pro,re,fold,tr,va,inner in splits:
        assert not set(tr)&set(va) and set(tr)|set(va)==set(range(138))
        for it,iv in inner:assert not set(it)&set(iv) and set(it)|set(iv)==set(range(len(tr)))
        if pro!='random':
            field={'climate_profile':'climate_profile','municipality':'municipality','spatial':'spatial'}[pro]
            assert not set(groups.iloc[tr][field])&set(groups.iloc[va][field])
            for it,iv in inner:assert not set(groups.iloc[np.asarray(tr)[it]][field])&set(groups.iloc[np.asarray(tr)[iv]][field])
        q=oof[(oof.protocol==pro)&(oof['repeat']==re)&(oof.fold==fold)].set_index('ID_POLIGONO')
        assert set(q.index)==set(ref.iloc[va].ID_POLIGONO)
        np.testing.assert_allclose(q.y_true.reindex(ref.iloc[va].ID_POLIGONO),ref.iloc[va].RENDIMIENTO_T_HA,atol=1e-12)
        outer_audit.append(dict(protocol=pro,repeat=re,fold=fold,n_train=len(tr),n_valid=len(va),n_inner=len(inner),ids_targets_groups_verified=True))
    pd.DataFrame(outer_audit).to_csv(OUT/'audit/fold_identity.csv',index=False)
    cfg=dict(scope='diagnostic phases I and II only',core=CORE,candidate_blocks=BLOCKS,block_justification=JUSTIFICATION,seed=2026,subspace_bootstrap=12,subspace_k_max=5,near_equivalence_correlation=.99999,descriptive_projection='OLS intercept+standardized core; not conditional independence',associations='retrospective OLS/FWL; weighted within-NDVI; existing CT3 external OOF errors paired with train-only X projection; no new Y predictor',support_flag='at least20 parcels and3 profiles; flag only, no filtering to find winners',no_pvalues=True,no_candidate_selection_from_y=True,no_phases_III_IV=True,no_predictive_y_fit=True,no_PRED_inference=True,dominant_profiles=dominant,source_hashes={str(p.relative_to(ROOT)):sha(p) for p in Path(__file__).parent.glob('*.py')})
    assert all(c in matrix for cols in BLOCKS.values() for c in cols)
    (OUT/'frozen_design.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    return a,b,matrix,train,meta,gp,dominant,splits,oof

def catalogue_metadata(a,b):
    rows=[]
    for r in a.to_dict('records'):
        rows.append(dict(variable=r['variable'],physical_source=r['fuente'],conceptual_group=r['familia'],origin=r['archivo_o_directorio_origen'],processed_table=r['tabla_procesada'],documents=r['documentos_y_diccionarios'],description=r['descripcion_documentada'],documented_unit=r['unidad_documentada'],inventory='1557'))
    for r in b.to_dict('records'):
        rows.append(dict(variable=r['variable'],physical_source=r['grupo'],conceptual_group=r['grupo'],origin=r['fuente_periodo_uso_documentado'],processed_table=r['tablas'],documents=r['documentos_diccionarios'],description=r['definicion_documentada'],documented_unit=r['unidad_documentada'],inventory='310'))
    return pd.DataFrame(rows).fillna('')

def nature(name,series):
    if not (pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series)):return 'categorical'
    vals=series.replace([np.inf,-np.inf],np.nan).dropna()
    if len(vals) and set(vals.unique())<={0,1,True,False}:return 'binary'
    if any(k in name.lower() for k in ['share','fraction','pct_area']):return 'proportion_or_composition'
    if any(k in name.lower() for k in ['n_obs','count','n_units','streak']):return 'count'
    if any(k in name.lower() for k in ['max_month','min_month','peak_day','start_day','duration']):return 'temporal_position_or_duration'
    return 'continuous'

def audit_information(a,b,matrix,train,meta,gp,dominant):
    cat=catalogue_metadata(a,b);lookup=cat.set_index('variable');out=[];subsets={'all138':np.ones(len(train),bool),'Chignahuapan':meta.Municipio.eq('Chignahuapan').to_numpy(),'outside_Chignahuapan':meta.Municipio.ne('Chignahuapan').to_numpy(),'omit_dominant_profiles':~meta.climate_profile.isin(dominant).to_numpy()}
    variation=[]
    for name in matrix:
        s=matrix[name];kind=nature(name,s);numeric=kind!='categorical'
        row=lookup.loc[name].to_dict();row.update(variable=name,type=kind,numeric=numeric,missing_197=int(s.isna().sum()),missing_138=int(train[name].isna().sum()),unique_197=int(s.nunique()),unique_138=int(train[name].nunique()))
        lower=name.lower();physical=str(row['physical_source']).lower()
        row['sensor_product']='CHIRPS' if lower.startswith(('rain','compact_','climate_precip','hist_climate_precip','anom_climate_precip')) else ('CHIRTS/ERA5' if any(k in physical for k in ['clima','temperatura']) else ('Sentinel-2' if lower.startswith(('s2_','hist_s2','anom_s2')) else ('Planet' if lower.startswith('planet') else ('Landsat' if lower.startswith('landsat') else row['physical_source']))))
        row['time_family']='anomaly' if 'anom' in lower or 'delta' in lower else ('historical' if lower.startswith(('hist','rain_hist')) else 'current_or_static')
        row['temporal_support']='2022–2024 reference; 2025 comparison for anomalies' if row['time_family']!='current_or_static' else ('Apr–Oct2025; monthly names identify subset' if any(k in lower for k in ['s2','planet','landsat','rain','tmin','tmax','tmean','dtr','climate','compact']) else 'static map/DEM; see source metadata')
        row['spatial_support']='0.05° climate grid; parcel weighted' if any(k in physical for k in ['clima','lluvia','temperatura']) else ('DEM120m; parcel zonal/neighbor summaries' if 'topograf' in physical else ('cartography1:250000; overlay fractions, not measured soil chemistry' if 'suelo' in physical or 'geolog' in physical else 'supplied parcel summaries; source resolution not certified by this inventory'))
        row['original_or_derived']='processed/derived descriptor; monthly parcel aggregate is closest to original product'
        row['phenomenon']='vegetation spectral state/dynamics' if any(k in lower for k in ['ndvi','evi','lai','savi','fapar']) else ('water/thermal regime' if any(k in lower for k in ['rain','precip','climate','tmin','tmax','tmean','dtr','compact']) else ('terrain' if any(k in lower for k in ['topo','slope','altitude']) else 'cartographic/other descriptor; see dictionary'))
        row['fixed_covariate_status']='excluded_identifier_or_metadata' if name.startswith('EXT_LOC_nearest_name') or name=='soil_all_units_summary' else 'fixed_processed_covariate'
        row['target_or_fold_dependency']='none documented for fixed columns; no y, residual, prediction or trained component admitted'
        row['limitations']='Observed equality does not certify semantic equivalence; historical/campaign/territorial confounding; finite sample.'
        if numeric:
            z=pd.to_numeric(train[name]).to_numpy(float);zall=pd.to_numeric(s).to_numpy(float)
            row['nonfinite_197']=int((~np.isfinite(zall)).sum());row['nonfinite_138']=int((~np.isfinite(z)).sum())
            if np.isfinite(z).any():row.update(min_138=float(np.nanmin(np.where(np.isfinite(z),z,np.nan))),max_138=float(np.nanmax(np.where(np.isfinite(z),z,np.nan))))
            res=residual_projection(train[CORE],z);valid=np.isfinite(res);total=np.sum((z[valid]-np.mean(z[valid]))**2) if valid.any() else 0
            row['fraction_unexplained_by_linear_CT3']=float(np.sum(res[valid]**2)/total) if total>1e-20 else np.nan
            row['max_absolute_correlation_core']=max([abs(correlation(z,train[c])) for c in CORE if np.isfinite(correlation(z,train[c]))],default=np.nan)
            for label,mask in subsets.items():
                parts=category_contrasts(train.loc[mask,name],meta.loc[mask,'climate_profile']) if kind=='binary' else variance_parts(z[mask],meta.loc[mask,'climate_profile'])
                variation.append(dict(variable=name,subset=label,type=kind,**parts))
                if label=='all138':row.update({f'within_{k}':v for k,v in parts.items()})
            parts197=category_contrasts(s,gp) if kind=='binary' else variance_parts(zall,gp)
            row.update({f'descriptive197_{k}':v for k,v in parts197.items()})
            if kind!='binary':
                withinres=variance_parts(res,meta.climate_profile);row['residual_within_ss_after_linear_CT3']=withinres['within_ss']
        else:
            for label,mask in subsets.items():
                parts=category_contrasts(train.loc[mask,name],meta.loc[mask,'climate_profile']);variation.append(dict(variable=name,subset=label,type=kind,**parts))
                if label=='all138':row.update({f'within_{k}':v for k,v in parts.items()})
        out.append(row)
    audit=pd.DataFrame(out);v=pd.DataFrame(variation)
    # Equality is based only on observed X; constants have no informative equivalence class.
    exact={};classes={};numerical={}
    for name in matrix:
        s=matrix[name]
        if s.nunique(dropna=True)<=1:continue
        if audit.set_index('variable').loc[name,'numeric']:
            ar=s.to_numpy(float).copy();ar[ar==0]=0.;ar[np.isnan(ar)]=np.nan;key=('numeric',hashlib.sha256(ar.tobytes()).hexdigest());numerical[name]=ar
        else:key=('categorical',tuple(s.fillna('__MISSING__').astype(str)))
        exact.setdefault(key,[]).append(name)
    pairs=[]
    for cols in exact.values():
        if len(cols)>1:
            label='EQ'+str(len(classes)+1)
            for c in cols:classes[c]=label
            for c in cols[1:]:pairs.append(dict(a=cols[0],b=c,relation='exact_observed_values',correlation=np.nan,n_shared=197))
    full={k:v for k,v in numerical.items() if np.isfinite(v).all() and np.std(v)>1e-12}
    cols=list(full);z=np.column_stack(list(full.values()));z=(z-z.mean(axis=0))/z.std(axis=0)
    corr=z.T@z/len(z);ii,jj=np.where(np.triu(abs(corr)>=.99999,1))
    for i,j in zip(ii,jj):
        if classes.get(cols[i],'a')==classes.get(cols[j],'b'):continue
        pairs.append(dict(a=cols[i],b=cols[j],relation='near_affine_observed_not_semantic',correlation=float(corr[i,j]),n_shared=197))
    audit['observed_equivalence_group']=audit.variable.map(classes).fillna('')
    audit.to_csv(OUT/'phase_i/variable_audit.csv',index=False,encoding='utf-8-sig');v.to_csv(OUT/'phase_i/profile_variation.csv',index=False)
    pd.DataFrame(pairs).to_csv(OUT/'phase_i/redundancy_relations.csv',index=False)
    return audit,v,pairs

def dimensions(matrix,train,meta,audit):
    numeric=audit[audit.numeric & audit.fixed_covariate_status.eq('fixed_processed_covariate')]
    rows=[];spectra=[];stable=[];rng=np.random.default_rng(2026)
    blocks={g:group.variable.tolist() for g,group in numeric.groupby('physical_source')}
    for scope,data,groups in [('138',train,meta.climate_profile),('197_descriptive_transductive',matrix,None)]:
        for block,cols in blocks.items():
            if len(cols)<2:continue
            a,keep=standardized_matrix(data[cols]);r,s,v=spectral_summary(a)
            rows.append(dict(scope=scope,block=block,n=len(data),original_columns=len(cols),nonconstant_columns=int(keep.sum()),**r))
            if len(s):
                for i,val in enumerate(s*s/(s*s).sum()):spectra.append(dict(scope=scope,block=block,component=i+1,variance_fraction=float(val)))
            if scope!='138' or r['rank']<2:continue
            k=min(5,r['rank']);baseline=v[:k];ids=list(pd.unique(groups))
            for rep in range(12):
                draws=rng.choice(ids,len(ids),replace=True);idx=np.concatenate([np.flatnonzero(groups.to_numpy()==g) for g in draws]);boot=a[idx];boot=boot-boot.mean(axis=0)
                rb,_,vb=spectral_summary(boot)
                if rb['rank']<k:stable.append(dict(block=block,replicate=rep,k=k,n_rows=len(idx),supported=False,mean_cosine_squared=np.nan,min_cosine=np.nan));continue
                cos=np.linalg.svd(baseline@vb[:k].T,compute_uv=False)
                stable.append(dict(block=block,replicate=rep,k=k,n_rows=len(idx),supported=True,mean_cosine_squared=float(np.mean(cos*cos)),min_cosine=float(cos.min())))
    # Global spectrum both raw column weighting and block-balanced diagnostic.
    for scope,data in [('138',train),('197_descriptive_transductive',matrix)]:
        parts=[]
        for cols in blocks.values():
            a,_=standardized_matrix(data[cols])
            if a.shape[1]:parts.append(a)
        for mode,a in [('column_weighted',np.column_stack(parts)),('block_balanced',np.column_stack([a/np.sqrt(a.shape[1]) for a in parts]))]:
            r,s,_=spectral_summary(a);rows.append(dict(scope=scope,block='ALL_'+mode,n=len(data),original_columns=sum(map(len,blocks.values())),nonconstant_columns=a.shape[1],**r))
            for i,val in enumerate(s*s/(s*s).sum()):spectra.append(dict(scope=scope,block='ALL_'+mode,component=i+1,variance_fraction=float(val)))
    pd.DataFrame(rows).to_csv(OUT/'phase_i/dimensionality.csv',index=False);pd.DataFrame(spectra).to_csv(OUT/'phase_i/spectra.csv',index=False);pd.DataFrame(stable).to_csv(OUT/'phase_i/subspace_stability.csv',index=False)

def associations(train,meta,dominant,splits,oof):
    data=train.join(meta);subsets={'all138':np.ones(len(data),bool),'Chignahuapan':meta.Municipio.eq('Chignahuapan').to_numpy(),'outside_Chignahuapan':meta.Municipio.ne('Chignahuapan').to_numpy(),'omit_dominant_profiles':~meta.climate_profile.isin(dominant).to_numpy()}
    retro=[];within=[];loo=[];cross=[];pair=[];candidates=[(b,c) for b,cols in BLOCKS.items() for c in cols]
    for block,c in candidates:
        for label,mask in subsets.items():
            d=data.loc[mask];good=d[[c,'RENDIMIENTO_T_HA','climate_profile']+CORE].replace([np.inf,-np.inf],np.nan).dropna()
            means=good.groupby('climate_profile')[[c,'RENDIMIENTO_T_HA']+CORE].mean()
            retro.append(dict(block=block,variable=c,subset=label,n=len(good),n_profiles=good.climate_profile.nunique(),raw_correlation=correlation(good[c],good.RENDIMIENTO_T_HA),partial_OLS_CT3=partial_correlation(good.RENDIMIENTO_T_HA,good[c],good[CORE]),between_profile_correlation=correlation(means[c],means.RENDIMIENTO_T_HA),method='retrospective associative OLS, not predictive validation'))
            for equal in [False,True]:
                row=within_association(d,c,'RENDIMIENTO_T_HA',CORE[-1],'climate_profile',equal)
                within.append(dict(block=block,variable=c,subset=label,weighting='equal_profile' if equal else 'parcel',support_sufficient=row['n']>=20 and row['n_profiles']>=3,**row))
            for excluded in sorted(data.climate_profile.unique()):
                if label!='all138':break
                sub=d[d.climate_profile.ne(excluded)];row=within_association(sub,c,'RENDIMIENTO_T_HA',CORE[-1],'climate_profile',True)
                loo.append(dict(block=block,variable=c,omitted_profile=excluded,**row))
        # Reuse immutable OOF CT3; auxiliary regressions fit X only on outer training.
        rz={}
        for pro,re,fold,tr,va,inner in splits:
            value=cross_projection(train.iloc[tr][CORE],train.iloc[tr][c],train.iloc[va][CORE],train.iloc[va][c])
            rz[(pro,re,fold)]=pd.Series(value,index=train.iloc[va].index)
        for (pro,re),pred in oof.groupby(['protocol','repeat']):
            pred=pred.set_index('ID_POLIGONO').reindex(train.index);resy=pred.y_true-pred.y_pred
            residual=pd.concat([value for (p,r,_),value in rz.items() if p==pro and r==re]).reindex(train.index)
            for label,mask in subsets.items():
                cross.append(dict(block=block,variable=c,protocol=pro,repeat=re,subset=label,n=int((resy.loc[mask].notna()&residual.loc[mask].notna()).sum()),n_profiles=meta.loc[mask,'climate_profile'].nunique(),correlation=correlation(resy.loc[mask],residual.loc[mask]),method='CT3 heldout prediction error versus train-only linear X residual; not FWL/DML or incremental performance'))
            dd=data.copy();dd['model_fold']=pred.fold.to_numpy();dd['OOF_CT3_residual_y']=resy.to_numpy()
            for label,mask in subsets.items():
                for equal in [False,True]:
                    row=pair_association(dd.loc[mask],c,'RENDIMIENTO_T_HA',CORE[-1],'climate_profile','model_fold',equal)
                    pair.append(dict(block=block,variable=c,protocol=pro,repeat=re,subset=label,weighting='equal_profile' if equal else 'pair',support_sufficient=row['n_parcels']>=20 and row['n_profiles']>=3,**row))
    pd.DataFrame(retro).to_csv(OUT/'phase_ii/retrospective_conditional.csv',index=False);pd.DataFrame(within).to_csv(OUT/'phase_ii/within_profile_associations.csv',index=False);pd.DataFrame(loo).to_csv(OUT/'phase_ii/leave_profile_out.csv',index=False)
    cf=pd.DataFrame(cross);cf.to_csv(OUT/'phase_ii/cross_fitted_X_archived_CT3_errors.csv',index=False)
    summary=cf.groupby(['block','variable','protocol','subset']).agg(mean_correlation=('correlation','mean'),min_correlation=('correlation','min'),max_correlation=('correlation','max'),n_repeats=('repeat','nunique'),min_n=('n','min'),min_profiles=('n_profiles','min')).reset_index();summary.to_csv(OUT/'phase_ii/cross_association_summary.csv',index=False)
    pp=pd.DataFrame(pair);pp.to_csv(OUT/'phase_ii/same_model_pair_associations.csv',index=False)
    return pd.DataFrame(retro),pd.DataFrame(within),summary

def evidence(inputs):
    rows=[
      ('C','compact rainfall+May','C-T3 transfers better than monthly reference, but geographic gains concentrated','No within-profile climate contrast; previous labels reused','compact3+May','Does additional parcel information remain conditional on compact4?','territorial_program_stage_c_decision.md'),
      ('F4-E','vegetation dynamics','LAI rise modest local complement; relief and LAI q10 transfer failures','Discovered with retrospective screening; LAI physical scale not established','monthly rain+May+one descriptor','Does the LAI contrast survive conditioning on compact4?','family4_e_decision_summary.md'),
      ('B','within-profile objective','Small/no local gain and large municipal damage','Selection objective changes regularization even at lambda0','monthly rain+May+optional LAI','Do not repeat objective optimization; investigate information first','territorial_program_stage_b_decision.md'),
      ('C-H','profile random intercept','No consistent advantage versus matched Ridge','Only12 repeated profiles; common intercept cancels in differences','monthly rain+May+profile intercept','Need parcel-varying information, not profile offsets','territorial_program_stage_c_decision.md'),
      ('F5','compact GP and sensitivities','Spatial return to mean; RBF/monthly/linear-trend sensitivities no balanced solution','Small sample, bounds frozen, territory dependence','compact/monthly rain+May','Information audit can separate new contrast from kernel choice','family5_gpr_s1.md'),
      ('F6-E','history2/slope/DTR','History and slope space gains with municipal damage; DTR harms all protocols','Architecture specific; many shared errors','compact4+history2 or slope or DTR','Conditioned local signal beyond core, not another open tree search','family6_expansion.md'),
      ('F7-E','history2/slope/both','All extensions worsen all four RMSE; local gains outside Chig depend weighting','Errors correlated; limited ALE/permutation support','compact4+fixed blocks','Whether limited stable residual information remains; no automatic correction','family7_expansion.md'),
      ('PLS','dense global compression','PLS1867 worse in all protocols; spatial low yields overestimated','Duplicates and regional categories; VIP not incremental importance','all1867 dense PLS','Blockwise conditioned representations remain untested','experimental_pls1867.md'),
      ('J/K/L','soil and terrain','Cartographic soil alone has regional signal, no consistent increment; slope localized','250k categories not measured soil properties; components trained per fold','monthly rain plus direct/residual/PCA blocks','Which existing contrasts remain after compact4; no new physical interpretation','soil_yield_quartile_analysis.md'),
      ('M','multisensor history','Historical descriptions/compressions/residual hypotheses already examined','History reference and anomaly definitions matter; no universal winner','historical and anomaly blocks','Audit precise NDVI2 definitions before reducing a block again','m_historical_multisensor.md'),
      ('A','territorial geology','Geology distinguishes many local pairs but weak partial associations','250k source; unavailable50k geometry; pairs dependent','composition/terrain metadata','Incremental conditional association of existing diversity, not causal explanation','territorial_program_stage_a_decision.md'),
      ('F8','residual research only','Design/audit completed; zero experiments','Requires review; no residual targets fitted here','compact4+small centered correction proposed','This diagnosis may justify/refute proceeding, not execute F8','family8_recommendation.md'),
    ]
    for row in rows:inputs.text('documentation/'+row[-1])
    ev=pd.DataFrame(rows,columns=['family','signal','previous_result','limitation','representation','open_question','document']);ev.to_csv(OUT/'audit/previous_evidence.csv',index=False)
    sourcepaths=[
       'outputs/research/family_4/territorial_intraprofile_program/v1/stage_c/tables/oof_predictions.parquet',
       'outputs/research/family_4/territorial_intraprofile_program/v1/stage_b/tables/oof_predictions.parquet',
       'outputs/modeling/family_4/conditional_yield_response/extensions/within_profile_complementarity/v1/tables/oof_predictions.parquet',
       'outputs/modeling/family_7/boosting/v1/tables/oof_predictions.parquet',
       'outputs/modeling/family_7/expansion/v1/tables/oof_predictions.parquet',
       'outputs/modeling/experimental_pls1867/v1/tables/oof_predictions.parquet']
    metricrows=[]
    for path in sourcepaths:
        p=inputs.parquet(path)
        for (exp,pro,re),g in p.groupby(['experiment','protocol','repeat']):
            assert len(g)==138 and g.ID_POLIGONO.nunique()==138
            e=g.y_pred-g.y_true;metricrows.append(dict(source=path,experiment=exp,protocol=pro,repeat=re,rmse=float(np.sqrt(np.mean(e*e))),mae=float(abs(e).mean()),bias=float(e.mean())))
    mm=pd.DataFrame(metricrows);mm.to_csv(OUT/'audit/recomputed_prior_metrics_repeat.csv',index=False)
    mm=mm.groupby(['source','experiment','protocol'])[['rmse','mae','bias']].mean().reset_index();mm.to_csv(OUT/'audit/recomputed_prior_metrics.csv',index=False)
    ct=mm[mm.experiment.eq('C-T3')].groupby('protocol').rmse.mean();pls=mm[mm.experiment.eq('PLS1867')].set_index('protocol').rmse
    expected={'random':(.511581804,.538506),'climate_profile':(.520603921,.559928),'municipality':(.581258919,.716929),'spatial':(.678778047,.891999)}
    for pro,(v,w) in expected.items():assert abs(ct[pro]-v)<1e-6 and abs(pls[pro]-w)<1e-6
    f7=mm[mm.experiment.isin(['F7-00','F7-E1','F7-E2','F7-E3'])].groupby(['experiment','protocol']).rmse.mean().unstack(0)
    assert (f7[['F7-E1','F7-E2','F7-E3']].sub(f7['F7-00'],axis=0)>0).all().all()
    inputs.text('documentation/chignahuapan_error_concentration.md')
    inputs.csv('outputs/modeling/family_4/conditional_yield_response/extensions/within_profile_complementarity/v1/diagnostics/chignahuapan_error_concentration/strict_location_summary.csv')
    inputs.path('outputs/research/family_8/residual_design/v1/manifest.json')
    return mm

def run():
    start=time.perf_counter();inputs=Inputs()
    with threadpool_limits(limits=1):
        a,b,matrix,train,meta,gp,dominant,splits,oof=prepare(inputs)
        print('Identity verified:197/138/59,1867 columns,65 folds; blocks frozen',flush=True)
        mm=evidence(inputs);print('Prior OOF evidence recomputed',flush=True)
        audit,v,pairs=audit_information(a,b,matrix,train,meta,gp,dominant);print('Phase I variable audit complete',flush=True)
        dimensions(matrix,train,meta,audit);print('Phase I spectra/stability complete',flush=True)
        retro,within,cross=associations(train,meta,dominant,splits,oof);print('Phase II bounded associations complete',flush=True)
    from .reporting import build
    build(audit,v,pairs,retro,within,cross,mm,dominant)
    inputs.verify();pd.DataFrame([dict(path=p,sha256=h) for p,h in inputs.hashes.items()]).to_csv(OUT/'audit/consumed_input_hashes.csv',index=False)
    cfg=json.loads((OUT/'frozen_design.json').read_text())
    for p,h in cfg['source_hashes'].items():assert sha(ROOT/p)==h
    artifacts={p.relative_to(ROOT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file()}
    (OUT/'manifest.json').write_text(json.dumps(dict(status='complete',new_predictive_y_fits=0,new_PRED_predictions=0,n_catalogue=1867,n_diagnostic_candidates=sum(map(len,BLOCKS.values())),wall_seconds=time.perf_counter()-start,consumed_inputs_verified=len(inputs.hashes),artifacts=artifacts),indent=2),encoding='utf-8')
    print('COMPLETE',time.perf_counter()-start,flush=True)
