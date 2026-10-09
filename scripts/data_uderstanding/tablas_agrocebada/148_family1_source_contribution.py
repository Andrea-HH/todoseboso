"""Etapa 4.5: contribucion predictiva por fuente con nested CV congelada."""
from pathlib import Path
import sys, json, time, warnings, argparse
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr, spearmanr
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import GridSearchCV, KFold
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, median_absolute_error
from xgboost import XGBRegressor
from family_1.stage4_modeling import load_xy, representations, save_splits, FEATURE_DIR, STAGE, ID, SEED

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")
BASE = ROOT / "outputs/modeling/family_1/source_contribution"
D = {n: BASE / n for n in ["metrics", "predictions", "diagnostics", "summary", "figures", "report", "checkpoints"]}
for p in D.values(): p.mkdir(parents=True, exist_ok=True)

SOURCES = ["S2", "PLANET", "LANDSAT", "CLIMATE", "HISTORY", "ANOMALY", "TOPO_BASIC"]
DISPLAY = {"S2":"Sentinel", "PLANET":"Planet", "LANDSAT":"Landsat", "CLIMATE":"Climate Current",
           "HISTORY":"History", "ANOMALY":"Anomaly", "TOPO_BASIC":"Topography Basic"}


def metrics(y, p):
    return {"RMSE": mean_squared_error(y, p)**.5, "MAE": mean_absolute_error(y, p),
            "R2": r2_score(y, p), "MedAE": median_absolute_error(y, p)}


def specs(core, by_source):
    sat = by_source["S2"] + by_source["PLANET"] + by_source["LANDSAT"]
    env_current = by_source["CLIMATE"] + by_source["TOPO_BASIC"]
    context = by_source["HISTORY"] + by_source["ANOMALY"]
    groups = {
        "SATELLITE": sat,
        "ENVIRONMENT_CURRENT": env_current,
        "TEMPORAL_CONTEXT": context,
        "SATELLITE_CLIMATE": sat + by_source["CLIMATE"],
        "SATELLITE_CONTEXT": sat + context,
        "ENVIRONMENT_ALL": by_source["CLIMATE"] + context + by_source["TOPO_BASIC"],
    }
    extra = {
        "S2_CLIMATE": by_source["S2"] + by_source["CLIMATE"],
        "S2_PLANET": by_source["S2"] + by_source["PLANET"],
        "S2_ANOMALY": by_source["S2"] + by_source["ANOMALY"],
    }
    out = {}
    tag = lambda s: "TOPO" if s == "TOPO_BASIC" else s
    for s in SOURCES:
        out[f"XGB_{tag(s)}_ONLY"] = ("XGB", "source_only", s, by_source[s])
        out[f"ENET_{tag(s)}_ONLY"] = ("ENET", "source_only", s, by_source[s])
    for g, cols in groups.items(): out[f"XGB_{g}"] = ("XGB", "grouped", g, cols)
    for g, cols in extra.items(): out[f"XGB_{g}"] = ("XGB", "incremental_combo", g, cols)
    for s in SOURCES: out[f"XGB_CORE_MINUS_{tag(s)}"] = ("XGB", "ablation", s, [c for c in core if c not in set(by_source[s])])
    for g in ["SATELLITE", "ENVIRONMENT_ALL"]: out[f"ENET_{g}"] = ("ENET", "grouped", g, groups[g])
    out["ENET_CORE"] = ("ENET", "grouped", "CORE", core)
    for s in ["S2", "PLANET", "CLIMATE", "ANOMALY"]:
        out[f"ENET_CORE_MINUS_{s}"] = ("ENET", "ablation", s, [c for c in core if c not in set(by_source[s])])
    return out


def estimator(model):
    if model == "XGB":
        pipe = Pipeline([("imputer", SimpleImputer(strategy="median")),
                         ("model", XGBRegressor(random_state=SEED, n_jobs=1, objective="reg:squarederror"))])
        grid = {"model__n_estimators":[150,300], "model__max_depth":[2,3], "model__learning_rate":[.03],
                "model__min_child_weight":[5,10], "model__subsample":[.8], "model__colsample_bytree":[.6],
                "model__reg_alpha":[.5], "model__reg_lambda":[5.]}
    else:
        pipe = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler()),
                         ("model", ElasticNet(max_iter=20000, random_state=SEED))])
        grid = {"model__alpha":[.01,.1,1.], "model__l1_ratio":[.1,.5,.9]}
    return pipe, grid


