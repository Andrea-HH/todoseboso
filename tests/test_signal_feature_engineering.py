import numpy as np
import pandas as pd
from src.signal_feature_engineering import historical_z,temporal_summaries,EngineeringAdjustment


def test_history_floor_missing_and_reference():
    z=historical_z(np.array([.3,.2,np.nan]),np.array([.1,.2,.1]),np.array([0.,.1,.1]))
    np.testing.assert_allclose(z[:2],[6.,0.]);assert np.isnan(z[2])


def test_temporal_persistence_timing_and_missing_month():
    evi=np.tile(np.arange(7)/10,(3,1));ndvi=np.ones((3,7));gap=np.array([[0,1,1,1,1,1,1],[0,0,0,1,0,0,0],[0,0,0,0,0,0,0]],float)
    z=temporal_summaries(evi,ndvi,gap)
    np.testing.assert_allclose(z[:2,0],[.2,.2]);np.testing.assert_allclose(z[:2,5],[1,1/6]);np.testing.assert_allclose(z[:2,4],[0,.4]);assert np.isnan(z[2,4]) and z[2,5]==0
    gap[0,3]=np.nan;assert np.isnan(temporal_summaries(evi,ndvi,gap)[0,5])


def test_training_only_interactions_null_and_bounded_replay():
    rng=np.random.default_rng(14);f=pd.DataFrame(rng.normal(size=(60,4)),columns=['a','b','c','d']);f.loc[0,'a']=np.nan
    y=4.+f['c'].to_numpy()*.3;base=np.full(60,4.)
    m=EngineeringAdjustment('P_ENG',list(f),alpha=.001,l1_ratio=.1,amplitude=1.).fit(f,y,base)
    med=m.medians.copy();scale=m.scale.copy();query=f.copy()*1000;query.loc[:,'a']=np.nan;p=m.predict(query,base)
    assert np.isfinite(p).all() and max(abs(p-base))<=.5+1e-12
    np.testing.assert_array_equal(m.medians,med);np.testing.assert_array_equal(m.scale,scale)
    assert len(m.feature_names)==8
    null=EngineeringAdjustment('P_ENG',list(f),amplitude=0.).fit(f,y,base);np.testing.assert_array_equal(null.predict(query,base),base)


def test_shift_control_and_constant_features():
    f=pd.DataFrame(index=range(10));base=np.full(10,4.);y=base+.2
    m=EngineeringAdjustment('SHIFT',[],amplitude=.5).fit(f,y,base)
    np.testing.assert_allclose(m.predict(f,base),4.1)
