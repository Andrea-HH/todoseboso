import json
import joblib
import numpy as np
import pandas as pd
from src.family_4 import within_profile_complementarity as e

def test_controls_are_identical_and_replay_every_frozen_fold():
    control=pd.read_parquet(e.OUT/'tables/control_oof.parquet')
    _,t=e.load();splits,_,groups=e.f.lm.k.j.load_frozen_splits(t)
    original=pd.read_parquet(e.f.OUT/'tables/oof_predictions.parquet')
    original=original[original.experiment.eq('F4-S1')]
    saved=control[control.experiment.eq('F4-E1')]
    keys=[e.ID,'protocol','repeat','fold']
    z=saved.merge(original,on=keys,validate='one_to_one',suffixes=('','_original'))
    np.testing.assert_array_equal(z.y_pred,z.y_pred_original)
    assert len(z)==1794
    for protocol,repeat,fold,tr,va,inner in splits:
        a,b=t.iloc[tr],t.iloc[va]
        if protocol!='random':
            assert not set(groups.loc[a[e.ID],protocol])&set(groups.loc[b[e.ID],protocol])
        for itr,iva in inner:
            assert not set(itr)&set(iva)
            if protocol!='random':assert not set(groups.loc[a.iloc[itr][e.ID],protocol])&set(groups.loc[a.iloc[iva][e.ID],protocol])
        for name,old in [('F4-E0','J0_RAIN'),('F4-E1','F4-S1')]:
            path=e.f.lm.k.j.locations()[0]/'models'/f'{old}_{protocol}_{repeat}_{fold}.joblib' if name=='F4-E0' else e.f.OUT/'models'/f'{old}_{protocol}_{repeat}_{fold}.joblib'
            model=joblib.load(path)
            if name=='F4-E1':model=model['model']
            yp=model.predict(b[e.RAIN] if name=='F4-E0' else b)
            ref=control[(control.experiment==name)&(control.protocol==protocol)&(control['repeat']==repeat)&(control.fold==fold)].set_index(e.ID).loc[b[e.ID]]
            np.testing.assert_allclose(yp,ref.y_pred,atol=1e-10,rtol=0)

def test_new_models_replay_and_do_not_use_validation_labels_or_metadata():
    _,t=e.load();p=pd.read_parquet(e.OUT/'tables/oof_predictions.parquet')
    assert len(p)==8970 and not p.duplicated(['experiment','protocol','repeat','fold',e.ID]).any()
    for protocol,repeat,fold,tr,va,inner in e.f.lm.k.j.load_frozen_splits(t)[0]:
        b=t.iloc[va].copy()
        for name in e.SPECS:
            model=joblib.load(e.OUT/'models'/f'{name}_{protocol}_{repeat}_{fold}.joblib')
            yp=model.predict(b)
            ref=p[(p.experiment==name)&(p.protocol==protocol)&(p['repeat']==repeat)&(p.fold==fold)].set_index(e.ID).loc[b[e.ID]]
            np.testing.assert_allclose(yp,ref.y_pred,atol=1e-10,rtol=0)
            altered=b.copy();altered[e.TARGET]=1e9;altered['climate_profile']='new';altered['Estado']='new';altered['longitude']=1e9
            np.testing.assert_array_equal(yp,model.predict(altered))

def test_exact_feature_definitions_on_source_samples():
    d,_=e.load();ts=pd.read_parquet(e.ROOT/'data/processed/family_1/timeseries/sentinel_timeseries.parquet')
    from src.family_1.temporal_primitives import extract_temporal_features
    for pid in d[e.ID].iloc[[0,50,100,196]]:
        g=ts[(ts[e.ID]==pid)&ts.fecha_captura.between('2025-04-01','2025-10-31')]
        lai=extract_temporal_features(g.fecha_captura,g.lai_promedio)
        row=d[d[e.ID].eq(pid)].iloc[0]
        np.testing.assert_allclose([row[e.LAI],row[e.RISE]],[lai['q10'],lai['runup_start_day']],atol=1e-12)
        may=g[g.fecha_captura.dt.month.eq(5)]
        np.testing.assert_allclose(row[e.f.NDVI],may.ndvi_promedio.mean(),atol=1e-12)
    assert e.TARGET not in d and len(d)==197

def test_pair_orientation_same_external_model_and_equal_weight_metrics():
    pp=pd.read_parquet(e.OUT/'tables/same_model_pairs.parquet');p=pd.read_parquet(e.OUT/'tables/oof_predictions.parquet')
    assert (pp.id_a<pp.id_b).all()
    for field,rename in [('id_a','a'),('id_b','b')]:
        z=p.rename(columns={e.ID:field,'y_pred':'pred_'+rename,'y_true':'true_'+rename})
        pp=pp.merge(z[['experiment','protocol','repeat','fold',field,'pred_'+rename,'true_'+rename]],on=['experiment','protocol','repeat','fold',field],validate='many_to_one')
    np.testing.assert_allclose(pp.pair_error,(pp.true_a-pp.true_b)-(pp.pred_a-pp.pred_b),atol=1e-12)
    g=pp[(pp.experiment=='F4-E2')&(pp.protocol=='random')&(pp['repeat']==1)]
    expected=np.sqrt(g.groupby('profile').pair_error.apply(lambda x:np.mean(x*x)).mean())
    saved=pd.read_csv(e.OUT/'tables/pair_metrics_repeat.csv')
    value=saved.query("experiment=='F4-E2' and protocol=='random' and repeat==1 and scope=='all'").equal_profile_RMSE.iloc[0]
    np.testing.assert_allclose(expected,value,atol=1e-12)

def test_previous_family4_artifacts_remain_unchanged():
    previous=json.loads((e.f.OUT/'manifest.json').read_text())
    assert all(e.sha(e.ROOT/path)==digest for path,digest in previous['artifacts'].items())
