"""Seal research-only F8 proposal; zero fits and no PRED inference."""
import sys,json,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd,sklearn,scipy
from src.family_8 import research as e
def main():
    if (e.OUT/'manifest.json').exists():raise FileExistsError('Completed F8 research immutable')
    root=ET.parse(e.OUT/'audit/tests.xml').getroot();assert not root.findall('.//failure') and not root.findall('.//error')
    assert len(root.findall('.//testcase'))==5
    sources=pd.read_csv(e.OUT/'audit/source_inventory.csv')
    for row in sources.itertuples():assert e.sha(e.ROOT/row.path)==row.sha256,row.path
    cfg=json.loads((e.OUT/'proposed_design.json').read_text());assert cfg['actual_models_fitted']==0 and not cfg['PRED_predictions']
    audit=pd.read_csv(e.OUT/'tables/residual_architecture_audit.csv')
    protection=json.loads((e.OUT/'audit/protection_scope.json').read_text())
    for name in ['architecture_audit','identifiability_extrapolation','nested_crossfitting','experimental_design','recommendation']:
        path=e.OUT/'report'/f'{name}.md';path.write_text(path.read_text(encoding='utf8')+f'\n\nVerificación: cinco pruebas pasaron; cero ajustes/predicciones nuevos; {len(sources)} fuentes consumidas verificadas. Se conserva inventario de{protection["inherited_protected_files"]} hashes anteriores; los archivos no utilizados no se reabrieron para rehash. Escrituras limitadas a nueva versión F8 y sus documentos.\n',encoding='utf8')
        (e.ROOT/'documentation'/f'family8_{name}.md').write_text(path.read_text(encoding='utf8'),encoding='utf8')
    environment=dict(python=sys.version,platform=sys.platform,numpy=np.__version__,pandas=pd.__version__,sklearn=sklearn.__version__,scipy=scipy.__version__,joblib=e.joblib.__version__,role='research; no estimators fit or predictions generated')
    (e.OUT/'audit/runtime_versions.json').write_text(json.dumps(environment,indent=2),encoding='utf8')
    files=[p for p in e.OUT.rglob('*') if p.is_file() and p.name!='manifest.json']+list((e.ROOT/'src/family_8').glob('*.py'))
    files += [e.ROOT/p for p in ['scripts/364_family8_research.py','scripts/365_family8_research_finalize.py','tests/test_family8_research.py']]
    files += [e.ROOT/'documentation'/f'family8_{n}.md' for n in ['architecture_audit','identifiability_extrapolation','nested_crossfitting','experimental_design','recommendation']]
    info=dict(status='complete',version='family_8/residual_design/v1',research_only=True,models_trained=0,predictions_generated=0,PRED_predictions=False,Champion_F4_F5_F6_F7_modified=False,earlier_decisions_changed=False,n_architecture_records=len(audit),tests='5 passed',consumed_sources_verified=len(sources),protection=protection,execution_authorized=False,recommendation=cfg['first'],next_stage_only_after_review=cfg['second_after_review'],R3_automatic=False,R4_executed=False,artifacts={p.relative_to(e.ROOT).as_posix():e.sha(p) for p in files})
    (e.OUT/'manifest.json').write_text(json.dumps(info,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in info.items() if k!='artifacts'},indent=2))
if __name__=='__main__':main()
