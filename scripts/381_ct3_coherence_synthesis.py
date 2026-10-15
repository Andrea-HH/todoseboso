"""Read-only scientific interpretation of the sealed coherence sensitivity."""
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import joblib,numpy as np,pandas as pd
from matplotlib import pyplot as plt
from src.ct3_residual_coherence import ROOT,OUT,SOURCE,metrics,sha

DEST=ROOT/'outputs/research/ct3_residual_coherence_synthesis/v1'
if DEST.exists():raise FileExistsError('Interpretation version already exists')
DEST.mkdir(parents=True)
inputs=[OUT/'manifest.json']+list((OUT/'tables').glob('*'))+[SOURCE/'cache/execution_plan.joblib',SOURCE/'cache/base_contexts.joblib',SOURCE/'cache/train138.parquet',Path(__file__)]
hashes={p.relative_to(ROOT).as_posix():sha(p) for p in inputs}
summary=pd.read_csv(OUT/'tables/metrics_summary.csv');registry=pd.read_csv(OUT/'tables/registry.csv');local=pd.read_csv(OUT/'tables/intraprofile_summary.csv');paired=pd.read_csv(OUT/'tables/paired_repeat.csv')
paired.groupby(['experiment','reference','protocol'])[['delta_rmse','delta_mae','delta_bias']].mean().reset_index().to_csv(DEST/'paired_summary.csv',index=False)
reg=registry.groupby(['experiment','protocol']).agg(fraction_zero=('amplitude',lambda x:float((x==0).mean())),mean_amplitude=('amplitude','mean'),mean_correction=('validation_mean_correction','mean'),max_abs_correction=('validation_max_correction','max')).reset_index();reg.to_csv(DEST/'selection_summary.csv',index=False)
plans=joblib.load(SOURCE/'cache/execution_plan.joblib');ctx=joblib.load(SOURCE/'cache/base_contexts.joblib');t=pd.read_parquet(SOURCE/'cache/train138.parquet');support=[]
for plan in plans:
    for j,item in enumerate(plan['inner']):
        for stage,cals in [('outer',[item['validation_positions']]),('inner',[d['held_positions'] for d in item['residual_contexts']])]:
            for k,cal in enumerate(cals):
                support.append(dict(protocol=plan['protocol'],repeat=plan['repeat'],fold=plan['fold'],component=j,stage=stage,calibration_component=k,n_calibration=len(cal),n_profiles=t.iloc[cal].climate_profile.nunique(),impossible_leaf15=len(cal)<30,impossible_leaf25=len(cal)<50))
sup=pd.DataFrame(support);sup.to_csv(DEST/'all_calibration_support.csv',index=False)
st=sup.groupby(['protocol','stage']).agg(n_components=('n_calibration','size'),minimum_n=('n_calibration','min'),maximum_n=('n_calibration','max'),fraction_no_split_leaf15=('impossible_leaf15','mean'),fraction_no_split_leaf25=('impossible_leaf25','mean')).reset_index();st.to_csv(DEST/'support_summary.csv',index=False)
om=pd.read_csv(OUT/'tables/omission_sensitivity.csv');delta=[]
for exp in om.experiment.unique():
    if not exp.startswith('PAIR_'):continue
    for ref in ['M0','PAIR_BASE']:
        if exp==ref:continue
        q=om[om.experiment==exp].merge(om[om.experiment==ref],on=['protocol','repeat','omitted_type','omitted'],suffixes=('_new','_ref'),validate='one_to_one')
        q['delta_rmse']=q.rmse_new-q.rmse_ref;q['experiment']=exp;q['reference']=ref
        delta.append(q[['experiment','reference','protocol','repeat','omitted_type','omitted','delta_rmse']])
pd.concat(delta).to_csv(DEST/'paired_omissions.csv',index=False)
regions=pd.read_csv(OUT/'tables/regional_repeat.csv');spatial=regions[(regions.protocol=='spatial')&(regions.group_type=='fold')];spatial.to_csv(DEST/'spatial_blocks.csv',index=False)
decisions=[]
for exp in registry.experiment.unique():
    a=summary[summary.experiment==exp].set_index('protocol');b=summary[summary.experiment=='PAIR_BASE'].set_index('protocol');m=summary[summary.experiment=='M0'].set_index('protocol')
    gains=b.rmse-a.rmse;gainoriginal=m.rmse-a.rmse
    bias_harm=(abs(a.bias)-abs(m.bias)).loc[['municipality','spatial']]
    compatible=bool(((a.rmse-m.rmse)<=.01).all() and ((a.mae-m.mae)<=.01).all() and (bias_harm<=.02).all())
    useful=bool((gains.loc[['climate_profile','municipality','spatial']]>=.01).any())
    decisions.append(dict(experiment=exp,grouped_gain_over_paired_base_ge_01=useful,no_material_harm_original=compatible,min_rmse_gain_original=float(gainoriginal.min()),max_geographic_absolute_bias_harm=float(bias_harm.max()),eligible_for_integration=useful and compatible))
