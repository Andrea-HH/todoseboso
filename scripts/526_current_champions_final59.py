"""Fit frozen26/14 on138, append to existing59 comparison; no hidden targets."""
from pathlib import Path
import os
import sys
os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('MKL_NUM_THREADS','1')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import hashlib
import itertools
import json
import time
import warnings
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from threadpoolctl import threadpool_limits
from src.current_champions import load_bundle,ColdExperts,predict_saved,LOCAL7
from src.ct3_residual_conditional.models import CORE

OUT=ROOT/'outputs/modeling/current_champions_final/v1'
PUBLIC=ROOT/'results/current_champions_final/v1'


def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(train,manifest):
    oldpath=ROOT/'outputs/research/geoc_bridge_audit/v1/predictions59_aligned_descriptive.csv'
    old=pd.read_csv(oldpath)
    assert len(old)==59 and old.ID_POLIGONO.is_unique
    ids=train.ID_POLIGONO.tolist()+old.ID_POLIGONO.tolist()
    assert len(set(ids))==197
    paths=[oldpath,ROOT/'outputs/modeling/winner_predictions/v1/tables/features197_target_free.parquet',
           ROOT/'outputs/modeling/geoc_signal_research/v1/cache/features197_target_free.parquet',
           ROOT/'data/processed/family_4/territorial_intraprofile_program/v1/stage_a/geology_full_composition_197.parquet',
           ROOT/'data/processed/family_1/features/family1_features_all.parquet',
           ROOT/'data/processed/family_1/timeseries/sentinel_timeseries.parquet',
           ROOT/'outputs/modeling/geoc_bridge/v1/cache/prepared.joblib']
    core=pd.read_parquet(paths[1]).set_index('ID_POLIGONO').loc[ids]
    local=pd.read_parquet(paths[2]).set_index('ID_POLIGONO').loc[ids]
    geo=pd.read_parquet(paths[3]).set_index('ID_POLIGONO').loc[ids]
    own=pd.read_parquet(paths[4],columns=['ID_POLIGONO','TOPO_BASIC_slope_min']).set_index('ID_POLIGONO').loc[ids]
    frame=pd.DataFrame(index=pd.Index(ids,name='ID_POLIGONO'))
    for c in ['Estado','Municipio','climate_profile']+list(CORE):frame[c]=core[c]
    for c in LOCAL7+['base_centroid_lat','base_centroid_lon']:frame[c]=local[c]
    for c in manifest['geology']['columns']:frame[c]=geo[c.split('::',1)[1]]
    s=pd.read_parquet(paths[5],columns=['ID_POLIGONO','year','month','ndvi_promedio','ndvi_min'])
    s=s[s.ID_POLIGONO.isin(ids)&s.year.between(2022,2025)&s.month.between(5,10)].replace([np.inf,-np.inf],np.nan).copy()
    gap=s.ndvi_promedio-s.ndvi_min
    s['relative_gap']=np.clip(gap.where(gap>=-1e-8).clip(lower=0)/np.maximum(abs(s.ndvi_promedio),.1),0,5)
    ix=pd.MultiIndex.from_product([ids,range(2022,2026),range(5,11)],names=['ID_POLIGONO','year','month'])
    monthly=s.groupby(['ID_POLIGONO','year','month'])[['ndvi_min','relative_gap']].median().reindex(ix)
    floor=monthly.ndvi_min.to_numpy().reshape(197,4,6)
    gap=monthly.relative_gap.to_numpy().reshape(197,4,6)
    frame['I_history_ndvi_floor']=floor[:,:3,:].mean(axis=2).mean(axis=1)
    excess=np.maximum(np.clip((gap[:,3,:]-gap[:,:3,:].mean(axis=1))/np.maximum(gap[:,:3,:].std(axis=1,ddof=1),.05),-6,6),0)
    den=6*np.sum(excess**2,axis=1)
    persistence=np.divide(excess.sum(axis=1)**2,den,out=np.zeros(197),where=den>1e-12)
    persistence[~np.isfinite(excess).all(axis=1)]=np.nan
    frame['I_gap_excess_persistence']=persistence
    frame['I_slope_min']=own.TOPO_BASIC_slope_min
    frame['RENDIMIENTO_T_HA']=np.r_[train.RENDIMIENTO_T_HA.to_numpy(),np.full(59,np.nan)]
    frame=frame.reset_index()[train.columns]
    for c in manifest['features']:
        np.testing.assert_allclose(frame.iloc[:138][c].to_numpy(float),train[c].to_numpy(float),rtol=0,atol=1e-12,equal_nan=True,err_msg=c)
    # Trusted local project artifact: read only frozen geometry and identifiers,
    # never its PCA scores or any fitted L40 prediction function.
    geometry=joblib.load(paths[6]);positions={pid:i for i,pid in enumerate(geometry['ids197'])}
    order=np.array([positions[pid] for pid in ids]);distance=geometry['distance'][np.ix_(order,order)]
    frame.to_parquet(OUT/'features197.parquet',index=False)
    np.save(OUT/'distance197.npy',distance)
    dump(OUT/'input_audit.json',dict(known_feature_parity=True,tolerance=1e-12,n_known=138,n_unknown=59,
        unknown_targets_all_missing=bool(frame.iloc[138:].RENDIMIENTO_T_HA.isna().all()),
        source_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in paths}))
    return frame,distance,old


