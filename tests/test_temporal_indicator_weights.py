import numpy as np
import pandas as pd
from src.temporal_indicator_weights import positive_persistence,derive_indicators,FixedCorrection,ContinuousWeight,INDICATORS,PARENTS


def test_effective_persistence_distinguishes_one_spike_from_sustained_event():
    z=np.array([[1,1,1,1,1,1],[0,0,6,0,0,0],[0,0,0,0,0,0]],float)
    np.testing.assert_allclose(positive_persistence(z),[1,1/6,0])


def test_temporal_history_excludes_current_and_propagates_missing():
    a=np.ones((2,4,6))*.2;gap=a.copy();gap[:,3,:]=.4;evi=np.tile(np.arange(6)/10,(2,4,1));planet=evi[:,3,:].copy()
    values=derive_indicators(a,a,gap,a,evi,planet,np.ones(2));np.testing.assert_allclose(values[:,0],.2);np.testing.assert_allclose(values[:,2],4.);np.testing.assert_allclose(values[:,3],1.);np.testing.assert_allclose(values[:,7],0.,atol=1e-12)
    gap[0,0,2]=np.nan;assert np.isnan(derive_indicators(a,a,gap,a,evi,planet,np.ones(2))[0,3])


def test_weights_are_bounded_and_cannot_flip_a_correction():
    rng=np.random.default_rng(27);f=pd.DataFrame(rng.normal(size=(80,len(INDICATORS))),columns=INDICATORS);delta=rng.uniform(-.25,.25,80);r=delta*.7
    for kind in ['CONSTANT','SHARED','DIRECTIONAL']:
        m=ContinuousWeight(kind).fit(f,r,delta);med=m.median.copy();w=m.predict_weight(f*1000,delta)
        assert ((w>=0)&(w<=1)).all();assert (w*delta*delta>=0).all();assert (abs(w*delta)<=abs(delta)+1e-12).all();np.testing.assert_array_equal(m.median,med)
    zero=ContinuousWeight('SHARED').fit(f,r,np.zeros(80));np.testing.assert_array_equal(zero.predict_weight(f,delta),np.zeros(80))


def test_candidate_cap_and_sparse_direction_fallback():
    rng=np.random.default_rng(45);f=pd.DataFrame(rng.normal(size=(40,len(PARENTS))),columns=PARENTS);m=FixedCorrection(PARENTS).fit(f,10*f.P_tpi.to_numpy());assert max(abs(m.predict_delta(f*1000)))<=.25+1e-12
    g=pd.DataFrame(rng.normal(size=(40,len(INDICATORS))),columns=INDICATORS);w=ContinuousWeight('DIRECTIONAL').fit(g,np.ones(40),np.ones(40)*.1);assert 'negative_constant' in w.fallbacks
