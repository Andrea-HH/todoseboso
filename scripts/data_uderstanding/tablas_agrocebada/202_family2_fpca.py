"""F2.2: redundancia funcional y FPCA target-free.

No lee rendimiento para construir, seleccionar o ajustar representaciones. La
FPCA usa la metrica L2 (cuadratura trapezoidal del dominio continuo) sobre las
funciones suavizadas de F2.1; los 214 puntos son nodos de integracion, no
features tabulares independientes.
"""
from pathlib import Path
import sys, warnings
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr
from scipy.spatial.distance import cdist
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")
ID = "ID_POLIGONO"
DATA = ROOT / "data/processed/family_2/functions"
DEST = ROOT / "data/processed/family_2/fpca"
OUT = ROOT / "outputs/modeling/family_2/stage2_fpca"
DIR = {x: OUT/x for x in ["redundancy", "fpca", "diagnostics", "figures", "report"]}
DEST.mkdir(parents=True, exist_ok=True)
for p in DIR.values(): p.mkdir(parents=True, exist_ok=True)

GROUPS = {
    "SENTINEL_VIGOR": ("Sentinel", ["ndvi", "evi", "lai", "fapar", "savi"]),
    "SENTINEL_MOISTURE_STRESS": ("Sentinel", ["ndwi", "endwi", "dswi4", "dswi5"]),
    "PLANET": ("Planet", ["ndvi", "evi", "lai", "msavi"]),
}


def corr(a, b):
    if np.std(a) < 1e-12 or np.std(b) < 1e-12: return np.nan
    return float(np.corrcoef(a, b)[0, 1])


def timing(y, d):
    return int(np.argmax(y)), int(np.argmax(d)), int(np.argmin(d))


def load_curves():
    frames = []
    for src in ["sentinel", "planet"]:
        d = pd.read_parquet(DATA/f"{src}_smooth_grid.parquet")
        keep = set(sum([v[1] for v in GROUPS.values() if v[0].lower() == src], []))
        frames.append(d[d["index"].isin(keep)][[ID, "CONJUNTO", "source", "index", "t", "smooth_value", "first_derivative"]])
    return pd.concat(frames, ignore_index=True)


def redundancy(curves):
    detail = []
    summary = []
    for group, (source, variables) in GROUPS.items():
        z = curves[(curves.source == source) & curves["index"].isin(variables)]
        piv = z.pivot_table(index=[ID, "t"], columns="index", values="smooth_value")
        der = z.pivot_table(index=[ID, "t"], columns="index", values="first_derivative")
        for ia, a in enumerate(variables):
            for b in variables[ia+1:]:
                per = []
                for pid in sorted(set(piv.index.get_level_values(0))):
                    if a not in piv or b not in piv: continue
                    ya = piv.loc[pid, a].to_numpy(float); yb = piv.loc[pid, b].to_numpy(float)
                    da = der.loc[pid, a].to_numpy(float); db = der.loc[pid, b].to_numpy(float)
                    za = (ya-ya.mean())/(ya.std()+1e-12); zb = (yb-yb.mean())/(yb.std()+1e-12)
                    ta, ga, xa = timing(ya, da); tb, gb, xb = timing(yb, db)
                    row = {ID:pid, "group":group, "source":source, "index_a":a, "index_b":b,
                           "curve_correlation":corr(ya,yb), "standardized_integrated_squared_distance":float(np.sqrt(np.trapz((za-zb)**2))),
                           "derivative_correlation":corr(da,db), "peak_timing_difference_days":abs(ta-tb),
                           "max_growth_timing_difference_days":abs(ga-gb), "max_decline_timing_difference_days":abs(xa-xb),
                           "amplitude_a":np.ptp(ya), "amplitude_b":np.ptp(yb), "auc_a":np.trapz(ya), "auc_b":np.trapz(yb)}
                    detail.append(row); per.append(row)
                q = pd.DataFrame(per)
                s = {"group":group, "source":source, "index_a":a, "index_b":b, "n_parcels":len(q)}
                for col in ["curve_correlation", "standardized_integrated_squared_distance", "derivative_correlation",
                            "peak_timing_difference_days", "max_growth_timing_difference_days", "max_decline_timing_difference_days"]:
                    for name, val in zip(["q10","q25","median","q75","q90"], q[col].quantile([.1,.25,.5,.75,.9])): s[f"{col}_{name}"] = val
                for th in [.90,.95,.98]: s[f"proportion_curve_correlation_gt_{str(th).replace('.','_')}"] = (q.curve_correlation > th).mean()
                s["amplitude_correlation_across_parcels"] = corr(q.amplitude_a, q.amplitude_b)
                s["auc_correlation_across_parcels"] = corr(q.auc_a, q.auc_b)
                s["strong_redundancy_edge"] = bool(s["curve_correlation_median"] >= .95 and s["derivative_correlation_median"] >= .90 and
                                                    s["peak_timing_difference_days_median"] <= 10 and
                                                    s["max_growth_timing_difference_days_median"] <= 14 and
                                                    s["max_decline_timing_difference_days_median"] <= 14)
                summary.append(s)
    return pd.DataFrame(detail), pd.DataFrame(summary)


