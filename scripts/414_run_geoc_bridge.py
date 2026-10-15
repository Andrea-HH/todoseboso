"""Freeze exact Local04D snapshot, parity gates, and two evaluation banks."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.geoc_bridge import GEO,OLD,OUT,fold,target_matched,local_prediction
from src.geoc_local04d_snapshot import haversine_distance_matrix,normalized_distance_matrix

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare():
    if (OUT/'execution_complete.json').exists():raise FileExistsError('Preserve complete run')
    for s in ['cache','audit','models','tables','checkpoints']:(OUT/s).mkdir(parents=True,exist_ok=True)
    source=[GEO/'reports/checkpoint_04a/transductive_embeddings.csv',GEO/'data/processed/features_v1/parcel_features_all.csv',GEO/'reports/checkpoint_04b/pseudo_competition_splits.csv',GEO/'reports/checkpoint_05/final_predictions.csv',GEO/'reports/checkpoint_06/parcel_oof_residuals.csv',OLD/'cache/train138.parquet',OLD/'cache/execution_plan.joblib',OLD/'cache/frozen65_splits.joblib',GEO/'data/source/tabular/ID_area_rendimiento_70_30_Reto_AgroCebada.csv',Path(__file__),ROOT/'src/geoc_bridge.py',ROOT/'src/geoc_local04d_snapshot.py']
    plans=joblib.load(OLD/'cache/execution_plan.joblib');keys=set()
    for p in plans:
        keys.add(p['outer_base_key'])
        for item in p['inner']:
            keys.add(item['base_key']);keys.update(v['base_key'] for v in item['residual_contexts'])
    source.extend(OLD/'base_cache'/f'{k}.joblib' for k in sorted(keys))
    cfg=dict(models=['CT3','LOCAL04D','FIXED50','INNER_BLEND','RESIDUAL_LOCAL'],local=dict(k=24,alpha=30,power=1,pca_components=20),representation='Frozen C4 PCA20 from all197 X; score standardization on197; geographic normalization on original138 known locations, no labels. Transductive, not new-parcel inductive.',blend_weights=[0,.25,.5,.75,1],residual_amplitudes=[0,.25,.5],selection='complete original inner OOF RMSE, rounded12 tie smaller Local weight/amplitude; no tuning k/alpha/PCA',residuals='Reuse exact recursively tuned CT3 caches; inner corrector targets exclude residual-heldout AND inner/outer validation labels; outer correction uses crossfitted training residuals. Crossfit/refit size mismatch remains.',banks=dict(original65='5 models, 65 exact folds',geoc16='CT3 retrained/tuned solely on97, Local04D fixed, fixed50; 16 original target_matched_97/41 masks. Development bank, not fresh confirmation08.'),parity='Local04D must reproduce original59 predictions and original656 target_matched predictions before interpretation',no_new_final_predictions=True,no_GeoC_mutation=True,statistical_scope='Exploratory repeatedly reused labels; paired losses with profile/municipal/spatial cluster sensitivity. No automatic winner promotion.',source_sha256={str(p):sha(p) for p in source})
    file=OUT/'frozen_design.json'
    if file.exists():assert json.loads(file.read_text())==cfg
    else:file.write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    meta=pd.read_csv(source[1],usecols=['ID_POLIGONO','CONJUNTO','base_centroid_lat','base_centroid_lon']);ids=meta.ID_POLIGONO.tolist();index={v:i for i,v in enumerate(ids)}
    embedded=pd.read_csv(source[0]);embedded=embedded[embedded.representation.eq('C4_all_deterministic')].set_index('ID_POLIGONO').loc[ids];cols=sorted([v for v in embedded if v.startswith('pc')],key=lambda c:int(c[2:]));assert len(cols)==20
    x=StandardScaler().fit_transform(embedded[cols].to_numpy(float));distance=haversine_distance_matrix(meta.base_centroid_lat,meta.base_centroid_lon)
    observed=np.flatnonzero(meta.CONJUNTO.eq('ENTRENAMIENTO'));distance,scale=normalized_distance_matrix(distance,reference_positions=observed)
    t=pd.read_parquet(source[5]);positions=np.array([index[v] for v in t.ID_POLIGONO]);label=pd.read_csv(source[8]).set_index('ID_POLIGONO')
    np.testing.assert_allclose(t.RENDIMIENTO_T_HA,label.loc[t.ID_POLIGONO].RENDIMIENTO_T_HA)
    prediction=pd.read_csv(source[3]);query=np.array([index[v] for v in prediction.ID_POLIGONO]);assert label.loc[prediction.ID_POLIGONO].RENDIMIENTO_T_HA.isna().all()
    replay=local_prediction(x,distance,observed,query,label.loc[meta.iloc[observed].ID_POLIGONO].RENDIMIENTO_T_HA.to_numpy())
    delta=float(abs(replay-prediction.RENDIMIENTO_T_HA).max());assert delta<1e-9,delta
    memberships=pd.read_csv(source[2]);memberships=memberships[memberships.family.eq('target_matched')];assert memberships.split_id.nunique()==16 and len(memberships)==2208
    memberships.to_csv(OUT/'cache/geoc_memberships.csv',index=False)
    replay_rows=[];old=pd.read_csv(source[4]);old=old[(old.method=='Local04D')&(old.family=='target_matched')]
    for split,g in memberships.groupby('split_id'):
        a=g[g.role=='pseudo_train'].ID_POLIGONO.tolist();b=g[g.role=='pseudo_target'].ID_POLIGONO.tolist()
        p=local_prediction(x,distance,[index[v] for v in a],[index[v] for v in b],label.loc[a].RENDIMIENTO_T_HA.to_numpy())
        q=old[old.split_id.eq(split)].set_index('ID_POLIGONO').loc[b]
        diff=float(abs(p-q.predicted.to_numpy()).max());assert diff<1e-9,(split,diff)
        replay_rows.append(dict(split_id=split,max_difference=diff))
    pd.DataFrame(replay_rows).to_csv(OUT/'audit/original_bank_replay.csv',index=False)
    (OUT/'audit/parity.json').write_text(json.dumps(dict(original59_max_difference=delta,original656_max_difference=max(r['max_difference'] for r in replay_rows),geographic_scale_km=scale,train138_same_labels=True),indent=2),encoding='utf-8')
    joblib.dump(dict(train=t,x=x,distance=distance,train_global=positions,ids197=ids),OUT/'cache/prepared.joblib',compress=3)
    meta.to_csv(OUT/'cache/geoc_metadata.csv',index=False);embedded[cols].reset_index().to_parquet(OUT/'cache/frozen_pca20_197.parquet',index=False)
    return cfg

if __name__=='__main__':
    cfg=prepare();joblib.Parallel(n_jobs=4,backend='loky')(joblib.delayed(fold)(i) for i in range(65))
    splits=pd.read_csv(OUT/'cache/geoc_memberships.csv').split_id.unique()
    joblib.Parallel(n_jobs=4,backend='loky')(joblib.delayed(target_matched)(s) for s in splits)
    packs=[joblib.load(p) for p in sorted((OUT/'checkpoints').glob('*.joblib'))]
    records=pd.DataFrame([r for p in packs for r in p['predictions']]);assert len(records)==5*1794+3*656
    records.to_parquet(OUT/'tables/oof_predictions.parquet',index=False);records.to_csv(OUT/'tables/oof_predictions.csv',index=False)
    pd.DataFrame([p['selection'] for p in packs if 'selection' in p]).to_csv(OUT/'tables/inner_selection.csv',index=False)
    assert all(sha(Path(p))==h for p,h in cfg['source_sha256'].items())
    (OUT/'execution_complete.json').write_text(json.dumps(dict(status='evaluation_complete',original_outer_folds=65,geoc_splits=16,new_oof_records=len(records),protected_sources_unchanged=True,no_new_final_predictions=True),indent=2),encoding='utf-8')
