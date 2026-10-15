"""E8 numerical, leakage, compositional and reproducibility contracts."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression,Ridge
from sklearn.model_selection import KFold
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from family_1.rainfall_pcr import pcr_pipeline,tune_pcr,HelmertShares,tune_shape
from family_1.rainfall_pcr_audit import MONTHLY,bounded_groups

def sample(n=32):
    rng=np.random.default_rng(2026)
    X=pd.DataFrame(rng.uniform(1,200,size=(n,7)),columns=MONTHLY)
    y=X.to_numpy()@np.array([.01,-.02,.003,.02,-.01,.005,.004])+rng.normal(0,.1,n)
    return X,y

class PCRTests(unittest.TestCase):
    def test_K7_matches_OLS_full_rank(self):
        X,y=sample();train=X.iloc[:24];val=X.iloc[24:]
        self.assertEqual(np.linalg.matrix_rank(train-train.mean()),7)
        pcr=pcr_pipeline(7).fit(train,y[:24])
        ols=Pipeline([('scale',StandardScaler()),('model',LinearRegression())]).fit(train,y[:24])
        np.testing.assert_allclose(pcr.predict(val),ols.predict(val),atol=1e-10)
    def test_full_PCA_Ridge_rotation_preserves_L2(self):
        X,y=sample();pca=pcr_pipeline(7,True);pca.set_params(model__alpha=2.)
        ridge=Pipeline([('scale',StandardScaler()),('model',Ridge(alpha=2.))])
        np.testing.assert_allclose(pca.fit(X,y).predict(X),ridge.fit(X,y).predict(X),atol=1e-10)
    def test_every_scaler_fit_is_inside_inner_or_outer_train(self):
        X,y=sample();train=X.iloc[:24];inner=list(KFold(4,shuffle=True,random_state=2026).split(train))
        allowed={frozenset(train.index)}|{frozenset(train.iloc[t].index) for t,_ in inner}
        seen=[];original=StandardScaler.fit
        def tracked(instance,frame,y=None,sample_weight=None):
            seen.append(frozenset(frame.index));return original(instance,frame,y,sample_weight=sample_weight)
        with patch.object(StandardScaler,'fit',tracked):search=tune_pcr(train,y[:24],inner)
        self.assertTrue(seen);self.assertTrue(all(ids in allowed for ids in seen))
        self.assertTrue(all(not(set(X.iloc[24:].index)&ids) for ids in seen))
        np.testing.assert_allclose(search.best_estimator_.named_steps['scaler'].mean_,train.mean())
    def test_reproducible_selection_and_only_seven_predictors(self):
        X,y=sample();inner=list(KFold(4,shuffle=True,random_state=2026).split(X))
        a=tune_pcr(X,y,inner,True);X['temperature']=1e9;X['RENDIMIENTO_T_HA']=y
        b=tune_pcr(X,y,inner,True)
        self.assertEqual(a.best_params_,b.best_params_)
        self.assertEqual(list(b.best_estimator_.feature_names_in_),MONTHLY)
        np.testing.assert_allclose(a.predict(X[MONTHLY]),b.predict(X[MONTHLY]))
    def test_missing_month_rejected(self):
        X,y=sample();X.loc[0,MONTHLY[0]]=np.nan
        with self.assertRaises(ValueError):tune_pcr(X,y,list(KFold(4).split(X)))
    def test_zero_variance_month_and_repeated_vectors(self):
        X,y=sample();X[MONTHLY[0]]=10
        p=pcr_pipeline(3).fit(X,y)
        self.assertEqual(p.named_steps['scaler'].scale_[0],1)
        duplicate=pd.concat([X.iloc[:1],X.iloc[:1]])
        values=p.predict(duplicate);self.assertEqual(values[0],values[1])
    def test_Helmert_closure_distances_and_scale_invariance(self):
        X,_=sample();transform=HelmertShares().fit(X)
        z=transform.transform(X);self.assertEqual(z.shape,(32,6))
        s=X.to_numpy()/X.sum(axis=1).to_numpy()[:,None]
        self.assertAlmostEqual(np.linalg.norm(z[0]-z[1]),np.linalg.norm(s[0]-s[1]),places=12)
        np.testing.assert_allclose(transform.transform(X*5),z,atol=1e-12)
        np.testing.assert_allclose(transform.basis_@np.ones(7),0,atol=1e-12)
    def test_shares_zero_policy(self):
        X,_=sample();X.loc[0,MONTHLY[0]]=0;self.assertTrue(np.isfinite(HelmertShares().fit_transform(X)).all())
        X.loc[0,MONTHLY]=0
        with self.assertRaises(ValueError):HelmertShares().fit(X)
        X.loc[0,MONTHLY]=-1
        with self.assertRaises(ValueError):HelmertShares().fit(X)
    def test_bounded_near_groups_never_chain(self):
        x=np.array([[0,1],[.009,1],[.018,1]])
        groups=bounded_groups(x,.01)
        self.assertEqual(len(np.unique(groups)),2)
        for g in np.unique(groups):self.assertLessEqual(np.ptp(x[groups==g],axis=0).max(),.01)
    def test_shape_tuning_uses_only_derived_rainfall(self):
        X,y=sample();inner=list(KFold(4,shuffle=True,random_state=2026).split(X))
        search=tune_shape(X,y,inner,True)
        self.assertEqual(set(search.best_estimator_.feature_names_in_),set(MONTHLY+['rain_total']))
        self.assertTrue(1<=search.best_params_['features__shape__pca__n_components']<=6)

if __name__=='__main__':unittest.main()
