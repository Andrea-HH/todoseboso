"""Climate Regime Extension R1: discovery completamente target-free."""
from pathlib import Path
import sys,warnings,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
from scipy.optimize import linear_sum_assignment
from scipy.stats import entropy
from scipy.spatial.distance import cdist
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score,adjusted_rand_score
from family_1.stage4_modeling import representations,FEATURE_DIR,ID,SEED
warnings.filterwarnings('ignore');sns.set_theme(style='whitegrid')

BASE=ROOT/'outputs/modeling/family_1/climate_regimes/stage1_discovery'
D={x:BASE/x for x in ['model_selection','memberships','profiles','diagnostics','figures','report']}
for p in D.values():p.mkdir(parents=True,exist_ok=True)
N_BOOT=50;KS=range(1,6);COVS=['diag','tied','full']

def climate_block():
    raw=pd.read_parquet(FEATURE_DIR/'climate_features.parquet').sort_values(ID).reset_index(drop=True)
    # Derivar el bloque exacto sin abrir la tabla maestra de rendimiento.
    all_columns=pd.read_parquet(FEATURE_DIR/'family1_features_all.parquet').columns
    core=representations(all_columns)['CORE'];dic=pd.read_csv(FEATURE_DIR/'family1_feature_dictionary.csv').set_index('feature_name')
    cols=[c for c in core if c in dic.index and dic.loc[c,'source']=='CLIMATE']
    if len(cols)!=48:raise ValueError(f'Se esperaban 48 variables Climate Current, hay {len(cols)}')
    return raw[[ID]+cols],cols

def audit(d,cols):
    rows=[];remove=[];seen={}
    for c in cols:
        x=d[c];constant=x.dropna().nunique()<=1;deg=(x.dropna().std() if x.notna().sum()>1 else 0)<1e-12;dup=''
        if not constant and not deg:
            for prev in seen:
                if x.equals(d[prev]):dup=prev;break
            if not dup:seen[c]=True
        reason='constant' if constant else 'numerically_degenerate' if deg else f'exact_duplicate_of:{dup}' if dup else ''
        if reason:remove.append(c)
        rows.append({'feature':c,'missing_n':x.isna().sum(),'missing_fraction':x.isna().mean(),'n_unique':x.nunique(dropna=True),'mean':x.mean(),'std':x.std(),'min':x.min(),'q25':x.quantile(.25),'median':x.median(),'q75':x.quantile(.75),'max':x.max(),'removed':bool(reason),'removal_reason':reason})
    a=pd.DataFrame(rows);a.to_csv(D['diagnostics']/'climate_feature_audit.csv',index=False)
    return [c for c in cols if c not in remove],remove

