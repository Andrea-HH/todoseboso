"""Exploratory core4 association and refitted ablation; frozen65, no PRED read."""
from pathlib import Path
import os
import sys
os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('MKL_NUM_THREADS','1')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import itertools
import json
import hashlib
import time
import warnings
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import ParameterGrid
from threadpoolctl import threadpool_limits
from src.family_4.conditional_response import ConditionalFeatures
from src.ct3_residual_conditional.models import CORE,BASE_GRID

OUT=ROOT/'outputs/research/core4_relevance/v1'
PUB=ROOT/'results/core4_relevance/v1'
SPECS={'FULL4':CORE,**{'DROP_'+c:[x for x in CORE if x!=c] for c in CORE},'NDVI_ONLY':[CORE[3]],'TRAIN_MEAN':[]}


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def holm(p):
    p=np.asarray(p,float);order=np.argsort(p);a=np.empty(len(p));a[order]=np.minimum(1,np.maximum.accumulate(p[order]*(len(p)-np.arange(len(p)))))
    return a


def signflip(loss,groups,seed=2026,draws=20000):
    unique=np.unique(groups);sums=np.array([loss[groups==g].sum() for g in unique]);observed=abs(sums.sum())
    if len(unique)<=16:
        signs=2*((np.arange(2**len(unique))[:,None]>>np.arange(len(unique)))&1)-1
        p=np.mean(abs(signs@sums)>=observed-1e-12);exact=True
    else:
        signs=np.random.default_rng(seed).choice([-1,1],size=(draws,len(unique)))
        p=(1+np.sum(abs(signs@sums)>=observed-1e-12))/(draws+1);exact=False
    return dict(p_two_sided=float(p),groups=len(unique),exact=exact)


def association(frame):
    import statsmodels.api as sm
    assert np.isfinite(frame[CORE].to_numpy(float)).all()
    z=(frame[CORE]-frame[CORE].mean())/frame[CORE].std(ddof=0)
    y=frame.RENDIMIENTO_T_HA.to_numpy();cluster=frame.climate_profile.to_numpy()
    rows=[];coefficients=[]
    for label,controls in [('CORE4',None),('CORE4_PLUS_STATE',pd.get_dummies(frame.Estado,drop_first=True,dtype=float))]:
        x=sm.add_constant(z)
        if controls is not None:x=pd.concat([x,controls],axis=1)
        base=sm.OLS(y,x).fit()
        fit=base.get_robustcov_results(cov_type='cluster',groups=cluster,use_correction=True,df_correction=True,use_t=True)
        intervals=fit.conf_int()
        for c in CORE:
            j=x.columns.get_loc(c)
            rows.append(dict(model=label,hypothesis=c+' coefficient=0',p_value=float(fit.pvalues[j]),test='cluster_t'))
            coefficients.append(dict(model=label,feature=c,coefficient_per_SD=float(fit.params[j]),se=float(fit.bse[j]),ci95_low=float(intervals[j,0]),ci95_high=float(intervals[j,1]),p_value=float(fit.pvalues[j]),n=len(frame),clusters=len(np.unique(cluster)),r2_descriptive=float(base.rsquared)))
        for block,columns in [('RAIN_BLOCK',CORE[:3]),('ALL4',CORE)]:
            restriction=np.zeros((len(columns),len(x.columns)))
            for i,c in enumerate(columns):restriction[i,x.columns.get_loc(c)]=1
            test=fit.f_test(restriction)
            rows.append(dict(model=label,hypothesis=block+' all coefficients=0',p_value=float(test.pvalue),test='cluster_F'))
    # Rainfall is constant within a profile; only NDVI is identified in this FE comparison.
    sizes=frame.groupby('climate_profile')[CORE[3]].nunique()
    use=frame.climate_profile.isin(sizes[sizes>1].index)
    within_frame=frame.loc[use]
    x=sm.add_constant(pd.concat([z.loc[use,[CORE[3]]],pd.get_dummies(within_frame.climate_profile.astype(str),drop_first=True,dtype=float)],axis=1))
    base=sm.OLS(y[use],x).fit();fit=base.get_robustcov_results(cov_type='cluster',groups=cluster[use],use_correction=True,df_correction=True,use_t=True)
    j=x.columns.get_loc(CORE[3]);ci=fit.conf_int()[j]
    rows.append(dict(model='NDVI_PLUS_PROFILE_FIXED_EFFECTS',hypothesis=CORE[3]+' within-profile coefficient=0',p_value=float(fit.pvalues[j]),test='cluster_t'))
    coefficients.append(dict(model='NDVI_PLUS_PROFILE_FIXED_EFFECTS',feature=CORE[3],coefficient_per_SD=float(fit.params[j]),se=float(fit.bse[j]),ci95_low=float(ci[0]),ci95_high=float(ci[1]),p_value=float(fit.pvalues[j]),n=int(use.sum()),clusters=int(within_frame.climate_profile.nunique()),r2_descriptive=float(base.rsquared)))
    tests=pd.DataFrame(rows);tests['p_holm_family13']=holm(tests.p_value)
    tests.to_csv(PUB/'association_tests.csv',index=False)
    pd.DataFrame(coefficients).to_csv(PUB/'association_coefficients.csv',index=False)
    return tests


