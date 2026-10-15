"""Paired metrics, geographic dependence, and replay for the bridge."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.geoc_bridge import OUT,OLD,data,local_prediction
from src.calendar_expansion import metric
from src.family_8.research import pair_metrics
from src.winner_delivery import cluster_weights,sampled_metrics,paired_signflip,holm

def main():
    assert (OUT/'execution_complete.json').exists()
    dest=OUT/'diagnostics'
    if dest.exists():raise FileExistsError('Preserve completed diagnostics')
    dest.mkdir();a=data();t=a['train'];p=pd.read_parquet(OUT/'tables/oof_predictions.parquet')
    meta=t[['ID_POLIGONO','Estado','Municipio','climate_profile']];z=p.merge(meta,on='ID_POLIGONO',validate='many_to_one')
    reps=[];regions=[];omissions=[];intra=[];summary=[]
    for (name,pro,re),g in z.groupby(['experiment','protocol','repeat']):
        assert len(g)==(41 if pro=='geoc_target_matched' else 138) and g.ID_POLIGONO.is_unique
        key=dict(experiment=name,protocol=pro,repeat=re)
        reps.append(dict(**key,n=len(g),**metric(g.y_true,g.y_pred)))
        intra.append(dict(**key,**pair_metrics(g)))
        for kind in ['Estado','Municipio','fold']:
            for zone,h in g.groupby(kind):
                regions.append(dict(**key,kind=kind,zone=str(zone),n=len(h),**metric(h.y_true,h.y_pred)))
                remaining=g[g[kind]!=zone]
                if len(remaining)>1:omissions.append(dict(**key,kind=kind,omitted=str(zone),**metric(remaining.y_true,remaining.y_pred)))
    r=pd.DataFrame(reps);r.to_csv(dest/'metrics_by_repeat.csv',index=False)
    for (name,pro),g in z.groupby(['experiment','protocol']):
        repeat=r[(r.experiment==name)&(r.protocol==pro)]
        summary.append(dict(experiment=name,protocol=pro,n_predictions=len(g),unique_parcels=g.ID_POLIGONO.nunique(),n_repeats=g['repeat'].nunique(),**{k+'_mean_repeat':repeat[k].mean() for k in ['rmse','mae','bias','r2']},**{k+'_pooled':v for k,v in metric(g.y_true,g.y_pred).items()}))
    summary=pd.DataFrame(summary);summary.to_csv(dest/'metrics_summary.csv',index=False)
    for name,records,keys in [('regional',regions,['experiment','protocol','kind','zone']),('omissions',omissions,['experiment','protocol','kind','omitted']),('intraprofile',intra,['experiment','protocol'])]:
        d=pd.DataFrame(records);d.to_csv(dest/f'{name}_by_repeat.csv',index=False);d.drop(columns='repeat').groupby(keys).mean(numeric_only=True).reset_index().to_csv(dest/f'{name}_summary.csv',index=False)
    groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO').loc[t.ID_POLIGONO];paired=[];gains=[];complement=[]
    ids=t.ID_POLIGONO.tolist();y=t.RENDIMIENTO_T_HA.to_numpy()
    with threadpool_limits(limits=1):
        for pro,frame in z.groupby('protocol'):
            groupcol={'random':'climate_profile','climate_profile':'climate_profile','municipality':'municipality','spatial':'spatial','geoc_target_matched':'climate_profile'}[pro]
            group=groups[groupcol].to_numpy();weights,nclusters=cluster_weights(group,5000,2026)
            base=frame[frame.experiment.eq('CT3')]
            for name,g in frame.groupby('experiment'):
                if name=='CT3':continue
                j=g.merge(base[['repeat','fold','ID_POLIGONO','y_pred']],on=['repeat','fold','ID_POLIGONO'],suffixes=('','_ref'),validate='one_to_one')
                e=j.y_pred-j.y_true;f=j.y_pred_ref-j.y_true
                j['sse_gain']=f**2-e**2;j['absolute_error_gain']=abs(f)-abs(e);gains.append(j)
                complement.append(dict(experiment=name,protocol=pro,error_correlation=e.corr(f),fraction_improved=float((abs(e)<abs(f)).mean()),opposite_sign_fraction=float((e*f<0).mean())))
                q=j.assign(loss_difference=e**2-f**2).groupby('ID_POLIGONO').loss_difference.sum().reindex(ids,fill_value=0).to_numpy()
                point=float(summary[(summary.experiment==name)&(summary.protocol==pro)].rmse_mean_repeat.iloc[0]-summary[(summary.experiment=='CT3')&(summary.protocol==pro)].rmse_mean_repeat.iloc[0])
                if pro=='geoc_target_matched':
                    aggregate=j.assign(sse=e**2,sse_ref=f**2,n=1).groupby('ID_POLIGONO')[['sse','sse_ref','n']].sum().reindex(ids,fill_value=0)
                    den=weights@aggregate.n.to_numpy();delta=np.sqrt((weights@aggregate.sse.to_numpy())/den)-np.sqrt((weights@aggregate.sse_ref.to_numpy())/den)
                    point=float(np.sqrt(np.mean(e**2))-np.sqrt(np.mean(f**2)));estimand='pooled repeated holdout RMSE'
                else:
                    ma=j.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy();mb=j.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred_ref').reindex(columns=ids).to_numpy()
                    delta=sampled_metrics(y,ma,weights)['rmse']-sampled_metrics(y,mb,weights)['rmse'];estimand='mean complete-repeat OOF RMSE'
                paired.append(dict(experiment=name,reference='CT3',protocol=pro,estimand=estimand,delta_rmse=point,low95=float(np.quantile(delta,.025)),high95=float(np.quantile(delta,.975)),**paired_signflip(q,group)))
    pd.DataFrame(complement).to_csv(dest/'error_complementarity.csv',index=False)
    tests=pd.DataFrame(paired);assert len(tests)==18;tests['p_holm']=holm(tests.p_mse_signflip);tests.to_csv(dest/'paired_cluster_inference.csv',index=False)
    g=pd.concat(gains);g.to_parquet(dest/'parcel_gains.parquet',index=False)
    g.groupby(['experiment','protocol','ID_POLIGONO','Estado','Municipio'])[['sse_gain','absolute_error_gain']].mean().reset_index().to_csv(dest/'parcel_gains_repeat_average.csv',index=False)
    # Original CT3 references must be numerically identical.
    archived=pd.read_parquet(ROOT/'outputs/modeling/compact_ensemble/v1/tables/oof_predictions.parquet');archived=archived[archived.experiment.eq('C-T3')]
    match=p[(p.experiment=='CT3')&(p.protocol!='geoc_target_matched')].merge(archived,on=['protocol','repeat','fold','ID_POLIGONO'],suffixes=('','_ref'),validate='one_to_one');assert len(match)==1794
    ct3delta=float(abs(match.y_pred-match.y_pred_ref).max());assert ct3delta==0
    replay=[];exclusion_checks=0
    with threadpool_limits(limits=1):
        for path in sorted((OUT/'models').glob('original_*.joblib')):
            fi=int(path.stem.split('_')[-1]);pack=joblib.load(path);tr=pack['train_positions'];va=pack['validation_positions'];pos=a['train_global']
            ct=pack['ct3'].predict(t.iloc[va]);loc=local_prediction(a['x'],a['distance'],pos[tr],pos[va],y[tr]);w=pack['blend_local_weight'];amp=pack['residual_amplitude']
            values=dict(CT3=ct,LOCAL04D=loc,FIXED50=(ct+loc)/2,INNER_BLEND=(1-w)*ct+w*loc,RESIDUAL_LOCAL=ct+amp*local_prediction(a['x'],a['distance'],pos[tr],pos[va],pack['residual_targets']) if amp else ct)
            pro,re,fo,*_=joblib.load(OLD/'cache/frozen65_splits.joblib')[fi]
            for name,pred in values.items():
                expected=p[(p.experiment==name)&(p.protocol==pro)&(p['repeat']==re)&(p.fold==fo)].set_index('ID_POLIGONO').loc[t.iloc[va].ID_POLIGONO].y_pred
                error=float(np.max(abs(pred-expected)));assert error==0;replay.append(dict(experiment=name,protocol=pro,repeat=re,fold=fo,max_difference=error))
            for check in pack['ledger']:
                used=set(joblib.load(OLD/'base_cache'/f'{check["base_key"]}.joblib')['registry']['train_ids'])
                excluded=check['residual_target_positions']+check['excluded_external_positions']+check['excluded_inner_positions']
                assert not used&set(t.iloc[excluded].ID_POLIGONO);exclusion_checks+=1
    pd.DataFrame(replay).to_csv(OUT/'audit/new_model_replay.csv',index=False)
    cfg=json.loads((OUT/'frozen_design.json').read_text());assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==h for path,h in cfg['source_sha256'].items())
    (OUT/'manifest.json').write_text(json.dumps(dict(status='complete',n_oof=len(p),original_folds=65,geoc_splits=16,new_predictors_replayed=len(replay),maximum_replay_difference=0.,CT3_reference_max_difference=ct3delta,honest_residual_exclusion_contexts_checked=exclusion_checks,tests_passed=2,source_hashes_preserved=True,no_new_final_predictions=True,GeoC_unchanged=True,statistics='5000 cluster bootstrap; 18 contrasts Holm; exploratory fixed-prediction inference'),indent=2),encoding='utf-8')
    print(summary[['experiment','protocol','rmse_mean_repeat','rmse_pooled','mae_mean_repeat','r2_mean_repeat']].to_string(index=False));print('\nSELECTION');print(pd.read_csv(OUT/'tables/inner_selection.csv').groupby('protocol')[['local_weight','residual_amplitude']].mean().to_string());print('\nTESTS');print(tests[['experiment','protocol','delta_rmse','low95','high95','p_holm']].to_string(index=False))

if __name__=='__main__':main()
