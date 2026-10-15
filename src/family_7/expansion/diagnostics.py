"""Expanded data-supported diagnostics; no additional scientific fits."""
import joblib,numpy as np,pandas as pd
from scipy.spatial.distance import cdist
from threadpoolctl import threadpool_limits
from src.family_7 import diagnostics as initial_diag
from src.family_6.expansion import diagnostics as effects
from . import execution as e

def conditional_permutation(model,v,cols,prediction,radius):
    frame=v.reset_index(drop=True);groups=[];eligible=np.zeros(len(frame),bool)
    for _,g in frame.groupby('climate_profile'):
        x=g[cols].to_numpy(float)
        if len(g)<2 or not np.any(np.nanmax(x,axis=0)-np.nanmin(x,axis=0)>1e-10):continue
        groups.append(g.index.to_numpy());eligible[g.index]=True
    n=int(eligible.sum())
    if n<10:return [dict(permutation=-1,status='not identifiable: constant block or <10 peers',n_eligible=n,n_supported=0,n_profiles=len(groups),delta_MSE=np.nan,delta_MAE=np.nan)]
    rng=np.random.default_rng(e.SEED);baseline=prediction-frame[e.TARGET].to_numpy();rows=[]
    for j in range(10):
        z=frame.copy()
        for indices in groups:z.loc[indices,cols]=frame.loc[rng.permutation(indices),cols].to_numpy()
        distances=cdist(model.preprocess_.transform(z),model.training_z_).min(axis=1)
        original=cdist(model.preprocess_.transform(frame),model.training_z_).min(axis=1)
        mask=eligible&(distances<=radius+1e-12)&(original<=radius+1e-12);ns=int(mask.sum())
        ok=ns>=10 and ns/n>=.8
        error=model.predict(z.loc[mask])-frame.loc[mask,e.TARGET].to_numpy() if ok else None
        rows.append(dict(permutation=j,status='supported profile-conditional permutation' if ok else 'not identifiable: insufficient local training support',n_eligible=n,n_supported=ns,n_profiles=len(groups),supported_fraction=ns/n,delta_MSE=float(np.mean(error**2-baseline[mask]**2)) if ok else np.nan,delta_MAE=float(np.mean(abs(error)-abs(baseline[mask]))) if ok else np.nan))
    return rows

def diagnose_fold(i):
    _,t,splits=e.load();p,r,f,tr,va,_=splits[i];a,v=t.iloc[tr],t.iloc[va]
    out={k:[] for k in ['nodes','leaves','usage','effects','interactions','permutation']}
    with threadpool_limits(limits=1):
        for name in ['F7-00',*e.SPECS]:
            root=e.initial.OUT if name=='F7-00' else e.OUT;stem=f'{name}_{p}_{r}_{f}'
            model=joblib.load(root/'models'/f'{stem}_outer.joblib');key=dict(experiment=name,protocol=p,repeat=r,fold=f)
            radius=effects.support_radius(model);cols=list(model.columns)
            # Original diagnostics implementation writes only inside this new version.
            old=initial_diag.e
            try:initial_diag.e=e;nodes,leaves,usage=initial_diag.tree_tables(model,key,stem)
            finally:initial_diag.e=old
            out['nodes']+=nodes;out['leaves']+=leaves;out['usage']+=usage
            for c in cols:out['effects'] += [{**key,**row} for row in effects.ale(model,a,c,radius)]
            pairs=e.INTERACTIONS.get(name,[(c,e.CORE[-1]) for c in e.CORE[:3]])
            for first,second in pairs:out['interactions'] += [{**key,**row} for row in effects.interaction(model,a,first,second,radius)]
            blocks={'rain_compact3':e.CORE[:3],'NDVI_may':[e.CORE[-1]]}
            if all(c in cols for c in e.HISTORY):blocks['history_NDVI2']=e.HISTORY
            if e.SLOPE in cols:blocks['slope_mean']=[e.SLOPE]
            pred=model.predict(v)
            for block,cs in blocks.items():out['permutation'] += [{**key,'block':block,**row} for row in conditional_permutation(model,v,cs,pred,radius)]
    return out
def build(p):
    (e.OUT/'audit/trees').mkdir(exist_ok=True)
    parts=joblib.Parallel(n_jobs=6,backend='loky',inner_max_num_threads=1)(joblib.delayed(diagnose_fold)(i) for i in range(65))
    files=dict(nodes='tree_partitions.parquet',leaves='tree_leaf_support.parquet',usage='variable_partition_stability.csv',effects='effects_by_outer_fit.csv',interactions='interactions_by_outer_fit.csv',permutation='permutation_by_outer_fit.csv')
    for k,f in files.items():
        z=pd.DataFrame([r for part in parts for r in part[k]])
        if f.endswith('.parquet'):z.to_parquet(e.OUT/'tables'/f,index=False)
        else:z.to_csv(e.OUT/'tables'/f,index=False)
    z=pd.read_csv(e.OUT/'tables/effects_by_outer_fit.csv')
    z.groupby(['experiment','protocol','feature','repeat','fold']).supported.all().reset_index(name='full_ALE_supported').to_csv(e.OUT/'tables/ALE_support_by_fit.csv',index=False)
    z=pd.read_csv(e.OUT/'tables/variable_partition_stability.csv')
    z.groupby(['experiment','protocol','feature']).agg(n_fits=('fold','size'),fraction_used_mean=('fraction_trees_used','mean'),fraction_used_sd=('fraction_trees_used','std'),threshold_median_mean=('threshold_median','mean'),threshold_median_sd=('threshold_median','std'),importance_mean=('importance_descriptive','mean')).reset_index().to_csv(e.OUT/'tables/variable_stability_summary.csv',index=False)
    z=pd.read_csv(e.OUT/'tables/permutation_by_outer_fit.csv')
    q=z.groupby(['experiment','protocol','repeat','fold','block']).agg(n_identifiable_permutations=('delta_MSE','count'),mean_delta_MSE=('delta_MSE','mean'),mean_delta_MAE=('delta_MAE','mean'),mean_supported=('n_supported','mean')).reset_index()
    q.to_csv(e.OUT/'tables/permutation_support_by_fit.csv',index=False)
    q.groupby(['experiment','protocol','block']).agg(n_fits=('fold','size'),n_supported_fits=('n_identifiable_permutations',lambda x:(x>0).sum()),mean_delta_MSE=('mean_delta_MSE','mean'),mean_delta_MAE=('mean_delta_MAE','mean')).reset_index().to_csv(e.OUT/'tables/permutation_summary.csv',index=False)
