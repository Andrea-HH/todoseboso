"""L/M shared nested EN/PCA engine. Historical files and Champion are read-only."""
from pathlib import Path
import json,hashlib,uuid,itertools,importlib.metadata
import numpy as np
import pandas as pd
import joblib
from sklearn.base import BaseEstimator,TransformerMixin
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import GridSearchCV,ParameterGrid
from . import k_geographic_edaphological as k
from .climate_signal_features import climate_current
from .climate_signal_modeling import estimator as climate_estimator

ROOT,ID,TARGET,RAIN,TOPO=k.ROOT,k.ID,k.TARGET,k.RAIN,k.TOPO
NAMES={'L':'l_multiblock_representation','M':'m_historical_multisensor'}
GRID={'model__alpha':k.ALPHA,'model__l1_ratio':k.L1}
PC=[1,2,4];ETA=k.ETA

def locations(section,version='v1'):
    return ROOT/'outputs/modeling/family_1'/NAMES[section]/version,ROOT/'data/processed/family_1'/NAMES[section]/version

def dump(value,path):
    assert path.resolve().is_relative_to(ROOT.resolve()) and any(s in str(path) for s in NAMES.values())
    if path.exists():return
    temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp');joblib.dump(value,temp,compress=3)
    try:temp.replace(path)
    except PermissionError:
        if not path.exists():raise
        joblib.load(path);temp.unlink()

def load_l():
    d,t,old,_,groups,units=k.load();clim,cols=climate_current()
    d=d.merge(clim,on=ID,validate='one_to_one')
    t=k.j.supervised_data(d,pd.read_csv(k.j.MASTER))
    assert len(t)==138 and len(d)==197 and TARGET not in d and d.climate_profile.nunique()==53
    return d,t,cols,groups,units

class BlockRepresentation(BaseEstimator,TransformerMixin):
    """Train-only imputation, bounded soil, guarded spectral scaling, optional PCA.

    Base climates retain their original imputer/StandardScaler specification.
    S2 support=5 is fixed before prediction; Other includes all rare/unseen mass.
    PCs are never whitened or standardized after fitting (no tiny eigenvalue blowup).
    """
    def __init__(self,base_columns=(),blocks=(),mode='raw',n_components=2,hellinger=False,pool=False):
        self.base_columns=base_columns;self.blocks=blocks;self.mode=mode
        self.n_components=n_components;self.hellinger=hellinger;self.pool=pool
    def fit(self,X,y=None):
        self.base_=None
        if self.base_columns:
            self.base_=Pipeline([('impute',SimpleImputer(strategy='median',keep_empty_features=True)),('scale',StandardScaler())]).fit(X[list(self.base_columns)])
        self.preps_=[];self.pcas_=[];self.names_=[]
        self.block_weights_=[]
        for label,cols in self.blocks:
            cols=list(cols)
            soil=all(c.startswith('soil') for c in cols)
            if self.pool and any(c.startswith('soil_unit_share__') for c in cols):
                prep=k.StableFeatures(5).fit(X[cols]);a=prep._raw(X[cols]).to_numpy(float)
                # Natural composition first; no imputation of unknown physical mass.
                if not np.isfinite(a).all() or (a<0).any():raise ValueError('Incomplete soil composition')
                names=list(prep._raw(X[cols]).columns)
                info=dict(kind='pooled',cols=cols,prep=prep,names=names)
            else:
                a=X[cols].to_numpy(float)
                median=np.array([np.nanmedian(z) if np.isfinite(z).any() else 0 for z in a.T])
                a=np.where(np.isfinite(a),a,median)
                center=np.zeros(len(cols)) if soil else a.mean(axis=0)
                scale=np.ones(len(cols)) if soil else np.maximum(a.std(axis=0),.05)
                # CEM4 uses ordinary z scaling; spectral floor is a fixed .05 index unit.
                for i,c in enumerate(cols):
                    if c.startswith('soil'):center[i]=0;scale[i]=1
                    if c in TOPO:scale[i]=a[:,i].std() if a[:,i].std()>1e-10 else 1
                a=(a-center)/scale;names=cols
                info=dict(kind='ordinary',cols=cols,median=median,center=center,scale=scale,names=names)
            if soil and self.hellinger:a=np.sqrt(a)
            support=a.var(axis=0)>1e-20
            if not support.any():support[0]=True
            info['support']=support;info['soil']=soil
            a=a[:,support];names=list(np.array(names)[support])
            pca=None
            if self.mode in ['pca','block_pca']:
                count=min(int(self.n_components),a.shape[1],max(1,len(a)-1))
                pca=PCA(n_components=count,svd_solver='full').fit(a)
                names=[label+f'_PC{i+1}' for i in range(count)]
            self.preps_.append(info);self.pcas_.append(pca);self.names_.extend(names)
            self.block_weights_.append(1/ max(np.sqrt(np.sum(pca.explained_variance_)),1.) if self.mode=='block_pca' and pca is not None else 1.)
        if self.mode in ['joint_pca','block_pca']:
            a=self._transform_parts(X)
            count=min(int(self.n_components),a.shape[1],max(1,len(a)-1))
            self.joint_=PCA(n_components=count,svd_solver='full').fit(a)
            self.output_names_=[f'joint_PC{i+1}' for i in range(count)]
        else:self.joint_=None;self.output_names_=list(self.base_columns)+self.names_
        self.effective_k_=len(self.output_names_) if self.mode in ['joint_pca','block_pca'] else [p.n_components_ for p in self.pcas_ if p is not None]
        return self
    def _transform_parts(self,X):
        pieces=[]
        if self.base_ is not None:pieces.append(self.base_.transform(X[list(self.base_columns)]))
        for info,pca,weight in zip(self.preps_,self.pcas_,getattr(self,'block_weights_',[1.]*len(self.preps_))):
            if info['kind']=='pooled':a=info['prep']._raw(X[info['cols']]).to_numpy(float)
            else:
                a=X[info['cols']].to_numpy(float);a=np.where(np.isfinite(a),a,info['median'])
                a=(a-info['center'])/info['scale']
            if info['soil'] and self.hellinger:a=np.sqrt(a)
            a=a[:,info['support']]
            if not np.isfinite(a).all():raise ValueError('Nonfinite predictive transform')
            pieces.append((pca.transform(a) if pca is not None else a)*weight)
        return np.concatenate(pieces,axis=1)
    def transform(self,X):
        a=self._transform_parts(X)
        return self.joint_.transform(a) if self.joint_ is not None else a
    def get_feature_names_out(self,input_features=None):return np.array(self.output_names_)

