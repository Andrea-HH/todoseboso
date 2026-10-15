"""F6 stage-one gate and only the four predefined conditional ablations."""
import json,time,traceback
from pathlib import Path
import joblib,numpy as np,pandas as pd
from scipy.spatial.distance import cdist
from threadpoolctl import threadpool_limits
from src.family_5.gpr_s1 import execution as prior
from src.family_5 import gpr_evidence_design as design
from .models import TreeModel,GRID,N_TREES,SEED
ROOT=prior.ROOT;ID=prior.ID;TARGET=prior.TARGET
OUT=ROOT/'outputs/modeling/family_6/bagging/v1'
CORE=prior.CORE
SPECS={'F6-00':dict(algorithm='RF',columns=CORE),'F6-01':dict(algorithm='ET',columns=CORE),'F6-02':dict(algorithm='ET',columns=prior.RAIN+[prior.old.c.NDVI]),'F6-03':dict(algorithm='ET',columns=CORE+[prior.old.c.DTR]),'F6-04':dict(algorithm='ET',columns=CORE+design.HISTORY),'F6-05':dict(algorithm='ET',columns=CORE+[design.SLOPE])}

def load():
    _,t,_=design.data();splits=prior.old.c.b.e.f.lm.k.j.load_frozen_splits(t)[0]
    assert len(t)==138 and t[ID].nunique()==138
    return None,t,splits

