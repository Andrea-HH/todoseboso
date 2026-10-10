"""F3.1.1 target-free structural representations and probabilistic memberships."""
from pathlib import Path
import json,warnings,joblib
import numpy as np,pandas as pd
import matplotlib.pyplot as plt,seaborn as sns
from scipy.linalg import orthogonal_procrustes,subspace_angles
from scipy.optimize import linear_sum_assignment
from scipy.stats import spearmanr
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA,FactorAnalysis
from sklearn.mixture import GaussianMixture
from sklearn.model_selection import KFold
from sklearn.metrics import adjusted_rand_score
warnings.filterwarnings('ignore');sns.set_theme(style='whitegrid')
ROOT=Path(__file__).resolve().parents[2];SRC=ROOT/'data/processed/family_1';AUD=ROOT/'outputs/modeling/family_3/f3_1_0_structural_audit';BASE=ROOT/'outputs/modeling/family_3/f3_1_1_structural_representation';T=BASE/'tables';F=BASE/'figures';M=BASE/'models';R=BASE/'report'
for p in [T,F,M,R]:p.mkdir(parents=True,exist_ok=True)
ID='ID_POLIGONO';SEED=2026;NBOOT=100
COMPACT=['HIST_S2_ndvi_promedio_mean','HIST_S2_ndvi_promedio_std','HIST_S2_ndwi_promedio_mean','HIST_S2_msi_promedio_mean','HIST_S2_nddi_promedio_mean','HIST_S2_nddi_promedio_std','TOPO_BASIC_elevation_mean','TOPO_BASIC_elevation_relief','TOPO_BASIC_slope_mean','TOPO_BASIC_slope_iqr','TOPO_BASIC_pct_area_slope_gt_10']
def build_data():
 h=pd.read_parquet(SRC/'features/history_features.parquet');t=pd.read_parquet(SRC/'features/topography_basic_features.parquet');s=pd.read_parquet(SRC/'timeseries/sentinel_timeseries.parquet',columns=[ID,'CONJUNTO']).drop_duplicates();d=s.merge(h,on=ID).merge(t,on=ID);hist=[c for c in h if c.startswith('HIST_S2_') and not c.endswith('_months')];top=[c for c in t if c.startswith('TOPO_BASIC_')];return d,hist,top
def specs(hist,top):
 return {'A1_COMPACT':{'cols':COMPACT,'balance':False,'role':'primary'},'A2_FULL_BALANCED':{'cols':hist+top,'balance':True,'role':'primary'},'A2_FULL_UNBALANCED':{'cols':hist+top,'balance':False,'role':'scaling_sensitivity'},'A3_SENTINEL_ONLY':{'cols':hist,'balance':False,'role':'source_ablation'},'A3_TOPO_ONLY':{'cols':top,'balance':False,'role':'source_ablation'}}
class Prep:
 def __init__(self,cols,hist,top,balance):self.cols=cols;self.hist=hist;self.top=top;self.balance=balance
 def fit(self,X):
  self.imp=SimpleImputer(strategy='median').fit(X[self.cols]);z=self.imp.transform(X[self.cols]);self.scaler=StandardScaler().fit(z);self.scaler.scale_[self.scaler.scale_<1e-8]=1.;self.weights=np.ones(len(self.cols));
  if self.balance:
   nh=sum(c in self.hist for c in self.cols);nt=sum(c in self.top for c in self.cols)
   for i,c in enumerate(self.cols):self.weights[i]=1/np.sqrt(nh) if c in self.hist else 1/np.sqrt(nt)
  return self
 def transform(self,X):return np.nan_to_num(self.scaler.transform(self.imp.transform(X[self.cols]))*self.weights,nan=0.,posinf=0.,neginf=0.)
def source_contrib(load,cols,hist):
 sq=load**2;den=sq.sum(axis=1);return [{'component':j+1,'sentinel_fraction':sq[j,[c in hist for c in cols]].sum()/den[j],'topography_fraction':sq[j,[c not in hist for c in cols]].sum()/den[j]} for j in range(load.shape[0])]
