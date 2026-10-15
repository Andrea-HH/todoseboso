"""Finalize provenance and five deliverables; no training or prediction calls."""
import sys,json,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from src.family_4 import stage_d_evidence as d
from src.family_4 import stage_c_models as c

def main():
    if (d.OUT/'manifest.json').exists():raise FileExistsError('Completed Stage D immutable')
    prior=pd.read_csv(d.OUT/'audit/protected_inputs.csv')
    for r in prior.itertuples():assert c.b.a.sha(d.ROOT/r.path)==r.sha256,r.path
    # Check actual feature inputs against pre-existing B provenance, not just today's hashes.
    direct=pd.read_csv(c.b.OUT/'audit/read_only_input_provenance.csv')
    for r in direct.itertuples():assert c.b.a.sha(d.ROOT/r.path)==r.sha256,r.path
    direct.to_csv(d.OUT/'audit/read_only_input_provenance.csv',index=False)
    result=subprocess.run([sys.executable,'-m','pytest','tests/test_stage_d_evidence.py','-q'],cwd=d.ROOT,capture_output=True,text=True)
    (d.OUT/'audit/automated_tests.txt').write_text(result.stdout+'\n'+result.stderr,encoding='utf8')
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    assert '20 passed' in result.stdout
    p=pd.read_parquet(d.OUT/'tables/compatible_oof.parquet');comp=pd.read_csv(d.OUT/'tables/comparability.csv');inv=pd.read_csv(d.OUT/'tables/model_inventory.csv')
    audit=dict(stage='D',status='complete',protected_files=len(prior),direct_source_files_verified=len(direct),n_labels=138,n_unlabelled=59,n_unique_oof_parcels=p[d.ID].nunique(),n_compatible_oof_rows=len(p),n_alias_series=p.experiment.nunique(),n_archived_inventory_series=len(inv),n_paired_comparison_protocols=len(comp),n_outer_folds=65,n_new_models=0,n_new_predictive_estimates=0,n_training_calls=0,tests='20 passed',exploratory=True)
    (d.OUT/'audit/integrity_results.json').write_text(json.dumps(audit,indent=2),encoding='utf8')
    pd.DataFrame([dict(path=r.path,sha256=r.sha256,matches=True) for r in prior.itertuples()]).to_csv(d.OUT/'audit/previous_results_integrity.csv',index=False)
    text=f'''# Etapa D — Auditoría de integridad

Estado: completa. Se verificaron {len(prior)} archivos protegidos anteriores y {len(direct)} referencias directas a fuentes contra la procedencia deB. Incluye artefactosA–C/F4/F4-E, Champion, antecedentes, métricas, configuraciones y scripts. Los archivos previos permanecen intactos.

Se conservaron138etiquetas,59parcelas sinYutilizado y65folds. Hay{len(p)}filas OOFcompatibles archivadas en{p.experiment.nunique()}series, con138IDsúnicos; aliasB2/E2 no son modelos independientes. Hay{len(comp)}comparaciones protocolo/candidato compatibles. Inventario histórico:{len(inv)}series de modelo/archivo, incluyendo controles descartados.

**Cero nuevos modelos, cero nuevas estimaciones predictivas, cero llamadas de entrenamiento.** La prueba AST verifica ausencia de fit/predict en los módulosD. Las importaciones de fuentes anteriores solo recuperan datos, constantes y folds; no llaman a estimadores. No existe directorioD/models. No se modificaronChampion,mezcla,pesos,variables,labels o splits.

Pasaron20pruebas automatizadas: identidadY/IDs y exclusión59PRED; particiones; llaves exactas; reproducción de métricasC; OOFporrepetición; SSEycontribuciones; omisiones sinreentrenamiento; pérdidas agrupadas por parcela; pares del mismo ajuste y ponderaciónperfil; protocolos separados; conservación de influyentes; hashes previos; Champion/mezcla exactos; ausencia de entrenamiento; trazabilidadfiguras; consistenciadocumental y soporte. Log:`audit/automated_tests.txt`.

`audit/protected_inputs.csv` registra hashes previos; `audit/read_only_input_provenance.csv` comprueba entradas realmente utilizadas; `tables/comparability.csv` documenta n por comparación; `tables/model_inventory.csv` registra IDs/modelos/procedencia. La llave es(ID_POLIGONO,protocolo,repetición,fold),Y idéntico. Los resultados Champion solo son aleatorios; no se inventaron OOFgeográficas. C-T0/F4-S1yB2/F4-E2son alias.

Los modelos iniciales y finales de esta etapa tienen el mismo conteo porque no se ajusta ninguno. El análisis omite comparaciones que no tienen protocolos compatibles, nunca recupera especulativamente predicciones inexistentes. Las sensibilidades no eliminan observaciones de las fuentes. Los nuevos artefactosD se identifican porSHA-256 en `manifest.json`; el propio manifiesto se excluye de su lista para evitar autorreferencia.

El diseñoD.0 conservó hashes del código diagnóstico inicial. El manifiesto final registra las fuentes de análisis/reportes/pruebas definitivas; refinamientos descriptivos/documentales no modificaron predicciones ni la matriz experimental. Las conclusiones siguen siendo exploratorias y los parámetros operativos de adquisición/precisión pendientes están señalados en el protocolo.
'''
    for path in [d.OUT/'report/integrity_audit.md',d.ROOT/'documentation/territorial_program_stage_d_integrity.md']:path.write_text(text,encoding='utf8')
    provenance=[]
    for path in (d.OUT/'tables').glob('*'):
        if path.is_file():provenance.append(dict(artifact=path.relative_to(d.ROOT).as_posix(),producer='src/family_4/stage_d_evidence.py or stage_d_reporting.py',inputs='audit/protected_inputs.csv; compatible_oof; source A/B/C tables',role='descriptive diagnostic; no predictions estimated'))
    for path in (d.OUT/'figures').glob('*.png'):provenance.append(dict(artifact=path.relative_to(d.ROOT).as_posix(),producer='stage_d_reporting.plot_all',inputs='tables/metric, block, gain, support, pair and evidence artifacts',role='descriptive figure'))
    pd.DataFrame(provenance).to_csv(d.OUT/'audit/artifact_provenance.csv',index=False)
    files=[x for x in d.OUT.rglob('*') if x.is_file() and x.name!='manifest.json']
    for pattern in ['src/family_4/stage_d*.py','scripts/34[67]_stage_d*.py','tests/test_stage_d*.py','documentation/territorial_program_stage_d*.md']:files.extend(d.ROOT.glob(pattern))
    manifest={**audit,'artifacts':{path.relative_to(d.ROOT).as_posix():c.b.a.sha(path) for path in files}}
    (d.OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print(f'STAGE D COMPLETE;20tests;{len(prior)} prior hashes;{len(files)} artifacts;0new models')

if __name__=='__main__':main()
