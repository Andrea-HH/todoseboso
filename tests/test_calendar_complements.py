import numpy as np
import pandas as pd
from src.calendar_complements import Corrector,subcv,honest_residual

def test_centered_constant_residual_cannot_create_shift():
    x=pd.DataFrame({'a':np.arange(40,dtype=float)})
    for kind,params in [('ridge',{'alpha':.1}),('tree',{'max_depth':2,'min_samples_leaf':15})]:
        m=Corrector(['a'],kind,params).fit(x,np.full(40,5.))
        np.testing.assert_allclose(m.predict(x),0.,atol=1e-12)

def test_transform_is_training_only_and_predictions_centered():
    x=pd.DataFrame({'a':[1.,2.,3.,np.nan,5.]})
    m=Corrector(['a'],'ridge',{'alpha':.1}).fit(x,np.arange(5.))
    before=m.predict(x);mean=m.mean_.copy();med=m.medians_.copy()
    m.predict(pd.DataFrame({'a':[1e12,np.nan]}))
    np.testing.assert_array_equal(m.mean_,mean);np.testing.assert_array_equal(m.medians_,med)
    np.testing.assert_allclose(m.predict(x),before);assert abs(before.mean())<1e-12

def test_grouped_subcv_never_splits_groups():
    x=pd.DataFrame({'ID_POLIGONO':np.arange(12)})
    groups=pd.DataFrame({'municipality':np.repeat(['a','b','c'],4)},index=np.arange(12))
    for a,b in subcv(x,np.arange(12),'municipality',groups):
        assert not set(groups.iloc[a].municipality)&set(groups.iloc[b].municipality)

def test_residual_target_excluded_from_base_and_tuning(tmp_path):
    x=pd.DataFrame({'ID_POLIGONO':np.arange(32),'a':np.linspace(-1,1,32),'b':np.sin(np.arange(32))})
    groups=pd.DataFrame({'municipality':np.repeat(np.arange(4),8)},index=np.arange(32))
    y=2*x.a.to_numpy()+x.b.to_numpy();pos=np.arange(32)
    cfg={'representations':{'a':['a'],'ab':['a','b']},'en_grid':[{'alpha':.1,'l1_ratio':.5,'gamma':1.}]}
    cv=subcv(x,pos,'municipality',groups)
    first=tmp_path/'first';second=tmp_path/'second';first.mkdir();second.mkdir()
    r=honest_residual(x,y,pos,cv,'municipality',groups,cfg,first,[])
    held=cv[0][1];altered=y.copy();altered[held]+=10000
    s=honest_residual(x,altered,pos,cv,'municipality',groups,cfg,second,[])
    np.testing.assert_allclose((y-r)[held],(altered-s)[held],atol=1e-10)
