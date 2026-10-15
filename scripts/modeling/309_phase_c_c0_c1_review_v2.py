"""Complemento versionado C0-C1 v2: resolución, cobertura e interpretabilidad."""
from pathlib import Path
import json,re,warnings
import numpy as np,pandas as pd,geopandas as gpd
from affine import Affine
from shapely.geometry import Polygon
from shapely.ops import transform as shp_transform
from pyproj import Transformer
import rasterio
import matplotlib.pyplot as plt,seaborn as sns
from scipy.stats import spearmanr
warnings.filterwarnings('ignore');sns.set_theme(style='whitegrid')
ROOT=Path(__file__).resolve().parents[2];ID='ID_POLIGONO';METRIC=6372
OLD=ROOT/'outputs/research/phase_c/c0_c1';RAW=ROOT/'data/externo';PROC=ROOT/'data/processed/phase_c/c0_c1_review_v2';OUT=ROOT/'outputs/research/phase_c/c0_c1_review_v2';TAB=OUT/'tables';FIG=OUT/'figures';REP=OUT/'report'
for p in [PROC,TAB,FIG,REP]:p.mkdir(parents=True,exist_ok=True)

def world_transform(path):
 a,d,b,e,c,f=[float(x) for x in Path(path).read_text().split()]
 return Affine(a,b,c,d,e,f)

def cell_polygon(T,row,col):
 pts=[T*(col-.5,row-.5),T*(col+.5,row-.5),T*(col+.5,row+.5),T*(col-.5,row+.5)]
 return Polygon(pts)

def raster_diagnostics(parcels,tif,tfwx,source):
 T=world_transform(tfwx);inv=~T;rows=[];cellowners={};signatures={}
 to32614=Transformer.from_crs(parcels.crs,32614,always_xy=True).transform
 with rasterio.open(tif) as ds:
  for _,r in parcels.iterrows():
   geom=shp_transform(to32614,r.geometry);xmin,ymin,xmax,ymax=geom.bounds;coords=[inv*xy for xy in [(xmin,ymin),(xmin,ymax),(xmax,ymin),(xmax,ymax)]];cs=[x for x,y in coords];rs=[y for x,y in coords]
   c0=max(0,int(np.floor(min(cs)-1)));c1=min(ds.width-1,int(np.ceil(max(cs)+1)));r0=max(0,int(np.floor(min(rs)-1)));r1=min(ds.height-1,int(np.ceil(max(rs)+1)))
   arr=ds.read(window=((r0,r1+1),(c0,c1+1)));weights=[];colors=[];cells=[];contained=0
   for rr in range(r0,r1+1):
    for cc in range(c0,c1+1):
     cp=cell_polygon(T,rr,cc);ia=geom.intersection(cp).area
     if ia<=0:continue
     w=ia/cp.area;weights.append(w);colors.append(tuple(int(v) for v in arr[:,rr-r0,cc-c0]));cells.append((rr,cc));contained+=int(geom.covers(cp))
   w=np.asarray(weights,float);col=np.asarray(colors,float) if colors else np.empty((0,3));key=r[ID]
   for cell in cells:cellowners.setdefault(cell,[]).append(key)
   dominant=tuple(np.median(col,axis=0).astype(int)) if len(col) else None;signatures[key]=dominant
   rows.append({ID:key,'source':source,'intersected_cells':len(w),'fully_contained_cells':contained,'valid_rgb_cells':len(w),'valid_coverage_fraction':min(1,w.sum()*abs(T.a*T.e-T.b*T.d)/geom.area) if len(w) else 0,'effective_cells_area_weighted':(w.sum()**2/(w@w)) if len(w) else 0,'unique_rgb_triplets':len(set(colors)),'rgb_r_mean':np.average(col[:,0],weights=w) if len(w) else np.nan,'rgb_g_mean':np.average(col[:,1],weights=w) if len(w) else np.nan,'rgb_b_mean':np.average(col[:,2],weights=w) if len(w) else np.nan,'rgb_r_sd':np.sqrt(np.average((col[:,0]-np.average(col[:,0],weights=w))**2,weights=w)) if len(w) else np.nan,'rgb_g_sd':np.sqrt(np.average((col[:,1]-np.average(col[:,1],weights=w))**2,weights=w)) if len(w) else np.nan,'rgb_b_sd':np.sqrt(np.average((col[:,2]-np.average(col[:,2],weights=w))**2,weights=w)) if len(w) else np.nan,'diagnostic_dominant_rgb':str(dominant)})
 out=pd.DataFrame(rows);shared={pid:0 for pid in parcels[ID]};others={pid:set() for pid in parcels[ID]}
 for owners in cellowners.values():
  if len(owners)>1:
   for pid in owners:shared[pid]+=1;others[pid].update(set(owners)-{pid})
 out['cells_shared_with_other_parcel']=out[ID].map(shared);out['other_parcels_sharing_any_cell']=out[ID].map(lambda x:len(others[x]));counts=pd.Series(signatures).value_counts();out['parcels_with_same_diagnostic_rgb_signature']=out[ID].map(lambda x:counts[signatures[x]])
 return out,T

