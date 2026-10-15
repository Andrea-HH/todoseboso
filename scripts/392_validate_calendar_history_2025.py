"""Independent reconstruction and descriptive annual shift, without targets."""
from pathlib import Path
import json,hashlib,calendar
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/processed/agronomic_calendar_set/v1'
OUT=ROOT/'outputs/research/agronomic_calendar_validation/v1'
if OUT.exists():raise FileExistsError('Preserve completed audit')
OUT.mkdir(parents=True)
panel=pd.read_parquet(BASE/'annual_features_2022_2025.parquet')
wide=pd.read_parquet(BASE/'current_history_delta_197_target_free.parquet').set_index('ID_POLIGONO')
meta=pd.read_parquet(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet',columns=['ID_POLIGONO','climate_profile','Estado','Municipio'])
monthly=pd.read_parquet(BASE/'monthly_inputs_apr_oct.parquet')
dictionary=pd.read_csv(BASE/'annual_feature_dictionary.csv')
checks=[]
for row in dictionary.itertuples():
    if row.window not in ['pre_apr','sowing_may_jun','post_jul_aug','late_sep_oct']:continue
    months=json.loads(row.months)
    m=monthly[monthly.month.isin(months)].copy()
    expected=[]
    for (pid,year),g in m.groupby(['ID_POLIGONO','year']):
        vals=g.set_index('month')[row.variable].reindex(months)
        if vals.notna().all():
            value=vals.sum() if row.variable=='precip_mean' else (np.average(vals,weights=[calendar.monthrange(int(year),a)[1] for a in months]) if row.block=='climate' else vals.mean())
        else:value=np.nan
        expected.append((pid,year,value))
    ref=pd.DataFrame(expected,columns=['ID_POLIGONO','year','expected']).merge(panel[['ID_POLIGONO','year',row.feature]],on=['ID_POLIGONO','year'],validate='one_to_one')
    checks.append(dict(check='independent_monthly_reconstruction',feature=row.feature,pass_check=bool(np.allclose(ref.expected,ref[row.feature],equal_nan=True))))
features=dictionary.feature.tolist()
for f in features:
    a=panel.pivot(index='ID_POLIGONO',columns='year',values=f)
    mean=a[[2022,2023,2024]].mean(axis=1).where(a[[2022,2023,2024]].count(axis=1).eq(3))
    for prefix,value in [('HIST_MEAN_',mean),('HIST_SD_',a[[2022,2023,2024]].std(axis=1,ddof=1).where(mean.notna())),('CURRENT_',a[2025]),('DELTA_',a[2025]-mean)]:
        checks.append(dict(check=prefix+'reconstruction',feature=f,pass_check=bool(np.allclose(value,wide.loc[value.index,prefix+f],equal_nan=True))))
assert all(r['pass_check'] for r in checks)
pd.DataFrame(checks).to_csv(OUT/'reconstruction_checks.csv',index=False)
train=panel.merge(meta,on='ID_POLIGONO',how='inner',validate='many_to_one')
support=pd.read_parquet(BASE/'satellite_support.parquet')
rows=[];regional=[];placebo=[];pairs=[]
for f in features:
    a=train.pivot(index='ID_POLIGONO',columns='year',values=f).dropna()
    hist=a[[2022,2023,2024]];delta=a[2025]-hist.mean(axis=1)
    joined=meta.set_index('ID_POLIGONO').join(pd.DataFrame({'delta':delta,'current':a[2025],'historical':hist.mean(axis=1),'above':a[2025]>hist.max(axis=1),'below':a[2025]<hist.min(axis=1)}),how='inner')
    q=support[support.feature.eq(f)]
    matched=[]
    if 'min_observations_per_month' in q and len(q):
        quality=q.pivot(index='ID_POLIGONO',columns='year',values='min_observations_per_month').reindex(a.index)
        matched=quality.index[(quality[[2022,2023,2024,2025]]>=2).all(axis=1)].tolist()
    row=dict(feature=f,n_complete_four_years=len(a),median_2025=a[2025].median(),median_history_mean=hist.mean(axis=1).median(),median_paired_delta=delta.median(),fraction_above_history=(a[2025]>hist.max(axis=1)).mean(),fraction_below_history=(a[2025]<hist.min(axis=1)).mean(),fraction_outside_history=((a[2025]>hist.max(axis=1))|(a[2025]<hist.min(axis=1))).mean(),equal_profile_mean_delta=joined.groupby('climate_profile').delta.mean().mean(),quality_matched_n=len(matched),quality_matched_median_delta=delta.reindex(matched).median() if matched else np.nan)
    rows.append(row)
    for state,g in joined.groupby('Estado'):
        regional.append(dict(feature=f,Estado=state,n=len(g),median_delta=g.delta.median(),mean_delta=g.delta.mean(),fraction_above=g.above.mean(),fraction_below=g.below.mean()))
    for year in [2022,2023,2024,2025]:
        other=a.drop(columns=year)
        placebo.append(dict(feature=f,year=year,n=len(a),median_delta_vs_other_three=(a[year]-other.mean(axis=1)).median(),fraction_outside_other_three=((a[year]>other.max(axis=1))|(a[year]<other.min(axis=1))).mean()))
    v=joined.groupby('climate_profile').agg(n=('delta','size'),delta_std=('delta','std'),current_std=('current','std'))
    pairs.append(dict(feature=f,repeated_profiles=int(v.n.ge(2).sum()),profiles_with_different_delta=int(((v.n>=2)&(v.delta_std>1e-10)).sum()),median_within_profile_delta_sd=v.loc[v.n>=2,'delta_std'].median()))
pd.DataFrame(rows).to_csv(OUT/'annual_shift_2025.csv',index=False)
pd.DataFrame(regional).to_csv(OUT/'annual_shift_by_state.csv',index=False)
pd.DataFrame(placebo).to_csv(OUT/'leave_one_year_out_descriptive.csv',index=False)
pd.DataFrame(pairs).to_csv(OUT/'anomaly_intraprofile_support.csv',index=False)
domains=[]
for f in features:
    vals=panel[f].dropna();rule=None
    if f.startswith('CAL_S2_ndvi_') and not any(x in f for x in ['spatial','change','peak','range']):rule=bool(vals.between(-1,1).all())
    if 'spatial_std' in f or 'seasonal_range' in f or '_CLIM_precip_' in f:rule=bool((vals>=0).all())
    if rule is not None:domains.append(dict(feature=f,valid_domain=rule,min=float(vals.min()),max=float(vals.max())))
pd.DataFrame(domains).to_csv(OUT/'domain_checks.csv',index=False)
summary=dict(reconstruction_checks=len(checks),checks_passed=sum(r['pass_check'] for r in checks),domain_checks_passed=all(d['valid_domain'] for d in domains),train_n=138,targets_read=False,model_fits=0,pred_inference=0,important='Outside 3 historical values has baseline probability 50% for an exchangeable continuous fourth observation; not a statistical rarity test. LOO-year tables are descriptive and not forecasting validations.')
(OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
print(pd.DataFrame(rows).loc[lambda d:d.feature.str.contains('ndvi_sowing|ndvi_post|ndvi_late|precip_sowing|tmax_sowing|tmax_post|ndvi_peak')].to_string(index=False))
