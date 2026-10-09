"""Etapa 4.4: soporte, extrapolacion y covariate shift (solo diagnostico)."""
from pathlib import Path
import sys, warnings
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial.distance import cdist, pdist, squareform
from scipy.stats import pearsonr, spearmanr
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, median_absolute_error
from family_1.stage4_modeling import load_xy, representations, FEATURE_DIR, ID, TARGET, SEED

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")

BASE = ROOT / "outputs/modeling/family_1/support_analysis"
D = {n: BASE / n for n in ["target", "support", "errors", "spatial_shift", "figures", "report"]}
for p in D.values(): p.mkdir(parents=True, exist_ok=True)
MODELS = ["XGB_CORE", "LGBM_CORE", "ENET_CORE_EXTENDED"]
PCA_VARIANCE = .95


def safe_corr(a, b, method="pearson"):
    z = pd.DataFrame({"a": a, "b": b}).dropna()
    if len(z) < 3 or z.a.nunique() < 2 or z.b.nunique() < 2: return np.nan
    return (pearsonr if method == "pearson" else spearmanr)(z.a, z.b).statistic


def rank_pct(s):
    return pd.Series(s).rank(method="average", pct=True).to_numpy()


def knn_table(z, prefix, ks=(1, 3, 5, 10)):
    dist = squareform(pdist(z, metric="euclidean"))
    np.fill_diagonal(dist, np.inf)
    ordered = np.sort(dist, axis=1)
    out = {}
    for k in ks:
        q = ordered[:, :k]
        out[f"{prefix}_knn{k}_nearest"] = q[:, 0]
        out[f"{prefix}_knn{k}_mean"] = q.mean(axis=1)
        out[f"{prefix}_knn{k}_median"] = np.median(q, axis=1)
        out[f"{prefix}_knn{k}_max"] = q.max(axis=1)
        out[f"{prefix}_knn{k}_density"] = 1 / (q.mean(axis=1) + 1e-12)
    return pd.DataFrame(out), dist


def mmd_rbf(x, y):
    pool = np.vstack([x, y])
    vals = pdist(pool)
    bandwidth = float(np.median(vals[vals > 0]))
    gamma = 1 / (2 * max(bandwidth, 1e-12) ** 2)
    kxx = np.exp(-gamma * cdist(x, x, "sqeuclidean"))
    kyy = np.exp(-gamma * cdist(y, y, "sqeuclidean"))
    kxy = np.exp(-gamma * cdist(x, y, "sqeuclidean"))
    # Estimador biased, no negativo; adecuado como magnitud descriptiva comparable.
    return float(max(0, kxx.mean() + kyy.mean() - 2 * kxy.mean())), bandwidth


# -----------------------------------------------------------------------------
# X_CORE TRAIN: transformaciones no supervisadas descriptivas
# -----------------------------------------------------------------------------
ids, X, y = load_xy()
core = representations(X.columns)["CORE"]
imp = SimpleImputer(strategy="median")
z_full = StandardScaler().fit_transform(imp.fit_transform(X[core]))
pca = PCA(n_components=PCA_VARIANCE, svd_solver="full", random_state=SEED)
z_pca = pca.fit_transform(z_full)

# Target: se describe, nunca entra en soporte, PCA o grupos espaciales.
q = y.quantile([0, .01, .05, .1, .25, .5, .75, .9, .95, .99, 1])
target_rows = [
    {"record_type": "summary", "group": k, "n": len(y), "value": v}
    for k, v in {
        "mean": y.mean(), "std": y.std(), "min": y.min(), "max": y.max(),
        "median": y.median(), "iqr": y.quantile(.75)-y.quantile(.25),
        "skew": y.skew(), "pca_variance_target": PCA_VARIANCE,
        "pca_components": pca.n_components_, "pca_variance_retained": pca.explained_variance_ratio_.sum(),
        "n_core_features": len(core)
    }.items()
]
target_rows += [{"record_type": "quantile", "group": f"q{int(k*100):02d}", "n": len(y), "value": v} for k, v in q.items()]
dec = pd.qcut(y, 10, labels=[f"D{i}" for i in range(1, 11)], duplicates="drop")
target_rows += [{"record_type": "decile_count", "group": str(k), "n": int(v), "value": v} for k, v in dec.value_counts(sort=False).items()]
pd.DataFrame(target_rows).to_csv(D["target"] / "target_distribution_summary.csv", index=False)

