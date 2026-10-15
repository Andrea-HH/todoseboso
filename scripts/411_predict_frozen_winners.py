"""Authorized 59 PRED delivery: preserve archives, freeze consolidation first."""
from pathlib import Path
import sys,json,hashlib,warnings,time
import numpy as np
import pandas as pd
import joblib
from scipy.stats import spearmanr
from sklearn.pipeline import Pipeline
from sklearn.linear_model import ElasticNet
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.ct3_residual_conditional.models import CORE
from src.family_4.conditional_response import ConditionalFeatures
from src.family_5.gpr_initial.model import CompactGPR,OPT
from src.family_7.models import BoostModel
from src.winner_delivery import FinalStage
OUT=ROOT/'outputs/modeling/winner_predictions/v1'
OLD=ROOT/'outputs/modeling/ct3_residual_conditional/v1'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def consensus(values):
    codes=pd.Series([json.dumps(v,sort_keys=True) for v in values]);counts=codes.value_counts()
    best=sorted(counts[counts==counts.max()].index)[0]
    return json.loads(best),{str(k):int(v) for k,v in counts.items()}
def rank(frame,target,n):
    # Preserve archived pandas ranking and candidate column order for ties.
    scores={c:abs(float(spearmanr(frame[c],target).statistic)) if frame[c].nunique()>1 else 0. for c in frame}
    return pd.Series(scores).sort_values(ascending=False).head(n).index.tolist()

