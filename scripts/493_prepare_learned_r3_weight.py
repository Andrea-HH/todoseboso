"""Freeze learned/asymmetric weighting before training and external evaluation."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.learned_r3_weight import OUT,FEATURES
from src.base_distribution_correction import load_design

def main():
    assert not (OUT/'frozen_design.json').exists()
    for sub in ['tables','models','checkpoints','cache','audit','figures']:(OUT/sub).mkdir(parents=True,exist_ok=True)
    previous=ROOT/'outputs/modeling/base_distribution_correction/v1';old=load_design(previous);recipes=dict(MASK=[dict(penalty=0.,strength=a) for a in [0.,.5,1.]],CONSTANT=[dict(penalty=0.,strength=a) for a in [0.,1.]])
    for name in ['ASYM','LEARNED','LEARNED_ASYM']:recipes[name]=[dict(penalty=10.,strength=0.)]+[dict(penalty=p,strength=1.) for p in [1.,10.]]
    files=[ROOT/'src/learned_r3_weight.py',ROOT/'scripts/493_prepare_learned_r3_weight.py',ROOT/'scripts/494_run_learned_r3_weight.py',ROOT/'tests/test_learned_r3_weight.py',ROOT/'documentation/learned_r3_weight_design.md',previous/'frozen_design.json',previous/'amendment_01.json',previous/'delivery_audit.json',previous/'tables/predictions.parquet'];protected=dict(old['source_sha256']);protected.update({str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files});cfg=dict(status='frozen',bases=['CT3','J7','SHARES'],recipes=recipes,definitions=old['definitions'],gate_features=FEATURES,local_geometry='SATELLITE, k24 fixed',penalties=[1.,10.],minimum_sign_support=15,weight_bounds=[0.,1.],null_enabled=True,correction_cap=.25,outer_folds=65,workers=4,new_recipes=15,outer_systems=975,comparisons=228,no_PRED=True,no_final138_fit=True,no_champion_change=True,exploratory=True,source_sha256=protected);(OUT/'frozen_design.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8');print('Frozen 15 new configurations and 9 exact archived controls, 65 outer folds.')

if __name__=='__main__':main()
