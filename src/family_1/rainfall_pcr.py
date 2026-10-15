"""E8: seven-month PCA/PCR, strictly nested within immutable rainfall folds."""
from pathlib import Path
import json
import platform
import importlib.metadata
import shutil
import joblib
import numpy as np
import pandas as pd
from scipy.linalg import helmert
from sklearn.base import BaseEstimator,TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression,Ridge
from sklearn.model_selection import GridSearchCV
from .rainfall_features import ID
from .rainfall_modeling import metrics,ALPHAS,TARGET
from .rainfall_pcr_audit import MONTHLY,REFERENCE,FEATURES,DICTIONARY,load_data,diagnose_profiles
from .rainfall_audit import ROOT,SHAPE,MASTER,sha

def pcr_pipeline(k=7,ridge=False):
    return Pipeline([('scaler',StandardScaler()),('pca',PCA(n_components=k,svd_solver='full')),
                     ('model',Ridge() if ridge else LinearRegression())])

def tune_pcr(X,y,inner,ridge=False):
    X=X[MONTHLY]
    if not np.isfinite(X).all().all():raise ValueError('Complete monthly vectors required; no imputation in E8')
    grid={'pca__n_components':list(range(1,8))}
    if ridge:grid['model__alpha']=ALPHAS
    return GridSearchCV(pcr_pipeline(ridge=ridge),grid,cv=inner,scoring='neg_root_mean_squared_error',
                        n_jobs=1,error_score='raise',return_train_score=False).fit(X,y)

class HelmertShares(BaseEstimator,TransformerMixin):
    """Six orthonormal Euclidean simplex contrasts; no log or zero replacement."""
    def fit(self,X,y=None):
        self.basis_=helmert(7,full=False)
        self.transform(X)
        return self
    def transform(self,X):
        x=np.asarray(X,float)
        if x.ndim!=2 or x.shape[1]!=7 or not np.isfinite(x).all() or (x<0).any() or (x.sum(axis=1)<=0).any():
            raise ValueError('Shares require 7 nonnegative monthly values and positive total')
        return (x/x.sum(axis=1,keepdims=True))@self.basis_.T
    def get_feature_names_out(self,input_features=None):return np.array([f'share_contrast_{i}' for i in range(1,7)])

def shape_pipeline(combine_total=False):
    shape=Pipeline([('shares',HelmertShares()),('center',StandardScaler(with_std=False)),
                    ('pca',PCA(n_components=2,svd_solver='full'))])
    if not combine_total:return Pipeline([('shape',shape),('model',LinearRegression())])
    features=ColumnTransformer([('total',StandardScaler(),['rain_total']),('shape',shape,MONTHLY)])
    return Pipeline([('features',features),('model',Ridge())])

def tune_shape(X,y,inner,combine_total=False):
    pipeline=shape_pipeline(combine_total)
    param='features__shape__pca__n_components' if combine_total else 'shape__pca__n_components'
    grid={param:list(range(1,7))}
    if combine_total:grid['model__alpha']=ALPHAS
    frame=X[MONTHLY].copy()
    if combine_total:frame['rain_total']=frame.sum(axis=1)
    return GridSearchCV(pipeline,grid,cv=inner,scoring='neg_root_mean_squared_error',n_jobs=1,error_score='raise').fit(frame,y)

def load_frozen_splits(train):
    """Restore exact outer AND inner ID lists, including grouped inner folds."""
    table=pd.read_csv(REFERENCE/'splits/outer_and_inner_splits.csv')
    assignments=pd.read_csv(REFERENCE/'splits/group_memberships.csv').set_index(ID)
    lookup=dict(zip(train[ID],range(len(train))))
    result=[]
    for row in table.itertuples():
        trids=json.loads(row.train_ID_POLIGONO);vaids=json.loads(row.validation_ID_POLIGONO)
        if set(trids)&set(vaids) or set(trids)|set(vaids)!=set(lookup):raise ValueError('Invalid existing outer split')
        positions=dict(zip(trids,range(len(trids))));inner=[]
        seen=[]
        for ids in json.loads(row.inner_validation_ID_POLIGONO):
            if not set(ids)<=set(trids):raise ValueError('Inner fold leaks outside training')
            iva=np.array([positions[pid] for pid in ids]);itr=np.setdiff1d(np.arange(len(trids)),iva)
            if row.protocol!='random':
                groups=assignments.loc[trids,row.protocol].to_numpy()
                if set(groups[itr])&set(groups[iva]):raise ValueError('Inner grouped split mixes groups')
            inner.append((itr,iva));seen.extend(ids)
        if len(seen)!=len(trids) or set(seen)!=set(trids):raise ValueError('Invalid inner coverage')
        result.append((row.protocol,int(row.repeat),int(row.fold),np.array([lookup[p] for p in trids]),
            np.array([lookup[p] for p in vaids]),inner))
    return result,table,assignments

