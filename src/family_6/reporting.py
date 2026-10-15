"""OOF complete-repeat comparisons, locality, influence and calibrated-coverage diagnostics."""
import json,itertools
import numpy as np
import pandas as pd
from . import execution as e
from src.family_4.stage_d_evidence import metrics

PAIRS=[]

def save(z,name):
    path=e.OUT/'tables'/name
    if path.suffix=='.parquet':z.to_parquet(path,index=False)
    else:z.to_csv(path,index=False)

def build(p):
    names=sorted(x for x in p.experiment.unique() if x.startswith('F6-'))
    global PAIRS
    PAIRS=[(x,b) for x in names for b in ['C-T3','F5-01','CHAMPION']]+[('F6-01','F6-00')]+[(x,'F6-01') for x in names if x not in ['F6-00','F6-01']]
    _,t,splits=e.load();context=t[[e.ID,'climate_profile','Municipio','Estado']]
    q=p.merge(context,on=e.ID,validate='many_to_one');q['error']=q.y_pred-q.y_true;q['SE']=q.error**2;q['AE']=abs(q.error)
    allmetrics=[];foldmetrics=[];stratum=[];interval=[];support=[]
    for (exp,protocol,repeat),g in q.groupby(['experiment','protocol','repeat']):
        allmetrics.append(dict(experiment=exp,protocol=protocol,repeat=repeat,**metrics(g)))
        for name,mask in [('Chignahuapan',g.Municipio.eq('Chignahuapan')),('outside_Chignahuapan',g.Municipio.ne('Chignahuapan'))]:
            h=g[mask];stratum.append(dict(experiment=exp,protocol=protocol,repeat=repeat,stratum=name,**metrics(h)))
        if exp=='F5-01':
            for name,mask in [('all',np.ones(len(g),bool)),('known_profile',g.profile_known.eq(True)),('new_profile',g.profile_known.eq(False)),('outside_marginal_support',g.outside_marginal_support.eq(True)),('inside_marginal_support',g.outside_marginal_support.eq(False))]:
                h=g[mask]
                if not len(h):continue
                interval.append(dict(experiment=exp,protocol=protocol,repeat=repeat,stratum=name,n=len(h),coverage=((h.y_true>=h.lower)&(h.y_true<=h.upper)).mean(),mean_width=(h.upper-h.lower).mean(),mean_predictive_sd=h.predictive_sd.mean(),mean_latent_sd=h.latent_sd.mean(),mean_noise_variance=h.noise_variance.mean(),**{k:v for k,v in metrics(h).items() if k!='n'}))
                support.append(dict(experiment=exp,protocol=protocol,repeat=repeat,stratum=name,**metrics(h),mean_nearest_training_distance=h.nearest_training_distance_z.mean()))
    for (exp,protocol,repeat,fold),g in q.groupby(['experiment','protocol','repeat','fold']):foldmetrics.append(dict(experiment=exp,protocol=protocol,repeat=repeat,fold=fold,**metrics(g)))
    m=pd.DataFrame(allmetrics);save(m,'metrics_repeat.csv')
    summary=m.groupby(['experiment','protocol']).agg(RMSE=('RMSE','mean'),MAE=('MAE','mean'),bias=('bias','mean'),RMSE_sd_repeats=('RMSE','std'),n=('n','first'),n_repeats=('repeat','size')).reset_index();save(summary,'metrics_summary.csv')
    save(pd.DataFrame(foldmetrics),'fold_metrics_diagnostic.csv');save(pd.DataFrame(stratum),'subgroup_metrics_repeat.csv');save(pd.DataFrame(stratum).groupby(['experiment','protocol','stratum']).mean(numeric_only=True).reset_index(),'subgroup_metrics_summary.csv')
    intervals=pd.DataFrame(interval);save(intervals,'interval_coverage_repeat.csv');save(intervals.groupby(['experiment','protocol','stratum']).mean(numeric_only=True).reset_index(),'interval_coverage_summary.csv');save(pd.DataFrame(support),'predictor_support_metrics_repeat.csv')
    paired=[];losses=[];blockgains=[];omissions=[];influence=[];removed=[];groupgain=[]
    key=[e.ID,'protocol','repeat','fold']
    for candidate,baseline in PAIRS:
        z=q[q.experiment.eq(candidate)].merge(q[q.experiment.eq(baseline)],on=key,validate='one_to_one',suffixes=('','_base'))
        assert np.array_equal(z.y_true,z.y_true_base)
        z['SE_gain']=z.SE_base-z.SE;z['AE_gain']=z.AE_base-z.AE;z['candidate']=candidate;z['baseline']=baseline
        losses.append(z[key+['y_true','y_pred','y_pred_base','SE','SE_base','AE','AE_base','SE_gain','AE_gain','candidate','baseline']])
        for (protocol,repeat),g in z.groupby(['protocol','repeat']):
            a=metrics(g);b=metrics(g.rename(columns={'y_pred':'discard','y_pred_base':'y_pred'}))
            paired.append(dict(candidate=candidate,baseline=baseline,protocol=protocol,repeat=repeat,n=len(g),delta_RMSE=a['RMSE']-b['RMSE'],delta_MAE=a['MAE']-b['MAE'],delta_bias=a['bias']-b['bias'],SSE_gain=g.SE_gain.sum(),mean_SE_gain=g.SE_gain.mean(),median_SE_gain=g.SE_gain.median(),fraction_SE_improve=(g.SE_gain>1e-12).mean(),fraction_AE_improve=(g.AE_gain>1e-12).mean()))
        for (protocol,repeat,fold),g in z.groupby(['protocol','repeat','fold']):
            ea=(g.y_pred-g.y_true).to_numpy();eb=(g.y_pred_base-g.y_true).to_numpy()
            blockgains.append(dict(candidate=candidate,baseline=baseline,protocol=protocol,repeat=repeat,fold=fold,n=len(g),SSE_gain=g.SE_gain.sum(),mean_AE_gain=g.AE_gain.mean(),delta_RMSE=np.sqrt(np.mean(ea**2))-np.sqrt(np.mean(eb**2)),delta_MAE=np.mean(abs(ea))-np.mean(abs(eb)),bias_candidate=ea.mean(),bias_base=eb.mean(),bias_squared_gain=len(g)*(eb.mean()**2-ea.mean()**2),error_variance_gain=len(g)*(eb.var()-ea.var())))
        for protocol in ['spatial','municipality']:
            gg=z[z.protocol.eq(protocol)]
            if not len(gg):continue
            for fold in range(1,6):
                h=gg[gg.fold.ne(fold)];a=metrics(h);b=metrics(h.rename(columns={'y_pred':'discard','y_pred_base':'y_pred'}))
                omissions.append(dict(candidate=candidate,baseline=baseline,protocol=protocol,omitted_fold=fold,n=len(h),delta_RMSE=a['RMSE']-b['RMSE'],delta_MAE=a['MAE']-b['MAE'],SSE_gain=h.SE_gain.sum(),analysis='OOF aggregation sensitivity only; no refitting'))
        byparcel=z.groupby(['protocol',e.ID])[['SE','SE_base','AE','AE_base','SE_gain','AE_gain']].mean().reset_index().merge(context,on=e.ID,validate='many_to_one');byparcel['candidate']=candidate;byparcel['baseline']=baseline
        save(byparcel,f'parcel_gains_{candidate}_vs_{baseline}.csv')
        for protocol,g in byparcel.groupby('protocol'):
            net=g.SE_gain.sum();pos=g.loc[g.SE_gain>0,'SE_gain'].sum()
            for k in [1,5,10]:
                top=g.nlargest(k,'SE_gain');bottom=g.nsmallest(k,'SE_gain')
                influence.append(dict(candidate=candidate,baseline=baseline,protocol=protocol,k=k,net_SSE_gain=net,top_positive_gain=top.SE_gain.sum(),fraction_net_gain=top.SE_gain.sum()/net if abs(net)>1e-12 else np.nan,fraction_positive_gain=top.SE_gain.sum()/pos if pos else np.nan,top_ids=json.dumps(top[e.ID].tolist()),bottom_gain=bottom.SE_gain.sum(),bottom_ids=json.dumps(bottom[e.ID].tolist())))
                kept=g[~g[e.ID].isin(top[e.ID])]
                removed.append(dict(candidate=candidate,baseline=baseline,protocol=protocol,n_removed=k,n_remaining=len(kept),delta_RMSE_pooled_mean_loss=np.sqrt(kept.SE.mean())-np.sqrt(kept.SE_base.mean()),delta_MAE=kept.AE.mean()-kept.AE_base.mean(),SSE_gain=kept.SE_gain.sum(),removed_ids=json.dumps(top[e.ID].tolist()),analysis='Descriptive influential-case omission; meanparcel losses, not primary meanrepeat RMSE'))
            for field in ['Municipio','climate_profile']:
                for value,h in g.groupby(field):groupgain.append(dict(candidate=candidate,baseline=baseline,protocol=protocol,group_type=field,group=value,n=len(h),SSE_gain=h.SE_gain.sum(),mean_AE_gain=h.AE_gain.mean(),fraction_improve=(h.SE_gain>0).mean()))
    paired=pd.DataFrame(paired);save(paired,'paired_metrics_repeat.csv');save(paired.groupby(['candidate','baseline','protocol']).mean(numeric_only=True).reset_index(),'paired_metrics_summary.csv');save(pd.concat(losses,ignore_index=True),'paired_parcel_losses.parquet');save(pd.DataFrame(blockgains),'paired_fold_contributions.csv');save(pd.DataFrame(omissions),'fold_omission_sensitivity.csv');save(pd.DataFrame(influence),'gain_concentration.csv');save(pd.DataFrame(removed),'influential_parcel_omission.csv');save(pd.DataFrame(groupgain),'paired_group_gains.csv')
    pairrows=[]
    for (exp,protocol,repeat,fold,profile),g in q.groupby(['experiment','protocol','repeat','fold','climate_profile']):
        for a,b in itertools.combinations(g[[e.ID,'y_true','y_pred','Municipio']].to_numpy(),2):pairrows.append(dict(experiment=exp,protocol=protocol,repeat=repeat,fold=fold,profile=profile,id_a=a[0],id_b=b[0],observed_difference=float(a[1]-b[1]),predicted_difference=float(a[2]-b[2]),pair_error=float((a[2]-b[2])-(a[1]-b[1])),both_Chignahuapan=bool(a[3]=='Chignahuapan' and b[3]=='Chignahuapan'),both_outside_Chignahuapan=bool(a[3]!='Chignahuapan' and b[3]!='Chignahuapan')))
    pairs=pd.DataFrame(pairrows);save(pairs,'same_model_pair_errors.parquet');local=[];perprofile=[]
    for scope,mask in [('all',np.ones(len(pairs),bool)),('both_Chignahuapan',pairs.both_Chignahuapan),('both_outside_Chignahuapan',pairs.both_outside_Chignahuapan)]:
        for (exp,protocol,repeat),g in pairs[mask].groupby(['experiment','protocol','repeat']):
            profiles=g.groupby('profile').pair_error.agg(mse=lambda x:np.mean(x*x),mae=lambda x:abs(x).mean(),n_pairs='size')
            local.append(dict(experiment=exp,protocol=protocol,repeat=repeat,scope=scope,n_pairs=len(g),n_profiles=len(profiles),n_parcels=len(set(g.id_a)|set(g.id_b)),equal_profile_RMSE=np.sqrt(profiles.mse.mean()),equal_profile_MAE=profiles.mae.mean(),pair_weighted_RMSE=np.sqrt(np.mean(g.pair_error**2)),pair_weighted_MAE=abs(g.pair_error).mean()))
            for profile,h in g.groupby('profile'):perprofile.append(dict(experiment=exp,protocol=protocol,repeat=repeat,scope=scope,profile=profile,n_pairs=len(h),n_parcels=len(set(h.id_a)|set(h.id_b)),pair_RMSE=np.sqrt(np.mean(h.pair_error**2)),pair_MAE=abs(h.pair_error).mean()))
    local=pd.DataFrame(local);save(local,'intraprofile_metrics_repeat.csv');save(local.groupby(['experiment','protocol','scope']).mean(numeric_only=True).reset_index(),'intraprofile_metrics_summary.csv');save(pd.DataFrame(perprofile),'intraprofile_by_profile_repeat.csv')
    # Honest internal diagnostic fits are retained separately from outer evaluation.
    inner=pd.read_parquet(e.OUT/'tables/inner_oof_predictions.parquet');im=[]
    for (exp,protocol,repeat,fold),g in inner.groupby(['experiment','protocol','repeat','fold']):im.append(dict(experiment=exp,protocol=protocol,repeat=repeat,fold=fold,**metrics(g),source='selected inner OOF; optimistic selection diagnostic, not independent validation'))
    save(pd.DataFrame(im),'inner_metrics_by_outer_train.csv')
    save(q,'errors_with_geography.parquet')
    territorial=[]
    for field in ['Municipio','Estado']:
        for (exp,protocol,repeat,value),g in q.groupby(['experiment','protocol','repeat',field]):territorial.append(dict(experiment=exp,protocol=protocol,repeat=repeat,group_type=field,group=value,**metrics(g)))
    territory=pd.DataFrame(territorial);save(territory,'territorial_metrics_repeat.csv')
    save(territory.groupby(['experiment','protocol','group_type','group']).agg(n=('n','first'),RMSE=('RMSE','mean'),MAE=('MAE','mean'),bias=('bias','mean'),n_repeats=('repeat','size')).reset_index(),'territorial_metrics_summary.csv')
    reg=pd.read_csv(e.OUT/'tables/fit_registry.csv');outer_reg=reg[reg.context.eq('outer')]
    save(outer_reg.groupby(['experiment','protocol','candidate_index']).size().rename('n_selected').reset_index(),'parameter_selection_stability.csv')
    plots(summary)
    from .diagnostics import build as tree_diagnostics
    tree_diagnostics(p)
    champion_stage_controls(p)
    from .interpretation import write
    write(summary)

