import json
import joblib
import numpy as np
import pandas as pd
from src.family_4 import stage_b_learning as b
from src.family_4.stage_b_objective import select_candidate,GroupObjectiveRegressor

def test_controls_and_all_lambda_zero_implementation_replays():
    old=pd.read_parquet(b.e.OUT/'tables/oof_predictions.parquet');old=old[old.experiment.isin(['F4-E1','F4-E2'])].copy();old.experiment=old.experiment.map({'F4-E1':'B0','F4-E2':'B2'})
    control=pd.read_parquet(b.OUT/'tables/control_oof.parquet');keys=[b.ID,'experiment','protocol','repeat','fold']
    z=control.merge(old,on=keys,validate='one_to_one',suffixes=('','_old'))
    assert len(z)==3588
    np.testing.assert_array_equal(z.y_pred,z.y_pred_old)
    audit=pd.read_csv(b.OUT/'audit/lambda0_implementation_replay.csv')
    assert len(audit)==130 and audit.max_abs_prediction_difference.max()<=1e-8

def test_each_saved_model_replays_and_transforms_only_train():
    _,t=b.load();p=pd.read_parquet(b.OUT/'tables/oof_predictions.parquet');reg=pd.read_csv(b.OUT/'tables/registry.csv')
    assert len(p)==7176 and not p.duplicated(['experiment','protocol','repeat','fold',b.ID]).any()
    for protocol,repeat,fold,tr,va,inner in b.e.f.lm.k.j.load_frozen_splits(t)[0]:
        train,valid=t.iloc[tr],t.iloc[va]
        for name in ['B1','B3']:
            fitted=joblib.load(b.OUT/'models'/f'{name}_{protocol}_{repeat}_{fold}.joblib')
            assert list(fitted.columns)==b.MODELS[name]
            np.testing.assert_allclose(fitted.preprocess_.median_,np.nanmedian(train[b.MODELS[name]].to_numpy(),axis=0),atol=1e-12)
            ref=p[(p.experiment==name)&(p.protocol==protocol)&(p['repeat']==repeat)&(p.fold==fold)].set_index(b.ID).loc[valid[b.ID]]
            np.testing.assert_allclose(fitted.predict(valid),ref.y_pred,atol=1e-12)
            altered=valid.copy();altered[b.TARGET]=1e9;altered.climate_profile='changed';altered.Municipio='changed'
            np.testing.assert_array_equal(fitted.predict(altered),fitted.predict(valid))
            row=reg[(reg.experiment==name)&(reg.protocol==protocol)&(reg['repeat']==repeat)&(reg.fold==fold)].iloc[0]
            assert set(json.loads(row.train_ids))==set(train[b.ID])
            assert set(json.loads(row.validation_ids))==set(valid[b.ID])
            assert row.converged

def test_internal_selection_and_group_fit_support_are_reproducible():
    _,t=b.load();inner=pd.read_csv(b.OUT/'tables/inner.csv');reg=pd.read_csv(b.OUT/'tables/registry.csv');con=pd.read_csv(b.OUT/'tables/convergence.csv')
    for protocol,repeat,fold,tr,va,splits in b.e.f.lm.k.j.load_frozen_splits(t)[0]:
        for name,control in [('B1','B0'),('B3','B2')]:
            old,_=b.archived(control,protocol,repeat,fold)
            rows=inner[(inner.experiment==name)&(inner.protocol==protocol)&(inner['repeat']==repeat)&(inner.fold==fold)].to_dict('records')
            assert len(rows)==48
            anchor=next(r for r in rows if r['lam']==0 and r['alpha']==old['model'].alpha and r['rho']==old['model'].l1_ratio)
            chosen,reason=select_candidate(rows,anchor)
            recorded=reg[(reg.experiment==name)&(reg.protocol==protocol)&(reg['repeat']==repeat)&(reg.fold==fold)].iloc[0]
            assert (chosen['alpha'],chosen['rho'],chosen['lam'])==(recorded.alpha,recorded.rho,recorded.lam)
            assert reason==recorded.selection_reason
            assert chosen['rmse']<=anchor['rmse']+.01+1e-12 and chosen['mae']<=anchor['mae']+.01+1e-12
            for j,(itr,iva) in enumerate(splits):
                sizes=t.iloc[tr].iloc[itr].groupby('climate_profile').size();n=(sizes>=2).sum()
                log=con[(con.experiment==name)&(con.protocol==protocol)&(con['repeat']==repeat)&(con.fold==fold)&(con.inner_fold==j)]
                assert len(log)==48 and log.n_eligible_train_profiles.eq(n).all() and log.n_train.eq(len(itr)).all()
                assert not set(t.iloc[tr].iloc[itr][b.ID])&set(t.iloc[tr].iloc[iva][b.ID])
    assert con.converged.all()