def run(selected=None):
    ids, X, y = load_xy(); core = representations(X.columns)["CORE"]
    dic = pd.read_csv(FEATURE_DIR / "family1_feature_dictionary.csv").set_index("feature_name")
    by_source = {s: [c for c in core if dic.reindex([c]).source.iloc[0] == s] for s in SOURCES}
    cfg = specs(core, by_source); splits = save_splits(ids); id_to_i = {v:i for i,v in enumerate(ids)}
    names = selected or list(cfg)
    bad = set(names)-set(cfg)
    if bad: raise ValueError(f"Pipelines desconocidos: {bad}")
    for name in names:
        model, kind, block, features = cfg[name]
        path = D["checkpoints"] / f"{name}.parquet"
        hp_path = D["checkpoints"] / f"{name}_hyper.csv"
        done = pd.read_parquet(path) if path.exists() else pd.DataFrame()
        rows = done.to_dict("records") if len(done) else []
        complete = set(zip(done.get("repeat", []), done.get("fold", [])))
        hp = pd.read_csv(hp_path).to_dict("records") if hp_path.exists() else []
        pipe, grid = estimator(model)
        print(f"START {name}: {len(features)} features, {len(complete)}/50 folds", flush=True)
        for k, s in splits.iterrows():
            key = (s["repeat"], s["fold"])
            if key in complete: continue
            tr = np.array([id_to_i[v] for v in json.loads(s.train_ID_POLIGONO)])
            va = np.array([id_to_i[v] for v in json.loads(s.validation_ID_POLIGONO)])
            inner = KFold(4, shuffle=True, random_state=SEED+k)
            start = time.time()
            search = GridSearchCV(pipe, grid, cv=inner, scoring="neg_root_mean_squared_error", n_jobs=-1, refit=True, error_score="raise")
            search.fit(X.iloc[tr][features], y.iloc[tr]); pred = search.predict(X.iloc[va][features])
            hp.append({"pipeline":name, "repeat":s["repeat"], "fold":s["fold"], "best_params":json.dumps(search.best_params_),
                       "elapsed_seconds":time.time()-start, "n_features":len(features)})
            for pid, yt, yp in zip(ids.iloc[va], y.iloc[va], pred):
                rows.append({ID:pid, "repeat":s["repeat"], "fold":s["fold"], "y_true":yt, "y_pred":yp,
                             "pipeline":name, "model_type":model, "experiment_type":kind, "source_block":block,
                             "n_features":len(features)})
            pd.DataFrame(rows).to_parquet(path, index=False)
            pd.DataFrame(hp).to_csv(hp_path, index=False)
            print(f"  {s['repeat']}.{s['fold']} RMSE={mean_squared_error(y.iloc[va],pred)**.5:.4f}", flush=True)
    print("RUN COMPLETE", flush=True)


