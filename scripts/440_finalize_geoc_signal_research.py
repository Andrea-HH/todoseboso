"""Validate delivered OOF references and add descriptive audits to the workbook."""
from pathlib import Path
import sys,json,hashlib
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=ROOT/'outputs/modeling/geoc_signal_research/v1'


def difference(a,b,name,other=None):
    keys=['protocol','repeat','fold','ID_POLIGONO'];other=other or name
    x=a[a.experiment==name][keys+['y_pred','y_true']].merge(b[b.experiment==other][keys+['y_pred','y_true']],on=keys,suffixes=('','_ref'),validate='one_to_one')
    assert len(x)==1794 and np.array_equal(x.y_true,x.y_true_ref)
    err=float(np.max(abs(x.y_pred-x.y_pred_ref)));assert err<1e-12
    return err


def main():
    if (OUT/'delivery_audit.json').exists():raise FileExistsError('Preserve delivered audit')
    manifest=json.loads((OUT/'manifest.json').read_text());assert manifest['status']=='complete' and manifest['exact_replay_max_difference']<1e-12
    p=pd.read_parquet(OUT/'tables/predictions.parquet');prev=pd.read_parquet(ROOT/'outputs/modeling/conditional_local_phases/v1/tables/predictions.parquet');checks={}
    for n in ['CT3','LEADER']:
        checks[n]=difference(p,prev,n)
    for n,other in [('P1_GLOBAL','P1_GLOBAL_global'),('P1_BOTH','P1_BOTH_clusters'),('P1_TEXTURE','P1_TEXTURE_clusters')]:checks[n]=difference(p,prev,n,other)
    municipal=p[p.protocol=='municipality'];wide=municipal.pivot(index=['repeat','fold','ID_POLIGONO'],columns='experiment',values='y_pred');checks['unseen_municipality_correction']=float(abs(wide.C_CORRECT_MUNICIPALITY-wide.CT3).max());checks['unseen_municipality_gate']=float(abs(wide.D_GATE_MUNICIPALITY-wide.P1_GLOBAL).max());assert max(checks.values())<1e-12
    inventory=pd.read_csv(OUT/'diagnostics/reduced_mixture_input_inventory.csv');counts=inventory.groupby('bundle').feature.nunique().to_dict();assert counts=={'EXPANDED30':51,'SMALL12':33}
    replay=pd.read_csv(OUT/'audit/exact_replay.csv');assert len(replay)==65*59 and len(p)==62*1794
    with pd.ExcelWriter(OUT/'resultados_senales_y_reduccion_GeoC.xlsx',engine='openpyxl',mode='a',if_sheet_exists='error') as writer:
        for file,sheet in [('diagnostics/local_shrinkage_summary.csv','Complejidad_local'),('diagnostics/prediction_agreement_summary.csv','Concordancia'),('diagnostics/reduced_mixture_input_inventory.csv','Entradas_mezclas'),('diagnostics/execution_by_fold.csv','Tiempo_por_fold'),('diagnostics/omission_deltas.csv','Sensibilidad_omisiones'),('audit/deep_fallbacks.csv','Limites_anidamiento')]:pd.read_csv(OUT/file).to_excel(writer,sheet_name=sheet,index=False)
    protected=json.loads((OUT/'frozen_design.json').read_text())['source_sha256'];assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in protected.items())
    sources=['scripts/438_summarize_geoc_signal_research.py','scripts/439_geoc_signal_structural_diagnostics.py','scripts/440_finalize_geoc_signal_research.py','documentation/geoc_signal_research_results.md'];audit=dict(status='complete',oof_rows=len(p),models_or_controls=62,replayed_fold_models=len(replay),reference_checks=checks,reduced_mixture_distinct_input_fields=counts,protected_sources_unchanged=True,no_new_final_fit=True,no_new_PRED=True,source_sha256={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sources});(OUT/'delivery_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8');print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
