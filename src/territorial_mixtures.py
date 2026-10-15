"""Nested regularized global, municipality and feature-gated compact mixtures."""
from pathlib import Path
import json,time,argparse
import joblib,numpy as np,pandas as pd
from scipy.spatial.distance import cdist
from threadpoolctl import threadpool_limits
from src.compact_ensemble import ROOT,OLD,F5,OUT as PREVIOUS,CORE,WEIGHTS,NAMES,files,sha
from src.ct3_residual_coherence import metrics
from src.family_7.models import BoostModel,CB_GRID
from src.family_5.gpr_initial.model import CompactGPR,OPT
from src.family_4.conditional_response import ConditionalFeatures
from src.family_8.research import pair_metrics

OUT=ROOT/'outputs/modeling/territorial_mixtures/v1'
ID='ID_POLIGONO';Y='RENDIMIENTO_T_HA'
EQUAL=np.ones(3)/3
W=np.vstack([EQUAL,WEIGHTS])
STRENGTHS=[None,1.,.1,.01,0.]
SHRINK=[None,150.,50.,15.]
CONFIGS={'R1':[dict(alpha=a) for a in STRENGTHS],
 'R2':[dict(alpha=a,shrink=s) for a in STRENGTHS for s in SHRINK],
 'R3':[dict(alpha=a,depth=d,leaf=n,shrink=s) for a in STRENGTHS for d,n,s in [(0,35,150.)]+[(d,n,s) for d in [1,2] for n in [35,20] for s in [150.,50.]]]}

def optimal(y,p,prior,alpha):
    if alpha is None:return prior.copy()
    loss=np.mean((p@W.T-np.asarray(y)[:,None])**2,axis=0)+alpha*max(float(np.var(y)),1e-12)*np.sum((W-prior)**2,axis=1)
    i=min(range(len(W)),key=lambda k:(round(float(loss[k]),12),float(np.sum((W[k]-prior)**2)),-W[k,0],-W[k,1]))
    return W[i].copy()

def supported_weights(y,p,prior,shrink):
    if shrink is None:return prior.copy()
    local=optimal(y,p,prior,0.)
    fraction=len(y)/(len(y)+shrink)
    return prior+fraction*(local-prior)

