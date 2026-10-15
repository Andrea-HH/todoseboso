"""Rainfall v1: strict features, EDA and nested experiments on audited data."""
import argparse
from pathlib import Path
import sys
import json
import platform
import importlib.metadata
import os
os.environ.setdefault('OMP_NUM_THREADS','1')
import pandas as pd
import geopandas as gpd
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from family_1.rainfall_audit import CLIMATE, MASTER, SHAPE, sha
from family_1.rainfall_features import build_features, ID, VERSION
from family_1.rainfall_modeling import supervised_data, make_splits, evaluate, summarize, experiments
from family_1.rainfall_reporting import exploratory, model_report

def main(run_id, audit_id):
    out=ROOT/'outputs/modeling/family_1/rainfall_yield'/run_id
    proc=ROOT/'data/processed/family_1/rainfall_yield'/run_id
    audit_path=ROOT/'outputs/data_audit/family_1/rainfall_yield'/audit_id/'audit_manifest.json'
    audit=json.loads(audit_path.read_text(encoding='utf-8'))
    if not audit['passed']:raise ValueError('Audit did not pass')
    # Every audited raster and canonical input must still match the independent audit.
    for path,digest in audit['inputs'].items():
        if sha(ROOT/path)!=digest:raise ValueError(f'Audited input changed: {path}')
    if out.exists() or proc.exists():raise FileExistsError('Choose a fresh run-id; prior results are preserved')
    out.mkdir(parents=True);proc.mkdir(parents=True)
    for name in ['tables','figures','report','splits']:(out/name).mkdir()
    climate=pd.read_parquet(CLIMATE);master=pd.read_csv(MASTER)
    features,dictionary=build_features(climate)
    features=features.merge(master[[ID,'CONJUNTO']],on=ID,validate='one_to_one')
    if len(features)!=197:raise ValueError('Expected 197 feature rows')
    features.to_parquet(proc/'rainfall_features.parquet',index=False)
    features.to_csv(proc/'rainfall_features.csv',index=False)
    dictionary.to_csv(proc/'rainfall_feature_dictionary.csv',index=False)
    dictionary.to_csv(out/'tables/00_feature_dictionary.csv',index=False)
    d=supervised_data(features,master)
    if len(d)!=138 or master.CONJUNTO.eq('PREDICCION').sum()!=59:raise ValueError('Unexpected supervised universe')
    geo=gpd.read_file(SHAPE).rename(columns={'ID_POLIGON':ID}).to_crs('EPSG:6372')
    geo['x']=geo.geometry.centroid.x;geo['z']=geo.geometry.centroid.y
    eda=exploratory(climate,features,d,geo,dictionary,out)
    splits,groups=make_splits(d,climate,geo)
    groups.to_csv(out/'splits/group_memberships.csv',index=False)
    config=dict(version=VERSION,run_id=run_id,seed=2026,alpha_grid=[.1,1,10,100,1000],
                experiments=experiments(),primary_metric='mean whole-repeat OOF RMSE, not averaged OOF ensemble',
                candidate_gate='5% RMSE gain, >=80% random fold wins and beat baseline under all grouped protocols; exploratory',
                prediction_mode='retrospective after October 2025',feature_selection='E7 internal CV only')
    (out/'configuration.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    p,fm,registry=evaluate(d,splits,out)
    comparison=summarize(p,fm,out)
    decision=model_report(p,fm,registry,comparison,geo,out,audit,eda)
    source_files=[CLIMATE,MASTER,SHAPE,ROOT/'outputs/modeling/family_1/stage4/splits/outer_splits.csv',audit_path]
    source_files+=list((ROOT/'src/family_1').glob('rainfall_*.py'))+[Path(__file__).resolve()]
    manifest=dict(status='complete',version=VERSION,train_n=138,prediction_n=59,feature_count=len(dictionary),
        outer_folds=len(splits),experiments=len(experiments()),prediction_set_y_used=False,raw_modified=False,
        decision=decision,python=platform.python_version(),packages={name:importlib.metadata.version(name) for name in ['numpy','pandas','scikit-learn','geopandas','rasterio','exactextract','scipy','joblib']},
        inputs={str(path.relative_to(ROOT)):sha(path) for path in source_files},
        outputs={str(path.relative_to(ROOT)):sha(path) for path in proc.iterdir()})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(comparison[comparison.protocol.eq('random')].sort_values('RMSE_mean').to_string(index=False),flush=True)
    print('Decision:',decision,flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',default='v1');parser.add_argument('--audit-id',default='v1')
    args=parser.parse_args()
    for value in [args.run_id,args.audit_id]:
        if Path(value).name!=value or value in ('.','..'):parser.error('IDs must be simple directory names')
    main(args.run_id,args.audit_id)
