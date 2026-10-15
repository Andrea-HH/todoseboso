"""Frozen 65-fold nested comparison: 2025 representations and penalized history."""
from pathlib import Path
import sys,json,time,hashlib,warnings
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
from sklearn.metrics import r2_score
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.calendar_modeling import CalendarRidge
from src.family_8.research import pair_metrics
OUT=ROOT/'outputs/modeling/agronomic_calendar/v1'
OLD=ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache'
DATA=ROOT/'data/processed/agronomic_calendar_set/v1/current_history_delta_197_target_free.parquet'
REF=ROOT/'outputs/modeling/compact_ensemble/v1/tables/oof_predictions.parquet'
CORE=['compact_precip_total','compact_early_fraction','compact_concentration_hhi','S2_ndvi_month_05']
W=['pre_apr','sowing_may_jun','post_jul_aug','late_sep_oct']
RAIN=['CURRENT_CAL_CLIM_precip_'+w for w in W]
TEMP=['CURRENT_CAL_CLIM_tmax_'+w for w in W]
SAT=['CAL_S2_ndvi_'+w for w in W]+['CAL_S2_ndvi_spatial_std_post_jul_aug']
CUR=['CURRENT_'+s for s in SAT]
HIST=['HIST_MEAN_'+s for s in SAT]+['HIST_SD_'+s for s in SAT]
DELTA=['DELTA_'+s for s in SAT]+['HIST_SD_'+s for s in SAT]
JOINT=RAIN+TEMP+[CORE[-1]]+CUR
SPECS={
 'CAL00':dict(columns=CORE,history=[],description='compact4 Ridge architecture control'),
 'CAL01':dict(columns=RAIN+[CORE[-1]],history=[],description='rain windows + original MayNDVI'),
 'CAL02':dict(columns=RAIN+TEMP+[CORE[-1]],history=[],description='rain/Tmax windows + original MayNDVI'),
 'CAL03':dict(columns=CORE+CUR,history=[],description='compact4 + Sentinel2025 trajectory/heterogeneity'),
 'CAL04':dict(columns=JOINT,history=[],description='joint current2025 windows'),
 'CAL05':dict(columns=JOINT+HIST,history=HIST,indicators=True,description='joint2025 + history mean/SD, missingness indicators'),
 'CAL06':dict(columns=JOINT+DELTA,history=DELTA,indicators=True,description='joint2025 + deviations/SD, missingness indicators'),
 'CAL07':dict(columns=JOINT+HIST,history=HIST,indicators=False,description='CAL05 without missingness indicators')}
ALPHAS=[100.,10.,1.,.1,.01,.001];GAMMAS=[.25,.5,1.]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def metric(y,p):
    e=np.asarray(p)-np.asarray(y)
    return dict(rmse=float(np.sqrt(np.mean(e**2))),mae=float(np.mean(abs(e))),bias=float(e.mean()),r2=float(r2_score(y,p)) if len(y)>1 else np.nan)
