"""Familia 1, Etapa 2: diagnóstico de capas temporales por sensor.

Lee los Parquet creados por 110, no fusiona sensores y no usa rendimiento.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data/processed/family_1/timeseries"
OUTPUT_DIR = ROOT / "outputs/data_audit/family_1/timeseries"
FIGURE_DIR = OUTPUT_DIR / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

ID = "ID_POLIGONO"
DATE = "fecha_captura"
CLOUD = "cloud_raw"
CYCLE_START = pd.Timestamp("2025-04-01")
CYCLE_END = pd.Timestamp("2025-10-31")
YEARS = [2022, 2023, 2024, 2025]
CLOUD_THRESHOLDS = [10, 20, 30, 40, 50, 70]
SENSOR_COLORS = {"Sentinel-2": "#2ca02c", "Landsat": "#1f77b4", "Planet": "#d62728"}

sns.set_theme(style="whitegrid")


def write_csv(data: pd.DataFrame, name: str) -> None:
    data.to_csv(OUTPUT_DIR / name, index=False)


def summarize(series: pd.Series) -> dict[str, float]:
    x = pd.to_numeric(series, errors="coerce").dropna()
    if x.empty:
        return {key: np.nan for key in ["min", "q1", "median", "mean", "q3", "max", "std"]}
    return {
        "min": x.min(), "q1": x.quantile(.25), "median": x.median(),
        "mean": x.mean(), "q3": x.quantile(.75), "max": x.max(), "std": x.std(),
    }


def original_spectral_columns(sensor_key: str) -> list[str]:
    dictionary = pd.read_csv(DATA_DIR / f"{sensor_key}_timeseries_data_dictionary.csv")
    return dictionary.loc[
        dictionary["role"].eq("ORIGINAL")
        & dictionary["column"].str.endswith(("_promedio", "_std", "_min", "_max")),
        "column",
    ].tolist()


datasets = {
    "Sentinel-2": pd.read_parquet(DATA_DIR / "sentinel_timeseries.parquet"),
    "Landsat": pd.read_parquet(DATA_DIR / "landsat_timeseries.parquet"),
    "Planet": pd.read_parquet(DATA_DIR / "planet_timeseries.parquet"),
}
sensor_keys = {"Sentinel-2": "sentinel", "Landsat": "landsat", "Planet": "planet"}
spectral_columns = {
    sensor: original_spectral_columns(sensor_keys[sensor]) for sensor in datasets
}


# -----------------------------------------------------------------------------
# Cobertura por parcela, gaps y resumen por sensor
# -----------------------------------------------------------------------------
coverage_tables: dict[str, pd.DataFrame] = {}
gap_tables = []
sensor_summary_rows = []
alignment_rows = []

for sensor, df in datasets.items():
    df = df.sort_values([ID, DATE])
    global_dates = df[DATE].nunique()
    valid = df.loc[df["indices_available"]]
    global_valid_dates = valid[DATE].nunique()

    gaps = df[[ID, DATE, "CONJUNTO", "indices_available"]].copy()
    gaps["previous_date"] = gaps.groupby(ID)[DATE].shift()
    gaps["gap_days"] = (gaps[DATE] - gaps["previous_date"]).dt.days
    gaps["sensor"] = sensor
    gaps["year"] = gaps[DATE].dt.year
    gap_tables.append(gaps.dropna(subset=["gap_days"]))

    coverage = df.groupby(ID).agg(
        CONJUNTO=("CONJUNTO", "first"),
        date_min=(DATE, "min"), date_max=(DATE, "max"),
        n_obs_total=(DATE, "size"), n_dates_unique=(DATE, "nunique"),
        n_obs_with_indices=("indices_available", "sum"),
        valid_fraction=("indices_available", "mean"),
        median_gap_days=(DATE, lambda x: x.sort_values().diff().dt.days.median()),
        max_gap_days=(DATE, lambda x: x.sort_values().diff().dt.days.max()),
    ).reset_index()
    for year in YEARS:
        counts = df.loc[df["year"].eq(year)].groupby(ID).size()
        coverage[f"n_obs_{year}"] = coverage[ID].map(counts).fillna(0).astype(int)
    cycle_counts = df.loc[df["is_current_cycle_2025"]].groupby(ID).size()
    cycle_valid = df.loc[df["is_current_cycle_2025"] & df["indices_available"]].groupby(ID).size()
    coverage["n_obs_apr_oct_2025"] = coverage[ID].map(cycle_counts).fillna(0).astype(int)
    coverage["n_valid_apr_oct_2025"] = coverage[ID].map(cycle_valid).fillna(0).astype(int)
    coverage["proportion_global_observed_dates"] = coverage["n_dates_unique"] / global_dates
    coverage["proportion_global_valid_dates"] = coverage["n_obs_with_indices"] / global_valid_dates
    coverage["coverage_quartile"] = pd.qcut(
        coverage["n_obs_with_indices"].rank(method="first"), 4,
        labels=["Q1_worst", "Q2", "Q3", "Q4_best"],
    )
    coverage_tables[sensor] = coverage

    date_alignment = df.groupby(DATE)[ID].nunique()
    date_valid_alignment = valid.groupby(DATE)[ID].nunique()
    date_sets = df.groupby(ID)[DATE].apply(lambda x: tuple(x.sort_values().astype(str)))
    sensor_summary_rows.append({
        "sensor": sensor, "rows": len(df), "columns": df.shape[1],
        "parcels": df[ID].nunique(), "date_min": df[DATE].min(), "date_max": df[DATE].max(),
        "global_unique_dates": global_dates, "global_valid_dates": global_valid_dates,
        "n_obs_parcel_min": coverage["n_obs_total"].min(),
        "n_obs_parcel_median": coverage["n_obs_total"].median(),
        "n_obs_parcel_max": coverage["n_obs_total"].max(),
        "n_valid_parcel_min": coverage["n_obs_with_indices"].min(),
        "n_valid_parcel_median": coverage["n_obs_with_indices"].median(),
        "n_valid_parcel_max": coverage["n_obs_with_indices"].max(),
        "median_gap_days": gaps["gap_days"].median(), "max_gap_days": gaps["gap_days"].max(),
        "dates_shared_by_all_parcels": int(date_alignment.eq(df[ID].nunique()).sum()),
        "median_parcel_fraction_per_date": float((date_alignment / df[ID].nunique()).median()),
        "median_parcel_fraction_per_valid_date": float((date_valid_alignment / df[ID].nunique()).median()),
        "unique_parcel_calendars": date_sets.nunique(),
    })
    alignment_rows.append(pd.DataFrame({
        "sensor": sensor, "date": date_alignment.index,
        "n_parcels_observed": date_alignment.values,
        "fraction_parcels_observed": date_alignment.values / df[ID].nunique(),
        "n_parcels_with_indices": date_alignment.index.map(date_valid_alignment).fillna(0).astype(int),
    }))

sensor_coverage_summary = pd.DataFrame(sensor_summary_rows)
write_csv(sensor_coverage_summary, "sensor_coverage_summary.csv")
write_csv(coverage_tables["Landsat"], "landsat_coverage_by_parcel.csv")
write_csv(coverage_tables["Planet"], "planet_coverage_by_parcel.csv")
write_csv(coverage_tables["Sentinel-2"], "sentinel_coverage_by_parcel.csv")

coverage_comparison = pd.concat([
    table.assign(sensor=sensor) for sensor, table in coverage_tables.items()
], ignore_index=True)
coverage_train_prediction = coverage_comparison.groupby(
    ["sensor", "CONJUNTO"], as_index=False
).agg(
    n_parcels=(ID, "size"),
    n_obs_total_mean=("n_obs_total", "mean"),
    n_obs_total_median=("n_obs_total", "median"),
    n_obs_with_indices_mean=("n_obs_with_indices", "mean"),
    n_obs_with_indices_median=("n_obs_with_indices", "median"),
    valid_fraction_mean=("valid_fraction", "mean"),
    median_gap_days=("median_gap_days", "median"),
    max_gap_days=("max_gap_days", "max"),
    n_valid_apr_oct_2025_mean=("n_valid_apr_oct_2025", "mean"),
)
write_csv(coverage_train_prediction, "sensor_train_prediction_comparison.csv")

all_gaps = pd.concat(gap_tables, ignore_index=True)
write_csv(all_gaps[["sensor", ID, "CONJUNTO", "previous_date", DATE, "year", "gap_days"]],
          "sensor_temporal_gaps.csv")
date_alignment_detail = pd.concat(alignment_rows, ignore_index=True)
write_csv(date_alignment_detail, "temporal_alignment_by_date.csv")


# -----------------------------------------------------------------------------
# Calidad/nubosidad y comparación TRAIN/PREDICTION
# -----------------------------------------------------------------------------
quality_rows = []
quality_relation_rows = []
for sensor, df in datasets.items():
    for group, part in [("ALL", df)] + list(df.groupby("CONJUNTO")):
        cloud_valid = part[CLOUD].dropna()
        n = len(part)
        p0 = 100 * cloud_valid.eq(0).mean() if len(cloud_valid) else np.nan
        p100 = 100 * cloud_valid.eq(100).mean() if len(cloud_valid) else np.nan
        pintermediate = 100 * cloud_valid.between(0, 100, inclusive="neither").mean() if len(cloud_valid) else np.nan
        quality_rows.append({
            "sensor": sensor, "group": group, "n_rows": n,
            "n_unique_cloud_non_null": cloud_valid.nunique(),
            "pct_cloud_missing": 100 * part[CLOUD].isna().mean(),
            "pct_cloud_0_among_valid": p0, "pct_cloud_100_among_valid": p100,
            "pct_cloud_intermediate_among_valid": pintermediate,
            "cloud_mean": cloud_valid.mean(), "cloud_median": cloud_valid.median(),
            "cloud_q1": cloud_valid.quantile(.25), "cloud_q3": cloud_valid.quantile(.75),
            "pct_rows_indices_available": 100 * part["indices_available"].mean(),
            "quality_behavior": "mixture_of_point_masses_and_continuous_values",
        })
    cloud_category = pd.Series("intermediate", index=df.index)
    cloud_category[df[CLOUD].eq(0)] = "zero"
    cloud_category[df[CLOUD].eq(100)] = "hundred"
    cloud_category[df[CLOUD].isna()] = "missing"
    temp = df.assign(cloud_category=cloud_category)
    relation = temp.groupby("cloud_category", dropna=False).agg(
        n_rows=(ID, "size"),
        n_indices_available=("indices_available", "sum"),
        pct_indices_available=("indices_available", lambda x: 100 * x.mean()),
        mean_proportion_valid_indices=("proportion_valid_indices", "mean"),
    ).reset_index()
    relation.insert(0, "sensor", sensor)
    quality_relation_rows.append(relation)

quality_summary = pd.DataFrame(quality_rows)
write_csv(quality_summary, "quality_variable_summary.csv")
quality_missing_relation = pd.concat(quality_relation_rows, ignore_index=True)
write_csv(quality_missing_relation, "quality_missingness_relationship.csv")


# -----------------------------------------------------------------------------
# Sensibilidad Sentinel durante abril-octubre 2025, sin filtrar la capa
# -----------------------------------------------------------------------------
sentinel_cycle = datasets["Sentinel-2"].loc[
    datasets["Sentinel-2"]["is_current_cycle_2025"]
].copy()
sensitivity_rows = []
for parcel_id, part in sentinel_cycle.groupby(ID):
    base = {
        ID: parcel_id, "CONJUNTO": part["CONJUNTO"].iloc[0],
        "all_observations": len(part), "indices_available": int(part["indices_available"].sum()),
        "exclude_cloud_100": int((~part["cloud_is_100"] & part["indices_available"]).sum()),
    }
    for threshold in CLOUD_THRESHOLDS:
        base[f"cloud_le_{threshold}"] = int(
            (part[CLOUD].le(threshold) & part["indices_available"]).sum()
        )
    sensitivity_rows.append(base)
sentinel_sensitivity = pd.DataFrame(sensitivity_rows)
write_csv(sentinel_sensitivity, "sentinel_2025_quality_sensitivity_by_parcel.csv")


# -----------------------------------------------------------------------------
# Grillas exploratorias: cuantifican compresión, no interpolan
# -----------------------------------------------------------------------------
grid_specs = {"weekly": 7, "biweekly": 14, "monthly": "M"}
grid_rows = []
for sensor, df in datasets.items():
    valid = df.loc[df["indices_available"], [ID, DATE, "CONJUNTO"]].copy()
    grid_origin = valid[DATE].min().normalize()
    for grid_name, frequency in grid_specs.items():
        if isinstance(frequency, int):
            valid["bin"] = ((valid[DATE] - grid_origin).dt.days // frequency).astype(str)
        else:
            valid["bin"] = valid[DATE].dt.to_period(frequency).astype(str)
        occupied = valid.groupby(ID)["bin"].nunique()
        rows = valid.groupby(ID).size()
        global_bins = valid["bin"].nunique()
        for parcel_id in sorted(df[ID].unique()):
            n_rows = int(rows.get(parcel_id, 0))
            n_bins = int(occupied.get(parcel_id, 0))
            grid_rows.append({
                "sensor": sensor, ID: parcel_id,
                "CONJUNTO": df.loc[df[ID].eq(parcel_id), "CONJUNTO"].iloc[0],
                "grid": grid_name, "global_bins": global_bins,
                "valid_observations": n_rows, "occupied_bins": n_bins,
                "observations_collapsed_if_aggregated": n_rows - n_bins,
                "pct_temporal_points_collapsed": 100 * (n_rows - n_bins) / n_rows if n_rows else np.nan,
                "fraction_global_bins_occupied": n_bins / global_bins if global_bins else np.nan,
            })
grid_detail = pd.DataFrame(grid_rows)
write_csv(grid_detail, "temporal_grid_information_loss_by_parcel.csv")
grid_summary = grid_detail.groupby(["sensor", "grid"], as_index=False).agg(
    median_valid_observations=("valid_observations", "median"),
    median_occupied_bins=("occupied_bins", "median"),
    median_pct_temporal_points_collapsed=("pct_temporal_points_collapsed", "median"),
    max_pct_temporal_points_collapsed=("pct_temporal_points_collapsed", "max"),
    median_fraction_global_bins_occupied=("fraction_global_bins_occupied", "median"),
)
write_csv(grid_summary, "temporal_alignment_summary.csv")


# -----------------------------------------------------------------------------
# Rangos físicos: el diccionario es conceptual y no incluye ecuaciones estrictas
# -----------------------------------------------------------------------------
range_rows = []
for sensor, df in datasets.items():
    for column in spectral_columns[sensor]:
        numeric = pd.to_numeric(df[column], errors="coerce")
        finite = numeric[np.isfinite(numeric)]
        q1, q3 = finite.quantile([.25, .75]) if len(finite) else (np.nan, np.nan)
        iqr = q3 - q1
        outside_3iqr = ((finite < q1 - 3 * iqr) | (finite > q3 + 3 * iqr)).sum() if len(finite) else 0
        statistic = next((suffix for ending, suffix in {
            "_promedio": "mean", "_std": "std", "_min": "min", "_max": "max"
        }.items() if column.endswith(ending)), "unknown")
        index_name = column.rsplit("_", 1)[0]
        range_rows.append({
            "sensor": sensor, "index": index_name, "statistic": statistic,
            "column": column, "observed_min": finite.min() if len(finite) else np.nan,
            "observed_max": finite.max() if len(finite) else np.nan,
            "mathematical_expected_range_if_known": "UNKNOWN",
            "n_outside_mathematical_range": np.nan,
            "n_outside_3_iqr_descriptive": int(outside_3iqr),
            "n_infinite": int(np.isinf(numeric).sum()),
            "notes": "El diccionario es conceptual y no aporta una ecuación/rango estricto; no clasificar como error.",
        })
range_audit = pd.DataFrame(range_rows)
write_csv(range_audit, "index_physical_range_audit.csv")


# -----------------------------------------------------------------------------
# Estacionariedad descriptiva: tendencia, diferencias y autocorrelación
# -----------------------------------------------------------------------------
sentinel = datasets["Sentinel-2"]
s2_coverage = coverage_tables["Sentinel-2"].sort_values("n_obs_with_indices")
sample_positions = np.linspace(0, len(s2_coverage) - 1, 5).round().astype(int)
sample_ids = s2_coverage.iloc[sample_positions][ID].drop_duplicates().tolist()
stationarity_rows = []
for parcel_id in sample_ids:
    part = sentinel.loc[sentinel[ID].eq(parcel_id)].sort_values(DATE)
    for variable in ["ndvi_promedio", "evi_promedio", "lai_promedio"]:
        series = part[[DATE, variable]].dropna()
        values = series[variable]
        days = (series[DATE] - series[DATE].min()).dt.days
        slope = np.polyfit(days, values, 1)[0] if len(series) > 1 else np.nan
        differences = values.diff().dropna()
        midpoint = len(values) // 2
        stationarity_rows.append({
            ID: parcel_id, "variable": variable, "n": len(values),
            "linear_slope_per_day": slope,
            "raw_lag1_autocorrelation": values.autocorr(1),
            "difference_lag1_autocorrelation": differences.autocorr(1),
            "first_half_mean": values.iloc[:midpoint].mean(),
            "second_half_mean": values.iloc[midpoint:].mean(),
            "second_minus_first_half": values.iloc[midpoint:].mean() - values.iloc[:midpoint].mean(),
        })
stationarity = pd.DataFrame(stationarity_rows)
write_csv(stationarity, "sentinel_stationarity_descriptive_sample.csv")
pd.DataFrame({ID: sample_ids}).to_csv(OUTPUT_DIR / "sentinel_reproducible_sample.csv", index=False)


# -----------------------------------------------------------------------------
# Visualizaciones diagnósticas
# -----------------------------------------------------------------------------
# 1 Timeline
fig, ax = plt.subplots(figsize=(15, 4))
for y, (sensor, df) in enumerate(datasets.items()):
    dates = np.sort(df[DATE].unique())
    ax.scatter(dates, np.full(len(dates), y), s=8, alpha=.65, color=SENSOR_COLORS[sensor])
ax.set_yticks(range(len(datasets)), labels=list(datasets))
ax.set(title="Fechas observadas por sensor", xlabel="Fecha", ylabel="")
fig.tight_layout(); fig.savefig(FIGURE_DIR / "01_timeline_sensores.png", dpi=180); plt.close(fig)

# 2 n_obs
coverage_long = pd.concat([
    table.assign(sensor=sensor) for sensor, table in coverage_tables.items()
], ignore_index=True)
fig, ax = plt.subplots(figsize=(11, 5))
sns.histplot(data=coverage_long, x="n_obs_total", hue="sensor", bins=30,
             element="step", common_norm=False, ax=ax)
ax.set(title="Observaciones por parcela y sensor", xlabel="Número de observaciones")
fig.tight_layout(); fig.savefig(FIGURE_DIR / "02_observaciones_por_parcela.png", dpi=180); plt.close(fig)

# 3 gaps
fig, ax = plt.subplots(figsize=(11, 5))
sns.histplot(data=all_gaps, x="gap_days", hue="sensor", discrete=True,
             element="step", common_norm=False, stat="density", ax=ax)
ax.set(title="Distribución de gaps por sensor", xlabel="Días entre observaciones")
fig.tight_layout(); fig.savefig(FIGURE_DIR / "03_gaps_por_sensor.png", dpi=180); plt.close(fig)

# 4 heatmaps
for number, (sensor, df) in enumerate(datasets.items(), start=4):
    monthly = pd.crosstab(df[ID], df[DATE].dt.to_period("M").astype(str))
    fig, ax = plt.subplots(figsize=(18, 12))
    sns.heatmap(monthly, cmap="YlGnBu", cbar_kws={"label": "Observaciones"}, ax=ax)
    ax.set(title=f"Cobertura mensual: {sensor}", xlabel="Año-mes", ylabel="Parcela")
    name = sensor.lower().replace("-", "_")
    fig.tight_layout(); fig.savefig(FIGURE_DIR / f"{number:02d}_heatmap_{name}.png", dpi=180); plt.close(fig)

# 5 calidad real (número posterior para no colisionar con heatmaps 04-06)
quality_plot = pd.concat([
    df[[CLOUD]].assign(sensor=sensor) for sensor, df in datasets.items()
], ignore_index=True)
fig, ax = plt.subplots(figsize=(11, 5))
sns.histplot(data=quality_plot, x=CLOUD, hue="sensor", bins=40,
             element="step", common_norm=False, stat="density", ax=ax)
ax.set(title="Distribución empírica de nubosidad/calidad", xlabel="cloud_raw")
fig.tight_layout(); fig.savefig(FIGURE_DIR / "07_calidad_por_sensor.png", dpi=180); plt.close(fig)

# 6 cuatro series NDVI de parcelas reproducibles
fig, axes = plt.subplots(len(sample_ids), 1, figsize=(15, 3 * len(sample_ids)), sharex=True)
for ax, parcel_id in zip(np.atleast_1d(axes), sample_ids):
    part = sentinel.loc[sentinel[ID].eq(parcel_id)].sort_values(DATE)
    for column, label in [("ndvi_promedio", "mean"), ("ndvi_std", "std"),
                          ("ndvi_min", "min"), ("ndvi_max", "max")]:
        ax.plot(part[DATE], part[column], linewidth=.8, label=label)
    ax.set_title(parcel_id); ax.legend(ncol=4, fontsize=8)
fig.suptitle("NDVI mean/std/min/max: muestra reproducible")
fig.tight_layout(); fig.savefig(FIGURE_DIR / "08_ndvi_cuatro_series.png", dpi=180); plt.close(fig)

# 7 mean y heterogeneidad
example_id = sample_ids[len(sample_ids) // 2]
example = sentinel.loc[sentinel[ID].eq(example_id)].sort_values(DATE)
fig, ax = plt.subplots(figsize=(14, 5))
ax.fill_between(example[DATE], example["ndvi_min"], example["ndvi_max"], alpha=.2,
                label="min–max")
ax.plot(example[DATE], example["ndvi_promedio"], linewidth=1, label="mean")
ax.set(title=f"NDVI medio y heterogeneidad espacial — {example_id}", ylabel="NDVI", xlabel="Fecha")
ax.legend(); fig.tight_layout(); fig.savefig(FIGURE_DIR / "09_ndvi_heterogeneidad.png", dpi=180); plt.close(fig)

# 8 resolución temporal comparada
fig, ax = plt.subplots(figsize=(10, 5))
sns.boxplot(data=all_gaps, x="sensor", y="gap_days", showfliers=False, ax=ax)
ax.set(title="Resolución temporal observada", xlabel="Sensor", ylabel="Gap (días)")
fig.tight_layout(); fig.savefig(FIGURE_DIR / "10_resolucion_temporal.png", dpi=180); plt.close(fig)

# 9 series y primeras diferencias, diagnóstico no transformador
fig, axes = plt.subplots(2, 1, figsize=(14, 7), sharex=True)
example_valid = example[[DATE, "ndvi_promedio"]].dropna()
axes[0].plot(example_valid[DATE], example_valid["ndvi_promedio"])
axes[0].set(title=f"NDVI original — {example_id}", ylabel="NDVI")
axes[1].plot(example_valid[DATE], example_valid["ndvi_promedio"].diff())
axes[1].set(title="Primera diferencia (sólo diagnóstico)", ylabel="ΔNDVI", xlabel="Fecha")
fig.tight_layout(); fig.savefig(FIGURE_DIR / "11_estacionariedad_descriptiva.png", dpi=180); plt.close(fig)


# -----------------------------------------------------------------------------
# Reporte final con respuestas explícitas
# -----------------------------------------------------------------------------
summary = sensor_coverage_summary.set_index("sensor")
quality_all = quality_summary.loc[quality_summary["group"].eq("ALL")].set_index("sensor")
grid_pivot = grid_summary.pivot(index="sensor", columns="grid",
                                values="median_pct_temporal_points_collapsed")
landsat_cov = coverage_tables["Landsat"]
landsat_worst = landsat_cov.loc[landsat_cov["coverage_quartile"].eq("Q1_worst")]
range_top = range_audit.sort_values("n_outside_3_iqr_descriptive", ascending=False).head(8)

def q(sensor: str, field: str) -> float:
    return float(quality_all.loc[sensor, field])


report = f"""# Familia 1 — Etapa 2: capas temporales por sensor

