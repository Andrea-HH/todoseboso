"""Familia 1, etapa 1: auditoría reproducible de Sentinel-2.

Esta etapa es exclusivamente descriptiva. No filtra, interpola, imputa,
selecciona variables con el target ni construye features predictivas.
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
RAW_BASIC = ROOT / "data/original/01_tablas_maestras/Conjunto_datos_BASICO_AgroCebada2026.csv"
PROCESSED_SENTINEL = ROOT / "data/processed/01_tablas_maestras/sentinel.csv"
MASTER = ROOT / "data/original/01_tablas_maestras/ID_area_rendimiento_70_30_Reto_AgroCebada.csv"
PARCELS_SHP = ROOT / "data/original/02_conjunto_70_30/Parcelas_Reto_AGC_CONJUNTO.shp"
OUTPUT_DIR = ROOT / "outputs/data_audit/family_1/sentinel"
FIGURE_DIR = OUTPUT_DIR / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

ID = "ID_POLIGONO"
DATE = "fecha_captura"
SENSOR = "sensor"
CLOUD = "porcentaje_nubosidad"
CYCLE_START = pd.Timestamp("2025-04-01")
CYCLE_END = pd.Timestamp("2025-10-31")
CLOUD_THRESHOLDS = [10, 20, 30, 40, 50, 70]
YEARS = [2022, 2023, 2024, 2025]
SUMMARY_STATS = ["min", "q1", "median", "mean", "q3", "max", "std"]

sns.set_theme(style="whitegrid")


def describe_series(series: pd.Series) -> dict[str, float]:
    """Resumen solicitado, conservando NaN cuando no hay datos."""
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return {key: np.nan for key in SUMMARY_STATS}
    return {
        "min": numeric.min(),
        "q1": numeric.quantile(0.25),
        "median": numeric.median(),
        "mean": numeric.mean(),
        "q3": numeric.quantile(0.75),
        "max": numeric.max(),
        "std": numeric.std(),
    }


def write_csv(df: pd.DataFrame, name: str) -> None:
    df.to_csv(OUTPUT_DIR / name, index=False)


def classify_column(column: str) -> tuple[str, str | None, str | None]:
    """Devuelve rol, índice base y estadístico espacial."""
    if column == ID:
        return "identifier", None, None
    if column == DATE:
        return "date", None, None
    if column == SENSOR:
        return "sensor", None, None
    if column == CLOUD:
        return "quality", None, None
    for suffix, statistic in [
        ("_promedio", "mean"), ("_std", "std"),
        ("_min", "min"), ("_max", "max"),
    ]:
        if column.endswith(suffix):
            return "satellite_index", column.removesuffix(suffix), statistic
    return "other", None, None


# -----------------------------------------------------------------------------
# Lectura: fuente canónica original y contraste con el CSV procesado
# -----------------------------------------------------------------------------
basic = pd.read_csv(RAW_BASIC, low_memory=False)
sentinel_raw = basic.loc[basic[SENSOR].eq("Sentinel-2")].copy()
sentinel = sentinel_raw.copy()
sentinel[DATE] = pd.to_datetime(sentinel[DATE], format="mixed", dayfirst=True, errors="coerce")
master = pd.read_csv(MASTER).drop(columns=["Unnamed: 4"], errors="ignore")
processed = pd.read_csv(PROCESSED_SENTINEL, low_memory=False)

input_inventory = pd.DataFrame([
    {"role": "dataset_basico_original", "path": str(RAW_BASIC.relative_to(ROOT)),
     "rows": len(basic), "columns": basic.shape[1]},
    {"role": "sentinel_filtrado_del_original", "path": str(RAW_BASIC.relative_to(ROOT)),
     "rows": len(sentinel), "columns": sentinel.shape[1]},
    {"role": "sentinel_procesado_existente", "path": str(PROCESSED_SENTINEL.relative_to(ROOT)),
     "rows": len(processed), "columns": processed.shape[1]},
    {"role": "maestro_area_rendimiento", "path": str(MASTER.relative_to(ROOT)),
     "rows": len(master), "columns": master.shape[1]},
    {"role": "geometrias_parcelas", "path": str(PARCELS_SHP.relative_to(ROOT)),
     "rows": 197, "columns": None},
])
write_csv(input_inventory, "00_input_inventory.csv")


# -----------------------------------------------------------------------------
# A. Esquema
# -----------------------------------------------------------------------------
schema_rows = []
for position, column in enumerate(sentinel.columns):
    role, base_index, statistic = classify_column(column)
    non_null = sentinel[column].dropna()
    examples = non_null.astype(str).drop_duplicates().head(3).tolist()
    schema_rows.append({
        "position": position,
        "column": column,
        "dtype_read": str(sentinel_raw[column].dtype),
        "dtype_audit": str(sentinel[column].dtype),
        "role": role,
        "base_index": base_index,
        "spatial_statistic": statistic,
        "unit": "%" if column == CLOUD else "not_provided",
        "n_unique_non_null": non_null.nunique(),
        "example_values": " | ".join(examples),
    })
schema = pd.DataFrame(schema_rows)
write_csv(schema, "sentinel_schema.csv")

index_columns = schema.loc[schema["role"].eq("satellite_index")]
base_indices = sorted(index_columns["base_index"].dropna().unique())


# -----------------------------------------------------------------------------
# B-C. Parcelas y cobertura temporal
# -----------------------------------------------------------------------------
sentinel_ids = set(sentinel[ID].dropna().unique())
master_ids = set(master[ID].dropna().unique())
missing_in_sentinel = sorted(master_ids - sentinel_ids)
extra_in_sentinel = sorted(sentinel_ids - master_ids)

coverage_base = (
    sentinel.groupby(ID)
    .agg(
        fecha_min=(DATE, "min"),
        fecha_max=(DATE, "max"),
        n_observaciones=(DATE, "size"),
        n_fechas_unicas=(DATE, "nunique"),
        n_fechas_invalidas=(DATE, lambda s: s.isna().sum()),
    )
)
for year in YEARS:
    coverage_base[f"n_observaciones_{year}"] = sentinel.loc[
        sentinel[DATE].dt.year.eq(year)
    ].groupby(ID).size()
coverage_base["n_observaciones_abril_octubre_2025"] = sentinel.loc[
    sentinel[DATE].between(CYCLE_START, CYCLE_END)
].groupby(ID).size()
coverage = (
    coverage_base.fillna({f"n_observaciones_{year}": 0 for year in YEARS})
    .fillna({"n_observaciones_abril_octubre_2025": 0})
    .reset_index()
    .merge(master[[ID, "AREA_HA", "CONJUNTO"]], on=ID, how="left", validate="one_to_one")
)
count_columns = ["n_observaciones", "n_fechas_unicas", "n_fechas_invalidas"] + [
    f"n_observaciones_{year}" for year in YEARS
] + ["n_observaciones_abril_octubre_2025"]
coverage[count_columns] = coverage[count_columns].astype(int)
write_csv(coverage, "sentinel_parcel_coverage.csv")

coverage_summary_rows = []
for column in count_columns:
    coverage_summary_rows.append({"metric": column, **describe_series(coverage[column])})
coverage_summary = pd.DataFrame(coverage_summary_rows)
write_csv(coverage_summary, "sentinel_parcel_coverage_summary.csv")

parcel_reconciliation = pd.DataFrame({
    "check": [
        "master_unique_parcels", "sentinel_unique_parcels", "training_parcels",
        "prediction_parcels", "master_absent_in_sentinel", "sentinel_absent_in_master",
    ],
    "value": [
        len(master_ids), len(sentinel_ids), master["CONJUNTO"].eq("ENTRENAMIENTO").sum(),
        master["CONJUNTO"].eq("PREDICCION").sum(), len(missing_in_sentinel),
        len(extra_in_sentinel),
    ],
    "details": ["", "", "", "", " | ".join(missing_in_sentinel), " | ".join(extra_in_sentinel)],
})
write_csv(parcel_reconciliation, "sentinel_parcel_reconciliation.csv")


# -----------------------------------------------------------------------------
# D. Gaps temporales
# -----------------------------------------------------------------------------
unique_dates = sentinel[[ID, DATE]].dropna().drop_duplicates().sort_values([ID, DATE])
unique_dates["previous_date"] = unique_dates.groupby(ID)[DATE].shift()
unique_dates["gap_days"] = (unique_dates[DATE] - unique_dates["previous_date"]).dt.days
gaps = unique_dates.dropna(subset=["gap_days"]).copy()
gaps["year"] = gaps[DATE].dt.year
q1_gap, q3_gap = gaps["gap_days"].quantile([0.25, 0.75])
gap_iqr_limit = q3_gap + 1.5 * (q3_gap - q1_gap)
gaps["is_iqr_outlier"] = gaps["gap_days"].gt(gap_iqr_limit)
gaps["is_gap_gt_10_days"] = gaps["gap_days"].gt(10)
write_csv(gaps[[ID, "previous_date", DATE, "year", "gap_days", "is_iqr_outlier",
                "is_gap_gt_10_days"]], "sentinel_temporal_gaps.csv")

gap_by_parcel = (
    gaps.groupby(ID)["gap_days"]
    .agg(n_gaps="size", gap_min="min", gap_q1=lambda x: x.quantile(.25),
         gap_median="median", gap_mean="mean", gap_q3=lambda x: x.quantile(.75),
         gap_max="max", gap_std="std")
    .reset_index()
)
write_csv(gap_by_parcel, "sentinel_temporal_gaps_by_parcel.csv")

gap_by_year = gaps.groupby("year")["gap_days"].agg(
    n="size", min="min", q1=lambda x: x.quantile(.25), median="median",
    mean="mean", q3=lambda x: x.quantile(.75), max="max", std="std"
).reset_index()
write_csv(gap_by_year, "sentinel_temporal_gaps_by_year.csv")


# -----------------------------------------------------------------------------
# E. Integridad fecha/parcela y orden
# -----------------------------------------------------------------------------
exact_duplicate_mask = sentinel_raw.duplicated(keep=False)
key_duplicate_mask = sentinel.duplicated([ID, DATE], keep=False)
key_counts = sentinel.groupby([ID, DATE], dropna=False).size().reset_index(name="n_records")
multiple_keys = key_counts.loc[key_counts["n_records"].gt(1)]
order_violations = (
    sentinel.groupby(ID, sort=False)[DATE]
    .apply(lambda s: int((s.diff().dropna() < pd.Timedelta(0)).sum()))
    .sum()
)
integrity = pd.DataFrame([
    {"check": "invalid_dates", "value": int(sentinel[DATE].isna().sum())},
    {"check": "exact_duplicate_rows_keep_all", "value": int(exact_duplicate_mask.sum())},
    {"check": "exact_duplicate_groups", "value": int(sentinel_raw.loc[exact_duplicate_mask].drop_duplicates().shape[0])},
    {"check": "rows_in_duplicated_ID_date_keys", "value": int(key_duplicate_mask.sum())},
    {"check": "duplicated_ID_date_keys", "value": int(len(multiple_keys))},
    {"check": "max_records_per_ID_date", "value": int(key_counts["n_records"].max())},
    {"check": "within_parcel_backward_date_steps_in_file_order", "value": int(order_violations)},
])
write_csv(integrity, "sentinel_integrity_checks.csv")
write_csv(multiple_keys, "sentinel_multiple_records_per_date.csv")


# -----------------------------------------------------------------------------
# F. Missingness, índices, rangos y relaciones lógicas
# -----------------------------------------------------------------------------
missingness = pd.DataFrame({
    "column": sentinel.columns,
    "n_missing": sentinel.isna().sum().values,
    "pct_missing": (100 * sentinel.isna().mean()).values,
    "n_non_missing": sentinel.notna().sum().values,
})
missingness = missingness.merge(schema[["column", "role", "base_index", "spatial_statistic"]],
                                on="column", how="left")
write_csv(missingness, "sentinel_missingness.csv")

index_audit_rows = []
logical_rows = []
for index_name in base_indices:
    cols = {
        "mean": f"{index_name}_promedio", "std": f"{index_name}_std",
        "min": f"{index_name}_min", "max": f"{index_name}_max",
    }
    present = {key: value for key, value in cols.items() if value in sentinel.columns}
    for statistic, column in present.items():
        numeric = pd.to_numeric(sentinel[column], errors="coerce")
        finite = numeric[np.isfinite(numeric)]
        q1, q3 = finite.quantile([0.25, 0.75]) if len(finite) else (np.nan, np.nan)
        iqr = q3 - q1
        rare_mask = (finite < q1 - 3 * iqr) | (finite > q3 + 3 * iqr) if len(finite) else pd.Series(dtype=bool)
        index_audit_rows.append({
            "base_index": index_name, "statistic": statistic, "column": column,
            "n_missing": numeric.isna().sum(), "pct_missing": 100 * numeric.isna().mean(),
            "n_infinite": np.isinf(numeric).sum(), "n_unique_non_null": numeric.nunique(dropna=True),
            "is_constant_non_null": numeric.nunique(dropna=True) <= 1,
            "min_observed": finite.min() if len(finite) else np.nan,
            "q1": q1, "median": finite.median() if len(finite) else np.nan,
            "q3": q3, "max_observed": finite.max() if len(finite) else np.nan,
            "n_outside_3_iqr": int(rare_mask.sum()),
        })

    quartet_present = all(column in sentinel.columns for column in cols.values())
    if quartet_present:
        quartet = sentinel[list(cols.values())]
        complete = quartet.notna().all(axis=1)
        partial = quartet.notna().any(axis=1) & ~complete
        violation = complete & (
            (sentinel[cols["min"]] > sentinel[cols["mean"]])
            | (sentinel[cols["mean"]] > sentinel[cols["max"]])
            | (sentinel[cols["std"]] < 0)
        )
        logical_rows.append({
            "base_index": index_name, "has_full_quartet_columns": True,
            "rows_all_four_available": int(complete.sum()),
            "rows_partially_available": int(partial.sum()),
            "rows_all_four_missing": int(quartet.isna().all(axis=1).sum()),
            "violations_min_mean_max_or_negative_std": int(violation.sum()),
        })

index_audit = pd.DataFrame(index_audit_rows)
logical_audit = pd.DataFrame(logical_rows)
write_csv(index_audit, "sentinel_index_audit.csv")
write_csv(logical_audit, "sentinel_index_logical_checks.csv")


# -----------------------------------------------------------------------------
# G. Nubosidad y sensibilidad sin aplicar filtros
# -----------------------------------------------------------------------------
cloud_rows = []
for threshold in CLOUD_THRESHOLDS:
    for scope, subset in [
        ("all_2022_2025", sentinel),
        ("cycle_apr_oct_2025", sentinel.loc[sentinel[DATE].between(CYCLE_START, CYCLE_END)]),
    ]:
        for group_name, group_df in [("ALL", subset)] + list(subset.merge(
            master[[ID, "CONJUNTO"]], on=ID, how="left"
        ).groupby("CONJUNTO")):
            keep = group_df[CLOUD].le(threshold)
            cloud_rows.append({
                "scope": scope, "group": group_name, "threshold_pct": threshold,
                "n_total": len(group_df), "n_cloud_non_missing": group_df[CLOUD].notna().sum(),
                "n_retained": int(keep.sum()), "pct_retained_total": 100 * keep.mean(),
                "n_parcels_retained": group_df.loc[keep, ID].nunique(),
            })
cloud_sensitivity = pd.DataFrame(cloud_rows)
write_csv(cloud_sensitivity, "sentinel_cloud_sensitivity.csv")

cloud_by_parcel = sentinel.groupby(ID)[CLOUD].agg(
    n="size", n_valid="count", mean="mean", median="median",
    q1=lambda x: x.quantile(.25), q3=lambda x: x.quantile(.75), min="min", max="max"
).reset_index()
write_csv(cloud_by_parcel, "sentinel_cloud_by_parcel.csv")

cloud_by_year = sentinel.assign(year=sentinel[DATE].dt.year).groupby("year")[CLOUD].agg(
    n="size", n_valid="count", mean="mean", median="median",
    q1=lambda x: x.quantile(.25), q3=lambda x: x.quantile(.75), min="min", max="max"
).reset_index()
write_csv(cloud_by_year, "sentinel_cloud_by_year.csv")

# Relación entre nubosidad y disponibilidad de índices, excluyendo columnas 100% vacías.
usable_index_columns = missingness.loc[
    missingness["role"].eq("satellite_index") & missingness["pct_missing"].lt(100), "column"
].tolist()
cloud_missing_groups = [
    ("cloud_eq_100", sentinel[CLOUD].eq(100)),
    ("cloud_lt_100", sentinel[CLOUD].lt(100)),
    ("cloud_missing", sentinel[CLOUD].isna()),
]
cloud_missing_rows = []
for label, mask in cloud_missing_groups:
    subset = sentinel.loc[mask, usable_index_columns]
    cloud_missing_rows.append({
        "cloud_group": label,
        "n_rows": len(subset),
        "rows_all_usable_indices_missing": int(subset.isna().all(axis=1).sum()),
        "rows_any_usable_index_missing": int(subset.isna().any(axis=1).sum()),
        "rows_all_usable_indices_present": int(subset.notna().all(axis=1).sum()),
    })
cloud_missing_relation = pd.DataFrame(cloud_missing_rows)
write_csv(cloud_missing_relation, "sentinel_cloud_missingness_relationship.csv")


# -----------------------------------------------------------------------------
# H. Comparación TRAIN vs PREDICTION sin usar el rendimiento
# -----------------------------------------------------------------------------
sentinel_grouped = sentinel.merge(master[[ID, "CONJUNTO"]], on=ID, how="left", validate="many_to_one")
comparison_rows = []
for group, df_group in sentinel_grouped.groupby("CONJUNTO"):
    cov_group = coverage.loc[coverage["CONJUNTO"].eq(group)]
    for metric_name in ["n_observaciones", "n_fechas_unicas", "n_observaciones_abril_octubre_2025"]:
        comparison_rows.append({
            "section": "coverage", "group": group, "variable": metric_name,
            **describe_series(cov_group[metric_name]), "n": len(cov_group),
            "pct_missing": np.nan,
        })
    comparison_rows.append({
        "section": "cloud", "group": group, "variable": CLOUD,
        **describe_series(df_group[CLOUD]), "n": len(df_group),
        "pct_missing": 100 * df_group[CLOUD].isna().mean(),
    })
    for column in index_columns["column"]:
        numeric = pd.to_numeric(df_group[column], errors="coerce")
        comparison_rows.append({
            "section": "satellite_variable", "group": group, "variable": column,
            **describe_series(numeric), "n": len(numeric),
            "pct_missing": 100 * numeric.isna().mean(),
        })
train_prediction_comparison = pd.DataFrame(comparison_rows)
write_csv(train_prediction_comparison, "sentinel_train_prediction_comparison.csv")


# -----------------------------------------------------------------------------
# I. Visualizaciones mínimas
# -----------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 5))
sns.histplot(data=coverage, x="n_observaciones", hue="CONJUNTO", bins=15,
             element="step", common_norm=False, ax=ax)
ax.set(title="Observaciones Sentinel-2 por parcela", xlabel="Número de observaciones")
fig.tight_layout()
fig.savefig(FIGURE_DIR / "01_observaciones_por_parcela.png", dpi=180)
plt.close(fig)

year_long = coverage.melt(
    id_vars=[ID, "CONJUNTO"],
    value_vars=[f"n_observaciones_{year}" for year in YEARS],
    var_name="year", value_name="n_observaciones_anuales",
)
year_long["year"] = year_long["year"].str.extract(r"(\d{4})").astype(int)
fig, ax = plt.subplots(figsize=(10, 5))
sns.boxplot(data=year_long, x="year", y="n_observaciones_anuales", hue="CONJUNTO", ax=ax)
ax.set(title="Cobertura anual Sentinel-2", xlabel="Año", ylabel="Observaciones por parcela")
fig.tight_layout()
fig.savefig(FIGURE_DIR / "02_observaciones_por_anio.png", dpi=180)
plt.close(fig)

monthly = sentinel.dropna(subset=[ID, DATE]).assign(
    year_month=lambda x: x[DATE].dt.to_period("M").astype(str)
)
heat = pd.crosstab(monthly[ID], monthly["year_month"]).reindex(sorted(sentinel_ids))
fig, ax = plt.subplots(figsize=(18, 12))
sns.heatmap(heat, cmap="YlGnBu", cbar_kws={"label": "Observaciones"}, ax=ax)
ax.set(title="Cobertura mensual Sentinel-2", xlabel="Año-mes", ylabel="Parcela")
fig.tight_layout()
fig.savefig(FIGURE_DIR / "03_heatmap_cobertura_mensual.png", dpi=180)
plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
sns.histplot(data=gaps, x="gap_days", discrete=True, ax=axes[0])
sns.boxplot(data=gaps, x="year", y="gap_days", showfliers=False, ax=axes[1])
axes[0].set(title="Distribución de gaps", xlabel="Días")
axes[1].set(title="Gaps por año", xlabel="Año", ylabel="Días")
fig.tight_layout()
fig.savefig(FIGURE_DIR / "04_gaps_temporales.png", dpi=180)
plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
sns.histplot(data=sentinel, x=CLOUD, bins=30, ax=axes[0])
sns.boxplot(data=sentinel.assign(year=sentinel[DATE].dt.year), x="year", y=CLOUD,
            showfliers=False, ax=axes[1])
axes[0].set(title="Nubosidad global", xlabel="Porcentaje de nubosidad")
axes[1].set(title="Nubosidad por año", xlabel="Año", ylabel="Porcentaje")
fig.tight_layout()
fig.savefig(FIGURE_DIR / "05_nubosidad.png", dpi=180)
plt.close(fig)

fig, ax = plt.subplots(figsize=(12, max(7, 0.18 * len(missingness))))
missing_plot = missingness.sort_values("pct_missing", ascending=False)
sns.barplot(data=missing_plot, y="column", x="pct_missing", color="#4c78a8", ax=ax)
ax.set(title="Missingness por variable Sentinel-2", xlabel="Porcentaje faltante", ylabel="")
fig.tight_layout()
fig.savefig(FIGURE_DIR / "06_missingness_por_variable.png", dpi=180)
plt.close(fig)

coverage_order = coverage.sort_values("n_observaciones")
positions = np.linspace(0, len(coverage_order) - 1, 5).round().astype(int)
example_ids = coverage_order.iloc[positions][ID].drop_duplicates().tolist()
ndvi_examples = sentinel.loc[sentinel[ID].isin(example_ids), [ID, DATE, "ndvi_promedio", CLOUD]]
fig, axes = plt.subplots(len(example_ids), 1, figsize=(14, 3 * len(example_ids)),
                         sharex=True, squeeze=False)
for ax, parcel_id in zip(axes.flat, example_ids):
    part = ndvi_examples.loc[ndvi_examples[ID].eq(parcel_id)]
    ax.plot(part[DATE], part["ndvi_promedio"], marker=".", linewidth=0.8)
    ax.set_title(parcel_id)
    ax.set_ylabel("NDVI")
axes[-1, 0].set_xlabel("Fecha")
fig.suptitle("Series NDVI de parcelas elegidas por cuantiles de cobertura")
fig.tight_layout()
fig.savefig(FIGURE_DIR / "07_ejemplos_series_ndvi.png", dpi=180)
plt.close(fig)
pd.DataFrame({ID: example_ids}).to_csv(OUTPUT_DIR / "sentinel_ndvi_example_parcels.csv", index=False)


# -----------------------------------------------------------------------------
# J. Resumen Markdown y manifiesto
# -----------------------------------------------------------------------------
obs_min = int(coverage["n_observaciones"].min())
obs_max = int(coverage["n_observaciones"].max())
obs_median = float(coverage["n_observaciones"].median())
cycle_min = int(coverage["n_observaciones_abril_octubre_2025"].min())
cycle_max = int(coverage["n_observaciones_abril_octubre_2025"].max())
logical_violations = int(logical_audit["violations_min_mean_max_or_negative_std"].sum())
partial_quartets = int(logical_audit["rows_partially_available"].sum())
all_null_columns = missingness.loc[missingness["pct_missing"].eq(100), "column"].tolist()
cloud_global = sentinel[CLOUD]
cloud_cycle = sentinel.loc[sentinel[DATE].between(CYCLE_START, CYCLE_END), CLOUD]
cloud_100_all_missing = int(
    sentinel.loc[sentinel[CLOUD].eq(100), usable_index_columns].isna().all(axis=1).sum()
)
non_cloud_100_any_missing = int(
    sentinel.loc[sentinel[CLOUD].lt(100), usable_index_columns].isna().any(axis=1).sum()
)

summary_md = f"""# Auditoría Sentinel-2 — Familia 1, Etapa 1

