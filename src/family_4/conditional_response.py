"""Frozen retrospective candidates; nested evaluation using immutable climate contexts."""
from pathlib import Path
import json
import hashlib
import itertools
import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import SplineTransformer
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import GridSearchCV, ParameterGrid
from src.family_1 import lm_multiblock as lm

ROOT,ID,TARGET,RAIN=lm.ROOT,lm.ID,lm.TARGET,lm.RAIN
OUT=ROOT/'outputs/modeling/family_4/conditional_yield_response/v1'
PROC=ROOT/'data/processed/family_4/conditional_yield_response/v1'
NDVI='S2_ndvi_month_05'
Q10='S2_ndvi_promedio_q10'
SAVI='S2_savi_promedio_runup_duration'
DTR='CLIMATE_dtr_mean_std'
SLOPE='slope_degrees'
SOIL='soil_map_share_mentions_group_VR'
GRID={'model__alpha':lm.k.ALPHA,'model__l1_ratio':lm.k.L1}
SPECS={
 'F4-S1':dict(kind='direct',cols=[NDVI]),
 'F4-S2':dict(kind='residual',cols=[NDVI]),
 'F4-S3':dict(kind='residual',cols=[Q10]),
 'F4-S4':dict(kind='residual',cols=[SAVI]),
 'F4-S5':dict(kind='direct',cols=[DTR]),
 'F4-S6':dict(kind='residual',cols=[DTR]),
 'F4-A':dict(kind='residual',cols=[SLOPE,'rain_total'],interaction=[SLOPE,'rain_total']),
 'F4-B':dict(kind='residual',cols=[NDVI,'rain_total'],interaction=[NDVI,'rain_total']),
 'F4-C':dict(kind='residual',cols=[NDVI,'expected_y'],interaction=[NDVI,'expected_y']),
 'F4-D':dict(kind='residual',cols=[SLOPE,SOIL],interaction=[SLOPE,SOIL],soil_gate=True),
 'F4-G1':dict(kind='residual',cols=[SLOPE],spline=True),
}

class ConditionalFeatures(BaseEstimator,TransformerMixin):
    """Train-only scaling; interactions include both main effects; small spline."""
    def __init__(self,cols=(),interaction=(),spline=False,soil_gate=False):
        self.cols=cols;self.interaction=interaction;self.spline=spline;self.soil_gate=soil_gate
    def fit(self,X,y=None):
        raw=X[list(self.cols)].to_numpy(float)
        self.median_=np.nanmedian(raw,axis=0)
        self.median_=np.where(np.isfinite(self.median_),self.median_,0)
        raw=np.where(np.isfinite(raw),raw,self.median_)
        self.mean_=raw.mean(axis=0);sd=raw.std(axis=0)
        self.support_=sd>1e-12
        floors=np.array([.05 if c==NDVI else 1e-12 for c in self.cols])
        self.scale_=np.maximum(sd,floors)
        self.interaction_enabled_=True
        if self.soil_gate:
            z=X[SOIL].to_numpy();positive=z>1e-8
            self.interaction_enabled_=bool(positive.sum()>=10 and (~positive).sum()>=10 and X.loc[positive,'climate_profile'].nunique()>=3 and X.loc[~positive,'climate_profile'].nunique()>=3)
        self.spline_=None
        if self.spline:
            self.spline_=SplineTransformer(n_knots=3,degree=2,include_bias=False,extrapolation='linear').fit(raw)
        self.effective_k_=[]
        self.names_=list(np.array(self.cols)[self.support_])
        if self.interaction:self.names_+=['interaction:'+'*'.join(self.interaction)]
        if self.spline:self.names_=[f'slope_spline_{i}' for i in range(self.spline_.n_features_out_)]
        return self
    def transform(self,X):
        raw=X[list(self.cols)].to_numpy(float)
        raw=np.where(np.isfinite(raw),raw,self.median_)
        if self.spline:return self.spline_.transform(raw)
        z=(raw-self.mean_)/self.scale_
        parts=[z[:,self.support_]]
        if self.interaction:
            i,j=[list(self.cols).index(c) for c in self.interaction]
            parts.append((z[:,i]*z[:,j]*self.interaction_enabled_)[:,None])
        return np.concatenate(parts,axis=1)
    def get_feature_names_out(self,input_features=None):return np.array(self.names_)

