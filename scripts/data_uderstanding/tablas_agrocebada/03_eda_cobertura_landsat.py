"""EDA 03: cobertura Landsat por parcela y relación con el rendimiento 2025.

No modifica los datos fuente. Los grupos de cobertura son descriptivos y se
definen con cuartiles de la proporción de fechas Landsat con VI6T válido.
"""

# %% Librerías y rutas
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


DATA_DIR = Path("data/processed/01_tablas_maestras")
TARGET_FILE = Path(
    "data/original/01_tablas_maestras/ID_area_rendimiento_70_30_Reto_AgroCebada.csv"
)
SHAPEFILE = Path("data/original/02_conjunto_70_30/Parcelas_Reto_AGC_CONJUNTO.shp")
OUTPUT_DIR = Path("outputs/eda/01_tablas_maestras/03_cobertura_landsat")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ID = "ID_POLIGONO"
DATE = "fecha_captura"
VI6T = "vi6t_promedio"
CLOUD = "porcentaje_nubosidad"
GROUP_ORDER = ["Baja", "Media", "Alta"]
GROUP_COLORS = {"Baja": "#d95f02", "Media": "#7570b3", "Alta": "#1b9e77"}

sns.set_theme(style="whitegrid")


# %% Lectura
landsat = pd.read_csv(DATA_DIR / "landsat.csv")
landsat[DATE] = pd.to_datetime(landsat[DATE], errors="coerce")
target = pd.read_csv(TARGET_FILE).drop(columns=["Unnamed: 4"], errors="ignore")

valid = landsat.dropna(subset=[ID, DATE]).drop_duplicates([ID, DATE]).copy()
all_dates = pd.Index(valid[DATE].unique()).sort_values()
cycle_mask = (valid[DATE] >= "2025-04-01") & (valid[DATE] <= "2025-10-31")
cycle = valid.loc[cycle_mask].copy()
cycle_dates = pd.Index(cycle[DATE].unique()).sort_values()


# %% Métricas de cobertura histórica y del ciclo objetivo
def coverage_metrics(df: pd.DataFrame, denominator: int, suffix: str) -> pd.DataFrame:
    ordered = df.sort_values([ID, DATE]).copy()
    ordered["gap_days"] = ordered.groupby(ID)[DATE].diff().dt.days
    return (
        ordered.groupby(ID)
        .agg(
            **{
                f"n_observaciones_{suffix}": (DATE, "size"),
                f"n_vi6t_validos_{suffix}": (VI6T, "count"),
                f"n_nubosidad_valida_{suffix}": (CLOUD, "count"),
                f"gap_mediano_dias_{suffix}": ("gap_days", "median"),
                f"gap_maximo_dias_{suffix}": ("gap_days", "max"),
                f"fecha_inicial_{suffix}": (DATE, "min"),
                f"fecha_final_{suffix}": (DATE, "max"),
            }
        )
        .assign(
            **{
                f"cobertura_relativa_{suffix}": lambda x: (
                    x[f"n_observaciones_{suffix}"] / denominator
                ),
                f"vi6t_valido_relativo_{suffix}": lambda x: (
                    x[f"n_vi6t_validos_{suffix}"] / denominator
                ),
                f"pct_vi6t_valido_en_observadas_{suffix}": lambda x: (
                    100
                    * x[f"n_vi6t_validos_{suffix}"]
                    / x[f"n_observaciones_{suffix}"]
                ),
            }
        )
        .reset_index()
    )


historical = coverage_metrics(valid, len(all_dates), "historica")
cycle_2025 = coverage_metrics(cycle, len(cycle_dates), "ciclo_2025")
coverage = historical.merge(cycle_2025, on=ID, how="left").merge(target, on=ID, how="left")

# Grupo transparente: cuartiles de disponibilidad histórica de VI6T utilizable.
metric = "vi6t_valido_relativo_historica"
q25, q75 = coverage[metric].quantile([0.25, 0.75])
coverage["grupo_cobertura"] = pd.cut(
    coverage[metric],
    bins=[-np.inf, q25, q75, np.inf],
    labels=GROUP_ORDER,
    include_lowest=True,
).astype("string")

