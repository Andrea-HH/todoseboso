"""Prepare then run remaining frozen calendar-block model comparisons."""
from pathlib import Path
import sys,json,hashlib,calendar,time,importlib
import numpy as np
import pandas as pd
import joblib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.calendar_expansion import OUT,BASE,work_fold
from src.agronomic_calendar_features import history_representation
from src.family_7.models import CB_GRID
old=importlib.import_module('scripts.394_calendar_modeling')
EXT=ROOT/'data/processed/agronomic_calendar_set/v2_temporal_extension'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare():
    if (OUT/'manifest.json').exists():raise FileExistsError('Preserve completed version')
    for name in ['cache','models','checkpoints','tables','audit']:(OUT/name).mkdir(parents=True,exist_ok=True)
    windows={'tri_apr_jun':[4,5,6],'tri_jul_sep':[7,8,9],'season_apr_oct':list(range(4,11))}
    specs={k:dict(v) for k,v in old.SPECS.items()}
    evi=['CURRENT_CAL_S2_evi_'+w for w in old.W]
    water=['CURRENT_CAL_S2_'+index+'_'+w for index in ['ndwi','msi'] for w in old.W]
    climate=[name.removeprefix('CURRENT_') for name in old.RAIN+old.TEMP]
    histclim=[pre+name for pre in ['HIST_MEAN_','HIST_SD_'] for name in climate]
    deltaclim=['DELTA_'+name for name in climate]+['HIST_SD_'+name for name in climate]
    specs.update({
      'CAL08':dict(columns=old.JOINT+evi,history=[],description='current joint + EVI windows'),
      'CAL09':dict(columns=old.JOINT+water,history=[],description='current joint + NDWI/MSI windows'),
      'CAL10':dict(columns=old.JOINT+evi+water,history=[],description='current joint + EVI + moisture'),
      'CAL11':dict(columns=old.JOINT+histclim,history=histclim,indicators=True,description='current joint + climate history mean/SD'),
      'CAL12':dict(columns=old.JOINT+deltaclim,history=deltaclim,indicators=True,description='current joint + climate departures/SD'),
    })
    satcols={'ndvi':'ndvi_promedio','evi':'evi_promedio','ndwi':'ndwi_promedio','msi':'msi_promedio','ndvi_spatial_std':'ndvi_std'}
    tri=['CURRENT_CALX_S2_'+a+'_'+w for a in satcols for w in ['tri_apr_jun','tri_jul_sep']]
    season=['CURRENT_CALX_S2_'+a+'_season_apr_oct' for a in satcols]
    climtri=['CURRENT_CALX_CLIM_'+a+'_'+w for a in ['precip','tmax'] for w in windows]
    specs.update({
      'CAL13':dict(columns=old.CORE+tri,history=[],description='compact4 + satellite two fixed trimesters'),
      'CAL14':dict(columns=old.CORE+season,history=[],description='compact4 + satellite full seven-month season'),
      'CAL15':dict(columns=climtri+[old.CORE[-1]],history=[],description='climate trimesters and full season + MayNDVI'),
      'CAL16':dict(columns=climtri+[old.CORE[-1]]+tri,history=[],description='CAL15 + satellite trimesters')})
    # Conservative fixed grids, not selected using previous external CAL outcomes.
    en=[dict(alpha=a,l1_ratio=l) for a in [1.,.1,.01,.001] for l in [1.,.9,.5,.1]]
    inputs=[ROOT/'data/processed/agronomic_calendar_set/v1/current_history_delta_197_target_free.parquet',ROOT/'data/processed/agronomic_calendar_set/v1/monthly_inputs_apr_oct.parquet',BASE/'train138.parquet',BASE/'frozen65_splits.joblib',ROOT/'outputs/modeling/agronomic_calendar/v1/tables/oof_predictions.parquet',ROOT/'outputs/modeling/compact_ensemble/v1/tables/oof_predictions.parquet',ROOT/'outputs/modeling/family_7/boosting/v1/tables/oof_predictions.parquet',ROOT/'src/calendar_expansion.py',Path(__file__),ROOT/'src/family_7/models.py']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in inputs}
    cfg=dict(specs=specs,en_grid=en,cb_grid=CB_GRID,history_en_gamma=[0.,.25,.5,1.],history_cb_split_weight=.5,
       selection='complete inner OOF RMSE; rounded12 ties first conservative candidate; folds and inner splits exactly frozen65',
       architecture_controls='CAL00 fitted under this common pooled-inner criterion and common preprocessing. Archives recovered separately; original F7 used meanfold inner criterion, so not equivalent retuning.',
       preprocessing='train medians, allmissing0, training scaling; fixed missing flags on means/deltas only when specified; EN gamma after scaling; CB weights .5 history/1 current at split scoring, not prediction percentages',
       feature_selection='EN coefficient zeros; CB actual split usage; neither selection nor hyperparameters use external folds',
       temporal_windows=windows,temporal_rule='same 2022-2025 monthly source; all months required; temperature day-weighted, precipitation summed; Sentinel equal-month mean of monthly medians',
       decision='exploratory on repeatedly reused labels; no automatic promotion, regional rules, residual models, final138 fit or PRED inference; no open screening',
       interpretation='historical years are X references, never replicated Y2025; current+mean+delta not combined; n=138, not552',
       workers=4,sha256=hashes,catboost_weight_documentation='https://catboost.ai/docs/en/references/training-parameters/common#feature_weights')
    frozen=OUT/'frozen_design.json'
    if frozen.exists():assert json.loads(frozen.read_text())==cfg
    else:frozen.write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    if not (OUT/'cache/features_train138.parquet').exists():
        monthly=pd.read_parquet(inputs[1]);rows=[];dictionary=[]
        for (pid,year),g in monthly.groupby(['ID_POLIGONO','year']):
            g=g.set_index('month');r=dict(ID_POLIGONO=pid,year=int(year))
            for w,months in windows.items():
                for label,col in satcols.items():
                    a=g[col].reindex(months);name='CALX_S2_'+label+'_'+w;r[name]=a.mean() if a.notna().all() else np.nan
                    dictionary.append(dict(feature=name,source=col,window=w,months=json.dumps(months),formula='equal-month mean of monthly medians'))
                for label,col in [('precip','precip_mean'),('tmax','tmax_mean'),('tmin','tmin_mean')]:
                    a=g[col].reindex(months);name='CALX_CLIM_'+label+'_'+w
                    r[name]=(a.sum() if label=='precip' else np.average(a,weights=[calendar.monthrange(int(year),m)[1] for m in months])) if a.notna().all() else np.nan
                    dictionary.append(dict(feature=name,source=col,window=w,months=json.dumps(months),formula='sum' if label=='precip' else 'day-weighted mean'))
            rows.append(r)
        panel=pd.DataFrame(rows);tmp=panel.rename(columns={col:col.replace('CALX_','CAL_',1) for col in panel if col.startswith('CALX_')})
        wide,counts=history_representation(tmp)
        wide=wide.rename(columns={col:col.replace('_CAL_','_CALX_',1) for col in wide if '_CAL_' in col})
        EXT.mkdir(parents=True,exist_ok=True);panel.to_parquet(EXT/'annual_features.parquet',index=False);wide.to_parquet(EXT/'current_history_delta.parquet',index=False)
        pd.DataFrame(dictionary).drop_duplicates('feature').to_csv(EXT/'dictionary.csv',index=False);counts.to_csv(EXT/'historical_counts.csv',index=False)
        source=pd.read_parquet(inputs[0]).merge(wide,on='ID_POLIGONO',validate='one_to_one');t=pd.read_parquet(BASE/'train138.parquet')
        x=source.set_index('ID_POLIGONO').reindex(t.ID_POLIGONO).reset_index()
        for col in old.CORE:x[col]=t[col].to_numpy()
        assert len(x)==138 and x.ID_POLIGONO.tolist()==t.ID_POLIGONO.tolist() and not any('rendimiento' in col.lower() for col in x)
        assert all(set(s['columns'])<=set(x) for s in specs.values())
        x.to_parquet(OUT/'cache/features_train138.parquet',index=False)
    print('FROZEN:',len(specs),'blocks x2 algorithms x65 folds. Original outputs preserved.',flush=True)

