"""Immutable reporting reuse plus expanded paired/error-complementarity diagnostics."""
import json,itertools
import pandas as pd,numpy as np
from src.family_6.expansion import reporting as shared,diagnostics as old_diag,interpretation as old_interpret
from src.family_4.stage_d_evidence import metrics
from . import execution as e,diagnostics
metric_summary=shared.metric_summary
def save(z,name):
    path=e.OUT/'tables'/name
    if name.endswith('.parquet'):z.to_parquet(path,index=False)
    else:z.to_csv(path,index=False)
def paired(z,candidate,baseline):
    key=[e.ID,'protocol','repeat','fold']
    q=z[z.experiment.eq(candidate)].merge(z[z.experiment.eq(baseline)],on=key,suffixes=('','_base'),validate='one_to_one')
    assert np.array_equal(q.y_true,q.y_true_base)
    rows=[]
    for (p,r),g in q.groupby(['protocol','repeat']):
        a=metrics(g);b=metrics(g.rename(columns={'y_pred':'unused','y_pred_base':'y_pred'}))
        rows.append(dict(candidate=candidate,baseline=baseline,protocol=p,repeat=r,n=len(g),delta_RMSE=a['RMSE']-b['RMSE'],delta_MAE=a['MAE']-b['MAE'],delta_bias=a['bias']-b['bias'],SSE_gain=b['SSE']-a['SSE'],fraction_SE_improve=(((g.y_pred_base-g.y_true)**2)>((g.y_pred-g.y_true)**2)).mean()))
    return rows
def build(p):
    # Existing reporter's internal baseline alias is translated only in this
    # new version. Original code, artifacts and native reference keys stay intact.
    z=p.copy();z.experiment=z.experiment.replace({'F7-00':'F6-E0'})
    old=shared.e,shared.PAIRS,old_diag.build,old_interpret.write
    try:
        shared.e=e;old_diag.build=diagnostics.build;old_interpret.write=lambda _:None
        shared.build(z)
    finally:shared.e,shared.PAIRS,old_diag.build,old_interpret.write=old
    for path in (e.OUT/'tables').glob('*'):
        if path.suffix not in ['.csv','.parquet']:continue
        frame=pd.read_parquet(path) if path.suffix=='.parquet' else pd.read_csv(path)
        changed=False
        for c in ['experiment','candidate','baseline']:
            if c in frame and frame[c].eq('F6-E0').any():frame[c]=frame[c].replace({'F6-E0':'F7-00'});changed=True
        if changed:save(frame,path.name)
        if 'vs_F6-E0' in path.name:path.rename(path.with_name(path.name.replace('vs_F6-E0','vs_F7-00')))
    pairs=[(x,b) for x in e.SPECS for b in ['F7-00','C-T3','F5-01','F6-E1','F6-E2','CHAMPION']]+[('F7-E3','F7-E1'),('F7-E3','F7-E2')]
    rows=[r for x,b in pairs for r in paired(p,x,b)];q=pd.DataFrame(rows)
    save(q,'expansion_paired_repeat.csv');save(q.groupby(['candidate','baseline','protocol']).mean(numeric_only=True).reset_index(),'expansion_paired_summary.csv')
    complementarity(p);regional_omissions(p);extra_evidence(p)
    from .interpretation import write
    write(pd.read_csv(e.OUT/'tables/metrics_summary.csv'))
    plots()
