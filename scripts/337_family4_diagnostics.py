"""Post-fit paired, conditional and provenance audits; no fitting."""
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import joblib
from src.family_4 import conditional_response as f

def main():
    out=f.OUT;d,t=f.load();splits,_,_=f.lm.k.j.load_frozen_splits(t)
    p=pd.read_parquet(out/'tables/errors_with_geography.parquet')
    metrics=pd.read_csv(out/'tables/subgroups_repeat.csv');paired=[]
    for baseline in ['J0_RAIN','K5_RAIN_RESID_SLOPE']:
        ref=metrics[metrics.experiment.eq(baseline)]
        z=metrics[metrics.experiment.isin(f.SPECS)].merge(ref,on=['protocol','repeat','stratum'],suffixes=('','_baseline'),validate='many_to_one')
        for row in z.to_dict('records'):
            paired.append(dict(experiment=row['experiment'],baseline=baseline,protocol=row['protocol'],repeat=row['repeat'],stratum=row['stratum'],delta_RMSE=row['RMSE']-row['RMSE_baseline'],delta_MAE=row['MAE']-row['MAE_baseline']))
    paired=pd.DataFrame(paired);paired.to_csv(out/'tables/paired_repeat.csv',index=False)
    paired.groupby(['experiment','baseline','protocol','stratum']).agg(delta_RMSE=('delta_RMSE','mean'),delta_MAE=('delta_MAE','mean'),fraction_repeats_improving=('delta_RMSE',lambda x:(x<0).mean())).reset_index().to_csv(out/'tables/paired_summary.csv',index=False)
    glob=metrics[metrics.stratum.eq('all')].groupby(['experiment','protocol'])[['RMSE','MAE']].mean()
    base=glob.loc['J0_RAIN'];decisions=[]
    for e in f.SPECS:
        delta=glob.loc[e]-base
        consistent=float((paired[(paired.experiment==e)&(paired.baseline=='J0_RAIN')&(paired.protocol=='random')&(paired.stratum=='all')].delta_RMSE<0).mean())
        decisions.append(dict(experiment=e,random_gain=-delta.loc['random','RMSE'],worst_grouped_rmse_harm=delta.drop('random').RMSE.max(),worst_mae_harm=delta.MAE.max(),fraction_random_repeats_improving=consistent,passes=bool(delta.loc['random','RMSE']<0 and delta.drop('random').RMSE.max()<=.01 and delta.MAE.max()<=.01 and consistent>=.8)))
    pd.DataFrame(decisions).to_csv(out/'tables/operational_decisions.csv',index=False)
    cond=[];effects=[];provenance=[];ref=p[p.experiment.eq('J0_RAIN')]
    for protocol,repeat,fold,tr,va,inner in splits:
        a,b=t.iloc[tr],t.iloc[va]
        full,inside,logs=joblib.load(f.lm.locations('L')[0]/'base_cache'/f'contexts_rain_{protocol}_{repeat}_{fold}.joblib')
        for log in logs:provenance.append(dict(outer_protocol=protocol,outer_repeat=repeat,outer_fold=fold,**log))
        g=p[(p.protocol==protocol)&(p['repeat']==repeat)&(p.fold==fold)].copy()
        baseline=ref[(ref.protocol==protocol)&(ref['repeat']==repeat)&(ref.fold==fold)].set_index(f.ID)
        g['baseline_pred']=g[f.ID].map(baseline.y_pred)
        g['rain_total']=g[f.ID].map(d.set_index(f.ID).rain_total)
        for field,trainvalues,validvalues in [('rain_total',a.rain_total,g.rain_total),('expected_y',full['crossfit'],g.baseline_pred)]:
            edges=np.quantile(trainvalues,[1/3,2/3])
            g[field+'_band']=np.where(validvalues<=edges[0],'low',np.where(validvalues<=edges[1],'middle','high'))
        for e,spec in f.SPECS.items():
            pack=joblib.load(out/'models'/f'{e}_{protocol}_{repeat}_{fold}.joblib');model=pack['model'];train=f.enrich(a,full['crossfit'])
            if spec.get('interaction'):
                target,condition=spec['interaction'];levels=np.quantile(train[condition],[.1,.5,.9]);xs=np.quantile(train[target],[.25,.75])
                for level in levels:
                    z=train.iloc[[0,0]].copy()
                    for c in model['repr'].cols:z[c]=train[c].median()
                    z[target]=xs;z[condition]=level
                    # Applied predicted change across training interquartile target range.
                    change=float(np.diff(model.predict(z))[0])*pack['eta']
                    effects.append(dict(experiment=e,protocol=protocol,repeat=repeat,fold=fold,target=target,condition=condition,condition_value=level,target_q25=xs[0],target_q75=xs[1],predicted_change=change,interaction_enabled=model['repr'].interaction_enabled_))
        for (e,field),z in [( (e,field),g[g.experiment.eq(e)]) for e in g.experiment.unique() for field in ['rain_total_band','expected_y_band']]:
            for band,zz in z.groupby(field):
                cond.append(dict(experiment=e,protocol=protocol,repeat=repeat,fold=fold,field=field,band=band,n=len(zz),sse=float(np.sum((zz.y_pred-zz.y_true)**2)),sae=float(np.sum(abs(zz.y_pred-zz.y_true))),sum_error=float(np.sum(zz.y_pred-zz.y_true))))
    cond=pd.DataFrame(cond)
    cond.to_csv(out/'tables/conditional_fold_sums.csv',index=False)
    z=cond.groupby(['experiment','protocol','repeat','field','band'])[['n','sse','sae','sum_error']].sum().reset_index()
    z['RMSE']=np.sqrt(z.sse/z.n);z['MAE']=z.sae/z.n;z['bias']=z.sum_error/z.n
    z.to_csv(out/'tables/conditional_repeat.csv',index=False)
    z.groupby(['experiment','protocol','field','band'])[['n','RMSE','MAE','bias']].mean().reset_index().to_csv(out/'tables/conditional_summary.csv',index=False)
    pd.DataFrame(effects).to_csv(out/'tables/conditional_effects.csv',index=False)
    pd.DataFrame(provenance).to_csv(out/'tables/crossfit_provenance.csv',index=False)
    # Satellite coverage support from original April-October observations.
    original=pd.read_parquet(f.ROOT/'data/processed/family_1/features/family1_features_all.parquet').set_index(f.ID)
    counts={'April_October':original['S2_ndvi_promedio_n_obs']}
    ts=pd.read_parquet(f.ROOT/'data/processed/family_1/timeseries/sentinel_timeseries.parquet')
    may=ts[ts.fecha_captura.between('2025-05-01','2025-05-31 23:59:59')]
    counts['May']=may.groupby(f.ID).ndvi_promedio.count().reindex(t[f.ID]).fillna(0)
    supportrows=[]
    for protocol,repeat,fold,tr,va,_ in splits:
        for window,count in counts.items():
            cut=np.quantile(count.loc[t.iloc[tr][f.ID]],.25)
            zz=p[(p.protocol==protocol)&(p['repeat']==repeat)&(p.fold==fold)].copy()
            zz['low_support']=zz[f.ID].map(count)<=cut
            for (e,low),g in zz.groupby(['experiment','low_support']):supportrows.append(dict(experiment=e,protocol=protocol,repeat=repeat,fold=fold,window=window,low_support=low,n=len(g),training_count_q25=cut,**f.lm.k.metrics(g.y_true,g.y_pred)))
    os=pd.DataFrame(supportrows);os.to_csv(out/'tables/observation_support_fold.csv',index=False)
    os['sse']=os.RMSE**2*os.n;os['sae']=os.MAE*os.n
    sums=os.groupby(['experiment','protocol','repeat','window','low_support'])[['n','sse','sae']].sum().reset_index()
    sums['RMSE']=np.sqrt(sums.sse/sums.n);sums['MAE']=sums.sae/sums.n
    sums.to_csv(out/'tables/observation_support_repeat.csv',index=False)
    sums.groupby(['experiment','protocol','window','low_support'])[['n','RMSE','MAE']].mean().reset_index().to_csv(out/'tables/observation_support_summary.csv',index=False)
    # Compatible archived Champion: random only, one frozen architecture.
    champion=pd.read_parquet(f.ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization/predictions/oof_predictions.parquet')
    champion=champion[champion.architecture.eq('A_CURRENT_CH_H_T')]
    common=ref[ref.protocol.eq('random')][[f.ID,'repeat','fold','y_true']].merge(champion,on=[f.ID,'repeat','fold'],validate='one_to_one',suffixes=('_ref',''))
    assert len(common)==1380 and np.allclose(common.y_true,common.y_true_ref)
    cm=[dict(repeat=r,**f.lm.k.metrics(z.y_true,z.y_pred)) for r,z in common.groupby('repeat')]
    pd.DataFrame(cm).to_csv(out/'tables/champion_compatible_random.csv',index=False)
    # Pre-existing scientific manifests remain authoritative; verify referenced artifacts.
    protection=[]
    for sec in ['L','M']:
        manifest=json.loads((f.lm.locations(sec)[0]/'manifest.json').read_text())
        for path,sha in manifest['artifacts'].items():
            artifact=f.ROOT/path
            actual=hashlib.sha256(artifact.read_bytes()).hexdigest()
            protection.append(dict(section=sec,path=path,matches=actual==sha))
    assert all(x['matches'] for x in protection)
    pd.DataFrame(protection).to_csv(out/'tables/previous_manifest_integrity.csv',index=False)
    print('Audits complete:',len(protection),'prior artifacts verified; Champion IDs match; nested provenance',len(provenance))
    print(z[z.experiment.isin(['J0_RAIN','F4-S2','F4-C'])].groupby(['experiment','protocol','field','band']).RMSE.mean().round(4).to_string())

if __name__=='__main__':main()