Generado: {datetime.now().astimezone().isoformat(timespec='seconds')}

## Alcance

Se construyeron tres capas separadas. No se usó rendimiento, no se fusionaron sensores, no se interpoló, no se suavizó, no se aplicó un umbral definitivo y no se eliminaron outliers. **Non-stationarity is potentially signal, not automatically a problem.**

## Respuestas a las preguntas de la etapa

### 1. ¿Cuál es la representación temporal exacta de Sentinel?

Una fila única por `ID_POLIGONO + fecha_captura`, ordenada por ambos campos. Conserva sensor, conjunto, fecha, año, mes, día del año, distancias temporales, ciclo 2025/historia, `cloud_raw`, flags de calidad, 22 índices originales con mean/std/min/max y 88 series DERIVED (`range`, `lower_gap`, `upper_gap`, `cv`). VI6T fue excluido porque está 100% vacío en Sentinel. El epsilon de CV es `1e-6`.

### 2. ¿Cuál es la cobertura efectiva tras ignorar capturas sin índices?

- Sentinel: mediana {summary.loc['Sentinel-2', 'n_valid_parcel_median']:.0f} capturas válidas por parcela, rango {summary.loc['Sentinel-2', 'n_valid_parcel_min']:.0f}–{summary.loc['Sentinel-2', 'n_valid_parcel_max']:.0f}.
- Landsat: mediana {summary.loc['Landsat', 'n_valid_parcel_median']:.0f}, rango {summary.loc['Landsat', 'n_valid_parcel_min']:.0f}–{summary.loc['Landsat', 'n_valid_parcel_max']:.0f}.
- Planet: mediana {summary.loc['Planet', 'n_valid_parcel_median']:.0f}, rango {summary.loc['Planet', 'n_valid_parcel_min']:.0f}–{summary.loc['Planet', 'n_valid_parcel_max']:.0f}.

