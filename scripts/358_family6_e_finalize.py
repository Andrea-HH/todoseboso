"""Immutable-reference verification and F6-E versioned deliverables; no fitting."""
import sys,json,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd,sklearn,scipy
from src.family_6.expansion import execution as e

def main():
    if (e.OUT/'manifest.json').exists():raise FileExistsError('Completed F6-E immutable')
    cases=[]
    for name in ['unit_tests.xml','integration_tests.xml']:
        root=ET.parse(e.OUT/'audit'/name).getroot();assert not root.findall('.//failure') and not root.findall('.//error')
        cases+=root.findall('.//testcase')
    assert len(cases)==9
    protected=pd.read_csv(e.OUT/'audit/protected_inputs.csv')
    for row in protected.itertuples():assert e.base.design.sha(e.ROOT/row.path)==row.sha256,row.path
    cfg=json.loads((e.OUT/'frozen_design.json').read_text())
    for path,h in {**cfg['source_sha'],**cfg['cache_sha']}.items():assert e.base.design.sha(e.ROOT/path)==h
    reg=pd.read_csv(e.OUT/'tables/fit_registry.csv');p=pd.read_parquet(e.OUT/'tables/oof_predictions.parquet')
    assert len(reg)==6435 and len(p)==13938 and set(reg.experiment)==set(e.SPECS)
    assert len(list((e.OUT/'models').glob('*.joblib')))==975 and len(list((e.OUT/'checkpoints').glob('*.joblib')))==195
    decision=json.loads((e.OUT/'report/decision.json').read_text());assert set(decision['executed'])==set(e.SPECS)
    info=dict(n_forest_fits=6435,n_outer=195,n_inner_candidates=6240,n_saved_selected_models=975,n_original_E0_models_recovered=325,n_trees_per_forest=384,n_trees_fitted=6435*384,workers=6,wall_seconds=float((e.OUT/'audit/wall_seconds.txt').read_text()),sum_fit_seconds=float(reg.seconds.sum()),n_fit_warnings=int(reg.warnings.apply(lambda s:len(json.loads(s))).sum()),no_E4_E5=True,no_final_training=True,no_PRED=True)
    (e.OUT/'audit/execution_diagnostics.json').write_text(json.dumps(info,indent=2),encoding='utf8')
    environment=dict(python=sys.version,platform=sys.platform,sklearn=sklearn.__version__,numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,joblib=e.joblib.__version__)
    (e.OUT/'audit/runtime_versions.json').write_text(json.dumps(environment,indent=2),encoding='utf8')
    (e.OUT/'audit/runtime_environment_note.txt').write_text('Windows workers emitted threadpoolctl warning for simultaneous Intel libiomp and LLVM libomp, whose message describes Linux incompatibility. All scientific fits and diagnostics completed. Model fit warnings are captured separately. No scientific limits changed.\n',encoding='utf8')
    verification=f'\n\n## Verificación final\n\nPasaron nueve pruebas unitarias y de integración: aislamiento/restauración del adaptador, bloques/regulación originales, soporte antes de predicción, permutación conjunta/constancia, replay de975 modelos guardados, selección entre ocho candidatos y particiones internas originales, E0/OOF/métricas exactas, gates de soporte/hojas y hashes de código/cache/folds. Se verificaron {len(protected)} archivos anteriores sin cambios. Se recuperó E0, se ajustaron195 modelos externos y6240 candidatos internos (6435 bosques en total), y se guardaron13938 filas OOF entre referencias y extensiones. No se ejecutaron E4/E5 ni F7, no se ajustó un modelo final y no se generaron59 predicciones PRED.\n'
    report=e.OUT/'report/synthesis.md';report.write_text(report.read_text(encoding='utf8')+verification,encoding='utf8')
    (e.ROOT/'documentation/family6_expansion.md').write_text(report.read_text(encoding='utf8'),encoding='utf8')
    (e.ROOT/'documentation/family6_expansion_frozen_design.md').write_text((e.OUT/'report/evidence_and_frozen_design.md').read_text(encoding='utf8'),encoding='utf8')
    pd.DataFrame([dict(path=p.relative_to(e.ROOT).as_posix(),producer='family_6.expansion execution/reporting/diagnostics/interpretation',inputs='exact E0 and contextual references; immutable original65folds; authorized independently tuned E1-E3',exploratory=True) for p in list((e.OUT/'tables').glob('*'))+list((e.OUT/'figures').glob('*'))]).to_csv(e.OUT/'audit/artifact_provenance.csv',index=False)
    files=[p for p in e.OUT.rglob('*') if p.is_file() and p.name!='manifest.json']+list((e.ROOT/'src/family_6/expansion').glob('*.py'))
    files+=[e.ROOT/p for p in ['scripts/356_family6_e_prepare.py','scripts/357_family6_e_bagging.py','scripts/358_family6_e_finalize.py','tests/test_family6_e_unit.py','tests/test_family6_e_integration.py','documentation/family6_expansion.md','documentation/family6_expansion_frozen_design.md']]
    manifest=dict(status='complete',version='family_6/expansion/v1',decision=decision,n_labels=138,n_outer_folds=65,n_fits=6435,n_saved_models=975,n_oof_rows=13938,tests='9 passed',protected_files_verified=len(protected),final_training=False,PRED_predictions=False,champion_modified=False,F6_original_modified=False,E4_E5_executed=False,F7_executed=False,artifacts={p.relative_to(e.ROOT).as_posix():e.base.design.sha(p) for p in files})
    (e.OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8');print(json.dumps(info,indent=2))
if __name__=='__main__':main()
