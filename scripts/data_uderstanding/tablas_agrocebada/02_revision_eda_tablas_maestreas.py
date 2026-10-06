"""02 - Revision dirigida del EDA de tablas maestras.

Profundiza en hallazgos del EDA inicial:
1. Completitud y comportamiento de porcentaje_nubosidad.
2. Nubosidad por mes comparando sensores únicamente en 2025.
3. Proporción de observaciones con nubosidad 0 / intermedia / 100.
4. Cobertura mensual real de la variable nubosidad.
5. Heterogeneidad de cobertura Landsat entre parcelas.
6. Comparación Planet vs Sentinel en mismas parcelas y fechas.
7. Revisión de saltos temporales fuertes de NDVI Sentinel.

Los resultados se guardan en:
outputs/eda/01_tablas_maestras/02_revision_dirigida/
"""

# %% Librerías
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# %% Configuración
DATA_DIR = Path("data/processed/01_tablas_maestras")
OUTPUT_DIR = Path("outputs/eda/01_tablas_maestras/02_revision_dirigida")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ID = "ID_POLIGONO"
DATE = "fecha_captura"
CLOUD = "porcentaje_nubosidad"

sns.set_theme(style="whitegrid")


# %% Leer datos procesados
sentinel = pd.read_csv(DATA_DIR / "sentinel.csv")
landsat = pd.read_csv(DATA_DIR / "landsat.csv")
planet = pd.read_csv(DATA_DIR / "planet.csv")

for df in [sentinel, landsat, planet]:
    df[DATE] = pd.to_datetime(df[DATE], errors="coerce")

datasets = {
    "Sentinel-2": sentinel,
    "Landsat": landsat,
    "Planet": planet,
}


# =========================================================
# 1. COMPLETITUD Y DISTRIBUCIÓN DE NUBOSIDAD
# =========================================================

cloud_summary = []

for sensor, df in datasets.items():

    s = df[CLOUD]

    n_total = len(df)
    n_valid = s.notna().sum()
    n_missing = s.isna().sum()

    n_zero = s.eq(0).sum()
    n_hundred = s.eq(100).sum()
    n_intermediate = ((s > 0) & (s < 100)).sum()

    cloud_summary.append({
        "sensor": sensor,
        "n_total": n_total,
        "n_con_nubosidad": n_valid,
        "n_missing": n_missing,
        "pct_con_nubosidad": 100 * n_valid / n_total,
        "n_cloud_0": n_zero,
        "pct_cloud_0": 100 * n_zero / n_valid if n_valid else np.nan,
        "n_cloud_intermedio": n_intermediate,
        "pct_cloud_intermedio": (
            100 * n_intermediate / n_valid if n_valid else np.nan
        ),
        "n_cloud_100": n_hundred,
        "pct_cloud_100": 100 * n_hundred / n_valid if n_valid else np.nan,
        "media": s.mean(),
        "mediana": s.median(),
    })

cloud_summary = pd.DataFrame(cloud_summary)

cloud_summary.to_csv(
    OUTPUT_DIR / "01_resumen_nubosidad.csv",
    index=False
)

print("\nRESUMEN DE NUBOSIDAD")
print(cloud_summary.to_string(index=False))


# Valores de nubosidad más frecuentes
cloud_values = []

for sensor, df in datasets.items():

    counts = (
        df[CLOUD]
        .value_counts(dropna=False)
        .rename_axis("nubosidad")
        .reset_index(name="frecuencia")
    )

    counts.insert(0, "sensor", sensor)
    cloud_values.append(counts)

cloud_values = pd.concat(cloud_values, ignore_index=True)

cloud_values.to_csv(
    OUTPUT_DIR / "02_frecuencias_valores_nubosidad.csv",
    index=False
)


# =========================================================
# 2. NUBOSIDAD POR MES: COMPARACIÓN JUSTA SOLO EN 2025
# =========================================================

cloud_2025 = pd.concat(
    [
        df.loc[
            df[DATE].dt.year.eq(2025),
            [ID, DATE, CLOUD]
        ].assign(sensor=sensor)
        for sensor, df in datasets.items()
    ],
    ignore_index=True
)

cloud_2025["mes"] = cloud_2025[DATE].dt.month


fig, ax = plt.subplots(figsize=(14, 6))

sns.boxplot(
    data=cloud_2025,
    x="mes",
    y=CLOUD,
    hue="sensor",
    showfliers=False,
    ax=ax
)

ax.set(
    title="Nubosidad por mes - comparación entre sensores en 2025",
    xlabel="Mes",
    ylabel="Porcentaje de nubosidad"
)

fig.tight_layout()
fig.savefig(
    OUTPUT_DIR / "01_nubosidad_por_mes_2025.png",
    dpi=180
)

plt.close(fig)


# =========================================================
# 3. NUBOSIDAD COMO 0 / INTERMEDIA / 100
# =========================================================