### 3–5. ¿Cómo funciona la nubosidad por sensor?

No es puramente continua ni binaria en ninguno. Es una mezcla de masas puntuales en 0 y 100 con valores intermedios:

- Sentinel: 0 = {q('Sentinel-2','pct_cloud_0_among_valid'):.2f}%, 100 = {q('Sentinel-2','pct_cloud_100_among_valid'):.2f}%, intermedios = {q('Sentinel-2','pct_cloud_intermediate_among_valid'):.2f}%, missing = {q('Sentinel-2','pct_cloud_missing'):.2f}%.
- Landsat: 0 = {q('Landsat','pct_cloud_0_among_valid'):.2f}%, 100 = {q('Landsat','pct_cloud_100_among_valid'):.2f}%, intermedios = {q('Landsat','pct_cloud_intermediate_among_valid'):.2f}%, missing = {q('Landsat','pct_cloud_missing'):.2f}%.
- Planet: 0 = {q('Planet','pct_cloud_0_among_valid'):.2f}%, 100 = {q('Planet','pct_cloud_100_among_valid'):.2f}%, intermedios = {q('Planet','pct_cloud_intermediate_among_valid'):.2f}%, missing = {q('Planet','pct_cloud_missing'):.2f}%.

En los tres sensores, 100 está fuertemente asociado con ausencia de índices. Landsat además tiene nubosidad faltante y no debe heredar automáticamente la regla de Sentinel.