class Mixture:
    def __init__(self,name,params):self.name=name;self.params=params
    def fit(self,t,p):
        self.global_weights=optimal(t[Y].to_numpy(),p,EQUAL,self.params['alpha']);self.regions={};self.nodes=[]
        y=t[Y].to_numpy();profiles=t.climate_profile.to_numpy()
        if self.name=='R2':
            for zone,indices in t.reset_index(drop=True).groupby(['Estado','Municipio']).indices.items():
                ix=np.asarray(indices)
                if len(ix)>=15 and len(set(profiles[ix]))>=2 and self.params['shrink'] is not None:
                    self.regions[zone]=dict(weights=supported_weights(y[ix],p[ix],self.global_weights,self.params['shrink']),n=len(ix),n_profiles=len(set(profiles[ix])))
        if self.name=='R3':
            self.transform=ConditionalFeatures(tuple(CORE)).fit(t);x=self.transform.transform(t);self.feature_names=list(self.transform.get_feature_names_out());self.minimum=x.min(axis=0);self.maximum=x.max(axis=0)
            self._grow(x,y,p,profiles,np.arange(len(t)),0,self.global_weights)
        return self
    def _grow(self,x,y,p,profiles,ix,depth,weights):
        node=len(self.nodes);self.nodes.append(dict(weights=weights,n=len(ix),n_profiles=len(set(profiles[ix])),feature=-1,left=-1,right=-1,threshold=None,depth=depth))
        if depth>=self.params['depth']:return node
        best_loss=float(np.sum((p[ix]@weights-y[ix])**2));best=None
        for feature in range(x.shape[1]):
            for threshold in np.unique(np.quantile(x[ix,feature],[.2,.4,.6,.8])):
                left=ix[x[ix,feature]<=threshold];right=ix[x[ix,feature]>threshold]
                if min(len(left),len(right))<self.params['leaf'] or min(len(set(profiles[left])),len(set(profiles[right])))<2:continue
                wl=supported_weights(y[left],p[left],self.global_weights,self.params['shrink']);wr=supported_weights(y[right],p[right],self.global_weights,self.params['shrink'])
                loss=float(np.sum((p[left]@wl-y[left])**2)+np.sum((p[right]@wr-y[right])**2))
                if loss<best_loss-1e-10:best_loss=loss;best=(feature,float(threshold),left,right,wl,wr)
        if best is not None:
            feature,threshold,left,right,wl,wr=best
            self.nodes[node].update(feature=feature,threshold=threshold,left=self._grow(x,y,p,profiles,left,depth+1,wl),right=self._grow(x,y,p,profiles,right,depth+1,wr))
        return node
    def weights(self,t):
        result=np.tile(self.global_weights,(len(t),1));route=np.full(len(t),'global',dtype=object)
        if self.name=='R2':
            for i,zone in enumerate(zip(t.Estado,t.Municipio)):
                if zone in self.regions:result[i]=self.regions[zone]['weights'];route[i]='municipal'
        if self.name=='R3':
            x=self.transform.transform(t)
            for i,row in enumerate(x):
                if np.any(row<self.minimum-1e-10) or np.any(row>self.maximum+1e-10):route[i]='outside_support_global';continue
                node=0
                while self.nodes[node]['feature']>=0:
                    n=self.nodes[node];node=n['left'] if row[n['feature']]<=n['threshold'] else n['right']
                result[i]=self.nodes[node]['weights'];route[i]=f'leaf{node}' if node else 'root_global'
        assert np.all(result>=-1e-12);np.testing.assert_allclose(result.sum(axis=1),1,atol=1e-12)
        return result,route
    def predict(self,t,p):
        w,_=self.weights(t);return np.sum(w*p,axis=1)