def compare(frame,distance,old,pack):
    q=np.arange(138,197)
    pred=predict_saved(pack,q,frame,distance)
    again=predict_saved(joblib.load(OUT/'final_train138.joblib'),q,frame,distance)
    for name in pred:np.testing.assert_array_equal(pred[name],again[name])
    result=old.copy()
    result=result.rename(columns={'Champion_t_ha':'Historical_TOP20_TOP15_t_ha'})
    for name in ['Reference26','Compact14']:result[name+'_t_ha']=pred[name]
    result['CT3_native_final138_t_ha']=pred['CT3']
    columns=['CT3_t_ha','Historical_TOP20_TOP15_t_ha','EQUAL3_t_ha','Local04D_t_ha','Reference26_t_ha','Compact14_t_ha']
    assert np.isfinite(result[columns].to_numpy()).all()
    result['six_model_spread_t_ha']=result[columns].max(axis=1)-result[columns].min(axis=1)
    result.to_csv(OUT/'predictions59_comparison.csv',index=False)
    result.to_parquet(OUT/'predictions59_comparison.parquet',index=False)
    rows=[];regional=[]
    for a,b in itertools.combinations(columns,2):
        for scope,subset in [('all',result)]+[('state:'+str(n),g) for n,g in result.groupby('Estado')]+[('municipality:'+str(n),g) for n,g in result.groupby('Municipio')]:
            d=subset[a]-subset[b]
            row=dict(model_A=a,model_B=b,scope=scope,n=len(d),mean_A_minus_B=float(d.mean()),
                mean_absolute_disagreement=float(abs(d).mean()),rms_disagreement=float(np.sqrt(np.mean(d*d))),
                max_absolute_disagreement=float(abs(d).max()),within_025=float((abs(d)<=.25).mean()),
                pearson=float(subset[a].corr(subset[b])) if len(d)>1 else None)
            (rows if scope=='all' else regional).append(row)
    pairs=pd.DataFrame(rows);regions=pd.DataFrame(regional)
    distributions=result[columns].describe(percentiles=[.25,.5,.75]).T.rename_axis('model').reset_index()
    pairs.to_csv(OUT/'pairwise_disagreement.csv',index=False)
    regions.to_csv(OUT/'regional_disagreement.csv',index=False)
    distributions.to_csv(OUT/'prediction_distributions.csv',index=False)
    support=result[['ID_POLIGONO','Estado','Municipio']].copy()
    support['R3_complete']=np.isfinite(frame.iloc[q][['I_history_ndvi_floor','I_gap_excess_persistence','I_slope_min']].to_numpy(float)).all(axis=1)
    support['nearest_training_normalized_distance']=distance[q,:138].min(axis=1)
    support.to_csv(OUT/'prediction_support.csv',index=False)
    for name in ['Reference26','Compact14']:
        result[['ID_POLIGONO',name+'_t_ha']].rename(columns={name+'_t_ha':'RENDIMIENTO_T_HA'}).to_csv(OUT/f'{name}_predictions59.csv',index=False)
    with pd.ExcelWriter(OUT/'comparacion_predicciones59.xlsx') as writer:
        for name,table in [('predictions59',result),('pairwise',pairs),('regional',regions),('distributions',distributions),('support',support),('largest_disagreements',result.nlargest(15,'six_model_spread_t_ha'))]:table.to_excel(writer,sheet_name=name,index=False)
    PUBLIC.mkdir(parents=True,exist_ok=True)
    for name,table in [('pairwise_disagreement',pairs),('prediction_distributions',distributions)]:table.to_csv(PUBLIC/(name+'.csv'),index=False)
    report='# Comparación de predicciones finales de 59 parcelas\n\n'
    report+='Se incorporaron **Reference26 y Compact14**, champions actuales, a la comparación existente de C-T3, Champion histórico TOP20/TOP15, EQUAL3 y L40. Los valores anteriores se conservaron sin reentrenar sus modelos. El archivo original permanece intacto.\n\n'
    report+='Las dos recetas actuales se consolidaron con los 138 rendimientos conocidos, KFold interno4 con shuffle y semilla2026, mismos hiperparámetros y lógica de calibración congelados. La selección y los residuos internos usan sólo entrenamiento. No se seleccionaron variantes por sus predicciones59 ni por acuerdo con L40. C-T3 interno se reajusta como parte nativa de la receta; la comparación conserva el C-T3 final histórico y entrega el nuevo por separado.\n\n'
    report+='## Diferencias entre predicciones\n\nEstos números son **desacuerdos**, no RMSE/MAE contra rendimientos reales. No se conoce cuál modelo acierta más en las59 y el rango entre modelos no es un intervalo predictivo.\n\n'
    report+='| A | B | Media A−B t/ha | Diferencia absoluta media t/ha | Máxima diferencia absoluta |\n|---|---|---|---|---|\n'
    for row in rows:
        if 'Reference26' in row['model_A']+row['model_B'] or 'Compact14' in row['model_A']+row['model_B']:
            report+=f"| {row['model_A']} | {row['model_B']} | {row['mean_A_minus_B']:.4f} | {row['mean_absolute_disagreement']:.4f} | {row['max_absolute_disagreement']:.4f} |\n"
    report+='\n## Archivos\n\nLos detalles por parcela y municipio son privados, bajo `outputs/modeling/current_champions_final/v1/`: `comparacion_predicciones59.xlsx`, `predictions59_comparison.csv`, dos archivos individuales de champions, desacuerdos regionales, soporte y modelo final. Git conserva sólo resúmenes sin identificadores. [Fichas de modelos](../../../documentation/models/README.md).\n'
    report+=f"\nSoporte completo para R3: {int(support.R3_complete.sum())}/59 parcelas. La corrección final se desactiva donde falta soporte, siguiendo la receta original.\n"
    (PUBLIC/'README.md').write_text(report,encoding='utf-8',newline='\n')
    dump(OUT/'comparison_audit.json',dict(n_predictions=59,champions_added=['Reference26','Compact14'],existing_predictions_preserved=True,
        old_columns_unchanged=all(np.array_equal(result[c],old[c]) for c in old if c not in ['Champion_t_ha']),
        historical_champion_unchanged=bool(np.array_equal(result.Historical_TOP20_TOP15_t_ha,old.Champion_t_ha)),
        saved_model_replay_exact=True,R3_complete=int(support.R3_complete.sum()),
        CT3_native_vs_historical_mean_abs=float(abs(pred['CT3']-old.CT3_t_ha).mean()),unknown_error_metrics_computed=False))