def metric_summary(p):
    rows=[dict(experiment=x,protocol=pr,repeat=r,**metrics(g)) for (x,pr,r),g in p.groupby(['experiment','protocol','repeat'])]
    m=pd.DataFrame(rows)
    return m,m.groupby(['experiment','protocol']).agg(RMSE=('RMSE','mean'),MAE=('MAE','mean'),bias=('bias','mean'),n=('n','first'),n_repeats=('repeat','size')).reset_index()

def plots(summary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    for metric in ['RMSE','MAE']:
        fig,ax=plt.subplots(figsize=(10,5));summary.pivot(index='experiment',columns='protocol',values=metric).plot.barh(ax=ax)
        ax.set(xlabel=f'{metric} OOF completa (t/ha)',ylabel='Modelo');fig.tight_layout();fig.savefig(e.OUT/'figures'/f'global_{metric}.png',dpi=170);plt.close(fig)
    z=pd.read_csv(e.OUT/'tables/paired_fold_contributions.csv')
    z=z[z.protocol.eq('spatial')&z.baseline.eq('C-T3')]
    fig,ax=plt.subplots(figsize=(10,5));z.pivot(index='fold',columns='candidate',values='SSE_gain').plot.bar(ax=ax)
    ax.axhline(0,color='black',lw=.7);ax.set(xlabel='Bloque espacial',ylabel='Ganancia SSE frente a C-T3');fig.tight_layout();fig.savefig(e.OUT/'figures/spatial_block_gains.png',dpi=170);plt.close(fig)
    z=pd.read_csv(e.OUT/'tables/intraprofile_metrics_summary.csv');z=z[z.scope.eq('all')]
    fig,ax=plt.subplots(figsize=(10,5));z.pivot(index='experiment',columns='protocol',values='equal_profile_RMSE').plot.barh(ax=ax)
    ax.set(xlabel='RMSE diferencias intraperfil, igual peso por perfil (t/ha)',ylabel='Modelo');fig.tight_layout();fig.savefig(e.OUT/'figures/intraprofile_RMSE.png',dpi=170);plt.close(fig)

def champion_stage_controls(p):
    """Read-only contextual stage controls; different inputs, random-only validation."""
    path=e.ROOT/'outputs/modeling/residual_signal_audit/stage4_champion_reconstruction/predictions/oof_predictions.parquet'
    archive=pd.read_parquet(path);names=['TOP20_ENET_BASE','TOP20_ENET_HISTORY15','PRECIPITATION_XGB_BASE']
    z=archive[archive.pipeline.isin(names)].copy();z['experiment']=z.pipeline;z['protocol']='random'
    _,t,splits=e.load();gate=[]
    for name in names:
        for protocol,repeat,fold,tr,va,inner in splits:
            if protocol!='random':continue
            q=z[(z.experiment==name)&(z['repeat']==repeat)&(z.fold==fold)].set_index(e.ID)
            assert set(q.index)==set(t.iloc[va][e.ID])
            np.testing.assert_allclose(q.y_true.reindex(t.iloc[va][e.ID]),t.iloc[va][e.TARGET],atol=1e-12)
            gate.append(dict(control=name,repeat=repeat,fold=fold,exact_validation_ids=True,n=len(q)))
    save(pd.DataFrame(gate),'champion_stage_compatibility.csv')
    save(z[['experiment','protocol','repeat','fold',e.ID,'y_true','y_pred']],'champion_stage_controls_oof.parquet')
    cm,cs=metric_summary(z);save(cm,'champion_stage_metrics_repeat.csv');save(cs,'champion_stage_metrics_summary.csv')
    paired=[]
    for name in sorted(x for x in p.experiment.unique() if x.startswith('F6-')):
        for base in names:
            q=p[(p.experiment==name)&p.protocol.eq('random')].merge(z[z.experiment.eq(base)],on=[e.ID,'protocol','repeat','fold'],validate='one_to_one',suffixes=('','_base'))
            assert np.array_equal(q.y_true,q.y_true_base)
            for repeat,g in q.groupby('repeat'):
                a=metrics(g);b=metrics(g.rename(columns={'y_pred':'discard','y_pred_base':'y_pred'}))
                paired.append(dict(candidate=name,baseline=base,protocol='random',repeat=repeat,n=len(g),delta_RMSE=a['RMSE']-b['RMSE'],delta_MAE=a['MAE']-b['MAE'],SSE_gain=b['SSE']-a['SSE'],different_predictors=True,context_only=True))
    save(pd.DataFrame(paired),'champion_stage_paired_metrics_repeat.csv')