def prepare():
    if OUT.exists():raise FileExistsError('Preserve previous versions')
    for d in ['cache','models','checkpoints','tables','audit','report','figures']:(OUT/d).mkdir(parents=True)
    plans=joblib.load(OLD/'cache/execution_plan.joblib');contexts=joblib.load(OLD/'cache/base_contexts.joblib');inner={i['base_key'] for p in plans for i in p['inner']};deep={d['base_key'] for p in plans for i in p['inner'] for d in i['residual_contexts']};keys=sorted(inner|deep)
    gp_paths={}
    for plan in plans:
        _,paths=files(plan)
        for j,item in enumerate(plan['inner']):gp_paths.setdefault(item['base_key'],paths[2*j+1].relative_to(ROOT).as_posix())
    joblib.dump(dict(keys=keys,new_keys=sorted(deep-inner),gp_paths=gp_paths,inner_keys=sorted(inner)),OUT/'cache/expert_plan.joblib')
    consumed=[OLD/'manifest.json',PREVIOUS/'manifest.json',OLD/'cache/train138.parquet',OLD/'cache/execution_plan.joblib',OLD/'cache/base_contexts.joblib',OLD/'cache/frozen65_splits.joblib',PREVIOUS/'tables/oof_predictions.parquet',PREVIOUS/'tables/inner.parquet',Path(__file__),ROOT/'src/compact_ensemble.py',ROOT/'src/family_7/models.py',ROOT/'src/family_5/gpr_initial/model.py',ROOT/'src/family_5/gpr_initial/kernel.py',ROOT/'src/family_4/conditional_response.py']
    consumed += [OLD/'base_cache'/f'{k}.joblib' for k in keys]
    consumed += [PREVIOUS/'models'/f'CB_{k}.joblib' for k in sorted(inner)]
    consumed += [ROOT/p for p in gp_paths.values()]
    for plan in plans:consumed+=files(plan)[0]
    pd.DataFrame([dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in dict.fromkeys(consumed)]).to_csv(OUT/'audit/protected_inputs.csv',index=False)
    cfg=dict(experiments=['R1','R2','R3'],configs=CONFIGS,weights=W.tolist(),expert_features=CORE,experts=NAMES,global_prior=EQUAL.tolist(),regularization='mean squared OOF error + alpha*train_y_variance*L2(weight-prior)^2; alpha None fixes equal prior',municipal='state+municipality key; local weights shrink n/(n+s) toward global; min15 labels and2 profiles; unseen/unsupported use global; shrink None disables locality',gate='greedy direct blended SSE improvement; depth0/1/2, leaf20/35, min2 profiles per child; train quartile-like thresholds .2/.4/.6/.8; local weights shrink50/150 toward global; out-of-training marginal support falls back global',selection='complete original inner OOF RMSE; rounded10 ties first candidate (stronger regularization, global fallback, shallower larger leaves); all gates/hyperparameters fitted recursively within training',expert_reuse='all outer originals frozen; original honest inner triples reused; deep CT3 caches reused; deep GPR/CB trained/tuned only in their context; GP original OPT, CB original grid meanfold criterion',new_deep_contexts=len(deep-inner),cb_grid=CB_GRID,gpr_optimizer=OPT,expected_cb_fits=sum(8*len(contexts[k]['cv'])+1 for k in deep-inner),expected_gp_fits=len(deep-inner),no_ad_hoc_municipal_rules=True,no_intercept=True,no_new_variables=True,no_residual=True,no_final_fit138=True,no_PRED=True,no_champion_change=True,workers=4,seed=2026,decision='exploratory gains >=.01 grouped, no RMSE/MAE harm>.01 vs CT3 or EQUAL3; absolute geographic bias harm<=.02; spatial omission harm<=.01; both intraprofile weights no harm>.01; no statistical superiority claim')
    (OUT/'frozen_design.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    (OUT/'report/design.md').write_text('# R1–R3: diseño congelado antes de entrenamiento\n\nR1 mezcla global regularizada hacia promedio fijo. R2 mezcla municipal contraída hacia su mezcla global, municipios nuevos o con menos de15 parcelas/2 perfiles usan global. R3 árbol pequeño que minimiza directamente SSE de predicción combinada, no clasificación de ganadores; puede quedar sin divisiones. Variables de compuerta: compact3+NDVI mayo. Fuera del rango marginal del entrenamiento usa global. Sin intercepto o corrección constante.\n\nCada candidato global/municipal/compuerta se ajusta en entrenamiento interno usando predicciones profundas honestas. Se valida exclusivamente en su fold interno retenido. Luego selección por OOF internas completas y ajuste del mezclador en entrenamiento externo con las OOF internas honestas originales. Se aplica a los expertos externos archivados sin modificarlos. Nunca reutilizar OOF externas para seleccionar reglas.\n\nLa media y escalas de predictores, objetivos y regularización se calculan solo en cada entrenamiento. Los expertos profundos GPR y CatBoost conservan configuración y rejillas originales; CatBoost retunea en su CV aún más interna. CT3 profundo se recupera de caché previamente auditado. Los nombres municipales solo intervienen en R2. R3 no usa estado, municipio, coordenadas, rendimientos externos ni modelo ganador por parcela.\n\nSelección de R2/R3 incluye su regularización global conjuntamente, sin fijarla con etiquetas internas que después se usan para validar la regla. Soporte y fallback se reportan por protocolo. La transferencia a municipios no vistos evalúa exclusivamente el fallback R2, no una regla municipal aprendida con sus etiquetas. Comparaciones externas son exploratorias sobre etiquetas reutilizadas. Sin ajuste final, PRED, promoción o ampliación de variables/experimentos.\n',encoding='utf-8')
    print('FROZEN',len(deep-inner),'new deep expert contexts;',cfg['expected_cb_fits'],'CB fits;',cfg['expected_gp_fits'],'GP fits',flush=True)

def fit_experts(key):
    t=pd.read_parquet(OLD/'cache/train138.parquet');ctx=joblib.load(OLD/'cache/base_contexts.joblib')[key];a=t.iloc[ctx['positions']];start=time.perf_counter();scores=[];logs=[]
    with threadpool_limits(limits=1):
        gp=CompactGPR(tuple(CORE)).fit(a,a[Y])
        for params in CB_GRID:
            loss=[]
            for tr,va in ctx['cv']:
                cb=BoostModel(CORE,'CatBoost',params).fit(a.iloc[tr],a.iloc[tr][Y]);loss.append(metrics(a.iloc[va][Y],cb.predict(a.iloc[va]))['rmse']);logs+=cb.warnings_
            scores.append(float(np.mean(loss)))
        best=min(range(len(scores)),key=lambda i:(round(scores[i],10),i));cb=BoostModel(CORE,'CatBoost',CB_GRID[best]).fit(a,a[Y]);logs+=cb.warnings_
    record=dict(key=key,protocol=ctx['protocol'],n_train=len(a),train_ids=a[ID].tolist(),candidate=best,scores=scores,cb_fits=8*len(ctx['cv'])+1,gp_fits=1,gp_parameters=gp.parameters(),cb_warnings=logs,seconds=time.perf_counter()-start)
    joblib.dump(dict(gp=gp,cb=cb,registry=record),OUT/'models'/f'EXPERTS_{key}.joblib',compress=3)
    print('Deep experts',key,ctx['protocol'],round(record['seconds'],1),'s',flush=True);return record

def build_predictions(index):
    t=pd.read_parquet(OLD/'cache/train138.parquet');plan=joblib.load(OLD/'cache/execution_plan.joblib')[index];ctx=joblib.load(OLD/'cache/base_contexts.joblib');ep=joblib.load(OUT/'cache/expert_plan.joblib');inner=[];ledger=[]
    for j,item in enumerate(plan['inner']):
        aa=item['train_positions'];bb=item['validation_positions'];mapping={int(k):i for i,k in enumerate(aa)};matrix=np.full((len(aa),3),np.nan)
        for deep in item['residual_contexts']:
            key=deep['base_key'];dd=deep['held_positions'];fitpos=ctx[key]['positions'];assert not set(fitpos)&set(dd) and not (set(fitpos)|set(dd))&set(bb) and not (set(fitpos)|set(dd))&set(plan['validation_positions'])
            en=joblib.load(OLD/'base_cache'/f'{key}.joblib')['model']
            if key in ep['gp_paths']:
                gp=joblib.load(ROOT/ep['gp_paths'][key]);pack=joblib.load(PREVIOUS/'models'/f'CB_{key}.joblib');cb=pack['model'];assert pack['registry']['train_ids']==t.iloc[fitpos][ID].tolist()
            else:
                pack=joblib.load(OUT/'models'/f'EXPERTS_{key}.joblib');gp,cb=pack['gp'],pack['cb'];assert pack['registry']['train_ids']==t.iloc[fitpos][ID].tolist()
            matrix[[mapping[int(k)] for k in dd]]=np.column_stack([m.predict(t.iloc[dd]) for m in [en,gp,cb]])
            ledger.append(dict(outer_index=index,inner_index=j,base_key=key,expert_train_ids=json.dumps(t.iloc[fitpos][ID].tolist()),meta_training_ids=json.dumps(t.iloc[dd][ID].tolist()),meta_validation_ids=json.dumps(t.iloc[bb][ID].tolist()),outer_validation_ids=json.dumps(t.iloc[plan['validation_positions']][ID].tolist()),exclusions_verified=True))
        assert np.isfinite(matrix).all();inner.append(dict(train_positions=aa,validation_positions=bb,training_predictions=matrix))
    joblib.dump(dict(inner=inner,ledger=ledger),OUT/'cache'/f'INNER_{index:02d}.joblib',compress=3)

def fold(index):
    t=pd.read_parquet(OLD/'cache/train138.parquet');plan=joblib.load(OLD/'cache/execution_plan.joblib')[index];tr=plan['train_positions'];va=plan['validation_positions'];original=joblib.load(PREVIOUS/'checkpoints'/f'{index:02d}.joblib');honest=pd.DataFrame(original['inner']).set_index(ID).reindex(t.iloc[tr][ID]);inside=honest[['ct3','gpr','catboost']].to_numpy();lookup={int(k):i for i,k in enumerate(tr)}
    outerframe=pd.DataFrame(original['predictions']);outer=np.column_stack([outerframe[outerframe.experiment==name].set_index(ID).reindex(t.iloc[va][ID]).y_pred for name in NAMES]);deep=joblib.load(OUT/'cache'/f'INNER_{index:02d}.joblib');common=dict(protocol=plan['protocol'],repeat=plan['repeat'],fold=plan['fold']);rows=[];tuning=[];regs=[];rules=[];fits=0
    for name,configs in CONFIGS.items():
        candidates=[]
        for ci,params in enumerate(configs):
            prediction=np.full(len(tr),np.nan)
            for item in deep['inner']:
                aa,bb=item['train_positions'],item['validation_positions'];model=Mixture(name,params).fit(t.iloc[aa],item['training_predictions']);fits+=1;ix=[lookup[int(k)] for k in bb];prediction[ix]=model.predict(t.iloc[bb],inside[ix])
            candidates.append(dict(candidate=ci,params=params,**metrics(t.iloc[tr][Y],prediction)))
        chosen=min(candidates,key=lambda z:(round(z['rmse'],10),z['candidate']));model=Mixture(name,chosen['params']).fit(t.iloc[tr],inside);fits+=1;pred=model.predict(t.iloc[va],outer);weights,route=model.weights(t.iloc[va])
        rows.extend(dict(experiment=name,**common,ID_POLIGONO=pid,y_true=float(y),y_pred=float(v),w_ct3=float(w[0]),w_gpr=float(w[1]),w_catboost=float(w[2]),route=str(r)) for pid,y,v,w,r in zip(t.iloc[va][ID],t.iloc[va][Y],pred,weights,route))
        reg=dict(experiment=name,**common,params=json.dumps(chosen['params']),inner_rmse=chosen['rmse'],global_weights=model.global_weights.tolist(),municipal_rules=len(model.regions),tree_splits=sum(n['feature']>=0 for n in model.nodes),fraction_fallback=float(np.mean(np.isin(route,['global','outside_support_global','root_global']))));regs.append(reg)
        tuning.extend(dict(experiment=name,**common,**{**z,'params':json.dumps(z['params'])},selected=z is chosen) for z in candidates)
        for zone,r in model.regions.items():rules.append(dict(experiment=name,**common,type='municipal',zone='::'.join(zone),weights=json.dumps(r['weights'].tolist()),n=r['n'],n_profiles=r['n_profiles']))
        for ni,n in enumerate(model.nodes):
            feature=model.feature_names[n['feature']] if n['feature']>=0 else ''
            raw=None
            if feature:
                j=CORE.index(feature);raw=float(n['threshold']*model.transform.scale_[j]+model.transform.mean_[j])
            rules.append(dict(experiment=name,**common,type='tree',node=ni,feature=feature,threshold_original=raw,left=n['left'],right=n['right'],weights=json.dumps(n['weights'].tolist()),n=n['n'],n_profiles=n['n_profiles'],depth=n['depth']))
        paths=files(plan)[0];joblib.dump(dict(mixture=model,expert_paths=[p.relative_to(ROOT).as_posix() for p in paths],registry=reg),OUT/'models'/f'{name}_{index:02d}.joblib',compress=3)
    joblib.dump(dict(predictions=rows,tuning=tuning,registry=regs,rules=rules,meta_fits=fits),OUT/'checkpoints'/f'{index:02d}.joblib',compress=3)
    print('Rules',index+1,'/65',plan['protocol'],[(r['experiment'],r['params'],r['tree_splits'],r['municipal_rules']) for r in regs],flush=True)

def finish(wall):
    packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(65)];new=pd.DataFrame([r for p in packs for r in p['predictions']]);assert len(new)==5382
    new.to_parquet(OUT/'tables/oof_predictions.parquet',index=False);new.to_csv(OUT/'tables/oof_predictions.csv',index=False)
    for name in ['tuning','registry','rules']:pd.DataFrame([r for p in packs for r in p[name]]).to_csv(OUT/'tables'/f'{name}.csv',index=False)
    ledger=pd.DataFrame([r for i in range(65) for r in joblib.load(OUT/'cache'/f'INNER_{i:02d}.joblib')['ledger']]);ledger.to_csv(OUT/'audit/nested_exclusions.csv',index=False)
    expert_records=[joblib.load(p)['registry'] for p in (OUT/'models').glob('EXPERTS_*.joblib')]
    pd.DataFrame([{**r,'train_ids':json.dumps(r['train_ids']),'scores':json.dumps(r['scores']),'gp_parameters':json.dumps(r['gp_parameters']),'cb_warnings':json.dumps(r['cb_warnings'])} for r in expert_records]).to_csv(OUT/'tables/deep_expert_registry.csv',index=False)
    refs=pd.read_parquet(PREVIOUS/'tables/oof_predictions.parquet');allp=pd.concat([new,refs],ignore_index=True);t=pd.read_parquet(OLD/'cache/train138.parquet');allp=allp.merge(t[[ID,'Estado','Municipio','climate_profile']],on=ID,validate='many_to_one');repeat=[];local=[];regional=[];omit=[];paired=[];gains=[]
    for (exp,pro,re),g in allp.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g[ID].is_unique;repeat.append(dict(experiment=exp,protocol=pro,repeat=re,**metrics(g.y_true,g.y_pred)));local.append(dict(experiment=exp,protocol=pro,repeat=re,**pair_metrics(g)))
        for field in ['fold','Estado','Municipio']:
            for zone,h in g.groupby(field):regional.append(dict(experiment=exp,protocol=pro,repeat=re,group_type=field,group=zone,n=len(h),**metrics(h.y_true,h.y_pred)))
        for field in ['fold','Municipio']:
            for zone in g[field].unique():
                h=g[g[field]!=zone];omit.append(dict(experiment=exp,protocol=pro,repeat=re,omitted_type=field,omitted=zone,**metrics(h.y_true,h.y_pred)))
    rm=pd.DataFrame(repeat);rm.to_csv(OUT/'tables/metrics_repeat.csv',index=False);summary=rm.groupby(['experiment','protocol'])[['rmse','mae','bias']].mean().reset_index();summary.to_csv(OUT/'tables/metrics_summary.csv',index=False)
    pd.DataFrame(local).groupby(['experiment','protocol']).mean(numeric_only=True).reset_index().to_csv(OUT/'tables/intraprofile_summary.csv',index=False);pd.DataFrame(regional).to_csv(OUT/'tables/regional_repeat.csv',index=False);pd.DataFrame(omit).to_csv(OUT/'tables/omissions.csv',index=False)
    for name in CONFIGS:
        for ref in ['C-T3','EQUAL3','R1']:
            if ref==name:continue
            q=allp[allp.experiment==name].merge(allp[allp.experiment==ref],on=['protocol','repeat','fold',ID],suffixes=('_new','_ref'),validate='one_to_one');np.testing.assert_allclose(q.y_true_new,q.y_true_ref)
            for (pro,re),g in q.groupby(['protocol','repeat']):
                a=metrics(g.y_true_new,g.y_pred_new);b=metrics(g.y_true_ref,g.y_pred_ref);paired.append(dict(experiment=name,reference=ref,protocol=pro,repeat=re,**{f'delta_{k}':a[k]-b[k] for k in a}))
            gains.extend(dict(experiment=name,reference=ref,protocol=r.protocol,repeat=r.repeat,fold=r.fold,ID_POLIGONO=getattr(r,ID),sse_gain=(r.y_pred_ref-r.y_true_ref)**2-(r.y_pred_new-r.y_true_new)**2) for r in q.itertuples())
    pd.DataFrame(paired).to_csv(OUT/'tables/paired_repeat.csv',index=False);pd.DataFrame(gains).to_parquet(OUT/'tables/parcel_gains.parquet',index=False)
    replay=[]
    for i,plan in enumerate(joblib.load(OLD/'cache/execution_plan.joblib')):
        v=t.iloc[plan['validation_positions']]
        for name in CONFIGS:
            pack=joblib.load(OUT/'models'/f'{name}_{i:02d}.joblib');models=[joblib.load(ROOT/p) for p in pack['expert_paths']];models[0]=models[0]['model'];matrix=np.column_stack([m.predict(v) for m in models]);p=pack['mixture'].predict(v,matrix);q=new[(new.experiment==name)&(new.protocol==plan['protocol'])&(new['repeat']==plan['repeat'])&(new.fold==plan['fold'])].set_index(ID).reindex(v[ID]);difference=float(np.max(abs(p-q.y_pred)));assert difference<1e-10;replay.append(dict(index=i,experiment=name,max_difference=difference))
    pd.DataFrame(replay).to_csv(OUT/'audit/model_replay.csv',index=False)
    verify_protected()
    (OUT/'report/results.md').write_text('# R1–R3: resultados\n\n```text\n'+summary.to_string(index=False)+'\n```\n\nResultados exploratorios, sin superioridad estadística demostrada.\n',encoding='utf-8')
    (OUT/'manifest.json').write_text(json.dumps(dict(status='complete',new_cb_fits=sum(r['cb_fits'] for r in expert_records),new_gp_fits=len(expert_records),new_ct3_fits=0,meta_fits=sum(p['meta_fits'] for p in packs),n_oof=5382,n_model_packs=195,replayed_models=195,wall_seconds=wall,no_final_fit138=True,no_PRED=True,no_champion_change=True,artifacts={p.relative_to(ROOT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json'}),indent=2),encoding='utf-8');print(summary.to_string(index=False),flush=True)

def verify_protected():
    correction=OUT/'audit/implementation_fix.json'
    fixes=json.loads(correction.read_text()) if correction.exists() else {}
    for r in pd.read_csv(OUT/'audit/protected_inputs.csv').itertuples():
        if r.path in fixes:
            f=fixes[r.path];assert f['original_sha256']==r.sha256
            assert sha(ROOT/f['archived_original'])==r.sha256
            assert sha(ROOT/r.path)==f['corrected_sha256']
        else:assert sha(ROOT/r.path)==r.sha256

def run():
    if (OUT/'manifest.json').exists():raise FileExistsError('Completed version immutable')
    verify_protected()
    ep=joblib.load(OUT/'cache/expert_plan.joblib');start=time.perf_counter();missing=[k for k in ep['new_keys'] if not (OUT/'models'/f'EXPERTS_{k}.joblib').exists()]
    joblib.Parallel(n_jobs=4,backend='loky',inner_max_num_threads=1)(joblib.delayed(fit_experts)(k) for k in missing)
    with threadpool_limits(limits=1):
        for i in range(65):build_predictions(i);fold(i)
    finish(time.perf_counter()-start)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');args=parser.parse_args()
    prepare() if args.prepare else run()
