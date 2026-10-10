"""Bloque A: investigación agroambiental y extremos de rendimiento.

Diagnóstico descriptivo reproducible. No modifica Champion V1 ni entrena un
modelo principal. Las asociaciones usan sólo las 138 parcelas TRAIN.
"""
from pathlib import Path
import json, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr, skew, rankdata
from sklearn.neighbors import NearestNeighbors

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid", context="notebook")
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/research/block_a_agroenvironmental"
TAB, FIG, REP = BASE / "tables", BASE / "figures", BASE / "report"
for p in (TAB, FIG, REP): p.mkdir(parents=True, exist_ok=True)
ID = "ID_POLIGONO"
RNG = np.random.default_rng(2026)


def rho(a, b):
    z = pd.DataFrame({"a": a, "b": b}).dropna()
    if len(z) < 8 or z.a.nunique() < 2 or z.b.nunique() < 2: return np.nan
    return float(spearmanr(z.a, z.b).statistic)


def boot_rho(a, b, n=399):
    z = pd.DataFrame({"a": a, "b": b}).dropna().reset_index(drop=True)
    est = rho(z.a, z.b)
    if len(z) < 8: return est, np.nan, np.nan
    vals = []
    aa=z.a.to_numpy(float); bb=z.b.to_numpy(float)
    for _ in range(n):
        ix=RNG.integers(0,len(z),len(z));ra=rankdata(aa[ix]);rb=rankdata(bb[ix])
        v=np.corrcoef(ra,rb)[0,1] if np.std(ra)>0 and np.std(rb)>0 else np.nan
        if np.isfinite(v): vals.append(v)
    lo, hi = np.quantile(vals, [.025, .975]) if vals else (np.nan, np.nan)
    return est, float(lo), float(hi)


def moran(x, xy, k=5, nperm=999):
    x = np.asarray(x, float); z = x - x.mean()
    nn = NearestNeighbors(n_neighbors=k + 1).fit(xy).kneighbors(return_distance=False)[:, 1:]
    W = np.zeros((len(x), len(x))); W[np.arange(len(x))[:, None], nn] = 1
    W = np.maximum(W, W.T)
    calc = lambda q: len(q) / W.sum() * (W * np.outer(q, q)).sum() / (q @ q)
    obs = calc(z); sims = np.array([calc(RNG.permutation(z)) for _ in range(nperm)])
    return obs, (np.sum(np.abs(sims) >= abs(obs)) + 1) / (nperm + 1), W.sum() / len(x)


def phenology_features(path, prefix, indices):
    d = pd.read_parquet(path)
    d = d[d["index"].isin(indices)].copy()
    d = d[d.observed_support_flag.eq("SUPPORTED")]
    rows = []
    for (pid, ix), g in d.groupby([ID, "index"]):
        g = g.sort_values("t"); t = g.t.to_numpy(float); v = g.smooth_value.to_numpy(float)
        der = g.first_derivative.to_numpy(float); peak = int(np.nanargmax(v))
        vmax, vmin = np.nanmax(v), np.nanmin(v); amp = vmax - vmin
        threshold = vmin + .5 * amp
        above = t[v >= threshold]
        rows.append({ID: pid,
            f"{prefix}_{ix}_auc": np.trapz(v, t) / max(t.max()-t.min(), 1),
            f"{prefix}_{ix}_peak": vmax,
            f"{prefix}_{ix}_peak_day": t[peak],
            f"{prefix}_{ix}_growth": np.nanmax(der),
            f"{prefix}_{ix}_decline": np.nanmin(der),
            f"{prefix}_{ix}_green_duration": above.max()-above.min() if len(above) else np.nan,
            f"{prefix}_{ix}_late_persistence": np.nanmean(v[t >= 150]) if np.any(t >= 150) else np.nan})
    if not rows: return pd.DataFrame(columns=[ID])
    return pd.DataFrame(rows).groupby(ID, as_index=False).first()


def heterogeneity_features(path, indices):
    d = pd.read_parquet(path)
    d = d[d["index"].isin(indices) & d.observed_support_flag.eq("SUPPORTED")]
    rows = []
    for (pid, ix, measure), g in d.groupby([ID, "index", "functional_measure"]):
        rows.append({ID: pid, f"S2_{ix}_{measure}_heterogeneity_mean": g.smooth_value.mean(),
                     f"S2_{ix}_{measure}_heterogeneity_peak": g.smooth_value.max()})
    return pd.DataFrame(rows).groupby(ID, as_index=False).first()


