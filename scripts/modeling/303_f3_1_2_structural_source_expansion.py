"""F3.1.2 target-free audit of Topography Advanced and structural expansion."""
from pathlib import Path
import json,warnings,joblib,importlib.util
import numpy as np,pandas as pd
import matplotlib.pyplot as plt,seaborn as sns
from scipy.linalg import orthogonal_procrustes,subspace_angles
from scipy.stats import spearmanr,ks_2samp
from scipy.optimize import linear_sum_assignment
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score,adjusted_rand_score
from sklearn.mixture import GaussianMixture
warnings.filterwarnings('ignore');sns.set_theme(style='whitegrid')
ROOT=Path(__file__).resolve().parents[2];SRC=ROOT/'data/processed/family_1/features';OLD=ROOT/'outputs/modeling/family_3/f3_1_1_structural_representation';BASE=ROOT/'outputs/modeling/family_3/f3_1_2_structural_source_expansion';T=BASE/'tables';F=BASE/'figures';M=BASE/'models';R=BASE/'report'
for p in [T,F,M,R]:p.mkdir(parents=True,exist_ok=True)
ID='ID_POLIGONO';SEED=2026;NBOOT=100
def family(c):
 for x in ['aspect_sin','aspect_cos','local_relief_3x3','tpi_3x3','plan_curvature','profile_curvature','flow_accumulation_log1p','twi']:
  if x in c:return x
 return 'other'
class Prep:
 def __init__(self,blocks):self.blocks=blocks;self.cols=sum(blocks.values(),[])
 def fit(self,d):
  self.imp=SimpleImputer(strategy='median').fit(d[self.cols]);z=self.imp.transform(d[self.cols]);self.sc=StandardScaler().fit(z);self.sc.scale_[self.sc.scale_<1e-8]=1;self.w=np.concatenate([np.repeat(1/np.sqrt(len(v)),len(v)) for v in self.blocks.values()]);return self
 def transform(self,d):return np.nan_to_num(self.sc.transform(self.imp.transform(d[self.cols]))*self.w)
def eff(Z):
 s=np.linalg.svd(Z,compute_uv=False);e=s*s/(s*s).sum();return 1/(e*e).sum(),np.searchsorted(np.cumsum(e),.9)+1
def distcorr(A,B):
 da=np.linalg.norm(A[:,None]-A[None,:],axis=2);db=np.linalg.norm(B[:,None]-B[None,:],axis=2);ix=np.triu_indices(len(A),1);return spearmanr(da[ix],db[ix]).statistic
def boot_pca(train,blocks,ref,k=3):
 rng=np.random.default_rng(SEED);refS=ref['pca'].transform(ref['prep'].transform(train));refL=ref['pca'].components_.T;rows=[]
 for b in range(NBOOT):
  ix=rng.integers(0,len(train),len(train));pr=Prep(blocks).fit(train.iloc[ix]);m=PCA(k,random_state=SEED+b).fit(pr.transform(train.iloc[ix]));S=m.transform(pr.transform(train));L=m.components_.T;ang=np.degrees(subspace_angles(refL,L));Q,_=orthogonal_procrustes(S,refS);Sa=S@Q;rows.append({'bootstrap':b,'mean_angle_deg':ang.mean(),'max_angle_deg':ang.max(),'mean_aligned_spearman':np.mean([abs(spearmanr(Sa[:,j],refS[:,j]).statistic) for j in range(k)]),'aligned_rmse':np.sqrt(np.mean((Sa-refS)**2))})
 return pd.DataFrame(rows)
def align(P,Q):
 c=np.corrcoef(P.T,Q.T)[:P.shape[1],P.shape[1]:];a,b=linear_sum_assignment(-np.nan_to_num(c));return Q[:,b[np.argsort(a)]]
