import numpy as np
from src.compact_ensemble import WEIGHTS,choose_weights

def test_convex_weights_and_vertex_support():
    assert np.all(WEIGHTS>=0)
    np.testing.assert_allclose(WEIGHTS.sum(axis=1),1)
    for v in np.eye(3):assert np.any(np.all(WEIGHTS==v,axis=1))

def test_complementary_errors_and_deterministic_ties():
    y=np.arange(6.)
    predictions=np.column_stack([y+1,y-1,y+2])
    weights,scores=choose_weights(y,predictions)
    np.testing.assert_array_equal(weights,[.5,.5,0])
    assert min(scores)<1e-12
    tied=np.column_stack([y,y,y]);weights,_=choose_weights(y,tied)
    np.testing.assert_array_equal(weights,[1,0,0])

def test_full_pipeline_external_labels_do_not_change_weights(tmp_path,monkeypatch):
    import joblib,pandas as pd
    import src.compact_ensemble as execution
    index=0
    reference=joblib.load(execution.OUT/'checkpoints'/f'{index:02d}.joblib')
    original_read=pd.read_parquet
    frame=original_read(execution.OLD/'cache/train138.parquet')
    plan=joblib.load(execution.OLD/'cache/execution_plan.joblib')[index]
    changed=frame.copy();changed.loc[plan['validation_positions'],execution.Y]+=10000
    def read(path,*args,**kwargs):
        if str(path)==str(execution.OLD/'cache/train138.parquet'):return changed.copy()
        return original_read(path,*args,**kwargs)
    (tmp_path/'models').mkdir();(tmp_path/'checkpoints').mkdir()
    for item in plan['inner']:
        pack=joblib.load(execution.OUT/'models'/f"CB_{item['base_key']}.joblib")
        joblib.dump(pack,tmp_path/'models'/f"CB_{item['base_key']}.joblib")
    monkeypatch.setattr(pd,'read_parquet',read);monkeypatch.setattr(execution,'OUT',tmp_path)
    execution.fold(index)
    altered=joblib.load(tmp_path/'checkpoints'/f'{index:02d}.joblib')
    assert reference['registry']==altered['registry']
    np.testing.assert_allclose([r['y_pred'] for r in reference['predictions']],[r['y_pred'] for r in altered['predictions']],rtol=0,atol=1e-12)
