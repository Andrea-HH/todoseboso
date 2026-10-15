"""OOF evidence and support diagnostics for the bounded compact geography test."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.geoc_bridge import data,OLD,OUT as BRIDGE
from src.compact_geographic import predict_bundle,neighborhood,support_factor
from src.calendar_expansion import metric
from src.family_8.research import pair_metrics
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm
OUT=ROOT/'outputs/modeling/compact_geography/v1'

def main():
    assert (OUT/'execution_complete.json').exists()
    dest=OUT/'diagnostics'
    if dest.exists():raise FileExistsError('Preserve diagnostics')
    dest.mkdir();a=data();t=a['train'];ids=t.ID_POLIGONO.tolist();y=t.RENDIMIENTO_T_HA.to_numpy()
    new=pd.read_parquet(OUT/'tables/new_oof_predictions.parquet');old=pd.read_parquet(BRIDGE/'tables/oof_predictions.parquet');reverse=pd.read_parquet(BRIDGE/'reverse/v1/tables/new_oof_predictions.parquet');p=pd.concat([new,old,reverse],ignore_index=True)
    assert not p.duplicated(['experiment','protocol','repeat','fold','ID_POLIGONO']).any()
    p.to_parquet(OUT/'tables/oof_predictions_with_references.parquet',index=False)
    z=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one');reps=[];regions=[];omissions=[];pairs=[]
    for (name,pro,re),g in z.groupby(['experiment','protocol','repeat']):
        assert len(g)==(41 if pro=='geoc_target_matched' else 138) and g.ID_POLIGONO.is_unique
        key=dict(experiment=name,protocol=pro,repeat=re);reps.append(dict(**key,**metric(g.y_true,g.y_pred)));pairs.append(dict(**key,**pair_metrics(g)))
        for kind in ['Estado','Municipio','fold']:
            for zone,h in g.groupby(kind):
                regions.append(dict(**key,kind=kind,zone=str(zone),n=len(h),**metric(h.y_true,h.y_pred)))
                remain=g[g[kind]!=zone]
                if len(remain)>1:omissions.append(dict(**key,kind=kind,omitted=str(zone),**metric(remain.y_true,remain.y_pred)))
    rep=pd.DataFrame(reps);summary=[]
    for (name,pro),g in z.groupby(['experiment','protocol']):
        h=rep[(rep.experiment==name)&(rep.protocol==pro)]
        summary.append(dict(experiment=name,protocol=pro,**{k+'_mean_repeat':h[k].mean() for k in ['rmse','mae','bias','r2']},**{k+'_pooled':v for k,v in metric(g.y_true,g.y_pred).items()}))
    summary=pd.DataFrame(summary);summary.to_csv(dest/'metrics_summary.csv',index=False)
    for name,records,keys in [('metrics',reps,['experiment','protocol']),('regional',regions,['experiment','protocol','kind','zone']),('omissions',omissions,['experiment','protocol','kind','omitted']),('intraprofile',pairs,['experiment','protocol'])]:
        d=pd.DataFrame(records);d.to_csv(dest/f'{name}_by_repeat.csv',index=False);d.drop(columns='repeat').groupby(keys).mean(numeric_only=True).reset_index().to_csv(dest/f'{name}_summary_mean_repeat.csv',index=False)
    groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO').loc[ids];tests=[];gains=[]
    with threadpool_limits(limits=1):
        for pro,frame in z.groupby('protocol'):
            cluster=pro if pro in ['municipality','spatial'] else 'climate_profile';group=groups[cluster].to_numpy();weights,_=cluster_weights(group,5000,2026)
            reference=frame[frame.experiment=='CT3'][['repeat','fold','ID_POLIGONO','y_pred']]
            for name in new.experiment.unique():
                j=frame[frame.experiment==name].merge(reference,on=['repeat','fold','ID_POLIGONO'],suffixes=('','_ref'),validate='one_to_one');e=j.y_pred-j.y_true;f=j.y_pred_ref-j.y_true
                j['sse_gain']=f**2-e**2;j['absolute_error_gain']=abs(f)-abs(e);gains.append(j)
                loss=j.assign(d=e**2-f**2).groupby('ID_POLIGONO').d.sum().reindex(ids,fill_value=0).to_numpy()
                if pro=='geoc_target_matched':
                    agg=j.assign(sse=e**2,ref=f**2,n=1).groupby('ID_POLIGONO')[['sse','ref','n']].sum().reindex(ids,fill_value=0);den=weights@agg.n.to_numpy();delta=np.sqrt((weights@agg.sse.to_numpy())/den)-np.sqrt((weights@agg.ref.to_numpy())/den);point=float(np.sqrt(np.mean(e**2))-np.sqrt(np.mean(f**2)))
                else:
                    aa=j.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy();bb=j.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred_ref').reindex(columns=ids).to_numpy();delta=sampled_metrics(y,aa,weights)['rmse']-sampled_metrics(y,bb,weights)['rmse'];point=float(sampled_metrics(y,aa,np.ones((1,138)))['rmse'][0]-sampled_metrics(y,bb,np.ones((1,138)))['rmse'][0])
                tests.append(dict(experiment=name,protocol=pro,reference='CT3',delta_rmse=point,low95=float(np.quantile(delta,.025)),high95=float(np.quantile(delta,.975)),**paired_signflip(loss,group)))
    tests=pd.DataFrame(tests);assert len(tests)==35;tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(dest/'paired_cluster_tests.csv',index=False)
    g=pd.concat(gains);g.to_parquet(dest/'parcel_gains.parquet',index=False);g=g.groupby(['experiment','protocol','ID_POLIGONO','Estado','Municipio'],as_index=False)[['sse_gain','absolute_error_gain']].mean();g.to_csv(dest/'parcel_gain_repeat_average.csv',index=False)
    extremes=[]
    for _,h in g.groupby(['experiment','protocol']):extremes.extend([h.nlargest(5,'sse_gain').assign(direction='improvement'),h.nsmallest(5,'sse_gain').assign(direction='deterioration')])
    pd.concat(extremes).to_csv(dest/'largest_changes.csv',index=False)
    reg=pd.read_parquet(OUT/'tables/registry.parquet');reg.to_csv(dest/'selection_by_fold.csv',index=False)
    reg.groupby(['experiment','protocol']).agg(mean_weight=('weight','mean'),zero_fraction=('weight',lambda v:(v==0).mean())).reset_index().to_csv(dest/'selection_summary.csv',index=False)
    replay=[];support=[];checks=0;geo_to_train={int(v):i for i,v in enumerate(a['train_global'])}
    with threadpool_limits(limits=1):
        for fi in range(81):
            pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');tr=pack['train_positions'];va=pack['validation_positions'];query=a['train_global'][va];assert not set(tr)&set(va)
            preds=predict_bundle(pack,t.iloc[va],query,a['distance']);selected=reg.iloc[fi*7];pro=selected.protocol;re=selected['repeat'];fold=selected.fold
            for name,pred in preds.items():
                expected=new[(new.experiment==name)&(new.protocol==pro)&(new['repeat']==re)&(new.fold==fold)].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred
                error=float(np.max(abs(pred-expected)));assert error==0;replay.append(dict(experiment=name,protocol=pro,repeat=re,fold=fold,max_difference=error))
                b=pack['variants'][name]
                if b['model'] is not None and name!='GLOBAL_RIDGE4':
                    params=b['params'];idx,near,w=neighborhood(a['distance'],a['train_global'][tr],query,params['k'],params['power']);s=support_factor(a['distance'],a['train_global'][tr],query,params['k']);neff=w.sum(axis=1)**2/(w*w).sum(axis=1)
                    for q,i in enumerate(va):
                        profiles=t.iloc[tr[idx[q]]].climate_profile
                        support.append(dict(experiment=name,protocol=pro,repeat=re,fold=fold,ID_POLIGONO=t.iloc[i].ID_POLIGONO,k=params['k'],power=params['power'],kth_distance_normalized=float(near[q,-1]),effective_neighbors=float(neff[q]),unique_neighbor_profiles=profiles.nunique(),support_factor=float(s[q])))
            checks+=sum(v['exclusion_verified'] for v in pack['ledger'])
    pd.DataFrame(replay).to_csv(OUT/'audit/exact_replay.csv',index=False);pd.DataFrame(support).to_csv(dest/'neighbor_support.csv',index=False)
    if support:pd.DataFrame(support).groupby(['experiment','protocol']).agg(median_effective_neighbors=('effective_neighbors','median'),median_profiles=('unique_neighbor_profiles','median'),median_support=('support_factor','median')).reset_index().to_csv(dest/'support_summary.csv',index=False)
    order=list(new.experiment.unique());protocols=['random','climate_profile','municipality','spatial'];matrix=summary.pivot(index='experiment',columns='protocol',values='rmse_mean_repeat');delta=matrix.loc[order,protocols]-matrix.loc['CT3',protocols]
    fig,ax=plt.subplots(figsize=(9,5.5));lim=max(abs(delta.to_numpy()).max(),.01);im=ax.imshow(delta,cmap='RdBu_r',vmin=-lim,vmax=lim,aspect='auto');ax.set(xticks=range(4),xticklabels=['Aleatoria','Perfil','Municipal','Espacial'],yticks=range(7),yticklabels=order,title='Cambio de RMSE frente a C-T3; negativo = mejora')
    for i in range(7):
        for j in range(4):ax.text(j,i,f'{delta.iloc[i,j]:+.3f}',ha='center',va='center')
    fig.colorbar(im,ax=ax);fig.tight_layout();fig.savefig(dest/'compact_geographic_comparison.png',dpi=160);plt.close(fig)
    with pd.ExcelWriter(OUT/'geografia_compacta_resultados.xlsx',engine='openpyxl') as writer:
        summary.to_excel(writer,sheet_name='Metricas_dos_bancos',index=False);tests.to_excel(writer,sheet_name='Pruebas_pareadas',index=False);reg.to_excel(writer,sheet_name='Seleccion_interna',index=False)
        for file,sheet in [('regional_summary_mean_repeat.csv','Regiones'),('intraprofile_summary_mean_repeat.csv','Intraperfil'),('support_summary.csv','Soporte_vecinos')]:pd.read_csv(dest/file).to_excel(writer,sheet_name=sheet,index=False)
    cfg=json.loads((OUT/'frozen_design.json').read_text());assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==h for path,h in cfg['source_sha256'].items())
    (OUT/'manifest.json').write_text(json.dumps(dict(status='complete',new_oof=17150,new_predictors=567,exact_replay_max_difference=0.,honest_residual_context_checks=checks,unit_tests_passed=3,no_new_final_fit=True,no_new_PRED=True,protected_sources_unchanged=True,inference='35 exploratory fixed-OOF cluster contrasts, Holm; no correction for all historical search',warnings=json.loads((OUT/'execution_complete.json').read_text())['warnings']),indent=2),encoding='utf-8')
    print(matrix.loc[['CT3','LOCAL04D']+order,protocols].to_string());print('\nGEOC');print(summary[summary.protocol=='geoc_target_matched'][['experiment','rmse_pooled','mae_pooled']].to_string(index=False));print('\nTESTS');print(tests[['experiment','protocol','delta_rmse','low95','high95','p_holm']].to_string(index=False))

if __name__=='__main__':main()