def model(spec):
    cols=(RAIN if spec['kind']=='direct' else [])+spec['cols']
    return Pipeline([('repr',ConditionalFeatures(tuple(cols),tuple(spec.get('interaction',[])),spec.get('spline',False),spec.get('soil_gate',False))),('model',ElasticNet(max_iter=200000,random_state=2026))])

def load():
    d=pd.read_parquet(ROOT/'data/processed/family_1/m_historical_multisensor/v1/m_features_197_target_free.parquet')
    f=pd.read_parquet(ROOT/'data/processed/family_1/features/family1_features_all.parquet')
    missing=[c for c in [NDVI,Q10,SAVI,DTR] if c not in d]
    d=d.merge(f[[ID]+missing],on=ID,validate='one_to_one')
    d['rain_total']=d[RAIN].sum(axis=1,min_count=7)
    assert TARGET not in d and len(d)==197
    t=lm.k.j.supervised_data(d,pd.read_csv(lm.k.j.MASTER))
    return d,t

def setup():
    if (OUT/'manifest.json').exists():raise FileExistsError('Completed F4 version is immutable')
    for p in [OUT,PROC]+[OUT/x for x in ['tables','models','checkpoints','figures','splits']]:p.mkdir(parents=True,exist_ok=True)
    config=dict(specs=SPECS,grid=GRID,eta=lm.ETA,exploratory=True,retrospective_screening_n=1473,selection_inside_internal_cv=True,s7_status='suspended: no verified whole K5 nested training contexts available; no global OOF residual reuse',gam='slope additive smooth,3knots degree2 fixed; no interactions with spline',soil='VR unit mention fraction; interaction disabled inside each training if <10 positive/negative parcels or <3 profiles on either side',quartiles='post-fit only',candidates_frozen_before_fitting=True)
    p=OUT/'configuration.json'
    if p.exists():assert json.loads(p.read_text())==json.loads(json.dumps(config))
    else:p.write_text(json.dumps(config,indent=2),encoding='utf-8')
    d,t=load();d.to_parquet(PROC/'f4_features_197_target_free.parquet',index=False)
    splits,table,assign=lm.k.j.load_frozen_splits(t)
    table.to_csv(OUT/'splits/outer_and_inner_splits.csv',index=False);assign.to_csv(OUT/'splits/group_memberships.csv')
    return splits

def enrich(frame,expected):
    a=frame.copy();a['expected_y']=np.asarray(expected)
    return a