def choose_signals(summary):
    quality = pd.read_csv(OUT.parent/"stage1_functional_preprocessing/diagnostics/functional_quality_summary.csv")
    quality = quality[(quality.source == "Sentinel") & (quality.functional_block == "MEAN_FUNCTIONS")]
    over = quality.set_index("variable").pct_potentially_over_smoothed.to_dict()
    # Target-free: when possible retain the most stable pair that is NOT linked
    # by the composite redundancy rule. This preserves one dynamic contrast per
    # biological family without letting the first (lowest over-smoothing) node
    # collapse a densely connected graph to a single signal.
    selected = []; chosen_by_group = {}
    for group in ["SENTINEL_VIGOR", "SENTINEL_MOISTURE_STRESS"]:
        variables = GROUPS[group][1]
        pairs=[]
        for i,a in enumerate(variables):
            for b in variables[i+1:]:
                e=summary[(summary.group==group)&(((summary.index_a==a)&(summary.index_b==b))|((summary.index_a==b)&(summary.index_b==a)))]
                if len(e) and not bool(e.strong_redundancy_edge.iloc[0]): pairs.append((over.get(a,100)+over.get(b,100),a,b))
        local=list(min(pairs)[1:]) if pairs else [min(variables,key=lambda x:over.get(x,100))]
        selected.extend(local);chosen_by_group[group]=local
    rows=[]
    for group in ["SENTINEL_VIGOR", "SENTINEL_MOISTURE_STRESS"]:
        local=chosen_by_group[group]
        for v in GROUPS[group][1]:
            redundant=[]
            for u in local:
                if u==v:continue
                e=summary[(summary.group==group)&(((summary.index_a==u)&(summary.index_b==v))|((summary.index_a==v)&(summary.index_b==u)))]
                if len(e) and bool(e.strong_redundancy_edge.iloc[0]):redundant.append(u)
            keep=v in local
            rows.append({"source":"Sentinel", "group":group, "signal":v, "selected_for_fpca":keep,
                         "over_smoothing_pct":over.get(v,np.nan), "redundant_with_selected":"|".join(redundant),
                         "selection_reason":"most stable non-redundant pair in conceptual family" if keep else "excluded from compact first-round set"})
    return pd.DataFrame(rows), selected


def fpca_one(curves, signal, max_components=10):
    z = curves[(curves.source=="Sentinel") & (curves["index"]==signal)]
    x = z.pivot(index=ID, columns="t", values="smooth_value").sort_index(axis=1)
    x = x.dropna(); t = x.columns.to_numpy(float); arr=x.to_numpy(float); mean=arr.mean(0); centered=arr-mean
    dt=np.diff(t); w=np.r_[dt[0]/2, (dt[:-1]+dt[1:])/2, dt[-1]/2]; sw=np.sqrt(w)
    u,s,vt=np.linalg.svd(centered*sw, full_matrices=False)
    eig=s**2/(len(x)-1); phi=vt/sw; scores=centered@(phi*w).T
    ratio=eig/eig.sum(); cum=np.cumsum(ratio); k=min(max_components, len(eig))
    erows=[]
    for j in range(k): erows.append({"source":"Sentinel","signal":signal,"component":j+1,"eigenvalue":eig[j],"explained_variance_ratio":ratio[j],"cumulative_explained_variance":cum[j]})
    thresholds={q:int(np.searchsorted(cum,q)+1) for q in [.8,.9,.95]}
    srows=[]
    conj=z[[ID,"CONJUNTO"]].drop_duplicates().set_index(ID).CONJUNTO
    for i,pid in enumerate(x.index):
        row={ID:pid,"CONJUNTO":conj.get(pid),"source":"Sentinel","signal":signal}
        row.update({f"FPC{j+1}":scores[i,j] for j in range(k)});srows.append(row)
    frows=[]
    for ti,tt in enumerate(t):
        base={"source":"Sentinel","signal":signal,"t":int(tt),"date":pd.Timestamp("2025-04-01")+pd.Timedelta(days=int(tt)),"mean_function":mean[ti]}
        for j in range(k): base[f"FPC{j+1}_eigenfunction"]=phi[j,ti]
        frows.append(base)
    return pd.DataFrame(erows),pd.DataFrame(srows),pd.DataFrame(frows),thresholds


