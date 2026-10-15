"""Separate transfer, profile-level, within-profile and conditional/marginal C diagnostics."""
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from . import stage_c_models as c

def transfer_audit(new):
    controls=pd.read_parquet(c.OUT/'tables/archived_controls.parquet');controls=controls[controls.experiment.str.startswith('C-T')]
    p=pd.concat([controls,new],ignore_index=True);rows=[]
    for (exp,protocol,repeat,fold),g in p.groupby(['experiment','protocol','repeat','fold']):rows.append(dict(experiment=exp,protocol=protocol,repeat=repeat,fold=fold,n=len(g),sse=np.sum((g.y_pred-g.y_true)**2),**c.b.e.f.lm.k.metrics(g.y_true,g.y_pred)))
    pd.DataFrame(rows).to_csv(c.OUT/'tables/transfer_fold_metrics.csv',index=False)
    _,t=c.load();splits,_,_=c.b.e.f.lm.k.j.load_frozen_splits(t);support=[]
    for protocol,repeat,fold,tr,va,_ in splits:
        a,v=t.iloc[tr],t.iloc[va];fields=[c.DTR,c.COMPACT[0],c.NDVI]
        raw=a[fields].to_numpy();target=v[fields].to_numpy();mean=np.nanmean(raw,axis=0);sd=np.nanstd(raw,axis=0);sd=np.maximum(sd,1e-8)
        nearest=cdist((target-mean)/sd,(raw-mean)/sd).min(axis=1)
        for j,pid in enumerate(v[c.ID]):
            r=dict(protocol=protocol,repeat=repeat,fold=fold,ID_POLIGONO=pid,joint_nearest_training_distance_z=nearest[j])
            for k,field in enumerate(fields):
                lo,hi=np.nanmin(raw[:,k]),np.nanmax(raw[:,k]);width=max(hi-lo,1e-8);value=target[j,k]
                r[field+'_train_min']=lo;r[field+'_train_max']=hi;r[field+'_validation_value']=value
                r[field+'_support']='outside' if value<lo-1e-10 or value>hi+1e-10 else 'near_boundary' if min(value-lo,hi-value)<=.05*width else 'interior'
            support.append(r)
    s=pd.DataFrame(support);s.to_csv(c.OUT/'tables/validation_predictor_support.csv',index=False)
    q=p.merge(s,on=[c.ID,'protocol','repeat','fold'],validate='many_to_one');metrics=[]
    for (exp,protocol,repeat,band),g in q.groupby(['experiment','protocol','repeat',c.DTR+'_support']):metrics.append(dict(experiment=exp,protocol=protocol,repeat=repeat,dtr_support=band,n=len(g),**c.b.e.f.lm.k.metrics(g.y_true,g.y_pred)))
    pd.DataFrame(metrics).to_csv(c.OUT/'tables/dtr_support_metrics_repeat.csv',index=False)
    # Paired per-parcel loss and fold contribution; no model choice by support.
    comparisons=[('C-T2','C-T0'),('C-T2','C-T1'),('C-T3','C-T0'),('C-T4','C-T2'),('C-T1','C-T0')]
    losses=[];folds=[];leave=[]
    for candidate,baseline in comparisons:
        z=p[p.experiment.eq(candidate)].merge(p[p.experiment.eq(baseline)],on=[c.ID,'protocol','repeat','fold'],suffixes=('','_base'),validate='one_to_one')
        assert np.allclose(z.y_true,z.y_true_base)
        z['squared_gain']=(z.y_true-z.y_pred_base)**2-(z.y_true-z.y_pred)**2;z['absolute_gain']=abs(z.y_true-z.y_pred_base)-abs(z.y_true-z.y_pred)
        losses.append(z[[c.ID,'protocol','repeat','fold','squared_gain','absolute_gain']].assign(candidate=candidate,baseline=baseline))
        for (protocol,repeat,fold),g in z.groupby(['protocol','repeat','fold']):folds.append(dict(candidate=candidate,baseline=baseline,protocol=protocol,repeat=repeat,fold=fold,n=len(g),sse_gain=g.squared_gain.sum(),mean_absolute_gain=g.absolute_gain.mean()))
        for protocol in ['municipality','spatial']:
            gg=z[z.protocol.eq(protocol)]
            for excluded in range(1,6):
                g=gg[gg.fold.ne(excluded)]
                leave.append(dict(candidate=candidate,baseline=baseline,protocol=protocol,excluded_fold=excluded,n=len(g),delta_rmse=np.sqrt(np.mean((g.y_true-g.y_pred)**2))-np.sqrt(np.mean((g.y_true-g.y_pred_base)**2)),delta_mae=np.mean(abs(g.y_true-g.y_pred))-np.mean(abs(g.y_true-g.y_pred_base))))
    pd.concat(losses,ignore_index=True).to_parquet(c.OUT/'tables/transfer_paired_parcel_losses.parquet',index=False)
    pd.DataFrame(folds).to_csv(c.OUT/'tables/transfer_fold_sse_contributions.csv',index=False)
    pd.DataFrame(leave).to_csv(c.OUT/'tables/transfer_leave_one_block_out.csv',index=False)
    print('Transfer diagnostics complete before C-H fitting',flush=True)

