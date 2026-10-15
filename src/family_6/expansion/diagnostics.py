"""Training-supported effects and conditional block permutations; no extra model fits."""
import json
import joblib,numpy as np,pandas as pd
from scipy.spatial.distance import cdist
from threadpoolctl import threadpool_limits
from . import execution as e

def model_path(name,protocol,repeat,fold):
    root=e.base.OUT if name=='F6-E0' else e.OUT;source='F6-01' if name=='F6-E0' else name
    return root/'models'/f'{source}_{protocol}_{repeat}_{fold}_outer.joblib'

def support_radius(model):
    z=model.training_z_;distance=cdist(z,z);np.fill_diagonal(distance,np.inf)
    return max(float(np.quantile(distance.min(axis=1),.95)),1e-8)

def supported_effect(model,X,columns,lower,upper,radius,min_n=5,min_fraction=.8):
    """Gate all corners before prediction; return NaN when empirical support is weak."""
    frames=[]
    if len(columns)==1:
        options=[(0,),(1,)]
    else:options=[(0,0),(0,1),(1,0),(1,1)]
    mask=np.ones(len(X),bool);maxdistance=np.zeros(len(X))
    for flags in options:
        frame=X.copy()
        for j,(column,flag) in enumerate(zip(columns,flags)):frame[column]=upper[j] if flag else lower[j]
        distance=cdist(model.preprocess_.transform(frame),model.training_z_).min(axis=1)
        mask&=distance<=radius+1e-12;maxdistance=np.maximum(maxdistance,distance);frames.append(frame)
    n=int(mask.sum());fraction=n/len(X) if len(X) else 0.;supported=n>=min_n and fraction>=min_fraction
    value=np.nan
    if supported:
        prediction=[model.predict(frame.loc[mask]) for frame in frames]
        value=float(np.mean(prediction[1]-prediction[0])) if len(columns)==1 else float(np.mean(prediction[3]-prediction[2]-prediction[1]+prediction[0]))
    return dict(supported=supported,n_supported=n,supported_fraction=fraction,max_corner_distance=float(maxdistance.max()) if len(X) else np.nan,effect=value,support_radius=radius)

def ale(model,X,column,radius,n_bins=4):
    values=X[column].to_numpy(float);finite=np.isfinite(values)
    if finite.sum()<10:return []
    edges=np.unique(np.quantile(values[finite],np.linspace(0,1,n_bins+1)))
    if len(edges)<3:return []
    bins=np.clip(np.searchsorted(edges,values,side='right')-1,0,len(edges)-2);rows=[]
    for b in range(len(edges)-1):
        a=X.loc[finite&(bins==b)].copy()
        if not len(a):continue
        info=supported_effect(model,a,[column],[edges[b]],[edges[b+1]],radius)
        rows.append(dict(feature=column,bin=b,lower=edges[b],upper=edges[b+1],midpoint=(edges[b]+edges[b+1])/2,n=len(a),local_difference=info.pop('effect'),**info))
    if rows and all(r['supported'] for r in rows):
        values=np.cumsum([r['local_difference'] for r in rows]);centre=np.average(values,weights=[r['n'] for r in rows])
        for row,value in zip(rows,values):row['ALE']=float(value-centre)
    else:
        for row in rows:row['ALE']=np.nan
    return rows

def interaction(model,X,first,second,radius):
    edges=[np.unique(X[c].dropna().quantile([0,1/3,2/3,1]).to_numpy()) for c in [first,second]]
    if any(len(a)<3 for a in edges):return []
    bins=[np.clip(np.searchsorted(a,X[c].to_numpy(),side='right')-1,0,len(a)-2) for a,c in zip(edges,[first,second])];rows=[]
    for i in range(len(edges[0])-1):
        for j in range(len(edges[1])-1):
            mask=(bins[0]==i)&(bins[1]==j)&X[first].notna().to_numpy()&X[second].notna().to_numpy();a=X.loc[mask].copy()
            info=supported_effect(model,a,[first,second],[edges[0][i],edges[1][j]],[edges[0][i+1],edges[1][j+1]],radius) if len(a) else dict(supported=False,n_supported=0,supported_fraction=0.,max_corner_distance=np.nan,effect=np.nan,support_radius=radius)
            rows.append(dict(first=first,second=second,bin_first=i,bin_second=j,n=len(a),mixed_local_difference=info.pop('effect'),first_low=edges[0][i],first_high=edges[0][i+1],second_low=edges[1][j],second_high=edges[1][j+1],**info))
    return rows