def main():
 shp=ROOT/'data/original/02_conjunto_70_30/Parcelas_Reto_AGC_CONJUNTO.shp';p=gpd.read_file(shp);p[ID]=p.ID_POLIGON.astype(str);p=p.to_crs(METRIC)
 old=pd.read_parquet(ROOT/'data/processed/phase_c/c0_c1/external_parcel_features.parquet');sup=pd.read_parquet(ROOT/'data/processed/phase_c/c0_c1/supervised_reference_matrix.parquet')
 # 1 RGB pixel support; values retained only in diagnostic table, never feature matrix.
 soil,Tsoil=raster_diagnostics(p,RAW/'suelo/e1402.tif',RAW/'suelo/e1402.tfwx','soil_rgb');gw,Tgw=raster_diagnostics(p,RAW/'hidrologia_subterranea/e1402.tif',RAW/'hidrologia_subterranea/e1402.tfwx','groundwater_rgb');pix=pd.concat([soil,gw],ignore_index=True);pix.to_csv(TAB/'01_rgb_pixel_support_by_parcel.csv',index=False);pix.to_parquet(PROC/'rgb_pixel_support_diagnostic.parquet',index=False)
 interp=pd.DataFrame([
 {'source':'soil_rgb','coverage':'197 parcels; see pixel table','legend_or_class_table_found':False,'rgb_variation_present':soil.unique_rgb_triplets.median()>1,'interpretability':'not interpretable as soil properties or official categories','reason':'RGB includes cartographic colors, labels, linework, antialiasing and scan artifacts; no color-to-class lookup','action':'obtain official vector soil units or raster class codes plus legend/key'},
 {'source':'groundwater_rgb','coverage':'197 parcels; see pixel table','legend_or_class_table_found':False,'rgb_variation_present':gw.unique_rgb_triplets.median()>1,'interpretability':'not interpretable as aquifer/groundwater properties or official categories','reason':'RGB is a rendered map, not thematic codes; channel means/SD depend on symbology, text and scan','action':'obtain official vector/tabular groundwater units and data dictionary'}]);interp.to_csv(TAB/'02_rgb_interpretability.csv',index=False)

 # 2 Hydrology missing coverage and exact evidence available.
 hdir=RAW/'hidrografia/RH26/RH26D/RH26Dp';sub=gpd.read_file(hdir/'RH26Dp_subc.shp').to_crs(METRIC);foot=sub.geometry.union_all();cent=p.centroid
 hd=pd.DataFrame({ID:p[ID],'Estado':p.Estado,'Municipio':p.Municipio,'longitude':p.to_crs(4326).centroid.x,'latitude':p.to_crs(4326).centroid.y,'inside_downloaded_RH26Dp':[foot.covers(x) for x in cent],'distance_to_RH26Dp_boundary_m':[x.distance(foot) for x in cent]})
 hd['official_subbasin_code']='UNRESOLVED_WITH_EXISTING_FILES';hd['required_product']='INEGI/CONAGUA national subbasin polygons covering each centroid, then matching 1:50k hydrographic networks and an external buffer >=2 km';hd.to_csv(TAB/'03_missing_hydrography_diagnosis.csv',index=False)
 needs=pd.DataFrame([{'needed_file':'National/complete subbasin boundary layer','purpose':'spatially identify official CVE_SUBC for 197 centroids','minimum_extent':'all parcels plus 2 km','required_attributes':'CVE_RH, CVE_CUE, CVE_SUBCUE, name','why_existing_fails':'only RH26Dp polygon downloaded; contains 0 parcels'}, {'needed_file':'1:50,000 hydrographic network packages for identified subbasins','purpose':'stream/canal/waterbody distances and density','minimum_extent':'each parcel plus complete 0.5/1/2 km buffers','required_attributes':'condition, stream order, flow direction, type, named hydraulic feature','why_existing_fails':'RH26Dp network is geographically disjoint'}, {'needed_file':'coverage footprints for every network package','purpose':'distinguish zero feature density from edge truncation','minimum_extent':'same packages','required_attributes':'official subbasin/package boundary','why_existing_fails':'cannot validate absent packages'}]);needs.to_csv(TAB/'04_required_hydrography_files.csv',index=False)

 # 3 inspect the two parcels whose UV polygon evidenced thematic coverage.
 wet_ids=old.loc[old.EXT_WET_LU_desc_.notna(),ID].tolist();wdir=RAW/'humedales/conjunto_de_datos';layers={k:gpd.read_file(wdir/f'c_dat_hum__{k}.shp').to_crs(METRIC) for k in ['hm','ca','uv','zh']}
 wr=[]
 for pid in wet_ids:
  pr=p[p[ID].eq(pid)].iloc[0];base=sup[sup[ID].eq(pid)].iloc[0]
  row={ID:pid,'CONJUNTO':base.CONJUNTO,'Estado':pr.Estado,'Municipio':pr.Municipio,'parcel_area_ha':pr.geometry.area/1e4,'y_true':base.y_true,'oof_prediction':base.prediction_mean,'residual_y_minus_pred':base.residual_mean}
  for k,d in layers.items():
   hit=d[d.intersects(pr.geometry)].copy();row[f'{k}_intersects']=len(hit)>0;row[f'{k}_n_polygons']=len(hit);row[f'{k}_intersection_fraction']=hit.geometry.intersection(pr.geometry).area.sum()/pr.geometry.area if len(hit) else 0
   attrs=[c for c in hit.columns if c!='geometry']
   row[f'{k}_attributes']=' | '.join(';'.join(f'{c}={str(x[c])}' for c in attrs[:12]) for _,x in hit.head(3).iterrows()) if len(hit) else ''
  for c in ['S2_ndvi_promedio_mean','S2_ndvi_promedio_normalized_auc','S2_ndwi_promedio_mean','S2_fapar_promedio_normalized_auc','TOPO_ADV_twi_mean']:
   if c in base:row[c]=base[c]
  wr.append(row)
 wet=pd.DataFrame(wr);wet.to_csv(TAB/'05_two_wetland_parcels_detail.csv',index=False)
 # Five nearest parcels; supervised fields remain missing for PREDICTION.
 near=[]
 for pid in wet_ids:
  pr=p[p[ID].eq(pid)].iloc[0];dist=p.geometry.centroid.distance(pr.geometry.centroid);ix=p.loc[p[ID].ne(pid)].assign(_distance=dist[p[ID].ne(pid)].to_numpy()).nsmallest(5,'_distance').index;ids=p.loc[ix,ID]
  for nid in ids:
   z=sup[sup[ID].eq(nid)].iloc[0];dm=float(p.loc[p[ID].eq(nid)].geometry.iloc[0].centroid.distance(pr.geometry.centroid));near.append({'focal_ID':pid,'neighbor_ID':nid,'distance_centroid_m':dm,'within_3km':dm<=3000,'neighbor_set':z.CONJUNTO,'y_true':z.y_true,'prediction_mean':z.prediction_mean,'residual_mean':z.residual_mean,'S2_ndvi_mean':z.get('S2_ndvi_promedio_mean',np.nan),'S2_ndwi_mean':z.get('S2_ndwi_promedio_mean',np.nan),'TWI_mean':z.get('TOPO_ADV_twi_mean',np.nan)})
 pd.DataFrame(near).to_csv(TAB/'06_wetland_parcel_nearest_neighbors.csv',index=False)

 # 4 locality diversity and radius redundancy.
 loccols=['EXT_LOC_distance_any_m','EXT_LOC_distance_rural_m','EXT_LOC_distance_urban_m','EXT_LOC_count_1000m','EXT_LOC_count_3000m','EXT_LOC_count_5000m','EXT_LOC_nearest_ambito','EXT_LOC_nearest_name']
 loc=old[[ID,'Estado','Municipio']+loccols].copy();ls=[]
 for state,g in [('ALL',loc)]+list(loc.groupby('Estado')):
  for c in loccols:
   s=g[c];ls.append({'scope':state,'variable':c,'n':s.notna().sum(),'n_unique':s.nunique(),'missing_pct':100*s.isna().mean(),'mean':s.mean() if pd.api.types.is_numeric_dtype(s) else np.nan,'sd':s.std() if pd.api.types.is_numeric_dtype(s) else np.nan,'median':s.median() if pd.api.types.is_numeric_dtype(s) else np.nan,'top_category_fraction':s.value_counts(normalize=True).iloc[0] if s.notna().any() else np.nan})
 pd.DataFrame(ls).to_csv(TAB/'07_locality_diversity_by_state.csv',index=False)
 numeric=[c for c in loccols if pd.api.types.is_numeric_dtype(loc[c])];corr=loc[numeric].corr(method='spearman');corr.to_csv(TAB/'08_locality_spearman_redundancy.csv')

 # 5 validate area overlays against original layers: sum fractions and dominant.
 fpath=next((RAW/'fisiografia').rglob('*.shp'));fis=gpd.read_file(fpath).to_crs(METRIC);fis=fis[fis.ENTIDAD.eq('PROVINCIA')]
 gdir=next((RAW/'geologia').rglob('cdgv_1_250_000_serie1'));geo=gpd.read_file(gdir/'e1402pg.shp').set_crs(26714,allow_override=True).to_crs(METRIC)
 checks=[]
 for source,layer,key,stored in [('physiography',fis,'CLAVE','EXT_PHYS_clave'),('geology',geo,'CLAVE','EXT_GEOL_clave')]:
  ov=gpd.overlay(p[[ID,'geometry']],layer[[key,'geometry']],how='intersection');ov['a']=ov.area;areas=p.set_index(ID).area;sm=ov.groupby(ID).a.sum()/areas;idx=ov.groupby(ID).a.idxmax();dom=ov.loc[idx].set_index(ID)[key]
  for pid in p[ID]:checks.append({ID:pid,'source':source,'sum_intersection_fraction':sm.get(pid,np.nan),'recomputed_dominant':dom.get(pid,np.nan),'stored_dominant':old.set_index(ID).loc[pid,stored],'dominant_matches':str(dom.get(pid))==str(old.set_index(ID).loc[pid,stored]),'geometry_valid':bool(layer.geometry.is_valid.all())})
 chk=pd.DataFrame(checks);chk.to_csv(TAB/'09_vector_overlay_validation.csv',index=False)

 # 6 transversal classification/actions.
 action=pd.DataFrame([
 ['Fisiografia','Homogeneidad verdadera a la escala de la fuente','All parcels Eje Neovolcánico; only province hierarchy downloaded','Do not use for clustering; seek subprovince/topoform layer if desired'],
 ['Geologia','No material processing problem; regional thematic resolution','197 valid, 10 dominant codes; overlays match','Usable cautiously; categorical plus structure distances'],
 ['Hidrografia','Fuera de cobertura','0/197 inside RH26Dp','Obtain national subbasin polygons and corresponding 1:50k networks'],
 ['Humedales','Dentro de extent without thematic coverage','2/197 intersect UV coverage polygons','Do not infer dryness; use only sensitivity/individual context'],
 ['Localidades','Valid context; partial redundancy among radii','197/197; numeric diversity within states','Keep compact subset and separate contextual block'],
 ['Suelo RGB','Datos no interpretables','Pixel support adequate but no class legend/lookup','Obtain vector/classified edaphology product plus data dictionary'],
 ['Hidrologia subterranea RGB','Datos no interpretables','Pixel support adequate but no class legend/lookup','Obtain vector/classified groundwater units plus data dictionary'],
 ['ENA','Resolución temática/ecological scale insufficient','National/state aggregates, no parcel link','Keep external contextual table only']
    ],columns=['dimension','primary_cause','evidence','pending_action']);action.to_csv(TAB/'10_transversal_diagnosis_actions.csv',index=False)
 make_figures(pix,hd,wet,loc,corr,chk)
 report(pix,hd,wet,loc,corr,chk,action,needs)
 manifest={'version':'c0_c1_review_v2','base_artifacts_modified':False,'parcel_count':197,'rgb_features_added_to_research_matrix':False,'hydro_subbasins_identified':['RH26Dp excluded'],'exact_missing_subbasin_codes_status':'requires official national subbasin polygon layer; not inferred','clustering_or_models_run':False}
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8');print(f'C0-C1 review v2 complete: {OUT}')

