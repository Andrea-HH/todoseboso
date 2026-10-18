"""Validate completed replay/cold-refit evidence and publish aggregate provenance."""
from pathlib import Path
import json
import hashlib
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pandas as pd


def main():
    public=ROOT/'results/current_champions/v1'
    replay=json.loads((public/'reproduction_audit.json').read_text(encoding='utf-8'))
    assert replay['mode']=='saved_model_replay' and replay['restricted_file_io']
    assert replay['external_folds']==81 and replay['max_prediction_difference']<1e-10
    # Validate public aggregate metrics against the untouched original research.
    actual=pd.read_csv(public/'metrics.csv')
    expected=pd.read_csv(ROOT/'outputs/modeling/four_expert_combinations/v1/tables/metrics.csv')
    joined=actual.merge(expected,on=['experiment','protocol'],suffixes=('_new','_old'),validate='one_to_one')
    assert len(joined)==20
    for metric in ['rmse','r2','mae','bias','p95_absolute','within_05']:
        assert (joined[metric+'_new']-joined[metric+'_old']).abs().max()<1e-12,metric
    reports=[]
    for folder in ['cold_verification_spatial','cold_verification','cold_inputs_only']:
        path=ROOT/'outputs/research/current_champions/v1'/folder/'reproduction_audit.json'
        report=json.loads(path.read_text(encoding='utf-8'))
        assert report['mode']=='cold_refit' and report['status']=='passed'
        assert report['max_prediction_difference']<1e-10
        reports.append(dict(folder=folder,fold_ids=report['fold_ids'],
                            max_prediction_difference=report['max_prediction_difference'],
                            restricted_file_io=report.get('restricted_file_io',False)))
    ids=sorted(set(i for r in reports for i in r['fold_ids']))
    assert ids==[0,50,55,60,63,64,65],ids
    output=dict(status='passed',scope='Representative cold refits, not all81 retrained',unique_folds=ids,
        protocols_checked=['random','climate_profile','municipality','spatial','fresh_97_41'],
        max_prediction_difference=max(r['max_prediction_difference'] for r in reports),
        runs=reports,inputs_only_run='cold_inputs_only',
        inputs_only_has_no_saved_models=not (ROOT/'data/processed/current_champions/v1_inputs_only/models').exists(),
        full_81_cold_refit_performed=False,no_PRED59=True,no_final138_fit=True)
    assert output['inputs_only_has_no_saved_models']
    (public/'cold_refit_verification.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8',newline='\n')
    sources=['src/current_champions.py','scripts/521_current_champions.py','scripts/522_finalize_current_champions.py','scripts/523_check_current_champions_exclusions.py',
        'src/base_distribution_correction.py','src/pruned_global_architecture.py','src/neighbor_signal_contrasts.py',
        'src/neighbor_signal_linear.py','src/geoc_signal_research.py','src/geoc_bridge.py','src/geoc_local04d_snapshot.py',
        'src/local_ridge_sufficient_statistics.py','src/signal_role_allocation.py','src/conditional_local_phases.py',
        'src/physical_representation.py','src/physical_similarity.py','src/indicator_neighborhoods.py',
        'src/temporal_indicator_weights.py','src/ct3_residual_conditional/models.py','src/family_4/conditional_response.py',
        'src/family_8/research.py','src/four_expert_fast_tuner.py','src/geoc_reverse.py',
        'configs/current_stage.json','configs/current_champions_inputs.json','requirements-research.txt']
    provenance=dict(date='2026-10-18',hash_convention='SHA256 of file bytes with CRLF normalized toLF for cross-platform code comparison',
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for p in sources},
        private_bundle_manifest_sha256=replay['input_manifest_sha256'],
        aggregate_metrics_equal_original=True,public_contains_individual_predictions=False,
        note='Module filenames with geoc reflect shared local code provenance; no external repository or L40 model is loaded by this runner.')
    (public/'source_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8',newline='\n')
    names={'random':'Aleatoria','climate_profile':'Perfil','municipality':'Municipal','spatial':'Espacial','fresh_97_41':'97/41 separado'}
    table='\n<!-- CURRENT_METRICS_START -->\n## Tabla de métricas reproducidas\n\n'
    table+='| Protocolo | Modelo | RMSE | R² | MAE | Sesgo |\n|---|---|---:|---:|---:|---:|\n'
    for protocol in names:
        for model in ['Reference26','Compact14','CT3','B1']:
            row=actual[(actual.protocol==protocol)&(actual.experiment==model)].iloc[0]
            table+=f'| {names[protocol]} | {model} | {row.rmse:.4f} | {row.r2:.4f} | {row.mae:.4f} | {row.bias:+.4f} |\n'
    table+='\nReconstrucción completa de81 particiones; reentrenamiento desde entradas verificado en7 folds representativos. No se reentrenaron de nuevo los81.\n<!-- CURRENT_METRICS_END -->\n'
    readme=public/'README.md';text=readme.read_text(encoding='utf-8').split('<!-- CURRENT_METRICS_START -->')[0].rstrip()
    readme.write_text(text+'\n'+table,encoding='utf-8',newline='\n')
    print(json.dumps(output,indent=2))


if __name__=='__main__':main()
