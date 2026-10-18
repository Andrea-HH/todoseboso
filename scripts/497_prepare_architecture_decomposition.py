"""Freeze base simplification factorial before training."""
from pathlib import Path
import sys,json,hashlib,itertools
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.architecture_decomposition import OUT,local_sets
from src.learned_r3_protocol import load_design
from src.indicator_neighborhoods import REDUCTIONS
from src.ct3_residual_conditional.models import CORE

def main():
    assert not (OUT/'frozen_design.json').exists()
    for sub in ['tables','models','checkpoints','cache','audit','figures']:(OUT/sub).mkdir(parents=True,exist_ok=True)
    previous=load_design();geology=previous['definitions']['geologic_composition']['columns'];recipes={}
    for local,internal,gate in itertools.product(local_sets(),['OFF','ON'],['RAW','PCA2','GLOBAL']):
        columns=list(CORE)+local_sets()[local]+['base_centroid_lat','base_centroid_lon']+(geology if gate!='GLOBAL' else []);recipes[local+'_'+internal+'_'+gate]=dict(local=local,internal=internal,gate=gate,base_input_count=len(set(columns)),mask_input_count=len(set(columns+REDUCTIONS['R3'])),fields=columns+REDUCTIONS['R3'])
    files=[ROOT/'src/architecture_decomposition.py',ROOT/'scripts/497_prepare_architecture_decomposition.py',ROOT/'scripts/498_run_architecture_decomposition.py',ROOT/'tests/test_architecture_decomposition.py',ROOT/'documentation/architecture_decomposition_design.md',ROOT/'outputs/modeling/learned_r3_weight/v1/delivery_audit.json',ROOT/'outputs/modeling/learned_r3_weight/v1/tables/predictions.parquet'];protected=dict(previous['source_sha256']);protected.update({str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files});cfg=dict(status='frozen',recipes=recipes,local_sets=local_sets(),gate_k=[4,8],strengths=[0.,.5,1.],workers=4,outer_folds=65,base_recipes=48,entries=99,primary_pairs=103,paired_tests=412,internal_corrector_hyperparameters='FULL7 same training context; refit coefficients on each ablation OOF residuals; OFF removed entirely',R3='unchanged; own nested OOF residuals and availability MASK',exploratory=True,no_PRED=True,no_final138_fit=True,no_champion_change=True,source_sha256=protected);(OUT/'frozen_design.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8');print('Frozen: 8 local sets x 2 internal corrections x 3 gates; base/MASK +3 controls =99 entries.')

if __name__=='__main__':main()
