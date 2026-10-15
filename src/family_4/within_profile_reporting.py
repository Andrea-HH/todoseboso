"""Post-fit figures and a self-contained exploratory F4-E report."""
import json
import numpy as np
import pandas as pd
from . import within_profile_complementarity as e

def table(frame):
    z=frame.reset_index()
    def cell(value):
        if isinstance(value,(float,np.floating)):return f'{value:.4f}'
        return str(value).replace('|','/')
    header='| '+' | '.join(map(str,z.columns))+' |'
    lines=[header,'| '+' | '.join(['---']*len(z.columns))+' |']
    lines += ['| '+' | '.join(cell(v) for v in row)+' |' for row in z.itertuples(index=False,name=None)]
    return '\n'.join(lines)

def build():
    out=e.OUT
    m=pd.read_csv(out/'tables/metrics_summary.csv')
    pair=pd.read_csv(out/'tables/pair_metrics_summary.csv')
    partial=pd.read_csv(out/'audit/partial_within_ndvi.csv')
    decomp=pd.read_csv(out/'audit/within_between_decomposition.csv')
    quality=pd.read_csv(out/'audit/temporal_quality_by_parcel.csv')
    global_rmse=m[m.stratum.eq('all')].pivot(index='experiment',columns='protocol',values='RMSE')
    global_mae=m[m.stratum.eq('all')].pivot(index='experiment',columns='protocol',values='MAE')
    intraprofile=pair[pair.scope.eq('all')].pivot(index='experiment',columns='protocol',values='equal_profile_RMSE')
    without=pair[pair.scope.eq('without_Chignahuapan')].pivot(index='experiment',columns='protocol',values='equal_profile_RMSE')
    primary_partial=partial[partial.scope.eq('all')].set_index('feature')[['n','n_profiles','partial_within_correlation']]
    primary_partial.index=[e.LABELS[c] for c in primary_partial.index]
    plots(m,pair,decomp)
    audit_summary=quality.groupby('index').agg(n_parcels=(e.ID,'size'),median_valid_dates=('n_valid_dates','median'),min_valid_dates=('n_valid_dates','min'),median_valid_months=('n_valid_months','median'),median_gap_days=('median_gap_days','median'),max_gap_days=('max_gap_days','max'),n_insufficient=('insufficient','sum'),negative_observations=('n_negative','sum'))
    decisions=[]
    for exp in e.SPECS:
        dr=global_rmse.loc[exp]-global_rmse.loc['F4-E1'];dm=global_mae.loc[exp]-global_mae.loc['F4-E1']
        local=intraprofile.loc[exp]-intraprofile.loc['F4-E1'];no_chig=without.loc[exp]-without.loc['F4-E1']
        decisions.append(dict(experiment=exp,random_rmse_gain=-dr['random'],worst_grouped_rmse_harm=dr.drop('random').max(),worst_mae_harm=dm.max(),random_equal_profile_pair_gain=-local['random'],random_no_chig_pair_gain=-no_chig['random'],all_metric_margins=bool(dr['random']<0 and dr.drop('random').max()<=.01 and dm.max()<=.01)))
    dec=pd.DataFrame(decisions).set_index('experiment');dec.to_csv(out/'tables/decision_scopes.csv')
    report=f'''# F4-E — Complementariedad intraperfil de vegetación, dinámica temporal y relieve

Esta extensión evalúa únicamente tres cambios aditivos frente a lluvia + NDVI mayo: inicio del mayor ascenso LAI (E2), relieve local medio (E3) y sustitución de NDVI mayo por LAI q10 (E4). No hay una nueva etapa residual ni nuevas búsquedas de variables. Los resultados siguen siendo exploratorios: las candidatas proceden del screening retrospectivo de 1,473 variables sobre las mismas 138 etiquetas.

## Antecedentes, diseño y controles

Se verificó el manifiesto anterior de Familia 4 antes de entrenar. Se recuperó `F4-S1` —el nombre real de la referencia aditiva— como F4-E1 y `J0_RAIN` como F4-E0. Las 1,794 predicciones de cada control se reutilizan literalmente. El modelo S1 archivado se reprodujo en los 65 folds sobre los mismos IDs, con tolerancia absoluta 1e-10. Los modelos/transformaciones de E0/E1 permanecen en sus rutas originales y son referencias inmutables; se guardan 195 modelos nuevos de E2/E3/E4 y 8,970 predicciones OOF totales incluyendo los controles.

La matriz tiene cinco modelos, 138 TRAIN y 59 PRED sin etiquetas usadas, 53 perfiles climáticos totales y 43 perfiles con etiquetas. Se conservan 50 folds aleatorios —cinco por diez repeticiones— y cinco por perfil, municipio y espacio; también sus particiones internas exactas. En protocolo por perfil, las parcelas de un perfil permanecen retenidas juntas.

Elastic Net y `ConditionalFeatures` son exactamente los de F4-S1, con el mismo grid de cuatro alpha y tres l1_ratio, max_iter=200000, imputación mediana, centrado/escala y eliminación de constantes aprendidos dentro de cada entrenamiento. Los nuevos modelos usan exclusivamente columnas predictoras declaradas. No se utilizan medias de Y por perfil, ID, estado, municipio, coordenadas, cuartiles observados ni diagnósticos de soporte como entradas. E2 y E3 añaden una sola columna; E4 sustituye NDVI por LAI q10. La alternativa LAI y el relieve medio se congelaron después de la auditoría y antes de inspeccionar nuevas métricas predictivas.

El relieve medio se eligió por ser un resumen representativo ponderado de cobertura, evitando seleccionar un mínimo o extremo por su correlación. Pendiente q10 y orientación seno/coseno son diagnósticos secundarios; EVI/FAPAR q10 y SAVI ascenso no se entrenan como sensibilidades para buscar ganadores.

## Definiciones verificadas y reservas

- NDVI/EVI mayo son medias de los promedios parcelarios válidos de mayo de 2025; LAI, NDVI y FAPAR q10 son percentiles **temporales** de promedios observados entre abril y octubre, no percentiles espaciales de píxeles.
- LAI inicio de ascenso se define mediante el mínimo acumulado de la trayectoria: se localiza el punto posterior con la mayor diferencia frente a ese mínimo y se toma la primera fecha del mínimo anterior. Se expresa en días desde el 1 de abril. Duplicados de fecha se promedian, observaciones faltantes se omiten y no se interpola ni suaviza. No es una fecha validada de emergencia, siembra o fase fenológica. La ventana completa llega hasta el 31 de octubre, por lo que no constituye un pronóstico temprano de mayo.
- La fuente contiene LAI negativos; las unidades y transformación física del índice entregado no están establecidas. E4 evalúa el índice numérico existente, sin corregirlo ni afirmar área foliar física. También el inicio de ascenso se interpreta como forma de esa serie suministrada.
- Relieve es el máximo menos mínimo de elevación en 3×3 celdas de DEM CEM de 120 m, luego promediado dentro de cada parcela con pesos de cobertura. Sus diferencias son metros y su soporte vecinal es unos 360 m: no mide microrelieve fino ni drenaje observado.
- La orientación se calculó como atan2(-gx,gy) a partir del gradiente raster y se conserva como medias zonales de seno y coseno. No se modelan grados linealmente ni se asume una convención cardinal no verificada. Se conserva el módulo de ese vector medio y se marca pendiente q10<2° como sensibilidad descriptiva de terrenos casi planos; no es una certificación de que toda la parcela sea plana.
- Se conservan los valores válidos suministrados y su máscara original, sin inventar máscaras de nubes ni eliminar parcelas. Cloud_raw es metadato del proveedor, no una máscara local verificada. Fechas de observación no certifican disponibilidad operativa o versión de procesamiento.

Soporte temporal de las 197 parcelas:

{table(audit_summary)}

La auditoría incluye por parcela/índice meses válidos, faltantes, número de fechas únicas, concentración mensual, gaps, nubes y trayectorias insuficientes (<4 fechas o <4 meses, umbral descriptivo). La omisión de cada mes documenta la sensibilidad del q10 y del inicio de ascenso; estos cálculos son auditorías y no reemplazan las matrices existentes. No se interpretan muchas observaciones de una parcela como escenas independientes.

## Redundancia y descomposición descriptiva

Se calculan Pearson y Spearman globales, intraperfil y entre medias de perfiles. Las asociaciones intraperfil excluyen grupos singleton; los tamaños efectivos están en cada tabla. Se reportan asociaciones por estado/municipio, sin Chignahuapan y al excluir cada perfil por turno. Las medias de perfil y su relación con Y solo se utilizan aquí para describir la muestra, nunca como transformación predictiva.

Para la correlación parcial intraperfil se residualizan tanto X como Y contra NDVI mayo centrado dentro del perfil. La lluvia mensual es idéntica dentro de cada perfil y su componente intraperfil es cero: no añade otra dimensión a ese ajuste dentro de grupos. Los residuos calculados con todas las etiquetas son exclusivamente descriptivos y no se usan para entrenar ni seleccionar nuevos candidatos.

{table(primary_partial)}

Una correlación parcial no equivale a complementariedad validada. Se examina su sensibilidad regional y a la exclusión de perfiles. La extensión tampoco prueba que los contrastes se mantengan en parcelas con NDVI casi idéntico: controla NDVI como covariable continua, sin crear un experimento adicional de emparejamiento por NDVI.

## Predicción y transferencia

RMSE t/ha, calculado con todas las predicciones de cada repetición y después promediado:

{table(global_rmse)}

MAE t/ha:

{table(global_mae)}

Las tablas contienen también R², sesgo, diferencias pareadas frente a E1, municipio/estado, Chignahuapan/resto y los cuatro cuartiles previamente definidos. Los resultados no promedian primero predicciones ni RMSE de folds.

La sensibilidad a soporte temporal define soporte bajo mediante el cuartil inferior de número de fechas válidas en entrenamiento, por índice. Se agregan errores cuadrados y absolutos individuales antes de calcular métricas por repetición. No se modifican folds, características ni filtros a partir de esos diagnósticos.

## Diferencias de rendimiento dentro de perfiles

Las parejas comparten perfil y modelo externo; se ordenan por ID ascendente para fijar una orientación reproducible. El error es diferencia observada menos diferencia predicha. El sesgo de parejas depende de esa orientación administrativa, sin interpretación agronómica. Las tablas incluyen diferencias observadas/predichas, correlación, RMSE/MAE, dispersión Y/predicción/incremento, soporte y ganancias/deterioros por perfil. Ninguna pareja de folds externos distintos se usa para atribuir diferenciación a variables.

Con igual peso por perfil se promedian los errores cuadrados individuales dentro de cada perfil y se toma la raíz del promedio de esos MSE. No se promedian RMSE de grupos. Las repeticiones se resumen posteriormente. También se conserva la perspectiva ponderada implícitamente por número de parejas.

RMSE de diferencias con igual peso por perfil:

{table(intraprofile)}

Igual peso por perfil excluyendo parejas con Chignahuapan:

{table(without)}

El informe de soporte distingue parcelas, perfiles y parejas por repetición. Las parejas comparten parcelas y no son muestras independientes. Excluir Chignahuapan en evaluación no equivale a reentrenar los modelos sin ese municipio. Dispersión mayor no se considera mejora sin reducción del error.

## Decisión sobre ámbitos de utilidad

Ganancias positivas favorecen el candidato; los deterioros se comparan con el margen descriptivo previo de 0.01 t/ha:

{table(dec)}

Estos márgenes no son pruebas de significación. Los resultados requieren interpretación conjunta de diferenciación local y transferencia, sin declarar superioridad universal por ganar una sola métrica. Las conclusiones específicas y el conjunto mínimo recomendado se documentan en la síntesis de decisiones que acompaña este reporte.

## Integridad, reproducibilidad y limitaciones

La configuración y los hashes de las fuentes están congelados antes del ajuste. Los controles mantienen sus especificaciones originales. Se guardan selección interna, modelos, escalas, coeficientes y las listas de IDs de entrenamiento/validación. No se sobrescriben Familias 1–3, E–M, Familia 4 original ni Champion. La integridad de los artefactos anteriores se verifica nuevamente al finalizar.

La reutilización de etiquetas/folds tras el screening conserva sesgo de descubrimiento, incluso con validación interna correcta. Los perfiles y estados se solapan con la estructura geográfica; el significado físico de LAI y la fase fenológica son reservas materiales. Se necesitan nuevos rendimientos, campañas o geografías para validación independiente. No se recomienda una expansión de combinaciones sobre esta misma muestra.

Reproducción: `python scripts/338_family4_within_profile_complementarity.py`; una versión completada es inmutable. Pruebas: `python -m pytest tests/test_family4_within_profile_complementarity.py -q`. Artefactos: `outputs/modeling/family_4/conditional_yield_response/extensions/within_profile_complementarity/v1`.
'''
    image_names=['01_redundancy.png','02_variance_decomposition.png','03_ndvi_dynamics_relief.png','04_RMSE_protocol.png','05_MAE_protocol.png','06_intraprofile.png','07_observed_predicted_pairs.png','08_profile_gains.png','09_Chignahuapan.png','10_coefficients_support.png']
    local_images='\n\n'.join(f'![{name}](../figures/{name})' for name in image_names)
    docs_images='\n\n'.join(f'![{name}](../{out.relative_to(e.ROOT).as_posix()}/figures/{name})' for name in image_names)
    (out/'report/technical_report.md').write_text(report+'\n\n## Figuras\n\n'+local_images,encoding='utf-8')
    (e.ROOT/'documentation/family4_e_within_profile_complementarity.md').write_text(report+'\n\n## Figuras\n\n'+docs_images,encoding='utf-8')
    print(global_rmse.round(5).to_string(),flush=True)
    print('INTRAPROFILE',intraprofile.round(5).to_string(),flush=True)