def model(spec,climate_cols=()):
    return Pipeline([('repr',BlockRepresentation(base_columns=tuple(climate_cols),blocks=tuple((name,tuple(cols)) for name,cols in spec['blocks']),mode=spec.get('mode','raw'),hellinger=spec.get('hellinger',False),pool=spec.get('pool',False))),('model',ElasticNet(max_iter=200000,random_state=2026))])

def grid(spec):
    result=dict(GRID)
    if spec.get('mode','raw')!='raw':result['repr__n_components']=PC
    return result

class BaseContexts:
    def __init__(self,out,groups,columns):self.out=out;self.groups=groups;self.columns=columns;self.logs=[]
    def tune(self,frame,base,protocol,cv):
        cols=RAIN if base=='rain' else self.columns
        signature=[base,protocol,frame[ID].tolist(),[[a.tolist(),b.tolist()] for a,b in cv]]
        key=hashlib.sha256(json.dumps(signature).encode()).hexdigest();path=self.out/'base_cache'/f'tune_{key}.joblib'
        if path.exists():return joblib.load(path)
        pipe,params=climate_estimator('enet')
        search=k.strict_fit(GridSearchCV(pipe,params,cv=cv,scoring='neg_root_mean_squared_error',n_jobs=1,error_score='raise'),frame[cols],frame[TARGET])
        pack=dict(model=search.best_estimator_,params=search.best_params_,train_ids=frame[ID].tolist(),columns=cols)
        dump(pack,path);return pack
    def context(self,frame,validation,base,protocol,cv,label):
        pred=np.full(len(frame),np.nan);cols=RAIN if base=='rain' else self.columns
        for index,(tr,va) in enumerate(cv):
            a,b=frame.iloc[tr],frame.iloc[va];sub=k.subcv(a,protocol,self.groups)
            fitted=self.tune(a,base,protocol,sub)
            assert not set(fitted['train_ids'])&set(b[ID])
            pred[va]=fitted['model'].predict(b[cols])
            self.logs.append(dict(context=label,base=base,protocol=protocol,subfold=index,fit_ids=json.dumps(a[ID].tolist()),heldout_ids=json.dumps(b[ID].tolist()),tuning_folds=json.dumps([[a.iloc[x][ID].tolist(),a.iloc[y][ID].tolist()] for x,y in sub])))
        if not np.isfinite(pred).all():raise ValueError('Incomplete base cross-fitting')
        fit=self.tune(frame,base,protocol,cv)
        return dict(model=fit['model'],params=fit['params'],columns=cols,base=fit['model'].predict(validation[cols]),crossfit=pred,residual=frame[TARGET].to_numpy()-pred)

