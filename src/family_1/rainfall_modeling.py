"""Nested, paired rainfall experiments integrated with frozen Family 1 CV."""
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, PolynomialFeatures, OneHotEncoder
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.dummy import DummyRegressor
from sklearn.model_selection import KFold, GroupKFold, GridSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.cluster import KMeans
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist
from .stage4_modeling import save_splits, SEED, TARGET
from .rainfall_features import ID, MONTHS

SUMMARY = ['rain_total','rain_std','rain_max_share','rain_early_share','rain_late_share']
DYNAMICS = ['rain_longest_increase_streak','rain_longest_decrease_streak','rain_mean_absolute_change']
ANOMALIES = ['rain_anomaly_total','rain_anomaly_largest_deficit','rain_anomaly_negative_streak']
ALPHAS = [.1,1.,10.,100.,1000.]

def experiments():
    monthly = [f'rain_{m}_2025' for m in MONTHS]
    return {
        'E0_MEAN': dict(kind='baseline',columns=[],family='none'),
        'E1_TOTAL_LINEAR': dict(kind='linear',columns=['rain_total'],family='total'),
        'E2_TOTAL_QUADRATIC': dict(kind='quadratic',columns=['rain_total'],family='total_squared'),
        'E3_MONTHLY_LINEAR': dict(kind='linear',columns=monthly,family='monthly'),
        'E3_MONTHLY_RIDGE': dict(kind='ridge',columns=monthly,family='monthly'),
        'E4_SUMMARY_RIDGE': dict(kind='ridge',columns=SUMMARY,family='summary'),
        'E4_TIMING_RIDGE': dict(kind='ridge',columns=SUMMARY+['rain_max_month','rain_min_month'],family='summary_categorical_timing'),
        'E5_DYNAMICS_RIDGE': dict(kind='ridge',columns=SUMMARY+DYNAMICS,family='summary+dynamics'),
        'E6_ANOMALIES_RIDGE': dict(kind='ridge',columns=ANOMALIES,family='anomalies_only'),
        'E6_MONTHLY_ANOMALIES_RIDGE': dict(kind='ridge',columns=[f'rain_anomaly_{m}' for m in MONTHS],family='monthly_anomalies_only'),
        'E6_ABSOLUTE_ANOMALIES_RIDGE': dict(kind='ridge',columns=SUMMARY+ANOMALIES,family='summary+anomalies'),
        'E7_NESTED_COMBINED': dict(kind='select',columns=SUMMARY+DYNAMICS+ANOMALIES,family='inner-selected compact combination'),
        'F_PRE_CYCLE_RIDGE': dict(kind='ridge',columns=SUMMARY+['rain_precycle_total','rain_precycle_anomaly'],family='summary+precycle; separate sensitivity'),
    }

def supervised_data(features, master):
    """CONJUNTO gates targets before any supervised join, even if hidden Y appears."""
    if not master[ID].is_unique or not features[ID].is_unique: raise ValueError('Duplicate parcel')
    train = master.loc[master.CONJUNTO.eq('ENTRENAMIENTO'),[ID,TARGET]].copy()
    if train[TARGET].isna().any(): raise ValueError('Training target missing')
    train[TARGET] = pd.to_numeric(train[TARGET],errors='raise')
    if not np.isfinite(train[TARGET]).all(): raise ValueError('Non-finite target')
    return train.merge(features.drop(columns=['CONJUNTO'],errors='ignore'),on=ID,validate='one_to_one').sort_values(ID).reset_index(drop=True)

def metrics(y, prediction):
    return dict(MAE=float(mean_absolute_error(y,prediction)),RMSE=float(mean_squared_error(y,prediction)**.5),
                R2=float(r2_score(y,prediction)) if len(y)>1 else np.nan,
                bias_pred_minus_y=float(np.mean(np.asarray(prediction)-np.asarray(y))))

def preprocessor(columns, quadratic=False):
    cat = [c for c in columns if c in ('rain_max_month','rain_min_month','rain_anomaly_deficit_month')]
    num = [c for c in columns if c not in cat]
    steps = [('imputer',SimpleImputer(strategy='median',keep_empty_features=True))]
    if quadratic: steps.append(('polynomial',PolynomialFeatures(degree=2,include_bias=False)))
    steps.append(('scale',StandardScaler()))
    parts = [('numeric',Pipeline(steps),num)]
    if cat:
        parts.append(('month',Pipeline([('imputer',SimpleImputer(strategy='most_frequent',keep_empty_features=True)),
            ('onehot',OneHotEncoder(categories=[list(range(4,11))]*len(cat),handle_unknown='ignore',drop='first',sparse_output=False))]),cat))
    return ColumnTransformer(parts,verbose_feature_names_out=False)

