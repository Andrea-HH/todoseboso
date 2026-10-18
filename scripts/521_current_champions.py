"""Export/replay/refit the current CT3/26/14/B1 scope, without L40 or GeoC."""
from pathlib import Path
import os
import sys
os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('MKL_NUM_THREADS','1')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import argparse
import hashlib
import json
import time
import warnings
import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from src.current_champions import MODELS,LOCAL7,LOCAL5,load_bundle,predict_saved,refit_fold
from src.indicator_neighborhoods import REDUCTIONS
from src.ct3_residual_conditional.models import CORE

DEFAULT_BUNDLE=ROOT/'data/processed/current_champions/v1'
DEFAULT_OUT=ROOT/'outputs/research/current_champions/v1'
KEY=['execution_index','protocol','repeat','fold','experiment','ID_POLIGONO']


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')


def restrict_inputs(bundle,out):
    """Fail on any read/write into historical/private roots outside this run."""
    allowed=[bundle.resolve(),out.resolve()]
    restricted=[(ROOT/'data').resolve(),(ROOT/'outputs').resolve(),(ROOT.parent/'fira/GeoC').resolve()]
    def audit(event,args):
        if event!='open' or not args or isinstance(args[0],int):return
        try:path=Path(os.fsdecode(args[0])).resolve()
        except (TypeError,ValueError,OSError):return
        if any(path.is_relative_to(root) for root in restricted) and not any(path.is_relative_to(root) for root in allowed):
            raise RuntimeError('Unexpected historical/private input outside standalone bundle: '+str(path))
    sys.addaudithook(audit)


