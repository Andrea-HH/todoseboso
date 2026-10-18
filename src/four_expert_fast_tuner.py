"""Same C-T3 grid and folds, reusing parameter-independent preprocessing."""
import warnings
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import ParameterGrid
from sklearn.metrics import root_mean_squared_error
from sklearn.exceptions import ConvergenceWarning
from src.ct3_residual_conditional.models import CORE,BASE_GRID,MeanBase,tune_base as ORIGINAL
from src.family_4.conditional_response import ConditionalFeatures

def tune_base_cached_repr(frame,y,positions,cv):
    if not isinstance(cv,(list,tuple)):return ORIGINAL(frame,y,positions,cv)
    a=frame.iloc[positions];target=np.asarray(y)[positions];raw=a[CORE].to_numpy(float)
    # Preserve legacy warning multiplicity for all-missing columns, not only predictions.
    if np.any(~np.isfinite(raw).any(axis=0)) or any(np.any(~np.isfinite(raw[c]).any(axis=0)) for c,d in cv):return ORIGINAL(frame,y,positions,cv)
    probe=ConditionalFeatures(tuple(CORE)).fit(a)
    if not probe.support_.any():return MeanBase().fit(a,target),dict(params={},mean_inner_rmse=np.nan,fit_count=1,fallback='all compact4 constant'),[]
    prepared=[]
    for c,d in cv:
        rep=ConditionalFeatures(tuple(CORE)).fit(a.iloc[c],target[c]);train=rep.transform(a.iloc[c]);held=rep.transform(a.iloc[d])
        if train.shape[1]==0:return ORIGINAL(frame,y,positions,cv)
        prepared.append((train,held,target[c],target[d]))
    candidates=list(ParameterGrid(BASE_GRID));scores=[]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        for params in candidates:
            kwargs={k.split('__',1)[1]:v for k,v in params.items()};fold=[]
            for train,held,yt,yv in prepared:
                model=ElasticNet(**kwargs,max_iter=200000,random_state=2026).fit(train,yt);fold.append(float(root_mean_squared_error(yv,model.predict(held))))
            scores.append(float(np.mean(fold)))
        best=int(np.argmin(scores));kwargs={k.split('__',1)[1]:v for k,v in candidates[best].items()};model=Pipeline([('repr',ConditionalFeatures(tuple(CORE))),('model',ElasticNet(**kwargs,max_iter=200000,random_state=2026))]).fit(a,target)
    logs=[dict(category=w.category.__name__,message=str(w.message)) for w in caught]
    if any(issubclass(w.category,ConvergenceWarning) for w in caught):raise ValueError('Original C-T3 convergence gate failed: '+str(logs))
    return model,dict(params=candidates[best],mean_inner_rmse=scores[best],fit_count=12*len(cv)+1,fallback='',candidate_mean_rmse=scores),logs

def activate():
    from src import neighbor_signal_contrasts
    neighbor_signal_contrasts.tune_base=tune_base_cached_repr