def fit_latent(kind,k,Z,seed=SEED):
 m=PCA(k,random_state=seed) if kind=='PCA' else FactorAnalysis(k,random_state=seed,max_iter=2000);return m.fit(Z)
def bootstrap_latent(X,refprep,refmodel,kind,k,sp,hist,top,rng):
 refZ=refprep.transform(X);refS=refmodel.transform(refZ);refL=refmodel.components_.T;rows=[]
 for b in range(NBOOT):
  ix=rng.integers(0,len(X),len(X));pr=Prep(sp['cols'],hist,top,sp['balance']).fit(X.iloc[ix]);Zb=pr.transform(X.iloc[ix]);m=fit_latent(kind,k,Zb,SEED+b);Sb=m.transform(pr.transform(X));Lb=m.components_.T;ang=np.degrees(subspace_angles(refL,Lb));Q,_=orthogonal_procrustes(Sb,refS);Sa=Sb@Q;rows.append({'bootstrap':b,'mean_principal_angle_deg':ang.mean(),'max_principal_angle_deg':ang.max(),'mean_score_correlation':np.mean([abs(spearmanr(refS[:,j],Sa[:,j]).statistic) for j in range(k)]),'aligned_score_rmse':np.sqrt(np.mean((Sa-refS)**2))})
 return pd.DataFrame(rows)
def gmm_cv_ll(S,k,cov):
 vals=[]
 for a,b in KFold(5,shuffle=True,random_state=SEED).split(S):
  try:vals.append(GaussianMixture(k,covariance_type=cov,reg_covar=1e-5,n_init=20,random_state=SEED).fit(S[a]).score(S[b]))
  except Exception:vals.append(np.nan)
 return np.nanmean(vals)
def align_probs(ref,cand):
 C=np.corrcoef(ref.T,cand.T)[:ref.shape[1],ref.shape[1]:];a,b=linear_sum_assignment(-np.nan_to_num(C));return cand[:,b[np.argsort(a)]]
def bootstrap_gmm(X,sp,hist,top,kind,kdim,K,cov,refP,refhard,rng):
 rows=[]
 for b in range(NBOOT):
  ix=rng.integers(0,len(X),len(X));pr=Prep(sp['cols'],hist,top,sp['balance']).fit(X.iloc[ix]);lat=fit_latent(kind,kdim,pr.transform(X.iloc[ix]),SEED+b);Sa=lat.transform(pr.transform(X));
  try:
   gm=GaussianMixture(K,covariance_type=cov,reg_covar=1e-5,n_init=10,random_state=SEED+b).fit(Sa[ix]);P=gm.predict_proba(Sa);P=align_probs(refP,P);hard=P.argmax(1);rows.append({'bootstrap':b,'ARI':adjusted_rand_score(refhard,hard),'membership_MAE':abs(P-refP).mean(),'coassignment_agreement':np.mean((hard[:,None]==hard[None,:])==(refhard[:,None]==refhard[None,:])),'min_effective_size':P.sum(0).min(),'converged':gm.converged_})
  except Exception:rows.append({'bootstrap':b,'ARI':np.nan,'membership_MAE':np.nan,'coassignment_agreement':np.nan,'min_effective_size':np.nan,'converged':False})
 return pd.DataFrame(rows)
