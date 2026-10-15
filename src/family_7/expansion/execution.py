from contextlib import contextmanager
from pathlib import Path
import json,time,shutil,joblib
import pandas as pd,numpy as np
from src.family_7 import execution as initial
from src.family_7.models import BoostModel,CB_GRID,SEED
base=initial.base;ROOT=initial.ROOT;ID=initial.ID;TARGET=initial.TARGET;CORE=initial.CORE
OUT=ROOT/'outputs/modeling/family_7/expansion/v1'
SPECS=initial.EXTENSIONS
HISTORY=base.design.HISTORY;SLOPE=base.design.SLOPE
INTERACTIONS={name:[(c,CORE[-1]) for c in CORE[:3]]+([(CORE[-1],h) for h in HISTORY] if name!='F7-E2' else [])+([(CORE[0],SLOPE)] if name!='F7-E1' else [])+([(h,SLOPE) for h in HISTORY] if name=='F7-E3' else []) for name in SPECS}
def load():return None,pd.read_parquet(OUT/'cache/train138_exact_features.parquet'),joblib.load(OUT/'cache/frozen65_splits.joblib')
@contextmanager
def redirected_engine():
    old=base.OUT,base.SPECS,base.load,base.TreeModel,base.GRID
    try:
        base.OUT=OUT;base.SPECS=SPECS;base.load=load;base.TreeModel=BoostModel;base.GRID=CB_GRID
        yield
    finally:base.OUT,base.SPECS,base.load,base.TreeModel,base.GRID=old
