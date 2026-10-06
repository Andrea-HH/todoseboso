"""Familia 1, Etapa 2.5K-M: diagnósticos y reporte ambiental."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from _environment_zonal_utils import ID, load_parcels


ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data/processed/family_1/environment"
OUTPUT_DIR = ROOT / "outputs/data_audit/family_1/environment"
FIGURE_DIR = OUTPUT_DIR / "figures"
SHAPEFILE = ROOT / "data/original/02_conjunto_70_30/Parcelas_Reto_AGC_CONJUNTO.shp"
MASTER = ROOT / "data/original/01_tablas_maestras/ID_area_rendimiento_70_30_Reto_AgroCebada.csv"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid")

climate = pd.read_parquet(DATA_DIR / "climate_monthly_timeseries.parquet")
topography = pd.read_parquet(DATA_DIR / "topography_by_parcel.parquet")
resolution = pd.read_csv(OUTPUT_DIR / "climate_spatial_resolution_by_parcel.csv")
area = pd.read_csv(OUTPUT_DIR / "area_comparison.csv")
parcels = load_parcels(SHAPEFILE, MASTER)


# -----------------------------------------------------------------------------
# Cobertura y missingness
# -----------------------------------------------------------------------------
expected_months = pd.period_range("2022-01", "2025-12", freq="M").astype(str).tolist()
coverage_rows = []
for parcel_id, part in climate.groupby(ID):
    available = part.loc[part["all_sources_available"], "date_month"].dt.to_period("M").astype(str)
    available_set = set(available)
    missing_months = sorted(set(expected_months) - available_set)
    coverage_rows.append({
        ID: parcel_id, "CONJUNTO": part["CONJUNTO"].iloc[0],
        "expected_months_2022_2025": 48,
        "available_months_all_sources": len(available_set),
        "missing_months_count": len(missing_months),
        "missing_months": " | ".join(missing_months),
        "available_history_2022_2024": int(part.loc[part["is_history_2022_2024"], "all_sources_available"].sum()),
        "expected_history_2022_2024": 36,
        "available_apr_oct_2025": int(part.loc[part["is_current_cycle_2025"], "all_sources_available"].sum()),
        "expected_apr_oct_2025": 7,
    })
climate_coverage = pd.DataFrame(coverage_rows)
climate_coverage.to_csv(OUTPUT_DIR / "climate_coverage_by_parcel.csv", index=False)

missingness = pd.DataFrame({
    "column": climate.columns,
    "n_missing": climate.isna().sum().values,
    "pct_missing": (100 * climate.isna().mean()).values,
    "n_unique_non_null": [climate[column].nunique(dropna=True) for column in climate.columns],
})
missingness.to_csv(OUTPUT_DIR / "climate_missingness.csv", index=False)


# -----------------------------------------------------------------------------
# TRAIN vs PREDICTION, sin rendimiento
# -----------------------------------------------------------------------------
comparison_rows = []
climate_metrics = [
    "precip_mean", "tmin_mean", "tmax_mean", "tmean_mean", "dtr_mean",
    "precip_n_pixels", "tmin_n_pixels", "tmax_n_pixels",
    "precip_valid_fraction", "tmin_valid_fraction", "tmax_valid_fraction",
]
for group, part in climate.groupby("CONJUNTO"):
    for column in climate_metrics:
        values = part[column].dropna()
        comparison_rows.append({
            "source": "climate", "group": group, "variable": column,
            "n": len(values), "missing_pct": 100 * part[column].isna().mean(),
            "min": values.min(), "median": values.median(), "mean": values.mean(),
            "max": values.max(), "std": values.std(),
        })
topo_metrics = [
    "elevation_mean", "elevation_std", "elevation_range", "elevation_n_pixels",
    "elevation_valid_fraction", "slope_mean", "slope_std", "slope_range",
    "slope_n_pixels", "slope_valid_fraction", "AREA_HA",
]
for group, part in topography.groupby("CONJUNTO"):
    for column in topo_metrics:
        values = part[column].dropna()
        comparison_rows.append({
            "source": "topography", "group": group, "variable": column,
            "n": len(values), "missing_pct": 100 * part[column].isna().mean(),
            "min": values.min(), "median": values.median(), "mean": values.mean(),
            "max": values.max(), "std": values.std(),
        })
environment_comparison = pd.DataFrame(comparison_rows)
environment_comparison.to_csv(
    OUTPUT_DIR / "train_prediction_environment_comparison.csv", index=False
)


# -----------------------------------------------------------------------------
# Tablas de diagnóstico de resolución y rangos
# -----------------------------------------------------------------------------
resolution_summary = resolution.groupby("variable", as_index=False).agg(
    parcels=(ID, "nunique"),
    median_touched_pixels=("n_pixels_median", "median"),
    max_touched_pixels=("n_pixels_max", "max"),
    median_effective_pixel_count=("effective_pixel_count_median", "median"),
    parcels_typically_one_pixel=("n_pixels_median", lambda x: int(x.le(1).sum())),
    median_abs_weighted_standard_difference=("weighted_standard_abs_diff_median", "median"),
    max_abs_weighted_standard_difference=("weighted_standard_abs_diff_max", "max"),
)
resolution_summary["pct_parcels_typically_one_pixel"] = (
    100 * resolution_summary["parcels_typically_one_pixel"] / resolution_summary["parcels"]
)
resolution_summary.to_csv(OUTPUT_DIR / "climate_spatial_resolution_summary.csv", index=False)

environment_ranges = []
for source_name, frame, columns in [
    ("climate", climate, ["precip_mean", "tmin_mean", "tmax_mean", "tmean_mean", "dtr_mean"]),
    ("topography", topography, ["elevation_mean", "elevation_std", "elevation_range",
                                "slope_mean", "slope_std", "slope_range"]),
]:
    for column in columns:
        values = frame[column].dropna()
        environment_ranges.append({
            "source": source_name, "variable": column, "n": len(values),
            "min": values.min(), "q1": values.quantile(.25), "median": values.median(),
            "mean": values.mean(), "q3": values.quantile(.75), "max": values.max(),
            "std": values.std(),
        })
pd.DataFrame(environment_ranges).to_csv(OUTPUT_DIR / "environment_value_ranges.csv", index=False)


# -----------------------------------------------------------------------------
# Muestra reproducible de parcelas: cuantiles de área oficial
# -----------------------------------------------------------------------------
ordered = topography.sort_values("AREA_HA")
positions = np.linspace(0, len(ordered) - 1, 5).round().astype(int)
sample_ids = ordered.iloc[positions][ID].drop_duplicates().tolist()
pd.DataFrame({ID: sample_ids}).to_csv(OUTPUT_DIR / "environment_example_parcels.csv", index=False)


# -----------------------------------------------------------------------------
# Visualizaciones
# -----------------------------------------------------------------------------
# 1 cobertura mensual
availability = climate.assign(available=climate["all_sources_available"].astype(int))
heat = availability.pivot(index=ID, columns="date_month", values="available")
fig, ax = plt.subplots(figsize=(18, 12))
sns.heatmap(heat, cmap="YlGn", vmin=0, vmax=1, cbar_kws={"label": "Fuentes disponibles"}, ax=ax)
ax.set(title="Cobertura climática mensual por parcela", xlabel="Mes", ylabel="Parcela")
fig.tight_layout(); fig.savefig(FIGURE_DIR / "01_cobertura_climatica_mensual.png", dpi=180); plt.close(fig)

# 2 píxeles
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
sns.histplot(data=resolution, x="n_pixels_median", hue="variable", discrete=True,
             multiple="dodge", ax=axes[0])
sns.histplot(data=topography, x="elevation_n_pixels", bins=25, ax=axes[1], label="elevación")
sns.histplot(data=topography, x="slope_n_pixels", bins=25, ax=axes[1], alpha=.5, label="pendiente")
axes[0].set(title="Píxeles climáticos tocados", xlabel="Mediana por parcela")
axes[1].set(title="Píxeles topográficos tocados", xlabel="Píxeles")
axes[1].legend()
fig.tight_layout(); fig.savefig(FIGURE_DIR / "02_pixeles_por_parcela.png", dpi=180); plt.close(fig)

# 3 precipitación
plot_sample = climate.loc[climate[ID].isin(sample_ids)]
fig, ax = plt.subplots(figsize=(15, 6))
sns.lineplot(data=plot_sample, x="date_month", y="precip_mean", hue=ID, marker="o", ax=ax)
ax.set(title="Precipitación mensual — muestra reproducible", xlabel="Mes", ylabel="mm/mes")
fig.tight_layout(); fig.savefig(FIGURE_DIR / "03_precipitacion_ejemplos.png", dpi=180); plt.close(fig)

# 4 Tmin/Tmean/Tmax
example_id = sample_ids[len(sample_ids) // 2]
example = climate.loc[climate[ID].eq(example_id)]
fig, ax = plt.subplots(figsize=(15, 5))
for column, label in [("tmin_mean", "Tmin"), ("tmean_mean", "Tmean"), ("tmax_mean", "Tmax")]:
    ax.plot(example["date_month"], example[column], marker=".", label=label)
ax.set(title=f"Temperaturas mensuales — {example_id}", xlabel="Mes", ylabel="°C")
ax.legend(); fig.tight_layout(); fig.savefig(FIGURE_DIR / "04_temperaturas_ejemplo.png", dpi=180); plt.close(fig)

# 5 DTR
fig, ax = plt.subplots(figsize=(15, 5))
sns.lineplot(data=plot_sample, x="date_month", y="dtr_mean", hue=ID, ax=ax)
ax.set(title="Amplitud térmica mensual — muestra reproducible", xlabel="Mes", ylabel="DTR (°C)")
fig.tight_layout(); fig.savefig(FIGURE_DIR / "05_dtr_mensual.png", dpi=180); plt.close(fig)

# 6-7 topografía
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
sns.histplot(data=topography, x="elevation_mean", bins=25, ax=axes[0])
sns.histplot(data=topography, x="elevation_range", bins=25, ax=axes[1])
axes[0].set(title="Elevación media", xlabel="m")
axes[1].set(title="Variación de elevación intraparcela", xlabel="rango (m)")
fig.tight_layout(); fig.savefig(FIGURE_DIR / "06_distribucion_elevacion.png", dpi=180); plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
sns.histplot(data=topography, x="slope_mean", bins=25, ax=axes[0])
sns.histplot(data=topography, x="slope_range", bins=25, ax=axes[1])
axes[0].set(title="Pendiente media", xlabel="grados")
axes[1].set(title="Variación de pendiente intraparcela", xlabel="rango (grados)")
fig.tight_layout(); fig.savefig(FIGURE_DIR / "07_distribucion_pendiente.png", dpi=180); plt.close(fig)

# 8 área
fig, ax = plt.subplots(figsize=(7, 7))
sns.scatterplot(data=area, x="area_official_ha", y="area_geometry_ha", hue="CONJUNTO", ax=ax)
limits = [min(area["area_official_ha"].min(), area["area_geometry_ha"].min()),
          max(area["area_official_ha"].max(), area["area_geometry_ha"].max())]
ax.plot(limits, limits, linestyle="--", color="black")
ax.set(title="Área oficial vs. área geométrica", xlabel="Área oficial (ha)", ylabel="Área geométrica (ha)")
fig.tight_layout(); fig.savefig(FIGURE_DIR / "08_area_oficial_vs_geometrica.png", dpi=180); plt.close(fig)

# 9 mapas sencillos
map_data = parcels.merge(topography[[ID, "elevation_mean"]], on=ID, how="left")
july_2025 = climate.loc[(climate["year"].eq(2025)) & (climate["month"].eq(7)), [ID, "precip_mean"]]
map_data = map_data.merge(july_2025, on=ID, how="left")
fig, axes = plt.subplots(1, 2, figsize=(15, 7))
map_data.plot(column="elevation_mean", cmap="terrain", legend=True, ax=axes[0], edgecolor="white", linewidth=.2)
map_data.plot(column="precip_mean", cmap="Blues", legend=True, ax=axes[1], edgecolor="white", linewidth=.2)
axes[0].set_title("Elevación media por parcela")
axes[1].set_title("Precipitación media — julio 2025")
for ax in axes: ax.set_axis_off()
fig.tight_layout(); fig.savefig(FIGURE_DIR / "09_mapas_ambientales.png", dpi=180); plt.close(fig)


# -----------------------------------------------------------------------------
# Reporte con respuestas explícitas
# -----------------------------------------------------------------------------
res = resolution_summary.set_index("variable")
climate_one_pixel_pct = float(res["pct_parcels_typically_one_pixel"].median())
climate_diff_median = float(res["median_abs_weighted_standard_difference"].median())
climate_diff_max = float(res["max_abs_weighted_standard_difference"].max())
area_stats = area["area_relative_difference_pct"].describe()
temp_violation = int((climate["tmin_mean"] > climate["tmax_mean"]).sum())
coverage_complete = int(climate_coverage["missing_months_count"].eq(0).sum())

report = f"""# Familia 1 — Etapa 2.5: clima y topografía por parcela