def contexts(section,version,index,base,t,climate_cols,splits,assignments):
    out,_=locations(section,version);protocol,rep,fold,tr,va,inner=splits[index]
    label=f'{base}_{protocol}_{rep}_{fold}';path=out/'base_cache'/f'contexts_{label}.joblib'
    if path.exists():return joblib.load(path)
    prior=locations('L',version)[0]/'base_cache'/f'contexts_{label}.joblib'
    if section=='M' and prior.exists():
        pack=joblib.load(prior);dump(pack,path);return pack
    # Rain cross-fitting was already correctly generated in K; reuse read-only.
    old=k.locations()[0]/'climate_cache'/f'contexts_{protocol}_{rep}_{fold}.joblib'
    if base=='rain' and old.exists():
        full,internal,logs=joblib.load(old)
        full={**full,'columns':RAIN}
        internal=[{**x,'columns':RAIN} for x in internal]
        logs=[{**x,'base':base,'subfold':x['fold'],'tuning_folds':x['inner_folds'],'source':'immutable K cross-fitting'} for x in logs]
    else:
        factory=BaseContexts(out,assignments,climate_cols);a,b=t.iloc[tr],t.iloc[va]
        full=factory.context(a,b,base,protocol,inner,label+'_outer');internal=[]
        for j,(itr,iva) in enumerate(inner):
            aa,bb=a.iloc[itr],a.iloc[iva]
            internal.append(factory.context(aa,bb,base,protocol,k.subcv(aa,protocol,assignments),label+f'_inner{j}'))
        logs=factory.logs
    pack=(full,internal,logs);dump(pack,path);return pack

def l_specs(climate_cols,soil,units):
    specs={}
    for base,num in [('rain',0),('current',1)]:
        specs[f'L{num}_BASE']=dict(kind='base',base=base,blocks=[])
        for block,cols,number in [('soil',soil,2+num),('topo_soil',TOPO+soil,4+num)]:
            # One joint complementary PCA; raw topo z + bounded soil, same in controls.
            blocks=[(block,cols)]
            for kind,mode in [('residual','pca'),('residual','raw'),('direct','pca'),('direct','raw')]:
                name=f'L{number}' if kind=='residual' and mode=='pca' else f'LC_{base}_{block}_{kind}_{mode}'
                specs[name]=dict(kind=kind,base=base,blocks=blocks,mode=mode)
        for mode,hell,name in [('raw',True,f'L{6+num}_HELL_DIRECT'),('joint_pca',True,f'L{6+num}_HELL_JOINT_PCA'),('raw',False,f'LC_{base}_S2_RAW_DIRECT')]:
            specs[name]=dict(kind='direct',base=base,blocks=[('composition',units)],mode=mode,hellinger=hell,pool=True)
    return specs

def setup(section,version,specs,d):
    out,proc=locations(section,version)
    if (out/'manifest.json').exists():raise FileExistsError('Completed version immutable')
    for path in [out,proc]+[out/x for x in ['tables','figures','models','checkpoints','base_cache','report','splits']]:path.mkdir(parents=True,exist_ok=True)
    config=dict(section=section,specs=specs,alpha=k.ALPHA,l1=k.L1,components=PC,eta=ETA,seed=2026,n_train=138,n_prediction=59,n_profiles_all=53,cutoff='2025-10-31',primary_soil='S1 natural group mention fractions',secondary_soil='S2 support>=5 pooled Other; natural or sqrt proportions, no CLR',soil_scaling='natural [0,1]; PCA centered, not whitened',spectral_scaling='training median and z with fixed minimum SD .05 index units',base_scaling='original median and StandardScaler',base_grid=dict(alpha=k.j.ALPHAS,l1=k.j.L1),nested='frozen inner folds evaluate whole residual pipeline with deeper cross-fitted/tuned bases',aggregation='complete 138 OOF repetition metrics then mean; no averaged-prediction scores',decision=dict(rmse_geographic_margin=.01,mae_all_protocol_margin=.01,repeat_consistency=.8),hidden_y_used=False)
    path=out/'configuration.json'
    config=json.loads(json.dumps(config))
    if path.exists() and json.loads(path.read_text())!=config:raise ValueError('Frozen configuration changed')
    path.write_text(json.dumps(config,indent=2),encoding='utf-8')
    d.to_parquet(proc/f'{section.lower()}_features_197_target_free.parquet',index=False)
    return out,proc

