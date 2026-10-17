"""Freeze twelve paired exploratory alternatives before any new external fit."""
from pathlib import Path
import sys,json,hashlib
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.difficult_case_signals import OUT,OWN,JOINT,SIGNALS,load_assets
from src.geoc_bridge import OLD
from src.geoc_reverse import GRID,AMPLITUDES


def main():
    if (OUT/'frozen_design.json').exists():raise FileExistsError('Preserve frozen design')
    for name in ['cache','checkpoints','models','tables','audit','figures']:(OUT/name).mkdir(parents=True,exist_ok=True)
    original=json.loads((JOINT/'frozen_design.json').read_text())
    variants={};recipes={};references={}
    for label,base,reference,count in [('J7','DROP_JOINT','J7_BOTH',28),('E9','DROP_SOIL','DROP_SOIL',30),('E10','DROP_HISTORY_WATER','DROP_HISTORY_WATER',31)]:
        for block,columns in [('ET',[SIGNALS['evi_change'],SIGNALS['tpi']]),('ETN',list(SIGNALS.values()))]:
            for placement in ['LOCAL','CORRECTION']:
                name=f'{label}_{block}_{placement}';v=dict(original['variants'][base]);v['columns']=list(v['columns']);v['legacy_variant']=None
                if placement=='LOCAL':v['columns']+=columns
                else:v['correction_columns']=columns
                variants[name]=v;recipes[name]=dict(variant=name,gate_atoms=original['recipes']['J7_BOTH']['gate_atoms'],input_count=count+len(columns),base_label=label,block=block,placement=placement)
                references[name]=reference
    sources=[OWN,JOINT/'frozen_design.json',JOINT/'tables/predictions.parquet',OLD/'cache/execution_plan.joblib',OLD/'cache/frozen65_splits.joblib',OLD/'cache/groups.csv',ROOT/'src/difficult_case_signals.py',ROOT/'src/signal_role_allocation.py',ROOT/'src/geoc_signal_research.py',ROOT/'src/conditional_local_phases.py',ROOT/'scripts/454_prepare_difficult_case_signals.py',ROOT/'scripts/455_run_difficult_case_signals.py']
    sources+=sorted((JOINT/'models').glob('*.joblib'))
    cfg=dict(status='frozen_before_training',exploratory=True,selection_warning='Features nominated after inspecting external residuals; reused folds are not independent confirmation.',variants=variants,recipes=recipes,references=references,gate_k=original['gate_k'],corrector_grid=GRID,amplitudes=AMPLITUDES,signal_columns=SIGNALS,outer_folds=65,local_recipe=dict(k=24,alpha=30,distance_power=1),placement_rationale='Primary: local predictors describing vegetation trajectory and microtopography. Alternative: additions to regularized compact residual corrector. Keep CT3 and gate feature atoms unchanged; reselect allowed correction and gate parameters internally.',selection_policy='No external winner selector, regional rules, case removal or automatic champion promotion.',no_PRED=True,no_final138_fit=True,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})
    (OUT/'frozen_design.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    a=load_assets();ids=a['a']['train'].ID_POLIGONO.tolist();raw=a['role_frame'][list(SIGNALS.values())].copy();raw.insert(0,'ID_POLIGONO',ids);raw.to_parquet(OUT/'cache/additions138_target_free.parquet',index=False)
    pd.DataFrame([dict(feature=c,n_valid=raw[c].notna().sum(),n_distinct=raw[c].nunique(),minimum=raw[c].min(),median=raw[c].median(),maximum=raw[c].max()) for c in SIGNALS.values()]).to_csv(OUT/'audit/input_support.csv',index=False)
    print('Frozen: 3 references x 2 fixed blocks x 2 placements = 12 recipes, same 65 folds; target-free alignment checked.')


if __name__=='__main__':main()
