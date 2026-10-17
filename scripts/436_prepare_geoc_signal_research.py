"""Freeze family ablations and definition-selected 12/30-feature representations."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.geoc_bridge import data,GEO,OLD
from src.nonclimatic_local import fit_representation
OUT=ROOT/'outputs/modeling/geoc_signal_research/v1';NC=ROOT/'outputs/modeling/nonclimatic_local/v1';AUDIT=ROOT/'outputs/research/geoc_variable_signal_audit/v1';PREV=ROOT/'outputs/modeling/conditional_local_phases/v1'

def family(name,record):
    source=record.get('source','derived')
    if source=='external_soilgrids':return 'SOIL'
    if source in ['official_topography','external_inegi_cem']:return 'TOPOGRAPHY'
    if source=='official_split+official_parcels+admin':return 'GEOMETRY_COORD'
    if source=='external_wapor':return 'NPP'
    if source in ['sat_basic','sat_pro']:
        token=name.split('__')[2].split('_')[0] if len(name.split('__'))>2 else ''
        period='HISTORY' if 'hist' in name.split('__')[0] else 'CURRENT'
        if token in ['ndvi','evi','lai','fapar','savi','msavi']:return period+'_VIGOR'
        if token in ['msi','ndwi','nddi','emsi','endwi','enddi','dswi1','dswi2','dswi3','dswi4','dswi5']:return period+'_WATER_PROXY'
    return 'OTHER_SAT_DERIVED'

def main():
    if (OUT/'frozen_design.json').exists():raise FileExistsError('Preserve frozen design')
    for p in ['audit','cache','models','checkpoints','tables','diagnostics']:(OUT/p).mkdir(parents=True,exist_ok=True)
    a=data();ids=a['ids197'];frame=pd.read_parquet(AUDIT/'variables_1831_197_sin_target.parquet').set_index('ID_POLIGONO').loc[ids];inventory=pd.read_csv(AUDIT/'inventario_1831_geoc.csv');columns=inventory.feature.tolist();records={};manifests=[]
    for folder in ['features_v1','agronomic_features_v1','empirical_features_v1']:
        p=GEO/'data/processed'/folder/'feature_manifest.json';manifests.append(p);records.update({r['column']:r for r in json.loads(p.read_text(encoding='utf-8'))['features']})
    ancestry={r.feature:json.loads(r.root_inputs) for r in inventory.itertuples()};families={};rows=[]
    for c in columns:
        roots=ancestry[c];groups={family(root,records[root]) for root in roots}
        if any(family(root,records[root])=='CURRENT_VIGOR' and root.endswith(('__m04','__m05','__m06')) for root in roots):groups.add('EARLY_VIGOR_MONTHLY')
        for g in groups:families.setdefault(g,[]).append(c)
        rows.append(dict(feature=c,families=';'.join(sorted(groups)),roots=json.dumps(roots)))
    pd.DataFrame(rows).to_csv(OUT/'audit/family_ancestry.csv',index=False)
    pd.DataFrame([dict(family=g,affected_features=len(cols),root_or_descendant_rule=True) for g,cols in sorted(families.items())]).to_csv(OUT/'audit/family_sizes.csv',index=False)
    variants={};static={};transforms={};pca_info=[]
    old=joblib.load(NC/'cache/representations.joblib');assert old['ids197']==ids;static['FULL']=old['scores']['nonclimatic'];variants['FULL']=dict(type='static',columns=columns)
    with threadpool_limits(limits=1):
        full,model=fit_representation(frame,columns);sign=np.sign((full*static['FULL']).sum(axis=0));parity=float(np.max(abs(full*sign-static['FULL'])));assert parity<1e-10
        for f,drop in sorted(families.items()):
            name='WITHOUT_'+f;keep=[c for c in columns if c not in set(drop)];z,model=fit_representation(frame,keep);variants[name]=dict(type='static',columns=keep,removed_family=f);static[name]=z;transforms[name]=model;pca_info.append(dict(variant=name,input_features=len(keep),explained_X_variance=float(model['pca'].explained_variance_ratio_.sum())))
    static['NEIGHBOR_MEAN']=np.zeros((197,1));variants['NEIGHBOR_MEAN']=dict(type='static',columns=[])
    small=['sat_basic_hist__sentinel_2__ndvi_promedio__mean','sat_basic_hist__sentinel_2__ndvi_promedio__std','sat_basic_hist__sentinel_2__msi_promedio__mean','sat_basic_hist__sentinel_2__msi_promedio__std','emp_shape__y2025_planet_evi__turning_fraction','agro_pheno__y2025_planet_ndvi__jun_to_aug_delta','sat_basic_2025__sentinel_2__ndwi_promedio__mean','sat_basic_2025__sentinel_2__ndwi_promedio__std','soilgrids__clay__depth_weighted_0_30cm','soilgrids__bdod__depth_weighted_0_30cm','soilgrids__soc__depth_weighted_0_30cm','topo_official__slope__mean']
    expanded=small+[f'sat_basic_2025_monthly__sentinel_2__ndvi_promedio__m{m:02d}' for m in [4,6,7,8,9,10]]+['sat_basic_hist__sentinel_2__fapar_promedio__mean','sat_basic_hist__sentinel_2__fapar_promedio__std']+[f'soilgrids__{p}__depth_weighted_0_30cm' for p in ['nitrogen','cec','phh2o','sand','cfvo','silt']]+['topo_official__elevation__mean','topo_official__slope__std','wapor_2025__npp__season_total','wapor_2025__npp__peak_dekad']
    assert len(small)==12 and len(expanded)==30 and set(expanded)<=set(columns)
    bundles={'SMALL12':small,'EXPANDED30':expanded};modes=['raw','pca3','pca5','pca8'];variants['FULL_INDUCTIVE20']=dict(type='inductive_control',columns=columns,mode='pca20')
    for b,cols in bundles.items():
        for mode in modes:variants[b+'_'+mode]=dict(type='small',columns=cols,mode=mode)
    frame.reset_index().to_parquet(OUT/'cache/features197_target_free.parquet',index=False);joblib.dump(dict(static=static,transforms=transforms,ids197=ids),OUT/'cache/static_representations.joblib',compress=3);pd.DataFrame(pca_info).to_csv(OUT/'audit/ablation_X_variance.csv',index=False)
    inventory[inventory.feature.isin(expanded)].to_csv(OUT/'audit/selected_definitions_30.csv',index=False)
    references={}
    for v in static:
        if v=='FULL':continue
        references['A_'+v+'_LOCAL']='FULL_LOCAL';references['A_'+v+'_COMPACT']='LEADER'
    references['A_FULL_INDUCTIVE20_LOCAL']='FULL_LOCAL';references['A_FULL_INDUCTIVE20_COMPACT']='LEADER'
    for b in bundles:
        for mode in modes:references['B_'+b+'_'+mode+'_LOCAL']='FULL_LOCAL';references['B_'+b+'_'+mode+'_COMPACT']='LEADER'
        references['B_'+b+'_SELECTOR']='LEADER';references['C_CORRECT_'+b]='CT3';references['D_GATE_'+b]='P1_GLOBAL';references['E_REDUCED_'+b+'_BOTH']='P1_BOTH';references['E_REDUCED_'+b+'_GLOBAL']='P1_GLOBAL'
    for control in ['STATE','MUNICIPALITY','COORDINATES']:references['C_CORRECT_'+control]='CT3';references['D_GATE_'+control]='P1_GLOBAL'
    files=[Path(__file__),ROOT/'src/geoc_signal_research.py',ROOT/'scripts/437_run_geoc_signal_research.py',ROOT/'tests/test_geoc_signal_research.py',ROOT/'documentation/geoc_signal_research_design.md',AUDIT/'inventario_1831_geoc.csv',AUDIT/'variables_1831_197_sin_target.parquet',NC/'cache/representations.joblib',PREV/'tables/predictions.parquet',PREV/'frozen_design.json',ROOT/'outputs/modeling/geoc_bridge/v1/cache/prepared.joblib',OLD/'cache/execution_plan.joblib',OLD/'cache/frozen65_splits.joblib',OLD/'cache/groups.csv',ROOT/'src/conditional_local_phases.py',ROOT/'src/geoc_reverse.py',ROOT/'src/physical_similarity.py',ROOT/'src/physical_representation.py',ROOT/'outputs/modeling/physical_representation/v1/frozen_design.json',ROOT/'outputs/modeling/physical_representation/v1/cache/features138_target_free.parquet']+manifests+list((OLD/'base_cache').glob('*.joblib'))
    cfg=dict(families=families,bundles=bundles,modes=modes,variants=variants,references=references,recipes=len(references),pca_parity=parity,ablation='Remove every predictor descending from a family, refit PCA20 on197X (legacy matched transductive design); early-vigor overlaps current vigor; not additive attribution. Geographical neighbor selection remains even when coordinate covariates removed.',small_representations='12/30 definitions fixed before outcomes; train-only imputation/scaling/PCA3/5/8 then score standardization; original geographical Ridge24 alpha30; no automatic α search',models='Original EN12 compact grid amplitude0/.25/.5; CT3-corrector Ridge n*alpha1/.1/.01; gateclusters4/8 shrink20; category controls shrink20 and unseen correction0/gate global prior',nested='Reduced expert representations fixed per candidate, EN retuned inside each expert training; full expert OOF and CT3 deep OOF generated strictly in enclosing train. Reuse frozen original expert cache read-only. Same insufficient-group fallback as prior phase, audited.',evaluation='Same65 outer/inner folds, exploratory reused labels, no GeoC97/41, no PRED/final138, no auto Champion. One matched paired reference per recipe, four protocols, Holm across all matched tests; bootstrap5000 clusters.',source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in dict.fromkeys(files)})
    (OUT/'frozen_design.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8');print(pd.read_csv(OUT/'audit/family_sizes.csv').to_string(index=False));print('Frozen recipes:',len(references),'PCA parity',parity)

if __name__=='__main__':main()
