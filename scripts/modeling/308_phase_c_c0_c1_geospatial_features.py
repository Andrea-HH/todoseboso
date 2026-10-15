"""Fase C, C0-C1: auditoría y variables geoespaciales externas por parcela.

No usa Y para diseñar variables, no entrena modelos, no clasifica mapas RGB y
no modifica artefactos previos. Canonical ID: ID_POLIGONO.
"""
from pathlib import Path
import json, warnings, re
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from shapely.ops import unary_union
from sklearn.neighbors import BallTree
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore");sns.set_theme(style="whitegrid")
ROOT=Path(__file__).resolve().parents[2];ID="ID_POLIGONO";METRIC=6372
RAW=ROOT/"data/externo";PROC=ROOT/"data/processed/phase_c/c0_c1"
OUT=ROOT/"outputs/research/phase_c/c0_c1";TAB=OUT/"tables";FIG=OUT/"figures";REP=OUT/"report"
for p in [PROC,TAB,FIG,REP]:p.mkdir(parents=True,exist_ok=True)

def nearest_distance(origins, targets):
    if len(targets)==0:return np.full(len(origins),np.nan)
    u=unary_union(list(targets.geometry));return np.array([g.distance(u) for g in origins.geometry])

def dominant_overlay(parcels, layer, cols, prefix):
    a=parcels[[ID,"geometry"]].copy();a["parcel_area_m2"]=a.area
    ov=gpd.overlay(a,layer[cols+["geometry"]],how="intersection",keep_geom_type=False)
    ov["intersection_m2"]=ov.area
    ov["fraction"]=ov.intersection_m2/ov.parcel_area_m2
    groupcol=cols[0];div=ov.groupby(ID)[groupcol].nunique().rename(prefix+"diversity")
    idx=ov.groupby(ID).intersection_m2.idxmax();dom=ov.loc[idx,[ID]+cols+["fraction"]].copy()
    dom=dom.rename(columns={c:prefix+c.lower() for c in cols}|{"fraction":prefix+"dominant_fraction"})
    return dom.merge(div,on=ID,how="left"),ov

def line_density(parcels, lines, radius):
    vals=[]
    for geom in parcels.geometry:
        b=geom.centroid.buffer(radius);cand=lines[lines.intersects(b)]
        length=cand.geometry.intersection(b).length.sum() if len(cand) else 0.0
        vals.append(length/(np.pi*radius**2/1e6))
    return np.asarray(vals)

def parse_rgb_footprint(folder):
    aux=Path(folder)/"e1402.tif.aux.xml";txt=aux.read_text(encoding="utf-8",errors="ignore")
    nums=[float(x) for x in re.findall(r"<Double>([-+0-9.eE]+)</Double>",txt)]
    # Last eight doubles in these auxiliaries are four TargetGCP coordinate pairs.
    pts=np.asarray(nums[-8:]).reshape(-1,2)
    return gpd.GeoDataFrame({"source":[Path(folder).name]},geometry=[Polygon(pts).convex_hull],crs=32614).to_crs(METRIC)

def coverage_rows(cov, parcels, source, scale, decision, valid_mask, extent_mask, no_theme_mask=None, note=""):
    if no_theme_mask is None:no_theme_mask=np.zeros(len(parcels),bool)
    status=np.select([valid_mask,no_theme_mask,extent_mask],["covered_valid_attribute","inside_extent_no_thematic_information","inside_extent_phenomenon_absent"],default="outside_coverage")
    for i,s in enumerate(status):cov.append({ID:parcels.iloc[i][ID],"CONJUNTO":parcels.iloc[i].CONJUNTO,"Estado":parcels.iloc[i].Estado,"source":source,"status":s,"scale":scale,"decision":decision,"note":note})
    return status

