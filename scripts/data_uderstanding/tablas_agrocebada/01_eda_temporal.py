#%%
"""EDA inicial de las tablas maestras de AgroCebada.

El script solo lee los CSV procesados, trabaja con copias en memoria y guarda
tablas y figuras en outputs/eda/01_tablas_maestras/01_eda_temporal/.
"""

# %% Librerias y configuracion
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


DATA_DIR = Path("data/processed/01_tablas_maestras")
OUTPUT_DIR = Path("outputs/eda/01_tablas_maestras/01_eda_temporal")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ID = "ID_POLIGONO"
DATE = "fecha_captura"
KEY = [ID, DATE]
SENSOR_COLORS = {
    "Sentinel-2": "#2ca02c",
    "Landsat": "#1f77b4",
    "Planet": "#d62728",
}

sns.set_theme(style="whitegrid")


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Crea una copia, normaliza faltantes de texto y convierte la fecha."""
    result = df.copy()
    text_cols = result.select_dtypes(include=["object", "string"]).columns
    result[text_cols] = result[text_cols].replace(r"^\s*$", pd.NA, regex=True)
    result[DATE] = pd.to_datetime(result[DATE], format="mixed", dayfirst=True,
                                  errors="coerce")
    return result


# %% Entrada: tres dataframes ya procesados y separados
READ_OPTIONS = {"na_values": ["", " ", "NA", "N/A", "null", "NULL"]}
sentinel = prepare(pd.read_csv(DATA_DIR / "sentinel.csv", **READ_OPTIONS))
landsat = prepare(pd.read_csv(DATA_DIR / "landsat.csv", **READ_OPTIONS))
planet = prepare(pd.read_csv(DATA_DIR / "planet.csv", **READ_OPTIONS))
datasets = {"Sentinel-2": sentinel, "Landsat": landsat, "Planet": planet}


# %% 1. Resumen estructural
summary_rows = []
missing_tables = []

for sensor, df in datasets.items():
    valid_dates = df[DATE].dropna()
    summary_rows.append(
        {
            "sensor": sensor,
            "filas": len(df),
            "columnas": df.shape[1],
            "parcelas_unicas": df[ID].nunique(dropna=True),
            "fechas_unicas": valid_dates.nunique(),
            "fecha_inicial": valid_dates.min(),
            "fecha_final": valid_dates.max(),
            "duplicados_ID_fecha": df.duplicated(KEY, keep=False).sum(),
            "claves_ID_fecha_duplicadas": df.loc[
                df.duplicated(KEY, keep=False), KEY
            ].drop_duplicates().shape[0],
        }
    )
    missing = df.isna().sum().rename("n_missing").to_frame()
    missing["porcentaje_missing"] = 100 * missing["n_missing"] / len(df)
    missing.insert(0, "variable", missing.index)
    missing.insert(0, "sensor", sensor)
    missing_tables.append(missing.reset_index(drop=True))

structural_summary = pd.DataFrame(summary_rows)
missing_summary = pd.concat(missing_tables, ignore_index=True)
structural_summary.to_csv(OUTPUT_DIR / "01_resumen_estructural.csv", index=False)
missing_summary.to_csv(OUTPUT_DIR / "02_missing_values.csv", index=False)
print("\nRESUMEN ESTRUCTURAL\n", structural_summary.to_string(index=False))


# %% 2. Cobertura temporal
temporal_tables = []
gap_tables = []

for sensor, df in datasets.items():
    # Una observacion es una combinacion unica parcela-fecha.
    observations = df.dropna(subset=KEY).drop_duplicates(KEY)
    temporal = (
        observations.assign(
            anio=observations[DATE].dt.year,
            mes=observations[DATE].dt.month,
        )
        .groupby(["anio", "mes"], as_index=False)
        .size()
        .rename(columns={"size": "n_observaciones"})
    )
    temporal.insert(0, "sensor", sensor)
    temporal_tables.append(temporal)

    gaps = observations.sort_values(KEY).copy()
    gaps["dias_entre_observaciones"] = gaps.groupby(ID)[DATE].diff().dt.days
    gaps = gaps.dropna(subset=["dias_entre_observaciones"])
    gaps["sensor"] = sensor
    gap_tables.append(gaps[["sensor", ID, DATE, "dias_entre_observaciones"]])

temporal_coverage = pd.concat(temporal_tables, ignore_index=True)
observation_gaps = pd.concat(gap_tables, ignore_index=True)
temporal_coverage.to_csv(OUTPUT_DIR / "03_observaciones_anio_mes.csv", index=False)
observation_gaps.to_csv(OUTPUT_DIR / "04_intervalos_dias.csv", index=False)

# Timeline: cada punto representa una fecha disponible, no una fila/parcela.
fig, ax = plt.subplots(figsize=(14, 4))
for y, (sensor, df) in enumerate(datasets.items()):
    dates = np.sort(df[DATE].dropna().unique())
    ax.scatter(dates, np.full(len(dates), y), s=11, alpha=0.65,
               color=SENSOR_COLORS[sensor], label=sensor)
ax.set_yticks(range(len(datasets)), labels=list(datasets))
ax.set(title="Fechas de captura disponibles por sensor", xlabel="Fecha", ylabel="")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "01_timeline_sensores.png", dpi=180)
plt.close(fig)

fig, ax = plt.subplots(figsize=(11, 5))
sns.histplot(data=observation_gaps, x="dias_entre_observaciones", hue="sensor",
             bins=50, element="step", stat="density", common_norm=False, ax=ax)
ax.set(xlabel="Dias entre observaciones consecutivas", title="Periodicidad por parcela")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "02_intervalos_observaciones.png", dpi=180)
plt.close(fig)


# %% 3. Cobertura por parcela
parcel_coverage = pd.concat(
    [
        df.dropna(subset=KEY).drop_duplicates(KEY).groupby(ID).size()
        .rename("n_observaciones").reset_index().assign(sensor=sensor)
        for sensor, df in datasets.items()
    ],
    ignore_index=True,
)
parcel_coverage.to_csv(OUTPUT_DIR / "05_cobertura_por_parcela.csv", index=False)

fig, axes = plt.subplots(1, 3, figsize=(16, 4), sharey=True)
for ax, sensor in zip(axes, datasets):
    values = parcel_coverage.loc[parcel_coverage["sensor"].eq(sensor)]
    sns.histplot(data=values, x="n_observaciones", bins=30,
                 color=SENSOR_COLORS[sensor], ax=ax)
    ax.set_title(sensor)
    ax.set_xlabel("Observaciones por parcela")
axes[0].set_ylabel("Numero de parcelas")
fig.suptitle("Cobertura de observaciones por parcela y sensor")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "03_cobertura_parcelas.png", dpi=180)
plt.close(fig)

for number, (sensor, df) in enumerate(datasets.items(), start=4):
    observations = df.dropna(subset=KEY).drop_duplicates(KEY).copy()
    observations["anio_mes"] = observations[DATE].dt.to_period("M").astype(str)
    heat = pd.crosstab(observations[ID], observations["anio_mes"])
    heat = heat.loc[heat.sum(axis=1).sort_values(ascending=False).index]
    # Limite visual: la tabla completa se conserva en CSV.
    heat.to_csv(OUTPUT_DIR / f"06_heatmap_{sensor.lower().replace('-', '_')}_datos.csv")
    shown = heat.head(100)
    fig, ax = plt.subplots(figsize=(max(12, 0.35 * len(shown.columns)), 10))
    sns.heatmap(shown, cmap="YlGnBu", cbar_kws={"label": "Observaciones"}, ax=ax)
    ax.set(title=f"Cobertura parcela x mes: {sensor} (100 con mayor cobertura)",
           xlabel="Ano-mes", ylabel="ID_POLIGONO")
    fig.tight_layout()
    filename = sensor.lower().replace("-", "_")
    fig.savefig(OUTPUT_DIR / f"{number:02d}_heatmap_{filename}.png", dpi=180)
    plt.close(fig)


# %% 4. Calidad: nubosidad
cloud = pd.concat(
    [df[[ID, DATE, "porcentaje_nubosidad"]].assign(sensor=sensor)
     for sensor, df in datasets.items() if "porcentaje_nubosidad" in df],
    ignore_index=True,
)

fig, ax = plt.subplots(figsize=(10, 5))
sns.histplot(data=cloud, x="porcentaje_nubosidad", hue="sensor", bins=30,
             element="step", stat="density", common_norm=False, ax=ax)
ax.set(title="Distribucion de nubosidad", xlabel="Porcentaje de nubosidad")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "07_distribucion_nubosidad.png", dpi=180)
plt.close(fig)

cloud["mes"] = cloud[DATE].dt.month
fig, ax = plt.subplots(figsize=(11, 5))
sns.boxplot(data=cloud, x="mes", y="porcentaje_nubosidad", hue="sensor",
            showfliers=False, ax=ax)
ax.set(title="Nubosidad por mes", xlabel="Mes", ylabel="Porcentaje de nubosidad")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "08_nubosidad_por_mes.png", dpi=180)
plt.close(fig)

# Proxy descriptivo: cobertura mensual frente a nubosidad observada. La
# nubosidad de capturas completamente ausentes no puede observarse en la tabla.
quality_monthly = (
    cloud.dropna(subset=[DATE])
    .assign(anio_mes=lambda x: x[DATE].dt.to_period("M").astype(str))
    .groupby(["sensor", "anio_mes"], as_index=False)
    .agg(observaciones=(ID, "size"), nubosidad_mediana=("porcentaje_nubosidad", "median"))
)
quality_monthly.to_csv(OUTPUT_DIR / "07_cobertura_nubosidad_mensual.csv", index=False)
fig, ax = plt.subplots(figsize=(8, 5))
sns.scatterplot(data=quality_monthly, x="nubosidad_mediana", y="observaciones",
                hue="sensor", palette=SENSOR_COLORS, ax=ax)
ax.set(title="Cobertura mensual vs. nubosidad observada",
       xlabel="Nubosidad mediana", ylabel="Numero de observaciones")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "09_cobertura_vs_nubosidad.png", dpi=180)
plt.close(fig)


# %% 5. Trayectorias temporales de parcelas representativas
# Se eligen parcelas comunes y los cuantiles 25, 50 y 75 de cobertura total.
common_ids = set.intersection(*(set(df[ID].dropna().unique()) for df in datasets.values()))
total_coverage = (
    parcel_coverage.loc[parcel_coverage[ID].isin(common_ids)]
    .groupby(ID)["n_observaciones"].sum().sort_values()
)
representative_ids = []
if not total_coverage.empty:
    for q in (0.25, 0.50, 0.75):
        target = total_coverage.quantile(q)
        representative_ids.append((total_coverage - target).abs().idxmin())
representative_ids = list(dict.fromkeys(representative_ids))
pd.Series(representative_ids, name=ID).to_csv(
    OUTPUT_DIR / "08_parcelas_representativas.csv", index=False
)

trajectory_vars = [
    "ndvi_promedio", "lai_promedio", "ndwi_promedio", "endwi_promedio",
    "msi_promedio", "emsi_promedio", "nddi_promedio", "enddi_promedio",
]
for plot_number, variable in enumerate(trajectory_vars, start=10):
    frames = []
    for sensor, df in datasets.items():
        if variable in df.columns:
            selected = df.loc[df[ID].isin(representative_ids), KEY + [variable]].copy()
            selected["sensor"] = sensor
            frames.append(selected)
    if not frames:
        continue
    plot_data = pd.concat(frames, ignore_index=True)
    fig, axes = plt.subplots(max(1, len(representative_ids)), 1,
                             figsize=(13, 3.5 * max(1, len(representative_ids))),
                             sharex=True, squeeze=False)
    for ax, parcel_id in zip(axes.flat, representative_ids):
        sns.lineplot(data=plot_data.loc[plot_data[ID].eq(parcel_id)], x=DATE,
                     y=variable, hue="sensor", style="sensor", marker="o", ax=ax)
        ax.set_title(f"Parcela {parcel_id}")
    fig.suptitle(f"Trayectoria temporal: {variable}")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / f"{plot_number:02d}_trayectoria_{variable}.png", dpi=180)
    plt.close(fig)


# %% 6. Solapamiento exacto entre sensores
def unique_keys(df: pd.DataFrame) -> pd.DataFrame:
    return df[KEY].dropna().drop_duplicates()


pairs = [("Planet", "Sentinel-2"), ("Planet", "Landsat"),
         ("Sentinel-2", "Landsat")]
overlap_rows = []
for left_name, right_name in pairs:
    matches = unique_keys(datasets[left_name]).merge(
        unique_keys(datasets[right_name]), on=KEY, how="inner"
    )
    overlap_rows.append(
        {"sensor_1": left_name, "sensor_2": right_name,
         "coincidencias_exactas": len(matches)}
    )
    pair_name = f"{left_name}_{right_name}".lower().replace("-", "_")
    matches.to_csv(OUTPUT_DIR / f"09_coincidencias_{pair_name}.csv", index=False)

exact_overlap = pd.DataFrame(overlap_rows)
exact_overlap.to_csv(OUTPUT_DIR / "10_resumen_solapamiento_exacto.csv", index=False)
print("\nSOLAPAMIENTO EXACTO\n", exact_overlap.to_string(index=False))


def matches_within_window(left: pd.DataFrame, right: pd.DataFrame,
                          days: int) -> pd.DataFrame:
    """Prepara coincidencias por parcela dentro de +/- days; no se ejecuta aun."""
    left_keys = unique_keys(left).rename(columns={DATE: "fecha_1"})
    right_keys = unique_keys(right).rename(columns={DATE: "fecha_2"})
    candidates = left_keys.merge(right_keys, on=ID, how="inner")
    candidates["diferencia_dias"] = (
        candidates["fecha_1"] - candidates["fecha_2"]
    ).abs().dt.days
    return candidates.loc[candidates["diferencia_dias"].le(days)].copy()


WINDOWS_DAYS = [1, 3, 5, 7]  # Para el analisis posterior.


# %% 7. Comparacion preliminar Planet vs Sentinel en claves exactas
comparison_vars = ["ndvi_promedio", "evi_promedio", "lai_promedio"]
available_vars = [v for v in comparison_vars if v in planet and v in sentinel]

# El promedio evita una union muchos-a-muchos si hubiera claves duplicadas.
planet_exact = planet.groupby(KEY, as_index=False)[available_vars].mean()
sentinel_exact = sentinel.groupby(KEY, as_index=False)[available_vars].mean()
planet_sentinel = planet_exact.merge(
    sentinel_exact, on=KEY, how="inner", suffixes=("_planet", "_sentinel")
)
planet_sentinel.to_csv(OUTPUT_DIR / "11_planet_sentinel_coincidencias.csv", index=False)

for number, variable in enumerate(available_vars, start=18):
    fig, ax = plt.subplots(figsize=(6, 6))
    sns.scatterplot(data=planet_sentinel, x=f"{variable}_planet",
                    y=f"{variable}_sentinel", alpha=0.35, s=25, ax=ax)
    ax.set(title=f"Planet vs Sentinel-2: {variable}\n(misma parcela y fecha)",
           xlabel=f"Planet: {variable}", ylabel=f"Sentinel-2: {variable}")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / f"{number:02d}_planet_sentinel_{variable}.png", dpi=180)
    plt.close(fig)

print(f"\nEDA terminado. Resultados guardados en: {OUTPUT_DIR.resolve()}")
