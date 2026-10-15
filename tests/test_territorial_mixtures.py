import numpy as np,pandas as pd
from src.territorial_mixtures import Mixture,EQUAL,CORE,Y

def data(n=80):
    x=np.linspace(-1,1,n)
    t=pd.DataFrame({c:x*(i+1) for i,c in enumerate(CORE)})
    t[Y]=0.;t['Estado']='A';t['Municipio']=np.where(x<0,'Left','Right');t['climate_profile']=np.arange(n)%4
    p=np.column_stack([np.where(x<0,0,2),np.where(x<0,2,0),np.full(n,3.)])
    return t,p

def test_fixed_regularization_and_convexity():
    t,p=data();model=Mixture('R1',dict(alpha=None)).fit(t,p)
    np.testing.assert_allclose(model.global_weights,EQUAL)
    np.testing.assert_allclose(model.predict(t,p),p.mean(axis=1))

def test_unseen_municipality_falls_back_and_small_groups_cannot_fit():
    t,p=data();model=Mixture('R2',dict(alpha=None,shrink=50.)).fit(t,p)
    assert len(model.regions)==2
    unknown=t.iloc[:3].copy();unknown.Municipio='New'
    w,route=model.weights(unknown);np.testing.assert_allclose(w,np.tile(EQUAL,(3,1)));assert set(route)=={'global'}
    tiny=Mixture('R2',dict(alpha=None,shrink=15.)).fit(t.iloc[:10],p[:10]);assert not tiny.regions

def test_gate_direct_objective_support_and_geography_independence():
    t,p=data();model=Mixture('R3',dict(alpha=None,depth=2,leaf=20,shrink=50.)).fit(t,p)
    assert sum(n['feature']>=0 for n in model.nodes)>0
    for n in model.nodes:
        if n['feature']<0:assert n['n']>=20 and n['n_profiles']>=2
    changed=t.copy();changed.Municipio='Anywhere';changed.Estado='Elsewhere'
    np.testing.assert_allclose(model.predict(t,p),model.predict(changed,p))
    unseen=t.iloc[:1].copy();unseen[CORE]=1000
    w,route=model.weights(unseen);np.testing.assert_allclose(w[0],EQUAL);assert route[0]=='outside_support_global'
    assert np.mean(model.predict(t,p)**2)<np.mean(p.mean(axis=1)**2)

def test_full_fold_external_labels_cannot_change_rules(tmp_path,monkeypatch):
    import joblib
    import src.territorial_mixtures as execution
    index=0;original_out=execution.OUT
    ref=joblib.load(original_out/'checkpoints'/f'{index:02d}.joblib')
    original_read=pd.read_parquet;t=original_read(execution.OLD/'cache/train138.parquet');plan=joblib.load(execution.OLD/'cache/execution_plan.joblib')[index]
    changed=t.copy();changed.loc[plan['validation_positions'],Y]+=10000
    def read(path,*args,**kwargs):
        if str(path)==str(execution.OLD/'cache/train138.parquet'):return changed.copy()
        return original_read(path,*args,**kwargs)
    for d in ['models','cache','checkpoints']:(tmp_path/d).mkdir()
    joblib.dump(joblib.load(original_out/'cache'/f'INNER_{index:02d}.joblib'),tmp_path/'cache'/f'INNER_{index:02d}.joblib')
    monkeypatch.setattr(pd,'read_parquet',read);monkeypatch.setattr(execution,'OUT',tmp_path)
    execution.fold(index)
    other=joblib.load(tmp_path/'checkpoints'/f'{index:02d}.joblib')
    assert ref['registry']==other['registry'] and ref['rules']==other['rules']
    np.testing.assert_allclose([r['y_pred'] for r in ref['predictions']],[r['y_pred'] for r in other['predictions']],rtol=0,atol=1e-12)