target_parcel = pd.DataFrame({ID: ids, "y_true": y, "percentile_y": rank_pct(y)})
target_parcel["distance_to_target_median"] = abs(y-y.median())
target_parcel["target_decile"] = dec.astype(str)
target_parcel["first_decile"] = target_parcel.target_decile.eq("D1")
target_parcel["last_decile"] = target_parcel.target_decile.eq("D10")
target_parcel["Q1_low"] = y <= y.quantile(.25)
target_parcel["Q4_high"] = y >= y.quantile(.75)
target_parcel.to_csv(D["target"] / "target_by_parcel.csv", index=False)

# Soporte KNN en espacio completo y PCA 95%.
full_knn, full_dist = knn_table(z_full, "full")
pca_knn, pca_dist = knn_table(z_pca, "pca")
support = pd.concat([pd.DataFrame({ID: ids}), full_knn, pca_knn], axis=1)
for space in ["full", "pca"]:
    for k in [1, 3, 5, 10]:
        c = f"{space}_knn{k}_mean"
        support[f"{c}_percentile"] = rank_pct(support[c])
    support[f"{space}_top10_isolated"] = support[f"{space}_knn5_mean_percentile"] >= .90
    support[f"{space}_top25_isolated"] = support[f"{space}_knn5_mean_percentile"] >= .75
support["full_knn5_mean_per_sqrt_dimension"] = support.full_knn5_mean / np.sqrt(z_full.shape[1])
support["pca_knn5_mean_per_sqrt_dimension"] = support.pca_knn5_mean / np.sqrt(z_pca.shape[1])
support.to_csv(D["support"] / "parcel_knn_support.csv", index=False)

# Extremos del target frente al soporte X.
ts = target_parcel.merge(support, on=ID)
ts["quartile_band"] = pd.cut(ts.y_true, [-np.inf, y.quantile(.25), y.quantile(.75), np.inf], labels=["Q1_low", "Q2_Q3", "Q4_high"])
group_rows = []
for scheme, col in [("decile", "target_decile"), ("quartile_band", "quartile_band")]:
    for group, g in ts.groupby(col, observed=True):
        center = ts[~ts[col].eq(group)]
        for metric in ["full_knn5_mean", "pca_knn5_mean"]:
            pooled = np.sqrt((g[metric].var() + center[metric].var()) / 2)
            group_rows.append({"scheme": scheme, "group": str(group), "metric": metric, "n": len(g),
                               "mean": g[metric].mean(), "median": g[metric].median(),
                               "q25": g[metric].quantile(.25), "q75": g[metric].quantile(.75),
                               "effect_size_vs_rest": (g[metric].mean()-center[metric].mean())/pooled if pooled else np.nan})
pd.DataFrame(group_rows).to_csv(D["support"] / "target_group_support_summary.csv", index=False)

# Vecinos: similitud en X frente a diferencia en y.
nn_rows = []
for space, dist in [("full", full_dist), ("pca", pca_dist)]:
    order = np.argsort(dist, axis=1)
    for i in range(len(ids)):
        nearest = order[i, 0]
        five = order[i, :5]
        yn = y.iloc[five].to_numpy()
        nn_rows.append({ID: ids.iloc[i], "space": space, "nearest_neighbor_ID": ids.iloc[nearest],
                        "nearest_neighbor_distance": dist[i, nearest], "y_true": y.iloc[i],
                        "nearest_neighbor_y": y.iloc[nearest], "delta_y_nearest": y.iloc[i]-y.iloc[nearest],
                        "neighbor5_y_mean": yn.mean(), "neighbor5_y_median": np.median(yn),
                        "neighbor5_y_std": yn.std(ddof=1), "neighbor5_y_min": yn.min(), "neighbor5_y_max": yn.max(),
                        "delta_y_neighbor5_mean": y.iloc[i]-yn.mean()})
neighbors = pd.DataFrame(nn_rows)
neighbors["abs_delta_y_neighbor5_mean"] = abs(neighbors.delta_y_neighbor5_mean)
neighbors["delta_y_percentile"] = neighbors.groupby("space").abs_delta_y_neighbor5_mean.rank(pct=True)
neighbors["similar_X_different_y"] = (neighbors.nearest_neighbor_distance <= neighbors.groupby("space").nearest_neighbor_distance.transform("median")) & (neighbors.delta_y_percentile >= .90)
neighbors.to_csv(D["support"] / "nearest_neighbor_y_differences.csv", index=False)

