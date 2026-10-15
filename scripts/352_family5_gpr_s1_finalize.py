"""Finalize S1 with replay tests and immutable-reference hashes; no model fits."""
import sys,json,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from src.family_5.gpr_s1 import execution as e

def main():
    assert not (e.OUT/'manifest.json').exists()
    import xml.etree.ElementTree as ET
    xml=e.OUT/'audit/preliminary_tests.xml'
    root=ET.parse(xml).getroot();cases=root.findall('.//testcase')
    assert len(cases)==8 and not root.findall('.//failure') and not root.findall('.//error')
    (e.OUT/'audit/tests.txt').write_text('8 passed: tests/test_family5_gpr_s1_math.py and tests/test_family5_gpr_s1_integration.py. Full replay of 1755 S1 and 195 archived reference models. Machine-readable results: preliminary_tests.xml. Observed environment warning: runtime_environment_note.txt.\n',encoding='utf8')
    protected=pd.read_csv(e.OUT/'audit/protected_inputs.csv')
    for row in protected.itertuples():assert e.old.design.sha(e.ROOT/row.path)==row.sha256,row.path
    reg=pd.read_csv(e.OUT/'tables/fit_registry.csv');starts=pd.read_json(e.OUT/'tables/optimizer_starts.json')
    assert len(reg)==1755 and len(starts)==5265
    timing=dict(wall_seconds=float((e.OUT/'audit/wall_seconds.txt').read_text()),sum_fit_seconds=float(reg.seconds.sum()),selected_optimizer_failures=int((~reg.selected_optimizer_converged).sum()),max_covariance_condition=float(reg.covariance_condition.max()),minimum_covariance_eigenvalue=float(reg.min_covariance_eigenvalue.min()),n_fits=1755,n_outer=195,n_inner=1560,n_optimizer_starts=5265,n_bound_hits=int(reg.bound_hits.apply(lambda s:len(json.loads(s))).sum()),n_fit_warnings=int(reg.warnings.apply(lambda s:len(json.loads(s))).sum()))
    (e.OUT/'audit/execution_diagnostics.json').write_text(json.dumps(timing,indent=2),encoding='utf8')
    text=(e.OUT/'report/synthesis.md').read_text(encoding='utf8')+f'\n\n## Integridad y reproducibilidad\n\nPasaron ocho pruebas matemáticas y de integración, incluyendo replay de los 1755 ajustes guardados. Se verificaron {len(protected)} archivos anteriores protegidos. Se conservan 195 modelos externos, 1560 internos, 5265 inicios de optimización y 10764 filas OOF (tres referencias y tres sensibilidades). No se ajustó ningún modelo final ni se generaron predicciones PRED. Diagnósticos numéricos y tiempos: `audit/execution_diagnostics.json`; advertencias del entorno y pruebas: `audit/tests.txt`.\n'
    (e.OUT/'report/synthesis.md').write_text(text,encoding='utf8');(e.ROOT/'documentation/family5_gpr_s1.md').write_text(text,encoding='utf8')
    pd.DataFrame([dict(path=p.relative_to(e.ROOT).as_posix(),producer='S1 execution/reporting/interpretation',inputs='frozen 65 splits; train-only approved fits; immutable archived reference OOF',exploratory=True) for p in list((e.OUT/'tables').glob('*'))+list((e.OUT/'figures').glob('*'))]).to_csv(e.OUT/'audit/artifact_provenance.csv',index=False)
    files=[p for p in e.OUT.rglob('*') if p.is_file() and p.name!='manifest.json']
    files+=list((e.ROOT/'src/family_5/gpr_s1').glob('*.py'))
    files+=[e.ROOT/p for p in ['scripts/351_family5_gpr_s1.py','scripts/352_family5_gpr_s1_finalize.py','tests/test_family5_gpr_s1_math.py','tests/test_family5_gpr_s1_integration.py','documentation/family5_gpr_s1.md']]
    manifest=dict(status='complete',version='gpr_s1/v1',experiments=list(e.SPECS),reference_experiments=['F5-00-C','F5-01','C-T3'],n_outer_folds=65,n_labels=138,n_fits=1755,n_oof=10764,protected_files_verified=len(protected),tests='8 passed',PRED_predictions=False,champion_modified=False,additional_experiments=False,artifacts={p.relative_to(e.ROOT).as_posix():e.old.design.sha(p) for p in files})
    (e.OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8');print(json.dumps(timing,indent=2))
if __name__=='__main__':main()
