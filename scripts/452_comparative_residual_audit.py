"""Compatible OOF comparison of Local04D, CT3, J7_BOTH and reduced expert mixtures."""
from pathlib import Path
import sys,json,hashlib,importlib.util,itertools
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.geoc_bridge import OLD
from src.signal_role_allocation import predict_role
from src.family_8.research import pair_metrics
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm
spec=importlib.util.spec_from_file_location('audit449',ROOT/'scripts/449_j7_both_residual_audit.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
spec2=importlib.util.spec_from_file_location('runner446',ROOT/'scripts/446_run_joint_simplification.py');runner=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(runner)
OUT=ROOT/'outputs/research/case_outliers_and_model_residual_comparison/v1';D=OUT/'tables';PROTOCOLS=audit.PROTOCOLS;MAIN=['LOCAL04D','CT3','J7_BOTH','MIX_EXPERT10','MIX_EXPERT9']


def write(name,rows,keys):
    f=pd.DataFrame(rows);f.to_csv(D/f'{name}_by_repeat.csv',index=False);f.drop(columns='repeat').groupby(keys).mean(numeric_only=True).reset_index().to_csv(D/f'{name}_summary.csv',index=False)


def main():
    if (OUT/'residual_comparison_manifest.json').exists():raise FileExistsError('Preserve comparison')
    for p in [OUT,D,OUT/'audit',OUT/'figures']:p.mkdir(parents=True,exist_ok=True)
    assets=runner.load_assets();t=assets['a']['train'];ids=t.ID_POLIGONO.tolist();y=t.RENDIMIENTO_T_HA.to_numpy();keys=['protocol','repeat','fold','ID_POLIGONO'];cols=keys+['y_true','y_pred'];source=runner.OUT/'tables/predictions.parquet';a=pd.read_parquet(source);bridge=ROOT/'outputs/modeling/geoc_bridge/v1/tables/oof_predictions.parquet';b=pd.read_parquet(bridge);b=b[b.protocol.isin(PROTOCOLS)];j=a[a.experiment=='CT3'].merge(b[b.experiment=='CT3'],on=keys,suffixes=('','_ref'),validate='one_to_one');assert len(j)==1794 and np.max(abs(j.y_pred-j.y_pred_ref))<1e-12
    frames=[b[b.experiment=='LOCAL04D'][cols].assign(experiment='LOCAL04D')]
    for name,original in [('CT3','CT3'),('J7_BOTH','J7_BOTH'),('MIX_EXPERT10','DROP_HISTORY_WATER'),('MIX_EXPERT9','DROP_SOIL'),('BIG_BOTH','PRIOR_BIGBOTH')]:frames.append(a[a.experiment==original][cols].assign(experiment=name))
    extra=[];replay=[]
    with threadpool_limits(limits=1):
        for fi in range(65):
            pack=joblib.load(runner.OUT/'models'/f'{fi:02d}.joblib');va=pack['validation_positions'];expected=a[(a['index']==fi)&(a.experiment=='J7_BOTH')].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO];tr=pack['train_positions'];assert not set(tr)&set(va)
            for name,v in [('EXPERT7','DROP_JOINT'),('EXPERT10','DROP_HISTORY_WATER'),('EXPERT9','DROP_SOIL')]:
                prediction=predict_role(pack['experts'][v],va,assets);extra.extend(dict(protocol=expected.protocol.iloc[0],repeat=int(expected['repeat'].iloc[0]),fold=int(expected.fold.iloc[0]),ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(pred),experiment=name) for i,pred in zip(va,prediction))
            model=pack['models']['J7_BOTH'];p=model['gate'].predict(model['space'].transform(assets['role_frame'].iloc[va]),pack['ct3'].predict(t.iloc[va]),predict_role(pack['experts']['DROP_JOINT'],va,assets));diff=float(np.max(abs(p-expected.y_pred.to_numpy())));assert diff<1e-12;replay.append(dict(index=fi,max_difference=diff))
    frames.append(pd.DataFrame(extra));p=pd.concat(frames,ignore_index=True);assert len(p)==9*1794 and not p.duplicated(['experiment']+keys).any();p=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one');p['error']=p.y_pred-p.y_true;p['absolute_error']=abs(p.error);p['squared_error']=p.error**2;p.to_parquet(OUT/'comparison_oof_residuals.parquet',index=False);targetbins=dict(zip(ids,pd.qcut(pd.Series(y),4,duplicates='drop').astype(str)));p['target_quartile']=p.ID_POLIGONO.map(targetbins);overall=[];regional=[];quartiles=[];concentration=[];pairs=[];decomp=[];spatial=[];calibrations=[];omits=[]
    roleframe=assets['role_frame'];geo=audit.haversine_distance_matrix(roleframe.base_centroid_lat,roleframe.base_centroid_lon);np.fill_diagonal(geo,np.inf);knn=np.argsort(geo,axis=1)[:,:6];W=np.zeros((138,138));W[np.arange(138)[:,None],knn]=1;W=np.maximum(W,W.T);W=W/W.sum(axis=1)[:,None];states=t.Estado.to_numpy()
    for (name,pro,re),g in p.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g.ID_POLIGONO.is_unique;key=dict(experiment=name,protocol=pro,repeat=re);overall.append(dict(**key,**audit.stats(g)));pairs.append(dict(**key,**pair_metrics(g)));sse=g.squared_error.sum()
        for kind in ['Estado','Municipio','fold','climate_profile']:
            for zone,h in g.groupby(kind):
                regional.append(dict(**key,kind=kind,zone=str(zone),sse_share=float(h.squared_error.sum()/sse),sample_share=len(h)/138,**audit.stats(h)));rest=g[g[kind]!=zone]
                if len(rest)>1:omits.append(dict(**key,kind=kind,omitted=str(zone),**audit.metric(rest.y_true,rest.y_pred)))
        for zone,h in g.groupby('target_quartile'):quartiles.append(dict(**key,zone=str(zone),ymin=float(h.y_true.min()),ymax=float(h.y_true.max()),**audit.stats(h)))
        for top in [1,2,5,10,20]:concentration.append(dict(**key,top=top,sse_share=float(g.nlargest(top,'squared_error').squared_error.sum()/sse)))
        for grouping in ['Estado','climate_profile']:
            means=g.groupby(grouping).error.transform('mean');decomp.append(dict(**key,grouping=grouping,between_mse=float(np.mean(means**2)),within_mse=float(np.mean((g.error-means)**2)),between_fraction=float(np.mean(means**2)/np.mean(g.squared_error))))
        e=g.set_index('ID_POLIGONO').loc[ids].error.to_numpy()
        for centered in [False,True]:
            v=e.copy()
            if centered:
                for state in np.unique(states):v[states==state]-=v[states==state].mean()
            v-=v.mean();spatial.append(dict(**key,state_centered=centered,moran_I=float(v@W@v/(v@v))))
    for label,rows,groups in [('models',overall,['experiment','protocol']),('regions',regional,['experiment','protocol','kind','zone']),('quartiles',quartiles,['experiment','protocol','zone']),('concentration',concentration,['experiment','protocol','top']),('intraprofile',pairs,['experiment','protocol']),('decomposition',decomp,['experiment','protocol','grouping']),('spatial_structure',spatial,['experiment','protocol','state_centered']),('omissions',omits,['experiment','protocol','kind','omitted'])]:write(label,rows,groups)
    parcel=p.groupby(['experiment','protocol','ID_POLIGONO','Estado','Municipio','climate_profile']).agg(y_true=('y_true','first'),mean_prediction=('y_pred','mean'),prediction_sd=('y_pred',lambda x:np.std(x)),mean_error=('error','mean'),mean_absolute_error=('absolute_error','mean'),mean_squared_error=('squared_error','mean'),max_absolute_error=('absolute_error','max')).reset_index();parcel['rms_error_across_repeats']=np.sqrt(parcel.mean_squared_error);parcel.to_csv(D/'all_parcel_errors.csv',index=False);parcel[parcel.ID_POLIGONO.isin(['AGC_171','AGC_015'])].to_csv(D/'case_errors_all_models.csv',index=False);pd.concat([g.nlargest(10,'mean_squared_error') for _,g in parcel.groupby(['experiment','protocol'])]).to_csv(D/'largest_errors_all_models.csv',index=False)
    tests=[];gains=[];errorcorr=[];groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO').loc[ids];intervals=[]
    with threadpool_limits(limits=1):
        for pro,g in p.groupby('protocol'):
            group=groups[pro if pro in ['municipality','spatial'] else 'climate_profile'].to_numpy();weights,ncluster=cluster_weights(group,5000,2026);arrays={name:h.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy() for name,h in g.groupby('experiment')};sampled={name:sampled_metrics(y,a,weights) for name,a in arrays.items()}
            for name in MAIN:
                point=pd.DataFrame(overall).query('experiment==@name and protocol==@pro').mean(numeric_only=True)
                for metric,values in sampled[name].items():intervals.append(dict(experiment=name,protocol=pro,metric=metric,point=float(point[metric]),low95=float(np.nanquantile(values,.025)),high95=float(np.nanquantile(values,.975)),n_clusters=ncluster))
            for name,refname in itertools.combinations(MAIN,2):
                aa=arrays[name];bb=arrays[refname];delta=sampled[name]['rmse']-sampled[refname]['rmse'];point=float(np.sqrt(np.mean((aa-y)**2,axis=1)).mean()-np.sqrt(np.mean((bb-y)**2,axis=1)).mean());loss=((aa-y)**2-(bb-y)**2).sum(axis=0);tests.append(dict(experiment=name,reference=refname,protocol=pro,delta_rmse=point,low95=float(np.quantile(delta,.025)),high95=float(np.quantile(delta,.975)),**paired_signflip(loss,group)))
                for re in sorted(g['repeat'].unique()):
                    a=g[(g.experiment==name)&(g['repeat']==re)].set_index('ID_POLIGONO').loc[ids];b=g[(g.experiment==refname)&(g['repeat']==re)].set_index('ID_POLIGONO').loc[ids];ea=a.error.to_numpy();eb=b.error.to_numpy();errorcorr.append(dict(experiment=name,reference=refname,protocol=pro,repeat=re,error_correlation=float(np.corrcoef(ea,eb)[0,1]),fraction_lower_absolute_error=float(np.mean(abs(ea)<abs(eb))),fraction_tie=float(np.mean(np.isclose(abs(ea),abs(eb),atol=1e-12)))));gains.extend(dict(experiment=name,reference=refname,protocol=pro,repeat=re,ID_POLIGONO=i,sse_gain=float(eb[j]**2-ea[j]**2),absolute_error_gain=float(abs(eb[j])-abs(ea[j]))) for j,i in enumerate(ids))
    tests=pd.DataFrame(tests);assert len(tests)==40;tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(D/'paired_cluster_tests.csv',index=False);pd.DataFrame(intervals).to_csv(D/'metric_cluster_intervals.csv',index=False);write('error_complementarity',errorcorr,['experiment','reference','protocol']);pd.DataFrame(gains).groupby(['experiment','reference','protocol','ID_POLIGONO'])[['sse_gain','absolute_error_gain']].mean().reset_index().to_csv(D/'paired_parcel_gains.csv',index=False)
    summary=pd.read_csv(D/'models_summary.csv');comparison=pd.DataFrame(index=MAIN+['BIG_BOTH','EXPERT7','EXPERT10','EXPERT9']);counts={'LOCAL04D':2082,'CT3':4,'J7_BOTH':28,'MIX_EXPERT10':31,'MIX_EXPERT9':30,'BIG_BOTH':1850,'EXPERT7':13,'EXPERT10':16,'EXPERT9':15};comparison['distinct_fields']=comparison.index.map(counts)
    # Local04D's original feature set already includes coordinates. Its count is a source descriptor count, not effective df.
    for pro in PROTOCOLS:
        q=summary[summary.protocol==pro].set_index('experiment');comparison[pro+'_RMSE']=q.rmse;comparison[pro+'_R2']=q.r2
    comparison.to_csv(D/'RMSE_R2_all_models.csv');presentation=pd.DataFrame(index=comparison.index);presentation['fields']=comparison.distinct_fields
    for pro in PROTOCOLS:presentation[pro]=[f'{r:.4f} / {s:.4f}' for r,s in zip(comparison[pro+'_RMSE'],comparison[pro+'_R2'])]
    presentation.to_csv(D/'presentation_RMSE_R2.csv')
    # Same representative repetition (first chronological) and axes across models.
    fig,axes=plt.subplots(4,5,figsize=(19,13),sharex=True,sharey=True);colors={'Puebla':'tab:blue','Hidalgo':'tab:orange','Tlaxcala':'tab:green'}
    for row,(pro,label) in enumerate(zip(PROTOCOLS,audit.LABELS)):
        repeat=int(p.loc[p.protocol==pro,'repeat'].min())
        for col,name in enumerate(MAIN):
            g=p[(p.protocol==pro)&(p['repeat']==repeat)&(p.experiment==name)];assert len(g)==138;ax=axes[row,col]
            for state,h in g.groupby('Estado'):ax.scatter(h.y_pred,h.y_true,s=10,alpha=.6,color=colors[state],label=state)
            ax.plot([1.5,6],[1.5,6],'k--',lw=1);cal=audit.calibration(g.y_true,g.y_pred);x=np.array([1.5,6]);ax.plot(x,cal['calibration_intercept']+cal['calibration_slope']*x,color='red',lw=1);ax.set(title=name if row==0 else '',xlabel='Predicho' if row==3 else '',ylabel=label+'\nObservado' if col==0 else '',xlim=(1.5,6),ylim=(1.5,6))
    axes[0,0].legend(fontsize=6);fig.suptitle('Comparación OOF: mismos casos y primera repetición; línea roja descriptiva');fig.tight_layout();fig.savefig(OUT/'figures/model_calibration_comparison.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    for name in MAIN:
        q=summary[summary.experiment==name].set_index('protocol').loc[PROTOCOLS];axes[0].plot(audit.LABELS,q.bias,marker='o',label=name);axes[1].plot(audit.LABELS,q.within_050,marker='o',label=name)
    axes[0].axhline(0,color='black',ls='--');axes[0].set(ylabel='Sesgo predicho − observado t/ha');axes[1].set(ylabel='Fracción |error|≤0.5 t/ha',ylim=(0,1));axes[1].legend(fontsize=7);fig.tight_layout();fig.savefig(OUT/'figures/bias_and_threshold_comparison.png',dpi=160);plt.close(fig)
    pd.DataFrame(replay).to_csv(OUT/'audit/j7_replay.csv',index=False);sources=[source,bridge,ROOT/'outputs/modeling/geoc_bridge/v1/cache/prepared.joblib',Path(__file__),ROOT/'scripts/449_j7_both_residual_audit.py']+sorted((runner.OUT/'models').glob('*.joblib'));(OUT/'residual_comparison_manifest.json').write_text(json.dumps(dict(status='complete',main_models=MAIN,supplementary=['BIG_BOTH','EXPERT7','EXPERT10','EXPERT9'],oof_rows=len(p),per_model_oof_rows=1794,compatible_outer_folds=65,geoc_97_41_excluded=True,ct3_reference_max_difference=0.,j7_replay_max_difference=max(r['max_difference'] for r in replay),paired_comparisons=40,no_predictive_refit=True,no_PRED=True,source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources}),indent=2),encoding='utf-8');print(presentation.to_string());print('Holm<.05');print(tests[tests.p_holm<.05].to_string(index=False))


if __name__=='__main__':main()
