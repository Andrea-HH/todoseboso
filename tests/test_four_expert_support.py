import numpy as np
import pandas as pd
from src.four_expert_combinations import SupportFeatures,local_sets

def test_support_uses_only_training_labels_and_excludes_self():
    rng=np.random.default_rng(12);cols=local_sets()['NO_PLANET'];values=rng.normal(size=(35,len(cols)));a={'features197':pd.DataFrame(values,columns=cols),'a':{'train_global':np.arange(35),'x':rng.normal(size=(35,20)),'distance':abs(np.arange(35)[:,None]-np.arange(35)[None,:]).astype(float)},'y':np.arange(35.)}
    tr=np.arange(30);q=np.arange(30,35);p=rng.normal(size=(5,4));s=SupportFeatures(a).fit(tr);z=s.transform(q,p);a['y'][q]=1e9;again=SupportFeatures(a).fit(tr).transform(q,p)
    for k in z:np.testing.assert_array_equal(z[k],again[k])
    assert np.all(z['B6'][:,-1]<30)
    self_z=s.transform(np.array([0]),p[:1]);assert self_z['B5'][0,-1]>0
