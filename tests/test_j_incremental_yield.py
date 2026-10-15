"""Section J leakage, encoding, model-origin and reproducibility checks."""
import json
import numpy as np
import pandas as pd
import pytest
from src.family_1.j_incremental_yield import WeightedTop3,FoldConstantDrop,load,locations,RAIN,ID,TARGET,H
from src.family_1.rainfall_pcr import load_frozen_splits

def topframe():
    x=pd.DataFrame({c:[1.,2.] for c in RAIN})
    x['soil_top1_unit']=['A','B'];x['soil_top1_share']=[.6,.8]
    x['soil_top2_unit']=['B','A'];x['soil_top2_share']=[.3,.2]
    x['soil_top3_unit']=[None,None];x['soil_top3_share']=[0.,0.]
    x['soil_remaining_share']=[.1,0.]
    return x

def test_nominal_weighted_top3_conserves_unknown_mass_and_ignores_rank():
    x=topframe();t=WeightedTop3().fit(x)
    z=x.iloc[[0]].copy();z['soil_top1_unit']='C';z['soil_top1_share']=.7;z['soil_top2_unit']='A';z['soil_top2_share']=.2
    v=t.transform(z)[0,len(RAIN):]
    assert t.units_==['A','B']
    assert v.tolist()==pytest.approx([.2,0.,.7,.1])
    assert v.sum()==pytest.approx(1)
    swapped=x.copy()
    for suffix in ['unit','share']:
        swapped[f'soil_top1_{suffix}']=x[f'soil_top2_{suffix}'];swapped[f'soil_top2_{suffix}']=x[f'soil_top1_{suffix}']
    assert np.allclose(t.transform(x),t.transform(swapped))

def test_fold_constant_drop_does_not_learn_from_validation():
    t=FoldConstantDrop().fit([[0,1],[0,3]])
    assert t.support_.tolist()==[False,True]
    assert t.transform([[500,8]]).tolist()==[[8]]
    assert FoldConstantDrop().fit([[1,1],[1,1]]).all_constant_

def test_input_schema_and_frozen_group_separation():
    d,train,specs=load()
    assert len(d)==197 and len(train)==138 and TARGET not in d
    assert [len(x) for x in specs.values()]==[7,8,9,17,19,29,14]
    splits,table,groups=load_frozen_splits(train)
    assert len(splits)==65
    for protocol,rep,fold,tr,va,inner in splits:
        assert not set(tr)&set(va)
        if protocol!='random':
            values=groups.loc[train[ID],protocol].to_numpy()
            assert not set(values[tr])&set(values[va])
            for a,b in inner:assert not set(values[tr[a]])&set(values[tr[b]])
            if protocol=='climate_profile':
                exact=train.climate_profile.to_numpy()
                assert not set(exact[tr])&set(exact[va])
                for a,b in inner:assert not set(exact[tr[a]])&set(exact[tr[b]])

def test_completed_j0_matches_h_and_all_experiments_share_oof_folds():
    out,_=locations();p=pd.read_parquet(out/'tables/02_oof_predictions.parquet')
    gate=json.loads((out/'baseline_reproduction_gate.json').read_text())
    assert gate['passed'] and gate['max_abs_prediction_difference']<1e-8
    assert len(p)==7*1794
    for _,z in p.groupby(['protocol','experiment','repeat']):assert len(z)==138 and z[ID].is_unique
    reference=p[p.experiment=='J0_RAIN'][[ID,'protocol','repeat','fold']]
    for _,z in p.groupby('experiment'):
        assert len(reference.merge(z,on=[ID,'protocol','repeat','fold'],validate='one_to_one'))==1794
    h=pd.read_parquet(H/'tables/31_oof_individual.parquet');h=h[h.experiment=='H1_RAIN']
    q=p[p.experiment=='J0_RAIN'].merge(h,on=[ID,'protocol','repeat','fold'],suffixes=('_J','_H'),validate='one_to_one')
    assert np.allclose(q.y_pred_J,q.y_pred_H,rtol=0,atol=1e-8)

def test_same_model_climate_baseline_cannot_differentiate_identical_vectors():
    out,_=locations();z=pd.read_csv(out/'tables/16_same_model_within_profile.csv')
    assert z.loc[z.experiment=='J0_RAIN','prediction_range'].max()<1e-8
    assert (z.n>=2).all()
    manifest=json.loads((out/'manifest.json').read_text())
    assert manifest['previous_results_unchanged'] and not manifest['hidden_y_used']

def test_primary_aggregation_and_context_use_compatible_complete_repetitions():
    out,_=locations();comparison=pd.read_csv(out/'tables/40_model_comparison.csv');reps=pd.read_csv(out/'tables/42_repetition_metrics.csv')
    actual=reps.groupby(['protocol','experiment']).RMSE.mean().sort_index()
    expected=comparison.set_index(['protocol','experiment']).RMSE_mean.sort_index()
    assert np.allclose(actual,expected)
    bench=pd.read_csv(out/'tables/23_contextual_benchmark_summary.csv').set_index('experiment')
    h=pd.read_csv(H/'tables/40_model_comparison.csv')
    reference=h[(h.protocol=='random')&(h.experiment=='H8_CLIMATE_CURRENT_ORIGINAL')].iloc[0].RMSE_mean
    assert bench.loc['H8_CLIMATE_CURRENT_ORIGINAL','RMSE']==pytest.approx(reference,abs=1e-10)
    assert bench.loc['J0_RAIN','RMSE']==pytest.approx(expected.loc[('random','J0_RAIN')],abs=1e-10)
    folds=pd.read_csv(out/'tables/03_registry.csv')
    assert folds.n_effective_columns.ge(1).all() and folds.convergence_warnings.eq(0).all()
