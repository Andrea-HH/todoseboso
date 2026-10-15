import numpy as np
import pandas as pd
import pytest
from src.physical_representation import PhysicalRepresentation


def test_unseen_composition_class_is_bounded_and_not_variance_scaled():
    a=pd.DataFrame({'a':[1.,1.,1.,1.],'b':[0.,0.,0.,0.]})
    q=pd.DataFrame({'a':[0.],'b':[1.]})
    for mode in ['raw','summary','pca1']:
        m=PhysicalRepresentation(['a','b'],['a','b'],True,mode,1).fit(a)
        assert np.linalg.norm(m.transform(q))<=np.sqrt(2)+1e-12
        np.testing.assert_allclose(m.transform(a),0.)


def test_pca_dimension_and_external_data_do_not_change_training_transform():
    a=pd.DataFrame(np.random.default_rng(4).normal(size=(20,9)),columns=list('abcdefghi'))
    m=PhysicalRepresentation(list(a),list(a)[:2],False,'pca3',3).fit(a)
    z=m.transform(a);assert z.shape==(20,3)
    m.transform(a*1000)
    np.testing.assert_array_equal(z,m.transform(a.assign(RENDIMIENTO_T_HA=9999)))
    with pytest.raises(ValueError):PhysicalRepresentation(['RENDIMIENTO_T_HA'],[],False).fit(a.assign(RENDIMIENTO_T_HA=2))


def test_summary_uses_only_prespecified_features_and_unknown_category_is_safe():
    a=pd.DataFrame({'a':[1.,2.,3.,4.],'b':['x','y','x','y'],'ignored':[7.,8.,9.,10.]})
    m=PhysicalRepresentation(list(a),['a','b'],False,'summary').fit(a)
    p=m.transform(a);q=a.copy();q['ignored']=1e10
    np.testing.assert_array_equal(p,m.transform(q))
    assert np.isfinite(m.transform(pd.DataFrame({'a':[np.nan],'b':['unseen'],'ignored':[0.]}))).all()
