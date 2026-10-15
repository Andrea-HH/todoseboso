"""Original Local04D + CT3 support blend, with a matched unshrunk control."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import KFold
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.geoc_bridge import data,OLD,OUT as BRIDGE,local_prediction
from src.compact_geographic import support_factor
from src.geoc_support_blend import choose,blend,WEIGHTS
from src.family_8.research import subcv
from src.ct3_residual_conditional.models import tune_base
OUT=ROOT/'outputs/modeling/geoc_support_blend/v1'

def work(index):
    dest=OUT/'checkpoints'/f'{index:02d}.joblib'
    if dest.exists():return
    a=data();t=a['train'];pos=a['train_global'];y=t.RENDIMIENTO_T_HA.to_numpy();d=a['distance'];groups=pd.read_csv(OLD/'cache/groups.csv').set_index('ID_POLIGONO');logs=[]
    if index<65:
        plan=joblib.load(OLD/'cache/execution_plan.joblib')[index];tr=plan['train_positions'];va=plan['validation_positions'];pro=plan['protocol'];re=plan['repeat'];fold=plan['fold'];ct3=joblib.load(OLD/'base_cache'/f'{plan["outer_base_key"]}.joblib')['model'];contexts=[];lookup={int(v):i for i,v in enumerate(tr)}
        for item in plan['inner']:
            aa=item['train_positions'];bb=item['validation_positions'];ct=joblib.load(OLD/'base_cache'/f'{item["base_key"]}.joblib')['model'];contexts.append((aa,bb,np.array([lookup[int(v)] for v in bb]),ct))
    else:
        membership=pd.read_csv(BRIDGE/'cache/geoc_memberships.csv');split=sorted(membership.split_id.unique())[index-65];g=membership[membership.split_id==split];lookup={v:i for i,v in enumerate(t.ID_POLIGONO)};tr=np.array([lookup[v] for v in g[g.role=='pseudo_train'].ID_POLIGONO]);va=np.array([lookup[v] for v in g[g.role=='pseudo_target'].ID_POLIGONO]);pro='geoc_target_matched';re=int(split.rsplit('_',1)[1]);fold=1;ct3=joblib.load(BRIDGE/'models'/f'{split}.joblib')['ct3'];contexts=[]
        for c,e in KFold(4,shuffle=True,random_state=2026).split(tr):
            aa=tr[c];bb=tr[e]
            with threadpool_limits(limits=1):ct,registry,ww=tune_base(t,y,aa,subcv(t,aa,'random',groups))
            logs.extend(ww);contexts.append((aa,bb,e,ct))
    ci=np.full(len(tr),np.nan);li=ci.copy();si=ci.copy();ledger=[]
    with threadpool_limits(limits=1):
        for aa,bb,where,m in contexts:
            assert not set(aa)&(set(bb)|set(va))
            ci[where]=m.predict(t.iloc[bb]);li[where]=local_prediction(a['x'],d,pos[aa],pos[bb],y[aa]);si[where]=support_factor(d,pos[aa],pos[bb],24)
            ledger.append(dict(training=aa.tolist(),inner_validation=bb.tolist(),external_validation=va.tolist()))
        assert np.isfinite(np.column_stack([ci,li,si])).all()
        ct=ct3.predict(t.iloc[va]);local=local_prediction(a['x'],d,pos[tr],pos[va],y[tr]);support=support_factor(d,pos[tr],pos[va],24)
        rows=[];selection=[];weights={}
        for name,sin,sout in [('ORIGINAL_LOCAL_SUPPORT',si,support),('MATCHED_PLAIN_BLEND',np.ones(len(tr)),np.ones(len(va)))]:
            w,scores=choose(y[tr],ci,li,sin);weights[name]=w;p=blend(ct,local,w,sout)
            selection.append(dict(experiment=name,protocol=pro,repeat=re,fold=fold,weight=w,inner_rmse=float(np.sqrt(min(scores))),median_support=float(np.median(sout)),mean_effective_local_weight=float(np.mean(w*sout))))
            rows.extend(dict(experiment=name,protocol=pro,repeat=re,fold=fold,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(v),support=float(s),effective_local_weight=float(w*s)) for i,v,s in zip(va,p,sout))
    joblib.dump(dict(ct3=ct3,weights=weights,train_positions=tr,validation_positions=va,ledger=ledger),OUT/'models'/f'{index:02d}.joblib',compress=3)
    joblib.dump(dict(predictions=rows,selection=selection,warnings=logs),dest,compress=3);print(f'original support {index+1}/81 {pro}',flush=True)

if __name__=='__main__':
    if (OUT/'execution_complete.json').exists():raise FileExistsError('Preserve complete version')
    for s in ['models','checkpoints','tables','audit']:(OUT/s).mkdir(parents=True,exist_ok=True)
    paths=[Path(__file__),ROOT/'src/geoc_support_blend.py',ROOT/'src/compact_geographic.py',ROOT/'src/geoc_bridge.py',ROOT/'src/geoc_local04d_snapshot.py',ROOT/'src/ct3_residual_conditional/models.py',BRIDGE/'cache/prepared.joblib',BRIDGE/'cache/geoc_memberships.csv',BRIDGE/'tables/oof_predictions.parquet',OLD/'cache/execution_plan.joblib',OLD/'cache/groups.csv']+list((OLD/'base_cache').glob('*.joblib'))+list((BRIDGE/'models').glob('*.joblib'))
    cfg=dict(scope='Original Local04D with CT3, support-conditioned convex blend plus matched constant-weight control. No new variables, no compact local replacement, no residual model.',local='Exactly archived original C4 PCA20, k24, alpha30, power1,197-X transductive representation',weights=WEIGHTS,support='Existing fixed X-only support: min(1, median training leave-one-out24th neighbor distance / query24th training neighbor distance); no municipal rules',selection='complete inner OOF MSE; rounded12 ties favor smaller Local weight; original inner splits, inner CT3 selection excludes validation; Local parameters never retuned',banks='65 original folds plus16 original97/41 GeoC masks; frozen97/41 development, not confirmation08',statistics='Primary support blend vsCT3/Local04D/plain matched in each5 protocols,15 comparisons Holm; exploratory fixed-prediction cluster resampling',no_final_fit=True,no_new59_PRED=True,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    f=OUT/'frozen_design.json'
    if f.exists():assert json.loads(f.read_text())==cfg
    else:f.write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    joblib.Parallel(n_jobs=4,backend='loky')(joblib.delayed(work)(i) for i in range(81))
    packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(81)];p=pd.DataFrame([r for q in packs for r in q['predictions']]);assert len(p)==4900
    p.to_parquet(OUT/'tables/new_oof_predictions.parquet',index=False);p.to_csv(OUT/'tables/new_oof_predictions.csv',index=False);pd.DataFrame([r for q in packs for r in q['selection']]).to_csv(OUT/'tables/selection.csv',index=False)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in cfg['source_sha256'].items())
    (OUT/'execution_complete.json').write_text(json.dumps(dict(status='complete',new_oof=4900,new_external_predictors=162,warnings=sum(len(q['warnings']) for q in packs),protected_sources_preserved=True),indent=2),encoding='utf-8')