pd.DataFrame(decisions).to_csv(DEST/'exploratory_decision_checks.csv',index=False)
fig,axes=plt.subplots(1,2,figsize=(12,4))
order=['random','climate_profile','municipality','spatial']
for name in ['M0','M2_Z','PAIR_BASE','PAIR_M1_LAI','PAIR_M1_Z','PAIR_M2_Z']:
    a=summary[summary.experiment==name].set_index('protocol').reindex(order)
    axes[0].plot(range(4),a.rmse,marker='o',label=name)
axes[0].set_xticks(range(4),['Aleatoria','Perfil','Municipal','Espacial']);axes[0].set_ylabel('RMSE (t/ha)');axes[0].legend(fontsize=7)
for name in ['M0','M2_Z','PAIR_BASE','PAIR_M1_Z']:
    a=spatial[spatial.experiment==name].sort_values('group');axes[1].plot(a.group.astype(int),a.bias,marker='o',label=name)
axes[1].axhline(0,color='gray',linewidth=.8);axes[1].set_xlabel('Bloque espacial');axes[1].set_ylabel('Sesgo predicho - observado (t/ha)');axes[1].legend(fontsize=7)
fig.tight_layout();fig.savefig(DEST/'performance_and_spatial_bias.png',dpi=160);plt.close(fig)
lines=['# Coherencia de la corrección residual: síntesis','', '## Diseño y controles','', 'Se reutilizaron todas las bases previamente ajustadas dentro de los entrenamientos permitidos. Cada corrector se calibra en observaciones excluidas de su base, y se aplica junto con esa misma base congelada. Se promedian cuatro parejas en cada fold externo. La selección de parámetros y amplitud usa las OOF internas originales completas, reproduciendo el procedimiento de parejas con bases profundas dentro de cada entrenamiento interno. No se emplean etiquetas externas, residuos del Champion ni parcelas PRED.','', 'PAIR_BASE es el promedio sin corrección. M0 es C-T3 original; M2_Z es su corrector CART original. PAIR_M1_LAI es Ridge LAI, PAIR_M1_Z es Ridge LAI+contexto, PAIR_M2_Z es CART LAI+contexto y PAIR_C_CONTEXT es CART sin LAI.','', '## Resultados','', '```text',summary.to_string(index=False),'```','', 'Amplitudes y correcciones:', '```text',reg.to_string(index=False),'```','', '## Soporte y límites de la comparación','', '```text',st.to_string(index=False),'```','', 'Las columnas fraction_no_split son cotas matemáticas por tamaño, sin nuevos ajustes: menos de dos veces el mínimo de hoja impide cualquier división. Otras calibraciones también pueden ser constantes por falta de variación. Una amplitud cero evita ajustar el corrector externo; no demuestra por sí sola ausencia de señal. La comparación cambia simultáneamente coherencia, tamaño de entrenamiento/calibración y agregación. Por ello no permite atribuir una diferencia de RMSE únicamente al desajuste crossfit/refit.','', '## Diagnósticos y decisión','', 'Los archivos paired_summary, paired_omissions, spatial_blocks y las tablas intraperfil distinguen la contribución del corrector del efecto de promediar bases, y permiten revisar concentración regional sin reajustes. Los umbrales exploratorios de 0.01 t/ha y 0.02 de sesgo geográfico conservan los de la etapa anterior; son criterios prácticos, no pruebas de significancia.','',pd.DataFrame(decisions).to_string(index=False),'', 'La coherencia de pares elimina por construcción el cambio de base después de calibrar. Un resultado negativo debilita la utilidad práctica de esta formulación con 138 etiquetas y los límites congelados, pero no refuta todas las correcciones residuales. Si los árboles quedan desactivados por soporte o selección, no demuestra que una interacción suficientemente medida no exista.','', '## Reproducibilidad','', 'Cuatro pruebas pasaron: exclusión de etiquetas externas a nivel de corrector y de pipeline completo, rechazo de muestras solapadas y comportamiento sin soporte para dividir. Se reprodujeron 260 predictores guardados completos. No hubo nuevos ajustes de bases, ajuste final sobre 138, cambio al Champion ni predicciones PRED. Modelos dependientes de las bases archivadas protegidas, con claves explícitas en cada paquete. Intervalos predictivos no se ofrecen: estos modelos deterministas no contienen un procedimiento de incertidumbre calibrado.']
(DEST/'informe.md').write_text('\n'.join(lines),encoding='utf-8')
for path,h in hashes.items():assert sha(ROOT/path)==h
(DEST/'manifest.json').write_text(json.dumps(dict(status='complete',new_fits=0,tests_passed=4,inputs=hashes,artifacts={p.relative_to(ROOT).as_posix():sha(p) for p in DEST.rglob('*') if p.is_file() and p.name!='manifest.json'}),indent=2),encoding='utf-8')
print(summary[summary.experiment.str.startswith('PAIR')|summary.experiment.eq('M0')].to_string(index=False));print(reg.to_string(index=False));print(st.to_string(index=False));print(pd.DataFrame(decisions).to_string(index=False))