def tune(frame,y,tr,va,inner,columns):
    target=y[tr];a=frame.iloc[tr]
    if not columns:return np.repeat(target.mean(),len(va)),dict(fallback='training mean')
    probe=ConditionalFeatures(tuple(columns)).fit(a)
    if not probe.support_.any():return np.repeat(target.mean(),len(va)),dict(fallback='all constant')
    prepared=[]
    for c,d in inner:
        rep=ConditionalFeatures(tuple(columns)).fit(a.iloc[c])
        z=rep.transform(a.iloc[c]);q=rep.transform(a.iloc[d])
        prepared.append((z,q,target[c],target[d]))
    params=list(ParameterGrid(BASE_GRID));scores=[]
    for p in params:
        kw={k.split('__')[1]:v for k,v in p.items()};loss=[]
        for z,q,yt,yv in prepared:
            prediction=ElasticNet(**kw,max_iter=200000,random_state=2026).fit(z,yt).predict(q) if z.shape[1] else np.repeat(yt.mean(),len(q))
            loss.append(np.sqrt(np.mean((prediction-yv)**2)))
        scores.append(float(np.mean(loss)))
    best=int(np.argmin(scores));kw={k.split('__')[1]:v for k,v in params[best].items()}
    model=ElasticNet(**kw,max_iter=200000,random_state=2026).fit(probe.transform(a),target)
    return model.predict(probe.transform(frame.iloc[va])),dict(params=kw,inner_mean_fold_rmse=scores[best])


def metrics(g):
    e=g.y_pred-g.y_true;den=np.sum((g.y_true-g.y_true.mean())**2)
    return dict(rmse=float(np.sqrt(np.mean(e**2))),mae=float(abs(e).mean()),r2=float(1-np.sum(e**2)/den),bias=float(e.mean()))