def make_figures(pix,hd,wet,loc,corr,chk):
 fig,ax=plt.subplots(1,2,figsize=(11,4));
 for a,(src,g) in zip(ax,pix.groupby('source')):sns.histplot(g.intersected_cells,ax=a);a.set_title(src);a.set_xlabel('Celdas intersectadas por parcela')
 fig.tight_layout();fig.savefig(FIG/'01_rgb_pixel_support.png',dpi=180);plt.close(fig)
 fig,ax=plt.subplots(1,2,figsize=(11,4));
 for a,(src,g) in zip(ax,pix.groupby('source')):sns.scatterplot(g,x='intersected_cells',y='unique_rgb_triplets',ax=a);a.set_title(src)
 fig.tight_layout();fig.savefig(FIG/'02_rgb_variation_not_classes.png',dpi=180);plt.close(fig)
 plt.figure(figsize=(7,4));sns.histplot(hd.distance_to_RH26Dp_boundary_m/1000);plt.xlabel('Distancia a RH26Dp (km)');plt.title('Las parcelas están fuera de la red descargada');plt.tight_layout();plt.savefig(FIG/'03_distance_to_downloaded_hydrography.png',dpi=180);plt.close()
 if len(wet):
  w=wet.set_index(ID)[[c for c in wet if c.endswith('intersection_fraction')]];w.plot.bar(figsize=(8,4));plt.ylabel('Fracción de parcela');plt.tight_layout();plt.savefig(FIG/'04_two_wetland_parcels_intersections.png',dpi=180);plt.close()
 plt.figure(figsize=(7,6));sns.heatmap(corr,annot=True,fmt='.2f',vmin=-1,vmax=1,cmap='coolwarm');plt.title('Redundancia de variables de localidades');plt.tight_layout();plt.savefig(FIG/'05_locality_redundancy.png',dpi=180);plt.close()
 plt.figure(figsize=(7,4));sns.histplot(loc,x='EXT_LOC_distance_urban_m',hue='Estado',element='step');plt.xlabel('Distancia a localidad urbana (m)');plt.tight_layout();plt.savefig(FIG/'06_locality_distance_by_state.png',dpi=180);plt.close()