def regional_omissions(p):
    _,t,_=e.load();q=p.merge(t[[e.ID,'Municipio','Estado']],on=e.ID,validate='many_to_one');rows=[]
    for name in e.SPECS:
        key=[e.ID,'protocol','repeat','fold'];z=q[q.experiment.eq(name)].merge(q[q.experiment.eq('F7-00')],on=key,suffixes=('','_base'),validate='one_to_one')
        for (pr,r),g in z.groupby(['protocol','repeat']):
            for field in ['Municipio','Estado']:
                for value in g[field].unique():
                    h=g[g[field].ne(value)]
                    if not len(h):continue
                    a=metrics(h);b=metrics(h.rename(columns={'y_pred':'unused','y_pred_base':'y_pred'}))
                    rows.append(dict(candidate=name,baseline='F7-00',protocol=pr,repeat=r,omitted_type=field,omitted_region=value,n=len(h),delta_RMSE=a['RMSE']-b['RMSE'],delta_MAE=a['MAE']-b['MAE'],SSE_gain=b['SSE']-a['SSE'],no_refit=True))
    z=pd.DataFrame(rows);save(z,'region_omission_repeat.csv');save(z.groupby(['candidate','baseline','protocol','omitted_type','omitted_region']).mean(numeric_only=True).reset_index(),'region_omission_summary.csv')
    ip=pd.read_csv(e.OUT/'tables/intraprofile_metrics_repeat.csv');ip['adequate_descriptive_support']=ip.n_profiles.ge(3)&ip.n_parcels.ge(10)
    save(ip,'intraprofile_metrics_with_support.csv')
    fm=pd.read_csv(e.OUT/'tables/paired_fold_contributions.csv');tm=pd.read_csv(e.OUT/'tables/territorial_metrics_repeat.csv');counts=[]
    for name in e.SPECS:
        for proto in ['municipality','spatial']:
            f=fm[(fm.candidate==name)&(fm.baseline=='F7-00')&(fm.protocol==proto)]
            a=tm[(tm.experiment==name)&(tm.protocol==proto)&tm.group_type.eq('Municipio')]
            b=tm[(tm.experiment=='F7-00')&(tm.protocol==proto)&tm.group_type.eq('Municipio')]
            z=a.merge(b,on=['protocol','repeat','group_type','group'],suffixes=('','_base'),validate='one_to_one')
            counts.append(dict(experiment=name,protocol=proto,n_folds=len(f),folds_RMSE_improve=int((f.delta_RMSE<0).sum()),folds_MAE_improve=int((f.delta_MAE<0).sum()),n_municipalities=len(z),municipalities_RMSE_improve=int((z.RMSE<z.RMSE_base).sum()),municipalities_MAE_improve=int((z.MAE<z.MAE_base).sum()),municipalities_ge10=int(z.n.ge(10).sum()),municipalities_ge10_RMSE_improve=int(((z.RMSE<z.RMSE_base)&z.n.ge(10)).sum())))
    save(pd.DataFrame(counts),'territorial_improvement_counts.csv')
def complementarity(p):
    names=['F7-00',*e.SPECS];key=[e.ID,'protocol','repeat','fold']
    wide=p[p.experiment.isin(names)].pivot(index=key,columns='experiment',values='y_pred').reset_index()
    truth=p[p.experiment.eq('F7-00')][key+['y_true']];wide=wide.merge(truth,on=key,validate='one_to_one')
    for n in names:wide['error_'+n]=wide[n]-wide.y_true
    save(wide,'compatible_errors_wide.parquet');rows=[];quartiles=[];patterns=[]
    for (proto,r),g in wide.groupby(['protocol','repeat']):
        for a,b in itertools.combinations(names,2):
            ea=g['error_'+a];eb=g['error_'+b]
            rows.append(dict(protocol=proto,repeat=r,model_a=a,model_b=b,n=len(g),error_correlation=ea.corr(eb),error_covariance_population=float(np.mean((ea-ea.mean())*(eb-eb.mean()))),bias_a=ea.mean(),bias_b=eb.mean(),mean_AE_a=abs(ea).mean(),mean_AE_b=abs(eb).mean(),same_error_direction=(ea*eb>0).mean()))
        base=g['error_F7-00'];bands=pd.qcut(abs(base).rank(method='first'),4,labels=False)
        for name in e.SPECS:
            err=g['error_'+name];gain=base**2-err**2
            for band in range(4):
                mask=bands.eq(band);quartiles.append(dict(experiment=name,protocol=proto,repeat=r,base_abs_error_quartile=band+1,n=int(mask.sum()),mean_base_AE=abs(base[mask]).mean(),mean_extension_AE=abs(err[mask]).mean(),mean_SE_gain=gain[mask].mean(),fraction_improve=(gain[mask]>0).mean(),same_error_direction=(base[mask]*err[mask]>0).mean(),postfit_descriptive=True))
        g1=base**2-g['error_F7-E1']**2
        g2=base**2-g['error_F7-E2']**2;g3=base**2-g['error_F7-E3']**2
        for label,mask in [('both_improve',(g1>0)&(g2>0)),('history_only',(g1>0)&(g2<=0)),('slope_only',(g1<=0)&(g2>0)),('neither',(g1<=0)&(g2<=0))]:
            patterns.append(dict(protocol=proto,repeat=r,pattern=label,n=int(mask.sum()),fraction=mask.mean(),mean_E3_SE_gain=g3[mask].mean(),E3_fraction_improve=(g3[mask]>0).mean()))
    for rows_,stem in [(rows,'error_covariance'),(quartiles,'gains_by_base_error_quartile'),(patterns,'complementary_gain_patterns')]:
        save(pd.DataFrame(rows_),stem+'_repeat.csv')
    losses=wide.copy()
    for name in e.SPECS:losses['SE_gain_'+name]=losses['error_F7-00']**2-losses['error_'+name]**2
    save(losses,'complementarity_parcel_cases.parquet')
