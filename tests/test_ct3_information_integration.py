"""Validate the completed diagnostics and preserved inputs, without fitting."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from src.ct3_information.research import ROOT,OUT,BLOCKS,sha

def test_completed_scope_identity_and_hashes():
    manifest=json.loads((OUT/'manifest.json').read_text())
    assert manifest['new_predictive_y_fits']==0 and manifest['new_PRED_predictions']==0
    assert manifest['n_catalogue']==1867 and manifest['n_diagnostic_candidates']==29
    fold=pd.read_csv(OUT/'audit/fold_identity.csv')
    assert len(fold)==65 and fold.ids_targets_groups_verified.all()
    for r in pd.read_csv(OUT/'audit/consumed_input_hashes.csv').itertuples():assert sha(ROOT/r.path)==r.sha256
    for p,h in manifest['artifacts'].items():assert sha(ROOT/p)==h
    replay=pd.read_csv(OUT/'audit/original_CT3_model_replay.csv')
    assert len(replay)==65 and replay.max_abs_replay_difference.max()<1e-10
    for r in replay.itertuples():assert sha(ROOT/r.path)==r.sha256
    f8=json.loads((ROOT/'outputs/research/family_8/residual_design/v1/manifest.json').read_text())
    assert f8['models_trained']==0 and f8['predictions_generated']==0

def test_variation_identity_and_catalogue_exclusions():
    audit=pd.read_csv(OUT/'phase_i/variable_audit.csv')
    assert len(audit)==audit.variable.nunique()==1867
    assert not set(['RENDIMIENTO_T_HA','Estado','Municipio','ID_POLIGONO','longitude','latitude'])&set(audit.variable)
    v=pd.read_csv(OUT/'phase_i/profile_variation.csv');v=v[v.total_ss.notna()]
    np.testing.assert_allclose(v.total_ss,v.within_ss+v.between_ss,rtol=1e-8,atol=1e-8)
    assert (audit[audit.variable.isin(['compact_precip_total','compact_early_fraction','compact_concentration_hhi'])].within_contrasting_profiles==0).all()

def test_association_scope_support_and_no_pseudoreplication():
    candidates={c for cols in BLOCKS.values() for c in cols}
    for name in ['retrospective_conditional','within_profile_associations','cross_association_summary','same_model_pair_associations']:
        table=pd.read_csv(OUT/f'phase_ii/{name}.csv');assert set(table.variable)==candidates
        assert not any(col.startswith('p_value') for col in table)
    s=pd.read_csv(OUT/'phase_ii/cross_association_summary.csv');assert s.min_n.max()<=138 and s.n_repeats.max()==10
    p=pd.read_csv(OUT/'phase_ii/same_model_pair_associations.csv');assert p.n_parcels.max()<=107 and p.n_profiles.max()<=12
    for tag in ['random','climate_profile','municipality','spatial']:assert tag in p.protocol.unique()
