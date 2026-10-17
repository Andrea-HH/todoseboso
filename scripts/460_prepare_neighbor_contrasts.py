"""Freeze four neighbor-contrast alternatives and two exact references."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.neighbor_signal_contrasts import OUT,JOINT,SIGNALS
from src.difficult_case_signals import OWN
from src.geoc_bridge import OLD


def main():
    if (OUT/'frozen_design.json').exists():raise FileExistsError('Preserve frozen experiment')
    for name in ['checkpoints','models','cache','tables','figures','audit']:(OUT/name).mkdir(parents=True,exist_ok=True)
    sources=[ROOT/'src/neighbor_signal_contrasts.py',ROOT/'src/difficult_case_signals.py',ROOT/'scripts/460_prepare_neighbor_contrasts.py',ROOT/'scripts/461_run_neighbor_contrasts.py',ROOT/'tests/test_neighbor_signal_contrasts.py',OWN,JOINT/'tables/predictions.parquet',JOINT/'frozen_design.json',OLD/'cache/execution_plan.joblib',OLD/'cache/frozen65_splits.joblib']+sorted((JOINT/'models').glob('*.joblib'))
    protected=dict(json.loads((JOINT/'frozen_design.json').read_text())['source_sha256']);protected.update({str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources})
    recipes={f'{neighborhood}_{use}':dict(neighborhood=neighborhood,use=use) for neighborhood in ['GEO','COMPACT'] for use in ['ATTENUATE','RESIDUAL']}
    cfg=dict(status='frozen_before_training',exploratory=True,recipes=recipes,signals=SIGNALS,k=24,tie_policy='Include all neighbors tied at kth distance; exclude self by parcel position.',features='Three signed local robust contrasts and three signed globally scaled differences; clip each to +/-6; local denominator max(1.4826*MAD_neighbors,0.25*SD_training,1e-8).',grid=[dict(depth=d,leaf=n,amplitude=a) for d in [1,2] for n in [15,25] for a in [.5,1.]],null_candidate=dict(depth=1,leaf=25,amplitude=0.),leaf_prior=20,residual_cap_t_ha=.5,outer_folds=65,protocols=['random','climate_profile','municipality','spatial'],base='Exact archived J7_BOTH externally; nested J7 retuned within each training for calibration.',deep_support_policy='At one remaining territorial group, fixed CT3 alpha=1,l1_ratio=.5 and local-only expert; uncalibratable inner gate predicts CT3. Never random-CV substitution. Record each fallback.',validation='Frozen outer and inner splits. Threshold/depth/leaf/amplitude selected inside outer training. Crossfitted calibration features use the matching base-training neighbors, never self or held targets.',no_final138_fit=True,no_PRED=True,no_champion_change=True,source_sha256=protected)
    (OUT/'frozen_design.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8');print('Frozen four recipes, null plus eight configurations each, 65 original folds.')


if __name__=='__main__':main()
