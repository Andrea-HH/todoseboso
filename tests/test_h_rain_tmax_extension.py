"""Scientific controls for the bounded rain/Tmax extension of H."""
from pathlib import Path
import sys,json,unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from family_1.h_rain_tmax_extension import load,profile_frame,COLS,NAME,locations,tune_pcr,verify_protected
from family_1.climate_signal_features import ID,RAIN,MAX,TARGET,paths,sha
from family_1.rainfall_pcr import load_frozen_splits

class ExtensionUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.q,cls.train=load()
    def test_only_rain_and_tmax_and_exactly_53_profiles(self):
        self.assertEqual(COLS,RAIN+MAX);self.assertEqual(len(COLS),14)
        self.assertEqual(len(self.q),197);self.assertEqual(len(self.train),138)
        profiles=profile_frame(self.q);self.assertEqual(len(profiles),53)
        self.assertEqual(profiles.n_parcels.sum(),197)
        for _,g in self.q.groupby('rain'):self.assertEqual(len(g[COLS].drop_duplicates()),1)
        self.assertFalse(set(COLS)&{ID,TARGET,'altitude_m','longitude','latitude','Estado','Municipio'})
    def test_balanced_equal_blocks_are_same_projection(self):
        z=StandardScaler().fit_transform(self.q[COLS]);a=PCA(svd_solver='full').fit(z);b=PCA(svd_solver='full').fit(z/np.sqrt(7))
        np.testing.assert_allclose(abs(np.diag(a.components_@b.components_.T)),1,atol=1e-6)
        np.testing.assert_allclose(a.explained_variance_ratio_,b.explained_variance_ratio_,atol=1e-12)
        np.testing.assert_allclose(a.explained_variance_/7,b.explained_variance_,atol=1e-12)
    def test_full_pcr_equals_OLS_in_same_predictor_space(self):
        rng=np.random.default_rng(413);X=rng.normal(size=(80,14));test=rng.normal(size=(15,14));y=rng.normal(size=80)
        scaler=StandardScaler().fit(X);z=scaler.transform(X);zt=scaler.transform(test);pca=PCA(n_components=14,svd_solver='full').fit(z)
        a=LinearRegression().fit(z,y).predict(zt);b=LinearRegression().fit(pca.transform(z),y).predict(pca.transform(zt))
        np.testing.assert_allclose(a,b,atol=1e-12)
    def test_pca_and_scaling_only_fit_inside_inner_and_outer_training(self):
        rng=np.random.default_rng(42);X=pd.DataFrame(rng.normal(size=(70,14)),columns=COLS);y=pd.Series(rng.normal(size=70))
        tr=np.arange(50);inner=list(KFold(3).split(tr));seen=[];pca_seen=[];original=StandardScaler.fit;original_pca=PCA.fit_transform
        def spy(obj,x,*args,**kwargs):seen.append(np.array(x));return original(obj,x,*args,**kwargs)
        def pca_spy(obj,x,*args,**kwargs):pca_seen.append(np.array(x));return original_pca(obj,x,*args,**kwargs)
        with patch.object(StandardScaler,'fit',spy),patch.object(PCA,'fit_transform',pca_spy):result=tune_pcr(X.iloc[tr],y.iloc[tr],inner)
        expected=[X.iloc[tr].to_numpy()]+[X.iloc[tr].iloc[a].to_numpy() for a,b in inner]
        for fit in seen:self.assertTrue(any(fit.shape==e.shape and np.allclose(fit,e) for e in expected))
        expected_scaled=[StandardScaler().fit_transform(e) for e in expected]
        for fit in pca_seen:self.assertTrue(any(fit.shape==e.shape and np.allclose(fit,e) for e in expected_scaled))
        self.assertEqual(len(seen),14*3+1);self.assertEqual(len(pca_seen),len(seen))
        self.assertEqual(result.best_estimator_.named_steps['scaler'].n_samples_seen_,50)

class ExtensionArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=locations('v1');cls.q,cls.train=load();cls.p=pd.read_parquet(cls.out/'tables/39_comparison_oof.parquet')
    def test_same_folds_and_same_targets_for_every_comparison(self):
        _,old,_=load_frozen_splits(self.train);new=pd.read_csv(self.out/'splits/outer_and_inner_splits.csv')
        pd.testing.assert_frame_equal(old,new,check_dtype=False)
        expected=self.train.set_index(ID)[TARGET]
        for _,z in self.p.groupby(['protocol','experiment','repeat']):
            self.assertEqual(len(z),138);self.assertTrue(z[ID].is_unique)
            np.testing.assert_array_equal(z.y_true,expected.loc[z[ID]])
    def test_cached_h6_and_rain_predictions_unchanged(self):
        keys=['protocol','repeat','fold',ID];cols=keys+['experiment','y_true','y_pred']
        old=pd.read_parquet(paths('H','v1')[0]/'tables/31_oof_individual.parquet')
        names=['H0_MEAN','H1_RAIN','H3_TMAX','H6_RAIN_TMAX'];old=old[old.experiment.isin(names)][cols].sort_values(cols[:5]).reset_index(drop=True)
        new=self.p[self.p.experiment.isin(names)][cols].sort_values(cols[:5]).reset_index(drop=True)
        pd.testing.assert_frame_equal(old,new)
    def test_replay_saved_pcr_and_profile_equal_fit_scope(self):
        splits,_,_=load_frozen_splits(self.train)
        for protocol,rep,fold,tr,va,inner in splits:
            if rep!=1 or fold!=1:continue
            model=joblib.load(self.out/'models'/f'{protocol}_{rep:02d}_{fold:02d}_{NAME}.joblib')
            saved=self.p[self.p.protocol.eq(protocol)&self.p.experiment.eq(NAME)&self.p['repeat'].eq(rep)&self.p.fold.eq(fold)].set_index(ID).loc[self.train.iloc[va][ID]]
            np.testing.assert_allclose(model.predict(self.train.iloc[va][COLS]),saved.y_pred,atol=1e-12)
            np.testing.assert_allclose(model.named_steps['scaler'].mean_,self.train.iloc[tr][COLS].mean(),atol=1e-12)
            self.assertEqual(model.named_steps['scaler'].n_samples_seen_,len(tr))
        profiles=profile_frame(self.q)
        for file in (self.out/'models').glob('descriptive_equal_profile_*.joblib'):
            obj=joblib.load(file);self.assertEqual(obj['scaler'].n_samples_seen_,53)
            np.testing.assert_allclose(obj['scaler'].mean_,profiles[obj['columns']].mean(),atol=1e-12)
    def test_paired_deltas_and_selected_K_match_inner_argmin(self):
        f=pd.read_csv(self.out/'tables/41_fold_metrics.csv');d=pd.read_csv(self.out/'tables/44_paired_fold_deltas.csv')
        for r in d.itertuples():
            z=f[f.protocol.eq(r.protocol)&f['repeat'].eq(r.repeat)&f.fold.eq(r.fold)].set_index('experiment')
            self.assertAlmostEqual(r.delta_RMSE,z.loc[r.base,'RMSE']-z.loc[NAME,'RMSE'],places=12)
        registry=pd.read_csv(self.out/'tables/31_pcr_registry.csv');inner=pd.read_csv(self.out/'tables/32_inner_K_selection.csv')
        for r in registry.itertuples():
            z=inner[inner.protocol.eq(r.protocol)&inner['repeat'].eq(r.repeat)&inner.fold.eq(r.fold)]
            self.assertEqual(r.selected_K,z.loc[z.inner_RMSE.idxmin(),'K'])
    def test_previous_inputs_and_manifest_and_target_free_scores(self):
        verify_protected(self.out)
        manifest=json.loads((self.out/'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['predictive_specs_added'],1);self.assertEqual(manifest['outer_fits'],65)
        self.assertFalse(manifest['hidden_y_used'])
        for name,digest in manifest['artifacts'].items():self.assertEqual(sha(self.out/name),digest,name)
        for name,digest in manifest.get('source_hashes',{}).items():self.assertEqual(sha(ROOT/name),digest,name)
        for file in (self.out/'tables').glob('13_*scores_target_free.parquet'):
            z=pd.read_parquet(file);self.assertFalse(set(z)&{TARGET,'y_true','y_pred'})
            self.assertEqual(len(z),53 if 'equal_profile' in file.name else 197)

if __name__=='__main__':unittest.main()
