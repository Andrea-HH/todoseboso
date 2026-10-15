"""F7-00/F7-01 only. Immutable F6 engine reused through a scoped adapter."""
from contextlib import contextmanager
from pathlib import Path
import json,time,joblib,shutil
import pandas as pd,numpy as np
from src.family_6 import execution as base
from src.family_6.expansion import execution as expansion
from .models import BoostModel,GRIDS,SEED

ROOT=base.ROOT;ID=base.ID;TARGET=base.TARGET;CORE=base.CORE
OUT=ROOT/'outputs/modeling/family_7/boosting/v1'
SPECS={'F7-00':dict(algorithm='CatBoost',columns=CORE),'F7-01':dict(algorithm='XGBoost',columns=CORE)}
EXTENSIONS={'F7-E1':dict(algorithm='CatBoost',columns=CORE+base.design.HISTORY),
            'F7-E2':dict(algorithm='CatBoost',columns=CORE+[base.design.SLOPE]),
            'F7-E3':dict(algorithm='CatBoost',columns=CORE+base.design.HISTORY+[base.design.SLOPE])}
def load():
    t=pd.read_parquet(OUT/'cache/train138_exact_features.parquet')
    return None,t,joblib.load(OUT/'cache/frozen65_splits.joblib')
@contextmanager
def redirected_engine(algorithm=None):
    old=base.OUT,base.SPECS,base.load,base.TreeModel,base.GRID
    try:
        base.OUT=OUT;base.SPECS=SPECS;base.load=load;base.TreeModel=BoostModel
        if algorithm is not None:base.GRID=GRIDS[algorithm]
        yield
    finally:base.OUT,base.SPECS,base.load,base.TreeModel,base.GRID=old