def exploratory_pca(matrix,train,geography,out,proc):
    X=matrix[MONTHLY];pipeline=Pipeline([('scaler',StandardScaler()),('pca',PCA(n_components=7,svd_solver='full'))]).fit(X)
    z=pipeline.named_steps['scaler'].transform(X);pca=pipeline.named_steps['pca'];scores=pipeline.transform(X)
    names=[f'PC{i}' for i in range(1,8)]
    eigen=pd.DataFrame({'component':names,'eigenvalue':pca.explained_variance_,
        'explained_variance':pca.explained_variance_ratio_,'cumulative_variance':np.cumsum(pca.explained_variance_ratio_)})
    eigen.to_csv(out/'tables/20_exploratory_variance.csv',index=False)
    loadings=pd.DataFrame(pca.components_.T,index=MONTHLY,columns=names)
    loadings.to_csv(out/'tables/21_exploratory_loadings.csv')
    loadings.pow(2).to_csv(out/'tables/22_month_squared_loading_contributions.csv')
    # Squared eigenvectors sum to one per component; loadings are NOT correlations.
    correlation=pd.DataFrame(np.corrcoef(scores.T,X.to_numpy().T)[:7,7:],index=names,columns=MONTHLY)
    correlation.to_csv(out/'tables/23_pc_original_month_correlations.csv')
    X.corr().to_csv(out/'tables/24_month_correlations.csv')
    scaling=pipeline.named_steps['scaler']
    pd.DataFrame({'month':MONTHLY,'mean_mm':scaling.mean_,'population_variance_mm2':scaling.var_,
        'scale_mm':scaling.scale_,'zero_variance':scaling.var_==0}).to_csv(out/'tables/25_exploratory_scaling.csv',index=False)
    score_table=pd.DataFrame(scores,columns=names);score_table.insert(0,ID,matrix[ID])
    score_table.to_parquet(proc/'exploratory_scores_197.parquet',index=False)
    score_table.to_csv(out/'tables/26_exploratory_scores_197.csv',index=False)
    joblib.dump(pipeline,out/'models/exploratory_PCA_197_target_free.joblib',compress=3)
    labeled=score_table.merge(train[[ID,TARGET]],on=ID,validate='one_to_one')
    pd.DataFrame([{'component':pc,'n_labeled':len(labeled),'pearson_y':labeled[pc].corr(labeled[TARGET]),
        'spearman_y':labeled[pc].corr(labeled[TARGET],method='spearman'),'role':'descriptive only; not used for K selection'} for pc in names]).to_csv(out/'tables/27_exploratory_pc_y_associations.csv',index=False)
    regions=score_table.merge(geography[[ID,'Estado','Municipio']],on=ID)
    total_ss=np.sum((scores-scores.mean(axis=0))**2,axis=0)
    eta=[]
    for field in ['Estado','Municipio']:
        for j,pc in enumerate(names):
            between=sum(len(g)*(g[pc].mean()-regions[pc].mean())**2 for _,g in regions.groupby(field))
            eta.append({'region':field,'component':pc,'descriptive_between_group_variance_fraction':between/total_ss[j]})
    pd.DataFrame(eta).to_csv(out/'tables/28_pc_geographic_structure.csv',index=False)
    k95=int(np.searchsorted(np.cumsum(pca.explained_variance_ratio_),.95)+1)
    return dict(pipeline=pipeline,scores=score_table,variance=eigen,loadings=loadings,k95=k95,
        zero_variance_months=list(X.columns[scaling.var_==0]),standardized_matrix_rank=int(np.linalg.matrix_rank(z)))