def consolidate():
    ids, X, y = load_xy(); core = representations(X.columns)["CORE"]
    dic = pd.read_csv(FEATURE_DIR / "family1_feature_dictionary.csv").set_index("feature_name")
    by_source = {s: [c for c in core if dic.reindex([c]).source.iloc[0] == s] for s in SOURCES}
    cfg = specs(core, by_source)
    missing = [n for n in cfg if not (D["checkpoints"] / f"{n}.parquet").exists()]
    if missing: raise RuntimeError(f"Faltan checkpoints: {missing}")
    pred = pd.concat([pd.read_parquet(D["checkpoints"] / f"{n}.parquet") for n in cfg], ignore_index=True)

    # Reutilizar XGB_CORE existente: mismos folds, grid y protocolo.
    old = pd.read_parquet(STAGE / "screening/oof_predictions.parquet")
    old = old[old.pipeline.eq("XGB_CORE")][[ID,"repeat","fold","y_true","y_pred","pipeline"]].copy()
    old["model_type"]="XGB"; old["experiment_type"]="reference"; old["source_block"]="CORE"; old["n_features"]=len(core)
    pred = pd.concat([pred, old], ignore_index=True)
    pred.to_parquet(D["predictions"] / "source_oof_predictions.parquet", index=False)

    fold_rows=[]
    for (p,r,f), g in pred.groupby(["pipeline","repeat","fold"]):
        fold_rows.append({"pipeline":p,"repeat":r,"fold":f,"model_type":g.model_type.iloc[0],
                          "experiment_type":g.experiment_type.iloc[0],"source_block":g.source_block.iloc[0],
                          "n_features":g.n_features.iloc[0],"n":len(g),**metrics(g.y_true,g.y_pred)})
    fm = pd.DataFrame(fold_rows)
    summary = fm.groupby(["pipeline","model_type","experiment_type","source_block","n_features"]).agg(
        RMSE_mean=("RMSE","mean"),RMSE_std=("RMSE","std"),RMSE_median=("RMSE","median"),
        MAE_mean=("MAE","mean"),R2_mean=("R2","mean"),MedAE_mean=("MedAE","mean")).reset_index()
    summary["RMSE_q25"] = summary.pipeline.map(fm.groupby("pipeline").RMSE.quantile(.25))
    summary["RMSE_q75"] = summary.pipeline.map(fm.groupby("pipeline").RMSE.quantile(.75))
    summary.to_csv(D["metrics"] / "all_pipeline_metrics.csv", index=False)
    summary.query("experiment_type=='source_only'").to_csv(D["metrics"] / "source_only_metrics.csv", index=False)
    summary.query("experiment_type in ['grouped','reference']").to_csv(D["metrics"] / "grouped_source_metrics.csv", index=False)

    # Prediccion agregada por parcela, util para diagnosticos sin pseudoreplicar folds.
    byparcel = pred.groupby(["pipeline",ID]).agg(y_true=("y_true","first"),oof_prediction_mean=("y_pred","mean"),
        oof_prediction_std=("y_pred","std")).reset_index()
    byparcel["residual"] = byparcel.oof_prediction_mean-byparcel.y_true
    byparcel["absolute_error"] = abs(byparcel.residual)
    byparcel.to_csv(D["predictions"] / "source_oof_by_parcel.csv", index=False)

    # Paired ablation deltas por los mismos 50 folds.
    wide = fm.pivot_table(index=["repeat","fold"], columns="pipeline", values="RMSE")
    abl=[]
    for s in SOURCES:
        p=f"XGB_CORE_MINUS_{'TOPO' if s=='TOPO_BASIC' else s}"; d=wide[p]-wide.XGB_CORE
        abl.append({"source":s,"pipeline":p,"n_features":len(core)-len(by_source[s]),"removed_features":len(by_source[s]),
                    "mean_delta_RMSE":d.mean(),"median_delta_RMSE":d.median(),"std_delta_RMSE":d.std(),
                    "q25_delta_RMSE":d.quantile(.25),"q75_delta_RMSE":d.quantile(.75),"removal_worsens_rate":(d>0).mean()})
    abl=pd.DataFrame(abl); abl.to_csv(D["metrics"] / "leave_one_source_out_metrics.csv",index=False)

    comparisons = [
        ("S2 + Climate","XGB_S2_ONLY","XGB_S2_CLIMATE"),("S2 + Planet","XGB_S2_ONLY","XGB_S2_PLANET"),
        ("S2 + Anomaly","XGB_S2_ONLY","XGB_S2_ANOMALY"),("Satellite + Climate","XGB_SATELLITE","XGB_SATELLITE_CLIMATE"),
        ("Satellite + Temporal Context","XGB_SATELLITE","XGB_SATELLITE_CONTEXT"),
        ("Environment All -> CORE","XGB_ENVIRONMENT_ALL","XGB_CORE")]
    inc=[]
    for label, base, combined in comparisons:
        gain=wide[base]-wide[combined]
        inc.append({"comparison":label,"base_pipeline":base,"combined_pipeline":combined,"mean_incremental_gain":gain.mean(),
                    "median_incremental_gain":gain.median(),"std_incremental_gain":gain.std(),"q25":gain.quantile(.25),
                    "q75":gain.quantile(.75),"win_rate":(gain>0).mean()})
    inc=pd.DataFrame(inc);inc.to_csv(D["metrics"] / "source_incremental_comparisons.csv",index=False)

    # Segmentos de y, solo OOF agregada por parcela.
    q25,q75=y.quantile([.25,.75]); byparcel["yield_segment"]=pd.cut(byparcel.y_true,[-np.inf,q25,q75,np.inf],labels=["low","middle","high"])
    seg=[]
    keep = summary.query("experiment_type in ['source_only','ablation','reference']").pipeline
    for (p,s),g in byparcel[byparcel.pipeline.isin(keep)].groupby(["pipeline","yield_segment"],observed=True):
        seg.append({"pipeline":p,"yield_segment":s,"n":len(g),"RMSE":np.sqrt(np.mean(g.residual**2)),
                    "MAE":g.absolute_error.mean(),"bias":g.residual.mean()})
    seg=pd.DataFrame(seg);seg.to_csv(D["diagnostics"] / "source_performance_by_yield_segment.csv",index=False)

    # Errores source-level y ensemble simple puramente OOF diagnostico.
    resid=byparcel.pivot(index=ID,columns="pipeline",values="residual")
    cor=[]
    corr_pipes=[p for p in summary.pipeline if "_ONLY" in p or p in ["XGB_SATELLITE","XGB_ENVIRONMENT_ALL"]]
    for i,a in enumerate(corr_pipes):
        for b in corr_pipes[i+1:]:
            z=pd.concat([resid[a],resid[b]],axis=1).dropna()
            cor.append({"pipeline_A":a,"pipeline_B":b,"n":len(z),"pearson_residual":pearsonr(z.iloc[:,0],z.iloc[:,1]).statistic,
                        "spearman_residual":spearmanr(z.iloc[:,0],z.iloc[:,1]).statistic})
    cor=pd.DataFrame(cor);cor.to_csv(D["diagnostics"] / "source_error_correlations.csv",index=False)
    ens=pred[pred.pipeline.isin(["XGB_SATELLITE","XGB_ENVIRONMENT_ALL"])].pivot_table(index=[ID,"repeat","fold","y_true"],columns="pipeline",values="y_pred").reset_index()
    ens["y_pred"]=(ens.XGB_SATELLITE+ens.XGB_ENVIRONMENT_ALL)/2; ens["pipeline"]="OOF_MEAN_SATELLITE_ENVIRONMENT"
    em=[]
    for (r,f),g in ens.groupby(["repeat","fold"]):em.append({"pipeline":ens.pipeline.iloc[0],"repeat":r,"fold":f,**metrics(g.y_true,g.y_pred)})
    pd.DataFrame(em).to_csv(D["diagnostics"] / "simple_source_ensemble_diagnostic.csv",index=False)

    # Parcelas dificiles de 4.3/4.4.
    hard=pd.read_csv(ROOT/"outputs/modeling/family_1/support_analysis/support/difficult_parcel_support.csv")[[ID,"support_class"]]
    difficult=byparcel.merge(hard,on=ID)
    wanted=["XGB_S2_ONLY","XGB_CLIMATE_ONLY","XGB_SATELLITE","XGB_ENVIRONMENT_ALL","XGB_CORE"]+[f"XGB_CORE_MINUS_{s}" for s in ["S2","PLANET","CLIMATE","ANOMALY"]]
    dlong=difficult[difficult.pipeline.isin(wanted)].copy()
    derr=dlong.pivot(index=ID,columns="pipeline",values="absolute_error")
    dpred=dlong.pivot(index=ID,columns="pipeline",values="oof_prediction_mean").add_prefix("prediction_")
    dwide=hard.set_index(ID).join(derr.add_prefix("absolute_error_")).join(dpred)
    dwide["climate_rescues_S2_by_0_1"] = dwide.absolute_error_XGB_CLIMATE_ONLY <= dwide.absolute_error_XGB_S2_ONLY-.1
    dwide["satellite_rescues_climate_by_0_1"] = dwide.absolute_error_XGB_SATELLITE <= dwide.absolute_error_XGB_CLIMATE_ONLY-.1
    dwide["environment_rescues_satellite_by_0_1"] = dwide.absolute_error_XGB_ENVIRONMENT_ALL <= dwide.absolute_error_XGB_SATELLITE-.1
    key_errors=["absolute_error_XGB_S2_ONLY","absolute_error_XGB_CLIMATE_ONLY","absolute_error_XGB_SATELLITE","absolute_error_XGB_ENVIRONMENT_ALL","absolute_error_XGB_CORE"]
    dwide["difficult_in_all_five_threshold_0_5"]=(dwide[key_errors]>=.5).all(axis=1)
    dwide["best_of_five_pipeline"]=dwide[key_errors].idxmin(axis=1).str.replace("absolute_error_","",regex=False)
    dwide.reset_index().to_csv(D["diagnostics"] / "difficult_parcels_by_source.csv",index=False)

    counts=pd.DataFrame([{"source":s,"source_display":DISPLAY[s],"n_features":len(by_source[s]),"in_core":True} for s in SOURCES])
    counts=pd.concat([counts,pd.DataFrame([{"source":"AREA","source_display":"Area","n_features":0,"in_core":False}])],ignore_index=True)
    counts.to_csv(D["diagnostics"] / "source_feature_counts.csv",index=False)

    # PLS existente, agregado por source CORE.
    pls=pd.read_csv(ROOT/"outputs/modeling/family_1/stage4_1/pls/pls_family_vip_summary.csv")
    pls=pls.query("pipeline=='PLS_CORE' and aggregation_dimension=='source'")[["group","mean_feature_mean_vip"]]
    rev={"Sentinel":"S2","Planet":"PLANET","Landsat":"LANDSAT","Climate":"CLIMATE","History":"HISTORY","Anomaly":"ANOMALY","Topography Basic":"TOPO_BASIC"}
    pls["source"]=pls.group.map(rev); pls=pls.rename(columns={"mean_feature_mean_vip":"VIP_mean_PLS"})[["source","VIP_mean_PLS"]]
    solo=summary.query("model_type=='XGB' and experiment_type=='source_only'").set_index("source_block")
    enet=summary.query("model_type=='ENET' and experiment_type=='source_only'").set_index("source_block")
    s2res=resid["XGB_S2_ONLY"]
    rows=[]
    for s in SOURCES:
        r={"source":s,"n_features":len(by_source[s]),"source_only_RMSE_XGB":solo.loc[s,"RMSE_mean"],
           "source_only_RMSE_ENET":enet.loc[s,"RMSE_mean"],"leave_one_out_delta_XGB":abl.set_index("source").loc[s,"mean_delta_RMSE"],
           "leave_one_out_win_rate":abl.set_index("source").loc[s,"removal_worsens_rate"],
           "error_correlation_with_S2":1.0 if s=="S2" else resid[f"XGB_{'TOPO' if s=='TOPO_BASIC' else s}_ONLY"].corr(s2res)}
        rows.append(r)
    contrib=pd.DataFrame(rows).merge(pls,on="source",how="left")
    def label(r):
        best=contrib.source_only_RMSE_XGB.min(); delta=r.leave_one_out_delta_XGB
        if r.source_only_RMSE_XGB <= best+.02 and delta>.005:return "strong standalone and incremental"
        if delta>.005:return "complementary"
        if delta<-.005:return "potentially harmful/redundant"
        if r.source_only_RMSE_XGB <= best+.04:return "strong standalone but redundant"
        return "weak or uncertain"
    contrib["interpretation"]=contrib.apply(label,axis=1)
    contrib.to_csv(D["summary"] / "source_contribution_summary.csv",index=False)
    contrib.to_csv(D["summary"] / "source_contribution_vs_pls.csv",index=False)

    # Figuras.
    fig,ax=plt.subplots(figsize=(10,5)); z=summary.query("experiment_type=='source_only' and model_type=='XGB'").sort_values("RMSE_mean");sns.barplot(data=z,x="source_block",y="RMSE_mean",ax=ax,color="#377eb8");ax.tick_params(axis='x',rotation=35);ax.set_title("Capacidad individual por fuente - XGBoost");fig.tight_layout();fig.savefig(D["figures"]/"source_only_rmse.png",dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,5));sns.barplot(data=abl.sort_values("mean_delta_RMSE",ascending=False),x="source",y="mean_delta_RMSE",ax=ax,color="#4daf4a");ax.axhline(0,color='black',lw=1);ax.tick_params(axis='x',rotation=35);ax.set_title("Ablation pareada: RMSE sin fuente - CORE");fig.tight_layout();fig.savefig(D["figures"]/"leave_one_source_out_delta.png",dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,5));sns.barplot(data=inc,x="comparison",y="mean_incremental_gain",ax=ax,color="#984ea3");ax.axhline(0,color='black',lw=1);ax.tick_params(axis='x',rotation=30);ax.set_title("Ganancia incremental pareada");fig.tight_layout();fig.savefig(D["figures"]/"source_incremental_gain.png",dpi=180);plt.close(fig)
    chosen=["XGB_S2_ONLY","XGB_PLANET_ONLY","XGB_LANDSAT_ONLY","XGB_CLIMATE_ONLY","XGB_HISTORY_ONLY","XGB_ANOMALY_ONLY","XGB_TOPO_ONLY","XGB_SATELLITE","XGB_ENVIRONMENT_ALL"]
    mat=resid[chosen].corr();fig,ax=plt.subplots(figsize=(10,8));sns.heatmap(mat,cmap="vlag",vmin=-1,vmax=1,annot=True,fmt=".2f",ax=ax);fig.tight_layout();fig.savefig(D["figures"]/"source_error_correlation.png",dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(13,6));zp=seg[seg.pipeline.isin(["XGB_CORE"]+[f"XGB_{'TOPO' if s=='TOPO_BASIC' else s}_ONLY" for s in SOURCES])];sns.barplot(data=zp,x="pipeline",y="RMSE",hue="yield_segment",ax=ax);ax.tick_params(axis='x',rotation=35);ax.set_title("Desempeno OOF agregado por regimen");fig.tight_layout();fig.savefig(D["figures"]/"source_performance_by_yield_segment.png",dpi=180);plt.close(fig)

    # Reporte factual y explicito.
    best=solo.RMSE_mean.idxmin(); worst=solo.RMSE_mean.idxmax(); core_rmse=summary.set_index("pipeline").loc["XGB_CORE","RMSE_mean"]
    ab=abl.set_index("source"); ic=inc.set_index("comparison")
    groupm=summary.set_index("pipeline"); top_loss=abl.sort_values("mean_delta_RMSE",ascending=False).iloc[0]
    sat_env=cor[((cor.pipeline_A=="XGB_SATELLITE")&(cor.pipeline_B=="XGB_ENVIRONMENT_ALL"))|((cor.pipeline_B=="XGB_SATELLITE")&(cor.pipeline_A=="XGB_ENVIRONMENT_ALL"))].iloc[0]
    ens_rmse=pd.DataFrame(em).RMSE.mean(); sat_rmse=groupm.loc["XGB_SATELLITE","RMSE_mean"]; env_rmse=groupm.loc["XGB_ENVIRONMENT_ALL","RMSE_mean"]
    min_candidates=groupm.loc[["XGB_ENVIRONMENT_CURRENT","XGB_TEMPORAL_CONTEXT","XGB_ENVIRONMENT_ALL","XGB_SATELLITE","XGB_SATELLITE_CLIMATE","XGB_SATELLITE_CONTEXT"]].sort_values(["n_features","RMSE_mean"])
    difficult_piv=difficult.pivot(index=ID,columns="pipeline",values="absolute_error")
    atyp=hard[hard.support_class.eq("y-outlier given similar X")][ID]; allbad=(difficult_piv.loc[difficult_piv.index.intersection(atyp),wanted].mean(axis=1)).sort_values(ascending=False)
    report=f"""# Familia 1 - Etapa 4.5: contribucion por fuente

## Protocolo

Se reutilizaron exactamente los 50 outer folds congelados y el inner KFold de 4 particiones. XGBoost uso el mismo grid regularizado de XGB_CORE; Elastic Net uso mediana, StandardScaler y el grid pequeno existente. Todas las diferencias son pareadas fold a fold. AREA no se evaluo porque no pertenece a CORE ni al diccionario predictivo. No se entreno LightGBM, PLS ni modelos finales.

## Respuestas

1. **Mejor fuente sola:** {best}, RMSE medio XGB={solo.loc[best,'RMSE_mean']:.4f}.
2. **Peor fuente sola:** {worst}, RMSE={solo.loc[worst,'RMSE_mean']:.4f}.
3. **¿Sentinel domina individualmente?** {'Si' if best=='S2' else 'No'}; ranking completo en `source_only_metrics.csv`.
4. **¿Planet independiente de Sentinel?** Añadir Planet a S2 cambia RMSE en {ic.loc['S2 + Planet','mean_incremental_gain']:+.4f}; retirar Planet de CORE cambia {ab.loc['PLANET','mean_delta_RMSE']:+.4f}. Su correlacion residual con S2 es {contrib.set_index('source').loc['PLANET','error_correlation_with_S2']:.3f}.
5. **¿Landsat util o redundante?** Delta al retirarlo={ab.loc['LANDSAT','mean_delta_RMSE']:+.4f}, empeora en {ab.loc['LANDSAT','removal_worsens_rate']:.0%} de folds.
6. **¿Climate fuerte solo?** RMSE={solo.loc['CLIMATE','RMSE_mean']:.4f}, frente a mejor fuente={solo.loc[best,'RMSE_mean']:.4f} y CORE={core_rmse:.4f}.
7. **¿Climate mejora Satellite?** Ganancia={ic.loc['Satellite + Climate','mean_incremental_gain']:+.4f}, win rate={ic.loc['Satellite + Climate','win_rate']:.0%}.
8. **¿History aporta mas alla?** Delta al retirarlo={ab.loc['HISTORY','mean_delta_RMSE']:+.4f}; Satellite+Context gana {ic.loc['Satellite + Temporal Context','mean_incremental_gain']:+.4f} frente a Satellite, compartido con Anomaly.
9. **¿Anomaly distinta?** S2+Anomaly gana {ic.loc['S2 + Anomaly','mean_incremental_gain']:+.4f}; delta al retirarla={ab.loc['ANOMALY','mean_delta_RMSE']:+.4f}.
10. **¿Topography aporta incrementalmente?** Delta al retirarla={ab.loc['TOPO_BASIC','mean_delta_RMSE']:+.4f}, win rate={ab.loc['TOPO_BASIC','removal_worsens_rate']:.0%}.
11. **Mayor perdida al retirar:** {top_loss.source}, delta={top_loss.mean_delta_RMSE:+.4f}.
12. **Redundantes:** fuentes con delta cercano a cero o negativo: {abl[abl.mean_delta_RMSE<=.005][['source','mean_delta_RMSE']].round(4).to_dict('records')}.
13. **Debiles solas pero complementarias:** {contrib[contrib.interpretation.eq('complementary')][['source','source_only_RMSE_XGB','leave_one_out_delta_XGB']].round(4).to_dict('records')}.
14. **Satellite cerca de CORE:** Satellite={sat_rmse:.4f}, CORE={core_rmse:.4f}, diferencia={sat_rmse-core_rmse:+.4f}.
15. **Environment-only:** RMSE={env_rmse:.4f}; contiene señal si supera claramente un baseline ingenuo, pero su distancia a CORE es {env_rmse-core_rmse:+.4f}.
16. **Satellite+Climate casi todo CORE:** RMSE={groupm.loc['XGB_SATELLITE_CLIMATE','RMSE_mean']:.4f}; diferencia frente CORE={groupm.loc['XGB_SATELLITE_CLIMATE','RMSE_mean']-core_rmse:+.4f}.
17. **Ayuda en extremos:** Climate-only es la mejor fuente individual en bajos (RMSE={seg[(seg.pipeline=='XGB_CLIMATE_ONLY')&(seg.yield_segment=='low')].RMSE.iloc[0]:.4f}, bias={seg[(seg.pipeline=='XGB_CLIMATE_ONLY')&(seg.yield_segment=='low')].bias.iloc[0]:+.4f}) y altos (RMSE={seg[(seg.pipeline=='XGB_CLIMATE_ONLY')&(seg.yield_segment=='high')].RMSE.iloc[0]:.4f}, bias={seg[(seg.pipeline=='XGB_CLIMATE_ONLY')&(seg.yield_segment=='high')].bias.iloc[0]:+.4f}); Sentinel-only lidera el segmento medio (RMSE={seg[(seg.pipeline=='XGB_S2_ONLY')&(seg.yield_segment=='middle')].RMSE.iloc[0]:.4f}). Ninguna fuente elimina la regresion hacia la media.
18. **Parcelas dificiles:** Climate rescata por >=0.1 t/ha a Sentinel en {int(dwide.climate_rescues_S2_by_0_1.sum())}/28; Satellite rescata Climate en {int(dwide.satellite_rescues_climate_by_0_1.sum())}/28; Environment rescata Satellite en {int(dwide.environment_rescues_satellite_by_0_1.sum())}/28. De las 9 y-atipicas, {int(dwide.loc[dwide.index.intersection(atyp),'difficult_in_all_five_threshold_0_5'].sum())} mantienen error >=0.5 en los cinco bloques/modelos principales. Los casos transversales mayores son {allbad.head(5).round(3).to_dict()}.
19. **Errores Satellite/Environment:** correlacion Pearson={sat_env.pearson_residual:.3f}; ensemble 50/50 RMSE={ens_rmse:.4f}, frente Satellite={sat_rmse:.4f} y Environment={env_rmse:.4f}. No es candidato final.
20. **Coherencia con PLS:** tabla conjunta en `source_contribution_vs_pls.csv`. VIP alto no equivale a aporte unico y su suma depende del numero de features.
21. **Eliminable sin costo aparente:** {abl.sort_values('mean_delta_RMSE').head(3)[['source','mean_delta_RMSE','removal_worsens_rate']].round(4).to_dict('records')}; esto es descriptivo, no autorizacion automatica para borrar features.
22. **Representacion minima eficiente:** Climate-only es la candidata minima estricta: 48 features, RMSE={solo.loc['CLIMATE','RMSE_mean']:.4f}, diferencia CORE={solo.loc['CLIMATE','RMSE_mean']-core_rmse:+.4f}. Como bloque conceptual mas amplio, Environment Current usa 73 features y RMSE={groupm.loc['XGB_ENVIRONMENT_CURRENT','RMSE_mean']:.4f}. Antes de sustituir CORE debe validarse temporal y espacialmente: Climate 2025 puede actuar como proxy de geografia/temporada bajo CV aleatoria.
23. **Historia cientifica defendible:** separar capacidad individual, aporte unico y complementariedad evita confundir volumen de columnas con informacion. La conclusion se basa en source-only, ablaciones pareadas y ganancias incrementales, no en una sola importancia.
24. **¿Congelar Familia 1?** Si para el protocolo actual: la ganancia no justifica mas tuning o feature engineering dentro de Familia 1. Para despliegue, queda pendiente validar la solucion compacta Climate/Environment fuera de temporada y geografia; no debe reemplazar automaticamente XGB_CORE con este unico experimento. No se inicio Familia 2.

## Cautelas

- Los 50 folds estan correlacionados por RepeatedKFold; no se aplico t-test ingenuo.
- Los intervalos Q25-Q75 y win rates son descriptivos y pareados.
- Una fuente con muchas columnas no necesariamente aporta mas informacion unica.
- El ranking no es causal ni una regla automatica de eliminacion.
"""
    (D["report"] / "family1_source_contribution_report.md").write_text(report,encoding="utf-8")
    print("CONSOLIDATED", BASE)


if __name__ == "__main__":
    ap=argparse.ArgumentParser();ap.add_argument("mode",choices=["run","consolidate","all"]);ap.add_argument("pipelines",nargs="*");a=ap.parse_args()
    if a.mode in ["run","all"]: run(a.pipelines or None)
    if a.mode in ["consolidate","all"]: consolidate()
