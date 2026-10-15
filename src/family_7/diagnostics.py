"""Data-supported effects, actual tree partitions and regional diagnostics."""
import json
import joblib,numpy as np,pandas as pd
from threadpoolctl import threadpool_limits
from src.family_6.expansion import diagnostics as shared
from . import execution as e

def tree_tables(model,key,stem):
    features=model.preprocess_.get_feature_names_out().tolist()
    oi=np.flatnonzero(model.preprocess_.support_);nodes=[];leaves=[]
    z=model.training_z_
    if model.algorithm=='CatBoost':
        path=e.OUT/'audit/trees'/f'{stem}.json';path.parent.mkdir(exist_ok=True);model.booster_.save_model(str(path),format='json')
        trees=json.loads(path.read_text())['oblivious_trees'];indices=model.booster_.calc_leaf_indexes(z)
        for j,tree in enumerate(trees):
            for level,split in enumerate(tree.get('splits') or []):
                k=split['float_feature_index'];i=oi[k]
                nodes.append({**key,'tree':j,'node':level,'feature':features[k],
                    'threshold_original':float(split['border']*model.preprocess_.scale_[i]+model.preprocess_.mean_[i]),'kind':'symmetric level; shared across nodes','gain':np.nan})
            counts=np.bincount(indices[:,j].astype(int),minlength=len(tree['leaf_values']))
            for leaf,(count,weight) in enumerate(zip(counts,tree['leaf_weights'])):
                leaves.append({**key,'tree':j,'leaf':leaf,'n_routed_training':int(count),'native_weight':weight,'weight_kind':'CatBoost sum of observation weights'})
        importance=model.booster_.feature_importances_;importance_kind='PredictionValuesChange; descriptive'
    else:
        dump=model.booster_.get_booster().trees_to_dataframe();indices=np.asarray(model.booster_.apply(z)).astype(int)
        for row in dump.itertuples():
            if row.Feature=='Leaf':
                leaves.append({**key,'tree':row.Tree,'leaf':row.Node,'n_routed_training':int((indices[:,row.Tree]==row.Node).sum()),'native_weight':row.Cover,'weight_kind':'XGBoost construction Hessian sum'})
            else:
                k=int(row.Feature[1:]);i=oi[k]
                nodes.append({**key,'tree':row.Tree,'node':row.Node,'feature':features[k],
                    'threshold_original':float(row.Split*model.preprocess_.scale_[i]+model.preprocess_.mean_[i]),'kind':'asymmetric node','gain':row.Gain})
        importance=model.booster_.feature_importances_;importance_kind='normalized average split gain; descriptive'
    usage=[]
    for k,feature in enumerate(features):
        selected=[n for n in nodes if n['feature']==feature];thresholds=[n['threshold_original'] for n in selected]
        usage.append({**key,'feature':feature,'n_splits_or_levels':len(selected),'fraction_trees_used':len(set(n['tree'] for n in selected))/indices.shape[1],
            'threshold_q25':float(np.quantile(thresholds,.25)) if thresholds else np.nan,'threshold_median':float(np.median(thresholds)) if thresholds else np.nan,
            'threshold_q75':float(np.quantile(thresholds,.75)) if thresholds else np.nan,'importance_descriptive':float(importance[k]),'importance_kind':importance_kind})
    return nodes,leaves,usage

def diagnose_fold(index):
    _,t,splits=e.load();p,r,f,tr,va,_=splits[index];a,v=t.iloc[tr],t.iloc[va]
    out=dict(nodes=[],leaves=[],usage=[],effects=[],interactions=[],permutation=[])
    with threadpool_limits(limits=1):
        for name in e.SPECS:
            key=dict(experiment=name,protocol=p,repeat=r,fold=f);stem=f'{name}_{p}_{r}_{f}'
            model=joblib.load(e.OUT/'models'/f'{stem}_outer.joblib');radius=shared.support_radius(model)
            nodes,leaves,usage=tree_tables(model,key,stem)
            out['nodes']+=nodes;out['leaves']+=leaves;out['usage']+=usage
            for c in e.CORE:out['effects'] += [{**key,**row} for row in shared.ale(model,a,c,radius)]
            for first in e.CORE[:3]:out['interactions'] += [{**key,**row} for row in shared.interaction(model,a,first,e.CORE[-1],radius)]
            pred=model.predict(v)
            for block,cols in [('rain_compact3',e.CORE[:3]),('NDVI_may',[e.CORE[-1]])]:
                out['permutation'] += [{**key,'block':block,**row} for row in shared.conditional_block_permutation(model,v,cols,pred)]
    return out

