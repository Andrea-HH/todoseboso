"""Read-only matched OOF comparison: no fitting, no PRED59 predictions."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'outputs/modeling/four_expert_combinations/v1/tables'
OUT = ROOT / 'outputs/research/four_architecture_explanation/v1'
MODELS = ['Reference26', 'Compact14', 'B1', 'L40']
KEY = ['execution_index', 'protocol', 'repeat', 'fold', 'ID_POLIGONO']


def summarize(f):
    e = f.y_pred.to_numpy() - f.y_true.to_numpy()
    ae = np.abs(e)
    sst = np.sum((f.y_true - f.y_true.mean()) ** 2)
    return dict(n=len(f), rmse=np.sqrt(np.mean(e**2)),
                r2=1-np.sum(e**2)/sst if sst > 0 else np.nan,
                mae=ae.mean(), bias=e.mean(), error_sd=e.std(),
                median_absolute=np.median(ae), p95_absolute=np.quantile(ae, .95),
                within_025=np.mean(ae <= .25), within_05=np.mean(ae <= .5),
                within_1=np.mean(ae <= 1), overestimate=np.mean(e > 0),
                underestimate=np.mean(e < 0))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    f = pd.read_parquet(SOURCE / 'oof_residuals.parquet')
    f = f[f.experiment.isin(MODELS)].copy()
    assert not f.duplicated(KEY + ['experiment']).any()
    assert np.allclose(f.error, f.y_pred-f.y_true)
    assert f.groupby(KEY).size().eq(4).all()
    assert f.groupby(KEY).y_true.nunique().eq(1).all()
    meta = f.groupby(KEY, as_index=False)[['y_true','Estado','Municipio','climate_profile']].first()
    wide = meta.merge(f.pivot(index=KEY, columns='experiment', values='y_pred').reset_index(), on=KEY, validate='one_to_one')
    for m in MODELS:
        wide.rename(columns={m:'pred_'+m}, inplace=True)
        wide['error_'+m] = wide['pred_'+m]-wide.y_true
        wide['residual_obs_minus_pred_'+m] = -wide['error_'+m]
        wide['abs_error_'+m] = wide['error_'+m].abs()
    wide['prediction_range'] = wide[['pred_'+m for m in MODELS]].max(axis=1)-wide[['pred_'+m for m in MODELS]].min(axis=1)
    wide.to_csv(OUT/'all_matched_oof_predictions.csv', index=False)
    wide[wide.protocol != 'fresh_97_41'].to_csv(OUT/'original_65_folds_predictions.csv', index=False)
    wide[wide.protocol == 'fresh_97_41'].to_csv(OUT/'separate_97_41_predictions.csv', index=False)
    repeat = pd.DataFrame([dict(experiment=m,protocol=p,repeat=r,**summarize(g)) for (m,p,r),g in f.groupby(['experiment','protocol','repeat'])])
    metrics = repeat.groupby(['experiment','protocol'],as_index=False).mean(numeric_only=True).drop(columns='repeat')
    old = pd.read_csv(SOURCE/'metrics.csv')
    check = metrics.merge(old,on=['experiment','protocol'],suffixes=('_new','_old'))
    for metric in ['rmse','r2','mae','bias','p95_absolute','within_05']:
        assert np.allclose(check[metric+'_new'],check[metric+'_old'],rtol=1e-10,atol=1e-12), metric
    repeat.to_csv(OUT/'metrics_by_repeat.csv',index=False)
    metrics.to_csv(OUT/'metrics.csv',index=False)
    regions=[]
    for axis in ['Estado','Municipio']:
        for (m,p,r,region),g in f.groupby(['experiment','protocol','repeat',axis]):
            regions.append(dict(experiment=m,protocol=p,repeat=r,axis=axis,region=region,**summarize(g)))
    regional = pd.DataFrame(regions).groupby(['experiment','protocol','axis','region'],as_index=False).mean(numeric_only=True).drop(columns='repeat')
    regional.to_csv(OUT/'regional_metrics.csv',index=False)
    parcels = f.groupby(['experiment','protocol','ID_POLIGONO','Estado','Municipio'],as_index=False).agg(y_true=('y_true','first'),mean_oof_prediction=('y_pred','mean'),sd_oof_prediction=('y_pred','std'),mean_signed_error=('error','mean'),n_evaluations=('error','size'))
    loss = f.assign(absolute=f.error.abs(),square=f.error**2).groupby(['experiment','protocol','ID_POLIGONO'],as_index=False).agg(mae=('absolute','mean'),mse=('square','mean'))
    parcels=parcels.merge(loss,on=['experiment','protocol','ID_POLIGONO'],validate='one_to_one')
    parcels['rmse']=np.sqrt(parcels.mse)
    parcels.to_csv(OUT/'parcel_oof_summary.csv',index=False)
    differences=[]
    parcel_differences=[]
    for i,a in enumerate(MODELS):
        for b in MODELS[i+1:]:
            d=wide[KEY+['y_true','Estado','Municipio']].copy()
            d['pair']=a+' minus '+b
            d['prediction_difference']=wide['pred_'+a]-wide['pred_'+b]
            d['absolute_error_gain_A_vs_B']=wide['abs_error_'+b]-wide['abs_error_'+a]
            d['squared_error_gain_A_vs_B']=wide['error_'+b]**2-wide['error_'+a]**2
            parcel_differences.append(d)
            for p,g in d.groupby('protocol'):
                differences.append(dict(pair=a+' minus '+b,protocol=p,n=len(g),
                    mean_prediction_difference=g.prediction_difference.mean(),
                    mean_absolute_prediction_difference=g.prediction_difference.abs().mean(),
                    p95_prediction_disagreement=g.prediction_difference.abs().quantile(.95),
                    fraction_A_lower_absolute_error=(g.absolute_error_gain_A_vs_B>1e-12).mean(),
                    fraction_ties=(g.absolute_error_gain_A_vs_B.abs()<=1e-12).mean(),
                    mean_absolute_error_gain_A_vs_B=g.absolute_error_gain_A_vs_B.mean()))
    pairs=pd.DataFrame(differences)
    pairs.to_csv(OUT/'pairwise_prediction_disagreement.csv',index=False)
    pd.concat(parcel_differences,ignore_index=True).to_csv(OUT/'every_pairwise_oof_difference.csv',index=False)
    spatial=wide[wide.protocol=='spatial'].sort_values('prediction_range',ascending=False)
    spatial.to_csv(OUT/'spatial_parcels_sorted_by_disagreement.csv',index=False)
    # Descriptive quartiles of observed target; never predictors or selectors.
    bins = pd.qcut(f[['ID_POLIGONO','y_true']].drop_duplicates().set_index('ID_POLIGONO').y_true,4,labels=False,duplicates='drop')+1
    f['target_quartile']=f.ID_POLIGONO.map(bins)
    qrep=pd.DataFrame([dict(experiment=m,protocol=p,repeat=r,quartile=int(q),**summarize(g)) for (m,p,r,q),g in f.groupby(['experiment','protocol','repeat','target_quartile'])])
    quartiles=qrep.groupby(['experiment','protocol','quartile'],as_index=False).mean(numeric_only=True).drop(columns='repeat')
    quartiles.to_csv(OUT/'observed_target_quartiles.csv',index=False)
    for name in ['intraprofile','actual_spatial_blocks','actual_block_omissions','architecture_complexity']:
        table=pd.read_csv(SOURCE/(name+'.csv'))
        col='experiment' if 'experiment' in table else None
        if col: table=table[table[col].isin(MODELS)]
        table.to_csv(OUT/(name+'.csv'),index=False)
    with pd.ExcelWriter(OUT/'four_models_predictions_and_residuals.xlsx',engine='openpyxl') as x:
        for name,t in [('metrics',metrics),('predictions_original65',wide[wide.protocol!='fresh_97_41']),('predictions_separate97_41',wide[wide.protocol=='fresh_97_41']),('parcel_summary',parcels),('regions',regional),('prediction_differences',pairs),('target_quartiles',quartiles),('spatial_disagreement',spatial)]:
            t.to_excel(x,sheet_name=name,index=False)
        for sheet in x.book:
            sheet.freeze_panes='A2'
            sheet.auto_filter.ref=sheet.dimensions
    # Plot each original protocol separately; no pooling repeated predictions.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,4,figsize=(17,8))
    for j,p in enumerate(['random','climate_profile','municipality','spatial']):
        for m in MODELS:
            g=parcels[(parcels.protocol==p)&(parcels.experiment==m)]
            axes[0,j].scatter(g.y_true,g.mean_oof_prediction,s=12,alpha=.45,label=m)
            axes[1,j].scatter(g.y_true,g.mean_signed_error,s=12,alpha=.45)
        axes[0,j].plot([1.5,5.5],[1.5,5.5],'k--',lw=1)
        axes[1,j].axhline(0,color='black',lw=1)
        axes[0,j].set_title(p)
        axes[0,j].set_ylabel('Predicción OOF media')
        axes[1,j].set_ylabel('Error: predicción - observado')
        axes[1,j].set_xlabel('Rendimiento observado (t/ha)')
    axes[0,0].legend(fontsize=8)
    fig.suptitle('Cada punto es una parcela; en aleatoria se promedian 10 predicciones OOF. No son predicciones finales.')
    fig.tight_layout()
    fig.savefig(OUT/'predictions_and_residuals.png',dpi=170)
    plt.close(fig)
    audit=dict(source=str(SOURCE/'oof_residuals.parquet'),models=MODELS,
        matched_evaluations=len(wide),original_evaluations=int((wide.protocol!='fresh_97_41').sum()),
        separate_97_41_evaluations=int((wide.protocol=='fresh_97_41').sum()),
        metric_reproduction='passed',residual_sign='error = prediction - observed',
        adjusted_r2='Not reported: raw feature counts are not effective degrees of freedom of these adaptive pipelines.',
        no_training=True,no_PRED59=True)
    (OUT/'audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False),encoding='utf-8')
    write_report(metrics, regional, pairs, spatial, quartiles)
    print(json.dumps(audit,ensure_ascii=False))
    print(metrics[['experiment','protocol','rmse','r2','mae','bias']].to_string(index=False))
    print(spatial[['ID_POLIGONO','y_true']+['pred_'+m for m in MODELS]].head(8).to_string(index=False))


def write_report(metrics, regional, pairs, spatial, quartiles):
    def md(t):
        def fmt(v):
            return f'{v:.4f}' if isinstance(v,(float,np.floating)) else str(v)
        return '| '+' | '.join(t.columns)+' |\n| '+' | '.join(['---']*len(t.columns))+' |\n'+'\n'.join('| '+' | '.join(fmt(v) for v in row)+' |' for row in t.itertuples(index=False,name=None))
    text='''# Comparación explicada: Reference26, Compact14, B1 y Local04D

Fecha: 2026-10-18. Análisis de artefactos existentes; no se entrenaron modelos ni se generaron predicciones PRED59. Script reproducible: `scripts/518_explain_four_architectures.py`.

## Decisión y ventajas reales

Reference26 ofrece el mejor equilibrio de precisión y transferencia entre estos cuatro en las OOF disponibles. Compact14 es la alternativa de menor dependencia de datos: elimina 12 entradas, Planet, la compuerta geológica y la corrección climática interna del experto, con una pérdida pequeña de RMSE. B1 no simplifica los datos: conserva las 26 entradas y añade un peso; su mejora municipal no compensa automáticamente la pérdida espacial. L40 mantiene ventajas locales importantes, especialmente Almoloya y Cuautepec, pero transfiere peor cuando se retienen territorios enteros.

Estas son ventajas observadas, no pruebas de superioridad estadística universal. Se han reutilizado ampliamente los mismos 138 rendimientos para investigar. La batería anterior no encontró mejoras de las nuevas mezclas frente a26 que superaran el ajuste Holm. Esto no demuestra equivalencia, y no sustituye una prueba específica de no inferioridad entre14 y26.

## 1. Reference26: las entradas y sus funciones

26 entradas finales distintas =4 globales +7 del experto local +2 coordenadas +10 proporciones geológicas +3 indicadores. Son variables derivadas, no26 mediciones brutas ni26 coeficientes. Construirlas sigue requiriendo sus series satelitales e insumos cartográficos.

**Núcleo global C-T3**, Elastic Net con imputación, escalado y selección de regularización dentro del entrenamiento:

1. `compact_precip_total`: lluvia total abril–octubre2025.
2. `compact_early_fraction`: fracción de esa lluvia que cae abril–junio.
3. `compact_concentration_hhi`: suma de cuadrados de las fracciones mensuales; distingue lluvia repartida frente a concentrada.
4. `S2_ndvi_month_05`: NDVI Sentinel-2 de mayo2025.

**Experto Ridge local7**, con24 vecinos geográficos, alpha30 y potencia de distancia1:

5. `sat_basic_hist__sentinel_2__ndvi_promedio__mean`: nivel histórico NDVI.
6. `sat_basic_hist__sentinel_2__ndvi_promedio__std`: variabilidad del resumen histórico NDVI.
7. `emp_shape__y2025_planet_evi__turning_fraction`: indicador de cambios de dirección de la curva EVI Planet2025.
8. `agro_pheno__y2025_planet_ndvi__jun_to_aug_delta`: cambio NDVI Planet junio–agosto2025.
9. `sat_basic_2025__sentinel_2__ndwi_promedio__mean`: nivel de NDWI2025.
10. `sat_basic_2025__sentinel_2__ndwi_promedio__std`: variabilidad de NDWI2025.
11. `topo_official__slope__mean`: pendiente media del terreno.

Las coordenadas latitud y longitud (12–13) seleccionan vecinos: no equivalen a agregar dos pendientes lineales globales. El experto7 también recibe una corrección climática Elastic Net interna, ajustada sobre residuos cross-fitted del entrenamiento. Usa el núcleo4 ya contado; no añade otras cuatro variables distintas.

Las diez proporciones de composición geológica (14–23) construyen una compuerta física: grupos KMeans de4 u8 seleccionados internamente, con pesos de mezcla regularizados hacia un peso global. Modifican cuánto se utiliza C-T3 frente al experto; no son diez términos aditivos libres. No confundir esta compuerta con la antigua variante de textura/fase, ni con escoger vecinos por semejanza física: aquí los24 vecinos siguen siendo geográficos.

**Corrector final R3** (24–26):

- `I_history_ndvi_floor`: media2022–2024 del nivel mínimo NDVI resumido mensualmente mayo–octubre; requiere soporte histórico completo.
- `I_gap_excess_persistence`: persistencia en2025 de exceso de heterogeneidad NDVI respecto a la historia propia del mismo mes. Para los seis excesos positivos z: `(sum z)^2/(6*sum z^2)`, cero si no hay exceso. No es simplemente NDVI bajo.
- `I_slope_min`: pendiente mínima topográfica; no es pendiente temporal de NDVI.

R3 es otro Elastic Net conservador (alpha.01,l1_ratio.5), con delta `0.5*clip(pred,-0.5,0.5)`: máximo absoluto0.25t/ha antes de intensidad. Su intensidad0/.5/1 se selecciona internamente; se desactiva cuando faltan indicadores (29 de138 parcelas tienen soporte R3 incompleto). Los residuos para entrenar correctores son observado menos predicción OOF, mientras que las tablas de evaluación llaman error a predicción menos observado.

Esquema: `R26 = C + g_geología(x)*(E7-C) + intensidad*completo_R3*delta_R3`.

Ventaja arquitectónica: combina señal agroclimática global con respuesta local y un ajuste acotado; el ancla global reduce la dependencia exclusiva de vecinos. Las aportaciones numéricas de un componente no son evidencia causal de su mecanismo agronómico.

## 2. Compact14: qué conserva y qué elimina

14 =4 C-T3 +5 experto local +2 coordenadas +3 R3. Conserva historia NDVI media/desviación, NDWI2025 media/desviación y pendiente media. Elimina los dos indicadores Planet y las diez proporciones geológicas. Usa los mismos24 vecinos geográficos y Ridge alpha30,potencia1. Elimina además la corrección climática interna del experto.

Esquema: `M14 = C + w_entrenamiento*(L5-C) + intensidad*completo_R3*delta_R3`.

El peso w es global para cada modelo ajustado y aprendido con OOF internas; no es un50/50 fijo ni una regla municipal. Mantiene el corrector R3 y sus límites. La reducción es de46.2% de entradas finales; elimina una fuente satelital y una capa cartográfica de la receta, además de simplificar la mezcla y quitar una capa Elastic Net. No demuestra que todas las series originales sean prescindibles: hay que derivar los14 indicadores.

Su desventaja observada es una pequeña pérdida de RMSE y mayor error en el cuartil alto bajo validación espacial. No empeora todas las métricas: su sesgo espacial es menor que el de26 y su MAE municipal es ligeramente menor.

## 3. B1: atenuar26 hacia C-T3

`B1 = C + a_entrenamiento*(R26-C)`, con0<=a<=1. Un único peso aprendido por mínimos cuadrados restringidos sobre OOF internas honestas. No es un clasificador por municipio, no selecciona el peso con la evaluación externa y no agrega variables. Como C-T3 ya está dentro de26, B1 vuelve a atenuar conjuntamente sus desviaciones locales y correctores. Conserva26 entradas más un metaparámetro aprendido; no es una alternativa de14 entradas.

Peso medio de26: aleatoria91.4%, perfil87.1%, municipal20.0%, espacial50.5%, banco97/4193.6%. Son resúmenes de distintos ajustes de CV, no pesos operativos definidos por protocolo. No hay un único peso de despliegue porque no se entrenó el modelo final con138.

En espacial, B1 mantiene26 en los dos bloques predominantemente de Chignahuapan, elige C-T3 en los bloques originales1 y3, y mezcla aproximadamente52.5% de26 en Almoloya. El selector interno no transfirió bien en los dos bloques donde volvió a C-T3. Una mezcla convexa puede empeorar a ambos extremos en el agregado si cambia de peso entre folds y selecciona el extremo menos favorable en distintos grupos; no contradice que cada predicción esté entre sus dos extremos.

## 4. L40 / Local04D

Representación C4 de2082 variables, imputación/escalado y PCA20; Ridge local por consulta sobre24 vecinos geográficos, alpha30,potencia1. Sus20 componentes no son20 variables originales y no hay20 coeficientes globales válidos para todas las parcelas. Aquí el PCA/escalado congelado utiliza las X de197 parcelas: transductivo, sin las etiquetas ocultas. Es una condición distinta de una representación puramente inductiva ajustada sólo al entrenamiento externo.

L40 no tiene el ancla C-T3 ni el corrector R3 explícitos de las otras recetas. Tanto26 como14 ya utilizan el principio de Ridge con24 vecinos; L40 aporta principalmente otra representación. Para estas197 parcelas las componentes están disponibles y el cálculo local puede ser ligero; su mayor dependencia de insumos no implica necesariamente inferencia lenta. Para nuevas parcelas hay que reproducir C4 y su proyección.

## 5. Validación y métricas

Mismas65 particiones externas:50aleatorias (10repeticiones de5folds),5por perfil,5municipales y5espaciales. Dentro de cada repetición se calcula la métrica sobre OOF completas y luego se promedian repeticiones. No son medias de RMSE por fold. Los16 splits nuevos97/41 se muestran aparte: reutilizan los mismos138 rendimientos y no son confirmación independiente.

- Aleatoria: faltantes dispersos entre territorios ya representados.
- Perfil: se retienen perfiles climáticos completos.
- Municipal: se retienen grupos municipales según las particiones originales.
- Espacial: se retienen bloques contiguos; exige transferencia territorial.

RMSE penaliza especialmente errores grandes; MAE da el tamaño absoluto medio, no un intervalo garantizado. R²=1-SSE/TSS: más alto es mejor en la misma muestra y protocolo; .686 significa reducir68.6% la suma de errores cuadrados frente al promedio observado de esa evaluación, no68.6% de predicciones correctas. R² negativo significa peor SSE que ese promedio. Entre RMSE y R² no hay dos evidencias independientes cuando comparten muestra: ambos dependen de SSE.

El R² global mezcla separación entre estados con variación dentro de cada estado. En espacial26 tieneR² global.442, pero por estado Puebla.118,Hidalgo.390 yTlaxcala-4.035. Tlaxcala tiene poca variación y está completamente fuera del entrenamiento en uno de los bloques: por eso un desplazamiento de nivel produce un R² muy negativo. No presentar el R² global como capacidad para ordenar parcelas de cada municipio.

**R² ajustado: no reportable válidamente con los conteos14/26/20.** La fórmula clásica es `1-(1-R²)*(n-1)/(n-p-1)` para regresión lineal de dimensión fija bajo sus supuestos. En estas recetas p no equivale al número de entradas: hay regularización, regresiones distintas por consulta, vecinos, compuertas, selección interna y correctores. B1 tampoco tiene p=1: contiene todos los expertos previos. Un número calculado sustituyendo esos conteos sería una penalización arbitraria. No se estimaron grados de libertad efectivos del pipeline completo. Las OOF y la validación territorial aportan una evaluación predictiva defendible de la complejidad, aunque no eliminan la selección adaptativa entre experimentos.

Tabla: unidades t/ha excepto R².

'''
    text += md(metrics[metrics.protocol!='fresh_97_41'][['experiment','protocol','rmse','r2','mae','bias']])
    text += '\n\nBanco97/41 separado:\n\n'+md(metrics[metrics.protocol=='fresh_97_41'][['experiment','rmse','r2','mae']])
    text += '''

La mejora de26 frente a14 en aleatoria es0.002514t/ha, unos2.5kg/ha de RMSE; municipal0.000262t/ha; espacial0.009720t/ha. No justificaría la complejidad adicional solamente con esa diferencia aleatoria. En espacial la diferencia26 frente aL40 es0.346054t/ha: aquí sí cambia mucho el comportamiento territorial observado.

El objetivo observado va de2.00 a5.59t/ha, media3.955 y rango3.59. El RMSE aleatorio de26 equivale aproximadamente al12.0% de la media y13.2% del rango; su MAE.3396 equivale8.6% de la media. En espacial su RMSE representa16.0% de la media. El rango depende de extremos y no debe ser la única escala de comparación; el RMSE no significa error garantizado±.475 en cada parcela.

## 6. Convenciones de residuos y forma de la pérdida

En este repositorio, `error = predicción - observado`: positivo=sobreestimación; negativo=subestimación. Ejemplo observado4.5,predicho4.0 => error-.5. El residuo clásico suele ser observado-predicción: es el signo opuesto. El archivo de entrega incluye ambas convenciones explícitas. Al entrenar una corrección aditiva se usa observado-base, no se suma el error con el signo incorrecto.

Sesgo es error medio: puede ser casi cero por cancelación de errores grandes. RMSE²=sesgo²+varianza del error en cada evaluación; el promedio de RMSE entre repeticiones no se descompone tomando el cuadrado del promedio. P95 absoluto indica el tamaño bajo el cual cae95% de errores en esa evaluación; no es cobertura de un intervalo predictivo. Porcentaje dentro de±.5 es una tolerancia descriptiva.

'''
    text += md(metrics[metrics.protocol.isin(['random','spatial'])][['experiment','protocol','median_absolute','p95_absolute','within_05','within_1']])
    text += '\n\nLas dos últimas columnas son proporciones. En aleatoria26 y14 son muy próximos en MAE;26 reduce más la cola P95. B1 mejora poco la proporción dentro de±.5, pero no la cola. En espacial26 mantiene menor RMSE y MAE que14 aun teniendo mayor sesgo positivo: reduce la dispersión de errores lo suficiente para compensar parte de ese desplazamiento. B1 aumenta el sesgo espacial a+.286 frente a+.229 de26. L40 llega a+.471.\n\n'
    text += 'Cuartiles del rendimiento observado en espacial, análisis descriptivo y no una regla utilizable al predecir:\n\n'+md(quartiles[quartiles.protocol=='spatial'][['experiment','quartile','n','rmse','bias']])
    text += '''

Los cuatro sobreestiman el cuartil bajo y subestiman el alto, con distinta intensidad. L40 destaca en el tercer cuartil pero falla mucho en el primero;14 sacrifica más el cuartil alto que26; B1 conserva mejor parte alta a costa del primer cuartil. Por eso no existe un ganador por cada criterio a la vez.

## 7. Dónde difieren las predicciones

'''
    text += md(pairs[pairs.protocol.isin(['random','spatial'])][['pair','protocol','mean_absolute_prediction_difference','p95_prediction_disagreement','fraction_A_lower_absolute_error','fraction_ties']])
    text += '\n\nEstos desacuerdos aleatorios describen las1380 predicciones OOF, no1380 parcelas independientes. En aleatoria26 y14 difieren en promedio.045t/ha;26 yL40 en.092. En espacial aumentan a.160 y.452, respectivamente. El efecto de arquitectura es mucho mayor al cambiar el soporte territorial. Una predicción diferente no implica mejor predicción; las columnas de ganancia por parcela usan el rendimiento observado para comprobarlo.\n\n'
    cases=spatial[spatial.ID_POLIGONO.isin(['AGC_001','AGC_074','AGC_059','AGC_152'])]
    text += md(cases[['ID_POLIGONO','Municipio','y_true']+['pred_'+m for m in MODELS]])
    text += '''

AGC_074 ilustra el riesgo de extrapolar un nivel alto: L40 predice4.489 frente a2.5 observado;26 y14 moderan el nivel. AGC_059 muestra la contrapartida: L40 casi acierta4.41, y26 subestima cerca de.58. No hay una regla conocida antes de observar Y que seleccione siempre el mejor experto. Esos ejemplos documentan comportamiento, no demuestran una causa agronómica particular.

RMSE por municipio en validación espacial:

'''
    reg=regional[(regional.protocol=='spatial')&(regional.axis=='Municipio')]
    text+=md(reg.pivot(index='region',columns='experiment',values='rmse').reset_index())
    text+='''

Calpulalpan deja expuesto el principal problema deL40; Almoloya yCuautepec conservan fortalezas deL40. En Chignahuapan26 mejora aL40 en RMSE pero no gana en todas las tolerancias. B1 conserva exactamente26 en Puebla en espacial; su ganancia municipal se concentra en otros casos y no se mantiene en Singuilucan al cambiar a validación espacial.

La estructura de estas diferencias es compatible con cambios en soporte de vecinos, anclaje climático, representación y calibración interna. No identifica por sí sola qué variable causó cada diferencia. Se necesitarían atribuciones por componentes del ajuste concreto o ablaciones para hacer esa afirmación; no se infiere causalidad de comparar cuatro predicciones.

## 8. Qué contiene la entrega

- `four_models_predictions_and_residuals.xlsx`: las cuatro predicciones alineadas, métricas, errores, regiones y diferencias.
- `original_65_folds_predictions.csv`:1794 filas de evaluación con las cuatro predicciones cada una.
- `separate_97_41_predictions.csv`:656 filas del banco adicional, separado.
- `parcel_oof_summary.csv`: resumen por parcela/protocolo; media y desviación de predicciones OOF. La desviación entre repeticiones no es un intervalo predictivo; la predicción media OOF no es un modelo final.
- `every_pairwise_oof_difference.csv`: las seis parejas, diferencia de predicción y ganancias de error absoluto/cuadrático. Ganancia positiva favorece al primer modelo.
- `actual_spatial_blocks.csv`, `actual_block_omissions.csv`, `intraprofile.csv`: diagnósticos originales filtrados, sin reajuste. Intraperfil evalúa diferencias entre pares y tiene soporte limitado; no es RMSE individual.
- `predictions_and_residuals.png`: gráfico por protocolo; en aleatoria representa la media OOF por parcela y no sustituye las métricas calculadas por repetición.
- `audit.json`: verificación de alineación, signos y reproducción de las métricas anteriores.

Todas son predicciones de validación de138 parcelas con Y conocido. No se generaron ni se presentan como estimaciones finales de las59 parcelas PRED. Los modelos anteriores se conservaron sin sobrescribir.

## Recomendación

Usaría26 como referencia de precisión observada y14 como candidato preferente si importan simplicidad de fuentes, mantenimiento y explicación. La cercanía de14 no demuestra equivalencia estadística, pero sí pone un coste explícito a conservar12 entradas adicionales. No promoveríaB1 por su mínima ganancia municipal ni usaríaL40 como único modelo para territorios no representados. MantendríaL40 como benchmark de interpolación y fortaleza local, sin convertir retrospectivamente sus mejores municipios en reglas. La siguiente evidencia más valiosa es confirmación con nuevos rendimientos y evaluación operacional, antes de añadir capas para diferencias de pocos kg/ha.
'''
    target=ROOT/'documentation/four_architecture_explanation.md'
    target.write_text(text,encoding='utf-8')
    (OUT/'explanation.md').write_text(text,encoding='utf-8')


if __name__=='__main__':
    main()
