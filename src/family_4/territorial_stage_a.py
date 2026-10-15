"""Stage A: source/geometry audit and descriptive contrasts; no predictive fitting."""
from pathlib import Path
import json,hashlib,itertools
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import pymupdf
from shapely.geometry import box
from shapely.ops import transform
from shapely import make_valid,segmentize
from pyproj import CRS,Transformer
from pyproj.transformer import TransformerGroup
from pyproj.aoi import AreaOfInterest
from . import within_profile_complementarity as e

ROOT,ID,TARGET=e.ROOT,e.ID,e.TARGET
OUT=ROOT/'outputs/research/family_4/territorial_intraprofile_program/v1/stage_a'
PROC=ROOT/'data/processed/family_4/territorial_intraprofile_program/v1/stage_a'
GEO=ROOT/'data/externo/geologia/702825674595_s/conjunto_de_datos/cdgv_1_250_000_serie1'
TERRAIN=['TOPO_ADV_tpi_3x3_mean','TOPO_ADV_plan_curvature_mean','TOPO_ADV_flow_accumulation_log1p_mean','TOPO_ADV_twi_mean']
CONFIG=dict(stage='A',scope='first delivery only; no B or C fitting',ndvi_similar_absolute=.03,soil_similar_tv=.05,geology_different_tv=.05,terrain_similar_rms_z=.5,terrain_different_rms_z=1,topography_features=TERRAIN,geometry_crs='EPSG:6372',geology_source='existing INEGI E1402 1:250000; NOT SGM50k',sheet_bounds=[-98-1/3,19.75,-98,20],geology_boundary_reserves_m=[50,125,250],no_y_in_pair_classification=True)

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def operation(source):
    group=TransformerGroup(CRS.from_epsg(source),CRS.from_epsg(6372),always_xy=True,area_of_interest=AreaOfInterest(-98.5,19.5,-97.8,20.2),allow_ballpark=False)
    if not group.transformers:raise ValueError('No documented non-ballpark CRS transformation')
    return group.transformers[0]

def project_geometries(frame,source):
    tr=operation(source)
    z=frame.copy();z.geometry=z.geometry.map(lambda geom:transform(tr.transform,geom))
    z=z.set_crs(6372,allow_override=True)
    return z,dict(source_epsg=source,target_epsg=6372,description=tr.description,accuracy_m=tr.accuracy,pipeline=tr.to_proj4())

