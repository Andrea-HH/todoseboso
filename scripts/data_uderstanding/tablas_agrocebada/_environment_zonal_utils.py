"""Funciones compartidas para la Etapa 2.5 ambiental."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from exactextract import exact_extract
from shapely.geometry import box


ID = "ID_POLIGONO"
AREA_CRS = "EPSG:6372"  # México ITRF2008 / LCC; unidades métricas.


def load_parcels(shapefile: Path, master_file: Path) -> gpd.GeoDataFrame:
    parcels = gpd.read_file(shapefile).rename(columns={"ID_POLIGON": ID})
    master = pd.read_csv(master_file).drop(columns=["Unnamed: 4"], errors="ignore")
    parcels = parcels.drop(columns=["CONJUNTO"], errors="ignore").merge(
        master[[ID, "AREA_HA", "CONJUNTO"]], on=ID, how="left", validate="one_to_one"
    )
    if len(parcels) != 197 or not parcels[ID].is_unique:
        raise ValueError("La capa de parcelas no conserva las 197 claves únicas")
    return parcels


def zonal_statistics(raster_path: Path, parcels: gpd.GeoDataFrame) -> pd.DataFrame:
    """Extrae estadísticas ponderadas por fracción de píxel.

    `exactextract mean/median/stdev` pondera cada celda por la fracción cubierta.
    La media estándar de comparación asigna igual peso a todo píxel tocado.
    """
    with rasterio.open(raster_path) as src:
        raster_crs = src.crs
        pixel_area_crs_units = abs(src.res[0] * src.res[1])
        raster_bounds = box(*src.bounds)
        nodata = src.nodata

    parcel_raster = parcels.to_crs(raster_crs)
    parcel_metric = parcels.to_crs(AREA_CRS)
    result = exact_extract(
        str(raster_path), parcel_raster,
        ["mean", "median", "min", "max", "stdev", "count", "values", "coverage"],
        output="pandas",
    )

    rows = []
    for position, (_, parcel) in enumerate(parcel_raster.iterrows()):
        values = np.asarray(result.iloc[position]["values"], dtype=float)
        coverage = np.asarray(result.iloc[position]["coverage"], dtype=float)
        finite_values = values[np.isfinite(values)]
        total_fraction_expected = parcel.geometry.intersection(raster_bounds).area / pixel_area_crs_units
        effective_pixel_count = float(result.iloc[position]["count"])
        valid_fraction = (
            effective_pixel_count / total_fraction_expected if total_fraction_expected > 0 else np.nan
        )
        valid_fraction = float(np.clip(valid_fraction, 0, 1)) if np.isfinite(valid_fraction) else np.nan
        metric_area = float(parcel_metric.geometry.iloc[position].area)
        rows.append({
            ID: parcel[ID],
            "weighted_mean": result.iloc[position]["mean"],
            "weighted_median": result.iloc[position]["median"],
            "min": result.iloc[position]["min"],
            "max": result.iloc[position]["max"],
            "weighted_std": result.iloc[position]["stdev"],
            "n_pixels": int(len(values)),
            "n_unique_pixel_values": int(np.unique(finite_values).size),
            "effective_pixel_count": effective_pixel_count,
            "effective_intersection_area_m2": metric_area * valid_fraction,
            "valid_fraction": valid_fraction,
            "standard_touched_pixel_mean": float(finite_values.mean()) if finite_values.size else np.nan,
            "weighted_minus_standard_mean": (
                float(result.iloc[position]["mean"] - finite_values.mean())
                if finite_values.size and pd.notna(result.iloc[position]["mean"]) else np.nan
            ),
            "parcel_intersects_raster_bounds": parcel.geometry.intersects(raster_bounds),
            "nodata": nodata,
        })
    return pd.DataFrame(rows)
