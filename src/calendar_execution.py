"""Equivalent single-thread scoring to avoid nested CatBoost thread oversubscription.

Training parameters are unchanged. CatBoost's post-fit feature importance and
predict default to all cores independently of the constructor thread_count.
"""
from catboost import CatBoostRegressor

def install_single_thread_scoring():
    if getattr(CatBoostRegressor,'_calendar_single_thread_scoring',False):return
    original_predict=CatBoostRegressor.predict
    original_importance=CatBoostRegressor.get_feature_importance
    def predict(self,*args,**kwargs):
        if len(args)<5:kwargs.setdefault('thread_count',1)
        return original_predict(self,*args,**kwargs)
    def importance(self,*args,**kwargs):
        if len(args)<4:kwargs.setdefault('thread_count',1)
        return original_importance(self,*args,**kwargs)
    CatBoostRegressor.predict=predict
    CatBoostRegressor.get_feature_importance=importance
    CatBoostRegressor._calendar_single_thread_scoring=True

def work_fold_single_thread(index):
    install_single_thread_scoring()
    from src.calendar_expansion import work_fold
    return work_fold(index)