def evaluate(train,splits,exploratory,out,shape_extension):
    predictions=[];registry=[];tuning=[];fold_pc=[];coefficients=[];equivalence=[]
    previous=pd.read_parquet(REFERENCE/'tables/02_oof_predictions.parquet')
    ref_loadings=exploratory['pipeline'].named_steps['pca'].components_
    for idx,(protocol,repeat,fold,tr,va,inner) in enumerate(splits):
        prefix=f'{protocol}_{repeat:02d}_{fold:02d}'
        checkpoint=out/'checkpoints'/f'{prefix}.joblib'
        if checkpoint.exists():
            pack=joblib.load(checkpoint)
        else:
            a=train.iloc[tr];b=train.iloc[va];X=a[MONTHLY];V=b[MONTHLY];y=a[TARGET]
            pack={name:[] for name in ['predictions','registry','tuning','fold_pc','coefficients','equivalence']}
            models={}
            for k in range(1,8):
                name=f'E8_PCR_K{k}';m=pcr_pipeline(k).fit(X,y)
                models[name]=(m,{'K':k,'selection':'fixed control; not selected on outer validation'})
            for name,ridge in [('E8_PCR',False),('E8_PCA_RIDGE',True)]:
                search=tune_pcr(X,y,inner,ridge)
                models[name]=(search.best_estimator_,dict(K=int(search.best_params_['pca__n_components']),
                    alpha=float(search.best_params_['model__alpha']) if ridge else None,inner_RMSE=float(-search.best_score_)))
                for j,params in enumerate(search.cv_results_['params']):
                    pack['tuning'].append(dict(protocol=protocol,repeat=repeat,fold=fold,experiment=name,
                        parameters=json.dumps(params),inner_mean_RMSE=float(-search.cv_results_['mean_test_score'][j]),
                        inner_fold_score_sd=float(search.cv_results_['std_test_score'][j])))
            if shape_extension:
                for name,combined in [('E8_SHAPE_PCR',False),('E8_TOTAL_SHAPE_RIDGE',True)]:
                    search=tune_shape(X,y,inner,combined)
                    key='features__shape__pca__n_components' if combined else 'shape__pca__n_components'
                    models[name]=(search.best_estimator_,dict(K=int(search.best_params_[key]),
                        alpha=float(search.best_params_['model__alpha']) if combined else None,inner_RMSE=float(-search.best_score_)))
                    for j,params in enumerate(search.cv_results_['params']):
                        pack['tuning'].append(dict(protocol=protocol,repeat=repeat,fold=fold,experiment=name,
                            parameters=json.dumps(params),inner_mean_RMSE=float(-search.cv_results_['mean_test_score'][j]),
                            inner_fold_score_sd=float(search.cv_results_['std_test_score'][j])))
            from scipy.optimize import linear_sum_assignment
            full=models['E8_PCR_K7'][0];pca=full.named_steps['pca'];z=full.named_steps['scaler'].transform(X);pc=pca.transform(z)
            match_i,match_j=linear_sum_assignment(-abs(pca.components_@ref_loadings.T))
            matching=dict(zip(match_i,match_j))
            for j in range(7):
                covariance=float(np.dot(pca.components_[j],ref_loadings[matching[j]]))
                pack['fold_pc'].append(dict(protocol=protocol,repeat=repeat,fold=fold,component=j+1,
                    eigenvalue=float(pca.explained_variance_[j]),variance_fraction=float(pca.explained_variance_ratio_[j]),
                    training_y_correlation=float(np.corrcoef(pc[:,j],y)[0,1]),
                    reference_component=matching[j]+1,absolute_loading_cosine=abs(covariance),
                    aligned_loadings=json.dumps((pca.components_[j]*np.sign(covariance)).tolist()),
                    role='postfit interpretation only; global reference never used to fit predictive model'))
            for name,(model,params) in models.items():
                validation=V.copy()
                if name=='E8_TOTAL_SHAPE_RIDGE':validation['rain_total']=validation.sum(axis=1)
                predicted=model.predict(validation)
                key=dict(protocol=protocol,experiment=name,repeat=repeat,fold=fold)
                pack['predictions'].extend([{**key,ID:pid,'y_true':float(actual),'y_pred':float(pred)} for pid,actual,pred in zip(b[ID],b[TARGET],predicted)])
                pack['registry'].append({**key,'parameters':json.dumps(params),'selected_K':params['K'],
                    'n_train':len(tr),'n_validation':len(va),'inputs':json.dumps(MONTHLY),
                    'algorithm':str(model),'status':'success'})
                joblib.dump(model,out/'models'/f'{prefix}_{name}.joblib',compress=3)
                if 'scaler' in model.named_steps:
                    scaler=model.named_steps['scaler'];p=model.named_steps['pca'];reg=model.named_steps['model']
                    beta_z=p.components_.T@reg.coef_;beta=beta_z/scaler.scale_
                    intercept=float(reg.intercept_-reg.coef_@p.components_@p.mean_-beta@scaler.mean_)
                    if not np.allclose(predicted,V.to_numpy()@beta+intercept,atol=1e-9):raise ValueError('Backprojected PCR coefficients disagree')
                    for j,c in enumerate(MONTHLY):pack['coefficients'].append({**key,'month':c,'coefficient_t_ha_per_mm':float(beta[j]),'original_intercept':intercept})
                    pc_train=p.transform(scaler.transform(X));singular=np.linalg.svd(pc_train,compute_uv=False)
                    pack['registry'][-1]['PC_condition_number']=float(singular[0]/singular[-1])
            q=previous[(previous.protocol==protocol)&(previous['repeat']==repeat)&(previous.fold==fold)&(previous.experiment=='E3_MONTHLY_LINEAR')].set_index(ID).loc[b[ID]]
            if not np.allclose(q.y_true,b[TARGET]):raise ValueError('E3 reference targets differ')
            error=float(np.max(abs(full.predict(V)-q.y_pred.to_numpy())))
            if np.linalg.matrix_rank(z)==7 and error>1e-7:raise ValueError(f'K7/OLS equivalence failed {prefix}: {error}')
            pack['equivalence'].append(dict(protocol=protocol,repeat=repeat,fold=fold,scaled_rank=int(np.linalg.matrix_rank(z)),
                max_K7_OLS_prediction_difference=error,tolerance_t_ha=1e-7))
            joblib.dump(pack,checkpoint,compress=3)
        for name in ['predictions','registry','tuning','fold_pc','coefficients','equivalence']:
            locals()[name].extend(pack[name])
        print(f'E8 {idx+1}/{len(splits)} {prefix}',flush=True)
    frames=dict(predictions=pd.DataFrame(predictions),registry=pd.DataFrame(registry),tuning=pd.DataFrame(tuning),
        fold_pc=pd.DataFrame(fold_pc),coefficients=pd.DataFrame(coefficients),equivalence=pd.DataFrame(equivalence))
    frames['predictions'].to_parquet(out/'tables/30_e8_oof_predictions.parquet',index=False)
    frames['predictions'].to_csv(out/'tables/30_e8_oof_predictions.csv',index=False)
    for key,name in [('registry','31_experiment_registry'),('tuning','32_inner_tuning_results'),('fold_pc','33_training_pc_stability'),
                     ('coefficients','34_backprojected_monthly_coefficients'),('equivalence','35_K7_OLS_equivalence')]:
        frames[key].to_csv(out/'tables'/f'{name}.csv',index=False)
    return frames

