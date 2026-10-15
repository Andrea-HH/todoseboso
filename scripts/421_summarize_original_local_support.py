"""Paired evidence for original Local04D support, distinct from local compact4."""
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
from src.compact_geographic import support_factor
from src.geoc_support_blend import blend
from src.calendar_expansion import metric
from src.family_8.research import pair_metrics
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm
OUT=ROOT/'outputs/modeling/geoc_support_blend/v1'

def main():
    assert (OUT/'execution_complete.json').exists()
    dest=OUT/'diagnostics'
    if dest.exists():raise FileExistsError('Preserve results')
    dest.mkdir();a=data();t=a['train'];ids=t.ID_POLIGONO.tolist();y=t.RENDIMIENTO_T_HA.to_numpy()
    new=pd.read_parquet(OUT/'tables/new_oof_predictions.parquet');old=pd.read_parquet(BRIDGE/'tables/oof_predictions.parquet');compact=pd.read_parquet(ROOT/'outputs/modeling/compact_geography/v1/tables/new_oof_predictions.parquet');compact=compact[compact.experiment.isin(['GLOBAL_RIDGE4','SUPPORT_BLEND4'])]
    p=pd.concat([new,old,compact],ignore_index=True);p.to_parquet(OUT/'tables/oof_predictions_with_references.parquet',index=False)
    z=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one');reps=[];regions=[];omissions=[];pairs=[]
    for (name,pro,re),g in z.groupby(['experiment','protocol','repeat']):
        key=dict(experiment=name,protocol=pro,repeat=re);assert len(g)==(41 if pro=='geoc_target_matched' else 138) and g.ID_POLIGONO.is_unique
        reps.append(dict(**key,**metric(g.y_true,g.y_pred)));pairs.append(dict(**key,**pair_metrics(g)))
        for kind in ['Estado','Municipio','fold']:
            for zone,h in g.groupby(kind):
                regions.append(dict(**key,kind=kind,zone=str(zone),n=len(h),**metric(h.y_true,h.y_pred)))
                left=g[g[kind]!=zone]
                if len(left)>1:omissions.append(dict(**key,kind=kind,omitted=str(zone),**metric(left.y_true,left.y_pred)))
    r=pd.DataFrame(reps);summary=[]
    for (name,pro),g in z.groupby(['experiment','protocol']):
        q=r[(r.experiment==name)&(r.protocol==pro)];summary.append(dict(experiment=name,protocol=pro,**{k+'_mean_repeat':q[k].mean() for k in ['rmse','mae','bias','r2']},**{k+'_pooled':v for k,v in metric(g.y_true,g.y_pred).items()}))
    summary=pd.DataFrame(summary);summary.to_csv(dest/'metrics_summary.csv',index=False)
    for name,records,keys in [('metrics',reps,['experiment','protocol']),('regional',regions,['experiment','protocol','kind','zone']),('omissions',omissions,['experiment','protocol','kind','omitted']),('intraprofile',pairs,['experiment','protocol'])]:
        d=pd.DataFrame(records);d.to_csv(dest/f'{name}_by_repeat.csv',index=False);d.drop(columns='repeat').groupby(keys).mean(numeric_only=True).reset_index().to_csv(dest/f'{name}_summary_mean_repeat.csv',index=False)
    groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO').loc[ids];tests=[];gains=[]
    with threadpool_limits(limits=1):
        for pro,frame in z.groupby('protocol'):
            cluster=pro if pro in ['municipality','spatial'] else 'climate_profile';group=groups[cluster].to_numpy();weights,_=cluster_weights(group,5000,2026)
            for reference in ['CT3','LOCAL04D','MATCHED_PLAIN_BLEND']:
                j=frame[frame.experiment=='ORIGINAL_LOCAL_SUPPORT'].merge(frame[frame.experiment==reference][['repeat','fold','ID_POLIGONO','y_pred']],on=['repeat','fold','ID_POLIGONO'],suffixes=('','_ref'),validate='one_to_one');e=j.y_pred-j.y_true;f=j.y_pred_ref-j.y_true
                j['reference']=reference;j['sse_gain']=f**2-e**2;j['absolute_error_gain']=abs(f)-abs(e);gains.append(j)
                loss=j.assign(d=e**2-f**2).groupby('ID_POLIGONO').d.sum().reindex(ids,fill_value=0).to_numpy()
                if pro=='geoc_target_matched':
                    agg=j.assign(sse=e**2,other=f**2,n=1).groupby('ID_POLIGONO')[['sse','other','n']].sum().reindex(ids,fill_value=0);den=weights@agg.n.to_numpy();delta=np.sqrt((weights@agg.sse.to_numpy())/den)-np.sqrt((weights@agg.other.to_numpy())/den);point=float(np.sqrt(np.mean(e**2))-np.sqrt(np.mean(f**2)))
                else:
                    aa=j.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy();bb=j.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred_ref').reindex(columns=ids).to_numpy();delta=sampled_metrics(y,aa,weights)['rmse']-sampled_metrics(y,bb,weights)['rmse'];point=float(sampled_metrics(y,aa,np.ones((1,138)))['rmse'][0]-sampled_metrics(y,bb,np.ones((1,138)))['rmse'][0])
                tests.append(dict(protocol=pro,reference=reference,delta_rmse=point,low95=float(np.quantile(delta,.025)),high95=float(np.quantile(delta,.975)),**paired_signflip(loss,group)))
    tests=pd.DataFrame(tests);assert len(tests)==15;tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(dest/'paired_cluster_tests.csv',index=False)
    pd.concat(gains).to_parquet(dest/'parcel_gains.parquet',index=False)
    selection=pd.read_csv(OUT/'tables/selection.csv');selection.groupby(['experiment','protocol'])[['weight','median_support','mean_effective_local_weight']].mean().reset_index().to_csv(dest/'weight_support_summary.csv',index=False)
    new.groupby(['experiment','protocol'])[['support','effective_local_weight']].agg(['mean','median','min','max']).to_csv(dest/'parcel_support_summary.csv')
    replay=[];checks=0
    with threadpool_limits(limits=1):
        for i in range(81):
            pack=joblib.load(OUT/'models'/f'{i:02d}.joblib');tr=pack['train_positions'];va=pack['validation_positions'];q=selection.iloc[2*i]
            ct=pack['ct3'].predict(t.iloc[va]);loc=local_prediction(a['x'],a['distance'],a['train_global'][tr],a['train_global'][va],y[tr]);support=support_factor(a['distance'],a['train_global'][tr],a['train_global'][va],24)
            for name,w in pack['weights'].items():
                pred=blend(ct,loc,w,support if name=='ORIGINAL_LOCAL_SUPPORT' else np.ones(len(va)))
                expected=new[(new.experiment==name)&(new.protocol==q.protocol)&(new['repeat']==q['repeat'])&(new.fold==q.fold)].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred
                error=float(np.max(abs(pred-expected)));assert error==0;replay.append(dict(experiment=name,index=i,max_difference=error))
            for item in pack['ledger']:assert not set(item['training'])&(set(item['inner_validation'])|set(item['external_validation']));checks+=1
    pd.DataFrame(replay).to_csv(OUT/'audit/exact_replay.csv',index=False)
    same=new[(new.experiment=='MATCHED_PLAIN_BLEND')&(new.protocol!='geoc_target_matched')].merge(old[old.experiment=='INNER_BLEND'],on=['protocol','repeat','fold','ID_POLIGONO'],suffixes=('','_ref'),validate='one_to_one');assert len(same)==1794
    parity=float(abs(same.y_pred-same.y_pred_ref).max());assert parity<1e-10
    chart=summary[summary.protocol!='geoc_target_matched'].pivot(index='experiment',columns='protocol',values='rmse_mean_repeat');order=['CT3','LOCAL04D','FIXED50','MATCHED_PLAIN_BLEND','ORIGINAL_LOCAL_SUPPORT','SUPPORT_BLEND4'];protocols=['random','climate_profile','municipality','spatial'];values=chart.loc[order,protocols]
    fig,ax=plt.subplots(figsize=(10,5));x=np.arange(4)
    for i,name in enumerate(order):ax.bar(x+(i-2.5)*.13,values.loc[name],width=.13,label=name)
    ax.set(xticks=x,xticklabels=['Aleatoria','Perfil','Municipal','Espacial'],ylabel='RMSE (t/ha)',title='Local04D original con soporte y controles;65 folds');ax.legend(fontsize=8);fig.tight_layout();fig.savefig(dest/'original_local_support_comparison.png',dpi=160);plt.close(fig)
    with pd.ExcelWriter(OUT/'mezcla_CT3_Local04D_original_soporte.xlsx',engine='openpyxl') as writer:
        summary.to_excel(writer,sheet_name='Metricas_dos_bancos',index=False);tests.to_excel(writer,sheet_name='Comparaciones_pareadas',index=False);selection.to_excel(writer,sheet_name='Pesos_soporte',index=False)
        for file,sheet in [('regional_summary_mean_repeat.csv','Regiones'),('intraprofile_summary_mean_repeat.csv','Intraperfil'),('weight_support_summary.csv','Resumen_pesos')]:pd.read_csv(dest/file).to_excel(writer,sheet_name=sheet,index=False)
    cfg=json.loads((OUT/'frozen_design.json').read_text());assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==h for path,h in cfg['source_sha256'].items())
    (OUT/'manifest.json').write_text(json.dumps(dict(status='complete',new_oof=4900,new_external_predictors=162,exact_replay_max_difference=0.,matched_plain_previous_max_difference=parity,membership_checks=checks,tests_passed=2,no_new_final_fit=True,no_new_PRED=True,source_hashes_preserved=True,statistical_scope='15 exploratory cluster contrasts Holm; repeated labels, fixed predictions, no independent superiority claim'),indent=2),encoding='utf-8')
    print(chart.loc[order,protocols].to_string());print('\nGEOC');print(summary[summary.protocol=='geoc_target_matched'][['experiment','rmse_pooled','mae_pooled']].to_string(index=False));print(tests.to_string(index=False))

if __name__=='__main__':main()
