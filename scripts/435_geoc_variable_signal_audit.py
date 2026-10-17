"""Read-only GeoC inventory and exploratory TRAIN138 associations, not feature selection."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
import joblib
from scipy.stats import spearmanr
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.geoc_bridge import data,GEO
from src.winner_delivery import holm
OUT=ROOT/'outputs/research/geoc_variable_signal_audit/v1'

def main():
    if (OUT/'manifest.json').exists():raise FileExistsError('Preserve complete audit')
    OUT.mkdir(parents=True,exist_ok=True);sources=[];records={};origins={};frame=None
    for folder,name in [('features_v1','parcel_features_all.csv'),('agronomic_features_v1','parcel_agronomic_features.csv'),('empirical_features_v1','parcel_empirical_features.csv')]:
        p=GEO/'data/processed'/folder/name;mp=p.parent/'feature_manifest.json';sources.extend([p,mp]);m=json.loads(mp.read_text(encoding='utf-8'));q=pd.read_csv(p).set_index('ID_POLIGONO');assert q.index.is_unique and len(q)==197
        frame=q if frame is None else pd.concat([frame,q[[c for c in q if c not in frame]]],axis=1)
        for r in m['features']:assert r['column'] not in records;records[r['column']]=r;origins[r['column']]=dict(source_table=str(p),source_manifest=str(mp))
    retained=ROOT/'outputs/modeling/nonclimatic_local/v1/audit/nonclimatic_retained_features.csv';cache=ROOT/'outputs/modeling/nonclimatic_local/v1/cache/audited_X197_target_free.parquet';repfile=ROOT/'outputs/modeling/nonclimatic_local/v1/cache/representations.joblib';oofpath=ROOT/'outputs/modeling/geoc_bridge/v1/tables/oof_predictions.parquet';prepared=ROOT/'outputs/modeling/geoc_bridge/v1/cache/prepared.joblib';sources.extend([retained,cache,repfile,oofpath,prepared,Path(__file__)])
    columns=pd.read_csv(retained).feature.tolist();assert len(columns)==1831
    x=frame[columns].replace([np.inf,-np.inf],np.nan);stored=pd.read_parquet(cache).set_index('ID_POLIGONO').reindex(x.index)
    np.testing.assert_allclose(x.to_numpy(float),stored[columns].to_numpy(float),rtol=1e-10,atol=1e-10,equal_nan=True)
    a=data();t=a['train'];ids=t.ID_POLIGONO.tolist();y=t.RENDIMIENTO_T_HA.to_numpy();xx=x.loc[ids];profiles=t.climate_profile.to_numpy();states=t.Estado.to_numpy();oof=pd.read_parquet(oofpath);base=oof[(oof.experiment=='CT3')&(oof.protocol=='random')];assert len(base)==1380
    pred=base.groupby('ID_POLIGONO').y_pred.mean().reindex(ids).to_numpy();residual=y-pred
    cfg=dict(scope='Exploratory census of frozen1831 GeoC predictors; no new prediction models, no Y feature selection, no PRED labels',associations='138 known yields, raw Spearman and mean random-OOF CT3 residual Spearman; within-profile Pearson with residual, pair-complete profile centering; not incremental predictive validation',tests='Exact profile-cluster signflip of within-profile crossproducts; complete12 repeated-profile groups, missing groups contribute zero; test only >=100 finite values and >=3 distinct values with nonzero within variation; Holm over eligible columns, exploratory conditional symmetry assumption; no geographic independence guaranteed',pca='Largest absolute loading across PCA20 and projection energy describe representation of X, not yield importance',source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})
    (OUT/'frozen_analysis.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    roots={}
    def leaves(name,stack=()):
        if name in roots:return roots[name]
        if name in stack:raise ValueError('Cycle')
        inputs=records[name].get('inputs',[])
        if not inputs:result={name}
        else:
            assert all(v in records for v in inputs);result=set().union(*(leaves(v,stack+(name,)) for v in inputs))
        roots[name]=result;return result
    repeated=[g for g in np.unique(profiles) if np.sum(profiles==g)>=2];assert len(repeated)==12
    signs=2*((np.arange(2**len(repeated))[:,None]>>np.arange(len(repeated)))&1)-1
    rep=joblib.load(repfile)['transforms']['nonclimatic'];loadings=rep['pca'].components_;pos={c:i for i,c in enumerate(rep['columns'])};rows=[];scores=[]
    def corr(s,v):
        ok=np.isfinite(s)&np.isfinite(v)
        return float(spearmanr(s[ok],v[ok]).statistic) if ok.sum()>=3 and np.unique(s[ok]).size>1 and np.unique(v[ok]).size>1 else np.nan
    def eta(s,g):
        ok=np.isfinite(s);z=pd.DataFrame(dict(x=s[ok],g=g[ok]));den=float(np.sum((z.x-z.x.mean())**2))
        return float(np.sum((z.groupby('g').x.transform('mean')-z.x.mean())**2)/den) if den>1e-20 else np.nan
    for c in columns:
        r=records[c];s=xx[c].to_numpy(float);v=s[np.isfinite(s)];leaf=sorted(leaves(c));lc=loadings[:,pos[c]];xcenter=np.zeros(138);rcenter=np.zeros(138);n_repeated=0
        for group in repeated:
            ix=np.flatnonzero((profiles==group)&np.isfinite(s))
            if len(ix)<2:continue
            xcenter[ix]=s[ix]-s[ix].mean();rcenter[ix]=residual[ix]-residual[ix].mean();n_repeated+=1
        denom=np.linalg.norm(xcenter)*np.linalg.norm(rcenter);within=float(xcenter@rcenter/denom) if denom>1e-12 else np.nan
        eligible=len(v)>=100 and len(np.unique(v))>=3 and np.isfinite(within)
        group_scores=np.array([float(xcenter[profiles==g]@rcenter[profiles==g])/denom if eligible else 0. for g in repeated])
        scores.append(group_scores)
        row=dict(feature=c,source=r.get('source','derived'),family=r.get('family','source_feature'),description=r.get('description',''),meaning=r.get('meaning',''),formula=r.get('formula',''),inputs=json.dumps(r.get('inputs',[]),ensure_ascii=False),root_inputs=json.dumps(leaf,ensure_ascii=False),root_sources=';'.join(sorted(set(records[v].get('source','derived') for v in leaf))),caveats=json.dumps(r.get('caveats',[]),ensure_ascii=False),references_as_supplied=json.dumps(r.get('references',[]),ensure_ascii=False),**origins[c],n_valid=len(v),missing=138-len(v),n_unique=len(np.unique(v)),minimum=float(np.min(v)) if len(v) else np.nan,q25=float(np.quantile(v,.25)) if len(v) else np.nan,median=float(np.median(v)) if len(v) else np.nan,q75=float(np.quantile(v,.75)) if len(v) else np.nan,maximum=float(np.max(v)) if len(v) else np.nan,spearman_yield=corr(s,y),spearman_CT3_OOF_residual=corr(s,residual),within_profile_residual_r=within,repeated_profiles_with_pairs=n_repeated,eligible_cluster_test=eligible,eta2_state=eta(s,states),eta2_profile=eta(s,profiles),max_loading_PC=int(np.argmax(abs(lc)))+1,max_abs_PCA_loading=float(np.max(abs(lc))),PCA20_projection_energy=float(lc@lc))
        rows.append(row)
    inventory=pd.DataFrame(rows);score=np.array(scores).T
    with threadpool_limits(limits=1):
        null=abs(signs@score);observed=abs(score.sum(axis=0));p=np.mean(null>=observed[None,:]-1e-12,axis=0)
    eligible=inventory.eligible_cluster_test.to_numpy();inventory['p_cluster_signflip']=np.where(eligible,p,np.nan);inventory['p_holm']=np.nan;inventory.loc[eligible,'p_holm']=holm(p[eligible]);inventory.to_csv(OUT/'inventario_1831_geoc.csv',index=False,encoding='utf-8-sig')
    # All197 predictors contain no target; source IDs join to separate known labels only.
    x.reset_index().to_parquet(OUT/'variables_1831_197_sin_target.parquet',index=False)
    inventory.groupby('source').agg(variables=('feature','size'),median_abs_CT3_association=('spearman_CT3_OOF_residual',lambda s:s.abs().median()),median_eta_state=('eta2_state','median'),median_eta_profile=('eta2_profile','median')).reset_index().to_csv(OUT/'resumen_fuentes.csv',index=False)
    rankings=[]
    for key in ['spearman_yield','spearman_CT3_OOF_residual','within_profile_residual_r']:
        z=inventory.loc[inventory[key].abs().sort_values(ascending=False).head(30).index].copy();z.insert(0,'ranking_by',key);rankings.append(z)
    tops=pd.concat(rankings);tops.to_csv(OUT/'asociaciones_destacadas_exploratorias.csv',index=False,encoding='utf-8-sig')
    with pd.ExcelWriter(OUT/'catalogo_y_senales_GeoC.xlsx',engine='openpyxl') as writer:
        inventory.to_excel(writer,sheet_name='Inventario_1831',index=False);tops.to_excel(writer,sheet_name='Asociaciones_exploratorias',index=False);pd.read_csv(OUT/'resumen_fuentes.csv').to_excel(writer,sheet_name='Fuentes',index=False)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in cfg['source_sha256'].items())
    manifest=dict(status='complete',variables=1831,parcels_X=197,labels=138,new_predictive_models=0,new_PRED=0,geoc_unchanged=True,source_values_match_archived_matrix=True,repeated_profile_clusters=12,exact_sign_assignments=4096,eligible_tests=int(eligible.sum()),holm_below_05=int((inventory.p_holm<.05).sum()),limitations='Exploratory associations on historically reused labels; CT3 residuals averaged over10 random repeats, not independent residuals; profiles may retain spatial dependence; not causal or incremental predictive significance')
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print(json.dumps(manifest,indent=2));print(tops[tops.ranking_by=='spearman_CT3_OOF_residual'][['feature','spearman_yield','spearman_CT3_OOF_residual','within_profile_residual_r','p_holm']].head(12).to_string(index=False))

if __name__=='__main__':main()
