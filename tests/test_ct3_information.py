import numpy as np
import pandas as pd
from src.ct3_information.statistics import variance_parts,category_contrasts,residual_projection,cross_projection,partial_correlation,pair_association,spectral_summary

def test_variance_decomposition_and_singletons():
    r=variance_parts([1,3,7,9,20],[0,0,1,1,2])
    np.testing.assert_allclose(r['total_ss'],r['within_ss']+r['between_ss'])
    assert r['contrasting_profiles']==2 and r['contrast_parcels']==4

def test_categories_are_not_ordinals_and_missing_is_omitted():
    a=category_contrasts(['A','B','B',None],[0,0,0,1]);b=category_contrasts(['Z','W','W',None],[0,0,0,1])
    assert a==b and a['n']==3 and a['contrasting_profiles']==1
    assert abs(a['discordance_pair_weighted']-2/3)<1e-12

def test_projection_exact_redundancy_and_train_only():
    x=np.arange(12.).reshape(6,2);z=3+x[:,0]*2
    np.testing.assert_allclose(residual_projection(x,z),0,atol=1e-12)
    r=cross_projection(x,z,np.array([[100.,101.]]),np.array([203.]))
    np.testing.assert_allclose(r,0,atol=1e-10)
    changed=cross_projection(x,z,np.array([[100.,101.]]),np.array([999.]))
    np.testing.assert_allclose(changed-r,796)

def test_partial_is_not_uncontrolled_correlation():
    rng=np.random.default_rng(3);c=rng.normal(size=(100,1));z=2*c[:,0]+rng.normal(size=100);y=4*c[:,0]+rng.normal(size=100)
    assert abs(partial_correlation(y,z,c))<.25

def test_pairs_require_same_external_model_and_do_not_expand_sample_size():
    d=pd.DataFrame({'z':[1.,3.,9.,11.],'y':[2.,6.,18.,22.],'ndvi':[0.,0.,0.,0.],'g':[1,1,1,1],'fold':[1,1,2,2]})
    r=pair_association(d,'z','y','ndvi','g','fold')
    assert r['n_pairs']==2 and r['n_parcels']==4 and r['n_profiles']==1

def test_spectral_duplicate_columns_do_not_add_rank():
    a=np.array([[-1.,-1.],[0,0],[1,1]])
    r,_,_=spectral_summary(a)
    assert r['rank']==1 and abs(r['effective_rank']-1)<1e-12
