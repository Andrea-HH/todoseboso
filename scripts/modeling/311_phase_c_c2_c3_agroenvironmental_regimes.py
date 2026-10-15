from __future__ import annotations
import json, hashlib, warnings, math
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd
import matplotlib.pyplot as plt, seaborn as sns
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, fcluster, dendrogram
from scipy.optimize import linear_sum_assignment
from scipy import stats
from sklearn.cluster import HDBSCAN, AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score, silhouette_samples, adjusted_rand_score, adjusted_mutual_info_score, normalized_mutual_info_score
from sklearn.preprocessing import RobustScaler, StandardScaler
from sklearn.impute import SimpleImputer
from statsmodels.stats.multitest import multipletests
import statsmodels.formula.api as smf

warnings.filterwarnings('ignore')
ROOT=Path(__file__).resolve().parents[2]; SEED=2026; rng=np.random.default_rng(SEED); ID='ID_POLIGONO'
OUT=ROOT/'outputs/research/phase_c/c2_c3_regimes'; PROC=ROOT/'data/processed/phase_c/c2_c3'
TAB=OUT/'tables'; FIG=OUT/'figures'; REP=OUT/'report'
for p in [OUT,PROC,TAB,FIG,REP]: p.mkdir(parents=True,exist_ok=True)

def sha(p):
 h=hashlib.sha256(); h.update(Path(p).read_bytes()); return h.hexdigest()
def bh(p): return multipletests(np.nan_to_num(p,nan=1.),method='fdr_bh')[1]
def cramers_v(a,b):
 t=pd.crosstab(a,b); n=t.to_numpy().sum()
 if n==0:return np.nan
 x=stats.chi2_contingency(t,correction=False)[0]; phi=x/n; r,k=t.shape
 return math.sqrt(max(0,phi-(k-1)*(r-1)/(n-1))/max(1e-12,min(k-1-(k-1)**2/(n-1),r-1-(r-1)**2/(n-1))))

def prepare():
 base=pd.read_parquet(ROOT/'data/processed/phase_c/c0_c1/integrated_research_matrix.parquet')
 sup=pd.read_parquet(ROOT/'data/processed/phase_c/c0_c1/supervised_reference_matrix.parquet')[[ID,'y_true']]
 rgb=pd.read_parquet(ROOT/'data/processed/phase_c/c1_2/rgb_compact_representations.parquet')
 shp=gpd.read_file(ROOT/'data/original/02_conjunto_70_30/Parcelas_Reto_AGC_CONJUNTO.shp'); shp[ID]=shp.ID_POLIGON.astype(str)
 cen=shp.to_crs(6372); xy=cen.geometry.centroid
 coords=pd.DataFrame({ID:cen[ID],'coord_x':xy.x,'coord_y':xy.y})
 d=base.merge(sup,on=ID).merge(coords,on=ID).merge(rgb.drop(columns=['CONJUNTO','Estado','AREA_HA']),on=ID)
 assert len(d)==197 and d[ID].nunique()==197 and (d.CONJUNTO=='ENTRENAMIENTO').sum()==138
 forbidden=('y_true','prediction','residual','error','rendimiento')
 phys=['EXT_area_geometry_ha','EXT_PHYS_dominant_fraction','EXT_GEOL_clave','EXT_GEOL_clase','EXT_GEOL_tipo','EXT_GEOL_era','EXT_GEOL_entidad','EXT_GEOL_dominant_fraction','EXT_GEOL_diversity','EXT_GEOL_distance_structure_m','EXT_GEOL_distance_fault_m','EXT_GEOL_distance_fracture_m']
 loc=['EXT_LOC_distance_any_m','EXT_LOC_distance_rural_m','EXT_LOC_distance_urban_m','EXT_LOC_nearest_ambito','EXT_LOC_nearest_population','EXT_LOC_count_1000m','EXT_LOC_count_3000m','EXT_LOC_count_5000m']
 agro=['CLIMATE_precip_early_sum','CLIMATE_precip_total','CLIMATE_tmax_mean_mean','TOPO_BASIC_elevation_mean','TOPO_BASIC_elevation_std','TOPO_BASIC_slope_mean','TOPO_BASIC_slope_std','TOPO_BASIC_elevation_relief','TOPO_ADV_twi_mean','TOPO_ADV_flow_accumulation_log1p_mean','TOPO_ADV_local_relief_3x3_mean']
 pheno=['S2_ndvi_promedio_mean','S2_ndvi_promedio_normalized_auc','S2_ndvi_promedio_peak_day','S2_ndvi_promedio_std','S2_ndwi_promedio_mean','S2_fapar_promedio_normalized_auc']
 rgbc=[c for c in rgb if ('palette_PC' in c or 'spatial_PC' in c) and not c.endswith(('PC7','PC8','PC9'))]
 scenarios={'S1_TERRITORIAL_PHYSICAL':{'physical':phys},'S2_TERRITORIAL_CONTEXT':{'physical':phys,'locality':loc},'S3_AGROCLIMATIC_FIRA':{'agroclimate':agro},'S4_PHENOLOGICAL_FIRA':{'phenology':pheno},'S5_INTEGRATED':{'physical':phys,'agroclimate':agro,'phenology':pheno},'S6_RGB_SENSITIVITY':{'physical':phys,'agroclimate':agro,'phenology':pheno,'rgb_compact':rgbc}}
 rows=[]
 for s,blocks in scenarios.items():
  for b,cols in blocks.items():
   for c in cols:
    rows.append({'scenario':s,'block':b,'variable':c,'dtype':'categorical' if d[c].dtype=='object' else 'continuous','missing_n':int(d[c].isna().sum()),'n_unique':int(d[c].nunique(dropna=True)),'retained':d[c].nunique(dropna=True)>1,'reason':'retained' if d[c].nunique(dropna=True)>1 else 'constant'})
 inv=pd.DataFrame(rows); inv.to_csv(TAB/'01_variable_inventory.csv',index=False)
 clean={s:{b:[c for c in cs if d[c].nunique(dropna=True)>1 and not any(x in c.lower() for x in forbidden)] for b,cs in bs.items()} for s,bs in scenarios.items()}
 assert not any(any(x in c.lower() for x in forbidden) for bs in clean.values() for cs in bs.values() for c in cs)
 return d,shp,clean

