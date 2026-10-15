"""Separate complete-repeat and same-external-model evaluation of Stage B and fixed blend."""
import json
import numpy as np
import pandas as pd
from . import stage_b_learning as b

def evaluate(predictions,prefix):
    out=b.OUT/'tables';_,t=b.load();q=pd.read_csv(b.ROOT/'outputs/research/family_1/soil_yield_quartile_analysis/v1/parcel_quartiles.csv')[[b.ID,'quartile']]
    p=predictions.merge(t[[b.ID,'climate_profile','Municipio','Estado']],on=b.ID,validate='many_to_one').merge(q,on=b.ID,validate='many_to_one')
    rows=[];pairs=[];disp=[]
    for (exp,protocol,repeat),g in p.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g[b.ID].is_unique
        scopes={'all':np.ones(len(g),bool),'Chignahuapan':g.Municipio.eq('Chignahuapan'),'without_Chignahuapan':g.Municipio.ne('Chignahuapan'),'Chignahuapan_profile4':g.Municipio.eq('Chignahuapan')&g.climate_profile.eq(4),'Chignahuapan_profile24':g.Municipio.eq('Chignahuapan')&g.climate_profile.eq(24),'other_Chignahuapan_profiles':g.Municipio.eq('Chignahuapan')&~g.climate_profile.isin([4,24])}
        scopes.update({label:g.quartile.eq(label) for label in ['Q1','Q2','Q3','Q4']})
        scopes.update({'municipality:'+str(v):g.Municipio.eq(v) for v in g.Municipio.unique()})
        scopes.update({'state:'+str(v):g.Estado.eq(v) for v in g.Estado.unique()})
        for scope,mask in scopes.items():
            z=g[mask]
            if len(z):rows.append(dict(experiment=exp,protocol=protocol,repeat=repeat,stratum=scope,n=len(z),sse=np.sum((z.y_true-z.y_pred)**2),**b.e.f.lm.k.metrics(z.y_true,z.y_pred)))
        for (profile,fold),z in g.groupby(['climate_profile','fold']):
            if len(z)<2:continue
            z=z.sort_values(b.ID);a,c=np.triu_indices(len(z),1);obs=z.y_true.to_numpy()[a]-z.y_true.to_numpy()[c];pred=z.y_pred.to_numpy()[a]-z.y_pred.to_numpy()[c]
            for i,j,dy,dp in zip(a,c,obs,pred):
                ch_a=z.Municipio.iloc[i]=='Chignahuapan';ch_b=z.Municipio.iloc[j]=='Chignahuapan'
                pairs.append(dict(experiment=exp,protocol=protocol,repeat=repeat,fold=fold,profile=profile,id_a=z[b.ID].iloc[i],id_b=z[b.ID].iloc[j],observed_difference=dy,predicted_difference=dp,pair_error=dy-dp,location='both_Chignahuapan' if ch_a and ch_b else 'both_outside' if not ch_a and not ch_b else 'mixed'))
            disp.append(dict(experiment=exp,protocol=protocol,repeat=repeat,fold=fold,profile=profile,n=len(z),observed_sd=z.y_true.std(),prediction_sd=z.y_pred.std()))
    m=pd.DataFrame(rows);m.to_csv(out/f'{prefix}_metrics_repeat.csv',index=False)
    summary=m.groupby(['experiment','protocol','stratum'])[['n','sse','RMSE','MAE','R2','bias_pred_minus_y']].mean().reset_index();summary.to_csv(out/f'{prefix}_metrics_summary.csv',index=False)
    pd.DataFrame(disp).to_csv(out/f'{prefix}_profile_dispersion.csv',index=False)
    pp=pd.DataFrame(pairs);pp.to_parquet(out/f'{prefix}_same_model_pairs.parquet',index=False)
    pairmetrics=[];profiles=[]
    for scope,mask in [('all',np.ones(len(pp),bool)),('without_Chignahuapan',pp.location.eq('both_outside')),('both_Chignahuapan',pp.location.eq('both_Chignahuapan'))]:
        for (exp,protocol,repeat),g in pp[mask].groupby(['experiment','protocol','repeat']):
            prof=g.groupby('profile').pair_error.agg(mse=lambda x:np.mean(x*x),mae=lambda x:abs(x).mean(),n_pairs='size')
            pairmetrics.append(dict(experiment=exp,protocol=protocol,repeat=repeat,scope=scope,n_pairs=len(g),n_profiles=len(prof),n_parcels=len(set(g.id_a)|set(g.id_b)),eligible_fraction=len(set(g.id_a)|set(g.id_b))/138,pair_rmse=np.sqrt(np.mean(g.pair_error**2)),pair_mae=abs(g.pair_error).mean(),equal_profile_rmse=np.sqrt(prof.mse.mean()),equal_profile_mae=prof.mae.mean(),hard_pair_fraction=(abs(g.pair_error)>1).mean()))
            for profile,row in prof.iterrows():profiles.append(dict(experiment=exp,protocol=protocol,repeat=repeat,scope=scope,profile=profile,**row.to_dict()))
    pm=pd.DataFrame(pairmetrics);pm.to_csv(out/f'{prefix}_pair_repeat.csv',index=False)
    pms=pm.groupby(['experiment','protocol','scope']).mean(numeric_only=True).reset_index();pms.to_csv(out/f'{prefix}_pair_summary.csv',index=False)
    pd.DataFrame(profiles).to_csv(out/f'{prefix}_profiles.csv',index=False)
    p.to_parquet(out/f'{prefix}_errors_with_geography.parquet',index=False)
    return summary,pms

