import numpy as np
import pandas as pd
from src.experimental_pls import TrainRepresentation,metrics

def test_representation_training_only_unknown_categories_and_missing():
    x=pd.DataFrame({'a':[1.,2.,3.],'dup':[1.,2.,3.],'empty':[np.nan]*3,'constant':[7]*3,'category':['a','b','a']})
    r=TrainRepresentation().fit(x)
    z=r.transform(pd.DataFrame({'a':[np.nan,100.],'dup':[np.nan,100.],'empty':[9,9],'constant':[8,8],'category':['new','a']}))
    assert np.isfinite(z).all()
    assert r.medians[0]==2
    assert not any(n in ['empty','constant'] for n in r.names)
    np.testing.assert_allclose(z[:,0],z[:,1])
    assert r.scaler.mean_[0]==2

def test_metric_bias_direction():
    assert metrics([2,4],[3,5])==dict(rmse=1.,mae=1.,bias=1.)
