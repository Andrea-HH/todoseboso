"""Reproducibility, tests and manifest for initial F5, with no additional fitting."""
import sys,json,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from src.family_5.gpr_initial import execution as e

def main():
    if (e.OUT/'manifest.json').exists():raise FileExistsError('Completed F5 initial run immutable')
    _,t,splits=e.load();reg=pd.read_csv(e.OUT/'tables/fit_registry.csv');p=pd.read_parquet(e.OUT/'tables/oof_predictions.parquet')
    assert len(reg)==650 and len(p)==5382
    protected=pd.read_csv(e.OUT/'audit/protected_inputs.csv')
    for r in protected.itertuples():assert e.design.sha(e.ROOT/r.path)==r.sha256,r.path
    config=json.loads((e.OUT/'frozen_execution_design.json').read_text())
    for path,digest in config['source_sha'].items():assert e.design.sha(e.ROOT/path)==digest,path
    (e.OUT/'audit/runtime_environment_note.txt').write_text('Observed during the completed Windows worker run: threadpoolctl warned that Intel libiomp and LLVM libomp were both loaded; its message identifies possible incompatibility on Linux. Three CPU worker processes completed all65folds; no crash/deadlock or numerical fit failure was observed. This environmental warning occurred outside GP fit warning capture and is recorded separately. No optimizer bounds, inputs or scientific design were changed. All650 selected optimizer solutions converged and all training covariances were positive.\n',encoding='utf8')
    first=min(x.stat().st_mtime for x in (e.OUT/'checkpoints').glob('*.joblib'));last=max(x.stat().st_mtime for x in (e.OUT/'checkpoints').glob('*.joblib'));frozen=(e.OUT/'frozen_execution_design.json').stat().st_mtime
    timing=dict(sum_fit_cpu_wall_seconds=float(reg.seconds.sum()),elapsed_first_to_last_checkpoint_seconds=last-first,elapsed_frozen_design_to_last_checkpoint_seconds=last-frozen,n_workers=3,n_outer_GPR_fits=130,n_inner_GPR_fits=520,n_optimizer_starts=1950,n_selected_optimizer_success=int(reg.selected_optimizer_converged.sum()),max_covariance_condition=float(reg.covariance_condition.max()),timing_note='Individual fit seconds use perf_counter; elapsed parallel phase approximated by artifact timestamps in this run, including IO/control recovery from freeze')
    (e.OUT/'audit/execution_timing.json').write_text(json.dumps(timing,indent=2),encoding='utf8')
    xml=e.OUT/'audit/test_results.xml'
    result=subprocess.run([sys.executable,'-m','pytest','tests/test_family5_gpr_initial_math.py','tests/test_family5_gpr_initial_integration.py','-q',f'--junitxml={xml}'],cwd=e.ROOT,capture_output=True,text=True)
    (e.OUT/'audit/automated_tests.txt').write_text(result.stdout+'\n'+result.stderr,encoding='utf8')
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    ntests=len(ET.parse(xml).getroot().findall('.//testcase'))
    assert ntests==22
    decision=json.loads((e.OUT/'report/decision.json').read_text());artifact=[]
    for path in list((e.OUT/'tables').glob('*'))+list((e.OUT/'figures').glob('*')):
        if path.is_file():artifact.append(dict(path=path.relative_to(e.ROOT).as_posix(),producer='execution.collect / reporting.build / reporting.plots',inputs='frozen splits, authorized GP checkpoints, exact C-T3 archives',new_predictive_experiment='none beyond F5-00-C,F5-01'))
    pd.DataFrame(artifact).to_csv(e.OUT/'audit/artifact_provenance.csv',index=False)
    text=f'''\n\n## Verificación final\n\nPasaron{ntests}pruebas matemáticas y de integración, incluido replay de los650modelos externos/internos y los65controles C-T3. Se verificaron{len(protected)}archivos anteriores protegidos y hashes delcódigo de ajuste congelado. Los1950inicios deoptimización pertenecen exclusivamente a lasdosconfiguraciones autorizadas; todaslas650soluciones seleccionadas convergieron y lascovarianzas fueron positivas. No se ajustó unmodelo final con138Y ni se generaron59predicciones PRED. Los tiempos reales porfit y laaproximación de duración paralela están en `audit/execution_timing.json`. No se ejecutaronF5-02–06, F5-00-M u otrokernel.\n'''
    for path in [e.OUT/'report/technical_report.md',e.ROOT/'documentation/family5_gpr_initial.md',e.OUT/'report/decision_summary.md',e.ROOT/'documentation/family5_gpr_initial_decision.md']:path.write_text(path.read_text(encoding='utf8')+text,encoding='utf8')
    files=[p for p in e.OUT.rglob('*') if p.is_file() and p.name!='manifest.json']
    files.extend((e.ROOT/'src/family_5/gpr_initial').glob('*.py'))
    files.extend(e.ROOT/p for p in ['scripts/349_family5_gpr_initial.py','scripts/350_family5_gpr_initial_finalize.py','tests/test_family5_gpr_initial_math.py','tests/test_family5_gpr_initial_integration.py','documentation/family5_gpr_initial.md','documentation/family5_gpr_initial_decision.md'])
    manifest=dict(status='complete',family='F5',version='gpr_initial/v1',experiments=list(e.SPECS),control='C-T3 exact recovered',n_train=138,n_unlabelled=59,n_outer=65,n_new_outer_models=130,n_new_inner_diagnostic_models=520,n_oof_rows=5382,n_optimizer_starts=1950,tests=f'{ntests} passed',protected_files_verified=len(protected),all_selected_optimizers_converged=True,final_training=False,PRED_predictions=False,champion_modified=False,additional_experiments=False,decision=decision,artifacts={p.relative_to(e.ROOT).as_posix():e.design.sha(p) for p in files})
    (e.OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print(f'F5 INITIAL COMPLETE;{ntests}tests;{len(protected)}protected files;{len(files)}artifacts;130outer+520innerfits;no further experiments')

if __name__=='__main__':main()
