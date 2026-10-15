"""Descriptive fitted-tree diagnostics, training-supported effects and heldout permutations."""
import json
import joblib,numpy as np,pandas as pd
from threadpoolctl import threadpool_limits
from src.family_4.stage_d_evidence import metrics
from . import execution as e

def ale(model,X,column,n_bins=6,min_support=5):
    values=X[column].to_numpy(float);finite=np.isfinite(values)
    edges=np.unique(np.quantile(values[finite],np.linspace(0,1,n_bins+1)))
    if len(edges)<3:return []
    bins=np.clip(np.searchsorted(edges,values,side='right')-1,0,len(edges)-2);rows=[]
    for b in range(len(edges)-1):
        mask=finite&(bins==b);a=X.loc[mask].copy();n=len(a)
        if not n:continue
        lo=a.copy();hi=a.copy();lo[column]=edges[b];hi[column]=edges[b+1]
        local=float((model.predict(hi)-model.predict(lo)).mean()) if n>=min_support else np.nan
        rows.append(dict(feature=column,bin=b,lower=edges[b],upper=edges[b+1],midpoint=(edges[b]+edges[b+1])/2,n=n,local_difference=local,supported=n>=min_support))
    # Cumulative effects cannot cross a gap with unsupported local differences.
    if rows and all(r['supported'] for r in rows):
        accumulated=np.cumsum([r['local_difference'] for r in rows]);centre=np.average(accumulated,weights=[r['n'] for r in rows])
        for row,value in zip(rows,accumulated):row['ALE']=float(value-centre)
    else:
        for row in rows:row['ALE']=np.nan
    return rows

def interaction(model,X,first,second,min_support=5):
    edges=[np.unique(X[c].dropna().quantile([0,1/3,2/3,1]).to_numpy()) for c in [first,second]]
    if any(len(a)<3 for a in edges):return []
    bins=[np.clip(np.searchsorted(a,X[c].to_numpy(),side='right')-1,0,len(a)-2) for a,c in zip(edges,[first,second])]
    rows=[]
    for i in range(len(edges[0])-1):
        for j in range(len(edges[1])-1):
            mask=(bins[0]==i)&(bins[1]==j)&X[first].notna().to_numpy()&X[second].notna().to_numpy();a=X.loc[mask].copy();n=len(a)
            mixed=np.nan
            if n>=min_support:
                pred=[]
                for u,v in [(0,0),(0,1),(1,0),(1,1)]:
                    z=a.copy();z[first]=edges[0][i+u];z[second]=edges[1][j+v];pred.append(model.predict(z))
                mixed=float(np.mean(pred[3]-pred[2]-pred[1]+pred[0]))
            rows.append(dict(first=first,second=second,bin_first=i,bin_second=j,n=n,supported=n>=min_support,mixed_local_difference=mixed,first_low=edges[0][i],first_high=edges[0][i+1],second_low=edges[1][j],second_high=edges[1][j+1]))
    return rows