def main():
 d,hist,top=build_data();train=d[d.CONJUNTO.eq('ENTRENAMIENTO')].reset_index(drop=True);pred=d[d.CONJUNTO.eq('PREDICCION')].reset_index(drop=True);assert len(train)==138 and len(pred)==59;SPECS=specs(hist,top);rng=np.random.default_rng(SEED);rep=[];stab=[];coords=[];models={};source=[]
 for name,sp in SPECS.items():
  pr=Prep(sp['cols'],hist,top,sp['balance']).fit(train);zt=pr.transform(train);zp=pr.transform(pred)
  for kind in ['PCA','FA']:
   dims=[1,2,3,4] if kind=='PCA' else [2,3,4]
   for k in dims:
    m=fit_latent(kind,k,zt);st=m.transform(zt);sv=m.transform(zp);expl=m.explained_variance_ratio_.sum() if kind=='PCA' else np.nan;comm=np.mean(np.sum(m.components_**2,axis=0)) if kind=='FA' else np.nan;specvar=np.mean(m.noise_variance_) if kind=='FA' else np.nan;b=bootstrap_latent(train,pr,m,kind,k,sp,hist,top,rng);bid=f'{name}_{kind}{k}';rep.append({'representation_id':bid,'input_id':name,'role':sp['role'],'method':kind,'latent_dim':k,'n_original_features':len(sp['cols']),'block_balanced':sp['balance'],'explained_variance':expl,'mean_communality':comm,'mean_specific_variance':specvar,'bootstrap_mean_angle_deg':b.mean_principal_angle_deg.mean(),'bootstrap_mean_score_correlation':b.mean_score_correlation.mean(),'bootstrap_aligned_score_rmse':b.aligned_score_rmse.mean(),'prediction_outside_train_score_range_pct':np.mean([(sv[:,j]<st[:,j].min()).mean()+(sv[:,j]>st[:,j].max()).mean() for j in range(k)])*100})
    b.insert(0,'representation_id',bid);stab.append(b);source.extend([{'representation_id':bid,**x} for x in source_contrib(m.components_,sp['cols'],hist)])
    for grp,ids,sc in [('TRAIN',train[ID],st),('PREDICTION',pred[ID],sv)]:
     for i,pid in enumerate(ids):coords.append({ID:pid,'CONJUNTO':grp,'representation_id':bid,**{f'F{j+1}':sc[i,j] for j in range(k)}})
    models[bid]={'preprocessor':pr,'latent_model':m,'columns':sp['cols'],'note':'inductive structural model; not predictively validated'}
 rep=pd.DataFrame(rep);pd.DataFrame([{'input_id':n,'role':s['role'],'n_features':len(s['cols']),'block_balanced':s['balance'],'variables':json.dumps(s['cols']),'selection_rule':'predefined target-free conceptual representatives' if n=='A1_COMPACT' else 'all eligible nonconstant variables'} for n,s in SPECS.items()]).to_csv(T/'01_representation_specifications.csv',index=False);rep.to_csv(T/'02_continuous_factor_comparison.csv',index=False);pd.concat(stab).to_csv(T/'03_bootstrap_factor_stability.csv',index=False);pd.DataFrame(coords).to_parquet(T/'04_structural_coordinates.parquet',index=False);pd.DataFrame(source).to_csv(T/'05_source_contributions.csv',index=False)
 # GMM only on predeclared 3D spaces; PCA primary, FA sensitivity.
 grow=[];probs=[];gstab=[]
 for rid in ['A1_COMPACT_PCA3','A2_FULL_BALANCED_PCA3','A3_SENTINEL_ONLY_PCA3','A3_TOPO_ONLY_PCA3','A2_FULL_BALANCED_FA3']:
  name=rid.rsplit('_',1)[0];kind='FA' if rid.endswith('FA3') else 'PCA';sp=SPECS[name];pr=models[rid]['preprocessor'];lat=models[rid]['latent_model'];St=lat.transform(pr.transform(train));Sp=lat.transform(pr.transform(pred))
  for K in [1,2,3]:
   for cov in ['diag','tied']:
    gm=GaussianMixture(K,covariance_type=cov,reg_covar=1e-5,n_init=50,random_state=SEED).fit(St);Pt=gm.predict_proba(St);Pp=gm.predict_proba(Sp);hard=Pt.argmax(1);ent=np.zeros(len(Pt)) if K==1 else -(Pt*np.log(Pt+1e-12)).sum(1)/np.log(K);bid=f'{rid}_GMM{K}_{cov}';bs=bootstrap_gmm(train,sp,hist,top,kind,3,K,cov,Pt,hard,rng) if K>1 else pd.DataFrame([{'bootstrap':i,'ARI':1,'membership_MAE':0,'coassignment_agreement':1,'min_effective_size':len(train),'converged':True} for i in range(NBOOT)]);bs.insert(0,'gmm_id',bid);gstab.append(bs);sizes=Pt.sum(0);grow.append({'gmm_id':bid,'representation_id':rid,'K':K,'covariance_type':cov,'BIC':gm.bic(St),'train_log_likelihood':gm.score(St),'cv_log_likelihood':gmm_cv_ll(St,K,cov),'converged':gm.converged_,'min_effective_size':sizes.min(),'max_effective_size':sizes.max(),'mean_max_probability':Pt.max(1).mean(),'mean_normalized_entropy':ent.mean(),'ambiguous_below_0_70_pct':(Pt.max(1)<.7).mean()*100,'bootstrap_ARI':bs.ARI.mean(),'bootstrap_membership_MAE':bs.membership_MAE.mean(),'bootstrap_coassignment':bs.coassignment_agreement.mean(),'bootstrap_convergence':bs.converged.mean()})
    for grp,ids,P in [('TRAIN',train[ID],Pt),('PREDICTION',pred[ID],Pp)]:
     for i,pid in enumerate(ids):probs.append({ID:pid,'CONJUNTO':grp,'gmm_id':bid,'hard_component':int(P[i].argmax()+1),'max_probability':P[i].max(),'normalized_entropy':0 if K==1 else -(P[i]*np.log(P[i]+1e-12)).sum()/np.log(K),**{f'prob_component_{j+1}':P[i,j] for j in range(K)}})
 pd.DataFrame(grow).to_csv(T/'06_gmm_membership_comparison.csv',index=False);pd.concat(gstab).to_csv(T/'07_bootstrap_gmm_stability.csv',index=False);pd.DataFrame(probs).to_parquet(T/'08_gmm_membership_probabilities.parquet',index=False)
 # Sensitivity and geographic diagnostic.
 c=pd.DataFrame(coords);wide=c[c.CONJUNTO.eq('TRAIN')&c.representation_id.isin(['A1_COMPACT_PCA3','A2_FULL_BALANCED_PCA3'])].pivot(index=ID,columns='representation_id',values=['F1','F2','F3']);A=wide.xs('A1_COMPACT_PCA3',level=1,axis=1).to_numpy();B=wide.xs('A2_FULL_BALANCED_PCA3',level=1,axis=1).to_numpy();Q,_=orthogonal_procrustes(A,B);pd.DataFrame([{'comparison':'A1 compact vs A2 balanced PCA3','mean_aligned_factor_spearman':np.mean([abs(spearmanr((A@Q)[:,j],B[:,j]).statistic) for j in range(3)]),'procrustes_RMSE':np.sqrt(np.mean((A@Q-B)**2))}]).to_csv(T/'09_representation_sensitivity.csv',index=False)
 try:
  import geopandas as gpd
  geo=gpd.read_file(ROOT/'data/original/02_conjunto_70_30/Parcelas_Reto_AGC_CONJUNTO.shp').to_crs(6372);cent=pd.DataFrame({ID:geo['ID_POLIGON'].astype(str),'x':geo.geometry.centroid.x,'y':geo.geometry.centroid.y});gg=[]
  for rid in ['A1_COMPACT_PCA3','A2_FULL_BALANCED_PCA3']:
   z=c[(c.CONJUNTO=='TRAIN')&(c.representation_id==rid)].merge(cent,on=ID)
   for f in ['F1','F2','F3']:gg.append({'representation_id':rid,'factor':f,'spearman_x':spearmanr(z[f],z.x).statistic,'spearman_y':spearmanr(z[f],z.y).statistic})
  pd.DataFrame(gg).to_csv(T/'10_geographic_gradient_diagnostic.csv',index=False)
 except Exception:pd.DataFrame(columns=['representation_id','factor','spearman_x','spearman_y']).to_csv(T/'10_geographic_gradient_diagnostic.csv',index=False)
 joblib.dump({'version':'F3.1.1','seed':SEED,'models':models},M/'f3_1_1_structural_models.joblib')
 figures(rep,pd.DataFrame(source),pd.DataFrame(coords),pd.DataFrame(grow),pd.DataFrame(probs));report(rep,pd.DataFrame(grow),pd.DataFrame(source))