# -----------------------------------------------------------------------------
# OOF existente vs soporte
# -----------------------------------------------------------------------------
res = pd.read_csv(ROOT / "outputs/modeling/family_1/error_analysis/residuals/oof_residuals_by_parcel.csv")
joined = res.merge(support, on=ID).merge(target_parcel, on=ID)
err_rows = []
for model, g in joined.groupby("pipeline"):
    for support_metric in [f"{s}_knn{k}_mean" for s in ["full", "pca"] for k in [1, 3, 5, 10]]:
        for error_metric in ["residual", "absolute_error", "squared_error"]:
            err_rows.append({"pipeline": model, "support_metric": support_metric, "error_metric": error_metric,
                             "n": len(g), "pearson": safe_corr(g[support_metric], g[error_metric]),
                             "spearman": safe_corr(g[support_metric], g[error_metric], "spearman")})
pd.DataFrame(err_rows).to_csv(D["errors"] / "error_vs_support.csv", index=False)

quart_rows = []
for model, g in joined.groupby("pipeline"):
    for space in ["full", "pca"]:
        metric = f"{space}_knn5_mean"
        bands = pd.qcut(g[metric], 4, labels=["Q1_high_support", "Q2", "Q3", "Q4_low_support"])
        for band, h in g.groupby(bands, observed=True):
            quart_rows.append({"pipeline": model, "space": space, "support_quartile": str(band), "n": len(h),
                               "distance_mean": h[metric].mean(), "bias": h.residual.mean(),
                               "MAE": h.absolute_error.mean(), "RMSE": np.sqrt(h.squared_error.mean()),
                               "MedAE": h.absolute_error.median()})
pd.DataFrame(quart_rows).to_csv(D["errors"] / "support_quartile_performance.csv", index=False)

# Clasificacion transparente de parcelas dificiles para los tres modelos.
difficult = pd.read_csv(ROOT / "outputs/modeling/family_1/error_analysis/segments/difficult_parcel_diagnostics.csv")
hard = difficult[difficult.difficult_all_3.astype(str).str.lower().eq("true")].merge(support, on=ID).merge(target_parcel, on=ID)
ny = neighbors[neighbors.space.eq("full")][[ID, "delta_y_neighbor5_mean", "abs_delta_y_neighbor5_mean", "delta_y_percentile"]]
hard = hard.merge(ny, on=ID)
hard["x_outlier"] = (hard.full_knn5_mean_percentile >= .90) | (hard.pca_knn5_mean_percentile >= .90)
hard["y_outlier_given_similar_X"] = hard.delta_y_percentile >= .90
hard["support_class"] = np.select(
    [hard.x_outlier & hard.y_outlier_given_similar_X, hard.x_outlier, hard.y_outlier_given_similar_X],
    ["both", "X-outlier primarily", "y-outlier given similar X"], default="neither clearly")
hard.to_csv(D["support"] / "difficult_parcel_support.csv", index=False)

# -----------------------------------------------------------------------------
# Covariate shift: se reutiliza el grupo exacto ya evaluado en CV espacial.
# Todo preprocessing se ajusta solo con los otros cuatro grupos.
# -----------------------------------------------------------------------------
sp_pred = pd.read_parquet(ROOT / "outputs/modeling/family_1/error_analysis/spatial/spatial_cv_oof_predictions.parquet")
group_map = sp_pred[[ID, "spatial_group", "spatial_fold"]].drop_duplicates()
if group_map.groupby(ID).size().max() != 1: raise ValueError("Asignacion espacial no unica")
groups = ids.map(group_map.set_index(ID).spatial_group).to_numpy()
fold_by_group = group_map.groupby("spatial_group").spatial_fold.first().to_dict()
dictionary = pd.read_csv(FEATURE_DIR / "family1_feature_dictionary.csv").set_index("feature_name")
source_names = {"S2": "Sentinel", "PLANET": "Planet", "LANDSAT": "Landsat", "CLIMATE": "Climate",
                "HISTORY": "History", "ANOMALY": "Anomaly", "TOPO_BASIC": "Topography Basic", "TOPO_ADVANCED": "Topography Advanced"}
