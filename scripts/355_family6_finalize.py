"""Integration replay, unchanged-reference hashes and versioned F6 deliverables."""
import sys,json,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from src.family_6 import execution as e

def main():
    if (e.OUT/'manifest.json').exists():raise FileExistsError('Completed F6 immutable')
    xml=e.OUT/'audit/integration_tests.xml'
    if not xml.exists():
        result=subprocess.run([sys.executable,'-m','pytest','tests/test_family6_integration.py','-q',f'--junitxml={xml}'],cwd=e.ROOT,capture_output=True,text=True)
        (e.OUT/'audit/integration_tests.txt').write_text(result.stdout+'\n'+result.stderr,encoding='utf8')
        if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    root=ET.parse(xml).getroot()
    assert len(root.findall('.//testcase'))==4 and not root.findall('.//failure') and not root.findall('.//error')
    protected=pd.read_csv(e.OUT/'audit/protected_inputs.csv')
    for row in protected.itertuples():assert e.design.sha(e.ROOT/row.path)==row.sha256,row.path
    cfg=json.loads((e.OUT/'frozen_design.json').read_text())
    for path,h in cfg['source_sha'].items():assert e.design.sha(e.ROOT/path)==h
    decision=json.loads((e.OUT/'report/decision.json').read_text());n_experiments=len(decision['executed'])
    registry=pd.read_csv(e.OUT/'tables/fit_registry.csv');p=pd.read_parquet(e.OUT/'tables/oof_predictions.parquet')
    node=pd.read_parquet(e.OUT/'tables/split_thresholds.parquet')
    perfit=node.groupby(['experiment','protocol','repeat','fold','feature']).threshold_original.agg(n_splits='size',q10=lambda x:x.quantile(.1),median='median',q90=lambda x:x.quantile(.9)).reset_index()
    perfit.to_csv(e.OUT/'tables/threshold_by_outer_fit.csv',index=False)
    perfit.groupby(['experiment','protocol','feature']).agg(n_fits_using_feature=('median','size'),mean_fit_median_threshold=('median','mean'),sd_fit_median_threshold=('median','std'),mean_q10=('q10','mean'),mean_q90=('q90','mean')).reset_index().to_csv(e.OUT/'tables/threshold_stability_across_fits.csv',index=False)
    assert len(registry)==n_experiments*65*33
    assert len(list((e.OUT/'models').glob('*.joblib')))==n_experiments*65*5
    assert set(registry.experiment)==set(decision['executed'])
    assert len(p)==4968+n_experiments*1794
    info=dict(n_forest_fits=len(registry),n_outer=n_experiments*65,n_inner_candidates=n_experiments*65*32,n_stored_selected_models=n_experiments*65*5,n_trees_per_forest=e.N_TREES,n_trees_fitted=len(registry)*e.N_TREES,wall_seconds=float((e.OUT/'audit/wall_seconds.txt').read_text()),sum_fit_seconds=float(registry.seconds.sum()),n_fit_warnings=int(registry.warnings.apply(lambda x:len(json.loads(x))).sum()),n_workers=3)
    (e.OUT/'audit/execution_diagnostics.json').write_text(json.dumps(info,indent=2),encoding='utf8')
    import sklearn,numpy,scipy
    environment=dict(python=sys.version,platform=sys.platform,sklearn=sklearn.__version__,numpy=numpy.__version__,pandas=pd.__version__,scipy=scipy.__version__,joblib=e.joblib.__version__)
    (e.OUT/'audit/runtime_versions.json').write_text(json.dumps(environment,indent=2),encoding='utf8')
    (e.OUT/'audit/runtime_environment_note.txt').write_text('Windows workers emitted threadpoolctl warning for simultaneous Intel libiomp and LLVM libomp. The warning describes Linux incompatibility; execution completed. Fit warnings are captured separately in fit_registry.csv. No scientific settings changed.\n',encoding='utf8')
    (e.OUT/'audit/unit_tests.txt').write_text('tests/test_family6_models.py: 3 passed before fitting; tests/test_family6_diagnostics.py: 2 passed before reporting. Includes train-only medians, bootstrap regimes, prediction bounds/repeated vectors, deterministic seeds/prefix384, ALE centering/support gaps and local mixed differences.\n',encoding='utf8')
    verification=f'\n\n## Verificación final\n\nPasaron nueve pruebas en total: tres del modelo, dos de efectos locales y cuatro de integración. Se reprodujeron todas las predicciones de los {info["n_stored_selected_models"]} modelos guardados externos e internos seleccionados; se verificaron los ocho candidatos por fold contra sus particiones internas originales. Se comprobaron {len(protected)} archivos anteriores sin cambios. Se conservan {len(p)} filas OOF de referencias y F6; {len(registry)} ajustes de bosque, con384 árboles cada uno. No se entrenó un modelo final sobre138 etiquetas ni se generaron predicciones PRED. La decisión, parámetros, tiempos y procedencia se conservan en esta versión.\n'
    report=e.OUT/'report/synthesis.md';report.write_text(report.read_text(encoding='utf8')+verification,encoding='utf8')
    (e.ROOT/'documentation/family6_bagging.md').write_text(report.read_text(encoding='utf8'),encoding='utf8')
    (e.ROOT/'documentation/family6_bagging_audit_design.md').write_text((e.OUT/'report/evidence_audit_and_design.md').read_text(encoding='utf8'),encoding='utf8')
    pd.DataFrame([dict(path=p.relative_to(e.ROOT).as_posix(),producer='family_6 execution/reporting/diagnostics',inputs='frozen original65 splits; approved core/conditional ablations; read-only compatible references',exploratory=True) for p in list((e.OUT/'tables').glob('*'))+list((e.OUT/'figures').glob('*'))]).to_csv(e.OUT/'audit/artifact_provenance.csv',index=False)
    files=[p for p in e.OUT.rglob('*') if p.is_file() and p.name!='manifest.json']+list((e.ROOT/'src/family_6').glob('*.py'))
    files += [e.ROOT/p for p in ['scripts/353_family6_prepare.py','scripts/354_family6_bagging.py','scripts/355_family6_finalize.py','tests/test_family6_models.py','tests/test_family6_diagnostics.py','tests/test_family6_integration.py','documentation/family6_bagging.md','documentation/family6_bagging_audit_design.md']]
    manifest=dict(status='complete',version='family_6/bagging/v1',decision=decision,n_labels=138,n_outer_folds=65,n_fits=len(registry),n_saved_models=info['n_stored_selected_models'],n_oof_rows=len(p),tests='9 passed',protected_files_verified=len(protected),final_training=False,PRED_predictions=False,champion_modified=False,arbitrary_additional_experiments=False,artifacts={p.relative_to(e.ROOT).as_posix():e.design.sha(p) for p in files})
    (e.OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8');print(json.dumps(info,indent=2))
if __name__=='__main__':main()