def build(p):
    (e.OUT/'audit/trees').mkdir(exist_ok=True)
    parts=joblib.Parallel(n_jobs=6,backend='loky',inner_max_num_threads=1)(joblib.delayed(diagnose_fold)(i) for i in range(65))
    filenames=dict(nodes='tree_partitions.parquet',leaves='tree_leaf_support.parquet',usage='variable_partition_stability.csv',effects='effects_by_outer_fit.csv',interactions='interactions_by_outer_fit.csv',permutation='permutation_by_outer_fit.csv')
    for k,filename in filenames.items():
        table=pd.DataFrame([row for part in parts for row in part[k]])
        if filename.endswith('.parquet'):table.to_parquet(e.OUT/'tables'/filename,index=False)
        else:table.to_csv(e.OUT/'tables'/filename,index=False)
    effects=pd.read_csv(e.OUT/'tables/effects_by_outer_fit.csv')
    support=effects.groupby(['experiment','protocol','feature','repeat','fold']).supported.all().reset_index(name='full_ALE_supported')
    support.to_csv(e.OUT/'tables/ALE_support_by_fit.csv',index=False)
    usage=pd.read_csv(e.OUT/'tables/variable_partition_stability.csv')
    usage.groupby(['experiment','protocol','feature']).agg(n_fits=('fold','size'),fraction_used_mean=('fraction_trees_used','mean'),fraction_used_sd=('fraction_trees_used','std'),threshold_median_mean=('threshold_median','mean'),threshold_median_sd=('threshold_median','std'),importance_mean=('importance_descriptive','mean'),importance_sd=('importance_descriptive','std')).reset_index().to_csv(e.OUT/'tables/variable_stability_summary.csv',index=False)
    from src.family_4.stage_d_evidence import metrics
    rows=[]
    for (name,protocol,repeat),g in p[p.experiment.isin(e.SPECS)].groupby(['experiment','protocol','repeat']):
        for label,mask in [('outside_marginal_support',g.outside_marginal_support.eq(True)),('inside_marginal_support',g.outside_marginal_support.eq(False)),('known_profile',g.profile_known.eq(True)),('new_profile',g.profile_known.eq(False))]:
            h=g[mask]
            if len(h):rows.append(dict(experiment=name,protocol=protocol,repeat=repeat,stratum=label,**metrics(h),mean_nearest_training_distance=h.nearest_training_distance_z.mean(),mean_prediction_minus_train_mean=(h.y_pred-h.training_y_mean).mean()))
    pd.DataFrame(rows).to_csv(e.OUT/'tables/boosting_support_metrics_repeat.csv',index=False)
    _,t,_=e.load();q=p.merge(t[[e.ID,'Municipio','Estado']],on=e.ID,validate='many_to_one');omissions=[]
    pairs=[(name,b) for name in e.SPECS for b in ['C-T3','F5-01','F6-E0']]+[('F7-01','F7-00')]
    for name,baseline in pairs:
        z=q[q.experiment.eq(name)].merge(q[q.experiment.eq(baseline)],on=[e.ID,'protocol','repeat','fold'],suffixes=('','_base'),validate='one_to_one')
        for (protocol,repeat),g in z.groupby(['protocol','repeat']):
            for field in ['Municipio','Estado']:
                for value in g[field].unique():
                    h=g[g[field].ne(value)]
                    if not len(h):continue
                    a=metrics(h);b=metrics(h.rename(columns={'y_pred':'unused','y_pred_base':'y_pred'}))
                    omissions.append(dict(candidate=name,baseline=baseline,protocol=protocol,repeat=repeat,omitted_type=field,omitted_region=value,n=len(h),delta_RMSE=a['RMSE']-b['RMSE'],delta_MAE=a['MAE']-b['MAE'],SSE_gain=b['SSE']-a['SSE'],analysis='Complete-repeat OOF region omission, no refit; very small remaining groups are descriptive'))
    omit=pd.DataFrame(omissions);omit.to_csv(e.OUT/'tables/region_omission_repeat.csv',index=False)
    omit.groupby(['candidate','baseline','protocol','omitted_type','omitted_region']).agg(n=('n','first'),n_repeats=('repeat','size'),delta_RMSE=('delta_RMSE','mean'),delta_MAE=('delta_MAE','mean'),SSE_gain=('SSE_gain','mean')).reset_index().to_csv(e.OUT/'tables/region_omission_summary.csv',index=False)
    summarize_saved_diagnostics()
    self_plots(effects,p)