def export(bundle):
    # This one-time extraction reads existing local research assets; no fitting.
    # All subsequent commands read only this narrow bundle and repository code.
    from src.architecture_decomposition import load_assets
    a=load_assets();t=a['a']['train'];geology=a['physical_definitions']['geologic_composition']
    fields=list(CORE)+LOCAL7+['base_centroid_lat','base_centroid_lon']+geology['columns']+REDUCTIONS['R3']
    assert len(set(fields))==26
    if (bundle/'manifest.json').exists():raise FileExistsError('Bundle already frozen; use a different --bundle directory, never overwrite.')
    bundle.mkdir(parents=True,exist_ok=True)
    frame=t[['ID_POLIGONO','RENDIMIENTO_T_HA','climate_profile','Estado','Municipio']].copy()
    indicators=pd.read_parquet(ROOT/'outputs/modeling/indicator_neighborhoods/v1/cache/features_train138_target_free.parquet').set_index('ID_POLIGONO')
    source=a['features197'].set_index('ID_POLIGONO');role=a['role_frame'].set_index('ID_POLIGONO')
    for c in fields:
        table=indicators if c in REDUCTIONS['R3'] else role if c in role else source
        frame[c]=table.loc[frame.ID_POLIGONO,c].to_numpy()
    frame.to_parquet(bundle/'train138.parquet',index=False)
    groups=pd.read_csv(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/groups.csv')
    groups.set_index('ID_POLIGONO').loc[frame.ID_POLIGONO].reset_index().to_csv(bundle/'groups.csv',index=False)
    pos=a['a']['train_global'];np.save(bundle/'distance.npy',a['a']['distance'][np.ix_(pos,pos)],allow_pickle=False)
    manifest=dict(schema_version=1,models=MODELS,current_champions=['Reference26','Compact14'],features=fields,
        geology=geology,n_train=138,n_predictors=26,no_L40=True,no_PCA20=True,no_PRED59=True,
        distance='Frozen normalized geographical distances restricted to138 known parcels; same scale/tie order as original fits, no yield fitting.',
        feature_provenance='Derived columns already audited in this repository; some originated in GeoC source feature engineering. No external repository or C4 needed after export.',files={})
    plans=json.loads((ROOT/'configs/validation/original65_plus_fresh16.json').read_text(encoding='utf-8'))
    dump(bundle/'splits.json',plans)
    expected=pd.read_parquet(ROOT/'outputs/modeling/four_expert_combinations/v1/tables/oof_residuals.parquet')
    expected[expected.experiment.isin(MODELS)].to_parquet(bundle/'expected_oof.parquet',index=False)
    (bundle/'models').mkdir(exist_ok=True)
    for fi in range(81):
        old=joblib.load(ROOT/f'outputs/modeling/four_expert_combinations/v1/models/{fi:02d}.joblib')
        outer=old['outer_experts'];raw=outer['raw']
        if raw['expert'] is not None:assert raw['expert']['local']['representation'].columns==LOCAL7
        if raw['compact']['local'] is not None:assert raw['compact']['local']['representation'].columns==LOCAL5
        pack=dict(outer_experts=outer,train_positions=old['train_positions'],validation_positions=old['validation_positions'],B1_weight=float(old['models']['B1']))
        joblib.dump(pack,bundle/f'models/{fi:02d}.joblib',compress=3)
    manifest['files']={p.relative_to(bundle).as_posix():digest(p) for p in sorted(bundle.rglob('*')) if p.is_file()}
    dump(bundle/'manifest.json',manifest)
    print(json.dumps(dict(bundle=str(bundle),exported_models=81,models=MODELS,training=False,no_L40=True)))


def metrics(f):
    records=[]
    for (m,p,r),g in f.groupby(['experiment','protocol','repeat']):
        e=g.y_pred-g.y_true;ae=e.abs();den=((g.y_true-g.y_true.mean())**2).sum()
        records.append(dict(experiment=m,protocol=p,repeat=r,n=len(g),rmse=np.sqrt(np.mean(e**2)),r2=1-np.sum(e**2)/den,
                            mae=ae.mean(),bias=e.mean(),p95_absolute=ae.quantile(.95),within_05=(ae<=.5).mean()))
    repeat=pd.DataFrame(records)
    return repeat,repeat.groupby(['experiment','protocol'],as_index=False).mean(numeric_only=True).drop(columns='repeat')


def evaluate(bundle,out,refit,fold_ids):
    frame,groups,distance,manifest=load_bundle(bundle,verify_saved_models=not refit)
    plan=json.loads((bundle/'splits.json').read_text(encoding='utf-8'))['folds']
    expected=pd.read_parquet(bundle/'expected_oof.parquet');rows=[];audit=[]
    out.mkdir(parents=True,exist_ok=True)
    for fi in fold_ids:
        record=plan[fi];started=time.perf_counter()
        with warnings.catch_warnings(record=True) as caught,threadpool_limits(limits=1):
            warnings.simplefilter('always')
            if refit:
                destination=out/f'refit_models/{fi:02d}.joblib'
                if destination.exists():raise FileExistsError('Refit destination exists; choose another --output. No silent model reuse.')
                pack=refit_fold(frame,groups,distance,manifest['geology'],record,out/f'cold_cache/{fi:02d}')
                destination.parent.mkdir(parents=True,exist_ok=True);joblib.dump(pack,destination,compress=3)
            else:pack=joblib.load(bundle/f'models/{fi:02d}.joblib')
            q=np.array(record['validation_positions']);assert np.array_equal(q,pack['validation_positions'])
            predictions=predict_saved(pack,q,frame,distance)
            for m in MODELS:
                lookup=expected[(expected.execution_index==fi)&(expected.experiment==m)].set_index('ID_POLIGONO')
                truth=lookup.loc[frame.iloc[q].ID_POLIGONO]
                assert np.array_equal(truth.y_true.to_numpy(),frame.iloc[q].RENDIMIENTO_T_HA.to_numpy())
                maximum=float(np.max(np.abs(predictions[m]-truth.y_pred.to_numpy())))
                assert maximum<1e-10,(fi,m,maximum)
                audit.append(dict(execution_index=fi,experiment=m,max_absolute_prediction_difference=maximum))
                for position,pred in zip(q,predictions[m]):
                    sample=frame.iloc[position]
                    rows.append(dict(execution_index=fi,protocol=record['protocol'],repeat=record['repeat'],fold=record['fold'],
                        experiment=m,ID_POLIGONO=sample.ID_POLIGONO,y_true=sample.RENDIMIENTO_T_HA,y_pred=float(pred),
                        error=float(pred-sample.RENDIMIENTO_T_HA),Estado=sample.Estado,Municipio=sample.Municipio,climate_profile=sample.climate_profile))
            log=[dict(category=w.category.__name__,message=str(w.message)) for w in caught]
            dump(out/f'audit/{fi:02d}.json',dict(fold=fi,refit=refit,seconds=time.perf_counter()-started,warnings=log,B1_weight=pack['B1_weight']))
        print(f'{"Cold refit" if refit else "Replay"} {fi+1}/81 {time.perf_counter()-started:.1f}s',flush=True)
    f=pd.DataFrame(rows);assert not f.duplicated(KEY).any()
    f.to_parquet(out/'oof_predictions.parquet',index=False);f.to_csv(out/'oof_predictions.csv',index=False)
    rowkey=[k for k in KEY if k!='experiment']
    metadata=f.drop_duplicates(rowkey)[rowkey+['y_true','Estado','Municipio','climate_profile']]
    wide=f.pivot(index=rowkey,columns='experiment',values='y_pred').reset_index()
    wide=metadata.merge(wide,on=rowkey,validate='one_to_one')
    for m in MODELS:
        wide.rename(columns={m:'pred_'+m},inplace=True)
        wide['error_'+m]=wide['pred_'+m]-wide.y_true
    wide.to_csv(out/'oof_predictions_wide.csv',index=False)
    pd.DataFrame(audit).to_csv(out/'prediction_parity.csv',index=False)
    complete=len(fold_ids)==81
    if complete:
        repeat,summary=metrics(f);repeat.to_csv(out/'metrics_by_repeat.csv',index=False);summary.to_csv(out/'metrics.csv',index=False)
        # Only anonymous aggregated metrics are published; OOF/IDs stay ignored.
        public=ROOT/'results/current_champions/v1';public.mkdir(parents=True,exist_ok=True)
        summary.to_csv(public/'metrics.csv',index=False);repeat.to_csv(public/'metrics_by_repeat.csv',index=False)
        regional=[]
        for (m,p,r,state),g in f.groupby(['experiment','protocol','repeat','Estado']):
            e=g.y_pred-g.y_true
            den=((g.y_true-g.y_true.mean())**2).sum()
            regional.append(dict(experiment=m,protocol=p,repeat=r,state=state,n=len(g),rmse=np.sqrt(np.mean(e**2)),
                r2=1-np.sum(e**2)/den if den>0 else np.nan,mae=e.abs().mean(),bias=e.mean()))
        pd.DataFrame(regional).groupby(['experiment','protocol','state'],as_index=False).mean(numeric_only=True).drop(columns='repeat').to_csv(public/'metrics_by_state.csv',index=False)
        for axis,column in [('municipality','Municipio'),('spatial_block','spatial_block')]:
            grouped=f.copy()
            if column=='spatial_block':grouped[column]=grouped.ID_POLIGONO.map(groups.spatial)
            records=[]
            for (m,p,r,region),g in grouped.groupby(['experiment','protocol','repeat',column]):
                e=g.y_pred-g.y_true;den=((g.y_true-g.y_true.mean())**2).sum()
                records.append(dict(experiment=m,protocol=p,repeat=r,region=region,n=len(g),rmse=np.sqrt(np.mean(e**2)),
                    r2=1-np.sum(e**2)/den if den>1e-12 else np.nan,mae=e.abs().mean(),bias=e.mean()))
            pd.DataFrame(records).groupby(['experiment','protocol','region'],as_index=False).mean(numeric_only=True).drop(columns='repeat').to_csv(public/f'metrics_by_{axis}.csv',index=False)
        with pd.ExcelWriter(out/'comparacion_modelos_propios.xlsx',engine='openpyxl') as workbook:
            for sheet,table in [('OOF_wide',wide),('OOF_long',f),('metrics',summary),('metrics_by_repeat',repeat)]:
                table.to_excel(workbook,sheet_name=sheet,index=False)
    report=dict(status='passed',mode='cold_refit' if refit else 'saved_model_replay',models=MODELS,current_champions=['Reference26','Compact14'],
        external_folds=len(fold_ids),fold_ids=fold_ids,complete_protocol_metrics=complete,
        max_prediction_difference=max(a['max_absolute_prediction_difference'] for a in audit),
        no_L40=True,no_external_repository=True,restricted_file_io=True,no_PRED59=True,no_final138_fit=True,
        limitation='Replay proves reconstruction of saved predictions, not cold training; refit mode proves only the explicitly listed folds.',
        input_manifest_sha256=digest(bundle/'manifest.json'))
    dump(out/'reproduction_audit.json',report)
    if complete:dump(ROOT/'results/current_champions/v1/reproduction_audit.json',report)
    print(json.dumps(report,ensure_ascii=False),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['export','replay','refit'])
    parser.add_argument('--bundle',type=Path,default=DEFAULT_BUNDLE)
    parser.add_argument('--output',type=Path,default=None)
    parser.add_argument('--folds',default='all',help='all or comma-separated zero-based execution indexes')
    args=parser.parse_args()
    if args.command=='export':export(args.bundle);return
    ids=list(range(81)) if args.folds=='all' else list(map(int,args.folds.split(',')))
    assert len(ids)==len(set(ids)) and all(0<=i<81 for i in ids)
    out=args.output or DEFAULT_OUT/args.command
    restrict_inputs(args.bundle,out)
    evaluate(args.bundle,out,args.command=='refit',ids)


if __name__=='__main__':main()