def fit_fold(section,version,index):
    out,proc=locations(section,version);config=json.loads((out/'configuration.json').read_text());specs=config['specs']
    d=pd.read_parquet(proc/f'{section.lower()}_features_197_target_free.parquet')
    t=k.j.supervised_data(d,pd.read_csv(k.j.MASTER));climate_cols=climate_current()[1]
    splits,table,assignments=k.j.load_frozen_splits(t);protocol,rep,fold,tr,va,inner=splits[index]
    a,b=t.iloc[tr],t.iloc[va];fold_id=f'{protocol}_{rep}_{fold}'
    ctx={}
    for name,spec in specs.items():
        path=out/'checkpoints'/f'{name}_{fold_id}.joblib'
        if path.exists():continue
        base=spec.get('base');key=dict(experiment=name,protocol=protocol,repeat=rep,fold=fold)
        basecols=RAIN if base=='rain' else climate_cols if base=='current' else []
        predictors=list(dict.fromkeys(basecols+[c for label,cols in spec['blocks'] for c in cols]))
        if spec['kind'] in ['base','residual']:
            if base not in ctx:ctx[base]=contexts(section,version,index,base,t,climate_cols,splits,assignments)
            full,internal,logs=ctx[base]
        if spec['kind']=='base':
            prediction=full['base'];fitted=full['model'];registry={**key,'params':json.dumps(full['params']),'eta':0,'n_effective':len(basecols)};tuning=[];co=[]
            reference=pd.read_parquet(k.j.H/'tables/31_oof_individual.parquet') if base=='current' else pd.read_parquet(k.j.locations()[0]/'tables/02_oof_predictions.parquet')
            oldname='H8_CLIMATE_CURRENT_ORIGINAL' if base=='current' else 'J0_RAIN'
            ref=reference[(reference.experiment==oldname)&(reference.protocol==protocol)&(reference['repeat']==rep)&(reference.fold==fold)].set_index(ID).loc[b[ID]]
            if not np.allclose(prediction,ref.y_pred,rtol=0,atol=1e-8):raise ValueError(f'{name} baseline reproduction failure')
            baseprediction=prediction;proposed=np.zeros(len(b));delta=proposed;eta=0
        elif spec['kind'] in ['direct','standalone']:
            search=k.strict_fit(GridSearchCV(model(spec,basecols),grid(spec),cv=inner,scoring='neg_root_mean_squared_error',n_jobs=1,error_score='raise'),a[predictors],a[TARGET])
            fitted=search.best_estimator_;prediction=fitted.predict(b[predictors]);eta=np.nan
            registry={**key,'params':json.dumps(search.best_params_),'inner_rmse':-search.best_score_,'n_effective':len(fitted['repr'].get_feature_names_out()),'effective_k':json.dumps(fitted['repr'].effective_k_)}
            tuning=[{**key,'params':json.dumps(p),'inner_rmse':float(-score)} for p,score in zip(search.cv_results_['params'],search.cv_results_['mean_test_score'])]
            baseprediction=np.full(len(b),np.nan);proposed=baseprediction;delta=baseprediction
            co=coefficient_rows(fitted,key,a)
        else:
            candidates=[]
            for params in ParameterGrid(grid(spec)):
                scores={e:[] for e in ETA}
                for (itr,iva),inside in zip(inner,internal):
                    fitted=k.strict_fit(model(spec).set_params(**params),a.iloc[itr][predictors],inside['residual']);r=fitted.predict(a.iloc[iva][predictors])
                    for e in ETA:scores[e].append(float(np.sqrt(np.mean((a.iloc[iva][TARGET].to_numpy()-inside['base']-e*r)**2))))
                for e in ETA:candidates.append({**key,'params':json.dumps(params),'eta':e,'inner_rmse':float(np.mean(scores[e]))})
            best=min(candidates,key=lambda x:(x['inner_rmse'],x['eta'],json.loads(x['params']).get('repr__n_components',0),-json.loads(x['params'])['model__alpha']))
            fitted=k.strict_fit(model(spec).set_params(**json.loads(best['params'])),a[predictors],full['residual'])
            eta=best['eta'];proposed=fitted.predict(b[predictors]);delta=eta*proposed;baseprediction=full['base'];prediction=baseprediction+delta
            registry={**key,'params':best['params'],'eta':eta,'inner_rmse':best['inner_rmse'],'n_effective':len(fitted['repr'].get_feature_names_out()),'effective_k':json.dumps(fitted['repr'].effective_k_)}
            co=coefficient_rows(fitted,key,a);tuning=candidates
            fitted=dict(base_model=full['model'],base_columns=basecols,corrector=fitted,eta=eta)
        rows=[{**key,ID:pid,'y_true':float(y),'y_pred':float(p),'y_base':float(bp),'proposed_correction':float(pc),'correction':float(dc),'eta':eta,'outer_model_id':name+'_'+fold_id} for pid,y,p,bp,pc,dc in zip(b[ID],b[TARGET],prediction,baseprediction,proposed,delta)]
        dump(fitted,out/'models'/f'{name}_{fold_id}.joblib')
        dump(dict(predictions=rows,registry=registry,tuning=tuning,coefficients=co),path)
    print(section,'FOLD',index+1,'/65',fold_id,flush=True)

