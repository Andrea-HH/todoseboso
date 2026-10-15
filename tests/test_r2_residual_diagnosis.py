import numpy as np
from src.r2_residual_diagnosis import stability,omissions

def test_cluster_resampling_keeps_profile_units_and_is_deterministic():
    v=np.array([-1.,-1.,1.,1.]);g=np.array([0,0,1,1])
    a=stability(v,g,n_boot=1000);b=stability(v,g,n_boot=1000)
    assert a==b and a['profile_low']==-1 and a['profile_high']==1

def test_omissions_are_descriptive_and_do_not_mutate_residuals():
    values=np.array([-4.,1.,1.,1.,1.,1.]);copy=values.copy()
    rows=omissions(values,np.array([0,1,1,2,2,3]))
    first=next(r for r in rows if r['omission']=='largest_absolute' and r['k']==1)
    assert first['remaining_residual_mean']==1 and first['n_remaining']==5
    np.testing.assert_array_equal(values,copy)