def run():
    start=time.perf_counter()
    if (OUT/'manifest.json').exists():raise FileExistsError('Preserve completed version')
    for sub in ['tables','models','checkpoints','audit']:(OUT/sub).mkdir(parents=True,exist_ok=True)
    protected=[DATA,OLD/'train138.parquet',OLD/'frozen65_splits.joblib',REF,Path(__file__),ROOT/'src/calendar_modeling.py']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in protected}
    design=dict(specs=SPECS,alphas=ALPHAS,gammas=GAMMAS,algorithm='Ridge, alpha_sklearn = alpha*n_training, minimizes MSE + alpha*sum(beta²)',selection='complete original inner OOF RMSE, ties rounded12 prefer larger alpha then smaller gamma',preprocessing='training median with allmissing fallback0; training StandardScaler; history multiplied by gamma after scaling; fixed history missing flags optionally included and penalized with history',outer_folds=65,history_selection='gamma selected within original inner folds; never by external spatial outcomes',no_champion_change=True,no_final_fit=True,no_PRED=True,reference='archived C-T3; CAL00 isolates Ridge architecture from EN C-T3',decision='exploratory reused labels; prioritize geographic and intraprofile stability; no automatic promotion or CatBoost execution',sha256=hashes)
    path=OUT/'frozen_design.json'
    if path.exists():assert json.loads(path.read_text())==design
    else:path.write_text(json.dumps(design,indent=2),encoding='utf-8')
    t=pd.read_parquet(OLD/'train138.parquet');x=pd.read_parquet(DATA).set_index('ID_POLIGONO').reindex(t.ID_POLIGONO).reset_index()
    for col in CORE:x[col]=t[col].to_numpy()
    assert x.ID_POLIGONO.tolist()==t.ID_POLIGONO.tolist()
    y=t.RENDIMIENTO_T_HA.to_numpy();splits=joblib.load(OLD/'frozen65_splits.joblib');assert len(splits)==65
    fit_count=0
    with threadpool_limits(limits=1):
        for fi,(protocol,repeat,fold,tr,va,inner) in enumerate(splits):
            checkpoint=OUT/'checkpoints'/f'{fi:02d}.joblib'
            if checkpoint.exists():continue
            assert not set(tr)&set(va) and set(tr)|set(va)==set(range(138))
            records=[];tuning=[];registry=[];coefs=[];logs=[]
            for name,spec in SPECS.items():
                candidates=[]
                for alpha in ALPHAS:
                    for gamma in (GAMMAS if spec['history'] else [1.]):
                        pred=np.full(len(tr),np.nan);seen=np.zeros(len(tr),int)
                        for a,b in inner:
                            assert not set(a)&set(b) and max(max(a),max(b))<len(tr)
                            model=CalendarRidge(spec['columns'],spec['history'],alpha,gamma,spec.get('indicators',False))
                            with warnings.catch_warnings(record=True) as ww:
                                warnings.simplefilter('always');model.fit(x.iloc[tr[a]],y[tr[a]]);pred[b]=model.predict(x.iloc[tr[b]])
                            logs.extend(str(w.message) for w in ww);fit_count+=1;seen[b]+=1
                        assert (seen==1).all() and np.isfinite(pred).all()
                        candidates.append(dict(alpha=alpha,gamma=gamma,**metric(y[tr],pred)))
                best=min(candidates,key=lambda a:(round(a['rmse'],12),-a['alpha'],a['gamma']))
                model=CalendarRidge(spec['columns'],spec['history'],best['alpha'],best['gamma'],spec.get('indicators',False)).fit(x.iloc[tr],y[tr]);fit_count+=1
                prediction=model.predict(x.iloc[va]);assert np.isfinite(prediction).all()
                key=dict(experiment=name,protocol=protocol,repeat=repeat,fold=fold)
                records.extend(dict(**key,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(p)) for i,p in zip(va,prediction))
                tuning.extend(dict(**key,**a,selected=a is best) for a in candidates)
                registry.append(dict(**key,n_train=len(tr),n_input=len(spec['columns']),n_design=len(model.feature_names_),effective_df=model.effective_df_,alpha=best['alpha'],gamma=best['gamma'],inner_rmse=best['rmse']))
                coefs.extend(dict(**key,feature=f,coefficient=float(v),unweighted_standardized_coefficient=float(v*w)) for f,v,w in zip(model.feature_names_,model.model_.coef_,model.weights_))
                joblib.dump(dict(model=model,train_ids=t.iloc[tr].ID_POLIGONO.tolist(),validation_ids=t.iloc[va].ID_POLIGONO.tolist(),registry=registry[-1]),OUT/'models'/f'{name}_{fi:02d}.joblib',compress=3)
            joblib.dump(dict(predictions=records,tuning=tuning,registry=registry,coefficients=coefs,warnings=logs),checkpoint,compress=3)
            print(f'{fi+1}/65 {protocol} repeat{repeat} fold{fold}',flush=True)
    packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(65)]
    for key in ['tuning','registry','coefficients']:
        pd.DataFrame([r for pack in packs for r in pack[key]]).to_csv(OUT/'tables'/f'{key}.csv',index=False)
    p=pd.DataFrame([r for pack in packs for r in pack['predictions']]);assert len(p)==8*1794
    ref=pd.read_parquet(REF);ref=ref[ref.experiment.eq('C-T3')].copy()
    for (pro,re,fold),g in ref.groupby(['protocol','repeat','fold']):
        allowed=next(t.iloc[v].ID_POLIGONO.tolist() for pp,rr,ff,tr,v,ins in splits if (pp,rr,ff)==(pro,re,fold))
        assert set(g.ID_POLIGONO)==set(allowed)
        np.testing.assert_allclose(g.y_true,t.set_index('ID_POLIGONO').loc[g.ID_POLIGONO,'RENDIMIENTO_T_HA'])
    p=pd.concat([ref,p],ignore_index=True);p.to_parquet(OUT/'tables/oof_predictions.parquet',index=False);p.to_csv(OUT/'tables/oof_predictions.csv',index=False)
    meta=t[['ID_POLIGONO','Estado','Municipio','climate_profile']]
    full=p.merge(meta,on='ID_POLIGONO',validate='many_to_one');reps=[];pairs=[];regions=[];omissions=[]
    for (name,pro,re),g in full.groupby(['experiment','protocol','repeat']):
        key=dict(experiment=name,protocol=pro,repeat=re);assert len(g)==138 and g.ID_POLIGONO.is_unique
        reps.append(dict(**key,**metric(g.y_true,g.y_pred)));pairs.append(dict(**key,**pair_metrics(g)))
        for kind in ['Estado','Municipio','fold']:
            for zone,h in g.groupby(kind):
                regions.append(dict(**key,kind=kind,zone=zone,n=len(h),**metric(h.y_true,h.y_pred)))
                q=g[g[kind]!=zone]
                if len(q)>1:omissions.append(dict(**key,kind=kind,omitted=zone,n=len(q),**metric(q.y_true,q.y_pred)))
    reps=pd.DataFrame(reps);reps.to_csv(OUT/'tables/metrics_by_repeat.csv',index=False)
    summary=reps.groupby(['experiment','protocol'])[['rmse','mae','bias','r2']].mean().reset_index();summary.to_csv(OUT/'tables/metrics_summary.csv',index=False)
    pd.DataFrame(pairs).to_csv(OUT/'tables/intraprofile_by_repeat.csv',index=False)
    pd.DataFrame(regions).to_csv(OUT/'tables/regional_by_repeat.csv',index=False)
    pd.DataFrame(omissions).to_csv(OUT/'tables/omission_without_refit.csv',index=False)
    gains=[]
    for reference in ['C-T3','CAL00','CAL04','CAL05']:
        base=p[p.experiment.eq(reference)].drop(columns='experiment')
        j=p[p.experiment.ne(reference)].merge(base,on=['protocol','repeat','fold','ID_POLIGONO'],suffixes=('','_ref'),validate='many_to_one')
        np.testing.assert_allclose(j.y_true,j.y_true_ref)
        j['reference']=reference;j['sse_gain']=(j.y_pred_ref-j.y_true)**2-(j.y_pred-j.y_true)**2;j['absolute_error_gain']=abs(j.y_pred_ref-j.y_true)-abs(j.y_pred-j.y_true)
        gains.append(j)
    gains=pd.concat(gains,ignore_index=True);gains.to_parquet(OUT/'tables/parcel_gains.parquet',index=False)
    paired=[]
    for reference in ['C-T3','CAL00','CAL04','CAL05']:
        j=reps[reps.experiment.ne(reference)].merge(reps[reps.experiment.eq(reference)].drop(columns='experiment'),on=['protocol','repeat'],suffixes=('','_ref'))
        for _,r in j.iterrows():paired.append(dict(experiment=r.experiment,reference=reference,protocol=r.protocol,repeat=r['repeat'],**{'delta_'+k:r[k]-r[k+'_ref'] for k in ['rmse','mae','bias','r2']}))
    pd.DataFrame(paired).to_csv(OUT/'tables/paired_by_repeat.csv',index=False)
    after={str(p.relative_to(ROOT)):sha(p) for p in protected};assert hashes==after
    (OUT/'audit/protected_inputs.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    (OUT/'manifest.json').write_text(json.dumps(dict(status='complete',experiments=list(SPECS),outer_folds=65,outer_models=520,new_fits_this_invocation=fit_count,seconds=time.perf_counter()-start,warnings=[w for pack in packs for w in pack['warnings']],no_final_fit138=True,no_PRED=True,all_protected_hashes_unchanged=True),indent=2),encoding='utf-8')
    print(summary.pivot(index='experiment',columns='protocol',values='rmse').to_string())
if __name__=='__main__':run()