def summarize_saved_diagnostics():
    """Recompute summaries from saved diagnostics only; no fit or prediction."""
    raw=pd.read_csv(e.OUT/'tables/permutation_by_outer_fit.csv')
    keys=['experiment','protocol','repeat','fold','block']
    fits=raw.groupby(keys).agg(n_permutations=('delta_MSE','count'),n_eligible=('n_eligible','first'),n_profiles=('n_profiles','first'),mean_delta_MSE=('delta_MSE','mean'),mean_delta_MAE=('delta_MAE','mean')).reset_index()
    fits['identifiable']=fits.n_permutations.gt(0)
    fits.to_csv(e.OUT/'tables/conditional_permutation_summary_by_fit.csv',index=False)
    fits.groupby(['experiment','protocol','block']).agg(n_fits=('fold','size'),n_identifiable=('identifiable','sum'),mean_delta_MSE_equal_supported_fit=('mean_delta_MSE','mean'),mean_delta_MAE_equal_supported_fit=('mean_delta_MAE','mean'),mean_eligible_parcels=('n_eligible','mean')).reset_index().to_csv(e.OUT/'tables/conditional_permutation_summary.csv',index=False)
    reg=pd.read_csv(e.OUT/'tables/fit_registry.csv');reg=reg[reg.context.eq('outer')].copy()
    reg['iterations_upper_bound']=reg.actual_trees.eq(300)
    reg.groupby(['experiment','protocol']).agg(n_selected=('fold','size'),n_iterations_upper_bound=('iterations_upper_bound','sum'),mean_actual_trees=('actual_trees','mean'),mean_fit_seconds=('seconds','mean')).reset_index().to_csv(e.OUT/'tables/selected_rounds_boundary_diagnostic.csv',index=False)

def self_plots(effects,p):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    for feature in e.CORE:
        fig,axs=plt.subplots(1,2,figsize=(11,4))
        for ax,name in zip(axs,e.SPECS):
            z=effects[(effects.experiment==name)&effects.supported]
            z=z[z.feature.eq(feature)]
            for protocol,g in z.groupby('protocol'):ax.scatter(g.midpoint,g.local_difference,s=12,alpha=.4,label=protocol)
            ax.axhline(0,color='black',lw=.5);ax.set(title=name,xlabel=feature,ylabel='Diferencia local respaldada (t/ha)')
            if len(z):ax.legend(fontsize=7)
            else:ax.text(.5,.5,'Sin soporte suficiente',transform=ax.transAxes,ha='center')
        fig.tight_layout();fig.savefig(e.OUT/'figures'/f'local_effect_{feature}.png',dpi=150);plt.close(fig)
    interaction=pd.read_csv(e.OUT/'tables/interactions_by_outer_fit.csv')
    for first in e.CORE[:3]:
        fig,axs=plt.subplots(1,2,figsize=(10,4))
        for ax,name in zip(axs,e.SPECS):
            q=interaction[(interaction.experiment==name)&(interaction['first']==first)&interaction.supported]
            if len(q):
                z=q.groupby(['bin_first','bin_second']).mixed_local_difference.mean().unstack().reindex(index=range(3),columns=range(3))
                limit=max(float(abs(z.to_numpy()[np.isfinite(z.to_numpy())]).max()),1e-6)
                im=ax.imshow(np.ma.masked_invalid(z.to_numpy()),cmap='RdBu_r',vmin=-limit,vmax=limit,origin='lower');fig.colorbar(im,ax=ax,label='Diferencia mixta respaldada (t/ha)')
            else:ax.text(.5,.5,'Sin soporte suficiente',transform=ax.transAxes,ha='center')
            ax.set(title=name,xlabel='Tercil NDVI mayo',ylabel='Tercil '+first)
        fig.tight_layout();fig.savefig(e.OUT/'figures'/f'interaction_{first}_NDVI.png',dpi=150);plt.close(fig)
    z=pd.read_parquet(e.OUT/'tables/errors_with_geography.parquet')
    for protocol in ['municipality','spatial']:
        q=z[z.protocol.eq(protocol)];fig,ax=plt.subplots(figsize=(10,5))
        q.boxplot(column='error',by=['experiment','fold'],ax=ax,rot=90,showfliers=True)
        ax.axhline(0,color='black',lw=.6);ax.set(title=f'Errores OOF por fold — {protocol}',ylabel='Predicción − observado (t/ha)',xlabel='Modelo / fold');fig.suptitle('')
        fig.tight_layout();fig.savefig(e.OUT/'figures'/f'regional_error_distribution_{protocol}.png',dpi=150);plt.close(fig)