Generado: {datetime.now().astimezone().isoformat(timespec='seconds')}

## Archivos encontrados

- Dataset Básico original: `{RAW_BASIC.relative_to(ROOT)}`
- Sentinel procesado existente: `{PROCESSED_SENTINEL.relative_to(ROOT)}`
- Maestro de parcelas, área y rendimiento: `{MASTER.relative_to(ROOT)}`
- Geometrías: `{PARCELS_SHP.relative_to(ROOT)}`

La auditoría usa como fuente canónica las filas `sensor == Sentinel-2` del Dataset Básico original. El CSV procesado se conserva sólo como contraste; no se sobrescribió ningún archivo fuente.

## Estructura real

- Dimensión Sentinel original: **{sentinel.shape[0]:,} filas × {sentinel.shape[1]} columnas**.
- Parcelas únicas: **{sentinel[ID].nunique()}**.
- Periodo: **{sentinel[DATE].min().date()} a {sentinel[DATE].max().date()}**.
- Índices base detectados: **{len(base_indices)}**.
- Estadísticos espaciales: `promedio`, `std`, `min` y `max`.
- Nubosidad: `{CLOUD}`, expresada como porcentaje según el nombre/documentación.
- Las unidades específicas de los índices no están declaradas en el CSV; deben consultarse en el diccionario de índices.

