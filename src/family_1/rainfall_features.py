"""Versioned rainfall-only parcel features; no target access or learned transforms."""
import numpy as np
import pandas as pd
from .temporal_primitives import extract_temporal_features

ID = 'ID_POLIGONO'
VERSION = 'rainfall_v1'
MONTHS = ('apr','may','jun','jul','aug','sep','oct')
TOL = 1e-6  # mm: numerical equality, not an agronomic threshold
REL_MIN = 1.0  # mm: references below 1 mm have unstable relative anomalies

def longest_streak(mask):
    best = run = 0
    for value in mask:
        run = run+1 if value else 0
        best = max(best, run)
    return best

def build_features(climate):
    """Strict complete windows; incomplete window aggregates are NaN.

    Only required climate columns are read, even if a caller supplies targets.
    Monthly missing values remain missing; no interpolation across gaps.
    """
    d = climate[[ID,'year','month','precip_mean']].copy()
    if d[ID].isna().any() or d.duplicated([ID,'year','month']).any():
        raise ValueError('Parcel/month keys must be non-null and unique')
    if not d.month.between(1,12).all() or not np.isfinite(d.year).all() or not d.month.mod(1).eq(0).all() or not d.year.mod(1).eq(0).all():
        raise ValueError('Invalid calendar key')
    d.precip_mean = pd.to_numeric(d.precip_mean, errors='raise')
    if d.precip_mean.lt(0).any(): raise ValueError('Negative rainfall')
    d.loc[~np.isfinite(d.precip_mean),'precip_mean'] = np.nan
    rows, definitions = [], {}
    def put(row, name, value, formula, unit='mm', family='SUMMARY', period='Apr-Oct 2025', warning=''):
        row[name] = value
        definitions[name] = dict(feature_name=name, definition=formula, formula=formula,
            units=unit, period=period, source='canonical CHIRPS precip_mean; exactextract',
            interpretation='Calendar rainfall descriptor; association is not causal',
            missing_policy='NaN unless all months/years required by this formula are finite; no partial sums',
            warning=warning, feature_family=family, version=VERSION,
            core_or_extended='EXTENDED', variable='precip', statistic=name, window=period, sensor='CHIRPS')
    for pid, group in d.groupby(ID, sort=True):
        grid = group.pivot(index='year', columns='month', values='precip_mean').reindex(index=range(2022,2026), columns=range(1,13))
        p = grid.loc[2025,4:10].to_numpy(float)
        hist = grid.loc[2022:2024,4:10].to_numpy(float)
        h = np.where(np.isfinite(hist).all(axis=0), np.mean(hist,axis=0), np.nan)
        a = p-h; rel = np.divide(a,h,out=np.full(7,np.nan),where=h>=REL_MIN)
        row = {ID:pid}
        for j, m in enumerate(MONTHS):
            put(row,f'rain_{m}_2025',p[j],f'P[2025,{j+4}]',family='MONTHLY',period=f'{j+4:02d}/2025')
            put(row,f'rain_hist_{m}',h[j],f'sum(P[2022:2024,{j+4}])/3',family='HISTORY',period=f'{j+4:02d}/2022-2024',warning='Three-year reference, not climate normal')
            put(row,f'rain_anomaly_{m}',a[j],f'P[2025,{j+4}]-H[{j+4}]',family='ANOMALY',warning='Not an official drought diagnosis')
            put(row,f'rain_relative_anomaly_{m}',rel[j],f'(P[2025,{j+4}]-H[{j+4}])/H[{j+4}] if H >= {REL_MIN} mm',unit='fraction',family='RELATIVE_ANOMALY')
        complete = np.isfinite(p).all()
        # Existing temporal primitives supply compatible complete-window statistics.
        z = extract_temporal_features(pd.date_range('2025-04-01',periods=7,freq='MS'),p) if complete else {}
        total = float(p.sum()) if complete else np.nan
        stats = {'total':(total,'sum(P[4:10])'), 'mean':(z.get('mean',np.nan),'sum(P)/7'),
                 'std':(z.get('std',np.nan),'sqrt(sum((P-mean(P))^2)/6); sample SD ddof=1'),
                 'min':(z.get('min',np.nan),'min(P)'), 'max':(z.get('max',np.nan),'max(P)'),
                 'range':(np.ptp(p) if complete else np.nan,'max(P)-min(P)'),
                 'cv':(np.std(p,ddof=1)/p.mean() if complete and p.mean()>TOL else np.nan,'sample SD/mean if mean > 1e-6 mm'),
                 'median':(z.get('median',np.nan),'median(P)'),
                 'max_month':(int(np.argmax(p))+4 if complete else np.nan,'earliest argmax(P)+4; exact ties choose earliest month'),
                 'min_month':(int(np.argmin(p))+4 if complete else np.nan,'earliest argmin(P)+4; exact ties choose earliest month'),
                 'max_share':(p.max()/total if complete and total>TOL else np.nan,'max(P)/sum(P) if total > 1e-6 mm')}
        for name,(v,f) in stats.items():
            unit = 'calendar month category' if name.endswith('month') else 'fraction' if name in ('cv','max_share') else 'mm'
            put(row,'rain_'+name,v,f,unit,warning='Month indices must be one-hot encoded in linear models; ordinal splits allowed for trees' if name.endswith('month') else 'total and mean are exactly redundant' if name in ('total','mean') else '')
        stages = {'early':(0,2),'middle':(2,5),'late':(5,7)}
        for name,(lo,hi) in stages.items():
            v = p[lo:hi].sum() if np.isfinite(p[lo:hi]).all() else np.nan
            put(row,f'rain_{name}',v,f'sum(P[{lo+4}:{hi+3}])',family='STAGES',warning='Calendar stage, not observed phenology')
            put(row,f'rain_{name}_share',v/total if total>TOL else np.nan,f'rain_{name}/rain_total if total > 1e-6',unit='fraction',family='STAGES')
        put(row,'rain_early_minus_late',row['rain_early']-row['rain_late'],'sum(P[4:5])-sum(P[9:10])',family='STAGES')
        put(row,'rain_middle_minus_early',row['rain_middle']-row['rain_early'],'sum(P[6:8])-sum(P[4:5])',family='STAGES')
        dx = np.diff(p)
        dynamics = {'largest_increase':(max(0.,dx.max()) if complete else np.nan,'max(0,max(diff(P)))'),
                    'largest_decrease':(max(0.,-dx.min()) if complete else np.nan,'max(0,-min(diff(P)))'),
                    'increase_count':((dx>TOL).sum() if complete else np.nan,'sum(diff(P)>1e-6 mm)'),
                    'decrease_count':((dx<-TOL).sum() if complete else np.nan,'sum(diff(P)<-1e-6 mm)'),
                    'longest_increase_streak':(longest_streak(dx>TOL) if complete else np.nan,'longest consecutive diff(P)>1e-6; equality breaks streak'),
                    'longest_decrease_streak':(longest_streak(dx<-TOL) if complete else np.nan,'longest consecutive diff(P)<-1e-6; equality breaks streak'),
                    'net_change':(p[-1]-p[0] if np.isfinite(p[[0,-1]]).all() else np.nan,'P[10]-P[4]'),
                    'mean_absolute_change':(z.get('mean_absolute_change',np.nan),'sum(abs(diff(P)))/6'),
                    'slope':(np.polyfit(np.arange(7),p,1)[0] if complete else np.nan,'OLS slope P vs equally spaced calendar month')}
        for name,(v,f) in dynamics.items():
            unit = 'transitions' if 'streak' in name or 'count' in name else 'mm/calendar month' if name=='slope' else 'mm'
            put(row,'rain_'+name,v,f,unit,family='DYNAMICS',warning='Monthly transitions, never consecutive rainy/dry days')
        valid_a = np.isfinite(a).all()
        ht = h.sum() if np.isfinite(h).all() else np.nan
        anomaly = {'total':(total-ht,'sum(P)-sum(H)','mm'),
                   'total_relative':((total-ht)/ht if ht>=REL_MIN else np.nan,'(sum(P)-sum(H))/sum(H) if sum(H)>=1 mm','fraction'),
                   'below_count':((a<-TOL).sum() if valid_a else np.nan,'sum(A<-1e-6 mm)','months'),
                   'above_count':((a>TOL).sum() if valid_a else np.nan,'sum(A>1e-6 mm)','months'),
                   'largest_deficit':(max(0.,-a.min()) if valid_a else np.nan,'max(0,-min(A))','mm'),
                   'largest_excess':(max(0.,a.max()) if valid_a else np.nan,'max(0,max(A))','mm'),
                   'deficit_month':(int(np.argmin(a))+4 if valid_a and a.min()<-TOL else np.nan,'earliest argmin(A)+4 if any deficit; absolute anomaly','calendar month category'),
                   'negative_streak':(longest_streak(a<-TOL) if valid_a else np.nan,'longest consecutive months A<-1e-6 mm; equality breaks','months'),
                   'positive_streak':(longest_streak(a>TOL) if valid_a else np.nan,'longest consecutive months A>1e-6 mm; equality breaks','months')}
        for name,(v,f,u) in anomaly.items(): put(row,'rain_anomaly_'+name,v,f,u,family='ANOMALY',warning='Short 2022-2024 reference; not a climate normal or diagnosed drought')
        pre = grid.loc[2025,1:3].to_numpy(float); old = grid.loc[2022:2024,1:3].to_numpy(float)
        put(row,'rain_precycle_total',pre.sum() if np.isfinite(pre).all() else np.nan,'sum(P[2025,1:3])',family='PRE_CYCLE',period='Jan-Mar 2025')
        put(row,'rain_mar_2025',pre[2],'P[2025,3]',family='PRE_CYCLE',period='Mar 2025')
        put(row,'rain_precycle_anomaly',row['rain_precycle_total']-old.sum()/3 if np.isfinite(old).all() else np.nan,'sum(P[2025,1:3])-sum(P[2022:2024,1:3])/3',family='PRE_CYCLE',period='Jan-Mar 2025 vs 2022-2024',warning='Does not measure stored soil moisture')
        rows.append(row)
    features = pd.DataFrame(rows)
    if not features[ID].is_unique: raise ValueError('Duplicate parcel features')
    return features, pd.DataFrame(definitions.values())

def merge_rainfall(existing, rainfall):
    """Opt-in integration for downstream models, preserving existing artifacts."""
    if not existing[ID].is_unique or not rainfall[ID].is_unique:
        raise ValueError('Expected one row per parcel')
    overlap = (set(existing.columns)&set(rainfall.columns))-{ID,'CONJUNTO'}
    if overlap: raise ValueError(f'Feature name collision: {sorted(overlap)}')
    if set(existing[ID]) != set(rainfall[ID]): raise ValueError('Parcel universes differ')
    return existing.merge(rainfall.drop(columns=['CONJUNTO'],errors='ignore'),on=ID,validate='one_to_one')