def main():
    start=time.perf_counter();OUT.mkdir(parents=True,exist_ok=True);PUB.mkdir(parents=True,exist_ok=True)
    design=dict(scope='Exploratory retrospective core4 relevance; no claim of confirmatory post-selection p-values or causal effects',
        specs=SPECS,outer_folds=65,association_tests=13,association_adjustment='Holm all13; OLS cluster-profile t/F; global4 and state-adjusted4; NDVI within-profile limited to profiles with NDVI variation, X-only support rule',
        prediction_tests=24,prediction_adjustment='Holm all6 ablation/control contrasts x4 protocols; two-sided grouped loss signflip with symmetry assumption',
        grouping='profile for random/profile; municipality for municipal; spatial block for spatial',
        random_repeats='losses averaged per parcel before inference; no1380 independent parcels',
        interval='no bootstrap confidence interval claimed; coefficient intervals marginal exploratory95percent',
        seed=2026,permutations=20000,new_PRED=False,new_Reference26_fit=False,
        caveat='Ablations identify predictive value inside CT3, not effects of deleting those inputs in the whole26 architecture.',
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    cfg=OUT/'frozen_design.json'
    if cfg.exists():assert json.loads(cfg.read_text(encoding='utf-8'))==design
    else:dump(cfg,design)
    dump(ROOT/'configs/core4_relevance/v1/frozen_design.json',design)
    frame=pd.read_parquet(ROOT/'data/processed/current_champions/v1/train138.parquet')
    assert len(frame)==138 and frame.ID_POLIGONO.is_unique
    assert frame.groupby('climate_profile')[CORE[:3]].nunique().max().max()==1
    groups=pd.read_csv(ROOT/'data/processed/current_champions/v1/groups.csv').set_index('ID_POLIGONO')
    plan=json.loads((ROOT/'data/processed/current_champions/v1/splits.json').read_text(encoding='utf-8'))
    if isinstance(plan,dict):plan=plan['folds']
    plan=plan[:65];assert len(plan)==65
    with threadpool_limits(limits=1):tests=association(frame)
    y=frame.RENDIMIENTO_T_HA.to_numpy();ledger=json.loads((OUT/'fit_ledger.json').read_text(encoding='utf-8')) if (OUT/'fit_ledger.json').exists() else [];records=[]
    with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        for ix,fold in enumerate(plan):
            path=OUT/'checkpoints'/f'{ix:02d}.parquet';path.parent.mkdir(exist_ok=True)
            tr=np.array(fold['train_positions']);va=np.array(fold['validation_positions'])
            inner=[(np.array(i['train_relative_positions']),np.array(i['validation_relative_positions'])) for i in fold['inner']]
            assert not set(tr)&set(va)
            if path.exists():records.append(pd.read_parquet(path));continue
            rows=[]
            for name,columns in SPECS.items():
                prediction,info=tune(frame,y,tr,va,inner,columns)
                ledger.append(dict(execution_index=ix,model=name,**info))
                for j,value in zip(va,prediction):rows.append(dict(execution_index=ix,protocol=fold['protocol'],repeat=fold['repeat'],fold=fold['fold'],experiment=name,ID_POLIGONO=frame.iloc[j].ID_POLIGONO,y_true=y[j],y_pred=float(value)))
            result=pd.DataFrame(rows);result.to_parquet(path,index=False);records.append(result)
            if (ix+1)%10==0:print(f'Completed {ix+1}/65 external folds',flush=True)
    p=pd.concat(records,ignore_index=True);p.to_parquet(OUT/'oof_predictions.parquet',index=False)
    expected=pd.read_parquet(ROOT/'data/processed/current_champions/v1/expected_oof.parquet')
    keys=['execution_index','protocol','repeat','fold','ID_POLIGONO']
    check=p[p.experiment=='FULL4'].merge(expected[expected.experiment=='CT3'],on=keys,suffixes=('_new','_original'),validate='one_to_one')
    assert len(check)==1794
    maxdiff=float(np.max(abs(check.y_pred_new-check.y_pred_original)))
    np.testing.assert_allclose(check.y_pred_new,check.y_pred_original,rtol=0,atol=1e-10)
    rows=[dict(experiment=n,protocol=pro,repeat=re,**metrics(g)) for (n,pro,re),g in p.groupby(['experiment','protocol','repeat'])]
    byrepeat=pd.DataFrame(rows);byrepeat.to_csv(PUB/'metrics_by_repeat.csv',index=False)
    summary=byrepeat.drop(columns='repeat').groupby(['experiment','protocol']).mean().reset_index();summary.to_csv(PUB/'metrics.csv',index=False)
    comparisons=[]
    for pro,g in p.groupby('protocol'):
        ids=sorted(g.ID_POLIGONO.unique());truth=g[['ID_POLIGONO','y_true']].drop_duplicates().set_index('ID_POLIGONO').loc[ids].y_true.to_numpy()
        arrays={n:h.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy() for n,h in g.groupby('experiment')}
        group=groups.loc[ids,pro if pro in ['municipality','spatial'] else 'climate_profile'].astype(str).to_numpy()
        full=arrays['FULL4'];full_loss=np.mean((full-truth)**2,axis=0)
        for name,values in arrays.items():
            if name=='FULL4':continue
            loss=np.mean((values-truth)**2,axis=0)-full_loss
            comparisons.append(dict(protocol=pro,removed_or_control=name,delta_rmse_reduced_minus_full=float(np.sqrt(np.mean((values-truth)**2,axis=1)).mean()-np.sqrt(np.mean((full-truth)**2,axis=1)).mean()),mean_mse_reduced_minus_full=float(loss.mean()),**signflip(loss,group)))
    prediction_tests=pd.DataFrame(comparisons);assert len(prediction_tests)==24
    prediction_tests['p_holm_family24']=holm(prediction_tests.p_two_sided);prediction_tests.to_csv(PUB/'ablation_tests.csv',index=False)
    prior=pd.read_csv(ROOT/'outputs/research/four_leaders/v1/paired_tests.csv')
    prior=prior[((prior.left=='CT3')&(prior.right=='Reference26'))|((prior.right=='CT3')&(prior.left=='Reference26'))]
    assert len(prior)==4;prior.to_csv(PUB/'existing_26_vs_CT3_tests.csv',index=False)
    dump(OUT/'fit_ledger.json',ledger)
    dump(OUT/'warnings.json',[dict(category=w.category.__name__,message=str(w.message)) for w in caught])
    audit=dict(n_parcels=138,n_profiles=int(frame.climate_profile.nunique()),n_outer_folds=65,ablation_rows=len(p),full4_matches_original_max_difference=maxdiff,
        new_26_fits=0,new_final_fits=0,PRED_read=False,association_tests=len(tests),prediction_tests=len(prediction_tests),
        association_holm_significant=int((tests.p_holm_family13<.05).sum()),ablation_holm_significant=int((prediction_tests.p_holm_family24<.05).sum()),elapsed_seconds=time.perf_counter()-start)
    dump(PUB/'audit.json',audit)
    with pd.ExcelWriter(OUT/'relevancia_core4.xlsx') as writer:
        for name,table in [('association_tests',tests),('association_coefficients',pd.read_csv(PUB/'association_coefficients.csv')),('ablation_metrics',summary),('ablation_tests',prediction_tests),('existing26_vs_CT3',prior)]:table.to_excel(writer,sheet_name=name,index=False)
    print(json.dumps(audit,indent=2),flush=True)


if __name__=='__main__':main()