def figures(rep,src,coord,gmm,prob):
 q=rep[rep.method.eq('PCA')];plt.figure(figsize=(9,4));sns.lineplot(q,x='latent_dim',y='explained_variance',hue='input_id',marker='o');plt.tight_layout();plt.savefig(F/'01_pca_cumulative_variance.png',dpi=180);plt.close();plt.figure(figsize=(9,4));sns.lineplot(rep,x='latent_dim',y='bootstrap_mean_score_correlation',hue='representation_id',legend=False,marker='o');plt.tight_layout();plt.savefig(F/'02_factor_stability.png',dpi=180);plt.close()
 for n,rid in enumerate(['A1_COMPACT_PCA3','A2_FULL_BALANCED_PCA3'],3):
  z=coord[coord.representation_id.eq(rid)];plt.figure(figsize=(6,5));sns.scatterplot(z,x='F1',y='F2',hue='CONJUNTO');plt.title(f'{rid}: proyección 2D de espacio 3D');plt.tight_layout();plt.savefig(F/f'{n:02d}_{rid.lower()}_space.png',dpi=180);plt.close()
 q=gmm[(gmm.K>1)&gmm.representation_id.isin(['A1_COMPACT_PCA3','A2_FULL_BALANCED_PCA3'])];plt.figure(figsize=(9,4));sns.scatterplot(q,x='mean_normalized_entropy',y='bootstrap_ARI',hue='representation_id',style='K',size='mean_max_probability');plt.tight_layout();plt.savefig(F/'05_gmm_uncertainty_stability.png',dpi=180);plt.close();q=src[src.representation_id.eq('A2_FULL_BALANCED_PCA3')].melt(['representation_id','component']);plt.figure(figsize=(7,4));sns.barplot(q,x='component',y='value',hue='variable');plt.tight_layout();plt.savefig(F/'06_source_contribution.png',dpi=180);plt.close();q=prob[prob.gmm_id.eq('A2_FULL_BALANCED_PCA3_GMM2_diag')];plt.figure(figsize=(7,4));sns.histplot(q,x='max_probability',hue='CONJUNTO',element='step');plt.tight_layout();plt.savefig(F/'07_membership_probability.png',dpi=180);plt.close()
