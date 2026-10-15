"""Scientific guards for G/H feature alignment, allowed inputs and nested fitting."""
from pathlib import Path
import sys,unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from family_1.climate_signal_features import *
from family_1.climate_signal_modeling import specifications,tune,COMPACT,partition_signature

class ClimateSignalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.long=load_longitudinal();cls.frame,cls.dictionary=build_features(cls.long)
    def test_complete_unique_finite_parcel_matrix(self):
        self.assertEqual(len(self.frame),197);self.assertTrue(self.frame[ID].is_unique)
        self.assertTrue(np.isfinite(self.frame.drop(columns=[ID,'CONJUNTO'])).all().all())
        self.assertEqual(len(self.dictionary),len(self.frame.columns)-2)
    def test_temporal_primitive_index_alignment(self):
        for pid in self.frame[ID].iloc[[0,90,196]]:
            z=self.long[self.long[ID].eq(pid)&self.long.year.eq(2025)&self.long.month.between(4,10)].sort_values('month')
            r=self.frame.set_index(ID).loc[pid]
            self.assertAlmostEqual(r.tmin_cycle_mean,z.tmin_mean.mean(),places=12)
            self.assertAlmostEqual(r.tmax_cycle_std,z.tmax_mean.std(ddof=1),places=12)
            t=(z.date_month-pd.Timestamp('2025-04-01')).dt.days
            self.assertAlmostEqual(r.tmin_cycle_slope_per_day,np.polyfit(t,z.tmin_mean,1)[0],places=12)
    def test_thermal_identities_and_inverse(self):
        a=self.frame[MIN].to_numpy();b=self.frame[MAX].to_numpy()
        mean=self.frame[THERMAL['tmean']].to_numpy();dtr=self.frame[THERMAL['dtr']].to_numpy()
        np.testing.assert_allclose(mean,(a+b)/2);np.testing.assert_allclose(dtr,b-a)
        np.testing.assert_allclose(mean-dtr/2,a);np.testing.assert_allclose(mean+dtr/2,b)
    def test_post_october_not_used_in_features(self):
        altered=self.long.copy();late=altered.year.eq(2025)&altered.month.gt(10)
        altered.loc[late,['tmin_mean','tmax_mean','tmean_mean','dtr_mean','precip_mean']]+=500
        f,_=build_features(altered);pd.testing.assert_frame_equal(f,self.frame)
    def test_short_reference_same_month_three_years(self):
        pid=self.frame[ID].iloc[100];z=self.long[self.long[ID].eq(pid)&self.long.month.eq(4)]
        expected=z.loc[z.year.eq(2025),'tmin_mean'].iloc[0]-z.loc[z.year.between(2022,2024),'tmin_mean'].mean()
        self.assertAlmostEqual(self.frame.set_index(ID).loc[pid,'tmin_anomaly_apr'],expected,places=12)
    def test_no_hidden_targets_even_if_filled(self):
        master=pd.read_csv(MASTER);master.loc[master.CONJUNTO.eq('PREDICCION'),TARGET]=999
        train=supervised_data(self.frame,master);self.assertEqual(len(train),138)
        self.assertFalse(train[TARGET].eq(999).any())
    def test_specifications_only_allowed_climate_inputs(self):
        original,cols=climate_current();specs=specifications(cols,[dict(name='Tmin_Tmax',k95=2)])
        for name,(section,features,kind) in specs.items():
            self.assertTrue(set(features)<=set(self.frame.columns)|set(cols))
            self.assertFalse(any(c in ['Estado','Municipio',ID,TARGET] or c.startswith(('TOPO','S2','PLANET')) for c in features))
            if section=='G':self.assertFalse(any(c in RAIN or 'precip' in c for c in features))
        self.assertEqual(len(specs['H7_JOINT'][1]),21);self.assertEqual(len(specs['H8_CLIMATE_CURRENT_ORIGINAL'][1]),48)
        self.assertEqual(len(COMPACT),12)
    def test_nested_scalers_never_fit_heldout(self):
        rng=np.random.default_rng(12);X=pd.DataFrame(rng.normal(size=(40,7)),columns=MIN);y=pd.Series(rng.normal(size=40))
        tr=np.arange(30);inner=list(KFold(3).split(tr));seen=[];original=StandardScaler.fit
        def spy(model,x,*args,**kwargs):
            seen.append(np.array(x));return original(model,x,*args,**kwargs)
        with patch.object(StandardScaler,'fit',spy):search=tune(X.iloc[tr],y.iloc[tr],inner,'enet')
        expected=[X.iloc[tr].to_numpy()]+[X.iloc[tr].iloc[a].to_numpy() for a,b in inner]
        for fitted in seen:self.assertTrue(any(fitted.shape==e.shape and np.allclose(fitted,e) for e in expected))
        self.assertEqual(search.best_estimator_.named_steps['scaler'].n_samples_seen_,30)
    def test_joint_profile_membership_not_just_equal_counts(self):
        a=np.array([1,1,2,2]);b=np.array([8,8,9,9]);c=np.array([1,2,1,2])
        self.assertEqual(partition_signature(a),partition_signature(b));self.assertNotEqual(partition_signature(a),partition_signature(c))
    def test_pcr_gate_independent_of_y(self):
        _,cols=climate_current()
        self.assertNotIn('G6_THERMAL_PCR',specifications(cols,[dict(name='Tmin_Tmax',k95=5)]))
        self.assertIn('G6_THERMAL_PCR',specifications(cols,[dict(name='Tmin_Tmax',k95=2)]))

if __name__=='__main__':unittest.main()