def main():
    shp=ROOT/"data/original/02_conjunto_70_30/Parcelas_Reto_AGC_CONJUNTO.shp"
    p=gpd.read_file(shp);p[ID]=p.ID_POLIGON.astype(str);p=p.to_crs(METRIC)
    assert len(p)==197 and p[ID].is_unique
    master=pd.read_csv(ROOT/"data/original/01_tablas_maestras/ID_area_rendimiento_70_30_Reto_AgroCebada.csv")
    p=p.merge(master[[ID,"AREA_HA","RENDIMIENTO_T_HA","CONJUNTO"]],on=ID,how="left",suffixes=("_shp",""));p["Estado"]=p.Estado.astype(str)
    ext=pd.DataFrame({ID:p[ID],"CONJUNTO":p.CONJUNTO,"Estado":p.Estado,"Municipio":p.Municipio,"EXT_area_geometry_ha":p.area/1e4})
    cov=[];dictionary=[];aud=[]
    def adddict(name,family,source,file,scale,date,method,unit,vtype,limitation,meaning,redundancy="low"):
        dictionary.append({"variable":name,"family":family,"source":source,"file":file,"scale":scale,"reference_date":date,"extraction_method":method,"unit":unit,"variable_type":vtype,"limitations":limitation,"physical_interpretation":meaning,"redundancy_risk":redundancy})

    # Fisiografía: the downloaded file contains only province level plus masks.
    fpath=next((RAW/"fisiografia").rglob("*.shp"));fis=gpd.read_file(fpath).to_crs(METRIC)
    fis=fis[fis.ENTIDAD.eq("PROVINCIA")][["CLAVE","NOMBRE","geometry"]]
    fd,fo=dominant_overlay(p,fis,["CLAVE","NOMBRE"],"EXT_PHYS_");ext=ext.merge(fd,on=ID,how="left")
    ffrac=fo.groupby(ID).intersection_m2.sum()/p.set_index(ID).area;valid=p[ID].isin(ffrac.index).to_numpy();extent=np.ones(len(p),bool)
    coverage_rows(cov,p,"Fisiografia","1:1,000,000","regional_context",valid,extent,note="Only province hierarchy present; no subprovince/topoform layers downloaded")
    for c,u,t,m in [("EXT_PHYS_clave","category","categorical","Dominant official province code"),("EXT_PHYS_nombre","category","categorical","Dominant physiographic province"),("EXT_PHYS_dominant_fraction","fraction","numeric","Parcel fraction in dominant province"),("EXT_PHYS_diversity","count","numeric","Number of provinces intersected")]:adddict(c,"Physiography","INEGI physiography",str(fpath.relative_to(ROOT)),"1:1,000,000","2001","area-weighted polygon overlay",u,t,"Generalized regional mapping",m,"medium")
    aud.append(["Fisiografia",str(fpath.relative_to(ROOT)),"polygon","1:1,000,000","2001",fis.crs.to_string(),len(fis),valid.sum(),"Apta únicamente para contexto regional","Only province level; high generalization"])

    # Geology: official AUX states UTM/NAD27, E14-2; zone 14 follows sheet location.
    gdir=next((RAW/"geologia").rglob("cdgv_1_250_000_serie1"));pg=gpd.read_file(gdir/"e1402pg.shp").set_crs(26714,allow_override=True).to_crs(METRIC)
    lg=gpd.read_file(gdir/"e1402lg.shp").set_crs(26714,allow_override=True).to_crs(METRIC)
    gd,go=dominant_overlay(p,pg,["CLAVE","CLASE","TIPO","ERA","ENTIDAD"],"EXT_GEOL_");ext=ext.merge(gd,on=ID,how="left")
    ext["EXT_GEOL_distance_structure_m"]=nearest_distance(p,lg)
    faults=lg[lg.ENTIDAD.str.contains("FALLA",case=False,na=False)];fract=lg[lg.ENTIDAD.str.contains("FRACTURA",case=False,na=False)]
    ext["EXT_GEOL_distance_fault_m"]=nearest_distance(p,faults);ext["EXT_GEOL_distance_fracture_m"]=nearest_distance(p,fract)
    sheet=Polygon([(394744,2100701),(605256,2100701),(605256,2211662),(394744,2211662)]);sheet=gpd.GeoSeries([sheet],crs=26714).to_crs(METRIC).iloc[0]
    extent=np.array([sheet.covers(x.centroid) for x in p.geometry]);valid=ext.EXT_GEOL_clave.notna().to_numpy();coverage_rows(cov,p,"Geologia","1:250,000","apt_for_parcel_extraction",valid,extent,no_theme_mask=extent&~valid,note="CRS resolved from official AUX: UTM NAD27; zone 14 from E14-2 sheet")
    geolcols=[c for c in ext if c.startswith("EXT_GEOL_")]
    for c in geolcols:adddict(c,"Geology","INEGI geological map",str(gdir.relative_to(ROOT)),"1:250,000","compiled 1982; digitized 2000","area-weighted overlay" if "distance" not in c else "minimum planar distance", "m" if "distance" in c else ("fraction" if "fraction" in c else "category/count"),"numeric" if any(x in c for x in ["distance","fraction","diversity"]) else "categorical","Regional generalization; geology is not soil texture/permeability",c.replace("EXT_GEOL_",""),"medium")
    aud.append(["Geologia",str(gdir.relative_to(ROOT)),"polygons/lines/points","1:250,000","1982/2000","EPSG:26714 assigned from official metadata",len(pg)+len(lg),valid.sum(),"Apta para extracción parcelaria con cautela","No .prj; CRS decision fully documented"])

    # Hydrography RH26Dp.
    hdir=RAW/"hidrografia/RH26/RH26D/RH26Dp";sub=gpd.read_file(hdir/"RH26Dp_subc.shp").to_crs(METRIC);hl=gpd.read_file(hdir/"RH26Dp_hl.shp").to_crs(METRIC);ha=gpd.read_file(hdir/"RH26Dp_ha.shp").to_crs(METRIC);top=gpd.read_file(hdir/"RH26Dp_to.shp").to_crs(METRIC)
    footprint=unary_union(list(sub.geometry));inside=np.array([footprint.covers(x.centroid) for x in p.geometry]);valid=inside.copy()
    ext["EXT_HYDRO_inside_RH26Dp"]=inside.astype(int);ext["EXT_HYDRO_distance_stream_m"]=np.where(inside,nearest_distance(p,hl),np.nan)
    per=hl[hl.CONDICION.str.contains("PERENNE",case=False,na=False)&~hl.CONDICION.str.contains("INTERMITENTE",case=False,na=False)];inter=hl[hl.CONDICION.str.contains("INTERMITENTE",case=False,na=False)]
    ext["EXT_HYDRO_distance_perennial_m"]=np.where(inside,nearest_distance(p,per),np.nan);ext["EXT_HYDRO_distance_intermittent_m"]=np.where(inside,nearest_distance(p,inter),np.nan);ext["EXT_HYDRO_distance_waterbody_m"]=np.where(inside,nearest_distance(p,ha),np.nan)
    canals=top[top.TERMINO_GE.str.contains("CANAL",case=False,na=False)];ext["EXT_HYDRO_distance_named_canal_m"]=np.where(inside,nearest_distance(p,canals),np.nan)
    for r in [500,1000,2000]:
        complete=np.array([footprint.covers(x.centroid.buffer(r)) for x in p.geometry]);ext[f"EXT_HYDRO_buffer_{r}m_complete"]=complete.astype(int);dens=line_density(p,hl,r);ext[f"EXT_HYDRO_stream_density_{r}m_km_km2"]=np.where(complete,dens,np.nan)
    coverage_rows(cov,p,"Hidrografia_RH26Dp","1:50,000","partially_apt_by_coverage",valid,inside,note="Features outside subbasin are NA; buffer density only if full buffer lies inside footprint")
    hydrocols=[c for c in ext if c.startswith("EXT_HYDRO_")]
    for c in hydrocols:adddict(c,"External hydrology","INEGI RH26Dp",str(hdir.relative_to(ROOT)),"1:50,000","features dated 1994-2003; edition 2","minimum planar distance" if "distance" in c else ("line length / circular buffer area" if "density" in c else "spatial coverage test"),"m" if "distance" in c else ("km/km2" if "density" in c else "boolean"),"numeric","Only RH26Dp; proximity is not irrigation or effective moisture",c.replace("EXT_HYDRO_",""),"medium")
    aud.append(["Hidrografia",str(hdir.relative_to(ROOT)),"lines/polygons/points","1:50,000","1994-2003",hl.crs.to_string(),len(hl)+len(ha)+len(top),valid.sum(),"Parcialmente apta por cobertura","Edge-truncated buffers set to missing"])

    # Wetland thematic product. UV intersection is used as evidence of thematic coverage.
    wdir=RAW/"humedales/conjunto_de_datos";hm=gpd.read_file(wdir/"c_dat_hum__hm.shp").to_crs(METRIC);ca=gpd.read_file(wdir/"c_dat_hum__ca.shp").to_crs(METRIC);uv=gpd.read_file(wdir/"c_dat_hum__uv.shp").to_crs(METRIC);zh=gpd.read_file(wdir/"c_dat_hum__zh.shp").to_crs(METRIC)
    uvhit=gpd.sjoin(p[[ID,"geometry"]],uv[["geometry"]],predicate="intersects",how="left");covered=set(uvhit.loc[uvhit.index_right.notna(),ID]);thematic=p[ID].isin(covered).to_numpy()
    def intersection_fraction(layer):
        ov=gpd.overlay(p[[ID,"geometry"]],layer[["geometry"]],how="intersection");return ov.assign(a=ov.area).groupby(ID).a.sum()/p.set_index(ID).area
    hfrac=intersection_fraction(hm);cfrac=intersection_fraction(ca);ext["EXT_WET_wetland_intersection_fraction"]=p[ID].map(hfrac).fillna(0).where(thematic,np.nan);ext["EXT_WET_water_inundation_intersection_fraction"]=p[ID].map(cfrac).fillna(0).where(thematic,np.nan)
    ext["EXT_WET_distance_wetland_m"]=np.where(thematic,nearest_distance(p,hm),np.nan);ext["EXT_WET_distance_water_inundation_m"]=np.where(thematic,nearest_distance(p,ca),np.nan)
    uvd,_=dominant_overlay(p,uv,["CLAVE","DESC_","TIP_INFO"],"EXT_WET_LU_");ext=ext.merge(uvd,on=ID,how="left")
    zhd,_=dominant_overlay(p,zh,["CLASIF","SUSTRATO","USO_SUE","TEX_SUE","PROF_SUE"],"EXT_WET_ZONE_");ext=ext.merge(zhd,on=ID,how="left")
    extent=np.ones(len(p),bool);coverage_rows(cov,p,"Humedales","1:50,000","partially_apt_by_thematic_coverage",thematic,extent,no_theme_mask=~thematic,note="UV polygon intersection evidences thematic coverage; no intersection otherwise is not dry-soil evidence")
    wetcols=[c for c in ext if c.startswith("EXT_WET_")]
    for c in wetcols:adddict(c,"Wetlands","INEGI priority-basin wetlands",str(wdir.relative_to(ROOT)),"1:50,000","RapidEye 2012; field 2015; revision 2023","area overlay" if "fraction" in c or "dominant" in c else ("minimum planar distance" if "distance" in c else "dominant polygon attribute"),"m" if "distance" in c else ("fraction" if "fraction" in c else "category/count"),"numeric" if any(x in c for x in ["distance","fraction","diversity"]) else "categorical","Historical, priority-basin thematic coverage; non-intersection is not absence of moisture",c.replace("EXT_WET_",""),"medium")
    aud.append(["Humedales",str(wdir.relative_to(ROOT)),"polygons/points","1:50,000","2012/2015; rev. 2023",hm.crs.to_string(),len(hm)+len(ca)+len(uv)+len(zh),thematic.sum(),"Parcialmente apta por cobertura temática","Coverage inferred only where UV polygons intersect"])

    # Localities: points with explicit coordinates; reference date unavailable locally.
    loc=[]
    for f in sorted((RAW/"localidades").glob("*.csv")):
        q=pd.read_csv(f,low_memory=False);q["source_file"]=f.name;loc.append(q)
    loc=pd.concat(loc,ignore_index=True);locg=gpd.GeoDataFrame(loc,geometry=gpd.points_from_xy(loc.LON_DECIMAL,loc.LAT_DECIMAL),crs=4326).to_crs(METRIC)
    ext["EXT_LOC_distance_any_m"]=nearest_distance(p,locg);rural=locg[locg.AMBITO.eq("R")];urban=locg[locg.AMBITO.eq("U")];ext["EXT_LOC_distance_rural_m"]=nearest_distance(p,rural);ext["EXT_LOC_distance_urban_m"]=nearest_distance(p,urban)
    # nearest name/type, BallTree in projected metric.
    xy=np.c_[locg.geometry.x,locg.geometry.y];cent=np.c_[p.centroid.x,p.centroid.y];tree=BallTree(xy);dist,ind=tree.query(cent,k=1);near=locg.iloc[ind[:,0]]
    ext["EXT_LOC_nearest_name"]=near.NOM_LOC.to_numpy();ext["EXT_LOC_nearest_ambito"]=near.AMBITO.to_numpy();ext["EXT_LOC_nearest_population"]=pd.to_numeric(near.POB_TOTAL,errors="coerce").to_numpy()
    for r in [1000,3000,5000]:
        counts=tree.query_radius(cent,r=r,count_only=True);ext[f"EXT_LOC_count_{r}m"]=counts
    valid=np.ones(len(p),bool);coverage_rows(cov,p,"Localidades","point inventory","apt_for_contextual_parcel_extraction",valid,valid,note="Reference census date not documented in downloaded files")
    loccols=[c for c in ext if c.startswith("EXT_LOC_")]
    for c in loccols:adddict(c,"Localities","INEGI locality inventory",";".join(str(x.relative_to(ROOT)) for x in sorted((RAW/'localidades').glob('*.csv'))),"point inventory","not documented","minimum centroid distance / count in radius / nearest point attribute","m" if "distance" in c else ("count" if "count" in c else "category/persons"),"numeric" if any(x in c for x in ["distance","count","population"]) else "categorical","Population proximity is not infrastructure or agricultural technology",c.replace("EXT_LOC_",""),"low")
    aud.append(["Localidades",str((RAW/'localidades').relative_to(ROOT)),"points","point inventory","date unavailable",locg.crs.to_string(),len(locg),197,"Apta para contexto parcelario","Temporal reference requires verification"])

    # RGB maps: coverage only, never sample colors as thematic measurements.
    for source,folder in [("Suelo_RGB",RAW/"suelo"),("Hidrologia_subterranea_RGB",RAW/"hidrologia_subterranea")]:
        fp=parse_rgb_footprint(folder);foot=fp.geometry.iloc[0];inside=np.array([foot.covers(x.centroid) for x in p.geometry]);coverage_rows(cov,p,source,"E14-2; nominal scale not documented in local files","pending_metadata_or_treatment",np.zeros(len(p),bool),inside,no_theme_mask=inside,note="RGB map image with affine/GCP georeferencing; no validated class legend/table")
        aud.append([source,str(folder.relative_to(ROOT)),"3-band RGB raster","E14-2; pixel about 21 m, not thematic resolution","unknown",fp.crs.to_string(),1,0,"Pendiente de tratamiento o metadatos","Spatial extent covers parcels, but no thematic class extraction; RGB is not soil/water measurement"])

    # ENA is contextual only and never attached as observed parcel values.
    coverage_rows(cov,p,"ENA_2025","national/state","regional_context_not_parcel_feature",np.zeros(len(p),bool),np.ones(len(p),bool),no_theme_mask=np.ones(len(p),bool),note="Aggregate survey statistics retained separately; not parcel attributes")
    aud.append(["ENA_2025",str((RAW/'ena').relative_to(ROOT)),"tables","national/state","Oct 2024-Sep 2025","not spatial geometry",0,0,"Apta únicamente para contexto regional","Ecological and temporal leakage risk"])

    # Persist external main table and coverage.
    assert len(ext)==197 and ext[ID].is_unique
    coverage=pd.DataFrame(cov);coverage.to_csv(PROC/"external_source_coverage_by_parcel.csv",index=False);coverage.to_csv(TAB/"03_external_source_coverage_by_parcel.csv",index=False)
    ext.to_parquet(PROC/"external_parcel_features.parquet",index=False);ext.to_csv(PROC/"external_parcel_features.csv",index=False)

    # Interpretable FIRA selection, 197 parcels, no large feature dump.
    f1=pd.read_parquet(ROOT/"data/processed/family_1/features/family1_features_all.parquet")
    firacols=[ID,"S2_ndvi_promedio_mean","S2_ndvi_promedio_normalized_auc","S2_ndvi_promedio_peak_day","S2_ndvi_promedio_std","S2_ndwi_promedio_mean","S2_fapar_promedio_normalized_auc","CLIMATE_precip_early_sum","CLIMATE_precip_total","CLIMATE_tmax_mean_mean","TOPO_BASIC_elevation_mean","TOPO_BASIC_elevation_std","TOPO_BASIC_slope_mean","TOPO_BASIC_slope_std","TOPO_BASIC_elevation_relief","TOPO_ADV_twi_mean","TOPO_ADV_flow_accumulation_log1p_mean","TOPO_ADV_local_relief_3x3_mean"]
    firacols=[c for c in firacols if c in f1];integrated=ext.merge(f1[firacols],on=ID,how="left")
    integrated.to_parquet(PROC/"integrated_research_matrix.parquet",index=False);integrated.to_csv(PROC/"integrated_research_matrix.csv",index=False)

    # Supervised reference: Y and verified frozen Champion OOF only for TRAIN.
    err=pd.read_csv(ROOT/"outputs/modeling/family_3/f3_2_1_structural_error_diagnostics/tables/02_parcel_error_master.csv")[[ID,"y_true","prediction_mean","residual_mean","mean_absolute_error","prediction_sd"]]
    supervised=integrated.merge(err,on=ID,how="left");supervised.to_parquet(PROC/"supervised_reference_matrix.parquet",index=False);supervised.to_csv(PROC/"supervised_reference_matrix.csv",index=False)
    assert supervised.loc[supervised.CONJUNTO.eq("PREDICCION"),"y_true"].isna().all()

    # Dictionary: append selected FIRA references and empirical missingness.
    for c in firacols:
        if c!=ID:adddict(c,"FIRA interpreted selection","FIRA processed family 1","data/processed/family_1/features/family1_features_all.parquet","parcel/time-derived","2022-2025","existing validated pipeline","see Family 1 dictionary","numeric","Existing feature; included only for research context","Existing FIRA variable","reference")
    dic=pd.DataFrame(dictionary).drop_duplicates("variable");dic["effective_nonmissing_n"]=dic.variable.map(integrated.notna().sum());dic["missing_pct"]=100*(197-dic.effective_nonmissing_n)/197;dic.to_csv(PROC/"external_integrated_variable_dictionary.csv",index=False);dic.to_csv(TAB/"02_variable_provenance_quality.csv",index=False)
    audit=pd.DataFrame(aud,columns=["source","file","geometry","nominal_scale","reference_date","crs_decision","feature_count","parcels_with_valid_attribute","decision","limitations"])
    cov_names={"Hidrografia":"Hidrografia_RH26Dp","Suelo_RGB":"Suelo_RGB","Hidrologia_subterranea_RGB":"Hidrologia_subterranea_RGB"}
    audit["parcels_within_extent"]=audit.source.map(lambda x:int((coverage.loc[coverage.source.eq(cov_names.get(x,x)),"status"]!="outside_coverage").sum()))
    audit["valid_attribute_pct"]=100*audit.parcels_with_valid_attribute/197;audit["extent_coverage_pct"]=100*audit.parcels_within_extent/197;audit.to_csv(TAB/"01_source_audit.csv",index=False)

    # Quality summaries.
    extvars=[c for c in ext if c.startswith("EXT_")];quality=[]
    for c in extvars:
        s=ext[c];quality.append({"variable":c,"dtype":str(s.dtype),"missing_n":s.isna().sum(),"missing_pct":100*s.isna().mean(),"n_unique":s.nunique(dropna=True),"constant":s.nunique(dropna=True)<=1,"near_constant_top_fraction":s.value_counts(normalize=True,dropna=True).iloc[0] if s.notna().any() else np.nan,"train_nonmissing":s[p.CONJUNTO.eq('ENTRENAMIENTO').to_numpy()].notna().sum(),"prediction_nonmissing":s[p.CONJUNTO.eq('PREDICCION').to_numpy()].notna().sum()})
    quality=pd.DataFrame(quality);quality.to_csv(TAB/"04_feature_quality.csv",index=False)
    covsum=coverage.groupby(["source","CONJUNTO","Estado","status"]).size().rename("n").reset_index();covsum.to_csv(TAB/"05_coverage_summary.csv",index=False)
    cats=[]
    for c in [x for x in extvars if ext[x].dtype=='object']:
        for val,n in ext.groupby(c,dropna=False).size().items():cats.append({"variable":c,"category":val,"n_all":n,"n_train":((ext[c]==val)&ext.CONJUNTO.eq('ENTRENAMIENTO')).sum() if pd.notna(val) else (ext[c].isna()&ext.CONJUNTO.eq('ENTRENAMIENTO')).sum()})
    pd.DataFrame(cats).to_csv(TAB/"06_category_cardinality.csv",index=False)

    make_figures(p,ext,coverage,audit,quality,sub,hl,hm)
    make_reports(ext,coverage,audit,quality,dic)
    manifest={"phase":"C0-C1","parcel_count":197,"train_count":138,"prediction_count":59,"canonical_id":ID,"metric_crs":"EPSG:6372","geology_source_crs":"EPSG:26714 based on official AUX UTM/NAD27 plus E14-2 zone","supervised_feature_design":False,"models_or_clustering_run":False,"rgb_classes_extracted":False,"external_downloads":False}
    (OUT/"c0_c1_manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    print(f"C0-C1 complete: {OUT}")

def make_figures(p,ext,coverage,audit,quality,sub,hl,hm):
    plt.figure(figsize=(10,5));sns.barplot(audit,x="source",y="valid_attribute_pct",hue="decision",dodge=False);plt.xticks(rotation=35,ha="right");plt.ylabel("Parcelas con atributo válido (%)");plt.tight_layout();plt.savefig(FIG/"01_source_valid_coverage.png",dpi=180);plt.close()
    g=p.merge(ext[[ID,"EXT_HYDRO_inside_RH26Dp"]],on=ID);ax=sub.boundary.plot(figsize=(7,7),color="blue");g.plot(column="EXT_HYDRO_inside_RH26Dp",categorical=True,legend=True,ax=ax,edgecolor="black",linewidth=.3);ax.set_axis_off();ax.set_title("Cobertura RH26Dp y parcelas");plt.tight_layout();plt.savefig(FIG/"02_hydro_coverage_map.png",dpi=180);plt.close()
    fig,ax=plt.subplots(1,2,figsize=(12,5));g2=p.merge(ext[[ID,"EXT_PHYS_nombre","EXT_GEOL_clave"]],on=ID);g2.plot(column="EXT_PHYS_nombre",categorical=True,legend=True,ax=ax[0],edgecolor="black",linewidth=.2);g2.plot(column="EXT_GEOL_clave",categorical=True,legend=False,ax=ax[1],edgecolor="black",linewidth=.2);ax[0].set_title("Provincia fisiográfica");ax[1].set_title("Unidad geológica dominante");[a.set_axis_off() for a in ax];plt.tight_layout();plt.savefig(FIG/"03_physiography_geology.png",dpi=180);plt.close()
    cols=[c for c in ["EXT_HYDRO_distance_stream_m","EXT_HYDRO_stream_density_1000m_km_km2","EXT_LOC_distance_any_m","EXT_WET_distance_wetland_m"] if c in ext]
    fig,ax=plt.subplots(2,2,figsize=(11,8));
    for a,c in zip(ax.flat,cols):sns.histplot(ext[c].dropna(),ax=a);a.set_title(c);a.set_xlabel("m" if "distance" in c else "km/km²")
    fig.tight_layout();fig.savefig(FIG/"04_numeric_feature_distributions.png",dpi=180);plt.close(fig)
    z=coverage.pivot_table(index=ID,columns="source",values="status",aggfunc="first");code={v:i for i,v in enumerate(["covered_valid_attribute","inside_extent_phenomenon_absent","inside_extent_no_thematic_information","outside_coverage"])};num=z.replace(code)
    plt.figure(figsize=(10,7));sns.heatmap(num,cmap="viridis",cbar=False,yticklabels=False);plt.title("Estado de cobertura por parcela y fuente");plt.tight_layout();plt.savefig(FIG/"05_coverage_matrix.png",dpi=180);plt.close()
    q=quality.nlargest(20,"missing_pct");plt.figure(figsize=(8,6));sns.barplot(q,y="variable",x="missing_pct");plt.xlabel("Faltantes (%)");plt.tight_layout();plt.savefig(FIG/"06_highest_missingness.png",dpi=180);plt.close()

def make_reports(ext,coverage,audit,quality,dic):
    cov=audit[["source","parcels_within_extent","parcels_with_valid_attribute","valid_attribute_pct","decision","limitations"]].round(2).to_dict("records")
    const=quality[quality.constant].variable.tolist();near=quality[(quality.near_constant_top_fraction>=.95)&~quality.constant][["variable","near_constant_top_fraction"]].to_dict("records")
    txt=f"""# Fase C — C0-C1: auditoría y variables geoespaciales externas

## Resumen ejecutivo

Se conservaron las 197 parcelas (138 TRAIN, 59 PREDICTION), una fila por `ID_POLIGONO`. No se usó rendimiento para construir variables, no se ejecutó clustering/modelado y no se interpretaron colores RGB como clases. Cobertura válida resumida: {cov}.

Las fuentes de mayor resolución conceptual son hidrografía y humedales 1:50,000, pero ambas tienen cobertura condicionada. Geología aporta unidades regionales y distancia a estructuras a 1:250,000. Fisiografía sólo distingue provincias a 1:1,000,000. Localidades aporta contexto puntual. Suelo e hidrología subterránea permanecen pendientes porque son cartas RGB sin tabla/leyenda clasificable disponible.

## C0 — Decisiones por fuente

- **Fisiografía:** contexto regional. El SHP descargado contiene provincias, no subprovincias ni sistemas de topoformas; se extrajo unidad dominante/proporción sin inventar jerarquías.
- **Geología:** apta con cautela. El CRS se resolvió mediante el AUX oficial: UTM, NAD27; la carta E14-2 ubica la zona 14 (`EPSG:26714`). Litología no se interpreta como suelo.
- **Hidrografía RH26Dp:** parcialmente apta. Fuera de la subcuenca todo queda NA. Densidades sólo se calculan cuando el buffer completo de 500/1000/2000 m queda dentro del footprint.
- **Humedales:** parcialmente apta y histórica. Sólo la intersección con polígonos UV acredita cobertura temática; no intersecar un humedal no demuestra suelo seco.
- **Localidades:** apta para contexto; fecha de referencia no documentada localmente y requiere verificación.
- **Suelo/Hidrología subterránea:** pendientes. Los TIF tienen GCP/afín y cobertura E14-2, pero tres bandas RGB y ninguna clasificación validada. El píxel ≈21 m no es resolución temática.
- **ENA:** únicamente contexto nacional/estatal; nunca se adjuntó como observación parcelaria.

## Calidad y granularidad

Variables constantes: {const}. Casi constantes (categoría dominante ≥95%): {near}. La tabla `04_feature_quality.csv` separa faltantes TRAIN/PREDICTION y `06_category_cardinality.csv` identifica categorías raras. Faltantes hidrológicos reflejan cobertura RH26Dp o buffers truncados, no ausencia de corrientes. Faltantes de humedales reflejan cobertura temática no acreditada.

## Productos

- `data/processed/phase_c/c0_c1/external_parcel_features.parquet`: atributos externos válidos.
- `integrated_research_matrix.parquet`: selección interpretable FIRA + externos.
- `supervised_reference_matrix.parquet`: Y/OOF sólo donde existen; PREDICTION conserva Y faltante.
- `external_integrated_variable_dictionary.csv`: procedencia, escala, método, unidad y limitación.
- `external_source_coverage_by_parcel.csv`: causa explícita de disponibilidad por fuente.

## Limitaciones decisivas

La escala nominal no equivale a precisión parcelaria. Fisiografía/geología pueden asignarse espacialmente, pero describen contexto generalizado. Distancia a canal no prueba riego; distancia a corriente no prueba humedad; cartografía histórica de humedales no describe necesariamente 2025. No existe todavía una clase edafológica verificable ni una medición parcelaria de drenaje/retención.
""";(REP/"c0_c1_technical_report.md").write_text(txt,encoding="utf-8")
    rec="""# Recomendaciones para C2-C6

## Variables adecuadas para clustering

- Clustering territorial físico: geología dominante (tratamiento categórico), provincia sólo si tiene variación, distancias/densidades hidrográficas con indicador de cobertura, variables de humedal válidas, y topografía FIRA compacta.
- Clustering integrado: añadir clima FIRA compacto y 2-4 descriptores de vegetación no redundantes; mantener localidades como bloque contextual separado.
- No usar ENA, Y, OOF ni residuos para construir ambientes.

## Tratamiento

- Numéricas: transformación `log1p` para distancias/densidades sesgadas, escalado robusto dentro del train fold y missingness explícita.
- Categóricas: one-hot/medida mixta; agrupar categorías raras sólo mediante reglas target-free. No imponer orden a litología/provincia.
- Cobertura: no imputar “cero” fuera de RH26Dp o fuera de cobertura temática. Para clustering global, comparar un conjunto común de cobertura contra análisis por subuniverso.
- Métodos difusos: evaluar entropía, probabilidad máxima, estabilidad bootstrap y sensibilidad al número de grupos; una pertenencia ambigua no es incertidumbre productiva calibrada.

## Fuentes débiles o pendientes

- Fisiografía 1:1M puede ser constante/gruesa; geología 1:250k es regional y parcialmente redundante con topografía/estado.
- Hidrografía/humedales pueden inducir clusters de disponibilidad si se mezclan NA con ausencia real.
- Suelo e hidrología subterránea siguen sin resolverse: se necesita producto vectorial/tabular con claves, leyenda oficial y unidades cartográficas; no vectorizar RGB improvisadamente.
- Localidades mide contexto de asentamiento, no infraestructura agrícola.

## Comparaciones posteriores

Preespecificar representaciones territorial e integrada, ajustar transformaciones dentro de folds y mantener clustering target-free. Sólo después comparar distribuciones de Y y residuos. Cualquier modelo por ambiente requiere tamaños efectivos suficientes, memberships cross-fitted y comparación nested contra Champion; evitar declarar regímenes predictivos por diferencias retrospectivas de Y.
""";(REP/"recommendations_c2_c6.md").write_text(rec,encoding="utf-8")

if __name__=="__main__":main()
