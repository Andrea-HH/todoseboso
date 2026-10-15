"""Target-free provenance filtering and local complementary representation."""
import re
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

MAY='sat_basic_2025_monthly__sentinel_2__ndvi_promedio__m05'

def exclusion_reasons(records,mode='nonclimatic',extra_copies=()):
    byname={r['column']:r for r in records};memo={};visiting=set()
    def walk(name):
        if name in memo:return memo[name]
        if name not in byname:raise ValueError('Unresolved predictor provenance: '+name)
        if name in visiting:raise ValueError('Cyclic predictor provenance: '+name)
        visiting.add(name);r=byname[name];source=str(r.get('source',''));why=set()
        if source=='external_siap':why.add('SIAP_outcome_context')
        if name.startswith('admin_'):why.add('administrative_code_or_quality')
        if name in ['base_area_delta_ha','base_area_ratio']:why.add('area_quality_metadata')
        if name==MAY or name in extra_copies:why.add('May_NDVI_or_exact_affine_copy')
        if name in ['ID_POLIGONO','RENDIMIENTO_T_HA','CONJUNTO']:why.add('identifier_target_or_split')
        if mode=='nonclimatic' and (source in ['official_climate','external_chirps_daily'] or '__aeti__' in name or re.search(r'(^|__)(climate|chirps|precip|tmax|tmin|tmean|dtr|gdd|vpd|evap|thermal)(_|$)',name)):
            why.add('climate_thermal_or_evapotranspiration')
        for parent in r.get('inputs',[]):why.update(walk(parent))
        visiting.remove(name);memo[name]=why;return why
    for name in byname:walk(name)
    return memo

def fit_representation(frame,columns):
    numeric=frame[columns].replace([np.inf,-np.inf],np.nan)
    usable=[c for c in columns if numeric[c].notna().any() and numeric[c].nunique(dropna=True)>1]
    if len(usable)<20:raise ValueError('Too few varying features for fixed PCA20')
    imputer=SimpleImputer(strategy='median');scale=StandardScaler();pca=PCA(n_components=20,svd_solver='full');score_scale=StandardScaler()
    z=scale.fit_transform(imputer.fit_transform(numeric[usable]));scores=pca.fit_transform(z)
    return score_scale.fit_transform(scores),dict(columns=usable,imputer=imputer,scale=scale,pca=pca,score_scale=score_scale)