def fit_experiment(spec, X, y, inner):
    kind = spec['kind']; cols = spec['columns']
    if kind=='baseline': return DummyRegressor(strategy='mean').fit(np.zeros((len(X),1)),y),{},[]
    X = X[cols].copy()
    pipe = Pipeline([('features',preprocessor(cols,kind=='quadratic')),
                     ('model',Ridge() if kind in ('ridge','select') else LinearRegression())])
    if kind in ('linear','quadratic'): return pipe.fit(X,y),{},cols
    if kind=='select':
        blocks = [SUMMARY, SUMMARY+DYNAMICS, SUMMARY+ANOMALIES, SUMMARY+DYNAMICS+ANOMALIES]
        grid = [{'features':[preprocessor(c)],'model__alpha':ALPHAS} for c in blocks]
    else: grid = {'model__alpha':ALPHAS}
    search = GridSearchCV(pipe,grid,cv=inner,scoring='neg_root_mean_squared_error',n_jobs=1,error_score='raise').fit(X,y)
    best = search.best_estimator_
    selected = sum([list(c) for _,transform,c in best.named_steps['features'].transformers_ if transform!='drop' and isinstance(c,list)],[])
    return best,{'alpha':float(best.named_steps['model'].alpha),'columns':selected,'inner_RMSE':float(-search.best_score_)},selected

def profile_groups(climate, ids, tolerance=.01):
    p = climate.pivot(index=ID,columns=['year','month'],values='precip_mean').reindex(ids)
    if p.isna().any().any(): raise ValueError('Cannot group incomplete climate profiles')
    # Complete linkage guarantees max pairwise month difference <= tolerance within a group.
    return fcluster(linkage(pdist(p.to_numpy(),metric='chebyshev'),method='complete'),t=tolerance,criterion='distance')

def make_splits(d, climate, geography):
    ids = d[ID]; positions = dict(zip(ids,range(len(ids))))
    frozen = save_splits(ids)
    rows = []
    for _,s in frozen.iterrows():
        tr = np.array([positions[p] for p in json.loads(s.train_ID_POLIGONO)])
        va = np.array([positions[p] for p in json.loads(s.validation_ID_POLIGONO)])
        if set(tr)&set(va) or set(tr)|set(va)!=set(range(len(d))): raise ValueError('Invalid frozen split')
        rows.append(('random',int(s['repeat']),int(s.fold),tr,va,None))
    geo = geography.set_index(ID).loc[ids]
    if geo[['Estado','Municipio','x','z']].isna().any().any(): raise ValueError('Missing grouping metadata')
    available_climate = climate[climate.year.lt(2025) | (climate.year.eq(2025) & climate.month.le(10))]
    groups = {'climate_profile':profile_groups(available_climate,ids),
              'municipality':(geo.Estado+'::'+geo.Municipio).to_numpy(),
              'spatial':KMeans(5,random_state=SEED,n_init=50).fit_predict(StandardScaler().fit_transform(geo[['x','z']]))}
    for protocol,g in groups.items():
        if len(np.unique(g)) < 3: continue
        for fold,(tr,va) in enumerate(GroupKFold(min(5,len(np.unique(g)))).split(d,groups=g),1):
            rows.append((protocol,1,fold,tr,va,g))
    table = pd.DataFrame({ID:ids,**groups})
    return rows,table

def evaluate(d, splits, output):
    output = Path(output); predictions=[]; fold_metrics=[]; registry=[]; coefficients=[]; split_records=[]
    specs = experiments()
    (output/'models').mkdir()
    for idx,(protocol,rep,fold,tr,va,groups) in enumerate(splits):
        train, val = d.iloc[tr], d.iloc[va]
        if groups is None:
            inner = list(KFold(4,shuffle=True,random_state=SEED+idx).split(train))
        else:
            inner = list(GroupKFold(min(4,len(np.unique(groups[tr])))).split(train,groups=groups[tr]))
        split_records.append(dict(protocol=protocol,repeat=rep,fold=fold,
            train_ID_POLIGONO=json.dumps(train[ID].tolist()),validation_ID_POLIGONO=json.dumps(val[ID].tolist()),
            inner_validation_ID_POLIGONO=json.dumps([train.iloc[v][ID].tolist() for _,v in inner]),seed=SEED+idx))
        for name,spec in specs.items():
            model,params,cols = fit_experiment(spec,train,train[TARGET],inner)
            prediction = model.predict(np.zeros((len(val),1)) if spec['kind']=='baseline' else val[spec['columns']])
            record = dict(protocol=protocol,experiment=name,repeat=rep,fold=fold)
            fold_metrics.append({**record,**metrics(val[TARGET],prediction), 'n':len(va)})
            predictions.extend([{**record,ID:pid,'y_true':float(y),'y_pred':float(p)} for pid,y,p in zip(val[ID],val[TARGET],prediction)])
            registry.append({**record,'family':spec['family'],'n_train':len(tr),'n_validation':len(va),
                             'n_features':len(cols),'columns':json.dumps(cols),'parameters':json.dumps(params),'status':'success'})
            joblib.dump(model,output/'models'/f'{protocol}_{rep:02d}_{fold:02d}_{name}.joblib',compress=3)
            if spec['kind']!='baseline':
                prep = model.named_steps['features']; reg = model.named_steps['model']
                names = prep.get_feature_names_out()
                z = prep.transform(train)
                singular = np.linalg.svd(z-z.mean(axis=0),compute_uv=False)
                condition = float(singular[0]/singular[-1]) if singular[-1]>1e-12 else np.inf
                scaler = prep.named_transformers_['numeric'].named_steps['scale']
                for j,(n,b) in enumerate(zip(names,reg.coef_)):
                    coefficients.append({**record,'feature_name':n,'coefficient_scaled_numeric':float(b),
                                         'coefficient_original_numeric_units':float(b/scaler.scale_[j]) if j<len(scaler.scale_) else float(b),
                                         'condition_number':condition,'matrix_rank':int(np.linalg.matrix_rank(z-z.mean(axis=0)))})
        print(f'Completed {protocol} repeat={rep} fold={fold} ({idx+1}/{len(splits)})',flush=True)
    p=pd.DataFrame(predictions); fm=pd.DataFrame(fold_metrics); ex=pd.DataFrame(registry)
    p.to_parquet(output/'tables/02_oof_predictions.parquet',index=False)
    p.to_csv(output/'tables/02_oof_predictions.csv',index=False)
    fm.to_csv(output/'tables/03_fold_metrics.csv',index=False)
    ex.to_csv(output/'tables/01_experiment_registry.csv',index=False)
    pd.DataFrame(coefficients).to_csv(output/'tables/04_coefficients.csv',index=False)
    pd.DataFrame(split_records).to_csv(output/'splits/outer_and_inner_splits.csv',index=False)
    return p,fm,ex

