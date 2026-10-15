"""Audit C4 ancestry without Y; rebuild full/safe/nonclimatic PCA20."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.geoc_bridge import GEO,OUT as BRIDGE,data
from src.nonclimatic_local import exclusion_reasons,fit_representation
OUT=ROOT/'outputs/modeling/nonclimatic_local/v1'

if __name__=='__main__':
    if (OUT/'feature_audit_complete.json').exists():raise FileExistsError('Preserve completed audit')
    for s in ['cache','audit','tables','models','checkpoints']:(OUT/s).mkdir(parents=True,exist_ok=True)
    ids=data()['ids197'];records=[];sources=[];frame=None
    for folder,filename in [('features_v1','parcel_features_all.csv'),('agronomic_features_v1','parcel_agronomic_features.csv'),('empirical_features_v1','parcel_empirical_features.csv')]:
        base=GEO/'data/processed'/folder;manifest=base/'feature_manifest.json';csv=base/filename;sources.extend([manifest,csv]);m=json.loads(manifest.read_text(encoding='utf-8'));records.extend(m['features']);q=pd.read_csv(csv).set_index('ID_POLIGONO').reindex(ids)
        if frame is None:frame=q
        else:
            add=[c for c in q if c not in frame];frame=pd.concat([frame,q[add]],axis=1)
    assert len(frame)==197 and frame.index.is_unique
    byname={r['column']:r for r in records};assert len(byname)==len(records)
    candidates=[r['column'] for r in records if r.get('mode') in ['clean','competition'] and r.get('source')!='external_chirps_daily' and r['column'] in frame and pd.api.types.is_numeric_dtype(frame[r['column']])]
    candidates=list(dict.fromkeys(candidates));assert 'RENDIMIENTO_T_HA' not in candidates
    numeric=frame[candidates].replace([np.inf,-np.inf],np.nan)
    compact=ROOT/'outputs/modeling/winner_predictions/v1/tables/features197_target_free.parquet';sources.append(compact)
    may=pd.read_parquet(compact).set_index('ID_POLIGONO').loc[ids,'S2_ndvi_month_05'].to_numpy();copies=[]
    for col in candidates:
        v=numeric[col].to_numpy(float);valid=np.isfinite(v)&np.isfinite(may)
        if valid.sum()>=100 and np.std(v[valid])>1e-12:
            coef=np.polyfit(may[valid],v[valid],1);error=np.max(abs(v[valid]-np.polyval(coef,may[valid])));scale=max(np.ptp(v[valid]),1e-12)
            if error/scale<1e-10:copies.append(col)
    policy=dict(climate='Exclude climate/CHIRPS/thermal/actualET roots and all declared descendants',other='Exclude SIAP outcome proxies, admin codes/quality, area quality metadata, direct Sentinel NDVI May and affine copies on197 X and declared descendants',may_affine_copies=copies,representations='Fixed PCA20 full SVD and post-score standardization on197 X, transductive; no Y in selection or PCA',sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})
    (OUT/'feature_policy_frozen.json').write_text(json.dumps(policy,indent=2),encoding='utf-8')
    selected={};audit=[]
    for mode in ['safe_with_climate','nonclimatic']:
        why=exclusion_reasons(records,mode,copies);selected[mode]=[c for c in candidates if not why[c]]
        for c in candidates:audit.append(dict(representation=mode,feature=c,source=byname[c].get('source','derived'),inputs=json.dumps(byname[c].get('inputs',[])),included=not bool(why[c]),exclusion='|'.join(sorted(why[c]))))
    pd.DataFrame(audit).to_csv(OUT/'audit/feature_inventory_ancestry.csv',index=False)
    representations={};transforms={};info={}
    with threadpool_limits(limits=1):
        for mode,columns in [('full_c4_parity',candidates)]+list(selected.items()):
            z,transform=fit_representation(frame,columns);representations[mode]=z;transforms[mode]=transform;info[mode]=dict(candidate_features=len(columns),usable_features=len(transform['columns']),pca20_explained_X_variance=float(transform['pca'].explained_variance_ratio_.sum()))
    original=data()['x'];recreated=representations['full_c4_parity'];sign=np.sign((original*recreated).sum(axis=0));delta=float(np.max(abs(original-recreated*sign[None,:])))
    info['full_c4_parity']['original_score_max_difference_after_sign']=delta
    if delta>1e-6:raise ValueError('Cannot isolate a source-matched C4 ablation: full original PCA parity failed '+str(info))
    for mode in selected:
        q=pd.DataFrame(representations[mode],columns=[f'pc{i+1:02d}' for i in range(20)]);q.insert(0,'ID_POLIGONO',ids);q.to_parquet(OUT/'cache'/f'{mode}_scores197.parquet',index=False)
        pd.DataFrame([dict(feature=c,source=byname[c].get('source','derived')) for c in transforms[mode]['columns']]).to_csv(OUT/'audit'/f'{mode}_retained_features.csv',index=False)
    joblib.dump(dict(scores={k:representations[k] for k in selected},transforms={k:transforms[k] for k in selected},ids197=ids),OUT/'cache/representations.joblib',compress=3)
    frame[list(dict.fromkeys(c for cols in selected.values() for c in cols))].reset_index().to_parquet(OUT/'cache/audited_X197_target_free.parquet',index=False)
    pd.DataFrame(audit).groupby(['representation','source','included']).size().rename('columns').reset_index().to_csv(OUT/'audit/source_counts.csv',index=False)
    (OUT/'feature_audit_complete.json').write_text(json.dumps(info,indent=2),encoding='utf-8');print(json.dumps(info,indent=2))
