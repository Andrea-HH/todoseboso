"""Five-model controlled experiment, strict recursive tuning and cached contexts."""
from pathlib import Path
import json,time,hashlib,platform
import joblib,numpy as np,pandas as pd
from threadpoolctl import threadpool_limits
from src.family_8.research import subcv
from .models import CORE,LAI,Z,SPECS,BASE_GRID,AMPLITUDES,tune_base,CenteredCorrector,selection_key

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/modeling/ct3_residual_conditional/v1'
ID='ID_POLIGONO';TARGET='RENDIMIENTO_T_HA'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load():
    t=pd.read_parquet(OUT/'cache/train138.parquet');splits=joblib.load(OUT/'cache/frozen65_splits.joblib');groups=pd.read_csv(OUT/'cache/groups.csv').set_index(ID)
    return t,splits,groups
def cv_list(cv):return [(np.asarray(a,dtype=int),np.asarray(b,dtype=int)) for a,b in cv]
def signature(pos,cv,protocol):
    payload=dict(pos=np.asarray(pos,dtype=int).tolist(),cv=[(a.tolist(),b.tolist()) for a,b in cv_list(cv)],protocol=protocol,grid=BASE_GRID,features=CORE)
    return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()[:24]

def prepare():
    if OUT.exists():raise FileExistsError('Output exists; completed/partial versions are preserved')
    for d in ['cache','base_cache','models','checkpoints','tables','audit','figures','report']:(OUT/d).mkdir(parents=True,exist_ok=True)
    protected=[]
    def readpath(p):
        p=ROOT/p;protected.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)));return p
    t=pd.read_parquet(readpath('outputs/modeling/family_7/boosting/v1/cache/train138_exact_features.parquet'))
    features=pd.read_parquet(readpath('data/processed/family_1/features/family1_features_all.parquet'),columns=[ID,LAI])
    t=t.merge(features,on=ID,validate='one_to_one');t=t[[ID,TARGET,'climate_profile','Municipio','Estado']+CORE+[LAI]]
    assert len(t)==138 and t[ID].is_unique and np.isfinite(t[CORE+[LAI,TARGET]].to_numpy(float)).all()
    splits=joblib.load(readpath('outputs/modeling/family_7/boosting/v1/cache/frozen65_splits.joblib'))
    groups=pd.read_csv(readpath('outputs/modeling/family_7/boosting/v1/splits/group_memberships.csv')).set_index(ID).reindex(t[ID])
    reference=pd.read_parquet(readpath('outputs/research/family_4/territorial_intraprofile_program/v1/stage_c/tables/oof_predictions.parquet'));reference=reference[reference.experiment.eq('C-T3')].copy()
    assert len(splits)==65 and len(reference)==1794
    for path in ['documentation/family8_nested_crossfitting.md','documentation/family8_experimental_design.md','documentation/family4_e_decision_summary.md','documentation/territorial_program_stage_b_decision.md','documentation/territorial_program_stage_c_decision.md','documentation/family7_expansion.md','documentation/ct3_incremental_information_findings.md','outputs/research/ct3_incremental_information/phase_iii/v2/manifest.json','outputs/research/family_8/residual_design/v1/manifest.json']:readpath(path)
    source_temporal='outputs/research/ct3_incremental_information/phase_iii/v2/audit/'
    for f in ['temporal_sensitivity.csv','temporal_coverage.csv']:
        d=pd.read_csv(readpath(source_temporal+f));d[d[ID].isin(t[ID])].to_csv(OUT/'cache'/f,index=False)
    contexts={};plans=[];gates=[]
    def context(pos,cv,p,role,external_model=None):
        pos=np.asarray(pos,dtype=int);cv=cv_list(cv);key=signature(pos,cv,p)
        if key not in contexts:contexts[key]=dict(key=key,positions=pos,cv=cv,protocol=p,role=role,external_model=external_model)
        for a,b in cv:
            assert not set(a)&set(b) and set(a)|set(b)==set(range(len(pos)))
            if p!='random':assert not set(groups.iloc[pos[a]][p])&set(groups.iloc[pos[b]][p])
        return key
    for i,(p,r,f,tr,va,inner) in enumerate(splits):
        tr=np.asarray(tr);va=np.asarray(va);assert not set(tr)&set(va) and set(tr)|set(va)==set(range(138))
        modelpath=readpath(f'outputs/research/family_4/territorial_intraprofile_program/v1/stage_c/models/C-T3_{p}_{r}_{f}.joblib')
        model=joblib.load(modelpath);q=reference[(reference.protocol==p)&(reference['repeat']==r)&(reference.fold==f)].set_index(ID)
        assert set(q.index)==set(t.iloc[va][ID]);np.testing.assert_allclose(q.y_true.reindex(t.iloc[va][ID]),t.iloc[va][TARGET],atol=1e-12)
        prediction=model.predict(t.iloc[va]);np.testing.assert_allclose(prediction,q.y_pred.reindex(t.iloc[va][ID]),atol=1e-12)
        outer=context(tr,inner,p,'outer_archived_CT3',modelpath.relative_to(ROOT).as_posix());innerplans=[]
        for j,(a,b) in enumerate(inner):
            aa=tr[a];bb=tr[b];cv=subcv(t,aa,p,groups)
            ik=context(aa,cv,p,'inner_base_and_outer_residual');deep=[]
            for c,d in cv:
                aaa=aa[c];ddd=aa[d];deeper=subcv(t,aaa,p,groups)
                key=context(aaa,deeper,p,'deep_base_for_inner_residual')
                assert not set(aaa)&set(ddd) and not set(aaa)&set(bb) and not set(aaa)&set(va)
                deep.append(dict(base_key=key,held_positions=ddd));gates.append(dict(outer_index=i,inner_index=j,train_ids=json.dumps(t.iloc[aaa][ID].tolist()),residual_held_ids=json.dumps(t.iloc[ddd][ID].tolist()),inner_validation_ids=json.dumps(t.iloc[bb][ID].tolist()),outer_validation_ids=json.dumps(t.iloc[va][ID].tolist()),exclusions_verified=True))
            innerplans.append(dict(train_positions=aa,validation_positions=bb,base_key=ik,residual_contexts=deep))
        plans.append(dict(index=i,protocol=p,repeat=r,fold=f,train_positions=tr,validation_positions=va,outer_base_key=outer,inner=innerplans))
    t.to_parquet(OUT/'cache/train138.parquet',index=False);joblib.dump(splits,OUT/'cache/frozen65_splits.joblib');groups.reset_index().to_csv(OUT/'cache/groups.csv',index=False)
    reference.to_parquet(OUT/'cache/reference_oof.parquet',index=False);joblib.dump(contexts,OUT/'cache/base_contexts.joblib');joblib.dump(plans,OUT/'cache/execution_plan.joblib')
    pd.DataFrame(gates).to_csv(OUT/'audit/nested_exclusion_ledger.csv',index=False)
    budget=sum(12*len(x['cv'])+1 for x in contexts.values() if x['external_model'] is None)
    cfg=dict(experiments=['M0']+list(SPECS),specs=SPECS,base_grid=BASE_GRID,base_selection='original mean innerfold RMSE, original GridSearchCV exact ties; never outer-chosen HP inside residual crossfits',corrector_selection='complete original inner OOF RMSE; rounded10 ties smaller amplitude then simpler/stronger penalty',amplitudes=AMPLITUDES,correction_center='train mean0; Ridge no intercept, alpha_solver=n*alpha; CART fit honest residuals then subtract mean train prediction',tree_support='min_samples_leaf15/25 fixed; no forcing splits on small samples; root-only=>zero; profiles/municipality per leaf diagnostic only',primary='incremental absolute performance; paired intraprofile utility separately; no change to B loss',acceptance='exploratory margin.01: benefit>=.01 in absolute grouped or intraprofile BOTH weights, no absolute RMSE/MAE harm>.01 any protocol, no local harm>.01 both weights; geographic |bias| harm<=.02; omissions/top5 stability; no significance claim',context_control='mandatory C_CONTEXT with exact same CART grid and amplitudes; M1_Z matches M2_Z inputs; H3 interactions remain descriptive without additive/LAI-only tree controls',sensitivity='fixed-model temporal perturbations and metric omissions; no extra refits',contexts=len(contexts),new_base_fit_upper=budget,corrector_fit_upper=65*(2*(3*4+1)+2*(4*4+1)),seed=2026,workers=4,no_final_fit138=True,no_PRED=True,no_F8_execution=True,no_champion_change=True,source_sha={p.relative_to(ROOT).as_posix():sha(p) for p in Path(__file__).parent.glob('*.py')},dependencies=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__),cache_sha={p.relative_to(ROOT).as_posix():sha(p) for p in (OUT/'cache').glob('*')})
    pd.DataFrame(protected).drop_duplicates('path').to_csv(OUT/'audit/protected_consumed_inputs.csv',index=False)
    (OUT/'frozen_design.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    (OUT/'report/frozen_plan.md').write_text('# Diseño congelado\n\nCinco modelos: M0 C-T3, M1_LAI lineal LAI, M1_Z lineal mismas4entradas que CART, M2_Z CART y C_CONTEXT CARTsinLAI. Amplitudes0/.25/.5. Base/targets se retunean recursivamente sin etiquetas retenidas. Contextos y exclusiones están en cache y audit. Árbolesdepth1/2,leaf15/25; centrar corrección, no control constante. Ninguna interacción demostrada por comparación arquitectónica solamente. F8no se ejecuta.\n',encoding='utf-8')
    print('FROZEN',len(contexts),'base contexts,',budget,'maximum new base fits',flush=True)

def build_base(key):
    t,_,_=load();ctx=joblib.load(OUT/'cache/base_contexts.joblib')[key];start=time.perf_counter()
    if ctx['external_model']:
        model=joblib.load(ROOT/ctx['external_model']);record=dict(params={k:model.get_params()[k] for k in ['model__alpha','model__l1_ratio']},mean_inner_rmse=np.nan,fit_count=0,fallback='',recovered=True);logs=[]
    else:
        with threadpool_limits(limits=1):model,record,logs=tune_base(t,t[TARGET].to_numpy(),ctx['positions'],ctx['cv'])
        record['recovered']=False
    record.update(key=key,protocol=ctx['protocol'],n_train=len(ctx['positions']),n_cv=len(ctx['cv']),train_ids=t.iloc[ctx['positions']][ID].tolist(),seconds=time.perf_counter()-start,warnings=logs)
    joblib.dump(dict(model=model,registry=record),OUT/'base_cache'/f'{key}.joblib',compress=3)
    return record

def base(key):return joblib.load(OUT/'base_cache'/f'{key}.joblib')['model']

def build_fold(index):
    t,_,_=load();plan=joblib.load(OUT/'cache/execution_plan.joblib')[index];tr=plan['train_positions'];va=plan['validation_positions'];start=time.perf_counter();y=t[TARGET].to_numpy()
    outer_model=base(plan['outer_base_key']);base_external=outer_model.predict(t.iloc[va]);cf_outer=np.full(len(tr),np.nan);map_outer={int(p):i for i,p in enumerate(tr)};inner=[];provenance=[]
    for j,item in enumerate(plan['inner']):
        aa=item['train_positions'];bb=item['validation_positions'];mb=base(item['base_key']);base_valid=mb.predict(t.iloc[bb]);cf_outer[[map_outer[int(p)] for p in bb]]=base_valid
        cf=np.full(len(aa),np.nan);mapping={int(p):i for i,p in enumerate(aa)}
        for deep in item['residual_contexts']:
            dd=deep['held_positions'];prediction=base(deep['base_key']).predict(t.iloc[dd]);cf[[mapping[int(p)] for p in dd]]=prediction
            provenance.append(dict(outer_index=index,inner_index=j,base_key=deep['base_key'],train_target_ids=json.dumps(t.iloc[dd][ID].tolist()),base_excludes_target=True))
        assert np.isfinite(cf).all();inner.append(dict(train_positions=aa,validation_positions=bb,base_valid=base_valid,cf_train=cf,residual=y[aa]-cf))
    assert np.isfinite(cf_outer).all()
    inner_base=np.full(len(tr),np.nan)
    for item in inner:inner_base[[map_outer[int(p)] for p in item['validation_positions']]]=item['base_valid']
    predictions=[];tuning=[];regs=[];rule_rows=[];leaf_rows=[];fitlogs=[];inner_model_paths=[];corrector_fit_count=0
    common=dict(protocol=plan['protocol'],repeat=plan['repeat'],fold=plan['fold'])
    for pid,true,b in zip(t.iloc[va][ID],y[va],base_external):predictions.append(dict(experiment='M0',**common,ID_POLIGONO=pid,y_true=float(true),y_base=float(b),raw_correction=0.,correction=0.,amplitude=0.,y_pred=float(b)))
    with threadpool_limits(limits=1):
        for name,spec in SPECS.items():
            candidates=[];stored={}
            for q,params in enumerate(spec['grid']):
                corrections=np.full(len(tr),np.nan);models=[]
                for j,item in enumerate(inner):
                    aa=item['train_positions'];bb=item['validation_positions'];model=CenteredCorrector(spec['kind'],spec['columns'],params).fit(t.iloc[aa],item['residual']);models.append(model);corrector_fit_count+=1
                    corrections[[map_outer[int(p)] for p in bb]]=model.predict(t.iloc[bb])
                stored[q]=models
                for amplitude in AMPLITUDES:
                    pred=inner_base+amplitude*corrections;e=pred-y[tr];row=dict(experiment=name,**common,candidate=q,params=params,amplitude=amplitude,rmse=float(np.sqrt(np.mean(e*e))),mae=float(abs(e).mean()),bias=float(e.mean()))
                    row['n_inner_constant_correctors']=sum(m.constant for m in models)
                    candidates.append(row)
            selected=min(candidates,key=lambda r:selection_key(r,spec['kind']));q=selected['candidate'];amplitude=selected['amplitude'];params=selected['params']
            tuning.extend([{**r,'params':json.dumps(r['params']),'selected':r is selected} for r in candidates])
            for j,model in enumerate(stored[q]):
                path=OUT/'models'/f'{name}_{index:02d}_inner{j}.joblib';joblib.dump(model,path,compress=3);inner_model_paths.append(path.relative_to(ROOT).as_posix())
            model=None
            if amplitude:
                model=CenteredCorrector(spec['kind'],spec['columns'],params).fit(t.iloc[tr],y[tr]-cf_outer);corrector_fit_count+=1;raw=model.predict(t.iloc[va]);train_raw=model.predict(t.iloc[tr])
            else:raw=np.zeros(len(va));train_raw=np.zeros(len(tr))
            stem=f'{name}_{index:02d}';joblib.dump(dict(model=model,base_key=plan['outer_base_key'],amplitude=amplitude,params=params,columns=spec['columns'],train_ids=t.iloc[tr][ID].tolist(),validation_ids=t.iloc[va][ID].tolist()),OUT/'models'/f'{stem}_outer.joblib',compress=3)
            final=base_external+amplitude*raw
            for pid,true,b,g,p in zip(t.iloc[va][ID],y[va],base_external,raw,final):predictions.append(dict(experiment=name,**common,ID_POLIGONO=pid,y_true=float(true),y_base=float(b),raw_correction=float(g),correction=float(amplitude*g),amplitude=amplitude,y_pred=float(p)))
            full_train=outer_model.predict(t.iloc[tr]);delta=full_train-cf_outer
            regs.append(dict(experiment=name,**common,outer_index=index,amplitude=amplitude,params=json.dumps(params),inner_rmse=selected['rmse'],n_train=len(tr),selected_inner_constant_correctors=selected['n_inner_constant_correctors'],correction_train_mean=float((amplitude*train_raw).mean()),correction_validation_mean=float((amplitude*raw).mean()),correction_validation_max_abs=float(np.max(abs(amplitude*raw))),crossfit_refit_delta_mean=float(delta.mean()),crossfit_refit_delta_sd=float(delta.std()),delta_correction_correlation=float(np.corrcoef(delta,train_raw)[0,1]) if np.std(train_raw)>1e-12 else np.nan,root_only=bool(model and model.constant),effective_depth=model.model.get_depth() if model and model.kind=='tree' and model.model else 0,fit_seconds=time.perf_counter()-start))
            if model and model.kind=='tree':
                for rule in model.rules():rule_rows.append(dict(experiment=name,**common,outer_index=index,**rule))
                leaves=model.leaves(t.iloc[tr]);held_leaves=model.leaves(t.iloc[va])
                for leaf in np.unique(leaves):
                    ix=leaves==leaf;leaf_rows.append(dict(experiment=name,**common,outer_index=index,leaf=int(leaf),n_train=int(ix.sum()),n_profiles=t.iloc[tr[ix]].climate_profile.nunique(),n_municipalities=t.iloc[tr[ix]].Municipio.nunique(),n_heldout=int((held_leaves==leaf).sum()),raw_correction_mean=float(train_raw[ix].mean()),applied_correction_mean=float(amplitude*train_raw[ix].mean())))
    targetrows=[dict(outer_index=index,role='outer_corrector_train',ID_POLIGONO=pid,y=float(v),crossfit_prediction=float(p),residual=float(v-p)) for pid,v,p in zip(t.iloc[tr][ID],y[tr],cf_outer)]
    for j,item in enumerate(inner):targetrows.extend(dict(outer_index=index,role=f'inner{j}_corrector_train',ID_POLIGONO=pid,y=float(v),crossfit_prediction=float(p),residual=float(v-p)) for pid,v,p in zip(t.iloc[item['train_positions']][ID],y[item['train_positions']],item['cf_train']))
    joblib.dump(dict(predictions=predictions,tuning=tuning,registry=regs,rules=rule_rows,leaves=leaf_rows,targets=targetrows,provenance=provenance,n_corrector_fits=corrector_fit_count),OUT/'checkpoints'/f'{index:02d}.joblib',compress=3)
    print('Residual fold',index+1,'/65',plan['protocol'],'amplitudes',[r['amplitude'] for r in regs],flush=True)

def run():
    prepare();start=time.perf_counter();contexts=joblib.load(OUT/'cache/base_contexts.joblib')
    records=joblib.Parallel(n_jobs=4,backend='loky',inner_max_num_threads=1)(joblib.delayed(build_base)(key) for key in contexts)
    pd.DataFrame([{**r,'params':json.dumps(r['params']),'train_ids':json.dumps(r['train_ids']),'warnings':json.dumps(r['warnings']),'candidate_mean_rmse':json.dumps(r.get('candidate_mean_rmse',[]))} for r in records]).to_csv(OUT/'tables/base_fit_registry.csv',index=False)
    print('Nested base cache complete',sum(r['fit_count'] for r in records),'fits',flush=True)
    joblib.Parallel(n_jobs=4,backend='loky',inner_max_num_threads=1)(joblib.delayed(build_fold)(i) for i in range(65))
    from .reporting import build
    build(time.perf_counter()-start)