def cloud_category(x):

    if pd.isna(x):
        return "Missing"

    if x == 0:
        return "0"

    if x == 100:
        return "100"

    return "Intermedia"


cloud_2025["categoria_nubosidad"] = (
    cloud_2025[CLOUD]
    .apply(cloud_category)
)


cloud_categories = (
    cloud_2025
    .groupby(
        ["sensor", "mes", "categoria_nubosidad"],
        dropna=False
    )
    .size()
    .rename("n")
    .reset_index()
)

cloud_categories["porcentaje"] = (
    cloud_categories["n"]
    /
    cloud_categories.groupby(
        ["sensor", "mes"]
    )["n"].transform("sum")
    * 100
)

cloud_categories.to_csv(
    OUTPUT_DIR / "03_nubosidad_categorias_mes_2025.csv",
    index=False
)


# Gráfica separada por sensor
for sensor in datasets:

    plot_data = cloud_categories[
        cloud_categories["sensor"].eq(sensor)
    ]

    pivot = (
        plot_data
        .pivot(
            index="mes",
            columns="categoria_nubosidad",
            values="porcentaje"
        )
        .fillna(0)
    )

    # Orden consistente
    order = [
        c for c in ["0", "Intermedia", "100", "Missing"]
        if c in pivot.columns
    ]

    pivot = pivot[order]

    ax = pivot.plot(
        kind="bar",
        stacked=True,
        figsize=(11, 5)
    )

    ax.set(
        title=f"Composición de nubosidad por mes - {sensor} - 2025",
        xlabel="Mes",
        ylabel="Porcentaje de observaciones"
    )

    ax.legend(title="Nubosidad")
    plt.tight_layout()

    name = sensor.lower().replace("-", "_")

    plt.savefig(
        OUTPUT_DIR / f"02_nubosidad_categorias_{name}_2025.png",
        dpi=180
    )

    plt.close()


# =========================================================
# 4. COBERTURA MENSUAL REAL DE LA VARIABLE NUBOSIDAD
# =========================================================

monthly_quality = []

for sensor, df in datasets.items():

    temp = df.copy()

    temp["anio_mes"] = (
        temp[DATE]
        .dt.to_period("M")
        .astype(str)
    )

    summary = (
        temp
        .groupby("anio_mes", as_index=False)
        .agg(
            n_filas=(ID, "size"),
            n_parcelas=(ID, "nunique"),
            n_fechas=(DATE, "nunique"),
            n_con_nubosidad=(CLOUD, "count"),
            nubosidad_mediana=(CLOUD, "median"),
            nubosidad_media=(CLOUD, "mean"),
        )
    )

    summary["pct_con_nubosidad"] = (
        100
        * summary["n_con_nubosidad"]
        / summary["n_filas"]
    )

    summary.insert(0, "sensor", sensor)

    monthly_quality.append(summary)


monthly_quality = pd.concat(
    monthly_quality,
    ignore_index=True
)

monthly_quality.to_csv(
    OUTPUT_DIR / "04_calidad_nubosidad_mensual.csv",
    index=False
)


# Cobertura de nubosidad vs nubosidad mediana
fig, ax = plt.subplots(figsize=(10, 6))

sns.scatterplot(
    data=monthly_quality,
    x="nubosidad_mediana",
    y="pct_con_nubosidad",
    hue="sensor",
    s=70,
    ax=ax
)

ax.set(
    title="Completitud de nubosidad vs. nubosidad mediana mensual",
    xlabel="Nubosidad mediana",
    ylabel="% de filas con dato de nubosidad"
)

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "03_completitud_vs_nubosidad.png",
    dpi=180
)

plt.close(fig)


# =========================================================
# 5. HETEROGENEIDAD DE COBERTURA LANDSAT
# =========================================================

landsat_coverage = (
    landsat
    .dropna(subset=[ID, DATE])
    .drop_duplicates([ID, DATE])
    .groupby(ID)
    .agg(
        n_observaciones=(DATE, "size"),
        fecha_inicial=(DATE, "min"),
        fecha_final=(DATE, "max")
    )
    .reset_index()
    .sort_values("n_observaciones")
)

landsat_coverage.to_csv(
    OUTPUT_DIR / "05_cobertura_landsat_por_parcela.csv",
    index=False
)

print("\nCOBERTURA LANDSAT")
print(landsat_coverage["n_observaciones"].describe())


fig, ax = plt.subplots(figsize=(13, 5))

ax.plot(
    np.arange(len(landsat_coverage)),
    landsat_coverage["n_observaciones"],
    marker=".",
    linestyle="none"
)

ax.axhline(
    landsat_coverage["n_observaciones"].median(),
    linestyle="--"
)

ax.set(
    title="Cobertura Landsat por parcela ordenada",
    xlabel="Parcelas ordenadas por cobertura",
    ylabel="Número de observaciones"
)

fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "04_cobertura_landsat_ordenada.png",
    dpi=180
)

plt.close(fig)


# =========================================================
# 6. PLANET VS SENTINEL - MISMA PARCELA Y FECHA
# =========================================================

comparison_vars = [
    "ndvi_promedio",
    "evi_promedio",
    "lai_promedio"
]

comparison_rows = []


for variable in comparison_vars:

    if variable not in sentinel.columns:
        continue

    if variable not in planet.columns:
        continue

    s = (
        sentinel[
            [ID, DATE, variable]
        ]
        .dropna()
        .groupby(
            [ID, DATE],
            as_index=False
        )[variable]
        .mean()
    )

    p = (
        planet[
            [ID, DATE, variable]
        ]
        .dropna()
        .groupby(
            [ID, DATE],
            as_index=False
        )[variable]
        .mean()
    )

    matched = p.merge(
        s,
        on=[ID, DATE],
        how="inner",
        suffixes=("_planet", "_sentinel")
    )

    x = matched[f"{variable}_planet"]
    y = matched[f"{variable}_sentinel"]

    if len(matched) == 0:
        continue

    correlation = x.corr(y)
    mean_difference = (x - y).mean()
    mae = (x - y).abs().mean()

    comparison_rows.append({
        "variable": variable,
        "n_coincidencias": len(matched),
        "correlacion": correlation,
        "diferencia_media_planet_menos_sentinel": mean_difference,
        "MAE_entre_sensores": mae
    })

    # Scatter
    fig, ax = plt.subplots(figsize=(6, 6))

    sns.scatterplot(
        x=x,
        y=y,
        alpha=0.3,
        s=25,
        ax=ax
    )

    low = min(x.min(), y.min())
    high = max(x.max(), y.max())

    ax.plot(
        [low, high],
        [low, high],
        linestyle="--"
    )

    ax.set(
        title=(
            f"Planet vs Sentinel-2: {variable}\n"
            "misma parcela y fecha"
        ),
        xlabel=f"Planet - {variable}",
        ylabel=f"Sentinel-2 - {variable}"
    )

    fig.tight_layout()

    fig.savefig(
        OUTPUT_DIR / f"05_comparacion_planet_sentinel_{variable}.png",
        dpi=180
    )

    plt.close(fig)


sensor_comparison = pd.DataFrame(comparison_rows)

sensor_comparison.to_csv(
    OUTPUT_DIR / "06_resumen_planet_vs_sentinel.csv",
    index=False
)

print("\nPLANET VS SENTINEL")
print(sensor_comparison.to_string(index=False))


# =========================================================
# 7. SALTOS TEMPORALES DE NDVI SENTINEL
# =========================================================

if "ndvi_promedio" in sentinel.columns:

    ndvi = (
        sentinel[
            [ID, DATE, "ndvi_promedio", CLOUD]
        ]
        .dropna(
            subset=[ID, DATE, "ndvi_promedio"]
        )
        .sort_values(
            [ID, DATE]
        )
        .copy()
    )

    ndvi["ndvi_anterior"] = (
        ndvi
        .groupby(ID)["ndvi_promedio"]
        .shift(1)
    )

    ndvi["cambio_ndvi"] = (
        ndvi["ndvi_promedio"]
        - ndvi["ndvi_anterior"]
    )

    ndvi["cambio_abs_ndvi"] = (
        ndvi["cambio_ndvi"].abs()
    )

    # Cuantil 99: observaciones con saltos más extremos
    threshold = (
        ndvi["cambio_abs_ndvi"]
        .quantile(0.99)
    )

    extreme_changes = (
        ndvi[
            ndvi["cambio_abs_ndvi"] >= threshold
        ]
        .sort_values(
            "cambio_abs_ndvi",
            ascending=False
        )
    )

    extreme_changes.to_csv(
        OUTPUT_DIR / "07_saltos_extremos_ndvi_sentinel.csv",
        index=False
    )

    print(
        "\nUmbral percentil 99 de cambio absoluto NDVI:",
        threshold
    )


    # Relación entre magnitud del salto y nubosidad
    fig, ax = plt.subplots(figsize=(9, 5))

    sns.scatterplot(
        data=ndvi,
        x=CLOUD,
        y="cambio_abs_ndvi",
        alpha=0.15,
        s=20,
        ax=ax
    )

    ax.set(
        title="Cambios abruptos de NDVI vs nubosidad - Sentinel-2",
        xlabel="Porcentaje de nubosidad",
        ylabel="Cambio absoluto de NDVI respecto a captura anterior"
    )

    fig.tight_layout()

    fig.savefig(
        OUTPUT_DIR / "06_saltos_ndvi_vs_nubosidad.png",
        dpi=180
    )

    plt.close(fig)


print(
    "\nRevisión 02 terminada. Resultados guardados en:",
    OUTPUT_DIR.resolve()
)
