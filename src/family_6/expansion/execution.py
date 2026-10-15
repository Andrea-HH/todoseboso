"""F6-E1–E3 only, using the immutable F6 search engine in isolated workers."""
from contextlib import contextmanager
from pathlib import Path
import json,time,joblib
import numpy as np,pandas as pd
from threadpoolctl import threadpool_limits
from src.family_6 import execution as base
from src.family_6.models import GRID,N_TREES,SEED

ROOT=base.ROOT;ID=base.ID;TARGET=base.TARGET;CORE=base.CORE
OUT=ROOT/'outputs/modeling/family_6/expansion/v1'
BLOCKS={'F6-E1':base.design.HISTORY,'F6-E2':[base.design.SLOPE],'F6-E3':[base.prior.old.c.DTR]}
SPECS={name:dict(algorithm='ET',columns=CORE+columns) for name,columns in BLOCKS.items()}
INTERACTIONS={'F6-E0':[(CORE[0],CORE[-1])],'F6-E1':[(CORE[-1],base.design.HISTORY[0]),tuple(base.design.HISTORY)],'F6-E2':[(CORE[-1],base.design.SLOPE),(CORE[0],base.design.SLOPE)],'F6-E3':[(CORE[2],base.prior.old.c.DTR),(CORE[-1],base.prior.old.c.DTR)]}

def load():
    t=pd.read_parquet(OUT/'cache/train138_exact_features.parquet');splits=joblib.load(OUT/'cache/frozen65_splits.joblib')
    return None,t,splits

@contextmanager
def redirected_engine():
    """Process-local adapter; original code/artifacts unchanged; always restore globals."""
    previous=base.OUT,base.SPECS,base.load
    try:
        base.OUT=OUT;base.SPECS=SPECS;base.load=load
        yield
    finally:base.OUT,base.SPECS,base.load=previous