def fixed_blend():
    champion=pd.read_parquet(b.ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization/predictions/oof_predictions.parquet');champion=champion[champion.architecture.eq('A_CURRENT_CH_H_T')]
    control=pd.read_parquet(b.OUT/'tables/control_oof.parquet');control=control[(control.experiment=='B0')&(control.protocol=='random')]
    keys=[b.ID,'repeat','fold'];assert not champion.duplicated(keys).any() and not control.duplicated(keys).any()
    z=champion.merge(control,on=keys,validate='one_to_one',suffixes=('_champion','_s1'))
    assert len(z)==1380 and np.allclose(z.y_true_champion,z.y_true_s1,atol=0,rtol=0)
    predictions=[];decomp=[];parcel=[]
    for exp,col in [('CHAMPION','y_pred_champion'),('F4_S1','y_pred_s1'),('FIXED_50_50','mix')]:
        z['mix']=(z.y_pred_champion+z.y_pred_s1)/2
        predictions.append(z[keys].assign(experiment=exp,protocol='random',y_true=z.y_true_champion,y_pred=z[col]))
    for repeat,g in z.groupby('repeat'):
        ea=g.y_true_champion-g.y_pred_champion;eb=g.y_true_champion-g.y_pred_s1;em=(ea+eb)/2
        component=.25*np.mean(ea*ea)+.25*np.mean(eb*eb)+.5*np.mean(ea*eb)
        assert np.isclose(np.mean(em*em),component,atol=1e-12)
        decomp.append(dict(repeat=repeat,mse_champion=np.mean(ea*ea),mse_s1=np.mean(eb*eb),mean_error_product=np.mean(ea*eb),error_covariance=np.mean((ea-ea.mean())*(eb-eb.mean())),error_correlation=ea.corr(eb),mse_mix=np.mean(em*em),decomposition_sum=component,bias_champion=ea.mean(),bias_s1=eb.mean(),bias_mix=em.mean(),bias_squared_gain_vs_champion=ea.mean()**2-em.mean()**2,variance_gain_vs_champion=np.var(ea)-np.var(em)))
        for pid,y,pa,pb in zip(g[b.ID],g.y_true_champion,g.y_pred_champion,g.y_pred_s1):parcel.append(dict(ID_POLIGONO=pid,repeat=repeat,y_true=y,error_champion=y-pa,error_s1=y-pb,error_mix=y-(pa+pb)/2,squared_error_gain=(y-pa)**2-(y-(pa+pb)/2)**2,absolute_error_gain=abs(y-pa)-abs(y-(pa+pb)/2)))
    pd.DataFrame(decomp).to_csv(b.OUT/'tables/fixed_blend_mse_decomposition.csv',index=False)
    per=pd.DataFrame(parcel);per.to_csv(b.OUT/'tables/fixed_blend_parcel_repeat.csv',index=False)
    per.groupby(b.ID).agg(mean_squared_gain=('squared_error_gain','mean'),mean_absolute_gain=('absolute_error_gain','mean'),n_repeats_improved=('absolute_error_gain',lambda x:(x>0).sum()),mean_square_champion=('error_champion',lambda x:np.mean(x*x)),mean_square_mix=('error_mix',lambda x:np.mean(x*x))).reset_index().to_csv(b.OUT/'tables/fixed_blend_parcel_summary.csv',index=False)
    mix=pd.concat(predictions,ignore_index=True);mix.to_parquet(b.OUT/'tables/fixed_blend_oof.parquet',index=False)
    return evaluate(mix,'blend')

def build():
    p=pd.read_parquet(b.OUT/'tables/oof_predictions.parquet')
    global_summary,pair_summary=evaluate(p,'objective')
    paired=[]
    for candidate,control in [('B1','B0'),('B3','B2')]:
        g=pd.read_csv(b.OUT/'tables/objective_metrics_repeat.csv')
        z=g[g.experiment.eq(candidate)].merge(g[g.experiment.eq(control)],on=['protocol','repeat','stratum'],suffixes=('','_control'),validate='one_to_one')
        for row in z.to_dict('records'):paired.append(dict(candidate=candidate,control=control,protocol=row['protocol'],repeat=row['repeat'],stratum=row['stratum'],delta_rmse=row['RMSE']-row['RMSE_control'],delta_mae=row['MAE']-row['MAE_control']))
    pd.DataFrame(paired).to_csv(b.OUT/'tables/paired_parcel_repeat.csv',index=False)
    pd.DataFrame(paired).groupby(['candidate','control','protocol','stratum']).agg(delta_rmse=('delta_rmse','mean'),delta_mae=('delta_mae','mean'),fraction_improving=('delta_rmse',lambda x:(x<0).mean())).reset_index().to_csv(b.OUT/'tables/paired_parcel_summary.csv',index=False)
    pr=pd.read_csv(b.OUT/'tables/objective_pair_repeat.csv');paircompare=[]
    for candidate,control in [('B1','B0'),('B3','B2')]:
        z=pr[pr.experiment.eq(candidate)].merge(pr[pr.experiment.eq(control)],on=['protocol','repeat','scope'],suffixes=('','_control'),validate='one_to_one')
        for row in z.to_dict('records'):paircompare.append(dict(candidate=candidate,control=control,protocol=row['protocol'],repeat=row['repeat'],scope=row['scope'],delta_equal_profile_rmse=row['equal_profile_rmse']-row['equal_profile_rmse_control'],delta_equal_profile_mae=row['equal_profile_mae']-row['equal_profile_mae_control'],delta_pair_rmse=row['pair_rmse']-row['pair_rmse_control']))
    pc=pd.DataFrame(paircompare);pc.to_csv(b.OUT/'tables/paired_local_repeat.csv',index=False);pc.groupby(['candidate','control','protocol','scope']).mean(numeric_only=True).reset_index().to_csv(b.OUT/'tables/paired_local_summary.csv',index=False)
    profile=pd.read_csv(b.OUT/'tables/objective_profiles.csv');rows=[]
    for candidate,control in [('B1','B0'),('B3','B2')]:
        z=profile[profile.experiment.eq(candidate)].merge(profile[profile.experiment.eq(control)],on=['protocol','repeat','scope','profile'],suffixes=('','_control'),validate='one_to_one')
        z['delta_rmse']=np.sqrt(z.mse)-np.sqrt(z.mse_control);z['candidate']=candidate;z['control']=control;rows.append(z)
    pd.concat(rows,ignore_index=True).to_csv(b.OUT/'tables/paired_profile_gains.csv',index=False)
    reg=pd.read_csv(b.OUT/'tables/registry.csv');reg.groupby(['experiment','protocol','lam']).size().rename('n_fits').to_csv(b.OUT/'tables/lambda_selection_counts.csv')
    co=pd.read_csv(b.OUT/'tables/coefficients.csv');co.groupby(['experiment','protocol','feature']).agg(n_fits=('coefficient','size'),mean_coef=('coefficient','mean'),sd_coef=('coefficient','std'),nonzero_fraction=('coefficient',lambda x:(abs(x)>1e-10).mean()),positive_fraction=('coefficient',lambda x:(x>1e-10).mean())).reset_index().to_csv(b.OUT/'tables/coefficient_stability.csv',index=False)
    blend_global,blend_local=fixed_blend()
    plots(global_summary,pair_summary,blend_global)
    from . import stage_b_final_report
    stage_b_final_report.write(global_summary,pair_summary,blend_global,blend_local)

def plots(global_summary,pair_summary,blend):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=b.OUT
    for i,metric in enumerate(['RMSE','MAE'],1):
        z=global_summary[global_summary.stratum.eq('all')].pivot(index='experiment',columns='protocol',values=metric);ax=z.plot.barh(figsize=(10,5));ax.set_xlabel(metric+' t/ha');ax.figure.tight_layout();ax.figure.savefig(out/'figures'/f'0{i}_{metric}_global.png',dpi=170);plt.close(ax.figure)
    z=pair_summary[pair_summary.scope.eq('all')].pivot(index='experiment',columns='protocol',values='equal_profile_rmse');ax=z.plot.barh(figsize=(10,5));ax.set_xlabel('RMSE diferencias, igual peso por perfil');ax.figure.tight_layout();ax.figure.savefig(out/'figures/03_local_RMSE.png',dpi=170);plt.close(ax.figure)
    inner=pd.read_csv(out/'tables/inner.csv');fig,axes=plt.subplots(1,2,figsize=(12,5))
    for ax,exp in zip(axes,['B1','B3']):
        z=inner[(inner.experiment==exp)&(inner.protocol=='random')&(inner['repeat']==1)&(inner.fold==1)]
        sc=ax.scatter(z.rmse,z.local_rmse,c=z.lam,cmap='viridis',s=35);ax.set(title=exp+' candidatos internos, primer fold',xlabel='RMSE parcela',ylabel='RMSE diferencias equilibrado');fig.colorbar(sc,ax=ax,label='lambda')
    fig.tight_layout();fig.savefig(out/'figures/04_internal_tradeoff.png',dpi=170);plt.close(fig)
    reg=pd.read_csv(out/'tables/registry.csv');z=reg.groupby(['experiment','protocol','lam']).size().unstack(fill_value=0);ax=z.plot.barh(stacked=True,figsize=(11,6));ax.set_xlabel('Ajustes externos');ax.figure.tight_layout();ax.figure.savefig(out/'figures/05_lambda_selection.png',dpi=170);plt.close(ax.figure)
    prof=pd.read_csv(out/'tables/paired_profile_gains.csv');z=prof[(prof.protocol=='random')&(prof.scope=='all')].groupby(['profile','candidate']).delta_rmse.mean().unstack();ax=z.plot.barh(figsize=(11,7));ax.axvline(0,color='black',lw=1);ax.set_xlabel('Cambio RMSE diferencias vs control');ax.figure.tight_layout();ax.figure.savefig(out/'figures/06_profile_gains.png',dpi=170);plt.close(ax.figure)
    pp=pd.read_parquet(out/'tables/objective_same_model_pairs.parquet');fig,axes=plt.subplots(2,2,figsize=(11,9))
    for ax,exp in zip(axes.ravel(),['B0','B1','B2','B3']):
        z=pp[(pp.experiment==exp)&(pp.protocol=='random')&(pp['repeat']==1)];ax.scatter(z.observed_difference,z.predicted_difference,s=14,alpha=.4);ax.plot([-2,2],[-2,2],color='black',lw=1);ax.set(title=exp,xlabel='Diferencia observada',ylabel='Diferencia predicha')
    fig.tight_layout();fig.savefig(out/'figures/07_difference_predictions.png',dpi=170);plt.close(fig)
    z=global_summary[(global_summary.protocol=='random')&global_summary.stratum.isin(['Chignahuapan','without_Chignahuapan'])].pivot(index='experiment',columns='stratum',values='RMSE');ax=z.plot.bar(figsize=(9,5),rot=0);ax.set_ylabel('RMSE parcela t/ha');ax.figure.tight_layout();ax.figure.savefig(out/'figures/08_Chignahuapan.png',dpi=170);plt.close(ax.figure)
    ax=reg.plot.scatter(x='n_iter',y='max_kkt_violation',figsize=(9,5));ax.set_ylabel('Máximo residuo KKT de J');ax.figure.tight_layout();ax.figure.savefig(out/'figures/09_convergence.png',dpi=170);plt.close(ax.figure)
    z=blend[blend.stratum.eq('all')].set_index('experiment')[['RMSE','MAE']];ax=z.plot.bar(figsize=(9,5),rot=0);ax.set_ylabel('t/ha');ax.figure.tight_layout();ax.figure.savefig(out/'figures/10_fixed_blend.png',dpi=170);plt.close(ax.figure)
    z=pd.read_csv(out/'tables/fixed_blend_parcel_summary.csv').sort_values('mean_squared_gain',ascending=False);fig,axes=plt.subplots(1,2,figsize=(12,5));axes[0].plot(np.arange(len(z)),z.mean_squared_gain.to_numpy());axes[0].axhline(0,color='black',lw=1);axes[0].set(xlabel='Parcelas ordenadas por ganancia',ylabel='Ganancia MSE vs Champion')
    ordered=z.sort_values('mean_square_champion',ascending=False);axes[1].plot(np.arange(len(z))+1,ordered.mean_square_champion.cumsum()/ordered.mean_square_champion.sum(),label='Champion');axes[1].plot(np.arange(len(z))+1,ordered.mean_square_mix.cumsum()/ordered.mean_square_mix.sum(),label='Mezcla');axes[1].set(xlabel='Parcelas ordenadas por error Champion',ylabel='Fracción acumulada SSE');axes[1].legend();fig.tight_layout();fig.savefig(out/'figures/11_blend_influence.png',dpi=170);plt.close(fig)
