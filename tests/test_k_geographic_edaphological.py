"""Stability, unknown mass, nested label exclusion and actual frozen outputs."""
import json
import numpy as np
import pandas as pd
import pytest
from src.family_1 import k_geographic_edaphological as k

def test_synthetic_stability():
    assert k.synthetic_checks().passed.all()

def test_unseen_mass_pooled_without_validation_support():
    x=pd.DataFrame({'soil_unit_share__A':[1.,.9,.8,.9],
                    'soil_unit_share__B':[0.,.1,.2,.1],
                    'soil_unit_share__C':[0.,0.,0.,0.]})
    transformer=k.StableFeatures(3).fit(x)
    validation=pd.DataFrame({'soil_unit_share__A':[.1],'soil_unit_share__B':[.2],'soil_unit_share__C':[.7]})
    raw=transformer._raw(validation)
    assert transformer.kept_units_==['soil_unit_share__A','soil_unit_share__B']
    assert raw.soil_other_share.iloc[0]==pytest.approx(.7)
    assert raw.sum(axis=1).iloc[0]==pytest.approx(1)
    assert 'soil_other_share' not in transformer.get_feature_names_out() # constant in training

def test_tiny_variance_never_amplifies_soil():
    x=pd.DataFrame({'soil_fraction':[1e-9,2e-9,3e-9]})
    transformer=k.StableFeatures().fit(x)
    assert abs(transformer.transform(pd.DataFrame({'soil_fraction':[.9]}))[0,0])<=1

def test_deeper_cv_group_integrity():
    d,t,old,specs,groups,units=k.load()
    splits,_,assignments=k.j.load_frozen_splits(t)
    assert len(t)==138 and k.TARGET not in d
    for protocol,rep,fold,tr,va,inner in splits:
        if protocol=='random':continue
        for a,b in inner:
            f=t.iloc[tr].iloc[a]
            for x,y in k.subcv(f,protocol,assignments):
                values=assignments.loc[f[k.ID],protocol].to_numpy()
                assert not set(values[x])&set(values[y])

def test_crossfitting_excludes_labels_even_from_tuning(tmp_path):
    (tmp_path/'climate_cache').mkdir()
    frame=pd.DataFrame({k.ID:['A','B','C','D','E','F'],k.TARGET:[1.,2.,3.,4.,5.,6.]})
    for c in k.RAIN:frame[c]=np.arange(6.)
    assignments=pd.DataFrame(index=frame[k.ID])
    contexts=k.ClimateContexts(tmp_path,assignments)
    seen=[]
    class Mean:
        def __init__(self,mean):self.mean=mean
        def predict(self,x):return np.full(len(x),self.mean)
    def tune(f,protocol,cv):
        seen.append(set(f[k.ID]))
        return dict(model=Mean(f[k.TARGET].mean()),params={},train_ids=f[k.ID].tolist())
    contexts.tune=tune
    cv=[(np.array([2,3,4,5]),np.array([0,1])),(np.array([0,1,4,5]),np.array([2,3])),(np.array([0,1,2,3]),np.array([4,5]))]
    result=contexts.context(frame,frame.iloc[:1],'random',cv,'test')
    assert np.allclose(result['crossfit'],[4.5,4.5,3.5,3.5,2.5,2.5])
    for log in contexts.audit:assert not set(json.loads(log['fit_ids']))&set(json.loads(log['heldout_ids']))

def test_completed_k_artifacts():
    out,_=k.locations()
    if not (out/'manifest.json').exists():pytest.skip('Full modeling run not yet complete')
    p=pd.read_parquet(out/'tables/11_k_oof_predictions.parquet')
    assert len(p)==14*1794
    for _,z in p.groupby(['experiment','protocol','repeat']):assert len(z)==138 and z[k.ID].is_unique
    residual=p[p.experiment.str.startswith(('K5_','K6_','K7_','K8_'))]
    assert np.allclose(residual.y_pred,residual.y_climate+residual.correction)
    assert np.allclose(residual.correction,residual.eta*residual.proposed_correction)
    jp=pd.read_parquet(k.j.locations()[0]/'tables/02_oof_predictions.parquet')
    base=jp[jp.experiment=='J0_RAIN']
    q=residual.merge(base,on=[k.ID,'protocol','repeat','fold'],suffixes=('_k','_j'),validate='many_to_one')
    assert np.allclose(q.y_climate,q.y_pred_j,atol=1e-8,rtol=0)
    provenance=pd.read_csv(out/'tables/16_crossfit_provenance.csv')
    d,train,_,_,_,_=k.load()
    assignments=k.j.load_frozen_splits(train)[2]
    train_ids=set(train[k.ID])
    for row in provenance.itertuples():
        fit=set(json.loads(row.fit_ids));held=set(json.loads(row.heldout_ids))
        assert not fit&held and fit|held<=train_ids
        if row.protocol!='random':assert not set(assignments.loc[list(fit),row.protocol])&set(assignments.loc[list(held),row.protocol])
        for a,b in json.loads(row.inner_folds):
            assert not set(a)&set(b) and set(a)|set(b)==fit and not held&(set(a)|set(b))
            if row.protocol!='random':assert not set(assignments.loc[a,row.protocol])&set(assignments.loc[b,row.protocol])
    screen=pd.read_csv(out/'tables/33_stable_soil_transformation_screen.csv')
    assert screen.max_abs_transformed.max()<=1+1e-8
    manifest=json.loads((out/'manifest.json').read_text())
    assert manifest['previous_results_unchanged'] and not manifest['hidden_y_used']
    assert manifest['saved_outer_models']==910
    cached=pd.read_csv(out/'tables/46_verified_contextual_benchmark_summary.csv').set_index('experiment')
    assert cached.loc['Champion','RMSE']==pytest.approx(.498127,abs=1e-6)
    # Every actual model validates exactly its frozen outer ID list.
    for protocol,rep,fold,tr,va,inner in k.j.load_frozen_splits(train)[0]:
        for _,z in p[(p.protocol==protocol)&(p['repeat']==rep)&(p.fold==fold)].groupby('experiment'):
            assert set(z[k.ID])==set(train.iloc[va][k.ID])