def setup():
    if (OUT/'manifest.json').exists():raise FileExistsError('Completed Stage A immutable')
    for p in [OUT,PROC]+[OUT/x for x in ['audit','tables','figures','report']]:p.mkdir(parents=True,exist_ok=True)
    p=OUT/'configuration.json'
    if p.exists():assert json.loads(p.read_text())==CONFIG
    else:p.write_text(json.dumps(CONFIG,indent=2),encoding='utf-8')
    inventory=[]
    roots=[ROOT/'data/externo/chignahuapan',ROOT/'docs/resources',ROOT/'data/externo/geologia',ROOT/'data/externo/suelo']
    for directory in roots:
        for path in directory.rglob('*'):
            if path.is_file():inventory.append(dict(path=str(path.relative_to(ROOT)),extension=path.suffix,size_bytes=path.stat().st_size,sha256=sha(path)))
    pd.DataFrame(inventory).to_csv(OUT/'audit/source_inventory.csv',index=False)
    metadata={}
    for name in ['cartageologicadechignahuapan.pdf','6249Chignahuapan - Zacatlan.pdf.crdownload']:
        path=ROOT/'docs/resources'/name
        if not path.exists():continue
        try:
            doc=pymupdf.open(path);text='\n'.join(page.get_text() for page in doc)
            (OUT/'audit'/('geology_pdf_fulltext.txt' if 'geologica' in name else 'forest_study_fulltext.txt')).write_text(text,encoding='utf-8')
            geo_objects=[x for x in range(1,doc.xref_length()) if any(k in doc.xref_object(x) for k in ['/GPTS','/LGIDict','/Subtype /GEO'])]
            metadata[name]=dict(pdf_metadata=doc.metadata,n_pages=len(doc),geospatial_objects=geo_objects,local_partial_download_extension=path.suffix=='.crdownload')
        except Exception as error:metadata[name]=dict(error=str(error))
    with rasterio.open(ROOT/'data/externo/chignahuapan/e14b13.tif') as src:
        metadata['e14b13.tif']=dict(width=src.width,height=src.height,count=src.count,dtype=src.dtypes,embedded_crs=str(src.crs),world_transform=list(src.transform),bounds=list(src.bounds),color_interpretation=[str(x) for x in src.colorinterp],tags=src.tags(),scan_pixel_m=list(src.res),classification='Palette-indexed printed TOPOGRAPHIC map with legends; not thematic class IDs')
    metadata['source_findings']=dict(A1='No historical50k edaphological source found; named folder actually contains topographic scan',A2='Same topographic TIFF: second edition and first print1996; photosMay1994; scan preparedMay2002; NAD27 Clarke1866 UTM14N, contour10m; not an extra PDF in docs/resources',A3='SGM E14-B13 scale50000 first editionDec2017; baseINEGIsecondedition2004; geographicbounds19.75..20,-98.333..-98; datumITRF92 indicated in margin; no geospatialPDF objects; PDFcreated2018,modified2022',extra_vector='INEGI E1402 250k SeriesI; aux statesNAD27 UTM, compilation1982, conversionJan2000; missingPRJ recovered from produceraux andzone14/bounds',forest_pdf='Readable225page forest supply basin study; partial-download suffix; not requested historical cartographic layer; no parcel thematic geometry derived')
    metadata['official_sources']=['https://www.sgm.gob.mx/cartas/Cartas_Ed50.jsp','https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=702825268978','https://www.inegi.org.mx/programas/geol/']
    (OUT/'audit/source_metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    return metadata

def geometry_and_coverage():
    d,t=e.load();p=gpd.read_file(ROOT/'data/original/02_conjunto_70_30/Parcelas_Reto_AGC_CONJUNTO.shp').rename(columns={'ID_POLIGON':ID})
    assert len(p)==197 and p[ID].is_unique and p.geometry.is_valid.all()
    p,crsmeta=project_geometries(p,4326)
    p=p[[ID,'geometry']].merge(d[[ID,'CONJUNTO','climate_profile','Municipio','Estado']],on=ID,validate='one_to_one')
    geog=segmentize(box(*CONFIG['sheet_bounds']),.002)
    coverage=[];outlines=[];ops=[crsmeta]
    for source,epsg in [('topographic1996_sheet',4267),('SGM2017_nominal_sheet',4482)]:
        tr=operation(epsg);geom=transform(tr.transform,geog);ops.append(dict(source=source,source_epsg=epsg,description=tr.description,accuracy_m=tr.accuracy,pipeline=tr.to_proj4()))
        outlines.append(dict(source=source,geometry=geom))
        for row in p.itertuples():
            share=row.geometry.intersection(geom).area/row.geometry.area
            coverage.append(dict(ID_POLIGONO=getattr(row,ID),source=source,coverage_share=share,classification='full' if share>=1-1e-6 else 'partial' if share>1e-6 else 'outside',coverage_kind='documented nominal sheet frame, not classified thematic availability'))
    geo=gpd.read_file(GEO/'e1402pg.shp');invalid=~geo.geometry.is_valid
    geo.loc[invalid,'geometry']=geo.loc[invalid,'geometry'].map(make_valid)
    assert geo.geometry.is_valid.all()
    geo,op=project_geometries(geo,26714);ops.append(dict(source='INEGI250k_geology',**op))
    union=geo.geometry.union_all()
    for row in p.itertuples():
        share=row.geometry.intersection(union).area/row.geometry.area
        coverage.append(dict(ID_POLIGONO=getattr(row,ID),source='INEGI250k_geology_vector',coverage_share=share,classification='full' if share>=1-1e-6 else 'partial' if share>1e-6 else 'outside',coverage_kind='actual polygon union; water and unlabeled categories retained'))
    z=pd.DataFrame(coverage).merge(p.drop(columns='geometry'),on=ID,validate='many_to_one');z.to_csv(OUT/'tables/source_coverage_197.csv',index=False)
    z.groupby(['source','classification','CONJUNTO']).agg(n_parcels=(ID,'size'),n_profiles=('climate_profile','nunique')).reset_index().to_csv(OUT/'tables/coverage_summary.csv',index=False)
    z[z.climate_profile.isin([4,24])].groupby(['source','climate_profile','classification','CONJUNTO']).size().rename('n').to_csv(OUT/'tables/dominant_profile_coverage.csv')
    z.groupby(['source','Municipio','classification']).size().rename('n').to_csv(OUT/'tables/municipal_coverage.csv')
    gpd.GeoDataFrame(outlines,crs=6372).to_file(PROC/'verified_sheet_frames.gpkg',driver='GPKG')
    (OUT/'audit/crs_operations.json').write_text(json.dumps(dict(operations=ops,geology_invalid_repaired=int(invalid.sum()),ballpark_allowed=False,accuracy_note='PROJ operation estimates, not full cartographic positional accuracy; no pixel precision claim'),indent=2),encoding='utf-8')
    p.to_file(PROC/'parcels_projected.gpkg',driver='GPKG')
    return p,geo,z,d,t

def geological_features(p,geo):
    intersections=[]
    index=geo.sindex
    for row in p.itertuples():
        candidates=geo.iloc[index.query(row.geometry,predicate='intersects')]
        for _,unit in candidates.iterrows():
            area=row.geometry.intersection(unit.geometry).area
            if area>1e-6:intersections.append(dict(ID_POLIGONO=getattr(row,ID),polygon_key=unit.E1402PG_ID,unit_key=str(unit.CLAVE),entity=str(unit.ENTIDAD),rock_class=str(unit.CLASE),rock_type=str(unit.TIPO),age=str(unit.ERA),intersection_m2=area,parcel_area_m2=row.geometry.area,share=area/row.geometry.area))
    long=pd.DataFrame(intersections);long.to_parquet(PROC/'geology_intersections_full.parquet',index=False)
    comp=long.groupby([ID,'unit_key']).share.sum().unstack(fill_value=0).reindex(p[ID],fill_value=0)
    sums=comp.sum(axis=1)
    if (sums>1+1e-5).any():raise ValueError('Overlapping geology polygons violate physical area shares')
    comp['UNKNOWN_OUTSIDE']=np.maximum(0,1-sums)
    comp.columns=['geo250_share__'+c for c in comp.columns]
    comp.reset_index().to_parquet(PROC/'geology_full_composition_197.parquet',index=False)
    rows=[]
    boundaries=geo.dissolve(by='CLAVE').geometry.boundary.union_all()
    local_boundaries=boundaries.intersection(p.geometry.union_all().buffer(1000))
    buffers={radius:local_boundaries.buffer(radius) for radius in CONFIG['geology_boundary_reserves_m']}
    for row in p.itertuples():
        pid=getattr(row,ID);v=comp.loc[pid];mapped=v.drop('geo250_share__UNKNOWN_OUTSIDE')
        r=dict(ID_POLIGONO=pid,geo250_mapped_share=mapped.sum(),geo250_n_units=int((mapped>1e-8).sum()),geo250_dominant_unit=mapped.idxmax().replace('geo250_share__','') if mapped.sum()>0 else 'UNKNOWN_OUTSIDE',geo250_dominant_share=mapped.max(),geo250_composition_entropy=float(-np.sum(v[v>0]*np.log(v[v>0]))),geo250_boundary_distance_m=row.geometry.distance(boundaries))
        for radius in CONFIG['geology_boundary_reserves_m']:r['geo250_boundary_buffer_'+str(radius)+'m_share']=row.geometry.intersection(buffers[radius]).area/row.geometry.area
        rows.append(r)
    attrs=pd.DataFrame(rows);attrs.to_parquet(PROC/'geology_attributes_197.parquet',index=False)
    long.groupby(['unit_key','entity','rock_class','rock_type','age']).agg(n_parcels=(ID,'nunique'),total_parcel_share=('share','sum')).reset_index().to_csv(OUT/'tables/geology_unit_inventory.csv',index=False)
    joined=long.merge(p.drop(columns='geometry'),on=ID,validate='many_to_one')
    joined.groupby(['unit_key','CONJUNTO']).agg(n_parcels=(ID,'nunique'),n_profiles=('climate_profile','nunique'),n_municipalities=('Municipio','nunique')).reset_index().to_csv(OUT/'tables/geology_category_support.csv',index=False)
    # Only local-area polygon export, without mining or mineral points.
    local=geo[geo.geometry.intersects(p.geometry.union_all().buffer(5000))]
    local.to_file(PROC/'geology_existing250k_local.gpkg',driver='GPKG')
    return comp,attrs,long

def descriptive_contrasts(d,t,comp,attrs):
    existing=pd.read_parquet(ROOT/'data/processed/family_1/features/family1_features_all.parquet')
    soil=pd.read_parquet(ROOT/'data/processed/family_1/i_climate_conditioned_geographic_edaphological/v1/soil_full_composition.parquet').set_index(ID)
    soilcols=soil.select_dtypes(include='number').columns.tolist()
    assert len(soilcols)==22 and np.allclose(soil[soilcols].sum(axis=1),1,atol=1e-6)
    targetfree=d[[ID,'CONJUNTO','climate_profile','Municipio','Estado',e.f.NDVI,e.RISE,'altitude_m','slope_degrees',e.RELIEF]].merge(existing[[ID]+TERRAIN],on=ID,validate='one_to_one').merge(attrs,on=ID,validate='one_to_one').merge(comp.reset_index(),on=ID,validate='one_to_one')
    assert TARGET not in targetfree
    targetfree.to_parquet(PROC/'territorial_candidate_matrix_197_target_free.parquet',index=False)
    z=t[[ID,TARGET]].merge(targetfree,on=ID,validate='one_to_one').set_index(ID)
    baseline=pd.read_parquet(e.OUT/'tables/oof_predictions.parquet');baseline=baseline[baseline.experiment.eq('F4-E1')]
    assert len(baseline)==1794
    diagnostics=[];pairs=[]
    scales=z[TERRAIN].std(ddof=0).replace(0,1)
    (OUT/'audit/x_only_pair_scales.json').write_text(json.dumps(dict(terrain_sd=scales.to_dict(),thresholds=CONFIG,scope='TRAIN predictor-only descriptive scale; NOT a predictive fit'),indent=2),encoding='utf-8')
    for (protocol,repeat,fold,profile),g in baseline.merge(targetfree[[ID,'climate_profile','Municipio']],on=ID,validate='many_to_one').groupby(['protocol','repeat','fold','climate_profile']):
        if profile not in [4,24]:continue
        g=g[g.Municipio.eq('Chignahuapan')].sort_values(ID)
        for i,j in itertools.combinations(g.to_dict('records'),2):
            ai,bi=i[ID],j[ID];x,y=z.loc[ai],z.loc[bi]
            geo_tv=float(abs(comp.loc[ai]-comp.loc[bi]).sum()/2)
            soil_tv=float(abs(soil.loc[ai,soilcols]-soil.loc[bi,soilcols]).sum()/2)
            terrain_distance=float(np.sqrt(np.mean(((x[TERRAIN].astype(float)-y[TERRAIN].astype(float))/scales)**2)))
            dy=i['y_true']-j['y_true'];dp=i['y_pred']-j['y_pred']
            pairs.append(dict(protocol=protocol,repeat=repeat,fold=fold,profile=profile,id_a=ai,id_b=bi,ndvi_distance=abs(x[e.f.NDVI]-y[e.f.NDVI]),geo250_tv=geo_tv,soil250_tv=soil_tv,terrain_rms_z=terrain_distance,geology_different=geo_tv>CONFIG['geology_different_tv'],ndvi_similar=abs(x[e.f.NDVI]-y[e.f.NDVI])<=CONFIG['ndvi_similar_absolute'],soil_similar=soil_tv<=CONFIG['soil_similar_tv'],terrain_different=terrain_distance>=CONFIG['terrain_different_rms_z'],all_observed_similar=bool(abs(x[e.f.NDVI]-y[e.f.NDVI])<=.03 and abs(x[e.RISE]-y[e.RISE])<=15 and terrain_distance<=.5 and soil_tv<=.05 and geo_tv<=.05),observed_difference=dy,predicted_difference=dp,pair_error=dy-dp))
    pair=pd.DataFrame(pairs);pair.to_parquet(OUT/'tables/dominant_same_model_pairs.parquet',index=False)
    for (protocol,repeat),g in pair.groupby(['protocol','repeat']):
        masks={'all':np.ones(len(g),bool),'different_geology250k':g.geology_different,'similar_NDVI_different_geology250k':g.ndvi_similar&g.geology_different,'similar_soil_different_geomorphology':g.soil_similar&g.terrain_different,'similar_observed_climate_vegetation_terrain_soil_geo':g.all_observed_similar}
        for scope,mask in masks.items():
            zz=g[mask]
            if len(zz):diagnostics.append(dict(protocol=protocol,repeat=repeat,stratum=scope,n_pairs=len(zz),n_parcels=len(set(zz.id_a)|set(zz.id_b)),n_profiles=zz.profile.nunique(),pair_rmse=np.sqrt(np.mean(zz.pair_error**2)),pair_mae=abs(zz.pair_error).mean(),observed_difference_rms=np.sqrt(np.mean(zz.observed_difference**2))))
    pd.DataFrame(diagnostics).to_csv(OUT/'tables/pair_strata_repeat.csv',index=False)
    pd.DataFrame(diagnostics).groupby(['protocol','stratum']).mean(numeric_only=True).reset_index().to_csv(OUT/'tables/pair_strata_summary.csv',index=False)
    # X-only inventory of all possible local pairs, independent of co-held-out eligibility.
    unique=pair.drop_duplicates(['id_a','id_b']);assert len(unique)==934
    unique.drop(columns=['observed_difference','predicted_difference','pair_error','protocol','repeat','fold']).to_csv(OUT/'tables/dominant_x_only_pair_inventory.csv',index=False)
    # Existing OOF residuals are only associated descriptively; never used as training targets.
    rand=baseline[baseline.protocol.eq('random')].groupby(ID)[['y_true','y_pred']].mean()
    z['mean_random_oof_residual']=z.index.map(rand.y_true-rand.y_pred)
    columns=['altitude_m','slope_degrees',e.RELIEF]+TERRAIN+['geo250_composition_entropy','geo250_boundary_distance_m']
    assoc=[]
    for scope,zz in [('all',z),('Chignahuapan',z[z.Municipio.eq('Chignahuapan')]),('dominant_profiles',z[z.climate_profile.isin([4,24])&z.Municipio.eq('Chignahuapan')])]:
        for c in columns:
            w=zz[[c,e.f.NDVI,'mean_random_oof_residual']]-zz.groupby('climate_profile')[[c,e.f.NDVI,'mean_random_oof_residual']].transform('mean')
            valid=w.dropna();design=np.column_stack([np.ones(len(valid)),valid[e.f.NDVI]])
            rx=valid[c]-design@np.linalg.lstsq(design,valid[c],rcond=None)[0];ry=valid.mean_random_oof_residual-design@np.linalg.lstsq(design,valid.mean_random_oof_residual,rcond=None)[0]
            assoc.append(dict(scope=scope,feature=c,n=len(valid),global_residual_correlation=zz[c].corr(zz.mean_random_oof_residual),within_residual_correlation=valid[c].corr(valid.mean_random_oof_residual),partial_profile_ndvi_residual_correlation=rx.corr(ry)))
    pd.DataFrame(assoc).to_csv(OUT/'tables/descriptive_oof_residual_associations.csv',index=False)
    z[columns+[e.f.NDVI]].corr().to_csv(OUT/'tables/terrain_geology_redundancy.csv')
    # Existing WRB versus geology cross-tab is coexistence, not taxonomic equivalence.
    soil_dom=soil[soilcols].idxmax(axis=1)
    pd.crosstab(targetfree.geo250_dominant_unit,targetfree[ID].map(soil_dom)).to_csv(OUT/'tables/geology_vs_existing_soil_dominant.csv')
    return targetfree,pair

def run():
    metadata=setup();p,geo,coverage,d,t=geometry_and_coverage();comp,attrs,long=geological_features(p,geo)
    features,pairs=descriptive_contrasts(d,t,comp,attrs)
    from .territorial_stage_a_reporting import report
    report(p,geo,coverage,features,pairs,metadata)
    print('STAGE A diagnostics complete; no predictive fitting',flush=True)
