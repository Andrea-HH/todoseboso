"""Constructores de bloques de features de Familia 1 (sin rendimiento)."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

from .temporal_primitives import CORE, EXTENDED, extract_temporal_features, select_features

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data/processed/family_1'; OUT=DATA/'features'; AUD=ROOT/'outputs/data_audit/family_1/features'
OUT.mkdir(parents=True,exist_ok=True); AUD.mkdir(parents=True,exist_ok=True)
ID='ID_POLIGONO'; START=pd.Timestamp('2025-04-01'); END=pd.Timestamp('2025-10-31')
PRIMARY=['ndvi','evi','lai','fapar','savi','ndwi','msi','nddi']

def parcels():
    p=pd.read_parquet(DATA/'environment/topography_by_parcel.parquet')
    return p[[ID]].sort_values(ID).reset_index(drop=True)

def meta(name,source,sensor,variable,statistic,window,family,level,description):
    return dict(feature_name=name,source=source,sensor=sensor,variable=variable,statistic=statistic,
                window=window,feature_family=family,core_or_extended=level,description=description)

def _temporal_table(df, variables, prefix, level='core', family='TEMPORAL', compact=False):
    rows=[]; md=[]
    stats=(['n_obs','mean','median','std','min','max','q25','q75','normalized_auc','slope','peak_value','peak_day',
            'first','last','last_minus_first','max_growth_rate','max_decline_rate','peak_drop','max_drawdown','max_runup']
           if level=='core' else ['q10','q90','iqr','skewness','kurtosis','pre_peak_slope','post_peak_slope',
             'cumulative_positive_change','cumulative_negative_change','total_variation','drawdown_start_day',
             'drawdown_end_day','drawdown_duration','runup_start_day','runup_end_day','runup_duration'])
    if compact: stats=['n_obs','mean','max','normalized_auc','slope','last_minus_first','max_growth_rate','max_decline_rate']
    for pid,g in df.groupby(ID,sort=True):
        r={ID:pid}
        for var in variables:
            vals=extract_temporal_features(g['fecha_captura'],g[var])
            for st in stats:
                name=f'{prefix}{var}_{st}'; r[name]=vals.get(st,np.nan)
                md.append(meta(name,prefix.rstrip('_'),prefix.rstrip('_'),var,st,'2025-04-01/2025-10-31',family,level.upper(),
                               'Primitiva temporal con fechas reales; días medidos desde 2025-04-01.'))
        rows.append(r)
    return parcels().merge(pd.DataFrame(rows),on=ID,how='left'),pd.DataFrame(md).drop_duplicates('feature_name')

def _write(table, filename, md):
    assert len(table)==197 and table[ID].is_unique and 'rendimiento' not in ' '.join(table.columns).lower()
    table.to_parquet(OUT/filename,index=False); md.to_csv(OUT/(filename.replace('.parquet','_dictionary.csv')),index=False)

def build_sentinel():
    d=pd.read_parquet(DATA/'timeseries/sentinel_timeseries.parquet'); d=d[d.fecha_captura.between(START,END)].copy()
    # CV seguro: se recalcula y se enmascara si |promedio| < 0.05.
    bases=sorted({c[:-9] for c in d if c.endswith('_promedio')})
    for b in bases:
        d[f'{b}_derived_cv']=d[f'{b}_std']/d[f'{b}_promedio'].abs().where(d[f'{b}_promedio'].abs()>=.05)
    primary=[f'{b}_promedio' for b in PRIMARY if f'{b}_promedio' in d]
    other=[c for c in d if c.endswith('_promedio') and c not in primary]
    # Control dimensional: heterogeneidad detallada sólo para los ocho índices
    # agronómicos prioritarios; los otros índices conservan su trayectoria media.
    hetero=[c for c in d if c.split('_')[0] in PRIMARY and c.endswith(('_std','_derived_range','_derived_lower_gap','_derived_upper_gap','_derived_cv'))]
    a,ma=_temporal_table(d,primary,'S2_', 'core','S2_LEVEL_SHAPE')
    b,mb=_temporal_table(d,other+hetero,'S2_', 'core','S2_HETEROGENEITY',compact=True)
    core=a.merge(b,on=ID,how='left',validate='one_to_one')
    ext,me=_temporal_table(d,primary,'S2_', 'extended','S2_LEVEL_SHAPE')
    ext2,me2=_temporal_table(d,[c for c in d if c.endswith(('_min','_max')) and c.split('_')[0] in PRIMARY],
                             'S2_','extended','S2_SPATIAL_EXTREMA',compact=True)
    ext=ext.merge(ext2,on=ID,how='left',validate='one_to_one')
    _write(core,'sentinel_features_core.parquet',pd.concat([ma,mb])); _write(ext,'sentinel_features_extended.parquet',pd.concat([me,me2]))

def build_landsat():
    d=pd.read_parquet(DATA/'timeseries/landsat_timeseries.parquet'); d=d[d.fecha_captura.between(START,END)]
    t,m=_temporal_table(d,['vi6t_promedio'],'LANDSAT_','core','LANDSAT_IRREGULAR')
    cov=[]
    for pid,g in d.groupby(ID):
        dates=g.loc[g.vi6t_promedio.notna(),'fecha_captura'].sort_values(); gaps=dates.diff().dt.days.dropna()
        cov.append({ID:pid,'LANDSAT_valid_observation_count':len(dates),'LANDSAT_valid_fraction':len(dates)/max(g.fecha_captura.nunique(),1),
                    'LANDSAT_median_gap':gaps.median(),'LANDSAT_max_gap':gaps.max()})
    t=t.merge(pd.DataFrame(cov),on=ID,how='left')
    for c in t.columns[1:]:
        if c not in set(m.feature_name): m.loc[len(m)]=meta(c,'LANDSAT','LANDSAT','VI6T',c.split('_')[-1],'2025-04-01/2025-10-31','COVERAGE','CORE','Cobertura temporal irregular sin interpolación.')
    _write(t,'landsat_features.parquet',m)

def build_planet():
    d=pd.read_parquet(DATA/'timeseries/planet_timeseries.parquet'); d=d[d.fecha_captura.between(START,END)]
    variables=[c for c in d if c.endswith(('_promedio','_std','_derived_range'))]
    a,ma=_temporal_table(d,variables,'PLANET_','core','PLANET_TEMPORAL')
    b,mb=_temporal_table(d,[c for c in d if c.endswith('_promedio')],'PLANET_','extended','PLANET_TEMPORAL')
    t=a.merge(b,on=ID,how='left',validate='one_to_one'); _write(t,'planet_features.parquet',pd.concat([ma,mb]))

def build_climate():
    d=pd.read_parquet(DATA/'environment/climate_monthly_timeseries.parquet'); d=d[d.date_month.between(START,END)]
    rows=[]; md=[]
    for pid,g in d.groupby(ID):
        r={ID:pid}; p=g.precip_mean.to_numpy(); dates=g.date_month
        pstats={'total':np.nansum(p),'mean':np.nanmean(p),'std':np.nanstd(p,ddof=1),'min':np.nanmin(p),'max':np.nanmax(p),
                'max_month':int(g.loc[g.precip_mean.idxmax(),'month']),'wettest_fraction':np.nanmax(p)/np.nansum(p) if np.nansum(p)>0 else np.nan,
                'cv':np.nanstd(p,ddof=1)/np.nanmean(p) if abs(np.nanmean(p))>=1e-6 else np.nan,
                'early_sum':g[g.month<=6].precip_mean.sum(),'mid_sum':g[g.month.between(7,8)].precip_mean.sum(),'late_sum':g[g.month>=9].precip_mean.sum()}
        for st,v in pstats.items(): r[f'CLIMATE_precip_{st}']=v
        for var in ['tmin_mean','tmax_mean','tmean_mean','dtr_mean']:
            z=extract_temporal_features(dates,g[var],START)
            for st in ['mean','median','std','min','max','peak_day','min_day','slope']: r[f'CLIMATE_{var}_{st}']=z[st]
            r[f'CLIMATE_{var}_early_mean']=g[g.month<=6][var].mean(); r[f'CLIMATE_{var}_mid_mean']=g[g.month.between(7,8)][var].mean(); r[f'CLIMATE_{var}_late_mean']=g[g.month>=9][var].mean()
        rows.append(r)
    t=parcels().merge(pd.DataFrame(rows),on=ID,how='left')
    for c in t.columns[1:]: md.append(meta(c,'CLIMATE','CHIRPS_OR_WORLDCLIM',c.split('_')[1],c.split('_')[-1],'2025-04-01/2025-10-31','CLIMATE_CURRENT','CORE','Resumen mensual ponderado por parcela.'))
    _write(t,'climate_features.parquet',pd.DataFrame(md))

def build_history_anomaly():
    sat=pd.read_parquet(DATA/'timeseries/sentinel_timeseries.parquet'); clim=pd.read_parquet(DATA/'environment/climate_monthly_timeseries.parquet').rename(columns={'date_month':'fecha_captura'})
    sources=[('S2',sat,[f'{b}_promedio' for b in PRIMARY if f'{b}_promedio' in sat]),('CLIMATE',clim,['precip_mean','tmin_mean','tmax_mean','tmean_mean','dtr_mean'])]
    hrows={p:{ID:p} for p in parcels()[ID]}; arows={p:{ID:p} for p in parcels()[ID]}; hm=[]; am=[]
    for src,d,vars_ in sources:
        d=d[d.fecha_captura.dt.month.between(4,10)].copy(); d['year']=d.fecha_captura.dt.year; d['month']=d.fecha_captura.dt.month
        monthly=d.groupby([ID,'year','month'])[vars_].mean().reset_index()
        for pid,g in monthly.groupby(ID):
            for var in vars_:
                hist=g[g.year.between(2022,2024)].groupby('month')[var].agg(['mean','std']); cur=g[g.year==2025].set_index('month')[var]
                aligned=hist.join(cur.rename('current'),how='outer'); aligned['anom']=aligned.current-aligned['mean']; stable=aligned['std']>=1e-6; aligned['zanom']=aligned.anom/aligned['std'].where(stable)
                pre=f'HIST_{src}_{var}'; hrows[pid][pre+'_mean']=hist['mean'].mean(); hrows[pid][pre+'_std']=hist['mean'].std(); hrows[pid][pre+'_months']=hist['mean'].notna().sum()
                ap=f'ANOM_{src}_{var}'; av=aligned.anom.dropna(); za=aligned.zanom.dropna()
                arows[pid].update({ap+'_mean':av.mean(),ap+'_min':av.min(),ap+'_max':av.max(),ap+'_auc':np.trapezoid(av.to_numpy(),av.index.to_numpy()) if len(av)>1 else np.nan,
                                   ap+'_prop_below':(av<0).mean(),ap+'_prop_above':(av>0).mean(),ap+'_strongest_negative':av.min(),ap+'_strongest_positive':av.max(),
                                   ap+'_standardized_mean':za.mean(),ap+'_standardized_max_abs':za.abs().max(),ap+'_unstable_fraction':1-stable.mean()})
    ht=pd.DataFrame(hrows.values()); at=pd.DataFrame(arows.values())
    for c in ht.columns[1:]: hm.append(meta(c,'HISTORY',c.split('_')[1],c,'historical_summary','calendar_month_Apr-Oct_2022-2024','HISTORY','HISTORY','Baseline mensual por parcela, sólo 2022-2024.'))
    for c in at.columns[1:]: am.append(meta(c,'ANOMALY',c.split('_')[1],c,'anomaly_summary','calendar_month_Apr-Oct_2025_vs_2022-2024','ANOMALY','ANOMALY','Anomalía 2025 contra el mismo mes histórico; z-anomaly sólo si std>=1e-6.'))
    _write(ht,'history_features.parquet',pd.DataFrame(hm)); _write(at,'anomaly_features.parquet',pd.DataFrame(am))

def combine_dictionary():
    files=sorted(OUT.glob('*_dictionary.csv')); d=pd.concat([pd.read_csv(p) for p in files if p.name!='family1_feature_dictionary.csv'],ignore_index=True).drop_duplicates('feature_name')
    d.to_csv(OUT/'family1_feature_dictionary.csv',index=False); return d