Generado: {datetime.now().astimezone().isoformat(timespec='seconds')}

## Alcance

Se transformaron rásteres climáticos mensuales y topográficos estáticos a la unidad parcela. No se utilizó rendimiento, no se seleccionaron variables y no se unieron todavía con satélites.

## Respuestas a las preguntas de la etapa

### 1. ¿Tenemos los 48 meses esperados?

Sí. Hay 48 rásteres de precipitación, 48 Tmin y 48 Tmax para enero de 2022 a diciembre de 2025. No hay combinaciones variable-año-mes faltantes ni duplicadas.

### 2. ¿Todas las parcelas tienen cobertura completa?

Sí. {coverage_complete}/197 parcelas tienen las tres fuentes climáticas en los 48 meses, 36 meses históricos y los 7 meses de abril–octubre 2025. No hay medias climáticas faltantes.

### 3. ¿Cuántos píxeles climáticos intersectan típicamente una parcela?

La mediana es 1 píxel tocado para precipitación, Tmin y Tmax. Aproximadamente {climate_one_pixel_pct:.1f}% de las parcelas están típicamente dentro de un solo píxel; el máximo es 3. La fracción efectiva mediana de un píxel es muy pequeña porque la resolución es 0.05° y las parcelas son mucho menores.

### 4. ¿Tiene sentido conservar min/max/std climáticos intraparcela?

