"""Summarize four completed studies, preserving frozen champions and59 outputs."""
from pathlib import Path
import json
import hashlib
import runpy
from collections import Counter
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/research/four_final_checks/v1'
PUB=ROOT/'results/four_final_checks/v1'
PROTOCOLS=['random','climate_profile','municipality','spatial']


def stats(g):
    e=g.y_pred-g.y_true;den=np.sum((g.y_true-g.y_true.mean())**2)
    return dict(n=len(g),rmse=float(np.sqrt(np.mean(e*e))),r2=float(1-np.sum(e*e)/den) if den>1e-12 else np.nan,mae=float(abs(e).mean()),bias=float(e.mean()),within05=float((abs(e)<=.5).mean()))


def bootstrap_delta(a,b,y,groups,draws=5000):
    rng=np.random.default_rng(2026);unique=np.unique(groups);indices=[np.flatnonzero(groups==g) for g in unique];values=[]
    for _ in range(draws):
        chosen=np.concatenate([indices[i] for i in rng.integers(0,len(unique),size=len(unique))])
        values.append(float(np.sqrt(np.mean((a[:,chosen]-y[chosen])**2,axis=1)).mean()-np.sqrt(np.mean((b[:,chosen]-y[chosen])**2,axis=1)).mean()))
    return np.quantile(values,[.025,.975])