def gower_block(df,cols):
 n=len(df); D=np.zeros((n,n)); W=np.zeros((n,n))
 for c in cols:
  x=df[c]; ok=x.notna().to_numpy(); valid=ok[:,None]&ok[None,:]
  if x.dtype=='object': delta=(x.astype(str).to_numpy()[:,None]!=x.astype(str).to_numpy()[None,:]).astype(float)
  else:
   v=x.to_numpy(float); q=np.nanpercentile(v,[25,75]); scale=q[1]-q[0]
   if not np.isfinite(scale) or scale<=0: scale=np.nanmax(v)-np.nanmin(v)
   delta=np.minimum(np.abs(v[:,None]-v[None,:])/max(scale,1e-12),1)
  D+=np.where(valid,delta,0); W+=valid
 return np.divide(D,W,out=np.zeros_like(D),where=W>0)
def distance(df,blocks,mode='balanced'):
 mats=[]; weights=[]
 for _,cols in blocks.items():
  if cols: mats.append(gower_block(df,cols)); weights.append(1 if mode=='balanced' else len(cols))
 w=np.array(weights,float); w/=w.sum(); D=sum(a*b for a,b in zip(w,mats)); np.fill_diagonal(D,0)
 assert np.allclose(D,D.T) and D.min()>=-1e-12 and np.allclose(np.diag(D),0)
 return D
def pam(D,k,seed=SEED,max_iter=100):
 rr=np.random.default_rng(seed); n=len(D); med=[rr.integers(n)]
 while len(med)<k:
  near=D[:,med].min(1); med.append(int(np.argmax(near)))
 med=np.array(med)
 for _ in range(max_iter):
  lab=np.argmin(D[:,med],axis=1); new=[]
  for j in range(k):
   ix=np.where(lab==j)[0]; new.append(int(ix[np.argmin(D[np.ix_(ix,ix)].sum(1))]) if len(ix) else rr.choice(np.setdiff1d(np.arange(n),med)))
  new=np.array(new)
  if set(new)==set(med):break
  med=new
 lab=np.argmin(D[:,med],axis=1); return lab,med,D[np.arange(n),med[lab]]
def fuzzy(X,k,m,seed=SEED,max_iter=300):
 rr=np.random.default_rng(seed); n=len(X); U=rr.dirichlet(np.ones(k),n)
 for _ in range(max_iter):
  old=U.copy(); um=U**m; C=(um.T@X)/(um.sum(0)[:,None]+1e-12); dist=np.sqrt(((X[:,None]-C[None,:])**2).sum(2))+1e-10
  U=1/((dist[:,:,None]/dist[:,None,:])**(2/(m-1))).sum(2)
  if np.max(abs(U-old))<1e-7:break
 fpc=np.mean((U**2).sum(1)); pe=-np.mean((U*np.log(U+1e-12)).sum(1)); xb=(U**m*dist**2).sum()/(n*max(1e-12,pdist(C).min()**2))
 return U,C,fpc,pe,xb
def compact_numeric(d,cols):
 X=SimpleImputer(strategy='median').fit_transform(d[cols]); X=RobustScaler().fit_transform(X); p=PCA(random_state=SEED).fit(X); q=max(2,min(10,np.searchsorted(np.cumsum(p.explained_variance_ratio_),.9)+1)); return p.transform(X)[:,:q],q,p.explained_variance_ratio_[:q].sum()