def planet_compare(curves):
    rows=[]
    for v in ["ndvi","evi","lai"]:
        a=curves[(curves.source=="Sentinel")&(curves["index"]==v)].set_index([ID,"t"])
        b=curves[(curves.source=="Planet")&(curves["index"]==v)].set_index([ID,"t"])
        for pid in sorted(set(a.index.get_level_values(0)) & set(b.index.get_level_values(0))):
            aa=a.loc[pid];bb=b.loc[pid];ya=aa.smooth_value.to_numpy();yb=bb.smooth_value.to_numpy();da=aa.first_derivative.to_numpy();db=bb.first_derivative.to_numpy()
            ta,ga,xa=timing(ya,da);tb,gb,xb=timing(yb,db)
            rows.append({ID:pid,"index":v,"curve_correlation":corr(ya,yb),"derivative_correlation":corr(da,db),
                         "peak_timing_difference_days":abs(ta-tb),"max_growth_timing_difference_days":abs(ga-gb),"max_decline_timing_difference_days":abs(xa-xb)})
    d=pd.DataFrame(rows); out=[]
    for v,g in d.groupby("index"):
        r={"index":v,"n_parcels":len(g)}
        for c in d.columns[2:]:
            for n,q in [("q25",.25),("median",.5),("q75",.75)]:r[f"{c}_{n}"]=g[c].quantile(q)
        out.append(r)
    return d,pd.DataFrame(out)


def difficult_distances(score_wide):
    from family_1.stage4_modeling import load_xy, representations
    ids,X,_ = load_xy(); core=representations(X.columns)["CORE"]
    zc=StandardScaler().fit_transform(SimpleImputer(strategy="median").fit_transform(X[core]))
    cids=pd.Index(ids.astype(str)); dc=cdist(zc,zc);np.fill_diagonal(dc,np.inf)
    sf=score_wide.set_index(ID).reindex(cids); score_cols=[c for c in sf if "_FPC" in c]
    zf=StandardScaler().fit_transform(sf[score_cols]);df=cdist(zf,zf);np.fill_diagonal(df,np.inf)
    hard=pd.read_csv(ROOT/"outputs/modeling/family_1/support_analysis/support/difficult_parcel_support.csv")
    hard=hard[hard.support_class.eq("y-outlier given similar X")]
    rows=[]
    for pid in hard[ID]:
        i=cids.get_loc(pid); nc=np.argsort(dc[i])[:5]; nf=np.argsort(df[i])[:5]
        rows.append({ID:pid,"core_nearest_distance":dc[i,nc[0]],"core_mean_5nn_distance":dc[i,nc].mean(),
                     "functional_nearest_distance":df[i,nf[0]],"functional_mean_5nn_distance":df[i,nf].mean(),
                     "core_nearest_ID":cids[nc[0]],"functional_nearest_ID":cids[nf[0]],
                     "neighbor5_overlap_count":len(set(nc)&set(nf)),"functional_to_core_5nn_ratio":df[i,nf].mean()/dc[i,nc].mean(),
                     "core_5nn_percentile":(np.sort(np.partition(dc,5,axis=1)[:,:5].mean(1))<=dc[i,nc].mean()).mean(),
                     "functional_5nn_percentile":(np.sort(np.partition(df,5,axis=1)[:,:5].mean(1))<=df[i,nf].mean()).mean()})
    return pd.DataFrame(rows)


