"""Familia 1, Etapa 2.5A-B: inventario y compatibilidad de rásteres."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import pandas as pd
import rasterio
from shapely.geometry import box


ROOT = Path(__file__).resolve().parents[3]
PRECIP_DIR = ROOT / "data/original/03_presipitacion"
TEMP_DIR = ROOT / "data/original/04_temperatura"
TOPO_DIR = ROOT / "data/original/05_topografia"
SHAPEFILE = ROOT / "data/original/02_conjunto_70_30/Parcelas_Reto_AGC_CONJUNTO.shp"
OUTPUT_DIR = ROOT / "outputs/data_audit/family_1/environment"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def identify(path: Path) -> tuple[str, int | None, int | None]:
    name = path.stem
    match = re.search(r"(PREC|Tmin|Tmax)_(\d{4})_(\d{2})", name, re.IGNORECASE)
    if match:
        variable = {"prec": "precip", "tmin": "tmin", "tmax": "tmax"}[match.group(1).lower()]
        return variable, int(match.group(2)), int(match.group(3))
    if "Elevacion" in name:
        return "elevation", None, None
    if "Pendiente" in name:
        return "slope", None, None
    return "unknown", None, None


files = sorted(PRECIP_DIR.rglob("*.tif")) + sorted(TEMP_DIR.rglob("*.tif"))
inventory_rows = []
for path in files:
    variable, year, month = identify(path)
    with rasterio.open(path) as src:
        inventory_rows.append({
            "variable": variable, "filepath": str(path.relative_to(ROOT)),
            "year": year, "month": month, "crs": str(src.crs),
            "resolution_x": src.res[0], "resolution_y": src.res[1],
            "width": src.width, "height": src.height, "nodata": src.nodata,
            "min_x": src.bounds.left, "max_x": src.bounds.right,
            "min_y": src.bounds.bottom, "max_y": src.bounds.top,
            "dtype": src.dtypes[0], "band_count": src.count,
        })
inventory = pd.DataFrame(inventory_rows).sort_values(["variable", "year", "month"])
inventory.to_csv(OUTPUT_DIR / "climate_raster_inventory.csv", index=False)

expected = pd.MultiIndex.from_product(
    [["precip", "tmin", "tmax"], range(2022, 2026), range(1, 13)],
    names=["variable", "year", "month"],
).to_frame(index=False)
availability = expected.merge(
    inventory.groupby(["variable", "year", "month"], as_index=False).size(),
    on=["variable", "year", "month"], how="left",
)
availability["size"] = availability["size"].fillna(0).astype(int)
availability = availability.rename(columns={"size": "n_files"})
availability["status"] = availability["n_files"].map(
    lambda n: "missing" if n == 0 else ("duplicate" if n > 1 else "ok")
)
availability.to_csv(OUTPUT_DIR / "climate_raster_availability.csv", index=False)

parcels = gpd.read_file(SHAPEFILE)
spatial_rows = []
for family, part in inventory.groupby("variable"):
    row = part.iloc[0]
    raster_crs = row["crs"]
    parcel_projected = parcels.to_crs(raster_crs)
    raster_extent = box(row["min_x"], row["min_y"], row["max_x"], row["max_y"])
    spatial_rows.append({
        "variable": family, "parcel_crs": str(parcels.crs), "raster_crs": raster_crs,
        "reprojection_required": str(parcels.crs) != raster_crs,
        "invalid_geometries": int((~parcels.geometry.is_valid).sum()),
        "empty_geometries": int(parcels.geometry.is_empty.sum()),
        "parcels_intersecting_extent": int(parcel_projected.intersects(raster_extent).sum()),
        "parcels_outside_extent": int((~parcel_projected.intersects(raster_extent)).sum()),
    })
spatial_audit = pd.DataFrame(spatial_rows)
spatial_audit.to_csv(OUTPUT_DIR / "environment_spatial_compatibility.csv", index=False)

topo_rows = []
for path in sorted(TOPO_DIR.rglob("*.tif")):
    variable, _, _ = identify(path)
    with rasterio.open(path) as src:
        topo_rows.append({
            "variable": variable, "filepath": str(path.relative_to(ROOT)), "crs": str(src.crs),
            "resolution_x": src.res[0], "resolution_y": src.res[1],
            "width": src.width, "height": src.height, "nodata": src.nodata,
            "min_x": src.bounds.left, "max_x": src.bounds.right,
            "min_y": src.bounds.bottom, "max_y": src.bounds.top,
        })
pd.DataFrame(topo_rows).to_csv(OUTPUT_DIR / "topography_raster_inventory.csv", index=False)

(OUTPUT_DIR / "raster_inventory_manifest.json").write_text(json.dumps({
    "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    "climate_files": len(inventory),
    "missing_months": int(availability["status"].eq("missing").sum()),
    "duplicate_months": int(availability["status"].eq("duplicate").sum()),
    "raw_modified": False,
}, indent=2), encoding="utf-8")

print(inventory.groupby("variable").size().to_string())
print("\nDisponibilidad:\n", availability["status"].value_counts().to_string())
print("\nCompatibilidad:\n", spatial_audit.to_string(index=False))
