"""Finalize reporting/provenance and artifact hashes without refitting models."""
from pathlib import Path
import sys,json,argparse,importlib.util
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from src.family_1 import lm_multiblock as lm
from src.family_1.lm_final_audit import satellite_quality,validate

def finalize(version='v1'):
    from src.family_1.m_satellite import soil_after_satellite
    soil_after_satellite(version)
    satellite_quality(version)
    for section in ['L','M']:
        lm.extrapolation_screen(section,version);validate(section,version)
    script=Path(__file__).with_name('332_lm_synthesis.py');spec=importlib.util.spec_from_file_location('lm_synthesis',script);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.synthesize(version)
    out,proc=lm.locations('M',version)
    p=out/'report/m_report.md';text=p.read_text(encoding='utf-8')
    text+='\n## Interpretación de la referencia y calidad\n\nEl PCA predictivo por bloques primero reduce cada sensor/familia y luego concatena sus scores con balance de energía; un PCA final conserva el mismo presupuesto total de1/2/4componentes en M0–M5, elegido dentro de entrenamiento. El balance divide por max(raíz de energía,1), por lo que no amplifica bloques casi constantes. No hay whitening. La dimensión efectivamente elegida se conserva por fold; igualdad de presupuesto no implica que todos los modelos hayan seleccionado el mismo K.\n\nLas diferencias de dispersión y rango principales comparan2025 con la curva mensual media2022–24. Promediar años suaviza la curva histórica: una diferencia positiva deσ no demuestra por sí sola mayor variabilidad anual. La sensibilidad descriptiva en annual_distribution_delta_sensitivity_descriptive.parquet compara también estadísticas de cada año y su promedio, sin nuevos modelos ni elecciones por Y. El soporte de años y observaciones se registra por parcela, mes e índice.\n\nLas fechas son observaciones agregadas, no un conteo verificable de escenas originales. No se suministran fechas separadas de procesamiento/disponibilidad, versiones de procesamiento por año, bandas/píxeles ni tipos de cultivo históricos. Comparar el mismo calendario no garantiza el mismo cultivo o estado fenológico. Esta evaluación retrospectiva no valida pronóstico temprano ni transferencia a otro año.\n\nCalidad temporal efectiva(gaps de fechas válidas), nubes y cobertura en tablas36–38; no se eliminan parcelas por esas reservas ni se retunea ningún modelo.\n'
    p.write_text(text,encoding='utf-8');(lm.ROOT/'documentation/m_historical_multisensor.md').write_text(text.replace('../figures/',f'../outputs/modeling/family_1/{lm.NAMES["M"]}/{version}/figures/'),encoding='utf-8')
    lo,_=lm.locations('L',version);inventory=json.loads((lo/'protected_inputs.json').read_text())
    changed=[path for path,value in inventory.items() if lm.k.j.sha(lm.ROOT/path)!=value]
    if changed:raise ValueError('Historical file change: '+str(changed[:5]))
    for section in ['L','M']:
        out,proc=lm.locations(section,version);m=json.loads((out/'manifest.json').read_text());m['previous_results_unchanged']=True;m['protected_file_count']=len(inventory)
        m['validation']=json.loads((out/'validation.json').read_text());m['final_59_predictions_generated']=False
        sources=list((lm.ROOT/'src/family_1').glob('lm_*.py'))+[lm.ROOT/'src/family_1/l_representation.py',lm.ROOT/'src/family_1/m_satellite.py']+list(Path(__file__).parent.glob('33[0-3]_*.py'))+[Path(__file__).with_name('329_lm_initial_audit.py'),lm.ROOT/'tests/test_lm_multiblock.py']
        m['sources']={str(x.relative_to(lm.ROOT)):lm.k.j.sha(x) for x in sources}
        files=[x for x in out.rglob('*') if x.is_file() and not any(z in x.parts for z in ['checkpoints','base_cache']) and x.name!='manifest.json']+list(proc.glob('*.parquet'))
        m['artifacts']={str(x.relative_to(lm.ROOT)):lm.k.j.sha(x) for x in files};(out/'manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
    print('L/M fully finalized; historical files unchanged; no models refitted',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-id',default='v1');a=p.parse_args();finalize(a.run_id)
