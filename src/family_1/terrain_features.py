"""Features topográficas básicas y avanzadas, derivadas sin usar rendimiento."""
from __future__ import annotations
from pathlib import Path
import json, sys
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from exactextract import exact_extract
from scipy import ndimage

from .feature_pipeline import ROOT, OUT, AUD, ID, meta, _write

RAW=ROOT/'data/original'; TOPO=RAW/'05_topografia'; SURF=ROOT/'data/processed/family_1/terrain_surfaces'; SURF.mkdir(parents=True,exist_ok=True)
SHP=RAW/'02_conjunto_70_30/Parcelas_Reto_AGC_CONJUNTO.shp'

def _parcels(crs=None):
    g=gpd.read_file(SHP).rename(columns={'ID_POLIGON':ID})[[ID,'geometry']]
    return g.to_crs(crs) if crs else g

def _weighted_quantile(v,w,q):
    ok=np.isfinite(v)&np.isfinite(w)&(w>0); v=v[ok]; w=w[ok]
    if not len(v): return np.nan
    ix=np.argsort(v); v=v[ix]; w=w[ix]; c=np.cumsum(w)-.5*w
    return float(np.interp(q,c/c[-1],v)) if c[-1]>0 else np.nan

def _zonal(path, prefix, extra=False):
    with rasterio.open(path) as src: g=_parcels(src.crs)
    z=exact_extract(str(path),g,['mean','median','min','max','stdev','values','coverage'],output='pandas')
    rows=[]
    for i,pid in enumerate(g[ID]):
        v=np.asarray(z.iloc[i]['values'],float); w=np.asarray(z.iloc[i]['coverage'],float); ok=np.isfinite(v)&np.isfinite(w)&(w>0); v=v[ok]; w=w[ok]
        r={ID:pid,f'{prefix}_mean':np.average(v,weights=w) if len(v) else np.nan,f'{prefix}_median':_weighted_quantile(v,w,.5),
           f'{prefix}_min':v.min() if len(v) else np.nan,f'{prefix}_max':v.max() if len(v) else np.nan,
           f'{prefix}_std':np.sqrt(np.average((v-np.average(v,weights=w))**2,weights=w)) if len(v) else np.nan,
           f'{prefix}_q10':_weighted_quantile(v,w,.1),f'{prefix}_q25':_weighted_quantile(v,w,.25),f'{prefix}_q75':_weighted_quantile(v,w,.75),f'{prefix}_q90':_weighted_quantile(v,w,.9)}
        r[f'{prefix}_iqr']=r[f'{prefix}_q75']-r[f'{prefix}_q25']; rows.append(r)
    return pd.DataFrame(rows)

def build_basic():
    elev=next(TOPO.rglob('Elevacion*.tif')); slope=next(TOPO.rglob('Pendiente*.tif'))
    t=_zonal(elev,'TOPO_BASIC_elevation').merge(_zonal(slope,'TOPO_BASIC_slope'),on=ID,validate='one_to_one')
    t['TOPO_BASIC_elevation_relief']=t.TOPO_BASIC_elevation_max-t.TOPO_BASIC_elevation_min
    with rasterio.open(slope) as src: g=_parcels(src.crs)
    z=exact_extract(str(slope),g,['values','coverage'],output='pandas'); classes=[(0,2,'0_2'),(2,5,'2_5'),(5,10,'5_10'),(10,np.inf,'gt_10')]
    cr=[]
    for i,pid in enumerate(g[ID]):
        v=np.asarray(z.iloc[i]['values'],float); w=np.asarray(z.iloc[i]['coverage'],float); ok=np.isfinite(v)&np.isfinite(w)&(w>0); v=v[ok];w=w[ok]; r={ID:pid}
        for lo,hi,n in classes: r[f'TOPO_BASIC_pct_area_slope_{n}']=100*w[(v>=lo)&(v<hi)].sum()/w.sum() if w.sum() else np.nan
        cr.append(r)
    t=t.merge(pd.DataFrame(cr),on=ID,validate='one_to_one')
    md=[meta(c,'TOPO_BASIC','DEM_OR_SLOPE',c,c.split('_')[-1],'STATIC','TOPO_BASIC','TOPO_BASIC','Estadística zonal ponderada por fracción de píxel; clases configurables 0-2, 2-5, 5-10 y >10 grados.') for c in t.columns[1:]]
    _write(t.sort_values(ID),'topography_basic_features.parquet',pd.DataFrame(md))

def _write_raster(path,arr,profile):
    p=profile.copy(); p.update(dtype='float32',count=1,nodata=-9999,compress='deflate')
    with rasterio.open(path,'w',**p) as dst: dst.write(np.where(np.isfinite(arr),arr,-9999).astype('float32'),1)

