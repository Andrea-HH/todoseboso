"""Explain final59 disagreements and update status after526 completes; no fitting."""
from pathlib import Path
import sys
import json
import hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from threadpoolctl import threadpool_limits
from src.current_champions import raw_local,predict_saved

OUT=ROOT/'outputs/modeling/current_champions_final/v1'
PUBLIC=ROOT/'results/current_champions_final/v1'


def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def update(path,pairs):
    text=path.read_text(encoding='utf-8')
    for old,new in pairs:text=text.replace(old,new)
    path.write_text(text,encoding='utf-8',newline='\n')


def main():
    assert (OUT/'complete.json').is_file(),'Complete526 first'
    result=pd.read_csv(OUT/'predictions59_comparison.csv')
    frame=pd.read_parquet(OUT/'features197.parquet');distance=np.load(OUT/'distance197.npy')
    pack=joblib.load(OUT/'final_train138.joblib');outer=pack['outer_experts'];raw=outer['raw'];q=np.arange(138,197)
    # In-memory negative control: no original yield is changed or written.
    probe=frame.copy();probe.loc[q,'RENDIMIENTO_T_HA']=98765.
    with threadpool_limits(limits=1):
        original_pred=predict_saved(pack,q,frame,distance)
        perturbed_pred=predict_saved(pack,q,probe,distance)
    for name in original_pred:np.testing.assert_array_equal(original_pred[name],perturbed_pred[name])
    rows=result[['ID_POLIGONO','Estado','Municipio']].copy()
    c=raw['ct3'].predict(frame.iloc[q]);rows['CT3_native']=c
    compact=raw['compact'];cm=compact['ct3'].predict(frame.iloc[q])
    with threadpool_limits(limits=1):
        local5=raw_local(compact['local'],q,frame,distance)
        expert=raw['expert'];local7=raw_local(expert['local'],q,frame,distance)
    expert_delta=expert['amplitude']*expert['corrector'].predict(frame.iloc[q]) if expert['amplitude'] else np.zeros(59)
    shares=raw['shares'];z=shares['space'].transform(frame.iloc[q])
    gate=shares['gate'].predict(z,np.zeros(59),np.ones(59))
    rows['local5_before_blend']=local5;rows['local7_before_internal_correction']=local7
    rows['expert7_internal_delta']=expert_delta;rows['Reference26_expert_weight']=gate
    rows['Compact14_expert_weight']=compact['weight']
    complete=np.isfinite(frame.iloc[q][['I_history_ndvi_floor','I_gap_excess_persistence','I_slope_min']].to_numpy(float)).all(axis=1)
    for j,(name,base) in enumerate([('Compact14',cm+compact['weight']*(local5-cm)),('Reference26',c+gate*(local7+expert_delta-c))]):
        delta=outer['strengths'][j]*complete*outer['correctors'][j].delta(frame.iloc[q])
        rows[name+'_before_R3']=base;rows[name+'_R3_delta']=delta
        np.testing.assert_allclose(base+delta,result[name+'_t_ha'],rtol=0,atol=2e-12)
    rows.to_csv(OUT/'champion_prediction_components.csv',index=False)
    for prefix,fields in [('state','Estado'),('municipality','Municipio')]:
        result.groupby(fields)[['CT3_t_ha','Local04D_t_ha','Reference26_t_ha','Compact14_t_ha','six_model_spread_t_ha']].agg(['size','mean','std','min','max']).to_csv(OUT/(prefix+'_prediction_summary.csv'))
    fig,axes=plt.subplots(2,2,figsize=(10,9))
    for axis,(a,b) in zip(axes.flat,[('CT3_t_ha','Reference26_t_ha'),('Local04D_t_ha','Reference26_t_ha'),('CT3_t_ha','Compact14_t_ha'),('Reference26_t_ha','Compact14_t_ha')]):
        for state,g in result.groupby('Estado'):axis.scatter(g[a],g[b],label=state,s=25,alpha=.8)
        low=min(result[a].min(),result[b].min())-.1;high=max(result[a].max(),result[b].max())+.1
        axis.plot([low,high],[low,high],color='gray',linestyle='--');axis.set(xlabel=a,ylabel=b,xlim=(low,high),ylim=(low,high));axis.grid(alpha=.2)
    axes[0,0].legend();fig.suptitle('59 parcelas: diferencias entre predicciones, sin rendimientos observados')
    fig.tight_layout();fig.savefig(OUT/'prediction_scatter59.png',dpi=160);plt.close(fig)
    pairs=pd.read_csv(OUT/'pairwise_disagreement.csv')
    regions=pd.read_csv(OUT/'regional_disagreement.csv')
    report_path=PUBLIC/'README.md';report=report_path.read_text(encoding='utf-8')
    marker='\n## Interpretación de las diferencias\n'
    report=report.split(marker)[0]+marker+'\n'
    for champ in ['Reference26','Compact14']:
        for baseline in ['CT3_t_ha','Local04D_t_ha']:
            row=pairs[(pairs.model_A==baseline)&(pairs.model_B==champ+'_t_ha')].iloc[0]
            # Stored orientation is baseline minus champion.
            report+=f"- {champ} frente a {baseline}: diferencia firmada media champion−referencia **{-row.mean_A_minus_B:+.4f} t/ha**, diferencia absoluta media **{row.mean_absolute_disagreement:.4f} t/ha**.\n"
    report+='\nPor estado (diferencia firmada champion−referencia / diferencia absoluta media):\n\n| Estado | Champion | Frente a | Media firmada | Absoluta media | n |\n|---|---|---|---|---|---|\n'
    for _,r in regions[regions.scope.str.startswith('state:')&regions.model_A.isin(['CT3_t_ha','Local04D_t_ha'])&regions.model_B.isin(['Reference26_t_ha','Compact14_t_ha'])].iterrows():
        report+=f"| {r.scope[6:]} | {r.model_B} | {r.model_A} | {-r.mean_A_minus_B:+.4f} | {r.mean_absolute_disagreement:.4f} | {int(r.n)} |\n"
    report+='\nLas diferencias pueden descomponerse en la mezcla entre C-T3 y el experto y la corrección R3: `champion_prediction_components.csv` verifica que esos componentes reconstruyen exactamente las predicciones. Esto explica el cálculo; no demuestra efectos causales de variables. Los desacuerdos por municipio y las parcelas con mayor separación están en el Excel privado.\n\n'
    native_difference=float(np.mean(abs(result.CT3_native_final138_t_ha-result.CT3_t_ha)))
    report+=f'La recalibración nativa de C-T3 difiere de su consolidación histórica en **{native_difference:.4f} t/ha de diferencia absoluta media**. Por ello, la diferencia champion−C-T3 histórico incluye tanto la nueva calibración de la base como las capas complementarias; no debe atribuirse por completo al experto o a R3. El Excel conserva ambas versiones y los componentes usan la base nativa.\n\n'
    native_rows=[]
    for champion in ['Reference26','Compact14']:
        delta=result[champion+'_t_ha']-result.CT3_native_final138_t_ha
        native_rows.append(dict(champion=champion,reference='CT3_native_final138',n=59,mean_champion_minus_reference=float(delta.mean()),mean_absolute_disagreement=float(abs(delta).mean())))
    pd.DataFrame(native_rows).to_csv(OUT/'native_ct3_champion_disagreement.csv',index=False)
    report+='No se adoptó un nuevo modelo ni se cambiaron pesos según esta comparación. Las métricas de validación de138 permanecen intactas y siguen siendo la evidencia de desempeño. No se calculan residuos, R² o errores sobre las59.\n'
    report_path.write_text(report,encoding='utf-8',newline='\n')
    config_dir=ROOT/'configs/current_champions_final/v1';config_dir.mkdir(parents=True,exist_ok=True)
    for name in ['frozen_design.json','inner_splits.json']:
        (config_dir/name).write_bytes((OUT/name).read_bytes())
    audit=json.loads((OUT/'comparison_audit.json').read_text(encoding='utf-8'))
    fit=json.loads((OUT/'fit_audit.json').read_text(encoding='utf-8'))
    ledger=fit['ledger']
    assert all(not set(r['train'])&set(r['held']) and set(r['train']+r['held'])<=set(range(138)) for r in ledger)
    audit.update(internal_ledger_verified=True,unknown_target_invariance_passed=True,ledger_records=len(ledger),training_seconds=fit['elapsed_seconds'],
                 R3_strengths=fit['R3_strengths'],warning_count=len(fit['warnings']))
    audit['warning_categories']=[w['category'] for w in fit['warnings']]
    audit['warning_summary']='One environment RuntimeWarning: Intel and LLVM OpenMP both loaded. Fit and exact replay completed; no convergence warning recorded.'
    dump(PUBLIC/'prediction_audit.json',audit)
    sources=['scripts/526_current_champions_final59.py','scripts/527_finalize_prediction_comparison.py','src/current_champions.py']
    dump(PUBLIC/'provenance.json',dict(source_sha256={name:hashlib.sha256((ROOT/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for name in sources},
        final_model_sha256=hashlib.sha256((OUT/'final_train138.joblib').read_bytes()).hexdigest(),
        original_comparison_sha256=json.loads((OUT/'complete.json').read_text())['original_comparison_sha256'],
        source_hash_encoding='UTF-8 source bytes with CRLF normalized to LF; model and original CSV use raw bytes'))
    # Add component details to existing workbook without dropping prior sheets.
    with pd.ExcelWriter(OUT/'comparacion_predicciones59.xlsx',engine='openpyxl',mode='a',if_sheet_exists='replace') as writer:rows.to_excel(writer,sheet_name='champion_components',index=False)
    registry_path=ROOT/'configs/model_registry.json';registry=json.loads(registry_path.read_text(encoding='utf-8'))
    registry['decision']='Reference26 and Compact14 are current champions; native final138 fits and59 predictions generated without changing frozen architecture.'
    for model in registry['models']:
        if model['id'] in ['Reference26','Compact14']:
            model.update(final138_fit_in_latest_battery=True,new_PRED59_in_latest_battery=True,
                final_artifacts='outputs/modeling/current_champions_final/v1',final_prediction_file=model['id']+'_predictions59.csv')
    dump(registry_path,registry)
    stage_path=ROOT/'configs/current_stage.json';stage=json.loads(stage_path.read_text(encoding='utf-8'))
    stage.update(stage='current_champions_final59_comparison',new_final138_fit=True,new_PRED59=True,
        final_prediction_models=['Reference26','Compact14'],final_entry_point='scripts/526_current_champions_final59.py',
        final_comparison_models=['CT3','Historical_TOP20_TOP15','EQUAL3','L40','Reference26','Compact14'],
        final_comparison='outputs/modeling/current_champions_final/v1/comparacion_predicciones59.xlsx',
        final_comparison_report='results/current_champions_final/v1/README.md')
    stage['decision_source']='Explicit user instruction to incorporate both current champions into the existing59 comparison.'
    dump(stage_path,stage)
    root_pairs=[
        ('Esta selección no implica que ya exista un ajuste final138 o una nueva entrega59 de ambos champions.', 'Ambos champions ya tienen ajuste final con138 rendimientos y59 predicciones incorporadas a la comparación existente.'),
        ('OOF reproducibles, sin nuevo ajuste final138/PRED59', 'OOF reproducibles y ajuste final138 con59 predicciones'),
        ('OOF reproducibles, sin nuevo ajuste final138/PRED59', 'OOF reproducibles y ajuste final138 con59 predicciones')]
    update(ROOT/'README.md',root_pairs)
    note='\n**Predicciones finales disponibles:** los dos champions se ajustaron con138 rendimientos y se incorporaron a la comparación existente de59. [Comparación entre predicciones](results/current_champions_final/v1/README.md); no se conoce aún su error real.\n'
    text=(ROOT/'README.md').read_text(encoding='utf-8')
    if note not in text:(ROOT/'README.md').write_text(text+note,encoding='utf-8',newline='\n')
    for name in ['documentation/model_registry.md','documentation/current_champions_reproduction.md']:
        update(ROOT/name,[('sin nuevo ajuste final138 ni nuevas59','con ajuste final138 y59 predicciones'),
            ('No se generan modelos finales138 ni predicciones59.', 'La auditoría de OOF descrita abajo no generó finales. Posteriormente se consolidaron ambos champions con138 y se generaron59 estimaciones; véase la comparación final.' )])
        text=(ROOT/name).read_text(encoding='utf-8')
        link='\n**Etapa posterior de predicción final:** [26/14 incorporados a la comparación59](../results/current_champions_final/v1/README.md). Los modelos y resultados históricos se conservan.\n'
        if link not in text:(ROOT/name).write_text(text+link,encoding='utf-8',newline='\n')
    print('Component parity, scatter plot, regional tables and final status complete.',flush=True)


if __name__=='__main__':main()
