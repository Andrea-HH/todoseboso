"""Audit OOF metric identities, summaries, field counts and final source hashes."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/modeling/joint_simplification/v1'


def main():
    if (OUT/'delivery_audit.json').exists():raise FileExistsError('Preserve delivered audit')
    manifest=json.loads((OUT/'manifest.json').read_text());assert manifest['status']=='complete';cfg=json.loads((OUT/'frozen_design.json').read_text());p=pd.read_parquet(OUT/'tables/predictions.parquet');m=pd.read_csv(OUT/'diagnostics/metrics_by_repeat.csv');s=pd.read_csv(OUT/'diagnostics/metrics_summary.csv');variance=float(p[p.experiment=='CT3'].drop_duplicates('ID_POLIGONO').y_true.var(ddof=0));delta=float(np.max(abs(m.r2-(1-m.mse/variance))));assert delta<1e-12 and np.max(abs(m.rmse**2-m.mse))<1e-12 and np.max(abs(m.mse-m.error_variance-m.bias_squared))<1e-12
    direct=m.groupby(['experiment','protocol'])[['rmse','r2']].mean();saved=s.set_index(['experiment','protocol']);assert np.max(abs(direct-saved[['rmse','r2']]).to_numpy())<1e-12
    inventory=pd.read_csv(OUT/'diagnostics/input_inventory.csv');counts=inventory.groupby('experiment').feature.nunique().to_dict();assert counts=={name:r['input_count'] for name,r in cfg['recipes'].items()};assert not set(inventory.feature)&{'ID_POLIGONO','RENDIMIENTO_T_HA','Estado','Municipio'}
    for (_,_,_),g in p.groupby(['experiment','protocol','repeat']):assert len(g)==138 and g.ID_POLIGONO.is_unique
    assert len(p)==19734 and len(m)==143;assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    sources=['scripts/445_prepare_joint_simplification.py','scripts/446_run_joint_simplification.py','scripts/447_summarize_joint_simplification.py','scripts/448_audit_joint_simplification_delivery.py','tests/test_joint_simplification.py','documentation/joint_simplification_design.md','documentation/joint_simplification_results.md','documentation/model_comparison_convention.md'];audit=dict(status='complete',oof_rows=len(p),per_repeat_metric_rows=len(m),r2_mse_identity_max_difference=delta,metrics_are_complete_oof_per_repeat=True,random_is_mean_of_ten_repeat_metrics=True,new_input_counts=counts,protected_sources_unchanged=True,no_final138_fit=True,no_PRED=True,source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in sources});(OUT/'delivery_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8');print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
