from pathlib import Path
import json,importlib.util
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.model_selection import KFold
from src.signal_role_allocation import RoleFactory,predict_role
from src.ct3_residual_conditional.models import CORE
ROOT=Path(__file__).resolve().parents[1]


def test_joint_routes_preserve_expected_fields_and_no_role_reintroduction():
    spec=importlib.util.spec_from_file_location('prep445',ROOT/'scripts/445_prepare_joint_simplification.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);old=json.loads((ROOT/'outputs/modeling/signal_role_allocation/v1/frozen_design.json').read_text());c=m.build_design(old);joint=c['variants']['DROP_JOINT'];assert len(joint['columns'])==7;assert joint['correction_columns']==[] and joint['correction_atoms']==[]
    assert joint['columns']==old['groups']['HISTORY_VIGOR']+old['groups']['CURRENT_DYNAMICS']+old['groups']['SLOPE']
    for name,r in c['recipes'].items():
        n=len(c['variants'][r['variant']]['columns']);gate=15 if len(r['gate_atoms'])==3 else 10;assert r['input_count']==4+n+gate+2
    assert set(c['recipes'])=={'J7_BOTH','J9_SHARES','J10_SHARES','J7_SHARES'}


def test_seven_feature_expert_ignores_heldout_targets(tmp_path):
    rng=np.random.default_rng(45);x=rng.normal(size=(32,7));f=pd.DataFrame(x,columns=[f'x{i}' for i in range(7)]);core=pd.DataFrame(x[:,:4],columns=CORE);frame=pd.concat([core,f],axis=1);y=3+x[:,0];a=dict(train=pd.DataFrame({'ID_POLIGONO':list(map(str,range(32)))}),train_global=np.arange(32),distance=cdist(x[:,:2],x[:,:2]));assets=dict(a=a,y=y,features197=f,role_frame=frame,physical_definitions={},variants={'J7':dict(type='small',columns=list(f),mode='raw',correction_columns=[],correction_atoms=[])},static={});tr=np.arange(26);va=np.arange(26,32);cv=list(KFold(3,shuffle=True,random_state=2026).split(tr));groups=pd.DataFrame(index=a['train'].ID_POLIGONO)
    factory=RoleFactory(assets,'random',groups,tmp_path/'a',tmp_path/'none');model=factory.fit(tr,'J7',cv);prediction=predict_role(model,va,assets);changed={**assets,'y':y.copy()};changed['y'][va]+=10000;other=RoleFactory(changed,'random',groups,tmp_path/'b',tmp_path/'none');np.testing.assert_array_equal(prediction,predict_role(other.fit(tr,'J7',cv),va,changed));assert all(not set(r['train'])&(set(r['held'])|set(va)) for r in factory.ledger)