def report(rep,gmm,src):
 p=rep.set_index('representation_id');sens=pd.read_csv(T/'09_representation_sensitivity.csv').iloc[0];valid=gmm[(gmm.K>1)&(gmm.min_effective_size>=10)&(gmm.bootstrap_convergence>.95)];best=valid.sort_values('BIC').iloc[0] if len(valid) else None;geo=pd.read_csv(T/'10_geographic_gradient_diagnostic.csv');txt=f'''# F3.1.1 — Structural Representation & Membership Comparison\n\n## Controles\nAnálisis target-free ajustado exclusivamente con 138 TRAIN; 59 PREDICTION sólo se transformaron. No se cargó yield, Climate Current ni satélite 2025. Climate Historical no construyó representaciones. Bootstrap={NBOOT}, seed={SEED}.\n\n## Evidencia\n### A. Dimensionalidad y redundancia\nA1 compacta usa {int(p.loc['A1_COMPACT_PCA3','n_original_features'])} representantes predefinidos; A2 balanceada usa {int(p.loc['A2_FULL_BALANCED_PCA3','n_original_features'])}. PCA3 explica A1={p.loc['A1_COMPACT_PCA3','explained_variance']:.1%}, A2={p.loc['A2_FULL_BALANCED_PCA3','explained_variance']:.1%}. La similitud compacta–completa alineada es Spearman medio={sens.mean_aligned_factor_spearman:.3f}, RMSE Procrustes={sens.procrustes_RMSE:.3f}.\n\n### B. Factores continuos\nEstabilidad bootstrap PCA3: A1 corr={p.loc['A1_COMPACT_PCA3','bootstrap_mean_score_correlation']:.3f}, ángulo={p.loc['A1_COMPACT_PCA3','bootstrap_mean_angle_deg']:.1f}°; A2 corr={p.loc['A2_FULL_BALANCED_PCA3','bootstrap_mean_score_correlation']:.3f}, ángulo={p.loc['A2_FULL_BALANCED_PCA3','bootstrap_mean_angle_deg']:.1f}°. FA3 A2: corr={p.loc['A2_FULL_BALANCED_FA3','bootstrap_mean_score_correlation']:.3f}, comunalidad media={p.loc['A2_FULL_BALANCED_FA3','mean_communality']:.3f}. PCA y FA deben compararse como subespacios, no factor por índice.\n\n### C–D. Perfiles probabilísticos y estabilidad\nMejor GMM no trivial admisible por BIC: {best.gmm_id if best is not None else 'ninguno'}, tamaños mínimos={best.min_effective_size:.1f}, entropía={best.mean_normalized_entropy:.3f}, max-prob={best.mean_max_probability:.3f}, bootstrap ARI={best.bootstrap_ARI:.3f}, membership MAE={best.bootstrap_membership_MAE:.3f} {'' if best is not None else ''}. BIC es evidencia relativa, no prueba de clusters. K=1 permanece referencia legítima.\n\n### E. Transferencia a PREDICTION\nPorcentaje medio fuera del rango TRAIN por eje: A1 PCA3={p.loc['A1_COMPACT_PCA3','prediction_outside_train_score_range_pct']:.1f}%, A2 PCA3={p.loc['A2_FULL_BALANCED_PCA3','prediction_outside_train_score_range_pct']:.1f}%. No se usó PREDICTION para elegir dimensión/K.\n\n### F. Fuente y confusión\nContribuciones A2 PCA3: {src[src.representation_id.eq('A2_FULL_BALANCED_PCA3')].round(3).to_dict('records')}. Ablaciones Sentinel/Topography permiten verificar origen de ejes. Gradientes geográficos: {geo.round(3).to_dict('records')}; correlación espacial no implica causalidad. F3.1.0 ya mostró confusión parcial con precipitación histórica.\n\n## Respuestas obligatorias\n1–3. La compacta conserva una fracción importante pero no idéntica de A2; revisar sensibilidad y varianza explicada antes de reducir. Los factores dependen moderadamente de construcción y balanceo.\n4. La contribución por fuente está cuantificada por componente; el balance iguala varianza total inicial, no carga final.\n5–6. Las direcciones PCA son reproducibles si las correlaciones/ángulos anteriores son favorables; FA no debe preferirse si pierde estabilidad sin revelar covariación claramente distinta.\n7–11. La evidencia de multimodalidad depende de estabilidad, entropía y tamaños; no se acepta sólo por BIC. Las probabilidades conservan incertidumbre y las tablas reportan degeneración/tamaños.\n12. PREDICTION se proyecta sin reajuste; el porcentaje fuera de rango anterior resume extrapolación axial.\n13. Los perfiles se describen por coordenadas/probabilidades y no reciben nombres agronómicos.\n14. Ablaciones, contribución y gradientes muestran cuánto puede provenir de topografía/geografía; clima histórico sigue siendo confusor plausible.\n15. **Recomendación:** {'Opción 1 — factores continuos sin clusters' if best is None or best.bootstrap_ARI<.7 or best.mean_normalized_entropy>.35 else 'Opción 2 — factores continuos y memberships probabilísticos como competidores'}. Preferir A1 PCA3 si conserva estabilidad comparable; de lo contrario A2 balanceada PCA3.\n\n## Decisión para F3.1.2\nUsar factores continuos como referencia primaria. Sólo conservar memberships como candidato secundario si ARI≥0.70, tamaño efectivo mínimo≥10 y entropía≤0.35. Cualquier evaluación predictiva futura deberá reconstruir todo dentro de cada train fold. No se ejecutó F3.2.\n''';(R/'f3_1_1_structural_representation_report.md').write_text(txt,encoding='utf-8');pd.DataFrame([{'seed':SEED,'bootstrap_resamples':NBOOT,'fit_scope':'TRAIN only','prediction_role':'transform only','yield_used':False,'gmm_grid':'K=1,2,3; diag,tied','decision_rule':'continuous primary; GMM retained only if ARI>=.70,min size>=10,entropy<=.35'}]).to_csv(T/'11_decision_log.csv',index=False)
