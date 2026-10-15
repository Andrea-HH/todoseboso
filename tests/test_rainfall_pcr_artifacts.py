"""Integration checks for completed E8, without refitting prior experiments."""
from pathlib import Path
import sys
import json
import unittest
import numpy as np
import pandas as pd
import joblib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from family_1.rainfall_pcr_audit import MONTHLY,REFERENCE,load_data
from family_1.rainfall_pcr import load_frozen_splits
from family_1.rainfall_audit import sha

class PCRArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=ROOT/'outputs/modeling/family_1/rainfall_yield/e8/v1'
        if not (cls.out/'manifest.json').exists():raise unittest.SkipTest('Completed E8 artifacts absent')
        cls.matrix,cls.train=load_data()
        cls.p=pd.read_parquet(cls.out/'tables/30_e8_oof_predictions.parquet')
        cls.splits,cls.table,_=load_frozen_splits(cls.train)
    def test_prior_files_unchanged_and_exact_split_copies(self):
        protected=json.loads((self.out/'protected_inputs.json').read_text(encoding='utf-8'))
        for path,digest in protected.items():self.assertEqual(sha(ROOT/path),digest,path)
        for name in ['outer_and_inner_splits.csv','group_memberships.csv']:
            self.assertEqual((self.out/'splits'/name).read_bytes(),(REFERENCE/'splits'/name).read_bytes())
    def test_same_evaluation_rows_no_hidden_targets(self):
        self.assertEqual(set(self.p.ID_POLIGONO),set(self.train.ID_POLIGONO))
        self.assertFalse(self.p.duplicated(['protocol','experiment','repeat','ID_POLIGONO']).any())
        self.assertTrue(self.p.groupby(['protocol','experiment','repeat']).size().eq(138).all())
        ref=pd.read_parquet(REFERENCE/'tables/02_oof_predictions.parquet').query("experiment == 'E3_MONTHLY_RIDGE'")
        keys=['protocol','repeat','fold','ID_POLIGONO']
        for _,p in self.p.groupby('experiment'):
            q=p.merge(ref,on=keys,validate='one_to_one',suffixes=('_new','_ref'))
            self.assertEqual(len(q),len(ref));np.testing.assert_allclose(q.y_true_new,q.y_true_ref)
    def test_65_K7_equivalence_controls(self):
        table=pd.read_csv(self.out/'tables/35_K7_OLS_equivalence.csv')
        self.assertEqual(len(table),65)
        self.assertTrue((table.loc[table.scaled_rank.eq(7),'max_K7_OLS_prediction_difference']<=1e-7).all())
    def test_saved_models_train_scope_and_prediction_replay(self):
        for protocol,rep,fold,tr,va,inner in self.splits:
            if rep!=1 or fold!=1:continue
            a=self.train.iloc[tr];b=self.train.iloc[va]
            for name in self.p.experiment.unique():
                m=joblib.load(self.out/'models'/f'{protocol}_{rep:02d}_{fold:02d}_{name}.joblib')
                X=b[MONTHLY].copy()
                if name=='E8_TOTAL_SHAPE_RIDGE':X['rain_total']=X.sum(axis=1)
                q=self.p[self.p.protocol.eq(protocol)&self.p['repeat'].eq(rep)&self.p.fold.eq(fold)&self.p.experiment.eq(name)].set_index('ID_POLIGONO').loc[b.ID_POLIGONO]
                np.testing.assert_allclose(m.predict(X),q.y_pred,atol=1e-10)
                if 'scaler' in m.named_steps:
                    self.assertEqual(list(m.feature_names_in_),MONTHLY)
                    np.testing.assert_allclose(m.named_steps['scaler'].mean_,a[MONTHLY].mean())
                    self.assertEqual(m.named_steps['scaler'].n_samples_seen_,len(a))
                    self.assertEqual(m.named_steps['pca'].n_samples_,len(a))
    def test_reference_metrics_copied_consistently(self):
        table=pd.read_csv(self.out/'tables/40_model_comparison.csv')
        prior=pd.read_csv(REFERENCE/'tables/05_model_comparison.csv')
        q=table[table.experiment.isin(['E0_MEAN','E3_MONTHLY_LINEAR','E3_MONTHLY_RIDGE'])].merge(prior,on=['protocol','experiment'],suffixes=('_new','_prior'),validate='one_to_one')
        self.assertEqual(len(q),12)
        for metric in ['RMSE_mean','MAE_mean','R2_mean','bias_pred_minus_y_mean']:
            np.testing.assert_allclose(q[metric+'_new'],q[metric+'_prior'],atol=1e-12)
    def test_exploratory_scores_separate_and_exact_profiles_preserved(self):
        proc=ROOT/'data/processed/family_1/rainfall_yield/e8/v1'
        scores=pd.read_parquet(proc/'exploratory_scores_197.parquet')
        self.assertEqual(len(scores),197);self.assertEqual(set(scores),{'ID_POLIGONO'}|{f'PC{i}' for i in range(1,8)})
        m=joblib.load(self.out/'models/random_01_01_E8_PCR.joblib')
        groups=pd.read_csv(self.out/'tables/05_seven_month_profile_groups.csv').set_index('ID_POLIGONO')
        q=self.matrix.copy();q['prediction']=m.predict(q[MONTHLY]);q=q.join(groups,on='ID_POLIGONO')
        self.assertTrue(q.groupby('exact_profile').prediction.agg(lambda x:x.max()-x.min()).le(1e-12).all())

if __name__=='__main__':unittest.main()
