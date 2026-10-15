"""Target-free cartographic support audit of newly supplied INEGI erosion data."""
import sys,json,hashlib,itertools
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import geopandas as gpd,pyogrio,pandas as pd,numpy as np
from shapely import union_all,make_valid
from matplotlib import pyplot as plt

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/research/erosion_spatial_audit/v1'
if OUT.exists():raise FileExistsError('Preserve existing versions')
for sub in ['tables','audit','figures']:(OUT/sub).mkdir(parents=True)
SOURCE=ROOT/'data/externo/erosion';PARCEL=ROOT/'data/original/02_conjunto_70_30/Parcelas_Reto_AGC_CONJUNTO.shp'
META=ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet'
ID='ID_POLIGONO';CRS='EPSG:32614'
source=SOURCE/'SHAPE/Poligonos_erosion.shp';info=pyogrio.read_info(source)
g=gpd.read_file(PARCEL).rename(columns={'ID_POLIGON':ID}).to_crs(CRS)
assert len(g)==197 and g[ID].is_unique
g.geometry=g.geometry.map(make_valid)
box=tuple(g.to_crs(info['crs']).total_bounds);s=gpd.read_file(source,bbox=box).to_crs(CRS);invalid=int((~s.is_valid).sum());s.geometry=s.geometry.map(make_valid)
rows=[];parcel=[]
for r in g.itertuples():
    geom=r.geometry;area=geom.area;pieces=[];inter=[]
    for j in s.sindex.query(geom,predicate='intersects'):
        feature=s.iloc[int(j)];a=geom.intersection(feature.geometry);value=a.area
        if value<=1e-5:continue
        pieces.append(a);inter.append(dict(ID_POLIGONO=getattr(r,ID),source_id=int(feature.OBJECTID),category=str(feature.c_uni_ero),dominant_type=str(feature.T_ero_d),dominant_form=str(feature.F_ero_d),dominant_grade=str(feature.G_ero_d),secondary_type=str(feature.T_ero_s),secondary_form=str(feature.F_ero_s),secondary_grade=str(feature.G_ero_s),intersection_m2=float(value),parcel_fraction=float(value/area),source_unit_ha=float(feature.geometry.area/10000)))
    rows.extend(inter);coverage=union_all(pieces).area/area if pieces else 0.
    parcel.append(dict(ID_POLIGONO=getattr(r,ID),Estado=r.Estado,Municipio=r.Municipio,CONJUNTO=r.CONJUNTO,area_ha=float(area/10000),coverage=float(coverage),sum_intersection_fraction=float(sum(a['parcel_fraction'] for a in inter)),source_units=len(inter)))
fractions=pd.DataFrame(rows);composition=fractions.pivot_table(index=ID,columns='category',values='parcel_fraction',aggfunc='sum',fill_value=0).reindex(g[ID],fill_value=0)
parcels=pd.DataFrame(parcel).set_index(ID);parcels['dominant_category']=composition.idxmax(axis=1);parcels['dominant_fraction']=composition.max(axis=1);parcels['n_categories']=(composition>1e-8).sum(axis=1)
parcels.loc[parcels.coverage<1e-8,'dominant_category']='UNCOVERED'
classes=s.dissolve(by='c_uni_ero');boundary=union_all(list(classes.boundary));parcels['distance_thematic_boundary_m']=[geom.distance(boundary) for geom in g.geometry]
parcels['within_125m_boundary']=parcels.distance_thematic_boundary_m<=125
train=pd.read_parquet(META,columns=[ID,'climate_profile']);parcels=parcels.join(train.set_index(ID));parcels['is_train']=parcels.index.isin(train[ID])
pairrows=[]
for profile,a in parcels[parcels.is_train].groupby('climate_profile'):
    for left,right in itertools.combinations(a.index,2):
        diff=float(np.sum(abs(composition.loc[left]-composition.loc[right]))/2)
        pairrows.append(dict(climate_profile=profile,left=left,right=right,different_dominant=parcels.loc[left,'dominant_category']!=parcels.loc[right,'dominant_category'],composition_distance=diff,composition_diff_ge10pp=diff>=.1,both_chignahuapan=parcels.loc[left,'Municipio']=='Chignahuapan' and parcels.loc[right,'Municipio']=='Chignahuapan',both_far125=not parcels.loc[left,'within_125m_boundary'] and not parcels.loc[right,'within_125m_boundary']))