def main():
    files=list((OUT/'no_hhi_memory').glob('*/complete.json'));assert len(files)==65,f'Only {len(files)}/65 folds complete'
    design=json.loads((ROOT/'configs/four_final_checks/v1/frozen_design.json').read_text(encoding='utf-8'))
    for source,digest in design['code_sha256'].items():
        assert hashlib.sha256((ROOT/source).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==digest,source
    for i in [0,63]:assert json.loads((OUT/'control_memory'/f'{i:02d}/complete.json').read_text())['maximum_difference_vs26']<1e-10
    new=pd.concat([pd.read_parquet(OUT/'no_hhi_memory'/f'{i:02d}/oof.parquet') for i in range(65)],ignore_index=True)
    assert len(new)==1794 and not new.duplicated(['execution_index','ID_POLIGONO']).any()
    old=pd.read_parquet(ROOT/'data/processed/current_champions/v1/expected_oof.parquet')
    old=old[(old.execution_index<65)&old.experiment.isin(['Reference26','Compact14','CT3'])]
    key=['execution_index','ID_POLIGONO'];anchor=old[old.experiment=='Reference26']
    check=new.merge(anchor,on=key,suffixes=('_new','_old'),validate='one_to_one')
    np.testing.assert_array_equal(check.y_true_new,check.y_true_old)
    for c in ['protocol','repeat','fold']:np.testing.assert_array_equal(check[c+'_new'],check[c+'_old'])
    p=pd.concat([new,old],ignore_index=True);p.to_parquet(OUT/'sensitivity_matched_oof.parquet',index=False)
    rows=[dict(experiment=m,protocol=pro,repeat=re,**stats(g)) for (m,pro,re),g in p.groupby(['experiment','protocol','repeat'])]
    byrepeat=pd.DataFrame(rows);byrepeat.to_csv(PUB/'sensitivity_metrics_by_repeat.csv',index=False)
    metrics=byrepeat.drop(columns='repeat').groupby(['experiment','protocol'],as_index=False).mean(numeric_only=True)
    metrics.to_csv(PUB/'sensitivity_metrics.csv',index=False)
    grouping=pd.read_csv(ROOT/'data/processed/current_champions/v1/groups.csv').set_index('ID_POLIGONO')
    helper=runpy.run_path(str(ROOT/'scripts/529_core4_relevance.py'));tests=[]
    for pro,g in p[p.experiment.isin(['Reference26','Reference25_NoHHI'])].groupby('protocol'):
        ids=sorted(g.ID_POLIGONO.unique());truth=g[['ID_POLIGONO','y_true']].drop_duplicates().set_index('ID_POLIGONO').loc[ids].y_true.to_numpy()
        values={m:h.pivot(index='repeat',columns='ID_POLIGONO',values='y_pred').reindex(columns=ids).to_numpy() for m,h in g.groupby('experiment')}
        a=values['Reference25_NoHHI'];b=values['Reference26'];groups=grouping.loc[ids,pro if pro in ['municipality','spatial'] else 'climate_profile'].astype(str).to_numpy()
        loss=np.mean((a-truth)**2-(b-truth)**2,axis=0);low,high=bootstrap_delta(a,b,truth,groups)
        tests.append(dict(protocol=pro,delta_rmse_NoHHI_minus26=float(np.sqrt(np.mean((a-truth)**2,axis=1)).mean()-np.sqrt(np.mean((b-truth)**2,axis=1)).mean()),low95_fixed_oof=float(low),high95_fixed_oof=float(high),**helper['signflip'](loss,groups)))
    tests=pd.DataFrame(tests);tests['p_holm4']=helper['holm'](tests.p_two_sided);tests.to_csv(PUB/'sensitivity_paired_tests.csv',index=False)
    regions=[];omissions=[]
    for (m,pro,re),g in p.groupby(['experiment','protocol','repeat']):
        g=g.copy();g['spatial_block']=g.ID_POLIGONO.map(grouping.spatial)
        for axis in ['Estado','Municipio','spatial_block']:
            for zone,h in g.groupby(axis):
                regions.append(dict(experiment=m,protocol=pro,repeat=re,axis=axis,region=str(zone),**stats(h)))
                other=g[g[axis]!=zone]
                omissions.append(dict(experiment=m,protocol=pro,repeat=re,axis=axis,omitted=str(zone),**stats(other)))
    regional=pd.DataFrame(regions).drop(columns='repeat').groupby(['experiment','protocol','axis','region'],as_index=False).mean(numeric_only=True)
    omitted=pd.DataFrame(omissions).drop(columns='repeat').groupby(['experiment','protocol','axis','omitted'],as_index=False).mean(numeric_only=True)
    regional.to_csv(PUB/'sensitivity_regional_metrics.csv',index=False);omitted.to_csv(PUB/'sensitivity_omission_metrics.csv',index=False)
    runtime=[];warning_types=Counter()
    for i in range(65):
        r=json.loads((OUT/'no_hhi_memory'/f'{i:02d}/complete.json').read_text())
        assert len(r['core'])==3 and 'compact_concentration_hhi' not in r['core'] and r['exclusions_passed']
        warning_types.update(w['category'] for w in r['warnings'])
        runtime.append(dict(fold=i,seconds=r['seconds'],R3_strength=r['R3_strength'],gate_k=r['gate_k'],warnings=len(r['warnings']),ledger_records=r['ledger_records']))
    pd.DataFrame(runtime).to_csv(PUB/'sensitivity_execution_audit.csv',index=False)
    snapshot=json.loads((OUT/'delivery_snapshot.json').read_text())['files']
    for name,value in snapshot.items():assert hashlib.sha256((ROOT/'outputs/modeling/current_champions_final/v1'/name).read_bytes()).hexdigest()==value
    audit=dict(status='complete',studies=4,no_HHI_external_folds=65,new_predictions_oof=1794,core_removed_from_both_consumers=True,
        baseline_control_folds=[0,63],baseline_control_max_difference=max(json.loads((OUT/'control_memory'/f'{i:02d}/complete.json').read_text())['maximum_difference_vs26'] for i in [0,63]),
        frozen_final_files_unchanged=True,new_final_fit=False,new_PRED_point_predictions=False,new_champion=False,
        sensitive_model='Reference25_NoHHI; candidate only, not champion',sum_worker_seconds=sum(r['seconds'] for r in runtime),warning_categories=dict(warning_types),convergence_warnings=warning_types.get('ConvergenceWarning',0))
    (PUB/'complete_audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8',newline='\n')
    summary_report(metrics,tests,audit)
    support=pd.read_csv(OUT/'support59.csv');interval=pd.read_parquet(OUT/'interval_assessment.parquet')
    with pd.ExcelWriter(OUT/'cuatro_investigaciones.xlsx') as writer:
        for name,table in [('NoHHI_metrics',metrics),('NoHHI_tests',tests),('NoHHI_regions',regional),('NoHHI_omissions',omitted),('support59',support),('interval_metrics',pd.read_csv(PUB/'interval_metrics.csv')),('intervals_by_state',pd.read_csv(PUB/'interval_metrics_by_state.csv')),('OOF_NoHHI',new)]:table.to_excel(writer,sheet_name=name,index=False)
    fig,ax=plt.subplots(figsize=(7,4));x=np.arange(4);ordered=tests.set_index('protocol').loc[PROTOCOLS]
    ax.vlines(x,ordered.low95_fixed_oof,ordered.high95_fixed_oof,color='tab:blue')
    ax.scatter(x,ordered.delta_rmse_NoHHI_minus26,color='tab:blue')
    ax.axhline(0,color='gray',linestyle='--');ax.set_xticks(x,PROTOCOLS);ax.set(ylabel='RMSE sin HHI − RMSE26 (t/ha)',title='Sensibilidad25: diferencias OOF, IC descriptivos por grupos');ax.grid(alpha=.2);fig.tight_layout();fig.savefig(PUB/'NoHHI_delta_RMSE.png',dpi=160);plt.close(fig)
    provenance=dict(source_code={f:hashlib.sha256((ROOT/f).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for f in ['src/reference26_only.py','scripts/535_no_hhi_reference26.py','scripts/536_operational_support_intervals.py','scripts/537_run_sensitivity_battery.py','scripts/538_finalize_four_checks.py','scripts/539_clean_replay_environment.py']},code_hash='CRLF normalized to LF',protected_delivery=snapshot)
    (PUB/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(metrics.to_string(index=False));print(tests.to_string(index=False));print(json.dumps(audit,indent=2))


def summary_report(metrics,tests,audit):
    operational=json.loads((PUB/'operational_audit.json').read_text())
    clean=json.loads((PUB/'clean_environment_audit.json').read_text()) if (PUB/'clean_environment_audit.json').exists() else {'status':'not_complete'}
    support=pd.read_csv(PUB/'support_summary.csv');interval=pd.read_csv(PUB/'interval_metrics.csv')
    text='# Cuatro investigaciones finales — entrega, soporte, intervalos y HHI\n\n'
    text+='**Los únicos champions siguen siendo Reference26 y Compact14.** Se preservaron los modelos y las59 predicciones finales por SHA256. La sensibilidad Reference25_NoHHI es una candidata experimental; no sustituye automáticamente a26. Las59 etiquetas siguen desconocidas.\n\n'
    text+='## 1. Entrega congelada y reproducción\n\n'
    text+='Los archivos de ambos champions contienen59 IDs únicos, coincidentes con el conjunto esperado, valores finitos/positivos y las mismas predicciones que la comparación conjunta. Se generaron copias locales de presentación con encabezado `ID_parcela` y rendimiento en t/ha, sin envío externo. La reproducción se ejecutó en proceso y venv aislados, con barrera de lectura que impide acceder a otros datos privados fuera del paquete final.\n\n'
    text+=f"Reproducción en venv que comparte paquetes instalados: **{operational['isolated_replay']['status']}**. Intento adicional de instalación limpia, sin paquetes compartidos: **{clean['status']}**. [Auditoría operativa](operational_audit.json) · [Instalación limpia](clean_environment_audit.json). Un resultado en Windows no demuestra portabilidad a otros sistemas.\n\n"
    if clean['status']=='passed':text+='La instalación limpia reprodujo las59 estimaciones dentro de1e-10t/ha con versiones fijadas. Los requisitos efectivos están en [replay_requirements.txt](../../../configs/four_final_checks/v1/replay_requirements.txt).\n\n'
    else:text+='La instalación limpia no queda acreditada. Se conserva el fallo/limitación exacta en la auditoría; el replay aislado compartiendo las versiones instaladas sí se evalúa por separado.\n\n'
    text+='## 2. Soporte de las59 parcelas\n\n'
    text+='Se usan distancias sin objetivo, umbrales95% de referencias de entrenamiento y disponibilidad de indicadores. No se ajustan modelos con las59 ni se usan sus etiquetas. Un aviso de soporte es diagnóstico, **no probabilidad de fallo ni evidencia de que la estimación sea incorrecta**.\n\n'
    text+='| Región | n | R3 incompleto | Geografía fuera q95 | Núcleo4 fuera q95 | Local7 fuera q95 | Geología nueva | Desacuerdo26–14 elevado | Algún aviso |\n|---|---|---|---|---|---|---|---|---|\n'
    for _,r in support.iterrows():text+=f'| {r.region} | {int(r.n)} | {int(r.missing_R3)} | {int(r.geo_above_training_q95)} | {int(r.core4_above_training_q95)} | {int(r.local7_above_training_q95)} | {int(r.unseen_geology)} | {int(r.disagreement_above_OOF_q95)} | {int(r.any_flag)} |\n'
    text+='\nLos avisos pueden coincidir en la misma parcela; no se suman como casos distintos. Los ocho R3 incompletos conservan la predicción de base sin esa corrección, conforme a la receta. El bajo desacuerdo26–14 no garantiza acierto compartido. La tabla privada `support59.csv` contiene IDs, municipios y distancias para el dashboard.\n\n'
    text+='## 3. Intervalos: cobertura observada y límites\n\n'
    text+='Se evaluaron niveles80% y90% con modelos OOF ya congelados. Cada fold externo se divide sin mirar Y en dos mitades: una calibra residuos absolutos y la otra evalúa; se intercambian después sus funciones. Una parcela no usa su propia etiqueta para calibrar su intervalo. El radio usa el estadístico de orden `ceil((m+1)·nivel)`; si no existe ese orden, se conserva radio infinito, sin inventar un límite finito.\n\n'
    text+='**Diagnóstico principal: aleatorio, separación por parcelas, nivel nominal90%.**\n\n| Modelo | Cobertura observada | Ancho medio t/ha | Intervalos finitos |\n|---|---|---|---|\n'
    for model in ['Reference26','Compact14']:
        r=interval[(interval.model==model)&(interval.protocol=='random')&(interval.strategy=='parcel_split')&(interval.level==.9)].iloc[0]
        text+=f'| {model} | {100*r.coverage:.2f}% | {r.mean_width_finite:.3f} | {100*r.finite_fraction:.1f}% |\n'
    text+='\nLas mitades de calibración pequeñas hacen que el90% nominal sea conservador. La cobertura se acompaña de intervalos amplios: no equivale a gran precisión parcelaria. Los resultados por estado están en [interval_metrics_by_state.csv](interval_metrics_by_state.csv); la cobertura marginal no asegura cobertura por cada estado o parcela.\n\n'
    text+='**Advertencia de dependencia:** al separar perfiles completos y calibrar máximos por perfil, hay pocos grupos. Para90%, sólo≈4.7% de los casos aleatorios tienen intervalos finitos; una cobertura cercana a100% con radios infinitos no es un éxito útil. Esto muestra el límite de138 observaciones agrupadas, no un método listo para prometer certidumbre territorial.\n\n'
    text+='Los protocolos municipal/espacial se incluyen como diagnósticos, pero su calibración utiliza algunas etiquetas del territorio externo: **no certifican transferencia a un territorio sin ninguna etiqueta disponible**. El banco97/41 se mantiene separado. [Tabla completa](interval_metrics.csv) · [Auditoría](interval_audit.json).\n\n'
    text+='**No se atribuye un intervalo garantizado a la predicción final del modelo entrenado con138.** La cobertura se midió para modelos retenidos y una calibración separada. Reentrenar con todas las138 y trasladar esos anchos sin validar sería otra receta. Las etiquetas se han reutilizado históricamente y la intercambiabilidad no está garantizada por perfiles o espacio. Referencia: [MAPIE, split y cross-conformal y sus supuestos](https://mapie.readthedocs.io/en/stable/content/conformal-prediction/split-cross-conformal/).\n\n'
    text+='## 4. Reference25_NoHHI: retiro de HHI en sus dos usos\n\n'
    text+='Se eliminó físicamente HHI de las entradas: la base y el corrector interno usan lluvia total, fracción temprana y NDVI mayo. Se mantuvieron experto7,24 vecinos, Ridge30, geología10 y K4/8, rejillas Elastic Net e intensidad/soporte R3. Cada capa se recalibró dentro del entrenamiento externo, con las65 particiones e internas originales. No se reajustó el campeón final ni se generaron59 predicciones para la candidata.\n\n'
    text+='Antes de entrenar la sensibilidad, el adaptador de26 sin cambios reprodujo los controles aleatorio0 y espacial63 con diferencia máxima inferior a1e-10t/ha. Los trabajadores están aislados: configurar tres entradas no altera módulos o modelos históricos en disco. [Diseño congelado](../../../configs/four_final_checks/v1/frozen_design.json).\n\n'
    text+=f"Los65 folds completaron la verificación de exclusión de entrenamiento/evaluación; advertencias de convergencia: **{audit['convergence_warnings']}**. Se registraron advertencias ambientales, sin ocultarlas: `{audit['warning_categories']}`. El detalle permanece en cada checkpoint privado y los tiempos en [auditoría de ejecución](sensitivity_execution_audit.csv).\n\n"
    text+='Cada celda es **RMSE t/ha / R²**. Se promedian métricas de OOF completas por repetición.\n\n| Modelo | Aleatoria | Perfil | Municipal | Espacial |\n|---|---|---|---|---|\n'
    for model in ['Reference26','Reference25_NoHHI','Compact14','CT3']:
        cells=[]
        for protocol in PROTOCOLS:
            r=metrics[(metrics.experiment==model)&(metrics.protocol==protocol)].iloc[0];cells.append(f'{r.rmse:.4f} / {r.r2:.4f}')
        text+='| '+model+' | '+' | '.join(cells)+' |\n'
    text+='\n### Comparaciones pareadas contra26\n\nDelta negativo favorece la candidata sin HHI; positivo favorece26. Holm cubre los cuatro contrastes primarios. Los IC95% son bootstrap5000 por grupos sobre OOF fijas, no incertidumbre del reajuste ni confirmación independiente.\n\n| Protocolo | Delta RMSE sinHHI−26 | IC95% OOF fijas | p Holm4 |\n|---|---|---|---|\n'
    for _,r in tests.iterrows():text+=f'| {r.protocol} | {r.delta_rmse_NoHHI_minus26:+.4f} | [{r.low95_fixed_oof:+.4f}, {r.high95_fixed_oof:+.4f}] | {r.p_holm4:.5g} |\n'
    text+='\nLos grupos de inferencia son perfiles para aleatoria/perfil, municipios para municipal y bloques para espacial. La enumeración de signos presupone condiciones de simetría/independencia de grupos; cinco bloques dan escasa resolución estadística. La corrección no elimina la selección histórica previa. [Pruebas](sensitivity_paired_tests.csv) · [MAE, sesgo y métricas](sensitivity_metrics.csv) · [Regiones](sensitivity_regional_metrics.csv) · [Omisiones sin reajustar](sensitivity_omission_metrics.csv).\n\n'
    gains=[r.protocol for _,r in tests.iterrows() if r.delta_rmse_NoHHI_minus26<0];losses=[r.protocol for _,r in tests.iterrows() if r.delta_rmse_NoHHI_minus26>0]
    text+='La candidata mejora puntualmente en: '+(', '.join(gains) or 'ningún protocolo')+'. Empeora en: '+(', '.join(losses) or 'ningún protocolo')+'. No se declara un nuevo champion a partir de esta comparación. El resultado de retirar HHI de C-T3 no se traslada automáticamente al sistema compuesto; ésta es su comprobación en la arquitectura completa.\n\n'
    if gains and losses:
        text+='**Recomendación:** conservar26/14 como entrega vigente. Retirar HHI representa un intercambio entre protocolos y no una sustitución que domine a26. La credibilidad aumenta al documentar esa sensibilidad, no al ocultar el protocolo que empeora. Una decisión de cambio requeriría un criterio de uso declarado y evidencia adicional; estos resultados reutilizan las mismas138 etiquetas.\n\n'
    elif len(gains)==4:
        text+='**Recomendación:** mantener26/14 mientras se revisa la candidata. Las cuatro mejoras puntuales justifican una revisión, pero no prueban superioridad confirmatoria ni autorizan generar otra entrega automáticamente.\n\n'
    else:
        text+='**Recomendación:** conservar26/14. La retirada de HHI no proporciona una mejora general que justifique sustituir la entrega.\n\n'
    regional=pd.read_csv(PUB/'sensitivity_regional_metrics.csv')
    spatial=regional[(regional.protocol=='spatial')&(regional.axis=='spatial_block')&regional.experiment.isin(['Reference26','Reference25_NoHHI'])]
    text+='### Distribución espacial de la diferencia\n\n| Bloque | RMSE26 | RMSE sin HHI | Delta |\n|---|---|---|---|\n'
    for zone,g in spatial.groupby('region'):
        a=g[g.experiment=='Reference25_NoHHI'].iloc[0];b=g[g.experiment=='Reference26'].iloc[0]
        text+=f'| {zone} | {b.rmse:.4f} | {a.rmse:.4f} | {a.rmse-b.rmse:+.4f} |\n'
    text+='\nLos bloques son conjuntos geográficos de validación; se conservan sus etiquetas0–4 del artefacto original, sin renumerarlos. Esta descomposición no seleccionó hiperparámetros ni reglas regionales. Las omisiones publicadas recalculan métricas sin un grupo, sin reajustar modelos. No convierten el resultado externo en confirmación independiente.\n\n'
    block_metrics=spatial.pivot(index='region',columns='experiment',values='rmse')
    block_n=spatial[spatial.experiment=='Reference26'].set_index('region').n
    contribution=(block_metrics.Reference26.pow(2)-block_metrics.Reference25_NoHHI.pow(2))*block_n
    if contribution.sum()>0:
        leader=contribution.idxmax();share=100*contribution.max()/contribution.sum()
        omission=pd.read_csv(PUB/'sensitivity_omission_metrics.csv')
        selected=omission[(omission.protocol=='spatial')&(omission.axis=='spatial_block')&(omission.omitted.astype(str)==str(leader))].set_index('experiment')
        diff=selected.loc['Reference25_NoHHI','rmse']-selected.loc['Reference26','rmse']
        text+=f'La mayor contribución a la reducción neta de error cuadrático espacial proviene del bloque **{leader}**: equivale al **{share:.1f}%** de esa reducción neta, después de compensar bloques que empeoran. Al omitir ese bloque del cálculo, el delta RMSE sinHHI−26 es **{diff:+.4f}t/ha**. Es una medida de concentración del beneficio, no porcentaje de parcelas beneficiadas.\n\n'
    municipal=regional[(regional.protocol=='municipality')&(regional.axis=='Municipio')&regional.experiment.isin(['Reference26','Reference25_NoHHI'])]
    text+='### Distribución municipal\n\n| Municipio | RMSE26 | RMSE sin HHI | Delta |\n|---|---|---|---|\n'
    for zone,g in municipal.groupby('region'):
        a=g[g.experiment=='Reference25_NoHHI'].iloc[0];b=g[g.experiment=='Reference26'].iloc[0]
        text+=f'| {zone} | {b.rmse:.4f} | {a.rmse:.4f} | {a.rmse-b.rmse:+.4f} |\n'
    text+='\nUn cambio de RMSE municipal en municipios pequeños tiene escaso soporte. Estas tablas describen el intercambio territorial y no justifican seleccionar modelos distintos por municipio con sus mismos residuos externos.\n\n'
    text+='![Sensibilidad y rangos de variación](NoHHI_delta_RMSE.png)\n\n'
    text+='## Entrega y uso recomendado\n\n'
    text+='Para el dashboard, mostrar predicción y componentes junto con disponibilidad histórica, distancia al soporte y avisos descriptivos. No convertir avisos o desacuerdo en probabilidades de error, ni anunciar intervalos garantizados para59. La sensibilidad se presenta como investigación adicional y los champions permanecen26/14 hasta una decisión explícita.\n\n'
    text+='Excel privado: `outputs/research/four_final_checks/v1/cuatro_investigaciones.xlsx`; contiene resultados, soporte por ID, regiones y candidatos OOF. Copias de presentación59 en `submission/` dentro de esa carpeta; no se enviaron externamente. [Auditoría de cierre](complete_audit.json) · [Configuración](../../../configs/four_final_checks/v1/frozen_design.json). Scripts535–539 reproducen la ejecución; las operaciones nuevas se guardaron separadas de los artefactos previos.\n'
    text+='\n## Reproducción local\n\nRequiere los artefactos privados del proyecto. Mantener los archivos de configuración congelados y sus enmiendas de implementación, que registran cambios de rendimiento computacional sin cambiar decisiones estadísticas. Las seis copias finales se verifican por SHA256 antes y después.\n\n'
    text+='```powershell\npython scripts/535_no_hhi_reference26.py worker --mode control --fast --folds 0,63\npython scripts/537_run_sensitivity_battery.py\npython scripts/536_operational_support_intervals.py support\npython scripts/536_operational_support_intervals.py intervals\npython scripts/538_finalize_four_checks.py\n```\n\n'
    text+='El supervisor reanuda únicamente folds que no tienen marcador de finalización. La auditoría operativa inicial y la instalación limpia se ejecutan con `python scripts/536_operational_support_intervals.py operational` y `python scripts/539_clean_replay_environment.py`. La primera crea el registro de los archivos protegidos; conservar ese registro para auditar la misma entrega. Los modelos transitorios interiores se mantienen en memoria; cada ajuste externo final se guarda. Se comprobó paridad con la ejecución original antes de utilizar esta optimización, sin ampliar rejillas o cambiar particiones.\n'
    (PUB/'README.md').write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':main()
