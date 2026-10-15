"""L/M numerical stability, representation isolation and historical label exclusion."""
import json
import numpy as np
import pandas as pd
import pytest
import joblib
from src.family_1 import lm_multiblock as lm
from src.family_1.m_satellite import aligned_history,distribution

def test_hellinger_pooling_keeps_unknown_mass_and_never_divides_tiny_sd():
    cols=['soil_unit_share__A','soil_unit_share__B','soil_unit_share__C']
    x=pd.DataFrame({cols[0]:[1.,.99999,1.,1.,1.,1.],cols[1]:[0.,.00001,0.,0.,0.,0.],cols[2]:np.zeros(6)})
    r=lm.BlockRepresentation(blocks=(('soil',tuple(cols)),),pool=True,hellinger=True).fit(x)
    v=pd.DataFrame({cols[0]:[.2],cols[1]:[.1],cols[2]:[.7]})
    raw=r.preps_[0]['prep']._raw(v)
    assert np.allclose(raw.sum(axis=1),1)
    assert np.isclose(raw.soil_other_share.iloc[0],.8)
    assert np.isfinite(r.transform(v)).all() and abs(r.transform(v)).max()<=1

def test_topo_soil_pca_natural_soil_scale_and_rank_cap():
    x=pd.DataFrame({'slope_degrees':[0.,1.,2.,3.],'soil_a':[0.,1e-8,2e-8,3e-8],'soil_absent':[0.,0.,0.,0.]})
    r=lm.BlockRepresentation(blocks=(('joint',tuple(x.columns)),),mode='pca',n_components=4).fit(x)
    assert r.preps_[0]['scale'][1]==1
    assert r.effective_k_==[2]
    v=x.iloc[[0]].copy();v.soil_a=1.;v.soil_absent=1.
    assert np.isfinite(r.transform(v)).all()

def test_spectral_guard_and_metadata_not_predictors():
    x=pd.DataFrame({'S2_x':[0.,1e-9,2e-9],'RENDIMIENTO_T_HA':[1.,2.,3.],'Estado':['a','b','c']})
    r=lm.BlockRepresentation(blocks=(('sat',('S2_x',)),)).fit(x)
    v=x.iloc[[0]].copy();v.S2_x=1.
    a=r.transform(v);v.RENDIMIENTO_T_HA=1000000;v.Estado='unseen'
    assert np.allclose(r.transform(v),a) and abs(a).max()<=20+1e-6

def test_multisensor_pca_has_common_total_budget():
    rng=np.random.default_rng(2026);x=pd.DataFrame(rng.normal(size=(20,8)),columns=[f'x{i}' for i in range(8)])
    a=lm.BlockRepresentation(blocks=(('a',tuple(x.columns[:4])),),mode='block_pca',n_components=2).fit(x)
    b=lm.BlockRepresentation(blocks=(('a',tuple(x.columns[:4])),('b',tuple(x.columns[4:]))),mode='block_pca',n_components=2).fit(x)
    assert a.transform(x).shape==(20,2) and b.transform(x).shape==(20,2)
    assert np.isfinite(b.transform(x)).all()

def test_reference_excludes_2025_and_requires_two_prior_years():
    x=pd.DataFrame({lm.ID:['a']*4+['b']*2,'year':[2022,2023,2024,2025,2024,2025],'month':[4]*6,'index':[1.,2.,3.,999.,4.,999.]})
    baseline,count=aligned_history(x,'index')
    assert baseline.loc[('a',4)]==2
    assert np.isnan(baseline.loc[('b',4)]) and count.loc[('b',4)]==1
    changed=x.copy();changed.loc[changed.year==2025,'index']=-999
    assert baseline.equals(aligned_history(changed,'index')[0])

def test_calendar_integral_not_bridged_over_missing_months():
    values=np.arange(7.).astype(float);assert distribution(values)['peak_month']==10
    values[3]=np.nan;assert np.isnan(distribution(values)['integral_calendar'])

def test_predictive_specifications_are_bounded_and_prespecified():
    d,t,c,soil,units=lm.load_l();specs=lm.l_specs(c,soil,units)
    assert len(specs)==24 and len(c)==48 and len(t)==138 and lm.TARGET not in d
    for spec in specs.values():
        for name,cols in spec['blocks']:assert not set(cols)&{lm.TARGET,'Estado','Municipio','longitude','latitude'}

@pytest.mark.parametrize('section,n_experiments',[('L',24),('M',26)])
def test_completed_oof_provenance_and_stage_sums(section,n_experiments):
    out,proc=lm.locations(section)
    if not (out/'validation.json').exists():pytest.skip('Completion audit pending')
    validation=json.loads((out/'validation.json').read_text())
    assert validation['status']=='passed' and validation['label_and_group_exclusion']
    p=pd.read_parquet(out/'tables/10_oof_predictions.parquet');assert len(p)==1794*n_experiments
    residual=p[p.correction.notna()&p.eta.gt(0)]
    assert np.allclose(residual.y_pred,residual.y_base+residual.correction)
    assert np.allclose(residual.correction,residual.eta*residual.proposed_correction)
    for _,z in p.groupby(['experiment','protocol','repeat']):assert len(z)==138 and z[lm.ID].is_unique
    d=pd.read_parquet(proc/f'{section.lower()}_features_197_target_free.parquet')
    assert lm.TARGET not in d and d.climate_profile.nunique()==53
    if section=='M':
        reg=pd.read_csv(out/'tables/11_registry.csv');assert reg[reg.experiment.str.endswith('BLOCK_PCA')].n_effective.le(4).all()
        support=pd.read_parquet(proc/'historical_reference_support.parquet')
        assert support[support.reference_available].n_years.ge(2).all()

def test_stored_l_pipelines_replay_their_own_oof():
    out,proc=lm.locations('L')
    if not (out/'validation.json').exists():pytest.skip('L pending')
    d=pd.read_parquet(proc/'l_features_197_target_free.parquet');t=lm.k.j.supervised_data(d,pd.read_csv(lm.k.j.MASTER))
    p=pd.read_parquet(out/'tables/10_oof_predictions.parquet')
    for protocol in ['random','climate_profile','municipality','spatial']:
        for name in ['L2','LC_current_soil_direct_raw','L6_HELL_JOINT_PCA']:
            q=p[(p.experiment==name)&(p.protocol==protocol)&(p['repeat']==1)&(p.fold==1)]
            x=t.set_index(lm.ID).loc[q[lm.ID]]
            fitted=joblib.load(out/'models'/f'{name}_{protocol}_1_1.joblib')
            if isinstance(fitted,dict):pred=fitted['base_model'].predict(x[fitted['base_columns']])+fitted['eta']*fitted['corrector'].predict(x)
            else:pred=fitted.predict(x)
            assert np.allclose(pred,q.y_pred,atol=1e-10,rtol=0)