## Parcelas

- ENTRENAMIENTO: **{master['CONJUNTO'].eq('ENTRENAMIENTO').sum()}**.
- PREDICCION: **{master['CONJUNTO'].eq('PREDICCION').sum()}**.
- Parcelas maestras ausentes en Sentinel: **{len(missing_in_sentinel)}** ({', '.join(missing_in_sentinel) or 'ninguna'}).
- Parcelas Sentinel ausentes en maestro: **{len(extra_in_sentinel)}** ({', '.join(extra_in_sentinel) or 'ninguna'}).

## Cobertura temporal

- Observaciones por parcela: mínimo **{obs_min}**, mediana **{obs_median:.0f}**, máximo **{obs_max}**.
- Abril–octubre 2025: mínimo **{cycle_min}**, máximo **{cycle_max}** por parcela.
- La observación preliminar de aproximadamente 297–302 observaciones se **confirma con precisión como {obs_min}–{obs_max}** en el archivo original.
- La tabla completa por parcela y el resumen min/Q1/mediana/media/Q3/max/std se guardan por separado.

## Integridad

- Fechas inválidas: **{sentinel[DATE].isna().sum()}**.
- Filas implicadas en duplicados exactos: **{exact_duplicate_mask.sum()}**.
- Filas implicadas en claves parcela-fecha duplicadas: **{key_duplicate_mask.sum()}**.
- Máximo de registros para una clave parcela-fecha: **{key_counts['n_records'].max()}**.
- Retrocesos de fecha dentro de parcela en el orden original: **{order_violations}**.
- No se eliminó ningún registro.