def build(p):
    _,t,splits=e.load();reg=pd.read_csv(e.OUT/'tables/fit_registry.csv');reg=reg[reg.context.eq('outer')]
    nodes=[];usage=[];effects=[];interactions=[];stability=[];permutation=[];support=[];municipality_omit=[]
    with threadpool_limits(limits=1):
        for row in reg.itertuples():
            key=dict(experiment=row.experiment,protocol=row.protocol,repeat=row.repeat,fold=row.fold)
            model=joblib.load(e.OUT/'models'/f'{row.experiment}_{row.protocol}_{row.repeat}_{row.fold}_outer.joblib')
            a=t.set_index(e.ID,drop=False).loc[json.loads(row.train_ids)];v=t.set_index(e.ID,drop=False).loc[json.loads(row.validation_ids)]
            names=model.preprocess_.get_feature_names_out().tolist();indices=np.flatnonzero(model.preprocess_.support_);counts=np.zeros(len(names));trees=np.zeros(len(names));roots=np.zeros(len(names))
            for tree_index,est in enumerate(model.forest_.estimators_):
                tr=est.tree_;active=np.flatnonzero(tr.feature>=0);used=set(tr.feature[active])
                for feature in used:trees[feature]+=1
                if tr.feature[0]>=0:roots[tr.feature[0]]+=1
                for node in active:
                    f=tr.feature[node];original_index=indices[f];threshold=model.preprocess_.mean_[original_index]+tr.threshold[node]*model.preprocess_.scale_[original_index];counts[f]+=1
                    nodes.append({**key,'tree':tree_index,'node':int(node),'feature':names[f],'threshold_original':float(threshold),'n_node_unique_samples':int(tr.n_node_samples[node]),'weighted_n_node_samples':float(tr.weighted_n_node_samples[node]),'root':node==0})
            for j,name in enumerate(names):usage.append({**key,'feature':name,'n_splits':int(counts[j]),'fraction_splits':float(counts[j]/counts.sum()) if counts.sum() else 0.,'fraction_trees_using_feature':trees[j]/e.N_TREES,'fraction_roots':roots[j]/e.N_TREES,'impurity_importance_descriptive':float(model.forest_.feature_importances_[j])})
            for column in e.SPECS[row.experiment]['columns']:
                effects.extend([{**key,**r} for r in ale(model,a,column)])
            rain='compact_precip_total' if 'compact_precip_total' in model.columns else e.prior.RAIN[0]
            interactions.extend([{**key,**r} for r in interaction(model,a,rain,e.prior.old.c.NDVI)])
            q=p[(p.experiment==row.experiment)&(p.protocol==row.protocol)&(p['repeat']==row.repeat)&(p.fold==row.fold)].set_index(e.ID).loc[v[e.ID]]
            pred=q.y_pred.to_numpy();err=pred-v[e.TARGET].to_numpy()
            for n in [128,256]:
                pp=q[f'prediction_{n}_trees'].to_numpy();diff=pp-pred
                stability.append({**key,'prefix_n_trees':n,'n':len(v),'RMS_prediction_difference_from_384':float(np.sqrt(np.mean(diff**2))),'max_absolute_prediction_difference':float(abs(diff).max()),'RMSE_prefix':float(np.sqrt(np.mean((pp-v[e.TARGET])**2))),'RMSE_384':float(np.sqrt(np.mean(err**2)))})
            distance=q.nearest_training_distance_z.to_numpy()
            for name,mask in [('all',np.ones(len(v),bool)),('outside_marginal_support',q.outside_marginal_support.eq(True).to_numpy()),('inside_marginal_support',q.outside_marginal_support.eq(False).to_numpy())]:
                if not mask.any():continue
                h=q.iloc[np.flatnonzero(mask)];support.append({**key,'stratum':name,**metrics(h),'mean_distance':float(distance[mask].mean()),'training_y_mean':float(a[e.TARGET].mean()),'prediction_mean':float(h.y_pred.mean()),'observed_mean':float(h.y_true.mean())})
            # Only NDVI is shuffled, only among climate-profile peers in validation.
            eligible=v.climate_profile.map(v.climate_profile.value_counts()).ge(2);n_eligible=int(eligible.sum());n_profiles=v.loc[eligible,'climate_profile'].nunique()
            if n_eligible>=10:
                rng=np.random.default_rng(e.SEED)
                for permutation_index in range(10):
                    shuffled=v.copy()
                    for _,g in v.loc[eligible].groupby('climate_profile'):
                        shuffled.loc[g.index,e.prior.old.c.NDVI]=rng.permutation(g[e.prior.old.c.NDVI].to_numpy())
                    pp=model.predict(shuffled);mask=eligible.to_numpy();before=err[mask];after=(pp-v[e.TARGET].to_numpy())[mask]
                    permutation.append({**key,'permutation':permutation_index,'n_eligible':n_eligible,'n_profiles':n_profiles,'delta_MSE':float(np.mean(after**2)-np.mean(before**2)),'delta_MAE':float(np.mean(abs(after))-np.mean(abs(before))),'method':'heldout within-profile NDVI permutation; descriptive dependency, not refitted ablation or causality'})
    pd.DataFrame(nodes).to_parquet(e.OUT/'tables/split_thresholds.parquet',index=False)
    usage=pd.DataFrame(usage);usage.to_csv(e.OUT/'tables/feature_usage_by_outer_fit.csv',index=False)
    usage.groupby(['experiment','protocol','feature']).agg(fraction_trees_mean=('fraction_trees_using_feature','mean'),fraction_trees_sd=('fraction_trees_using_feature','std'),root_frequency_mean=('fraction_roots','mean'),split_fraction_mean=('fraction_splits','mean'),impurity_mean_descriptive=('impurity_importance_descriptive','mean')).reset_index().to_csv(e.OUT/'tables/feature_usage_stability.csv',index=False)
    node=pd.DataFrame(nodes);node.groupby(['experiment','protocol','feature']).threshold_original.agg(n='size',q10=lambda x:x.quantile(.1),median='median',q90=lambda x:x.quantile(.9)).reset_index().to_csv(e.OUT/'tables/threshold_distribution_descriptive.csv',index=False)
    effect=pd.DataFrame(effects);effect.to_csv(e.OUT/'tables/ALE_training_support_by_fold.csv',index=False)
    curves=effect.groupby(['experiment','protocol','repeat','fold','feature']).agg(n_bins=('bin','size'),n_supported_bins=('supported','sum'),full_curve_supported=('ALE',lambda x:x.notna().all())).reset_index()
    curves.to_csv(e.OUT/'tables/ALE_curve_support.csv',index=False)
    pd.DataFrame(interactions).to_csv(e.OUT/'tables/rain_NDVI_supported_local_interactions.csv',index=False)
    pd.DataFrame(stability).to_csv(e.OUT/'tables/tree_count_stability.csv',index=False);pd.DataFrame(permutation).to_csv(e.OUT/'tables/within_profile_NDVI_permutation.csv',index=False);pd.DataFrame(support).to_csv(e.OUT/'tables/predictor_support_by_fold.csv',index=False)
    for x in reg.experiment.unique():
        for base in ['C-T3','F5-01']:
            for protocol in ['municipality','spatial']:
                a=p[(p.experiment==x)&(p.protocol==protocol)];b=p[(p.experiment==base)&(p.protocol==protocol)]
                z=a[[e.ID,'y_true','y_pred']].merge(b[[e.ID,'y_pred']],on=e.ID,suffixes=('','_base'),validate='one_to_one').merge(t[[e.ID,'Municipio']],on=e.ID)
                for municipality in z.Municipio.unique():
                    h=z[z.Municipio.ne(municipality)];error=h.y_pred-h.y_true;eb=h.y_pred_base-h.y_true
                    municipality_omit.append(dict(candidate=x,baseline=base,protocol=protocol,omitted_municipality=municipality,n=len(h),delta_RMSE=np.sqrt(np.mean(error**2))-np.sqrt(np.mean(eb**2)),delta_MAE=abs(error).mean()-abs(eb).mean(),refit=False))
    pd.DataFrame(municipality_omit).to_csv(e.OUT/'tables/municipality_omission_sensitivity.csv',index=False)
    plots(pd.DataFrame(effects),pd.DataFrame(interactions),usage,pd.DataFrame(stability))

