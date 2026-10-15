"""Build historical/current calendar set without reading yields or fitting models."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.agronomic_calendar_features import WINDOWS,SAT,build_year,history_representation

OUT=ROOT/'outputs/research/agronomic_calendar_set/v1'
DATA=ROOT/'data/processed/agronomic_calendar_set/v1'
if (OUT/'manifest.json').exists() or DATA.exists():raise FileExistsError('Preserve existing completed versions')
OUT.mkdir(parents=True,exist_ok=True)
satpath=ROOT/'data/processed/family_1/timeseries/sentinel_timeseries.parquet'
climpath=ROOT/'data/processed/family_1/environment/climate_monthly_timeseries.parquet'
metapath=ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet'
ids=pd.read_parquet(ROOT/'data/processed/family_1/environment/topography_by_parcel.parquet',columns=['ID_POLIGONO']).sort_values('ID_POLIGONO')
train=pd.read_parquet(metapath,columns=['ID_POLIGONO','climate_profile','Estado','Municipio'])
sources=[satpath,climpath,*sorted((ROOT/'docs/resources/firadocs').glob('*.pdf'))]
hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
design=dict(years=[2022,2023,2024,2025],history_years=[2022,2023,2024],windows=WINDOWS,satellite_variables=SAT,
    cutoff='October 31 of each year',spatial_assignment='same calendar for all parcels; no state lookup or productivity class assignment',
    rationale='April preparation/seed treatment; May-June sowing in FIRA reports; later bins are calendar intervals, not confirmed phenology',
    aggregation='monthly medians then equal-month means for Sentinel; sums for precipitation; day-weighted temperatures',
    quality='finite canonical observations, no new cloud threshold, no interpolation or imputation; require every month in each window; peak requires >=4 May-Oct months',
    historical_support='exactly three available annual values for historical mean/sample SD/delta',
    decision='representation construction only; no target-based screening, no fit, no model selection with PRED',
    caveats=['Historical land cover/crop/management may differ from barley2025.','Report calendars are hypotheses, not observed parcel sowing/harvest.','Late Sep-Oct is not complete harvest for October-December calendars.','Monthly climate cannot resolve daily extremes, true degree-days or dry spells.'],sha256=hashes)
(OUT/'frozen_design.json').write_text(json.dumps(design,ensure_ascii=False,indent=2),encoding='utf-8')
s=pd.read_parquet(satpath,columns=['ID_POLIGONO','fecha_captura','year','month','cloud_raw',*SAT.values()])
c=pd.read_parquet(climpath,columns=['ID_POLIGONO','year','month','precip_mean','tmax_mean','tmin_mean'])
panels=[];supports=[]
for year in design['years']:
    p,q,d=build_year(s,c,ids.ID_POLIGONO,year);panels.append(p);supports.append(q)
panel=pd.concat(panels,ignore_index=True);support=pd.concat(supports,ignore_index=True)
wide,hcount=history_representation(panel)
assert len(ids)==197 and ids.ID_POLIGONO.is_unique and len(panel)==788 and len(wide)==197
assert not panel.duplicated(['ID_POLIGONO','year']).any()
assert len(train)==138 and not any('rendimiento' in col.lower() for col in panel)
assert np.isfinite(panel.filter(like='CAL_').to_numpy()).sum()>0
DATA.mkdir(parents=True)
panel.to_parquet(DATA/'annual_features_2022_2025.parquet',index=False)
wide.to_parquet(DATA/'current_history_delta_197_target_free.parquet',index=False)
wide.to_csv(DATA/'current_history_delta_197_target_free.csv',index=False)
support.to_parquet(DATA/'satellite_support.parquet',index=False)
hcount.to_csv(DATA/'historical_valid_year_counts.csv',index=False)
d.to_csv(DATA/'annual_feature_dictionary.csv',index=False)
dictionary=[]
for prefix,desc in [('CURRENT_','2025 value'),('HIST_MEAN_','mean annual features2022-2024; require3'),('HIST_SD_','sample SD annual features2022-2024; require3'),('DELTA_','2025 minus mean2022-2024; require3')]:
    for r in d.to_dict('records'):
        r['annual_feature']=r['feature'];r['feature']=prefix+r['feature'];r['representation']=desc
        r['not_independent']='CURRENT = HIST_MEAN + DELTA; do not automatically use all three together'
        dictionary.append(r)
pd.DataFrame(dictionary).to_csv(DATA/'representation_dictionary.csv',index=False)
# Monthly panel retained for reproducibility; no new pixel processing or target joins.
monthly=s.loc[s.month.between(4,10)].groupby(['ID_POLIGONO','year','month'])[list(SAT.values())].median().reset_index()
monthly.merge(c,on=['ID_POLIGONO','year','month'],validate='one_to_one').to_parquet(DATA/'monthly_inputs_apr_oct.parquet',index=False)
current=wide.merge(train,on='ID_POLIGONO',how='inner',validate='one_to_one')
audit=[]
for feature in wide.columns[1:]:
    g=current.groupby('climate_profile')[feature]
    sizes=current.groupby('climate_profile').size();eligible=sizes[sizes>=2].index
    count=g.count().reindex(eligible);var=g.nunique().reindex(eligible)
    supported=(count>=2);ranges=g.max()-g.min()
    audit.append(dict(feature=feature,missing_train_fraction=float(current[feature].isna().mean()),n_unique_train=current[feature].nunique(),profiles_with_2_valid=int(supported.sum()),profiles_with_variation=int((var[supported]>=2).sum()),fraction_supported_profiles_vary=float((var[supported]>=2).mean()) if supported.any() else np.nan,median_within_profile_range=float(ranges.reindex(eligible[supported]).median())))
pd.DataFrame(audit).to_csv(OUT/'train_feature_support_and_intraprofile_variation.csv',index=False)
coverage=panel.merge(train,on='ID_POLIGONO',how='inner',validate='many_to_one').groupby('year')[d.feature.tolist()].agg(lambda a:a.notna().mean()).T
coverage.to_csv(OUT/'train_annual_coverage.csv')
# Compare with pre-existing representations to expose redundancy, without selecting by Y.
oldpath=ROOT/'data/processed/family_1/features/family1_features_all.parquet'
if oldpath.exists():
    old=pd.read_parquet(oldpath).set_index('ID_POLIGONO').reindex(current.ID_POLIGONO)
    old=old.select_dtypes(include='number').replace([np.inf,-np.inf],np.nan)
    matches=[]
    for feature in [col for col in wide if col.startswith('CURRENT_')]:
        x=current.set_index('ID_POLIGONO')[feature];scores=old.corrwith(x).abs().dropna().sort_values(ascending=False)
        if len(scores):matches.append(dict(feature=feature,closest_existing_feature=scores.index[0],absolute_pearson_train=float(scores.iloc[0])))
    pd.DataFrame(matches).to_csv(OUT/'nearest_existing_representation.csv',index=False)
manifest=dict(rows_annual=len(panel),rows_wide=len(wide),annual_features=len(d),representation_features=len(wide.columns)-1,train_rows=len(current),train_profiles=train.climate_profile.nunique(),target_read=False,model_fits=0,pred_inference=0,sha256=hashes,
    annual_median_feature_coverage_train={str(y):float(coverage[y].median()) for y in coverage},
    all_missing_train_features=[r['feature'] for r in audit if r['n_unique_train']==0])
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in manifest.items() if k!='sha256'},indent=2))