pairs=pd.DataFrame(pairrows);assert len(pairs)==1073
pairsummary=[]
for subset,mask in [('all_train',np.ones(len(pairs),bool)),('Chignahuapan',pairs.both_chignahuapan),('outside_Chignahuapan',~pairs.both_chignahuapan),('both_far125',pairs.both_far125)]:
    a=pairs[mask];pairsummary.append(dict(subset=subset,n_pairs=len(a),n_profiles=a.climate_profile.nunique(),different_dominant=int(a.different_dominant.sum()),fraction_different_dominant=float(a.different_dominant.mean()) if len(a) else None,difference_ge10pp=int(a.composition_diff_ge10pp.sum()),fraction_ge10pp=float(a.composition_diff_ge10pp.mean()) if len(a) else None))
pointsource=SOURCE/'SHAPE/Puntos_erosion.shp';points=gpd.read_file(pointsource).to_crs(CRS);closest=[]
for r in g.itertuples():
    distances=points.distance(r.geometry);j=int(np.argmin(distances.to_numpy()));point=points.iloc[j]
    closest.append(dict(ID_POLIGONO=getattr(r,ID),nearest_point_id=int(point.OBJECTID),nearest_point_distance_m=float(distances.iloc[j]),points_inside=int(sum(distances<=1e-6)),nearest_date=str(point.FECHA)))
nearest=pd.DataFrame(closest).set_index(ID);parcels=parcels.join(nearest)
fractions.to_csv(OUT/'tables/intersections.csv',index=False);composition.to_csv(OUT/'tables/category_composition.csv');parcels.reset_index().to_csv(OUT/'tables/parcel_support.csv',index=False);pairs.to_csv(OUT/'tables/same_climate_pairs.csv',index=False);pd.DataFrame(pairsummary).to_csv(OUT/'tables/pair_support_summary.csv',index=False)
parcels.groupby(['is_train','Estado','dominant_category']).size().reset_index(name='n').to_csv(OUT/'tables/categories_by_state.csv',index=False)
regional=parcels.groupby(['is_train','Estado','Municipio']).agg(n=('area_ha','size'),dominant_categories=('dominant_category','nunique'),mixed=('n_categories',lambda a:int((a>1).sum())),near_boundary=('within_125m_boundary','sum'));regional.to_csv(OUT/'tables/municipal_support.csv')
summary=dict(n_parcels=197,n_train=138,n_prediction_shapes=59,scale='1:250000',reference_date='2013-11-29',field_checks='2009-01-05/2012-07-02',source_polygons_national=int(info['features']),source_polygons_aoi=len(s),invalid_aoi_repaired=invalid,covered=int((parcels.coverage>=.999).sum()),partial_or_uncovered=int((parcels.coverage<.999).sum()),coverage_min=float(parcels.coverage.min()),max_overlap_fraction=float((parcels.sum_intersection_fraction-parcels.coverage).max()),intersected_units=fractions.source_id.nunique(),intersected_categories=fractions.category.nunique(),dominant_categories=parcels.dominant_category.nunique(),mixed_parcels=int((parcels.n_categories>1).sum()),parcels_multi_source_units=int((parcels.source_units>1).sum()),near_boundary125=int(parcels.within_125m_boundary.sum()),parcel_area_ha_quantiles=parcels.area_ha.quantile([0,.5,1]).to_dict(),source_intersected_unit_ha_quantiles=fractions.drop_duplicates('source_id').source_unit_ha.quantile([0,.5,1]).to_dict(),point_inside_parcels=int((parcels.points_inside>0).sum()),nearest_point_m_quantiles=parcels.nearest_point_distance_m.quantile([0,.5,1]).to_dict(),pair_summary=pairsummary,no_y_used=True,no_model_fits=True,no_PRED_inference=True)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
fig,axes=plt.subplots(1,3,figsize=(15,5))
for ax,(state,a) in zip(axes,g.groupby('Estado')):
    view=a.copy();view['category']=parcels.dominant_category.reindex(view[ID]).to_numpy();view.plot(column='category',ax=ax,categorical=True,legend=True,legend_kwds={'fontsize':6},markersize=10);ax.set_title(state+' — categoría dominante');ax.set_axis_off()
fig.tight_layout();fig.savefig(OUT/'figures/parcel_categories.png',dpi=170);plt.close(fig)
paths=list(SOURCE.rglob('*'));paths=[p for p in paths if p.is_file()]+list(PARCEL.parent.glob(PARCEL.stem+'.*'))+[META,Path(__file__)]
hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
(OUT/'audit/inputs.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
(OUT/'manifest.json').write_text(json.dumps(dict(status='complete',no_y_used=True,no_model_fits=True,no_PRED_inference=True,artifacts={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json'}),indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2));print(parcels[parcels.is_train].groupby(['Estado','dominant_category']).size().to_string());print(regional.to_string())
