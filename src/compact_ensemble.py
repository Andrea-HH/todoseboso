"""Strict inner prediction blend of original compact EN, GPR and CatBoost."""
from pathlib import Path
import json,time,hashlib
import joblib,numpy as np,pandas as pd
from threadpoolctl import threadpool_limits
from src.family_7.models import BoostModel,CB_GRID
from src.ct3_residual_conditional.models import CORE
from src.ct3_residual_coherence import metrics
from src.family_8.research import pair_metrics

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'outputs/modeling/ct3_residual_conditional/v1'
F7=ROOT/'outputs/modeling/family_7/boosting/v1'
F5=ROOT/'outputs/modeling/family_5/gpr_initial/v1'
OUT=ROOT/'outputs/modeling/compact_ensemble/v1'
ID='ID_POLIGONO';Y='RENDIMIENTO_T_HA'
NAMES=['C-T3','F5-01','F7-00']
WEIGHTS=np.array([(a/10,b/10,(10-a-b)/10) for a in range(11) for b in range(11-a)])

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def choose_weights(y,p):
    scores=np.sqrt(np.mean((p@WEIGHTS.T-np.asarray(y)[:,None])**2,axis=0))
    i=min(range(len(scores)),key=lambda k:(round(float(scores[k]),10),-WEIGHTS[k,0],-WEIGHTS[k,1]))
    return WEIGHTS[i].copy(),scores

def files(plan):
    pro,r,f=plan['protocol'],plan['repeat'],plan['fold']
    outer=[OLD/'base_cache'/f"{plan['outer_base_key']}.joblib",F5/'models'/f'F5-01_{pro}_{r}_{f}_outer_-1.joblib',F7/'models'/f'F7-00_{pro}_{r}_{f}_outer.joblib']
    inner=[]
    for j,item in enumerate(plan['inner']):inner.extend([OLD/'base_cache'/f"{item['base_key']}.joblib",F5/'models'/f'F5-01_{pro}_{r}_{f}_inner_{j}.joblib'])
    return outer,inner

