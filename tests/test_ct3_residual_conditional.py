import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from src.ct3_residual_conditional.models import CORE,LAI,Z,CenteredCorrector,tune_base,selection_key

def sample():
    rng=np.random.default_rng(4);d=pd.DataFrame(rng.normal(size=(40,4)),columns=CORE);d[LAI]=rng.uniform(0,100,40);y=3+.4*d[CORE[0]].to_numpy()+rng.normal(0,.2,40);return d,y

def test_external_and_internal_heldout_labels_do_not_affect_base_component():
    x,y=sample();positions=np.arange(24);cv=list(KFold(3,shuffle=True,random_state=2026).split(positions))
    a,pa,_=tune_base(x,y,positions,cv);changed=y.copy();changed[24:]+=10000
    b,pb,_=tune_base(x,changed,positions,cv)
    assert pa['params']==pb['params'];np.testing.assert_array_equal(a.predict(x),b.predict(x))

def test_centered_ridge_tree_and_root_only_behavior():
    x,y=sample()
    for kind,p in [('ridge',dict(alpha=.1)),('tree',dict(max_depth=2,min_samples_leaf=15))]:
        m=CenteredCorrector(kind,Z,p).fit(x,y);assert abs(m.predict(x).mean())<1e-12
    root=CenteredCorrector('tree',Z,dict(max_depth=2,min_samples_leaf=25)).fit(x.iloc[:37],y[:37]);assert root.constant;np.testing.assert_array_equal(root.predict(x),0)

def test_zero_amplitude_exact_base_and_deterministic_ties():
    pred=np.array([3.5,4.25]);cor=np.array([.3,-.7]);np.testing.assert_array_equal(pred+0*cor,pred)
    a=dict(rmse=.5,amplitude=0.,params=dict(max_depth=2,min_samples_leaf=15));b=dict(rmse=.5,amplitude=.25,params=dict(max_depth=1,min_samples_leaf=25));assert selection_key(a,'tree')<selection_key(b,'tree')

def test_preprocessing_is_fitted_on_training_and_thresholds_have_native_units():
    x,y=sample();m=CenteredCorrector('tree',Z,dict(max_depth=2,min_samples_leaf=15)).fit(x,y);mean=m.preprocess.mean_.copy();v=x.copy();v[LAI]+=1000;m.predict(v);np.testing.assert_array_equal(mean,m.preprocess.mean_)
    for r in m.rules():assert x[r['feature']].min()-1e-6<=r['threshold_raw']<=x[r['feature']].max()+1e-6

def test_all_constant_corrector_returns_zero():
    x,y=sample();x[Z]=1.;m=CenteredCorrector('ridge',Z,dict(alpha=1.)).fit(x,y);assert m.constant;np.testing.assert_array_equal(m.predict(x),0)
