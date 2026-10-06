"""Familia 1, Etapa 2: construir capas temporales canónicas por sensor.

No fusiona sensores, no interpola, no filtra por nubosidad y no usa rendimiento.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
RAW_BASIC = ROOT / "data/original/01_tablas_maestras/Conjunto_datos_BASICO_AgroCebada2026.csv"
RAW_PRO = ROOT / "data/original/01_tablas_maestras/Conjunto_datos_PRO_AgroCebada.csv"
MASTER = ROOT / "data/original/01_tablas_maestras/ID_area_rendimiento_70_30_Reto_AgroCebada.csv"
OUTPUT_DIR = ROOT / "data/processed/family_1/timeseries"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ID = "ID_POLIGONO"
DATE = "fecha_captura"
SENSOR = "sensor"
CLOUD_SOURCE = "porcentaje_nubosidad"
CLOUD = "cloud_raw"
CYCLE_START = pd.Timestamp("2025-04-01")
CYCLE_END = pd.Timestamp("2025-10-31")
EPSILON_CV = 1e-6
STAT_SUFFIXES = {
    "_promedio": "mean",
    "_std": "std",
    "_min": "min",
    "_max": "max",
}


def index_structure(columns: list[str]) -> dict[str, dict[str, str]]:
    structure: dict[str, dict[str, str]] = {}
    for column in columns:
        for suffix, statistic in STAT_SUFFIXES.items():
            if column.endswith(suffix):
                index_name = column.removesuffix(suffix)
                structure.setdefault(index_name, {})[statistic] = column
                break
    return structure


def build_canonical(source: pd.DataFrame, sensor_name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    data = source.copy()
    data[DATE] = pd.to_datetime(data[DATE], format="mixed", dayfirst=True, errors="coerce")
    data = data.sort_values([ID, DATE], kind="stable").reset_index(drop=True)

    if data[DATE].isna().any():
        raise ValueError(f"{sensor_name}: existen fechas inválidas")
    if data.duplicated([ID, DATE]).any():
        raise ValueError(f"{sensor_name}: la clave parcela-fecha no es única")

    data = data.merge(
        master[[ID, "CONJUNTO"]], on=ID, how="left", validate="many_to_one"
    )
    if data["CONJUNTO"].isna().any():
        raise ValueError(f"{sensor_name}: hay parcelas sin clasificación TRAIN/PREDICTION")

    data[SENSOR] = sensor_name
    data = data.rename(columns={CLOUD_SOURCE: CLOUD})

    structure = index_structure(data.columns.tolist())
    mean_columns = [parts["mean"] for parts in structure.values() if "mean" in parts]
    data["cloud_is_100"] = data[CLOUD].eq(100)
    data["n_valid_indices"] = data[mean_columns].notna().sum(axis=1).astype("int16")
    data["proportion_valid_indices"] = data["n_valid_indices"] / len(mean_columns)
    data["indices_available"] = data["n_valid_indices"].gt(0)
    data["all_indices_available"] = data["n_valid_indices"].eq(len(mean_columns))

    data["year"] = data[DATE].dt.year.astype("int16")
    data["month"] = data[DATE].dt.month.astype("int8")
    data["day_of_year"] = data[DATE].dt.dayofyear.astype("int16")
    global_start = data[DATE].min()
    parcel_start = data.groupby(ID)[DATE].transform("min")
    data["days_since_first_observation_global"] = (data[DATE] - global_start).dt.days
    data["days_since_first_observation_parcel"] = (data[DATE] - parcel_start).dt.days
    data["days_from_2025_04_01"] = (data[DATE] - CYCLE_START).dt.days
    data["is_current_cycle_2025"] = data[DATE].between(CYCLE_START, CYCLE_END)
    data["is_history_2022_2024"] = data["year"].between(2022, 2024)

    derived_data: dict[str, pd.Series] = {}
    for index_name, parts in structure.items():
        if not {"mean", "std", "min", "max"}.issubset(parts):
            continue
        mean, std, minimum, maximum = (
            parts["mean"], parts["std"], parts["min"], parts["max"]
        )
        definitions = {
            f"{index_name}_derived_range": data[maximum] - data[minimum],
            f"{index_name}_derived_lower_gap": data[mean] - data[minimum],
            f"{index_name}_derived_upper_gap": data[maximum] - data[mean],
            f"{index_name}_derived_cv": data[std] / (data[mean].abs() + EPSILON_CV),
        }
        derived_data.update(definitions)

    derived_columns = list(derived_data)
    if derived_data:
        data = pd.concat([data, pd.DataFrame(derived_data, index=data.index)], axis=1)

    leading = [
        ID, DATE, SENSOR, "CONJUNTO", "year", "month", "day_of_year",
        "days_since_first_observation_global", "days_since_first_observation_parcel",
        "days_from_2025_04_01", "is_current_cycle_2025", "is_history_2022_2024",
        CLOUD, "cloud_is_100", "indices_available", "all_indices_available",
        "n_valid_indices", "proportion_valid_indices",
    ]
    remaining = [column for column in data.columns if column not in leading]
    data = data[leading + remaining]

    dictionary_rows = []
    for column in data.columns:
        role = "ORIGINAL"
        description = "Variable original del archivo fuente"
        if column in [ID, SENSOR, "CONJUNTO"]:
            role, description = "IDENTIFIER", "Identificador o grupo; no derivado del target"
        elif column == DATE:
            role, description = "TIME", "Fecha de captura original convertida a datetime"
        elif column in ["year", "month", "day_of_year", "days_since_first_observation_global",
                        "days_since_first_observation_parcel", "days_from_2025_04_01",
                        "is_current_cycle_2025", "is_history_2022_2024"]:
            role, description = "TIME_AUXILIARY", "Variable temporal auxiliar no derivada del target"
        elif column in [CLOUD, "cloud_is_100", "indices_available", "all_indices_available",
                        "n_valid_indices", "proportion_valid_indices"]:
            role, description = "QUALITY", "Variable de calidad/disponibilidad"
        elif column in derived_columns:
            role, description = "DERIVED", "Heterogeneidad espacial derivada dentro de la misma observación"
        dictionary_rows.append({
            "column": column,
            "dtype": str(data[column].dtype),
            "role": role,
            "description": description,
            "sensor": sensor_name,
            "epsilon_cv": EPSILON_CV if column.endswith("_derived_cv") else np.nan,
        })
    return data, pd.DataFrame(dictionary_rows)


basic = pd.read_csv(RAW_BASIC, low_memory=False)
pro = pd.read_csv(RAW_PRO, low_memory=False)
master = pd.read_csv(MASTER).drop(columns=["Unnamed: 4"], errors="ignore")

sentinel_source = basic.loc[basic[SENSOR].eq("Sentinel-2")].copy()
sentinel_source = sentinel_source.drop(
    columns=["vi6t_promedio", "vi6t_std", "vi6t_min", "vi6t_max"], errors="ignore"
)
landsat_source = basic.loc[basic[SENSOR].eq("Landsat")].copy()
landsat_source = landsat_source.dropna(axis=1, how="all")
planet_source = pro.copy()

sources = {
    "sentinel": (sentinel_source, "Sentinel-2"),
    "landsat": (landsat_source, "Landsat"),
    "planet": (planet_source, "Planet"),
}

manifest_rows = []
for file_stem, (source, sensor_name) in sources.items():
    canonical, dictionary = build_canonical(source, sensor_name)
    parquet_path = OUTPUT_DIR / f"{file_stem}_timeseries.parquet"
    dictionary_path = OUTPUT_DIR / f"{file_stem}_timeseries_data_dictionary.csv"
    canonical.to_parquet(parquet_path, index=False)
    dictionary.to_csv(dictionary_path, index=False)
    reloaded = pd.read_parquet(parquet_path)
    if len(reloaded) != len(canonical) or reloaded.duplicated([ID, DATE]).any():
        raise RuntimeError(f"Falló la validación posterior a escritura: {file_stem}")
    manifest_rows.append({
        "sensor": sensor_name,
        "file": str(parquet_path.relative_to(ROOT)),
        "rows": len(canonical),
        "columns": canonical.shape[1],
        "parcels": canonical[ID].nunique(),
        "date_min": canonical[DATE].min().isoformat(),
        "date_max": canonical[DATE].max().isoformat(),
        "derived_columns": int(dictionary["role"].eq("DERIVED").sum()),
        "quality_columns": int(dictionary["role"].eq("QUALITY").sum()),
        "unique_ID_date": not canonical.duplicated([ID, DATE]).any(),
    })

manifest_df = pd.DataFrame(manifest_rows)
manifest_df.to_csv(OUTPUT_DIR / "timeseries_build_manifest.csv", index=False)
(OUTPUT_DIR / "timeseries_build_manifest.json").write_text(
    json.dumps({
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "epsilon_cv": EPSILON_CV,
        "raw_files_modified": False,
        "target_used": False,
        "cloud_filter_applied": False,
        "interpolation_applied": False,
        "sensors_fused": False,
        "tables": manifest_rows,
    }, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print(manifest_df.to_string(index=False))
print("\nCapas guardadas en:", OUTPUT_DIR)
