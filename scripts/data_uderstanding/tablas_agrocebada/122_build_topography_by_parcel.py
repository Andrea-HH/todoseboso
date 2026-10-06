"""Familia 1, Etapa 2.5I-J: topografía estática y auditoría de área."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import pandas as pd

from _environment_zonal_utils import AREA_CRS, ID, load_parcels, zonal_statistics


ROOT = Path(__file__).resolve().parents[3]
SHAPEFILE = ROOT / "data/original/02_conjunto_70_30/Parcelas_Reto_AGC_CONJUNTO.shp"
MASTER = ROOT / "data/original/01_tablas_maestras/ID_area_rendimiento_70_30_Reto_AgroCebada.csv"
TOPO_DIR = ROOT / "data/original/05_topografia"
OUTPUT_DIR = ROOT / "data/processed/family_1/environment"
AUDIT_DIR = ROOT / "outputs/data_audit/family_1/environment"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

parcels = load_parcels(SHAPEFILE, MASTER)
elevation_path = next(TOPO_DIR.rglob("Elevacion*.tif"))
slope_path = next(TOPO_DIR.rglob("Pendiente*.tif"))

elevation = zonal_statistics(elevation_path, parcels)
slope = zonal_statistics(slope_path, parcels)

rename_base = {
    "weighted_mean": "mean", "weighted_median": "median",
    "min": "min", "max": "max", "weighted_std": "std",
    "n_pixels": "n_pixels", "n_unique_pixel_values": "n_unique_pixels",
    "effective_pixel_count": "effective_pixel_count",
    "effective_intersection_area_m2": "effective_intersection_area_m2",
    "valid_fraction": "valid_fraction",
    "standard_touched_pixel_mean": "standard_mean",
    "weighted_minus_standard_mean": "weighted_minus_standard_mean",
}

def prefixed(stats: pd.DataFrame, prefix: str) -> pd.DataFrame:
    return stats[[ID] + list(rename_base)].rename(
        columns={source: f"{prefix}_{target}" for source, target in rename_base.items()}
    )


topography = prefixed(elevation, "elevation").merge(
    prefixed(slope, "slope"), on=ID, how="outer", validate="one_to_one"
)
topography = topography.merge(
    parcels[[ID, "CONJUNTO", "AREA_HA"]], on=ID, how="left", validate="one_to_one"
)
topography["elevation_range"] = topography["elevation_max"] - topography["elevation_min"]
topography["slope_range"] = topography["slope_max"] - topography["slope_min"]

leading = [ID, "CONJUNTO", "AREA_HA"]
topography = topography[leading + [column for column in topography.columns if column not in leading]]
topography = topography.sort_values(ID).reset_index(drop=True)
if len(topography) != 197 or not topography[ID].is_unique:
    raise ValueError("La tabla topográfica debe tener exactamente una fila por parcela")
topography.to_parquet(OUTPUT_DIR / "topography_by_parcel.parquet", index=False)

# Diccionario
dictionary_rows = []
for column in topography.columns:
    role = "ZONAL_STATISTIC"
    description = "Estadística zonal estática ponderada por fracción de píxel"
    if column in [ID, "CONJUNTO"]:
        role, description = "IDENTIFIER", "Identificador/grupo sin uso del rendimiento"
    elif column == "AREA_HA":
        role, description = "OFFICIAL", "Área oficial proporcionada por el reto"
    elif column.endswith("_range"):
        role, description = "DERIVED", "Máximo menos mínimo dentro de parcela"
    elif "n_pixels" in column or "valid_fraction" in column:
        role, description = "QUALITY", "Soporte y cobertura espacial"
    elif "standard_mean" in column or "weighted_minus_standard_mean" in column:
        role, description = "DIAGNOSTIC", "Comparación contra media no ponderada de píxeles tocados"
    units = "source_or_quality_units"
    if column.startswith("elevation_") and column.endswith(("mean", "median", "min", "max", "std", "range")):
        units = "meters"
    elif column.startswith("slope_") and column.endswith(("mean", "median", "min", "max", "std", "range")):
        units = "degrees"
    dictionary_rows.append({"column": column, "dtype": str(topography[column].dtype),
                            "role": role, "description": description, "units": units})
pd.DataFrame(dictionary_rows).to_csv(OUTPUT_DIR / "topography_data_dictionary.csv", index=False)

# Área y geometría: sólo auditoría, no se añaden como features a topography.
metric = parcels.to_crs(AREA_CRS)
area_comparison = pd.DataFrame({
    ID: metric[ID], "CONJUNTO": metric["CONJUNTO"],
    "area_official_ha": metric["AREA_HA"],
    "area_geometry_ha": metric.geometry.area / 10_000,
    "perimeter_geometry_m": metric.geometry.length,
    "centroid_x_area_crs": metric.geometry.centroid.x,
    "centroid_y_area_crs": metric.geometry.centroid.y,
})
area_comparison["area_difference_ha"] = (
    area_comparison["area_geometry_ha"] - area_comparison["area_official_ha"]
)
area_comparison["area_relative_difference_pct"] = (
    100 * area_comparison["area_difference_ha"] / area_comparison["area_official_ha"]
)
area_comparison.to_csv(AUDIT_DIR / "area_comparison.csv", index=False)

# Auditoría por parcela, incluyendo método y disponibilidad.
audit = topography.merge(
    area_comparison[[ID, "area_geometry_ha", "area_relative_difference_pct"]],
    on=ID, how="left", validate="one_to_one",
)
audit["elevation_raster"] = str(elevation_path.relative_to(ROOT))
audit["slope_raster"] = str(slope_path.relative_to(ROOT))
audit["zonal_method"] = "exactextract_fractional_pixel_weighting"
audit.to_csv(AUDIT_DIR / "topography_audit.csv", index=False)

(OUTPUT_DIR / "topography_build_manifest.json").write_text(json.dumps({
    "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    "rows": len(topography), "columns": topography.shape[1], "key_unique": topography[ID].is_unique,
    "area_crs": AREA_CRS, "raw_modified": False, "target_used": False,
    "weighted_method": "exactextract fractional pixel coverage",
}, indent=2), encoding="utf-8")

print("Topografía:", topography.shape)
print("Elevación missing:", topography["elevation_mean"].isna().sum())
print("Pendiente missing:", topography["slope_mean"].isna().sum())
print("Diferencia relativa de área (%):")
print(area_comparison["area_relative_difference_pct"].describe().to_string())
