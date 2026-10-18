"""Replay new ablations, inspect saved R3, and deliver both research reports."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
import pandas as pd
import joblib
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.indicator_neighborhoods import OUT as SOURCE,CALIBRATION
OUT=ROOT/'outputs/research/j7_r3_residual_simplification/v1';D=OUT/'tables'

def md(d):
    def cell(v):return f'{v:.4f}' if isinstance(v,(float,np.floating)) else str(v).replace('|','/')
    return '\n'.join(['| '+' | '.join(d.columns)+' |','| '+' | '.join(['---']*len(d.columns))+' |']+['| '+' | '.join(map(cell,r))+' |' for r in d.itertuples(index=False,name=None)])

def main():
    assert json.loads((OUT/'complete.json').read_text())['status']=='complete'
    spec=importlib.util.spec_from_file_location('research487',ROOT/'scripts/487_j7_r3_residual_simplification.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    x=pd.read_parquet(SOURCE/'cache/features_train138_target_free.parquet');p=pd.read_parquet(D/'oof.parquet');selected=pd.read_csv(D/'selection.csv');replay=[];coefs=[]
    with threadpool_limits(limits=1):
        for fi in range(65):
            pack=joblib.load(OUT/'models'/f'{fi:02d}.joblib');old=joblib.load(CALIBRATION/'checkpoints'/f'{fi:02d}.joblib');base=pd.DataFrame(old['predictions']);base=base[base.experiment=='J7_BOTH']
            for name,item in pack.items():
                tr=item['train_positions'];va=item['validation_positions'];assert not set(tr)&set(va);q=x.iloc[va];expected=p[(p.experiment==name)&(p.protocol==base.protocol.iloc[0])&(p['repeat']==base['repeat'].iloc[0])&(p.fold==base.fold.iloc[0])].set_index('ID_POLIGONO').loc[q.ID_POLIGONO].y_pred.to_numpy();pred=base.set_index('ID_POLIGONO').loc[q.ID_POLIGONO].y_pred.to_numpy()+item['amplitude']/.5*item['model'].delta(q);difference=float(max(abs(pred-expected)));assert difference<1e-12;replay.append(dict(execution_index=fi,experiment=name,max_difference=difference))
            item=joblib.load(SOURCE/'models'/f'{fi:02d}.joblib')['models']['J7_GLOBAL_R3'];m=item['model'];local=m.model;beta=np.zeros(len(m.space.columns))
            if local.model is not None:beta[np.flatnonzero(m.space.support)[local.support]]=local.model.coef_/local.scale[local.support]
            for feature,b in zip(m.space.columns,beta):coefs.append(dict(execution_index=fi,protocol=base.protocol.iloc[0],feature=feature,amplitude=item['amplitude'],standardized_coefficient=b,active=item['amplitude']>0,median_training=m.space.med[m.space.columns.index(feature)]))
    pd.DataFrame(replay).to_csv(OUT/'model_replay.csv',index=False);c=pd.DataFrame(coefs);c.to_csv(D/'R3_coefficients_by_fold.csv',index=False);c[c.active].groupby(['protocol','feature']).standardized_coefficient.agg(['mean','min','max']).reset_index().to_csv(D/'R3_active_coefficient_summary.csv',index=False)
    # Verify metrics independently from saved predictions.
    metrics=pd.read_csv(D/'metrics_by_repeat.csv')
    for (name,pro,re),g in p.groupby(['experiment','protocol','repeat']):
        row=metrics[(metrics.experiment==name)&(metrics.protocol==pro)&(metrics['repeat']==re)].iloc[0];e=g.y_pred-g.y_true;assert abs(np.sqrt(np.mean(e**2))-row.rmse)<1e-12;assert abs(1-np.sum(e**2)/np.sum((g.y_true-g.y_true.mean())**2)-row.r2)<1e-12
    # Original J7 and R3 predictions must remain byte-for-byte numeric references.
    original=pd.read_parquet(SOURCE/'tables/oof_residuals.parquet')
    for name in ['J7_BOTH','J7_GLOBAL_R3','J7_GLOBAL_R2','CT3']:
        keys=['protocol','repeat','fold','ID_POLIGONO'];a=p[p.experiment==name].merge(original[original.experiment==name],on=keys,suffixes=('','_old'),validate='one_to_one');assert len(a)==1794;np.testing.assert_array_equal(a.y_pred,a.y_pred_old);np.testing.assert_array_equal(a.y_true,a.y_true_old)
    # Correction selection is useful only when active.
    selected.assign(active=selected.amplitude>0).groupby(['experiment','protocol']).agg(active_folds=('active','sum'),total_folds=('active','size')).reset_index().to_csv(D/'activation.csv',index=False)
    summary=pd.read_csv(D/'metrics_summary.csv');regions=pd.read_csv(D/'regions_summary.csv');quartiles=pd.read_csv(D/'quartiles_summary.csv');effects=pd.read_csv(D/'correction_effect_summary.csv');changes=pd.read_csv(D/'parcel_changes.csv');tests=pd.read_csv(D/'paired_tests.csv');arch=pd.read_csv(D/'existing_architectures_summary.csv')
    def presentation(d):
        d=d.copy();d['RMSE / R2']=d.apply(lambda z:f'{z.rmse:.4f} / {z.r2:.4f}',axis=1);return d.pivot(index='experiment',columns='protocol',values='RMSE / R2').reset_index()[['experiment','random','climate_profile','municipality','spatial']]
    base=summary[summary.experiment.isin(['J7_BOTH','J7_GLOBAL_R3'])];present=presentation(summary);present.to_csv(D/'presentation_RMSE_R2.csv',index=False)
    state=regions[(regions.experiment.isin(['J7_BOTH','J7_GLOBAL_R3']))&(regions.kind=='Estado')];state=state[['experiment','protocol','zone','n','rmse','r2','mae','bias']]
    residual_sections=[
        '# Investigación de residuos: J7 y J7 + corrector global R3',
        'Se conservan las 138 respuestas y 65 folds. Cada modelo tiene 1,794 OOF: 10 repeticiones aleatorias y una evaluación completa por perfil, municipal y espacial. Son 138 parcelas, no 1,794 observaciones independientes. Error = predicho − observado; positivo es sobreestimación. Las métricas se calculan por OOF completa de cada repetición y luego se promedian. No se ajustó ningún calibrador sobre las OOF externas.',
        '## Métricas globales',md(base[['experiment','protocol','rmse','r2','mae','bias','p95_absolute','within_05','calibration_slope']]),
        '## Qué hace la corrección',md(effects),
        'En aleatoria mejora 51.6% de las predicciones individuales y perjudica 48.4%; el cambio absoluto medio es .0512 t/ha. Esto no es una mejora uniforme. En municipal 70.3% queda sin cambio porque la selección interna apaga la corrección en tres de los cinco folds. La ganancia municipal no se distribuye entre todos los municipios: Puebla/Chignahuapan queda exactamente igual.',
        'En espacial reduce el sesgo +.2913→+.2210. La reducción de sesgo al cuadrado aporta .0360 (t/ha)²; la varianza del error aumenta .0016. Por tanto, allí mejora fundamentalmente el nivel medio y no la dispersión. En aleatoria/perfil la ganancia procede principalmente de menor varianza del error. En municipal aumenta la magnitud del sesgo global negativo, aunque baja RMSE/MAE: sesgo y precisión no son equivalentes.',
        'La cola espacial mejora: percentil95 absoluto 1.4279→1.3240, pero la proporción dentro de ±.5 t/ha cae 55.8%→53.6%. En aleatoria ese umbral mejora sólo 76.2%→76.7%. R3 reduce algunos errores grandes y empeora algunos moderados; su menor RMSE no implica que la mayoría de las parcelas quede más cerca dentro de cualquier tolerancia.',
        '## Cuartiles de rendimiento observado',md(quartiles[quartiles.experiment.isin(['J7_BOTH','J7_GLOBAL_R3'])][['experiment','protocol','zone','n','rmse','r2','mae','bias']]),
        'La corrección mejora el cuartil bajo en los cuatro protocolos. En espacial su RMSE baja 1.1198→1.0317, pero el sesgo sigue siendo +.9326 t/ha. Empeora los cuartiles altos espaciales: tercero .2508→.3337 y cuarto .4374→.4998. En aleatoria el tercero también empeora .2006→.2231; el superior mejora .4837→.4659. El modelo todavía comprime extremos. Estos cuartiles se definen usando la respuesta observada: son diagnóstico, nunca una regla utilizable al predecir. R² de grupos estrechos no es comparable con R² global.',
        '## Estados y transferencia territorial',md(state),
        'R² global aleatorio .6854 convive con .0974 dentro de Puebla y −.1492 dentro de Tlaxcala. Parte de la explicación global corresponde a diferencias entre estados; no demuestra ordenamiento preciso dentro de cada estado. Hidalgo conserva .7743. Los R² territoriales usan la media de evaluación de cada grupo como referencia descriptiva, no un baseline entrenable.',
        'En espacial Almoloya empeora .3621→.5859, y la corrección es negativa en sus diez parcelas, donde J7 ya subestimaba. Singuilucan mejora .8247→.7384 y Chignahuapan .5493→.5378. Tlaxcala mejora, pero mantiene fuerte sobreestimación y R² negativo. Municipios con una o tres parcelas no permiten conclusiones sólidas; no se generan reglas regionales.',
        '## Casos de mejora y deterioro (aleatoria)',md(pd.concat([changes[changes.protocol=='random'].nsmallest(5,'sse_gain'),changes[changes.protocol=='random'].nlargest(5,'sse_gain')])[['ID_POLIGONO','Municipio','y_true','base_error','corrected_error','correction','sse_gain']]),
        'AGC_015 mejora de +2.0800 a +1.9970 t/ha: sigue siendo un error muy grande. No se resolvió la parcela por mejorar el agregado. El deterioro espacial más claro es AGC_152, de −.6468 a −.8968, por alcanzar el límite de corrección negativa. Se entregan cambios para las 138 parcelas, no sólo los casos destacados.',
        '## Concentración, soporte e intraperfil',
        'La auditoría previa de vecindarios muestra que R3 empeora RMSE aleatorio .0059 fuera de las 35 difíciles previamente definidas; la ganancia aleatoria se concentra allí. La ganancia espacial persiste al omitir cualquiera de los cinco bloques del cálculo, sin reentrenar, pero no elimina el daño de Almoloya. Las diferencias intraperfil con igual peso por perfil mejoran en aleatoria (.5777→.5697), por perfil (.5317→.5169) y espacial (.5320→.5198), pero municipal apenas empeora (.5257→.5262). Son errores de diferencias entre pares, no errores individuales.',
        'Los mínimos históricos usan mayo–octubre 2022–2024 y la persistencia compara 2025 con esa historia. Hay 29 parcelas con historia incompleta; se imputan sólo con estadísticas del entrenamiento. La imputación no aporta la información faltante. Las correlaciones del archivo descriptive_associations son descriptivas, sin selección automática ni interpretación causal.',
        '## Estabilidad de los coeficientes del corrector',md(pd.read_csv(D/'R3_active_coefficient_summary.csv')),
        'Los coeficientes describen residuos condicionales en escala estandarizada, antes de amplitud y recorte: no son efectos causales ni t/ha por unidad física original. En aleatoria los tres signos permanecen positivos en los 50 folds; en espacial el coeficiente de NDVI histórico cambia de signo entre folds. Pendiente y persistencia conservan signo positivo en los folds activos, pero con magnitudes variables. El signo del coeficiente no equivale al signo de la corrección total: también intervienen centrado, intercepto, las otras variables, amplitud y recorte.',
        '## Incertidumbre y conclusión',md(tests[tests.experiment=='J7_GLOBAL_R3']),
        'Los intervalos usan 5,000 remuestreos por conglomerados de OOF fijas; no incorporan toda la selección histórica ni incertidumbre de reajuste. Hay 43 perfiles TRAIN, nueve municipios y cinco bloques. Ningún contraste R3 vs J7 supera Holm en esta batería de 28 contrastes; tampoco lo hizo en la batería anterior de 208. No son intervalos predictivos individuales. R3 reduce errores agregados y corrige parcialmente sobreestimación territorial, pero no resuelve transferencia, extremos ni la mayoría de las parcelas difíciles.',
        'Gráfica: outputs/research/j7_r3_residual_simplification/v1/figures/residual_comparison.png. Las gráficas aleatorias promedian predicciones por parcela únicamente para visualizar; las métricas no usan ese promedio.'
    ]
    (ROOT/'documentation/j7_r3_residual_research.md').write_text('\n\n'.join(residual_sections),encoding='utf-8')
    simplify=[
        '# Investigación de simplificación de J7 + R3',
        'Se congelaron seis nuevas ablaciones antes del entrenamiento: tres indicadores individuales, dos parejas faltantes y una corrección constante. Se recuperó la pareja persistencia + pendiente (R2) ya existente, sin reentrenarla. Cada variante conserva J7 exactamente y selecciona amplitud 0/.25/.5 con OOF internas completas, imputación/escalado dentro del entrenamiento, Elastic Net alpha .01 y l1_ratio .5 y límite final ±.25 t/ha. La comparación externa es exploratoria; no constituye confirmación independiente ni selección final.',
        '## Simplificar el corrector',md(present),
        'La simplificación más defendible es R2: persistencia de heterogeneidad NDVI + pendiente mínima. Frente a R3 pierde .0046 t/ha aleatoria, .0054 por perfil y .0020 municipal, y mejora .0022 espacial. No demuestra equivalencia, pero representa un compromiso de complejidad. Un solo indicador no conserva el balance: pendiente sola ayuda espacial, pero apenas mejora aleatoria/perfil; NDVI solo mejora aleatoria, pero empeora espacial a .6929. La pareja sin pendiente pierde espacial (.6836). No basta una corrección del promedio: el control constante llega a .6929 espacial.',
        '## Qué complejidad se ahorra realmente',
        'J7 usa 28 campos de entrada: compact4, siete entradas del experto local, quince del gate físico y dos coordenadas. R3 añade tres indicadores diferentes, por lo que son 31 campos de entrada; R2 añade dos y deja 30. No son 31 parámetros efectivos ni 31 mediciones originales. R3 requiere reconstruir historia de NDVI mínimo; R2 retira ese agregado del corrector, pero su persistencia sigue requiriendo NDVI medio/mínimo históricos. J7 también conserva NDVI histórico, Planet y geología. Quitar un indicador no elimina automáticamente una fuente ni el costo de entrenamiento del sistema.',
        'La arquitectura mantiene C-T3, Ridge local de 24 vecinos, su corrector de compact4, el gate físico y ahora el corrector global final. Este último suma pocos coeficientes; el costo principal sigue en los ajustes locales, la validación anidada y la construcción de señales. No se ha demostrado que convertir el sistema entero en un único Elastic Net conserve su capacidad.',
        '## Simplificar J7 completo: evidencia ya existente',md(presentation(arch)),
        'Estos modelos se recuperan sin nuevas ejecuciones. J7_SHARES reduce 28→23 campos usando sólo diez proporciones geológicas en el gate: conserva aleatoria (.4865 vs .4864), pero empeora espacial (.6894 vs .6808). MEAN_BOTH reduce a 21 campos sustituyendo Ridge por promedio de vecinos; pierde aleatoria/perfil y no ofrece una mejora territorial consistente. Ninguna de estas filas incluye el nuevo R3. No se suman sus diferencias a la ganancia de R3 ni se simula la combinación añadiendo un corrector entrenado sobre otra base.',
        '## Recomendación y siguiente prueba concreta',
        'Mantener R3 como referencia y R2 como alternativa mínima, sin declarar equivalencia estadística. Para simplificar todo el sistema, la siguiente prueba acotada sería J7_SHARES + corrector R2/R3 y MEAN_BOTH + R2/R3, reconstruyendo residuos y calibraciones internas de cada base. Permitiría saber si el nuevo corrector compensa retirar parte del gate o Ridge; esa compensación no está probada. No se ejecutaron estas nuevas arquitecturas en esta investigación. Evitar una búsqueda abierta por todas las subcombinaciones o elegir pesos usando los folds espaciales.',
        'Las seis nuevas ablaciones produjeron 390 sistemas externos; se guardaron modelos por fold, selecciones y predicciones OOF. Scripts reproducibles: 487 y 488. Fuentes/modelos previos permanecen intactos; no hay ajuste final138, PRED59 ni cambio de Champion. Las tablas muestran RMSE/R² separados por protocolo; no se crea una métrica mezclando validaciones distintas.'
    ]
    (ROOT/'documentation/j7_r3_simplification_research.md').write_text('\n\n'.join(simplify),encoding='utf-8')
    with pd.ExcelWriter(OUT/'residuos_y_simplificacion.xlsx',engine='openpyxl',mode='a',if_sheet_exists='replace') as writer:
        for name in ['R3_coefficients_by_fold','R3_active_coefficient_summary','activation','presentation_RMSE_R2']:pd.read_csv(D/(name+'.csv')).to_excel(writer,sheet_name=name[:31],index=False)
    design=json.loads((OUT/'frozen_design.json').read_text());assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in design['source_hashes'].items())
    files=[OUT/'residuos_y_simplificacion.xlsx',ROOT/'documentation/j7_r3_residual_research.md',ROOT/'documentation/j7_r3_simplification_research.md',D/'oof.parquet'];report=dict(status='complete',models_replayed=len(replay),max_replay_difference=max(r['max_difference'] for r in replay),reference_predictions_exact=True,metrics_verified=True,protected_sources_unchanged=True,no_PRED=True,no_champion_change=True,artifacts={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files});(OUT/'delivery_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='artifacts'},indent=2))

if __name__=='__main__':main()
