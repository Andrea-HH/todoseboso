"""C1.2: statistical cartographic representations of RGB maps by parcel."""
from pathlib import Path
import json,warnings
import numpy as np,pandas as pd,geopandas as gpd
from affine import Affine
from shapely.geometry import Polygon
from shapely.ops import transform as shp_transform
from pyproj import Transformer
import rasterio
from skimage.color import rgb2lab
from scipy.ndimage import label
from scipy.stats import spearmanr
from scipy.spatial.distance import pdist,squareform
from sklearn.cluster import MiniBatchKMeans,KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.model_selection import GridSearchCV,KFold,GroupKFold
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score,median_absolute_error
import matplotlib.pyplot as plt,seaborn as sns
warnings.filterwarnings('ignore');sns.set_theme(style='whitegrid')
ROOT=Path(__file__).resolve().parents[2];ID='ID_POLIGONO';SEED=2026;METRIC=6372
RAW=ROOT/'data/externo';PROC=ROOT/'data/processed/phase_c/c1_2';OUT=ROOT/'outputs/research/phase_c/c1_2_rgb_representation';TAB=OUT/'tables';FIG=OUT/'figures';REP=OUT/'report';CROPS=OUT/'crops'
for p in [PROC,TAB,FIG,REP,CROPS/'soil',CROPS/'groundwater']:p.mkdir(parents=True,exist_ok=True)
SOURCES={'soil':(RAW/'suelo/e1402.tif',RAW/'suelo/e1402.tfwx'),'groundwater':(RAW/'hidrologia_subterranea/e1402.tif',RAW/'hidrologia_subterranea/e1402.tfwx')};K=12

def world(path):
 a,d,b,e,c,f=map(float,Path(path).read_text().split());return Affine(a,b,c,d,e,f)
def cellpoly(T,r,c):return Polygon([T*(c-.5,r-.5),T*(c+.5,r-.5),T*(c+.5,r+.5),T*(c-.5,r+.5)])
def weighted_quantile(x,w,qs):
 i=np.argsort(x);x=np.asarray(x)[i];w=np.asarray(w)[i];return np.interp(qs,(np.cumsum(w)-.5*w)/w.sum(),x)
def extract(ds,T,geom):
 inv=~T;x0,y0,x1,y1=geom.bounds;cr=[inv*z for z in [(x0,y0),(x0,y1),(x1,y0),(x1,y1)]];cs=[z[0] for z in cr];rs=[z[1] for z in cr];c0=max(0,int(np.floor(min(cs)-1)));c1=min(ds.width-1,int(np.ceil(max(cs)+1)));r0=max(0,int(np.floor(min(rs)-1)));r1=min(ds.height-1,int(np.ceil(max(rs)+1)));arr=ds.read(window=((r0,r1+1),(c0,c1+1)));rec=[];mask=np.zeros((r1-r0+1,c1-c0+1),float)
 for r in range(r0,r1+1):
  for c in range(c0,c1+1):
   cp=cellpoly(T,r,c);a=geom.intersection(cp).area
   if a>0:
    w=a/cp.area;rgb=arr[:,r-r0,c-c0].astype(float);rec.append((r,c,*rgb,w,int(geom.covers(cp))));mask[r-r0,c-c0]=w
 return np.asarray(rec,float),arr,mask,(r0,c0,T.a,T.b,T.c,T.d,T.e,T.f)