def stable_pam(D,base,k,reps=20):
 vals=[]; n=len(D)
 for r in range(reps):
  ix=np.sort(np.random.default_rng(SEED+r).choice(n,int(.8*n),False)); z,_,_=pam(D[np.ix_(ix,ix)],k,SEED+r); vals.append((adjusted_rand_score(base[ix],z),adjusted_mutual_info_score(base[ix],z)))
 a=np.array(vals); return dict(stability_ari_mean=a[:,0].mean(),stability_ari_sd=a[:,0].std(),stability_ari_q10=np.quantile(a[:,0],.1),stability_ami_mean=a[:,1].mean(),stability_reps=reps)

def discover(d,scenarios):
 ex=[]; members=[]; dist_diag=[]; store={}
 for sn,blocks in scenarios.items():
  cols=sum(blocks.values(),[]); X,q,ev=compact_numeric(d,[c for c in cols if d[c].dtype!='object'])
  for mode in ['balanced','variable_weighted']:
   D=distance(d,blocks,mode); store[(sn,mode)]=D; tri=D[np.triu_indices(len(D),1)]
   cv=tri.std()/tri.mean(); null=[]
   for r in range(30):
    perm=np.array([np.random.default_rng(SEED+r+j).permutation(d[c].to_numpy()) for j,c in enumerate(cols)]).T
    nd=d.copy(); nd.loc[:,cols]=perm; nt=distance(nd,blocks,mode)[np.triu_indices(len(D),1)]; null.append(nt.std()/nt.mean())
   dist_diag.append({'scenario':sn,'weighting':mode,'distance_mean':tri.mean(),'distance_sd':tri.std(),'distance_cv':cv,'null_cv_mean':np.mean(null),'effective_pca_dimensions':q,'pca_variance':ev})
   for k in range(2,7):
    lab,med,dm=pam(D,k); sil=silhouette_score(D,lab,metric='precomputed'); st=stable_pam(D,lab,k)
    vals=silhouette_samples(D,lab,metric='precomputed'); sizes=np.bincount(lab,minlength=k); ambiguous=np.mean(vals<.1)
    assert adjusted_rand_score(lab,(lab+1)%k)==1.0  # invariance to label names
    md=np.sort(D[:,med],axis=1); margin=(md[:,1]-md[:,0])/(md[:,1]+1e-12)
    eid=f'{sn}_PAM_{mode}_K{k}'; regional=adjusted_mutual_info_score(d.Estado,lab)
    ex.append(dict(experiment_id=eid,scenario=sn,variables=len(cols),preprocessing='Gower robust-IQR; pairwise missing',distance=f'block_gower_{mode}',algorithm='PAM',parameters=json.dumps({'k':k}),seed=SEED,n_groups=k,sizes=json.dumps(sizes.tolist()),silhouette=sil,noise_fraction=np.nan,converged=True,regional_AMI=regional,medoids=json.dumps(d.iloc[med][ID].tolist()),mean_medoid_distance=dm.mean(),ambiguous_fraction=ambiguous,**st))
    for i in range(len(d)): members.append({'experiment_id':eid,ID:d.loc[i,ID],'label':int(lab[i]),'membership_max':np.nan,'membership_margin':margin[i],'entropy':np.nan,'is_noise':False,'distance_center':dm[i],'stability':st['stability_ari_mean']})
  if sn in ['S1_TERRITORIAL_PHYSICAL','S5_INTEGRATED']:
   D=store[(sn,'balanced')]
   for link in ['average','complete']:
    for k in [2,3,4,5,6]:
     lab=AgglomerativeClustering(n_clusters=k,metric='precomputed',linkage=link).fit_predict(D); eid=f'{sn}_HIER_{link}_K{k}'; sil=silhouette_score(D,lab,metric='precomputed')
     ex.append(dict(experiment_id=eid,scenario=sn,variables=len(cols),preprocessing='Gower',distance='balanced block Gower',algorithm=f'hierarchical_{link}',parameters=json.dumps({'k':k}),seed=SEED,n_groups=k,sizes=json.dumps(np.bincount(lab).tolist()),silhouette=sil,noise_fraction=np.nan,converged=True,regional_AMI=adjusted_mutual_info_score(d.Estado,lab)))
     for i in range(len(d)):members.append({'experiment_id':eid,ID:d.loc[i,ID],'label':int(lab[i]),'is_noise':False})
   for mcs in [10,20,30]:
    for ms in [5,10]:
     lab=HDBSCAN(min_cluster_size=mcs,min_samples=ms,metric='precomputed').fit_predict(D); ng=len(set(lab)-{-1}); eid=f'{sn}_HDBSCAN_MCS{mcs}_MS{ms}'; ok=lab>=0
     Dok=D[np.ix_(ok,ok)].copy(); np.fill_diagonal(Dok,0); sil=silhouette_score(Dok,lab[ok],metric='precomputed') if ng>1 and ok.sum()>ng else np.nan
     ex.append(dict(experiment_id=eid,scenario=sn,variables=len(cols),preprocessing='Gower',distance='balanced block Gower',algorithm='HDBSCAN',parameters=json.dumps({'min_cluster_size':mcs,'min_samples':ms}),seed=SEED,n_groups=ng,sizes=json.dumps(pd.Series(lab[ok]).value_counts().sort_index().tolist()),silhouette=sil,noise_fraction=np.mean(~ok),converged=True,regional_AMI=adjusted_mutual_info_score(d.Estado,lab)))
     for i in range(len(d)):members.append({'experiment_id':eid,ID:d.loc[i,ID],'label':int(lab[i]),'is_noise':bool(lab[i]<0)})
  if sn in ['S3_AGROCLIMATIC_FIRA','S4_PHENOLOGICAL_FIRA','S5_INTEGRATED','S6_RGB_SENSITIVITY']:
   for k in [2,3,4,5]:
    for cov in ['diag','tied','full']:
     gm=GaussianMixture(k,covariance_type=cov,reg_covar=1e-5,n_init=10,random_state=SEED).fit(X); U=gm.predict_proba(X); lab=U.argmax(1); eid=f'{sn}_GMM_{cov}_K{k}'
     ex.append(dict(experiment_id=eid,scenario=sn,variables=len(cols),preprocessing=f'robust PCA{q}',distance='Gaussian likelihood',algorithm='GMM',parameters=json.dumps({'k':k,'covariance':cov,'reg_covar':1e-5}),seed=SEED,n_groups=k,sizes=json.dumps(np.bincount(lab,minlength=k).tolist()),silhouette=silhouette_score(X,lab),noise_fraction=0,converged=gm.converged_,regional_AMI=adjusted_mutual_info_score(d.Estado,lab),bic=gm.bic(X),aic=gm.aic(X),log_likelihood=gm.score(X),membership_entropy=np.mean(-(U*np.log(U+1e-12)).sum(1)),membership_max=U.max(1).mean()))
     for i in range(len(d)):members.append({'experiment_id':eid,ID:d.loc[i,ID],'label':int(lab[i]),**{f'membership_{j}':U[i,j] for j in range(k)},'membership_max':U[i].max(),'membership_margin':np.sort(U[i])[-1]-np.sort(U[i])[-2],'entropy':-(U[i]*np.log(U[i]+1e-12)).sum(),'is_noise':False})
    for m in [1.5,2.,2.5]:
     U,C,fpc,pe,xb=fuzzy(X,k,m); lab=U.argmax(1); eid=f'{sn}_FUZZY_M{m}_K{k}'
     ex.append(dict(experiment_id=eid,scenario=sn,variables=len(cols),preprocessing=f'robust PCA{q}',distance='Euclidean',algorithm='fuzzy_cmeans',parameters=json.dumps({'k':k,'m':m}),seed=SEED,n_groups=k,sizes=json.dumps(np.bincount(lab,minlength=k).tolist()),silhouette=silhouette_score(X,lab),noise_fraction=0,converged=True,regional_AMI=adjusted_mutual_info_score(d.Estado,lab),fpc=fpc,partition_entropy=pe,xie_beni=xb,membership_entropy=pe,membership_max=U.max(1).mean()))
     assert np.allclose(U.sum(1),1)
     for i in range(len(d)):members.append({'experiment_id':eid,ID:d.loc[i,ID],'label':int(lab[i]),**{f'membership_{j}':U[i,j] for j in range(k)},'membership_max':U[i].max(),'membership_margin':np.sort(U[i])[-1]-np.sort(U[i])[-2],'entropy':-(U[i]*np.log(U[i]+1e-12)).sum(),'is_noise':False})
 ex=pd.DataFrame(ex); mem=pd.DataFrame(members); diag=pd.DataFrame(dist_diag)
 # Eligibility and target-free selection. PAM is primary because it has resampling stability.
 ex['min_size']=ex.sizes.map(lambda s:min(json.loads(s)) if pd.notna(s) and s!='[]' else 0)
 ex['eligible']=(ex.n_groups.between(2,5))&(ex.min_size>=15)&(ex.noise_fraction.fillna(0)<=.25)&(ex.converged==True)
 pamx=ex[(ex.algorithm=='PAM')&ex.eligible].copy(); pamx['selection_score']=pamx.stability_ari_mean.fillna(0)+pamx.silhouette.fillna(0)-.25*pamx.regional_AMI.fillna(0)
 selected=[]
 for sn in ['S1_TERRITORIAL_PHYSICAL','S3_AGROCLIMATIC_FIRA','S4_PHENOLOGICAL_FIRA','S5_INTEGRATED','S6_RGB_SENSITIVITY']:
  z=pamx[(pamx.scenario==sn)&(pamx.distance=='block_gower_balanced')].sort_values('selection_score',ascending=False)
  if len(z): selected.append(z.iloc[0].experiment_id)
 # Keep three diverse primary candidates plus S1 reference; never consult Y.
 pref=[]
 for sn in ['S5_INTEGRATED','S3_AGROCLIMATIC_FIRA','S1_TERRITORIAL_PHYSICAL']:
  cand=[x for x in selected if x.startswith(sn)]
  if cand:pref.append(cand[0])
 ex['selected_for_external_validation']=ex.experiment_id.isin(pref); ex['decision']=np.where(ex.selected_for_external_validation,'selected target-free','not selected')
 ex.to_csv(TAB/'03_experiment_table.csv',index=False); mem.to_csv(TAB/'04_membership_master_all.csv',index=False); diag.to_csv(TAB/'02_clusterability_diagnostics.csv',index=False)
 np.savez_compressed(PROC/'selected_distance_matrices.npz',**{k[0]+'__'+k[1]:v for k,v in store.items()})
 return ex,mem,diag,pref,store

