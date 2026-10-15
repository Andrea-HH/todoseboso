"""Prepare/freeze, then run bounded physical representation sensitivity."""
from pathlib import Path
import sys,json,time,warnings,hashlib
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.geoc_bridge import data,OLD
from src.physical_similarity import ResidualCorrector,select_candidate,GRIDS
from src.physical_representation import PhysicalRepresentation,MODES
OUT=ROOT/'outputs/modeling/physical_representation/v1';PREV=ROOT/'outputs/modeling/physical_similarity/v2'

def prepare():
    if (OUT/'frozen_design.json').exists():raise FileExistsError('Preserve design')
    for p in ['cache','audit','models','checkpoints','tables','diagnostics']:(OUT/p).mkdir(parents=True,exist_ok=True)
    previous=json.loads((PREV/'frozen_design.json').read_text());b=previous['blocks'];atoms={}
    def add(name,cols,composition=False,summary=None):
        assert cols,name
        atoms[name]=dict(columns=cols,summary=summary or cols,composition=composition)
    r=b['relief']
    for name,patterns in [('slope',['slope_']),('local_relief',['local_relief_']),('position',['tpi_']),('curvature',['curvature_']),('terrain_water',['flow_accumulation','twi_'])]:
        cols=[c for c in r if any(p in c for p in patterns)]
        summary=[c for c in cols if c.endswith(('_mean','_std','pct_area_slope_gt_10'))]
        add(name,cols,summary=summary)
    add('geologic_composition',[c for c in b['geology_physiography'] if 'geo250_share__' in c],True)
    add('geologic_distances',[c for c in b['geology_physiography'] if 'distance_' in c])
    add('soil_composition',[c for c in b['soil_inegi'] if 'soil_unit_share__' in c],True)
    add('soil_texture_phase',[c for c in b['soil_inegi'] if c.endswith(('dominant_texture','dominant_physical_phase'))])
    add('soil_mixture_boundaries',[c for c in b['soil_inegi'] if not ('soil_unit_share__' in c or c.endswith(('dominant_texture','dominant_physical_phase')))])
    for name,props in [('soilgrids_physical',['bdod','cfvo','clay','sand','silt']),('soilgrids_chemical',['cec','nitrogen','phh2o','soc'])]:
        cols=[c for c in b['soilgrids'] if any('__'+p+'__' in c for p in props)]
        add(name,cols,summary=[c for c in cols if c.endswith('depth_weighted_0_30cm')])
    add('erosion_composition',b['erosion'],True)
    add('altitude_sensitivity',b['altitude_sensitivity'],summary=[c for c in b['altitude_sensitivity'] if c.endswith(('elevation_mean','elevation_std'))])
    specs={a:[a] for a in atoms};specs.update(GEOLOGY=['geologic_composition','geologic_distances'],TERRAIN=['slope','local_relief','position','curvature','terrain_water'],SOIL=['soil_composition','soil_texture_phase','soil_mixture_boundaries','soilgrids_physical','soilgrids_chemical'],PHYSICAL_ALL=[a for a in atoms if a!='altitude_sensitivity'])
    features=pd.read_parquet(PREV/'cache/features138_target_free.parquet');features[['ID_POLIGONO']+list(dict.fromkeys(c for a in atoms.values() for c in a['columns']))].to_parquet(OUT/'cache/features138_target_free.parquet',index=False)
    files=[Path(__file__),ROOT/'src/physical_representation.py',ROOT/'src/physical_similarity.py',ROOT/'tests/test_physical_representation.py',ROOT/'documentation/physical_representation_design.md',PREV/'frozen_design.json',PREV/'cache/features138_target_free.parquet',OLD/'cache/execution_plan.joblib',OLD/'cache/frozen65_splits.joblib']+list((OLD/'base_cache').glob('*.joblib'))
    cfg=dict(atoms=atoms,specs=specs,modes=MODES,grids=GRIDS,amplitudes=[0.,.25,.5],selection='Full internal OOF MSE; ties smaller amplitude, mode order summary,pca1,pca3,pca5,pca8,raw, grid order; selector ties spec and family order. Altitude excluded from omnibus selectors.',composition='raw shares or square roots; center on training; no column variance division or RMS normalization; PCA on centered roots, no whitening. Fixed 1/sqrt(number blocks) concatenation.',continuous='Training median/onehot, standardization and training RMS normalization; PCA <=1/3/5/8; summary fixed means/stds, depth weighted 0-30cm; log1p of nonnegative distances in summary only.',frozen_schema='Inherited X-only138 coverage and aliases; no new Y feature screening; numeric transformations fit within each training context',evaluation='Same65 outer and frozen inner folds/deep CT3 residual caches; no GeoC97/41, final138 fit or PRED; subsequent exploratory sensitivity informed by earlier external folds, not independent confirmation',source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in dict.fromkeys(files)})
    (OUT/'frozen_design.json').write_text(json.dumps(cfg,indent=2,ensure_ascii=False),encoding='utf-8')
    pd.DataFrame([dict(atom=a,n_features=len(s['columns']),n_summary=len(s['summary']),composition=s['composition']) for a,s in atoms.items()]).to_csv(OUT/'audit/subblocks.csv',index=False)
    print('FROZEN:',len(atoms),'atoms',len(specs),'specs; 54 block/family recipes, internal selector and six mode selectors')