def build_advanced():
    dempath=next(TOPO.rglob('Elevacion*.tif'))
    with rasterio.open(dempath) as src: dem=src.read(1).astype('float64'); profile=src.profile; nodata=src.nodata; res=abs(src.res[0]); bounds=src.bounds
    valid=np.isfinite(dem)&(dem!=nodata); nearest=ndimage.distance_transform_edt(~valid,return_distances=False,return_indices=True); filled=dem[tuple(nearest)]
    gy,gx=np.gradient(filled,res,res); slope=np.arctan(np.hypot(gx,gy)); aspect=np.mod(np.arctan2(-gx,gy),2*np.pi)
    relief=ndimage.maximum_filter(filled,3)-ndimage.minimum_filter(filled,3); tpi=filled-ndimage.uniform_filter(filled,3)
    q,p=gx,gy; r=np.gradient(gx,res,axis=1); tt=np.gradient(gy,res,axis=0); s=.5*(np.gradient(gx,res,axis=0)+np.gradient(gy,res,axis=1)); g2=p*p+q*q; eps=1e-12
    plan=(q*q*r-2*p*q*s+p*p*tt)/np.power(g2+eps,1.5)
    prof=-(p*p*r+2*p*q*s+q*q*tt)/((g2+eps)*np.power(1+g2,1.5))
    arrays={'aspect_sin':np.sin(aspect),'aspect_cos':np.cos(aspect),'local_relief_3x3':relief,'tpi_3x3':tpi,'plan_curvature':plan,'profile_curvature':prof}
    for a in arrays.values(): a[~valid]=np.nan
    # Hidrología D8 sobre toda la extensión entregada; los bordes no conocen cuencas externas.
    from pysheds.grid import Grid
    grid=Grid.from_raster(str(dempath)); raw=grid.read_raster(str(dempath)); pit=grid.fill_pits(raw); dep=grid.fill_depressions(pit); flat=grid.resolve_flats(dep); fdir=grid.flowdir(flat); acc=np.asarray(grid.accumulation(fdir),dtype=float)
    acc[~valid]=np.nan; flowlog=np.log1p(acc); twi=np.log((np.maximum(acc,1)*res)/(np.maximum(np.tan(slope),1e-6))); twi[~valid]=np.nan
    arrays.update(flow_accumulation_log1p=flowlog,twi=twi)
    for name,a in arrays.items(): _write_raster(SURF/f'{name}.tif',a,profile)
    t=None
    for name in arrays:
        z=_zonal(SURF/f'{name}.tif',f'TOPO_ADV_{name}')
        t=z if t is None else t.merge(z,on=ID,validate='one_to_one')
    # Proporciones con significado matemático explícito.
    for name in ['tpi_3x3','plan_curvature','profile_curvature']:
        path=SURF/f'{name}.tif';
        with rasterio.open(path) as src: g=_parcels(src.crs)
        z=exact_extract(str(path),g,['values','coverage'],output='pandas'); neg=[]
        for i,pid in enumerate(g[ID]):
            v=np.asarray(z.iloc[i]['values'],float);w=np.asarray(z.iloc[i]['coverage'],float);ok=np.isfinite(v)&np.isfinite(w)&(w>0);v=v[ok];w=w[ok]
            neg.append({ID:pid,f'TOPO_ADV_{name}_pct_negative':100*w[v<0].sum()/w.sum(),f'TOPO_ADV_{name}_pct_positive':100*w[v>0].sum()/w.sum()})
        t=t.merge(pd.DataFrame(neg),on=ID,validate='one_to_one')
    threshold=float(np.nanquantile(flowlog,.9)); path=SURF/'flow_accumulation_log1p.tif'
    with rasterio.open(path) as src:g=_parcels(src.crs)
    z=exact_extract(str(path),g,['values','coverage'],output='pandas'); rr=[]
    for i,pid in enumerate(g[ID]):
        v=np.asarray(z.iloc[i]['values'],float);w=np.asarray(z.iloc[i]['coverage'],float);ok=np.isfinite(v)&np.isfinite(w)&(w>0);v=v[ok];w=w[ok]
        rr.append({ID:pid,'TOPO_ADV_flow_accumulation_pct_above_regional_q90':100*w[v>threshold].sum()/w.sum()})
    t=t.merge(pd.DataFrame(rr),on=ID,validate='one_to_one').sort_values(ID)
    md=[meta(c,'TOPO_ADVANCED','CONTINUOUS_DEM',c,c.split('_')[-1],'STATIC_FULL_DELIVERED_DEM','TOPO_ADVANCED','TOPO_ADVANCED','Superficie derivada sobre DEM completo; curvatura según fórmulas diferenciales documentadas; hidrología D8 acondicionada.') for c in t.columns[1:]]
    _write(t,'topography_advanced_features.parquet',pd.DataFrame(md))
    manifest={'dem':str(dempath.relative_to(ROOT)),'shape':list(dem.shape),'resolution_m':res,'bounds':list(bounds),'hydrology':'pysheds D8, fill pits/depressions, resolve flats','flow_regional_q90_log1p':threshold,'twi':'ln((flow_accumulation_cells*cellsize)/max(tan(slope),1e-6))','crop_or_buffer_applied':False,'target_used':False,'limitations':['No se conoce aporte aguas arriba fuera del borde del DEM entregado','TWI es potencial estructural, no humedad observada','Curvaturas dependen de resolución y convención de signo']}
    (AUD/'terrain_derivation_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