# Peso candidato, no definitivo: 1 para la parcela con mayor proporción válida.
coverage["peso_cobertura_candidato"] = coverage[metric] / coverage[metric].max()
coverage = coverage.sort_values(metric)
coverage.to_csv(OUTPUT_DIR / "01_metricas_cobertura_landsat.csv", index=False)

group_summary = (
    coverage.groupby("grupo_cobertura", observed=True)
    .agg(
        n_parcelas=(ID, "size"),
        observaciones_mediana=("n_observaciones_historica", "median"),
        vi6t_validos_mediana=("n_vi6t_validos_historica", "median"),
        cobertura_relativa_mediana=("cobertura_relativa_historica", "median"),
        vi6t_valido_relativo_mediana=(metric, "median"),
        gap_maximo_mediana=("gap_maximo_dias_historica", "median"),
        cobertura_ciclo_2025_mediana=("cobertura_relativa_ciclo_2025", "median"),
        area_mediana_ha=("AREA_HA", "median"),
        rendimiento_mediano=("RENDIMIENTO_T_HA", "median"),
        rendimiento_medio=("RENDIMIENTO_T_HA", "mean"),
    )
    .reindex(GROUP_ORDER)
    .reset_index()
)
group_summary.to_csv(OUTPUT_DIR / "02_resumen_grupos_cobertura.csv", index=False)

set_group = pd.crosstab(coverage["grupo_cobertura"], coverage["CONJUNTO"])
set_group.to_csv(OUTPUT_DIR / "03_grupo_cobertura_por_conjunto.csv")

correlations = coverage[
    ["n_observaciones_historica", metric, "AREA_HA", "RENDIMIENTO_T_HA"]
].corr(method="spearman")
correlations.to_csv(OUTPUT_DIR / "04_correlaciones_spearman.csv")


# %% 1. Parcelas ordenadas y grupos
fig, ax = plt.subplots(figsize=(14, 6))
plot_ordered = coverage.reset_index(drop=True)
for group in GROUP_ORDER:
    part = plot_ordered.loc[plot_ordered["grupo_cobertura"].eq(group)]
    ax.scatter(part.index, part[metric], s=28, color=GROUP_COLORS[group], label=group)
ax.axhline(q25, color="grey", linestyle="--", linewidth=1)
ax.axhline(q75, color="grey", linestyle="--", linewidth=1)
ax.set(
    title="Disponibilidad histórica de VI6T Landsat por parcela",
    xlabel="Parcelas ordenadas por cobertura válida",
    ylabel="Fechas con VI6T válido / fechas Landsat disponibles",
)
ax.legend(title="Grupo")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "01_cobertura_relativa_ordenada.png", dpi=180)
plt.close(fig)


# %% 2. Distribución
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
sns.histplot(data=coverage, x="cobertura_relativa_historica", bins=25, ax=axes[0])
sns.histplot(data=coverage, x=metric, bins=25, ax=axes[1], color="#1b9e77")
axes[0].set(title="Cobertura de fechas", xlabel="Observaciones / fechas disponibles")
axes[1].set(title="Cobertura utilizable", xlabel="VI6T válido / fechas disponibles")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "02_distribucion_cobertura.png", dpi=180)
plt.close(fig)


# %% 3. Cobertura histórica frente al ciclo objetivo
fig, ax = plt.subplots(figsize=(8, 6))
sns.scatterplot(
    data=coverage,
    x="cobertura_relativa_historica",
    y="cobertura_relativa_ciclo_2025",
    hue="grupo_cobertura",
    hue_order=GROUP_ORDER,
    palette=GROUP_COLORS,
    s=55,
    ax=ax,
)
ax.set(
    title="Cobertura histórica vs. cobertura abril--octubre 2025",
    xlabel="Cobertura relativa 2022--2025",
    ylabel="Cobertura relativa abril--octubre 2025",
)
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "03_historica_vs_ciclo_2025.png", dpi=180)
plt.close(fig)


