"""Target-free additions for frozen exploratory role-allocation sensitivities."""
from pathlib import Path
import importlib.util
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/modeling/difficult_case_signals/v1'
OWN = ROOT / 'outputs/modeling/experimental_pls1867/v1/cache/train138_1867.parquet'
JOINT = ROOT / 'outputs/modeling/joint_simplification/v1'
SIGNALS = {
    'evi_change': 'PLANET_evi_promedio_last_minus_first',
    'tpi': 'TOPO_ADV_tpi_3x3_mean',
    'ndvi_dynamics': 'S2_ndvi_derived_lower_gap_max_growth_rate',
}


def load_assets():
    spec = importlib.util.spec_from_file_location('runner446_signals', ROOT/'scripts/446_run_joint_simplification.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    a = runner.load_assets()
    ids = a['a']['train'].ID_POLIGONO.tolist()
    raw = pd.read_parquet(OWN).set_index('ID_POLIGONO')
    assert raw.index.is_unique and set(ids) == set(raw.index)
    for column in SIGNALS.values():
        assert column not in a['features197'] and column not in a['role_frame']
        values = pd.to_numeric(raw.loc[ids, column], errors='raise').to_numpy(float)
        assert np.isfinite(values).sum() >= 100
        a['features197'][column] = a['features197'].ID_POLIGONO.map(raw[column])
        a['role_frame'][column] = values
        np.testing.assert_equal(a['features197'].iloc[a['a']['train_global']][column].to_numpy(), values)
        assert a['features197'].loc[~a['features197'].ID_POLIGONO.isin(ids),column].isna().all()
    a['variants'] = json.loads((OUT/'frozen_design.json').read_text())['variants']
    return a