def main():
    # Frozen outcome/error backbone from F3.2.1.
    err = pd.read_csv(ROOT / "outputs/modeling/family_3/f3_2_1_structural_error_diagnostics/tables/02_parcel_error_master.csv")
    meta = pd.read_csv(ROOT / "data/original/01_tablas_maestras/ID_area_rendimiento_70_30_Reto_AgroCebada.csv")[[ID,"AREA_HA","RENDIMIENTO_T_HA","CONJUNTO"]]
    basic = pd.read_parquet(ROOT / "data/processed/family_1/features/topography_basic_features.parquet")
    adv = pd.read_parquet(ROOT / "data/processed/family_1/features/topography_advanced_features.parquet")
    climate = pd.read_parquet(ROOT / "data/processed/family_1/environment/climate_monthly_timeseries.parquet")
    climate = climate[(climate.year == 2025) & climate.month.between(4,10)].copy()
    cw = climate.groupby(ID).agg(
        precip_cycle_sum=("precip_mean","sum"), precip_early_sum=("precip_mean",lambda x: x.iloc[:3].sum()),
        precip_late_sum=("precip_mean",lambda x: x.iloc[3:].sum()), tmax_cycle_mean=("tmax_mean","mean"),
        tmax_cycle_max=("tmax_mean","max"), tmin_cycle_mean=("tmin_mean","mean"),
        dtr_cycle_mean=("dtr_mean","mean")).reset_index()
    s2 = phenology_features(ROOT/"data/processed/family_2/functions/sentinel_smooth_weekly_grid.parquet", "S2", ["ndvi","evi","lai","fapar","ndwi","dswi4"])
    pl = phenology_features(ROOT/"data/processed/family_2/functions/planet_smooth_weekly_grid.parquet", "PL", ["ndvi","evi","lai"])
    het = heterogeneity_features(ROOT/"data/processed/family_2/functions/sentinel_heterogeneity_smooth_weekly_grid.parquet", ["ndvi","evi","lai","fapar","ndwi","dswi4"])
    master = err.merge(meta, on=ID, how="left").merge(basic,on=ID,how="left").merge(adv,on=ID,how="left").merge(cw,on=ID,how="left").merge(s2,on=ID,how="left").merge(pl,on=ID,how="left").merge(het,on=ID,how="left")
    assert len(master) == 138 and master.RENDIMIENTO_T_HA.notna().all()
    q1, q3 = master.y_true.quantile([.25,.75]); master["yield_group_A"] = np.select([master.y_true<=q1,master.y_true>=q3],["LOW","HIGH"],"MID")

    # Spatial metadata and local relative elevation (context, not watershed).
    import geopandas as gpd
    geo = gpd.read_file(ROOT/"data/original/02_conjunto_70_30/Parcelas_Reto_AGC_CONJUNTO.shp").to_crs(6372)
    geo[ID] = geo.ID_POLIGON.astype(str); geo = geo.merge(master[[ID]],on=ID)
    xy = np.c_[geo.geometry.centroid.x,geo.geometry.centroid.y]
    master = master.merge(pd.DataFrame({ID:geo[ID],"centroid_x_m":xy[:,0],"centroid_y_m":xy[:,1]}),on=ID)
    nn = NearestNeighbors(n_neighbors=6).fit(xy).kneighbors(return_distance=False)[:,1:]
    elev = master.set_index(ID).loc[geo[ID],"TOPO_BASIC_elevation_mean"].to_numpy()
    rel = elev - np.array([elev[j].mean() for j in nn])
    master = master.merge(pd.DataFrame({ID:geo[ID],"elevation_minus_5nn_mean_m":rel}),on=ID)
    master.to_csv(TAB/"01_parcel_master_auditable.csv",index=False)

    # Variable catalog with provenance and interpretation safeguards.
    variables = {
      "AREA_HA":("Master FIRA","Área parcelaria","ha","context"),
      "TOPO_BASIC_slope_mean":("DEM FIRA","Pendiente media interna","DEM-derived","topography"),
      "TOPO_BASIC_slope_max":("DEM FIRA","Pendiente máxima interna","DEM-derived","topography"),
      "TOPO_BASIC_slope_std":("DEM FIRA","Dispersión de pendiente","DEM-derived","ruggedness"),
      "TOPO_BASIC_elevation_relief":("DEM FIRA","Rango vertical interno","m","ruggedness"),
      "TOPO_BASIC_elevation_std":("DEM FIRA","Dispersión de elevación","m","ruggedness"),
      "TOPO_ADV_local_relief_3x3_mean":("DEM derivado","Relieve local 3x3","DEM-derived","ruggedness"),
      "TOPO_ADV_tpi_3x3_mean":("DEM derivado","Posición topográfica local; no cuenca","DEM-derived","topographic_position"),
      "TOPO_ADV_twi_mean":("DEM derivado","Potencial topográfico de humedad; no humedad medida","index","potential_wetness"),
      "TOPO_ADV_twi_q90":("DEM derivado","Cola alta de TWI intraparcela","index","potential_wetness"),
      "TOPO_ADV_flow_accumulation_log1p_mean":("DEM derivado","Acumulación D8 potencial log1p","index","potential_flow"),
      "TOPO_ADV_flow_accumulation_pct_above_regional_q90":("DEM derivado","Fracción en acumulación regional alta","fraction","potential_flow"),
      "TOPO_ADV_plan_curvature_mean":("DEM derivado","Curvatura de plano","DEM-derived","curvature"),
      "TOPO_ADV_profile_curvature_mean":("DEM derivado","Curvatura de perfil","DEM-derived","curvature"),
      "elevation_minus_5nn_mean_m":("Derivado Bloque A","Elevación vs 5 centroides vecinos; no aportación hidrológica","m","context"),
      "precip_cycle_sum":("CHIRPS FIRA","Precipitación mensual abril-octubre sumada","mm","climate"),
      "precip_early_sum":("CHIRPS FIRA","Precipitación mensual abril-junio sumada","mm","climate"),
      "tmax_cycle_mean":("Temperatura FIRA","Tmax mensual media abril-octubre","°C","climate"),
      "tmax_cycle_max":("Temperatura FIRA","Máxima de resúmenes mensuales; no extremo diario","°C","climate"),
    }
    for c in master.columns:
        if c.startswith(("S2_","PL_")) and c not in variables:
            src="Sentinel suavizado" if c.startswith("S2_") else "Planet suavizado"
            variables[c]=(src,"Descriptor de trayectoria satelital estimada","index-dependent","phenology" if "heterogeneity" not in c else "heterogeneity")
    catalog=pd.DataFrame([{"variable":k,"source":v[0],"definition":v[1],"unit":v[2],"domain":v[3],"predeclared":True} for k,v in variables.items() if k in master])
    catalog.to_csv(TAB/"02_variable_catalog.csv",index=False)

    # Predeclared association battery; continuous Y and residual outcomes.
    candidates = catalog.variable.tolist()
    outcomes = ["y_true","residual_mean","mean_absolute_error"]
    assoc=[]
    keep=~master.top10_SSE.astype(bool)
    for v in candidates:
        for out in outcomes:
            est,lo,hi=boot_rho(master[v],master[out])
            assoc.append({"variable":v,"outcome":out,"n":master[[v,out]].dropna().shape[0],"spearman":est,"ci95_low":lo,"ci95_high":hi,
                          "spearman_without_top10_SSE":rho(master.loc[keep,v],master.loc[keep,out]),"domain":dict(zip(catalog.variable,catalog.domain))[v]})
    assoc=pd.DataFrame(assoc);assoc.to_csv(TAB/"03_associations_bootstrap.csv",index=False)

    # Group effect sizes LOW vs HIGH, using pooled SD; continuous analysis remains primary.
    effects=[]
    for v in candidates:
        lo=master.loc[master.yield_group_A.eq("LOW"),v].dropna(); hi=master.loc[master.yield_group_A.eq("HIGH"),v].dropna()
        pool=np.sqrt(((len(lo)-1)*lo.var()+(len(hi)-1)*hi.var())/max(len(lo)+len(hi)-2,1))
        effects.append({"variable":v,"n_low":len(lo),"n_high":len(hi),"low_mean":lo.mean(),"high_mean":hi.mean(),"standardized_high_minus_low":(hi.mean()-lo.mean())/pool if pool>0 else np.nan})
    pd.DataFrame(effects).to_csv(TAB/"04_extreme_group_effects.csv",index=False)

    # Spatial sensitivity: 4/5/8 symmetric KNN.
    spatial=[]
    ordered=master.set_index(ID).loc[geo[ID]]
    for k in [4,5,8]:
        for v in ["y_true","residual_mean","mean_absolute_error"]:
            I,p,nbr=moran(ordered[v],xy,k)
            spatial.append({"variable":v,"k":k,"Moran_I":I,"permutation_p":p,"mean_neighbors_after_symmetry":nbr})
    pd.DataFrame(spatial).to_csv(TAB/"05_spatial_sensitivity.csv",index=False)

    # Four explicitly defined interactions, tested as descriptive product terms.
    defs=[
      ("H1_temperature_x_vigor","tmax_cycle_mean","S2_ndvi_auc"),
      ("H2_early_rain_x_growth","precip_early_sum","S2_ndvi_growth"),
      ("H3_rain_x_potential_wetness","precip_cycle_sum","TOPO_ADV_twi_mean"),
      ("H4_temperature_x_persistence","tmax_cycle_mean","S2_ndvi_late_persistence")]
    interactions=[]
    for name,a,b in defs:
        za=(master[a]-master[a].mean())/master[a].std();zb=(master[b]-master[b].mean())/master[b].std();prod=za*zb
        for out in outcomes:
            est,lo,hi=boot_rho(prod,master[out])
            interactions.append({"hypothesis":name,"variable_a":a,"variable_b":b,"outcome":out,"n":prod.notna().sum(),"spearman_product":est,"ci95_low":lo,"ci95_high":hi,"status":"descriptive_not_incrementally_validated"})
    inter=pd.DataFrame(interactions);inter.to_csv(TAB/"06_predeclared_interactions.csv",index=False)

    # Yield anatomy and error concentration.
    desc=master.y_true.describe(percentiles=[.01,.05,.1,.25,.5,.75,.9,.95,.99]).to_frame("value")
    desc.loc["skewness","value"]=skew(master.y_true);desc.to_csv(TAB/"07_yield_distribution.csv")
    conc=master.sort_values("mean_residual_squared",ascending=False)[[ID,"y_true","prediction_mean","residual_mean","mean_absolute_error","mean_residual_squared","yield_group_A","difficult","y_atypical"]].copy()
    conc["cumulative_SSE_fraction"]=conc.mean_residual_squared.cumsum()/conc.mean_residual_squared.sum();conc.to_csv(TAB/"08_error_concentration.csv",index=False)

    # Signal catalog classification is conservative: association != validated increment.
    ay=assoc[assoc.outcome.eq("y_true")].set_index("variable");ae=assoc[assoc.outcome.eq("residual_mean")].set_index("variable")
    sig=[]
    for v in candidates:
        ry=ay.loc[v,"spearman"]; re=ae.loc[v,"spearman"]; stable=abs(ay.loc[v,"spearman_without_top10_SSE"]-ry)<.10
        cls="señal explicativa exploratoria" if abs(ry)>=.20 and stable else "señal no confirmada"
        if abs(ry)>=.20 and abs(re)<.10: cls="probablemente redundante con Champion"
        sig.append({"variable":v,"source":variables[v][0],"agronomic_meaning":variables[v][1],"rho_yield":ry,"rho_champion_residual":re,
                    "robust_without_top_error":stable,"classification":cls,"incremental_predictive_evidence":"none_from_Block_A; requires nested CV",
                    "methodological_risk":"association; no causality; satellite phenology/topographic moisture are inferred"})
    signals=pd.DataFrame(sig).sort_values("rho_yield",key=lambda x:x.abs(),ascending=False);signals.to_csv(TAB/"09_signal_catalog.csv",index=False)

    make_figures(master, geo, assoc, inter)
    make_report(master, assoc, inter, pd.DataFrame(spatial), signals, q1, q3)
    manifest={"train_parcels":138,"prediction_parcels_excluded_from_supervised_analysis":59,"yield_unit":"t/ha","residual_definition":"y_true - Champion OOF prediction mean",
      "champion_oof":"outputs/modeling/residual_signal_audit/stage6_architecture_optimization/predictions/oof_predictions.parquet via frozen F3.2.1 master",
      "validation":"descriptive bootstrap; no new principal model; prior F3.2 nested results reused","seed":2026,
      "limitations":["monthly climate cannot resolve daily events","TWI/flow are potential terrain indices, not measured soil moisture","5NN relative elevation is not a watershed","satellite phenology is not field-observed phenology","parcel aggregates cannot locate within-field patches"]}
    (BASE/"block_a_manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    print(f"Bloque A completo: {BASE}")


def make_figures(m, geo, assoc, inter):
    fig,ax=plt.subplots(1,2,figsize=(11,4));sns.histplot(m.y_true,kde=True,ax=ax[0]);ax[0].set(xlabel="Rendimiento (t/ha)",title="Distribución de rendimiento TRAIN")
    sns.histplot(m.residual_mean,kde=True,ax=ax[1]);ax[1].set(xlabel="Residuo OOF y−ŷ (t/ha)",title="Error firmado del Champion");fig.tight_layout();fig.savefig(FIG/"01_yield_and_residual_distribution.png",dpi=180);plt.close(fig)
    fig,ax=plt.subplots(1,2,figsize=(11,4));sns.scatterplot(m,x="y_true",y="residual_mean",hue="yield_group_A",ax=ax[0]);ax[0].axhline(0,color="k",ls="--");ax[0].set(xlabel="Rendimiento (t/ha)",ylabel="Residuo y−ŷ (t/ha)")
    z=m.sort_values("mean_residual_squared",ascending=False);ax[1].plot(np.arange(1,len(z)+1),z.mean_residual_squared.cumsum()/z.mean_residual_squared.sum());ax[1].set(xlabel="Parcelas ordenadas",ylabel="Fracción acumulada SSE",title="Concentración del error");fig.tight_layout();fig.savefig(FIG/"02_error_anatomy.png",dpi=180);plt.close(fig)
    gm=geo.merge(m,on=ID)
    fig,ax=plt.subplots(1,2,figsize=(12,5));gm.plot(column="y_true",cmap="viridis",legend=True,ax=ax[0],edgecolor=".5",linewidth=.2);ax[0].set_title("Rendimiento observado (t/ha)");gm.plot(column="residual_mean",cmap="coolwarm",legend=True,ax=ax[1],edgecolor=".5",linewidth=.2);ax[1].set_title("Residuo OOF y−ŷ (t/ha)");[a.set_axis_off() for a in ax];fig.tight_layout();fig.savefig(FIG/"03_maps_yield_residual.png",dpi=180);plt.close(fig)
    topo=["TOPO_BASIC_slope_mean","TOPO_BASIC_elevation_relief","TOPO_ADV_twi_mean","TOPO_ADV_flow_accumulation_log1p_mean","TOPO_ADV_tpi_3x3_mean","elevation_minus_5nn_mean_m"]
    fig,ax=plt.subplots(2,3,figsize=(14,8));
    for a,v in zip(ax.flat,topo):sns.scatterplot(m,x=v,y="y_true",hue="yield_group_A",legend=False,ax=a);a.set_ylabel("Rendimiento (t/ha)")
    fig.suptitle("Relieve e hidrología potencial: asociaciones descriptivas");fig.tight_layout();fig.savefig(FIG/"04_topography_yield.png",dpi=180);plt.close(fig)
    curves=pd.read_parquet(ROOT/"data/processed/family_2/functions/sentinel_smooth_weekly_grid.parquet");curves=curves[curves["index"].isin(["ndvi","evi","lai","fapar"])].merge(m[[ID,"yield_group_A"]],on=ID)
    fig,ax=plt.subplots(2,2,figsize=(13,8));
    for a,(ix,g) in zip(ax.flat,curves.groupby("index")):
        q=g.groupby(["yield_group_A","date"]).smooth_value.agg(["mean","sem"]).reset_index()
        for seg,h in q.groupby("yield_group_A"):a.plot(pd.to_datetime(h.date),h["mean"],label=seg);a.fill_between(pd.to_datetime(h.date),h["mean"]-1.96*h["sem"],h["mean"]+1.96*h["sem"],alpha=.15)
        a.set_title(ix.upper());a.set_ylabel("Índice suavizado");a.tick_params(axis="x",rotation=30)
    ax[0,0].legend();fig.suptitle("Trayectorias Sentinel por cuartiles de rendimiento (media ±1.96 SE descriptivo)");fig.tight_layout();fig.savefig(FIG/"05_phenology_by_yield.png",dpi=180);plt.close(fig)
    fig,ax=plt.subplots(1,2,figsize=(11,4));sns.scatterplot(m,x="S2_ndvi_std_heterogeneity_mean",y="y_true",hue="yield_group_A",ax=ax[0]);sns.scatterplot(m,x="S2_ndvi_std_heterogeneity_mean",y="residual_mean",hue="yield_group_A",ax=ax[1]);ax[0].set_ylabel("Rendimiento (t/ha)");ax[1].set_ylabel("Residuo OOF (t/ha)");fig.suptitle("Heterogeneidad intraparcela NDVI: dispersión agregada, no mapa de parches");fig.tight_layout();fig.savefig(FIG/"06_heterogeneity.png",dpi=180);plt.close(fig)
    top=assoc[assoc.outcome.eq("y_true")].assign(a=lambda x:x.spearman.abs()).nlargest(20,"a").sort_values("spearman")
    plt.figure(figsize=(8,7));plt.errorbar(top.spearman,np.arange(len(top)),xerr=[top.spearman-top.ci95_low,top.ci95_high-top.spearman],fmt="o");plt.yticks(np.arange(len(top)),top.variable);plt.axvline(0,color="k",lw=.8);plt.xlabel("Spearman con rendimiento (IC bootstrap 95%)");plt.tight_layout();plt.savefig(FIG/"07_top_yield_associations.png",dpi=180);plt.close()
    fig,ax=plt.subplots(2,2,figsize=(12,9));pairs=[("tmax_cycle_mean","S2_ndvi_auc"),("precip_early_sum","S2_ndvi_growth"),("precip_cycle_sum","TOPO_ADV_twi_mean"),("tmax_cycle_mean","S2_ndvi_late_persistence")]
    for a,(x,y) in zip(ax.flat,pairs):sns.scatterplot(m,x=x,y=y,hue="y_true",palette="viridis",ax=a);a.legend(title="Y t/ha",fontsize=7)
    fig.suptitle("Interacciones predefinidas: color indica rendimiento, no causalidad");fig.tight_layout();fig.savefig(FIG/"08_climate_vegetation_topography_interactions.png",dpi=180);plt.close(fig)


def make_report(m, assoc, inter, spatial, signals, q1, q3):
    topy=assoc[assoc.outcome.eq("y_true")].assign(a=lambda x:x.spearman.abs()).nlargest(10,"a")
    tope=assoc[assoc.outcome.eq("residual_mean")].assign(a=lambda x:x.spearman.abs()).nlargest(10,"a")
    topo_domains=['topography','ruggedness','potential_wetness','potential_flow','topographic_position','curvature','context']
    top_topo=assoc[assoc.outcome.eq("y_true") & assoc.domain.isin(topo_domains)].assign(a=lambda x:x.spearman.abs()).nlargest(8,"a")
    n50=(m.sort_values("mean_residual_squared",ascending=False).mean_residual_squared.cumsum()/m.mean_residual_squared.sum() < .5).sum()+1
    low=m[m.yield_group_A.eq("LOW")];high=m[m.yield_group_A.eq("HIGH")]
    mor=spatial[spatial.k.eq(5)].round(4).to_dict("records")
    hypotheses=[
      ["A1 Regresión hacia la media",f"Bias LOW={low.residual_mean.mean():+.3f}; HIGH={high.residual_mean.mean():+.3f} t/ha","Direcciones opuestas en extremos","OOF 10 repeticiones; descriptivo","Consistente con F3.2.1","No causal","Respaldada por los datos"],
      ["A1 Concentración del error",f"{n50} parcelas acumulan ≥50% del SSE","Concentración fuerte","Sensible a casos individuales","Confirmada con ranking SSE","Extremos Y y error no son equivalentes","Respaldada por los datos"],
      ["A2 Relieve/hidrología potencial",f"Mayores asociaciones: {top_topo[['variable','spearman']].head(4).round(3).to_dict('records')}","Ver rho e IC","Bootstrap + sensibilidad top-SSE","Exploratoria","TWI/flujo no son humedad medida","Evidencia parcial o exploratoria"],
      ["A3 Fenología/vigor",f"Mayores asociaciones: {topy[topy.domain.eq('phenology')][['variable','spearman']].head(5).round(3).to_dict('records')}","Ver rho e IC","Bootstrap + comparación continua","Consistente sólo si no depende de top-SSE","Eventos satelitales, no etapas reales","Evidencia parcial o exploratoria"],
      ["A3 Heterogeneidad",f"Mayores asociaciones: {topy[topy.domain.eq('heterogeneity')][['variable','spearman']].head(4).round(3).to_dict('records')}","Ver rho e IC","Agregados std/range","No localiza parches","No hay píxeles internos persistidos aquí","Evidencia parcial o exploratoria"],
      ["A4 Interacciones",f"Productos predefinidos: {inter[inter.outcome.eq('y_true')][['hypothesis','spearman_product']].round(3).to_dict('records')}","Asociaciones descriptivas","IC bootstrap","F3.2 no halló ganancia estable de interacciones estructurales","Clima mensual","Sin evidencia suficiente"],
      ["A5 Incremento frente Champion",f"Top asociaciones residuales: {tope[['variable','spearman']].head(5).round(3).to_dict('records')}","Débil/moderado según tabla","No es validación predictiva","F3.2: M1≈M0; interacciones peores","No corregir OOF retrospectivamente","Sin evidencia suficiente"]]
    hdf=pd.DataFrame(hypotheses,columns=["Hipótesis","Evidencia observada","Tamaño/dirección del efecto","Incertidumbre","Estabilidad","Interpretación","Veredicto"]);hdf.to_csv(TAB/"10_hypothesis_evidence.csv",index=False)
    md_header="| "+" | ".join(hdf.columns)+" |\n|"+"|".join(["---"]*len(hdf.columns))+"|"
    md_rows="\n".join("| "+" | ".join(str(v).replace("|","/") for v in row)+" |" for row in hdf.itertuples(index=False,name=None))
    hypothesis_md=md_header+"\n"+md_rows
    txt=f"""# Bloque A — Investigación agroambiental y rendimientos extremos

## Resumen ejecutivo

El análisis usa **138 parcelas TRAIN** y excluye las 59 parcelas sin rendimiento de toda asociación supervisada. Champion V1 se conserva congelado; el residuo es `y − predicción OOF media`. Los extremos se definieron por Q25={q1:.3f} y Q75={q3:.3f} t/ha, manteniendo Y continuo como análisis principal.

El hallazgo más sólido sigue siendo la **regresión hacia la media**: el Champion sobreestima el cuartil bajo (residuo medio {low.residual_mean.mean():+.3f}) y subestima el alto ({high.residual_mean.mean():+.3f} t/ha). {n50} parcelas concentran al menos 50% del SSE. Los extremos reales de Y, las parcelas atípicas y los extremos de error se reportan separadamente.

Las variables de relieve, hidrología potencial y trayectorias vegetativas muestran asociaciones exploratorias que deben leerse con sus intervalos bootstrap y sensibilidad a las parcelas dominantes. Ninguna asociación se interpreta causalmente. El diagnóstico F3.2 previamente validado no encontró una mejora estable al condicionar el corrector climático con A1/E3 ni con interacciones; por ello Bloque A **no declara señal predictiva incremental validada**.

## Datos y auditoría

- Universo: 197 parcelas FIRA; 138 TRAIN con Y y 59 PREDICTION excluidas del análisis supervisado.
- Y: rendimiento reportado en t/ha, sin fecha individual de cosecha disponible.
- OOF: 10 predicciones por parcela del Champion congelado, agregadas en F3.2.1.
- Topografía: elevación/pendiente y derivados avanzados sobre DEM entregado: relieve local, TPI, curvaturas, acumulación D8 y TWI.
- Fenología: curvas suavizadas de abril–octubre 2025. NDVI/EVI/LAI/FAPAR son señales remotas; máximos y cambios no se renombran como espigamiento, emergencia o cosecha.
- Clima: resúmenes mensuales espacialmente asignados a cada parcela; no permiten detectar heladas, olas de calor o tormentas diarias.
- Documentación FIRA local describe los campos, pero no aporta una ficha oficial completa con ecuaciones espectrales para todos los índices. Se conservan nombres originales y no se rederivan índices.

## A1 — Anatomía del rendimiento y errores

La tabla `07_yield_distribution.csv` contiene cuantiles y asimetría. LOW/MID/HIGH son descriptivos (cuartiles), no clases agronómicas. Moran con vecindad simétrica de 5 centroides: {mor}; la sensibilidad k=4,5,8 está en `05_spatial_sensitivity.csv`. Autocorrelación no implica un mecanismo causal.

El patrón residual dominante es compresión/calibración: bajos sobreestimados, altos subestimados, y SSE concentrado en pocos casos. Los mapas permiten inspección zonal, pero no justifican atribuir causas locales.

## A2 — Topografía, rugosidad e hidrología potencial

Se evaluaron pendiente, relieve interno, rugosidad local, TPI, curvaturas, TWI y acumulación D8. Las asociaciones más grandes con Y son: {top_topo[['variable','spearman','ci95_low','ci95_high','spearman_without_top10_SSE']].round(3).to_dict('records')}.

`elevation_minus_5nn_mean_m` sólo indica posición relativa frente a centroides vecinos; **no delimita una cuenca aportante** ni demuestra escorrentía desde parcelas contiguas. TWI y flow accumulation representan potencial geomorfológico, no humedad observada ni anegamiento. Sin humedad de suelo, drenaje/edafología y un DEM hidrológicamente validado más allá del recorte, drenaje favorable, captación y anegamiento sólo son hipótesis parciales.

## A3 — Fenología, vigor y heterogeneidad

Las curvas por cuartil muestran perfiles medios con incertidumbre descriptiva. Los descriptores con mayor asociación continua son: {topy[topy.domain.isin(['phenology','heterogeneity'])][['variable','spearman','ci95_low','ci95_high','spearman_without_top10_SSE']].head(10).round(3).to_dict('records')}.

Se distinguen nivel/AUC, máximo, timing, crecimiento, declive, duración sobre el 50% de amplitud y persistencia tardía. Son descriptores matemáticos de curvas suavizadas, no fechas fenológicas de campo. Sentinel y Planet permanecen separados. Las dispersiones std/range resumen heterogeneidad intraparcela, pero no permiten localizar parches ni seguir su geometría.

La redundancia ya documentada en F2.2 es alta entre NDVI–EVI–LAI–FAPAR y entre varias señales de humedad. Por tanto, no se recomienda trasladar indiscriminadamente todos los descriptores a un modelo.

## A4 — Interacciones clima–vegetación–topografía

Se fijaron cuatro productos antes de comparar: temperatura×vigor, lluvia temprana×crecimiento, lluvia×TWI y temperatura×persistencia. Resultados: {inter[inter.outcome.eq('y_true')][['hypothesis','spearman_product','ci95_low','ci95_high']].round(3).to_dict('records')}.

Son asociaciones descriptivas. Las ventanas son abril–junio (temprana) y abril–octubre (ciclo), no etapas observadas. El experimento F3.2, más fuerte por validación nested, mostró que las interacciones A1/E3 no mejoraron de forma estable el corrector climático; esto pesa más que un patrón visual retrospectivo.

## A5 — Evidencia, estabilidad y utilidad predictiva

La tabla de hipótesis completa es:

{hypothesis_md}

No se ajustó una corrección sobre residuos OOF completos. Las correlaciones residuales sólo generan hipótesis. Una señal será “predictiva incremental” únicamente si mejora el Champion mediante transformaciones ajustadas dentro de cada fold y con estabilidad entre repeticiones, extremos y espacio.

## Recomendaciones

1. Continuar con un conjunto **muy compacto**: un descriptor de vigor/duración no redundante, uno de heterogeneidad, TWI/flow y rugosidad, sólo si sus asociaciones conservan dirección sin top-SSE.
2. Someterlos a un único experimento nested preespecificado contra Champion; no hacer búsqueda masiva ni selección usando estos mismos resultados.
3. No promover diferencias de elevación a “captación de agua”; para Bloque B se requiere delimitación de cuencas/flujo exterior, suelo (textura, profundidad, drenaje), humedad observada y manejo.
4. ENA/Censo servirían como contexto municipal/estatal de manejo y tecnología, no como etiqueta parcelaria. DGSIAP puede aportar contexto productivo regional. Cartografía edafológica debe integrarse por intersección espacial parcela–unidad de suelo y conservar incertidumbre/escala.
5. Datos realmente resolutivos: fecha de siembra/cosecha por parcela, variedad, riego, fertilización, incidencia sanitaria, humedad del suelo y rendimiento histórico parcelario. No se descargó ninguna fuente externa.

## Conclusión

Hay evidencia defendible de compresión de extremos y concentración del error. Existen señales agroambientales exploratorias, pero con 138 parcelas y alta redundancia no se demuestra todavía un mecanismo causal ni una mejora incremental. Las interacciones no quedan respaldadas para incorporación automática. El Bloque B debe priorizar suelo, manejo y fenología de campo con unidad espacial compatible, no ampliar indiscriminadamente el feature space.
"""
    (REP/"block_a_technical_report.md").write_text(txt,encoding="utf-8")


if __name__ == "__main__": main()