def main():
    if OUT.exists():raise FileExistsError('Preserve completed or in-progress delivery; use a new version')
    for sub in ['models','tables','audit','statistics']:(OUT/sub).mkdir(parents=True)
    src=ROOT/'data/processed/family_1/features'
    compact=ROOT/'data/processed/family_4/territorial_intraprofile_program/v1/stage_c/c_features_197_target_free.parquet'
    master=ROOT/'data/original/01_tablas_maestras/ID_area_rendimiento_70_30_Reto_AgroCebada.csv'
    hp_path=ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization/models/selected_hyperparameters.csv'
    rs4_path=ROOT/'outputs/modeling/residual_signal_audit/stage4_champion_reconstruction/predictions/oof_predictions.parquet'
    rs5_path=ROOT/'outputs/modeling/residual_signal_audit/stage5_second_residual_audit/checkpoints/residual2_predictions.parquet'
    sources=[compact,master,OLD/'cache/train138.parquet',OLD/'cache/execution_plan.joblib',OLD/'tables/base_fit_registry.csv',src/'climate_features.parquet',src/'history_features.parquet',src/'topography_basic_features.parquet',hp_path,rs4_path,rs5_path,ROOT/'outputs/modeling/family_7/boosting/v1/tables/fit_registry.csv',ROOT/'outputs/modeling/compact_ensemble/v1/tables/oof_predictions.parquet',ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization/predictions/oof_predictions.parquet',ROOT/'outputs/modeling/family_7/expansion/v1/splits/group_memberships.csv',Path(__file__),ROOT/'src/winner_delivery.py',ROOT/'src/family_7/models.py',ROOT/'src/family_5/gpr_initial/model.py',ROOT/'src/family_5/gpr_initial/kernel.py',ROOT/'src/family_4/conditional_response.py']
    plans=joblib.load(OLD/'cache/execution_plan.joblib');keys={p['outer_base_key'] for p in plans if p['protocol']=='random'}
    reg=pd.read_csv(OLD/'tables/base_fit_registry.csv');ctparams,ctfreq=consensus(reg[reg.key.isin(keys)].params.map(json.loads));assert len(keys)==50
    cbreg=pd.read_csv(sources[11]);cbreg=cbreg[(cbreg.experiment=='F7-00')&(cbreg.protocol=='random')&(cbreg.context=='outer')];assert len(cbreg)==50
    cbparams,cbfreq=consensus([dict(iterations=int(r.iterations),depth=int(r.depth),learning_rate=float(r.learning_rate),l2_leaf_reg=float(r.l2_leaf_reg)) for r in cbreg.itertuples()])
    hp=pd.read_csv(hp_path);chparams={};chfreq={}
    for k in ['climate_params','history_params','topography_params']:chparams[k],chfreq[k]=consensus(hp[k].map(json.loads))
    design=dict(winners=['C-T3','Champion','EQUAL3'],authorization='User explicitly confirmed three winners and 59 PRED generation',final_training_n=138,prediction_n=59,consolidation='modal complete hyperparameter tuple across the 50 original random outer fits, lexical JSON tie; no selection from PRED values or external protocol rankings',ct3=ctparams,catboost=cbparams,gpr=OPT,champion=chparams,equal3_weights=dict(ct3=1/3,gpr=1/3,catboost=1/3),champion_final_targets='History: y minus mean of 10 archived TOP20_ENET_BASE OOF predictions. Topography: y minus mean of 10 archived strict Climate+History champion_pred OOF predictions. Re-rank climate20 on full TRAIN y, history15 on full TRAIN cross-fitted residual1. All final stages fit 138 TRAIN; never fit PRED or substitute training fitted residuals.',evaluation='Reuse archived OOF, Champion random only; refit consolidation is defined now and has no new independent test. Mean repeated OOF losses, never score mean predictions as original CV.',statistics=dict(seed=2026,bootstrap_draws=5000,primary_clusters=dict(random='climate_profile',climate_profile='climate_profile',municipality='municipality',spatial='spatial'),paired_signflip='mean per-parcel squared loss averaged over repeats; exact signs up to16 clusters, otherwise20000 draws',multiplicity='Holm across all six available model-pair/protocol MSE contrasts',limitations='Fixed-prediction conditional exploratory intervals; no training or model-selection uncertainty, no correction for historical search over all project experiments; clusters may retain spatial dependence. Five spatial blocks imply two-sided exact p>=.0625. No calibrated PRED intervals.'),sha256={str(p.relative_to(ROOT)):sha(p) for p in sources})
    (OUT/'frozen_design.json').write_text(json.dumps(design,indent=2),encoding='utf-8')
    (OUT/'audit/parameter_consensus.json').write_text(json.dumps(dict(ct3=ctfreq,catboost=cbfreq,champion=chfreq),indent=2),encoding='utf-8')
    data=pd.read_parquet(compact);labels=pd.read_csv(master);train=pd.read_parquet(OLD/'cache/train138.parquet')
    label=labels.set_index('ID_POLIGONO');trainids=train.ID_POLIGONO.tolist();predids=labels.loc[labels.RENDIMIENTO_T_HA.isna(),'ID_POLIGONO'].sort_values().tolist()
    assert len(trainids)==138 and len(predids)==59 and not set(trainids)&set(predids)
    x=data.set_index('ID_POLIGONO');assert len(x)==197 and x.index.is_unique
    for file in ['climate_features.parquet','history_features.parquet','topography_basic_features.parquet']:
        extra=pd.read_parquet(src/file).set_index('ID_POLIGONO')
        for c in extra:
            if c in x:np.testing.assert_allclose(x[c],extra.reindex(x.index)[c],equal_nan=True)
            else:x[c]=extra.reindex(x.index)[c]
    x=x.reset_index();x.to_parquet(OUT/'tables/features197_target_free.parquet',index=False)
    a=x.set_index('ID_POLIGONO').loc[trainids].reset_index();b=x.set_index('ID_POLIGONO').loc[predids].reset_index()
    np.testing.assert_allclose(a[CORE],train[CORE]);y=train.RENDIMIENTO_T_HA.to_numpy();np.testing.assert_allclose(y,label.loc[trainids].RENDIMIENTO_T_HA)
    ccols=[c for c in pd.read_parquet(src/'climate_features.parquet') if c!='ID_POLIGONO'];hcols=[c for c in pd.read_parquet(src/'history_features.parquet') if c.startswith('HIST_S2_') and not c.endswith('_months')];tcols=[c for c in pd.read_parquet(src/'topography_basic_features.parquet') if c!='ID_POLIGONO']
    assert len(hcols)==16 and len(tcols)==25
    climate_oof=pd.read_parquet(rs4_path);climate_oof=climate_oof[climate_oof.pipeline.eq('TOP20_ENET_BASE')]
    ch_oof=pd.read_parquet(rs5_path);ch_oof=ch_oof[ch_oof.pipeline.eq('RIDGE_RESIDUAL2_TOPO_BASIC')]
    for frame in [climate_oof,ch_oof]:
        assert len(frame)==1380 and (frame.groupby('ID_POLIGONO').size()==10).all()
        np.testing.assert_allclose(frame.y_true,label.loc[frame.ID_POLIGONO].RENDIMIENTO_T_HA)
    r1=y-climate_oof.groupby('ID_POLIGONO').y_pred.mean().reindex(trainids).to_numpy()
    r2=y-ch_oof.groupby('ID_POLIGONO').champion_pred.mean().reindex(trainids).to_numpy()
    pd.DataFrame(dict(ID_POLIGONO=trainids,y_true=y,residual_history_target=r1,residual_topography_target=r2)).to_csv(OUT/'tables/champion_crossfitted_training_targets.csv',index=False)
    chosen_c=rank(a[ccols],y,20);chosen_h=rank(a[hcols],r1,15)
    start=time.perf_counter();logs=[]
    with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        ct3=Pipeline([('repr',ConditionalFeatures(tuple(CORE))),('model',ElasticNet(alpha=ctparams['model__alpha'],l1_ratio=ctparams['model__l1_ratio'],max_iter=200000,random_state=2026))]).fit(a,y)
        gp=CompactGPR(CORE).fit(a,y)
        cb=BoostModel(CORE,'CatBoost',cbparams).fit(a,y)
        champion=[FinalStage(chosen_c,'ENET',chparams['climate_params']).fit(a,y),FinalStage(chosen_h,'XGB',chparams['history_params']).fit(a,r1),FinalStage(tcols,'RIDGE',chparams['topography_params']).fit(a,r2)]
        logs=[dict(category=w.category.__name__,message=str(w.message)) for w in caught]
        # No PRED value participates before the models and policies are frozen.
        ct=ct3.predict(b);g=gp.predict(b);c=np.asarray(cb.booster_.predict(cb.preprocess_.transform(b),thread_count=1))
        stages=np.column_stack([m.predict(b) for m in champion]);ch=stages.sum(axis=1);eq=(ct+g+c)/3
    pack=dict(ct3=ct3,gpr=gp,catboost=cb,champion=champion,train_ids=trainids,prediction_ids=predids,equal3_weights=[1/3]*3,features=dict(compact4=CORE,champion_climate=chosen_c,champion_history=chosen_h,champion_topography=tcols),policy=design)
    joblib.dump(pack,OUT/'models/final_winners_train138.joblib',compress=3)
    result=b[['ID_POLIGONO','Estado','Municipio','climate_profile']].copy();result['AREA_HA']=label.loc[predids].AREA_HA.to_numpy()
    for name,values in [('CT3_t_ha',ct),('Champion_t_ha',ch),('EQUAL3_t_ha',eq),('component_GPR_t_ha',g),('component_CatBoost_t_ha',c),('Champion_climate_t_ha',stages[:,0]),('Champion_history_correction_t_ha',stages[:,1]),('Champion_topography_correction_t_ha',stages[:,2])]:result[name]=values
    assert len(result)==59 and result.ID_POLIGONO.is_unique and np.isfinite(result.select_dtypes('number')).all().all()
    result['winner_spread_t_ha']=result[['CT3_t_ha','Champion_t_ha','EQUAL3_t_ha']].max(axis=1)-result[['CT3_t_ha','Champion_t_ha','EQUAL3_t_ha']].min(axis=1)
    result.to_csv(OUT/'tables/predictions59.csv',index=False);result.to_parquet(OUT/'tables/predictions59.parquet',index=False)
    for c in ['CT3','Champion','EQUAL3']:result[['ID_POLIGONO','Estado','Municipio','AREA_HA',c+'_t_ha']].to_csv(OUT/'tables'/f'predictions59_{c}.csv',index=False)
    # Explicitly diagnostic: marginal support, not a confidence interval.
    support=[]
    for model,cols in [('compact4',CORE),('Champion',chosen_c+chosen_h+tcols)]:
        low=a[cols].min();high=a[cols].max();outside=b[cols].lt(low)|b[cols].gt(high)
        for i,pid in enumerate(predids):support.append(dict(ID_POLIGONO=pid,representation=model,outside_training_range_count=int(outside.iloc[i].sum()),outside_features='|'.join(outside.columns[outside.iloc[i]].tolist()),missing_count=int(b.iloc[i][cols].isna().sum())))
    pd.DataFrame(support).to_csv(OUT/'tables/prediction_support.csv',index=False)
    (OUT/'audit/fit_diagnostics.json').write_text(json.dumps(dict(warnings=logs,gpr=gp.parameters(),catboost=cb.parameters(),ct3_iterations=int(ct3['model'].n_iter_),ct3_dual_gap=float(ct3['model'].dual_gap_),seconds=time.perf_counter()-start),indent=2),encoding='utf-8')
    (OUT/'prediction_complete.json').write_text(json.dumps(dict(status='predictions_complete',n_train=138,n_PRED=59,final_base_models=6,source_hashes_preserved=all(sha(ROOT/p)==h for p,h in design['sha256'].items())),indent=2),encoding='utf-8')
    print(result[['CT3_t_ha','Champion_t_ha','EQUAL3_t_ha','winner_spread_t_ha']].describe().to_string())

if __name__=='__main__':main()
