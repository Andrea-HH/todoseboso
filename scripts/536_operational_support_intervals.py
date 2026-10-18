"""Freeze delivery, isolated replay, target-free support and honest split intervals."""
from pathlib import Path
import os
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[name]='1'
import argparse
import hashlib
import json
import subprocess
import venv
import numpy as np
import pandas as pd

OUT=ROOT/'outputs/research/four_final_checks/v1'
PUB=ROOT/'results/four_final_checks/v1'
FINAL=ROOT/'outputs/modeling/current_champions_final/v1'


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def operational():
    files=['final_train138.joblib','features197.parquet','distance197.npy','Reference26_predictions59.csv','Compact14_predictions59.csv','predictions59_comparison.csv']
    path=OUT/'delivery_snapshot.json'
    values={name:sha(FINAL/name) for name in files}
    if path.exists():assert json.loads(path.read_text(encoding='utf-8'))['files']==values,'Frozen delivery changed'
    else:dump(path,dict(files=values,models=['Reference26','Compact14'],purpose='Read-only immutable delivery snapshot'))
    complete=[]
    reference=pd.read_csv(FINAL/'predictions59_comparison.csv')
    for name in ['Reference26','Compact14']:
        a=pd.read_csv(FINAL/(name+'_predictions59.csv'))
        assert len(a)==59 and a.ID_POLIGONO.is_unique
        assert set(a.ID_POLIGONO)==set(reference.ID_POLIGONO)
        assert np.isfinite(a.RENDIMIENTO_T_HA).all() and (a.RENDIMIENTO_T_HA>0).all()
        check=reference.merge(a,on='ID_POLIGONO',validate='one_to_one')
        np.testing.assert_allclose(check[name+'_t_ha'],check.RENDIMIENTO_T_HA,rtol=0,atol=1e-12)
        destination=OUT/'submission';destination.mkdir(parents=True,exist_ok=True)
        a.rename(columns={'ID_POLIGONO':'ID_parcela'}).to_csv(destination/(name+'_FIRA59.csv'),index=False)
        complete.append(dict(model=name,n=59,unique_IDs=True,same_expected_IDs=True,finite_positive=True,comparison_parity=True))
    envdir=OUT/'isolated_replay_env'
    if not (envdir/'Scripts/python.exe').exists():venv.EnvBuilder(system_site_packages=True,with_pip=False).create(envdir)
    command=[str((envdir/'Scripts/python.exe').resolve()),str(Path(__file__).resolve()),'replay']
    result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
    (OUT/'isolated_replay_stdout.txt').write_text(result.stdout,encoding='utf-8')
    (OUT/'isolated_replay_stderr.txt').write_text(result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError('Isolated replay failed: '+result.stderr[-3000:])
    assert {name:sha(FINAL/name) for name in files}==values
    dump(PUB/'operational_audit.json',dict(delivery_files=values,file_checks=complete,isolated_process_exit=result.returncode,isolated_replay=json.loads((OUT/'isolated_replay.json').read_text(encoding='utf-8')),
        original_files_unchanged=True,private_submission_files='outputs/research/four_final_checks/v1/submission',
        limitation='Isolated venv and fresh process reuse installed package versions via system_site_packages; not an independent OS or clean dependency installation. No automatic submission.'))
    print('Operational freeze,59-ID checks and isolated replay passed.',flush=True)


def replay():
    import joblib
    from threadpoolctl import threadpool_limits
    from src.current_champions import predict_saved
    allowed=[FINAL.resolve(),OUT.resolve()]
    def guard(event,args):
        if event!='open' or not args or isinstance(args[0],int):return
        try:p=Path(os.fsdecode(args[0])).resolve()
        except (TypeError,ValueError,OSError):return
        restricted=[(ROOT/'data').resolve(),(ROOT/'outputs').resolve(),(ROOT.parent/'fira/GeoC').resolve()]
        if any(p.is_relative_to(r) for r in restricted) and not any(p.is_relative_to(r) for r in allowed):raise RuntimeError('Replay escaped final bundle: '+str(p))
    sys.addaudithook(guard)
    pack=joblib.load(FINAL/'final_train138.joblib');frame=pd.read_parquet(FINAL/'features197.parquet');distance=np.load(FINAL/'distance197.npy')
    assert frame.iloc[138:].RENDIMIENTO_T_HA.isna().all()
    with threadpool_limits(limits=1):values=predict_saved(pack,np.arange(138,197),frame,distance)
    checks={}
    for name in ['Reference26','Compact14']:
        old=pd.read_csv(FINAL/(name+'_predictions59.csv')).set_index('ID_POLIGONO').loc[frame.iloc[138:].ID_POLIGONO].RENDIMIENTO_T_HA.to_numpy()
        error=float(np.max(abs(values[name]-old)));assert error<1e-10;checks[name]=error
    from importlib import metadata
    mapping=metadata.packages_distributions();packages={}
    for name,module in list(sys.modules.items()):
        path=str(getattr(module,'__file__','') or '')
        if 'site-packages' not in path:continue
        for distribution in mapping.get(name.split('.')[0],[]):packages[distribution]=metadata.version(distribution)
    dump(OUT/'isolated_replay.json',dict(status='passed',max_difference=checks,python=sys.version,executable=sys.executable,restricted_private_file_IO=True,no_refitting=True,imported_distributions=packages))


def nearest_features(train,query,columns):
    x=train[columns].to_numpy(float);q=query[columns].to_numpy(float)
    med=np.nanmedian(x,axis=0);med=np.where(np.isfinite(med),med,0)
    x=np.where(np.isfinite(x),x,med);q=np.where(np.isfinite(q),q,med)
    mean=x.mean(axis=0);scale=x.std(axis=0);valid=scale>1e-10
    x=((x-mean)/np.maximum(scale,1e-8))[:,valid];q=((q-mean)/np.maximum(scale,1e-8))[:,valid]
    dd=np.sqrt(np.sum((x[:,None,:]-x[None,:,:])**2,axis=2));np.fill_diagonal(dd,np.inf)
    reference=dd.min(axis=1);distance=np.sqrt(np.sum((q[:,None,:]-x[None,:,:])**2,axis=2)).min(axis=1)
    return distance,float(np.quantile(reference,.95))


def support():
    from src.current_champions import LOCAL7
    from src.ct3_residual_conditional.models import CORE
    frame=pd.read_parquet(FINAL/'features197.parquet');train=frame.iloc[:138];query=frame.iloc[138:]
    distance=np.load(FINAL/'distance197.npy');pred=pd.read_csv(FINAL/'predictions59_comparison.csv')
    assert query.ID_POLIGONO.tolist()==pred.ID_POLIGONO.tolist()
    d=distance[:138,:138].copy();np.fill_diagonal(d,np.inf)
    reference=np.sort(d,axis=1)[:,:24];qd=np.sort(distance[138:,:138],axis=1)[:,:24]
    result=pred[['ID_POLIGONO','Estado','Municipio']].copy()
    result['nearest_normalized_distance']=qd[:,0];result['mean24_normalized_distance']=qd.mean(axis=1)
    result['geo_q95_training_threshold']=np.quantile(reference.mean(axis=1),.95)
    result['geo_above_training_q95']=result.mean24_normalized_distance>result.geo_q95_training_threshold
    r3=['I_history_ndvi_floor','I_gap_excess_persistence','I_slope_min']
    result['missing_R3']=~np.isfinite(query[r3].to_numpy(float)).all(axis=1)
    for name,columns in [('core4',list(CORE)),('local7',LOCAL7)]:
        values,threshold=nearest_features(train,query,columns)
        result[name+'_nearest_feature_distance']=values;result[name+'_q95_training_threshold']=threshold;result[name+'_above_training_q95']=values>threshold
        result[name+'_missing_count']=query[columns].isna().sum(axis=1).to_numpy()
    geology=[c for c in train if c.startswith('geology_physiography::')]
    novel=train[geology].max(axis=0)<=1e-12
    result['unseen_geology_share']=query[geology].loc[:,novel].sum(axis=1).to_numpy() if novel.any() else 0.
    result['unseen_geology']=result.unseen_geology_share>1e-10
    result['outside_training_range_count']=np.sum((query[train.columns[5:]].to_numpy(float)<np.nanmin(train.iloc[:,5:].to_numpy(float),axis=0))|(query[train.columns[5:]].to_numpy(float)>np.nanmax(train.iloc[:,5:].to_numpy(float),axis=0)),axis=1)
    expected=pd.read_parquet(ROOT/'data/processed/current_champions/v1/expected_oof.parquet')
    rr=expected[(expected.protocol=='random')&expected.experiment.isin(['Reference26','Compact14'])].pivot(index=['repeat','ID_POLIGONO'],columns='experiment',values='y_pred')
    disagreement=abs(rr.Reference26-rr.Compact14).groupby('ID_POLIGONO').mean()
    result['abs_26_minus14']=abs(pred.Reference26_t_ha-pred.Compact14_t_ha)
    threshold=float(disagreement.quantile(.95));result['disagreement_q95_OOF_threshold']=threshold;result['disagreement_above_OOF_q95']=result.abs_26_minus14>threshold
    flags=['missing_R3','geo_above_training_q95','core4_above_training_q95','local7_above_training_q95','unseen_geology','disagreement_above_OOF_q95']
    result['diagnostic_flag_count']=result[flags].sum(axis=1)
    result.to_csv(OUT/'support59.csv',index=False)
    summaries=[]
    for name,g in [('all',result)]+list(result.groupby('Estado')):
        summaries.append(dict(region=name,n=len(g),**{c:int(g[c].sum()) for c in flags},any_flag=int((g.diagnostic_flag_count>0).sum()),median_nearest_distance=float(g.nearest_normalized_distance.median()),median_abs_26_minus14=float(g.abs_26_minus14.median())))
    pd.DataFrame(summaries).to_csv(PUB/'support_summary.csv',index=False)
    dump(PUB/'support_audit.json',dict(n=59,R3_complete=int((~result.missing_R3).sum()),target_used=False,thresholds='Training-only LOO q95 for geometry/features; known-parcel mean random OOF disagreement q95; descriptive not calibrated error risk',flags=flags,
        final_predictions_changed=False,imputed_feature_distances='Missingness reported separately; no prediction interval inferred from distance'))
    print(pd.DataFrame(summaries).to_string(index=False),flush=True)


def conformal_radius(scores,level):
    scores=np.asarray(scores,float);assert np.isfinite(scores).all()
    k=int(np.ceil((len(scores)+1)*level-1e-12))
    return float(np.partition(scores,k-1)[k-1]) if 1<=k<=len(scores) else np.inf


def intervals():
    expected=pd.read_parquet(ROOT/'data/processed/current_champions/v1/expected_oof.parquet')
    frame=pd.read_parquet(ROOT/'data/processed/current_champions/v1/train138.parquet').set_index('ID_POLIGONO')
    plan=json.loads((ROOT/'data/processed/current_champions/v1/splits.json').read_text(encoding='utf-8'))['folds']
    rows=[];ledger=[]
    for ix,record in enumerate(plan):
        subset=expected[(expected.execution_index==ix)&expected.experiment.isin(['Reference26','Compact14'])]
        anchor=subset[subset.experiment=='Reference26'].sort_values('ID_POLIGONO')
        ids=anchor.ID_POLIGONO.to_numpy();profiles=frame.loc[ids].climate_profile.to_numpy()
        rng=np.random.default_rng(2026+ix)
        order=rng.permutation(len(ids));half=len(ids)//2
        parcel=[order[:half],order[half:]]
        unique=np.unique(profiles);ordergroup=rng.permutation(unique);group_half=len(unique)//2
        grouped=[np.flatnonzero(np.isin(profiles,ordergroup[:group_half])),np.flatnonzero(np.isin(profiles,ordergroup[group_half:]))]
        for strategy,parts in [('parcel_split',parcel),('profile_group_split',grouped)]:
            for orientation in [0,1]:
                cal=parts[orientation];test=parts[1-orientation]
                if not len(test):continue
                assert not set(cal)&set(test)
                for model in ['Reference26','Compact14']:
                    values=subset[subset.experiment==model].set_index('ID_POLIGONO').loc[ids]
                    errors=abs(values.y_true.to_numpy()-values.y_pred.to_numpy())
                    scores=errors[cal]
                    if strategy=='profile_group_split':scores=pd.Series(scores,index=profiles[cal]).groupby(level=0).max().to_numpy()
                    for level in [.8,.9]:
                        radius=conformal_radius(scores,level)
                        ledger.append(dict(fold=ix,model=model,strategy=strategy,orientation=orientation,level=level,n_calibration_parcels=len(cal),n_calibration_units=len(scores),n_evaluation=len(test),radius=radius,disjoint=True))
                        for i in test:
                            a=frame.loc[ids[i]];truth=float(values.iloc[i].y_true);prediction=float(values.iloc[i].y_pred)
                            rows.append(dict(execution_index=ix,protocol=record['protocol'],repeat=record['repeat'],fold=record['fold'],model=model,strategy=strategy,level=level,ID_POLIGONO=ids[i],Estado=a.Estado,Municipio=a.Municipio,y_true=truth,y_pred=prediction,radius=radius,finite=bool(np.isfinite(radius)),covered=bool(abs(truth-prediction)<=radius+1e-12),width=2*radius,n_calibration_units=len(scores)))
    result=pd.DataFrame(rows);result.to_parquet(OUT/'interval_assessment.parquet',index=False)
    pd.DataFrame(ledger).to_csv(OUT/'interval_calibration_ledger.csv',index=False)
    groups=['protocol','repeat','model','strategy','level']
    def describe(g):
        finite=g[g.finite]
        return dict(n=len(g),coverage=g.covered.mean(),finite_fraction=g.finite.mean(),coverage_finite=finite.covered.mean() if len(finite) else np.nan,mean_width_finite=finite.width.mean() if len(finite) else np.nan,median_width_finite=finite.width.median() if len(finite) else np.nan)
    byrepeat=pd.DataFrame([dict(zip(groups,key),**describe(g)) for key,g in result.groupby(groups)])
    byrepeat.to_csv(PUB/'interval_metrics_by_repeat.csv',index=False)
    summary=byrepeat.drop(columns='repeat').groupby(['protocol','model','strategy','level'],as_index=False).mean(numeric_only=True)
    summary.to_csv(PUB/'interval_metrics.csv',index=False)
    regions=[]
    for key,g in result.groupby(groups+['Estado']):regions.append(dict(zip(groups+['Estado'],key),**describe(g)))
    region=pd.DataFrame(regions).drop(columns='repeat').groupby(['protocol','model','strategy','level','Estado'],as_index=False).mean(numeric_only=True)
    region.to_csv(PUB/'interval_metrics_by_state.csv',index=False)
    # Simple finite-sample boundary and leakage guards for the quantile routine.
    assert np.isinf(conformal_radius(np.arange(8.),.9))
    assert conformal_radius(np.arange(9.),.9)==8.
    assert conformal_radius(np.array([.1,.3,.2,.4,.5,.6,.7,.8,.9]),.8)==.8
    dump(PUB/'interval_audit.json',dict(n_rows=len(result),models=['Reference26','Compact14'],levels=[.8,.9],primary='random parcel_split; group-split diagnostic with group maxima',
        own_evaluation_labels_used_for_calibration=False,all_inner_halves_disjoint=True,
        point_model_selection='Frozen before interval experiment; no tuning on coverage or width',
        grouped_protocol_limit='Municipal/spatial heldout folds are split to calibrate/evaluate; calibration sees some labels of excluded territory. This is not strict territorial prediction with no labels there.',
        exchangeability_limit='Empirical OOF coverage after historical model selection; no formal guarantee of future/conditional/state coverage. Infinite intervals retained when insufficient calibration units.',
        no_final138_interval_claim=True,no_59_targets_read=True,new_model_training=False))
    print(summary[(summary.level==.9)&(summary.strategy=='parcel_split')].to_string(index=False),flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['operational','replay','support','intervals']);args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);PUB.mkdir(parents=True,exist_ok=True)
    globals()[args.command]()


if __name__=='__main__':main()