def fit_fold(index):
    d,t=load();splits,_,_=lm.k.j.load_frozen_splits(t)
    protocol,repeat,fold,tr,va,inner=splits[index];a,b=t.iloc[tr],t.iloc[va]
    path=lm.locations('L')[0]/'base_cache'/f'contexts_rain_{protocol}_{repeat}_{fold}.joblib'
    if not path.exists():raise FileNotFoundError('Verified nested base context required: '+str(path))
    full,internal,logs=joblib.load(path)
    assert len(full['crossfit'])==len(a)
    for log in logs:
        assert not set(json.loads(log['fit_ids']))&set(json.loads(log['heldout_ids']))
    for name,spec in SPECS.items():
        dest=OUT/'checkpoints'/f'{name}_{protocol}_{repeat}_{fold}.joblib'
        if dest.exists():continue
        key=dict(experiment=name,protocol=protocol,repeat=repeat,fold=fold)
        if spec['kind']=='direct':
            search=lm.k.strict_fit(GridSearchCV(model(spec),GRID,cv=inner,scoring='neg_root_mean_squared_error',n_jobs=1,error_score='raise'),a,a[TARGET])
            fitted=search.best_estimator_;prediction=fitted.predict(b);eta=1
            best=dict(params=search.best_params_,inner_rmse=-search.best_score_,eta=1)
            tune=[dict(params=p,inner_rmse=-s,eta=1) for p,s in zip(search.cv_results_['params'],search.cv_results_['mean_test_score'])]
            train=a;valid=b
        else:
            tune=[]
            for params in ParameterGrid(GRID):
                scores={e:[] for e in lm.ETA}
                for (itr,iva),ctx in zip(inner,internal):
                    aa=enrich(a.iloc[itr],ctx['crossfit']);bb=enrich(a.iloc[iva],ctx['base'])
                    fit=lm.k.strict_fit(model(spec).set_params(**params),aa,ctx['residual'])
                    correction=fit.predict(bb)
                    for e in lm.ETA:scores[e].append(np.sqrt(np.mean((bb[TARGET].to_numpy()-ctx['base']-e*correction)**2)))
                tune += [dict(params=params,inner_rmse=float(np.mean(scores[e])),eta=e) for e in lm.ETA]
            best=min(tune,key=lambda z:(z['inner_rmse'],z['eta'],-z['params']['model__alpha']))
            train=enrich(a,full['crossfit']);valid=enrich(b,full['base'])
            fitted=lm.k.strict_fit(model(spec).set_params(**best['params']),train,full['residual'])
            eta=best['eta'];prediction=full['base']+eta*fitted.predict(valid)
        correction=prediction-full['base']
        rows=[]
        for pid,yt,yp,yb,c in zip(b[ID],b[TARGET],prediction,full['base'],correction):
            rows.append({**key,ID:pid,'y_true':float(yt),'y_pred':float(yp),'y_base':float(yb),'correction':float(c),'eta':eta,'outer_model_id':f'{name}_{protocol}_{repeat}_{fold}'})
        co=lm.coefficient_rows(fitted,key,train)
        registry={**key,'params':json.dumps(best['params']),'eta':eta,'inner_rmse':best['inner_rmse'],'interaction_enabled':fitted['repr'].interaction_enabled_,'n_train':len(a),'train_ids':json.dumps(a[ID].tolist()),'validation_ids':json.dumps(b[ID].tolist())}
        joblib.dump(dict(model=fitted,base_model=full['model'],eta=eta,spec=spec),OUT/'models'/dest.name,compress=3)
        joblib.dump(dict(predictions=rows,registry=registry,tuning=[{**key,**x,'params':json.dumps(x['params'])} for x in tune],coefficients=co),dest,compress=3)
    print('F4 FOLD',index+1,protocol,repeat,fold,flush=True)

def run(workers=3):
    splits=setup()
    joblib.Parallel(n_jobs=workers,backend='loky',inner_max_num_threads=1)(joblib.delayed(fit_fold)(i) for i in range(len(splits)))
    packs=[joblib.load(OUT/'checkpoints'/f'{name}_{p}_{r}_{f}.joblib') for p,r,f,*_ in splits for name in SPECS]
    for field,file in [('predictions','oof_predictions.parquet'),('registry','registry.csv'),('tuning','inner_tuning.csv'),('coefficients','coefficients.csv')]:
        z=pd.DataFrame([row for pack in packs for row in (pack[field] if isinstance(pack[field],list) else [pack[field]])])
        if file.endswith('parquet'):z.to_parquet(OUT/'tables'/file,index=False)
        else:z.to_csv(OUT/'tables'/file,index=False)
    analyze()