def wstats(rec,prefix):
 rgb=rec[:,2:5];w=rec[:,5];w=w/w.sum();o={}
 for j,ch in enumerate('rgb'):
  x=rgb[:,j];mu=np.sum(w*x);var=np.sum(w*(x-mu)**2);q=weighted_quantile(x,w,[.1,.25,.5,.75,.9]);o|={f'{prefix}_{ch}_mean':mu,f'{prefix}_{ch}_var':var,f'{prefix}_{ch}_sd':np.sqrt(var),f'{prefix}_{ch}_min':x.min(),f'{prefix}_{ch}_max':x.max(),f'{prefix}_{ch}_q10':q[0],f'{prefix}_{ch}_q25':q[1],f'{prefix}_{ch}_q50':q[2],f'{prefix}_{ch}_q75':q[3],f'{prefix}_{ch}_q90':q[4],f'{prefix}_{ch}_iqr':q[3]-q[1]}
 cov=np.cov(rgb,rowvar=False,aweights=w,ddof=0);sd=np.sqrt(np.diag(cov));cor=cov/np.outer(sd,sd);pairs=[(0,1,'rg'),(0,2,'rb'),(1,2,'gb')]
 for a,b,n in pairs:o[f'{prefix}_cov_{n}']=cov[a,b];o[f'{prefix}_corr_{n}']=cor[a,b] if sd[a]*sd[b]>0 else np.nan
 return o