def report(pix,hd,wet,loc,corr,chk,action,needs):
 ps=pix.groupby('source').agg(intersected_min=('intersected_cells','min'),intersected_median=('intersected_cells','median'),intersected_max=('intersected_cells','max'),contained_median=('fully_contained_cells','median'),effective_median=('effective_cells_area_weighted','median'),coverage_min=('valid_coverage_fraction','min'),unique_rgb_median=('unique_rgb_triplets','median'),shared_cells_parcels=('cells_shared_with_other_parcel',lambda x:(x>0).sum()),same_signature_max=('parcels_with_same_diagnostic_rgb_signature','max')).reset_index()
 overlay=chk.groupby('source').agg(n=(ID,'size'),fraction_min=('sum_intersection_fraction','min'),fraction_median=('sum_intersection_fraction','median'),fraction_max=('sum_intersection_fraction','max'),dominant_match_rate=('dominant_matches','mean'),all_valid=('geometry_valid','all')).reset_index()
 wrec=wet.fillna('NA').to_dict('records');lr=loc.groupby('Estado').agg(n=(ID,'size'),nearest_names=('EXT_LOC_nearest_name','nunique'),median_any_m=('EXT_LOC_distance_any_m','median'),median_urban_m=('EXT_LOC_distance_urban_m','median'),median_n_1km=('EXT_LOC_count_1000m','median'),median_n_3km=('EXT_LOC_count_3000m','median'),median_n_5km=('EXT_LOC_count_5000m','median')).reset_index()
 txt=f"""# Complemento C0-C1 v2 — resolución y cobertura

## Resumen

La imposibilidad de usar suelo e hidrología subterránea **no se debe a falta de píxeles ni cobertura**. El soporte es: {ps.round(3).to_dict('records')}. Cada parcela intersecta múltiples celdas y existe variación RGB, pero esos valores son simbología cartográfica renderizada. Medias, extremos y desviaciones RGB mezclan colores de clase, texto, bordes, sombreado y antialiasing; no tienen unidad física ni orden temático. Se calcularon sólo como diagnóstico y no se incorporaron a ninguna matriz de features.

No se encontró en `data/externo/suelo` o `hidrologia_subterranea` una leyenda digital, tabla color→clave, VAT, raster categórico o diccionario enlazable. Para recuperar clases se requiere el producto vectorial oficial o un ráster de códigos con leyenda estable. Una imagen/leyenda visual aislada todavía exigiría georreferenciación y validación de colores, no una clasificación improvisada.

## Hidrografía

Las 197 parcelas están fuera de RH26Dp; distancia a su límite: mínimo={hd.distance_to_RH26Dp_boundary_m.min()/1000:.2f} km, mediana={hd.distance_to_RH26Dp_boundary_m.median()/1000:.2f} km. Los archivos existentes sólo permiten excluir RH26Dp. **No permiten identificar con seguridad los códigos reales de subcuenca**, porque falta el mosaico nacional de límites; no se infirieron por municipio. Archivos requeridos: {needs.to_dict('records')}. Después deben descargarse las redes 1:50,000 correspondientes y conservar un buffer completo de al menos 2 km.

Variables futuras prioritarias: distancia a corriente total/perenne/intermitente, cuerpo de agua y canal; orden de corriente; longitud/densidad dentro de 0.5/1/2 km; indicador de buffer completo. Proximidad no será tratada como riego o humedad efectiva.

## Las dos parcelas de humedales

Detalle: {wrec}. Su cobertura válida proviene de polígonos de uso del suelo `uv` —agricultura de temporal anual— y el archivo registra además las intersecciones separadas con humedal (`hm`), cuerpo de agua/inundación (`ca`) y zonificación (`zh`). Por tanto el archivo `05_two_wetland_parcels_detail.csv` permite distinguir si realmente son humedales o sólo están dentro del contexto cartográfico. No se generaliza a partir de n=2. No existen otras parcelas a ≤3 km; las cinco más cercanas y comparaciones supervisadas sólo cuando TRAIN están en `06_wetland_parcel_nearest_neighbors.csv`.

## Localidades

Diversidad por estado: {lr.round(2).to_dict('records')}. Los radios 1/3/5 km son acumulativos y correlacionados; ver `08_locality_spearman_redundancy.csv`. Para C2 conviene una representación compacta: distancia rural, distancia urbana y uno de los conteos (preferentemente 3 km), más ámbito de la localidad más cercana. Mantener el bloque separado: asentamientos no miden infraestructura o manejo.

## Geología y fisiografía

Validación de overlays: {overlay.round(4).to_dict('records')}. Las proporciones se recalcularon mediante intersección y las unidades dominantes coinciden con C1. Fisiografía es homogénea porque el producto descargado sólo contiene nivel provincia y todas las parcelas están en Eje Neovolcánico; no es un fallo técnico. Geología sí distingue diez códigos dominantes a escala 1:250,000.

## Diagnóstico transversal

La clasificación completa está en `10_transversal_diagnosis_actions.csv`: {action.to_dict('records')}.

## Recomendación para C2

Usar geología + topografía FIRA y un bloque compacto de localidades. Excluir fisiografía constante, hidrografía sin cobertura, RGB no interpretables y ENA agregado. Humedales sólo como sensibilidad/estudio de casos, no como eje de clustering global. No codificar faltantes de cobertura como cero. C2 debe seguir esperando las redes hidrográficas correctas y clases oficiales de suelo si el objetivo es un clustering físico completo.
""";(REP/'c0_c1_review_v2_report.md').write_text(txt,encoding='utf-8')
 rec="""# Recomendaciones actualizadas para C2

1. Representación territorial mínima disponible: geología dominante/clase/tipo, distancias a estructuras, topografía FIRA y localidades compactas.
2. Tratar geología como categórica sin orden; escalar distancias de forma robusta y considerar `log1p` dentro del pipeline.
3. No incluir provincia fisiográfica: es constante por resolución jerárquica.
4. No incluir RH26Dp ni sustituir NA por cero. Incorporar hidrografía sólo después de obtener límites y redes correctos con buffers completos.
5. No incluir RGB ni sus estadísticas diagnósticas. Incorporar suelo/agua subterránea sólo mediante códigos oficiales verificables.
6. No usar las dos parcelas con cobertura de humedales para definir clusters globales; pueden documentarse como casos.
7. Localidades: usar distancia rural, urbana y conteo a 3 km; comprobar sensibilidad a 1/5 km y mantener interpretación contextual.
8. Clustering siempre target-free; medir estabilidad, tamaños efectivos y confusión con Estado/cobertura antes de examinar Y.
""";(REP/'recommendations_c2_updated.md').write_text(rec,encoding='utf-8')

if __name__=='__main__':main()
