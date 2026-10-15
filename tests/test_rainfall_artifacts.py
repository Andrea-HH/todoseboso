"""Integration contracts for a completed v1 run (skipped when artifacts absent)."""
import json
from pathlib import Path
import sys
import unittest
import joblib
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from family_1.rainfall_features import build_features,ID
from family_1.rainfall_modeling import supervised_data,metrics

class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=ROOT/'outputs/modeling/family_1/rainfall_yield/v1'
        if not (cls.out/'manifest.json').exists():raise unittest.SkipTest('Completed rainfall v1 artifacts not present')
        cls.features=pd.read_parquet(ROOT/'data/processed/family_1/rainfall_yield/v1/rainfall_features.parquet')
        cls.master=pd.read_csv(ROOT/'data/original/01_tablas_maestras/ID_area_rendimiento_70_30_Reto_AgroCebada.csv')
        cls.d=supervised_data(cls.features,cls.master)
        cls.pred=pd.read_parquet(cls.out/'tables/02_oof_predictions.parquet')
        cls.splits=pd.read_csv(cls.out/'splits/outer_and_inner_splits.csv')
    def test_supervised_universe_and_coverage(self):
        self.assertEqual(len(self.features),197);self.assertEqual(len(self.d),138)
        self.assertEqual(set(self.pred[ID]),set(self.d[ID]))
        self.assertFalse(self.pred.duplicated(['protocol','experiment','repeat',ID]).any())
        self.assertTrue(self.pred.groupby(['protocol','experiment','repeat']).size().eq(138).all())
    def test_frozen_and_grouped_splits(self):
        frozen=pd.read_csv(ROOT/'outputs/modeling/family_1/stage4/splits/outer_splits.csv')
        q=self.splits[self.splits.protocol.eq('random')].merge(frozen,on=['repeat','fold'],suffixes=('_new','_old'))
        self.assertEqual(len(q),50)
        for row in q.itertuples():
            self.assertEqual(json.loads(row.train_ID_POLIGONO_new),json.loads(row.train_ID_POLIGONO_old))
            self.assertEqual(json.loads(row.validation_ID_POLIGONO_new),json.loads(row.validation_ID_POLIGONO_old))
        groups=pd.read_csv(self.out/'splits/group_memberships.csv').set_index(ID)
        for row in self.splits.itertuples():
            tr=json.loads(row.train_ID_POLIGONO);va=json.loads(row.validation_ID_POLIGONO)
            self.assertFalse(set(tr)&set(va));self.assertEqual(set(tr)|set(va),set(self.d[ID]))
            for inner in json.loads(row.inner_validation_ID_POLIGONO):self.assertTrue(set(inner)<=set(tr))
            if row.protocol!='random':self.assertFalse(set(groups.loc[tr,row.protocol])&set(groups.loc[va,row.protocol]))
    def test_feature_reproduction(self):
        rebuilt,_=build_features(pd.read_parquet(ROOT/'data/processed/family_1/environment/climate_monthly_timeseries.parquet'))
        pd.testing.assert_frame_equal(self.features.drop(columns='CONJUNTO'),rebuilt)
    def test_registry_and_saved_predictions(self):
        registry=pd.read_csv(self.out/'tables/01_experiment_registry.csv')
        for row in registry.itertuples():
            columns=json.loads(row.columns);self.assertNotIn('RENDIMIENTO_T_HA',columns);self.assertNotIn(ID,columns)
            self.assertLessEqual(row.n_features,11)
        for protocol in self.pred.protocol.unique():
            subset=self.pred[self.pred.protocol.eq(protocol)]
            rep=int(subset.repeat.min());fold=int(subset.fold.min())
            for name in subset.experiment.unique():
                q=subset[subset.repeat.eq(rep)&subset.fold.eq(fold)&subset.experiment.eq(name)].set_index(ID)
                m=joblib.load(self.out/'models'/f'{protocol}_{rep:02d}_{fold:02d}_{name}.joblib')
                data=self.features.set_index(ID).loc[q.index].reset_index()
                actual=m.predict(data[['rain_total']] if name=='E0_MEAN' else data)
                np.testing.assert_allclose(actual,q.y_pred,atol=1e-12)
    def test_metrics_reproduction(self):
        table=pd.read_csv(self.out/'tables/06_repetition_metrics.csv')
        for row in table.itertuples():
            q=self.pred[self.pred.protocol.eq(row.protocol)&self.pred.experiment.eq(row.experiment)&self.pred.repeat.eq(row.repeat)]
            values=metrics(q.y_true,q.y_pred)
            for key,value in values.items():self.assertAlmostEqual(getattr(row,key),value,places=12)

if __name__=='__main__':unittest.main()
