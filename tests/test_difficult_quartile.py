import numpy as np
from src.difficult_quartile import effect,conditional_effect,labels_for_errors,DiagnosticClassifier,family


def test_physical_pool_excludes_temporal_slopes():
    assert family('S2_ndvi_promedio_slope')!='Relieve/topografía'
    assert family('S2_msi_derived_cv_slope')!='Relieve/topografía'
    assert family('TOPO_BASIC_slope_mean')=='Relieve/topografía'


def test_effect_direction_ties_and_conditional_confounding():
    a=np.array([[2.,1],[3.,1]]);b=np.array([[0.,1],[1.,1]]);d,_,_,_=effect(a,b);np.testing.assert_allclose(d,[1.,0.])
    x=np.array([[0.],[0.],[0.],[0.],[10.],[10.],[10.],[10.]])
    aa=np.array([1,1,0,0,1,1,0,0],bool);delta,eq,n=conditional_effect(x,aa,~aa,np.array([0]*4+[1]*4));np.testing.assert_allclose(delta,0);np.testing.assert_allclose(eq,0);assert n[0]==2


def test_hard_sign_labels_have_no_target_predictor():
    np.testing.assert_array_equal(labels_for_errors(np.array([-.6,.6,.1]),.5),[2,1,0])


def test_classifier_train_only_selection_and_constant_fallback():
    rng=np.random.default_rng(7);x=rng.normal(size=(70,10));y=np.tile([0,1,2,0,0,1,2],10);x[:,1]=x[:,0];x[0,2]=np.nan
    m=DiagnosticClassifier(4).fit(x,y);median=m.median.copy();selected=m.selected.copy();p=m.predict_proba(x*1000)
    assert p.shape==(70,3);np.testing.assert_allclose(p.sum(axis=1),1);np.testing.assert_array_equal(m.median,median);np.testing.assert_array_equal(m.selected,selected);assert not (0 in selected and 1 in selected)
    fallback=DiagnosticClassifier().fit(np.ones((70,3)),y);assert fallback.model is None
