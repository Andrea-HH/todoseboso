"""Freeze bounded block deletions and moves between expert, corrector and gate."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=ROOT/'outputs/modeling/signal_role_allocation/v1';PREV=ROOT/'outputs/modeling/geoc_signal_research/v1'


def main():
    if (OUT/'frozen_design.json').exists():raise FileExistsError('Preserve frozen role design')
    for p in [OUT]+[OUT/x for x in ['models','cache','checkpoints','tables','diagnostics','audit']]:p.mkdir(parents=True,exist_ok=True)
    old=json.loads((PREV/'frozen_design.json').read_text());cols=old['bundles']['SMALL12'];groups=dict(HISTORY_VIGOR=cols[:2],HISTORY_WATER=cols[2:4],CURRENT_DYNAMICS=cols[4:8],SOIL=cols[8:11],SLOPE=cols[11:]);assert len(set(sum(groups.values(),[])))==12
    physical=dict(TEXTURE=['soil_texture_phase'],SHARES=['geologic_composition'],DISTANCES=['geologic_distances']);atoms=sum(physical.values(),[]);variants={};recipes={};refs={}
    def variant(name,main,correction_columns=(),correction_atoms=(),legacy=None,mean=False):
        variants[name]=dict(type='static' if mean else 'small',columns=list(main),mode='raw',correction_columns=list(correction_columns),correction_atoms=list(correction_atoms),legacy_variant=legacy)
    def recipe(name,v,gate_atoms,gate_columns=(),reference='BASE12_BOTH'):
        recipes[name]=dict(variant=v,gate_atoms=list(gate_atoms),gate_columns=list(gate_columns));refs[name]=reference
    variant('FULL12',cols,legacy='SMALL12_raw');variant('MEAN',[],legacy='NEIGHBOR_MEAN',mean=True)
    recipe('BASE12_BOTH','FULL12',atoms,reference='PRIOR_SMALL12')
    recipe('GATE_GLOBAL','FULL12',[])
    recipe('MEAN_BOTH','MEAN',atoms);recipe('MEAN_GLOBAL','MEAN',[],reference='GATE_GLOBAL')
    for label,part in physical.items():
        remaining=[a for a in atoms if a not in part]
        recipe('GATE_ONLY_'+label,'FULL12',part)
        recipe('GATE_NO_'+label,'FULL12',remaining)
        v='PHYS_CORRECT_'+label;variant(v,cols,correction_atoms=part);recipe(v,v,remaining,reference='GATE_NO_'+label)
    for label,part in groups.items():
        remain=[c for c in cols if c not in part];v='DROP_'+label;variant(v,remain);recipe(v,v,atoms)
        moved='MOVE_CORRECT_'+label;variant(moved,remain,correction_columns=part);recipe(moved,moved,atoms,reference=v)
        recipe('MOVE_GATE_'+label,v,atoms,part,reference=v)
    assert len(recipes)==28
    refs.update(SELECT_MIN_RMSE='BASE12_BOTH',SELECT_COMPACT_001='BASE12_BOTH')
    defs=json.loads((ROOT/'outputs/modeling/physical_representation/v1/frozen_design.json').read_text())['atoms']
    for name,spec in recipes.items():
        v=variants[spec['variant']];fields=set(v['columns'])|set(v['correction_columns'])|set(spec['gate_columns'])
        for a in set(v['correction_atoms'])|set(spec['gate_atoms']):fields.update(defs[a]['columns'])
        spec['input_count']=len(fields)+6 # compact4 and coordinates2, disjoint from all other inputs
    protected=dict(old['source_sha256'])
    for f in [PREV/'frozen_design.json',PREV/'tables/predictions.parquet',PREV/'manifest.json',ROOT/'src/signal_role_allocation.py',ROOT/'scripts/441_prepare_signal_role_allocation.py',ROOT/'scripts/442_run_signal_role_allocation.py',ROOT/'tests/test_signal_role_allocation.py',ROOT/'documentation/signal_role_allocation_design.md']:
        protected[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
    cfg=dict(groups=groups,physical_groups=physical,variants=variants,recipes=recipes,references=refs,recipe_count=30,selector_tolerance_rmse=.01,gate_k=[4,8],local_k=24,local_alpha=30,expert_mode='raw',compact_correction_grid=old['source_sha256'].get('grid','same original 12-point EN grid and amplitude 0/.25/.5'),source_sha256=protected)
    (OUT/'frozen_design.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8');print('Frozen: 28 routes + 2 internally selected pipelines; no training yet.')


if __name__=='__main__':main()