## Índices y missingness

- Columnas completamente vacías en Sentinel original: **{len(all_null_columns)}**: {', '.join(all_null_columns) or 'ninguna'}.
- Filas parcialmente disponibles dentro de cuartetos mean/std/min/max, sumadas por índice: **{partial_quartets:,}**.
- Violaciones completas de `min <= promedio <= max` o `std >= 0`, sumadas por índice: **{logical_violations:,}**.
- Los valores marcados como raros usan sólo una regla descriptiva de 3×IQR; no fueron eliminados ni declarados erróneos.

## Nubosidad

- Media global: **{cloud_global.mean():.2f}%**; mediana: **{cloud_global.median():.2f}%**.
- Media abril–octubre 2025: **{cloud_cycle.mean():.2f}%**; mediana: **{cloud_cycle.median():.2f}%**.
- Filas con nubosidad 100%: **{sentinel[CLOUD].eq(100).sum():,}**; de ellas, **{cloud_100_all_missing:,}** tienen todos los índices utilizables ausentes.
- Filas con nubosidad menor que 100% y algún índice utilizable ausente: **{non_cloud_100_any_missing:,}**.
- No se aplicó ningún umbral. `sentinel_cloud_sensitivity.csv` cuantifica el costo de 10, 20, 30, 40, 50 y 70% para todo el periodo y para el ciclo 2025, global y por conjunto.

