import json
import numpy as np
import pandas as pd
from src.ct3_information.phase_iii.execution import ROOT,OUT,sha
from src.ct3_information.phase_iii.representations import NumericRepresentation,centered_groups

def test_residual_climate_contrast_can_be_induced_by_existing_ndvi():
    groups=np.repeat(np.arange(6),5);noise=np.tile(np.linspace(-1,1,5),6)
    z=pd.DataFrame({'climate':groups.astype(float)});core=pd.DataFrame(np.zeros((30,4)));core.iloc[:,-1]=groups+noise
    rep=NumericRepresentation(mode='ct3_residual',k=1).fit(z,core,groups)
    original=centered_groups(rep.raw_scaled(z),groups);res=centered_groups(rep.transformed_input(z,core,groups),groups)
    assert np.max(abs(original))<1e-12 and np.std(res)>.01
    expected=-rep.beta[-1,0]*centered_groups(core.to_numpy(),groups)[:,-1]/rep.core_scale[-1]
    np.testing.assert_allclose(res[:,0],expected,atol=1e-12)

def test_review_preserves_calculations_and_marks_interpretation_limits():
    dest=OUT.parent/'v2';manifest=json.loads((dest/'manifest.json').read_text())
    assert manifest['yield_values_used']==manifest['new_yield_models']==manifest['PRED_predictions']==0
    assert manifest['source_manifest_sha256']==sha(OUT/'manifest.json')
    for p,h in manifest['artifacts'].items():assert sha(ROOT/p)==h
    catalog=pd.read_csv(dest/'representation_catalog.csv')
    assert catalog.loc[catalog.block.eq('climate_monthly_between'),'category'].str.startswith('C').all()
    assert catalog.loc[catalog.block.eq('dynamics_original'),'category'].str.startswith('B').all()
    old=pd.read_csv(OUT/'block_comparison.csv');new=pd.read_csv(dest/'block_comparison.csv')
    pd.testing.assert_frame_equal(old,new[old.columns])