def coefficient_rows(fitted,key,train):
    r=fitted['repr'];z=r.transform(train);beta=fitted['model'].coef_
    return [{**key,'feature':c,'coefficient':float(b),'beta_times_training_sd':float(b*np.std(z[:,i])),'nonzero':bool(abs(b)>1e-10)} for i,(c,b) in enumerate(zip(r.get_feature_names_out(),beta))]

def run_models(section,version='v1',workers=3):
    out,proc=locations(section,version);d=pd.read_parquet(proc/f'{section.lower()}_features_197_target_free.parquet');t=k.j.supervised_data(d,pd.read_csv(k.j.MASTER))
    splits,table,assignments=k.j.load_frozen_splits(t);table.to_csv(out/'splits/outer_and_inner_splits.csv',index=False);assignments.to_csv(out/'splits/group_memberships.csv')
    joblib.Parallel(n_jobs=workers,backend='loky',inner_max_num_threads=1)(joblib.delayed(fit_fold)(section,version,i) for i in range(65))
    config=json.loads((out/'configuration.json').read_text());packs=[]
    for protocol,rep,fold,tr,va,inner in splits:
        for name in config['specs']:packs.append(joblib.load(out/'checkpoints'/f'{name}_{protocol}_{rep}_{fold}.joblib'))
    p=pd.DataFrame(sum([x['predictions'] for x in packs],[]));p.to_parquet(out/'tables/10_oof_predictions.parquet',index=False)
    pd.DataFrame([x['registry'] for x in packs]).to_csv(out/'tables/11_registry.csv',index=False)
    pd.DataFrame(sum([x['tuning'] for x in packs],[])).to_csv(out/'tables/12_inner_tuning.csv',index=False)
    pd.DataFrame(sum([x['coefficients'] for x in packs],[])).to_csv(out/'tables/13_coefficients.csv',index=False)
    provenance=[];residuals=[]
    for protocol,rep,fold,tr,va,inner in splits:
        for base in ['rain','current']:
            path=out/'base_cache'/f'contexts_{base}_{protocol}_{rep}_{fold}.joblib'
            if not path.exists():continue
            full,internal,logs=joblib.load(path);provenance.extend(logs)
            for pid,y,cf in zip(t.iloc[tr][ID],t.iloc[tr][TARGET],full['crossfit']):residuals.append(dict(protocol=protocol,repeat=rep,fold=fold,base=base,ID_POLIGONO=pid,y_true=y,y_crossfit=cf,residual=y-cf))
    pd.DataFrame(provenance).to_csv(out/'tables/14_crossfit_provenance.csv',index=False)
    pd.DataFrame(residuals).to_parquet(out/'tables/15_outer_train_crossfit_residuals.parquet',index=False)
    diagnostics(section,version,d,p)
    return p

