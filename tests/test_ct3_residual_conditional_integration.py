import json
import numpy as np,pandas as pd,joblib
from src.ct3_residual_conditional.execution import OUT,ROOT,sha,load,base
from src.ct3_residual_conditional.models import SPECS,Z,LAI
from src.ct3_residual_conditional import execution

def test_manifest_and_preservation():
    m=json.loads((OUT/'manifest.json').read_text())
    assert m['status']=='complete' and m['n_oof']==8970 and m['PRED_predictions']==0 and m['no_final_fit138'] and not m['F8_executed']
    for p,h in m['artifacts'].items():assert sha(ROOT/p)==h
    for r in pd.read_csv(OUT/'audit/protected_consumed_inputs.csv').itertuples():assert sha(ROOT/r.path)==r.sha256
    f8=json.loads((ROOT/'outputs/research/family_8/residual_design/v1/manifest.json').read_text());assert f8['models_trained']==0

def test_nested_membership_and_no_final_training():
    contexts=joblib.load(OUT/'cache/base_contexts.joblib');plans=joblib.load(OUT/'cache/execution_plan.joblib');t,_,groups=load()
    assert len(contexts)==1218 and len(plans)==65
    for ctx in contexts.values():
        pos=ctx['positions'];assert len(pos)<138
        for a,b in ctx['cv']:assert not set(a)&set(b)
    for plan in plans:
        external=set(plan['validation_positions'])
        for inner in plan['inner']:
            bb=set(inner['validation_positions']);aa=set(inner['train_positions']);assert not bb&external
            for deep in inner['residual_contexts']:
                positions=set(contexts[deep['base_key']]['positions']);held=set(deep['held_positions'])
                assert positions<=aa and not positions&held and not positions&bb and not positions&external
    assert pd.read_csv(OUT/'audit/nested_exclusion_ledger.csv').exclusions_verified.all()

def test_oof_reconstruction_centering_and_control_matching():
    p=pd.read_parquet(OUT/'tables/oof_predictions.parquet');np.testing.assert_allclose(p.y_pred,p.y_base+p.correction,atol=1e-12);np.testing.assert_allclose(p.correction,p.amplitude*p.raw_correction,atol=1e-12)
    assert p[p.amplitude.eq(0)].y_pred.equals(p[p.amplitude.eq(0)].y_base)
    for _,g in p.groupby(['experiment','protocol','repeat']):assert len(g)==138 and g.ID_POLIGONO.nunique()==138
    r=pd.read_csv(OUT/'tables/corrector_registry.csv');assert r.correction_train_mean.abs().max()<1e-12
    assert SPECS['M1_Z']['columns']==SPECS['M2_Z']['columns']==Z and LAI not in SPECS['C_CONTEXT']['columns']
    assert pd.read_csv(OUT/'audit/model_replay.csv').max_abs_difference.max()<1e-10

def test_pair_aggregation_and_leaf_support():
    pairs=pd.read_parquet(OUT/'tables/same_model_pairs.parquet');stats=pd.read_csv(OUT/'tables/intraprofile_repeat.csv')
    for (exp,pro,re,subset),g in pairs.groupby(['experiment','protocol','repeat','subset']):
        row=stats[(stats.experiment==exp)&(stats.protocol==pro)&(stats['repeat']==re)&(stats.subset==subset)].iloc[0]
        np.testing.assert_allclose(np.sqrt(np.mean(g.error**2)),row.pair_weighted_RMSE,atol=1e-12)
        np.testing.assert_allclose(np.sqrt(g.assign(e2=g.error**2).groupby('profile').e2.mean().mean()),row.equal_profile_RMSE,atol=1e-12)
    leaves=pd.read_csv(OUT/'tables/tree_leaf_support.csv')
    if len(leaves):assert leaves.n_train.min()>=15 and leaves.n_profiles.min()>=1

def test_complete_fold_is_independent_of_external_labels(monkeypatch,tmp_path):
    """Refit correctors in isolated test storage, reuse bases excluding E."""
    real_out=OUT;t,splits,groups=load();plan=joblib.load(real_out/'cache/execution_plan.joblib')[0]
    expected=joblib.load(real_out/'checkpoints/00.joblib');mutated=t.copy();mutated.loc[plan['validation_positions'],execution.TARGET]+=10000
    for folder in ['cache','models','checkpoints']:(tmp_path/folder).mkdir()
    import shutil
    shutil.copy2(real_out/'cache/execution_plan.joblib',tmp_path/'cache/execution_plan.joblib')
    monkeypatch.setattr(execution,'OUT',tmp_path)
    monkeypatch.setattr(execution,'load',lambda:(mutated,splits,groups))
    monkeypatch.setattr(execution,'base',lambda key:joblib.load(real_out/'base_cache'/f'{key}.joblib')['model'])
    execution.build_fold(0);actual=joblib.load(tmp_path/'checkpoints/00.joblib')
    a=pd.DataFrame(actual['predictions']);b=pd.DataFrame(expected['predictions'])
    for col in ['y_base','raw_correction','amplitude','y_pred']:np.testing.assert_array_equal(a[col],b[col])
    ar=pd.DataFrame(actual['registry']);br=pd.DataFrame(expected['registry'])
    assert ar.params.equals(br.params) and ar.amplitude.equals(br.amplitude)
