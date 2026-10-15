"""Freeze and execute bounded complements; resume only unchanged designs."""
from pathlib import Path
import sys,json,hashlib,time
import numpy as np
import pandas as pd
import joblib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.calendar_complements import OUT,OLD,fold

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare():
    if (OUT/'manifest.json').exists():raise FileExistsError('Completed run preserved')
    for s in ['models','checkpoints','context_cache','tables','audit']:(OUT/s).mkdir(parents=True,exist_ok=True)
    source=ROOT/'outputs/modeling/agronomic_calendar/expansion/v1'
    specs=json.loads((source/'frozen_design.json').read_text())['specs'];core=specs['CAL00']['columns'];cal=specs['CAL02']['columns']
    reps=dict(COMPACT4=core,CAL02=cal,WINDOW_SHAPES7=cal[:4]+core[1:3]+[core[-1]],UNION11=cal+core[1:3],COMPACT_TMAX8=core+cal[4:8])
    w=['pre_apr','sowing_may_jun','post_jul_aug','late_sep_oct']
    veg=['CURRENT_CAL_S2_'+i+'_'+v for i in ['ndvi','evi','ndwi','msi'] for v in w]+['CURRENT_CAL_S2_ndvi_spatial_std_post_jul_aug']
    ctx=core[1:];slope=['TOPO_BASIC_slope_mean'];hist=['HIST_S2_ndvi_promedio_mean','HIST_S2_ndvi_promedio_std']
    ridge=[dict(alpha=a) for a in [1.,.1,.01]]
    tree=[dict(max_depth=d,min_samples_leaf=n,ccp_alpha=0.) for d in [1,2] for n in [25,15]]
    corrections=dict(VEG_RIDGE=dict(columns=veg,kind='ridge',grid=ridge),VEG_CONTEXT_CART=dict(columns=ctx+veg,kind='tree',grid=tree),CONTEXT_CART=dict(columns=ctx,kind='tree',grid=tree),SLOPE_RIDGE=dict(columns=slope,kind='ridge',grid=ridge),HISTORY_RIDGE=dict(columns=hist,kind='ridge',grid=ridge))
    inputs=[source/'cache/features_train138.parquet',OLD/'train138.parquet',OLD/'frozen65_splits.joblib',ROOT/'outputs/modeling/family_7/expansion/v1/cache/train138_exact_features.parquet',ROOT/'outputs/modeling/family_7/expansion/v1/splits/group_memberships.csv',source/'tables/oof_predictions.parquet',ROOT/'src/calendar_complements.py',ROOT/'src/calendar_expansion.py',Path(__file__)]
    cfg=dict(representations=reps,corrections=corrections,en_grid=[dict(alpha=a,l1_ratio=l,gamma=1.) for a in [1.,.1,.01,.001] for l in [1.,.9,.5,.1]],amplitudes=[0,.25,.5],selection='complete inner OOF RMSE; rounded12 ties conservative grid order, zero amplitude first; representation selected solely inside each training context',outer_folds=65,residuals='honest nested crossfit: each residual observation excluded from base fitting AND hyperparameter/representation tuning; inner correction evaluation excludes inner validation; training-only imputation/scaling; centered correction, no intercept shift',limitations='exploratory reused labels; crossfit/refit base training-size mismatch remains; architecture and correction selection are not independent confirmation; no regional rules',scope='5 representations, internally selected base, 5 correctors; no CatBoost duplicate or LAI repeat; no final138 or59PRED',sha256={str(p.relative_to(ROOT)):sha(p) for p in inputs})
    path=OUT/'frozen_design.json'
    if path.exists():assert json.loads(path.read_text())==cfg
    else:path.write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    x=pd.read_parquet(inputs[0]);t=pd.read_parquet(inputs[1]);e=pd.read_parquet(inputs[3]).set_index('ID_POLIGONO')
    assert x.ID_POLIGONO.tolist()==t.ID_POLIGONO.tolist()
    for c in ['RENDIMIENTO_T_HA','Estado','Municipio','climate_profile']:x[c]=t[c].to_numpy()
    for c in slope+hist:x[c]=x.ID_POLIGONO.map(e[c])
    assert len(x)==138 and x.ID_POLIGONO.is_unique
    if (OUT/'features_train138.parquet').exists():pd.testing.assert_frame_equal(pd.read_parquet(OUT/'features_train138.parquet'),x)
    else:x.to_parquet(OUT/'features_train138.parquet',index=False)
    return cfg

if __name__=='__main__':
    cfg=prepare();start=time.perf_counter()
    joblib.Parallel(n_jobs=4,backend='loky')(joblib.delayed(fold)(i) for i in range(65))
    packs=[joblib.load(OUT/'checkpoints'/f'{i:02d}.joblib') for i in range(65)]
    p=pd.DataFrame([r for a in packs for r in a['predictions']]);assert len(p)==11*1794
    for name in ['predictions','registry','tuning']:
        pd.DataFrame([dict(protocol=a['protocol'],repeat=a['repeat'],fold=a['fold'],**r) if name!='predictions' else r for a in packs for r in a[name]]).to_parquet(OUT/'tables'/f'{name}.parquet',index=False)
    changed=[s for s,h in cfg['sha256'].items() if sha(ROOT/s)!=h];assert not changed
    (OUT/'audit/warnings.json').write_text(json.dumps([r for a in packs for r in a['warnings']],indent=2),encoding='utf-8')
    (OUT/'execution_complete.json').write_text(json.dumps(dict(new_configurations=11,external_folds=65,new_oof=len(p),seconds_last_segment=time.perf_counter()-start,warnings=sum(len(a['warnings']) for a in packs),protected_sources_unchanged=True),indent=2),encoding='utf-8')
