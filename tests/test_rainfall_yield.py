"""Mathematical and leakage contracts for rainfall-only modeling."""
import sys
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from family_1.rainfall_features import build_features, longest_streak, merge_rainfall, ID
from family_1.rainfall_modeling import supervised_data, fit_experiment, preprocessor, profile_groups, experiments

def climate(values=None):
    values = values if values is not None else [10,20,30,40,30,20,10]
    return pd.DataFrame([{ID:'A','year':y,'month':m,'precip_mean':values[m-4] if y==2025 and 4<=m<=10 else 10.}
                         for y in range(2022,2026) for m in range(1,13)])

def feature(d): return build_features(d)[0].iloc[0]

class RainfallTests(unittest.TestCase):
    def test_totals_stages(self):
        f=feature(climate());self.assertEqual(f.rain_total,160);self.assertEqual(f.rain_early,30)
        self.assertEqual(f.rain_middle,100);self.assertEqual(f.rain_late,30)
        self.assertAlmostEqual(f.rain_mean,160/7);self.assertAlmostEqual(f.rain_std,np.std([10,20,30,40,30,20,10],ddof=1))
    def test_anomalies(self):
        f=feature(climate());self.assertEqual(f.rain_anomaly_may,10)
        self.assertEqual(f.rain_relative_anomaly_may,1);self.assertEqual(f.rain_anomaly_total,90)
    def test_anomaly_streaks_and_deficit_tie(self):
        f=feature(climate([5,4,10,20,25,10,3]))
        self.assertEqual(f.rain_anomaly_below_count,3);self.assertEqual(f.rain_anomaly_above_count,2)
        self.assertEqual(f.rain_anomaly_negative_streak,2);self.assertEqual(f.rain_anomaly_positive_streak,2)
        self.assertEqual(f.rain_anomaly_largest_deficit,7);self.assertEqual(f.rain_anomaly_largest_excess,15)
        self.assertEqual(f.rain_anomaly_deficit_month,10)
        self.assertEqual(feature(climate([5,5,10,20,20,10,10])).rain_anomaly_deficit_month,4)
    def test_future_climate_not_used(self):
        d=climate();original=build_features(d)[0]
        d.loc[d.year.eq(2025)&d.month.isin([11,12]),'precip_mean']=1e9
        future=d[d.year.eq(2025)].copy();future['year']=2026;future['precip_mean']=1e10
        pd.testing.assert_frame_equal(original,build_features(pd.concat([d,future]))[0])
    def test_differences_and_streaks(self):
        f=feature(climate());self.assertEqual(f.rain_largest_increase,10);self.assertEqual(f.rain_largest_decrease,10)
        self.assertEqual(f.rain_increase_count,3);self.assertEqual(f.rain_decrease_count,3)
        self.assertEqual(f.rain_longest_increase_streak,3);self.assertEqual(f.rain_longest_decrease_streak,3)
        self.assertEqual(f.rain_net_change,0);self.assertEqual(f.rain_mean_absolute_change,10)
    def test_ties_and_zero_breaks(self):
        f=feature(climate([10,20,20,30,10,10,10]));self.assertEqual(f.rain_max_month,7);self.assertEqual(f.rain_min_month,4)
        self.assertEqual(f.rain_longest_increase_streak,1)
        f=feature(climate([20]*7));self.assertEqual(f.rain_max_month,4);self.assertEqual(f.rain_min_month,4)
    def test_tolerance(self):
        f=feature(climate([10,10+1e-7,11,12,12,12,12]));self.assertEqual(f.rain_increase_count,2)
        self.assertEqual(f.rain_longest_increase_streak,2);self.assertEqual(longest_streak([True,False,True,True]),2)
    def test_zero_reference(self):
        d=climate([0]*7);d.precip_mean=0;f=feature(d)
        self.assertTrue(np.isnan(f.rain_cv));self.assertTrue(np.isnan(f.rain_max_share))
        self.assertTrue(np.isnan(f.rain_relative_anomaly_apr));self.assertTrue(np.isnan(f.rain_anomaly_total_relative))
        self.assertEqual(f.rain_total,0);self.assertTrue(np.isnan(f.rain_anomaly_deficit_month))
    def test_short_reference_policy(self):
        d=climate();d.loc[d.year.lt(2025),'precip_mean']=.5;f=feature(d)
        self.assertTrue(np.isnan(f.rain_relative_anomaly_apr));self.assertEqual(f.rain_anomaly_apr,9.5)
    def test_missing_windows(self):
        d=climate();d.loc[d.year.eq(2025)&d.month.eq(6),'precip_mean']=np.nan;f=feature(d)
        self.assertTrue(np.isnan(f.rain_total));self.assertTrue(np.isnan(f.rain_longest_increase_streak))
        self.assertEqual(f.rain_early,30);self.assertTrue(np.isnan(f.rain_middle));self.assertEqual(f.rain_net_change,0)
        d=climate();d=d[~(d.year.eq(2023)&d.month.eq(4))];f=feature(d)
        self.assertTrue(np.isnan(f.rain_hist_apr));self.assertTrue(np.isnan(f.rain_anomaly_total))
        self.assertEqual(f.rain_anomaly_may,10)
    def test_duplicates_and_negative(self):
        d=climate()
        with self.assertRaises(ValueError):build_features(pd.concat([d,d.iloc[:1]]))
        d.loc[0,'precip_mean']=-1
        with self.assertRaises(ValueError):build_features(d)
    def test_target_independence(self):
        d=climate();f,_=build_features(d);d['RENDIMIENTO_T_HA']=999
        pd.testing.assert_frame_equal(f,build_features(d)[0])
        features=pd.DataFrame({ID:['A','B'],'rain_total':[10,20]})
        m=pd.DataFrame({ID:['A','B'],'CONJUNTO':['ENTRENAMIENTO','PREDICCION'],'RENDIMIENTO_T_HA':[3,999]})
        self.assertEqual(supervised_data(features,m)[ID].tolist(),['A'])
        m.loc[1,'RENDIMIENTO_T_HA']=-999
        self.assertEqual(supervised_data(features,m).RENDIMIENTO_T_HA.tolist(),[3])
    def test_dictionary_and_merge(self):
        f,dd=build_features(climate());self.assertEqual(set(f.columns)-{ID},set(dd.feature_name))
        merged=merge_rainfall(pd.DataFrame({ID:['A'],'other':[3]}),f);self.assertEqual(len(merged),1)
        with self.assertRaises(ValueError):merge_rainfall(f,f)
        f['CONJUNTO']='ENTRENAMIENTO'
        self.assertEqual(merge_rainfall(pd.DataFrame({ID:['A'],'CONJUNTO':['ENTRENAMIENTO']}),f).CONJUNTO.tolist(),['ENTRENAMIENTO'])
    def test_preprocessing_is_train_only_and_month_categories(self):
        x=pd.DataFrame({'rain_total':[1.,2.,3.,np.nan],'rain_max_month':[4,5,6,4]})
        prep=preprocessor(list(x));prep.fit(x)
        self.assertEqual(prep.named_transformers_['numeric'].named_steps['imputer'].statistics_[0],2)
        prep.transform(pd.DataFrame({'rain_total':[1e9],'rain_max_month':[10]}))
        self.assertEqual(prep.named_transformers_['numeric'].named_steps['imputer'].statistics_[0],2)
        self.assertIn('rain_max_month_10',prep.get_feature_names_out())
    def test_reproducible_tuning_and_grouping(self):
        x=pd.DataFrame({'rain_total':np.arange(24,dtype=float)});y=2*x.rain_total+np.sin(x.rain_total)
        inner=list(KFold(4,shuffle=True,random_state=2026).split(x))
        spec={'kind':'ridge','columns':['rain_total']}
        a,pa,_=fit_experiment(spec,x,y,inner);b,pb,_=fit_experiment(spec,x,y,inner)
        self.assertEqual(pa,pb);np.testing.assert_allclose(a.predict(x),b.predict(x))
        d=climate();copy=d.copy();copy[ID]='B';both=pd.concat([d,copy])
        groups=profile_groups(both,['A','B']);self.assertEqual(groups[0],groups[1])
    def test_combination_registry_excludes_dropped_columns(self):
        spec=experiments()['E7_NESTED_COMBINED'];rng=np.random.default_rng(2026)
        x=pd.DataFrame(rng.normal(size=(24,len(spec['columns']))),columns=spec['columns'])
        x['RENDIMIENTO_T_HA']=999;inner=list(KFold(4,shuffle=True,random_state=2026).split(x))
        m,params,selected=fit_experiment(spec,x,x.rain_total,inner)
        self.assertNotIn('RENDIMIENTO_T_HA',selected)
        self.assertLessEqual(len(selected),11);self.assertEqual(selected,params['columns'])
        self.assertNotIn('RENDIMIENTO_T_HA',m.feature_names_in_)
    def test_baseline_uses_only_training_y_mean(self):
        x=pd.DataFrame({'rain_total':[100,200,300]});y=np.array([1.,2.,6.])
        model,_,cols=fit_experiment(experiments()['E0_MEAN'],x,y,[])
        self.assertEqual(cols,[]);np.testing.assert_allclose(model.predict(np.zeros((2,1))),[3,3])

if __name__=='__main__':unittest.main()