def validate(d,shp,ex,mem,selected,scenarios,store):
 y=d.set_index(ID).y_true; meta=d.set_index(ID)[['Estado','CONJUNTO']]; desc=[]; tests=[]; nulls=[]; region=[]; inter=[]; errors=[]; evidence=[]; catalog=[]
 oof=pd.read_csv(ROOT/'outputs/modeling/family_1/error_analysis/residuals/oof_residuals_by_parcel.csv')
 q1,q3=y.dropna().quantile([.25,.75])
 for eid in selected:
  m=mem[mem.experiment_id==eid][[ID,'label']].drop_duplicates().set_index(ID); z=meta.join(y).join(m).reset_index(); tr=z[z.y_true.notna()]
  for g,a in z.groupby('label'):
   t=a.y_true.dropna(); desc.append({'solution':eid,'group':g,'n_total':len(a),'n_train':len(t),'n_prediction':a.y_true.isna().sum(),'mean':t.mean(),'median':t.median(),'sd':t.std(),'iqr':t.quantile(.75)-t.quantile(.25),'p10':t.quantile(.1),'p25':t.quantile(.25),'p75':t.quantile(.75),'p90':t.quantile(.9),'min':t.min(),'max':t.max(),'skew':t.skew(),'low_fraction':(t<=q1).mean(),'high_fraction':(t>=q3).mean()})
  groups=[a.y_true.to_numpy() for _,a in tr.groupby('label')]; k=len(groups)
  welch=stats.f_oneway(*groups,equal_var=False); kw=stats.kruskal(*groups); bf=stats.levene(*groups,center='median'); eta=np.var(tr.groupby('label').y_true.transform('mean'))/np.var(tr.y_true)
  # State-stratified permutation of between-group sum of squares.
  obs=sum(len(a)*(a.y_true.mean()-tr.y_true.mean())**2 for _,a in tr.groupby('label')); vals=[]
  for r in range(999):
   yy=tr.groupby('Estado').y_true.transform(lambda s:np.random.default_rng(SEED+r).permutation(s)); vals.append(sum(len(a)*(yy.loc[a.index].mean()-yy.mean())**2 for _,a in tr.groupby('label')))
  pp=(1+sum(v>=obs for v in vals))/(1+len(vals)); tests += [{'solution':eid,'test':'Welch_ANOVA','statistic':welch.statistic,'p_value':welch.pvalue,'effect_size':eta},{'solution':eid,'test':'Kruskal_Wallis','statistic':kw.statistic,'p_value':kw.pvalue,'effect_size':np.nan},{'solution':eid,'test':'Brown_Forsythe','statistic':bf.statistic,'p_value':bf.pvalue,'effect_size':np.nan},{'solution':eid,'test':'state_stratified_permutation_between_SS','statistic':obs,'p_value':pp,'effect_size':eta}]
  # Random partitions with identical sizes.
  labs=tr.label.to_numpy(); null_eta=[]
  for r in range(999):
   lp=np.random.default_rng(SEED+r).permutation(labs); null_eta.append(np.var(pd.Series(tr.y_true.to_numpy()).groupby(lp).transform('mean'))/np.var(tr.y_true))
  nulls.append({'solution':eid,'observed_eta2':eta,'null_mean':np.mean(null_eta),'null_p':(1+sum(v>=eta for v in null_eta))/1000})
  region.append({'solution':eid,'AMI_state':adjusted_mutual_info_score(tr.Estado,tr.label),'NMI_state':normalized_mutual_info_score(tr.Estado,tr.label),'cramers_v_state':cramers_v(tr.Estado,tr.label),'contingency':pd.crosstab(tr.Estado,tr.label).to_json()})
  # Parsimonious interactions; descriptive only.
  vars=['CLIMATE_precip_early_sum','TOPO_BASIC_slope_mean','TOPO_ADV_twi_mean','S2_ndvi_promedio_normalized_auc','S2_ndwi_promedio_mean']
  dd=d[[ID,'y_true']+vars].merge(m.reset_index(),on=ID).dropna(subset=['y_true'])
  for v in vars:
   dat=dd[['y_true','label',v]].dropna().rename(columns={v:'x'}); dat['label']=dat.label.astype('category'); a=smf.ols('y_true ~ x + C(label)',dat).fit(); b=smf.ols('y_true ~ x*C(label)',dat).fit(); ft=b.compare_f_test(a)
   inter.append({'solution':eid,'variable':v,'n':len(dat),'interaction_F':ft[0],'p_value':ft[1],'delta_adjusted_R2':b.rsquared_adj-a.rsquared_adj})
  oo=oof.merge(m.reset_index(),on=ID)
  for (model,g),a in oo.groupby(['pipeline','label']):
   errors.append({'solution':eid,'model':model,'group':g,'n':len(a),'bias':a.residual.mean(),'MAE':a.absolute_error.mean(),'RMSE':np.sqrt(a.squared_error.mean()),'MedAE':a.absolute_error.median(),'residual_sd':a.residual.std(),'SSE_fraction':a.squared_error.sum()/oo[oo.pipeline==model].squared_error.sum()})
  ee=ex.loc[ex.experiment_id==eid].iloc[0]; evidence.append({'solution':eid,'stability':ee.get('stability_ari_mean',np.nan),'environmental_separation':ee.silhouette,'regional_dependence':region[-1]['AMI_state'],'yield_eta2':eta,'yield_permutation_p':pp,'conditional_min_p':min(x['p_value'] for x in inter if x['solution']==eid),'recommendation':'candidate for global interactions only' if ee.stability_ari_mean>=.6 and pp<.1 else 'retain as descriptive gradient/stratification'})
  sn=ee.scenario; profile_cols=sum(scenarios[sn].values(),[]); numeric=[c for c in profile_cols if d[c].dtype!='object']
  zz=d[[ID]+numeric].merge(m.reset_index(),on=ID); scale=zz[numeric].std().replace(0,np.nan); overall=zz[numeric].mean(); margins=mem[mem.experiment_id==eid].set_index(ID).membership_margin
  for g,a in z.groupby('label'):
   gp=zz[zz.label==g][numeric].mean(); top=((gp-overall)/scale).abs().sort_values(ascending=False).head(5).index.tolist(); rep=mem[(mem.experiment_id==eid)&(mem.label==g)].nsmallest(5,'distance_center')[ID].tolist(); amb=margins.loc[a[ID]].sort_values().head(5).index.tolist()
   catalog.append({'solution':eid,'group':g,'n_total':len(a),'states':a.Estado.value_counts().to_json(),'distinguishing_variables':','.join(top),'representative_parcels':','.join(rep),'ambiguous_parcels':','.join(amb),'interpretation':'data-defined environmental profile; no causal agronomic label'})
 tests=pd.DataFrame(tests); tests['q_value']=bh(tests.p_value); inter=pd.DataFrame(inter); inter['q_value']=bh(inter.p_value)
 for frame,name in [(pd.DataFrame(desc),'05_y_group_descriptives.csv'),(tests,'06_y_statistical_tests.csv'),(pd.DataFrame(nulls),'07_null_partition_comparison.csv'),(pd.DataFrame(region),'08_regional_dependence.csv'),(inter,'09_conditional_interactions.csv'),(pd.DataFrame(errors),'10_oof_error_by_environment.csv'),(pd.DataFrame(evidence),'11_evidence_matrix.csv'),(pd.DataFrame(catalog),'12_regime_catalog.csv')]:frame.to_csv(TAB/name,index=False)
 # Selected memberships enriched with metadata.
 mm=mem[mem.experiment_id.isin(selected)].merge(d[[ID,'Estado','CONJUNTO']],on=ID,how='left'); mm.to_csv(TAB/'13_selected_memberships.csv',index=False); mm.to_parquet(PROC/'selected_regime_memberships.parquet',index=False)
 return pd.DataFrame(desc),tests,pd.DataFrame(region),inter,pd.DataFrame(errors),pd.DataFrame(evidence)