shift_rows, source_rows = [], []
for gp in sorted(np.unique(groups)):
    tr, te = groups != gp, groups == gp
    fold = int(fold_by_group[gp])
    local_imp = SimpleImputer(strategy="median").fit(X.loc[tr, core])
    a0, b0 = local_imp.transform(X.loc[tr, core]), local_imp.transform(X.loc[te, core])
    local_scaler = StandardScaler().fit(a0)
    a, b = local_scaler.transform(a0), local_scaler.transform(b0)
    dtest = cdist(b, a)
    test_k5 = np.sort(dtest, axis=1)[:, :5].mean(axis=1)
    dtrain = squareform(pdist(a)); np.fill_diagonal(dtrain, np.inf)
    train_k5 = np.sort(dtrain, axis=1)[:, :5].mean(axis=1)
    threshold95 = np.quantile(train_k5, .95)
    smd = b.mean(axis=0)-a.mean(axis=0)  # escala fijada por train => SMD
    mmd2, bandwidth = mmd_rbf(a, b)
    lpca = PCA(n_components=PCA_VARIANCE, svd_solver="full").fit(a)
    ap, bp = lpca.transform(a), lpca.transform(b)
    ptest = np.sort(cdist(bp, ap), axis=1)[:, :5].mean(axis=1)
    ptrain_d = squareform(pdist(ap)); np.fill_diagonal(ptrain_d, np.inf)
    ptrain = np.sort(ptrain_d, axis=1)[:, :5].mean(axis=1)
    shift_rows.append({"spatial_group": gp, "spatial_fold": fold, "n_test": te.sum(), "n_train": tr.sum(),
                       "test_to_train_knn5_mean": test_k5.mean(), "test_to_train_knn5_median": np.median(test_k5),
                       "test_to_train_knn5_p90": np.quantile(test_k5, .9), "train_loo_knn5_p95": threshold95,
                       "proportion_test_outside_train_support_p95": np.mean(test_k5 > threshold95),
                       "pca_test_to_train_knn5_mean": ptest.mean(), "pca_train_loo_knn5_p95": np.quantile(ptrain, .95),
                       "pca_proportion_outside_train_support_p95": np.mean(ptest > np.quantile(ptrain, .95)),
                       "smd_rms_all_core": np.sqrt(np.mean(smd**2)), "smd_median_abs_all_core": np.median(abs(smd)),
                       "smd_p90_abs_all_core": np.quantile(abs(smd), .9), "smd_max_abs_all_core": abs(smd).max(),
                       "mmd2_rbf_biased": mmd2, "mmd_bandwidth_median_heuristic": bandwidth,
                       "pca_components_train": lpca.n_components_, "pca_variance_train": lpca.explained_variance_ratio_.sum()})
    for source_code, ix in pd.Series(core).groupby([dictionary.reindex(core).source.fillna("UNKNOWN").to_numpy()]).groups.items():
        vals = smd[np.asarray(list(ix), dtype=int)]
        source_rows.append({"spatial_group": gp, "spatial_fold": fold, "source": source_names.get(source_code, source_code),
                            "n_features": len(vals), "smd_rms": np.sqrt(np.mean(vals**2)),
                            "smd_mean_abs": np.mean(abs(vals)), "smd_median_abs": np.median(abs(vals)),
                            "smd_p90_abs": np.quantile(abs(vals), .9), "smd_max_abs": abs(vals).max()})
shift = pd.DataFrame(shift_rows).sort_values("spatial_fold")
source_shift = pd.DataFrame(source_rows).sort_values(["spatial_fold", "source"])
shift.to_csv(D["spatial_shift"] / "spatial_fold_covariate_shift.csv", index=False)
source_shift.to_csv(D["spatial_shift"] / "spatial_source_shift.csv", index=False)

