"""Familia 1, Etapa 2.5C-H: serie climática mensual por parcela."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from _environment_zonal_utils import ID, load_parcels, zonal_statistics


ROOT = Path(__file__).resolve().parents[3]
SHAPEFILE = ROOT / "data/original/02_conjunto_70_30/Parcelas_Reto_AGC_CONJUNTO.shp"
MASTER = ROOT / "data/original/01_tablas_maestras/ID_area_rendimiento_70_30_Reto_AgroCebada.csv"
AUDIT_DIR = ROOT / "outputs/data_audit/family_1/environment"
OUTPUT_DIR = ROOT / "data/processed/family_1/environment"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

inventory = pd.read_csv(AUDIT_DIR / "climate_raster_inventory.csv")
parcels = load_parcels(SHAPEFILE, MASTER)

stat_name_map = {
    "weighted_mean": "mean",
    "weighted_median": "median",
    "min": "min",
    "max": "max",
    "weighted_std": "std",
    "n_pixels": "n_pixels",
    "n_unique_pixel_values": "n_unique_pixels",
    "effective_pixel_count": "effective_pixel_count",
    "effective_intersection_area_m2": "effective_intersection_area_m2",
    "valid_fraction": "valid_fraction",
    "standard_touched_pixel_mean": "standard_mean",
    "weighted_minus_standard_mean": "weighted_minus_standard_mean",
}

long_frames = []
for position, raster in inventory.reset_index(drop=True).iterrows():
    raster_path = ROOT / raster["filepath"]
    stats = zonal_statistics(raster_path, parcels)
    stats["variable"] = raster["variable"]
    stats["year"] = int(raster["year"])
    stats["month"] = int(raster["month"])
    stats["filepath"] = raster["filepath"]
    long_frames.append(stats)
    if (position + 1) % 12 == 0:
        print(f"Procesados {position + 1}/{len(inventory)} rásteres climáticos")

climate_long = pd.concat(long_frames, ignore_index=True)
climate_long.to_parquet(AUDIT_DIR / "climate_zonal_statistics_long.parquet", index=False)

keys = [ID, "year", "month"]
wide_parts = []
for variable, part in climate_long.groupby("variable"):
    selected = part[keys + list(stat_name_map)].rename(
        columns={source: f"{variable}_{target}" for source, target in stat_name_map.items()}
    )
    wide_parts.append(selected)

climate = wide_parts[0]
for part in wide_parts[1:]:
    climate = climate.merge(part, on=keys, how="outer", validate="one_to_one")

climate = climate.merge(
    parcels[[ID, "CONJUNTO"]], on=ID, how="left", validate="many_to_one"
)
climate["date_month"] = pd.to_datetime(
    dict(year=climate["year"], month=climate["month"], day=1)
)
climate["tmean_mean"] = (climate["tmax_mean"] + climate["tmin_mean"]) / 2
climate["dtr_mean"] = climate["tmax_mean"] - climate["tmin_mean"]
climate["is_current_cycle_2025"] = (
    climate["year"].eq(2025) & climate["month"].between(4, 10)
)
climate["is_history_2022_2024"] = climate["year"].between(2022, 2024)
climate["all_sources_available"] = climate[
    ["precip_mean", "tmin_mean", "tmax_mean"]
].notna().all(axis=1)

leading = [
    ID, "CONJUNTO", "year", "month", "date_month",
    "is_current_cycle_2025", "is_history_2022_2024", "all_sources_available",
]
climate = climate[leading + [column for column in climate.columns if column not in leading]]
climate = climate.sort_values([ID, "year", "month"]).reset_index(drop=True)

if climate.duplicated(keys).any():
    raise ValueError("La clave ID_POLIGONO + year + month no es única")
if len(climate) != 197 * 48:
    raise ValueError(f"Se esperaban 9,456 filas y se obtuvieron {len(climate)}")

climate.to_parquet(OUTPUT_DIR / "climate_monthly_timeseries.parquet", index=False)

# Diccionario de datos
dictionary_rows = []
for column in climate.columns:
    role = "ZONAL_STATISTIC"
    description = "Estadística zonal ponderada por fracción de píxel"
    if column in [ID, "CONJUNTO"]:
        role, description = "IDENTIFIER", "Identificador/grupo sin uso del rendimiento"
    elif column in ["year", "month", "date_month", "is_current_cycle_2025", "is_history_2022_2024"]:
        role, description = "TIME", "Variable temporal auxiliar"
    elif column in ["tmean_mean", "dtr_mean"]:
        role, description = "DERIVED", "Definición física mensual derivada de Tmin/Tmax medios"
    elif column == "all_sources_available" or "valid_fraction" in column or "n_pixels" in column:
        role, description = "QUALITY", "Disponibilidad o soporte espacial de la estadística"
    elif "standard_mean" in column or "weighted_minus_standard_mean" in column:
        role, description = "DIAGNOSTIC", "Comparación de ponderación; no reemplaza la media ponderada"
    dictionary_rows.append({
        "column": column, "dtype": str(climate[column].dtype), "role": role,
        "description": description,
        "units": (
            "mm/month" if column.startswith("precip_") and column.endswith(("mean", "median", "min", "max", "std"))
            else "degrees_C_assumed_from_source" if column.startswith(("tmin_", "tmax_", "tmean_", "dtr_")) and column.endswith(("mean", "median", "min", "max", "std"))
            else "count_or_fraction_or_source_units"
        ),
    })
dictionary = pd.DataFrame(dictionary_rows)
dictionary.to_csv(OUTPUT_DIR / "climate_monthly_data_dictionary.csv", index=False)

# Diagnóstico espacial resumido por parcela y variable.
resolution_rows = []
for variable, part in climate_long.groupby("variable"):
    for parcel_id, parcel_part in part.groupby(ID):
        resolution_rows.append({
            ID: parcel_id, "variable": variable,
            "months": len(parcel_part),
            "n_pixels_min": parcel_part["n_pixels"].min(),
            "n_pixels_median": parcel_part["n_pixels"].median(),
            "n_pixels_max": parcel_part["n_pixels"].max(),
            "n_unique_pixels_median": parcel_part["n_unique_pixel_values"].median(),
            "effective_pixel_count_median": parcel_part["effective_pixel_count"].median(),
            "valid_fraction_min": parcel_part["valid_fraction"].min(),
            "valid_fraction_median": parcel_part["valid_fraction"].median(),
            "weighted_standard_abs_diff_median": parcel_part["weighted_minus_standard_mean"].abs().median(),
            "weighted_standard_abs_diff_max": parcel_part["weighted_minus_standard_mean"].abs().max(),
            "CONJUNTO": parcels.loc[parcels[ID].eq(parcel_id), "CONJUNTO"].iloc[0],
        })
resolution = pd.DataFrame(resolution_rows)
resolution.to_csv(AUDIT_DIR / "climate_spatial_resolution_by_parcel.csv", index=False)

# Comprobaciones físicas/descriptivas sin eliminar valores.
checks = pd.DataFrame([
    {"check": "negative_precip_mean", "count": int(climate["precip_mean"].lt(0).sum())},
    {"check": "tmin_mean_gt_tmax_mean", "count": int(climate["tmin_mean"].gt(climate["tmax_mean"]).sum())},
    {"check": "negative_dtr", "count": int(climate["dtr_mean"].lt(0).sum())},
    {"check": "missing_precip_mean", "count": int(climate["precip_mean"].isna().sum())},
    {"check": "missing_tmin_mean", "count": int(climate["tmin_mean"].isna().sum())},
    {"check": "missing_tmax_mean", "count": int(climate["tmax_mean"].isna().sum())},
])
checks.to_csv(AUDIT_DIR / "climate_value_checks.csv", index=False)

(OUTPUT_DIR / "climate_build_manifest.json").write_text(json.dumps({
    "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    "rows": len(climate), "columns": climate.shape[1], "parcels": climate[ID].nunique(),
    "months": climate["date_month"].nunique(), "key_unique": not climate.duplicated(keys).any(),
    "weighted_method": "exactextract fractional pixel coverage",
    "raw_modified": False, "target_used": False,
}, indent=2), encoding="utf-8")

print("Clima canónico:", climate.shape)
print(checks.to_string(index=False))
print("Salida:", OUTPUT_DIR / "climate_monthly_timeseries.parquet")