if __name__=='__main__':main()

def finalize_interpretation_artifacts():
 """Create transparent loading and component-profile tables from frozen F3.1.1 artifacts."""
 d,hist,top=build_data();train=d[d.CONJUNTO.eq('ENTRENAMIENTO')].reset_index(drop=True);portable={};
 for name,sp in specs(hist,top).items():
  pr=Prep(sp['cols'],hist,top,sp['balance']).fit(train);Z=pr.transform(train)
  for kind in ['PCA','FA']:
   for k in ([1,2,3,4] if kind=='PCA' else [2,3,4]):
    rid=f'{name}_{kind}{k}';portable[rid]={'columns':sp['cols'],'imputer':pr.imp,'scaler':pr.scaler,'weights':pr.weights,'latent_model':fit_latent(kind,k,Z),'block_balanced':sp['balance']}
 bundle={'version':'F3.1.1','seed':SEED,'models':portable,'serialization':'portable sklearn objects; no custom-class dependency'};joblib.dump(bundle,M/'f3_1_1_structural_models.joblib');bundle=joblib.load(M/'f3_1_1_structural_models.joblib');loads=[]
 for rid,obj in bundle['models'].items():
  model=obj['latent_model'];cols=obj['columns']
  for j,row in enumerate(model.components_):
   for c,v in zip(cols,row):loads.append({'representation_id':rid,'component':j+1,'feature':c,'block':'Sentinel Historical' if c in hist else 'Topography Basic','loading':v,'absolute_loading':abs(v)})
 pd.DataFrame(loads).to_csv(T/'12_latent_loadings.csv',index=False)
 probs=pd.read_parquet(T/'08_gmm_membership_probabilities.parquet');profiles=[]
 for gid in probs.gmm_id.unique():
  if '_GMM1_' in gid:continue
  rid=gid.split('_GMM')[0];obj=bundle['models'][rid];P=probs[(probs.gmm_id==gid)&(probs.CONJUNTO=='TRAIN')][[ID,'hard_component']];Z=obj['scaler'].transform(obj['imputer'].transform(train[obj['columns']]))*obj['weights'];z=pd.DataFrame(Z,columns=obj['columns']);z[ID]=train[ID].values;z=z.merge(P,on=ID)
  for comp,g in z.groupby('hard_component'):
   for c in obj['columns']:profiles.append({'gmm_id':gid,'component':comp,'feature':c,'block':'Sentinel Historical' if c in hist else 'Topography Basic','standardized_mean':g[c].mean(),'n_hard_members':len(g)})
 pd.DataFrame(profiles).to_csv(T/'13_gmm_component_profiles.csv',index=False)
