import numpy as np
from src.architecture_decomposition import local_sets,GeologySpace

def test_partitions_and_minimal_combinations():
    s=local_sets();full=set(s['FULL7']);assert len(full)==7
    assert [len(s[k]) for k in ['NO_HISTORY','NO_PLANET','NO_NDWI','NO_SLOPE']]==[5,5,5,6]
    assert all(set(v)<=full for v in s.values())
    assert all(len(s[k])==3 for k in ['HISTORY_SLOPE','PLANET_SLOPE','NDWI_SLOPE'])

def test_global_gate_needs_no_geological_fields():
    import pandas as pd
    f=pd.DataFrame({'anything':[1,2,3]});m=GeologySpace('GLOBAL',{}).fit(f);np.testing.assert_array_equal(m.transform(f),np.zeros((3,1)))

def test_reused_target_free_clusters_equal_independent_gate_fits():
    from src.architecture_decomposition import DecompositionFactory
    from src.conditional_local_phases import ExpertGate
    rng=np.random.default_rng(49);z=rng.normal(size=(35,4));y=rng.normal(size=35);ct=rng.normal(size=35);ep=rng.normal(size=35);f=DecompositionFactory.__new__(DecompositionFactory);f.gate_templates={};f.gate('same_geometry',z,y,ct,ep,4);ep2=ep*.7
    actual=f.gate('same_geometry',z,y,ct,ep2,4);expected=ExpertGate('clusters',4).fit(z,y,ct,ep2);np.testing.assert_allclose(actual.predict(z,ct,ep2),expected.predict(z,ct,ep2),atol=1e-12,rtol=0)
