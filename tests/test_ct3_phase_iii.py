import numpy as np
import pandas as pd
import pytest
from src.ct3_information.phase_iii.representations import NumericRepresentation,angles,evaluate

def sample():
    rng=np.random.default_rng(22);x=pd.DataFrame(rng.normal(size=(30,6)),columns=list('abcdef'));core=pd.DataFrame(rng.normal(size=(30,4)));g=np.repeat(np.arange(10),3)
    return x,core,g

def test_no_target_and_no_y_interface():
    x,c,g=sample();x['RENDIMIENTO_T_HA']=0
    with pytest.raises(ValueError):NumericRepresentation().fit(x,c,g)

def test_transform_does_not_refit_on_validation():
    x,c,g=sample();r=NumericRepresentation(mode='ct3_residual',k=2).fit(x.iloc[:20],c.iloc[:20],g[:20]);mean=r.location.copy();beta=r.beta.copy()
    v=x.iloc[20:].copy();v.iloc[0,0]=np.nan;r.transform(v,c.iloc[20:],g[20:]);v.iloc[1,1]=10000;r.transform(v,c.iloc[20:],g[20:]);np.testing.assert_array_equal(r.location,mean);np.testing.assert_array_equal(r.beta,beta)

def test_within_unseen_profile_uses_training_reference_only():
    x,c,g=sample();r=NumericRepresentation(mode='within',k=2).fit(x.iloc[:20],c.iloc[:20],g[:20]);v=r.transform(x.iloc[20:],c.iloc[20:],np.repeat(999,10));assert np.isfinite(v).all();assert 999 not in r.profile_means

def test_angles_invariant_to_sign_and_order():
    a=np.eye(5)[:,:3];b=a[:,[2,0,1]]*[-1,1,-1];assert abs(angles(a,b,3)['overlap']-1)<1e-12

def test_original_keeps_redundant_named_indicators_and_reconstruction():
    x,c,g=sample();x['b']=x.a;r=NumericRepresentation(kind='original').fit(x,c,g);assert r.retained==6
    m,_=evaluate(r,x,c,g,[0,1],np.repeat('outside',30));assert abs(m['within_reconstruction_fraction']-1)<1e-10

def test_hierarchy_and_constancy_under_profile_centering():
    x,c,g=sample();x['a']=g;groups=[('S2','index1'),('S2','index1'),('S2','index2'),('P','index1'),('P','index1'),('P','index1')]
    r=NumericRepresentation(kind='hierarchical',mode='within',k=2,hierarchical_groups=groups).fit(x,c,g);assert np.max(abs(r.transformed_input(x,c,g)[:,0]))<1e-12;assert np.isfinite(r.transform(x,c,g)).all()