def analyze():
    d,t=load();p=pd.read_parquet(OUT/'tables/oof_predictions.parquet')
    assert len(p)==len(SPECS)*1794
    j=pd.read_parquet(lm.k.j.locations()[0]/'tables/02_oof_predictions.parquet');j=j[j.experiment.eq('J0_RAIN')]
    k=pd.read_parquet(lm.k.locations()[0]/'tables/11_k_oof_predictions.parquet');k=k[k.experiment.eq('K5_RAIN_RESID_SLOPE')]
    h=pd.read_parquet(lm.k.j.H/'tables/31_oof_individual.parquet');h=h[h.experiment.eq('H8_CLIMATE_CURRENT_ORIGINAL')]
    refs=pd.concat([j,k,h],ignore_index=True)
    refs['outer_model_id']=refs.experiment+'_'+refs.protocol+'_'+refs['repeat'].astype(str)+'_'+refs.fold.astype(str)
    allp=pd.concat([p,refs],ignore_index=True)
    q=pd.read_csv(ROOT/'outputs/research/family_1/soil_yield_quartile_analysis/v1/parcel_quartiles.csv')[[ID,'quartile']]
    allp=allp.merge(d[[ID,'climate_profile','Estado','Municipio','altitude_m','longitude','latitude',NDVI,Q10,SAVI,DTR]],on=ID,validate='many_to_one').merge(q,on=ID,validate='many_to_one')
    allp['error']=allp.y_pred-allp.y_true
    rows=[];pairs=[];profilemetrics=[]
    for (e,pr,r),g in allp.groupby(['experiment','protocol','repeat']):
        masks={'all':np.ones(len(g),bool),'Chignahuapan':g.Municipio.eq('Chignahuapan'),'without_Chignahuapan':~g.Municipio.eq('Chignahuapan')}
        masks.update({x:g.quartile.eq(x) for x in ['Q1','Q2','Q3','Q4']})
        masks.update({'state:'+str(x):g.Estado.eq(x) for x in g.Estado.unique()})
        for label,mask in masks.items():
            z=g[mask]
            if len(z):rows.append(dict(experiment=e,protocol=pr,repeat=r,stratum=label,n=len(z),**lm.k.metrics(z.y_true,z.y_pred)))
        for (prof,fold),z in g.groupby(['climate_profile','fold']):
            if len(z)<2:continue
            a,b=np.triu_indices(len(z),1)
            err=(z.y_pred.to_numpy()[a]-z.y_pred.to_numpy()[b])-(z.y_true.to_numpy()[a]-z.y_true.to_numpy()[b])
            for i,jj,v in zip(a,b,err):pairs.append(dict(experiment=e,protocol=pr,repeat=r,fold=fold,profile=prof,id_a=z[ID].iloc[i],id_b=z[ID].iloc[jj],pair_error=v,Chignahuapan=bool(z.Municipio.iloc[i]=='Chignahuapan' or z.Municipio.iloc[jj]=='Chignahuapan')))
            profilemetrics.append(dict(experiment=e,protocol=pr,repeat=r,fold=fold,profile=prof,n=len(z),prediction_sd=z.y_pred.std(),correction_sd=z.correction.std() if 'correction' in z else np.nan,pair_mse=np.mean(err**2),pair_mae=np.mean(abs(err))))
    metrics=pd.DataFrame(rows);metrics.to_csv(OUT/'tables/subgroups_repeat.csv',index=False)
    summary=metrics.groupby(['experiment','protocol','stratum'])[['n','RMSE','MAE','R2','bias_pred_minus_y']].mean().reset_index();summary.to_csv(OUT/'tables/summary.csv',index=False)
    pp=pd.DataFrame(pairs);pp.to_parquet(OUT/'tables/same_model_pair_errors.parquet',index=False)
    pm=pd.DataFrame(profilemetrics);pm.to_csv(OUT/'tables/profile_metrics.csv',index=False)
    # Equal profile weight after aggregating same-model pair errors within each profile.
    paired=[]
    for scope in ['all','without_Chignahuapan']:
        zz=pp if scope=='all' else pp[~pp.Chignahuapan]
        for (e,pr,r),z in zz.groupby(['experiment','protocol','repeat']):
            prof=z.groupby('profile').pair_error.agg(mse=lambda v:np.mean(v*v),mae=lambda v:abs(v).mean())
            paired.append(dict(experiment=e,protocol=pr,repeat=r,scope=scope,n_pairs=len(z),n_profiles=len(prof),n_parcels=len(set(z.id_a)|set(z.id_b)),pair_RMSE=np.sqrt(np.mean(z.pair_error**2)),pair_MAE=abs(z.pair_error).mean(),equal_profile_RMSE=np.sqrt(prof.mse.mean()),equal_profile_MAE=prof.mae.mean()))
    pd.DataFrame(paired).to_csv(OUT/'tables/pair_repeat_metrics.csv',index=False)
    pd.DataFrame(paired).groupby(['experiment','protocol','scope']).mean(numeric_only=True).reset_index().to_csv(OUT/'tables/pair_summary.csv',index=False)
    allp.to_parquet(OUT/'tables/errors_with_geography.parquet',index=False)
    report(summary,p,allp,d,t)