def main():
 h=pd.read_parquet(SRC/'history_features.parquet');b=pd.read_parquet(SRC/'topography_basic_features.parquet');a=pd.read_parquet(SRC/'topography_advanced_features.parquet');s=pd.read_parquet(ROOT/'data/processed/family_1/timeseries/sentinel_timeseries.parquet',columns=[ID,'CONJUNTO']).drop_duplicates();d=s.merge(h,on=ID).merge(b,on=ID).merge(a,on=ID);tr=d[d.CONJUNTO.eq('ENTRENAMIENTO')].reset_index(drop=True);pr=d[d.CONJUNTO.eq('PREDICCION')].reset_index(drop=True);hist=[c for c in h if c.startswith('HIST_S2_') and not c.endswith('_months')];basic=[c for c in b if c.startswith('TOPO_BASIC_')];adv=[c for c in a if c.startswith('TOPO_ADV_')]
 # Audit.
 audit=[]
 for c in adv:
  x=d[c];xt=tr[c];xp=pr[c];sd=np.sqrt((xt.var()+xp.var())/2);audit.append({'feature':c,'family':family(c),'statistic':c.split('_')[-1],'source':'DEM-derived surface, 120m zonal summary','missing_all_pct':x.isna().mean()*100,'n_unique':x.nunique(),'variance':x.var(),'min':x.min(),'q01':x.quantile(.01),'median':x.median(),'q99':x.quantile(.99),'max':x.max(),'constant':x.nunique()<=1,'SMD_prediction_vs_train':(xp.mean()-xt.mean())/sd if sd else 0,'KS_prediction_vs_train':ks_2samp(xt,xp).statistic,'prediction_outside_train_pct':((xp<xt.min())|(xp>xt.max())).mean()*100})
 aud=pd.DataFrame(audit);aud.to_csv(T/'01_topography_advanced_audit.csv',index=False)
 # Redundancy.
 X=tr[basic+adv].fillna(tr[basic+adv].median());sp=X.corr(method='spearman');pairs=[]
 for x in adv:
  for y in basic:pairs.append({'advanced_feature':x,'basic_feature':y,'spearman':sp.loc[x,y],'abs_spearman':abs(sp.loc[x,y])})
 pd.DataFrame(pairs).sort_values('abs_spearman',ascending=False).to_csv(T/'02_basic_advanced_redundancy.csv',index=False)
 # Leakage-safe multivariate Ridge reconstruction Advanced <- Basic.
 outer=KFold(5,shuffle=True,random_state=SEED);pred=np.zeros((len(tr),len(adv)));choices=[]
 for fold,(ii,jj) in enumerate(outer.split(tr)):
  ib=SimpleImputer(strategy='median').fit(tr.iloc[ii][basic]);ia=SimpleImputer(strategy='median').fit(tr.iloc[ii][adv]);xb=ib.transform(tr.iloc[ii][basic]);xa=ia.transform(tr.iloc[ii][adv]);sb=StandardScaler().fit(xb);sa=StandardScaler().fit(xa);xb=sb.transform(xb);xa=sa.transform(xa);inner=list(KFold(4,shuffle=True,random_state=SEED+fold).split(ii));scores=[]
  for al in [.1,1,10,100]:
   z=[]
   for u,v in inner:z.append(np.mean((Ridge(alpha=al).fit(xb[u],xa[u]).predict(xb[v])-xa[v])**2))
   scores.append((np.mean(z),al))
  al=min(scores)[1];choices.append({'fold':fold,'alpha':al});pred[jj]=Ridge(alpha=al).fit(xb,xa).predict(sb.transform(ib.transform(tr.iloc[jj][basic])))
 Y=StandardScaler().fit_transform(SimpleImputer(strategy='median').fit_transform(tr[adv]));recon=[]
 for j,c in enumerate(adv):recon.append({'feature':c,'family':family(c),'cv_R2':r2_score(Y[:,j],pred[:,j]),'cv_RMSE_standardized':np.sqrt(np.mean((Y[:,j]-pred[:,j])**2)),'residual_variance':np.var(Y[:,j]-pred[:,j])})
 rec=pd.DataFrame(recon);rec.to_csv(T/'03_advanced_reconstruction_from_basic.csv',index=False);pd.DataFrame(choices).to_csv(T/'04_reconstruction_hyperparameters.csv',index=False);res=Y-pred;er,k90=eff(res);pd.DataFrame([{'global_variance_weighted_R2':r2_score(Y,pred,multioutput='variance_weighted'),'mean_feature_R2':rec.cv_R2.mean(),'median_feature_R2':rec.cv_R2.median(),'residual_effective_dimension':er,'residual_dimensions_for_90pct':k90}]).to_csv(T/'05_incremental_information.csv',index=False)
 # E1-E3, fixed block balancing. E0 read frozen.
 cond={'E1_ADVANCED_ONLY':{'advanced':adv},'E2_BASIC_ADVANCED':{'basic':basic,'advanced':adv},'E3_AUGMENTED':{'sentinel':hist,'basic':basic,'advanced':adv}};summ=[];coords=[];stabs=[];contrib=[];mods={}
 for name,blocks in cond.items():
  pp=Prep(blocks).fit(tr);zt=pp.transform(tr);zp=pp.transform(pr);ed,n90=eff(zt)
  for k in [2,3,4]:
   pc=PCA(k,random_state=SEED).fit(zt);st=pc.transform(zt);sv=pc.transform(zp);ref={'prep':pp,'pca':pc};bs=boot_pca(tr,blocks,ref,k);rid=f'{name}_PCA{k}';summ.append({'representation_id':rid,'condition':name,'latent_dim':k,'n_features':len(pp.cols),'effective_dimension':ed,'dimensions_for_90pct':n90,'explained_variance':pc.explained_variance_ratio_.sum(),'bootstrap_angle_deg':bs.mean_angle_deg.mean(),'bootstrap_spearman':bs.mean_aligned_spearman.mean(),'prediction_outside_score_range_pct':np.mean([((sv[:,j]<st[:,j].min())|(sv[:,j]>st[:,j].max())).mean() for j in range(k)])*100});bs.insert(0,'representation_id',rid);stabs.append(bs)
   for j,row in enumerate(pc.components_):
    den=(row*row).sum();offset=0
    for bn,cols in blocks.items():contrib.append({'representation_id':rid,'component':j+1,'block':bn,'squared_loading_fraction':(row[offset:offset+len(cols)]**2).sum()/den});offset+=len(cols)
   for grp,ids,S in [('TRAIN',tr[ID],st),('PREDICTION',pr[ID],sv)]:
    for i,pid in enumerate(ids):coords.append({ID:pid,'CONJUNTO':grp,'representation_id':rid,**{f'F{j+1}':S[i,j] for j in range(k)}})
   mods[rid]={'columns':pp.cols,'blocks':blocks,'imputer':pp.imp,'scaler':pp.sc,'weights':pp.w,'pca':pc}
 sm=pd.DataFrame(summ);sm.to_csv(T/'06_e1_e3_comparison.csv',index=False);pd.concat(stabs).to_csv(T/'07_factor_bootstrap_stability.csv',index=False);pd.DataFrame(contrib).to_csv(T/'08_block_contributions.csv',index=False);co=pd.DataFrame(coords);co.to_parquet(T/'09_e1_e3_coordinates.parquet',index=False);joblib.dump({'version':'F3.1.2','seed':SEED,'models':mods},M/'f3_1_2_models.joblib')
 # Compare common-parcel geometry with frozen E0.
 old=pd.read_parquet(OLD/'tables/04_structural_coordinates.parquet');cmp=[]
 for e0 in ['A1_COMPACT_PCA3','A2_FULL_BALANCED_PCA3']:
  A=old[(old.CONJUNTO=='TRAIN')&(old.representation_id==e0)].sort_values(ID)[['F1','F2','F3']].to_numpy()
  for e in ['E1_ADVANCED_ONLY_PCA3','E2_BASIC_ADVANCED_PCA3','E3_AUGMENTED_PCA3']:
   B=co[(co.CONJUNTO=='TRAIN')&(co.representation_id==e)].sort_values(ID)[['F1','F2','F3']].to_numpy();Q,_=orthogonal_procrustes(B,A);cmp.append({'reference':e0,'candidate':e,'distance_spearman':distcorr(A,B),'aligned_coordinate_spearman':np.mean([abs(spearmanr((B@Q)[:,j],A[:,j]).statistic) for j in range(3)]),'aligned_RMSE':np.sqrt(np.mean((B@Q-A)**2))})
 cmp=pd.DataFrame(cmp);cmp.to_csv(T/'10_e0_e3_geometry_comparison.csv',index=False)
 # Spatial.
 import geopandas as gpd
 geo=gpd.read_file(ROOT/'data/original/02_conjunto_70_30/Parcelas_Reto_AGC_CONJUNTO.shp').to_crs(6372);cent=pd.DataFrame({ID:geo.ID_POLIGON.astype(str),'x':geo.geometry.centroid.x,'y':geo.geometry.centroid.y});geoout=[]
 for rid in ['E1_ADVANCED_ONLY_PCA3','E2_BASIC_ADVANCED_PCA3','E3_AUGMENTED_PCA3']:
  z=co[(co.CONJUNTO=='TRAIN')&(co.representation_id==rid)].merge(cent,on=ID)
  for f in ['F1','F2','F3']:geoout.append({'representation_id':rid,'factor':f,'spearman_x':spearmanr(z[f],z.x).statistic,'spearman_y':spearmanr(z[f],z.y).statistic})
 pd.DataFrame(geoout).to_csv(T/'11_spatial_diagnostics.csv',index=False)
 # Predeclared decision and conditional comparable GMM.
 e3=sm[sm.representation_id.eq('E3_AUGMENTED_PCA3')].iloc[0];geom=cmp[(cmp.reference=='A2_FULL_BALANCED_PCA3')&(cmp.candidate=='E3_AUGMENTED_PCA3')].iloc[0];inc=pd.read_csv(T/'05_incremental_information.csv').iloc[0];justify=(inc.global_variance_weighted_R2<.75)&(inc.residual_effective_dimension>=2)&(e3.bootstrap_spearman>=.95)&(geom.distance_spearman<.98);gout=[]
 if justify:
  St=co[(co.CONJUNTO=='TRAIN')&(co.representation_id=='E3_AUGMENTED_PCA3')].sort_values(ID)[['F1','F2','F3']].to_numpy();Sp=co[(co.CONJUNTO=='PREDICTION')&(co.representation_id=='E3_AUGMENTED_PCA3')].sort_values(ID)[['F1','F2','F3']].to_numpy();gm=GaussianMixture(2,covariance_type='diag',reg_covar=1e-5,n_init=50,random_state=SEED).fit(St);P=gm.predict_proba(St);ent=-(P*np.log(P+1e-12)).sum(1)/np.log(2);rng=np.random.default_rng(SEED);br=[]
  for z in range(NBOOT):
   ix=rng.integers(0,len(St),len(St));gg=GaussianMixture(2,covariance_type='diag',reg_covar=1e-5,n_init=10,random_state=SEED+z).fit(St[ix]);Q=align(P,gg.predict_proba(St));br.append({'bootstrap':z,'ARI':adjusted_rand_score(P.argmax(1),Q.argmax(1)),'membership_MAE':abs(P-Q).mean(),'coassignment':np.mean((P.argmax(1)[:,None]==P.argmax(1)[None,:])==(Q.argmax(1)[:,None]==Q.argmax(1)[None,:]))})
  br=pd.DataFrame(br);gout=[{'model':'E3_PCA3_GMM2_diag','effective_sizes':json.dumps(P.sum(0).tolist()),'mean_max_probability':P.max(1).mean(),'entropy':ent.mean(),'ambiguous_pct':(P.max(1)<.7).mean()*100,'bootstrap_ARI':br.ARI.mean(),'membership_MAE':br.membership_MAE.mean(),'coassignment':br.coassignment.mean()}];br.to_csv(T/'12_e3_gmm_bootstrap.csv',index=False)
 pd.DataFrame(gout if gout else [{'model':'NOT_RUN','reason':'E3 did not satisfy predefined incremental-stability criteria'}]).to_csv(T/'13_e3_gmm_comparison.csv',index=False)
 figures(aud,rec,sm,cmp,pd.DataFrame(contrib));report(aud,rec,inc,sm,cmp,pd.DataFrame(contrib),justify,pd.DataFrame(gout))
