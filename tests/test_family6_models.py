import numpy as np
import pandas as pd
from src.family_6.models import TreeModel,GRID,N_TREES
from src.family_6.execution import CORE

def sample():
    rng=np.random.default_rng(22);x=pd.DataFrame(rng.normal(size=(48,4)),columns=CORE);y=3+.4*x.iloc[:,0]+.5*(x.iloc[:,3]>.2)+rng.normal(0,.1,48)
    return x,np.asarray(y)

def test_train_only_preprocessing_and_forest_range():
    x,y=sample();x.iloc[0,0]=np.nan;m=TreeModel(CORE,'RF',GRID[0]).fit(x,y)
    np.testing.assert_allclose(m.preprocess_.median_,x.median().to_numpy())
    before=m.preprocess_.mean_.copy();pred=m.predict(x*100)
    np.testing.assert_array_equal(before,m.preprocess_.mean_)
    assert pred.min()>=y.min()-1e-12 and pred.max()<=y.max()+1e-12

def test_bootstrap_and_extra_tree_regimes():
    x,y=sample();rf=TreeModel(CORE,'RF',GRID[1]).fit(x,y);et=TreeModel(CORE,'ET',GRID[1]).fit(x,y)
    assert rf.forest_.bootstrap and not et.forest_.bootstrap
    assert rf.parameters()['mean_unique_sample_count']<len(x)
    assert rf.parameters()['mean_bootstrap_draws']==round(.8*len(x))
    assert et.parameters()['mean_unique_sample_count']==len(x)
    for m in [rf,et]:
        assert len(m.forest_.estimators_)==N_TREES
        assert m.forest_.min_samples_leaf>=5

def test_identical_vectors_prefixes_and_reproducibility():
    x,y=sample();a=TreeModel(CORE,'ET',GRID[0]).fit(x,y);b=TreeModel(CORE,'ET',GRID[0]).fit(x,y)
    np.testing.assert_array_equal(a.predict(x),b.predict(x))
    p=a.predict(x.iloc[[0,0]]);assert p[0]==p[1]
    np.testing.assert_allclose(a.prefix_predictions(x)[384],a.predict(x),atol=1e-12)
    assert len(GRID)==8
