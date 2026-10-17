"""Freeze four joint reductions suggested by the preceding role experiment."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=ROOT/'outputs/modeling/joint_simplification/v1';PREV=ROOT/'outputs/modeling/signal_role_allocation/v1'


def build_design(old):
    full=old['variants']['FULL12']['columns'];water=old['groups']['HISTORY_WATER'];soil=old['groups']['SOIL'];joint=[c for c in full if c not in water+soil];assert len(joint)==7 and not set(joint)&set(water+soil)
    variants={}
    for v in ['DROP_HISTORY_WATER','DROP_SOIL']:
        variants[v]={**old['variants'][v],'legacy_variant':v}
    variants['DROP_JOINT']=dict(type='small',columns=joint,mode='raw',correction_columns=[],correction_atoms=[],legacy_variant=None)
    both=['soil_texture_phase','geologic_composition','geologic_distances'];shares=['geologic_composition']
    recipes={
        'J7_BOTH':dict(variant='DROP_JOINT',gate_atoms=both,input_count=28),
        'J9_SHARES':dict(variant='DROP_SOIL',gate_atoms=shares,input_count=25),
        'J10_SHARES':dict(variant='DROP_HISTORY_WATER',gate_atoms=shares,input_count=26),
        'J7_SHARES':dict(variant='DROP_JOINT',gate_atoms=shares,input_count=23)}
    references=dict(J7_BOTH='DROP_SOIL',J9_SHARES='DROP_SOIL',J10_SHARES='DROP_HISTORY_WATER',J7_SHARES='J7_BOTH')
    return dict(variants=variants,recipes=recipes,references=references,gate_k=[4,8],removed_groups=dict(history_water=water,soilgrids=soil))


def main():
    if (OUT/'frozen_design.json').exists():raise FileExistsError('Preserve joint design')
    for p in [OUT]+[OUT/x for x in ['models','cache','checkpoints','tables','diagnostics','audit']]:p.mkdir(parents=True,exist_ok=True)
    old=json.loads((PREV/'frozen_design.json').read_text());cfg=build_design(old);protected=dict(old['source_sha256'])
    for f in [PREV/'frozen_design.json',PREV/'tables/predictions.parquet',PREV/'manifest.json',PREV/'delivery_audit.json',ROOT/'scripts/445_prepare_joint_simplification.py',ROOT/'scripts/446_run_joint_simplification.py',ROOT/'tests/test_joint_simplification.py',ROOT/'documentation/joint_simplification_design.md']:
        protected[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
    cfg['source_sha256']=protected;(OUT/'frozen_design.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8');print('Frozen: four fixed joint simplifications; only K and existing EN parameters selected internally.')


if __name__=='__main__':main()