def conditional_block_permutation(model,v,columns,prediction,min_n=10):
    """Within-validation climate peers; preserve multicolumn block rows together."""
    eligible=np.zeros(len(v),bool);group_indices=[]
    # Reset positional indices to prevent ID-label assignment ambiguity.
    frame=v.reset_index(drop=True)
    for _,g in frame.groupby('climate_profile'):
        if len(g)<2:continue
        values=g[columns].to_numpy(float)
        if not np.any(np.nanmax(values,axis=0)-np.nanmin(values,axis=0)>1e-10):continue
        indices=g.index.to_numpy();eligible[indices]=True;group_indices.append(indices)
    n=int(eligible.sum());profiles=len(group_indices)
    if n<min_n:return [dict(permutation=-1,status='not identifiable: constant block within profile or <10 varying eligible parcels',n_eligible=n,n_profiles=profiles,delta_MSE=np.nan,delta_MAE=np.nan)]
    baseline=np.asarray(prediction)-frame[e.TARGET].to_numpy();rng=np.random.default_rng(e.SEED);rows=[]
    for repetition in range(10):
        shuffled=frame.copy()
        for indices in group_indices:
            other=rng.permutation(indices);shuffled.loc[indices,columns]=frame.loc[other,columns].to_numpy()
        error=model.predict(shuffled)-frame[e.TARGET].to_numpy()
        rows.append(dict(permutation=repetition,status='evaluated conditional on climate profile only',n_eligible=n,n_profiles=profiles,delta_MSE=float(np.mean(error[eligible]**2)-np.mean(baseline[eligible]**2)),delta_MAE=float(np.mean(abs(error[eligible]))-np.mean(abs(baseline[eligible])))))
    return rows

def diagnose_fold(index):
    _,t,splits=e.load();protocol,repeat,fold,tr,va,inner=splits[index];a,v=t.iloc[tr],t.iloc[va]
    result=dict(nodes=[],leaves=[],usage=[],effects=[],interactions=[],permutation=[],stability=[],support=[])
    with threadpool_limits(limits=1):
        for name in ['F6-E0',*e.SPECS]:
            key=dict(experiment=name,protocol=protocol,repeat=repeat,fold=fold)
            model=joblib.load(model_path(name,protocol,repeat,fold));radius=support_radius(model)
            features=model.preprocess_.get_feature_names_out().tolist();original_indices=np.flatnonzero(model.preprocess_.support_)
            counts=np.zeros(len(features));tree_use=np.zeros(len(features));roots=np.zeros(len(features))
            for tree_index,est in enumerate(model.forest_.estimators_):
                tree=est.tree_;nodes=np.flatnonzero(tree.feature>=0)
                for f in set(tree.feature[nodes]):tree_use[f]+=1
                if tree.feature[0]>=0:roots[tree.feature[0]]+=1
                for node in nodes:
                    f=tree.feature[node];oi=original_indices[f];counts[f]+=1
                    threshold=tree.threshold[node]*model.preprocess_.scale_[oi]+model.preprocess_.mean_[oi]
                    result['nodes'].append({**key,'tree':tree_index,'node':int(node),'feature':features[f],'threshold_original':float(threshold),'n_node_samples':int(tree.n_node_samples[node]),'root':node==0})
                for node in np.flatnonzero(tree.feature<0):result['leaves'].append({**key,'tree':tree_index,'leaf':int(node),'n_leaf_samples':int(tree.n_node_samples[node]),'leaf_prediction':float(tree.value[node,0,0])})
            for j,c in enumerate(features):result['usage'].append({**key,'feature':c,'n_splits':int(counts[j]),'fraction_splits':float(counts[j]/counts.sum()) if counts.sum() else 0.,'fraction_trees_using_feature':tree_use[j]/e.N_TREES,'fraction_roots':roots[j]/e.N_TREES,'impurity_importance_descriptive':float(model.forest_.feature_importances_[j])})
            columns=e.CORE if name=='F6-E0' else e.SPECS[name]['columns']
            for column in columns:result['effects'].extend([{**key,**r} for r in ale(model,a,column,radius)])
            for first,second in e.INTERACTIONS[name]:result['interactions'].extend([{**key,**r} for r in interaction(model,a,first,second,radius)])
            prefix=model.prefix_predictions(v);pred=prefix[384];error=pred-v[e.TARGET].to_numpy()
            for n in [128,256]:result['stability'].append({**key,'prefix_n_trees':n,'n':len(v),'RMS_prediction_difference_from_384':float(np.sqrt(np.mean((prefix[n]-pred)**2))),'max_absolute_prediction_difference':float(abs(prefix[n]-pred).max()),'RMSE_prefix':float(np.sqrt(np.mean((prefix[n]-v[e.TARGET])**2))),'RMSE_384':float(np.sqrt(np.mean(error**2)))})
            block=[e.CORE[-1]] if name=='F6-E0' else e.BLOCKS[name]
            result['permutation'].extend([{**key,'block':';'.join(block),**r} for r in conditional_block_permutation(model,v,block,pred)])
            z=model.preprocess_.transform(v);distance=cdist(z,model.training_z_).min(axis=1)
            outside=(v[columns].lt(a[columns].min()-1e-10)|v[columns].gt(a[columns].max()+1e-10)).any(axis=1).to_numpy()
            for label,mask in [('all',np.ones(len(v),bool)),('outside_marginal_support',outside),('inside_marginal_support',~outside)]:
                if not mask.any():continue
                er=error[mask];result['support'].append({**key,'stratum':label,'n':int(mask.sum()),'RMSE':float(np.sqrt(np.mean(er**2))),'MAE':float(abs(er).mean()),'bias':float(er.mean()),'training_y_mean':float(a[e.TARGET].mean()),'prediction_mean':float(pred[mask].mean()),'observed_mean':float(v[e.TARGET].to_numpy()[mask].mean()),'mean_native_distance':float(distance[mask].mean()),'support_radius':radius})
    print(f'F6-E DIAGNOSTIC {index+1}/65 {protocol} fold{fold}',flush=True)
    return result