def figures(d,shp,ex,mem,selected,store,desc,errors):
 sns.set_theme(style='whitegrid')
 dg=pd.read_csv(TAB/'02_clusterability_diagnostics.csv'); plt.figure(figsize=(10,5)); sns.barplot(dg,x='scenario',y='distance_cv',hue='weighting'); plt.xticks(rotation=25,ha='right'); plt.tight_layout(); plt.savefig(FIG/'01_distance_concentration.png',dpi=180);plt.close()
 px=ex[ex.algorithm=='PAM'];plt.figure(figsize=(11,5));sns.scatterplot(px,x='n_groups',y='silhouette',hue='scenario',style='distance');plt.tight_layout();plt.savefig(FIG/'02_pam_silhouette.png',dpi=180);plt.close()
 plt.figure(figsize=(11,5));sns.scatterplot(px,x='silhouette',y='stability_ari_mean',hue='scenario',size='min_size');plt.tight_layout();plt.savefig(FIG/'03_stability_vs_separation.png',dpi=180);plt.close()
 if selected:
  eid=selected[0]; m=mem[mem.experiment_id==eid][[ID,'label']].drop_duplicates(); g=shp.merge(m,left_on='ID_POLIGON',right_on=ID); ax=g.plot(column='label',categorical=True,legend=True,figsize=(8,7),cmap='tab10',edgecolor='.4');ax.set_axis_off();ax.set_title(eid);plt.tight_layout();plt.savefig(FIG/'04_selected_regime_map.png',dpi=180);plt.close()
  tr=d[[ID,'y_true']].merge(m,on=ID).dropna();plt.figure(figsize=(8,5));sns.boxplot(tr,x='label',y='y_true');sns.stripplot(tr,x='label',y='y_true',color='black',alpha=.55);plt.tight_layout();plt.savefig(FIG/'05_y_distribution.png',dpi=180);plt.close()
  er=errors[errors.solution==eid];plt.figure(figsize=(9,5));sns.barplot(er,x='group',y='RMSE',hue='model');plt.tight_layout();plt.savefig(FIG/'06_oof_error_by_environment.png',dpi=180);plt.close()
  D=store[(ex.loc[ex.experiment_id==eid,'scenario'].iloc[0],'balanced')]; plt.figure(figsize=(7,6));sns.heatmap(D,cmap='viridis',xticklabels=False,yticklabels=False);plt.tight_layout();plt.savefig(FIG/'07_selected_distance_matrix.png',dpi=180);plt.close()
  Z=linkage(squareform(D,checks=False),method='average');plt.figure(figsize=(12,5));dendrogram(Z,no_labels=True,color_threshold=None);plt.tight_layout();plt.savefig(FIG/'08_selected_dendrogram.png',dpi=180);plt.close()

