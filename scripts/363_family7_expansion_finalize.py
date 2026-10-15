"""Verify and seal controlled F7 expansion without any scientific fit."""
import sys,json,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd,catboost,xgboost,sklearn,scipy
from src.family_7.expansion import execution as e
def main():
    if (e.OUT/'manifest.json').exists():raise FileExistsError('Completed expansion immutable')
    cases=[]
    for f in ['unit_tests.xml','integration_tests.xml']:
        root=ET.parse(e.OUT/'audit'/f).getroot();assert not root.findall('.//failure') and not root.findall('.//error');cases+=root.findall('.//testcase')
    assert len(cases)==7
    protected=pd.read_csv(e.OUT/'audit/protected_inputs.csv')
    for row in protected.itertuples():assert e.base.design.sha(e.ROOT/row.path)==row.sha256,row.path
    cfg=json.loads((e.OUT/'frozen_design.json').read_text())
    for p,h in {**cfg['source_sha'],**cfg['cache_sha']}.items():assert e.base.design.sha(e.ROOT/p)==h
    reg=pd.read_csv(e.OUT/'tables/fit_registry.csv');p=pd.read_parquet(e.OUT/'tables/oof_predictions.parquet')
    assert len(reg)==6435 and set(reg.experiment)==set(e.SPECS) and len(p)==17526
    assert len(list((e.OUT/'models').glob('*.joblib')))==975 and len(list((e.OUT/'checkpoints').glob('*.joblib')))==195
    decomposition=pd.read_csv(e.OUT/'tables/municipal_bias_dispersion_decomposition.csv')
    np.testing.assert_allclose(decomposition.SSE_gain,decomposition.bias_squared_gain+decomposition.error_variance_gain,atol=1e-10)
    assert 'F6-E0' not in set(pd.read_csv(e.OUT/'tables/metrics_summary.csv').experiment)
    versions=dict(python=sys.version,platform=sys.platform,catboost=catboost.__version__,xgboost=xgboost.__version__,sklearn=sklearn.__version__,scipy=scipy.__version__,numpy=np.__version__,pandas=pd.__version__,joblib=e.joblib.__version__)
    (e.OUT/'audit/runtime_versions.json').write_text(json.dumps(versions,indent=2),encoding='utf8')
    info=dict(n_fits=6435,n_outer=195,n_inner_candidates=6240,n_saved_models=975,n_oof_rows=17526,workers=6,wall_seconds=float((e.OUT/'audit/wall_seconds.txt').read_text()),sum_fit_seconds=float(reg.seconds.sum()),n_fit_warnings=int(reg.warnings.apply(lambda s:len(json.loads(s))).sum()),core_recovered_without_fitting=True,no_XGB_fit=True,no_ensemble=True,no_residual=True,no_final_training=True,no_PRED=True)
    (e.OUT/'audit/execution_diagnostics.json').write_text(json.dumps(info,indent=2),encoding='utf8')
    (e.OUT/'audit/runtime_environment_note.txt').write_text('Windows workers emitted threadpoolctl warnings for simultaneous Intel libiomp and LLVM libomp; the message describes Linux incompatibility. All scientific fits/diagnostics completed; fit warnings are separately captured. Tests emitted asttokens/astroid deprecation warnings. Immutable shared engine retains F6 console prefix while experiment keys are F7-E1/E2/E3. Reporter baseline alias F6-E0 is scoped internally and translated back to actual F7-00 in all scientific tables and global/intraprofile figures; native OOF references never alias previous ET core. No scientific configuration changed.\n',encoding='utf8')
    report=e.OUT/'report/synthesis.md'
    report.write_text(report.read_text(encoding='utf8')+f'\n\n## Verificación\n\nSiete pruebas pasaron: ámbito y restauración del adaptador, permutación conjunta y soporte antes de predicción, replay de975 modelos, entrenamiento exclusivo,65 particiones y selección interna originales, referencias/OOF/métricas, hojas y efectos respaldados. Se conservaron {len(protected)} hashes anteriores.195 modelos externos y6240 ajustes internos;6435 ajustes científicos,17526 filas OOF con controles. Advertencias de ajuste: {info["n_fit_warnings"]}. No modelos combinados, residuos, modelo final ni59 PRED.\n',encoding='utf8')
    (e.ROOT/'documentation/family7_expansion.md').write_text(report.read_text(encoding='utf8'),encoding='utf8')
    (e.ROOT/'documentation/family7_expansion_frozen_design.md').write_text((e.OUT/'report/frozen_design.md').read_text(encoding='utf8'),encoding='utf8')
    pd.DataFrame([dict(path=p.relative_to(e.ROOT).as_posix(),producer='family_7.expansion plus immutable shared execution/reporting/diagnostic methods',inputs='138 labels; original65outer/4inner; authorized compact4/history2/slope; read-only compatible controls',exploratory=True,no_external_combination_weights=True) for p in list((e.OUT/'tables').glob('*'))+list((e.OUT/'figures').glob('*'))]).to_csv(e.OUT/'audit/artifact_provenance.csv',index=False)
    files=[p for p in e.OUT.rglob('*') if p.is_file() and p.name!='manifest.json']+list((e.ROOT/'src/family_7/expansion').glob('*.py'))
    files += [e.ROOT/p for p in ['scripts/362_family7_expansion.py','scripts/363_family7_expansion_finalize.py','tests/test_family7_expansion_unit.py','tests/test_family7_expansion_integration.py','documentation/family7_expansion.md','documentation/family7_expansion_frozen_design.md']]
    decision=json.loads((e.OUT/'report/decision.json').read_text())
    manifest=dict(status='complete',version='family_7/expansion/v1',decision=decision,n_labels=138,n_outer_folds=65,n_fits=6435,n_saved_models=975,n_oof_rows=17526,tests='7 passed',protected_files_verified=len(protected),Champion_F5_F6_F7_initial_modified=False,XGBoost_refitted=False,ensemble_fitted=False,residual_fitted=False,final_training=False,PRED_predictions=False,artifacts={p.relative_to(e.ROOT).as_posix():e.base.design.sha(p) for p in files})
    (e.OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8');print(json.dumps(info,indent=2))
if __name__=='__main__':main()