def prepare():
    if (OUT/'manifest.json').exists():raise FileExistsError('Completed F7 immutable')
    for directory in ['audit','tables','models','checkpoints','cache','splits','figures','report']:
        (OUT/directory).mkdir(parents=True,exist_ok=True)
    m=json.loads((expansion.OUT/'manifest.json').read_text())
    protected=pd.read_csv(expansion.OUT/'audit/protected_inputs.csv').to_dict('records')
    protected+=[dict(path=p,sha256=h) for p,h in m['artifacts'].items()]
    protected.append(dict(path=(expansion.OUT/'manifest.json').relative_to(ROOT).as_posix(),sha256=base.design.sha(expansion.OUT/'manifest.json')))
    for row in protected:assert base.design.sha(ROOT/row['path'])==row['sha256'],row['path']
    pd.DataFrame(protected).drop_duplicates('path').to_csv(OUT/'audit/protected_inputs.csv',index=False)
    _,t,splits=expansion.load();features=list(dict.fromkeys(CORE+base.design.HISTORY+[base.design.SLOPE]))
    t=t[[ID,TARGET,'climate_profile','Municipio','Estado']+features].copy()
    assert len(t)==138 and t[ID].is_unique
    t.to_parquet(OUT/'cache/train138_exact_features.parquet',index=False)
    shutil.copyfile(expansion.OUT/'cache/frozen65_splits.joblib',OUT/'cache/frozen65_splits.joblib')
    for name in ['outer_and_inner_splits.csv','group_memberships.csv']:
        shutil.copyfile(expansion.OUT/'splits'/name,OUT/'splits'/name)
    ref=pd.read_parquet(expansion.OUT/'tables/oof_predictions.parquet')
    ref=ref[ref.experiment.isin(['C-T3','F5-01','F6-E0','CHAMPION'])].copy();assert len(ref)==6762
    ref.to_parquet(OUT/'tables/reference_oof.parquet',index=False)
    gate=[]
    for protocol,repeat,fold,tr,va,inner in splits:
        for name in ref.experiment.unique():
            if name=='CHAMPION' and protocol!='random':continue
            q=ref[(ref.experiment==name)&(ref.protocol==protocol)&(ref['repeat']==repeat)&(ref.fold==fold)].set_index(ID)
            assert set(q.index)==set(t.iloc[va][ID])
            np.testing.assert_allclose(q.y_true.reindex(t.iloc[va][ID]),t.iloc[va][TARGET],atol=1e-12)
            gate.append(dict(experiment=name,protocol=protocol,repeat=repeat,fold=fold,exact_ids_and_targets=True,n=len(q)))
    pd.DataFrame(gate).to_csv(OUT/'audit/reference_compatibility.csv',index=False)
    cfg=dict(executed_stage=list(SPECS),specs=SPECS,extensions_not_executed=EXTENSIONS,
        extension_algorithm='CatBoost prospectively chosen before any F7 fit; symmetric shallow trees contrast with previous ET; not an external-winner selection',
        grids=GRIDS,seed=SEED,selection='eight curated candidates x four ORIGINAL frozen inner folds; mean internal fold RMSE; rounded10 ties first candidate; no early stopping; native target',
        constants=dict(CatBoost=dict(grow_policy='SymmetricTree',boosting_type='Plain',bootstrap_type='No',random_strength=0,border_count=64,leaf_estimation_iterations=1,thread_count=1,allow_writing_files=False),
                       XGBoost=dict(objective='reg:squarederror',tree_method='hist',max_bin=64,subsample=1,colsample_bytree=1,gamma=0,n_jobs=1)),
        preprocessing='unchanged ConditionalFeatures medians, affine scale, constant removal fitted on each train only; NDVI scale floor .05; no target normalization needed for native-Y trees',
        aggregation='complete138 OOF per repeat; mean of10 random repeat metrics; other protocols one repeat; fold metrics diagnostic only',
        interpretation='reused support-gated ALE4quantiles and mixed differences3x3; min5 supported and80percent corner support; q95 train LOO nearest-neighbor distance; no unsupported predictions; grouped joint permutation conditional on validation climate profile only, min10 eligible; no causal importance',
        interactions=[(CORE[0],CORE[-1]),(CORE[1],CORE[-1]),(CORE[2],CORE[-1])],
        deferred_interactions={'NDVI_history':[CORE[-1],base.design.HISTORY[0]],'rain_slope':[CORE[0],base.design.SLOPE]},
        expected_fits=4290,expected_outer=130,expected_saved_models=650,expected_oof_rows=10350,
        workers=6,no_final_training=True,no_PRED=True,no_residual=True,no_monthly=True,no_DTR=True,no_extension_fits=True,
        decision='stop after F7-00/F7-01 for user review; contextual/exploratory OOF on reused labels; no champion promotion or statistical superiority assertion',
        cache_sha={p.relative_to(ROOT).as_posix():base.design.sha(p) for p in (OUT/'cache').glob('*')},
        source_sha={p.relative_to(ROOT).as_posix():base.design.sha(p) for p in [Path(__file__),Path(__file__).with_name('models.py'),ROOT/'src/family_6/execution.py',ROOT/'src/family_4/conditional_response.py']})
    path=OUT/'frozen_design.json'
    if path.exists():assert json.loads(path.read_text())==json.loads(json.dumps(cfg))
    else:path.write_text(json.dumps(cfg,indent=2),encoding='utf8')
    from .audit import build
    build()
    print('F7 frozen: F7-00/F7-01 only, 4290 fits; extensions deferred for review',flush=True)
def fit_fold(index):
    try:
        for name,spec in SPECS.items():
            with redirected_engine(spec['algorithm']):base.fit_fold(index,[name])
    except Exception:
        import traceback
        (OUT/'audit'/f'failure_fold_{index}.txt').write_text(traceback.format_exc(),encoding='utf8');raise
def run(workers=6):
    if not (OUT/'frozen_design.json').exists():prepare()
    if (OUT/'manifest.json').exists():raise FileExistsError('Completed F7 immutable')
    cfg=json.loads((OUT/'frozen_design.json').read_text())
    for path,h in {**cfg['source_sha'],**cfg['cache_sha']}.items():assert base.design.sha(ROOT/path)==h
    start=time.perf_counter()
    joblib.Parallel(n_jobs=workers,backend='loky',inner_max_num_threads=1)(joblib.delayed(fit_fold)(i) for i in range(65))
    with redirected_engine():p=base.collect()
    assert len(p)==10350
    (OUT/'audit/wall_seconds.txt').write_text(str(time.perf_counter()-start))
    from .reporting import build
    build(p)
