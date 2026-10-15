"""Reverse formulation diagnostics, exact replay, clustered contrasts and cost."""
from pathlib import Path
import sys,json,time,pickle,hashlib
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.geoc_bridge import OUT as BRIDGE,OLD,data,local_prediction
from src.calendar_expansion import metric
from src.family_8.research import pair_metrics
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm
OUT=BRIDGE/'reverse/v1'

def main():
    if (OUT/'manifest.json').exists():raise FileExistsError('Preserve completed synthesis')
    dest=OUT/'diagnostics';dest.mkdir(exist_ok=False);a=data();t=a['train'];y=t.RENDIMIENTO_T_HA.to_numpy();ids=t.ID_POLIGONO.tolist()
    new=pd.read_parquet(OUT/'tables/new_oof_predictions.parquet');old=pd.read_parquet(BRIDGE/'tables/oof_predictions.parquet');p=pd.concat([old,new],ignore_index=True)
    p.to_parquet(OUT/'tables/oof_predictions.parquet',index=False)
    z=p.merge(t[['ID_POLIGONO','Estado','Municipio','climate_profile']],on='ID_POLIGONO',validate='many_to_one')
    reps=[];regions=[];pairs=[];omissions=[]
    for (name,pro,re),g in z.groupby(['experiment','protocol','repeat']):
        key=dict(experiment=name,protocol=pro,repeat=re);reps.append(dict(**key,**metric(g.y_true,g.y_pred)));pairs.append(dict(**key,**pair_metrics(g)))
        for kind in ['Estado','Municipio','fold']:
            for zone,h in g.groupby(kind):
                regions.append(dict(**key,kind=kind,zone=str(zone),n=len(h),**metric(h.y_true,h.y_pred)))
                left=g[g[kind]!=zone]
                if len(left)>1:omissions.append(dict(**key,kind=kind,omitted=str(zone),**metric(left.y_true,left.y_pred)))
    r=pd.DataFrame(reps);summary=[]
    for (name,pro),g in z.groupby(['experiment','protocol']):
        q=r[(r.experiment==name)&(r.protocol==pro)]
        summary.append(dict(experiment=name,protocol=pro,**{k+'_mean_repeat':q[k].mean() for k in ['rmse','mae','bias','r2']},**{k+'_pooled':v for k,v in metric(g.y_true,g.y_pred).items()}))
    summary=pd.DataFrame(summary);summary.to_csv(dest/'metrics_summary.csv',index=False)
    for name,records,keys in [('metrics',reps,['experiment','protocol']),('regional',regions,['experiment','protocol','kind','zone']),('intraprofile',pairs,['experiment','protocol']),('omissions',omissions,['experiment','protocol','kind','omitted'])]:
        d=pd.DataFrame(records);d.to_csv(dest/f'{name}_by_repeat.csv',index=False);d.drop(columns='repeat').groupby(keys).mean(numeric_only=True).reset_index().to_csv(dest/f'{name}_summary_mean_repeat.csv',index=False)
    groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO').loc[ids];tests=[];gains=[]
    with threadpool_limits(limits=1):
        for pro,frame in z.groupby('protocol'):
            cluster='climate_profile' if pro in ['random','climate_profile','geoc_target_matched'] else pro
            group=groups[cluster].to_numpy();weights,_=cluster_weights(group,5000,2026)
            v=frame[frame.experiment=='LOCAL_PLUS_COMPACT_EN']
            for reference in (['CT3','LOCAL04D'] if pro=='geoc_target_matched' else ['CT3','LOCAL04D','RESIDUAL_LOCAL']):
                b=frame[frame.experiment==reference][['repeat','fold','ID_POLIGONO','y_pred']]
                j=v.merge(b,on=['repeat','fold','ID_POLIGONO'],suffixes=('','_ref'),validate='one_to_one');e=j.y_pred-j.y_true;f=j.y_pred_ref-j.y_true
                j['reference']=reference;j['sse_gain']=f**2-e**2;j['absolute_error_gain']=abs(f)-abs(e);gains.append(j)
                loss=j.assign(d=e**2-f**2).groupby('ID_POLIGONO').d.sum().reindex(ids,fill_value=0).to_numpy()
                if pro=='geoc_target_matched':
                    agg=j.assign(sse=e**2,other=f**2,n=1).groupby('ID_POLIGONO')[['sse','other','n']].sum().reindex(ids,fill_value=0);den=weights@agg.n.to_numpy()
                    delta=np.sqrt((weights@agg.sse.to_numpy())/den)-np.sqrt((weights@agg.other.to_numpy())/den);point=float(np.sqrt(np.mean(e**2))-np.sqrt(np.mean(f**2)))
                else:
                    aa=j.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy();bb=j.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred_ref').reindex(columns=ids).to_numpy()
                    delta=sampled_metrics(y,aa,weights)['rmse']-sampled_metrics(y,bb,weights)['rmse'];point=float(sampled_metrics(y,aa,np.ones((1,138)))['rmse'][0]-sampled_metrics(y,bb,np.ones((1,138)))['rmse'][0])
                tests.append(dict(protocol=pro,reference=reference,delta_rmse=point,low95=float(np.quantile(delta,.025)),high95=float(np.quantile(delta,.975)),**paired_signflip(loss,group)))
    tests=pd.DataFrame(tests);assert len(tests)==14;tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(dest/'paired_cluster_tests.csv',index=False)
    pd.concat(gains).to_parquet(dest/'parcel_gains.parquet',index=False)
    registry=pd.read_parquet(OUT/'tables/registry.parquet');registry.to_csv(dest/'selection_by_fold.csv',index=False)
    registry.groupby('protocol').agg(amplitude_mean=('amplitude','mean'),zero_fraction=('amplitude',lambda v:(v==0).mean()),n_folds=('fold','size')).reset_index().to_csv(dest/'selection_summary.csv',index=False)
    replays=[];checks=0
    with threadpool_limits(limits=1):
        for fi in range(81):
            pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');tr=pack['train_positions'];va=pack['validation_positions'];amp=pack['selection']['amplitude']
            base=local_prediction(a['x'],a['distance'],a['train_global'][tr],a['train_global'][va],y[tr]);pred=base if amp==0 else base+amp*pack['model'].predict(t.iloc[va])
            q=registry.iloc[fi];expected=new[(new.protocol==q.protocol)&(new['repeat']==q['repeat'])&(new.fold==q.fold)].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred
            error=float(np.max(abs(pred-expected)));assert error==0;replays.append(dict(index=fi,max_difference=error))
            for check in pack['membership']:
                assert not set(check['fit_positions'])&(set(check['residual_positions'])|set(check['inner_validation'])|set(check['external_validation']));checks+=1
    pd.DataFrame(replays).to_csv(OUT/'audit/exact_replay.csv',index=False)
    # Inference-only benchmark: existing final CT3 and frozen Local04D, 59 X.
    final=joblib.load(ROOT/'outputs/modeling/winner_predictions/v1/models/final_winners_train138.joblib')['ct3'];x197=pd.read_parquet(ROOT/'outputs/modeling/winner_predictions/v1/tables/features197_target_free.parquet').set_index('ID_POLIGONO')
    seen=set(a['train_global']);query=np.array([i for i in range(len(a['ids197'])) if i not in seen]);frame=x197.loc[[a['ids197'][i] for i in query]].reset_index()
    timings={}
    with threadpool_limits(limits=1):
        for name,func in [('CT3',lambda:final.predict(frame)),('Local04D',lambda:local_prediction(a['x'],a['distance'],a['train_global'],query,y))]:
            for _ in range(3):func()
            times=[]
            for _ in range(20):
                start=time.perf_counter();func();times.append(time.perf_counter()-start)
            timings[name]=dict(median_seconds_59=float(np.median(times)),median_ms_per_parcel=float(np.median(times)*1000/59))
    timings['local_over_ct3_ratio']=timings['Local04D']['median_seconds_59']/timings['CT3']['median_seconds_59'];timings['CT3_serialized_bytes']=len(pickle.dumps(final));timings['Local_training_score_coordinates_labels_float64_bytes']=(138*20+138*2+138)*8;timings['benchmark_scope']='20 warm CPU runs, one thread, 59 existing X; excludes feature extraction, original PCA fitting and model loading; no revised final predictions.'
    (OUT/'audit/complexity_benchmark.json').write_text(json.dumps(timings,indent=2),encoding='utf-8')
    cfg=json.loads((OUT/'frozen_design.json').read_text());assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==h for path,h in cfg['source_sha256'].items())
    with pd.ExcelWriter(OUT/'comparacion_inversa_y_complejidad.xlsx',engine='openpyxl') as writer:
        summary.to_excel(writer,sheet_name='Metricas_dos_bancos',index=False);tests.to_excel(writer,sheet_name='Pruebas_pareadas',index=False);registry.to_excel(writer,sheet_name='Seleccion_interna',index=False);pd.read_csv(dest/'regional_summary_mean_repeat.csv').to_excel(writer,sheet_name='Regiones',index=False);pd.read_csv(dest/'intraprofile_summary_mean_repeat.csv').to_excel(writer,sheet_name='Intraperfil',index=False)
    (OUT/'manifest.json').write_text(json.dumps(dict(status='complete',new_oof=2450,new_outer_models=81,exact_replay_max_difference=0.,membership_exclusion_checks=checks,tests_passed=2,no_new_final_predictions=True,protected_sources_preserved=True,paired_tests=14,statistical_scope='conditional fixed-OOF bootstrap, signs and Holm within14 reverse contrasts, no correction for all project searches',complexity_benchmark=timings),indent=2),encoding='utf-8')
    print(summary[summary.experiment=='LOCAL_PLUS_COMPACT_EN'].to_string(index=False));print(tests.to_string(index=False));print(json.dumps(timings,indent=2))

if __name__=='__main__':main()