def build(predictions):
    _,t=c.load();quart=pd.read_csv(c.ROOT/'outputs/research/family_1/soil_yield_quartile_analysis/v1/parcel_quartiles.csv')[[c.ID,'quartile']]
    p=predictions.merge(t[[c.ID,'climate_profile','Municipio','Estado']],on=c.ID,validate='many_to_one').merge(quart,on=c.ID,validate='many_to_one')
    rows=[];pairs=[];levels=[];intervals=[];support=[]
    for (exp,protocol,repeat),g in p.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g[c.ID].is_unique
        scopes={'all':np.ones(len(g),bool),'Chignahuapan':g.Municipio.eq('Chignahuapan'),'without_Chignahuapan':g.Municipio.ne('Chignahuapan')}
        scopes.update({label:g.quartile.eq(label) for label in ['Q1','Q2','Q3','Q4']})
        scopes.update({'municipality:'+str(v):g.Municipio.eq(v) for v in g.Municipio.unique()});scopes.update({'state:'+str(v):g.Estado.eq(v) for v in g.Estado.unique()})
        if exp.startswith('C-H') and exp!='C-H0':scopes.update({'known_profile':g.profile_known.eq(True),'new_profile':g.profile_known.eq(False)})
        for scope,mask in scopes.items():
            z=g[mask]
            if not len(z):continue
            rows.append(dict(experiment=exp,protocol=protocol,repeat=repeat,stratum=scope,n=len(z),sse=np.sum((z.y_true-z.y_pred)**2),**c.b.e.f.lm.k.metrics(z.y_true,z.y_pred)))
            if exp in ['C-H0M','C-H1']:intervals.append(dict(experiment=exp,protocol=protocol,repeat=repeat,stratum=scope,n=len(z),nominal=.9,coverage=np.mean((z.y_true>=z.lower)&(z.y_true<=z.upper)),mean_width=(z.upper-z.lower).mean(),min_width=(z.upper-z.lower).min(),max_width=(z.upper-z.lower).max()))
        # Profile-level mean error aggregates segments only within the same external model.
        for (profile,fold),z in g.groupby(['climate_profile','fold']):
            levels.append(dict(experiment=exp,protocol=protocol,repeat=repeat,fold=fold,profile=profile,n=len(z),observed_mean=z.y_true.mean(),predicted_mean=z.y_pred.mean(),profile_level_error=z.y_pred.mean()-z.y_true.mean(),observed_sd=z.y_true.std(),predicted_sd=z.y_pred.std(),mean_random_effect=z.random_effect.mean() if exp in ['C-H0M','C-H1'] else np.nan))
            if len(z)<2:continue
            z=z.sort_values(c.ID);a,b=np.triu_indices(len(z),1);dy=z.y_true.to_numpy()[a]-z.y_true.to_numpy()[b];dp=z.y_pred.to_numpy()[a]-z.y_pred.to_numpy()[b]
            for i,j,y,pred in zip(a,b,dy,dp):pairs.append(dict(experiment=exp,protocol=protocol,repeat=repeat,fold=fold,profile=profile,id_a=z[c.ID].iloc[i],id_b=z[c.ID].iloc[j],observed_difference=y,predicted_difference=pred,pair_error=y-pred,without_Chignahuapan=bool(z.Municipio.iloc[i]!='Chignahuapan' and z.Municipio.iloc[j]!='Chignahuapan')))
        if exp in ['C-H0M','C-H1']:
            for fold,z in g.groupby('fold'):support.append(dict(experiment=exp,protocol=protocol,repeat=repeat,fold=fold,n_known=int(z.profile_known.sum()),n_new=int((~z.profile_known.astype(bool)).sum()),n_known_profiles=z.loc[z.profile_known.eq(True),'climate_profile'].nunique(),n_new_profiles=z.loc[z.profile_known.eq(False),'climate_profile'].nunique()))
    m=pd.DataFrame(rows);m.to_csv(c.OUT/'tables/metrics_repeat.csv',index=False);summary=m.groupby(['experiment','protocol','stratum'])[['n','sse','RMSE','MAE','R2','bias_pred_minus_y']].mean().reset_index();summary.to_csv(c.OUT/'tables/metrics_summary.csv',index=False)
    level=pd.DataFrame(levels);level.to_csv(c.OUT/'tables/profile_level_errors.csv',index=False)
    levelmetrics=[]
    for (exp,protocol,repeat),z in level.groupby(['experiment','protocol','repeat']):
        byprofile=z.groupby('profile').apply(lambda g:np.average(g.profile_level_error,weights=g.n),include_groups=False)
        levelmetrics.append(dict(experiment=exp,protocol=protocol,repeat=repeat,n_profiles=len(byprofile),profile_mean_rmse=np.sqrt(np.mean(byprofile**2)),profile_mean_mae=abs(byprofile).mean()))
    pd.DataFrame(levelmetrics).to_csv(c.OUT/'tables/profile_mean_metrics_repeat.csv',index=False)
    pd.DataFrame(levelmetrics).groupby(['experiment','protocol']).mean(numeric_only=True).reset_index().to_csv(c.OUT/'tables/profile_mean_metrics_summary.csv',index=False)
    pp=pd.DataFrame(pairs);pp.to_parquet(c.OUT/'tables/same_model_pairs.parquet',index=False);pairmetrics=[]
    for scope,mask in [('all',np.ones(len(pp),bool)),('without_Chignahuapan',pp.without_Chignahuapan)]:
        for (exp,protocol,repeat),g in pp[mask].groupby(['experiment','protocol','repeat']):
            profile=g.groupby('profile').pair_error.agg(mse=lambda x:np.mean(x*x),mae=lambda x:abs(x).mean())
            pairmetrics.append(dict(experiment=exp,protocol=protocol,repeat=repeat,scope=scope,n_pairs=len(g),n_profiles=len(profile),n_parcels=len(set(g.id_a)|set(g.id_b)),pair_rmse=np.sqrt(np.mean(g.pair_error**2)),pair_mae=abs(g.pair_error).mean(),equal_profile_rmse=np.sqrt(profile.mse.mean()),equal_profile_mae=profile.mae.mean()))
    pm=pd.DataFrame(pairmetrics);pm.to_csv(c.OUT/'tables/pair_metrics_repeat.csv',index=False);ps=pm.groupby(['experiment','protocol','scope']).mean(numeric_only=True).reset_index();ps.to_csv(c.OUT/'tables/pair_metrics_summary.csv',index=False)
    pd.DataFrame(intervals).to_csv(c.OUT/'tables/interval_calibration_repeat.csv',index=False)
    pd.DataFrame(intervals).groupby(['experiment','protocol','stratum'])[['n','coverage','mean_width','min_width','max_width']].mean().reset_index().to_csv(c.OUT/'tables/interval_calibration_summary.csv',index=False)
    pd.DataFrame(support).to_csv(c.OUT/'tables/hierarchy_known_new_support.csv',index=False)
    p.to_parquet(c.OUT/'tables/errors_with_geography.parquet',index=False)
    paired=[]
    for candidate,baseline in [('C-T2','C-T0'),('C-T2','C-T1'),('C-T3','C-T0'),('C-T4','C-T2'),('C-H0M','C-H0'),('C-H1','C-H0M')]:
        z=m[m.experiment.eq(candidate)].merge(m[m.experiment.eq(baseline)],on=['protocol','repeat','stratum'],suffixes=('','_base'),validate='one_to_one')
        for row in z.to_dict('records'):paired.append(dict(candidate=candidate,baseline=baseline,protocol=row['protocol'],repeat=row['repeat'],stratum=row['stratum'],delta_rmse=row['RMSE']-row['RMSE_base'],delta_mae=row['MAE']-row['MAE_base']))
    paired=pd.DataFrame(paired);paired.to_csv(c.OUT/'tables/paired_repeat.csv',index=False);paired.groupby(['candidate','baseline','protocol','stratum'])[['delta_rmse','delta_mae']].mean().reset_index().to_csv(c.OUT/'tables/paired_summary.csv',index=False)
    co=pd.concat([pd.read_csv(c.OUT/'tables'/f'{label}_coefficients.csv') for label in ['transfer','hierarchy']],ignore_index=True)
    co.groupby(['experiment','protocol','feature']).agg(n_present=('coefficient','size'),mean_beta=('coefficient','mean'),sd_beta=('coefficient','std'),positive_fraction=('coefficient',lambda x:(x>1e-10).mean()),nonzero_fraction=('coefficient',lambda x:(abs(x)>1e-10).mean())).reset_index().to_csv(c.OUT/'tables/coefficient_stability.csv',index=False)
    plots(summary,ps)
    from .stage_c_final_report import write
    write(summary,ps)