def extra_evidence(p):
    _,t,_=e.load();q=p.merge(t[[e.ID,'Municipio','Estado']],on=e.ID,validate='many_to_one');key=[e.ID,'protocol','repeat','fold']
    rows=[];parcels=[]
    for candidate,baseline in [(x,'F7-00') for x in e.SPECS]+[('F7-E3','F7-E1'),('F7-E3','F7-E2')]:
        z=q[q.experiment.eq(candidate)].merge(q[q.experiment.eq(baseline)],on=key,suffixes=('','_base'),validate='one_to_one')
        z['candidate']=candidate;z['baseline']=baseline;z['SE_gain']=(z.y_pred_base-z.y_true)**2-(z.y_pred-z.y_true)**2
        parcels.append(z[key+['candidate','baseline','y_true','y_pred','y_pred_base','SE_gain','Municipio']])
        for (pr,r,municipality),g in z.groupby(['protocol','repeat','Municipio']):
            a=(g.y_pred-g.y_true).to_numpy();b=(g.y_pred_base-g.y_true).to_numpy()
            rows.append(dict(candidate=candidate,baseline=baseline,protocol=pr,repeat=r,Municipio=municipality,n=len(g),SSE_gain=float(np.sum(b*b-a*a)),bias_squared_gain=float(len(g)*(b.mean()**2-a.mean()**2)),error_variance_gain=float(len(g)*(b.var()-a.var())),bias_candidate=a.mean(),bias_base=b.mean()))
    save(pd.DataFrame(rows),'municipal_bias_dispersion_decomposition.csv');save(pd.concat(parcels,ignore_index=True),'ablation_parcel_cases.parquet')
    old=pd.read_parquet(e.initial.expansion.OUT/'tables/oof_predictions.parquet');patterns=[];caseframes=[]
    for name,previous in [('F7-E1','F6-E1'),('F7-E2','F6-E2')]:
        a=old[old.experiment.eq(previous)][key+['y_true','y_pred']].merge(old[old.experiment.eq('F6-E0')][key+['y_pred']],on=key,suffixes=('','_base'),validate='one_to_one')
        a['F6_gain']=(a.y_pred_base-a.y_true)**2-(a.y_pred-a.y_true)**2
        b=p[p.experiment.eq(name)][key+['y_true','y_pred']].merge(p[p.experiment.eq('F7-00')][key+['y_pred']],on=key,suffixes=('','_base'),validate='one_to_one')
        b['F7_gain']=(b.y_pred_base-b.y_true)**2-(b.y_pred-b.y_true)**2
        z=a[key+['F6_gain']].merge(b[key+['F7_gain']],on=key,validate='one_to_one');z['experiment']=name;caseframes.append(z)
        for (pr,r),g in z.groupby(['protocol','repeat']):
            shared_harm=(g.F6_gain<0)&(g.F7_gain<0)
            patterns.append(dict(experiment=name,protocol=pr,repeat=r,n=len(g),F6_harm_fraction=(g.F6_gain<0).mean(),F7_harm_fraction=(g.F7_gain<0).mean(),shared_harm_fraction=shared_harm.mean(),F6_harm_corrected_by_F7=int(((g.F6_gain<0)&(g.F7_gain>0)).sum()),gain_correlation=g.F6_gain.corr(g.F7_gain),warning='incremental changes versus each family core; architectures and selected regularization differ'))
    save(pd.DataFrame(patterns),'F6_vs_F7_incremental_harm_repeat.csv');save(pd.concat(caseframes,ignore_index=True),'F6_vs_F7_incremental_parcel_cases.parquet')