def run(out):
    out=Path(out)
    if (out/'manifest.json').exists():raise FileExistsError('Completed E8 run is immutable; choose a new run-id')
    if not (out/'audit_manifest.json').exists():raise ValueError('Run E8 audit first')
    snapshot=json.loads((out/'protected_inputs.json').read_text(encoding='utf-8'))
    for path,digest in snapshot.items():
        if sha(ROOT/path)!=digest:raise ValueError(f'Protected input changed: {path}')
    matrix,train=load_data()
    import geopandas as gpd
    geo=gpd.read_file(SHAPE).rename(columns={'ID_POLIGON':ID}).to_crs(6372)
    if not (out/'figures/01_profile_colored_individual_vs_average.png').exists():diagnose_profiles(matrix,train,geo,out)
    proc=ROOT/'data/processed/family_1/rainfall_yield/e8'/out.name
    proc.mkdir(parents=True,exist_ok=True)
    matrix.to_parquet(proc/'monthly_input_matrix_197.parquet',index=False)
    splits,table,assignments=load_frozen_splits(train)
    shutil.copy2(REFERENCE/'splits/outer_and_inner_splits.csv',out/'splits/outer_and_inner_splits.csv')
    shutil.copy2(REFERENCE/'splits/group_memberships.csv',out/'splits/group_memberships.csv')
    info=exploratory_pca(matrix,train,geo,out,proc)
    # One bounded composition extension, decided from climate structure without Y.
    shape_extension=bool(info['k95']<=4 and (matrix[MONTHLY].sum(axis=1)>0).all())
    configuration=dict(experiment='E8_RAINFALL_PCA_PCR',inputs=MONTHLY,seed=2026,
        K_grid=list(range(1,8)),alpha_grid=ALPHAS,outer_folds=len(splits),
        split_source='exact saved E3 outer and inner ID assignments',
        predictive_pipeline='StandardScaler -> PCA -> LinearRegression / Ridge',
        selection='nested inner mean-fold RMSE only; ties choose first (lowest K, then alpha)',
        primary_metrics='mean complete-repeat OOF metrics; averaged OOF is diagnostic only',
        descriptive_PCA='197 parcels; never used as precomputed predictive input',
        shape_extension=shape_extension,shape_gate='exploratory absolute PCA needs <=4 PCs for 95% climate variance; positive cycle totals',
        shape_representation='S=P/sum(P), six orthonormal Helmert contrasts, center only, PCA; Euclidean compositional limitation',
        shape_K_grid=list(range(1,7)),shape_total_algorithm='standardized total + shape PCs -> Ridge; all fit in inner folds',
        shape_zeros='zeros valid; zero-total vector rejected; no log-ratios or arbitrary zero substitution')
    config_path=out/'configuration.json'
    if config_path.exists() and json.loads(config_path.read_text(encoding='utf-8'))!=configuration:raise ValueError('Checkpoint configuration differs')
    config_path.write_text(json.dumps(configuration,indent=2),encoding='utf-8')
    from .rainfall_pcr_reporting import exploratory_figures,finish
    exploratory_figures(matrix,train,geo,info,out,proc,shape_extension)
    frames=evaluate(train,splits,info,out,shape_extension)
    decision=finish(matrix,train,geo,info,frames,out,shape_extension)
    for path,digest in snapshot.items():
        if sha(ROOT/path)!=digest:raise ValueError(f'Previous result was modified: {path}')
    source=list((ROOT/'src/family_1').glob('rainfall_pcr*.py'))+[ROOT/'scripts/modeling/315_rainfall_pca_pcr.py']
    manifest=dict(status='complete',experiment='E8_RAINFALL_PCA_PCR',train_n=138,all_n=197,hidden_y_used=False,
        monthly_predictors=MONTHLY,outer_folds=len(splits),shape_extension=shape_extension,
        exploratory_PCA_used_in_predictive_transform=False,original_results_unchanged=True,
        max_K7_OLS_difference=float(frames['equivalence'].max_K7_OLS_prediction_difference.max()),
        decision=decision,python=platform.python_version(),
        packages={p:importlib.metadata.version(p) for p in ['numpy','pandas','scikit-learn','scipy','joblib','geopandas']},
        source_hashes={str(p.relative_to(ROOT)):sha(p) for p in source},
        protected_input_manifest_sha256=sha(out/'protected_inputs.json'),
        artifacts={str(p.relative_to(ROOT)):sha(p) for p in list(out.rglob('*'))+list(proc.rglob('*')) if p.is_file() and 'checkpoints' not in p.parts})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('E8 complete:',decision,flush=True)