def prepare():
    if (OUT/'manifest.json').exists():raise FileExistsError('Completed expansion immutable')
    for d in ['audit','tables','models','checkpoints','cache','splits','figures','report']:(OUT/d).mkdir(parents=True,exist_ok=True)
    m=json.loads((initial.OUT/'manifest.json').read_text());protected=pd.read_csv(initial.OUT/'audit/protected_inputs.csv').to_dict('records')
    protected += [dict(path=p,sha256=h) for p,h in m['artifacts'].items()]
    protected.append(dict(path=(initial.OUT/'manifest.json').relative_to(ROOT).as_posix(),sha256=base.design.sha(initial.OUT/'manifest.json')))
    for row in protected:assert base.design.sha(ROOT/row['path'])==row['sha256'],row['path']
    pd.DataFrame(protected).drop_duplicates('path').to_csv(OUT/'audit/protected_inputs.csv',index=False)
    for f in ['train138_exact_features.parquet','frozen65_splits.joblib']:shutil.copyfile(initial.OUT/'cache'/f,OUT/'cache'/f)
    for f in ['outer_and_inner_splits.csv','group_memberships.csv']:shutil.copyfile(initial.OUT/'splits'/f,OUT/'splits'/f)
    ref=pd.read_parquet(initial.OUT/'tables/oof_predictions.parquet');ref=ref[ref.experiment.isin(['F7-00','F7-01','C-T3','F5-01','CHAMPION'])]
    f6=pd.read_parquet(initial.expansion.OUT/'tables/oof_predictions.parquet');f6=f6[f6.experiment.isin(['F6-E1','F6-E2'])]
    ref=pd.concat([ref,f6],ignore_index=True);assert len(ref)==12144
    ref.to_parquet(OUT/'tables/reference_oof.parquet',index=False)
    _,t,splits=load();gate=[]
    for p,r,f,tr,va,inner in splits:
        for name in ref.experiment.unique():
            if name=='CHAMPION' and p!='random':continue
            q=ref[(ref.experiment==name)&(ref.protocol==p)&(ref['repeat']==r)&(ref.fold==f)].set_index(ID)
            assert set(q.index)==set(t.iloc[va][ID]);np.testing.assert_allclose(q.y_true.reindex(t.iloc[va][ID]),t.iloc[va][TARGET],atol=1e-12)
            gate.append(dict(experiment=name,protocol=p,repeat=r,fold=f,n=len(q),exact_ids_and_targets=True))
    pd.DataFrame(gate).to_csv(OUT/'audit/reference_compatibility.csv',index=False)
    # Read-only copies of core tuning and prior evidence, not a new core fit.
    for f in ['inner_selection.csv','parameter_selection_stability.csv']:
        shutil.copyfile(initial.OUT/'tables'/f,OUT/'audit'/('initial_'+f))
    for f in ['audit_and_frozen_design.md','synthesis.md']:shutil.copyfile(initial.OUT/'report'/f,OUT/'audit'/('initial_'+f))
    cfg=dict(specs=SPECS,grid=CB_GRID,seed=SEED,implementation='immutable family_7.models.BoostModel and scoped family_6 execution reuse',selection='original eight CatBoost configurations x four frozen inner folds; mean inner fold RMSE; round10 ties first; no early stopping',normalization='original ConditionalFeatures fitted separately on each corresponding training set; native Y',aggregation='138 complete OOF per repetition; average ten random repetition metrics; per-fold metrics diagnostic',interactions=INTERACTIONS,support='q95 train LOO nearest-neighbor radius; >=5 supported parcels and >=80percent corners; no predictions on unsupported corners',permutation='joint rainfall3 and joint history2; MayNDVI and slope separately; within validation climate profile; min10 eligible; empirical training-neighbor gate added for expanded conditional permutations',expected_fits=6435,expected_models=975,expected_oof=17526,workers=6,no_final_training=True,no_PRED=True,no_XGB_fit=True,no_ensemble=True,no_residual=True,decision='stop after E1-E3; descriptive error covariance only; never optimize combination weights on external OOF',cache_sha={p.relative_to(ROOT).as_posix():base.design.sha(p) for p in (OUT/'cache').glob('*')},source_sha={p.relative_to(ROOT).as_posix():base.design.sha(p) for p in [Path(__file__),ROOT/'src/family_7/models.py',ROOT/'src/family_6/execution.py',ROOT/'src/family_4/conditional_response.py']})
    path=OUT/'frozen_design.json'
    if path.exists():assert json.loads(path.read_text())==json.loads(json.dumps(cfg))
    else:path.write_text(json.dumps(cfg,indent=2),encoding='utf8')
    text='# F7 — Expansión controlada: diseño congelado\n\nSolo E1/E2/E3 CatBoost; F7-00/F7-01 y referencias recuperados sin ajustes. Historia NDVI2 conserva las dos columnas F5: mean/std entre siete promedios de meses calendario históricos 2022–24, no std interanual. Pendiente media usa TOPO_BASIC_slope_mean=slope_degrees. No History15/16, slope14, DTR, coordenadas, estado ni municipio como entradas. Se conservan ocho configuraciones y65 folds externos con4 internos. E3 se reajusta conjuntamente. Interacciones predefinidas, soporte y permutación conjunta se fijan abajo. Las permutaciones expandidas se restringen además a esquinas respaldadas en espacio de entrenamiento; condicionan al perfil climático, no a todas las otras variables.\n\nIgual peso por perfil y por parejas se reporta por separado; solo parejas del mismo ajuste externo. Grupos con <10 parcelas o <3 perfiles se marcan de soporte reducido para interpretación intraperfil, sin borrar resultados descriptivos. Todas las omisiones son de cálculo OOF, nunca de ajustes. La evaluación es exploratoria sobre etiquetas y particiones previamente reutilizadas. No hay superioridad estadística, selección externa de pesos, ensemble, stacking, corrector residual, modelo final, PRED ni promoción.\n\n```json\n'+json.dumps(cfg,indent=2)+'\n```\n'
    (OUT/'report/frozen_design.md').write_text(text,encoding='utf8')
    print('Frozen E1-E3 only;6435 scientific fits',flush=True)
def fit_fold(i):
    with redirected_engine():base.fit_fold(i,list(SPECS))
def run():
    if not (OUT/'frozen_design.json').exists():prepare()
    if (OUT/'manifest.json').exists():raise FileExistsError('Completed expansion immutable')
    cfg=json.loads((OUT/'frozen_design.json').read_text())
    for p,h in {**cfg['source_sha'],**cfg['cache_sha']}.items():assert base.design.sha(ROOT/p)==h
    start=time.perf_counter()
    joblib.Parallel(n_jobs=6,backend='loky',inner_max_num_threads=1)(joblib.delayed(fit_fold)(i) for i in range(65))
    with redirected_engine():p=base.collect()
    assert len(p)==17526
    (OUT/'audit/wall_seconds.txt').write_text(str(time.perf_counter()-start))
    from .reporting import build
    build(p)