def work(fi):
    checkpoint=OUT/'checkpoints'/f'{fi:02d}.joblib'
    if checkpoint.exists():return
    start=time.perf_counter();cfg=json.loads((OUT/'frozen_design.json').read_text());t=data()['train'];x=pd.read_parquet(OUT/'cache/features138_target_free.parquet');assert x.ID_POLIGONO.tolist()==t.ID_POLIGONO.tolist();y=t.RENDIMIENTO_T_HA.to_numpy()
    plan=joblib.load(OLD/'cache/execution_plan.joblib')[fi];tr=np.asarray(plan['train_positions']);va=np.asarray(plan['validation_positions']);lookup={int(v):i for i,v in enumerate(tr)};key=dict(protocol=plan['protocol'],repeat=plan['repeat'],fold=plan['fold']);cf=np.full(len(tr),np.nan);contexts=[];ledger=[]
    def base(k):return joblib.load(OLD/'base_cache'/f'{k}.joblib')
    for item in plan['inner']:
        aa=np.asarray(item['train_positions']);bb=np.asarray(item['validation_positions']);where=np.array([lookup[int(v)] for v in bb]);b=base(item['base_key']);assert set(b['registry']['train_ids'])==set(t.iloc[aa].ID_POLIGONO);cf[where]=b['model'].predict(t.iloc[bb]);deep=np.full(len(aa),np.nan);mapping={int(v):i for i,v in enumerate(aa)}
        for ctx in item['residual_contexts']:
            dd=ctx['held_positions'];b=base(ctx['base_key']);excluded=set(t.iloc[np.r_[dd,bb,va]].ID_POLIGONO);assert not set(b['registry']['train_ids'])&excluded;deep[[mapping[int(v)] for v in dd]]=b['model'].predict(t.iloc[dd]);ledger.append(dict(base_key=ctx['base_key'],excluded_ids=sorted(excluded),verified=True))
        assert np.isfinite(deep).all();contexts.append(dict(aa=aa,bb=bb,where=where,residual=y[aa]-deep))
    assert np.isfinite(cf).all();ct3=base(plan['outer_base_key'])['model'];ct=ct3.predict(t.iloc[va]);targets=y[tr]-cf;rows=[];selections=[];tuning=[];saved={};all_candidates=[]
    with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        # Cache transforms per training context/atom/mode; never cache validation fits.
        outer={};inner=[{} for _ in contexts]
        for mode,k in cfg['modes']:
            for atom,s in cfg['atoms'].items():
                m=PhysicalRepresentation(**s,mode=mode,components=k).fit(x.iloc[tr]);outer[(atom,mode)]=(m,m.transform(x.iloc[tr]),m.transform(x.iloc[va]))
                for j,ctx in enumerate(contexts):
                    m=PhysicalRepresentation(**s,mode=mode,components=k).fit(x.iloc[ctx['aa']]);inner[j][(atom,mode)]=(m.transform(x.iloc[ctx['aa']]),m.transform(x.iloc[ctx['bb']]))
        for spec,atoms in cfg['specs'].items():
            for kind,grid in cfg['grids'].items():
                name=spec+'__'+kind;choices=[]
                for mode,k in cfg['modes']:
                    deltas=[]
                    for params in grid:
                        delta=np.full(len(tr),np.nan)
                        for ctx,rep in zip(contexts,inner):
                            zz=np.column_stack([rep[(a,mode)][0] for a in atoms])/np.sqrt(len(atoms));qq=np.column_stack([rep[(a,mode)][1] for a in atoms])/np.sqrt(len(atoms));m=ResidualCorrector(kind,params).fit(zz,ctx['residual']);delta[ctx['where']]=m.predict(qq)
                        assert np.isfinite(delta).all();deltas.append(delta)
                    best,records=select_candidate(y[tr],cf,deltas,grid)
                    choice=dict(mode=mode,components=k,**best);choices.append(choice);tuning.extend(dict(**key,experiment=name,mode=mode,**r) for r in records)
                order={m:i for i,(m,k) in enumerate(cfg['modes'])};best=min(choices,key=lambda r:(round(r['mse'],12),r['amplitude'],order[r['mode']],r['candidate']))
                mode=best['mode'];amp=best['amplitude'];zz=np.column_stack([outer[(a,mode)][1] for a in atoms])/np.sqrt(len(atoms));qq=np.column_stack([outer[(a,mode)][2] for a in atoms])/np.sqrt(len(atoms));m=ResidualCorrector(kind,best['params']).fit(zz,targets) if amp else None;pred=ct+amp*m.predict(qq) if amp else ct.copy()
                saved[name]=dict(model=m,representations=[outer[(a,mode)][0] for a in atoms],selection=best,atoms=atoms);all_candidates.append(dict(name=name,spec=spec,kind=kind,best=best,pred=pred))
                selections.append(dict(**key,experiment=name,spec=spec,kind=kind,mode=mode,amplitude=amp,params=json.dumps(best['params']),inner_rmse=float(np.sqrt(best['mse'])),n_components=zz.shape[1]))
                rows.extend(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(v)) for i,v in zip(va,pred))
        def choice_key(c):return (round(c['best']['mse'],12),c['best']['amplitude'],list(cfg['specs']).index(c['spec']),list(cfg['grids']).index(c['kind']))
        winner=min([c for c in all_candidates if c['spec']!='altitude_sensitivity'],key=choice_key)
        selected_names={}
        def store_selector(name,w):
            selected_names[name]=w['name'];rows.extend(dict(**key,experiment=name,ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(v)) for i,v in zip(va,w['pred']));selections.append(dict(**key,experiment=name,spec=w['spec'],kind=w['kind'],mode=w['best']['mode'],amplitude=w['best']['amplitude'],params=json.dumps(w['best']['params']),inner_rmse=float(np.sqrt(w['best']['mse'])),selected_variant=w['name']))
        store_selector('INTERNAL_SELECTOR',winner)
        # Fixed-mode selectors need candidates tuned within that mode, not the mode-winning candidates above.
        # Their full fits reuse the same honest targets; they provide direct matched representation controls.
        for mode,k in cfg['modes']:
            candidates=[]
            for spec,atoms in cfg['specs'].items():
                if spec=='altitude_sensitivity':continue
                for kind,grid in cfg['grids'].items():
                    records=[r for r in tuning if r['experiment']==spec+'__'+kind and r['mode']==mode];best=min(records,key=lambda r:(round(r['mse'],12),r['amplitude'],r['candidate']));candidates.append(dict(name=spec+'__'+kind,spec=spec,kind=kind,best=best))
            win=min(candidates,key=choice_key);atoms=cfg['specs'][win['spec']];amp=win['best']['amplitude'];zz=np.column_stack([outer[(a,mode)][1] for a in atoms])/np.sqrt(len(atoms));qq=np.column_stack([outer[(a,mode)][2] for a in atoms])/np.sqrt(len(atoms));m=ResidualCorrector(win['kind'],win['best']['params']).fit(zz,targets) if amp else None;pred=ct+amp*m.predict(qq) if amp else ct.copy();name='MODE_'+mode
            win['best']=dict(win['best'],mode=mode);win['pred']=pred;store_selector(name,win);saved[name]=dict(model=m,representations=[outer[(a,mode)][0] for a in atoms],selection=win['best'],atoms=atoms)
        rows.extend(dict(**key,experiment='CT3',ID_POLIGONO=t.iloc[i].ID_POLIGONO,y_true=float(y[i]),y_pred=float(v)) for i,v in zip(va,ct))
        joblib.dump(dict(ct3=ct3,correctors=saved,selected_variant=winner['name'],train_positions=tr,validation_positions=va,ledger=ledger),OUT/'models'/f'{fi:02d}.joblib',compress=3)
    joblib.dump(dict(predictions=rows,selection=selections,tuning=tuning,warnings=[dict(category=w.category.__name__,message=str(w.message)) for w in caught],seconds=time.perf_counter()-start),checkpoint,compress=3)
    print(f'representation {fi+1}/65 {key["protocol"]} {time.perf_counter()-start:.1f}s',flush=True)

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    else:
        if (OUT/'execution_complete.json').exists():raise FileExistsError('Preserve complete run')
        cfg=json.loads((OUT/'frozen_design.json').read_text());assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in cfg['source_sha256'].items());start=time.perf_counter()
        joblib.Parallel(n_jobs=4,backend='loky')(joblib.delayed(work)(i) for i in range(65))
        packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(65)]
        for field in ['predictions','selection','tuning']:
            d=pd.DataFrame([r for q in packs for r in q[field]])
            if field=='tuning':d['params']=d.params.map(json.dumps)
            d.to_parquet(OUT/'tables'/f'{field}.parquet',index=False)
        logs=[r for q in packs for r in q['warnings']];(OUT/'audit/warnings.json').write_text(json.dumps(logs,indent=2),encoding='utf-8')
        assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in cfg['source_sha256'].items())
        (OUT/'execution_complete.json').write_text(json.dumps(dict(status='complete',folds=65,recipes=61,seconds=time.perf_counter()-start,warnings=len(logs),protected_sources_unchanged=True,no_final138_fit=True,no_PRED=True),indent=2),encoding='utf-8')