def hist_features(rec,palette,prefix):
 rgb=rec[:,2:5];w=rec[:,5];w=w/w.sum();lab=rgb2lab((rgb/255).reshape(-1,1,3)).reshape(-1,3);labels=palette.predict(lab);h=np.bincount(labels,weights=w,minlength=K);q=(rgb//64).clip(0,3).astype(int);idx=q[:,0]*16+q[:,1]*4+q[:,2];hq=np.bincount(idx,weights=w,minlength=64);nz=h[h>0];H=-(nz*np.log(nz)).sum();sim=1-(h*h).sum();s=np.sort(h)[::-1]
 o={f'{prefix}_pal_{i:02d}':h[i] for i in range(K)}|{f'{prefix}_qrgb_{i:02d}':hq[i] for i in range(64)}
 o|={f'{prefix}_raw_colors':len(set(map(tuple,rgb.astype(int)))),f'{prefix}_palette_categories':int((h>0).sum()),f'{prefix}_dominant_palette':int(h.argmax()),f'{prefix}_dominant_prop':h.max(),f'{prefix}_entropy':H,f'{prefix}_simpson':sim,f'{prefix}_top2_prop':s[:2].sum(),f'{prefix}_top3_prop':s[:3].sum()}
 return o,labels,h
def spatial_features(rec,labels,prefix):
 rc=rec[:,:2].astype(int);w=rec[:,5];d={(r,c):i for i,(r,c) in enumerate(rc)};edges=[]
 for i,(r,c) in enumerate(rc):
  for z in [(r+1,c),(r,c+1)]:
   if z in d:edges.append((i,d[z]))
 transitions=np.mean([labels[a]!=labels[b] for a,b in edges]) if edges else np.nan;R=rc[:,0].max()-rc[:,0].min()+1;C=rc[:,1].max()-rc[:,1].min()+1;grid=np.full((R,C),-1);wg=np.zeros((R,C))
 for i,(r,c) in enumerate(rc):grid[r-rc[:,0].min(),c-rc[:,1].min()]=labels[i];wg[r-rc[:,0].min(),c-rc[:,1].min()]=w[i]
 comps=[]
 for k in range(K):
  lab,n=label(grid==k)
  for j in range(1,n+1):comps.append(wg[lab==j].sum())
 comps=np.asarray(comps);L=rgb2lab((rec[:,2:5]/255).reshape(-1,1,3)).reshape(-1,3)[:,0];mu=np.average(L,weights=w);num=sum((L[a]-mu)*(L[b]-mu) for a,b in edges);den=np.sum((L-mu)**2);moran=(len(L)/max(2*len(edges),1))*2*num/den if den>0 and edges else np.nan
 return {f'{prefix}_transition_density':transitions,f'{prefix}_connected_regions':len(comps),f'{prefix}_regions_per_effective_cell':len(comps)/(w.sum()**2/(w@w)),f'{prefix}_largest_region_prop':comps.max()/w.sum() if len(comps) else np.nan,f'{prefix}_moran_luminance':moran}
def bh(p):
 p=np.asarray(p,float);out=np.full(len(p),np.nan);ok=np.isfinite(p);v=p[ok];order=np.argsort(v);adj=np.minimum.accumulate((v[order]*len(v)/np.arange(1,len(v)+1))[::-1])[::-1];tmp=np.empty(len(v));tmp[order]=np.minimum(adj,1);out[ok]=tmp;return out

def main():
 p=gpd.read_file(ROOT/'data/original/02_conjunto_70_30/Parcelas_Reto_AGC_CONJUNTO.shp');p[ID]=p.ID_POLIGON.astype(str);p=p.to_crs(METRIC);to14=Transformer.from_crs(METRIC,32614,always_xy=True).transform
 records={};all_lab={};audit=[]
 # Extract exact crops/masks once, preserve original pixel arrays losslessly.
 for src,(tif,tfw) in SOURCES.items():
  T=world(tfw);records[src]={};labs=[];weights=[]
  with rasterio.open(tif) as ds:
   for _,z in p.iterrows():
    geom=shp_transform(to14,z.geometry);rec,arr,mask,meta=extract(ds,T,geom);records[src][z[ID]]=rec;labs.append(rgb2lab((rec[:,2:5]/255).reshape(-1,1,3)).reshape(-1,3));weights.append(rec[:,5]);np.savez_compressed(CROPS/src/f'{z[ID]}.npz',rgb_crop=arr.astype(np.uint8),area_fraction_mask=mask,cell_records=rec,window_and_affine=np.asarray(meta),parcel_area_m2=geom.area,pixel_area_m2=abs(T.a*T.e-T.b*T.d))
  all_lab[src]=np.vstack(labs);w=np.concatenate(weights);palette=MiniBatchKMeans(K,batch_size=2048,n_init=20,random_state=SEED).fit(all_lab[src],sample_weight=w);records[src]['_palette']=palette
  pd.DataFrame(palette.cluster_centers_,columns=['L','a','b']).assign(source=src,palette_id=np.arange(K)).to_csv(TAB/f'palette_{src}_lab.csv',index=False)
 # Feature families, interior sensitivity and parcel-environment histograms.
 statrows=[];histrows=[];spatrows=[];regrows=[];compact_raw=[]
 for _,z in p.iterrows():
  base={ID:z[ID],'CONJUNTO':z.CONJUNTO,'Estado':z.Estado,'AREA_HA':z.geometry.area/1e4};S=base.copy();H=base.copy();G=base.copy();Q=base.copy();geom=shp_transform(to14,z.geometry)
  for src,(tif,tfw) in SOURCES.items():
   rec=records[src][z[ID]];pal=records[src]['_palette'];prefix=f'RGB_{src}';S|=wstats(rec,prefix);hf,labels,h=hist_features(rec,pal,prefix);H|=hf;G|=spatial_features(rec,labels,prefix)
   w=rec[:,5];neff=w.sum()**2/(w@w);regrows.append({**base,'source':src,'crop_file':str((CROPS/src/f'{z[ID]}.npz').relative_to(ROOT)),'pixel_size_approx_m':np.sqrt(abs(world(tfw).a*world(tfw).e-world(tfw).b*world(tfw).d)),'intersected_cells':len(rec),'fully_contained_cells':int(rec[:,6].sum()),'effective_cells':neff,'valid_coverage_fraction':1.0,'weight_sum':w.sum(),'parcel_area_m2':geom.area})
   # Conservative sensitivities: contracted polygon and suspected graphic pixels.
   with rasterio.open(tif) as ds:
    inner=geom.buffer(-22);irec=extract(ds,world(tfw),inner)[0] if not inner.is_empty else np.empty((0,7));rings=[]
    for r in [250,500]:
     ring=geom.buffer(r).difference(geom);rr=extract(ds,world(tfw),ring)[0];_,_,rh=hist_features(rr,pal,f'x');rings.append((r,rh))
   if len(irec):_,_,ih=hist_features(irec,pal,'x');Q[f'{prefix}_interior_hist_L1']=np.abs(h-ih).sum();Q[f'{prefix}_interior_area_fraction']=inner.area/geom.area
   dark=(rec[:,2:5].max(1)-rec[:,2:5].min(1)<8)&(rec[:,2:5].mean(1)<100);frec=rec[~dark];fh=hist_features(frec,pal,'x')[2] if len(frec) else h;Q[f'{prefix}_dark_gray_fraction']=np.sum(rec[dark,5])/np.sum(rec[:,5]);Q[f'{prefix}_filter_hist_L1']=np.abs(h-fh).sum()
   for r,rh in rings:Q[f'{prefix}_environment_{r}m_L1']=np.abs(h-rh).sum();Q[f'{prefix}_environment_{r}m_similarity']=1-.5*np.abs(h-rh).sum()
  statrows.append(S);histrows.append(H);spatrows.append(G);compact_raw.append(Q)
 stats=pd.DataFrame(statrows);hists=pd.DataFrame(histrows);spatial=pd.DataFrame(spatrows);registry=pd.DataFrame(regrows);sens=pd.DataFrame(compact_raw)
 stats.to_csv(TAB/'01_parcel_rgb_statistics.csv',index=False);hists.to_parquet(PROC/'rgb_histogram_composition.parquet',index=False);hists.to_csv(TAB/'02_histogram_composition.csv',index=False);spatial.to_csv(TAB/'03_spatial_graphic_structure.csv',index=False);registry.to_csv(TAB/'04_crop_mask_registry.csv',index=False);sens.to_csv(TAB/'05_artifact_scale_environment_sensitivity.csv',index=False)
 # Frozen target-free compact PCs for each family/source.
 merged=stats.merge(hists,on=[ID,'CONJUNTO','Estado','AREA_HA']).merge(spatial,on=[ID,'CONJUNTO','Estado','AREA_HA']).merge(sens,on=[ID,'CONJUNTO','Estado','AREA_HA']);comp=merged[[ID,'CONJUNTO','Estado','AREA_HA']].copy();pload=[]
 families={}
 for src in SOURCES:
  families[f'{src}_stats']=[c for c in stats if c.startswith(f'RGB_{src}_')];families[f'{src}_palette']=[c for c in hists if c.startswith(f'RGB_{src}_pal_')];families[f'{src}_spatial']=[c for c in spatial if c.startswith(f'RGB_{src}_')];families[f'{src}_sensitivity']=[c for c in sens if c.startswith(f'RGB_{src}_')]
 for fam,cols in families.items():
  X=SimpleImputer(strategy='median').fit_transform(merged[cols]);X=StandardScaler().fit_transform(X);pc=PCA().fit(X);n=max(1,np.searchsorted(np.cumsum(pc.explained_variance_ratio_),.90)+1);Z=pc.transform(X)[:,:n]
  for j in range(n):comp[f'{fam}_PC{j+1}']=Z[:,j]
  for j in range(n):
   for c,v in zip(cols,pc.components_[j]):pload.append({'family':fam,'component':j+1,'feature':c,'loading':v,'explained_variance':pc.explained_variance_ratio_[j]})
 comp.to_parquet(PROC/'rgb_compact_representations.parquet',index=False);pd.DataFrame(pload).to_csv(TAB/'06_compact_pca_loadings.csv',index=False)
 # Scale dependence, territorial redundancy via distance-matrix correlations.
 scale=[]
 for src in SOURCES:
  for y in [f'RGB_{src}_raw_colors',f'RGB_{src}_entropy',f'RGB_{src}_r_var',f'RGB_{src}_transition_density']:
   x=merged.AREA_HA;scale.append({'source':src,'feature':y,'spearman_area':spearmanr(x,merged[y]).statistic,'spearman_effective_cells':spearmanr(registry[registry.source.eq(src)].effective_cells,merged[y]).statistic})
 pd.DataFrame(scale).to_csv(TAB/'07_scale_dependence.csv',index=False)
 ext=pd.read_parquet(ROOT/'data/processed/phase_c/c0_c1/integrated_research_matrix.parquet');geo_cols=[c for c in ext if c.startswith('EXT_GEOL_') and pd.api.types.is_numeric_dtype(ext[c])];topo=[c for c in ext if c.startswith('TOPO_') and pd.api.types.is_numeric_dtype(ext[c])];coords=p.to_crs(METRIC).centroid;blocks={'coordinates':np.c_[coords.x,coords.y],'geology_numeric':ext[geo_cols].to_numpy(),'topography_FIRA':ext[topo].to_numpy()}
 for src in SOURCES:blocks[f'{src}_compact']=comp[[c for c in comp if c.startswith(src+'_')]].to_numpy()
 red=[];keys=list(blocks)
 for i,a in enumerate(keys):
  A=StandardScaler().fit_transform(SimpleImputer(strategy='median').fit_transform(blocks[a]));da=pdist(A)
  for b in keys[i+1:]:
   B=StandardScaler().fit_transform(SimpleImputer(strategy='median').fit_transform(blocks[b]));db=pdist(B);red.append({'block_a':a,'block_b':b,'spearman_pairwise_distance':spearmanr(da,db).statistic})
 pd.DataFrame(red).to_csv(TAB/'08_territorial_redundancy.csv',index=False)
 # Supervised exploratory only after freeze.
 sup=pd.read_parquet(ROOT/'data/processed/phase_c/c0_c1/supervised_reference_matrix.parquet')[[ID,'y_true','prediction_mean','residual_mean','mean_absolute_error']];tr=comp.merge(sup,on=ID);tr=tr[tr.y_true.notna()].copy();assoc=[]
 for c in [x for x in comp if '_PC' in x]:
  for out in ['y_true','prediction_mean','residual_mean','mean_absolute_error']:
   r,pv=spearmanr(tr[c],tr[out]);xd=tr[c]-tr.groupby('Estado')[c].transform('mean');yd=tr[out]-tr.groupby('Estado')[out].transform('mean');assoc.append({'feature':c,'outcome':out,'n':len(tr),'spearman':r,'p_value_exploratory':pv,'within_state_spearman':spearmanr(xd,yd).statistic})
 ass=pd.DataFrame(assoc);ass['fdr_bh_within_outcome']=ass.groupby('outcome').p_value_exploratory.transform(bh);ass.to_csv(TAB/'09_supervised_exploratory_associations.csv',index=False)
 # Preliminary leakage-safe outer evaluation, exact persisted 5x10 splits.
 metrics,preds=evaluate_models(ext,stats,hists,spatial,comp,sup,p);pd.DataFrame(metrics).to_csv(TAB/'10_predictive_preliminary_metrics.csv',index=False);pd.DataFrame(preds).to_csv(TAB/'11_predictive_oof.csv',index=False)
 dictionary_rows=[]
 for df,fam in [(stats,'channel_statistics'),(hists,'histogram_composition'),(spatial,'graphic_spatial_structure'),(sens,'sensitivity_environment'),(comp,'compact_target_free_PCA')]:
  for c in df.columns:
   if c not in [ID,'CONJUNTO','Estado','AREA_HA']:dictionary_rows.append({'variable':c,'family':fam,'unit':'RGB level/proportion/count/dimensionless as encoded','source':'soil or groundwater rendered RGB map','interpretation':'cartographic statistical descriptor; not physical soil/water property','weighting':'exact cell intersection area where applicable','target_used_in_construction':False})
 pd.DataFrame(dictionary_rows).drop_duplicates('variable').to_csv(TAB/'12_variable_dictionary.csv',index=False)
 figures(merged,comp,pd.DataFrame(red),pd.DataFrame(metrics));report(stats,hists,spatial,registry,sens,comp,pd.DataFrame(scale),pd.DataFrame(red),ass,pd.DataFrame(metrics))
 (OUT/'manifest.json').write_text(json.dumps({'stage':'C1.2','seed':SEED,'palette_space':'CIELAB','palette_k':K,'palette_universe':'all exact parcel-intersecting pixels from 197 parcels, target-free, per source','rgb_quantization':'4 bins/channel = 64 joint bins','connectivity':4,'environment_buffers_m':[250,500],'interior_contraction_m':22,'outer_splits':'existing Family1 5x10','models':'Ridge with alpha selected in inner 4-fold','original_rasters_modified':False},indent=2),encoding='utf-8');print(f'C1.2 complete: {OUT}')

def evaluate_models(ext,stats,hists,spatial,comp,sup,p):
 fira=[c for c in ext if c.startswith(('S2_','CLIMATE_','TOPO_')) and pd.api.types.is_numeric_dtype(ext[c])];st=[c for c in stats if c.startswith('RGB_')];hi=[c for c in hists if '_pal_' in c];sp=[c for c in spatial if c.startswith('RGB_')];co=[c for c in comp if '_PC' in c]
 d=ext[[ID]+fira].merge(stats[[ID]+st],on=ID).merge(hists[[ID]+hi],on=ID).merge(spatial[[ID]+sp],on=ID).merge(comp[[ID]+co],on=ID).merge(sup,on=ID);d=d[d.y_true.notna()].reset_index(drop=True);ids=d[ID];y=d.y_true.to_numpy();xy=p.set_index(ID).loc[ids].to_crs(METRIC).centroid;d['coord_x']=xy.x.to_numpy();d['coord_y']=xy.y.to_numpy();sets={'FIRA_SELECTED':fira,'SPATIAL_ONLY':['coord_x','coord_y'],'FIRA_PLUS_RGB_STATS':fira+st,'FIRA_PLUS_PALETTE_HIST':fira+hi,'FIRA_PLUS_RGB_COMPACT':fira+co};spl=pd.read_csv(ROOT/'outputs/modeling/family_1/stage4/splits/outer_splits.csv');pos={v:i for i,v in enumerate(ids)};preds=[]
 for oi,s in spl.iterrows():
  tr=np.array([pos[v] for v in json.loads(s.train_ID_POLIGONO)]);va=np.array([pos[v] for v in json.loads(s.validation_ID_POLIGONO)])
  for name,cols in sets.items():
   pipe=Pipeline([('imp',SimpleImputer(strategy='median')),('scale',StandardScaler()),('ridge',Ridge())]);gs=GridSearchCV(pipe,{'ridge__alpha':[.1,1,10,100,1000]},scoring='neg_root_mean_squared_error',cv=KFold(4,shuffle=True,random_state=SEED+oi),n_jobs=1).fit(d.loc[tr,cols],y[tr]);ph=gs.predict(d.loc[va,cols])
   for j,pred in zip(va,ph):preds.append({'protocol':'random_repeated_5x10','model':name,ID:ids.iloc[j],'repeat':int(s['repeat']),'fold':int(s.fold),'y_true':y[j],'prediction':pred,'alpha':gs.best_params_['ridge__alpha']})
 # Secondary spatial GroupKFold, groups target-free.
 groups=KMeans(5,n_init=50,random_state=SEED).fit_predict(d[['coord_x','coord_y']]);gkf=GroupKFold(5)
 for fold,(tr,va) in enumerate(gkf.split(d,y,groups),1):
  for name,cols in sets.items():
   pipe=Pipeline([('imp',SimpleImputer(strategy='median')),('scale',StandardScaler()),('ridge',Ridge())]);gs=GridSearchCV(pipe,{'ridge__alpha':[.1,1,10,100,1000]},scoring='neg_root_mean_squared_error',cv=KFold(4,shuffle=True,random_state=SEED+fold),n_jobs=1).fit(d.loc[tr,cols],y[tr]);ph=gs.predict(d.loc[va,cols])
   for j,pred in zip(va,ph):preds.append({'protocol':'spatial_group5','model':name,ID:ids.iloc[j],'repeat':1,'fold':fold,'y_true':y[j],'prediction':pred,'alpha':gs.best_params_['ridge__alpha']})
 pr=pd.DataFrame(preds);metrics=[]
 for (protocol,model),g in pr.groupby(['protocol','model']):
  # aggregate repeated predictions by parcel for random protocol.
  z=g.groupby(ID).agg(y=('y_true','first'),pred=('prediction','mean')).reset_index();metrics.append({'protocol':protocol,'model':model,'n':len(z),'RMSE':np.sqrt(mean_squared_error(z.y,z.pred)),'MAE':mean_absolute_error(z.y,z.pred),'MedAE':median_absolute_error(z.y,z.pred),'R2':r2_score(z.y,z.pred),'bias_pred_minus_y':(z.pred-z.y).mean(),'champion_reference_RMSE':.4902845})
 return metrics,preds

def figures(m,c,r,met):
 fig,ax=plt.subplots(1,2,figsize=(11,4));
 for a,src in zip(ax,SOURCES):sns.scatterplot(m,x='AREA_HA',y=f'RGB_{src}_raw_colors',hue='Estado',ax=a);a.set_title(src)
 fig.tight_layout();fig.savefig(FIG/'01_area_color_diversity.png',dpi=180);plt.close(fig)
 plt.figure(figsize=(8,5));z=r.pivot(index='block_a',columns='block_b',values='spearman_pairwise_distance');sns.heatmap(z,annot=True,fmt='.2f',cmap='viridis');plt.tight_layout();plt.savefig(FIG/'02_block_distance_redundancy.png',dpi=180);plt.close()
 plt.figure(figsize=(7,5));pcs=[x for x in c if x.endswith('PC1')];sns.scatterplot(c,x=pcs[0],y=pcs[len(pcs)//2],hue='Estado');plt.title('Representaciones RGB compactas target-free');plt.tight_layout();plt.savefig(FIG/'03_compact_rgb_space.png',dpi=180);plt.close()
 plt.figure(figsize=(9,5));sns.barplot(met,x='model',y='RMSE',hue='protocol');plt.axhline(.4902845,color='black',ls='--',label='Champion ref.');plt.xticks(rotation=25,ha='right');plt.tight_layout();plt.savefig(FIG/'04_preliminary_predictive_metrics.png',dpi=180);plt.close()

def report(stats,hists,spatial,registry,sens,comp,scale,red,assoc,metrics):
 reg=registry.groupby('source').agg(n=('ID_POLIGONO','size'),cells_median=('intersected_cells','median'),effective_median=('effective_cells','median'),area_min=('parcel_area_m2','min'),area_max=('parcel_area_m2','max')).reset_index();sc=scale.round(3).to_dict('records');rr=red.assign(a=lambda x:x.spearman_pairwise_distance.abs()).nlargest(10,'a').drop(columns='a').round(3).to_dict('records');aa=assoc.assign(a=lambda x:x.spearman.abs()).nlargest(10,'a').drop(columns='a').round(3).to_dict('records');mm=metrics.round(4).to_dict('records')
 txt=f"""# C1.2 — Representación estadística rigurosa de cartas RGB

## Alcance y matemática

Para cada celda se usó el área exacta `a_ij=Area(P_i∩C_j)` y `w_ij=a_ij/sum(a_ik)`. Medias, varianzas poblacionales, cuantiles, covarianzas e histogramas son ponderados. `n_eff=(sum a)^2/sum(a^2)` mide balance de pesos, no independencia estadística. Soporte: {reg.round(2).to_dict('records')}. No se construyen intervalos tratando píxeles como réplicas independientes.

## Representaciones congeladas sin Y

1. Estadísticos R/G/B y covarianzas.
2. Histograma conjunto RGB fijo 4×4×4.
3. Paleta CIELAB K={K}, aprendida por fuente con todos los píxeles que intersectan las 197 parcelas, `random_state={SEED}`, ponderada por área.
4. Diversidad: Shannon, Simpson, dominancia y top-2/top-3.
5. Estructura 4-conexa: transiciones, componentes, mayor región y Moran descriptivo de luminancia.
6. PCA por familia hasta ≥90%, sólo como representación cartográfica target-free.

Ninguna dimensión equivale a clase edafológica/hidrogeológica. Las imágenes conservadas en `crops/` contienen recorte uint8, máscara de fracción de área, registros de celda y transformación; no se redimensionaron.

## Escala, borde y artefactos

Dependencia de área/n_eff: {sc}. La contracción de 22 m compara interior con borde. Un filtro conservador de gris oscuro se reporta sólo como sensibilidad, porque no distingue texto/líneas de categorías reales. Las diferencias parcela–anillos de 250/500 m excluyen la propia parcela. Texto, bordes, símbolos, antialiasing y fondo pueden dominar algunas paletas; ningún color raro se eliminó definitivamente.

## Novedad territorial

Mayores asociaciones entre matrices de distancias: {rr}. Valores altos con coordenadas indican firma regional; valores altos suelo–groundwater pueden reflejar cartografía compartida, no mecanismo común. Correlación de distancias complementa correlaciones marginales, pero no prueba novedad predictiva.

## Exploración supervisada separada

Sólo 138 TRAIN, después de congelar representaciones. Principales asociaciones exploratorias: {aa}. `fdr_bh_within_outcome` controla multiplicidad dentro de cada outcome; la columna within-state funciona como control espacial simple. No se interpretan colores como clases físicas ni se usan PREDICTION con Y.

## Evaluación predictiva preliminar

Resultados: {mm}. Se reutilizaron los 50 outer folds 5×10; imputación, escalado y alpha Ridge se ajustaron en train con inner 4-fold. La sensibilidad espacial usa cinco clusters de centroides sin Y. Estos modelos son diagnósticos y no sustituyen Champion. Una mejora pequeña/inestable o que desaparece espacialmente no justifica incorporación.

## Decisión para C2

Incorporar una familia RGB sólo si muestra: estabilidad borde/filtro, variación intrarregional, baja dependencia mecánica del área, novedad frente a coordenadas/geología/topografía y mejora consistente en random y spatial CV. De lo contrario conservarla como representación cartográfica auxiliar. No usar categorías dominantes como tipos de suelo/acuífero ni entrenar CNN con 138 etiquetas.
""";(REP/'c1_2_technical_report.md').write_text(txt,encoding='utf-8')
 rec="""# Recomendaciones C1.2 para C2-C6

- Mantener separadas soil-RGB y groundwater-RGB; no concatenarlas sin revisar redundancia.
- Preferir paleta CIELAB y PCs compactos sobre 64 bins crudos si la estabilidad es comparable.
- Excluir conteo bruto de colores si depende fuertemente del área; entropía/proporciones y métricas normalizadas son más comparables.
- Conservar indicadores de área, n_eff y sensibilidad de borde como controles de calidad, no como evidencia física.
- En clustering, reajustar scaler/PCA target-free y evaluar estabilidad; revisar asociación con Estado/coordenadas antes de llamar a los grupos “ambientes”.
- Para modelado, exigir ganancia nested estable y validación espacial. No corregir residuos OOF retrospectivamente.
""";(REP/'recommendations_for_c2_c6.md').write_text(rec,encoding='utf-8')

if __name__=='__main__':main()