## TRAIN vs PREDICTION

La comparación se realizó sin usar el valor del rendimiento. Se compararon cobertura, nubosidad, missingness y rangos de todos los índices. Los resultados están en `sentinel_train_prediction_comparison.csv`; cualquier diferencia debe evaluarse como posible cambio de distribución antes del modelado, no como criterio automático de exclusión.

## Problemas y discrepancias detectados

1. “Observaciones repetidas” no equivale necesariamente a duplicados: esta auditoría distingue múltiples fechas por parcela de claves parcela-fecha repetidas.
2. El Dataset Básico conserva columnas que pueden estar 100% vacías para Sentinel; el CSV procesado tiene {processed.shape[1]} columnas frente a {sentinel.shape[1]} del original.
3. Nubosidad está concentrada en valores extremos, por lo que no debe asumirse que funciona como una variable continua ordinaria.
4. Las unidades y rangos físicos válidos de cada índice no están codificados en el CSV.

## Decisiones pendientes

1. Definir el umbral de nubosidad mediante sensibilidad de cobertura y validación posterior; no fijarlo por intuición.
2. Decidir si una fila con nubosidad alta pero índices presentes se conserva, se marca o se excluye.
3. Confirmar con el diccionario los rangos físicos y unidades antes de clasificar extremos como errores.
4. Definir el corte temporal de predicción dentro de abril–octubre de 2025.
5. Elegir una estrategia de representación de missingness antes de construir features.

