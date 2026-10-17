import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.model_selection import KFold
from src.geoc_signal_research import SignalRepresentation,SignalFactory,predict_expert,predict_base,CategoryCorrection,CategoryGate


def test_reduced_tuned_pipeline_ignores_external_targets(tmp_path):
    rng=np.random.default_rng(2026);x=rng.normal(size=(36,5));y=3+x[:,0];ids=[str(i) for i in range(36)];frame=pd.DataFrame(x,columns=list('abcde'));core=pd.DataFrame(x[:,:4],columns=['compact_precip_total','compact_early_fraction','compact_concentration_hhi','S2_ndvi_month_05']);a=dict(train=pd.DataFrame({'ID_POLIGONO':ids}),train_global=np.arange(36),distance=cdist(x[:,:2],x[:,:2]))
    assets=dict(a=a,y=y,features197=frame,core=core,static={'FULL':x},variants={'RED':dict(type='small',columns=list(frame),mode='pca3')});tr=np.arange(30);va=np.arange(30,36);cv=list(KFold(3,shuffle=True,random_state=2026).split(tr));groups=pd.DataFrame(index=ids)
    f=SignalFactory(assets,'random',groups,tmp_path/'a',tmp_path/'no-old');p=f.fit(tr,'RED',cv);prediction=predict_expert(p,va,assets)
    changed={**assets,'y':y.copy()};changed['y'][va]+=10000;g=SignalFactory(changed,'random',groups,tmp_path/'b',tmp_path/'no-old');q=g.fit(tr,'RED',cv);np.testing.assert_array_equal(prediction,predict_expert(q,va,changed));assert all(not set(r['train'])&set(va) for r in f.ledger)


def test_category_unseen_fallback_is_global_or_zero():
    c=np.array(['a']*10+['b']*10);y=np.r_[np.ones(10)*2,np.ones(10)*3];ct=np.ones(20);expert=np.ones(20)*4
    gate=CategoryGate().fit(c,y,ct,expert);assert gate.weights(np.array(['unseen']))[0]==gate.global_
    correction=CategoryCorrection().fit(c,y-ct);assert correction.predict(np.array(['unseen']))[0]==0.
    assert abs(correction.predict(c).mean())<1e-12


def test_zero_features_local_equals_geographic_weighted_mean():
    x=np.zeros((10,1));d=cdist(np.arange(10.)[:,None],np.arange(10.)[:,None]);a=dict(train_global=np.arange(10),distance=d);tr=np.arange(8);q=np.array([8,9]);targets=np.arange(8.)
    pack=dict(train_positions=tr,targets=targets,representation=None,variant='MEAN');p=predict_base(pack,q,dict(a=a,static={'MEAN':x}));w=1/(d[np.ix_(q,tr)]+1e-6);expected=(w@targets)/w.sum(axis=1);np.testing.assert_allclose(p,expected,atol=1e-12)


def test_representation_training_only_and_rank_cap():
    x=pd.DataFrame({'a':[1.,2.,3.,4.],'b':[2.,4.,6.,8.]});m=SignalRepresentation(list(x),'pca8').fit(x);before=m.transform(x);m.transform(x*1000);np.testing.assert_array_equal(before,m.transform(x));assert before.shape[1]==1
