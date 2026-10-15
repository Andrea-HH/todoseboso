import json
import joblib
import numpy as np
import pandas as pd
from src.family_4 import conditional_response as f

def test_interaction_uses_training_scale_and_includes_main_effects():
    a=pd.DataFrame({f.NDVI:[.1,.2,.3,.4],'rain_total':[10.,20.,30.,40.]})
    r=f.ConditionalFeatures((f.NDVI,'rain_total'),(f.NDVI,'rain_total')).fit(a)
    z=r.transform(a)
    assert z.shape==(4,3)
    np.testing.assert_allclose(z[:,2],z[:,0]*z[:,1])
    before=r.transform(a.iloc[:1])
    r.transform(pd.DataFrame({f.NDVI:[1000.],'rain_total':[100000.]}))
    np.testing.assert_allclose(before,r.transform(a.iloc[:1]))

def test_soil_gate_requires_training_support():
    a=pd.DataFrame({f.SLOPE:np.arange(20.),f.SOIL:[1.]*19+[0.],'climate_profile':['one']*20})
    r=f.ConditionalFeatures((f.SLOPE,f.SOIL),(f.SLOPE,f.SOIL),soil_gate=True).fit(a)
    assert not r.interaction_enabled_
    assert (r.transform(a)[:,-1]==0).all()

def test_target_and_location_do_not_enter_predictors():
    _,t=f.load()
    a=t.iloc[:60];b=t.iloc[60:65].copy()
    model=f.model(f.SPECS['F4-S1']).fit(a,a[f.TARGET])
    expected=model.predict(b)
    b[f.TARGET]=1e9;b['longitude']=1e9;b['Estado']='changed';b[f.ID]='changed'
    np.testing.assert_allclose(expected,model.predict(b))

def test_all_cached_base_contexts_respect_nested_groups_and_targets():
    _,t=f.load();splits,_,groups=f.lm.k.j.load_frozen_splits(t)
    for protocol,repeat,fold,tr,va,inner in splits:
        full,inside,logs=joblib.load(f.lm.locations('L')[0]/'base_cache'/f'contexts_rain_{protocol}_{repeat}_{fold}.joblib')
        a=t.iloc[tr]
        np.testing.assert_allclose(full['residual'],a[f.TARGET].to_numpy()-full['crossfit'])
        assert len(inside)==len(inner)
        for (itr,iva),ctx in zip(inner,inside):
            np.testing.assert_allclose(ctx['residual'],a.iloc[itr][f.TARGET].to_numpy()-ctx['crossfit'])
            assert len(ctx['base'])==len(iva)
        for log in logs:
            fit=set(json.loads(log['fit_ids']));held=set(json.loads(log['heldout_ids']))
            assert not fit&held
            assert fit|held<=set(a[f.ID])
            if protocol!='random':
                assert not set(groups.loc[list(fit),protocol])&set(groups.loc[list(held),protocol])
            for train_ids,val_ids in json.loads(log['tuning_folds']):
                assert set(train_ids)|set(val_ids)<=fit
                assert not set(train_ids)&set(val_ids)
                if protocol!='random':
                    assert not set(groups.loc[train_ids,protocol])&set(groups.loc[val_ids,protocol])

def test_saved_models_replay_each_architecture_and_protocol():
    _,t=f.load();splits,_,_=f.lm.k.j.load_frozen_splits(t)
    predictions=pd.read_parquet(f.OUT/'tables/oof_predictions.parquet')
    assert len(predictions)==11*1794
    assert not predictions.duplicated(['experiment','protocol','repeat','fold',f.ID]).any()
    for index in [0,50,55,60]:
        protocol,repeat,fold,tr,va,inner=splits[index]
        full,_,_=joblib.load(f.lm.locations('L')[0]/'base_cache'/f'contexts_rain_{protocol}_{repeat}_{fold}.joblib')
        b=t.iloc[va]
        np.testing.assert_allclose(full['base'],full['model'].predict(b[f.RAIN]),atol=1e-10)
        for name,spec in f.SPECS.items():
            pack=joblib.load(f.OUT/'models'/f'{name}_{protocol}_{repeat}_{fold}.joblib')
            yp=pack['model'].predict(b) if spec['kind']=='direct' else full['base']+pack['eta']*pack['model'].predict(f.enrich(b,full['base']))
            old=predictions[(predictions.experiment==name)&(predictions.protocol==protocol)&(predictions['repeat']==repeat)&(predictions.fold==fold)].set_index(f.ID).loc[b[f.ID]]
            np.testing.assert_allclose(yp,old.y_pred,atol=1e-10)