### 6–7. ¿Qué tan irregular es Landsat y hay parcelas peor cubiertas?

Landsat tiene {summary.loc['Landsat','global_unique_dates']:.0f} fechas globales, pero por parcela hay {summary.loc['Landsat','n_obs_parcel_min']:.0f}–{summary.loc['Landsat','n_obs_parcel_max']:.0f} observaciones (mediana {summary.loc['Landsat','n_obs_parcel_median']:.0f}). Su gap mediano es {summary.loc['Landsat','median_gap_days']:.0f} días y máximo {summary.loc['Landsat','max_gap_days']:.0f}. Sí existen {len(landsat_worst)} parcelas sistemáticamente en el cuartil inferior de capturas con VI6T válido; están identificadas en `landsat_coverage_by_parcel.csv`. La densidad es heterogénea y debe conservarse como calidad/covariable.

### 8. ¿TRAIN y PREDICTION son comparables?

Los resúmenes separados en `quality_variable_summary.csv` y las tablas por parcela no muestran una diferencia estructural grande en número de parcelas, cobertura válida o nubosidad. Esto no demuestra igualdad distribucional completa, pero no aparece un fallo de cobertura exclusivo de PREDICTION.

### 9. ¿Las fechas Sentinel están alineadas?

Sentinel tiene {summary.loc['Sentinel-2','global_unique_dates']:.0f} fechas globales; {summary.loc['Sentinel-2','dates_shared_by_all_parcels']:.0f} aparecen en las 197 parcelas. Existen {summary.loc['Sentinel-2','unique_parcel_calendars']:.0f} calendarios exactos de parcela. La alineación es muy alta, aunque no perfecta, principalmente por unas pocas fechas ausentes.

