"""Descriptive rainfall diagnostics and honest out-of-fold reporting."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr
from .rainfall_features import ID, MONTHS
from .rainfall_modeling import metrics, profile_groups

def savefig(fig, output, name):
    fig.tight_layout();fig.savefig(output/'figures'/name,dpi=160);plt.close(fig)

def exploratory(climate, features, supervised, geography, dictionary, output):
    """Y is supplied already gated to ENTRENAMIENTO; no feature selection here."""
    out=Path(output); sns.set_theme(style='whitegrid')
    cycle=climate[climate.month.between(4,10)].copy()
    current=cycle[cycle.year.eq(2025)].merge(geography[[ID,'Estado','Municipio']],on=ID,validate='many_to_one')
    current.groupby('month').precip_mean.describe().to_csv(out/'tables/10_monthly_distribution.csv')
    temporal=cycle.groupby(['year','month']).precip_mean.agg(['mean','std','min','max'])
    temporal.to_csv(out/'tables/11_spatial_temporal_variability.csv')
    totals=cycle.groupby([ID,'year']).precip_mean.agg(lambda s:s.sum(min_count=7)).reset_index(name='rain_total')
    totals.to_csv(out/'tables/12_yearly_totals.csv',index=False)
    current.groupby(['Estado','Municipio','month']).precip_mean.agg(['count','mean','std','min','max']).to_csv(out/'tables/13_geographic_monthly.csv')
    features.drop(columns=[ID,'CONJUNTO'],errors='ignore').describe().T.to_csv(out/'tables/14_feature_distribution.csv')
    cat=dictionary.loc[dictionary.units.eq('calendar month category'),'feature_name'].tolist()
    numeric=features.drop(columns=[ID,'CONJUNTO']+cat,errors='ignore')
    corr=numeric.corr();corr.to_csv(out/'tables/15_feature_correlations.csv')
    redundant=[]
    for j,a in enumerate(corr):
        for b in corr.columns[j+1:]:
            if abs(corr.loc[a,b])>=.98:redundant.append({'feature_a':a,'feature_b':b,'pearson':corr.loc[a,b]})
    pd.DataFrame(redundant).to_csv(out/'tables/16_redundancy_pairs.csv',index=False)
    associations=[]
    for c in numeric:
        q=supervised[[c,'RENDIMIENTO_T_HA']].dropna()
        rho=spearmanr(q[c],q.RENDIMIENTO_T_HA).statistic if q[c].nunique()>1 else np.nan
        associations.append({'feature_name':c,'n_train':len(q),'spearman':rho})
    pd.DataFrame(associations).merge(dictionary[['feature_name','feature_family']],on='feature_name').to_csv(out/'tables/17_exploratory_y_associations.csv',index=False)
    for c in cat:
        supervised.groupby(c).RENDIMIENTO_T_HA.agg(['count','mean','std']).to_csv(out/'tables'/f'17_category_{c}.csv')
    wide=climate.pivot(index=ID,columns=['year','month'],values='precip_mean').sort_index()
    ids=wide.index; geo=geography.set_index(ID).loc[ids]
    distances=cdist(geo[['x','z']],geo[['x','z']]);np.fill_diagonal(distances,np.inf)
    nearest=distances.argmin(axis=1);values=wide.to_numpy()
    pd.DataFrame({ID:ids,'nearest_ID':ids[nearest],'distance_m':distances[np.arange(len(ids)),nearest],
                  'profile_RMSE_mm':np.sqrt(np.mean((values-values[nearest])**2,axis=1)),
                  'profile_max_abs_difference_mm':np.max(abs(values-values[nearest]),axis=1)}).to_csv(out/'tables/18_nearby_profile_similarity.csv',index=False)
    groups=profile_groups(climate,features[ID])
    profiles=pd.DataFrame({ID:features[ID],'profile_group':groups})
    profiles.to_csv(out/'tables/19_all_profile_groups.csv',index=False)
    within=supervised[[ID,'RENDIMIENTO_T_HA']].merge(profiles,on=ID)
    within['profile_mean_y']=within.groupby('profile_group').RENDIMIENTO_T_HA.transform('mean')
    within.groupby('profile_group').RENDIMIENTO_T_HA.agg(['count','mean','std','min','max']).to_csv(out/'tables/20_within_profile_y_variability.csv')
    bound=float(np.sqrt(np.mean((within.RENDIMIENTO_T_HA-within.profile_mean_y)**2)))
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    sns.boxplot(data=current,x='month',y='precip_mean',ax=axes[0]);axes[0].set_ylabel('Precipitación (mm/mes)')
    pivot=current.pivot(index=ID,columns='month',values='precip_mean')
    axes[1].plot(range(4,11),pivot.T,color='steelblue',alpha=.08)
    axes[1].plot(range(4,11),pivot.mean(),color='black',lw=2,label='Media parcelas')
    axes[1].set(xlabel='Mes 2025',ylabel='mm/mes');axes[1].legend();savefig(fig,out,'01_monthly_series.png')
    fig,ax=plt.subplots(figsize=(7,4));sns.boxplot(data=totals,x='year',y='rain_total',ax=ax);ax.set_ylabel('Acumulado abril–octubre (mm)');savefig(fig,out,'02_historical_totals.png')
    an=features[[f'rain_anomaly_{m}' for m in MONTHS]].rename(columns={f'rain_anomaly_{m}':m for m in MONTHS}).melt(var_name='month',value_name='anomaly')
    fig,ax=plt.subplots(figsize=(8,4));sns.boxplot(data=an,x='month',y='anomaly',ax=ax);ax.axhline(0,color='black',lw=1);ax.set_ylabel('Anomalía absoluta (mm)');savefig(fig,out,'03_anomalies.png')
    selected=['rain_total','rain_std','rain_max_share','rain_early_share','rain_longest_increase_streak','rain_longest_decrease_streak','rain_anomaly_total','rain_precycle_total']
    fig,axes=plt.subplots(2,4,figsize=(14,7))
    for c,ax in zip(selected,axes.flat):ax.hist(features[c].dropna(),bins=15);ax.set_title(c,fontsize=9)
    savefig(fig,out,'04_feature_histograms.png')
    fig,ax=plt.subplots(figsize=(9,7));sns.heatmap(corr.loc[selected,selected],vmin=-1,vmax=1,cmap='coolwarm',annot=True,fmt='.2f',ax=ax);savefig(fig,out,'05_correlations.png')
    fig,axes=plt.subplots(1,3,figsize=(13,4))
    for c,ax in zip(['rain_total','rain_anomaly_total','rain_longest_increase_streak'],axes):
        ax.scatter(supervised[c],supervised.RENDIMIENTO_T_HA,alpha=.65,s=20);ax.set(xlabel=c,ylabel='Rendimiento (t/ha)')
    savefig(fig,out,'06_exploratory_y.png')
    mapped=geography.merge(features[[ID,'rain_total']],on=ID)
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    sc=axes[0].scatter(mapped.x,mapped.z,c=mapped.rain_total,cmap='Blues',s=18);fig.colorbar(sc,ax=axes[0],label='mm abril–octubre')
    axes[0].set(xlabel='Este EPSG:6372 (m)',ylabel='Norte (m)')
    sns.boxplot(data=mapped,x='Estado',y='rain_total',ax=axes[1]);axes[1].set_ylabel('mm abril–octubre');savefig(fig,out,'07_geographic_rainfall.png')
    n_groups=len(np.unique(groups))
    (out/'report/exploratory_report.md').write_text(f'''# Exploración hídrica

197 filas parcelarias, 48 meses; no se cuentan meses como observaciones supervisadas. Solo 138 parcelas intervienen en asociaciones con rendimiento. Los mapas muestran centroides proyectados; Estado/Municipio son diagnósticos y grupos de validación, nunca predictores del módulo.

Se identifican {n_groups} grupos de perfiles prácticamente equivalentes usando distancia máxima mensual ≤0.01 mm en 48 meses y enlace completo. Las diferencias de vecinos están en 18_nearby_profile_similarity.csv. CHIRPS tiene resolución 0.05°: compartir píxel reduce fuertemente la distinción entre parcelas.

RMSE descriptivo dentro de perfiles tras asignar la media del propio grupo: {bound:.4f} t/ha. Es un diagnóstico optimista ajustado a las mismas etiquetas, NO una métrica de validación ni un límite fuera de muestra. La dispersión intragrupo muestra rendimiento que estos perfiles no distinguen.

Las tablas 10–20 contienen distribución mensual, variabilidad espacial y temporal, acumulados 2022–2025, regiones, cada variable derivada, correlaciones, redundancias, asociaciones por familia y variabilidad intraperfil. No se seleccionan variables con estas asociaciones. Total y media son redundantes; etapas suman al total y sus proporciones suman 1. No se incluyen simultáneamente en los modelos todos estos candidatos.

La referencia 2022–2024 no es normal climatológica; las rachas son mensuales y las etapas calendáricas no son fases observadas del cultivo. Enero–marzo se examina por separado sin atribuirlo a humedad almacenada.

'''+'\n'.join(f'![{p.stem}](../figures/{p.name})\n' for p in sorted((out/'figures').glob('*.png'))),encoding='utf-8')
    return {'profile_groups_001mm':n_groups,'within_profile_descriptive_RMSE':bound}

def model_report(p, fm, registry, comparison, geography, output, audit, eda):
    out=Path(output)
    # Report the fitted transformer's actual columns, never its dropped remainder.
    registry=registry.copy()
    for idx,row in registry.iterrows():
        path=out/'models'/f'{row.protocol}_{int(row["repeat"]):02d}_{int(row.fold):02d}_{row.experiment}.joblib'
        model=joblib.load(path)
        columns=[]
        if row.experiment!='E0_MEAN':
            for _,transformer,names in model.named_steps['features'].transformers_:
                if transformer!='drop':columns.extend(list(names))
        registry.loc[idx,'columns']=json.dumps(columns)
        registry.loc[idx,'n_features']=len(columns)
        params=json.loads(row.parameters)
        if 'columns' in params:params['columns']=columns
        registry.loc[idx,'parameters']=json.dumps(params)
    registry.to_csv(out/'tables/01_experiment_registry.csv',index=False)
    averaged=p.groupby(['protocol','experiment',ID]).agg(y_true=('y_true','first'),y_pred=('y_pred','mean')).reset_index()
    # Averaged OOF is used for diagnostic figures only; primary comparison averages whole-repeat metrics.
    averaged['error']=averaged.y_pred-averaged.y_true
    averaged=averaged.merge(geography[[ID,'Estado','Municipio']],on=ID)
    regions=[]
    for (protocol,exp),q in averaged.groupby(['protocol','experiment']):
        for field in ['Estado','Municipio']:
            for name,g in q.groupby(field):
                if len(g)>=5:regions.append(dict(protocol=protocol,experiment=exp,region_type=field,region=name,n=len(g),**metrics(g.y_true,g.y_pred)))
    pd.DataFrame(regions).to_csv(out/'tables/21_regional_diagnostic_metrics.csv',index=False)
    segments=[]
    for (protocol,exp),q in averaged.groupby(['protocol','experiment']):
        lo,hi=q.y_true.quantile([.25,.75]);q=q.copy();q['segment']=np.where(q.y_true<=lo,'LOW',np.where(q.y_true>=hi,'HIGH','MID'))
        for seg,g in q.groupby('segment'):segments.append(dict(protocol=protocol,experiment=exp,segment=seg,n=len(g),**metrics(g.y_true,g.y_pred)))
    segments=pd.DataFrame(segments);segments.to_csv(out/'tables/22_yield_segment_diagnostics.csv',index=False)
    co=pd.read_csv(out/'tables/04_coefficients.csv')
    stability=co.groupby(['protocol','experiment','feature_name']).coefficient_original_numeric_units.agg(['mean','std','min','max',lambda s:(s>0).mean()]).rename(columns={'<lambda_0>':'positive_fraction'})
    stability.to_csv(out/'tables/23_coefficient_stability.csv')
    choice=registry[registry.experiment.eq('E7_NESTED_COMBINED')].groupby(['protocol','columns']).size().rename('outer_fold_count').reset_index()
    choice.to_csv(out/'tables/24_inner_selected_families.csv',index=False)
    random=comparison[comparison.protocol.eq('random')].sort_values('RMSE_mean')
    best=random.iloc[0]; base=random[random.experiment.eq('E0_MEAN')].iloc[0]
    # Predeclared cautious gate: >=5% RMSE gain and wins >=80% random folds;
    # all grouped protocols must beat their own baseline. Still an exploratory candidate.
    f=fm[fm.protocol.eq('random')]; cand=f[f.experiment.eq(best.experiment)].merge(f[f.experiment.eq('E0_MEAN')],on=['repeat','fold'],suffixes=('_c','_b'))
    win=float((cand.RMSE_c<cand.RMSE_b).mean())
    grouped=comparison[(comparison.protocol.ne('random'))&comparison.experiment.eq(best.experiment)]
    gate=bool(best.relative_RMSE_improvement>=.05 and win>=.8 and (grouped.delta_RMSE<0).all() and best.experiment!='E0_MEAN')
    decision={'best_random_experiment':best.experiment,'candidate':best.experiment if gate else None,
              'candidate_status':'exploratory_only' if gate else 'no_robust_candidate',
              'random_fold_win_fraction':win,'gate':'at least 5% random RMSE gain, 80% fold wins, beats baseline under every grouped protocol',
              'independent_test_available':False}
    (out/'report/candidate_decision.json').write_text(json.dumps(decision,indent=2),encoding='utf-8')
    root=Path(__file__).resolve().parents[2]
    external_path=root/'outputs/modeling/residual_signal_audit/stage6_architecture_optimization/predictions/oof_predictions.parquet'
    external=[]
    if external_path.exists():
        previous=pd.read_parquet(external_path)
        target=p[p.protocol.eq('random') & p.experiment.eq('E0_MEAN')][[ID,'repeat','fold','y_true']]
        for name,g in previous.groupby('architecture'):
            q=g.merge(target,on=[ID,'repeat','fold'],suffixes=('','_rain'),validate='one_to_one')
            if len(q)!=len(target) or not np.allclose(q.y_true,q.y_true_rain):continue
            m=[metrics(r.y_true,r.y_pred) for _,r in q.groupby('repeat')]
            external.append({'experiment':name,'family':'existing integrated architecture','protocol':'random',
                             **{k+'_mean':np.mean([v[k] for v in m]) for k in m[0]},'same_folds_verified':True})
    pd.DataFrame(external).to_csv(out/'tables/25_existing_model_comparison.csv',index=False)
    selected=['E0_MEAN','E1_TOTAL_LINEAR','E3_MONTHLY_RIDGE','E7_NESTED_COMBINED']
    fig,axes=plt.subplots(2,2,figsize=(10,9))
    for name,ax in zip(selected,axes.flat):
        q=averaged[(averaged.protocol=='random')&(averaged.experiment==name)]
        ax.scatter(q.y_true,q.y_pred,s=18,alpha=.7);bounds=[q.y_true.min(),q.y_true.max()];ax.plot(bounds,bounds,'k--');ax.set(title=name,xlabel='Observado t/ha',ylabel='Predicción OOF media t/ha')
    savefig(fig,out,'08_observed_predicted.png')
    q=averaged[(averaged.protocol=='random')&(averaged.experiment==best.experiment)]
    fig,axes=plt.subplots(1,2,figsize=(11,4));axes[0].scatter(q.y_pred,q.error,s=20);axes[0].axhline(0,color='black');axes[0].set(xlabel='Predicción OOF media (t/ha)',ylabel='Error pred − real (t/ha)')
    axes[1].hist(q.error,bins=20);axes[1].set_xlabel('Error pred − real (t/ha)');savefig(fig,out,'09_errors.png')
    fig,ax=plt.subplots(figsize=(12,7));sns.barplot(data=comparison,x='RMSE_mean',y='experiment',hue='protocol',ax=ax);ax.set_xlabel('RMSE OOF medio por repetición (t/ha)');savefig(fig,out,'10_experiment_performance.png')
    fig,ax=plt.subplots(figsize=(8,4));sns.barplot(data=segments[segments.experiment.eq(best.experiment)],x='segment',y='bias_pred_minus_y',hue='protocol',ax=ax);ax.axhline(0,color='black');savefig(fig,out,'11_bias_by_yield.png')
    regional=pd.DataFrame(regions)
    fig,ax=plt.subplots(figsize=(8,4));sns.barplot(data=regional[regional.experiment.eq(best.experiment)&regional.region_type.eq('Estado')],x='region',y='RMSE',hue='protocol',ax=ax);savefig(fig,out,'12_regional_errors.png')
    # Explicit magnitudes and partition sensitivity for simple models and monthly Ridge.
    linear=stability.loc[('random','E1_TOTAL_LINEAR')]
    monthly=stability.loc[('random','E3_MONTHLY_RIDGE')]
    abs_total=co[(co.protocol=='random')&(co.experiment=='E2_TOTAL_QUADRATIC')]
    poly=abs_total.pivot(index=['repeat','fold'],columns='feature_name',values='coefficient_original_numeric_units')
    if {'rain_total','rain_total^2'}<=set(poly):
        poly['stationary_point_mm']=-poly.rain_total/(2*poly['rain_total^2'])
        poly.to_csv(out/'tables/26_quadratic_stability.csv')
    warnings='No hay prueba final independiente; comparar múltiples experimentos introduce optimismo de selección. Las 50 particiones se solapan: desviaciones y win rates son descriptivos, no 50 muestras independientes. Solo hay un ciclo etiquetado: no se prueba generalización a otro año. Coeficientes no causales y pueden reflejar ubicación, suelo, variedad, manejo o riego no observados. La colinealidad impide atribuir importancia agronómica a un mes a partir del signo de su coeficiente.'
    rm=random.set_index('experiment')
    grouped_best=comparison[(comparison.experiment==best.experiment)&comparison.protocol.ne('random')]
    explanatory=f'''El total solo alcanza R² predictivo {rm.loc['E1_TOTAL_LINEAR','R2_mean']:.3f}; la distribución mensual alcanza {rm.loc['E3_MONTHLY_RIDGE','R2_mean']:.3f}. La pendiente simple es {float(linear.iloc[0]['mean'])*100:.3f} t/ha por 100 mm, negativa en todas las particiones aleatorias. No demuestra que aumentar agua reduzca rendimiento: geografía y manejo pueden confundir la relación.

La cuadrática empeora el RMSE frente a la recta; no se respalda un óptimo de precipitación. Los resúmenes compactos quedan cerca del modelo mensual bajo CV aleatoria, pero se comportan de otra manera al transferir a zonas nuevas. Los meses máximo y mínimo son constantes (junio y abril en las 197 parcelas), así que la sensibilidad one-hot no agrega información.

Agregar rachas al resumen cambia RMSE aleatorio de {rm.loc['E4_SUMMARY_RIDGE','RMSE_mean']:.4f} a {rm.loc['E5_DYNAMICS_RIDGE','RMSE_mean']:.4f}; no hay mejora aleatoria, aunque sí una mejora espacial respecto del resumen, que por sí solo extrapola mal. Añadir anomalías cambia a {rm.loc['E6_ABSOLUTE_ANOMALIES_RIDGE','RMSE_mean']:.4f}: mejora pequeña frente al resumen, sin superar al modelo mensual y con deterioro municipal. Pre-ciclo cambia a {rm.loc['F_PRE_CYCLE_RIDGE','RMSE_mean']:.4f}; el incremento pequeño no es consistente bajo perfiles y municipios. El combinado tampoco supera al mensual aleatorio: {rm.loc['E7_NESTED_COMBINED','RMSE_mean']:.4f}.

La elección depende de la tarea de generalización. El candidato aleatorio al retener grupos:
```
{grouped_best[['protocol','RMSE_mean','R2_mean','bias_pred_minus_y_mean']].round(4).to_string(index=False)}
```
La caída espacial y el sesgo positivo en rendimientos bajos limitan su uso fuera de la mezcla regional observada. Las dinámicas compactas son una sensibilidad espacial interesante, no una superioridad universal confirmada.
'''
    report=f'''# Rainfall Yield Modeling — reporte técnico v1

## Resultado

Mejor experimento aleatorio exploratorio: **{best.experiment}**, RMSE medio {best.RMSE_mean:.4f} t/ha, MAE {best.MAE_mean:.4f}, R² {best.R2_mean:.4f}. Baseline: RMSE {base.RMSE_mean:.4f} t/ha. Reducción relativa de RMSE: {best.relative_RMSE_improvement:.1%}; gana {win:.1%} de folds. Decisión: {decision['candidate_status']}; candidato: {decision['candidate']}.

## Auditoría y unidad estadística

Se reutiliza la tabla original: {audit['rows']} filas, 197 parcelas, 48 meses, 46 columnas; ninguna fuente se reconstruye. Error máximo independiente {audit['max_manual_error_mm']:.3g} mm, unidades verificadas en tags, NoData excluido con renormalización; cobertura íntegra. {audit['unique_series_exact']} series exactas, {audit['one_pixel_parcels']} parcelas de un solo píxel. Ponderación en área de grilla EPSG:4326, no m² geodésicos exactos. Limitación del indicador original de cobertura respecto del recorte sin efecto en estas parcelas totalmente cubiertas.

La unidad supervisada son 138 parcelas ENTRENAMIENTO; 59 PREDICCION nunca aportan rendimiento. Matriz de características sin Y, compatible por ID_POLIGONO con Familia 1. No temperatura, satélites, suelo, topografía ni sequía externa como predictores. Modelo retrospectivo al final de octubre 2025: no es pronóstico anticipado.

## Diseño reproducible

E0 media del train; E1 total lineal; E2 total cuadrático; E3 siete meses OLS/Ridge; E4 cinco resúmenes no exactamente redundantes y sensibilidad a meses extremos one-hot; E5 E4 más tres descriptores de dinámica; E6 anomalías compactas, mensuales y E4+anomalías; E7 elección interna entre E4, E4+dinámica, E4+anomalías y ambas; F pre-ciclo separado. Grid Ridge [0.1,1,10,100,1000]. No se entrenan árboles sin evidencia adicional que justifique otra etapa.

CV aleatoria: exactamente los 50 folds congelados de Familia 1, 5 folds × 10 repeticiones. Mide nuevas parcelas de la mezcla regional observada, donde perfiles climáticos pueden compartirse. CV climate_profile: enlace completo con diferencia máxima mensual ≤0.01 mm hasta octubre 2025 (46 meses disponibles); retiene perfiles completos. CV municipality: Estado::Municipio; CV spatial: cinco clusters KMeans de centroides métricos, como Fase C. Estos protocolos miden transferencia a perfiles o zonas retenidas, no son réplicas de la misma tarea. Todas las comparaciones de experimentos comparten folds dentro de cada protocolo.

Imputación, escala, regularización y elección de familias E7 ajustadas dentro de cada inner-train, con 4 KFold aleatorios o GroupKFold que conserva los grupos del protocolo externo. Las fechas históricas se restringen a 2022–2024 y las variables actuales a octubre 2025; noviembre/diciembre no entran en features. Los perfiles de agrupación usan clima sin Y solo para diseñar particiones.

Las métricas principales son la media de métricas OOF de cada repetición completa. RMSE_fold_sd y RMSE_repeat_sd documentan variación. Las gráficas de errores/regiones usan OOF promediado por parcela y son diagnósticas; el ensamble promedio puede mejorar artificialmente frente a una predicción por fold y no se presenta como métrica principal.

## Comparación por protocolo

```
{comparison[['protocol','experiment','RMSE_mean','MAE_mean','R2_mean','bias_pred_minus_y','RMSE_fold_sd','delta_RMSE']].round(4).to_string(index=False) if 'bias_pred_minus_y' in comparison else comparison.round(4).to_string(index=False)}
```

## Interpretación y estabilidad

{explanatory}

Pendiente lineal total en t/ha por mm y dispersión entre folds:
```
{linear.round(6).to_string()}
```
Coeficientes Ridge mensuales en t/ha por mm (sin interpretación causal):
```
{monthly.round(6).to_string()}
```
04_coefficients.csv registra coeficientes de cada fold, escala original y condición/rango del diseño; 23_coefficient_stability.csv muestra sensibilidad de signos. La cuadrática y su punto estacionario por fold se guardan en 26_quadratic_stability.csv; no se declara un óptimo agronómico aunque el vértice esté dentro del rango. Las contribuciones pareadas de resúmenes, rachas, anomalías y pre-ciclo están en 07_family_contribution.csv: mejoras pequeñas o inestables no establecen superioridad. E7 elige familias sin mirar Y externo (24_inner_selected_families.csv).

Dentro de perfiles prácticamente iguales persiste un RMSE descriptivo optimista de {eda['within_profile_descriptive_RMSE']:.4f} t/ha al asignar la media de su propio grupo; esto evidencia variación que la lluvia gruesa no resuelve, sin ser estimación validada del error irreducible. Los sesgos en rendimientos bajos/altos y regiones aparecen en tablas 21–22 y figuras 11–12; positivo significa sobreestimación.

## Comparación e integración

25_existing_model_comparison.csv recalcula métricas de arquitecturas integrales existentes SOLO después de verificar correspondencia ID/repeat/fold/Y. Es contexto de familias; no atribuye diferencias únicamente a lluvia porque también cambia el algoritmo y el conjunto de predictores. No se modifican Champion ni sus resultados. Las features se reutilizan mediante family_1.rainfall_features.merge_rainfall; el bloque se versiona y no se añade automáticamente a family1_features_all.

## Incertidumbre y próximos datos

{warnings}

Recabar ciclos etiquetados adicionales y parcelas de zonas independientes antes de confirmar el candidato. Fechas reales de siembra/cosecha, manejo, variedades, riego y suelo podrán ayudar a explicar variabilidad intrapíxel en módulos integrales posteriores. SPI, lluvia diaria, eventos extremos, sequía externa e interacciones quedan previstos para validación futura; no forman parte de esta versión. La referencia de tres años no es una normal y una anomalía negativa no diagnostica sequía.

## Productos

Diccionario con fórmulas, unidades, periodos y políticas de faltantes; características para las 197 parcelas; configuraciones, splits externos/internos, modelos por fold, predicciones OOF, tablas de métricas y contribuciones, EDA, auditoría y hashes. Cada run rechaza sobrescritura. Modelos por fold permiten reproducir las predicciones; no se refita ni publica un modelo final sin superar el criterio de candidato.

'''
    report+='\n'.join(f'![{file.stem}](../figures/{file.name})\n' for file in sorted((out/'figures').glob('*.png')) if int(file.name[:2])>=8)
    (out/'report/technical_report.md').write_text(report,encoding='utf-8')
    return decision
