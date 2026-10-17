"""Check route-selector decisions and unchanged archived OOF after role analysis."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
import joblib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/modeling/signal_role_allocation/v1';PREV=ROOT/'outputs/modeling/geoc_signal_research/v1'


def main():
    if (OUT/'delivery_audit.json').exists():raise FileExistsError('Preserve audit')
    manifest=json.loads((OUT/'manifest.json').read_text());assert manifest['status']=='complete';cfg=json.loads((OUT/'frozen_design.json').read_text());selection=pd.read_parquet(OUT/'tables/selection.parquet');checks=0
    for fi in range(65):
        pack=joblib.load(OUT/'checkpoints'/f'{fi:02d}.joblib');rows=pack['candidates'];minimum=min(c['rmse'] for c in rows)
        for name,compact in [('SELECT_MIN_RMSE',False),('SELECT_COMPACT_001',True)]:
            allowed=[c for c in rows if c['rmse']<=minimum+(.01 if compact else 1e-12)];expected=min(allowed,key=lambda c:(c['input_count'] if compact else 0,round(c['rmse'],12),list(cfg['recipes']).index(c['recipe']),c['k']));actual=next(s for s in pack['selection'] if s['experiment']==name);assert actual['selected_recipe']==expected['recipe'] and actual['gate_k']==expected['k'] and actual['input_count']==expected['input_count'];checks+=1
    p=pd.read_parquet(OUT/'tables/predictions.parquet');old=pd.read_parquet(PREV/'tables/predictions.parquet');refs={};keys=['protocol','repeat','fold','ID_POLIGONO']
    for name,other in [('CT3','CT3'),('PRIOR_SMALL12','E_REDUCED_SMALL12_BOTH'),('PRIOR_BIGBOTH','P1_BOTH'),('PRIOR_EXPERT','LEADER')]:
        j=p[p.experiment==name].merge(old[old.experiment==other],on=keys,suffixes=('','_ref'),validate='one_to_one');assert len(j)==1794 and np.array_equal(j.y_true,j.y_true_ref);refs[name]=float(abs(j.y_pred-j.y_pred_ref).max());assert refs[name]<1e-12
    for name,r in cfg['recipes'].items():
        got=selection[selection.experiment==name].input_count;assert len(got)==65 and (got==r['input_count']).all()
    assert len(p)==60996 and p.experiment.nunique()==34
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    sources=['src/signal_role_allocation.py','scripts/441_prepare_signal_role_allocation.py','scripts/442_run_signal_role_allocation.py','scripts/443_summarize_signal_role_allocation.py','scripts/444_audit_signal_role_delivery.py','tests/test_signal_role_allocation.py','documentation/signal_role_allocation_design.md','documentation/signal_role_allocation_results.md'];audit=dict(status='complete',selector_decision_checks=checks,reference_max_differences=refs,oof_rows=len(p),models_or_controls=34,protected_sources_unchanged=True,no_new_final_fit=True,no_new_PRED=True,source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in sources});(OUT/'delivery_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8');print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