def summarize(p, fm, output):
    reps=[]; summary=[]; paired=[]
    for (protocol,name,rep),g in p.groupby(['protocol','experiment','repeat']):
        if not g[ID].is_unique: raise ValueError('Repeated parcel within OOF repetition')
        reps.append(dict(protocol=protocol,experiment=name,repeat=rep,**metrics(g.y_true,g.y_pred)))
    reps=pd.DataFrame(reps)
    for (protocol,name),g in reps.groupby(['protocol','experiment']):
        folds=fm[(fm.protocol==protocol)&(fm.experiment==name)]
        summary.append(dict(protocol=protocol,experiment=name,
            **{f'{m}_mean':g[m].mean() for m in ['MAE','RMSE','R2','bias_pred_minus_y']},
            RMSE_repeat_sd=g.RMSE.std() if len(g)>1 else np.nan,
            RMSE_fold_sd=folds.RMSE.std(),n_repeats=len(g)))
    summary=pd.DataFrame(summary)
    for protocol,g in summary.groupby('protocol'):
        base=g[g.experiment=='E0_MEAN'].iloc[0]
        for _,row in g.iterrows():
            paired.append(dict(protocol=protocol,experiment=row.experiment,
                               delta_RMSE=row.RMSE_mean-base.RMSE_mean,
                               relative_RMSE_improvement=1-row.RMSE_mean/base.RMSE_mean))
    summary=summary.merge(pd.DataFrame(paired),on=['protocol','experiment'])
    summary.to_csv(output/'tables/05_model_comparison.csv',index=False)
    reps.to_csv(output/'tables/06_repetition_metrics.csv',index=False)
    pairs=[('E2_TOTAL_QUADRATIC','E1_TOTAL_LINEAR'),('E3_MONTHLY_RIDGE','E3_MONTHLY_LINEAR'),
           ('E4_SUMMARY_RIDGE','E3_MONTHLY_RIDGE'),('E4_TIMING_RIDGE','E4_SUMMARY_RIDGE'),
           ('E5_DYNAMICS_RIDGE','E4_SUMMARY_RIDGE'),('E6_ABSOLUTE_ANOMALIES_RIDGE','E4_SUMMARY_RIDGE'),
           ('E7_NESTED_COMBINED','E4_SUMMARY_RIDGE'),('F_PRE_CYCLE_RIDGE','E4_SUMMARY_RIDGE')]
    ab=[]
    for protocol in p.protocol.unique():
        for candidate,reference in pairs:
            a=fm[(fm.protocol==protocol)&(fm.experiment==candidate)]
            b=fm[(fm.protocol==protocol)&(fm.experiment==reference)]
            q=a.merge(b,on=['repeat','fold'],suffixes=('_c','_r'))
            loss=(q.RMSE_c-q.RMSE_r)
            ab.append(dict(protocol=protocol,candidate=candidate,reference=reference,
                           mean_paired_fold_delta_RMSE=loss.mean(),fold_win_fraction=(loss<0).mean(),
                           delta_q25=loss.quantile(.25),delta_q75=loss.quantile(.75)))
    pd.DataFrame(ab).to_csv(output/'tables/07_family_contribution.csv',index=False)
    return summary