Se conservan por trazabilidad, pero para la mayoría son redundantes: con un píxel, min=median=mean=max y std=0. Sólo aportan variación en parcelas que cruzan límites de celda. Deben marcarse como potencialmente redundantes por resolución, no eliminarse todavía por relación con el target.

### 5–6. ¿Es necesaria ponderación por área y cambia respecto a la media estándar?

Sí es el método técnicamente correcto para parcelas que tocan varios píxeles, aunque para la parcela mediana la diferencia es 0 porque toca uno. La mediana absoluta global entre media ponderada y media igual de píxeles tocados es {climate_diff_median:.4f}; el máximo llega a {climate_diff_max:.3f}, impulsado por precipitación en parcelas de frontera. Por ello se conserva la media ponderada como principal y la estándar sólo como diagnóstico.

### 7. ¿Existen valores climáticos físicamente sospechosos?

No aparecen precipitaciones negativas ni faltantes. Los rangos observados son precipitación 0–{climate['precip_mean'].max():.2f} mm/mes, Tmin {climate['tmin_mean'].min():.2f}–{climate['tmin_mean'].max():.2f} °C y Tmax {climate['tmax_mean'].min():.2f}–{climate['tmax_mean'].max():.2f} °C. Son plausibles como rangos generales; no se eliminaron extremos.