def main():
    start=time.perf_counter()
    OUT.mkdir(parents=True,exist_ok=True)
    train,groups,d138,manifest=load_bundle(ROOT/'data/processed/current_champions/v1',verify_saved_models=False)
    design_path=OUT/'frozen_design.json'
    design=dict(models=['Reference26','Compact14'],n_train=138,n_predict=59,inner_splits=4,shuffle=True,seed=2026,
        scope='Native frozen champion consolidation; no B1/new architecture or hyperparameter search.',
        fit_inputs='Only train138 and distance138. Prediction features never used for selection.',
        implementation_sha256=sha(ROOT/'src/current_champions.py'),feature_names=manifest['features'])
    if design_path.exists():assert json.loads(design_path.read_text(encoding='utf-8'))==design
    else:dump(design_path,design)
    model_path=OUT/'final_train138.joblib'
    if not model_path.exists():
        cv=list(KFold(4,shuffle=True,random_state=2026).split(train))
        dump(OUT/'inner_splits.json',[dict(train=a.tolist(),validation=b.tolist()) for a,b in cv])
        print('Fit frozen champions on138; native internal4-fold calibration; no PRED inputs loaded.',flush=True)
        with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            factory=ColdExperts(train,groups,d138,manifest['geology'],'random',np.arange(138),cv,OUT/'fit_cache')
            outer=factory.full_fit(np.arange(138))
            pack=dict(outer_experts=outer,train_positions=np.arange(138),prediction_positions=np.arange(138,197),B1_weight=0.)
            joblib.dump(pack,model_path,compress=3)
            dump(OUT/'fit_audit.json',dict(elapsed_seconds=time.perf_counter()-start,training_rows=138,
                PRED_features_loaded_during_fit=False,R3_strengths=outer['strengths'],
                warnings=[dict(category=w.category.__name__,message=str(w.message)) for w in caught],
                ledger=factory.helper.ledger+factory.helper.role.ledger))
    pack=joblib.load(model_path)
    frame,distance,old=prepare(train,manifest)
    np.testing.assert_array_equal(distance[:138,:138],d138)
    with threadpool_limits(limits=1):compare(frame,distance,old,pack)
    dump(OUT/'complete.json',dict(status='complete',elapsed_seconds=time.perf_counter()-start,final_model_sha256=sha(model_path),
        original_comparison_sha256=sha(ROOT/'outputs/research/geoc_bridge_audit/v1/predictions59_aligned_descriptive.csv')))
    print('Complete:59 aligned predictions, frozen champions, aggregate and private comparisons.',flush=True)


if __name__=='__main__':main()