# %% 4. Heatmap parcela x mes
monthly = valid.assign(anio_mes=valid[DATE].dt.to_period("M").astype(str))
monthly = pd.crosstab(monthly[ID], monthly["anio_mes"])
ordered_ids = coverage[ID].tolist()
monthly = monthly.reindex(ordered_ids)
monthly.to_csv(OUTPUT_DIR / "05_cobertura_mensual_landsat.csv")

fig, ax = plt.subplots(figsize=(18, 12))
sns.heatmap(monthly, cmap="YlGnBu", cbar_kws={"label": "Observaciones"}, ax=ax)
ax.set(
    title="Cobertura Landsat mensual; parcelas ordenadas de menor a mayor cobertura válida",
    xlabel="Año-mes",
    ylabel="Parcela",
)
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "04_heatmap_cobertura_mensual.png", dpi=180)
plt.close(fig)


# %% 5. Huecos máximos por grupo
fig, ax = plt.subplots(figsize=(9, 5))
sns.boxplot(
    data=coverage,
    x="grupo_cobertura",
    y="gap_maximo_dias_historica",
    order=GROUP_ORDER,
    hue="grupo_cobertura",
    palette=GROUP_COLORS,
    legend=False,
    ax=ax,
)
ax.set(title="Hueco temporal máximo por grupo", xlabel="Grupo", ylabel="Días")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "05_huecos_temporales_por_grupo.png", dpi=180)
plt.close(fig)


# %% 6. Cobertura y área
fig, ax = plt.subplots(figsize=(9, 6))
sns.scatterplot(
    data=coverage, x="AREA_HA", y=metric, hue="grupo_cobertura",
    hue_order=GROUP_ORDER, palette=GROUP_COLORS, s=55, ax=ax,
)
ax.set(title="Cobertura Landsat utilizable vs. área", xlabel="Área (ha)",
       ylabel="VI6T válido / fechas disponibles")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "06_cobertura_vs_area.png", dpi=180)
plt.close(fig)


# %% 7. Cobertura y rendimiento (sólo entrenamiento)
training = coverage.loc[coverage["CONJUNTO"].eq("ENTRENAMIENTO")].copy()
fig, ax = plt.subplots(figsize=(9, 6))
sns.scatterplot(
    data=training, x=metric, y="RENDIMIENTO_T_HA", hue="grupo_cobertura",
    hue_order=GROUP_ORDER, palette=GROUP_COLORS, s=60, ax=ax,
)
ax.set(title="Rendimiento 2025 vs. cobertura Landsat utilizable",
       xlabel="VI6T válido / fechas disponibles", ylabel="Rendimiento (t/ha)")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "07_cobertura_vs_rendimiento.png", dpi=180)
plt.close(fig)


# %% 8. Distribución espacial de grupos
parcels = gpd.read_file(SHAPEFILE)
parcels = parcels.rename(columns={"ID_POLIGON": ID})
map_data = parcels.merge(coverage[[ID, "grupo_cobertura"]], on=ID, how="left")
fig, ax = plt.subplots(figsize=(10, 9))
map_data.plot(
    column="grupo_cobertura",
    categorical=True,
    categories=GROUP_ORDER,
    cmap="Dark2",
    legend=True,
    edgecolor="white",
    linewidth=0.25,
    ax=ax,
)
ax.set_title("Distribución espacial de los grupos de cobertura Landsat")
ax.set_axis_off()
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "08_mapa_grupos_cobertura.png", dpi=180)
plt.close(fig)


print("Fechas Landsat históricas:", len(all_dates))
print("Fechas Landsat abril-octubre 2025:", len(cycle_dates))
print("Umbrales VI6T válido relativo (Q25, Q75):", q25, q75)
print("\nResumen por grupo:\n", group_summary.to_string(index=False))
print("\nGrupo por conjunto:\n", set_group.to_string())
print("\nCorrelaciones Spearman:\n", correlations.to_string())
print("\nResultados:", OUTPUT_DIR.resolve())
