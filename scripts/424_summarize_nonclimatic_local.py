"""Matched climate ablation, both residual directions and geography-only control."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.geoc_bridge import data,OLD,OUT as BRIDGE,local_prediction
from src.compact_geographic import neighborhood
from src.calendar_expansion import metric
from src.family_8.research import pair_metrics
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm
OUT=ROOT/'outputs/modeling/nonclimatic_local/v1'

def main():
    assert (OUT/'execution_complete.json').exists()
    dest=OUT/'diagnostics'
    if dest.exists():raise FileExistsError('Preserve complete diagnostics')
    dest.mkdir();a=data();t=a['train'];ids=t.ID_POLIGONO.tolist();y=t.RENDIMIENTO_T_HA.to_numpy();rep=joblib.load(OUT/'cache/representations.joblib');scores=rep['scores']
    new=pd.read_parquet(OUT/'tables/new_oof_predictions.parquet');old=pd.read_parquet(BRIDGE/'tables/oof_predictions.parquet');old=old[old.experiment.isin(['CT3','LOCAL04D','FIXED50','RESIDUAL_LOCAL'])];reverse=pd.read_parquet(BRIDGE/'reverse/v1/tables/new_oof_predictions.parquet');p=pd.concat([new,old,reverse],ignore_index=True)
    assert not p.duplicated(['experiment','protocol','repeat','fold','ID_POLIGONO']).any();p.to_parquet(OUT/'tables/oof_predictions_with_references.parquet',index=False)
    z=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one');rows=[];regional=[];omissions=[];pairs=[]
    for (name,pro,re),g in z.groupby(['experiment','protocol','repeat']):
        key=dict(experiment=name,protocol=pro,repeat=re);assert len(g)==(41 if pro=='geoc_target_matched' else 138) and g.ID_POLIGONO.is_unique
        rows.append(dict(**key,**metric(g.y_true,g.y_pred)));pairs.append(dict(**key,**pair_metrics(g)))
        for kind in ['Estado','Municipio','fold']:
            for zone,h in g.groupby(kind):
                regional.append(dict(**key,kind=kind,zone=str(zone),n=len(h),**metric(h.y_true,h.y_pred)))
                left=g[g[kind]!=zone]
                if len(left)>1:omissions.append(dict(**key,kind=kind,omitted=str(zone),**metric(left.y_true,left.y_pred)))
    r=pd.DataFrame(rows);summary=[]
    for (name,pro),g in z.groupby(['experiment','protocol']):
        q=r[(r.experiment==name)&(r.protocol==pro)];summary.append(dict(experiment=name,protocol=pro,**{k+'_mean_repeat':q[k].mean() for k in ['rmse','mae','bias','r2']},**{k+'_pooled':v for k,v in metric(g.y_true,g.y_pred).items()}))
    summary=pd.DataFrame(summary);summary.to_csv(dest/'metrics_summary.csv',index=False)
    for name,records,keys in [('metrics',rows,['experiment','protocol']),('regional',regional,['experiment','protocol','kind','zone']),('omissions',omissions,['experiment','protocol','kind','omitted']),('intraprofile',pairs,['experiment','protocol'])]:
        d=pd.DataFrame(records);d.to_csv(dest/f'{name}_by_repeat.csv',index=False);d.drop(columns='repeat').groupby(keys).mean(numeric_only=True).reset_index().to_csv(dest/f'{name}_summary_mean_repeat.csv',index=False)
    groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO').loc[ids];tests=[];gains=[];primary=['NONCLIM_LOCAL','CT3_PLUS_NONCLIM','NONCLIM_PLUS_COMPACT_EN']
    with threadpool_limits(limits=1):
        for pro,frame in z.groupby('protocol'):
            cluster=pro if pro in ['municipality','spatial'] else 'climate_profile';group=groups[cluster].to_numpy();weights,_=cluster_weights(group,5000,2026)
            for name in primary:
                for reference in ['CT3','LOCAL04D']:
                    j=frame[frame.experiment==name].merge(frame[frame.experiment==reference][['repeat','fold','ID_POLIGONO','y_pred']],on=['repeat','fold','ID_POLIGONO'],suffixes=('','_ref'),validate='one_to_one');e=j.y_pred-j.y_true;f=j.y_pred_ref-j.y_true
                    j['reference']=reference;j['sse_gain']=f**2-e**2;j['absolute_error_gain']=abs(f)-abs(e);gains.append(j)
                    loss=j.assign(d=e**2-f**2).groupby('ID_POLIGONO').d.sum().reindex(ids,fill_value=0).to_numpy()
                    if pro=='geoc_target_matched':
                        agg=j.assign(sse=e**2,other=f**2,n=1).groupby('ID_POLIGONO')[['sse','other','n']].sum().reindex(ids,fill_value=0);den=weights@agg.n.to_numpy();delta=np.sqrt((weights@agg.sse.to_numpy())/den)-np.sqrt((weights@agg.other.to_numpy())/den);point=float(np.sqrt(np.mean(e**2))-np.sqrt(np.mean(f**2)))
                    else:
                        aa=j.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy();bb=j.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred_ref').reindex(columns=ids).to_numpy();delta=sampled_metrics(y,aa,weights)['rmse']-sampled_metrics(y,bb,weights)['rmse'];point=float(sampled_metrics(y,aa,np.ones((1,138)))['rmse'][0]-sampled_metrics(y,bb,np.ones((1,138)))['rmse'][0])
                    tests.append(dict(experiment=name,reference=reference,protocol=pro,delta_rmse=point,low95=float(np.quantile(delta,.025)),high95=float(np.quantile(delta,.975)),**paired_signflip(loss,group)))
    tests=pd.DataFrame(tests);assert len(tests)==30;tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(dest/'paired_cluster_tests.csv',index=False)
    g=pd.concat(gains);g.to_parquet(dest/'parcel_gains.parquet',index=False);g=g.groupby(['experiment','reference','protocol','ID_POLIGONO','Estado','Municipio'],as_index=False)[['sse_gain','absolute_error_gain']].mean();g.to_csv(dest/'parcel_gain_repeat_average.csv',index=False)
    extremes=[]
    for _,h in g.groupby(['experiment','reference','protocol']):extremes.extend([h.nlargest(5,'sse_gain').assign(direction='improvement'),h.nsmallest(5,'sse_gain').assign(direction='deterioration')])
    pd.concat(extremes).to_csv(dest/'largest_changes.csv',index=False)
    registry=pd.read_parquet(OUT/'tables/registry.parquet');registry.to_csv(dest/'selection_by_fold.csv',index=False)
    registry.groupby('protocol').agg(forward_mean=('forward_amplitude','mean'),forward_zero_fraction=('forward_amplitude',lambda v:(v==0).mean()),reverse_mean=('reverse_amplitude','mean'),reverse_zero_fraction=('reverse_amplitude',lambda v:(v==0).mean())).reset_index().to_csv(dest/'selection_summary.csv',index=False)
    replays=[];checks=0
    with threadpool_limits(limits=1):
        for i in range(81):
            b=joblib.load(OUT/'models'/f'{i:02d}.joblib');tr=b['train_positions'];va=b['validation_positions'];q=registry.iloc[i];pos=a['train_global'];d=a['distance'];x=scores['nonclimatic']
            nc=local_prediction(x,d,pos[tr],pos[va],y[tr]);ct=b['ct3'].predict(t.iloc[va]);amp=b['forward_amplitude'];forward=ct if amp==0 else ct+amp*local_prediction(x,d,pos[tr],pos[va],b['forward_residual_target']);reverse=b['reverse'];amp2=reverse['selection']['amplitude'];back=nc if amp2==0 else nc+amp2*reverse['model'].predict(t.iloc[va])
            indices,near,w=neighborhood(d,pos[tr],pos[va],24,1.);mean=(y[tr][indices]*w).sum(axis=1)/w.sum(axis=1)
            predictions=dict(NONCLIM_LOCAL=nc,CT3_PLUS_NONCLIM=forward,NONCLIM_PLUS_COMPACT_EN=back,SAFE_CLIMATE_LOCAL=local_prediction(scores['safe_with_climate'],d,pos[tr],pos[va],y[tr]),GEO_MEAN24=mean)
            for name,values in predictions.items():
                expected=new[(new.experiment==name)&(new.protocol==q.protocol)&(new['repeat']==q['repeat'])&(new.fold==q.fold)].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred;error=float(np.max(abs(values-expected)));assert error==0;replays.append(dict(experiment=name,index=i,max_difference=error))
            for item in b['ledger']:assert item['verified'];checks+=1
            for item in reverse['membership']:assert not set(item['fit_positions'])&(set(item['residual_positions'])|set(item['inner_validation'])|set(item['external_validation']));checks+=1
    pd.DataFrame(replays).to_csv(OUT/'audit/exact_replay.csv',index=False)
    # PCA loadings describe X variance, not supervised predictive importance.
    loading=[]
    for mode,b in rep['transforms'].items():
        for pc,coefs in enumerate(b['pca'].components_):
            for index in np.argsort(abs(coefs))[-10:][::-1]:loading.append(dict(representation=mode,pc=pc+1,feature=b['columns'][index],loading=float(coefs[index]),explained_X_variance=float(b['pca'].explained_variance_ratio_[pc])))
    pd.DataFrame(loading).to_csv(dest/'PCA_top_loadings_descriptive.csv',index=False)
    table=summary[summary.protocol!='geoc_target_matched'].pivot(index='experiment',columns='protocol',values='rmse_mean_repeat');order=['CT3','LOCAL04D','SAFE_CLIMATE_LOCAL','NONCLIM_LOCAL','CT3_PLUS_NONCLIM','NONCLIM_PLUS_COMPACT_EN','GEO_MEAN24'];protocols=['random','climate_profile','municipality','spatial'];values=table.loc[order,protocols]
    fig,ax=plt.subplots(figsize=(11,5.5));xx=np.arange(4)
    for i,name in enumerate(order):ax.bar(xx+(i-3)*.11,values.loc[name],width=.11,label=name)
    ax.set(xticks=xx,xticklabels=['Aleatoria','Perfil','Municipal','Espacial'],ylabel='RMSE (t/ha)',title='Bloque sin clima y correcciones:65 folds originales');ax.legend(fontsize=8);fig.tight_layout();fig.savefig(dest/'nonclimatic_comparison.png',dpi=160);plt.close(fig)
    with pd.ExcelWriter(OUT/'fase_sin_clima_resultados.xlsx',engine='openpyxl') as writer:
        summary.to_excel(writer,sheet_name='Metricas_dos_bancos',index=False);tests.to_excel(writer,sheet_name='Comparaciones_pareadas',index=False);registry.to_excel(writer,sheet_name='Seleccion_interna',index=False)
        for path,sheet in [(dest/'regional_summary_mean_repeat.csv','Regiones'),(dest/'intraprofile_summary_mean_repeat.csv','Intraperfil'),(OUT/'audit/feature_inventory_ancestry.csv','Inventario_exclusiones'),(OUT/'audit/source_counts.csv','Fuentes_variables')]:pd.read_csv(path).to_excel(writer,sheet_name=sheet,index=False)
    cfg=json.loads((OUT/'frozen_design.json').read_text());policy=json.loads((OUT/'feature_policy_frozen.json').read_text());assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==h for path,h in cfg['source_sha256'].items());assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==h for path,h in policy['sources'].items())
    (OUT/'manifest.json').write_text(json.dumps(dict(status='complete',new_oof=12250,new_predictors=405,exact_replay_max_difference=0.,residual_exclusion_context_checks=checks,tests_passed=5,protected_sources_unchanged=True,no_new_final138_fit=True,no_new_PRED=True,representation_audit=json.loads((OUT/'feature_audit_complete.json').read_text()),statistical_scope='30 exploratory paired fixed-OOF cluster contrasts, Holm within phase not full historical search',warnings=json.loads((OUT/'execution_complete.json').read_text())['warnings']),indent=2),encoding='utf-8')
    print(values.to_string());print('\nGEOC');print(summary[summary.protocol=='geoc_target_matched'][['experiment','rmse_pooled','mae_pooled']].to_string(index=False));print('\nTESTS');print(tests[['experiment','reference','protocol','delta_rmse','low95','high95','p_holm']].to_string(index=False))

if __name__=='__main__':main()
