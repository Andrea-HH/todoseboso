"""Read-only comprehensive J7_BOTH OOF residual audit; no predictive refits."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
import pandas as pd
import joblib
from scipy.stats import skew,kurtosis,spearmanr,probplot
from scipy.spatial.distance import cdist
from threadpoolctl import threadpool_limits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.geoc_bridge import OLD
from src.signal_role_allocation import predict_role
from src.geoc_signal_research import predict_base
from src.geoc_local04d_snapshot import haversine_distance_matrix
from src.family_4.conditional_response import ConditionalFeatures
from src.family_8.research import pair_metrics
from src.calendar_expansion import metric
from src.winner_delivery import cluster_weights,sampled_metrics
spec=importlib.util.spec_from_file_location('runner446',ROOT/'scripts/446_run_joint_simplification.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
SOURCE=runner.OUT;OUT=ROOT/'outputs/research/j7_both_residual_audit/v1';D=OUT/'tables';PROTOCOLS=['random','climate_profile','municipality','spatial'];LABELS=['Aleatoria','Perfil','Municipal','Espacial']


def calibration(y,p,weights=None):
    y=np.asarray(y,float);p=np.asarray(p,float);w=np.ones(len(y)) if weights is None else np.asarray(weights,float);w=w/w.sum();ym=w@y;pm=w@p;vp=w@((p-pm)**2);cov=w@((p-pm)*(y-ym));b=cov/vp if vp>1e-12 else np.nan
    return dict(calibration_intercept=float(ym-b*pm),calibration_slope=float(b),prediction_sd=float(np.sqrt(vp)),target_sd=float(np.sqrt(w@((y-ym)**2))),prediction_target_corr=float(np.corrcoef(y,p)[0,1]) if np.std(y)>1e-12 and np.std(p)>1e-12 else np.nan)


def stats(g):
    e=g.y_pred.to_numpy()-g.y_true.to_numpy();a=abs(e);m=metric(g.y_true,g.y_pred);return dict(n=len(g),**m,median_error=float(np.median(e)),median_absolute_error=float(np.median(a)),error_sd=float(np.std(e)),error_variance=float(np.var(e)),bias_squared=float(e.mean()**2),q025=float(np.quantile(e,.025)),q10=float(np.quantile(e,.1)),q90=float(np.quantile(e,.9)),q975=float(np.quantile(e,.975)),p90_absolute=float(np.quantile(a,.9)),p95_absolute=float(np.quantile(a,.95)),max_absolute=float(a.max()),over_fraction=float(np.mean(e>1e-12)),under_fraction=float(np.mean(e<-1e-12)),within_025=float(np.mean(a<=.25)),within_050=float(np.mean(a<=.5)),within_075=float(np.mean(a<=.75)),within_100=float(np.mean(a<=1)),skewness=float(skew(e,bias=False)) if np.std(e)>1e-12 and len(e)>2 else np.nan,excess_kurtosis=float(kurtosis(e,bias=False)) if np.std(e)>1e-12 and len(e)>3 else np.nan,**calibration(g.y_true,g.y_pred))


def corr(a,b):
    a=np.asarray(a,float);b=np.asarray(b,float);ix=np.isfinite(a)&np.isfinite(b)
    return float(spearmanr(a[ix],b[ix]).statistic) if ix.sum()>=5 and np.ptp(a[ix])>1e-12 and np.ptp(b[ix])>1e-12 else np.nan


def write_summary(name,rows,keys):
    f=pd.DataFrame(rows);f.to_csv(D/f'{name}_by_repeat.csv',index=False);f.drop(columns='repeat').groupby(keys).mean(numeric_only=True).reset_index().to_csv(D/f'{name}_summary.csv',index=False)


def main():
    if (OUT/'manifest.json').exists():raise FileExistsError('Preserve completed residual audit')
    for p in [OUT,D,OUT/'figures',OUT/'audit']:p.mkdir(parents=True,exist_ok=True)
    assert json.loads((SOURCE/'manifest.json').read_text())['status']=='complete';cfg=json.loads((SOURCE/'frozen_design.json').read_text());protected=dict(cfg['source_sha256'])
    for p in [SOURCE/'tables/predictions.parquet',SOURCE/'manifest.json',SOURCE/'delivery_audit.json']+sorted((SOURCE/'models').glob('*.joblib')):protected[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in protected.items());assets=runner.load_assets();t=assets['a']['train'];ids=t.ID_POLIGONO.tolist();ids_index={v:i for i,v in enumerate(ids)};frame=assets['role_frame'];allp=pd.read_parquet(SOURCE/'tables/predictions.parquet');reference_names=['J7_BOTH','CT3','BASE12_BOTH','PRIOR_BIGBOTH'];p=allp[allp.experiment=='J7_BOTH'].copy();p=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one');assert len(p)==1794 and not p.duplicated(['protocol','repeat','ID_POLIGONO']).any();p['error']=p.y_pred-p.y_true;p['absolute_error']=abs(p.error);p['squared_error']=p.error**2
    target=t.RENDIMIENTO_T_HA.to_numpy();target_edges=np.quantile(target,[0,.25,.5,.75,1]);bins=pd.qcut(pd.Series(target),4,duplicates='drop');target_bins=dict(zip(ids,bins.astype(str)));p['target_quartile']=p.ID_POLIGONO.map(target_bins);within={}
    for state,g in t.groupby('Estado'):
        if g.RENDIMIENTO_T_HA.nunique()<4:labels=g.RENDIMIENTO_T_HA.map(lambda v:f'level_{v:g}')
        else:labels=pd.qcut(g.RENDIMIENTO_T_HA,4,duplicates='drop').astype(str)
        within.update(dict(zip(g.ID_POLIGONO,labels)))
    p['within_state_target_bin']=p.ID_POLIGONO.map(within);overall=[];regional=[];ranges=[];concentration=[];intraprofile=[];decomposition=[];associations=[];statecenter=[];comparisons=[]
    for (pro,re),g in p.groupby(['protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique;key=dict(protocol=pro,repeat=re);overall.append(dict(**key,**stats(g)));intraprofile.append(dict(**key,**pair_metrics(g)));sse=float(g.squared_error.sum())
        for kind in ['Estado','Municipio','fold','climate_profile']:
            for zone,h in g.groupby(kind):regional.append(dict(**key,kind=kind,zone=str(zone),sse_share=float(h.squared_error.sum()/sse),sample_share=len(h)/138,**stats(h)))
        for kind in ['target_quartile','y_true']:
            for zone,h in g.groupby(kind):ranges.append(dict(**key,kind=kind,zone=str(zone),y_min=float(h.y_true.min()),y_max=float(h.y_true.max()),**stats(h)))
        for (state,zone),h in g.groupby(['Estado','within_state_target_bin']):ranges.append(dict(**key,kind='within_state_target',zone=state+' | '+str(zone),y_min=float(h.y_true.min()),y_max=float(h.y_true.max()),**stats(h)))
        for top in [1,5,10,20]:
            h=g.nlargest(top,'squared_error');rest=g.drop(h.index);concentration.append(dict(**key,top=top,sse_share=float(h.squared_error.sum()/sse),remaining_n=len(rest),remaining_rmse=metric(rest.y_true,rest.y_pred)['rmse']))
        for grouping in [['Estado'],['climate_profile'],['climate_profile','fold']]:
            means=g.groupby(grouping).error.transform('mean');between=float(np.mean(means**2));withinvar=float(np.mean((g.error-means)**2));assert abs(between+withinvar-float(g.squared_error.mean()))<1e-12;decomposition.append(dict(**key,grouping='+'.join(grouping),between_group_mse=between,within_group_mse=withinvar,between_fraction=between/g.squared_error.mean(),within_fraction=withinvar/g.squared_error.mean()))
        yc=g.y_true-g.groupby('Estado').y_true.transform('mean');pc=g.y_pred-g.groupby('Estado').y_pred.transform('mean');statecenter.append(dict(**key,within_state_centered_r2=float(1-np.sum((pc-yc)**2)/np.sum(yc**2)),within_state_centered_corr=float(np.corrcoef(yc,pc)[0,1])))
        associations.extend([dict(**key,predictor='prediction',signed_error_spearman=corr(g.y_pred,g.error),absolute_error_spearman=corr(g.y_pred,g.absolute_error)),dict(**key,predictor='observed_yield_coupled_to_error',signed_error_spearman=corr(g.y_true,g.error),absolute_error_spearman=corr(g.y_true,g.absolute_error))])
    for (name,pro,re),g in allp[allp.experiment.isin(reference_names)].groupby(['experiment','protocol','repeat']):comparisons.append(dict(experiment=name,protocol=pro,repeat=re,**metric(g.y_true,g.y_pred)))
    write_summary('residual',overall,['protocol']);write_summary('regional',regional,['protocol','kind','zone']);write_summary('target_ranges',ranges,['protocol','kind','zone']);write_summary('concentration',concentration,['protocol','top']);write_summary('intraprofile',intraprofile,['protocol']);write_summary('decomposition',decomposition,['protocol','grouping']);write_summary('within_state_centered',statecenter,['protocol']);write_summary('error_associations',associations,['protocol','predictor']);write_summary('reference_comparison',comparisons,['experiment','protocol'])
    # Parcel-level repeated errors remain errors of individual repeat models, not errors of their ensemble mean.
    parcel=p.groupby(['protocol','ID_POLIGONO','Estado','Municipio','climate_profile']).agg(y_true=('y_true','first'),mean_prediction=('y_pred','mean'),prediction_sd=('y_pred',lambda x:np.std(x)),mean_error=('error','mean'),mean_absolute_error=('absolute_error','mean'),mean_squared_error=('squared_error','mean'),max_absolute_error=('absolute_error','max'),over_fraction=('error',lambda x:np.mean(x>0))).reset_index();parcel['rms_error_across_repeats']=np.sqrt(parcel.mean_squared_error);parcel['sse_share']=parcel.mean_squared_error/parcel.groupby('protocol').mean_squared_error.transform('sum');parcel.to_csv(D/'parcel_errors.csv',index=False);pd.concat([g.nlargest(10,'mean_squared_error') for _,g in parcel.groupby('protocol')]).to_csv(D/'largest_errors.csv',index=False)
    # Conditional bootstrap of fixed OOF vectors, using the same cluster draw across all repeats.
    groupframe=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO').loc[ids];intervals=[]
    with threadpool_limits(limits=1):
        for pro,g in p.groupby('protocol'):
            pp=g.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy();weights,nclusters=cluster_weights(groupframe[pro if pro in ['municipality','spatial'] else 'climate_profile'],5000,2026);sampled=sampled_metrics(target,pp,weights);den=weights.sum(axis=1);ym=(weights@target)/den;pm=(weights@pp.T)/den[:,None];cov=(weights@(pp*target[None,:]).T)/den[:,None]-pm*ym[:,None];var=(weights@(pp**2).T)/den[:,None]-pm**2;slopes=np.divide(cov,var,out=np.full_like(cov,np.nan),where=var>1e-12);sampled['calibration_slope']=np.nanmean(slopes,axis=1);sampled['calibration_intercept']=np.nanmean(ym[:,None]-slopes*pm,axis=1)
            point=pd.DataFrame(overall).query('protocol==@pro').mean(numeric_only=True)
            for name,values in sampled.items():intervals.append(dict(protocol=pro,metric=name,point=float(point[name]),low95=float(np.nanquantile(values,.025)),high95=float(np.nanquantile(values,.975)),n_clusters=nclusters))
    pd.DataFrame(intervals).to_csv(D/'cluster_bootstrap_intervals.csv',index=False)
    # Support and component diagnostics use each frozen outer training set; no new predictive model is fit.
    latitude=frame.base_centroid_lat.to_numpy();longitude=frame.base_centroid_lon.to_numpy();geo=haversine_distance_matrix(latitude,longitude);component_rows=[];replay=[]
    with threadpool_limits(limits=1):
        for fi in range(65):
            pack=joblib.load(SOURCE/'models'/f'{fi:02d}.joblib');tr=pack['train_positions'];va=pack['validation_positions'];g=p[p['index']==fi].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO];model=pack['models']['J7_BOTH'];expert=pack['experts'][model['variant']];ct=pack['ct3'].predict(t.iloc[va]);local=predict_base(expert['local'],va,assets);ep=predict_role(expert,va,assets);q=model['space'].transform(frame.iloc[va]);zt=model['space'].transform(frame.iloc[tr]);w=model['gate'].weights(q);pred=model['gate'].predict(q,ct,ep);err=float(np.max(abs(pred-g.y_pred.to_numpy())));assert err<1e-12;replay.append(dict(index=fi,max_difference=err));rep=expert['local']['representation'];xt=rep.transform(assets['features197'].iloc[assets['a']['train_global'][tr]]);xq=rep.transform(assets['features197'].iloc[assets['a']['train_global'][va]]);cr=ConditionalFeatures(tuple(assets['core'].columns)).fit(frame.iloc[tr]);ctz=cr.transform(frame.iloc[tr]);cq=cr.transform(frame.iloc[va]);rawtr=frame.iloc[tr][list(assets['core'])].to_numpy(float);rawq=frame.iloc[va][list(assets['core'])].to_numpy(float);outside=((rawq<np.nanmin(rawtr,axis=0)-1e-12)|(rawq>np.nanmax(rawtr,axis=0)+1e-12)).sum(axis=1);localtr=frame.iloc[tr][rep.columns].to_numpy(float);localq=frame.iloc[va][rep.columns].to_numpy(float);localoutside=((localq<np.nanmin(localtr,axis=0)-1e-12)|(localq>np.nanmax(localtr,axis=0)+1e-12)).sum(axis=1)
            distances=dict(nearest_geo_km=geo[np.ix_(va,tr)].min(axis=1),nearest_core_distance=cdist(cq,ctz).min(axis=1),nearest_local_distance=cdist(xq,xt).min(axis=1),nearest_physical_distance=cdist(q,zt).min(axis=1))
            for j,i in enumerate(va):component_rows.append(dict(index=fi,protocol=g.protocol.iloc[0],repeat=int(g['repeat'].iloc[0]),fold=int(g.fold.iloc[0]),ID_POLIGONO=t.iloc[i].ID_POLIGONO,ct3_prediction=float(ct[j]),local_prediction=float(local[j]),compact_correction=float(ep[j]-local[j]),expert_prediction=float(ep[j]),expert_weight=float(w[j]),mixture_change_vs_ct3=float(pred[j]-ct[j]),outside_core_dimensions=int(outside[j]),outside_local_dimensions=int(localoutside[j]),same_profile_training_n=int((t.iloc[tr].climate_profile==t.iloc[i].climate_profile).sum()),**{k:float(v[j]) for k,v in distances.items()}))
            if fi%20==19:print(f'Frozen component replay {fi+1}/65',flush=True)
    components=pd.DataFrame(component_rows);p=p.merge(components,on=['index','protocol','repeat','fold','ID_POLIGONO'],validate='one_to_one');p.to_parquet(OUT/'oof_residuals_components.parquet',index=False);components.to_csv(D/'training_support_and_components.csv',index=False);pd.DataFrame(replay).to_csv(OUT/'audit/exact_replay.csv',index=False);support_rows=[];component_metrics=[];support_assoc=[]
    support_names=['nearest_geo_km','nearest_core_distance','nearest_local_distance','nearest_physical_distance','expert_weight','outside_core_dimensions','outside_local_dimensions']
    for (pro,re),g in p.groupby(['protocol','repeat']):
        for name in support_names:
            support_assoc.append(dict(protocol=pro,repeat=re,predictor=name,signed_error_spearman=corr(g[name],g.error),absolute_error_spearman=corr(g[name],g.absolute_error)))
            if g[name].nunique()>1:
                bins=pd.qcut(g[name],4,duplicates='drop')
                for label,h in g.groupby(bins,observed=True):support_rows.append(dict(protocol=pro,repeat=re,predictor=name,bin=str(label),**stats(h)))
        for name in ['ct3_prediction','local_prediction','expert_prediction','y_pred']:
            component_metrics.append(dict(protocol=pro,repeat=re,component=name,**metric(g.y_true,g[name])))
        for kind in ['Estado','fold']:
            for label,h in g.groupby(kind):support_assoc.extend(dict(protocol=pro,repeat=re,predictor=name,within_kind=kind,zone=str(label),n=len(h),signed_error_spearman=corr(h[name],h.error),absolute_error_spearman=corr(h[name],h.absolute_error)) for name in support_names)
    write_summary('component_metrics',component_metrics,['protocol','component']);pd.DataFrame(support_rows).to_csv(D/'support_bins_by_repeat.csv',index=False);pd.DataFrame(support_assoc).to_csv(D/'support_correlations.csv',index=False)
    # Input-error associations are descriptive and never used to select variables.
    input_features=list(assets['core'])+assets['variants']['DROP_JOINT']['columns']+['base_centroid_lat','base_centroid_lon'];input_rows=[]
    for (pro,re),g in p.groupby(['protocol','repeat']):
        ix=[ids_index[v] for v in g.ID_POLIGONO]
        for feature in input_features:
            x=frame.iloc[ix][feature].to_numpy(float);e=g.error.to_numpy();a=abs(e);input_rows.append(dict(protocol=pro,repeat=re,feature=feature,signed_error_spearman=corr(x,e),absolute_error_spearman=corr(x,a),within_state_signed_spearman=corr(x-pd.Series(x).groupby(g.Estado.to_numpy()).transform('mean').to_numpy(),e-g.groupby('Estado').error.transform('mean').to_numpy())))
    write_summary('input_error_associations',input_rows,['protocol','feature'])
    # Residual spatial structure: descriptive Moran I, no exchangeability-based significance claims.
    np.fill_diagonal(geo,np.inf);knn=np.argsort(geo,axis=1)[:,:6];W=np.zeros((138,138));W[np.arange(138)[:,None],knn]=1;W=np.maximum(W,W.T);W=W/W.sum(axis=1)[:,None];spatial_rows=[];state=t.Estado.to_numpy()
    for (pro,re),g in p.groupby(['protocol','repeat']):
        e=g.set_index('ID_POLIGONO').loc[ids].error.to_numpy()
        for centered in [False,True]:
            v=e.copy()
            if centered:
                for s in np.unique(state):v[state==s]-=v[state==s].mean()
            v=v-v.mean();I=float((138/W.sum())*(v@W@v)/(v@v)) if v@v>1e-12 else np.nan;spatial_rows.append(dict(protocol=pro,repeat=re,state_centered=centered,moran_I=I))
    write_summary('spatial_structure',spatial_rows,['protocol','state_centered'])
    # Improvements relative to compatible baselines and cross-model error correlations.
    gains=[];correlations=[]
    for name in ['CT3','BASE12_BOTH','PRIOR_BIGBOTH']:
        b=allp[allp.experiment==name][['protocol','repeat','fold','ID_POLIGONO','y_pred']];j=p.merge(b,on=['protocol','repeat','fold','ID_POLIGONO'],suffixes=('','_reference'),validate='one_to_one');j['reference']=name;j['sse_gain']=(j.y_pred_reference-j.y_true)**2-j.error**2;j['absolute_error_gain']=abs(j.y_pred_reference-j.y_true)-j.absolute_error;gains.append(j[['reference','protocol','repeat','ID_POLIGONO','Estado','Municipio','sse_gain','absolute_error_gain']])
        for (pro,re),h in j.groupby(['protocol','repeat']):correlations.append(dict(reference=name,protocol=pro,repeat=re,error_correlation=float(np.corrcoef(h.error,h.y_pred_reference-h.y_true)[0,1]),improved_parcel_fraction=float(np.mean(h.absolute_error_gain>0))))
    pd.concat(gains).groupby(['reference','protocol','ID_POLIGONO','Estado','Municipio'])[['sse_gain','absolute_error_gain']].mean().reset_index().to_csv(D/'parcel_gains_vs_references.csv',index=False);write_summary('error_complementarity',correlations,['reference','protocol'])
    # Figures: first chronological repetition per protocol, not selected by performance.
    colors={'Puebla':'tab:blue','Hidalgo':'tab:orange','Tlaxcala':'tab:green'};fig,axes=plt.subplots(2,4,figsize=(16,7));fig2,ax2=plt.subplots(2,4,figsize=(16,7))
    for col,(pro,label) in enumerate(zip(PROTOCOLS,LABELS)):
        g=p[(p.protocol==pro)&(p['repeat']==p.loc[p.protocol==pro,'repeat'].min())];assert len(g)==138;lo=min(g.y_true.min(),g.y_pred.min());hi=max(g.y_true.max(),g.y_pred.max());ax=axes[0,col]
        for state,h in g.groupby('Estado'):ax.scatter(h.y_pred,h.y_true,c=colors.get(state,'gray'),s=17,alpha=.65,label=state)
        ax.plot([lo,hi],[lo,hi],color='black',linestyle='--');cal=calibration(g.y_true,g.y_pred);xx=np.array([lo,hi]);ax.plot(xx,cal['calibration_intercept']+cal['calibration_slope']*xx,color='red');ax.set(title=label,xlabel='Predicho t/ha',ylabel='Observado t/ha');ax.legend(fontsize=6)
        axes[1,col].scatter(g.y_pred,g.error,c=g.Estado.map(colors),s=17,alpha=.65);axes[1,col].axhline(0,color='black',linestyle='--');axes[1,col].set(xlabel='Predicho t/ha',ylabel='Predicho − observado t/ha');ax2[0,col].hist(g.error,bins=16,color='steelblue',alpha=.8);ax2[0,col].axvline(0,color='black',linestyle='--');ax2[0,col].set(title=label,xlabel='Error t/ha');probplot(g.error,dist='norm',plot=ax2[1,col]);ax2[1,col].set(title='QQ descriptivo')
    fig.suptitle('J7_BOTH OOF: calibración y residuos; aleatoria repetición 0');fig.tight_layout();fig.savefig(OUT/'figures/calibration_and_residuals.png',dpi=160);plt.close(fig);fig2.suptitle('Distribución de residuos; aleatoria repetición 0');fig2.tight_layout();fig2.savefig(OUT/'figures/residual_distribution_QQ.png',dpi=160);plt.close(fig2)
    fig,axes=plt.subplots(1,4,figsize=(16,4));lim=max(abs(parcel.mean_error).max(),.5)
    for ax,pro,label in zip(axes,PROTOCOLS,LABELS):
        g=parcel[parcel.protocol==pro];ix=[ids_index[v] for v in g.ID_POLIGONO];im=ax.scatter(longitude[ix],latitude[ix],c=g.mean_error,cmap='RdBu_r',vmin=-lim,vmax=lim,s=27);ax.set(title=label,xlabel='Longitud',ylabel='Latitud')
    fig.colorbar(im,ax=list(axes),label='Error medio firmado t/ha',shrink=.8);fig.suptitle('Errores por parcela: aleatoria promedia errores de 10 repeticiones');fig.savefig(OUT/'figures/residual_map.png',dpi=160,bbox_inches='tight');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4));r=pd.read_csv(D/'residual_summary.csv').set_index('protocol').loc[PROTOCOLS];axes[0].bar(LABELS,r.bias_squared,label='Sesgo²');axes[0].bar(LABELS,r.error_variance,bottom=r.bias_squared,label='Varianza del error');axes[0].set(ylabel='MSE (t/ha)²');axes[0].legend();axes[1].plot(LABELS,r.within_050,marker='o',label='|error| ≤0.5');axes[1].plot(LABELS,r.within_100,marker='o',label='|error| ≤1');axes[1].set(ylabel='Fracción de parcelas',ylim=(0,1));axes[1].legend();fig.tight_layout();fig.savefig(OUT/'figures/bias_dispersion_and_thresholds.png',dpi=160);plt.close(fig)
    with pd.ExcelWriter(OUT/'evaluacion_residuos_J7_BOTH.xlsx',engine='openpyxl') as writer:
        for f,sheet in [('reference_comparison_summary.csv','RMSE_R2_referencias'),('residual_summary.csv','Distribucion_calibracion'),('cluster_bootstrap_intervals.csv','Intervalos_bootstrap'),('regional_summary.csv','Estados_municipios_bloques'),('target_ranges_summary.csv','Cuartiles_y_niveles'),('largest_errors.csv','Mayores_errores'),('parcel_errors.csv','Cada_parcela'),('concentration_summary.csv','Concentracion'),('decomposition_summary.csv','Entre_y_dentro_grupos'),('intraprofile_summary.csv','Intraperfil'),('within_state_centered_summary.csv','Centrado_estado_descriptivo'),('component_metrics_summary.csv','Partes_del_modelo'),('support_correlations.csv','Soporte'),('input_error_associations_summary.csv','Asociaciones_no_causales'),('spatial_structure_summary.csv','Moran_descriptivo'),('error_complementarity_summary.csv','Comparacion_errores'),('parcel_gains_vs_references.csv','Ganancias_por_parcela')]:pd.read_csv(D/f).to_excel(writer,sheet_name=sheet,index=False)
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in protected.items());(OUT/'manifest.json').write_text(json.dumps(dict(status='complete',model='J7_BOTH',oof_rows=1794,unique_parcels=138,protocols=PROTOCOLS,random_repeats=10,residual_sign='prediction minus observation',target_quartile_edges=target_edges.tolist(),replayed_outer_models=65,replay_max_difference=max(r['max_difference'] for r in replay),no_predictive_refit=True,no_new_PRED=True,no_champion_change=True,protected_source_sha256=protected,code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2),encoding='utf-8');print(r[['rmse','r2','bias','error_sd','within_050','within_100','calibration_intercept','calibration_slope']].round(6).to_string())


if __name__=='__main__':main()