def figures(aud,rec,sm,cmp,con):
 plt.figure(figsize=(8,4));sns.boxplot(aud,x='family',y='KS_prediction_vs_train');plt.xticks(rotation=35);plt.tight_layout();plt.savefig(F/'01_advanced_train_prediction.png',dpi=180);plt.close();plt.figure(figsize=(8,4));sns.boxplot(rec,x='family',y='cv_R2');plt.xticks(rotation=35);plt.axhline(0);plt.tight_layout();plt.savefig(F/'02_advanced_reconstruction.png',dpi=180);plt.close();plt.figure(figsize=(8,4));sns.lineplot(sm,x='latent_dim',y='explained_variance',hue='condition',marker='o');plt.tight_layout();plt.savefig(F/'03_e1_e3_explained_variance.png',dpi=180);plt.close();q=sm[sm.latent_dim.eq(3)];plt.figure(figsize=(7,4));sns.barplot(q,x='condition',y='bootstrap_spearman');plt.xticks(rotation=25);plt.tight_layout();plt.savefig(F/'04_factor_stability.png',dpi=180);plt.close();plt.figure(figsize=(8,4));sns.barplot(cmp,x='candidate',y='distance_spearman',hue='reference');plt.xticks(rotation=25);plt.tight_layout();plt.savefig(F/'05_geometry_concordance.png',dpi=180);plt.close();q=con[con.representation_id.eq('E3_AUGMENTED_PCA3')];plt.figure(figsize=(7,4));sns.barplot(q,x='component',y='squared_loading_fraction',hue='block');plt.tight_layout();plt.savefig(F/'06_e3_block_contributions.png',dpi=180);plt.close()
