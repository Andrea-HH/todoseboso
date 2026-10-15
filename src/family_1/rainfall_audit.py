"""Independent, read-only audit of canonical CHIRPS extraction."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.windows import from_bounds, Window
from shapely.geometry import box
from exactextract import exact_extract
from pyproj import Geod

ROOT = Path(__file__).resolve().parents[2]
ID = 'ID_POLIGONO'
CLIMATE = ROOT / 'data/processed/family_1/environment/climate_monthly_timeseries.parquet'
MASTER = ROOT / 'data/original/01_tablas_maestras/ID_area_rendimiento_70_30_Reto_AgroCebada.csv'
SHAPE = ROOT / 'data/original/02_conjunto_70_30/Parcelas_Reto_AGC_CONJUNTO.shp'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def audit(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    d = pd.read_parquet(CLIMATE)
    master = pd.read_csv(MASTER)
    g = gpd.read_file(SHAPE).rename(columns={'ID_POLIGON': ID})
    inventory = pd.read_csv(ROOT/'outputs/data_audit/family_1/environment/climate_raster_inventory.csv')
    inventory = inventory[inventory.variable.eq('precip')].sort_values(['year', 'month'])
    expected = pd.MultiIndex.from_product([master[ID], range(2022, 2026), range(1, 13)])
    actual = pd.MultiIndex.from_frame(d[[ID, 'year', 'month']])
    if d.duplicated([ID, 'year', 'month']).any() or set(actual) != set(expected):
        raise ValueError('Incomplete or duplicated canonical parcel/month grid')
    dates = pd.to_datetime(dict(year=d.year, month=d.month, day=1))
    if not dates.equals(d.date_month) or not d.CONJUNTO.equals(d[ID].map(master.set_index(ID).CONJUNTO)):
        raise ValueError('Dates or train/prediction identifiers disagree')
    rows, files, metadata = [], {}, []
    files.update({str(p.relative_to(ROOT)):sha(p) for p in SHAPE.parent.glob(SHAPE.stem+'.*')})
    geod = Geod(ellps='WGS84')
    for _, rec in inventory.iterrows():
        path = ROOT/rec.filepath
        files[str(path.relative_to(ROOT))] = sha(path)
        with rasterio.open(path) as src:
            tags = src.tags()
            if tags.get('Unidad') != 'mm/mes' or tags.get('Periodo') != f'{int(rec.year)}-{int(rec.month):02d}':
                raise ValueError(f'Units/period not verified: {path}')
            expected_days = pd.Timestamp(int(rec.year),int(rec.month),1).days_in_month
            if src.scales != (1.,) or src.offsets != (0.,) or int(tags.get('Dias_acumulados',-1)) != expected_days:
                raise ValueError(f'Scale/offset/daily accumulation not verified: {path}')
            metadata.append(dict(filepath=rec.filepath,year=int(rec.year),month=int(rec.month),
                                 units=tags['Unidad'],days=expected_days,scale=src.scales[0],offset=src.offsets[0],
                                 nodata=src.nodata,crs=str(src.crs),resolution_x=src.res[0],resolution_y=src.res[1]))
            projected = g.to_crs(src.crs)
            exact = exact_extract(str(path), projected, ['mean', 'values', 'coverage'], output='pandas')
            canonical = d[(d.year.eq(rec.year)) & (d.month.eq(rec.month))].set_index(ID)
            for pos, parcel in projected.iterrows():
                geom = parcel.geometry
                raw_window = from_bounds(*geom.bounds, transform=src.transform)
                c0, r0 = int(np.floor(raw_window.col_off)), int(np.floor(raw_window.row_off))
                c1 = int(np.ceil(raw_window.col_off+raw_window.width))
                r1 = int(np.ceil(raw_window.row_off+raw_window.height))
                valid_area, numerator, geodesic_area, geodesic_numerator, n = 0., 0., 0., 0., 0
                for rr in range(max(0, r0), min(src.height, r1)):
                    for cc in range(max(0, c0), min(src.width, c1)):
                        x0, y0 = src.transform*(cc, rr)
                        x1, y1 = src.transform*(cc+1, rr+1)
                        intersection = geom.intersection(box(min(x0,x1),min(y0,y1),max(x0,x1),max(y0,y1)))
                        area = intersection.area
                        if area <= 0: continue
                        v = src.read(1, window=Window(cc, rr, 1, 1), masked=True)
                        if np.ma.is_masked(v[0,0]) or not np.isfinite(v[0,0]): continue
                        n += 1; valid_area += area; numerator += area*float(v[0,0])
                        physical_area = abs(geod.geometry_area_perimeter(intersection)[0])
                        geodesic_area += physical_area;geodesic_numerator += physical_area*float(v[0,0])
                manual = numerator/valid_area if valid_area > 0 else np.nan
                values = np.asarray(exact.iloc[pos]['values'], float)
                coverage = np.asarray(exact.iloc[pos]['coverage'], float)
                mask = np.isfinite(values) & (coverage > 0)
                if src.nodata is not None: mask &= values != src.nodata
                weighted = np.average(values[mask], weights=coverage[mask]) if mask.any() else np.nan
                center = geom.centroid
                central = next(src.sample([(center.x, center.y)], masked=True))[0]
                central = np.nan if np.ma.is_masked(central) else float(central)
                stored = canonical.loc[parcel[ID], 'precip_mean']
                rows.append({ID:parcel[ID], 'year':int(rec.year), 'month':int(rec.month),
                             'stored_mm':stored, 'manual_minus_stored_mm':manual-stored,
                             'coverage_minus_stored_mm':weighted-stored,
                             'geodesic_minus_stored_mm':geodesic_numerator/geodesic_area-stored if geodesic_area else np.nan,
                             'centroid_minus_weighted_mm':central-stored,
                             'valid_geometry_fraction':valid_area/geom.area,
                             'manual_valid_pixels':n, 'exact_valid_pixels':int(mask.sum())})
        print(f'Audit CHIRPS {int(rec.year)}-{int(rec.month):02d}', flush=True)
    checks = pd.DataFrame(rows)
    checks.to_csv(output/'01_extraction_checks.csv', index=False)
    pd.DataFrame(metadata).to_csv(output/'02_raster_metadata_checks.csv',index=False)
    pivot = d.pivot(index=ID, columns=['year','month'], values='precip_mean')
    summary = dict(rows=len(d), columns=d.shape[1], parcels=d[ID].nunique(), months=48,
                   key_unique=True, missing=int(d.precip_mean.isna().sum()), negative=int(d.precip_mean.lt(0).sum()),
                   unique_series_exact=len(pivot.drop_duplicates()),
                   unique_series_rounded_001mm=len(pivot.round(2).drop_duplicates()),
                   max_manual_error_mm=float(checks.manual_minus_stored_mm.abs().max()),
                   max_coverage_error_mm=float(checks.coverage_minus_stored_mm.abs().max()),
                   geodesic_area_sensitivity_max_mm=float(checks.geodesic_minus_stored_mm.abs().max()),
                   minimum_valid_geometry_fraction=float(checks.valid_geometry_fraction.min()),
                   pixel_count_disagreements=int(checks.manual_valid_pixels.ne(checks.exact_valid_pixels).sum()),
                   centroid_absolute_difference_mean_mm=float(checks.centroid_minus_weighted_mm.abs().mean()),
                   centroid_absolute_difference_max_mm=float(checks.centroid_minus_weighted_mm.abs().max()),
                   one_pixel_parcels=int(checks.groupby(ID).manual_valid_pixels.max().eq(1).sum()),
                   units='mm accumulated per calendar month, verified raster tags',
                   method='fractional cell coverage; area in EPSG:4326 grid coordinates',
                   physical_area_caveat='Degree-squared area fractions, not exact geodesic m2 weights; appropriate grid-cell statistic at parcel scale.',
                   quality_caveat='Existing valid_fraction denominator clips to raster bounds; effective_intersection_area_m2 is approximate. Independent audit uses full geometry denominator.',
                   target_used=False, raw_modified=False,
                   inputs={str(CLIMATE.relative_to(ROOT)):sha(CLIMATE),str(MASTER.relative_to(ROOT)):sha(MASTER),**files})
    summary['passed'] = bool(summary['missing']==0 and summary['negative']==0 and
                             summary['max_manual_error_mm'] < 1e-3 and summary['max_coverage_error_mm'] < 1e-6 and
                             summary['minimum_valid_geometry_fraction'] > .99999 and summary['pixel_count_disagreements']==0)
    (output/'audit_manifest.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    (output/'audit_report.md').write_text('# Rainfall Yield Modeling: auditoría de extracción\n\n'+
        'Verificación independiente de los 48 rásteres y las 9,456 intersecciones: suma explícita de valores por área de intersección Shapely, contra fracciones de exactextract y tabla canónica. Se consideran todas las celdas con área positiva; se excluyen NoData y no finitos y se renormaliza por superficie válida. Sin cobertura válida se obtiene NaN.\n\n'+
        'Las etiquetas originales confirman suma de precipitación diaria en mm/mes, periodo, escala 1 y offset 0. Los pesos corresponden a superficie en coordenadas de la grilla, no a m² geodésicos exactos. No se reconstruyen rásteres ni se publica otra serie longitudinal.\n\n'+
        'El constructor 121 y load_parcels únicamente incorporan ID, AREA_HA y CONJUNTO del maestro: el rendimiento no entra en exactextract. Los indicadores de superficie del pipeline tienen una limitación en cobertura exterior; la auditoría calcula cobertura respecto de toda la geometría. No afecta la lluvia si la cobertura comprobada es completa.\n\n'+
        '```json\n'+json.dumps({k:v for k,v in summary.items() if k!='inputs'},indent=2,ensure_ascii=False)+'\n```\n', encoding='utf-8')
    return summary