def prepare():
    if OUT.exists():raise FileExistsError('Existing versions are immutable')
    for d in ['cache','models','checkpoints','tables','audit','report','figures']:(OUT/d).mkdir(parents=True)
    plans=joblib.load(OLD/'cache/execution_plan.joblib');contexts=joblib.load(OLD/'cache/base_contexts.joblib');keys=sorted({item['base_key'] for p in plans for item in p['inner']})
    consumed=[OLD/'manifest.json',F5/'manifest.json',F7/'manifest.json',OLD/'cache/train138.parquet',OLD/'cache/execution_plan.joblib',OLD/'cache/base_contexts.joblib',OLD/'cache/frozen65_splits.joblib',F7/'tables/oof_predictions.parquet',F5/'tables/fit_registry.csv']
    for plan in plans:
        a,b=files(plan);consumed+=a+b
    consumed += [Path(__file__),ROOT/'src/family_7/models.py',ROOT/'src/ct3_residual_conditional/models.py',ROOT/'src/family_4/conditional_response.py',ROOT/'src/family_5/gpr_initial/model.py',ROOT/'src/family_5/gpr_initial/kernel.py']
    pd.DataFrame([dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in dict.fromkeys(consumed)]).to_csv(OUT/'audit/protected_inputs.csv',index=False)
    joblib.dump(keys,OUT/'cache/cb_keys.joblib')
    config=dict(models=NAMES,features=CORE,weights=WEIGHTS.tolist(),weight_selection='complete original inner OOF RMSE; ties rounded10 prefer CT3 then GPR; nonnegative weights sum1, no intercept',cb_grid=CB_GRID,cb_selection='within each inner training only, archived local protocol CV; original meanfoldRMSE rounded10 ties first; no early stopping',outer_models='archived original models frozen, replayed against archived OOF',inner_models='CT3 recursively tuned cached models; GPR original training-only LML fits; CatBoost independently retuned in each inner training, never original outer-selected inner models',comparators=['C-T3','F5-01','F7-00','EQUAL3'],outer_folds=65,cb_contexts=len(keys),cb_fits_budget=sum(8*len(contexts[k]['cv'])+1 for k in keys),decision='exploratory gain .01 in at least one grouped protocol, no RMSE/MAE harm >.01 vs CT3 anywhere, geographic absolute-bias harm<=.02; inspect omission/local support, no champion promotion',no_residual=True,no_new_variables=True,no_final_fit138=True,no_PRED=True,seed=2026,workers=4)
    (OUT/'frozen_design.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    (OUT/'report/design.md').write_text('# Complementariedad de arquitecturas compactas\n\nC-T3, F5-01 GPR y F7-00 CatBoost con cuatro entradas idénticas. Diagnósticos externos de errores son exploratorios; no eligen pesos ni rejillas. Pesos globales por entrenamiento externo, no regionales: simplex con pasos .1, selección por OOF internas completas. Control promedio fijo equiponderado. Las configuraciones originales externas no se modifican. CatBoost interno se retunea exclusivamente dentro de su entrenamiento interno; modelos internos originalmente seleccionados por toda la validación interna no son admisibles para seleccionar pesos. No se incorporan variables, intercepto o reglas territoriales.\n\nLas OOF históricas se han explorado repetidamente: esta evaluación no constituye confirmación independiente. No se presentan oráculos por parcela como modelos, no se generan intervalos de mezcla no calibrados, ni ajustes finales o PRED.\n',encoding='utf-8')
    print('FROZEN',len(keys),'CatBoost internal contexts; budget',config['cb_fits_budget'],flush=True)

def fit_cb(key):
    t=pd.read_parquet(OLD/'cache/train138.parquet');c=joblib.load(OLD/'cache/base_contexts.joblib')[key];pos=c['positions'];a=t.iloc[pos];start=time.perf_counter();scores=[];warnings=[];fits=0
    with threadpool_limits(limits=1):
        for params in CB_GRID:
            losses=[]
            for tr,va in c['cv']:
                m=BoostModel(CORE,'CatBoost',params).fit(a.iloc[tr],a.iloc[tr][Y]);fits+=1;warnings+=m.warnings_
                losses.append(metrics(a.iloc[va][Y],m.predict(a.iloc[va]))['rmse'])
            scores.append(float(np.mean(losses)))
        chosen=min(range(len(scores)),key=lambda i:(round(scores[i],10),i))
        model=BoostModel(CORE,'CatBoost',CB_GRID[chosen]).fit(a,a[Y]);fits+=1;warnings+=model.warnings_
    registry=dict(key=key,protocol=c['protocol'],train_ids=a[ID].tolist(),n_train=len(a),n_local_cv=len(c['cv']),candidate=chosen,params=CB_GRID[chosen],scores=scores,fits=fits,warnings=warnings,seconds=time.perf_counter()-start)
    joblib.dump(dict(model=model,registry=registry),OUT/'models'/f'CB_{key}.joblib',compress=3)
    print('Nested CatBoost',key,c['protocol'],round(registry['seconds'],1),'s',flush=True)
    return registry

def fold(index):
    t=pd.read_parquet(OLD/'cache/train138.parquet');p=joblib.load(OLD/'cache/execution_plan.joblib')[index];contexts=joblib.load(OLD/'cache/base_contexts.joblib');tr=p['train_positions'];va=p['validation_positions'];position={int(i):j for j,i in enumerate(tr)};inside=np.full((len(tr),3),np.nan);ledger=[];outerpaths,innerpaths=files(p)
    gp_registry=pd.read_csv(F5/'tables/fit_registry.csv')
    for j,item in enumerate(p['inner']):
        a,b=item['train_positions'],item['validation_positions'];key=item['base_key'];cb=joblib.load(OUT/'models'/f'CB_{key}.joblib')
        np.testing.assert_array_equal(contexts[key]['positions'],a);assert cb['registry']['train_ids']==t.iloc[a][ID].tolist()
        g=gp_registry[(gp_registry.experiment=='F5-01')&(gp_registry.protocol==p['protocol'])&(gp_registry['repeat']==p['repeat'])&(gp_registry.fold==p['fold'])&(gp_registry.context=='inner')&(gp_registry.inner_index==j)]
        assert len(g)==1 and json.loads(g.iloc[0].train_ids)==t.iloc[a][ID].tolist()
        assert not set(a)&set(b) and not (set(a)|set(b))&set(va)
        for c,d in contexts[key]['cv']:assert not set(a[c])&set(a[d]) and not (set(a[c])|set(a[d]))&set(b) and not (set(a[c])|set(a[d]))&set(va)
        models=[joblib.load(innerpaths[2*j])['model'],joblib.load(innerpaths[2*j+1]),cb['model']]
        inside[[position[int(i)] for i in b]]=np.column_stack([m.predict(t.iloc[b]) for m in models])
        ledger.append(dict(outer_index=index,inner_index=j,base_key=key,train_ids=json.dumps(t.iloc[a][ID].tolist()),weight_validation_ids=json.dumps(t.iloc[b][ID].tolist()),outer_validation_ids=json.dumps(t.iloc[va][ID].tolist()),exclusions_verified=True))
    assert np.isfinite(inside).all();weights,scores=choose_weights(t.iloc[tr][Y],inside)
    outermodels=[joblib.load(outerpaths[0])['model'],joblib.load(outerpaths[1]),joblib.load(outerpaths[2])];outside=np.column_stack([m.predict(t.iloc[va]) for m in outermodels]);common=dict(protocol=p['protocol'],repeat=p['repeat'],fold=p['fold'])
    rows=[]
    for name,values in list(zip(NAMES,outside.T))+[('EQUAL3',outside.mean(axis=1)),('BLEND3',outside@weights)]:
        rows.extend(dict(experiment=name,**common,ID_POLIGONO=pid,y_true=float(y),y_pred=float(pred)) for pid,y,pred in zip(t.iloc[va][ID],t.iloc[va][Y],values))
    reg=dict(**common,w_ct3=float(weights[0]),w_gpr=float(weights[1]),w_catboost=float(weights[2]),inner_rmse=float(min(scores)),inner_equal_rmse=metrics(t.iloc[tr][Y],inside.mean(axis=1))['rmse'],n_train=len(tr))
    joblib.dump(dict(weights=weights,outer_paths=[str(v.relative_to(ROOT)) for v in outerpaths],registry=reg),OUT/'models'/f'BLEND_{index:02d}.joblib')
    innerrows=[dict(**common,ID_POLIGONO=pid,y_true=float(y),ct3=float(v[0]),gpr=float(v[1]),catboost=float(v[2])) for pid,y,v in zip(t.iloc[tr][ID],t.iloc[tr][Y],inside)]
    joblib.dump(dict(predictions=rows,registry=reg,inner=innerrows,ledger=ledger,tuning=[dict(**common,weights=w.tolist(),rmse=float(s)) for w,s in zip(WEIGHTS,scores)]),OUT/'checkpoints'/f'{index:02d}.joblib',compress=3)
    print('Blend',index+1,'/65',p['protocol'],weights.tolist(),flush=True)

def finish(wall,records):
    packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(65)];pred=pd.DataFrame([r for p in packs for r in p['predictions']]);assert len(pred)==8970
    pred.to_parquet(OUT/'tables/oof_predictions.parquet',index=False);pred.to_csv(OUT/'tables/oof_predictions.csv',index=False)
    for key in ['inner','ledger','tuning']:pd.DataFrame([r for p in packs for r in p[key]]).to_parquet(OUT/'tables'/f'{key}.parquet',index=False)
    pd.DataFrame([p['registry'] for p in packs]).to_csv(OUT/'tables/weights.csv',index=False)
    pd.DataFrame([{**r,'params':json.dumps(r['params']),'train_ids':json.dumps(r['train_ids']),'warnings':json.dumps(r['warnings']),'scores':json.dumps(r['scores'])} for r in records]).to_csv(OUT/'tables/cb_registry.csv',index=False)
    refs=pd.read_parquet(F7/'tables/oof_predictions.parquet');checks=[]
    for name in NAMES:
        q=pred[pred.experiment==name].merge(refs[refs.experiment==name],on=['protocol','repeat','fold',ID],suffixes=('_new','_old'),validate='one_to_one');assert len(q)==1794;np.testing.assert_allclose(q.y_true_new,q.y_true_old,atol=1e-12);difference=float(np.max(abs(q.y_pred_new-q.y_pred_old)));assert difference<1e-10;checks.append(dict(experiment=name,max_difference=difference))
    pd.DataFrame(checks).to_csv(OUT/'audit/reference_replay.csv',index=False)
    t=pd.read_parquet(OLD/'cache/train138.parquet');allp=pred.merge(t[[ID,'Estado','Municipio','climate_profile']],on=ID,validate='many_to_one');repeat=[];local=[];regional=[];omissions=[];complement=[];paired=[]
    for (exp,pro,re),g in allp.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g[ID].is_unique;repeat.append(dict(experiment=exp,protocol=pro,repeat=re,**metrics(g.y_true,g.y_pred)));local.append(dict(experiment=exp,protocol=pro,repeat=re,**pair_metrics(g)))
        for field in ['fold','Estado','Municipio']:
            for zone,h in g.groupby(field):regional.append(dict(experiment=exp,protocol=pro,repeat=re,group_type=field,group=zone,n=len(h),**metrics(h.y_true,h.y_pred)))
        for field in ['fold','Municipio']:
            for zone in g[field].unique():
                h=g[g[field]!=zone];omissions.append(dict(experiment=exp,protocol=pro,repeat=re,omitted_type=field,omitted=zone,**metrics(h.y_true,h.y_pred)))
    rm=pd.DataFrame(repeat);rm.to_csv(OUT/'tables/metrics_repeat.csv',index=False);summary=rm.groupby(['experiment','protocol'])[['rmse','mae','bias']].mean().reset_index();summary.to_csv(OUT/'tables/metrics_summary.csv',index=False)
    pd.DataFrame(local).groupby(['experiment','protocol']).mean(numeric_only=True).reset_index().to_csv(OUT/'tables/intraprofile_summary.csv',index=False)
    pd.DataFrame(regional).to_csv(OUT/'tables/regional_repeat.csv',index=False);pd.DataFrame(omissions).to_csv(OUT/'tables/omissions.csv',index=False)
    wide=allp.pivot(index=['protocol','repeat','fold',ID,'Estado','Municipio','climate_profile','y_true'],columns='experiment',values='y_pred').reset_index()
    for (pro,re),g in wide.groupby(['protocol','repeat']):
        for field in ['all','fold','Municipio']:
            zones=[('all',g)] if field=='all' else list(g.groupby(field))
            for zone,h in zones:
                for i,a in enumerate(NAMES):
                    for b in NAMES[i+1:]:
                        ea=(h[a]-h.y_true).to_numpy();eb=(h[b]-h.y_true).to_numpy()
                        complement.append(dict(protocol=pro,repeat=re,group_type=field,group=zone,n=len(h),model_a=a,model_b=b,error_correlation=float(np.corrcoef(ea,eb)[0,1]) if len(h)>2 and np.std(ea)>1e-12 and np.std(eb)>1e-12 else np.nan,opposite_error_fraction=float(np.mean(ea*eb<0)),mean_error_crossproduct=float(np.mean(ea*eb)),fraction_b_lower_absolute_error=float(np.mean(abs(eb)<abs(ea))),equal_pair_rmse=float(np.sqrt(np.mean(((ea+eb)/2)**2)))))
        for name in ['BLEND3','EQUAL3']:
            for ref in NAMES+(['EQUAL3'] if name=='BLEND3' else []):
                a=metrics(g.y_true,g[name]);b=metrics(g.y_true,g[ref]);paired.append(dict(experiment=name,reference=ref,protocol=pro,repeat=re,**{f'delta_{k}':a[k]-b[k] for k in a}))
    pd.DataFrame(complement).to_csv(OUT/'tables/error_complementarity.csv',index=False);pd.DataFrame(paired).to_csv(OUT/'tables/paired_repeat.csv',index=False)
    for ref in NAMES:
        wide[f'sse_gain_vs_{ref}']=(wide[ref]-wide.y_true)**2-(wide.BLEND3-wide.y_true)**2
    wide.to_parquet(OUT/'tables/parcel_gains.parquet',index=False)
    replay=[]
    for i,p in enumerate(joblib.load(OLD/'cache/execution_plan.joblib')):
        pack=joblib.load(OUT/'models'/f'BLEND_{i:02d}.joblib');models=[joblib.load(ROOT/path) for path in pack['outer_paths']];models[0]=models[0]['model'];v=t.iloc[p['validation_positions']];values=np.column_stack([m.predict(v) for m in models])@pack['weights'];q=pred[(pred.experiment=='BLEND3')&(pred.protocol==p['protocol'])&(pred['repeat']==p['repeat'])&(pred.fold==p['fold'])].set_index(ID).reindex(v[ID]);difference=float(np.max(abs(values-q.y_pred)));assert difference<1e-10;replay.append(dict(outer_index=i,max_difference=difference))
    pd.DataFrame(replay).to_csv(OUT/'audit/blend_replay.csv',index=False)
    for r in pd.read_csv(OUT/'audit/protected_inputs.csv').itertuples():assert sha(ROOT/r.path)==r.sha256
    (OUT/'report/results.md').write_text('# Combinación compacta: resultados\n\n```text\n'+summary.to_string(index=False)+'\n```\n\nSelección completa interna, diagnósticos externos exploratorios; no superioridad estadística demostrada.\n',encoding='utf-8')
    (OUT/'manifest.json').write_text(json.dumps(dict(status='complete',new_cb_fits=sum(r['fits'] for r in records),new_en_gp_fits=0,n_oof=8970,n_blends=65,wall_seconds=wall,no_final_fit138=True,no_PRED=True,artifacts={p.relative_to(ROOT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json'}),indent=2),encoding='utf-8');print(summary.to_string(index=False),flush=True)

def run():
    prepare();start=time.perf_counter();keys=joblib.load(OUT/'cache/cb_keys.joblib')
    records=joblib.Parallel(n_jobs=4,backend='loky',inner_max_num_threads=1)(joblib.delayed(fit_cb)(key) for key in keys)
    with threadpool_limits(limits=1):
        for i in range(65):fold(i)
    finish(time.perf_counter()-start,records)
