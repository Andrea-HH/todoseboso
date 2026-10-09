"""Etapa 4.1: correlación/pruning e interpretación PLS, sin nuevos modelos."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
import numpy as np,pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,RobustScaler
from sklearn.cross_decomposition import PLSRegression
from family_1.stage4_modeling import *

BASE=ROOT/'outputs/modeling/family_1/stage4_1';CORR=BASE/'correlation';PLSO=BASE/'pls';FIG=BASE/'figures';REP=BASE/'reports'
for p in [CORR,PLSO,FIG,REP]:p.mkdir(parents=True,exist_ok=True)
ids,X,y=load_xy();dictionary=pd.read_csv(FEATURE_DIR/'family1_feature_dictionary.csv').set_index('feature_name').reindex(X.columns)

# ---------------- Correlación descriptiva TRAIN ----------------
corr=X.corr().abs();iu=np.triu_indices_from(corr,1);vals=corr.to_numpy()[iu];vals=vals[np.isfinite(vals)]
pd.DataFrame({'abs_pearson_r':vals}).to_csv(CORR/'correlation_distribution.csv',index=False)
thresholds=[.80,.85,.90,.92,.95,.97,.98,.99]
pair_counts=pd.DataFrame([{'threshold':t,'n_pairs':int((vals>=t).sum()),'pct_pairs':100*(vals>=t).mean()} for t in thresholds])
pair_counts.to_csv(CORR/'correlation_pair_counts.csv',index=False)

def source_priority(c):
 row=dictionary.loc[c];return (X[c].isna().mean(),0 if str(row.core_or_extended)=='CORE' else 1,c)

sens=[];groups=[]
for t in [.85,.90,.92,.95,.97,.98,.99]:
 g=nx.Graph();g.add_nodes_from(X.columns);i,j=np.where(np.triu(corr.to_numpy()>=t,1));g.add_edges_from((X.columns[a],X.columns[b]) for a,b in zip(i,j))
 comps=[sorted(c) for c in nx.connected_components(g) if len(c)>1]
 priority=sorted([c for c in X if X[c].std()>1e-10],key=source_priority);kept=[]
 for c in priority:
  if not kept or not (corr.loc[c,kept]>=t).any():kept.append(c)
 sizes=[len(c) for c in comps]
 sens.append({'threshold':t,'features_retained':len(kept),'features_removed':X.shape[1]-len(kept),'pct_reduced':100*(X.shape[1]-len(kept))/X.shape[1],
              'n_correlated_components':len(comps),'largest_component_size':max(sizes,default=1),'median_component_size':np.median(sizes) if sizes else 1,
              'q90_component_size':np.quantile(sizes,.9) if sizes else 1,'features_in_correlated_components':sum(sizes)})
 for k,c in enumerate(comps):groups.append({'threshold':t,'component_id':k,'size':len(c),'features':'|'.join(c)})
sens=pd.DataFrame(sens);sens['delta_retained_vs_previous_threshold']=sens.features_retained.diff();sens.to_csv(CORR/'correlation_threshold_sensitivity.csv',index=False)
pd.DataFrame(groups).to_csv(CORR/'correlation_group_sizes.csv',index=False)

sns.set_theme(style='whitegrid')
fig,ax=plt.subplots(figsize=(8,5));ax.hist(vals,bins=100,color='#386cb0');ax.set(xlabel='|Pearson r|',ylabel='Número de pares',title='Distribución completa de correlación entre features (TRAIN)');fig.tight_layout();fig.savefig(FIG/'01_correlation_distribution.png',dpi=180);plt.close(fig)
tail=vals[vals>=.70];fig,ax=plt.subplots(figsize=(8,5));ax.hist(tail,bins=60,color='#7fc97f');ax.set(xlabel='|Pearson r|',ylabel='Número de pares',title='Cola de correlaciones |r| ≥ 0.70');fig.tight_layout();fig.savefig(FIG/'02_correlation_tail_ge_070.png',dpi=180);plt.close(fig)
sv=np.sort(vals);fig,ax=plt.subplots(figsize=(8,5));ax.plot(sv,np.arange(1,len(sv)+1)/len(sv));ax.set(xlabel='|Pearson r|',ylabel='ECDF',title='ECDF de correlaciones absolutas');fig.tight_layout();fig.savefig(FIG/'03_correlation_ecdf.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(8,5));ax.plot(sens.threshold,sens.features_retained,marker='o');
for _,r in sens.iterrows():ax.annotate(str(int(r.features_retained)),(r.threshold,r.features_retained),xytext=(0,7),textcoords='offset points',ha='center',fontsize=8)
ax.set(xlabel='Threshold |r|',ylabel='Features retenidas',title='Sensibilidad del pruning determinístico');fig.tight_layout();fig.savefig(FIG/'04_pruning_sensitivity.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(8,5));ax.plot(sens.threshold,sens.largest_component_size,marker='o',label='Mayor componente');ax.plot(sens.threshold,sens.q90_component_size,marker='s',label='Q90 tamaño');ax.legend();ax.set(xlabel='Threshold |r|',ylabel='Número de features',title='Tamaño de grupos correlacionados');fig.tight_layout();fig.savefig(FIG/'05_correlation_group_sizes.png',dpi=180);plt.close(fig)

# ---------------- Reconstrucción PLS por outer fold ----------------
stage4=ROOT/'outputs/modeling/family_1/stage4';splits=pd.read_csv(stage4/'splits/outer_splits.csv');hyper=pd.read_csv(stage4/'screening/selected_hyperparameters.csv');reps=representations(X.columns);id_to_i={v:i for i,v in enumerate(ids)}
raw=[];foldmeta=[];oof=[];verification=[]
for pipeline,rep in [('PLS_CORE','CORE'),('PLS_ALL','ALL')]:
 features=reps[rep];p=len(features)
 for k,s in splits.iterrows():
  tr=np.array([id_to_i[v] for v in json.loads(s.train_ID_POLIGONO)]);va=np.array([id_to_i[v] for v in json.loads(s.validation_ID_POLIGONO)])
  pars=json.loads(hyper[(hyper.pipeline==pipeline)&(hyper['repeat']==s['repeat'])&(hyper.fold==s['fold'])].best_params.iloc[0]);ncomp=int(pars['model__n_components']);scaler_name=pars.get('scaler','StandardScaler')
  imp=SimpleImputer(strategy='median');zt=imp.fit_transform(X.iloc[tr][features]);zv=imp.transform(X.iloc[va][features]);scaler=RobustScaler() if scaler_name=='RobustScaler' else StandardScaler();zt=scaler.fit_transform(zt);zv=scaler.transform(zv)
  model=PLSRegression(n_components=ncomp,scale=False,max_iter=1000).fit(zt,y.iloc[tr]);W=model.x_weights_.copy();P=model.x_loadings_.copy();T=model.x_scores_.copy();Q=model.y_loadings_.reshape(-1).copy()
  # Orientación reproducible: y_loading positivo en cada componente.
  signs=np.where(Q<0,-1.,1.);W*=signs;P*=signs;T*=signs;Q*=signs;scores=np.asarray(model.transform(zv))*signs
  ssy=np.sum(T*T,axis=0)*(Q*Q);den=ssy.sum();vip=np.sqrt(p*((W*W/(W*W).sum(axis=0))*ssy).sum(axis=1)/den) if den>0 else np.full(p,np.nan)
  verification.append({'pipeline':pipeline,'repeat':s['repeat'],'fold':s['fold'],'n_components':ncomp,'mean_vip_squared':np.nanmean(vip**2),'expected':1.0,'max_abs_error':abs(np.nanmean(vip**2)-1)})
  coef=np.asarray(model.coef_).reshape(-1)
  for j,f in enumerate(features):
   raw.append({'pipeline':pipeline,'repeat':s['repeat'],'fold':s['fold'],'feature_name':f,'vip':vip[j],'coefficient_scaled_x':coef[j],
               'weight_component_1':W[j,0],'weight_component_2':W[j,1] if ncomp>=2 else np.nan,'loading_component_1':P[j,0],'loading_component_2':P[j,1] if ncomp>=2 else np.nan})
  foldmeta.append({'pipeline':pipeline,'repeat':s['repeat'],'fold':s['fold'],'n_components':ncomp,'scaler':scaler_name,'y_loading_component_1':Q[0],'y_loading_component_2':Q[1] if ncomp>=2 else np.nan,
                   'train_score_1_mean':T[:,0].mean(),'train_score_1_std':T[:,0].std(),'train_score_2_mean':T[:,1].mean(),'train_score_2_std':T[:,1].std()})
  for pos,idx in enumerate(va):oof.append({'pipeline':pipeline,'ID_POLIGONO':ids.iloc[idx],'repeat':s['repeat'],'fold':s['fold'],'PLS1_OOF':scores[pos,0],'PLS2_OOF':scores[pos,1],'y_true':y.iloc[idx]})
raw=pd.DataFrame(raw);raw.to_parquet(PLSO/'pls_fold_feature_diagnostics.parquet',index=False);pd.DataFrame(foldmeta).to_csv(PLSO/'pls_fold_component_diagnostics.csv',index=False);pd.DataFrame(oof).to_parquet(PLSO/'pls_oof_scores.parquet',index=False);pd.DataFrame(verification).to_csv(PLSO/'pls_vip_formula_verification.csv',index=False)

# Taxonomía interpretable.
def source(c):
 for pre,n in [('TOPO_ADV_','Topography Advanced'),('TOPO_BASIC_','Topography Basic'),('PLANET_','Planet'),('LANDSAT_','Landsat'),('CLIMATE_','Climate'),('HIST_','History'),('ANOM_','Anomaly'),('S2_','Sentinel')]:
  if c.startswith(pre):return n
 return 'Other'
def temporal_family(c):
 cl=c.lower()
 for token,n in [('drawdown','drawdown'),('runup','runup'),('max_growth','growth'),('positive_change','growth'),('max_decline','decline'),('negative_change','decline'),('peak','peak'),('_day','timing'),('_doy','timing'),('duration','timing'),('auc','AUC'),('anomaly','anomaly'),('anom_','anomaly'),('hist_','historical')]:
  if token in cl:return n
 if any(x in cl for x in ['derived_range','lower_gap','upper_gap','derived_cv','_std_']):return 'heterogeneity'
 if any(x in cl for x in ['slope','last_minus_first','relative_change','total_variation']):return 'trajectory_change'
 if any(x in cl for x in ['mean','median','min','max','q10','q25','q75','q90','iqr','skew','kurt']):return 'level/distribution'
 return 'other'
def spatial(c):
 cl=c.lower()
 for token,n in [('derived_lower_gap','lower_gap'),('derived_upper_gap','upper_gap'),('derived_range','range'),('derived_cv','cv'),('_promedio_','mean'),('_std_','std'),('_min_','min'),('_max_','max')]:
  if token in cl:return n
 return 'not_applicable'
raw['source']=raw.feature_name.map(source);raw['temporal_feature_family']=raw.feature_name.map(temporal_family);raw['spatial_statistic']=raw.feature_name.map(spatial);raw['variable']=raw.feature_name.map(dictionary.variable.to_dict()).fillna('unknown')
agg=raw.groupby(['pipeline','feature_name']).agg(mean_vip=('vip','mean'),median_vip=('vip','median'),std_vip=('vip','std'),proportion_folds_vip_gt_1=('vip',lambda x:(x>1).mean()),mean_abs_weight_component_1=('weight_component_1',lambda x:abs(x).mean()),mean_abs_weight_component_2=('weight_component_2',lambda x:abs(x).mean()),loading_1_sign_stability=('loading_component_1',lambda x:max((x>0).mean(),(x<0).mean())),loading_2_sign_stability=('loading_component_2',lambda x:max((x>0).mean(),(x<0).mean())),mean_abs_coefficient=('coefficient_scaled_x',lambda x:abs(x).mean()),n_folds=('vip','size')).reset_index()
tax=raw[['pipeline','feature_name','source','variable','temporal_feature_family','spatial_statistic']].drop_duplicates();agg=agg.merge(tax,on=['pipeline','feature_name']);agg.to_csv(PLSO/'pls_feature_vip_stability.csv',index=False)
family=[]
for dimension in ['source','variable','temporal_feature_family','spatial_statistic']:
 z=agg.groupby(['pipeline',dimension]).agg(n_features=('feature_name','size'),mean_feature_mean_vip=('mean_vip','mean'),median_feature_mean_vip=('mean_vip','median'),mean_vip_gt1_frequency=('proportion_folds_vip_gt_1','mean'),component_1_abs_weight=('mean_abs_weight_component_1','sum'),component_2_abs_weight=('mean_abs_weight_component_2','sum')).reset_index().rename(columns={dimension:'group'});z['aggregation_dimension']=dimension;family.append(z)
fam=pd.concat(family,ignore_index=True);fam.to_csv(PLSO/'pls_family_vip_summary.csv',index=False)
loads=[]
for dimension in ['source','variable','temporal_feature_family','spatial_statistic']:
 z=agg.groupby(['pipeline',dimension]).agg(component_1_mean_abs_weight=('mean_abs_weight_component_1','mean'),component_2_mean_abs_weight=('mean_abs_weight_component_2','mean'),component_1_total_abs_weight=('mean_abs_weight_component_1','sum'),component_2_total_abs_weight=('mean_abs_weight_component_2','sum'),mean_loading_1_sign_stability=('loading_1_sign_stability','mean'),mean_loading_2_sign_stability=('loading_2_sign_stability','mean')).reset_index().rename(columns={dimension:'group'});z['aggregation_dimension']=dimension;loads.append(z)
pd.concat(loads,ignore_index=True).to_csv(PLSO/'pls_component_loadings_summary.csv',index=False)
src=fam[fam.aggregation_dimension=='source'].copy();src['component_1_contribution_pct']=100*src.component_1_abs_weight/src.groupby('pipeline').component_1_abs_weight.transform('sum');src['component_2_contribution_pct']=100*src.component_2_abs_weight/src.groupby('pipeline').component_2_abs_weight.transform('sum');src.to_csv(PLSO/'pls_source_contribution.csv',index=False)

oo=pd.DataFrame(oof);fig,axes=plt.subplots(1,2,figsize=(13,5),sharex=False,sharey=False)
for ax,(pipeline,g) in zip(axes,oo.groupby('pipeline')):
 sc=ax.scatter(g.PLS1_OOF,g.PLS2_OOF,c=g.y_true,cmap='viridis',s=14,alpha=.55);ax.set(title=f'{pipeline}: scores estrictamente OOF',xlabel='PLS1',ylabel='PLS2');fig.colorbar(sc,ax=ax,label='Rendimiento t/ha')
fig.tight_layout();fig.savefig(FIG/'06_pls_oof_scores.png',dpi=180);plt.close(fig)

# Reporte automático descriptivo.
top_sources=src.sort_values(['pipeline','component_1_contribution_pct'],ascending=[True,False]).groupby('pipeline').head(3)
top_families=fam[fam.aggregation_dimension=='temporal_feature_family'].sort_values(['pipeline','mean_feature_mean_vip'],ascending=[True,False]).groupby('pipeline').head(5)
mega=sens.sort_values('threshold');mega['largest_share_pct']=100*mega.largest_component_size/X.shape[1]
candidates=[.90,.95,.98]
report=f'''# Familia 1 — Etapa 4.1 diagnóstica

No se ejecutaron modelos de Ronda 2 ni se modificaron resultados de Etapa 4. La correlación general usa exclusivamente las 138 parcelas TRAIN; cualquier pruning futuro deberá reaprenderse dentro de cada train fold.

## Correlación y pruning

Pares por threshold: {pair_counts.to_dict('records')}.

Sensibilidad: {sens.to_dict('records')}.

El mayor salto en retención entre thresholds consecutivos fue {int(sens.delta_retained_vs_previous_threshold.abs().max())} features. La evolución del mayor componente permite detectar el chain effect: {mega[['threshold','largest_component_size','largest_share_pct']].round(2).to_dict('records')}.

No se elige threshold ganador. Se recomiendan **{candidates}** para nested CV: 0.90 como pruning fuerte, 0.95 intermedio y 0.98 conservador/referencia actual.

## Interpretación PLS

VIP implementado como `sqrt(p * sum_a(SSY_a * (w_ja/||w_a||)^2) / sum_a SSY_a)`, con `SSY_a = sum(t_a^2) * q_a^2`. La verificación numérica exige `mean(VIP^2)=1`; error máximo observado={pd.DataFrame(verification).max_abs_error.max():.3e}.

Contribuciones dominantes por fuente y componente: {top_sources[['pipeline','group','component_1_contribution_pct','component_2_contribution_pct']].round(2).to_dict('records')}.

Familias temporales con VIP agregado más alto: {top_families[['pipeline','group','mean_feature_mean_vip','mean_vip_gt1_frequency']].round(3).to_dict('records')}.

La estructura macro se repite en CORE y ALL. En contribución total, PLS1 combina satélite con más peso relativo de clima/anomalía/histórico; PLS2 se concentra todavía más en Sentinel/Planet y en heterogeneidad/AUC. La suma por fuente está influida por el número de columnas: Sentinel domina el total porque contiene muchas features, mientras **Climate tiene el VIP promedio por feature más alto** (CORE={src[(src.pipeline=='PLS_CORE')&(src.group=='Climate')].mean_feature_mean_vip.iloc[0]:.3f}; ALL={src[(src.pipeline=='PLS_ALL')&(src.group=='Climate')].mean_feature_mean_vip.iloc[0]:.3f}).

Las features climáticas y anomalías climáticas encabezan el ranking estable. Algunas features individuales CORE cambian más en magnitud/signo del segundo loading, pero los rankings por fuente y familia son más consistentes; esto favorece interpretar constructos agregados y no convertir VIP en selector automático.

PLS1 y PLS2 son diferenciables cuando sus rankings agregados divergen; consultar `pls_component_loadings_summary.csv`. La estabilidad debe interpretarse a nivel familia además de feature individual. `VIP>1` es sólo descriptor y no regla de selección.

La figura PLS usa únicamente scores de validation transformados por modelos ajustados en el outer train correspondiente. El rendimiento sólo colorea puntos y no ajusta una transformación nueva.

## Ajuste recomendado del grid de Ronda 2

- Probar thresholds 0.90, 0.95 y 0.98 dentro del inner CV para XGB/LGBM/ElasticNet PRUNED.
- Mantener la regla determinística: menor missingness, CORE antes que EXTENDED y desempate lexicográfico.
- No utilizar VIP para filtrar features en Ronda 2; usarlo únicamente para interpretación posterior.
- No ampliar PLS por encima de la pequeña rejilla actual: los resultados previos favorecen dos componentes.
'''
(REP/'family1_stage4_1_diagnostics.md').write_text(report,encoding='utf-8')
print(sens.to_string(index=False));print('VIP error máximo:',pd.DataFrame(verification).max_abs_error.max());print('Reporte:',REP/'family1_stage4_1_diagnostics.md')