def report(d,ex,diag,selected,desc,tests,region,inter,errors,evidence,scenarios):
 chosen=ex[ex.experiment_id.isin(selected)][['experiment_id','scenario','n_groups','sizes','silhouette','stability_ari_mean','regional_AMI']].round(3).to_dict('records')
 tt=tests[tests.test=='state_stratified_permutation_between_SS'][['solution','p_value','effect_size']].round(4).to_dict('records'); ii=inter.groupby('solution').agg(min_interaction_p=('p_value','min'),max_delta_adj_R2=('delta_adjusted_R2','max')).reset_index().round(4).to_dict('records')
 er=errors.groupby(['solution','model']).agg(RMSE_range=('RMSE',lambda x:x.max()-x.min()),max_RMSE=('RMSE','max')).reset_index().round(3).to_dict('records')
 text=f'''# Fase C2–C3 — Regímenes agroambientales

## 1. Resumen ejecutivo

Se analizaron 197 parcelas (138 TRAIN, 59 PREDICTION). El descubrimiento, preprocesamiento y selección se realizaron sin rendimiento, predicciones ni residuos. Soluciones congeladas: {chosen}. La evidencia con Y se abrió posteriormente. Contrastes estratificados por Estado: {tt}. Interacciones descriptivas: {ii}. Diferencias de RMSE OOF: {er}.

## 2. Preguntas e hipótesis

Se evaluó si la estructura es discreta, difusa o continua; su dependencia regional; diferencias completas de Y; heterogeneidad condicional y error OOF. Encontrar clusters no se consideró éxito por sí mismo.

## 3. Inventario y escenarios

S1 físico territorial; S2 añade localidades como proxy contextual; S3 agroclima FIRA; S4 fenología Sentinel; S5 integración balanceada S1+S3+S4; S6 añade RGB compacto sólo como sensibilidad. Se excluyeron fisiografía constante, ENA, hidrografía sin cobertura y humedales cuya ausencia temática se confunde con cero. Inventario completo en `01_variable_inventory.csv`.

## 4. Preprocesamiento y distancias

Gower implementado por atributo: continuas escaladas por IQR y truncadas a [0,1], nominales 0/1, faltantes excluidos por pareja. Se comparó peso igual por bloque y peso por número de variables. Todas las matrices pasaron simetría, no negatividad y diagonal cero. En espacios numéricos: mediana, RobustScaler y PCA ≥90% (máximo 10 componentes). Las transformaciones no consultaron Y.

## 5. Agrupabilidad

{diag.round(3).to_dict('records')}. La concentración de distancias se comparó con 30 nulos de permutación marginal. PCA se usó sólo para representación compatible, nunca como prueba de clusters.

## 6–8. Clustering, incertidumbre, estabilidad y selección

PAM K=2…6 fue el método principal; average/complete y HDBSCAN fueron controles estructurales. GMM y fuzzy c-means se aplicaron sólo en espacios numéricos. PAM usó 20 submuestras de 80%, comparadas sobre IDs comunes mediante ARI/AMI. La selección target-free priorizó estabilidad, silhouette, tamaño mínimo ≥15, ruido ≤25% y menor dependencia estatal. No se eligió por silhouette aislado. GMM reporta BIC/AIC y entropía; fuzzy reporta FPC, entropía y Xie–Beni. Las probabilidades GMM y membresías fuzzy no se interpretan como equivalentes.

## 9–10. Rendimiento e inferencia

Las distribuciones por grupo incluyen media, mediana, dispersión, cuantiles, colas y extremos. Se aplicaron Welch, Kruskal–Wallis, Brown–Forsythe y 999 permutaciones de Y dentro de Estado. Se controló FDR en la familia de contrastes. Las particiones aleatorias conservan tamaños de grupo. Son resultados exploratorios posteriores a selección basada en X, no causalidad.

## 11. Comparaciones dentro de estados

AMI/NMI/Cramér V cuantifican confusión regional. La permutación dentro de Estado es una sensibilidad; no elimina toda dependencia espacial residual ni resuelve falta de solapamiento.

## 12. Relaciones condicionales

Se probaron de forma parsimoniosa interacciones de grupo con precipitación temprana, pendiente, TWI, AUC NDVI y NDWI. Son caracterización, no validación predictiva.

## 13. Errores OOF

Se utilizaron únicamente OOF agregadas por parcela de XGB_CORE, LGBM_CORE y ENET_CORE_EXTENDED. Las 138 parcelas, no las repeticiones, son la unidad. Se reportan bias, MAE, RMSE, MedAE, dispersión y fracción SSE.

## 14. Limitaciones

N=197 y sólo 138 con Y; cartografía y clima tienen estructura regional; memberships transductivas no son asignadores inductivos finales; estabilidad PAM no sustituye validación espacial; no hay manejo observado; RGB carece de semántica física; pruebas e interacciones son exploratorias.

## 15. Conclusiones científicas

Matriz de evidencia: {evidence.round(4).to_dict('records')}. Se distingue explícitamente estructura ambiental de separación de Y. Una diferencia de media no implica necesidad de modelos separados.

## 16. Recomendaciones C4–C6

Priorizar primero un modelo global con interacciones regularizadas o efectos parcialmente agrupados sólo para soluciones estables y con soporte. Comparar contra Champion mediante nested/spatial CV con todo el descubrimiento target-free ajustado dentro de train. No abrir mixture-of-experts salvo que persistan pendientes diferentes, errores sistemáticos y tamaños adecuados. Si la evidencia es débil, conservar los ambientes sólo como estratos diagnósticos.
'''
 (REP/'c2_c3_technical_report.md').write_text(text,encoding='utf-8')
 (REP/'executive_decisions.md').write_text('# Decisiones C2–C3\n\n'+text.split('## 15. Conclusiones científicas')[1],encoding='utf-8')

def main():
 d,shp,sc=prepare(); ex,mem,diag,selected,store=discover(d,sc); desc,tests,region,inter,errors,evidence=validate(d,shp,ex,mem,selected,sc,store); figures(d,shp,ex,mem,selected,store,desc,errors);report(d,ex,diag,selected,desc,tests,region,inter,errors,evidence,sc)
 manifest={'stage':'C2-C3','seed':SEED,'n_parcels':197,'n_train':138,'n_prediction':59,'selected_solutions':selected,'subsample_fraction':.8,'subsample_repetitions':20,'null_repetitions':999,'inputs':{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'data/processed/phase_c/c0_c1/integrated_research_matrix.parquet',ROOT/'data/processed/phase_c/c1_2/rgb_compact_representations.parquet',ROOT/'outputs/modeling/family_1/error_analysis/residuals/oof_residuals_by_parcel.csv']}}
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8'); print('C2-C3 complete:',OUT)
if __name__=='__main__':main()
