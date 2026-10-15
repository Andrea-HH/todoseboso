"""Metrics and full replay for the exploratory compact spectral comparator."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.calendar_expansion import metric,BASE
from src.calendar_execution import install_single_thread_scoring
from src.family_8.research import pair_metrics
OUT=ROOT/'outputs/modeling/agronomic_calendar/compact_spectral_addendum/v1'

def replay(i):
    install_single_thread_scoring();x=pd.read_parquet(OUT/'cache/features_train138.parquet').set_index('ID_POLIGONO');n=models=0;maximum=0.
    with threadpool_limits(limits=1):
        for f in (OUT/'checkpoints').glob(f'*_{i:02d}.joblib'):
            pack=joblib.load(f);m=joblib.load(OUT/'models'/f.name);ids=m['validation_ids'];assert not set(ids)&set(m['train_ids']) and len(m['train_ids'])<138
            expected=pd.DataFrame(pack['predictions']).set_index('ID_POLIGONO').loc[ids,'y_pred'].to_numpy();actual=m['model'].predict(x.loc[ids]);err=float(np.max(abs(expected-actual)));assert err<1e-10
            maximum=max(maximum,err);n+=len(ids);models+=1
    return models,n,maximum

if __name__=='__main__':
    DEST=OUT/'diagnostics'
    if DEST.exists():raise FileExistsError('Preserve addendum diagnostics')
    DEST.mkdir();p=pd.read_parquet(OUT/'tables/oof_predictions.parquet');meta=pd.read_parquet(BASE/'train138.parquet',columns=['ID_POLIGONO','Estado','Municipio','climate_profile']);z=p.merge(meta,on='ID_POLIGONO',validate='many_to_one')
    reps=[];pairs=[];regions=[];om=[]
    for (name,pro,re),g in z.groupby(['experiment','protocol','repeat']):
        key=dict(experiment=name,protocol=pro,repeat=re);assert len(g)==138 and g.ID_POLIGONO.is_unique
        reps.append(dict(**key,**metric(g.y_true,g.y_pred)));pairs.append(dict(**key,**pair_metrics(g)))
        for kind in ['Estado','Municipio','fold']:
            for zone,h in g.groupby(kind):
                regions.append(dict(**key,kind=kind,zone=zone,n=len(h),**metric(h.y_true,h.y_pred)))
                q=g[g[kind]!=zone]
                if len(q)>1:om.append(dict(**key,kind=kind,omitted=str(zone),**metric(q.y_true,q.y_pred)))
    reps=pd.DataFrame(reps);reps.to_csv(DEST/'metrics_by_repeat.csv',index=False);summary=reps.groupby(['experiment','protocol'])[['rmse','mae','bias','r2']].mean().reset_index();summary.to_csv(DEST/'metrics_summary.csv',index=False)
    pd.DataFrame(pairs).groupby(['experiment','protocol']).mean(numeric_only=True).reset_index().to_csv(DEST/'intraprofile_summary.csv',index=False)
    pd.DataFrame(regions).groupby(['experiment','protocol','kind','zone'])[['n','rmse','mae','bias','r2']].mean().reset_index().to_csv(DEST/'regional_summary.csv',index=False)
    om=pd.DataFrame(om);om.to_csv(DEST/'omission_without_refit.csv',index=False);paired=[];gains=[];omrows=[]
    for name in p.experiment.unique():
        if '_CMP_' not in name:continue
        for ref in [name.split('_')[0]+'_CAL00','C-T3','F7-00']:
            a=reps[reps.experiment.eq(name)].merge(reps[reps.experiment.eq(ref)].drop(columns='experiment'),on=['protocol','repeat'],suffixes=('','_ref'),validate='one_to_one');a['reference']=ref
            for k in ['rmse','mae','bias','r2']:a['delta_'+k]=a[k]-a[k+'_ref']
            paired.append(a[['experiment','reference','protocol','repeat','delta_rmse','delta_mae','delta_bias','delta_r2']])
            b=p[p.experiment.eq(name)].merge(p[p.experiment.eq(ref)].drop(columns=['experiment','algorithm','block']),on=['protocol','repeat','fold','ID_POLIGONO'],suffixes=('','_ref'),validate='one_to_one');np.testing.assert_allclose(b.y_true,b.y_true_ref)
            b['reference']=ref;b['sse_gain']=(b.y_pred_ref-b.y_true)**2-(b.y_pred-b.y_true)**2;b['absolute_error_gain']=abs(b.y_pred_ref-b.y_true)-abs(b.y_pred-b.y_true);gains.append(b)
            o=om[om.experiment.eq(name)].merge(om[om.experiment.eq(ref)].drop(columns='experiment'),on=['protocol','repeat','kind','omitted'],suffixes=('','_ref'),validate='one_to_one');o['reference']=ref;o['delta_rmse']=o.rmse-o.rmse_ref;omrows.append(o[['experiment','reference','protocol','repeat','kind','omitted','delta_rmse']])
    paired=pd.concat(paired);paired.to_csv(DEST/'paired_by_repeat.csv',index=False);paired.groupby(['experiment','reference','protocol'])[['delta_rmse','delta_mae','delta_bias','delta_r2']].mean().reset_index().to_csv(DEST/'paired_summary.csv',index=False)
    pd.concat(omrows).to_csv(DEST/'paired_omissions.csv',index=False)
    g=pd.concat(gains).merge(meta[['ID_POLIGONO','Estado','Municipio']],on='ID_POLIGONO',validate='many_to_one');g.to_parquet(DEST/'parcel_gains.parquet',index=False)
    parcel=g.groupby(['experiment','reference','protocol','ID_POLIGONO','Estado','Municipio'],as_index=False)[['sse_gain','absolute_error_gain']].mean();parcel.to_csv(DEST/'parcel_gain_repeat_average.csv',index=False)
    parcel.groupby(['experiment','reference','protocol','Estado','Municipio']).agg(n=('ID_POLIGONO','size'),sse_gain=('sse_gain','sum'),mean_absolute_error_gain=('absolute_error_gain','mean')).reset_index().to_csv(DEST/'municipal_gain_contributions.csv',index=False)
    usage=pd.read_parquet(OUT/'tables/usage.parquet');usage.groupby(['experiment','protocol','feature']).agg(fraction_selected=('used','mean'),median_effect=('effect_standardized','median'),mean_split_count=('split_count','mean')).reset_index().to_csv(DEST/'feature_selection_stability.csv',index=False)
    registry=pd.read_parquet(OUT/'tables/registry.parquet');registry.groupby(['experiment','protocol']).agg(n_input=('n_input','first'),n_design=('n_design','first'),selected_median=('n_selected','median'),selected_min=('n_selected','min'),selected_max=('n_selected','max')).reset_index().to_csv(DEST/'selection_complexity.csv',index=False)
    full=pd.read_csv(ROOT/'outputs/modeling/agronomic_calendar/expansion/v1/diagnostics/metrics_summary.csv');pd.concat([full,summary[summary.experiment.str.contains('_CMP_')]],ignore_index=True).to_csv(DEST/'combined_metrics_summary.csv',index=False)
    results=joblib.Parallel(n_jobs=4)(joblib.delayed(replay)(i) for i in range(65));audit=dict(models=sum(a[0] for a in results),predictions=sum(a[1] for a in results),max_absolute_difference=max(a[2] for a in results),no_full138_fit=True,no_PRED=True)
    assert audit['models']==390 and audit['predictions']==10764
    cfg=json.loads((OUT/'frozen_design.json').read_text())
    for path,value in cfg['sha256'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==value
    audit['protected_hashes_unchanged']=True;(OUT/'audit/replay.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    print(summary.pivot(index='experiment',columns='protocol',values='rmse').to_string());print(json.dumps(audit,indent=2))
