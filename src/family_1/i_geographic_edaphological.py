"""Section I: reproducible descriptive spatial research; no yield models."""
from pathlib import Path
import json, itertools, re, unicodedata
import numpy as np
import pandas as pd
import geopandas as gpd
import pyogrio
from scipy.spatial import cKDTree
from scipy.spatial.distance import pdist, squareform
from shapely import union_all
from .climate_signal_features import ROOT, ID, MASTER, sha, supervised_data, TARGET
from .climate_signal_descriptive import geography

NAME='i_climate_conditioned_geographic_edaphological'
OUT=ROOT/'outputs/research/family_1'/NAME/'v1'
DATA=ROOT/'data/processed/family_1'/NAME/'v1'
SOURCE=ROOT/'data/externo/suelo/inegi_serie_iii_794551118313'
AREA_CRS='+proj=laea +lat_0=19.75 +lon_0=-98.4 +datum=WGS84 +units=m +no_defs'
ATTRS=['Grupo1','Califp_g1','Califs_g1','Grupo2','Califp_g2','Califs_g2','Grupo3','Califp_g3','Clase_tex','Lmte_sup','Fase_fis_u','Fase_qui_u']
ABSENT={'N','N/A','','None','nan'}

def setup():
    for p in [OUT,OUT/'tables',OUT/'figures',OUT/'interactive',DATA]:p.mkdir(parents=True,exist_ok=True)