def finish(seconds):
    cfg=json.loads((OUT/'frozen_design.json').read_text());paths=sorted((OUT/'checkpoints').glob('*.joblib'));assert len(paths)==17*2*65
    packs=[joblib.load(p) for p in paths]
    for key in ['registry','usage','tuning']:
        records=[r for p in packs for r in ([p[key]] if key=='registry' else p[key])]
        a=pd.DataFrame(records)
        if key=='tuning':a['params']=a.params.map(json.dumps)
        a.to_parquet(OUT/'tables'/f'{key}.parquet',index=False)
        if key!='tuning':a.to_csv(OUT/'tables'/f'{key}.csv',index=False)
    p=pd.DataFrame([r for pack in packs for r in pack['predictions']]);assert len(p)==17*2*1794
    p.to_parquet(OUT/'tables/new_oof_predictions.parquet',index=False)
    # Keep only compatible archived rows; do not train duplicate legacy models.
    cols=['experiment','protocol','repeat','fold','ID_POLIGONO','y_true','y_pred']
    legacy=pd.read_parquet(ROOT/'outputs/modeling/compact_ensemble/v1/tables/oof_predictions.parquet')[cols]
    legacy=legacy[legacy.experiment.isin(['C-T3','F5-01','F7-00','EQUAL3'])]
    ridge=pd.read_parquet(ROOT/'outputs/modeling/agronomic_calendar/v1/tables/oof_predictions.parquet')[cols];ridge=ridge[ridge.experiment.ne('C-T3')];ridge['experiment']='R_'+ridge.experiment
    allp=pd.concat([p,legacy,ridge],ignore_index=True)
    allp.to_parquet(OUT/'tables/oof_predictions.parquet',index=False)
    assert not allp.duplicated(['experiment','protocol','repeat','fold','ID_POLIGONO']).any()
    for name,value in cfg['sha256'].items():assert sha(ROOT/name)==value
    manifest=dict(status='complete',new_blocks=17,algorithms=['EN','CB'],outer_folds=65,outer_models=len(paths),total_fits=sum(a['registry']['fits'] for a in packs),new_oof=len(p),seconds=seconds,warnings=sum(len(a['warnings']) for a in packs),protected_hashes_unchanged=True,no_final_fit138=True,no_PRED=True)
    logs=[dict(experiment=p['registry']['experiment'],protocol=p['registry']['protocol'],repeat=p['registry']['repeat'],fold=p['registry']['fold'],**w) for p in packs for w in p['warnings']]
    (OUT/'audit/warnings.json').write_text(json.dumps(logs,indent=2),encoding='utf-8')
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print(json.dumps(manifest,indent=2))

if __name__=='__main__':
    prepare();start=time.perf_counter();joblib.Parallel(n_jobs=4,backend='loky')(joblib.delayed(work_fold)(i) for i in range(65));finish(time.perf_counter()-start)