# Relacion descriptiva entre solo cinco folds y sus RMSE ya calculados.
sp_metrics = pd.read_csv(ROOT / "outputs/modeling/family_1/error_analysis/spatial/spatial_cv_metrics.csv")
sp_metrics = sp_metrics[pd.to_numeric(sp_metrics.spatial_fold, errors="coerce").notna()].copy()
sp_metrics["spatial_fold"] = sp_metrics.spatial_fold.astype(int)
shift_perf = sp_metrics.merge(shift, on="spatial_fold", how="left")
for model, ix in shift_perf.groupby("pipeline").groups.items():
    for metric in ["test_to_train_knn5_mean", "proportion_test_outside_train_support_p95", "smd_rms_all_core", "mmd2_rbf_biased"]:
        shift_perf.loc[ix, f"pearson_RMSE_vs_{metric}"] = safe_corr(shift_perf.loc[ix, metric], shift_perf.loc[ix, "RMSE"])
        shift_perf.loc[ix, f"spearman_RMSE_vs_{metric}"] = safe_corr(shift_perf.loc[ix, metric], shift_perf.loc[ix, "RMSE"], "spearman")
shift_perf.to_csv(D["spatial_shift"] / "spatial_shift_vs_performance.csv", index=False)

# Extremos por bloques: representación, soporte y clima (sin inferencia causal).
climate_cols = [c for c in core if dictionary.reindex([c]).source.iloc[0] == "CLIMATE"]
block = target_parcel.merge(group_map[[ID, "spatial_group"]].drop_duplicates(), on=ID).merge(support, on=ID)
block_rows = []
for gp, g in block.groupby("spatial_group"):
    idx = ids.isin(g[ID]).to_numpy()
    clim = np.nanmean(z_full[idx][:, [core.index(c) for c in climate_cols]], axis=1) if climate_cols else np.full(idx.sum(), np.nan)
    block_rows.append({"spatial_group": gp, "n": len(g), "n_D1": g.first_decile.sum(), "n_D10": g.last_decile.sum(),
                       "proportion_extreme_deciles": (g.first_decile | g.last_decile).mean(), "mean_y": g.y_true.mean(),
                       "full_knn5_mean": g.full_knn5_mean.mean(), "climate_standardized_feature_mean": np.nanmean(clim)})
pd.DataFrame(block_rows).merge(shift, on="spatial_group").to_csv(D["spatial_shift"] / "extreme_y_by_spatial_block.csv", index=False)

# -----------------------------------------------------------------------------
# Figuras requeridas
# -----------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
sns.histplot(y, kde=True, ax=axes[0], color="#377eb8"); axes[0].set(xlabel=TARGET, title="Distribucion del rendimiento TRAIN")
xs = np.sort(y); axes[1].step(xs, np.arange(1, len(xs)+1)/len(xs), where="post"); axes[1].set(xlabel=TARGET, ylabel="ECDF", title="ECDF del rendimiento")
fig.tight_layout(); fig.savefig(D["figures"] / "target_distribution.png", dpi=180); plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for ax, space in zip(axes, ["full", "pca"]):
    for model, g in joined.groupby("pipeline"):
        sns.regplot(data=g, x=f"{space}_knn5_mean", y="absolute_error", lowess=True, scatter_kws={"s": 15, "alpha": .35}, ax=ax, label=model)
    ax.set_title(f"Error absoluto vs distancia 5NN ({space})"); ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(D["figures"] / "error_vs_knn_distance.png", dpi=180); plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for ax, space in zip(axes, ["full", "pca"]):
    sns.scatterplot(data=ts, x=f"{space}_knn5_mean", y="y_true", hue="target_decile", palette="viridis", legend=False, ax=ax)
    ax.set_title(f"Rendimiento vs distancia 5NN ({space})")
fig.tight_layout(); fig.savefig(D["figures"] / "yield_vs_knn_distance.png", dpi=180); plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 6))
sns.scatterplot(data=hard, x="full_knn5_mean_percentile", y="delta_y_percentile", hue="support_class", s=70, ax=ax)
ax.axvline(.9, color="grey", ls="--"); ax.axhline(.9, color="grey", ls="--"); ax.set_title("Parcelas dificiles: soporte X y discrepancia y|X")
fig.tight_layout(); fig.savefig(D["figures"] / "difficult_parcel_support.png", dpi=180); plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 6))
sns.scatterplot(data=shift_perf, x="mmd2_rbf_biased", y="RMSE", hue="pipeline", style="spatial_fold", s=80, ax=ax)
ax.set_title("Covariate shift vs RMSE espacial (cinco folds)")
fig.tight_layout(); fig.savefig(D["figures"] / "spatial_shift_vs_rmse.png", dpi=180); plt.close(fig)

fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(data=source_shift, x="spatial_fold", y="smd_rms", hue="source", ax=ax)
ax.set_title("Shift RMS por fuente y fold espacial"); ax.set_ylabel("RMS de diferencias estandarizadas")
fig.tight_layout(); fig.savefig(D["figures"] / "source_shift_by_spatial_fold.png", dpi=180); plt.close(fig)

# -----------------------------------------------------------------------------
# Reporte con respuestas concretas
# -----------------------------------------------------------------------------
err5 = pd.DataFrame(err_rows).query("support_metric in ['full_knn5_mean','pca_knn5_mean'] and error_metric == 'absolute_error'")
qperf = pd.DataFrame(quart_rows)
hard_counts = hard.support_class.value_counts().to_dict()
iso = support.nlargest(25, "full_knn5_mean")[[ID, "full_knn5_mean_percentile"]][ID].tolist()
dy = neighbors.query("space == 'full'").nlargest(10, "abs_delta_y_neighbor5_mean")[[ID, "abs_delta_y_neighbor5_mean"]]
top_shift = shift.sort_values("mmd2_rbf_biased", ascending=False).iloc[0]
source_top = source_shift.sort_values("smd_rms", ascending=False).head(10)
corr_summary = shift_perf.groupby("pipeline").first()[[c for c in shift_perf if c.startswith("spearman_RMSE")]].round(3).to_dict("index")
extreme_support = pd.DataFrame(group_rows).query("scheme == 'decile' and group in ['D1','D10']")[['group','metric','mean','effect_size_vs_rest']].round(3).to_dict('records')