def test_same_external_model_pairs_and_equal_profile_aggregation():
    pp=pd.read_parquet(b.OUT/'tables/objective_same_model_pairs.parquet');p=pd.read_parquet(b.OUT/'tables/oof_predictions.parquet')
    for field,suffix in [('id_a','a'),('id_b','c')]:
        z=p.rename(columns={b.ID:field,'y_true':'y_'+suffix,'y_pred':'p_'+suffix})
        pp=pp.merge(z[['experiment','protocol','repeat','fold',field,'y_'+suffix,'p_'+suffix]],on=['experiment','protocol','repeat','fold',field],validate='many_to_one')
    np.testing.assert_allclose(pp.pair_error,(pp.y_a-pp.y_c)-(pp.p_a-pp.p_c),atol=1e-12)
    g=pp[(pp.experiment=='B3')&(pp.protocol=='random')&(pp['repeat']==1)]
    expected=np.sqrt(g.groupby('profile').pair_error.apply(lambda x:np.mean(x*x)).mean())
    records=pd.read_csv(b.OUT/'tables/objective_pair_repeat.csv')
    saved=records.query("experiment=='B3' and protocol=='random' and repeat==1 and scope=='all'").equal_profile_rmse.iloc[0]
    np.testing.assert_allclose(expected,saved,atol=1e-12)

def test_fixed_mix_correspondence_and_mse_identity():
    mix=pd.read_parquet(b.OUT/'tables/fixed_blend_oof.parquet')
    assert len(mix)==4140 and mix.protocol.eq('random').all()
    wide=mix.pivot(index=[b.ID,'repeat','fold'],columns='experiment',values='y_pred')
    np.testing.assert_array_equal(wide.FIXED_50_50,(wide.CHAMPION+wide.F4_S1)/2)
    d=pd.read_csv(b.OUT/'tables/fixed_blend_mse_decomposition.csv')
    np.testing.assert_allclose(d.mse_mix,d.decomposition_sum,atol=1e-12)
    np.testing.assert_allclose(d.mean_error_product,d.error_covariance+d.bias_champion*d.bias_s1,atol=1e-12)

def test_complete_repeat_global_metrics_not_fold_average():
    p=pd.read_parquet(b.OUT/'tables/oof_predictions.parquet');m=pd.read_csv(b.OUT/'tables/objective_metrics_repeat.csv')
    for (exp,protocol,repeat),g in p.groupby(['experiment','protocol','repeat']):
        assert len(g)==138
        ref=m[(m.experiment==exp)&(m.protocol==protocol)&(m['repeat']==repeat)&(m.stratum=='all')].iloc[0]
        np.testing.assert_allclose(ref.RMSE,np.sqrt(np.mean((g.y_true-g.y_pred)**2)),atol=1e-12)

def test_frozen_source_and_previous_results_integrity():
    config=json.loads((b.OUT/'frozen_design.json').read_text())
    assert all(b.a.sha(b.ROOT/path)==digest for path,digest in config['source_sha'].items())
    for out in [b.a.OUT,b.e.OUT,b.e.f.OUT]:
        manifest=json.loads((out/'manifest.json').read_text())
        assert all(b.a.sha(b.ROOT/path)==digest for path,digest in manifest['artifacts'].items())
