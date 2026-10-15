import numpy as np
import pandas as pd
from src.geoc_reverse import local_residuals,evaluate
from src.ct3_residual_conditional.models import CORE
from sklearn.model_selection import KFold

def fixture():
    rng=np.random.default_rng(2026);n=40
    t=pd.DataFrame(rng.normal(size=(n,4)),columns=CORE);t['ID_POLIGONO']=np.arange(n);t['RENDIMIENTO_T_HA']=rng.normal(4,.5,n)
    return dict(train=t,x=rng.normal(size=(n,20)),distance=abs(np.arange(n)[:,None]-np.arange(n)[None,:]).astype(float),train_global=np.arange(n))

def test_local_residual_is_honest_for_held_label():
    a=fixture();tr=np.arange(32);cv=list(KFold(4,shuffle=True,random_state=2026).split(tr));y=a['train'].RENDIMIENTO_T_HA.to_numpy().copy()
    r=local_residuals(a,tr,cv);held=tr[cv[0][1]];a['train'].loc[held,'RENDIMIENTO_T_HA']+=10000
    s=local_residuals(a,tr,cv);np.testing.assert_allclose((y[tr]-r)[cv[0][1]],(a['train'].RENDIMIENTO_T_HA.to_numpy()[tr]-s)[cv[0][1]],atol=1e-10)

def test_external_labels_do_not_affect_selection_or_predictions():
    a=fixture();tr=np.arange(32);va=np.arange(32,40);inner=list(KFold(4,shuffle=True,random_state=2026).split(tr));groups=pd.DataFrame(index=np.arange(40))
    p=evaluate(a,tr,va,inner,'random',groups);a['train'].loc[va,'RENDIMIENTO_T_HA']+=10000
    q=evaluate(a,tr,va,inner,'random',groups)
    assert p['selection']==q['selection'];np.testing.assert_allclose(p['prediction'],q['prediction'],atol=0,rtol=0)