def plots(metrics,pair,decomp):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=e.OUT;figs=out/'figures'
    fig,axes=plt.subplots(1,2,figsize=(17,8))
    for ax,level in zip(axes,['global','within']):
        z=pd.read_csv(out/'audit'/f'{level}_pearson.csv',index_col=0).loc[e.CANDIDATES,e.CANDIDATES]
        im=ax.imshow(z,vmin=-1,vmax=1,cmap='coolwarm');labels=[e.LABELS[c] for c in z.columns]
        ax.set_xticks(range(len(labels)),labels,rotation=90);ax.set_yticks(range(len(labels)),labels);ax.set_title('Correlación '+level)
    fig.subplots_adjust(bottom=.31,wspace=.6,right=.88)
    cax=fig.add_axes([.93,.32,.015,.54]);fig.colorbar(im,cax=cax)
    fig.savefig(figs/'01_redundancy.png',dpi=170);plt.close(fig)
    z=decomp[decomp.feature.isin(e.CANDIDATES)].set_index('feature')[['between_fraction','within_fraction']];z.index=[e.LABELS[c] for c in z.index]
    ax=z.plot.barh(stacked=True,figsize=(11,7));ax.set_xlabel('Fracción de variación');ax.figure.tight_layout();ax.figure.savefig(figs/'02_variance_decomposition.png',dpi=170);plt.close(ax.figure)
    _,t=e.load();fig,axes=plt.subplots(1,2,figsize=(12,5))
    for ax,c in zip(axes,[e.RISE,e.RELIEF]):
        for state,g in t.groupby('Estado'):ax.scatter(g[e.f.NDVI],g[c],label=state,alpha=.7,s=25)
        ax.set(xlabel='NDVI mayo',ylabel=e.LABELS[c]);ax.legend(fontsize=8)
    fig.tight_layout();fig.savefig(figs/'03_ndvi_dynamics_relief.png',dpi=170);plt.close(fig)
    for i,metric in enumerate(['RMSE','MAE'],4):
        z=metrics[metrics.stratum.eq('all')].pivot(index='experiment',columns='protocol',values=metric)
        ax=z.plot.barh(figsize=(11,5));ax.set_xlabel(metric+' t/ha');ax.figure.tight_layout();ax.figure.savefig(figs/f'0{i}_{metric}_protocol.png',dpi=170);plt.close(ax.figure)
    z=pair[pair.scope.eq('all')].pivot(index='experiment',columns='protocol',values='equal_profile_RMSE')
    ax=z.plot.barh(figsize=(11,5));ax.set_xlabel('RMSE diferencias, igual peso por perfil');ax.figure.tight_layout();ax.figure.savefig(figs/'06_intraprofile.png',dpi=170);plt.close(ax.figure)
    pp=pd.read_parquet(out/'tables/same_model_pairs.parquet');fig,axes=plt.subplots(2,2,figsize=(11,9))
    for ax,exp in zip(axes.ravel(),['F4-E1','F4-E2','F4-E3','F4-E4']):
        z=pp[(pp.protocol=='random')&(pp['repeat']==1)&(pp.experiment==exp)];ax.scatter(z.observed_difference,z.predicted_difference,s=12,alpha=.4)
        lim=max(abs(z.observed_difference).max(),abs(z.predicted_difference).max());ax.plot([-lim,lim],[-lim,lim],color='black',linewidth=1);ax.set(title=exp,xlabel='Diferencia observada t/ha',ylabel='Diferencia predicha t/ha')
    fig.tight_layout();fig.savefig(figs/'07_observed_predicted_pairs.png',dpi=170);plt.close(fig)
    prof=pd.read_csv(out/'tables/paired_profile_metrics.csv');z=prof[(prof.protocol=='random')&(prof.scope=='all')&prof.experiment.isin(e.SPECS)].groupby(['profile','experiment']).delta_RMSE.mean().unstack()
    ax=z.plot.barh(figsize=(12,7));ax.axvline(0,color='black',lw=1);ax.set_xlabel('Cambio RMSE de diferencias vs E1; negativo mejora');ax.figure.tight_layout();ax.figure.savefig(figs/'08_profile_gains.png',dpi=170);plt.close(ax.figure)
    z=metrics[(metrics.protocol=='random')&metrics.stratum.isin(['Chignahuapan','without_Chignahuapan'])].pivot(index='experiment',columns='stratum',values='RMSE')
    ax=z.plot.bar(figsize=(9,5),rot=0);ax.set_ylabel('RMSE t/ha');ax.figure.tight_layout();ax.figure.savefig(figs/'09_Chignahuapan.png',dpi=170);plt.close(ax.figure)
    co=pd.read_csv(out/'tables/coefficients.csv');z=co[~co.feature.isin(e.RAIN)].copy();fig,axes=plt.subplots(1,2,figsize=(13,5))
    labels=[];data=[]
    for (exp,c),g in z.groupby(['experiment','feature']):labels.append(exp+' '+e.LABELS[c]);data.append(g.coefficient)
    axes[0].boxplot(data,tick_labels=labels);axes[0].tick_params(axis='x',rotation=30);axes[0].set_ylabel('Coeficiente en escala del entrenamiento')
    sup=pd.read_csv(out/'tables/support_summary.csv');z=sup[(sup.protocol=='random')&(sup['index']=='lai')].pivot(index='experiment',columns='support',values='RMSE');z.plot.bar(ax=axes[1],rot=0);axes[1].set_ylabel('RMSE según soporte LAI')
    fig.tight_layout();fig.savefig(figs/'10_coefficients_support.png',dpi=170);plt.close(fig)