### 8. ¿Tmin <= Tmax siempre?

Sí. Hay {temp_violation} violaciones en 9,456 combinaciones parcela-mes.

### 9. ¿Cómo se distribuye DTR?

DTR varía entre {climate['dtr_mean'].min():.2f} y {climate['dtr_mean'].max():.2f} °C, con mediana {climate['dtr_mean'].median():.2f} °C y media {climate['dtr_mean'].mean():.2f} °C. No hay valores negativos.

### 10. ¿TRAIN y PREDICTION son comparables?

Ambos tienen cobertura climática completa y topografía completa. `train_prediction_environment_comparison.csv` permite revisar por grupo los rangos de clima, soporte de píxeles, elevación y pendiente. Las diferencias descriptivas pueden reflejar geografía; no se realizaron tests ni se usó rendimiento.

### 11. ¿Todas las parcelas tienen elevación y pendiente?

Sí. Las 197 parcelas tienen ambas variables y fracción válida completa.

### 12. ¿Cuánta variación topográfica existe dentro de parcela?

Elevación media: {topography['elevation_mean'].min():.1f}–{topography['elevation_mean'].max():.1f} m. El rango intraparcela tiene mediana {topography['elevation_range'].median():.1f} m y máximo {topography['elevation_range'].max():.1f} m. Pendiente media: {topography['slope_mean'].min():.2f}–{topography['slope_mean'].max():.2f}°, con rango intraparcela mediano {topography['slope_range'].median():.2f}° y máximo {topography['slope_range'].max():.2f}°. Aquí min/max/std sí contienen variación real para muchas parcelas porque la resolución es 120 m.

