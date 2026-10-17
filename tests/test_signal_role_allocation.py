import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.model_selection import KFold
from src.signal_role_allocation import RoleFactory,RoleSpace,predict_role,role_corrector
from src.conditional_local_phases import PhysicalSpace
from src.ct3_residual_conditional.models import CORE


def test_moved_block_excluded_from_expert_and_external_targets(tmp_path):
    rng=np.random.default_rng(21);n=32;x=rng.normal(size=(n,6));frame=pd.DataFrame(x,columns=list('abcdef'));core=pd.DataFrame(x[:,:4],columns=CORE);full=pd.concat([core,frame],axis=1);y=3+x[:,0]+x[:,5];tr=np.arange(26);va=np.arange(26,n);cv=list(KFold(3,shuffle=True,random_state=2026).split(tr));a=dict(train=pd.DataFrame({'ID_POLIGONO':list(map(str,range(n)))}),train_global=np.arange(n),distance=cdist(x[:,:2],x[:,:2]));variant=dict(type='small',columns=list('abcde'),mode='raw',correction_columns=['f'],correction_atoms=[])
    assets=dict(a=a,y=y,features197=frame,role_frame=full,physical_definitions={},variants={'MOVE':variant},static={});f=RoleFactory(assets,'random',pd.DataFrame(index=a['train'].ID_POLIGONO),tmp_path/'a',tmp_path/'none');m=f.fit(tr,'MOVE',cv);p=predict_role(m,va,assets);assert 'f' not in m['local']['representation'].columns
    assert role_corrector(variant,dict(alpha=.1,l1_ratio=.5),assets).fit(full.iloc[tr],y[tr]).named_steps['repr'].core.cols==tuple(CORE)+('f',)
    changed={**assets,'y':y.copy()};changed['y'][va]+=1e5;g=RoleFactory(changed,'random',pd.DataFrame(index=a['train'].ID_POLIGONO),tmp_path/'b',tmp_path/'none');np.testing.assert_array_equal(p,predict_role(g.fit(tr,'MOVE',cv),va,changed));assert all(not set(e['train'])&(set(e['held'])|set(va)) for e in f.ledger)


def test_role_physical_space_matches_previous_and_unseen_category():
    x=pd.DataFrame({'texture':['a','a','b','b'],'phase':['n','p','n','p'],'share':[0.,.2,.5,1.],'distance':[1.,5.,20.,50.]});defs={'soil_texture_phase':dict(columns=['texture','phase'],summary=['texture','phase'],composition=False),'geologic_composition':dict(columns=['share'],summary=['share'],composition=True),'geologic_distances':dict(columns=['distance'],summary=['distance'],composition=False)}
    m=RoleSpace(list(defs),[],defs).fit(x);old=PhysicalSpace('BOTH',defs).fit(x);np.testing.assert_array_equal(m.transform(x),old.transform(x));q=x.copy();q['texture']='unseen';assert np.isfinite(m.transform(q)).all();assert RoleSpace([],[],defs).fit(x).transform(q).shape==(4,1)


def test_role_signal_preprocessing_training_only():
    x=pd.DataFrame({'v':[0.,1.,2.,3.],'w':[1.,4.,2.,6.]});m=RoleSpace([],list(x),{}).fit(x);before=m.transform(x);m.transform(x*10000);np.testing.assert_array_equal(before,m.transform(x));assert np.isclose(np.mean(np.sum(before**2,axis=1)),1.)