def diagnostics(section,version,d,p):
    out,proc=locations(section,version)
    comparison,folds,reps=k.summarize(p,out)
    baseline_names={'rain':'L0_BASE','current':'L1_BASE'} if section=='L' else {'rain':'MB_RAIN','current':'MB_CURRENT'}
    specs=json.loads((out/'configuration.json').read_text())['specs'];paired=[];subgroups=[];same=[];pairs=[];corrections=[]
    q=p.merge(d[[ID,'climate_profile','Municipio','Estado','altitude_m','slope_degrees','soil_assignment_reserve','soil_boundary_buffer_50m_share','soil_boundary_buffer_125m_share','soil_boundary_buffer_250m_share','soil_share_key_not_found_in_E1402_text']],on=ID,validate='many_to_one')
    q['error']=q.y_pred-q.y_true;q['abs_error']=abs(q.error)
    for name,spec in specs.items():
        targets=[baseline_names[spec['base']]] if spec.get('base') else []
        if section=='M' and name.startswith('M') and spec['kind']=='standalone':targets=['M0_RAW']
        if spec['kind']=='residual':
            matching=[n for n,s in specs.items() if s['kind']=='direct' and s.get('base')==spec['base'] and s['blocks']==spec['blocks'] and s.get('mode','raw')==spec.get('mode','raw') and s.get('hellinger',False)==spec.get('hellinger',False)]
            targets+=matching
        for base in set(targets)-{name}:
            for scope,table,keys in [('repeat',reps,['protocol','repeat']),('fold',folds,['protocol','repeat','fold'])]:
                z=table[table.experiment.eq(base)].merge(table[table.experiment.eq(name)],on=keys,suffixes=('_base','_candidate'),validate='one_to_one')
                for row in z.to_dict('records'):paired.append(dict(scope=scope,baseline=base,candidate=name,**{x:row[x] for x in keys},delta_RMSE=row['RMSE_base']-row['RMSE_candidate'],delta_MAE=row['MAE_base']-row['MAE_candidate']))
    pd.DataFrame(paired).to_csv(out/'tables/20_paired_comparisons.csv',index=False)
    pd.DataFrame(paired).groupby(['scope','protocol','baseline','candidate']).agg(delta_RMSE=('delta_RMSE','mean'),delta_MAE=('delta_MAE','mean'),fraction_improving=('delta_RMSE',lambda x:(x>1e-10).mean())).reset_index().to_csv(out/'tables/21_paired_summary.csv',index=False)
    for (protocol,name,rep),z in q.groupby(['protocol','experiment','repeat']):
        spec=specs[name];bn=baseline_names.get(spec.get('base'),'M0_RAW');base=q[(q.protocol==protocol)&(q.experiment==bn)&(q['repeat']==rep)].set_index(ID)
        z=z.copy();z['baseline_error']=z[ID].map(base.error);z['absolute_error_improvement']=z[ID].map(base.abs_error)-z.abs_error
        masks={'all':np.ones(len(z),bool),'Chignahuapan':z.Municipio.eq('Chignahuapan'),'other_municipalities':~z.Municipio.eq('Chignahuapan'),'low_lt3':z.y_true<3,'high_gt5':z.y_true>5,'source_key_discrepancy':z.soil_share_key_not_found_in_E1402_text>0}
        for radius in [50,125,250]:masks[f'near_{radius}m']=z[f'soil_boundary_buffer_{radius}m_share']>0;masks[f'away_{radius}m']=~masks[f'near_{radius}m']
        for field in ['Estado','Municipio']:
            for value in z[field].unique():masks[field+'_'+str(value)]=z[field].eq(value)
        if section=='M':
            quality=pd.read_parquet(proc/'m_quality_by_parcel.parquet').set_index(ID)
            for sensor in ['S2','PLANET','LANDSAT']:
                vals=z[ID].map(quality[sensor+'_current_valid_months'])
                masks[sensor+'_months_lt7']=vals<7;masks[sensor+'_months7']=vals==7
        for label,mask in masks.items():
            zz=z[mask]
            if len(zz):subgroups.append(dict(protocol=protocol,experiment=name,repeat=rep,stratum=label,n=len(zz),absolute_error_improvement=zz.absolute_error_improvement.mean(),**k.metrics(zz.y_true,zz.y_pred)))
        if spec['kind']=='residual':
            residual=z.y_true-z.y_base
            corrections.append(dict(protocol=protocol,experiment=name,repeat=rep,n=len(z),mean_abs_correction=z.correction.abs().mean(),max_abs_correction=z.correction.abs().max(),max_abs_proposed=z.proposed_correction.abs().max(),correlation_residual_correction=residual.corr(z.correction) if z.correction.std()>1e-12 else np.nan,correlation_residual_proposed=residual.corr(z.proposed_correction) if z.proposed_correction.std()>1e-12 else np.nan,bias_improvement=abs(residual.mean())-abs(z.error.mean()),n_negative=int((z.y_pred<0).sum())))
        for (profile,outer),zz in z.groupby(['climate_profile','outer_model_id']):
            if len(zz)<2:continue
            same.append(dict(protocol=protocol,experiment=name,repeat=rep,profile=profile,outer_model_id=outer,n=len(zz),y_sd=zz.y_true.std(),prediction_sd=zz.y_pred.std(),base_sd=zz.y_base.std(),correction_sd=zz.correction.std(),absolute_error_improvement=zz.absolute_error_improvement.mean(),**k.metrics(zz.y_true,zz.y_pred)))
            y=zz.y_true.to_numpy();pred=zz.y_pred.to_numpy();a,b=np.triu_indices(len(zz),1)
            errors=(pred[a]-pred[b])-(y[a]-y[b])
            for e in errors:pairs.append(dict(protocol=protocol,experiment=name,repeat=rep,profile=profile,pair_error=float(e)))
    q.to_parquet(out/'tables/22_errors_with_geography.parquet',index=False)
    pd.DataFrame(subgroups).to_csv(out/'tables/23_subgroups_repeat.csv',index=False)
    pd.DataFrame(subgroups).groupby(['protocol','experiment','stratum']).agg(n=('n','first'),RMSE=('RMSE','mean'),MAE=('MAE','mean'),bias=('bias_pred_minus_y','mean'),absolute_error_improvement=('absolute_error_improvement','mean')).reset_index().to_csv(out/'tables/24_subgroup_summary.csv',index=False)
    pd.DataFrame(same).to_csv(out/'tables/25_same_model_intraprofile.csv',index=False)
    pp=pd.DataFrame(pairs);pp.to_parquet(out/'tables/26_same_model_pair_errors.parquet',index=False)
    pp.groupby(['protocol','experiment','repeat']).pair_error.agg(pair_RMSE=lambda x:float(np.sqrt(np.mean(x*x))),pair_MAE=lambda x:float(abs(x).mean()),n_pairs='size').reset_index().to_csv(out/'tables/27_pair_metrics.csv',index=False)
    pd.DataFrame(corrections).to_csv(out/'tables/28_residual_corrections_oof.csv',index=False)
    q.groupby(['protocol','experiment']).agg(n_negative=('y_pred',lambda x:(x<0).sum()),min_prediction=('y_pred','min'),max_prediction=('y_pred','max'),max_abs_error=('error',lambda x:abs(x).max())).reset_index().to_csv(out/'tables/29_prediction_extremes.csv',index=False)
    co=pd.read_csv(out/'tables/13_coefficients.csv')
    selection=co.groupby(['protocol','experiment','feature']).agg(n_present_fits=('fold','size'),nonzero_frequency_when_present=('nonzero','mean'),mean_beta=('coefficient','mean'),mean_beta_sd=('beta_times_training_sd','mean'),sd_beta_sd=('beta_times_training_sd','std'),positive_fraction=('coefficient',lambda x:(x>1e-10).mean()),negative_fraction=('coefficient',lambda x:(x<-1e-10).mean())).reset_index()
    count=folds.groupby(['protocol','experiment']).size().rename('n_outer_fits').reset_index();selection=selection.merge(count,on=['protocol','experiment'])
    selection['nonzero_frequency_all_fits']=selection.nonzero_frequency_when_present*selection.n_present_fits/selection.n_outer_fits
    selection['sign_interpretation']=np.where(selection.feature.str.contains('PC'), 'local PCA axis; sign/loadings can change across folds, not a stable agronomic effect','original feature; absent training column counts as zero')
    selection.to_csv(out/'tables/30_selection_stability.csv',index=False)
    decisions=[]
    for name,spec in specs.items():
        if not spec.get('base') or spec['kind']=='base':continue
        baseline=comparison[comparison.experiment==baseline_names[spec['base']]].set_index('protocol');z=comparison[comparison.experiment==name].set_index('protocol')
        dr=baseline.RMSE_mean-z.RMSE_mean;dm=baseline.MAE_mean-z.MAE_mean
        decisions.append(dict(experiment=name,base=spec['base'],random_RMSE_gain=dr['random'],worst_grouped_RMSE_gain=dr.drop('random').min(),worst_MAE_gain=dm.min(),passes_metric_margins=bool(dr['random']>0 and dr.drop('random').min()>=-.01 and dm.min()>=-.01)))
    pd.DataFrame(decisions).to_csv(out/'tables/31_operational_decisions.csv',index=False)
    extrapolation_screen(section,version)
    plots(section,out,comparison,q)