def report(summary,p,allp,d,t):
    global_table=summary[summary.stratum.eq('all')]
    global_table.pivot(index='experiment',columns='protocol',values='RMSE').to_csv(OUT/'tables/global_rmse.csv')
    co=pd.read_csv(OUT/'tables/coefficients.csv')
    co.groupby(['experiment','protocol','feature']).agg(n_fits=('coefficient','size'),mean_coef=('coefficient','mean'),positive_fraction=('coefficient',lambda x:(x>1e-10).mean()),negative_fraction=('coefficient',lambda x:(x< -1e-10).mean()),nonzero_frequency=('nonzero','mean')).reset_index().to_csv(OUT/'tables/coefficient_stability.csv',index=False)
    p.groupby(['experiment','protocol']).agg(mean_abs_correction=('correction',lambda x:abs(x).mean()),max_abs_correction=('correction',lambda x:abs(x).max()),min_prediction=('y_pred','min'),max_prediction=('y_pred','max'),n_negative=('y_pred',lambda x:(x<0).sum())).reset_index().to_csv(OUT/'tables/correction_extremes.csv',index=False)
    td=t[[NDVI,Q10,SAVI]+RAIN+[DTR,'altitude_m','longitude','latitude']]
    td.corr().to_csv(OUT/'tables/candidate_correlations.csv')
    t.groupby(['Estado','Municipio'])[DTR].agg(['size','mean','std','min','max']).to_csv(OUT/'tables/dtr_geography.csv')
    # Spatial/temporal availability is descriptive, not a predictor.
    quality=pd.read_parquet(ROOT/'data/processed/family_1/m_historical_multisensor/v1/m_quality_by_parcel.parquet').set_index(ID)
    qq=allp[allp.experiment.isin(SPECS)].copy()
    qq['S2_valid_months']=qq[ID].map(quality.S2_current_valid_months)
    qq['support']=np.where(qq.S2_valid_months.eq(7),'7 valid months','<7 valid months')
    support=[]
    for (e,pr,r,s),z in qq.groupby(['experiment','protocol','repeat','support']):support.append(dict(experiment=e,protocol=pr,repeat=r,support=s,n=len(z),**lm.k.metrics(z.y_true,z.y_pred)))
    pd.DataFrame(support).to_csv(OUT/'tables/temporal_support_repeat.csv',index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    ax=global_table.pivot(index='experiment',columns='protocol',values='RMSE').plot.barh(figsize=(12,9));ax.set_xlabel('RMSE (t/ha)');ax.figure.tight_layout();ax.figure.savefig(OUT/'figures/protocol_rmse.png',dpi=160);plt.close(ax.figure)
    pairs=pd.read_csv(OUT/'tables/pair_summary.csv')
    ax=pairs[pairs.scope.eq('all')].pivot(index='experiment',columns='protocol',values='equal_profile_RMSE').plot.barh(figsize=(12,9));ax.set_xlabel('RMSE de diferencias, igual peso por perfil');ax.figure.tight_layout();ax.figure.savefig(OUT/'figures/intraprofile.png',dpi=160);plt.close(ax.figure)
    manifest=dict(status='models_and_diagnostics_complete',n_experiments=len(SPECS),n_outer=65,n_models=len(SPECS)*65,n_oof=len(p),exploratory=True,s7='suspended',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(global_table.pivot(index='experiment',columns='protocol',values='RMSE').round(5).to_string())
