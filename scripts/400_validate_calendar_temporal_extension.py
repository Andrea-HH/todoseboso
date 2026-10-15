"""Check new trimester/season data independently from model fitting."""
from pathlib import Path
import json,calendar
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/processed/agronomic_calendar_set'
OUT=ROOT/'outputs/research/agronomic_calendar_temporal_validation/v1'
if (OUT/'summary.csv').exists():raise FileExistsError('Preserve validation')
OUT.mkdir(parents=True,exist_ok=True)
monthly=pd.read_parquet(BASE/'v1/monthly_inputs_apr_oct.parquet')
panel=pd.read_parquet(BASE/'v2_temporal_extension/annual_features.parquet')
wide=pd.read_parquet(BASE/'v2_temporal_extension/current_history_delta.parquet').set_index('ID_POLIGONO')
d=pd.read_csv(BASE/'v2_temporal_extension/dictionary.csv');checks=[]
assert len(panel)==788 and not panel.duplicated(['ID_POLIGONO','year']).any() and len(wide)==197 and len(d)==24
for r in d.itertuples():
    months=json.loads(r.months);g=monthly[monthly.month.isin(months)].copy()
    g['value']=g[r.source]
    if r.formula=='day-weighted mean':
        g['days']=[calendar.monthrange(int(y),int(m))[1] for y,m in zip(g.year,g.month)];g['value']*=g.days
    stat=g.groupby(['ID_POLIGONO','year']).agg(total=('value','sum'),n=('value','count'))
    if r.formula=='sum':expected=stat.total
    elif r.formula=='day-weighted mean':expected=stat.total/g.groupby(['ID_POLIGONO','year']).days.sum()
    else:expected=stat.total/len(months)
    expected=expected.where(stat.n.eq(len(months)))
    actual=panel.set_index(['ID_POLIGONO','year'])[r.feature].reindex(expected.index)
    checks.append(dict(feature=r.feature,check='monthly_reconstruction',passed=bool(np.allclose(actual,expected,equal_nan=True))))
    a=panel.pivot(index='ID_POLIGONO',columns='year',values=r.feature);h=a[[2022,2023,2024]];mean=h.mean(axis=1).where(h.count(axis=1).eq(3));sd=h.std(axis=1,ddof=1).where(mean.notna())
    for prefix,value in [('CURRENT_',a[2025]),('HIST_MEAN_',mean),('HIST_SD_',sd),('DELTA_',a[2025]-mean)]:
        checks.append(dict(feature=r.feature,check=prefix+'reconstruction',passed=bool(np.allclose(value,wide.loc[value.index,prefix+r.feature],equal_nan=True))))
assert all(r['passed'] for r in checks)
pd.DataFrame(checks).to_csv(OUT/'checks.csv',index=False)
pd.DataFrame(dict(rows=788,parcels=197,years=4,features=24,wide_features=96,checks=len(checks),passed=sum(c['passed'] for c in checks)),index=[0]).to_csv(OUT/'summary.csv',index=False)
counts=pd.read_csv(BASE/'v2_temporal_extension/historical_counts.csv');counts=counts.rename(columns={c:c.replace('CAL_','CALX_',1) for c in counts if c.startswith('CAL_')});counts.to_csv(OUT/'historical_counts_with_CALX_names.csv',index=False)
print('PASSED',len(checks),'independent checks. No targets/models used.')
