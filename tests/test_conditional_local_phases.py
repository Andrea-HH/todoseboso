import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.model_selection import KFold
from src.conditional_local_phases import ExpertGate,global_weight,LeaderFactory,predict_leader
from src.ct3_residual_conditional.models import CORE


def assets():
    rng=np.random.default_rng(2026);x=rng.normal(size=(36,4));ids=[f'p{i}' for i in range(36)];t=pd.DataFrame({'ID_POLIGONO':ids});d=cdist(x[:,:2],x[:,:2])
    return dict(y=2+x[:,0]+rng.normal(scale=.2,size=36),scores=x,geo=d,features=pd.DataFrame(index=range(36)),core=pd.DataFrame(x,columns=CORE),definitions={},a=dict(train=t,x=x,distance=d,train_global=np.arange(36))),pd.DataFrame({'spatial':np.repeat([0,1],18)},index=ids)


def test_gate_is_convex_and_identical_experts_choose_ct3():
    z=np.arange(20.)[:,None];ct=np.ones(20);leader=np.ones(20)*2;y=np.ones(20)*1.4
    assert abs(global_weight(y,ct,leader)-.4)<1e-12
    for kind,p in [('global',0),('clusters',4),('support',3)]:
        m=ExpertGate(kind,p).fit(z,y,ct,leader);pred=m.predict(np.array([[0.],[1000.]]),np.ones(2),np.ones(2)*2)
        assert np.all((pred>=1)&(pred<=2))
    assert global_weight(y,ct,ct)==0.


def test_entire_tuned_pipeline_does_not_use_external_labels(tmp_path):
    a,g=assets();tr=np.arange(30);va=np.arange(30,36);cv=list(KFold(3,shuffle=True,random_state=2026).split(tr))
    f=LeaderFactory(a,'random',g,tmp_path/'a');p=f.fit(tr,'GEOGRAPHY',12,cv);before=predict_leader(p,va,a)
    b={**a,'y':a['y'].copy()};b['y'][va]+=10000
    h=LeaderFactory(b,'random',g,tmp_path/'b');q=h.fit(tr,'GEOGRAPHY',12,cv)
    np.testing.assert_array_equal(before,predict_leader(q,va,b))
    assert all(not set(e['train'])&set(va) for e in f.ledger)


def test_insufficient_group_depth_retires_compact_corrector(tmp_path):
    a,g=assets();f=LeaderFactory(a,'spatial',g,tmp_path);p=f.fit(np.arange(36),'GEOGRAPHY',24)
    assert p['amplitude']==0. and p['fallback']
