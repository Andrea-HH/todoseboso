"""Frozen paired-base/disjoint-calibration sensitivity; no new base fits."""
from pathlib import Path
import json,time,hashlib
import joblib,numpy as np,pandas as pd
from threadpoolctl import threadpool_limits
from src.ct3_residual_conditional.models import SPECS,AMPLITUDES,CenteredCorrector,selection_key
from src.family_8.research import pair_metrics

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/modeling/ct3_residual_conditional/v1'
OUT=ROOT/'outputs/modeling/ct3_residual_coherence/v1'
ID='ID_POLIGONO';Y='RENDIMIENTO_T_HA'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def metrics(y,p):
    e=np.asarray(p)-np.asarray(y)
    return dict(rmse=float(np.sqrt(np.mean(e*e))),mae=float(np.mean(abs(e))),bias=float(e.mean()))

def fit_pair(t,base,base_positions,calibration_positions,evaluation_positions,spec,params):
    """Base excludes calibration; both fitting stages exclude evaluation."""
    a,c,e=map(set,[base_positions,calibration_positions,evaluation_positions])
    assert not a&c and not a&e and not c&e
    residual=t.iloc[calibration_positions][Y].to_numpy()-base.predict(t.iloc[calibration_positions])
    model=CenteredCorrector(spec['kind'],spec['columns'],params).fit(t.iloc[calibration_positions],residual)
    return model,model.predict(t.iloc[evaluation_positions])