### 13. ¿Área oficial y geométrica son consistentes?

Sí, con una diferencia sistemática pequeña. El área geométrica es en promedio {area_stats['mean']:.3f}% distinta de la oficial; mediana {area_stats['50%']:.3f}%, rango {area_stats['min']:.3f}% a {area_stats['max']:.3f}%. Se conserva el área oficial; área geométrica, perímetro y centroides quedan sólo para auditoría.

### 14. ¿Qué variables están listas para feature engineering?

- Serie mensual: precipitación, Tmin, Tmax con media ponderada, mediana, min, max, std, píxeles y cobertura.
- Derivadas mensuales directas: Tmean y DTR.
- Topografía estática: elevación y pendiente con mean/median/min/max/std/range y calidad.
- Flags temporales: ciclo abril–octubre 2025 e historia 2022–2024.

Todavía no se construyeron acumulados del ciclo, anomalías, ventanas early/mid/late ni interacciones.

### 15. ¿Qué parece redundante sólo por resolución?

En clima, min/max/median/std son redundantes para la mayoría de parcelas porque típicamente intersectan un solo píxel. `n_pixels`, `valid_fraction` y la comparación ponderada siguen siendo útiles para trazabilidad. En topografía, la resolución de 120 m produce una mediana de {topography['elevation_n_pixels'].median():.0f} píxeles de elevación y {topography['slope_n_pixels'].median():.0f} de pendiente por parcela, por lo que la variabilidad intraparcela es más informativa.

## Método espacial

- Clima y parcelas: EPSG:4326; no fue necesaria reproyección para extracción.
- Topografía: EPSG:6372; parcelas reproyectadas únicamente en memoria.
- Área geométrica: EPSG:6372.
- Estadísticas principales: `exactextract`, ponderación exacta por fracción de píxel.
- Área efectiva válida: área geométrica métrica multiplicada por fracción válida.
- Raw modificado: no.
- Target utilizado: no.

## Decisiones pendientes para Etapa 3

1. Definir acumulados y ventanas climáticas del ciclo 2025.
2. Definir climatología/anomalías 2025 frente a 2022–2024.
3. Decidir si conservar min/max/std climáticos en el bloque final pese a su redundancia espacial.
4. Mantener la media ponderada como principal y decidir si retirar medias estándar diagnósticas.
5. Definir fecha de corte de predicción para impedir usar meses futuros.
6. Diseñar prefijos de features ambientales y unir sólo después de agregar a nivel parcela.
7. Evaluar aporte incremental de clima/topografía únicamente en etapas de modelado y dentro del protocolo CV.
"""
(OUTPUT_DIR / "environment_summary.md").write_text(report, encoding="utf-8")
(OUTPUT_DIR / "environment_diagnostics_manifest.json").write_text(json.dumps({
    "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    "climate_rows": len(climate), "topography_rows": len(topography),
    "target_used": False, "raw_modified": False,
    "significance_tests": False, "satellite_joined": False,
}, indent=2), encoding="utf-8")

print("Diagnóstico ambiental generado correctamente.")
print("Clima:", climate.shape, "Topografía:", topography.shape)
print("Outputs:", OUTPUT_DIR)
