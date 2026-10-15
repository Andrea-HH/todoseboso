"""Descriptive predictor overlap, no predictive model selection or fits."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/modeling/agronomic_calendar/expansion/v1'
OUT=ROOT/'outputs/research/calendar_core_variable_overlap/v1'

def main():
    if OUT.exists():raise FileExistsError('Preserve previous analysis')
    OUT.mkdir(parents=True)
    spec=json.loads((BASE/'frozen_design.json').read_text())['specs']
    core=spec['CAL00']['columns'];cal=spec['CAL02']['columns'];cols=list(dict.fromkeys(core+cal))
    x=pd.read_parquet(BASE/'cache/features_train138.parquet')[['ID_POLIGONO']+cols]
    t=pd.read_parquet(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet')
    z=x.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile','RENDIMIENTO_T_HA']],on='ID_POLIGONO',validate='one_to_one')
    assert len(z)==138 and not z[cols].isna().any().any()
    z.to_csv(OUT/'train138_variables.csv',index=False)
    z[cols].describe().T.to_csv(OUT/'ranges.csv')
    # Equal-profile weighting uses one mean per archived climate profile;
    # compare with one vote per parcel, not an additional independent sample.
    profile=z.groupby('climate_profile')[cols+['RENDIMIENTO_T_HA']].mean()
    for name,frame in [('parcel',z),('equal_profile',profile)]:
        for method in ['pearson','spearman']:
            frame[cols].corr(method=method).to_csv(OUT/f'{name}_{method}.csv')
        rows=[]
        for c in cols:
            rows.append(dict(feature=c,pearson_target=frame[c].corr(frame.RENDIMIENTO_T_HA),spearman_target=frame[c].corr(frame.RENDIMIENTO_T_HA,method='spearman')))
        pd.DataFrame(rows).to_csv(OUT/f'{name}_target_associations.csv',index=False)
    z.groupby('Estado')[cols].agg(['mean','min','max']).to_csv(OUT/'state_ranges.csv')
    within=[]
    for c in cols:
        groups=[g[c] for _,g in z.groupby('climate_profile') if len(g)>1]
        within.append(dict(feature=c,repeated_profiles=len(groups),varying_profiles=sum(np.ptp(v)>1e-10 for v in groups),unique_values=z[c].nunique()))
    pd.DataFrame(within).to_csv(OUT/'within_profile_variation.csv',index=False)
    rain=cal[:4]
    total=z[rain].sum(axis=1)
    early=(z[rain[0]]+z[rain[1]])/(total+1e-6)
    checks=dict(n=138,archived_profiles=z.climate_profile.nunique(),unique_climate_vectors=z[cols[0:3]+cal[:8]].drop_duplicates().shape[0],union_variables=len(cols),shared_variables=sorted(set(core)&set(cal)),total_max_difference=float(abs(total-z.compact_precip_total).max()),early_fraction_max_difference=float(abs(early-z.compact_early_fraction).max()))
    a=z[cols].to_numpy();a=(a-a.mean(axis=0))/a.std(axis=0)
    checks['standardized_matrix_rank']=int(np.linalg.matrix_rank(a))
    checks['standardized_singular_values']=np.linalg.svd(a,compute_uv=False).tolist()
    checks['source_sha256']=hashlib.sha256((BASE/'cache/features_train138.parquet').read_bytes()).hexdigest()
    (OUT/'audit.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    sel=pd.read_csv(BASE/'diagnostics/feature_selection_stability.csv')
    sel[(sel.experiment=='EN_CAL02')].to_csv(OUT/'existing_EN_CAL02_selection.csv',index=False)
    print(json.dumps(checks,indent=2))
    print(pd.read_csv(OUT/'parcel_target_associations.csv').to_string(index=False))
    print(pd.read_csv(OUT/'within_profile_variation.csv').to_string(index=False))
    print(sel[(sel.experiment=='EN_CAL02')&(sel.protocol=='random')][['feature','fraction_selected','median_effect']].to_string(index=False))

if __name__=='__main__':main()