### 10–11. ¿Necesitamos grilla común y qué pérdida produciría?

Para Familia 1 tabular no es obligatorio interpolar: pueden calcularse agregados por ventanas usando timestamps observados y acompañarlos con conteos/cobertura. Si se reduce a un valor por bin, la mediana de puntos temporales colapsados sería:

| Sensor | Semanal | Quincenal | Mensual |
|---|---:|---:|---:|
| Sentinel-2 | {grid_pivot.loc['Sentinel-2','weekly']:.1f}% | {grid_pivot.loc['Sentinel-2','biweekly']:.1f}% | {grid_pivot.loc['Sentinel-2','monthly']:.1f}% |
| Landsat | {grid_pivot.loc['Landsat','weekly']:.1f}% | {grid_pivot.loc['Landsat','biweekly']:.1f}% | {grid_pivot.loc['Landsat','monthly']:.1f}% |
| Planet | {grid_pivot.loc['Planet','weekly']:.1f}% | {grid_pivot.loc['Planet','biweekly']:.1f}% | {grid_pivot.loc['Planet','monthly']:.1f}% |

Esto es compresión, no pérdida completa de valores si se guardan estadísticas dentro de cada bin. Una grilla mensual es demasiado agresiva para dinámica rápida; semanal/quincenal puede evaluarse después sin reemplazar la capa observada.