def plots():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    z=pd.read_csv(e.OUT/'tables/metrics_summary.csv')
    for metric in ['RMSE','MAE']:
        fig,ax=plt.subplots(figsize=(10,6));z.pivot(index='experiment',columns='protocol',values=metric).plot.barh(ax=ax)
        ax.legend(loc='upper left',bbox_to_anchor=(1,1));ax.set(xlabel=f'{metric} OOF completa (t/ha)',ylabel='Modelo');fig.tight_layout();fig.savefig(e.OUT/'figures'/f'global_{metric}.png',dpi=150);plt.close(fig)
    z=pd.read_csv(e.OUT/'tables/effects_by_outer_fit.csv')
    for c in e.HISTORY+[e.SLOPE]:
        fig,ax=plt.subplots(figsize=(8,4))
        for name,g in z[z.feature.eq(c)&z.supported].groupby('experiment'):ax.scatter(g.midpoint,g.local_difference,alpha=.3,s=10,label=name)
        ax.axhline(0,color='black',lw=.5);ax.set(xlabel=c,ylabel='Diferencia local respaldada (t/ha)')
        if len(ax.collections):ax.legend()
        else:ax.text(.5,.5,'Sin soporte suficiente',transform=ax.transAxes,ha='center')
        fig.tight_layout();fig.savefig(e.OUT/'figures'/f'local_effect_{c}.png',dpi=150);plt.close(fig)
    z=pd.read_csv(e.OUT/'tables/intraprofile_metrics_summary.csv');z=z[z.scope.eq('all')]
    fig,ax=plt.subplots(figsize=(10,6));z.pivot(index='experiment',columns='protocol',values='equal_profile_RMSE').plot.barh(ax=ax)
    ax.legend(loc='upper left',bbox_to_anchor=(1,1));ax.set(xlabel='RMSE diferencias intraperfil; igual peso por perfil (t/ha)',ylabel='Modelo');fig.tight_layout();fig.savefig(e.OUT/'figures/intraprofile_RMSE.png',dpi=150);plt.close(fig)
    errors=pd.read_parquet(e.OUT/'tables/errors_with_geography.parquet')
    for protocol in ['municipality','spatial']:
        q=errors[errors.experiment.isin(['F7-00',*e.SPECS])&errors.protocol.eq(protocol)]
        fig,ax=plt.subplots(figsize=(12,5));q.boxplot(column='error',by=['experiment','fold'],ax=ax,rot=90)
        ax.axhline(0,color='black',lw=.5);ax.set(title=f'Errores por fold — {protocol}',ylabel='Predicción − observado (t/ha)',xlabel='Modelo / fold');fig.suptitle('');fig.tight_layout();fig.savefig(e.OUT/'figures'/f'regional_error_distribution_{protocol}.png',dpi=150);plt.close(fig)
    inter=pd.read_csv(e.OUT/'tables/interactions_by_outer_fit.csv')
    pairs=list(dict.fromkeys(pair for values in e.INTERACTIONS.values() for pair in values))
    for first,second in pairs:
        names=[name for name,values in e.INTERACTIONS.items() if (first,second) in values]
        fig,axs=plt.subplots(1,len(names),figsize=(4*len(names),4),squeeze=False)
        for ax,name in zip(axs[0],names):
            q=inter[(inter.experiment==name)&inter['first'].eq(first)&inter['second'].eq(second)&inter.supported]
            if len(q):
                z=q.groupby(['bin_first','bin_second']).mixed_local_difference.mean().unstack().reindex(index=range(3),columns=range(3));arr=z.to_numpy();limit=max(float(abs(arr[np.isfinite(arr)]).max()),1e-6)
                im=ax.imshow(np.ma.masked_invalid(arr),origin='lower',cmap='RdBu_r',vmin=-limit,vmax=limit);fig.colorbar(im,ax=ax,label='Diferencia mixta respaldada (t/ha)')
            else:ax.text(.5,.5,'Sin soporte suficiente',transform=ax.transAxes,ha='center')
            ax.set(title=name,xlabel='Tercil '+second,ylabel='Tercil '+first)
        fig.tight_layout();fig.savefig(e.OUT/'figures'/f'interaction_{first}_{second}.png',dpi=150);plt.close(fig)
