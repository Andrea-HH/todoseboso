import numpy as np
import pandas as pd
import pytest
from src.nonclimatic_local import exclusion_reasons,fit_representation,MAY

def test_climate_and_may_exclusions_propagate_through_derivatives():
    records=[dict(column='rain',source='official_climate'),dict(column='slope',source='official_topography'),dict(column=MAY,source='sat_basic'),dict(column='interaction',inputs=['rain','slope']),dict(column='may_change',inputs=[MAY,'slope'])]
    a=exclusion_reasons(records);b=exclusion_reasons(records,mode='safe_with_climate')
    assert a['interaction'] and not b['interaction'] and not a['slope'];assert a['may_change'] and b['may_change']

def test_unknown_dependencies_are_not_silently_retained():
    with pytest.raises(ValueError):exclusion_reasons([dict(column='derived',inputs=['unknown'])])

def test_representation_uses_requested_X_columns_only():
    rng=np.random.default_rng(2026);x=pd.DataFrame(rng.normal(size=(40,25)),columns=[f'x{i}' for i in range(25)]);cols=list(x)
    x['RENDIMIENTO_T_HA']=np.arange(40);a,_=fit_representation(x,cols);x['RENDIMIENTO_T_HA']+=10000;b,_=fit_representation(x,cols)
    np.testing.assert_array_equal(a,b)
