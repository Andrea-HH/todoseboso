"""EDA 04: distribución espacial de parcelas y rendimiento observado en 2025."""

# %% Librerías y rutas
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch


SHAPEFILE = Path("data/original/02_conjunto_70_30/Parcelas_Reto_AGC_CONJUNTO.shp")
TARGET_FILE = Path(
    "data/original/01_tablas_maestras/ID_area_rendimiento_70_30_Reto_AgroCebada.csv"
)
OUTPUT_DIR = Path("outputs/eda/01_tablas_maestras/04_parcelas_rendimiento")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ID = "ID_POLIGONO"
YIELD = "RENDIMIENTO_T_HA"
sns.set_theme(style="whitegrid")


# %% Lectura y unión espacial
parcels = gpd.read_file(SHAPEFILE).rename(columns={"ID_POLIGON": ID})
target = pd.read_csv(TARGET_FILE).drop(columns=["Unnamed: 4"], errors="ignore")

# El CSV es la fuente canónica de área, rendimiento y conjunto.
geo = parcels.drop(columns=["CONJUNTO"], errors="ignore").merge(
    target, on=ID, how="left", validate="one_to_one"
)
geo["estado_municipio"] = geo["Estado"] + " — " + geo["Municipio"]
geo["estado_rendimiento"] = geo[YIELD].notna().map(
    {True: "Rendimiento observado", False: "Rendimiento oculto"}
)

assert len(geo) == 197, "La unión espacial debe conservar las 197 parcelas."
assert geo[ID].is_unique, "El identificador debe ser único."

mismatch = geo[
    (geo["CONJUNTO"].eq("ENTRENAMIENTO") & geo[YIELD].isna())
    | (geo["CONJUNTO"].eq("PREDICCION") & geo[YIELD].notna())
]
assert mismatch.empty, "Rendimiento faltante y CONJUNTO no son consistentes."


# %% Tablas de salida
overall_summary = geo[YIELD].describe().rename("valor").reset_index()
overall_summary = overall_summary.rename(columns={"index": "estadistica"})
overall_summary.to_csv(OUTPUT_DIR / "01_resumen_rendimiento.csv", index=False)

state_summary = (
    geo.groupby("Estado", as_index=False)
    .agg(
        parcelas=(ID, "size"),
        rendimientos_observados=(YIELD, "count"),
        rendimiento_media=(YIELD, "mean"),
        rendimiento_mediana=(YIELD, "median"),
        rendimiento_std=(YIELD, "std"),
        rendimiento_min=(YIELD, "min"),
        rendimiento_max=(YIELD, "max"),
        area_mediana_ha=("AREA_HA", "median"),
    )
)
state_summary["rendimientos_ocultos"] = (
    state_summary["parcelas"] - state_summary["rendimientos_observados"]
)
state_summary.to_csv(OUTPUT_DIR / "02_resumen_por_estado.csv", index=False)

municipality_summary = (
    geo.groupby(["Estado", "Municipio"], as_index=False)
    .agg(
        parcelas=(ID, "size"),
        rendimientos_observados=(YIELD, "count"),
        rendimiento_media=(YIELD, "mean"),
        rendimiento_mediana=(YIELD, "median"),
        rendimiento_std=(YIELD, "std"),
    )
)
municipality_summary["rendimientos_ocultos"] = (
    municipality_summary["parcelas"] - municipality_summary["rendimientos_observados"]
)
municipality_summary.to_csv(OUTPUT_DIR / "03_resumen_por_municipio.csv", index=False)

geo.drop(columns="geometry").to_csv(
    OUTPUT_DIR / "04_parcelas_atributos_rendimiento.csv", index=False
)


# %% 1. Mapa principal: rendimiento continuo y faltantes grises
observed = geo.loc[geo[YIELD].notna()]
missing = geo.loc[geo[YIELD].isna()]

fig, ax = plt.subplots(figsize=(12, 9))
missing.plot(color="#bdbdbd", edgecolor="white", linewidth=0.35, ax=ax,
             label="Rendimiento oculto")
observed.plot(column=YIELD, cmap="viridis", edgecolor="white", linewidth=0.35,
              legend=True, legend_kwds={"label": "Rendimiento (t/ha)", "shrink": 0.7},
              ax=ax)
ax.set_title("Rendimiento observado por parcela — ciclo abril–octubre 2025")
ax.set_axis_off()
ax.legend(handles=[Patch(facecolor="#bdbdbd", edgecolor="white",
                         label="Rendimiento oculto")], loc="lower left")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "01_mapa_rendimiento_parcelas.png", dpi=200)
plt.close(fig)


# %% 2. Mapa explícito de disponibilidad de etiqueta
fig, ax = plt.subplots(figsize=(12, 9))
geo.plot(column="estado_rendimiento", categorical=True,
         cmap="Set2", edgecolor="white", linewidth=0.35, legend=True, ax=ax)
ax.set_title("Parcelas con rendimiento observado y oculto")
ax.set_axis_off()
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "02_mapa_disponibilidad_rendimiento.png", dpi=200)
plt.close(fig)


# %% 3. Distribución general
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
sns.histplot(data=observed, x=YIELD, bins=15, kde=True, ax=axes[0], color="#2c7fb8")
sns.boxplot(data=observed, x=YIELD, ax=axes[1], color="#7fcdbb")
axes[0].set(title="Distribución del rendimiento observado", xlabel="Rendimiento (t/ha)")
axes[1].set(title="Rango y posibles extremos", xlabel="Rendimiento (t/ha)")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "03_distribucion_rendimiento.png", dpi=180)
plt.close(fig)


# %% 4. Comparación por estado
fig, ax = plt.subplots(figsize=(10, 6))
sns.boxplot(data=observed, x="Estado", y=YIELD, hue="Estado", legend=False, ax=ax)
sns.stripplot(data=observed, x="Estado", y=YIELD, color="black", alpha=0.35,
              size=3, ax=ax)
ax.set(title="Rendimiento observado por estado", xlabel="Estado",
       ylabel="Rendimiento (t/ha)")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "04_rendimiento_por_estado.png", dpi=180)
plt.close(fig)


# %% 5. Comparación por municipio
municipality_plot = municipality_summary.sort_values("rendimiento_media")
fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(data=municipality_plot, y="Municipio", x="rendimiento_media",
            hue="Estado", dodge=False, ax=ax)
for container in ax.containers:
    ax.bar_label(container, fmt="%.2f", padding=2, fontsize=8)
ax.set(title="Rendimiento medio observado por municipio",
       xlabel="Rendimiento medio (t/ha)", ylabel="Municipio")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "05_rendimiento_por_municipio.png", dpi=180)
plt.close(fig)


# %% 6. Área y rendimiento
fig, ax = plt.subplots(figsize=(9, 6))
sns.scatterplot(data=observed, x="AREA_HA", y=YIELD, hue="Estado", s=60, ax=ax)
ax.set(title="Área de parcela frente a rendimiento observado",
       xlabel="Área (ha)", ylabel="Rendimiento (t/ha)")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "06_area_vs_rendimiento.png", dpi=180)
plt.close(fig)


print("Fuente espacial:", SHAPEFILE)
print("CRS:", geo.crs)
print("Parcelas:", len(geo))
print("Rendimiento observado:", geo[YIELD].notna().sum())
print("Rendimiento oculto:", geo[YIELD].isna().sum())
print("\nResumen global:\n", overall_summary.to_string(index=False))
print("\nResumen por estado:\n", state_summary.to_string(index=False))
print("\nResultados:", OUTPUT_DIR.resolve())