def prepare():
    if (OUT/'manifest.json').exists():raise FileExistsError('Completed F6-E immutable')
    for directory in ['audit','tables','models','checkpoints','cache','splits','figures','report']:(OUT/directory).mkdir(parents=True,exist_ok=True)
    manifest=json.loads((base.OUT/'manifest.json').read_text())
    protected=pd.read_csv(base.OUT/'audit/protected_inputs.csv').to_dict('records')+[dict(path=p,sha256=h) for p,h in manifest['artifacts'].items()]
    protected.append(dict(path=(base.OUT/'manifest.json').relative_to(ROOT).as_posix(),sha256=base.design.sha(base.OUT/'manifest.json')))
    for row in protected:assert base.design.sha(ROOT/row['path'])==row['sha256'],row['path']
    pd.DataFrame(protected).drop_duplicates('path').to_csv(OUT/'audit/protected_inputs.csv',index=False)
    _,full,splits=base.load();features=list(dict.fromkeys(CORE+base.design.HISTORY+[base.design.SLOPE,base.prior.old.c.DTR]+base.prior.RAIN))
    t=full[[ID,TARGET,'climate_profile','Municipio','Estado']+features].copy()
    assert len(t)==138 and t[ID].is_unique
    t.to_parquet(OUT/'cache/train138_exact_features.parquet',index=False);joblib.dump(splits,OUT/'cache/frozen65_splits.joblib')
    for name in ['outer_and_inner_splits.csv','group_memberships.csv']:
        path=base.OUT/'splits'/name;(OUT/'splits'/name).write_bytes(path.read_bytes())
    reference=pd.read_parquet(base.OUT/'tables/oof_predictions.parquet');reference=reference[reference.experiment.isin(['F6-00','F6-01','C-T3','F5-01','CHAMPION'])].copy()
    reference['experiment']=reference.experiment.replace({'F6-01':'F6-E0'})
    assert len(reference)==8556
    reference.to_parquet(OUT/'tables/reference_oof.parquet',index=False)
    replay=[]
    with threadpool_limits(limits=1):
        for protocol,repeat,fold,tr,va,inner in splits:
            model_path=base.OUT/'models'/f'F6-01_{protocol}_{repeat}_{fold}_outer.joblib';model=joblib.load(model_path)
            q=reference[(reference.experiment=='F6-E0')&(reference.protocol==protocol)&(reference['repeat']==repeat)&(reference.fold==fold)].set_index(ID).loc[t.iloc[va][ID]]
            yp=model.predict(t.iloc[va]);original=model.predict(full.iloc[va])
            np.testing.assert_allclose(yp,original,atol=1e-12,rtol=0);np.testing.assert_allclose(yp,q.y_pred,atol=1e-12,rtol=0)
            replay.append(dict(protocol=protocol,repeat=repeat,fold=fold,n=len(va),reference_model_path=model_path.relative_to(ROOT).as_posix(),max_prediction_difference=float(abs(yp-q.y_pred).max()),minimal_cache_equals_original=True))
    pd.DataFrame(replay).to_csv(OUT/'audit/E0_exact_replay_and_cache_equivalence.csv',index=False)
    registry=pd.read_csv(base.OUT/'tables/fit_registry.csv');registry=registry[(registry.experiment=='F6-01')&registry.selected].copy();registry['experiment']='F6-E0'
    registry.to_csv(OUT/'tables/E0_original_selected_fit_registry.csv',index=False)
    config=dict(authorized_fits=list(SPECS),recovered_E0='F6-01 exact original OOF and models; no refitting',specs=SPECS,blocks=BLOCKS,grid=GRID,n_trees=N_TREES,seed=SEED,bootstrap=False,selection='original eight configurations x four frozen innerfolds; meanfold internal RMSE; rounded10 ties first grid entry; independent retuning per representation',refitted_ablation='E0 independently retuned core models already archived under original65folds; E1/E2/E3 independently retuned extended models; no feature masking substitute',expected_outer=195,expected_inner_candidate=6240,expected_total_fits=6435,expected_stored_models=975,normalization='unchanged immutable TreeModel/ConditionalFeatures train-only medians and affine scaling; native Y',max_features_note='fractions0.5/1.0 retained; effective number differs by dimensionality and any trainconstant removal',effects=dict(n_bins=4,min_supported_parcels=5,min_corner_supported_fraction=.8,radius='95th percentile of train-only leave-one-out nearest-neighbor distances in each fitted preprocessing space; floor1e-8',ALE='show cumulative curve only if all occupied bins supported; otherwise supported local differences; no unsupported corners predicted',interactions=INTERACTIONS,conditioning='block joint permutation only within same validation climate profile; minimum10 eligible parcels;10 deterministic permutations; constants/not enough support marked not identifiable; no marginal unsupported climate permutations'),tree_count_stability='384 fixed; only original prefix128/256 diagnostics; no n_estimators expansion',aggregation='138 complete OOF per repetition; then mean10 random repeats; fold metrics diagnostic',decision='E4/E5 recommendation only, never execution; exploratory comparison against E0 and compatible controls, no global external winner declared independently confirmed',no_final_training=True,no_PRED=True,no_E4_E5=True,workers=6,cache_sha={p.relative_to(ROOT).as_posix():base.design.sha(p) for p in (OUT/'cache').glob('*')},source_sha={p.relative_to(ROOT).as_posix():base.design.sha(p) for p in [Path(__file__),base.ROOT/'src/family_6/execution.py',base.ROOT/'src/family_6/models.py',base.ROOT/'src/family_4/conditional_response.py']})
    file=OUT/'frozen_design.json'
    if file.exists():assert json.loads(file.read_text())==json.loads(json.dumps(config))
    else:file.write_text(json.dumps(config,indent=2),encoding='utf8')
    from .audit import build
    build()
    print('F6-E frozen;E0 replayed65folds;E1-E3 only;6435fits;minimal cache exactly equivalent',flush=True)

def fit_fold(index):
    try:
        with redirected_engine():base.fit_fold(index,list(SPECS))
    except Exception:
        import traceback
        (OUT/'audit'/f'failure_fold_{index}.txt').write_text(traceback.format_exc(),encoding='utf8');raise

def run(workers=6):
    if not (OUT/'frozen_design.json').exists():prepare()
    else:
        if (OUT/'manifest.json').exists():raise FileExistsError('Completed F6-E immutable')
        cfg=json.loads((OUT/'frozen_design.json').read_text())
        for path,h in {**cfg['source_sha'],**cfg['cache_sha']}.items():assert base.design.sha(ROOT/path)==h
    start=time.perf_counter()
    joblib.Parallel(n_jobs=workers,backend='loky',inner_max_num_threads=1)(joblib.delayed(fit_fold)(i) for i in range(65))
    with redirected_engine():p=base.collect()
    assert len(p)==13938
    (OUT/'audit/wall_seconds.txt').write_text(str(time.perf_counter()-start))
    from .reporting import build
    build(p)
