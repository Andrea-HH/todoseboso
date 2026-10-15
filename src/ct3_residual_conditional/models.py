"""Exact original C-T3 tuner and small centered correctors."""
import warnings
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.linear_model import ElasticNet,Ridge
from sklearn.model_selection import GridSearchCV
from sklearn.tree import DecisionTreeRegressor
from sklearn.exceptions import ConvergenceWarning
from src.family_4.conditional_response import ConditionalFeatures

CORE=['compact_precip_total','compact_early_fraction','compact_concentration_hhi','S2_ndvi_month_05']
LAI='S2_lai_promedio_runup_start_day'
CONTEXT=CORE[1:]
Z=[LAI]+CONTEXT
BASE_GRID={'model__alpha':[.001,.01,.1,1.],'model__l1_ratio':[.1,.5,.9]}
AMPLITUDES=[0.,.25,.5]
RIDGE_GRID=[dict(alpha=a) for a in [1.,.1,.01]]
TREE_GRID=[dict(max_depth=d,min_samples_leaf=n) for d in [1,2] for n in [25,15]]
SPECS={
 'M1_LAI':dict(kind='ridge',columns=[LAI],grid=RIDGE_GRID),
 'M1_Z':dict(kind='ridge',columns=Z,grid=RIDGE_GRID),
 'M2_Z':dict(kind='tree',columns=Z,grid=TREE_GRID),
 'C_CONTEXT':dict(kind='tree',columns=CONTEXT,grid=TREE_GRID),
}

class MeanBase:
    def fit(self,x,y):self.mean_=float(np.mean(y));return self
    def predict(self,x):return np.repeat(self.mean_,len(x))

def tune_base(frame,y,positions,cv):
    """Only positions and their local CV labels participate in tuning/refit."""
    a=frame.iloc[positions];target=np.asarray(y)[positions]
    probe=ConditionalFeatures(tuple(CORE)).fit(a)
    if not probe.support_.any():return MeanBase().fit(a,target),dict(params={},mean_inner_rmse=np.nan,fit_count=1,fallback='all compact4 constant'),[]
    model=Pipeline([('repr',ConditionalFeatures(tuple(CORE))),('model',ElasticNet(max_iter=200000,random_state=2026))])
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        search=GridSearchCV(model,BASE_GRID,cv=cv,scoring='neg_root_mean_squared_error',n_jobs=1,error_score='raise').fit(a,target)
    logs=[dict(category=w.category.__name__,message=str(w.message)) for w in caught]
    if any(issubclass(w.category,ConvergenceWarning) for w in caught):raise ValueError('Original C-T3 convergence gate failed: '+str(logs))
    return search.best_estimator_,dict(params=search.best_params_,mean_inner_rmse=float(-search.best_score_),fit_count=12*len(cv)+1,fallback='',candidate_mean_rmse=[float(-v) for v in search.cv_results_['mean_test_score']]),logs

class CenteredCorrector:
    def __init__(self,kind,columns,params):self.kind=kind;self.columns=columns;self.params=params
    def fit(self,x,residual):
        assert np.isfinite(np.asarray(residual)).all()
        self.preprocess=ConditionalFeatures(tuple(self.columns)).fit(x)
        a=self.preprocess.transform(x);self.names=list(self.preprocess.get_feature_names_out());self.center=0.;self.constant=not a.shape[1]
        if self.constant:self.model=None;return self
        if self.kind=='ridge':self.model=Ridge(alpha=len(x)*self.params['alpha'],fit_intercept=False,solver='svd').fit(a,residual)
        else:self.model=DecisionTreeRegressor(**self.params,ccp_alpha=0.,random_state=2026).fit(a,residual)
        self.center=float(self.model.predict(a).mean())
        self.constant=bool(np.ptp(self.model.predict(a))<=1e-12)
        assert np.isfinite(self.predict(x)).all()
        return self
    def predict(self,x):
        if self.model is None or self.constant:return np.zeros(len(x))
        return self.model.predict(self.preprocess.transform(x))-self.center
    def leaves(self,x):
        if self.kind!='tree' or self.model is None:return np.zeros(len(x),dtype=int)
        return self.model.apply(self.preprocess.transform(x))
    def rules(self):
        if self.kind!='tree' or self.model is None:return []
        tree=self.model.tree_;rows=[]
        for i in range(tree.node_count):
            j=tree.feature[i]
            if j<0:continue
            feature=self.names[j];original=self.columns.index(feature)
            threshold=float(tree.threshold[i]*self.preprocess.scale_[original]+self.preprocess.mean_[original])
            rows.append(dict(node=i,feature=feature,threshold_raw=threshold,left=int(tree.children_left[i]),right=int(tree.children_right[i]),n_samples=int(tree.n_node_samples[i])))
        return rows

def selection_key(r,kind):
    params=r['params'];complexity=(-params['alpha'],) if kind=='ridge' else (params['max_depth'],-params['min_samples_leaf'])
    return (round(r['rmse'],10),r['amplitude'],*complexity)