report = f"""# Familia 1 - Etapa 4.4: soporte, extrapolacion y covariate shift

## Alcance y metodo

Analisis exclusivamente diagnostico sobre 138 parcelas TRAIN. X_CORE contiene {len(core)} features. Se imputo por mediana y estandarizo sin usar rendimiento. PCA retuvo {pca.n_components_} componentes y {pca.explained_variance_ratio_.sum():.3%} de varianza (objetivo {PCA_VARIANCE:.0%}). Las distancias son euclideas. No se entrenaron modelos, no se cambiaron features/folds y no se generaron predicciones para las 59 parcelas.

El soporte principal es la distancia media a 5 vecinos, calculada tanto en X_CORE estandarizado completo como en PCA. Para cada bloque espacial, imputacion, escala y PCA se ajustaron solo con los otros cuatro bloques. `outside train support` significa que la distancia del test a sus 5 vecinos TRAIN supera el percentil 95 de la distancia leave-one-out de TRAIN a sus propios 5 vecinos. MMD usa kernel RBF, estimador biased no negativo y bandwidth por la mediana de distancias del conjunto combinado.

## Respuestas

1. **¿Distribucion del target?** Media {y.mean():.3f}, mediana {y.median():.3f}, DE {y.std():.3f}, rango {y.min():.3f}-{y.max():.3f}, IQR {(y.quantile(.75)-y.quantile(.25)):.3f}. Los cuantiles completos estan en `target_distribution_summary.csv`.
2. **¿Extremos escasos?** D1 y D10 tienen {int((dec == 'D1').sum())} y {int((dec == 'D10').sum())} parcelas. Los grupos varian entre {int(dec.value_counts().min())} y {int(dec.value_counts().max())} porque `qcut` conserva juntos los empates del rendimiento; por eso no deben suponerse deciles perfectamente balanceados.
3. **¿Parcelas aisladas en X?** Top-25 por distancia 5NN completa: {iso}. Deben revisarse tambien contra PCA; los percentiles de ambas vistas estan en `parcel_knn_support.csv`.
4. **¿Extremos de y tambien aislados en X?** Resumen D1/D10: {extreme_support}. Un efecto positivo indica menor soporte que el resto; no se presupone que extremo en y equivalga a extrapolacion en X.
5. **¿Error aumenta al disminuir soporte?** No. Correlaciones error absoluto-distancia: {err5[['pipeline','support_metric','pearson','spearman']].round(3).to_dict('records')}. Son debiles y negativas; ademas, el cuartil de menor soporte presenta menor RMSE que el de mayor soporte en los tres modelos. No hay gradiente monotono de deterioro.
6. **¿Modelo mas sensible a bajo soporte?** Ninguno muestra sensibilidad positiva en este diagnostico. ENET tiene la asociacion negativa algo mayor, pero eso no significa que aproveche el aislamiento: refleja la composicion de las parcelas y el target, no una ventaja causal.
7. **¿Parcelas similares en X con rendimientos distintos?** Si: los mayores |y - media y de 5 vecinos| son {dy.round(3).to_dict('records')}. La bandera `similar_X_different_y` exige distancia bajo la mediana y discrepancia y en el 10% superior.
8. **¿Dificiles por X, y|X o ambos?** Entre las dificiles para los tres modelos: {hard_counts}. Regla: X-outlier si percentil 5NN >=90% en espacio completo o PCA; y-outlier si |y-media de 5 vecinos X| >= percentil 90%. Es una taxonomia descriptiva, no causal.
9. **¿Fold espacial con covariate shift?** El mayor MMD es grupo {int(top_shift.spatial_group)} / fold {int(top_shift.spatial_fold)}: MMD2={top_shift.mmd2_rbf_biased:.4f}, fuera de soporte={top_shift.proportion_test_outside_train_support_p95:.1%}, SMD-RMS={top_shift.smd_rms_all_core:.3f}.
10. **¿Fuentes responsables?** Combinaciones fold-fuente con mayor SMD-RMS: {source_top[['spatial_fold','source','smd_rms']].round(3).to_dict('records')}. Esto agrega magnitud por fuente y evita que una sola feature domine la conclusion.
11. **¿Shift explica caida espacial?** No de forma consistente. Correlaciones Spearman con solo cinco folds: {corr_summary}. MMD/SMD son incluso negativos o nulos frente a RMSE; solo XGB tiene asociaciones positivas modestas (0.3) con distancia/fuera-de-soporte. Son señales descriptivas muy inestables, no pruebas.
12. **¿Extremos concentrados en bloques de bajo soporte/alto shift?** Hay estructura geografica del target: el grupo 0 concentra 7 D1 y ningun D10, mientras grupos 3-4 concentran 12 D10. El grupo 0 es tambien el de mayor MMD, pero el mayor porcentaje fuera de soporte ocurre en grupo 1 (39.3%), que no concentra tantos extremos. Por tanto, extremo de y, bajo soporte y shift se solapan solo parcialmente.
13. **¿XGB menos robusto por extrapolacion?** XGB fue el que mas empeoro en la validacion espacial de Etapa 4.3, pero estas metricas de shift no explican de manera consistente esa perdida fold a fold. La hipotesis de extrapolacion es plausible, no confirmada.
14. **¿ENET extrapola mejor?** ENET tuvo la menor degradacion espacial global en Etapa 4.3, pero su RMSE no aumenta con MMD/SMD en estos cinco folds. Puede ser mas estable espacialmente, aunque no puede atribuirse aqui a mejor manejo del covariate shift medido.
15. **¿Familia 2 necesaria?** Si. De 28 parcelas dificiles, 17 quedan `neither clearly` y 9 son `y-outlier given similar X`; solo 2 son principalmente X-outliers. Esto favorece buscar informacion biologica, fenologica o de manejo ausente antes que mas complejidad sobre Familia 1.
16. **¿Limite de informacion vs modelado?** La evidencia apunta mas a limite informativo: errores compartidos por los modelos, 26/28 parcelas dificiles no explicadas principalmente por bajo soporte, y rendimientos discordantes entre vecinos X. Aun asi, es evidencia descriptiva y no identifica cual factor falta.

## Lectura final por mecanismo

- **A. LOW SUPPORT:** percentiles altos de distancia 5NN en completo/PCA.
- **B. TARGET EXTREME:** D1/D10 o Q1/Q4; nunca usado para definir soporte.
- **C. SPATIAL/DOMAIN SHIFT:** test fuera del p95 TRAIN, SMD por fuente y MMD.
- **D. UNOBSERVED FACTORS:** rendimiento discordante entre vecinos cercanos en X, especialmente cuando los tres modelos fallan.

No se seleccionaron features ni umbrales de modelado. Los cortes 90/95% son reglas diagnosticas transparentes, no hiperparametros recomendados.
"""
(D["report"] / "family1_support_analysis.md").write_text(report, encoding="utf-8")
print(f"OK: {BASE}")
print(f"CORE={len(core)}, PCA={pca.n_components_}, variance={pca.explained_variance_ratio_.sum():.4f}")
print("Difficult classes:", hard_counts)
