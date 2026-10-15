import numpy as np
import pandas as pd
import pytest
from src.ct3_residual_coherence import fit_pair,Y
from src.ct3_residual_conditional.models import CORE,LAI,SPECS

class FixedBase:
    def predict(self,x):return 2.+x[CORE[0]].to_numpy()*.01

def frame():
    rng=np.random.default_rng(2026)
    t=pd.DataFrame(rng.normal(size=(90,5)),columns=CORE+[LAI])
    t[Y]=3.+t[LAI]*.7+t[CORE[1]]*.3
    return t

def test_evaluation_labels_cannot_change_correction():
    t=frame();a=np.arange(30);c=np.arange(30,70);e=np.arange(70,90)
    for name in ['M1_Z','M2_Z']:
        s=SPECS[name];m,p=fit_pair(t,FixedBase(),a,c,e,s,s['grid'][-1])
        changed=t.copy();changed.loc[e,Y]+=10000
        other,q=fit_pair(changed,FixedBase(),a,c,e,s,s['grid'][-1])
        np.testing.assert_allclose(p,q,rtol=0,atol=1e-12)
        assert abs(m.predict(t.iloc[c]).mean())<1e-12

def test_overlapping_calibration_and_base_rejected():
    with pytest.raises(AssertionError):
        fit_pair(frame(),FixedBase(),np.arange(40),np.arange(30,70),np.arange(70,90),SPECS['M2_Z'],SPECS['M2_Z']['grid'][0])

def test_small_calibration_tree_is_zero_without_relaxing_leaf_limit():
    t=frame();s=SPECS['M2_Z'];m,p=fit_pair(t,FixedBase(),np.arange(30),np.arange(30,50),np.arange(50,90),s,s['grid'][-1])
    assert m.constant
    np.testing.assert_array_equal(p,np.zeros(40))

def test_full_fold_selection_excludes_external_labels(tmp_path,monkeypatch):
    import joblib
    import src.ct3_residual_coherence as run
    index=4
    reference=joblib.load(run.OUT/'checkpoints'/f'{index:02d}.joblib')
    original_read=pd.read_parquet
    original=original_read(run.SOURCE/'cache/train138.parquet')
    plan=joblib.load(run.SOURCE/'cache/execution_plan.joblib')[index]
    changed=original.copy()
    changed.loc[plan['validation_positions'],Y]+=10000
    def read(path,*args,**kwargs):
        if str(path)==str(run.SOURCE/'cache/train138.parquet'):return changed.copy()
        return original_read(path,*args,**kwargs)
    for d in ['models','checkpoints']:(tmp_path/d).mkdir()
    monkeypatch.setattr(pd,'read_parquet',read)
    monkeypatch.setattr(run,'OUT',tmp_path)
    run.fold(index)
    altered=joblib.load(tmp_path/'checkpoints'/f'{index:02d}.joblib')
    for left,right in zip(reference['predictions'],altered['predictions']):
        for key in ['y_pred','y_base','raw_correction','amplitude']:
            np.testing.assert_allclose(left[key],right[key],rtol=0,atol=1e-12)
    for left,right in zip(reference['registry'],altered['registry']):
        assert left['params']==right['params'] and left['amplitude']==right['amplitude']
        np.testing.assert_allclose(left['inner_rmse'],right['inner_rmse'],rtol=0,atol=1e-12)
