"""F5 evidence and proposal only; no model execution authorized at this stage."""
import sys,json,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.family_5 import gpr_evidence_design as g

def finalize():
    if (g.OUT/'manifest.json').exists():raise FileExistsError('Completed design immutable')
    result=subprocess.run([sys.executable,'-m','pytest','tests/test_family5_gpr_design.py','-q'],cwd=g.ROOT,capture_output=True,text=True)
    (g.OUT/'audit/automated_tests.txt').write_text(result.stdout+'\n'+result.stderr,encoding='utf8')
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    import pandas as pd
    prior=pd.read_csv(g.OUT/'audit/protected_inputs.csv');inventory=pd.read_csv(g.OUT/'tables/candidate_variable_inventory.csv')
    for r in prior.itertuples():assert g.sha(g.ROOT/r.path)==r.sha256
    files=[p for p in g.OUT.rglob('*') if p.is_file() and p.name!='manifest.json']
    for pattern in ['src/family_5/*.py','scripts/348_family5*.py','tests/test_family5*.py','documentation/family5_gpr*.md']:files.extend(g.ROOT.glob(pattern))
    manifest=dict(status='research_and_design_complete_pending_review',family='F5',version='gpr_evidence_design/v1',n_train=138,n_prediction=59,n_candidate_inventory=len(inventory),n_matrix_rows=8,n_GPR_fits=0,n_optimizations=0,n_new_predictive_estimates=0,n_final_PRED_predictions=0,tests='14 passed',protected_files_verified=len(prior),first_recommended='F5-01',champion_residual_execution='suspended until honest three-layer nestedbase available',artifacts={p.relative_to(g.ROOT).as_posix():g.sha(p) for p in files})
    (g.OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print(f'F5 DESIGN COMPLETE;{len(inventory)} variables;14tests;{len(prior)} protected files;0GPRfits')

if __name__=='__main__':
    if '--finalize-only' not in sys.argv:g.run()
    finalize()
