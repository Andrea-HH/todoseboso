"""G/H parcel climate representations; canonical extraction is never rebuilt."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from .rainfall_audit import ROOT,CLIMATE,MASTER,SHAPE,sha
from .rainfall_features import ID
from .rainfall_modeling import supervised_data,TARGET
from .rainfall_pcr_audit import MONTHLY as RAIN,bounded_groups
from .temporal_primitives import extract_temporal_features
MONTHS=['apr','may','jun','jul','aug','sep','oct']
THERMAL={v:[f'{v}_{m}_2025' for m in MONTHS] for v in ['tmin','tmax','tmean','dtr']}
MIN=THERMAL['tmin'];MAX=THERMAL['tmax'];TEMP=MIN+MAX;JOINT=RAIN+TEMP

def load_longitudinal():
    d=pd.read_parquet(CLIMATE).sort_values([ID,'year','month']).reset_index(drop=True)
    m=pd.read_csv(MASTER)
    expected=pd.MultiIndex.from_product([sorted(m[ID]),range(2022,2026),range(1,13)])
    actual=pd.MultiIndex.from_frame(d[[ID,'year','month']])
    if not actual.is_unique or set(actual)!=set(expected):raise ValueError('Incomplete canonical climate grid')
    cols=['precip_mean','tmin_mean','tmax_mean','tmean_mean','dtr_mean']
    if not np.isfinite(d[cols]).all().all() or (d.tmin_mean>d.tmax_mean).any():raise ValueError('Invalid temperatures')
    if not np.allclose(d.tmean_mean,(d.tmin_mean+d.tmax_mean)/2) or not np.allclose(d.dtr_mean,d.tmax_mean-d.tmin_mean):raise ValueError('Invalid thermal identities')
    if not d.CONJUNTO.equals(d[ID].map(m.set_index(ID).CONJUNTO)):raise ValueError('Parcel membership mismatch')
    dates=pd.to_datetime(dict(year=d.year,month=d.month,day=1))
    if not dates.equals(d.date_month):raise ValueError('Monthly dates inconsistent')
    return d

def longest(signs,value):
    best=run=0
    for s in signs:
        run=run+1 if s==value else 0;best=max(best,run)
    return best

def build_features(d):
    """Target-free features of 2025 Apr–Oct and short 2022–24 monthly reference."""
    rows=[];dictionary=[]
    def describe(name,family,formula,units='degrees C',period='Apr-Oct 2025'):
        dictionary.append(dict(feature=name,family=family,formula=formula,units=units,period=period,
            source='CHIRPS canonical precip_mean' if family=='rain' else 'CHIRTS-ERA5 canonical monthly means',
            fit_scope='deterministic per parcel; no Y',warning='Monthly extrema are not daily extremes; 3-year reference is not climate normal'))
    for pid,g in d.groupby(ID,sort=True):
        current=g[g.year.eq(2025)&g.month.between(4,10)].sort_values('month')
        if len(current)!=7:raise ValueError('Seven complete cycle months required')
        row={ID:pid,'CONJUNTO':g.CONJUNTO.iloc[0]}
        for var in ['rain','tmin','tmax','tmean','dtr']:
            src='precip_mean' if var=='rain' else var+'_mean';x=current[src].to_numpy()
            names=RAIN if var=='rain' else THERMAL[var]
            for name,value in zip(names,x):row[name]=float(value)
            if var=='rain':continue
            delta=np.diff(x);primitives=extract_temporal_features(current.date_month.to_numpy(),x,'2025-04-01')
            stats=dict(mean=primitives['mean'],min=primitives['min'],max=primitives['max'],std=primitives['std'],range=np.ptp(x),
                max_month=int(current.month.iloc[np.argmax(x)]),min_month=int(current.month.iloc[np.argmin(x)]),
                slope_per_day=primitives['slope'],largest_increase=max(0,float(delta.max())),
                largest_decrease=min(0,float(delta.min())),increase_streak=longest(np.sign(delta),1),
                decrease_streak=longest(np.sign(delta),-1))
            for key,value in stats.items():row[f'{var}_cycle_{key}']=value
            for j,value in enumerate(delta):row[f'{var}_change_{MONTHS[j]}_{MONTHS[j+1]}']=value
            reference=g[g.year.between(2022,2024)&g.month.between(4,10)].groupby('month')[src].mean().reindex(range(4,11))
            for j,m in enumerate(MONTHS):row[f'{var}_anomaly_{m}']=float(x[j]-reference.iloc[j])
        rows.append(row)
    result=pd.DataFrame(rows)
    for name in result.columns:
        if name in [ID,'CONJUNTO']:continue
        var=name.split('_')[0];units='mm/month' if var=='rain' else ('calendar month' if name.endswith('_month') else ('monthly transitions' if name.endswith('_streak') else ('degrees C/day' if name.endswith('_per_day') else 'degrees C')))
        formula=('2025 minus mean of same month 2022–24' if '_anomaly_' in name else
            '(Tmax+Tmin)/2; approximate mean of monthly daily extrema' if var=='tmean' and '_cycle_' not in name and '_change_' not in name else
            'Tmax-Tmin' if var=='dtr' and '_cycle_' not in name and '_change_' not in name else
            'successive monthly difference' if '_change_' in name else
            'OLS slope versus actual days since April 1' if name.endswith('_per_day') else
            'sample SD between 7 months, ddof=1' if name.endswith('_std') else
            'first month on tied minimum/maximum' if name.endswith('_month') else
            'maximum of seven monthly means minus minimum' if name.endswith('_range') else
            'max(0, max of six successive monthly differences)' if name.endswith('_largest_increase') else
            'min(0, min of six successive monthly differences); negative is cooling' if name.endswith('_largest_decrease') else
            'longest consecutive strictly positive monthly differences; zero breaks streak' if name.endswith('_increase_streak') else
            'longest consecutive strictly negative monthly differences; zero breaks streak' if name.endswith('_decrease_streak') else
            'arithmetic mean of seven monthly means' if '_cycle_' in name and name.endswith('_mean') else
            'minimum of seven monthly means' if '_cycle_' in name and name.endswith('_min') else
            'maximum of seven monthly means' if '_cycle_' in name and name.endswith('_max') else
            'canonical parcel-weighted monthly mean')
        describe(name,var,formula,units,'Apr-Oct 2025 versus 2022-24' if '_anomaly_' in name else 'Apr-Oct 2025')
    if len(result)!=197 or not result[ID].is_unique:raise ValueError('Invalid parcel features')
    if not np.isfinite(result.drop(columns=[ID,'CONJUNTO'])).all().all():raise ValueError('Non-finite deterministic climate candidates')
    return result,pd.DataFrame(dictionary)

def climate_current():
    """Exactly the original 48 retained CORE columns, not the later TOP20."""
    from .stage4_modeling import FEATURE_DIR,representations
    all_features=pd.read_parquet(FEATURE_DIR/'family1_features_all.parquet')
    dic=pd.read_csv(FEATURE_DIR/'family1_feature_dictionary.csv').set_index('feature_name')
    cols=[c for c in representations(all_features.columns.drop(ID))['CORE'] if dic.loc[c,'source']=='CLIMATE']
    if len(cols)!=48:raise ValueError('Original Climate Current schema changed')
    return all_features[[ID]+cols],cols

def paths(section,run_id):
    name='g_temperature_signal' if section=='G' else 'h_joint_climate_signal'
    return ROOT/'outputs/modeling/family_1'/name/run_id,ROOT/'data/processed/family_1'/name/run_id

def original_snapshot():
    roots=[ROOT/'outputs/modeling/family_1/rainfall_yield',ROOT/'outputs/modeling/family_1/source_contribution',
        ROOT/'outputs/modeling/residual_signal_audit',ROOT/'outputs/modeling/family_2',ROOT/'outputs/modeling/family_3',
        ROOT/'data/processed/family_1/environment',ROOT/'data/processed/family_1/features',ROOT/'data/processed/family_1/rainfall_yield']
    files=[p for r in roots for p in r.rglob('*') if p.is_file()]
    files+=[p for p in (ROOT/'data/original').rglob('*') if p.is_file()]
    files+=[p for p in (ROOT/'src/family_1').glob('*.py') if not p.name.startswith('climate_signal')]
    return {str(p.relative_to(ROOT)):sha(p) for p in files}

def verify_snapshot(out):
    for p,h in json.loads((out/'protected_inputs.json').read_text(encoding='utf-8')).items():
        if sha(ROOT/p)!=h:raise ValueError(f'Protected input changed: {p}')

def audit_sources(d,out):
    """Verify existing extraction against saved audited zonal rows and source metadata."""
    import rasterio
    inv=pd.read_csv(ROOT/'outputs/data_audit/family_1/environment/climate_raster_inventory.csv')
    long=pd.read_parquet(ROOT/'outputs/data_audit/family_1/environment/climate_zonal_statistics_long.parquet')
    meta=[];grids=[]
    for row in inv.itertuples():
        with rasterio.open(ROOT/row.filepath) as r:
            tags=r.tags();grids.append((str(r.crs),tuple(r.transform),r.width,r.height))
            thermal=row.variable in ['tmin','tmax']
            if thermal and (tags.get('Fuente')!='CHIRTS-ERA5' or tags.get('Unidad')!='grados Celsius'):raise ValueError('Unverified thermal units/source')
            if r.scales!=(1.,) or r.offsets!=(0.,) or r.nodata!=-9999:raise ValueError('Unexpected conversion/NoData')
            meta.append(dict(variable=row.variable,year=row.year,month=row.month,filepath=row.filepath,
                unit=tags.get('Unidad'),source=tags.get('Fuente'),resolution_x=r.res[0],resolution_y=r.res[1],
                nodata=r.nodata,scale=r.scales[0],offset=r.offsets[0]))
    reference=grids[0]
    if not all(g[0]==reference[0] and g[2:]==reference[2:] and np.allclose(g[1],reference[1],atol=1e-6,rtol=0) for g in grids):raise ValueError('Climate raster grids materially misaligned')
    max_shift=float(max(np.max(abs(np.array(g[1])-np.array(reference[1]))) for g in grids))
    # The delivered temperature origin differs by ~3 cm; verify actual polygon support.
    import geopandas as gpd
    from shapely.geometry import box
    parcels=gpd.read_file(SHAPE).rename(columns={'ID_POLIGON':ID})
    supports={ID:parcels[ID].to_numpy()}
    for var in ['precip','tmin','tmax']:
        with rasterio.open(ROOT/inv.loc[inv.variable.eq(var),'filepath'].iloc[0]) as r:
            values=[]
            for geom in parcels.to_crs(r.crs).geometry:
                x0,y0,x1,y1=geom.bounds;a,b=r.index(x0,y1);c,e=r.index(x1,y0);cells=[]
                for row in range(a,c+1):
                    for col in range(b,e+1):
                        left,top=r.transform*(col,row);right,bottom=r.transform*(col+1,row+1)
                        if geom.intersection(box(left,bottom,right,top)).area>0:cells.append((row,col))
                values.append(json.dumps(cells))
            supports[var]=values
    support=pd.DataFrame(supports)
    support['same_cells']=support.precip.eq(support.tmin)&support.precip.eq(support.tmax)
    support.to_csv(out/'tables/01_raster_support_by_parcel.csv',index=False)
    errors={}
    for var in ['precip','tmin','tmax']:
        z=long[long.variable.eq(var)]
        q=d.merge(z[[ID,'year','month','weighted_mean','valid_fraction']],on=[ID,'year','month'],validate='one_to_one')
        errors[var]=float(np.max(abs(q[var+'_mean']-q.weighted_mean)))
        if len(q)!=9456 or errors[var]>1e-9 or q.valid_fraction.min()<.99999:raise ValueError('Existing zonal audit mismatch')
    pd.DataFrame(meta).to_csv(out/'tables/01_source_raster_metadata.csv',index=False)
    result=dict(parcels=197,labeled=138,months=48,rows=9456,missing=0,tmin_gt_tmax=0,
        source='CHIRTS-ERA5',units='degrees C, no Kelvin conversion, scale=1 offset=0',
        nodata='-9999 masked by exactextract; no zero substitution',aligned_rain_temperature_grid=True,
        grids_bitwise_identical=all(g==reference for g in grids),max_affine_difference_degrees=max_shift,
        parcels_same_rain_temperature_cells=int(support.same_cells.sum()),
        resolution_degrees=.05,extraction='existing exactextract fractional cell coverage in EPSG:4326',
        extraction_caveat='degree-squared coverage fractions; not geodesic m2 weights',
        max_difference_saved_zonal_means=errors,raw_reextraction=False,hidden_y_used=False,
        old_dictionary_correction='Legacy CHIRPS_OR_WORLDCLIM label is generic/inaccurate: Tmax/Tmin are CHIRTS-ERA5, verified TIFF tags and LEEME; old dictionary preserved')
    (out/'report/source_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result

def context(out):
    rows=[
        ('G','Family 1','src/family_1; scripts 120/121/123/134/135','canonical extraction and temporal primitives; new thermal exploration'),
        ('H','Family 1 Climate Current','148_family1_source_contribution.py','48 retained CORE features; median imputation, StandardScaler, ElasticNet; alpha .01/.1/1, l1 .1/.5/.9; 4 inner folds'),
        ('G/H','Family 2','201–204; outputs/modeling/family_2','functional curves/FPCA/hybrids preserved; later ENET grid .1/.7 distinguished'),
        ('G/H','Family 3','301–305; outputs/modeling/family_3','historical structural representation and climate conditioning preserved'),
        ('H','Champion','212; RS6 A_CURRENT_CH_H_T','per-fold climate TOP20 ENET -> Sentinel historical residual XGB -> topography residual Ridge; not Climate Current alone'),
        ('G/H','E/F antecedents','313–315; rainfall_yield/v1 and e8/v1','E0–E8 internal rainfall IDs; F_PRE_CYCLE_RIDGE distinct sensitivity; no separate top-level E/F module found, no renaming'),
        ('G/H','Prior climate analysis','205/206 climate regimes; 209 RS3','48-summary correlations/PCA/subfamilies already exist; new monthly controlled nested ablation and geographic transfer'),
        ('G/H','Validation','stage4/splits; rainfall_yield/v1/splits','same 50 original random outer/inner assignments and 15 grouped folds; fixed saved climate_profile is Jan2022–Oct2025 rain-derived, not silently redefined as seven-month/joint profile')]
    pd.DataFrame(rows,columns=['section','module','location','reuse_and_distinction']).to_csv(out/'tables/00_repository_correspondence.csv',index=False)
