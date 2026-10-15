"""Training-only transforms and conservative boosting; no external eval_set."""
import time,warnings
import numpy as np
from catboost import CatBoostRegressor
from xgboost import XGBRegressor
from src.family_4.conditional_response import ConditionalFeatures

SEED=2026
# Eight curated candidates, not an open Cartesian search. Fixed before fitting.
CB_GRID=[dict(iterations=n,depth=d,learning_rate=lr,l2_leaf_reg=l2)
         for n,d,lr,l2 in [(150,2,.03,10),(300,2,.03,10),(300,2,.06,10),(300,2,.03,30),
                          (150,3,.03,10),(300,3,.03,10),(300,3,.06,10),(300,3,.03,30)]]
XGB_GRID=[dict(n_estimators=n,max_depth=d,learning_rate=lr,reg_lambda=l2,min_child_weight=10,reg_alpha=1)
          for n,d,lr,l2 in [(150,2,.03,10),(300,2,.03,10),(300,2,.06,10),(300,2,.03,30),
                           (150,3,.03,10),(300,3,.03,10),(300,3,.06,10),(300,3,.03,30)]]
GRIDS={'CatBoost':CB_GRID,'XGBoost':XGB_GRID}

class BoostModel:
    def __init__(self,columns,algorithm,params):
        if algorithm not in GRIDS:raise ValueError(algorithm)
        self.columns=tuple(columns);self.algorithm=algorithm;self.params=params.copy()
    def fit(self,X,y):
        start=time.perf_counter();y=np.asarray(y,float)
        if not np.isfinite(y).all() or len(y)!=len(X):raise ValueError('Finite training targets required')
        self.preprocess_=ConditionalFeatures(self.columns).fit(X);z=self.preprocess_.transform(X)
        if not z.shape[1]:raise ValueError('No varying predictors')
        if self.algorithm=='CatBoost':
            self.booster_=CatBoostRegressor(loss_function='RMSE',grow_policy='SymmetricTree',
                boosting_type='Plain',bootstrap_type='No',random_strength=0,border_count=64,
                leaf_estimation_iterations=1,allow_writing_files=False,thread_count=1,
                random_seed=SEED,verbose=False,**self.params)
        else:
            self.booster_=XGBRegressor(objective='reg:squarederror',tree_method='hist',max_bin=64,
                subsample=1,colsample_bytree=1,gamma=0,n_jobs=1,random_state=SEED,
                verbosity=1,validate_parameters=True,**self.params)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always');self.booster_.fit(z,y)
        self.warnings_=[dict(category=w.category.__name__,message=str(w.message)) for w in caught]
        self.training_z_=z;self.training_y_=y.copy();self.fit_seconds_=time.perf_counter()-start
        return self
    def predict(self,X):return np.asarray(self.booster_.predict(self.preprocess_.transform(X)),float)
    def prefix_predictions(self,X):return {} # No retrospective retuning of boosting rounds.
    def parameters(self):
        n=self.booster_.tree_count_ if self.algorithm=='CatBoost' else self.booster_.get_booster().num_boosted_rounds()
        return dict(algorithm=self.algorithm,**self.params,actual_trees=n,seed=SEED,n_train=len(self.training_y_),
            n_features=len(self.preprocess_.get_feature_names_out()),training_y_mean=float(self.training_y_.mean()),
            training_y_min=float(self.training_y_.min()),training_y_max=float(self.training_y_.max()),
            early_stopping=False,external_eval_set=False,warnings=self.warnings_,seconds=self.fit_seconds_)