def extrapolation_screen(section,version):
    out,proc=locations(section,version);config=json.loads((out/'configuration.json').read_text());d=pd.read_parquet(proc/f'{section.lower()}_features_197_target_free.parquet');t=k.j.supervised_data(d,pd.read_csv(k.j.MASTER));rows=[]
    for protocol,rep,fold,tr,va,inner in k.j.load_frozen_splits(t)[0]:
        for name,spec in config['specs'].items():
            if spec['kind']=='base':continue
            fitted=joblib.load(out/'models'/f'{name}_{protocol}_{rep}_{fold}.joblib')
            eta=fitted['eta'] if isinstance(fitted,dict) else 1
            fitted=fitted['corrector'] if isinstance(fitted,dict) else fitted
            z=fitted['repr'].transform(t.iloc[tr]);v=fitted['repr'].transform(t.iloc[va]);cols=fitted['repr'].get_feature_names_out()
            for j,col in enumerate(cols):
                if 'PC' not in col and not col.startswith('soil'):continue
                sd=z[:,j].std();mean=z[:,j].mean();beta=fitted['model'].coef_[j]
                rows.append(dict(experiment=name,protocol=protocol,repeat=rep,fold=fold,feature=col,training_sd=sd,training_min=z[:,j].min(),training_max=z[:,j].max(),validation_min=v[:,j].min(),validation_max=v[:,j].max(),n_outside_training_range=int(((v[:,j]<z[:,j].min()-1e-10)|(v[:,j]>z[:,j].max()+1e-10)).sum()),max_abs_score_z=float(abs((v[:,j]-mean)/sd).max()) if sd>1e-12 else np.nan,constant_training_dimension=sd<=1e-12,max_abs_proposed_contribution=float(abs(v[:,j]*beta).max()),max_abs_applied_contribution=float(abs(v[:,j]*beta*eta).max())))
    pd.DataFrame(rows).to_csv(out/'tables/33_component_extrapolation.csv',index=False)

