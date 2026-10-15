import numpy as np
import pandas as pd
from src.calendar_expansion import BlockEstimator

def test_elasticnet_can_remove_orthogonal_history_and_null_gamma_is_exact():
    x=pd.DataFrame({'x':[-1.,-1.,1.,1.]*4,'HIST_MEAN_h':[-1.,1.,-1.,1.]*4})
    params=dict(alpha=.1,l1_ratio=1.,gamma=0.)
    m=BlockEstimator(list(x),['HIST_MEAN_h'],False,'EN',params).fit(x,x.x,audit=True)
    assert m.used_.tolist()==[True,False]
    p=m.predict(x);b=x.copy();b.HIST_MEAN_h=1e8
    np.testing.assert_allclose(p,m.predict(b))

def test_cb_uses_actual_split_counts_and_historical_priority_without_target_leak():
    x=pd.DataFrame({'x':np.arange(16.),'HIST_MEAN_h':[np.nan,1.,2.,3.]*4})
    m=BlockEstimator(list(x),['HIST_MEAN_h'],True,'CB',dict(iterations=4,depth=2,learning_rate=.03,l2_leaf_reg=10)).fit(x,x.x,audit=True)
    weights=m.model_.get_all_params()['feature_weights']
    assert weights.get('0',1)==1 and weights['1']==.5 and weights['2']==.5
    assert m.split_counts_.sum()>0 and len(m.names_)==3
    median=m.medians_.copy();assert np.isfinite(m.predict(x.iloc[:2])).all()
    np.testing.assert_array_equal(median,m.medians_)
