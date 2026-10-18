"""Freeze a finite base-by-proximity factorial before external evaluation."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.indicator_neighborhoods import OUT as SOURCE,REDUCTIONS,TERRAIN,SATELLITE
from src.ct3_residual_conditional.models import CORE
OUT=ROOT/'outputs/modeling/base_distribution_correction/v1'

def main():
    assert not (OUT/'frozen_design.json').exists()
    for sub in ['tables','models','cache','checkpoints','audit','figures']:(OUT/sub).mkdir(parents=True,exist_ok=True)
    original=json.loads((SOURCE/'frozen_design.json').read_text());joint=json.loads((ROOT/'outputs/modeling/joint_simplification/v1/frozen_design.json').read_text());definitions=original['definitions'];local=joint['variants']['DROP_JOINT']['columns'];coords=['base_centroid_lat','base_centroid_lon'];physical=sum([definitions[k]['columns'] for k in ['soil_texture_phase','geologic_composition','geologic_distances']],[])
    fields=dict(CT3=list(CORE),RAW7=local+coords,EXPERT7=local+coords+list(CORE),EQUAL7=local+coords+list(CORE),SHARES=local+coords+list(CORE)+definitions['geologic_composition']['columns'],J7=local+coords+list(CORE)+physical)
    def canonical(c):return 'slope_mean' if c in ['topo_official__slope__mean','relief::TOPO_BASIC_slope_mean'] else c
    inventory=[]
    for base,columns in fields.items():
        for geometry,extra in [('BASE',[]),('GLOBAL',REDUCTIONS['R3']),('GEO',REDUCTIONS['R3']+coords),('PHYSICAL',REDUCTIONS['R3']+physical+TERRAIN),('SATELLITE',REDUCTIONS['R3']+SATELLITE)]:
            names=sorted(set(map(canonical,columns+extra)));inventory.append(dict(base=base,geometry=geometry,input_count=len(names),fields=names))
    files=[ROOT/'scripts/489_prepare_base_distribution_correction.py',ROOT/'scripts/490_run_base_distribution_correction.py',ROOT/'src/base_distribution_correction.py',ROOT/'tests/test_base_distribution_correction.py',ROOT/'documentation/base_distribution_correction_design.md',SOURCE/'frozen_design.json',SOURCE/'tables/oof_residuals.parquet',SOURCE/'delivery_audit.json',ROOT/'outputs/modeling/joint_simplification/v1/frozen_design.json']
    protected=dict(original['source_sha256']);protected.update({str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files})
    cfg=dict(status='frozen',bases=list(fields),new_bases=['RAW7','EXPERT7','EQUAL7','SHARES'],representations=fields,inventory=inventory,geometries=['GEO','PHYSICAL','SATELLITE'],uses=['SUPPORT','NOVELTY'],k_grid=[8,16,24,48,72],amplitudes=[0,.25,.5],corrector='R3 unchanged EN alpha .01 l1 .5; train-only transforms; final cap .25',definitions=definitions,outer_folds=65,workers=4,entries=48,new_outer_systems=2860,exploratory=True,no_PRED=True,no_final138_fit=True,no_champion_change=True,source_sha256=protected)
    (OUT/'frozen_design.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8');print('Frozen 6 bases x [baseline + global R3 + 6 local-distribution R3 uses]; 48 entries.')

if __name__=='__main__':main()