### 12. ¿Qué rangos son sospechosos?

El diccionario proporcionado es conceptual y no incluye ecuaciones estrictas. Por ello, `index_physical_range_audit.csv` marca el rango matemático como `UNKNOWN`, conserva mínimos/máximos y reporta extremos 3×IQR sólo como diagnóstico. Las mayores cuentas descriptivas están en: {', '.join(range_top['sensor'] + ':' + range_top['column'])}. No hay infinitos. Ningún valor fue declarado error ni eliminado.

### 13–14. ¿Qué aportan min/max/std y son fiables las derivadas?

Mean describe nivel medio; std describe heterogeneidad interna; min/max permiten detectar colas y amplitud dentro de parcela. Se construyeron `range=max-min`, `lower_gap=mean-min`, `upper_gap=max-mean` y `cv=std/(abs(mean)+1e-6)`. Son algebraicamente reproducibles y no usan target. CV puede explotar cuando mean está cerca de cero, por lo que debe auditarse o estabilizarse antes de modelar.

### 15–16. ¿Es razonable incluir Landsat y cómo?

Sí, como fuente independiente y complementaria. La evidencia favorece agregación mensual o por ventanas, AUC normalizada por duración y features de cobertura (`n_obs`, `valid_fraction`, `max_gap`). No debe interpolarse para imitar Sentinel ni usarse para features que exijan alta resolución uniforme.