def prepare():
    if (OUT/'manifest.json').exists():raise FileExistsError('Completed F6 version immutable')
    for name in ['audit','tables','models','checkpoints','figures','report','splits']:(OUT/name).mkdir(parents=True,exist_ok=True)
    m=json.loads((prior.OUT/'manifest.json').read_text())
    protected=pd.read_csv(prior.OUT/'audit/protected_inputs.csv').to_dict('records')+[dict(path=p,sha256=h) for p,h in m['artifacts'].items()]
    protected.append(dict(path=(prior.OUT/'manifest.json').relative_to(ROOT).as_posix(),sha256=design.sha(prior.OUT/'manifest.json')))
    for r in protected:assert design.sha(ROOT/r['path'])==r['sha256'],r['path']
    pd.DataFrame(protected).drop_duplicates('path').to_csv(OUT/'audit/protected_inputs.csv',index=False)
    _,t,splits=load();_,table,groups=prior.old.c.b.e.f.lm.k.j.load_frozen_splits(t)
    table.to_csv(OUT/'splits/outer_and_inner_splits.csv',index=False);groups.to_csv(OUT/'splits/group_memberships.csv')
    refs=pd.read_parquet(prior.old.OUT/'tables/oof_predictions.parquet');refs=refs[refs.experiment.isin(['C-T3','F5-01'])].copy()
    champion=pd.read_parquet(ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization/predictions/oof_predictions.parquet')
    champion=champion[champion.architecture.eq('A_CURRENT_CH_H_T')].copy();champion['experiment']='CHAMPION';champion['protocol']='random'
    gate=[]
    for protocol,repeat,fold,tr,va,inner in splits:
        if protocol!='random':continue
        q=champion[(champion['repeat']==repeat)&(champion.fold==fold)]
        assert set(q[ID])==set(t.iloc[va][ID]);np.testing.assert_allclose(q.set_index(ID).y_true.reindex(t.iloc[va][ID]),t.iloc[va][TARGET],atol=1e-12)
        gate.append(dict(protocol=protocol,repeat=repeat,fold=fold,n=len(q),exact_validation_ids=True,target_max_difference=0.))
    pd.DataFrame(gate).to_csv(OUT/'audit/champion_compatibility.csv',index=False)
    pd.concat([refs,champion[['experiment','protocol','repeat','fold',ID,'y_true','y_pred']]],ignore_index=True).to_parquet(OUT/'tables/reference_oof.parquet',index=False)
    config=dict(experiments=SPECS,first_stage=['F6-00','F6-01'],conditional_stage=['F6-02','F6-03','F6-04','F6-05'],grid=GRID,n_trees=N_TREES,seed=SEED,RF_bootstrap=True,RF_max_samples=.8,ET_bootstrap=False,ET_max_samples=None,selection='mean frozen inner-fold RMSE; rounded10 ties first grid entry; whole training-only pipeline; 8 candidates x4 frozen folds',features='existing ConditionalFeatures train-only median and affine scaling; NDVI scale floor0.05; constants dropped; no territorial predictors; trees fit native targets',aggregation='138 complete OOF per repetition, then mean10 random repeats; fold metrics diagnostic only',continuation=dict(baseline='C-T3',municipal_RMSE_gain_min=.01,max_any_protocol_RMSE_MAE_harm=.01,municipal_improving_folds_min=3,space_omit_each_block_max_RMSE_harm=.01,note='engineering exploratory margins, not statistical or economic superiority; gate may trigger only ET predefined ablations; all later results exploratory on same external folds; no independent confirmation'),trees_stability='fixed384; retrospective prefix128/256/384 predictions only, no adaptive n_estimators; dispersion across trees not prediction intervals',interpretation='training-supported ALE; supported rainfall-NDVI mixed local differences; threshold usage and impurity descriptive, not causal; no Y-based screening',no_final_training=True,no_PRED=True,source_sha={p.relative_to(ROOT).as_posix():design.sha(p) for p in [Path(__file__),Path(__file__).with_name('models.py'),ROOT/'src/family_4/conditional_response.py']})
    path=OUT/'frozen_design.json'
    if path.exists():assert json.loads(path.read_text())==json.loads(json.dumps(config))
    else:path.write_text(json.dumps(config,indent=2),encoding='utf8')
    from .audit import build
    build()
    print('F6 frozen;8 candidates per algorithm;65 folds;Champion comparable only random',flush=True)

def pack_fit(model,name,p,r,f,context,j,a,v,candidate):
    pred=model.predict(v);params=model.parameters();key=dict(experiment=name,protocol=p,repeat=r,fold=f,context=context,inner_index=j,candidate_index=candidate)
    distance=cdist(model.preprocess_.transform(v),model.training_z_).min(axis=1)
    columns=SPECS[name]['columns'];outside=(v[columns].lt(a[columns].min()-1e-10)|v[columns].gt(a[columns].max()+1e-10)).any(axis=1)
    rows=[{**key,ID:pid,'y_true':float(y),'y_pred':float(yhat),'profile_known':bool(v.iloc[i].climate_profile in set(a.climate_profile)),'outside_marginal_support':bool(outside.iloc[i]),'nearest_training_distance_z':float(distance[i]),'training_y_mean':float(a[TARGET].mean())} for i,(pid,y,yhat) in enumerate(zip(v[ID],v[TARGET],pred))]
    registry={**key,**{k:json.dumps(x) if isinstance(x,(dict,list)) else x for k,x in params.items()},'train_ids':json.dumps(a[ID].tolist()),'validation_ids':json.dumps(v[ID].tolist())}
    return dict(predictions=rows,registry=registry)

def fit_fold(index,names):
    _,t,splits=load();p,r,f,tr,va,inner=splits[index];a,v=t.iloc[tr],t.iloc[va]
    with threadpool_limits(limits=1):
        for name in names:
            stem=f'{name}_{p}_{r}_{f}';path=OUT/'checkpoints'/f'{stem}.joblib'
            if path.exists():continue
            tuning=[];allpacks=[];best=None;best_models=None;best_packs=None
            for candidate,params in enumerate(GRID):
                models=[];packs=[];scores=[]
                for j,(it,iv) in enumerate(inner):
                    aa,vv=a.iloc[it],a.iloc[iv];model=TreeModel(SPECS[name]['columns'],SPECS[name]['algorithm'],params).fit(aa,aa[TARGET]);pack=pack_fit(model,name,p,r,f,'inner',j,aa,vv,candidate)
                    models.append(model);packs.append(pack);scores.append(np.sqrt(np.mean([(x['y_pred']-x['y_true'])**2 for x in pack['predictions']])))
                score=float(np.mean(scores));tuning.append(dict(experiment=name,protocol=p,repeat=r,fold=f,candidate_index=candidate,parameters=json.dumps(params),mean_inner_fold_RMSE=score,fold_RMSE=json.dumps(scores)))
                allpacks.extend(packs)
                if best is None or round(score,10)<round(best,10):best=score;best_models=models;best_packs=packs;best_index=candidate
            for j,model in enumerate(best_models):joblib.dump(model,OUT/'models'/f'{stem}_inner_{j}.joblib',compress=3)
            model=TreeModel(SPECS[name]['columns'],SPECS[name]['algorithm'],GRID[best_index]).fit(a,a[TARGET]);outer=pack_fit(model,name,p,r,f,'outer',-1,a,v,best_index)
            prefix=model.prefix_predictions(v)
            for row,i in zip(outer['predictions'],range(len(v))):
                for n in prefix:row[f'prediction_{n}_trees']=float(prefix[n][i])
            for row in tuning:row['selected']=row['candidate_index']==best_index
            for pack in allpacks:pack['registry']['selected']=pack['registry']['candidate_index']==best_index
            outer['registry']['selected']=True
            joblib.dump(model,OUT/'models'/f'{stem}_outer.joblib',compress=3)
            joblib.dump(dict(outer=outer,inner=allpacks,selected_inner=best_packs,tuning=tuning),path,compress=3)
    print(f'F6 {index+1}/65 {p} repeat{r} fold{f} {names}',flush=True)

def collect():
    packs=[joblib.load(path) for path in sorted((OUT/'checkpoints').glob('*.joblib'))]
    outer=pd.DataFrame([r for pack in packs for r in pack['outer']['predictions']]);inner=pd.DataFrame([r for pack in packs for ip in pack['inner'] for r in ip['predictions']])
    selected=pd.DataFrame([r for pack in packs for ip in pack['selected_inner'] for r in ip['predictions']]);tuning=pd.DataFrame([r for pack in packs for r in pack['tuning']])
    reg=pd.DataFrame([pack['outer']['registry'] for pack in packs]+[ip['registry'] for pack in packs for ip in pack['inner']])
    p=pd.concat([pd.read_parquet(OUT/'tables/reference_oof.parquet'),outer],ignore_index=True)
    p.to_parquet(OUT/'tables/oof_predictions.parquet',index=False);inner.to_parquet(OUT/'tables/all_inner_candidates.parquet',index=False);selected.to_parquet(OUT/'tables/inner_oof_predictions.parquet',index=False)
    tuning.to_csv(OUT/'tables/inner_selection.csv',index=False);reg.to_csv(OUT/'tables/fit_registry.csv',index=False)
    return p

def continuation(p):
    from src.family_4.stage_d_evidence import metrics
    from .reporting import metric_summary
    summary=metric_summary(p)[1].set_index(['experiment','protocol']);rows=[]
    for name in ['F6-00','F6-01']:
        gains={protocol:summary.loc[('C-T3',protocol),'RMSE']-summary.loc[(name,protocol),'RMSE'] for protocol in ['random','climate_profile','municipality','spatial']}
        harms=[summary.loc[(name,protocol),metric]-summary.loc[('C-T3',protocol),metric] for protocol in gains for metric in ['RMSE','MAE']]
        improving=0
        for fold in range(1,6):
            a=p[(p.experiment==name)&(p.protocol=='municipality')&(p.fold==fold)];b=p[(p.experiment=='C-T3')&(p.protocol=='municipality')&(p.fold==fold)]
            improving+=metrics(a)['RMSE']<metrics(b)['RMSE']
        omissions=[]
        for fold in range(1,6):
            a=p[(p.experiment==name)&(p.protocol=='spatial')&(p.fold!=fold)];b=p[(p.experiment=='C-T3')&(p.protocol=='spatial')&(p.fold!=fold)]
            omissions.append(metrics(a)['RMSE']-metrics(b)['RMSE'])
        passed=gains['municipality']>=.01 and max(harms)<=.01 and improving>=3 and max(omissions)<=.01
        rows.append(dict(experiment=name,municipal_RMSE_gain=gains['municipality'],max_RMSE_MAE_harm=max(harms),municipal_improving_folds=int(improving),max_space_omission_RMSE_harm=max(omissions),passes=bool(passed)))
    decision=dict(criterion='prospectively frozen exploratory external gate; not independent confirmation',criteria=rows,run_predefined_ablations=any(x['passes'] for x in rows),executed=['F6-00','F6-01'])
    (OUT/'report/continuation_decision.json').write_text(json.dumps(decision,indent=2),encoding='utf8');return decision

def run(workers=3):
    if not (OUT/'frozen_design.json').exists():prepare()
    else:
        cfg=json.loads((OUT/'frozen_design.json').read_text())
        for path,h in cfg['source_sha'].items():assert design.sha(ROOT/path)==h
        if (OUT/'manifest.json').exists():raise FileExistsError('Completed F6 immutable')
    start=time.perf_counter()
    joblib.Parallel(n_jobs=workers,backend='loky',inner_max_num_threads=1)(joblib.delayed(fit_fold)(i,['F6-00','F6-01']) for i in range(65))
    p=collect();decision=continuation(p)
    if decision['run_predefined_ablations']:
        joblib.Parallel(n_jobs=workers,backend='loky',inner_max_num_threads=1)(joblib.delayed(fit_fold)(i,['F6-02','F6-03','F6-04','F6-05']) for i in range(65))
        p=collect();decision['executed']+=['F6-02','F6-03','F6-04','F6-05']
        (OUT/'report/continuation_decision.json').write_text(json.dumps(decision,indent=2),encoding='utf8')
    (OUT/'audit/wall_seconds.txt').write_text(str(time.perf_counter()-start))
    from .reporting import build
    build(p)