def report(aud,rec,inc,sm,cmp,con,justify,g):
 e={r.representation_id:r for _,r in sm[sm.latent_dim.eq(3)].iterrows()};geom=cmp[(cmp.reference=='A2_FULL_BALANCED_PCA3')&(cmp.candidate=='E3_AUGMENTED_PCA3')].iloc[0];case='C — Advanced aporta estructura estable y complementaria' if justify else ('B — Advanced aporta información, pero no justifica incorporación principal' if inc.global_variance_weighted_R2<.75 else 'A — Advanced principalmente redundante');txt=f'''# F3.1.2 — Structural Source Expansion\n\n## Controles\nTarget-free; modelos ajustados sólo con 138 TRAIN y 59 PREDICTION transformadas. E0 no fue recalculado. Seed={SEED}, bootstrap={NBOOT}. Sin Climate Current, satélite 2025 ni modelos de rendimiento.\n\n## Auditoría Advanced\n87 variables, familias={aud.family.value_counts().to_dict()}; missing={int((aud.missing_all_pct>0).sum())}, constantes={int(aud.constant.sum())}. Mediana KS TRAIN–PREDICTION={aud.KS_prediction_vs_train.median():.3f}; máximo porcentaje fuera de rango={aud.prediction_outside_train_pct.max():.1f}%. Son estadísticas zonales de superficies DEM a 120 m; cuantiles contiguos pueden ser redundantes y curvaturas/hidrología sensibles a resolución/acondicionamiento.\n\n## Información incremental\nReconstrucción Advanced←Basic: R² global CV={inc.global_variance_weighted_R2:.3f}, mediana por variable={inc.median_feature_R2:.3f}. El residuo conserva dimensión efectiva={inc.residual_effective_dimension:.1f} ({int(inc.residual_dimensions_for_90pct)} direcciones para 90%). Familias menos reconstruibles: {rec.groupby('family').cv_R2.median().sort_values().round(3).to_dict()}. Baja reconstrucción significa novedad matemática, no utilidad.\n\n## E1–E3\nPCA3: E1 var={e['E1_ADVANCED_ONLY_PCA3'].explained_variance:.1%}, estabilidad={e['E1_ADVANCED_ONLY_PCA3'].bootstrap_spearman:.3f}; E2 var={e['E2_BASIC_ADVANCED_PCA3'].explained_variance:.1%}, estabilidad={e['E2_BASIC_ADVANCED_PCA3'].bootstrap_spearman:.3f}; E3 var={e['E3_AUGMENTED_PCA3'].explained_variance:.1%}, estabilidad={e['E3_AUGMENTED_PCA3'].bootstrap_spearman:.3f}, ángulo={e['E3_AUGMENTED_PCA3'].bootstrap_angle_deg:.1f}°. Concordancia geométrica E3–A2: distancias Spearman={geom.distance_spearman:.3f}, coordenadas alineadas={geom.aligned_coordinate_spearman:.3f}. Contribución E3={con[con.representation_id.eq('E3_AUGMENTED_PCA3')].round(3).to_dict('records')}.\n\n## GMM\nJustificación predefinida={justify}. Resultado={g.round(3).to_dict('records') if len(g) else 'omitido; conservar GMM A2 congelado'}. No se buscó otro K.\n\n## Decisión\n**{case}.** {'Conservar E3 PCA3 como candidata aumentada junto con A1 PCA3; mantener GMM K=2 sólo como competidor secundario.' if justify else 'Conservar A1 y A2 como representaciones principales; no aumentar complejidad con Advanced.'}\n\n## Limitaciones\nLa topografía está ligada a ubicación; información nueva puede ser gradiente geográfico. Resolución 120 m, n=138 y estadísticas altamente redundantes limitan interpretación. Ningún factor demuestra mecanismo agronómico ni utilidad predictiva. Cualquier F3.2 deberá reconstruir transformaciones dentro de folds. No se ejecutó F3.2.\n''';(R/'f3_1_2_structural_source_expansion_report.md').write_text(txt,encoding='utf-8');pd.DataFrame([{'classification':case,'gmm_run':justify,'recommendation':'A1 PCA3 + E3 PCA3' if justify else 'retain A1/A2','seed':SEED,'bootstrap':NBOOT}]).to_csv(T/'14_decision_log.csv',index=False)