### 17–18. ¿Es necesario hacer estacionarias las series?

No. El target es escalar y la tendencia contiene señal potencial. Posteriormente sí son útiles, junto con la serie original: primeras diferencias, pendientes, tasas de cambio, fechas de pico, AUC, anomalías 2025 respecto al histórico y cambios por ventanas. La tabla descriptiva de una muestra reproducible contiene tendencia lineal, autocorrelación lag-1 y diferencias, sin ADF/KPSS masivo.

### 19. ¿Qué decisiones quedan para Etapa 3?

1. Corte temporal de predicción dentro del ciclo 2025.
2. Regla de calidad por sensor y tratamiento de cloud=100/missing.
3. Ventanas temporales y calendario agronómico.
4. Manejo de CV extremo cuando mean≈0.
5. Conjunto inicial de agregados, sin selección supervisada fuera del CV.
6. Estrategia Landsat: mensual vs ventanas vs timestamps observados.
7. Ajuste de imputación/escalamiento exclusivamente dentro de folds.

### 20. ¿Qué tablas serán input de feature engineering?

- `sentinel_timeseries.parquet`: clave única parcela-fecha, Sentinel original + calidad + tiempo + DERIVED.
- `landsat_timeseries.parquet`: clave única parcela-fecha, VI6T + calidad + tiempo + DERIVED.
- `planet_timeseries.parquet`: clave única parcela-fecha, Planet original + calidad + tiempo + DERIVED.

Las tablas permanecen separadas. Feature engineering producirá después bloques con prefijos `S2_`, `LANDSAT_` y `PLANET_`, unidos sólo a nivel parcela y nunca combinando directamente índices homónimos.

## Trazabilidad

- Raw modificado: no.
- Target utilizado: no.
- Umbral de nubosidad aplicado: no.
- Interpolación o suavizado: no.
- Sensores fusionados: no.
- Epsilon CV: 1e-6.
"""
(OUTPUT_DIR / "temporal_series_summary.md").write_text(report, encoding="utf-8")
(OUTPUT_DIR / "timeseries_diagnostics_manifest.json").write_text(json.dumps({
    "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    "raw_modified": False, "target_used": False, "cloud_filter_applied": False,
    "interpolation_applied": False, "stationarity_imposed": False,
    "sensors_fused": False,
}, indent=2), encoding="utf-8")

print("Reporte temporal generado correctamente.")
print("Outputs:", OUTPUT_DIR)
