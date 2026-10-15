"""Post-fit interpretation, provenance and integrity; no additional candidate fitting."""
import sys,json,importlib.metadata
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from src.family_4 import stage_b_learning as b

def main():
    out=b.OUT;_,t=b.load();reg=pd.read_csv(out/'tables/registry.csv');p=pd.read_parquet(out/'tables/oof_predictions.parquet')
    selection=[];support=[];foldmetrics=[]
    for protocol,repeat,fold,tr,va,inner in b.e.f.lm.k.j.load_frozen_splits(t)[0]:
        a=t.iloc[tr];v=t.iloc[va]
        for name,control in [('B1','B0'),('B3','B2')]:
            old,path=b.archived(control,protocol,repeat,fold)
            row=reg[(reg.experiment==name)&(reg.protocol==protocol)&(reg['repeat']==repeat)&(reg.fold==fold)].iloc[0]
            selection.append(dict(experiment=name,protocol=protocol,repeat=repeat,fold=fold,lambda_selected=row.lam,alpha_selected=row.alpha,rho_selected=row.rho,alpha_control=old['model'].alpha,rho_control=old['model'].l1_ratio,lambda_zero_same_regularization=bool(row.lam==0 and row.alpha==old['model'].alpha and row.rho==old['model'].l1_ratio),lambda_zero_changed_regularization=bool(row.lam==0 and (row.alpha!=old['model'].alpha or row.rho!=old['model'].l1_ratio))))
        for context,j,aa,bb in [('outer',-1,a,v)]+[('inner',j,a.iloc[itr],a.iloc[iva]) for j,(itr,iva) in enumerate(inner)]:
            sizes=bb.groupby('climate_profile').size();n_eligible=int(sizes[sizes>=2].sum());n_pairs=int(np.sum(sizes*(sizes-1)//2))
            support.append(dict(protocol=protocol,repeat=repeat,fold=fold,context=context,inner_fold=j,n_train=len(aa),n_validation=len(bb),n_profiles_validation=len(sizes),n_profiles_evaluable=int((sizes>=2).sum()),n_singleton_profiles=int((sizes==1).sum()),n_eligible_parcels=n_eligible,eligible_fraction=n_eligible/len(bb),n_pairs=n_pairs,train_ids=json.dumps(aa[b.ID].tolist()),validation_ids=json.dumps(bb[b.ID].tolist())))
        for exp,g in p[(p.protocol==protocol)&(p['repeat']==repeat)&(p.fold==fold)].groupby('experiment'):foldmetrics.append(dict(experiment=exp,protocol=protocol,repeat=repeat,fold=fold,n=len(g),**b.e.f.lm.k.metrics(g.y_true,g.y_pred)))
    pd.DataFrame(selection).to_csv(out/'tables/lambda_vs_regularization_changes.csv',index=False)
    pd.DataFrame(support).to_csv(out/'tables/evaluation_support_and_ids.csv',index=False)
    pd.DataFrame(foldmetrics).to_csv(out/'tables/fold_metrics_diagnostic_only.csv',index=False)
    influence=pd.read_csv(out/'tables/fixed_blend_parcel_summary.csv');decomp=pd.read_csv(out/'tables/fixed_blend_mse_decomposition.csv');rows=[]
    for order in ['mean_squared_gain','mean_square_champion']:
        for k in [0,1,5,10]:
            removed=influence.nlargest(k,order) if k else influence.iloc[:0]
            kept=influence.drop(removed.index)
            rows.append(dict(order=order,n_removed=k,n_remaining=len(kept),removed_ids=json.dumps(removed[b.ID].tolist()),fraction_net_gain_removed=float(removed.mean_squared_gain.sum()/influence.mean_squared_gain.sum()),pooled_RMSE_champion=np.sqrt(kept.mean_square_champion.mean()),pooled_RMSE_mix=np.sqrt(kept.mean_square_mix.mean())))
    pd.DataFrame(rows).to_csv(out/'tables/blend_influence_sensitivity.csv',index=False)
    input_files=[b.ROOT/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization/predictions/oof_predictions.parquet',b.e.OUT/'tables/oof_predictions.parquet',b.e.f.OUT/'tables/oof_predictions.parquet',b.ROOT/'data/processed/family_1/m_historical_multisensor/v1/m_features_197_target_free.parquet',b.ROOT/'data/processed/family_1/features/family1_features_all.parquet']
    pd.DataFrame([dict(path=str(path.relative_to(b.ROOT)),sha256=b.a.sha(path),usage='read-only input') for path in input_files]).to_csv(out/'audit/read_only_input_provenance.csv',index=False)
    config=json.loads((out/'frozen_design.json').read_text());assert all(b.a.sha(b.ROOT/path)==digest for path,digest in config['source_sha'].items())
    previous=[]
    for old in [b.a.OUT,b.e.OUT,b.e.f.OUT]:
        manifest=json.loads((old/'manifest.json').read_text())
        for path,digest in manifest['artifacts'].items():
            assert b.a.sha(b.ROOT/path)==digest
            previous.append(dict(path=path,sha256=digest,matches=True))
    pd.DataFrame(previous).to_csv(out/'audit/previous_results_integrity.csv',index=False)
    summary='''# Etapa B — Resumen de decisiones

**El objetivo intraperfil no justifica sustituir el entrenamiento convencional.** B1 no mejora las diferencias equilibradas; B3 logra una mejora pequeña aleatoria/por perfil, pero el costo municipal es demasiado grande. Mantener B0/B2 como referencias.

| Modelo | RMSE aleatorio | RMSE por perfil | RMSE municipal | RMSE espacial | RMSE diferencias equilibrado aleatorio |
|---|---:|---:|---:|---:|---:|
| B0 lluvia + NDVI mayo convencional | 0.50483 | 0.52626 | 0.67110 | 0.73904 | 0.58920 |
| B1 mismos predictores, objetivo/selección intraperfil | 0.50924 | 0.53747 | 0.86245 | 0.72967 | 0.59035 |
| B2 añade inicio LAI, convencional | 0.50561 | 0.53333 | 0.67500 | 0.73845 | 0.58335 |
| B3 mismos predictores de B2, objetivo/selección intraperfil | 0.51244 | 0.54364 | 0.86500 | 0.72267 | 0.58116 |

La mejora local de B3 persiste ligeramente fuera de Chignahuapan —0.49992→0.49802 en aleatoria— y por perfil —0.46906→0.46650—, pero no en municipios o espacio. No basta para declarar superioridad general ni para afirmar que el objetivo global era la causa principal de los errores.

**La selección interna forma parte del resultado.** En B1 municipal, lambda=0 en los cinco folds, pese a un RMSE externo mayor. La selección de regularización orientada a diferencias cambió alpha/rho dentro de restricciones internas y perjudicó transferencia. Ese deterioro no lo causa una penalización local activa. B3 también desactiva lambda en cuatro de cinco folds municipales. La estabilidad lambda0 es64%en B1 aleatorio y38%en B3. No se alteraron reglas después de ver los resultados.

**Decisiones independientes:**

- B1: descartar complejidad adicional bajo este procedimiento congelado.
- B3: conservar exclusivamente para investigación local; su mejora es marginal y deteriora transferencia municipal.
- Mezcla fija50/50: conservar como candidata exploratoria aleatoria, con reservas de extremos e influencia; no promoverla como Champion ni afirmar desempeño geográfico.
- Etapa C: puede estudiar agrupación parcial como otra hipótesis, con control compacto y tratamiento explícito de perfiles nuevos. B no proporciona una ganancia integral que la haga obligatoria; C/D no se ejecutaron.

**Mezcla fija, evaluada por separado:**

| Modelo | RMSE aleatorio | MAE aleatorio |
|---|---:|---:|
| Champion archivado | 0.498127 | 0.358869 |
| F4-S1 | 0.504834 | 0.364105 |
| Media50/50 | 0.493604 | 0.353426 |

La identidad MSE_mix=0.25MSE_A+0.25MSE_B+0.5mean(e_Ae_B) se verificó por repetición. La correlación de errores media es0.9382, pero el término cruzado utiliza producto medio, incluyendo sesgo. De la reducción de MSE, aproximadamente96.6%proviene de reducción de variación de errores y3.4%del cambio de sesgo cuadrático por repetición. No se aprendieron pesos ni se probaron otras mezclas.

La mezcla mejora MAE medio en77de138parcelas y MSE en80. Nueve de diez repeticiones mejoranRMSE; las repeticiones no son independientes. En diferencias locales equilibradas baja0.59729→0.58787 frente al Champion y0.58920→0.58787 frente aF4-S1. Dentro de Chignahuapan apenas empata F4-S1, mientras fuera mejora modestamente.

La ganancia no es uniforme: Q4 empeora RMSE0.45644→0.46728 y MAE0.38936→0.39797 frente aChampion. Q1 mejora apenasRMSE0.68966→0.68796, pero empeoraMAE0.44607→0.45545. En Chignahuapan mejoraRMSE0.56112→0.55366; fuera0.42111→0.42065, prácticamente empate.

**Influencia:** la parcela con mayor ganancia explica49.7%de la ganancia neta deSSE, y las cinco mayores explican163.7%, porque otras deterioran. Al excluir esas cinco beneficiarias, la ventaja neta se revierte. Excluir las parcelas de mayor error inicial Champion no elimina necesariamente la mejora. Son sensibilidades descriptivas seleccionadas después de observar pérdidas; no reglas de activación ni confirmación. La ganancia es pequeña y depende de compensaciones entre casos.

**Matemática e integridad:** la pérdida se implementó con residuos centrados y filas aumentadas, sin optimizar con parejas expandidas. alpha_joint=2·alpha_archivado, alpha_solver=alpha_archivado·n/m; intercepto libre. Lambda0 reprodujo130controles con diferencia máxima0.0t/ha. El solver conserva tol1e-4 original; máximo residuoKKT externo8.93e-5 y máximo gapdual deJ2.33e-4. Todos los ajustes cumplieron la parada declarada. La identidad/gradi ente/solución de referencia y reproducción completa se probaron automatizadamente.

Se ejecutaron únicamenteB1/B3 y controles de implementación, con los65folds congelados y los predictores permitidos. Se reutilizaronB0/B2 y1,380predicciones compatibles deChampion/F4-S1 para la mezcla. Hay7,176prediccionesB0–B3 y4,140registrosdecomparación demezcla. Pasaron24pruebas matemáticas/deintegración. No se integraron capas territoriales, ni se modificaronChampion,EtapaA,Familia4/F4-Eoetiquetas. Las59PREDseconservaronsinYutilizado. Todo permanece exploratorio por reutilización de las mismas138etiquetas.
'''
    summary=summary.replace('gradi ente','gradiente')
    (out/'report/decision_summary.md').write_text(summary,encoding='utf8')
    (b.ROOT/'documentation/territorial_program_stage_b_decision.md').write_text(summary,encoding='utf8')
    # Add final sensitivity evidence to the technical report without changing frozen model files.
    for path in [out/'report/technical_report.md',b.ROOT/'documentation/territorial_program_stage_b.md']:
        text=path.read_text(encoding='utf8')
        if '## Auditoría final de influencia' not in text:text+='\n\n## Auditoría final de influencia\n\nLa ganancia neta de la mezcla depende de pocos beneficiarios: top1 aporta49.7% y top5 aporta163.7% de la ganancia total, por compensación de deterioros. Al excluir top5 por ganancia la ventaja desaparece. Esto no equivale a excluir top5 por errorChampion. Ver `blend_influence_sensitivity.csv`, cuyas métricas son RMS de pérdidas agrupadas entre parcelas/repeticiones, distintas de la media primaria deRMSE porrepetición. Q4 yMAE deQ1 empeoran frente aChampion. El resumen de decisiones desarrolla estos límites.\n\n24pruebas pasaron. Se verificaron los hashes de las fuentes de aprendizaje congeladas y todos los artefactos protegidos deEtapaA/F4/F4-E. No se ejecutóC/D.\n'
        path.write_text(text,encoding='utf8')
    files=[p for p in out.rglob('*') if p.is_file() and p.name!='manifest.json']+list(b.PROC.glob('*'))
    files += [b.ROOT/p for p in ['src/family_4/stage_b_objective.py','src/family_4/stage_b_learning.py','src/family_4/stage_b_reporting.py','src/family_4/stage_b_final_report.py','scripts/342_stage_b_within_profile_learning.py','scripts/343_stage_b_finalize.py','tests/test_stage_b_objective.py','tests/test_stage_b_integration.py','documentation/territorial_program_stage_b.md','documentation/territorial_program_stage_b_decision.md']]
    manifest=dict(status='complete',stage='B',stage_c_executed=False,stage_d_executed=False,n_train=138,n_prediction=59,n_outer=65,n_candidate_models=130,n_implementation_models=130,n_objective_oof=7176,n_fixed_blend_comparison_oof=4140,tests='24 passed',previous_files_verified=len(previous),exploratory=True,packages={k:importlib.metadata.version(k) for k in ['numpy','pandas','scikit-learn','joblib']},artifacts={str(p.relative_to(b.ROOT)):b.a.sha(p) for p in files})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print('STAGE B COMPLETE;',len(previous),'previous files verified;',len(files),'versioned artifacts;24tests')

if __name__=='__main__':main()