def download_official_source():
    """Retrieve the published official archive if the local audited copy is absent."""
    import requests,zipfile
    SOURCE.mkdir(parents=True,exist_ok=True)
    archive=SOURCE/'794551118313_s.zip'
    if not archive.exists():
        metadata=requests.get('https://www.inegi.org.mx/app/api/productos/interna_v2/ficha/datos',params={'upc':'794551118313','lang':'false'},timeout=60).json()
        url='https://www.inegi.org.mx'+metadata['info']['generales']['formatos'][0]['url']['valor']
        (SOURCE/'product_metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
        response=requests.get(url,stream=True,timeout=180);response.raise_for_status()
        temporary=archive.with_suffix('.download')
        with temporary.open('wb') as f:
            for chunk in response.iter_content(1024*1024):f.write(chunk)
        temporary.replace(archive)
    if sha(archive)!='9277315fd3bf82ca49f089798428ca1ffa6a23f5b668c74df8ae74a95a087926':raise ValueError('Official archive changed; review source version')
    if not list(SOURCE.rglob('*area.shp')):
        with zipfile.ZipFile(archive) as z:
            if any(not (SOURCE/n).resolve().is_relative_to(SOURCE.resolve()) for n in z.namelist()):raise ValueError('Unsafe archive member')
            z.extractall(SOURCE)

def write(frame,name):
    frame.to_csv(OUT/'tables'/f'{name}.csv',index=False,encoding='utf-8-sig')
    return frame

def markdown_table(frame):
    def cell(x):return f'{x:.4f}' if isinstance(x,float) else str(x).replace('|','/')
    lines=['| '+' | '.join(frame.columns)+' |','| '+' | '.join(['---']*len(frame.columns))+' |']
    return '\n'.join(lines+['| '+' | '.join(cell(x) for x in row)+' |' for row in frame.itertuples(index=False,name=None)])

def protected():
    from concurrent.futures import ThreadPoolExecutor
    paths=[]
    for prefix in ['data/original','outputs/modeling','data/processed/family_1','src/family_1','documentation']:
        paths.extend(p for p in (ROOT/prefix).rglob('*') if p.is_file() and NAME not in str(p) and 'i_geographic_edaphological' not in p.name and not p.name.startswith('i_') and '__pycache__' not in str(p))
    ordered=sorted(set(paths))
    with ThreadPoolExecutor(max_workers=8) as pool:
        return dict(zip([str(p.relative_to(ROOT)) for p in ordered],pool.map(sha,ordered)))

def variance_parts(x,groups):
    x=np.asarray(x,dtype=float);groups=np.asarray(groups)
    total=float(np.sum((x-x.mean())**2))
    between=sum(np.sum(groups==k)*(x[groups==k].mean()-x.mean())**2 for k in np.unique(groups))
    return dict(ss_total=total,ss_between=float(between),ss_within=float(total-between),between_fraction=float(between/total) if total else np.nan,n=len(x),n_groups=len(np.unique(groups)))

def correlation(x,y,method='pearson'):
    z=pd.DataFrame({'x':np.asarray(x),'y':np.asarray(y)}).dropna()
    return float(z.x.corr(z.y,method=method)) if len(z)>2 and z.x.std()>1e-12 and z.y.std()>1e-12 else np.nan

def record_execution():
    import sys,scipy,shapely,pyproj,plotly
    paths=[Path(__file__),ROOT/'scripts/modeling/323_i_soil_representation.py',ROOT/'scripts/modeling/324_i_geographic_edaphological_exploration.py']
    manifest=dict(section='I',yield_models_fitted=0,hidden_targets_used=False,n_parcels=197,n_labeled=138,n_climate_profiles=53,
        software=dict(python=sys.version,pandas=pd.__version__,numpy=np.__version__,geopandas=gpd.__version__,scipy=scipy.__version__,shapely=shapely.__version__,pyproj=pyproj.__version__,plotly=plotly.__version__),code_sha256={str(p.relative_to(ROOT)):sha(p) for p in paths},commands=['python scripts/modeling/323_i_soil_representation.py','python scripts/modeling/324_i_geographic_edaphological_exploration.py'],protected_inputs_verified=True)
    (OUT/'execution_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')

def structure(wide):
    rows=[]
    for pid,x in wide.iterrows():
        valid=x[x>0].sort_index().sort_values(ascending=False,kind='stable');coverage=float(x.sum())
        if coverage>1+1e-7:raise ValueError('Overlapping soil polygons')
        q=valid/coverage if coverage else valid
        rows.append({ID:pid,'soil_unit_count':len(valid),'soil_dominant_unit':valid.index[0] if len(valid) else None,
          'soil_dominant_share':float(valid.iloc[0]) if len(valid) else np.nan,
          'soil_second_unit':valid.index[1] if len(valid)>1 else None,'soil_second_share':float(valid.iloc[1]) if len(valid)>1 else 0.,
          'soil_mixed_share':1-float(valid.iloc[0]) if len(valid) else np.nan,
          'soil_entropy':float(-(q*np.log(q)).sum()) if coverage else np.nan,
          'soil_unclassified_share':max(0.,1-coverage)})
    return pd.DataFrame(rows)

def soil_dictionary(st,attrs):
    definitions={
        'soil_unit_count':'count(p_ij > 0), including all small intersections',
        'soil_dominant_unit':'argmax coverage; lexical key resolves ties deterministically',
        'soil_dominant_share':'max_j p_ij; NaN if no valid coverage',
        'soil_second_unit':'second key ordered by coverage descending, lexical ties; null if absent',
        'soil_second_share':'second coverage; zero if no second unit',
        'soil_mixed_share':'1 - dominant share; includes separately documented unclassified area',
        'soil_entropy':'-sum(q_j ln(q_j)), q_j=p_ij/sum(p_ij) over positive valid shares; missing area NOT redistributed in full matrix',
        'soil_unclassified_share':'max(0, 1-sum_j p_ij); coverage checked before zeros assigned',
        'soil_boundary_distance_m':'minimum parcel-polygon distance to dissolved cartographic unit boundary; AOI clipped 2km beyond parcels',
        'soil_assignment_reserve':'any parcel area within 125m boundary scenario; not a measured accuracy probability',
        'soil_dominant_principal_group':'official Grupo1 of dominant cartographic unit; not measured physical dominance in parcel',
        'soil_dominant_texture':'official Clase_tex of dominant unit: 1 coarse / 2 medium / 3 fine',
        'soil_dominant_physical_phase':'official Fase_fis_u of dominant unit; N absence in mapped nomenclature',
        'soil_dominant_chemical_phase':'official Fase_qui_u of dominant unit; N absence in mapped nomenclature, not a lab value',
        'soil_dominant_key_found_in_E1402_text':'exact key found in whitespace-normalized local PDF text; does not verify geometric registration',
        'soil_share_key_not_found_in_E1402_text':'sum of coverage of official units whose exact keys were not found in local E1402 text; no automatic qualifier substitution'}
    rows=[]
    for c in list(st.columns)+list(attrs.columns):
        if c==ID:continue
        if 'share_mentions' in c:definition='sum_j p_ij * I(official unit j mentions code); association coverage, NOT fraction of component soil; sums across group codes can exceed 1'
        elif 'map_presence' in c:definition='I(any p_ij >0 for official unit mentioning code); cartographic presence only'
        elif 'boundary_buffer' in c:definition='area(parcel intersect boundary buffer of indicated metres) / parcel area in LAEA; sensitivity scenario, not accuracy estimate'
        else:definition=definitions[c]
        units='metres' if c.endswith('_m') else 'nats' if c=='soil_entropy' else 'fraction 0-1' if 'share' in c else 'boolean' if 'presence' in c or 'reserve' in c or 'found_in' in c else 'count' if c=='soil_unit_count' else 'categorical code'
        rows.append(dict(feature=c,definition=definition,units=units,source='INEGI Serie III official vector; E1402 PDF text for edition comparison',scope='197 target-free parcels',warning='1:250000; no point laboratory values assigned; see source edition and boundary reserves'))
    return write(pd.DataFrame(rows),'07_soil_dictionary')

def soil():
    setup();download_official_source();g=geography();src=next(SOURCE.rglob('*area.shp'));info=pyogrio.read_info(src)
    projected=g.to_crs(info['crs']);bounds=projected.total_bounds+np.array([-2000,-2000,2000,2000])
    s=gpd.read_file(src,bbox=tuple(bounds));invalid=int((~s.is_valid).sum())
    if invalid or s.crs is None:raise ValueError('Official vector requires geometry/CRS review')
    s['Clave_wrb']=s.Clave_wrb.str.strip()
    # Every repeated key must have the same thematic attributes before dissolving.
    if (s.groupby('Clave_wrb')[ATTRS].nunique(dropna=False)>1).any().any():raise ValueError('Inconsistent official keys')
    legend=s.drop_duplicates('Clave_wrb')[['Clave_wrb']+ATTRS].sort_values('Clave_wrb')
    import pymupdf
    dictionary='\n'.join(p.get_text() for p in pymupdf.open(next(SOURCE.rglob('702825092023.pdf'))))
    (OUT/'official_dictionary.txt').write_text(dictionary,encoding='utf-8')
    annex=dictionary[dictionary.rfind('B. Listado de grupos de suelo'):]
    names=dict(re.findall(r'\n([A-Za-z]{2,3})\s*\n([^\n]+)',annex))
    write(pd.DataFrame([dict(code=k,name=v.strip()) for k,v in names.items()]),'01_official_code_names')
    pdf=(ROOT/'outputs/data_audit/soil_pdf_review/e1402.txt').read_text(encoding='utf-8')
    compact=re.sub(r'\s+','',pdf)
    legend['key_found_in_E1402_text']=legend.Clave_wrb.map(lambda x:re.sub(r'\s+','',x) in compact)
    write(legend,'02_unit_legend_audit')
    from shapely.geometry import box
    # Clip only derived geometries, 2km beyond parcels. Artificial edges cannot
    # affect the <=250m boundary sensitivity around any parcel.
    clip=box(*bounds)
    s.geometry=s.geometry.intersection(clip)
    s=s[~s.geometry.is_empty].copy()
    s.to_file(DATA/'official_soil_aoi.gpkg',layer='soil',driver='GPKG')
    area=g.to_crs(AREA_CRS);units=s.dissolve(by='Clave_wrb',aggfunc='first').to_crs(AREA_CRS)
    rows=[]
    for _,a in area.iterrows():
        for j in units.sindex.query(a.geometry,predicate='intersects'):
            u=units.iloc[j];intersection=a.geometry.intersection(u.geometry);m=intersection.area
            if m>0:
                rows.append({ID:a[ID],'unidad_edafologica':units.index[j],'area_interseccion_m2':m,'area_parcela_m2':a.geometry.area,'porcentaje_parcela':m/a.geometry.area,**{c:u[c] for c in ATTRS}})
    long=pd.DataFrame(rows);write(long,'03_all_intersections');long.to_parquet(DATA/'soil_intersections_long.parquet',index=False)
    wide=long.pivot_table(index=ID,columns='unidad_edafologica',values='porcentaje_parcela',aggfunc='sum',fill_value=0).reindex(g[ID],fill_value=0).sort_index(axis=1)
    if not np.allclose(wide.sum(axis=1),1,atol=1e-6):raise ValueError('Incomplete or overlapping official coverage: inspect intersections')
    wide.reset_index().to_parquet(DATA/'soil_full_composition.parquet',index=False);write(wide.reset_index(),'04_full_composition')
    st=structure(wide)
    printed=legend.set_index('Clave_wrb').key_found_in_E1402_text
    st['soil_dominant_key_found_in_E1402_text']=st.soil_dominant_unit.map(printed)
    unmatched=[u for u in wide if not printed.loc[u]]
    st['soil_share_key_not_found_in_E1402_text']=wide[unmatched].sum(axis=1).reindex(st[ID]).to_numpy()
    # Dissolved cartographic boundaries; same-key internal polygon seams excluded.
    boundaries=union_all(units.geometry.boundary.to_numpy())
    st['soil_boundary_distance_m']=area.set_index(ID).geometry.reindex(st[ID]).map(lambda x:x.distance(boundaries)).to_numpy()
    edge=gpd.GeoSeries([clip],crs=s.crs).to_crs(AREA_CRS).iloc[0].boundary
    qa=pd.DataFrame({ID:st[ID],'aoi_artificial_edge_distance_m':area.set_index(ID).geometry.reindex(st[ID]).map(lambda x:x.distance(edge)).to_numpy(),'soil_boundary_distance_m':st.soil_boundary_distance_m})
    qa['artificial_edge_is_farther']=qa.aoi_artificial_edge_distance_m>qa.soil_boundary_distance_m+1
    write(qa,'49_boundary_aoi_edge_check')
    if not qa.artificial_edge_is_farther.all():raise ValueError('AOI clipping may censor boundary distances; enlarge source window')
    local_boundary=boundaries.intersection(union_all(area.geometry.buffer(300).to_numpy()))
    for radius in [50,125,250]:
        buffered=local_boundary.buffer(radius)
        st[f'soil_boundary_buffer_{radius}m_share']=area.set_index(ID).geometry.reindex(st[ID]).map(lambda x:x.intersection(buffered).area/x.area).to_numpy()
    st['soil_assignment_reserve']=st.soil_boundary_buffer_125m_share>0
    # Source codes describe associations, never a measured component-soil fraction.
    attrs=pd.DataFrame(index=wide.index);lookup=legend.set_index('Clave_wrb')
    specs={'group':['Grupo1','Grupo2','Grupo3'],'qualifier':['Califp_g1','Califs_g1','Califp_g2','Califs_g2','Califp_g3'],'texture':['Clase_tex'],'surface_limit':['Lmte_sup'],'physical_phase':['Fase_fis_u'],'chemical_phase':['Fase_qui_u']}
    for family,cols in specs.items():
        codes=sorted({str(lookup.loc[u,c]) for u in wide for c in cols}-ABSENT)
        for code in codes:
            selected=[u for u in wide if code in set(str(lookup.loc[u,c]) for c in cols)]
            attrs[f'soil_map_share_mentions_{family}_{code}']=wide[selected].sum(axis=1)
            attrs[f'soil_map_presence_{family}_{code}']=(wide[selected]>0).any(axis=1).astype(int)
    st['soil_dominant_principal_group']=st.soil_dominant_unit.map(lookup.Grupo1)
    st['soil_dominant_texture']=st.soil_dominant_unit.map(lookup.Clase_tex)
    st['soil_dominant_physical_phase']=st.soil_dominant_unit.map(lookup.Fase_fis_u)
    st['soil_dominant_chemical_phase']=st.soil_dominant_unit.map(lookup.Fase_qui_u)
    write(st,'05_soil_structure');st.to_parquet(DATA/'soil_structure.parquet',index=False)
    write(attrs.reset_index(),'06_soil_attributes');attrs.reset_index().to_parquet(DATA/'soil_attributes.parquet',index=False)
    audit=dict(source=str(src.relative_to(ROOT)),source_sha256=sha(src),archive_sha256=sha(SOURCE/'794551118313_s.zip'),source_crs=info['crs'],area_crs=AREA_CRS,n_aoi_polygons=len(s),invalid_geometries=invalid,n_intersections=len(long),n_units=wide.shape[1],coverage_min=float(wide.sum(axis=1).min()),coverage_max=float(wide.sum(axis=1).max()),crossing_parcels=int((st.soil_unit_count>1).sum()),near_125m=int(st.soil_assignment_reserve.sum()),scale='1:250000',reconstruction='Official vector; no RGB classification or PDF boundary digitization',compatibility='Same Serie III / WRB2014 / coverage2021; national edition2024 vs E1402 print2025. Keys text-audited; exact graphic-registration equivalence not asserted.',buffer_note='50/125/250m = 0.2/0.5/1mm at map scale; sensitivity scenarios, not accuracy estimates')
    (OUT/'soil_audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False),encoding='utf-8')
    soil_dictionary(st,attrs)
    return audit

def localities(g):
    sources=[];inventory=[]
    for p in sorted((ROOT/'data/externo/localidades').glob('loc_*.csv')):
        z=pd.read_csv(p,dtype=str);z['source']=str(p.relative_to(ROOT));sources.append(z)
        inventory.append(dict(source=str(p.relative_to(ROOT)),n=len(z),columns='|'.join(z.columns),source_sha256=sha(p),date='not supplied',geometry='points; no locality boundaries',crs='decimal lat/lon, assumed WGS84; not documented by these CSVs'))
    write(pd.DataFrame(inventory),'10_locality_inventory')
    z=pd.concat(sources,ignore_index=True).drop_duplicates('CVEGEO').sort_values('CVEGEO')
    lon=pd.to_numeric(z.LON_DECIMAL,errors='coerce');lat=pd.to_numeric(z.LAT_DECIMAL,errors='coerce');valid=lon.between(-180,180)&lat.between(-90,90)
    z=gpd.GeoDataFrame(z[valid].copy(),geometry=gpd.points_from_xy(lon[valid],lat[valid]),crs=4326).to_crs(g.crs)
    centers=g.geometry.centroid;xy=np.c_[centers.x,centers.y];lxy=np.c_[z.geometry.x,z.geometry.y]
    distance,index=cKDTree(lxy).query(xy,k=2);nearest=z.iloc[index[:,0]].reset_index(drop=True)
    out=pd.DataFrame({ID:g[ID].to_numpy(),'locality_CVEGEO':nearest.CVEGEO,'locality_name':nearest.NOM_LOC,'locality_municipality':nearest.NOM_MUN,'locality_state':nearest.NOM_ENT,'locality_distance_m':distance[:,0],'locality_second_distance_m':distance[:,1],'locality_source':nearest.source})
    out['locality_method']='Nearest point to parcel centroid in EPSG6372; proximity, not membership'
    out['locality_confidence']=np.where((distance[:,0]<=1000)&(distance[:,1]-distance[:,0]>=250),'near, separated reference point; administrative membership unverified','proximity only; distant or ambiguous')
    def norm(s):return ''.join(c for c in unicodedata.normalize('NFKD',str(s).upper()) if not unicodedata.combining(c)).strip()
    out['locality_municipality_agrees']=[norm(a)==norm(b) for a,b in zip(out.locality_municipality,g.Municipio)]
    old=pd.read_parquet(ROOT/'data/processed/phase_c/c0_c1/external_parcel_features.parquet')
    out=out.merge(old[[ID,'EXT_LOC_distance_any_m','EXT_LOC_nearest_name']],on=ID,validate='one_to_one')
    out['previous_distance_abs_difference_m']=(out.locality_distance_m-out.EXT_LOC_distance_any_m).abs()
    out['previous_distance_method']='Minimum parcel-polygon to locality-point distance in phase C; not centroid distance'
    out['previous_nearest_name_agrees']=[norm(a)==norm(b) for a,b in zip(out.locality_name,out.EXT_LOC_nearest_name)]
    write(out,'11_locality_references');out.to_parquet(DATA/'locality_references.parquet',index=False)
    return out

def pair_indices(groups):
    return np.array([(a,b) for k in np.unique(groups) for a,b in itertools.combinations(np.flatnonzero(groups==k),2)],dtype=int)

def topn(wide,groups,areas):
    pairs=pair_indices(groups);full=squareform(pdist(wide.to_numpy(),metric='cityblock'))/2
    allpairs=np.array(list(itertools.combinations(range(len(wide)),2)))
    rows=[];ranks=pd.DataFrame({'unit':wide.columns,'parcel_count':(wide>0).sum().values,'area_m2':wide.mul(areas,axis=0).sum().values,'mean_share':wide.mean().values})
    write(ranks,'20_unit_prevalence')
    orders={c:ranks.sort_values([c,'unit'],ascending=[False,True]).unit.tolist() for c in ['parcel_count','area_m2','mean_share']}
    maxunits=int((wide>0).sum(axis=1).max())
    for method in ['per_parcel']+list(orders):
        limits=range(1,maxunits+1) if method=='per_parcel' else range(1,wide.shape[1]+1)
        for n in limits:
            retained=wide.copy()*0;slots=[]
            for pid,x in wide.iterrows():
                chosen=x[x>0].sort_index().sort_values(ascending=False,kind='stable').index[:n] if method=='per_parcel' else orders[method][:n]
                retained.loc[pid,chosen]=x[chosen]
                if method=='per_parcel':
                    row={ID:pid}
                    for k,u in enumerate(chosen,1):row[f'soil_top{k}_unit']=u;row[f'soil_top{k}_share']=x[u]
                    row['soil_remaining_share']=1-retained.loc[pid].sum();slots.append(row)
            remaining=1-retained.sum(axis=1)
            representation=retained.copy();representation['soil_remaining_share']=remaining
            distance=squareform(pdist(representation.to_numpy(),metric='cityblock'))/2
            for tol in [.01,.05,.10]:
                f=full[allpairs[:,0],allpairs[:,1]]>tol;r=distance[allpairs[:,0],allpairs[:,1]]>tol
                fp=full[pairs[:,0],pairs[:,1]]>tol;rp=distance[pairs[:,0],pairs[:,1]]>tol
                rows.append(dict(method=method,N=n,tv_tolerance=tol,area_coverage=float(np.sum(retained.sum(axis=1)*areas)/np.sum(areas)),parcels_represented=float((retained.sum(axis=1)>0).mean()),mean_omitted_share=float(remaining.mean()),max_omitted_share=float(remaining.max()),units_dropped=int((retained.sum()==0).sum()),pairs_full_distinguished=int(f.sum()),pairs_distinguished=int(r.sum()),pairs_lost=int((f&~r).sum()),pairs_added_by_reduction=int((~f&r).sum()),within_profile_full_distinguished=int(fp.sum()),within_profile_distinguished=int(rp.sum()),within_profile_lost=int((fp&~rp).sum()),within_profile_added_by_reduction=int((~fp&rp).sum())))
            table=pd.DataFrame(slots) if method=='per_parcel' else representation.loc[:,representation.any()].reset_index()
            table.to_parquet(DATA/f'soil_topn_{method}_{n}.parquet',index=False)
            write(pd.DataFrame({ID:wide.index,'omitted_share':remaining.to_numpy()}),f'21_omitted_{method}_{n}')
    return write(pd.DataFrame(rows),'22_topn_comparison')

def explore():
    setup();before=protected();g=geography().sort_values(ID).reset_index(drop=True);m=pd.read_csv(MASTER)
    # Gate supervised rows using the existing helper before accessing Y.
    train=supervised_data(pd.DataFrame({ID:g[ID]}),m)[[ID,TARGET]]
    if len(train)!=138:raise ValueError('Expected 138 labeled parcels')
    membership=pd.read_csv(ROOT/'outputs/modeling/family_1/h_joint_climate_signal/v1/tables/06_profile_memberships.csv')
    if membership.rain.nunique()!=53 or not membership.rain.equals(membership.joint):raise ValueError('Climate partition changed')
    topo=pd.read_parquet(ROOT/'data/processed/family_1/features/topography_basic_features.parquet')
    st=pd.read_parquet(DATA/'soil_structure.parquet');attrs=pd.read_parquet(DATA/'soil_attributes.parquet');wide=pd.read_parquet(DATA/'soil_full_composition.parquet').set_index(ID).reindex(g[ID])
    loc=localities(g)
    d=g.drop(columns='geometry').drop(columns='CONJUNTO').merge(m[[ID,'AREA_HA','CONJUNTO']],on=ID,validate='one_to_one').merge(membership[[ID,'rain']],on=ID).rename(columns={'rain':'climate_profile'}).merge(topo,on=ID).merge(st,on=ID).merge(attrs,on=ID).merge(loc,on=ID).merge(train,on=ID,how='left')
    unit_frame=wide.add_prefix('soil_unit_share__').reset_index()
    d=d.merge(unit_frame,on=ID,validate='one_to_one')
    d['soil_all_units_summary']=d[ID].map(wide.apply(lambda x:'; '.join(f'{u}: {v:.2%}' for u,v in x.items() if v>0),axis=1))
    d['altitude_m']=d.TOPO_BASIC_elevation_mean;d['slope_degrees']=d.TOPO_BASIC_slope_mean
    for c in ['altitude_m','slope_degrees']:d[c+'_within_profile_all197']=d[c]-d.groupby('climate_profile')[c].transform('mean')
    d.to_parquet(DATA/'integrated_diagnostic_197.parquet',index=False);write(d,'30_integrated_diagnostic_197')
    labeled=d[d.CONJUNTO.eq('ENTRENAMIENTO')].copy()
    if d.loc[d.CONJUNTO.eq('PREDICCION'),TARGET].notna().any():raise ValueError('Hidden labels leaked')
    yparts=variance_parts(labeled[TARGET],labeled.climate_profile);write(pd.DataFrame([yparts]),'31_y_variance_decomposition_138')
    regional_variance=[]
    for field in ['Estado','Municipio']:
        for region,z in labeled.groupby(field):
            if len(z)>=5:regional_variance.append(dict(aggregation=field,name=region,**variance_parts(z[TARGET],z.climate_profile)))
    write(pd.DataFrame(regional_variance),'47_regional_y_variance')
    summaries=[]
    for profile,z in d.groupby('climate_profile'):
        row=dict(climate_profile=profile,n=len(z),n_labeled=z[TARGET].count(),states='|'.join(sorted(z.Estado.unique())),municipalities='|'.join(sorted(z.Municipio.unique())),localities='|'.join(sorted(z.locality_CVEGEO.unique())),n_soil_units=int((wide.loc[z[ID]].sum()>0).sum()),n_dominant_units=z.soil_dominant_unit.nunique(),n_boundary_reserve=int(z.soil_assignment_reserve.sum()))
        for c in ['altitude_m','slope_degrees',TARGET]:
            x=z[c];row.update({f'{c}_{k}':v for k,v in {'min':x.min(),'max':x.max(),'range':x.max()-x.min(),'mean':x.mean(),'sd':x.std()}.items()})
        summaries.append(row)
    profiles=write(pd.DataFrame(summaries),'32_profile_diagnostics')
    write(wide.groupby(d.set_index(ID).climate_profile).mean().reset_index(),'33_profile_mean_soil_composition')
    geo=[]
    for field in ['Estado','Municipio','locality_CVEGEO']:
        for k,z in d.groupby(field):
            observed=z[z.CONJUNTO.eq('ENTRENAMIENTO')]
            geo.append(dict(aggregation=field,name=k,n=len(z),n_labeled=len(observed),n_prediction=len(z)-len(observed),area_ha=z.AREA_HA.sum(),fraction_197=len(z)/197,fraction_138=len(observed)/138,n_profiles=z.climate_profile.nunique(),n_soil_units=int((wide.loc[z[ID]].sum()>0).sum()),altitude_range=z.altitude_m.max()-z.altitude_m.min(),slope_range=z.slope_degrees.max()-z.slope_degrees.min(),y_mean=observed[TARGET].mean() if len(observed)>=5 else np.nan,y_sd=observed[TARGET].std() if len(observed)>=5 else np.nan,y_min=observed[TARGET].min() if len(observed)>=5 else np.nan,y_max=observed[TARGET].max() if len(observed)>=5 else np.nan,sufficient_y_support=len(observed)>=5))
    regions=write(pd.DataFrame(geo),'34_territorial_concentration')
    areas=g.to_crs(AREA_CRS).set_index(ID).geometry.area.reindex(wide.index);comparison=topn(wide,d.climate_profile.to_numpy(),areas)
    pairs=pair_indices(d.climate_profile.to_numpy());w=wide.to_numpy();attribute_cols=[c for c in attrs if 'share_mentions' in c];a=d[attribute_cols].to_numpy();pair=[]
    for i,j in pairs:
        pair.append(dict(ID_A=d.iloc[i][ID],ID_B=d.iloc[j][ID],climate_profile=int(d.iloc[i].climate_profile),altitude_delta=abs(d.iloc[i].altitude_m-d.iloc[j].altitude_m),slope_delta=abs(d.iloc[i].slope_degrees-d.iloc[j].slope_degrees),soil_total_variation=float(np.abs(w[i]-w[j]).sum()/2),attribute_max_share_delta=float(np.abs(a[i]-a[j]).max()),boundary_reserve=bool(d.iloc[i].soil_assignment_reserve or d.iloc[j].soil_assignment_reserve)))
    pair=write(pd.DataFrame(pair),'35_identical_climate_pairs');sensitivity=[]
    for alt,slope,tol in [(10,.5,.01),(25,1,.05),(50,2,.10)]:
        t=(pair.altitude_delta>alt)|(pair.slope_delta>slope);u=pair.soil_total_variation>tol;v=pair.attribute_max_share_delta>tol
        sensitivity.append(dict(altitude_tolerance_m=alt,slope_tolerance_degrees=slope,soil_share_tolerance=tol,n_pairs=len(pair),topography=int(t.sum()),soil_units=int(u.sum()),soil_attributes=int(v.sum()),combined=int((t|u).sum()),soil_units_away_boundary_125m=int((u&~pair.boundary_reserve).sum()),soil_units_with_boundary_reserve=int((u&pair.boundary_reserve).sum()),profiles_soil_distinguished=pair.loc[u,'climate_profile'].nunique()))
    sensitivity=write(pd.DataFrame(sensitivity),'36_pair_tolerance_sensitivity')
    contributions=[]
    continuous=['altitude_m','slope_degrees','soil_entropy','soil_dominant_share','soil_unit_count','longitude','latitude']+attribute_cols+[c for c in d if c.startswith('soil_unit_share__')]
    for c in continuous:
        for scope,z in [('all_labeled',labeled),('Chignahuapan_labeled',labeled[labeled.Municipio.str.contains('Chignahuapan',case=False)])]:
            xc=z[c]-z.groupby('climate_profile')[c].transform('mean');yc=z[TARGET]-z.groupby('climate_profile')[TARGET].transform('mean')
            contributions.append(dict(feature=c,scope=scope,n=len(z),global_pearson=correlation(z[c],z[TARGET]),global_spearman=correlation(z[c],z[TARGET],'spearman'),within_profile_pearson=correlation(xc,yc),n_profiles_with_variation=int((z.groupby('climate_profile')[c].nunique()>1).sum()),role='descriptive associations; no causal or predictive interpretation'))
    write(pd.DataFrame(contributions),'37_descriptive_associations_138')
    categories=[];contrasts=[]
    for c in ['soil_dominant_unit','soil_dominant_principal_group','soil_dominant_texture','soil_dominant_physical_phase','soil_dominant_chemical_phase','Estado','Municipio','locality_CVEGEO']:
        for k,z in labeled.groupby(c):categories.append(dict(feature=c,category=k,n=len(z),n_profiles=z.climate_profile.nunique(),y_mean=z[TARGET].mean() if len(z)>=5 else np.nan,y_sd=z[TARGET].std() if len(z)>=5 else np.nan,support_at_least5=len(z)>=5))
        for profile,z in labeled.groupby('climate_profile'):
            counts=z[c].value_counts();supported=counts[counts>=3].index
            if len(supported)>=2:
                for aa,bb in itertools.combinations(supported,2):contrasts.append(dict(feature=c,profile=profile,category_a=aa,category_b=bb,n_a=int(counts[aa]),n_b=int(counts[bb]),y_mean_difference=z.loc[z[c].eq(aa),TARGET].mean()-z.loc[z[c].eq(bb),TARGET].mean(),role='within-profile descriptive contrast; >=3 per category; no significance claim'))
    write(pd.DataFrame(categories),'38_category_y_support');write(pd.DataFrame(contrasts,columns=['feature','profile','category_a','category_b','n_a','n_b','y_mean_difference','role']),'39_within_profile_category_contrasts')
    featureaudit=[]
    for c in continuous:
        var=variance_parts(d[c],d.climate_profile)
        featureaudit.append(dict(feature=c,**var,altitude_pearson=correlation(d[c],d.altitude_m),slope_pearson=correlation(d[c],d.slope_degrees),state_between_fraction=variance_parts(d[c],pd.factorize(d.Estado)[0])['between_fraction'],municipality_between_fraction=variance_parts(d[c],pd.factorize(d.Municipio)[0])['between_fraction'],locality_between_fraction=variance_parts(d[c],pd.factorize(d.locality_CVEGEO)[0])['between_fraction'],n_train_nonzero=int((labeled[c]!=0).sum()),n_prediction_nonzero=int((d.loc[d.CONJUNTO.eq('PREDICCION'),c]!=0).sum()),prediction_only=bool((labeled[c]==0).all() and (d.loc[d.CONJUNTO.eq('PREDICCION'),c]!=0).any())))
    write(pd.DataFrame(featureaudit),'40_feature_viability_dependence')
    freq=[]
    for u in wide:
        present=wide[u]>0;training=d.set_index(ID).CONJUNTO.eq('ENTRENAMIENTO')
        freq.append(dict(unit=u,n_total=int(present.sum()),n_train=int((present&training).sum()),n_prediction=int((present&~training).sum()),prediction_only=bool((present&training).sum()==0),n_profiles=d.set_index(ID).loc[present,'climate_profile'].nunique()))
    write(pd.DataFrame(freq),'41_unit_train_prediction_support')
    representation_rows=[]
    allpairs=np.array(list(itertools.combinations(range(len(d)),2)))
    unit_distance=squareform(pdist(w,metric='cityblock'))/2
    attribute_distance=squareform(pdist(a,metric='chebyshev'))
    representations=[('full_units',w,unit_distance,'total variation'),('attribute_coverages',a,attribute_distance,'maximum difference of mentioning coverages')]
    for family in ['group','qualifier','texture','surface_limit','physical_phase','chemical_phase']:
        cols=[c for c in attribute_cols if f'mentions_{family}_' in c]
        if cols:
            matrix=d[cols].to_numpy();distance=squareform(pdist(matrix,metric='chebyshev'))
            representations.append((family,matrix,distance,'maximum difference of mentioning coverages'))
            d[[ID]+cols].to_parquet(DATA/f'soil_attribute_representation_{family}.parquet',index=False)
    for label,matrix,distance,metric in representations:
        representation_rows.append(dict(representation=label,n_columns=matrix.shape[1],nonconstant_columns=int((np.ptp(matrix,axis=0)>1e-9).sum()),n_unique_vectors_rounded_5pp=len(np.unique(np.round(matrix/.05),axis=0)),n_pairs_distinguished_5pp=int((distance[allpairs[:,0],allpairs[:,1]]>.05).sum()),within_profile_pairs_distinguished_5pp=int((distance[pairs[:,0],pairs[:,1]]>.05).sum()),distance_metric=metric,coverage='complete; attributes can mention multiple groups per unit, not a closed physical composition'))
    write(pd.DataFrame(representation_rows),'45_representation_dimension_differentiation')
    categorical_variation=[]
    for field in ['soil_dominant_unit','soil_dominant_principal_group','soil_dominant_texture','soil_dominant_physical_phase','soil_dominant_chemical_phase']:
        counts=d[field].value_counts(normalize=True);gini=1-float((counts**2).sum())
        within=sum(len(z)*(1-float((z[field].value_counts(normalize=True)**2).sum())) for _,z in d.groupby('climate_profile'))/len(d)
        categorical_variation.append(dict(feature=field,global_gini=gini,weighted_within_profile_gini=within,n_categories=d[field].nunique(),n_profiles_with_variation=int((d.groupby('climate_profile')[field].nunique()>1).sum()),measure='probability of category disagreement; no numeric unit correlation'))
    write(pd.DataFrame(categorical_variation),'46_category_heterogeneity')
    composition_within=[]
    for profile,z in d.groupby('climate_profile'):
        matrix=wide.loc[z[ID]].to_numpy();dist=pdist(matrix,metric='cityblock')/2
        composition_within.append(dict(profile=profile,n=len(z),n_pairs=len(dist),mean_pair_total_variation=float(dist.mean()) if len(dist) else np.nan,max_pair_total_variation=float(dist.max()) if len(dist) else np.nan,n_pairs_tv_gt_5pp=int((dist>.05).sum()),n_varying_attribute_coverages=int((np.ptp(z[attribute_cols].to_numpy(),axis=0)>.05).sum())))
    write(pd.DataFrame(composition_within),'48_within_profile_soil_variation')
    # Euclidean inertia is reported explicitly as compositional descriptive SS, not independent shares.
    soilparts=[variance_parts(wide[u],d.climate_profile) for u in wide];total=sum(x['ss_total'] for x in soilparts);between=sum(x['ss_between'] for x in soilparts)
    write(pd.DataFrame([dict(ss_total=total,ss_between=between,ss_within=total-between,between_fraction=between/total,metric='Euclidean inertia of full closed composition; dependent shares')]),'42_composition_variation')
    profilemeans=wide.groupby(d.set_index(ID).climate_profile).mean();centers=d.groupby('climate_profile')[['longitude','latitude']].mean();from pyproj import Geod
    geod=Geod(ellps='WGS84');neighbors=[]
    for aa,bb in itertools.combinations(profilemeans.index,2):
        ca=centers.loc[aa];cb=centers.loc[bb];dist=geod.inv(ca.longitude,ca.latitude,cb.longitude,cb.latitude)[2]/1000
        neighbors.append(dict(profile_a=aa,profile_b=bb,distance_km=dist,soil_total_variation=float(abs(profilemeans.loc[aa]-profilemeans.loc[bb]).sum()/2)))
    write(pd.DataFrame(neighbors),'43_between_profile_soil_geographic_distances')
    findings=dict(y_variance=yparts,pair_sensitivity=sensitivity.to_dict('records'),n_units=wide.shape[1],n_attributes=len(attribute_cols),chignahuapan=regions[(regions.aggregation=='Municipio')&regions.name.str.contains('Chignahuapan',case=False)].to_dict('records'),composition_between_fraction=between/total)
    (OUT/'findings.json').write_text(json.dumps(findings,indent=2,ensure_ascii=False),encoding='utf-8')
    figures(d,g,profiles,wide,comparison,regions,pair,yparts)
    report(d,findings,comparison)
    after=protected()
    if before!=after:raise ValueError('Protected original/model inputs changed')
    (OUT/'protected_inputs_sha256.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
    record_execution()
    return findings

def figures(d,g,profiles,wide,comparison,regions,pair,yparts):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import seaborn as sns
    def save(fig,name):fig.tight_layout();fig.savefig(OUT/'figures'/f'{name}.png',dpi=160);plt.close(fig)
    spatial=g[[ID,'geometry']].merge(d,on=ID)
    for c,name in [('Estado','01_state'),('Municipio','02_municipality'),('locality_CVEGEO','03_nearest_locality'),('climate_profile','04_climate_profiles'),('soil_dominant_unit','06_dominant_soil')]:
        fig,ax=plt.subplots(figsize=(10,7));spatial.plot(column=c,categorical=True,legend=True,ax=ax,legend_kwds={'fontsize':5,'loc':'upper left','bbox_to_anchor':(1,1)});ax.set_title(c+' — descriptivo, sin pertenencia por proximidad');save(fig,name)
    fig,ax=plt.subplots(figsize=(10,7));s=gpd.read_file(DATA/'official_soil_aoi.gpkg').to_crs(g.crs);s.plot(column='Clave_wrb',alpha=.3,ax=ax,categorical=True);g.boundary.plot(ax=ax,color='black',linewidth=.7);ax.set_xlim(*[g.total_bounds[0]-2000,g.total_bounds[2]+2000]);ax.set_ylim(g.total_bounds[1]-2000,g.total_bounds[3]+2000);ax.set_title('INEGI Serie III 1:250000 y parcelas');save(fig,'05_soil_overlay')
    fig,ax=plt.subplots(figsize=(12,5));sns.heatmap(wide.T,cmap='viridis',ax=ax);ax.set_title('Cobertura cartográfica completa');save(fig,'07_soil_shares')
    fig,ax=plt.subplots();d.soil_unit_count.value_counts().sort_index().plot.bar(ax=ax);ax.set_title('Unidades cartográficas por parcela');save(fig,'08_unit_counts')
    fig,axes=plt.subplots(1,2,figsize=(13,5))
    for field,ax in zip(['Municipio','locality_CVEGEO'],axes):r=regions[regions.aggregation.eq(field)].sort_values('n',ascending=False).head(15);ax.barh(r.name.astype(str),r.n);ax.set_title(field+' — primeras 15')
    save(fig,'09_concentration')
    fig,axes=plt.subplots(2,1,figsize=(15,8))
    for c,ax in zip(['altitude_m','slope_degrees'],axes):sns.boxplot(data=d,x='climate_profile',y=c,ax=ax,fliersize=2);ax.tick_params(axis='x',labelsize=6)
    save(fig,'10_topography_within_profiles')
    fig,ax=plt.subplots(figsize=(12,4));ax.bar(profiles.climate_profile,profiles.n_dominant_units);ax.set(xlabel='Perfil',ylabel='Unidades dominantes distintas');save(fig,'11_soil_within_profiles')
    fig,axes=plt.subplots(1,2,figsize=(13,5));l=d[d[TARGET].notna()];sns.boxplot(data=l,x='climate_profile',y=TARGET,ax=axes[0],fliersize=2);axes[0].tick_params(axis='x',labelsize=5);axes[1].bar(['Entre perfiles','Dentro perfiles'],[yparts['ss_between'],yparts['ss_within']]);axes[1].set_title('SS descriptiva de Y; no atribución causal');save(fig,'12_y_variability')
    fig,axes=plt.subplots(1,2,figsize=(11,4));r=comparison[comparison.tv_tolerance.eq(.05)]
    for method,z in r.groupby('method'):axes[0].plot(z.N,z.area_coverage,'o-',label=method);axes[1].plot(z.N,z.within_profile_lost,'o-',label=method)
    axes[0].set(ylabel='Cobertura de superficie',xlabel='N');axes[1].set(ylabel='Parejas intraperfil perdidas, TV >5 pp',xlabel='N');axes[0].legend(fontsize=7);save(fig,'13_topn_comparison')
    potential=pair.groupby('climate_profile').agg(n_pairs=('ID_A','size'),soil_fraction=('soil_total_variation',lambda x:(x>.05).mean()),topo_fraction=('altitude_delta',lambda x:(x>25).mean())).reset_index()
    write(potential,'44_profile_differentiation_potential');fig,ax=plt.subplots(figsize=(10,5));ax.scatter(potential.topo_fraction,potential.soil_fraction,s=potential.n_pairs**.5*15)
    for _,r in potential.iterrows():ax.annotate(str(int(r.climate_profile)),(r.topo_fraction,r.soil_fraction),fontsize=7)
    ax.set(xlabel='Fracción parejas con diferencia altitud >25m',ylabel='Fracción con TV de suelo >5 pp',title='Potencial descriptivo; reservas cartográficas aplican');save(fig,'14_profile_potential')
    for c,name in [('altitude_m','15_altitude_y'),('slope_degrees','16_slope_y')]:
        fig,axes=plt.subplots(1,2,figsize=(10,4));axes[0].scatter(l[c],l[TARGET],s=15);xc=l[c]-l.groupby('climate_profile')[c].transform('mean');yc=l[TARGET]-l.groupby('climate_profile')[TARGET].transform('mean');axes[1].scatter(xc,yc,s=15);axes[0].set(xlabel=c,ylabel='Y observado');axes[1].set(xlabel=c+' centrado en 138',ylabel='Y centrado en 138');save(fig,name)
    fig,ax=plt.subplots(figsize=(9,6));sc=ax.scatter(l.longitude,l.latitude,c=l[TARGET],cmap='viridis',s=28);fig.colorbar(sc,ax=ax,label='Y observado t/ha, solo 138 TRAIN');ax.set(xlabel='Longitud',ylabel='Latitud',title='Rendimiento observado; cobertura geográfica de la muestra');save(fig,'17_observed_y_map')
    import plotly.graph_objects as go
    fig=go.Figure();choices=[]
    for label,z in [('Todas',d)]+[(str(k),z) for k,z in d.groupby('climate_profile')]:
        custom=z[[ID,'climate_profile','Estado','Municipio','locality_name','locality_distance_m','altitude_m','slope_degrees','soil_dominant_unit','soil_dominant_share','soil_assignment_reserve',TARGET,'soil_all_units_summary','soil_share_key_not_found_in_E1402_text']].fillna('sin rendimiento observado').astype(str).to_numpy()
        fig.add_trace(go.Scatter(x=z.longitude,y=z.latitude,mode='markers',visible=label=='Todas',marker=dict(size=9,color=z.altitude_m,colorscale='Viridis',showscale=True,colorbar=dict(title='Altitud m')),customdata=custom,hovertemplate='<br>'.join(f'{c}: %{{customdata[{i}]}}' for i,c in enumerate([ID,'Perfil','Estado','Municipio','Localidad cercana','Distancia m','Altitud m','Pendiente grados','Unidad dominante','Fracción dominante','Reserva límite','Y observado','Todas las unidades y coberturas','Cobertura clave discrepante con carta']))+'<extra></extra>'))
        choices.append(dict(label=label,method='update',args=[{'visible':[False]*(len(choices))+[True]+[False]*(53-len(choices))}]))
    # Add parcel boundaries to every selection via an always-visible trace.
    for button in choices:button['args'][0]['visible'].append(True)
    xs=[];ys=[]
    for geom in g.to_crs(4326).geometry:
        for poly in (geom.geoms if geom.geom_type=='MultiPolygon' else [geom]):xx,yy=poly.exterior.xy;xs.extend(list(xx)+[None]);ys.extend(list(yy)+[None])
    fig.add_trace(go.Scatter(x=xs,y=ys,mode='lines',line=dict(color='gray',width=.6),hoverinfo='skip',showlegend=False))
    fig.update_layout(title='Sección I — selección de perfil; suelo cartográfico, localidades por proximidad',updatemenus=[dict(buttons=choices)],xaxis_title='Longitud',yaxis_title='Latitud',height=800,showlegend=False)
    fig.write_html(OUT/'interactive/profile_explorer.html',include_plotlyjs=True)

def report(d,f,comparison):
    audit=json.loads((OUT/'soil_audit.json').read_text(encoding='utf-8'));p=f['pair_sensitivity'][1];y=f['y_variance'];ch=f['chignahuapan'][0]
    r=comparison[(comparison.method=='per_parcel')&comparison.tv_tolerance.eq(.05)].sort_values('N');complete=r[r.max_omitted_share<1e-6].iloc[0]
    compact_candidates=r[(r.area_coverage>=.99)&(r.max_omitted_share<=.05)&(r.within_profile_lost==0)&(r.pairs_lost==0)]
    preferred_compact=compact_candidates.iloc[0] if len(compact_candidates) else complete
    reps=pd.read_csv(OUT/'tables/45_representation_dimension_differentiation.csv')
    support=pd.read_csv(OUT/'tables/41_unit_train_prediction_support.csv')
    assoc=pd.read_csv(OUT/'tables/37_descriptive_associations_138.csv')
    compact=markdown_table(reps[['representation','n_columns','nonconstant_columns','within_profile_pairs_distinguished_5pp']])
    topo_assoc=markdown_table(assoc[assoc.feature.isin(['altitude_m','slope_degrees'])][['feature','scope','global_pearson','within_profile_pearson']])
    chig_variance=pd.read_csv(OUT/'tables/47_regional_y_variance.csv');chig_variance=chig_variance[(chig_variance.aggregation=='Municipio')&(chig_variance.name=='Chignahuapan')].iloc[0]
    text=f'''# Sección I — Exploración geográfica, topográfica y edafológica condicionada al clima

Se construyó una representación cartográfica de suelo para las 197 parcelas usando el vector oficial nacional INEGI Serie III, WRB 2014, escala 1:250000. No se entrenó ningún modelo de rendimiento, no se generaron predicciones para los 59 casos ocultos y se preservaron E–H y el Champion mediante hashes.

## Auditoría edafológica y productos A–D

La descarga oficial incluye polígonos, CRS original ITRF92 Lambert, metadatos y diccionario versión 4. La carta E1402 impresa es edición 2025 y el vector nacional edición 2024: comparten Serie III, WRB2014 y cobertura temporal 2021; no se afirma equivalencia geométrica exacta entre ambos productos. `02_unit_legend_audit.csv` registra claves encontradas en el texto de E1402. El vector oficial se usa como fuente explícita independiente: no se reconstruyen límites a partir de colores.

De las 22 claves intersectadas, 20 aparecen exactamente en el texto de E1402. `UMlep-lo+RGdy+LPdy/2` y `UMlep-lo+RGdy+LPli/2` aparecen en la carta con `hu` en lugar de `lo`. Es una diferencia temática entre ediciones, no una equivalencia corregida automáticamente: la variable `soil_share_key_not_found_in_E1402_text` conserva la cobertura afectada. Estas parcelas requieren reserva adicional para interpretar calificadores y validación contra la fuente que se quiera adoptar en modelado. Los grupos de las asociaciones coinciden; no se afirma que las propiedades sean intercambiables.

Se filtraron {audit['n_aoi_polygons']} polígonos próximos al área. Hay {f['n_units']} claves cartográficas intersectadas y {audit['n_intersections']} intersecciones. Cobertura mínima {audit['coverage_min']:.9f}, máxima {audit['coverage_max']:.9f}; {audit['crossing_parcels']} parcelas cruzan unidades. Se agregan polígonos de igual clave tras comprobar igualdad de atributos, sin eliminar intersecciones pequeñas. Las áreas usan LAEA local de igual área, no grados ni áreas originales del DBF.

{audit['near_125m']} parcelas tienen alguna superficie a menos de 125 m de un límite temático. Buffers de 50/125/250m son escenarios de sensibilidad equivalentes a 0.2/0.5/1mm a escala, **no estimaciones de exactitud**. El número de unidades y las fracciones expresan heterogeneidad cartográfica; el mapa no mide heterogeneidad física parcelaria. No se trasladan análisis de laboratorio de los reversos ni se derivan pH, infiltración o retención cuantitativa.

La geometría derivada se recorta con margen de 2km para procesar únicamente el área de interés. `49_boundary_aoi_edge_check.csv` comprueba, para las 197 parcelas, que el borde artificial del recorte está más lejos que el límite temático más cercano; no determina distancias ni los buffers de sensibilidad.

La matriz longitudinal conserva todas las intersecciones y atributos. La matriz ancha conserva todas las claves. Ausencia verificada=0; se comprueba cobertura completa antes de usar ceros. `soil_mixed_share=1-dominant_share`; entropía `-sum(q*ln(q))`, con q normalizada únicamente sobre cobertura cartográfica válida; el faltante se conserva por separado. Los empates se resuelven por clave lexicográfica, sin depender del orden de geometrías.

Grupos y calificadores se recuperan de campos oficiales, no de estimaciones RGB. `soil_map_share_mentions_*` es cobertura de unidades que **mencionan** un atributo, no fracción física de cada suelo asociado. Las menciones de grupos pueden sumar más de uno. `N` indica atributo ausente en la nomenclatura, no propiedad física medida; `N/A` no aplicable. El diccionario y los nombres oficiales se guardan junto a la leyenda.

Top-N por parcela se evaluó desde N=1 hasta todas las unidades presentes; N={int(complete.N)} conserva toda la composición observada. También se conservaron variantes globales por frecuencia, superficie y cobertura media; los órdenes se calculan separadamente. `22_topn_comparison.csv` mide cobertura, omisiones, categorías eliminadas y pérdidas de diferenciación de todas las parejas e intraperfil a tolerancias 1/5/10 pp. Cada N tiene matriz y tabla de omisiones. No se usó Y para escoger N. La referencia provisional sigue siendo la matriz completa; Top-N es una alternativa auditable, no un ganador predictivo.

Aplicando un criterio descriptivo explícito —cobertura total >=99%, omisión máxima por parcela <=5% y cero pérdidas de diferenciación a TV>5pp— el menor Top-N admisible es N={int(preferred_compact.N)}: cobertura {preferred_compact.area_coverage:.3%}, omisión máxima {preferred_compact.max_omitted_share:.3%}. El criterio utiliza exclusivamente coberturas y diferenciación, sin rendimiento. N=2 conserva mucha cobertura total, pero concentra una pérdida elevada en una parcela; por eso la media no basta. Los identificadores de Top-N se mantienen como categorías, no como números continuos, y el restante conserva la omisión visible.

## Geografía, localidades y diagnóstico integrado E–F

La geometría tiene estado y municipio; no localidad. Los CSV externos contienen puntos, nombres y códigos, sin límites de localidad ni fecha/CRS documentados. Se interpretan las coordenadas decimales como WGS84 con esta reserva explícita. Se mide proximidad al centroide en EPSG6372 y se conserva CVEGEO, fuente, distancia y segundo vecino. La regla «cercano y separado» exige distancia <=1km y margen al segundo >=250m: es confianza en la referencia de proximidad, **no pertenencia administrativa**. La auditoría compara nombre/distancia con la extracción previa de fase C; añade identidad y reservas sin reemplazarla.

Chignahuapan contiene {ch['n']} parcelas ({ch['fraction_197']:.1%} de la muestra), {ch['n_labeled']} etiquetadas ({ch['fraction_138']:.1%} del entrenamiento), {ch['n_profiles']} perfiles y {ch['n_soil_units']} unidades. Su rango de altitud es {ch['altitude_range']:.1f}m y de pendiente {ch['slope_range']:.2f} grados. La tabla territorial incluye estados, municipios y referencias de localidad; estadísticos de Y solo se muestran con >=5 observaciones. No se extrapolan estas concentraciones a todo un estado o al país.

En las parcelas etiquetadas de Chignahuapan, {chig_variance.between_fraction:.1%} de SS de Y se encuentra entre sus perfiles y {1-chig_variance.between_fraction:.1%} dentro. El resultado es regional y descriptivo; las demás regiones se comparan en `47_regional_y_variance.csv` solamente con soporte de al menos cinco etiquetas.

La auditoría de fase C encontró dos procedimientos distintos: `EXT_LOC_distance_any_m` mide distancia mínima desde el **polígono** parcelario al punto, aunque su diccionario la describía como centroide; el nombre cercano se había obtenido desde el centroide. Se conservan ambos campos previos, sin modificar aquel procesamiento. I explicita la distancia desde el centroide usada para identificar el punto de referencia y su segundo vecino. La diferencia máxima entre distancias es {d.previous_distance_abs_difference_m.max():.2f}m y responde a esos procedimientos distintos. Hay {int((~d.locality_municipality_agrees).sum())} referencias cercanas cuyo municipio difiere del municipio real de la parcela: proximidad no significa pertenencia.

## Variación entre/dentro de perfiles G

Se reutiliza la asignación exacta de 53 perfiles de H. Se informan rangos, medias y desviaciones de altitud y pendiente, geografía, suelo y rendimiento observado por perfil. Elevación y pendiente provienen de la extracción CEM4 de 120m. Sus versiones centradas en 197 parcelas son descriptivas y objetivo-libres; las asociaciones con Y centran **ambas variables en las 138 etiquetadas**, evitando usar la media de Y o asignar etiquetas al conjunto de predicción.

De {p['n_pairs']} parejas con clima idéntico, {p['topography']} se distinguen por altitud >25m o pendiente >1 grado; {p['soil_units']} por distancia de variación total de composición >0.05; {p['soil_attributes']} por alguna cobertura de atributo >5pp; {p['combined']} por topografía o suelo. De las diferenciadas por suelo, {p['soil_units_away_boundary_125m']} están fuera del escenario de reserva de límites y {p['soil_units_with_boundary_reserve']} requieren reserva. Hay {p['profiles_soil_distinguished']} perfiles con diferenciación cartográfica de suelo. Las tolerancias son filtros descriptivos de sensibilidad, **no certificación de diferencias físicas**; se guardan también escenarios 10m/0.5°/1pp y 50m/2°/10pp. No se cuentan cambios infinitesimales como evidencia.

Variación composicional entre perfiles: {f['composition_between_fraction']:.1%} de la inercia euclídea de la composición cerrada. Se describen proporciones dependientes; los ID de unidad no se correlacionan como números. La comparación de perfiles próximos usa distancia geográfica y variación total de sus composiciones medias, con todos los pares conservados.

Para Y, SS total={y['ss_total']:.6f}, entre={y['ss_between']:.6f}, dentro={y['ss_within']:.6f}. La proporción entre perfiles es {y['between_fraction']:.1%} y dentro {1-y['between_fraction']:.1%}. Es una partición descriptiva, no contribución causal del clima ni mejora predictiva. Las asociaciones globales, intraperfil y locales de Chignahuapan están en `37_descriptive_associations_138.csv`. Las categorías se describen con soporte >=5; contrastes intraperfil requieren >=3 casos por cada categoría y no se interpretan como significancia.

Asociaciones topográficas observadas (correlaciones descriptivas, sin selección de predictores por Y):

{topo_assoc}

La relación global de altitud con Y se debilita considerablemente al comparar dentro del mismo clima; parte de su asociación global puede corresponder a estructura geográfica entre perfiles. La pendiente conserva mayor asociación intraperfil y muestra un patrón local semejante en Chignahuapan. Esto justifica estudiar altitud y pendiente por separado, sin declarar causalidad, significancia ni mejora predictiva. El soporte local depende de pocos perfiles repetidos y se informa en las tablas.

## Viabilidad de variables H

| Familia | Situación provisional | Justificación |
|---|---|---|
| Altitud y pendiente continuas | Lista para prueba controlada | Extracción existente, cobertura completa, variación intraperfil; distinta información geomorfológica, sin inferir temperatura local. |
| Composición completa de unidades | Utilizable con reservas | Cobertura validada y todas las categorías preservadas, pero escala 1:250000, dependencia geográfica y bordes inciertos. |
| Atributos y limitantes cartográficos | Utilizable con reservas | Interpretables, {f['n_attributes']} coberturas; revisar redundancia, códigos poco frecuentes y asociaciones múltiples. |
| Top-N por parcela / global | Utilizable con reservas | Pérdidas cuantificadas sin Y; identidad categórica separada del porcentaje. Ajustar selección futura dentro de entrenamiento de cada fold. |
| Localidades y coordenadas | Requiere validación adicional como predictor | Útiles para diagnóstico/particiones; puntos cercanos no prueban pertenencia y la muestra es concentrada. |
| RGB de suelo, laboratorio asignado por cercanía y propiedades hidrológicas inventadas | No recomendable | No hay correspondencia parcelaria validada ni estimación física respaldada. |

`40_feature_viability_dependence.csv` cuantifica variación, redundancia con topografía y dependencia de estado/municipio/localidad; `41_unit_train_prediction_support.csv` identifica categorías exclusivas de predicción y escaso soporte. No hay selección por RMSE en I.

`45_representation_dimension_differentiation.csv` compara dimensionalidad, columnas variables y distinciones globales/intraperfil de unidades y atributos; usa métricas explícitas distintas para composición y menciones. `46_category_heterogeneity.csv` informa probabilidad de desacuerdo categórico global e intraperfil. Las representaciones de grupos mantienen interpretación pero pueden perder variación de calificadores y textura; no se seleccionan solo por producir más distinciones.

{compact}

Hay {int(support.prediction_only.sum())} unidades solo en predicción y {int((support.n_train<5).sum())} unidades con menos de cinco parcelas de entrenamiento. Esas categorías no tienen evidencia suficiente para ajustar efectos individuales sin regularización/agrupación validada. La representación completa de atributos puede tener más columnas que la composición de unidades: «por atributos» no significa automáticamente compacta. Se conservan matrices separadas de grupos, calificadores, textura y limitantes para evaluar esa reducción explícitamente.

Como primer bloque compacto de suelo para una prueba posterior, las diez coberturas de unidades que mencionan grupos conservan 833 de 863 distinciones intraperfil a la tolerancia de 5pp, frente a 22 columnas de unidades. Es una reducción interpretable con pérdida explícita, no un ganador predictivo. Los 45 atributos juntos no reducen dimensionalidad; los calificadores tienen además la discrepancia entre ediciones señalada. Las limitantes químicas no aportan variación cartográfica en esta muestra (`N`), por lo que no se inventan indicadores químicos continuos.

## Propuesta posterior I — no ejecutada

Comparar solo lluvia, lluvia+altitud/pendiente, lluvia+suelo y lluvia+ambos. Mantener la misma lluvia, algoritmo base y folds congelados de E–H para atribuir incrementos; contrastar los resultados con Climate Current y Champion respetando sus arquitecturas y métrica. Preprocesamiento, selección por frecuencia, codificación y cualquier ajuste se aprenden dentro de cada entrenamiento interno; categorías nuevas tienen tratamiento explícito. No usar centrados calculados con las 197 parcelas como entrada aprendida a validación.

Usar RMSE, MAE, R², sesgo y diferencias pareadas por fold, con validación aleatoria, por perfil, municipal y espacial. La integración requerirá mejora reproducible más allá del error de comparación, ausencia de deterioro material preespecificado en protocolos geográficos y soporte de categorías. Definir antes de ejecutar margen de no inferioridad de 0.01t/ha en RMSE y evaluar intervalos mediante repeticiones o grupos independientes, sin tratar folds correlacionados como muestras independientes. Si mejora aleatoria y empeora municipal/espacial, registrar asociación local sin generalización demostrada. Interacciones lluvia–suelo se estudiarían después, con unas pocas hipótesis respaldadas y soporte suficiente.

## Visualizaciones y reproducibilidad

Se guardan mapas territoriales, de localidades cercanas, perfiles, suelo oficial y dominancia; composiciones, unidades por parcela, concentración, topografía y suelo intraperfil, descomposición de Y, comparación Top-N y potencial de diferenciación. `interactive/profile_explorer.html` es autónomo y permite elegir los 53 perfiles, consultar referencias territoriales, topografía, unidad dominante, reservas de límites y Y observado. La simbología es descriptiva.

Ejecutar scripts 323 (suelo oficial) y 324 (exploración) desde la raíz. Fuente nueva en `data/externo/suelo/inegi_serie_iii_794551118313`; derivados en `data/processed/family_1/{NAME}/v1`; tablas, figuras y manifiestos en `outputs/research/family_1/{NAME}/v1`. SHA256 del archivo oficial y de insumos protegidos permiten auditar trazabilidad. Los apartados de productos son internos a Sección I.
'''
    (ROOT/'documentation/i_geographic_edaphological_exploration.md').write_text(text,encoding='utf-8')
    (OUT/'section_i_report.md').write_text(text,encoding='utf-8')