def plots(effects,interactions,usage,stability):
    import matplotlib.pyplot as plt
    names=sorted(effects.experiment.unique());fig,axes=plt.subplots(len(names),4,figsize=(16,4*len(names)),squeeze=False)
    columns=e.CORE
    for i,name in enumerate(names):
        for ax,column in zip(axes[i],columns):
            g=effects[(effects.experiment==name)&(effects.feature==column)&effects.protocol.eq('random')].groupby('bin').agg(midpoint=('midpoint','mean'),effect=('ALE','mean'))
            ylabel='ALE entrenado (t/ha)'
            if g.effect.notna().sum()>=2:ax.plot(g.midpoint,g.effect,marker='o')
            else:
                h=effects[(effects.experiment==name)&(effects.feature==column)&effects.protocol.eq('random')&effects.supported].groupby('bin').agg(midpoint=('midpoint','mean'),effect=('local_difference','mean'))
                if len(h):ax.scatter(h.midpoint,h.effect)
                ylabel='Cambio local respaldado; sin ALE continuo (t/ha)'
            ax.axhline(0,color='black',lw=.7);ax.set(title=f'{name}: {column}',ylabel=ylabel,xlabel='Valor original; centros de cuantiles por fold')
    fig.tight_layout();fig.savefig(e.OUT/'figures/ALE_compact_core.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,len(names),figsize=(6*len(names),5),squeeze=False)
    finite=interactions.mixed_local_difference.dropna();limit=max(float(abs(finite).max()),1e-6) if len(finite) else 1.
    for ax,name in zip(axes[0],names):
        h=interactions[(interactions.experiment==name)&interactions.protocol.eq('random')].groupby(['bin_first','bin_second']).mixed_local_difference.mean().unstack()
        im=ax.imshow(h,origin='lower',cmap='coolwarm',aspect='auto',vmin=-limit,vmax=limit);ax.set(title=name,xlabel='Tercil NDVI',ylabel='Tercil lluvia: diferencia local mixta')
        fig.colorbar(im,ax=ax,label='Diferencia local mixta (t/ha)')
    fig.tight_layout();fig.savefig(e.OUT/'figures/rain_NDVI_local_interactions.png',dpi=160);plt.close(fig)
    for name in names:
        extra=[c for c in e.SPECS[name]['columns'] if c not in e.CORE]
        if not extra:continue
        fig,axes=plt.subplots(int(np.ceil(len(extra)/3)),3,figsize=(15,4*int(np.ceil(len(extra)/3))),squeeze=False)
        for ax,column in zip(axes.ravel(),extra):
            g=effects[(effects.experiment==name)&(effects.feature==column)&effects.protocol.eq('random')].groupby('bin').agg(midpoint=('midpoint','mean'),effect=('ALE','mean'))
            ax.plot(g.midpoint,g.effect,marker='o');ax.set(title=column,ylabel='ALE (t/ha)',xlabel='Valor original')
        for ax in axes.ravel()[len(extra):]:ax.set_visible(False)
        fig.tight_layout();fig.savefig(e.OUT/'figures'/f'ALE_additional_{name}.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,5));z=stability[stability.prefix_n_trees.eq(256)].groupby(['experiment','protocol']).RMS_prediction_difference_from_384.mean().unstack();z.plot.barh(ax=ax);ax.axvline(.01,color='black',ls='--');ax.set_xlabel('Diferencia RMS de predicción: 256 frente a 384 árboles (t/ha)');fig.tight_layout();fig.savefig(e.OUT/'figures/tree_count_stability.png',dpi=170);plt.close(fig)