def build(p,workers=6):
    result=joblib.Parallel(n_jobs=workers,backend='loky',inner_max_num_threads=1)(joblib.delayed(diagnose_fold)(i) for i in range(65))
    tables={name:pd.DataFrame([row for pack in result for row in pack[name]]) for name in result[0]}
    for name,frame in tables.items():
        if name in ['nodes','leaves']:frame.to_parquet(e.OUT/'tables'/f'tree_{name}_support.parquet',index=False)
        else:frame.to_csv(e.OUT/'tables'/f'{name}_by_outer_fit.csv',index=False)
    u=tables['usage'];u.groupby(['experiment','protocol','feature']).agg(n_fits=('fraction_trees_using_feature','size'),mean_tree_usage=('fraction_trees_using_feature','mean'),sd_tree_usage=('fraction_trees_using_feature','std'),mean_root_frequency=('fraction_roots','mean'),mean_split_fraction=('fraction_splits','mean'),mean_impurity_descriptive=('impurity_importance_descriptive','mean')).reset_index().to_csv(e.OUT/'tables/feature_usage_stability.csv',index=False)
    node=tables['nodes'];threshold=node.groupby(['experiment','protocol','repeat','fold','feature']).threshold_original.agg(n_splits='size',q10=lambda x:x.quantile(.1),median='median',q90=lambda x:x.quantile(.9)).reset_index()
    threshold.to_csv(e.OUT/'tables/threshold_by_outer_fit.csv',index=False)
    threshold.groupby(['experiment','protocol','feature']).agg(n_fits_using_feature=('median','size'),mean_threshold=('median','mean'),sd_threshold=('median','std'),mean_q10=('q10','mean'),mean_q90=('q90','mean')).reset_index().to_csv(e.OUT/'tables/threshold_stability_across_fits.csv',index=False)
    tables['leaves'].groupby(['experiment','protocol']).n_leaf_samples.agg(minimum='min',median='median',q10=lambda x:x.quantile(.1),q90=lambda x:x.quantile(.9)).reset_index().to_csv(e.OUT/'tables/leaf_support_summary.csv',index=False)
    tables['effects'].groupby(['experiment','protocol','repeat','fold','feature']).agg(n_bins=('bin','size'),n_supported_bins=('supported','sum'),complete_ALE_supported=('ALE',lambda x:x.notna().all())).reset_index().to_csv(e.OUT/'tables/ALE_support_summary.csv',index=False)
    per=tables['permutation'];valid=per[per.permutation.ge(0)]
    valid.groupby(['experiment','protocol']).agg(mean_delta_MSE=('delta_MSE','mean'),mean_delta_MAE=('delta_MAE','mean'),n_eligible_mean=('n_eligible','mean'),n_profiles_mean=('n_profiles','mean'),n_permutations=('permutation','size')).reset_index().to_csv(e.OUT/'tables/conditional_block_permutation_summary.csv',index=False)
    municipality_omissions(p)
    plots(tables)

