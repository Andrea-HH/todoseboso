"""Target-free census, source triage and frozen physical-similarity design."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
import joblib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.geoc_bridge import data, OLD
from src.physical_similarity import GRIDS, AMPLITUDES
OUT=ROOT/'outputs/modeling/physical_similarity/v2'

def main():
    if (OUT/'frozen_design.json').exists():raise FileExistsError('Preserve frozen design')
    for folder in ['audit','cache','models','checkpoints','tables','diagnostics']:(OUT/folder).mkdir(parents=True,exist_ok=True)
    t=data()['train'];ids=t.ID_POLIGONO.tolist();sources=[];inventory=[];blocks={};values={}
    def read(path):
        p=ROOT/path;sources.append(p)
        d=pd.read_parquet(p) if p.suffix=='.parquet' else pd.read_csv(p)
        assert d.ID_POLIGONO.is_unique
        return d.set_index('ID_POLIGONO').reindex(ids)
    def add(block,frame,columns,path):
        blocks.setdefault(block,[])
        for c in columns:
            key=block+'::'+c;s=frame[c]
            if s.dtype==bool:s=s.astype(float)
            values[key]=s;blocks[block].append(key)
            inventory.append(dict(block=block,feature=c,column=key,source_table=path,n_missing=int(s.isna().sum()),n_unique=int(s.nunique()),dtype=str(s.dtype)))
    master_path='data/processed/family_1/features/family1_features_all.parquet';m=read(master_path)
    baseinv=ROOT/'outputs/research/variable_inventory/v1/inventario_1557.csv';sources.append(baseinv);inv=pd.read_csv(baseinv)
    # Full historical inventory remains an audit, not a claim that every alias is independent.
    inv.to_csv(OUT/'audit/legacy_inventory_1557.csv',index=False)
    quality=lambda c:any(v in c.lower() for v in ['n_obs','valid_count','valid_year','support','coverage','complete','missing','key_found','not_found','assignment_reserve'])
    topo=[c for c in m if c.startswith('TOPO') and not quality(c)]
    add('relief',m,[c for c in topo if not any(v in c.lower() for v in ['elevation','altitude','aspect'])],master_path)
    add('altitude_sensitivity',m,[c for c in topo if 'elevation' in c.lower()],master_path)
    sat=[c for c in m if c.startswith(('S2_','PLANET_','LANDSAT_')) and c!='S2_ndvi_month_05' and not quality(c)]
    add('satellite_2025',m,sat,master_path)
    history=[c for c in m if c.startswith(('HIST_S2_','HIST_PLANET_','HIST_LANDSAT_','ANOM_S2_','ANOM_PLANET_','ANOM_LANDSAT_')) and not quality(c)]
    add('satellite_history_anomaly',m,history,master_path)
    ext_path='data/processed/phase_c/c0_c1/external_parcel_features.parquet';e=read(ext_path)
    add('hydrology_wetlands',e,[c for c in e if c.startswith(('EXT_HYDRO_','EXT_WET_')) and not quality(c)],ext_path)
    # Prefer the full geological composition to duplicating its dominant-category summaries.
    geo='data/processed/family_4/territorial_intraprofile_program/v1/stage_a/geology_full_composition_197.parquet';g=read(geo)
    add('geology_physiography',g,list(g),geo)
    add('geology_physiography',e,[c for c in e if c.startswith('EXT_PHYS_') or c.startswith(('EXT_GEOL_distance_',))],ext_path)
    soil_path='data/processed/family_1/i_climate_conditioned_geographic_edaphological/v1/integrated_diagnostic_197.parquet';s=read(soil_path)
    soilcols=[c for c in s if c.startswith('soil_unit_share__') or c in ['soil_unit_count','soil_dominant_share','soil_mixed_share','soil_entropy','soil_boundary_distance_m','soil_boundary_buffer_125m_share','soil_dominant_texture','soil_dominant_physical_phase','soil_dominant_chemical_phase']]
    add('soil_inegi',s,soilcols,soil_path)
    safe_path='outputs/modeling/nonclimatic_local/v1/cache/audited_X197_target_free.parquet';safe=read(safe_path)
    add('soilgrids',safe,[c for c in safe if c.startswith('soilgrids__')],safe_path)
    add('wapor_npp_2025',safe,[c for c in safe if c.startswith('wapor_2025__npp__')],safe_path)
    er='outputs/research/erosion_spatial_audit/v1/tables/category_composition.csv';erframe=read(er)
    add('erosion',erframe,list(erframe),er)
    for p in ['data/processed/agronomic_calendar_set/v1/current_history_delta_197_target_free.parquet','data/processed/agronomic_calendar_set/v2_temporal_extension/current_history_delta.parquet']:
        q=read(p)
        satcols=[c for c in q if '_S2_' in c and not quality(c)]
        add('calendar_2025',q,[c for c in satcols if c.startswith('CURRENT_')],p)
        # CURRENT = HISTORY + DELTA: avoid putting all three into the same representation.
        add('calendar_history',q,[c for c in satcols if c.startswith('HIST_MEAN_')],p)
    x=pd.DataFrame(values,index=pd.Index(ids,name='ID_POLIGONO'))
    assert all(blocks.values()),{k:len(v) for k,v in blocks.items()}
    # Exact aliases within a block are removed on training X, without yield selection.
    alias=[]
    for b,cols in blocks.items():
        seen={};keep=[]
        for c in cols:
            signature=tuple(x[c].fillna('__MISSING__').astype(str))
            if signature in seen:alias.append(dict(block=b,removed=c,retained=seen[signature]))
            elif x[c].notna().mean()<.5:alias.append(dict(block=b,removed=c,retained='insufficient_X_coverage_below_50pct'))
            elif x[c].nunique()>1 and (not pd.api.types.is_numeric_dtype(x[c]) or float(x[c].std())>1e-10):seen[signature]=c;keep.append(c)
            else:alias.append(dict(block=b,removed=c,retained='constant_or_numerical_roundoff_on_138'))
        blocks[b]=keep
    deferred=[b for b,cols in blocks.items() if not cols]
    blocks={b:cols for b,cols in blocks.items() if cols}
    physical=['relief','soil_inegi','geology_physiography','soilgrids','erosion']
    dynamic=['satellite_2025','satellite_history_anomaly','wapor_npp_2025','calendar_2025','calendar_history']
    specs={k:[k] for k in blocks}
    specs.update(PHYSICAL_BALANCED=physical,DYNAMIC_BALANCED=dynamic,ALL_BALANCED=physical+dynamic)
    x.reset_index().to_parquet(OUT/'cache/features138_target_free.parquet',index=False)
    pd.DataFrame(inventory).assign(retained=lambda d:d.column.isin([c for v in blocks.values() for c in v])).to_csv(OUT/'audit/features.csv',index=False)
    pd.DataFrame(alias).to_csv(OUT/'audit/aliases_constants.csv',index=False)
    # Audit every local source folder, including sources deliberately not treated as parcel predictors.
    decisions={'ena':'Context only; state/national outcome statistics, not parcel physical measurements',
      'localidades':'Excluded: settlement context/geographic proxy, outside physical similarity hypothesis',
      'hidrologia_subterranea':'Deferred: RGB map representation is not a calibrated physical property; no new interpretation from colors',
      'chignahuapan':'Documentation only; avoid adding one-municipality-specific coverage',
      'erosion':'Included composition; 1:250k regional classes, not measured parcel erosion',
      'suelo':'Included INEGI composition; map scale, not chemical percentage',
      'geologia':'Included full composition and structural distances',
      'hidrografia':'Deferred: current parcel extraction has no valid distance/density coverage; not zero hydrological influence',
      'humedales':'Deferred: only two parcels have values; insufficient support; missing is not absence'}
    folders=[]
    for parent in ['data/original','data/externo','docs/resources']:
        for folder in (ROOT/parent).iterdir():
            if folder.is_dir():
                files=[p for p in folder.rglob('*') if p.is_file()]
                folders.append(dict(folder=str(folder.relative_to(ROOT)),files=len(files),extensions=';'.join(sorted(set(p.suffix.lower() for p in files))),policy=decisions.get(folder.name,'Official source: satellite/topography included; climate reserved to C-T3; labels/geometry audit only' if parent=='data/original' else 'Documentation/context only; calendars already derived; no historical yield targets as predictors')))
    pd.DataFrame(folders).to_csv(OUT/'audit/source_folder_triage.csv',index=False)
    # X-only intraprofile support: raw blocks, not supervised feature selection.
    exploration=[]
    for b,cols in blocks.items():
        q=x[cols];numeric=q.select_dtypes(include='number').replace([np.inf,-np.inf],np.nan)
        unique_profiles=0;within=0;totalpairs=0
        profile=t.climate_profile.to_numpy()
        rounded=q.copy()
        for c in numeric:rounded[c]=pd.to_numeric(rounded[c],errors='coerce').round(6)
        patterns=rounded.fillna('__MISSING__').astype(str).agg('|'.join,axis=1).to_numpy()
        for v in np.unique(profile):
            ix=np.flatnonzero(profile==v)
            if len(ix)<2:continue
            unique_profiles+=int(len(np.unique(patterns[ix]))>1)
            totalpairs+=len(ix)*(len(ix)-1)//2
            within+=sum(patterns[i]!=patterns[j] for a,i in enumerate(ix) for j in ix[a+1:])
        def eta(group):
            vals=[]
            for c in numeric:
                s=numeric[c];ok=s.notna()
                if ok.sum()<3 or s[ok].var()==0:continue
                z=pd.DataFrame({'x':s.to_numpy(),'g':np.asarray(group)}).dropna();means=z.groupby('g').x.transform('mean')
                vals.append(float(np.sum((means-z.x.mean())**2)/np.sum((z.x-z.x.mean())**2)))
            return float(np.median(vals)) if vals else None
        exploration.append(dict(block=b,n_input=len(cols),categorical=sum(not pd.api.types.is_numeric_dtype(q[c]) for c in q),missing_fraction=float(q.isna().mean().mean()),distinct_vectors=int(len(np.unique(patterns))),same_profile_pairs=totalpairs,different_vector_pairs=within,different_vector_fraction=within/totalpairs if totalpairs else None,profiles_with_internal_contrast=unique_profiles,median_numeric_eta2_state=eta(t.Estado),median_numeric_eta2_profile=eta(t.climate_profile)))
    pd.DataFrame(exploration).to_csv(OUT/'audit/block_exploration.csv',index=False)
    sources += [ROOT/'src/physical_similarity.py',Path(__file__),ROOT/'scripts/426_run_physical_similarity.py',ROOT/'tests/test_physical_similarity.py',OLD/'cache/execution_plan.joblib',OLD/'cache/frozen65_splits.joblib']+list((OLD/'base_cache').glob('*.joblib'))
    cfg=dict(blocks=blocks,specs=specs,grids=GRIDS,amplitudes=AMPLITUDES,components_per_block=5,deferred_empty_blocks=deferred,revision='v1 audit only, no model fit: discovered absent hydrology coverage and only two wetlands parcels; v2 excludes columns with <50pct X coverage and numerical roundoff constants before any outcome fits',schema_policy='X-only schema/coverage/alias audit on138; no Y feature selection. Model transforms are training-only; not a fully blind inductive schema discovery experiment.',representation='Training-only median/onehot/standardization/full PCA<=5; each atomic block unit expected squared norm; concatenate balanced blocks; no coordinates or administrative identifiers',selection='Complete internal OOF MSE; amplitude zero wins ties, then smaller amplitude and grid order. INTERNAL_SELECTOR also chooses block and family internally.',residuals='Original frozen deep C-T3 crossfit caches; no outer or inner held labels in residual-target base models',evaluation='65 original outer folds; random mean of complete OOF repeat metrics; other protocols complete OOF. No GeoC97/41 execution in this first phase.',scope='Exploratory source-block battery, not independent confirmation; no PRED/final138 fit; no climate inputs to correctors; altitude separate sensitivity only',no_new_final_fit=True,no_PRED=True,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in dict.fromkeys(sources)})
    (OUT/'frozen_design.json').write_text(json.dumps(cfg,indent=2,ensure_ascii=False),encoding='utf-8')
    print(pd.DataFrame(exploration).to_string(index=False));print('FROZEN',len(blocks),'atomic blocks;',len(specs)*3+1,'models including internal selector')

if __name__=='__main__':main()