## Recomendaciones para la etapa siguiente

- Mantener una fila por parcela-fecha durante la construcción de series.
- Conservar nubosidad y flags de disponibilidad junto a cada observación.
- Calcular features individuales sin target antes del CV; ajustar imputación, selección supervisada y escalamiento dentro de cada fold.
- Reutilizar exactamente los mismos splits persistidos para las tres familias.
- No mezclar todavía Sentinel con otros sensores hasta definir alineación y sesgos.
"""
(OUTPUT_DIR / "sentinel_audit_summary.md").write_text(summary_md, encoding="utf-8")

manifest = {
    "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    "stage": "family_1_stage_1_sentinel_audit",
    "inputs": [str(path.relative_to(ROOT)) for path in [RAW_BASIC, PROCESSED_SENTINEL, MASTER, PARCELS_SHP]],
    "rows_sentinel": len(sentinel),
    "parcels_sentinel": int(sentinel[ID].nunique()),
    "source_files_modified": False,
    "cloud_threshold_applied": False,
    "interpolation_applied": False,
    "target_used_for_analysis": False,
    "warnings": [
        "Physical ranges and units require the satellite index dictionary.",
        "Rare-value flags are descriptive 3-IQR flags, not automatic outliers.",
    ],
}
(OUTPUT_DIR / "audit_manifest.json").write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
)

print(summary_md)
print(f"\nOutputs guardados en: {OUTPUT_DIR}")