def plots(metrics,pairs):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=c.OUT
    for label,prefix in [('C-T','transfer'),('C-H','hierarchy')]:
        for metric in ['RMSE','MAE']:
            z=metrics[(metrics.stratum=='all')&metrics.experiment.str.startswith(label)].pivot(index='experiment',columns='protocol',values=metric);ax=z.plot.barh(figsize=(11,5));ax.set_xlabel(metric+' t/ha, OOF completa por repetición');ax.set_title('138 parcelas TRAIN; 43 perfiles; 65 folds externos');ax.legend(title='Protocolo / comparaci?n',bbox_to_anchor=(1.02,1),loc='upper left');ax.figure.tight_layout();ax.figure.savefig(out/'figures'/f'{prefix}_{metric}.png',dpi=170);plt.close(ax.figure)
    z=pairs[pairs.scope=='all'].pivot(index='experiment',columns='protocol',values='equal_profile_rmse');ax=z.plot.barh(figsize=(12,7));ax.set_xlabel('RMSE diferencias (t/ha), igual peso por perfil');ax.set_title('138 parcelas TRAIN; 43 perfiles; 65 folds externos');ax.legend(title='Protocolo / comparaci?n',bbox_to_anchor=(1.02,1),loc='upper left');ax.figure.tight_layout();ax.figure.savefig(out/'figures/local_differences.png',dpi=170);plt.close(ax.figure)
    reg=pd.read_csv(out/'tables/hierarchy_registry.csv');fig,axes=plt.subplots(1,2,figsize=(12,5))
    z=reg[reg.experiment=='C-H1'];z.groupby(['protocol','ratio']).size().unstack(fill_value=0).plot.barh(stacked=True,ax=axes[0]);axes[0].set_xlabel('Ajustes externos por ratio seleccionado');axes[1].scatter(z.tau2,z.sigma2,s=25);axes[1].set(xlabel='tau² (t/ha)²',ylabel='sigma² (t/ha)²');fig.suptitle('C-H1: 65 ajustes externos; 138 parcelas TRAIN, 43 perfiles');fig.tight_layout();fig.savefig(out/'figures/hierarchy_variances.png',dpi=170);plt.close(fig)
    q=pd.read_csv(out/'tables/interval_calibration_summary.csv');z=q[(q.experiment=='C-H1')&q.stratum.isin(['known_profile','new_profile'])].pivot(index='protocol',columns='stratum',values='coverage');ax=z.plot.bar(figsize=(10,5),rot=0);ax.axhline(.9,color='black',ls='--',label='Nominal90%');ax.set_ylim(0,1);ax.set_ylabel('Cobertura OOF');ax.set_title('138 parcelas TRAIN; 43 perfiles; 65 folds externos');ax.legend(title='Protocolo / comparaci?n',bbox_to_anchor=(1.02,1),loc='upper left');ax.figure.tight_layout();ax.figure.savefig(out/'figures/interval_coverage.png',dpi=170);plt.close(ax.figure)
    losses=pd.read_csv(out/'tables/transfer_fold_sse_contributions.csv');z=losses[(losses.protocol=='spatial')&(losses.candidate=='C-T2')].pivot(index='fold',columns='baseline',values='sse_gain');ax=z.plot.bar(figsize=(10,5),rot=0);ax.axhline(0,color='black');ax.set_ylabel('Ganancia SSE (t/ha)²; positiva mejora');ax.set_title('138 parcelas TRAIN; 43 perfiles; 65 folds externos');ax.legend(title='Protocolo / comparaci?n',bbox_to_anchor=(1.02,1),loc='upper left');ax.figure.tight_layout();ax.figure.savefig(out/'figures/spatial_block_contributions.png',dpi=170);plt.close(ax.figure)
