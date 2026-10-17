"""Descriptive target/predictor outlier census for AGC_171/015, without model selection."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('runner446',ROOT/'scripts/446_run_joint_simplification.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
OUT=ROOT/'outputs/research/case_outliers_and_model_residual_comparison/v1';CASES=['AGC_171','AGC_015']


def describe(value,reference):
    x=np.asarray(reference,float);x=x[np.isfinite(x)];n=len(x)
    if not np.isfinite(value) or not n:return dict(n_valid=n,value=float(value),status='missing',flag_iqr=False,flag_outer3=False,flag_robust_z=False)
    q1,med,q3=np.quantile(x,[.25,.5,.75]);iqr=q3-q1;mad=float(np.median(abs(x-med)));continuous=n>=12 and len(np.unique(np.round(x,10)))>=5 and iqr>1e-10;lo=q1-1.5*iqr;hi=q3+1.5*iqr;z=.67448975*(value-med)/mad if mad>1e-10 else np.nan
    return dict(n_valid=n,n_distinct=len(np.unique(x)),value=float(value),minimum=float(x.min()),q25=float(q1),median=float(med),q75=float(q3),maximum=float(x.max()),iqr=float(iqr),lower_fence=float(lo),upper_fence=float(hi),robust_z=float(z),percentile_midrank=float(100*(np.sum(x<value-1e-12)+.5*np.sum(np.isclose(x,value,rtol=0,atol=1e-12)))/n),level_frequency=float(np.mean(np.isclose(x,value,rtol=0,atol=1e-12))),flag_iqr=bool(continuous and (value<lo-1e-10 or value>hi+1e-10)),flag_outer3=bool(continuous and (value<q1-3*iqr-1e-10 or value>q3+3*iqr+1e-10)),flag_robust_z=bool(continuous and abs(z)>3.5),direction='low' if value<lo-1e-10 else ('high' if value>hi+1e-10 else 'within'),status='continuous' if continuous else ('constant_or_degenerate' if iqr<=1e-10 else 'discrete_or_small_support'))


def main():
    if (OUT/'case_audit_manifest.json').exists():raise FileExistsError('Preserve case audit')
    for p in [OUT,OUT/'tables',OUT/'audit',OUT/'figures']:p.mkdir(parents=True,exist_ok=True)
    a=runner.load_assets();t=a['a']['train'].set_index('ID_POLIGONO');ids=t.index.tolist();ownpath=ROOT/'outputs/modeling/experimental_pls1867/v1/cache/train138_1867.parquet';own=pd.read_parquet(ownpath).set_index('ID_POLIGONO').loc[ids];geopath=ROOT/'outputs/research/geoc_variable_signal_audit/v1/variables_1831_197_sin_target.parquet';geo=pd.read_parquet(geopath).set_index('ID_POLIGONO').loc[ids];meta=pd.read_csv(ROOT/'outputs/research/geoc_variable_signal_audit/v1/inventario_1831_geoc.csv').set_index('feature');master=pd.read_csv(ROOT/'outputs/research/variable_inventory/v1/inventario_1557.csv').set_index('variable');extra=pd.read_csv(ROOT/'outputs/research/experimental_variable_inventory/v1/variables_adicionales.csv').set_index('variable');role=a['role_frame'].set_index('ID_POLIGONO') if 'ID_POLIGONO' in a['role_frame'] else a['role_frame'].set_axis(ids);parts=[('OWN1867',own),('GEOC1831',geo),('MODEL',role[list(a['core'])+a['variants']['DROP_JOINT']['columns']+sum([a['physical_definitions'][k]['columns'] for k in ['soil_texture_phase','geologic_composition','geologic_distances']],[])+['base_centroid_lat','base_centroid_lon']])];records=[];categorical=[]
    for case in CASES:
        scopes={'TRAIN138':ids,'state':t.index[t.Estado==t.loc[case,'Estado']].tolist(),'municipality':t.index[t.Municipio==t.loc[case,'Municipio']].tolist(),'climate_profile':t.index[t.climate_profile==t.loc[case,'climate_profile']].tolist()}
        for scope,index in scopes.items():
            records.append(dict(case=case,scope=scope,cohort=str(t.loc[case,{'TRAIN138':'Estado','state':'Estado','municipality':'Municipio','climate_profile':'climate_profile'}[scope]]) if scope!='TRAIN138' else 'all known labels',source='TARGET',feature='RENDIMIENTO_T_HA',quality_field=False,used_in_J7=False,description='Observed yield t/ha; diagnostic only',**describe(t.loc[case,'RENDIMIENTO_T_HA'],t.loc[index,'RENDIMIENTO_T_HA'])))
            for source,frame in parts:
                for feature in frame:
                    s=frame[feature];value=s.loc[case];description='';family=''
                    if source=='GEOC1831' and feature in meta.index:description=str(meta.loc[feature,'description']);family=str(meta.loc[feature,'family'])
                    elif source=='OWN1867' and feature in master.index:description=str(master.loc[feature,'descripcion_documentada']);family=str(master.loc[feature,'fuente'])
                    elif source=='OWN1867' and feature in extra.index:description=str(extra.loc[feature,'definicion_documentada']);family=str(extra.loc[feature,'grupo'])
                    quality=any(v in feature.lower() for v in ['n_obs','valid_count','coverage','missing','support','n_years','key_found']);base=dict(case=case,scope=scope,source=source,feature=feature,family=family,quality_field=quality,used_in_J7=feature in parts[-1][1].columns,description=description)
                    if pd.api.types.is_numeric_dtype(s) or pd.api.types.is_bool_dtype(s):records.append(dict(**base,**describe(float(value) if pd.notna(value) else np.nan,s.loc[index].to_numpy(float))))
                    else:
                        ref=s.loc[index].dropna().astype(str);categorical.append(dict(**base,value=str(value),n_valid=len(ref),n_distinct=ref.nunique(),level_frequency=float(np.mean(ref==str(value))) if len(ref) else np.nan))
    result=pd.DataFrame(records);result.to_parquet(OUT/'tables/outliers_all_numeric.parquet',index=False);result.to_csv(OUT/'tables/outliers_all_numeric.csv',index=False);result[result.source=='TARGET'].to_csv(OUT/'tables/target_outliers_by_scope.csv',index=False);result[result.source=='MODEL'].to_csv(OUT/'tables/model_input_outliers_by_scope.csv',index=False);result[result.flag_iqr|result.flag_robust_z].to_csv(OUT/'tables/flagged_predictors.csv',index=False);pd.DataFrame(categorical).to_csv(OUT/'tables/categorical_levels.csv',index=False)
    # Raw named descriptors are correlated/aliased; census counts are not independent tests.
    result.groupby(['case','scope','source']).agg(n_numeric=('feature','size'),iqr_flags=('flag_iqr','sum'),outer3_flags=('flag_outer3','sum'),robust_flags=('flag_robust_z','sum'),missing=('status',lambda s:(s=='missing').sum())).reset_index().to_csv(OUT/'tables/outlier_counts.csv',index=False)
    # Multivariate rank of leave-one-out 5NN distances in train/cohort-standardized core4 and local7.
    multivariate=[];neighbors=[];full=role
    for case in CASES:
        scopes={'TRAIN138':ids,'municipality':t.index[t.Municipio==t.loc[case,'Municipio']].tolist(),'climate_profile':t.index[t.climate_profile==t.loc[case,'climate_profile']].tolist()}
        for scope,index in scopes.items():
            for label,cols in [('core4',list(a['core'])),('local7',a['variants']['DROP_JOINT']['columns']),('core4_plus_local7',list(a['core'])+a['variants']['DROP_JOINT']['columns'])]:
                x=full.loc[index,cols].to_numpy(float);med=np.nanmedian(x,axis=0);x=np.where(np.isfinite(x),x,med);sd=x.std(axis=0);support=sd>1e-10;z=(x[:,support]-med[support])/sd[support];distance=cdist(z,z);np.fill_diagonal(distance,np.inf);k=min(5,len(index)-1);radius=np.sort(distance,axis=1)[:,:k].mean(axis=1);j=index.index(case);rank=100*(np.sum(radius<radius[j])+.5*np.sum(np.isclose(radius,radius[j],rtol=0,atol=1e-10)))/len(radius);multivariate.append(dict(case=case,scope=scope,representation=label,n=len(index),active_dimensions=int(support.sum()),mean_5nn_distance=float(radius[j]),percentile_5nn_distance=float(rank)))
                for h in np.argsort(distance[j])[:5]:neighbors.append(dict(case=case,scope=scope,representation=label,neighbor_ID=index[h],distance=float(distance[j,h]),neighbor_yield=float(t.loc[index[h],'RENDIMIENTO_T_HA']),neighbor_municipality=t.loc[index[h],'Municipio'],neighbor_profile=t.loc[index[h],'climate_profile']))
    pd.DataFrame(multivariate).to_csv(OUT/'tables/multivariate_case_ranks.csv',index=False);pd.DataFrame(neighbors).to_csv(OUT/'tables/case_nearest_feature_neighbors.csv',index=False)
    sources=[ownpath,geopath,ROOT/'outputs/modeling/geoc_bridge/v1/cache/prepared.joblib',ROOT/'outputs/research/geoc_variable_signal_audit/v1/inventario_1831_geoc.csv',ROOT/'outputs/research/variable_inventory/v1/inventario_1557.csv',ROOT/'outputs/research/experimental_variable_inventory/v1/variables_adicionales.csv',Path(__file__)];(OUT/'case_audit_manifest.json').write_text(json.dumps(dict(status='complete',cases=CASES,n_own_features=len(own.columns),n_geoc_features=len(geo.columns),numeric_comparisons=len(result),minimum_continuous_cohort=12,minimum_distinct=5,rules='Tukey1.5IQR, outer3IQR, robust abs(z)>3.5; degeneracy/discrete levels separated; cohorts include focal case; descriptive only',no_model_selection=True,no_PRED=True,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}),indent=2),encoding='utf-8');print(result[result.source=='TARGET'][['case','scope','n_valid','value','q25','q75','lower_fence','flag_iqr','flag_outer3','robust_z']].to_string(index=False));print(pd.DataFrame(multivariate).round(3).to_string(index=False))


if __name__=='__main__':main()