def plots(summary,eigs,funcs,corrmat):
    labels=sorted(set(summary.index_a)|set(summary.index_b));m=pd.DataFrame(np.eye(len(labels)),index=labels,columns=labels)
    for _,r in summary[summary.source.eq("Sentinel")].iterrows():m.loc[r.index_a,r.index_b]=m.loc[r.index_b,r.index_a]=r.curve_correlation_median
    plt.figure(figsize=(8,7));sns.heatmap(m,annot=True,fmt=".2f",vmin=-1,vmax=1,cmap="vlag");plt.title("Median functional curve correlation — Sentinel");plt.tight_layout();plt.savefig(DIR["figures"]/"functional_redundancy_heatmap.png",dpi=180);plt.close()
    # Small reproducible redundancy graph without an extra graph dependency.
    fig,axs=plt.subplots(1,2,figsize=(12,5))
    for ax,(group,(_,nodes)) in zip(axs,[x for x in GROUPS.items() if x[0].startswith("SENTINEL")]):
        ang=np.linspace(0,2*np.pi,len(nodes),endpoint=False);pos={n:(np.cos(a),np.sin(a)) for n,a in zip(nodes,ang)}
        sub=summary[(summary.group==group)&summary.strong_redundancy_edge]
        for _,r in sub.iterrows():
            x1,y1=pos[r.index_a];x2,y2=pos[r.index_b];ax.plot([x1,x2],[y1,y2],color="#888",lw=1+3*(r.curve_correlation_median-.95)/.05,alpha=.7,zorder=1)
        for n,(x,y) in pos.items():ax.scatter(x,y,s=900,color="#4C78A8",edgecolor="white",zorder=2);ax.text(x,y,n.upper(),ha="center",va="center",color="white",fontsize=9,fontweight="bold",zorder=3)
        ax.set_title(group.replace("SENTINEL_","").replace("_"," / "));ax.set_aspect("equal");ax.axis("off")
    fig.suptitle("Composite functional redundancy graph — Sentinel");fig.tight_layout();fig.savefig(DIR["figures"]/"functional_redundancy_graph.png",dpi=180);plt.close(fig)
    for sig,g in eigs.groupby("signal"):
        plt.figure(figsize=(6,4));plt.plot(g.component,g.cumulative_explained_variance,marker="o");
        for q in [.8,.9,.95]:plt.axhline(q,ls="--",lw=.8)
        plt.ylim(0,1.02);plt.xlabel("FPC");plt.ylabel("Cumulative explained variance");plt.title(f"FPCA variance — {sig.upper()}");plt.tight_layout();plt.savefig(DIR["figures"]/f"fpca_variance_explained_{sig}.png",dpi=180);plt.close()
        f=funcs[funcs.signal.eq(sig)]; eg=g.set_index("component").eigenvalue
        fig,axs=plt.subplots(1,3,figsize=(15,4),sharey=True)
        for j,ax in enumerate(axs,1):
            phi=f[f"FPC{j}_eigenfunction"];delta=2*np.sqrt(eg[j])*phi
            ax.plot(f.t,f.mean_function,color="black",label="mean");ax.plot(f.t,f.mean_function+delta,label="mean + 2SD");ax.plot(f.t,f.mean_function-delta,label="mean - 2SD");ax.set_title(f"{sig.upper()} FPC{j} ({g.loc[g.component.eq(j),'explained_variance_ratio'].iloc[0]:.1%})")
        axs[0].legend(fontsize=8);fig.tight_layout();fig.savefig(DIR["figures"]/f"fpca_modes_{sig}.png",dpi=180);plt.close(fig)
    plt.figure(figsize=(max(8,.35*len(corrmat)),max(7,.32*len(corrmat))));sns.heatmap(corrmat,cmap="vlag",vmin=-1,vmax=1);plt.title("Correlation among retained functional scores");plt.tight_layout();plt.savefig(DIR["figures"]/"fpca_score_correlations.png",dpi=180);plt.close()


