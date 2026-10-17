"""Freeze the user's continuous-feature alternative, without changing tree results."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.neighbor_signal_linear import OUT,TREE_OUT
from src.geoc_reverse import GRID


def main():
    if (OUT/'frozen_design.json').exists():raise FileExistsError('Preserve continuous contrast design')
    assert (TREE_OUT/'execution_complete.json').exists()
    for name in ['cache','checkpoints','models','tables','audit','figures']:(OUT/name).mkdir(parents=True,exist_ok=True)
    original=json.loads((TREE_OUT/'frozen_design.json').read_text());protected=dict(original['source_sha256'])
    for file in [ROOT/'src/neighbor_signal_linear.py',ROOT/'scripts/464_run_neighbor_signal_linear.py',ROOT/'scripts/465_prepare_neighbor_signal_linear.py',ROOT/'tests/test_neighbor_signal_linear.py',TREE_OUT/'frozen_design.json',TREE_OUT/'execution_complete.json',TREE_OUT/'tables/predictions.parquet']:protected[str(file)]=hashlib.sha256(file.read_bytes()).hexdigest()
    cfg=dict(status='frozen_before_continuous_training',exploratory=True,recipes={k+'_LINEAR':dict(neighborhood=k,use='LINEAR') for k in ['GEO','COMPACT']},grid=[dict(**params,amplitude=amp) for params in GRID for amp in [.5,1.]],null_candidate=dict(alpha=1.,l1_ratio=.9,amplitude=0.),intercept=False,centering=False,normalization='Training SD only, constant contrast columns dropped; zero contrast implies zero adjustment.',residual_cap_t_ha=.5,features=original['features'],signals=original['signals'],k=24,outer_folds=65,base='Exact external J7; same nested crossfitted calibration as the tree experiment, with read-only warm component reuse.',source_sha256=protected,no_PRED=True,no_final138_fit=True,no_champion_change=True,workers=8,global_reference_note='Subtracting a single training-wide mean/median is only a reparameterization with a linear intercept; use parcel-specific neighbor references to provide different information.')
    (OUT/'frozen_design.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8');print('Frozen two continuous zero-intercept alternatives; same 65 folds, null plus 24 configurations each.')


if __name__=='__main__':main()
