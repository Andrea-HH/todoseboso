"""Target-free, calendar-based Sentinel and monthly climate representations."""
import calendar
import numpy as np
import pandas as pd

ID='ID_POLIGONO'
WINDOWS={'pre_apr':[4],'sowing_may_jun':[5,6],
         'post_jul_aug':[7,8],'late_sep_oct':[9,10]}
SAT={'ndvi':'ndvi_promedio','evi':'evi_promedio','ndwi':'ndwi_promedio',
     'msi':'msi_promedio','ndvi_spatial_std':'ndvi_std'}
CLIMATE={'precip':'precip_mean','tmax':'tmax_mean','tmin':'tmin_mean'}

def strict_average(values,months,weights=None):
    a=values.reindex(months).to_numpy(dtype=float)
    return float(np.average(a,weights=weights)) if np.isfinite(a).all() else np.nan

def build_year(satellite,climate,ids,year):
    """Equal-month satellite aggregation; climate totals/day-weighted temperatures."""
    s=satellite.loc[satellite.year.eq(year)&satellite.month.between(4,10)].copy()
    c=climate.loc[climate.year.eq(year)&climate.month.between(4,10)].copy()
    assert not s.duplicated([ID,'fecha_captura']).any()
    assert not c.duplicated([ID,'month']).any()
    s[list(SAT.values())]=s[list(SAT.values())].replace([np.inf,-np.inf],np.nan)
    med=s.groupby([ID,'month'])[list(SAT.values())].median()
    counts=s.groupby([ID,'month'])[list(SAT.values())].count()
    rows=[];support=[];dictionary=[]
    for pid in ids:
        r={ID:pid,'year':year}
        sm=med.loc[pid] if pid in med.index.get_level_values(0) else pd.DataFrame(columns=SAT.values())
        cm=c.loc[c[ID].eq(pid)].set_index('month')
        for window,months in WINDOWS.items():
            for label,col in SAT.items():
                name=f'CAL_S2_{label}_{window}'
                r[name]=strict_average(sm[col],months)
                dictionary.append(dict(feature=name,block='satellite',variable=col,window=window,months=str(months),formula='mean of monthly medians; all window months required',units='source index units',available_by=f'{max(months):02d}-'+str(calendar.monthrange(year,max(months))[1])))
                n=counts.loc[pid,col].reindex(months,fill_value=0) if pid in counts.index.get_level_values(0) else pd.Series(0,index=months)
                dates=s.loc[s[ID].eq(pid)&s.month.isin(months)&s[col].notna(),'fecha_captura'].sort_values()
                start=pd.Timestamp(year,months[0],1);end=pd.Timestamp(year,months[-1],calendar.monthrange(year,months[-1])[1])
                gaps=pd.DatetimeIndex([start,*dates.tolist(),end]).sort_values().to_series().diff().dt.days
                support.append(dict(ID_POLIGONO=pid,year=year,feature=name,valid_observations=int(n.sum()),supported_months=int((n>0).sum()),required_months=len(months),min_observations_per_month=int(n.min()),max_gap_including_window_edges_days=float(gaps.max()),cloud_mean_all_acquisitions=s.loc[s[ID].eq(pid)&s.month.isin(months),'cloud_raw'].mean()))
            for label,col in CLIMATE.items():
                name=f'CAL_CLIM_{label}_{window}'
                weights=[calendar.monthrange(year,m)[1] for m in months]
                value=strict_average(cm[col],months,weights=None if label=='precip' else weights)
                r[name]=value*len(months) if label=='precip' else value
                dictionary.append(dict(feature=name,block='climate',variable=col,window=window,months=str(months),formula='sum monthly precipitation' if label=='precip' else 'calendar-day-weighted monthly temperature mean',units='mm' if label=='precip' else 'degC',available_by=f'{max(months):02d}-'+str(calendar.monthrange(year,max(months))[1])))
        for a,b in [('pre_apr','sowing_may_jun'),('sowing_may_jun','post_jul_aug'),('post_jul_aug','late_sep_oct')]:
            name=f'CAL_S2_ndvi_change_{a}_to_{b}';r[name]=r[f'CAL_S2_ndvi_{b}']-r[f'CAL_S2_ndvi_{a}']
            dictionary.append(dict(feature=name,block='satellite',variable='ndvi_promedio',window=a+' -> '+b,months='',formula='later window minus earlier window',units='NDVI difference',available_by={'sowing_may_jun':'06-30','post_jul_aug':'08-31','late_sep_oct':'10-31'}[b]))
        ndvi=sm['ndvi_promedio'].reindex(range(5,11));valid=ndvi.dropna()
        r['CAL_S2_ndvi_peak_month']=float(valid.idxmax()) if len(valid)>=4 else np.nan
        r['CAL_S2_ndvi_seasonal_range']=float(valid.max()-valid.min()) if len(valid)>=4 else np.nan
        for feature,formula,unit in [('CAL_S2_ndvi_peak_month','month of largest observed monthly median May-Oct; >=4 months; ties earliest','month'),('CAL_S2_ndvi_seasonal_range','max-min of monthly medians May-Oct; >=4 months','NDVI difference')]:
            dictionary.append(dict(feature=feature,block='satellite',variable='ndvi_promedio',window='may_oct',months='[5,6,7,8,9,10]',formula=formula,units=unit,available_by='10-31'))
        support.append(dict(ID_POLIGONO=pid,year=year,feature='CAL_S2_ndvi_peak_month',supported_months=len(valid),required_months=4,peak_at_search_boundary=bool(len(valid) and valid.idxmax() in [5,10])))
        rows.append(r)
    return pd.DataFrame(rows),pd.DataFrame(support),pd.DataFrame(dictionary).drop_duplicates('feature')

def history_representation(panel):
    features=[c for c in panel if c.startswith('CAL_')]
    old=panel.loc[panel.year.between(2022,2024)]
    g=old.groupby(ID)[features];n=g.count();mean=g.mean().where(n.eq(3));sd=g.std(ddof=1).where(n.eq(3))
    current=panel.loc[panel.year.eq(2025)].set_index(ID)[features]
    return pd.concat([current.add_prefix('CURRENT_'),mean.add_prefix('HIST_MEAN_'),sd.add_prefix('HIST_SD_'),(current-mean).add_prefix('DELTA_')],axis=1).reset_index(),n.reset_index()