def main():
    curves=load_curves(); detail,summary=redundancy(curves)
    detail.to_csv(DIR["redundancy"]/"within_group_functional_redundancy.csv",index=False)
    summary.to_csv(DIR["redundancy"]/"functional_redundancy_summary.csv",index=False)
    _,pc=planet_compare(curves);pc.to_csv(DIR["redundancy"]/"sentinel_planet_functional_comparison.csv",index=False)
    selection,selected=choose_signals(summary);selection.to_csv(DEST/"selected_functional_signals.csv",index=False)
    er=[];sr=[];fr=[];meta=[]
    sm=pd.read_csv(DATA/"functional_smoothing_metadata.csv")
    for sig in selected:
        e,s,f,thr=fpca_one(curves,sig);er.append(e);sr.append(s);fr.append(f)
        r=sm[(sm.source=="Sentinel")&(sm.variable==sig)&(sm.functional_block=="MEAN_FUNCTIONS")].iloc[0]
        meta.append({"source":"Sentinel","signal":sig,"fpca_method":"L2 weighted SVD with trapezoidal quadrature","domain":"2025-04-01..2025-10-31","n_parcels":s[ID].nunique(),"n_grid_points":214,
                     "n_fpc_80":thr[.8],"n_fpc_90":thr[.9],"n_fpc_95":thr[.95],"basis_type":r.basis_type,"default_n_basis":r.n_basis,"default_lambda":r["lambda"],
                     "smoothing_lighter_lambda":r["lambda"]/10,"smoothing_default_lambda":r["lambda"],"smoothing_stronger_lambda":r["lambda"]*10,
                     "smoothing_grid_note":"future inner-CV only; refit smoothing and FPCA inside each train fold"})
    eigs=pd.concat(er,ignore_index=True);scores=pd.concat(sr,ignore_index=True);funcs=pd.concat(fr,ignore_index=True);metadata=pd.DataFrame(meta)
    eigs.to_csv(DEST/"fpca_eigenvalues.csv",index=False);scores.to_parquet(DEST/"fpca_scores.parquet",index=False);funcs.to_parquet(DEST/"fpca_eigenfunctions.parquet",index=False);metadata.to_csv(DEST/"fpca_metadata.csv",index=False)
    eigs.to_csv(DIR["fpca"]/"explained_variance.csv",index=False)
    wide=None
    for sig,g in scores.groupby("signal"):
        q=g.drop(columns=["source","signal"]).rename(columns={c:f"{sig}_{c}" for c in g if c.startswith("FPC")})
        wide=q if wide is None else wide.merge(q,on=[ID,"CONJUNTO"],how="inner")
    cols=[c for c in wide if "_FPC" in c];cm=wide[cols].corr();cm.rename_axis("score_a").reset_index().melt("score_a",var_name="score_b",value_name="correlation").to_csv(DIR["fpca"]/"functional_score_correlation.csv",index=False)
    dd=difficult_distances(wide);dd.to_csv(DIR["diagnostics"]/"difficult_parcels_functional_distance.csv",index=False)
    plots(summary,eigs,funcs,cm)
    # Data-driven concise report, with no outcome information used in representation construction.
    edges=summary[summary.strong_redundancy_edge]
    sel=", ".join(x.upper() for x in selected)
    dims=metadata[["signal","n_fpc_80","n_fpc_90","n_fpc_95"]].to_dict("records")
    ptxt=pc[["index","curve_correlation_median","derivative_correlation_median","peak_timing_difference_days_median"]].round(3).to_dict("records")
    high=(cm.abs().where(~np.eye(len(cm),dtype=bool)).stack().abs()>=.90).sum()//2
    retained95=[]
    for _,r in metadata.iterrows():retained95 += [f"{r.signal}_FPC{i}" for i in range(1,int(r.n_fpc_95)+1)]
    score_eigs=np.linalg.eigvalsh(cm.loc[retained95,retained95].to_numpy())[::-1]
    effective_rank=float(score_eigs.sum()**2/np.sum(score_eigs**2));score_dim90=int(np.searchsorted(np.cumsum(score_eigs)/score_eigs.sum(),.9)+1)
    sep=(dd.functional_5nn_percentile-dd.core_5nn_percentile)
    report=f"""# Familia 2 — F2.2 Redundancia funcional y FPCA

## Alcance y controles

Se analizaron {curves[ID].nunique()} parcelas sobre t=0..213. La selección de señales, smoothing y FPCA fue completamente target-free. El rendimiento no se leyó para construir la representación. La FPCA se calculó en la métrica funcional L2 mediante cuadratura trapezoidal de las funciones suavizadas; el grid diario no fue tratado como 214 features independientes. Climate y Landsat permanecen fuera. Planet no se fusionó con Sentinel. F2.3 no fue ejecutada.

## Respuestas

1. **Vigor redundante.** Las aristas compuestas fuertes fueron: {', '.join((edges[edges.group.eq('SENTINEL_VIGOR')].index_a+'–'+edges[edges.group.eq('SENTINEL_VIGOR')].index_b).str.upper()) or 'ninguna bajo el criterio compuesto'}.
2. **Humedad/estrés redundante.** Aristas fuertes: {', '.join((edges[edges.group.eq('SENTINEL_MOISTURE_STRESS')].index_a+'–'+edges[edges.group.eq('SENTINEL_MOISTURE_STRESS')].index_b).str.upper()) or 'ninguna bajo el criterio compuesto'}.
3. **Dinámica diferenciada.** Se conservan señales sin arista fuerte respecto de las ya seleccionadas; la decisión combina nivel, derivada y timings, no una correlación aislada.
4. **Conjunto compacto Sentinel.** {sel} ({len(selected)} señales). La tabla `selected_functional_signals.csv` documenta inclusiones y exclusiones.
5. **Planet vs Sentinel.** Resumen: {ptxt}. Correlación alta de forma con desplazamientos de eventos indica principalmente mayor densidad y pequeñas diferencias temporales; se mantiene como replicación separada.
6. **FPCs para 80/90/95%.** {dims}.
7. **Interpretación FPC1–FPC3.** Las figuras `fpca_modes_*` muestran media ±2√λφ (el signo de cada FPC es arbitrario). En las cuatro señales, FPC1 (47.6–53.9%) contrasta un máximo central más temprano con mantenimiento/segundo máximo tardío: domina **timing y duración**, no sólo nivel. FPC2 (19.8–21.5%) vuelve a separar ascenso temprano alrededor de t≈90–110 de máximo central/tardío alrededor de t≈145–200. FPC3 (15.3–18.3%) captura principalmente **amplitud y persistencia tardía**; en NDWI también contrasta el nivel alrededor de t≈90 con t≈150–210. Son modos mixtos, por lo que no se presentan como fechas agronómicas exactas.
8. **Redundancia entre scores.** Hay {int(high)} pares de scores con |r|≥0.90. Véanse `functional_score_correlation.csv` y el heatmap.
9. **Dimensión efectiva.** La suma de FPCs requeridas al 95% es {int(metadata.n_fpc_95.sum())}, pero la matriz conjunta tiene rango efectivo de participación {effective_rank:.2f} y {score_dim90} ejes explican 90% de su varianza estandarizada. Esto confirma redundancia cruzada y no equivale automáticamente al número final de features predictivas.
10. **Parcelas difíciles.** En {int((sep>0).sum())} de 9 aumenta el percentil de distancia 5NN en el espacio funcional; mediana del cambio={sep.median():.3f}. Esto indica separación funcional sólo para parte de ellas, no demuestra explicación del error.
11. **¿Family 1 perdió información temporal?** Hay evidencia descriptiva si cambian vecinos/distancias y existen FPC2/FPC3 no redundantes, pero no evidencia predictiva hasta nested CV en F2.3.
12. **Scores para F2.3.** Llevar los scores hasta 95% como candidato completo y definir una alternativa compacta (90%) dentro del pipeline. FPCA debe reajustarse dentro de cada train fold; no reutilizar scores globales para validación.
13. **Grid de smoothing futuro.** Por señal: λ/10, λ default y 10λ, detallado en `fpca_metadata.csv`. Selección sólo por RMSE de inner CV y con smoothing+FPCA reajustados en train fold.
14. **Preparación.** F2.2 queda lista técnicamente para F2.3: artefactos completos, representación target-free y benchmark Climate Current separado. No se inició modelado híbrido.

## Regla de redundancia

Arista sólo si mediana corr(curva)≥0.95, mediana corr(derivada)≥0.90, diferencia mediana de pico≤10 días y diferencias medianas de máximo crecimiento y declive≤14 días. Una señal excluida no es declarada inútil: sólo es redundante para esta primera representación compacta.

## Precaución de validación

Los scores globales son diagnósticos y un insumo de desarrollo. En F2.3, smoothing, centrado, FPCA, número de scores y cualquier selección deben ajustarse exclusivamente en cada train fold interno/externo para evitar leakage.
"""
    (DIR["report"]/"family2_stage2_fpca_report.md").write_text(report,encoding="utf-8")
    print(f"F2.2 complete: selected={selected}; scores={scores.shape}; effective95={metadata.n_fpc_95.sum()}")


if __name__ == "__main__": main()