def plots(section,out,c,p):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    for metric in ['RMSE','MAE']:
        table=c.pivot(index='experiment',columns='protocol',values=metric+'_mean');ax=table.plot.barh(figsize=(13,max(8,len(table)*.35)));ax.set_xlabel(metric+' t/ha, complete OOF repetition');ax.figure.tight_layout();ax.figure.savefig(out/'figures'/f'{metric}_protocol.png',dpi=160);plt.close(ax.figure)
    residual=p[p.experiment.str.startswith(('L2','L3','L4','L5','MR_'))&p.protocol.eq('random')]
    if len(residual):
        avg=residual.groupby(['experiment',ID]).correction.mean().unstack('experiment');ax=avg.plot(figsize=(13,5));ax.set_ylabel('Mean random OOF correction t/ha');ax.set_xlabel('Parcel ID order');ax.figure.tight_layout();ax.figure.savefig(out/'figures/corrections_by_parcel.png',dpi=160);plt.close(ax.figure)

def finish(section,version,extra=None):
    out,proc=locations(section,version)
    config=json.loads((out/'configuration.json').read_text());p=pd.read_parquet(out/'tables/10_oof_predictions.parquet')
    files=[x for x in out.rglob('*') if x.is_file() and not any(z in x.parts for z in ['checkpoints','base_cache']) and x.name!='manifest.json']+list(proc.glob('*'))
    sources=[ROOT/'src/family_1'/name for name in ['lm_multiblock.py','l_representation.py','m_satellite.py']]
    manifest=dict(status='complete',section=section,n_labelled=138,n_prediction=59,hidden_y_used=False,n_outer=65,n_experiments=len(config['specs']),n_oof_predictions=len(p),models_saved=65*len(config['specs']),packages={x:importlib.metadata.version(x) for x in ['numpy','pandas','scikit-learn','joblib']},sources={str(x.relative_to(ROOT)):k.j.sha(x) for x in sources if x.exists()},artifacts={str(x.relative_to(ROOT)):k.j.sha(x) for x in files},extra=extra or {})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
