import json
import numpy as np
import pandas as pd
from src.ct3_information.phase_iii.execution import ROOT,OUT,sha

def test_scope_preservation_and_frozen_sources():
    m=json.loads((OUT/'manifest.json').read_text())
    assert m['yield_values_used']==m['new_yield_models']==m['PRED_predictions']==0 and not m['F8_executed']
    for path,h in m['artifacts'].items():assert sha(ROOT/path)==h
    for r in pd.read_csv(OUT/'audit/consumed_hashes.csv').itertuples():assert sha(ROOT/r.path)==r.sha256
    cfg=json.loads((OUT/'frozen_design.json').read_text())
    for path,h in cfg['source_sha'].items():assert sha(ROOT/path)==h
    assert all(not {'RENDIMIENTO_T_HA','y_true','y_pred','Estado','Municipio','ID_POLIGONO'}&set(cols) for cols in cfg['blocks'].values())

def test_identity_scopes_contrasts_and_composition_handling():
    d=pd.read_csv(OUT/'block_comparison.csv');assert set(d.scope)=={'138','197_descriptive_transductive'}
    assert d.loc[d.scope.eq('138'),'n'].eq(138).all() and d.loc[d.scope.ne('138'),'n'].eq(197).all()
    assert d.loc[d.scope.eq('138'),'contrasting_profiles'].max()<=12
    climate=d[d.block.eq('climate_monthly_between')&d['mode'].eq('within')];assert climate.dimensions.eq(0).all()
    assert d[d.block.eq('soil_groups_original')].kind.eq('original').all()
    original=d[d.kind.eq('original')];np.testing.assert_allclose(original.total_reconstruction_fraction,1,atol=1e-10)

def test_temporal_support_and_hierarchy_trace_contract():
    organization=pd.read_csv(OUT/'audit/satellite_feature_organization.csv')
    assert len(organization)==1041 and organization.feature_name.nunique()==1041
    q=pd.read_csv(OUT/'audit/temporal_coverage.csv');assert q.n_months.eq(7).all();assert q.ID_POLIGONO.nunique()==197
    t=pd.read_csv(OUT/'audit/temporal_sensitivity.csv');assert set(t.case)=={f'omit_month_{m}' for m in range(4,11)}|{f'drop20pct_{k}' for k in range(4)}
    assert not (OUT/'models').exists()