if __name__=='__main__':main()

def finalize_reproducibility():
 h=pd.read_parquet(SRC/'history_features.parquet');b=pd.read_parquet(SRC/'topography_basic_features.parquet');a=pd.read_parquet(SRC/'topography_advanced_features.parquet');s=pd.read_parquet(ROOT/'data/processed/family_1/timeseries/sentinel_timeseries.parquet',columns=[ID,'CONJUNTO']).drop_duplicates();d=s.merge(h,on=ID).merge(b,on=ID).merge(a,on=ID);tr=d[d.CONJUNTO.eq('ENTRENAMIENTO')].reset_index(drop=True);hist=[c for c in h if c.startswith('HIST_S2_') and not c.endswith('_months')];basic=[c for c in b if c.startswith('TOPO_BASIC_')];adv=[c for c in a if c.startswith('TOPO_ADV_')];conds={'E1_ADVANCED_ONLY':{'advanced':adv},'E2_BASIC_ADVANCED':{'basic':basic,'advanced':adv},'E3_AUGMENTED':{'sentinel':hist,'basic':basic,'advanced':adv}};portable={}
 for name,blocks in conds.items():
  pp=Prep(blocks).fit(tr);Z=pp.transform(tr)
  for k in [2,3,4]:portable[f'{name}_PCA{k}']={'columns':pp.cols,'blocks':blocks,'imputer':pp.imp,'scaler':pp.sc,'weights':pp.w,'pca':PCA(k,random_state=SEED).fit(Z)}
 joblib.dump({'version':'F3.1.2','seed':SEED,'models':portable,'serialization':'portable sklearn objects'},M/'f3_1_2_models.joblib');joblib.load(M/'f3_1_2_models.joblib')
 co=pd.read_parquet(T/'09_e1_e3_coordinates.parquet');z=co[(co.CONJUNTO=='TRAIN')&(co.representation_id=='E3_AUGMENTED_PCA3')].sort_values(ID);gm=GaussianMixture(2,covariance_type='diag',reg_covar=1e-5,n_init=50,random_state=SEED).fit(z[['F1','F2','F3']]);P=gm.predict_proba(z[['F1','F2','F3']]);old=pd.read_parquet(OLD/'tables/08_gmm_membership_probabilities.parquet');o=old[(old.CONJUNTO=='TRAIN')&(old.gmm_id=='A2_FULL_BALANCED_PCA3_GMM2_diag')].sort_values(ID);OP=o[['prob_component_1','prob_component_2']].to_numpy();P=align(OP,P);hard=P.argmax(1);oh=OP.argmax(1);out=pd.DataFrame({ID:z[ID].values,'e0_component':oh+1,'e3_component':hard+1,'e0_max_probability':OP.max(1),'e3_max_probability':P.max(1),'e0_ambiguous':OP.max(1)<.7,'e3_ambiguous':P.max(1)<.7,'membership_L1_change':abs(P-OP).sum(1)});out.to_csv(T/'15_e0_e3_membership_changes.csv',index=False);pd.DataFrame([{'ARI_E0_vs_E3':adjusted_rand_score(oh,hard),'hard_assignment_agreement':(oh==hard).mean(),'mean_membership_L1_change':abs(P-OP).sum(1).mean(),'ambiguous_E0_n':(OP.max(1)<.7).sum(),'ambiguous_E3_n':(P.max(1)<.7).sum(),'newly_ambiguous_n':((P.max(1)<.7)&(OP.max(1)>=.7)).sum(),'resolved_ambiguous_n':((P.max(1)>=.7)&(OP.max(1)<.7)).sum()}]).to_csv(T/'16_e0_e3_gmm_concordance.csv',index=False)
