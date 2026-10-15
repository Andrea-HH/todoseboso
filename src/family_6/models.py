"""Conservative direct tree ensembles; existing training-only feature transforms."""
import time,warnings
import numpy as np
from sklearn.ensemble import RandomForestRegressor,ExtraTreesRegressor
from src.family_4.conditional_response import ConditionalFeatures

SEED=2026;N_TREES=384
GRID=[dict(max_depth=depth,min_samples_leaf=leaf,min_samples_split=split,max_features=features)
      for depth,leaf,split in [(3,10,20),(5,5,10),(None,10,20),(None,5,10)] for features in [.5,1.]]

class TreeModel:
    def __init__(self,columns,algorithm,params):self.columns=tuple(columns);self.algorithm=algorithm;self.params=params
    def fit(self,X,y):
        start=time.perf_counter();y=np.asarray(y,float)
        if not np.isfinite(y).all() or len(y)!=len(X):raise ValueError('Finite training targets required')
        self.preprocess_=ConditionalFeatures(self.columns).fit(X);z=self.preprocess_.transform(X)
        if not z.shape[1]:raise ValueError('No varying predictors')
        cls=RandomForestRegressor if self.algorithm=='RF' else ExtraTreesRegressor
        self.forest_=cls(n_estimators=N_TREES,criterion='squared_error',bootstrap=self.algorithm=='RF',max_samples=.8 if self.algorithm=='RF' else None,n_jobs=1,random_state=SEED,**self.params)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always');self.forest_.fit(z,y)
        self.warnings_=[dict(category=w.category.__name__,message=str(w.message)) for w in caught]
        self.training_z_=z;self.training_y_=y.copy();self.fit_seconds_=time.perf_counter()-start
        return self
    def predict(self,X):return self.forest_.predict(self.preprocess_.transform(X))
    def prefix_predictions(self,X):
        z=self.preprocess_.transform(X);pred=np.array([tree.predict(z) for tree in self.forest_.estimators_])
        return {n:pred[:n].mean(axis=0) for n in [128,256,384]}
    def parameters(self):
        samples=self.forest_.estimators_samples_
        return dict(algorithm=self.algorithm,**self.params,n_estimators=N_TREES,bootstrap=self.algorithm=='RF',max_samples=.8 if self.algorithm=='RF' else None,seed=SEED,n_train=len(self.training_y_),n_features=len(self.preprocess_.get_feature_names_out()),training_y_mean=float(self.training_y_.mean()),training_y_min=float(self.training_y_.min()),training_y_max=float(self.training_y_.max()),mean_bootstrap_draws=float(np.mean([len(s) for s in samples])),mean_unique_sample_count=float(np.mean([len(np.unique(s)) for s in samples])),mean_tree_depth=float(np.mean([t.get_depth() for t in self.forest_.estimators_])),mean_leaf_count=float(np.mean([t.get_n_leaves() for t in self.forest_.estimators_])),warnings=self.warnings_,seconds=self.fit_seconds_)