def municipality_omissions(p):
    _,t,_=e.load();rows=[]
    for name in e.SPECS:
        for base in ['F6-E0','C-T3','F5-01']:
            for protocol in ['municipality','spatial']:
                a=p[(p.experiment==name)&(p.protocol==protocol)];b=p[(p.experiment==base)&(p.protocol==protocol)]
                z=a[[e.ID,'y_true','y_pred']].merge(b[[e.ID,'y_pred']],on=e.ID,suffixes=('','_base'),validate='one_to_one').merge(t[[e.ID,'Municipio']],on=e.ID)
                for municipality in z.Municipio.unique():
                    h=z[z.Municipio.ne(municipality)];er=h.y_pred-h.y_true;eb=h.y_pred_base-h.y_true
                    rows.append(dict(candidate=name,baseline=base,protocol=protocol,omitted_municipality=municipality,n=len(h),delta_RMSE=np.sqrt(np.mean(er**2))-np.sqrt(np.mean(eb**2)),delta_MAE=abs(er).mean()-abs(eb).mean(),refit=False))
    pd.DataFrame(rows).to_csv(e.OUT/'tables/municipality_omission_sensitivity.csv',index=False)

def plots(tables):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    for name in e.SPECS:
        columns=e.BLOCKS[name];fig,axes=plt.subplots(1,len(columns),figsize=(7*len(columns),5),squeeze=False)
        for ax,column in zip(axes[0],columns):
            rows=tables['effects'][(tables['effects'].experiment==name)&(tables['effects'].feature==column)&tables['effects'].protocol.eq('random')]
            g=rows.groupby('bin').agg(midpoint=('midpoint','mean'),effect=('ALE','mean'))
            if g.effect.notna().sum()>=2:ax.plot(g.midpoint,g.effect,marker='o');label='ALE respaldado (t/ha)'
            else:
                g=rows[rows.supported].groupby('bin').agg(midpoint=('midpoint','mean'),effect=('local_difference','mean'));ax.scatter(g.midpoint,g.effect);label='Cambio local respaldado (t/ha)'
            ax.axhline(0,color='black',lw=.7);ax.set(title=f'{name}: {column}',xlabel='Valor original; centros de cuantiles por fit',ylabel=label)
            if not len(g):ax.text(.5,.5,'Soporte insuficiente',ha='center',transform=ax.transAxes)
        fig.tight_layout();fig.savefig(e.OUT/'figures'/f'ALE_added_block_{name}.png',dpi=170);plt.close(fig)
    inter=tables['interactions']
    for name in e.SPECS:
        pairs=e.INTERACTIONS[name];fig,axes=plt.subplots(1,len(pairs),figsize=(7*len(pairs),5),squeeze=False)
        for ax,(first,second) in zip(axes[0],pairs):
            h=inter[(inter.experiment==name)&inter['first'].eq(first)&inter.second.eq(second)&inter.protocol.eq('random')]
            matrix=h.groupby(['bin_first','bin_second']).mixed_local_difference.mean().unstack().reindex(index=range(3),columns=range(3))
            limit=float(abs(matrix).max().max())
            if not np.isfinite(limit) or limit==0:limit=1.
            im=ax.imshow(matrix,origin='lower',cmap='coolwarm',vmin=-limit,vmax=limit);ax.set(title=name,xlabel=f'Tercil {second}',ylabel=f'Tercil {first}');fig.colorbar(im,ax=ax,label='Diferencia mixta respaldada (t/ha)')
        fig.tight_layout();fig.savefig(e.OUT/'figures'/f'interactions_{name}.png',dpi=170);plt.close(fig)
    fig,ax=plt.subplots(figsize=(11,5));g=tables['stability'];g=g[g.prefix_n_trees.eq(256)].groupby(['experiment','protocol']).RMS_prediction_difference_from_384.mean().unstack();g.plot.barh(ax=ax);ax.axvline(.01,color='black',ls='--');ax.set_xlabel('Diferencia RMS:256 frente a384 árboles (t/ha)');fig.tight_layout();fig.savefig(e.OUT/'figures/tree_count_stability.png',dpi=170);plt.close(fig)