def prepare():
    if OUT.exists():raise FileExistsError('Existing versions must remain intact')
    for d in ['models','checkpoints','tables','audit','report']:(OUT/d).mkdir(parents=True)
    plans=joblib.load(SOURCE/'cache/execution_plan.joblib');contexts=joblib.load(SOURCE/'cache/base_contexts.joblib')
    consumed=[SOURCE/'manifest.json',SOURCE/'cache/train138.parquet',SOURCE/'cache/execution_plan.joblib',SOURCE/'cache/base_contexts.joblib',SOURCE/'cache/frozen65_splits.joblib',SOURCE/'tables/oof_predictions.parquet',Path(__file__),ROOT/'src/ct3_residual_conditional/models.py',ROOT/'src/family_4/conditional_response.py',ROOT/'src/family_8/research.py']
    keys=set()
    for p in plans:
        for item in p['inner']:
            keys.add(item['base_key'])
            keys.update(d['base_key'] for d in item['residual_contexts'])
    consumed += [SOURCE/'base_cache'/f'{k}.joblib' for k in sorted(keys)]
    pd.DataFrame([dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in consumed]).to_csv(OUT/'audit/protected_inputs.csv',index=False)
    cfg=dict(experiment='CT3 paired-base coherence',specs=SPECS,amplitudes=AMPLITUDES,outer_folds=65,selection='complete original inner OOF RMSE; original selection_key',base_policy='reuse previously nested-tuned archived caches exactly; no new base fitting',outer_prediction='equal-weight four original inner base models, each corrected on its disjoint heldout calibration fold; never refit the paired base',inner_prediction='for each original inner validation fold, average deep base/calibration pairs contained entirely in inner training; evaluate only original inner heldout',controls='paired ensemble with zero correction; original five-model archived OOF unchanged',centering='original calibration mean-zero centered corrector; no new intercept',limits='original features, grids, amplitudes and frozen splits; no regional rules, no extra depth',scope='exploratory structural contrast, not independent confirmation or pure isolation: training sizes and calibration support also change',no_final_fit138=True,no_PRED=True,no_champion_change=True)
    (OUT/'frozen_design.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    (OUT/'report/frozen_design.md').write_text('# Sensibilidad de coherencia residual\n\nCada base permanece congelada al calibrar y predecir. Calibrador y base se ajustan en muestras disjuntas. Promedio equiponderado de parejas. Control obligatorio del promedio sin correccion. Cuatro correctores anteriores, mismas variables y limites. Seleccion solo con OOF internas originales, aplicando el procedimiento completo de parejas en cada entrenamiento interno. No se selecciona con resultados externos.\n\nMenor soporte de calibracion: especialmente en protocolos agrupados, una hoja minima de 15/25 puede impedir divisiones. No se relajan limites. El contraste modifica coherencia, tamaño de entrenamiento y mecanismo de agregacion; no atribuir cambios exclusivamente a un mecanismo. No ejecuta F8 ni amplía variables.\n',encoding='utf-8')

def fold(index):
    t=pd.read_parquet(SOURCE/'cache/train138.parquet');plans=joblib.load(SOURCE/'cache/execution_plan.joblib');contexts=joblib.load(SOURCE/'cache/base_contexts.joblib');p=plans[index];tr=p['train_positions'];va=p['validation_positions'];lookup={int(k):j for j,k in enumerate(tr)}
    memo={}
    def base(k):
        if k not in memo:memo[k]=joblib.load(SOURCE/'base_cache'/f'{k}.joblib')['model']
        return memo[k]
    common=dict(protocol=p['protocol'],repeat=p['repeat'],fold=p['fold'])
    inner_base=np.full(len(tr),np.nan);outer_components=[];ledger=[]
    for j,item in enumerate(p['inner']):
        a=item['train_positions'];c=item['validation_positions'];b=base(item['base_key'])
        assert set(contexts[item['base_key']]['positions'])==set(a)
        assert not set(a)&set(c) and not set(a)&set(va) and not set(c)&set(va)
        outer_components.append(b.predict(t.iloc[va]))
        preds=[]
        for d in item['residual_contexts']:
            k=d['base_key'];cal=d['held_positions'];bp=contexts[k]['positions']
            assert not set(bp)&set(cal) and not set(bp)&set(c) and not set(cal)&set(c)
            assert not (set(bp)|set(cal))&set(va)
            preds.append(base(k).predict(t.iloc[c]))
            ledger.append(dict(outer_index=index,inner_index=j,base_key=k,base_ids=json.dumps(t.iloc[bp][ID].tolist()),calibration_ids=json.dumps(t.iloc[cal][ID].tolist()),inner_validation_ids=json.dumps(t.iloc[c][ID].tolist()),outer_validation_ids=json.dumps(t.iloc[va][ID].tolist()),disjoint=True))
        inner_base[[lookup[int(i)] for i in c]]=np.mean(preds,axis=0)
    assert np.isfinite(inner_base).all()
    outer_base=np.mean(outer_components,axis=0);rows=[];tuning=[];registry=[];support=[];rules=[];fits=0
    def add(name,pred,raw,amp):
        for pid,y,b,g,v in zip(t.iloc[va][ID],t.iloc[va][Y],outer_base,raw,pred):rows.append(dict(experiment=name,**common,ID_POLIGONO=pid,y_true=float(y),y_base=float(b),raw_correction=float(g),amplitude=amp,y_pred=float(v)))
    add('PAIR_BASE',outer_base,np.zeros(len(va)),0.)
    for name,spec in SPECS.items():
        candidates=[]
        for q,params in enumerate(spec['grid']):
            correction=np.full(len(tr),np.nan)
            for item in p['inner']:
                c=item['validation_positions'];vals=[]
                for d in item['residual_contexts']:
                    k=d['base_key'];model,pred=fit_pair(t,base(k),contexts[k]['positions'],d['held_positions'],c,spec,params);fits+=1;vals.append(pred)
                correction[[lookup[int(i)] for i in c]]=np.mean(vals,axis=0)
            for amp in AMPLITUDES:candidates.append(dict(candidate=q,params=params,amplitude=amp,**metrics(t.iloc[tr][Y],inner_base+amp*correction)))
        chosen=min(candidates,key=lambda z:selection_key(z,spec['kind']));amp=chosen['amplitude'];params=chosen['params'];components=[];raws=[]
        for j,item in enumerate(p['inner']):
            k=item['base_key'];cal=item['validation_positions'];model=None
            if amp:
                model,raw=fit_pair(t,base(k),item['train_positions'],cal,va,spec,params);fits+=1
            else:raw=np.zeros(len(va))
            raws.append(raw);components.append(dict(base_key=k,corrector=model,calibration_ids=t.iloc[cal][ID].tolist(),base_ids=t.iloc[item['train_positions']][ID].tolist()))
            support.append(dict(experiment='PAIR_'+name,**common,component=j,n_base=len(item['train_positions']),n_calibration=len(cal),n_profiles=t.iloc[cal].climate_profile.nunique(),amplitude=amp,corrector_fitted=model is not None,constant=bool(model.constant) if model else True,calibration_correction_mean=float(model.predict(t.iloc[cal]).mean()) if model else 0.,effective_depth=model.model.get_depth() if model and model.kind=='tree' and model.model else 0))
            if model and model.kind=='tree':rules.extend(dict(experiment='PAIR_'+name,**common,component=j,**r) for r in model.rules())
        raw=np.mean(raws,axis=0);add('PAIR_'+name,outer_base+amp*raw,raw,amp)
        registry.append(dict(experiment='PAIR_'+name,**common,amplitude=amp,params=json.dumps(params),inner_rmse=chosen['rmse'],validation_mean_correction=float((amp*raw).mean()),validation_max_correction=float(np.max(abs(amp*raw)))))
        tuning.extend(dict(experiment='PAIR_'+name,**common,**z,selected=z is chosen) for z in candidates)
        joblib.dump(dict(components=components,amplitude=amp,params=params,registry=registry[-1]),OUT/'models'/f'{name}_{index:02d}.joblib',compress=3)
    joblib.dump(dict(predictions=rows,tuning=tuning,registry=registry,support=support,rules=rules,ledger=ledger,fits=fits),OUT/'checkpoints'/f'{index:02d}.joblib',compress=3)
    print('Coherence',index+1,'/65',p['protocol'],[r['amplitude'] for r in registry],flush=True)

def finish(wall):
    packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(65)]
    for key in ['tuning','registry','support','rules','ledger']:
        pd.DataFrame([r for p in packs for r in p[key]]).to_csv(OUT/'tables'/f'{key}.csv',index=False)
    pred=pd.DataFrame([r for p in packs for r in p['predictions']]);assert len(pred)==8970
    pred.to_parquet(OUT/'tables/oof_predictions.parquet',index=False);pred.to_csv(OUT/'tables/oof_predictions.csv',index=False)
    old=pd.read_parquet(SOURCE/'tables/oof_predictions.parquet');allp=pd.concat([pred,old],ignore_index=True);t=pd.read_parquet(SOURCE/'cache/train138.parquet');allp=allp.merge(t[[ID,'climate_profile','Estado','Municipio']],on=ID,validate='many_to_one')
    repeat=[];local=[];regional=[];omissions=[];paired=[]
    for (exp,pro,re),g in allp.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g[ID].is_unique
        repeat.append(dict(experiment=exp,protocol=pro,repeat=re,**metrics(g.y_true,g.y_pred)))
        local.append(dict(experiment=exp,protocol=pro,repeat=re,**pair_metrics(g)))
        for field in ['fold','Municipio','Estado']:
            for zone,h in g.groupby(field):regional.append(dict(experiment=exp,protocol=pro,repeat=re,group_type=field,group=zone,n=len(h),**metrics(h.y_true,h.y_pred)))
        for field in ['fold','Municipio']:
            for zone in g[field].unique():
                h=g[g[field]!=zone];omissions.append(dict(experiment=exp,protocol=pro,repeat=re,omitted_type=field,omitted=zone,**metrics(h.y_true,h.y_pred)))
    rm=pd.DataFrame(repeat);ip=pd.DataFrame(local)
    rm.to_csv(OUT/'tables/metrics_repeat.csv',index=False);summary=rm.groupby(['experiment','protocol'])[['rmse','mae','bias']].mean().reset_index();summary.to_csv(OUT/'tables/metrics_summary.csv',index=False)
    ip.to_csv(OUT/'tables/intraprofile_repeat.csv',index=False);ip.groupby(['experiment','protocol']).mean(numeric_only=True).reset_index().to_csv(OUT/'tables/intraprofile_summary.csv',index=False)
    pd.DataFrame(regional).to_csv(OUT/'tables/regional_repeat.csv',index=False);pd.DataFrame(omissions).to_csv(OUT/'tables/omission_sensitivity.csv',index=False)
    gains=[]
    for exp in pred.experiment.unique():
        for ref in ['M0','PAIR_BASE',exp.replace('PAIR_','')]:
            if ref==exp or ref not in allp.experiment.unique():continue
            q=allp[allp.experiment==exp].merge(allp[allp.experiment==ref],on=['protocol','repeat','fold',ID],suffixes=('_new','_ref'),validate='one_to_one');np.testing.assert_allclose(q.y_true_new,q.y_true_ref)
            for (pro,re),g in q.groupby(['protocol','repeat']):
                a=metrics(g.y_true_new,g.y_pred_new);b=metrics(g.y_true_ref,g.y_pred_ref)
                paired.append(dict(experiment=exp,reference=ref,protocol=pro,repeat=re,**{f'delta_{k}':a[k]-b[k] for k in a}))
            gains.extend(dict(experiment=exp,reference=ref,protocol=r.protocol,repeat=r.repeat,fold=r.fold,ID_POLIGONO=getattr(r,ID),squared_error_gain=(r.y_pred_ref-r.y_true_ref)**2-(r.y_pred_new-r.y_true_new)**2) for r in q.itertuples())
    pd.DataFrame(paired).to_csv(OUT/'tables/paired_repeat.csv',index=False);pd.DataFrame(gains).to_parquet(OUT/'tables/parcel_gains.parquet',index=False)
    # Replay saved complete paired predictors, with original immutable base caches.
    replay=[]
    for i,p in enumerate(joblib.load(SOURCE/'cache/execution_plan.joblib')):
        x=t.iloc[p['validation_positions']]
        for name in SPECS:
            pack=joblib.load(OUT/'models'/f'{name}_{i:02d}.joblib');values=[]
            for c in pack['components']:
                b=joblib.load(SOURCE/'base_cache'/f"{c['base_key']}.joblib")['model'];v=b.predict(x)
                if c['corrector'] is not None:v=v+pack['amplitude']*c['corrector'].predict(x)
                values.append(v)
            q=pred[(pred.experiment=='PAIR_'+name)&(pred.protocol==p['protocol'])&(pred['repeat']==p['repeat'])&(pred.fold==p['fold'])].set_index(ID).reindex(x[ID]);difference=float(np.max(abs(np.mean(values,axis=0)-q.y_pred)))
            assert difference<1e-10;replay.append(dict(outer_index=i,experiment=name,max_difference=difference))
    pd.DataFrame(replay).to_csv(OUT/'audit/model_replay.csv',index=False)
    protected=pd.read_csv(OUT/'audit/protected_inputs.csv')
    for r in protected.itertuples():assert sha(ROOT/r.path)==r.sha256
    (OUT/'report/results.md').write_text('# Coherencia residual: resultados exploratorios\n\n```text\n'+summary.to_string(index=False)+'\n```\n\nRMSE/MAE/sesgo sobre OOF completas por repeticion, promedio de 10 repeticiones aleatorias. No media de folds. PAIR_BASE es el control equiponderado sin correccion. Comparar primero cada corrector con PAIR_BASE, despues con M0 y con su formulacion original. No hay intervalos predictivos calibrados para estos correctores deterministas.\n\nEl diseño cambia coherencia, soporte de calibracion y agregacion; no aísla causalmente el desajuste crossfit/refit. Limites originales conservados, sin reglas regionales ni seleccion externa.\n',encoding='utf-8')
    manifest=dict(status='complete',wall_seconds=wall,n_new_base_fits=0,n_corrector_fits=sum(p['fits'] for p in packs),n_oof=8970,n_saved_model_packs=260,replay_models=260,protected_inputs_verified=len(protected),no_final_fit138=True,no_PRED=True,no_champion_change=True,artifacts={p.relative_to(ROOT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json'})
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print(summary.to_string(index=False),flush=True)

def run():
    prepare();start=time.perf_counter()
    with threadpool_limits(limits=1):
        for i in range(65):fold(i)
    finish(time.perf_counter()-start)
