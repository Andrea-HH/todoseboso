"""Seal verified F7 initial artifacts; no fitting or promotion."""
import sys,json,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd,numpy as np,sklearn,scipy,catboost,xgboost
from src.family_7 import execution as e
def main():
    if (e.OUT/'manifest.json').exists():raise FileExistsError('Completed F7 immutable')
    cases=[]
    for filename in ['unit_tests.xml','integration_tests.xml']:
        root=ET.parse(e.OUT/'audit'/filename).getroot()
        assert not root.findall('.//failure') and not root.findall('.//error')
        cases+=root.findall('.//testcase')
    assert len(cases)==9
    protected=pd.read_csv(e.OUT/'audit/protected_inputs.csv')
    for row in protected.itertuples():assert e.base.design.sha(e.ROOT/row.path)==row.sha256,row.path
    cfg=json.loads((e.OUT/'frozen_design.json').read_text())
    for path,h in {**cfg['source_sha'],**cfg['cache_sha']}.items():assert e.base.design.sha(e.ROOT/path)==h
    reg=pd.read_csv(e.OUT/'tables/fit_registry.csv');p=pd.read_parquet(e.OUT/'tables/oof_predictions.parquet')
    assert len(reg)==4290 and len(p)==10350 and set(reg.experiment)==set(e.SPECS)
    assert len(list((e.OUT/'models').glob('*.joblib')))==650
    decision=json.loads((e.OUT/'report/decision.json').read_text());assert not decision['extensions_executed']
    versions=dict(python=sys.version,platform=sys.platform,catboost=catboost.__version__,xgboost=xgboost.__version__,sklearn=sklearn.__version__,numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,joblib=e.joblib.__version__)
    (e.OUT/'audit/runtime_versions.json').write_text(json.dumps(versions,indent=2),encoding='utf8')
    (e.OUT/'audit/runtime_environment_note.txt').write_text('Windows threadpoolctl emitted a RuntimeWarning about simultaneous Intel libiomp and LLVM libomp; its message describes possible Linux incompatibility. Scientific fit warnings are captured separately in fit_registry.csv. Unit tests also emitted two asttokens/astroid deprecation warnings. No bounds or scientific configuration changed. The shared immutable fitting engine prints its original F6 prefix; experiment keys and artifacts are F7.\nFirst integration run: four passed and one failed because a pandas row index dropped intentionally by the cache was compared to the source index. The test was corrected to compare exact values, scientific keys and row order after resetting that metadata index. No data or predictions changed. The initial XML is retained; all five integration tests were rerun in the final XML.\n',encoding='utf8')
    info=dict(n_fits=4290,n_outer=130,n_inner_candidates=4160,n_saved_models=650,n_oof_rows=10350,
        n_fit_warnings=int(reg.warnings.apply(lambda s:len(json.loads(s))).sum()),workers=6,
        scientific_fit_wall_seconds=float((e.OUT/'audit/wall_seconds.txt').read_text()),sum_fit_seconds=float(reg.seconds.sum()),
        external_eval_set=False,extensions_executed=False,final_training=False,PRED_predictions=False)
    (e.OUT/'audit/execution_diagnostics.json').write_text(json.dumps(info,indent=2),encoding='utf8')
    path=e.OUT/'report/synthesis.md'
    path.write_text(path.read_text(encoding='utf8')+f'\n\n## Verificación\n\nNueve pruebas pasaron: transformaciones exclusivamente de entrenamiento, particiones internas originales y selección acotada, replay de650 modelos, referencias y agregación exactas, soporte de efectos y contabilidad de hojas. {len(protected)} archivos anteriores conservaron su hash. Se ajustaron130 modelos externos y4160 candidatos internos; se guardaron10350 filas OOF entre referencias y candidatos. Advertencias de ajuste: {info["n_fit_warnings"]}. No se ejecutaron E1–E3, modelo final, residuos ni59 PRED.\n',encoding='utf8')
    (e.ROOT/'documentation/family7_boosting.md').write_text(path.read_text(encoding='utf8'),encoding='utf8')
    pd.DataFrame([dict(path=p.relative_to(e.ROOT).as_posix(),producer='family_7 bounded execution / shared immutable reporting engine',inputs='138 training labels; original65outer and4inner; compact4; frozen reference OOF',exploratory=True) for p in list((e.OUT/'tables').glob('*'))+list((e.OUT/'figures').glob('*'))]).to_csv(e.OUT/'audit/artifact_provenance.csv',index=False)
    files=[p for p in e.OUT.rglob('*') if p.is_file() and p.name!='manifest.json']+list((e.ROOT/'src/family_7').glob('*.py'))
    files+=[e.ROOT/p for p in ['scripts/359_family7_prepare.py','scripts/360_family7_boosting.py','scripts/361_family7_finalize.py','tests/test_family7_unit.py','tests/test_family7_integration.py','documentation/family7_boosting.md','documentation/family7_boosting_frozen_design.md']]
    manifest=dict(status='complete',version='family_7/boosting/v1',decision=decision,n_labels=138,n_outer_folds=65,n_fits=4290,n_saved_models=650,n_oof_rows=10350,tests='9 passed',protected_files_verified=len(protected),final_training=False,PRED_predictions=False,champion_modified=False,F5_F6_modified=False,extensions_executed=False,artifacts={p.relative_to(e.ROOT).as_posix():e.base.design.sha(p) for p in files})
    (e.OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8');print(json.dumps(info,indent=2))
if __name__=='__main__':main()