def nparams(k,p,cov):
    covp={'diag':k*p,'tied':p*(p+1)//2,'full':k*p*(p+1)//2}[cov]
    return (k-1)+k*p+covp

def fit_gmm(z,k,cov,seed,n_init=20):
    g=GaussianMixture(n_components=k,covariance_type=cov,reg_covar=1e-5,n_init=n_init,max_iter=1000,random_state=seed,init_params='kmeans').fit(z)
    return g

def covariance_floor_diagnostic(g,tol=1.1e-5):
    if g.covariance_type=='diag':vals=np.ravel(g.covariances_)
    elif g.covariance_type=='tied':vals=np.linalg.eigvalsh(g.covariances_)
    else:vals=np.concatenate([np.linalg.eigvalsh(q) for q in g.covariances_])
    frac=float(np.mean(vals<=tol));return float(vals.min()),frac,bool(frac>0)

def weighted_median(x,w):
    o=np.argsort(x);x=np.asarray(x)[o];w=np.asarray(w)[o];return x[np.searchsorted(np.cumsum(w),w.sum()/2)]

def memberships_stats(proba):
    k=proba.shape[1];mx=proba.max(1);ent=np.zeros(len(proba)) if k==1 else entropy(proba.T)/np.log(k)
    return mx,ent

def bootstrap_stability(x,ref_by_k,best_cov,nboot=N_BOOT):
    rng=np.random.default_rng(SEED+991);rows=[]
    for k in KS:
        refp=ref_by_k[k]['proba'];refl=refp.argmax(1);refprof=refp.T@x/refp.sum(0)[:,None]
        for b in range(nboot):
            idx=rng.integers(0,len(x),len(x));imp=SimpleImputer(strategy='median').fit(x[idx]);xi=imp.transform(x[idx]);allx=imp.transform(x)
            sc=StandardScaler().fit(xi);zi=sc.transform(xi);za=sc.transform(allx);pca=PCA(n_components=.95,svd_solver='full').fit(zi);zr=pca.transform(zi);zall=pca.transform(za)
            try:g=fit_gmm(zr,k,best_cov[k],SEED+1000*k+b,n_init=5);pb=g.predict_proba(zall);conv=g.converged_
            except Exception:
                rows.append({'k':k,'resample':b,'converged':False,'ARI':np.nan,'membership_correlation':np.nan,'profile_similarity':np.nan});continue
            if k>1:
                cost=np.zeros((k,k))
                for i in range(k):
                    for j in range(k):
                        a=refp[:,i];c=pb[:,j];cost[i,j]=-(np.corrcoef(a,c)[0,1] if np.std(a)>0 and np.std(c)>0 else -1)
                ri,cj=linear_sum_assignment(cost);order=np.empty(k,dtype=int);order[ri]=cj;pb=pb[:,order]
            lab=pb.argmax(1);cors=[np.corrcoef(refp[:,j],pb[:,j])[0,1] for j in range(k) if np.std(refp[:,j])>0 and np.std(pb[:,j])>0]
            prof=pb.T@x/pb.sum(0)[:,None];ps=np.mean([np.corrcoef(refprof[j],prof[j])[0,1] for j in range(k)])
            rows.append({'k':k,'resample':b,'covariance_type':best_cov[k],'converged':conv,'ARI':1. if k==1 else adjusted_rand_score(refl,lab),'membership_correlation':1. if k==1 else np.nanmean(cors),'profile_similarity':ps})
    return pd.DataFrame(rows)

def select_candidate(ms,stab):
    valid_ms=ms[ms.converged&~ms.singularity_warning]
    best=valid_ms.loc[valid_ms.groupby('k').BIC.idxmin()].set_index('k');s=stab.groupby('k').agg(ARI=('ARI','mean'),membership=('membership_correlation','mean'),convergence=('converged','mean')).join(best[['BIC','AIC','min_effective_size','min_hard_size']])
    bic1=s.loc[1,'BIC'];valid=[]
    for k in range(2,6):
        if bic1-s.loc[k,'BIC']>10 and s.loc[k,'min_effective_size']>=10 and s.loc[k,'ARI']>=.60 and s.loc[k,'membership']>=.75 and s.loc[k,'convergence']>=.95:valid.append(k)
    if not valid:return 1,s
    winner=min(valid,key=lambda k:s.loc[k,'BIC']);near=[k for k in valid if s.loc[k,'BIC']-s.loc[winner,'BIC']<=10]
    return min(near),s

def main():
    data,original_cols=climate_block();cols,removed=audit(data,original_cols);x=data[cols].to_numpy(float)
    correlations=data[cols].corr();correlations.to_csv(D['diagnostics']/'climate_feature_correlations.csv')
    imp=SimpleImputer(strategy='median').fit(x);xi=imp.transform(x);sc=StandardScaler().fit(xi);z=sc.transform(xi);pca=PCA(n_components=None,svd_solver='full').fit(z);cum=np.cumsum(pca.explained_variance_ratio_);npc={q:int(np.searchsorted(cum,q)+1) for q in [.8,.9,.95]};p95=PCA(n_components=npc[.95],svd_solver='full').fit(z);zp=p95.transform(z)
    pd.DataFrame({'feature':cols,'imputer_median':imp.statistics_,'scaler_mean':sc.mean_,'scaler_scale':sc.scale_}).to_csv(D['diagnostics']/'scaler_parameters.csv',index=False)
    ev=pd.DataFrame({'component':np.arange(1,len(cum)+1),'explained_variance_ratio':pca.explained_variance_ratio_,'cumulative_explained_variance':cum});ev['selected_95']=ev.component<=npc[.95];ev.to_csv(D['model_selection']/'pca_explained_variance.csv',index=False)
    rows=[];models={};ref_by_k={};best_cov={}
    for k in KS:
      for cov in COVS:
        try:
            g=fit_gmm(zp,k,cov,SEED+k);pb=g.predict_proba(zp);lab=pb.argmax(1);mx,en=memberships_stats(pb);sil=np.nan if k==1 or len(np.unique(lab))<2 else silhouette_score(zp,lab);ne=pb.sum(0);hard=np.bincount(lab,minlength=k)
            mincov,floorfrac,singular=covariance_floor_diagnostic(g)
            r={'k':k,'covariance_type':cov,'converged':g.converged_,'n_iter':g.n_iter_,'log_likelihood_total':g.score(zp)*len(zp),'n_parameters':nparams(k,zp.shape[1],cov),'BIC':g.bic(zp),'AIC':g.aic(zp),'silhouette':sil,'mean_membership_entropy':en.mean(),'mean_max_probability':mx.mean(),'min_effective_size':ne.min(),'min_hard_size':hard.min(),'min_covariance_eigenvalue':mincov,'covariance_floor_fraction':floorfrac,'singularity_warning':singular}
            models[(k,cov)]=g
        except Exception as e:r={'k':k,'covariance_type':cov,'converged':False,'n_iter':np.nan,'log_likelihood_total':np.nan,'n_parameters':nparams(k,zp.shape[1],cov),'BIC':np.inf,'AIC':np.inf,'silhouette':np.nan,'mean_membership_entropy':np.nan,'mean_max_probability':np.nan,'min_effective_size':np.nan,'min_hard_size':np.nan,'singularity_warning':True,'error':type(e).__name__}
        rows.append(r)
    ms=pd.DataFrame(rows);ms.to_csv(D['model_selection']/'gmm_model_selection.csv',index=False)
    for k in KS:
        candidate=ms[(ms.k==k)&ms.converged&~ms.singularity_warning].sort_values(['BIC','n_parameters'])
        if candidate.empty:raise RuntimeError(f'No existe GMM numericamente estable para K={k}')
        r=candidate.iloc[0];best_cov[k]=r.covariance_type;g=models[(k,best_cov[k])];ref_by_k[k]={'model':g,'proba':g.predict_proba(zp)}
    stab=bootstrap_stability(x,ref_by_k,best_cov);stab.to_csv(D['model_selection']/'clustering_stability.csv',index=False);chosen,decision=select_candidate(ms,stab)
    g=ref_by_k[chosen]['model'];pb=ref_by_k[chosen]['proba'];lab=pb.argmax(1);mx,en=memberships_stats(pb)
    mem=pd.DataFrame({ID:data[ID],'regime_hard':lab+1});
    for j in range(chosen):mem[f'regime_probability_{j+1}']=pb[:,j]
    mem['max_membership_probability']=mx;mem['membership_entropy']=en;mem['membership_class']=np.select([mx>.9,mx>.75,mx>=.5],['HIGH_CONFIDENCE_>0.90','MODERATE_0.75_0.90','AMBIGUOUS_0.50_0.75'],default='AMBIGUOUS_<0.50');mem.to_parquet(D['memberships']/'climate_regime_memberships.parquet',index=False)
    eff=[]
    for j in range(chosen):eff.append({'regime':j+1,'effective_size':pb[:,j].sum(),'hard_size':(lab==j).sum(),'mean_probability':pb[:,j].mean(),'high_confidence_hard_n':((lab==j)&(mx>.9)).sum(),'potentially_small':pb[:,j].sum()<10})
    pd.DataFrame(eff).to_csv(D['diagnostics']/'effective_cluster_sizes.csv',index=False);mem[mem.max_membership_probability<=.75].to_csv(D['diagnostics']/'ambiguous_memberships.csv',index=False)
    # Original-variable weighted profiles.
    prof=[]
    for j in range(chosen):
        wj=pb[:,j]
        for c in cols:
            v=data[c].to_numpy(float);mask=np.isfinite(v);mu=np.average(v[mask],weights=wj[mask]);med=weighted_median(v[mask],wj[mask]);prof.append({'regime':j+1,'feature':c,'weighted_mean':mu,'weighted_median':med,'population_mean':np.nanmean(v),'population_std':np.nanstd(v),'standardized_regime_mean':(mu-np.nanmean(v))/(np.nanstd(v)+1e-12)})
    profiles=pd.DataFrame(prof);profiles.to_csv(D['profiles']/'climate_regime_profiles.csv',index=False)
    monthly=pd.read_parquet(ROOT/'data/processed/family_1/environment/climate_monthly_timeseries.parquet');monthly=monthly[(monthly.year==2025)&monthly.month.between(4,10)].merge(mem[[ID]+[c for c in mem if c.startswith('regime_probability_')]],on=ID)
    mr=[]
    for j in range(chosen):
      wc=f'regime_probability_{j+1}'
      for m,gg in monthly.groupby('month'):
        r={'regime':j+1,'month':m,'effective_month_weight':gg[wc].sum()}
        for v in ['precip_mean','tmin_mean','tmax_mean','tmean_mean','dtr_mean']:r[v]=np.average(gg[v],weights=gg[wc])
        mr.append(r)
    pd.DataFrame(mr).to_csv(D['profiles']/'monthly_regime_profiles.csv',index=False)
    # K-means sanity check on same PCA space.
    km=KMeans(n_clusters=chosen,random_state=SEED,n_init=50).fit(zp);ari=1. if chosen==1 else adjusted_rand_score(lab,km.labels_);kmrows=[{'record_type':'summary','gmm_regime':np.nan,'kmeans_cluster':np.nan,'n':len(lab),'ARI':ari}]
    for a in range(chosen):
      for b in range(chosen):kmrows.append({'record_type':'contingency','gmm_regime':a+1,'kmeans_cluster':b+1,'n':int(((lab==a)&(km.labels_==b)).sum()),'ARI':ari})
    pd.DataFrame(kmrows).to_csv(D['diagnostics']/'kmeans_gmm_comparison.csv',index=False)
    # Figures.
    plt.figure(figsize=(7,4));plt.plot(ev.component,ev.cumulative_explained_variance,marker='o');[plt.axhline(q,ls='--',lw=.8) for q in [.8,.9,.95]];plt.xlabel('PC');plt.ylabel('Cumulative variance');plt.tight_layout();plt.savefig(D['figures']/'pca_variance.png',dpi=180);plt.close()
    fig,axs=plt.subplots(1,2,figsize=(12,4));
    for cov,gg in ms.groupby('covariance_type'):axs[0].plot(gg.k,gg.BIC,marker='o',label=cov);axs[1].plot(gg.k,gg.AIC,marker='o',label=cov)
    axs[0].set_title('BIC');axs[1].set_title('AIC');[a.legend() for a in axs];fig.tight_layout();fig.savefig(D['figures']/'bic_aic_by_k.png',dpi=180);plt.close(fig)
    plt.figure(figsize=(7,5));sns.scatterplot(x=zp[:,0],y=zp[:,1] if zp.shape[1]>1 else np.zeros(len(zp)),hue=lab+1,size=mx,palette='tab10');plt.xlabel('Climate PC1');plt.ylabel('Climate PC2');plt.tight_layout();plt.savefig(D['figures']/'climate_pca_regimes.png',dpi=180);plt.close()
    plt.figure(figsize=(7,4));sns.histplot(mx,bins=20);plt.axvline(.75,ls='--');plt.axvline(.9,ls='--');plt.xlabel('Maximum membership probability');plt.tight_layout();plt.savefig(D['figures']/'membership_probability_distribution.png',dpi=180);plt.close()
    top=profiles.assign(a=lambda q:q.standardized_regime_mean.abs()).sort_values('a',ascending=False).groupby('regime').head(12)
    pm=top.pivot(index='feature',columns='regime',values='standardized_regime_mean').fillna(0);plt.figure(figsize=(9,max(5,.28*len(pm))));sns.heatmap(pm,cmap='vlag',center=0);plt.tight_layout();plt.savefig(D['figures']/'climate_regime_profiles.png',dpi=180);plt.close()
    mp=pd.DataFrame(mr);plt.figure(figsize=(8,4));sns.lineplot(data=mp,x='month',y='precip_mean',hue='regime',marker='o');plt.tight_layout();plt.savefig(D['figures']/'monthly_precip_by_regime.png',dpi=180);plt.close()
    fig,axs=plt.subplots(2,2,figsize=(12,8));
    for ax,v in zip(axs.flat,['tmin_mean','tmax_mean','tmean_mean','dtr_mean']):sns.lineplot(data=mp,x='month',y=v,hue='regime',marker='o',ax=ax);ax.set_title(v)
    fig.tight_layout();fig.savefig(D['figures']/'monthly_temperature_by_regime.png',dpi=180);plt.close(fig)
    shp=ROOT/'data/original/02_conjunto_70_30/Parcelas_Reto_AGC_CONJUNTO.shp';geo=gpd.read_file(shp).rename(columns={'ID_POLIGON':ID}).merge(mem,on=ID)
    metric_geo=geo.to_crs('EPSG:6372');cent=np.column_stack([metric_geo.geometry.centroid.x,metric_geo.geometry.centroid.y]);dist=cdist(cent,cent);np.fill_diagonal(dist,np.inf);nn=np.argsort(dist,axis=1)[:,:6];labels=geo.regime_hard.to_numpy();neighbor_agreement=np.mean(labels[:,None]==labels[nn]);rng=np.random.default_rng(SEED+77);perm=np.array([np.mean((q:=rng.permutation(labels))[:,None]==q[nn]) for _ in range(999)]);spatial={'k_neighbors':6,'observed_neighbor_agreement':neighbor_agreement,'permutation_mean':perm.mean(),'permutation_std':perm.std(),'permutation_p_greater':(1+(perm>=neighbor_agreement).sum())/1000,'agreement_excess':neighbor_agreement-perm.mean()};pd.DataFrame([spatial]).to_csv(D['diagnostics']/'spatial_regime_diagnostic.csv',index=False)
    fig,axs=plt.subplots(1,2,figsize=(14,6));geo.plot(column='regime_hard',categorical=True,legend=True,cmap='tab10',ax=axs[0],edgecolor='white',linewidth=.2);geo.plot(column='max_membership_probability',legend=True,cmap='viridis',vmin=0,vmax=1,ax=axs[1],edgecolor='white',linewidth=.2);axs[0].set_title('Hard regime (post hoc)');axs[1].set_title('Dominant membership probability');[a.axis('off') for a in axs];fig.tight_layout();fig.savefig(D['figures']/'regime_map.png',dpi=180);plt.close(fig)
    # Evidence summary/report, without opening yield.
    valid_ms=ms[ms.converged&~ms.singularity_warning];bc=valid_ms.loc[valid_ms.groupby('k').BIC.idxmin()].set_index('k');ss=stab.groupby('k').agg(ARI_mean=('ARI','mean'),ARI_q25=('ARI',lambda x:x.quantile(.25)),membership_corr_mean=('membership_correlation','mean'),profile_similarity_mean=('profile_similarity','mean'),convergence_rate=('converged','mean')).reset_index();
    chosen_st=ss.set_index('k').loc[chosen];bic_gain=bc.loc[1,'BIC']-bc.loc[chosen,'BIC'];counts=mem.membership_class.value_counts().to_dict();topvars=profiles.groupby('feature').standardized_regime_mean.agg(lambda x:x.max()-x.min()).sort_values(ascending=False).head(12).round(3).to_dict();monthly_summary=mp.groupby('regime').agg(precip_total=('precip_mean','sum'),tmean_average=('tmean_mean','mean'),dtr_average=('dtr_mean','mean')).round(3).to_dict('index')
    geotab=pd.crosstab(geo.get('CONJUNTO',pd.Series('ALL',index=geo.index)),geo.regime_hard).to_dict() if 'CONJUNTO' in geo else {}
    upper=correlations.abs().where(np.triu(np.ones(correlations.shape),1).astype(bool)).stack();corr_summary={'max_abs_correlation':upper.max(),'pairs_abs_ge_0.90':int((upper>=.90).sum()),'pairs_abs_ge_0.95':int((upper>=.95).sum()),'pairs_abs_ge_0.99':int((upper>=.99).sum())}
    promising=chosen>1 and bic_gain>10 and chosen_st.ARI_mean>=.6 and chosen_st.membership_corr_mean>=.75 and min(e['effective_size'] for e in eff)>=10
    report=f"""# Climate Regime Extension — Stage R1

## Controles

Análisis target-free de 197 parcelas con exactamente 48 variables Climate Current de Familia 1. No se leyó rendimiento, errores OOF, satélite, topografía ni coordenadas para formar clusters. La geografía se utilizó sólo después de congelar la solución. Tras auditoría quedaron {len(cols)} variables; eliminaciones: {removed or 'ninguna'}. Hay {data[cols].drop_duplicates().shape[0]} perfiles de fila exactamente distintos.

Missingness, escalas y distribuciones están en `climate_feature_audit.csv`; correlaciones en `climate_feature_correlations.csv`. Resumen de correlación: {corr_summary}. La correlación moderada/alta no se utilizó para eliminar variables; PCA absorbió la redundancia.

## Respuestas

1. **¿Más de un régimen?** {'Sí, existe evidencia conjunta prometedora' if promising else 'No existe evidencia suficientemente robusta bajo todos los criterios simultáneos'}.
2. **K defendible:** K={chosen}, covarianza `{best_cov[chosen]}`.
3. **Evidencia frente K=1:** mejora BIC de {bic_gain:.2f} puntos (positivo favorece K={chosen}); AIC K1={bc.loc[1,'AIC']:.2f}, candidato={bc.loc[chosen,'AIC']:.2f}. No se decide por una diferencia mínima aislada.
4. **Estabilidad:** ARI bootstrap medio={chosen_st.ARI_mean:.3f}, correlación media de memberships={chosen_st.membership_corr_mean:.3f}, similitud de perfiles={chosen_st.profile_similarity_mean:.3f}, convergencia={chosen_st.convergence_rate:.1%} (50 resamples).
5. **Pertenencia clara:** hard/high-confidence por régimen: {pd.DataFrame(eff)[['regime','hard_size','high_confidence_hard_n']].to_dict('records')}.
6. **Ambigüedad:** {counts}.
7. **Tamaños efectivos:** {pd.DataFrame(eff)[['regime','effective_size','hard_size','potentially_small']].round(2).to_dict('records')}.
8. **Variables diferenciadoras:** rango máximo estandarizado entre regímenes: {topvars}.
9. **Precipitación mensual:** perfiles completos en `monthly_regime_profiles.csv`; resumen Apr–Oct: {monthly_summary}.
10. **Temperatura y DTR:** el mismo resumen reporta Tmean/DTR y las figuras muestran Tmin/Tmax/Tmean/DTR por mes.
11. **Naturaleza de clusters:** se interpreta por la combinación de precipitación total/timing y temperatura/DTR indicada por los perfiles; no se asignan nombres agronómicos fuertes.
12. **Estructura espacial post hoc:** concordancia observada con 6 vecinos={spatial['observed_neighbor_agreement']:.3f}, referencia permutada={spatial['permutation_mean']:.3f}, p descriptivo={spatial['permutation_p_greater']:.3f}. Distribución por CONJUNTO: {geotab}. Es un diagnóstico posterior y no intervino en clustering.
13. **GMM vs K-means:** ARI={ari:.3f}; {'macroestructura semejante' if ari>=.6 else 'estructura débil o no esférica'}.
14. **Uso predictivo futuro:** {'la solución es suficientemente robusta para congelar memberships como candidatos target-free, todavía sin afirmar valor predictivo' if promising else 'no conviene promover memberships a features predictivas como solución discreta; conservar probabilidades sólo para diagnóstico'}.
15. **Avance a R2:** {'Sí, puede avanzarse a caracterización con la solución congelada y sin redefinirla usando yield' if promising else 'No todavía; los criterios conjuntos no sostienen regímenes múltiples estables'}.

## PCA y selección

PCs para 80/90/95%: {npc[.8]}/{npc[.9]}/{npc[.95]}. GMM se ajustó sobre {npc[.95]} PCs. Se evaluaron exclusivamente K=1..5 y covarianzas diagonal, tied y full con `reg_covar=1e-5`. Se excluyó de la selección toda solución que alcanzara el piso de covarianza; permanece en la tabla para auditoría. La tabla documenta likelihood, parámetros, convergencia, singularidad, BIC, AIC, silhouette, entropía y tamaños.

## Stop condition

No se abrió rendimiento, no se entrenaron modelos predictivos, no se ejecutó mixture-of-experts y no se inició Stage R2.
"""
    (D['report']/'climate_regime_discovery_report.md').write_text(report,encoding='utf-8')
    print(f'R1 complete: K={chosen}, covariance={best_cov[chosen]}, promising={promising}, PCs95={npc[.95]}')

if __name__=='__main__':main()
