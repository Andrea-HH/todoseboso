import numpy as np
import pandas as pd
from src.calendar_modeling import CalendarRidge

def test_imputation_and_scale_are_training_only_and_prediction_is_pure():
    t=pd.DataFrame({'x':[1.,np.nan,3.],'HIST_MEAN_h':[2.,4.,np.nan]})
    m=CalendarRidge(t.columns,['HIST_MEAN_h'],.1,.5,True).fit(t,[1.,2.,3.])
    before=m.medians_.copy();assert np.allclose(before,[2.,3.])
    p=m.predict(pd.DataFrame({'x':[1e9,np.nan],'HIST_MEAN_h':[np.nan,1e9]}))
    assert np.isfinite(p).all() and np.array_equal(before,m.medians_)
    assert len(m.feature_names_)==3

def test_lower_history_gamma_imposes_stronger_history_shrinkage():
    t=pd.DataFrame({'x':[-1.,-1.,1.,1.],'HIST_MEAN_h':[-1.,1.,-1.,1.]})
    y=t.x+t.HIST_MEAN_h
    a=CalendarRidge(t.columns,['HIST_MEAN_h'],1.,1.).fit(t,y)
    b=CalendarRidge(t.columns,['HIST_MEAN_h'],1.,.25).fit(t,y)
    assert np.ptp(b.predict(pd.DataFrame({'x':[0.,0.],'HIST_MEAN_h':[-1.,1.]}))) < np.ptp(a.predict(pd.DataFrame({'x':[0.,0.],'HIST_MEAN_h':[-1.,1.]})))
    assert b.effective_df_<a.effective_df_
