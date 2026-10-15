"""Stage D tables, figures and five documentary deliverables, from archived evidence."""
import json
import numpy as np
import pandas as pd
from . import stage_d_evidence as d
from . import stage_c_models as c
from .stage_c_final_report import md

def read(name):return pd.read_csv(d.OUT/'tables'/name)

def plot_all(t,p,metrics):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=d.OUT/'figures'
    names={'random':'Aleatoria','climate_profile':'Por perfil','municipality':'Municipal','spatial':'Espacial'}
    def finish(fig,name,title):
        fig.suptitle(title,fontsize=11);fig.tight_layout(rect=(0,0,1,.94));fig.savefig(out/name,dpi=170,bbox_inches='tight');plt.close(fig)
    available=metrics.pivot(index='experiment',columns='protocol',values='RMSE').notna().astype(int)
    fig,ax=plt.subplots(figsize=(9,6));ax.imshow(available,cmap='Blues',vmin=0,vmax=1);ax.set_xticks(range(len(available.columns)),[names[x] for x in available.columns]);ax.set_yticks(range(len(available)),available.index)
    for i in range(len(available)):
        for j in range(len(available.columns)):ax.text(j,i,'Disponible' if available.iloc[i,j] else 'Sin OOF',ha='center',va='center',fontsize=8)
    finish(fig,'01_availability.png','Disponibilidad comparable: 138 etiquetas; no equivalencia Champion geográfica')
    fig,axes=plt.subplots(1,2,figsize=(15,6))
    for ax,protocols,title in [(axes[0],['random'],'Aleatoria'),(axes[1],['climate_profile','municipality','spatial'],'Geográfica')]:
        z=metrics[metrics.protocol.isin(protocols)&~metrics.experiment.isin(['B2','B3'])].pivot(index='experiment',columns='protocol',values='RMSE');z=z.rename(columns=names);z.plot.barh(ax=ax);ax.set_xlabel('RMSE (t/ha), media OOF completa por repetición');ax.set_title(title)
        if len(protocols)==1:ax.get_legend().remove()
        else:ax.legend(bbox_to_anchor=(1.02,1),loc='upper left',fontsize=8)
    finish(fig,'02_compatible_errors.png','138 parcelas: 10 repeticiones aleatorias; 1 por cada protocolo geográfico')
    fig,ax=plt.subplots(figsize=(9,7))
    for block,g in t.groupby('spatial_block'):ax.scatter(g.longitude,g.latitude,s=25,label=f'Bloque {int(block)}: n={len(g)}',alpha=.8)
    ax.set(xlabel='Longitud (grados)',ylabel='Latitud (grados)');ax.legend(bbox_to_anchor=(1.02,1),loc='upper left')
    finish(fig,'03_geographic_blocks.png','Asignaciones espaciales congeladas, 138 etiquetas; coordenadas descriptivas')
    fig,axes=plt.subplots(1,3,figsize=(14,5))
    for ax,field,label in zip(axes,[c.COMPACT[0],c.DTR,c.NDVI],['Lluvia abril–octubre (mm)','SD mensual DTR abril–octubre (°C)','NDVI mayo (sin unidad)']):
        arrays=[g[field].dropna().to_numpy() for _,g in t.groupby('spatial_block')];ax.boxplot(arrays,tick_labels=[f'{int(b)}\nn={len(g)}' for b,g in t.groupby('spatial_block')],showfliers=True);ax.set(xlabel='Bloque espacial',ylabel=label)
    finish(fig,'04_block_covariates.png','Distribuciones observadas: 138 etiquetas; no prueba causal')
    gain=read('spatial_block_gains.csv');fig,ax=plt.subplots(figsize=(10,5));gain[gain.candidate.isin(['C-T1','C-T3'])].pivot(index='block',columns='candidate',values='sse_gain').plot.bar(ax=ax,rot=0);ax.axhline(0,color='black',lw=.8);ax.set(xlabel='Bloque espacial',ylabel='Ganancia SSE frente a F4-S1 ((t/ha)²)');ax.legend()
    finish(fig,'05_block_gains.png','Ganancias sumables, 138 etiquetas; positivo favorece candidato')
    omit=read('spatial_block_omission.csv');fig,ax=plt.subplots(figsize=(10,5));omit.pivot(index='omitted_block',columns='candidate',values='delta_RMSE').plot.bar(ax=ax,rot=0);ax.axhline(0,color='black',lw=.8);ax.set(xlabel='Bloque omitido solo del cálculo OOF',ylabel='Δ RMSE candidato − F4-S1 (t/ha)');ax.legend(bbox_to_anchor=(1.02,1),loc='upper left')
    counts=t.groupby('spatial_block').size();ax.set_xticklabels([f'{int(b)}\nn={138-int(counts.loc[b])}' for b in counts.index])
    finish(fig,'06_block_omission.png','Sensibilidad de agregación OOF; mismas predicciones, ningún reentrenamiento')
    loss=pd.read_parquet(d.OUT/'tables/paired_losses.parquet');fig,axes=plt.subplots(1,2,figsize=(14,5))
    for ax,protocol in zip(axes,['random','spatial']):
        for candidate,baseline in [('FIXED_50_50','CHAMPION'),('C-T3',d.BASE),('C-T1',d.BASE)]:
            g=loss[(loss.candidate==candidate)&(loss.baseline==baseline)&(loss.protocol==protocol)].groupby(d.ID).SE_gain.mean()
            if len(g):ax.plot(np.sort(g),(np.arange(len(g))+1)/len(g),label=f'{candidate}: n={len(g)}')
        ax.axvline(0,color='black',lw=.8);ax.set(xlabel='Ganancia de pérdida cuadrática ((t/ha)²)',ylabel='Fracción acumulada de parcelas',title=names[protocol]);ax.legend(fontsize=8)
    finish(fig,'07_paired_losses.png','ECDF por parcela; pérdidas promediadas entre repeticiones, no 1,380 individuos')
    fig,axes=plt.subplots(1,2,figsize=(14,5))
    for ax,protocol in zip(axes,['random','spatial']):
        for candidate,baseline in [('FIXED_50_50','CHAMPION'),('C-T3',d.BASE),('C-T1',d.BASE)]:
            g=loss[(loss.candidate==candidate)&(loss.baseline==baseline)&(loss.protocol==protocol)].groupby(d.ID).SE_gain.mean().sort_values(ascending=False)
            if len(g):ax.plot(np.arange(1,len(g)+1),g.cumsum(),label=candidate)
        ax.axhline(0,color='black',lw=.8);ax.set(xlabel='Parcelas ordenadas por ganancia, n=138',ylabel='Ganancia acumulada de SSE ((t/ha)²)',title=names[protocol]);ax.legend(fontsize=8)
    finish(fig,'08_gain_concentration.png','Orden descriptivo por ganancia; última posición conserva todas las parcelas')
    fig,axes=plt.subplots(1,2,figsize=(13,5));context=t.set_index(d.ID)
    for ax,profile in zip(axes,[4,24]):
        ids=t.loc[(t.climate_profile==profile)&t.Municipio.eq('Chignahuapan'),d.ID];ax.scatter(context.loc[ids,c.NDVI],context.loc[ids,d.TARGET],s=25,label='Y observado')
        for exp in [d.BASE,'C-T3','F4-E2']:
            q=p[(p.protocol=='random')&(p.experiment==exp)&p[d.ID].isin(ids)].groupby(d.ID).y_pred.mean();ax.scatter(context.loc[q.index,c.NDVI],q,s=14,alpha=.65,label=exp)
        ax.set(xlabel='NDVI mayo (sin unidad)',ylabel='Rendimiento (t/ha)',title=f'Perfil {profile}, Chignahuapan: n={len(ids)}');ax.legend(fontsize=7)
    finish(fig,'09_dominant_profiles.png','Dispersión descriptiva: media de predicciones aleatorias; no métrica primaria')
    support=read('spatial_support.csv');s=support.set_index(d.ID);fig,ax=plt.subplots(figsize=(10,6))
    outside=s[[f+'_support' for f in [c.COMPACT[0],c.DTR,c.NDVI]]].eq('outside').any(axis=1)
    for flag,label in [(False,'Dentro de rangos marginales'),(True,'Fuera de ≥1 rango marginal')]:
        ids=s.index[outside.eq(flag)];g=context.loc[ids];ax.scatter(g.longitude,g.latitude,s=28,label=f'{label}: n={len(g)}')
    ax.set(xlabel='Longitud (grados)',ylabel='Latitud (grados)');ax.legend(bbox_to_anchor=(1.02,1),loc='upper left')
    finish(fig,'10_support_map.png','Soporte respecto al entrenamiento de cada fold espacial: lluvia total/DTR/NDVI')
    fig,ax=plt.subplots(figsize=(12,5));ax.axis('off');table=[['S1 similares','Champion / mezcla fija','Sin confirmación externa'],['S2 perfiles nuevos','F4-S1 / C-T3 / H0M','Perfiles ≠ municipios'],['S3 municipios nuevos','C-T3 vs F4-S1; H0M control','Ventaja observada municipal'],['S4 regiones distintas','T1 / T3 vs F4-S1','Sin ganador espacial estable'],['S5 diferencias locales','F4-S1 / E2; H0M control','Heterogeneidad no resuelta']];tab=ax.table(cellText=table,colLabels=['Escenario','Comparación congelada','Límite'],loc='center',cellLoc='left',colWidths=[.23,.39,.38]);tab.auto_set_font_size(False);tab.set_fontsize(9);tab.scale(1,2.3)
    finish(fig,'11_scenario_matrix.png','Decisiones por estimando, sin ranking universal ni pesos retrospectivos')
    fig,ax=plt.subplots(figsize=(13,5));ax.axis('off')
    for j,(name,label) in enumerate([('V1','Parcelas nuevas\nperfiles conocidos'),('V2','Perfiles nuevos\nmunicipios conocidos'),('V3','Municipios nuevos\nprioridad geográfica'),('V4','Regiones distintas\ncontraste bloque 3'),('V5','Nueva campaña\nprioridad temporal')]):
        x=.02+j*.195;ax.text(x,.58,name+'\n'+label,transform=ax.transAxes,va='center',bbox=dict(boxstyle='round',facecolor='#e4eef6'),fontsize=9)
    ax.text(.5,.13,'Congelar protocolo → predecir sin Y nueva → bloquear predicciones → medir Y → evaluar por unidad objetivo',ha='center',transform=ax.transAxes,fontsize=10)
    finish(fig,'12_external_design.png','Diseño prospectivo: tamaños pendientes de precisión, agrupamiento y recursos')

def evidence_matrix():
    data=[
      ('Champion','Referencia histórica','Arquitectura clima→historia→terreno','Mejor referencia histórica aleatoria evaluada; sin OOF geográfica equivalente','S1','Faltan validación externa y reconstrucción geográfica compatible'),
      ('FIXED_50_50','Candidato congelado','Media fija Champion/F4-S1','Mejora aleatoria pequeña; influencia concentrada; extremos no uniformes','S1','Comparación externa frente a Champion; no nuevos pesos'),
      ('F4-S1','Candidato congelado','Lluvia mensual + NDVI mayo','Control climático parcelario parsimonioso; heterogeneidad local persiste','S1/S2/S3/S4/S5','Campañas y municipios independientes'),
      ('C-T3','Candidato congelado','Lluvia compacta + NDVI mayo','Ventaja municipal; mejora espacial concentrada y costo aleatorio','S3 principal; S2 secundario','Municipios nuevos y costo aleatorio/local'),
      ('C-H0M','Control metodológico','Gaussian Ridge sin intercepto aleatorio','Separa cambio L2 de efecto jerárquico','S2/S3/S4/S5','Control externo bajo mismo procedimiento'),
      ('C-T1','Candidato congelado','Lluvia mensual + SD temporal DTR','Hipótesis espacial; depende del bloque 3','S4 experimental','Regiones nuevas con/sin covariables del bloque3'),
      ('F4-E2 / B2','Control metodológico','Añade inicio ascenso LAI a F4-S1','Mejora local pequeña, sin ventaja global uniforme','S5','Fechas reales y prueba local independiente'),
      ('B1/B3','No recomendado bajo la formulación evaluada','Objetivo y selección intraperfil','Costo municipal excesivo; cambio hiperparámetros incluso lambda0','Metodológico','No priorizar más complejidad sobre estas etiquetas'),
      ('C-H1','No recomendado bajo la formulación evaluada','Intercepto aleatorio de perfil','No supera H0M; ratio0 frecuente; intervalos municipales subcubren','Metodológico','Más grupos repetidos si se retoma la hipótesis'),
      ('C-T2/C-T4','Exploratorio sin prioridad','NDVI + DTR mensuales/compactos','No reúne fortalezas de forma general','Comparación conceptual','No abrir nuevas combinaciones retrospectivas'),
      ('J/K/L suelo y terreno','Exploratorio sin prioridad','Adiciones/correcciones y representaciones de bloques','Asociación propia no garantiza incremento estable sobre clima','Descriptivo regional/local','Suelo medido, escala y soporte de categorías'),
      ('M histórico/multisensor','Exploratorio sin prioridad','Índices actuales e historia; raw/PCA','Ganancias cambian por arquitectura/protocolo; no integración automática','Descriptivo y controles','Campañas independientes, calidad y corte temporal'),
      ('Familia2 FPCA/SOF','Exploratorio sin prioridad','Funciones temporales e híbridos','Interpretación temporal sin superar controles de manera suficiente','Interpretativo','No reabrir concurso de parametrizaciones'),
      ('Familia3 factores/interacciones','No recomendado bajo la formulación evaluada','Estructura y condicionamiento climático','Interacciones no justifican expertos/GMM supervisados','Metodológico','Más datos y nueva hipótesis previa si se retoma'),
      ('Screening1473','Exploratorio sin prioridad','Ridge univariado + asociaciones','Descubrimiento retrospectivo; no evaluación imparcial de selección','Generación de hipótesis','Validar candidatos fijados sin volver a seleccionar'),
      ('Suelo50k / SGM50k','Suspendido por datos','Cartografía local solicitada','Suelo inexistente; PDF geológico sin geometría temática fiable','Inventario','Fuente oficial vectorial y auditoría geométrica'),
      ('Geología250k','Exploratorio sin prioridad','Composición parcelaria existente','Contrastes locales repetidos, sin ganancia incremental demostrada','Descriptivo intraperfil','Verificar límites y soporte; no integración en D')]
    z=pd.DataFrame(data,columns=['model_or_hypothesis','decision_state','question_specification','evidence_result','utility_scope','external_evidence_pending']);z['risk']='Exploratorio; reutilización de 138 etiquetas; asociaciones no causales';d.save(z,'final_evidence_matrix.csv');return z

def acquisition():
    rows=[
      ('Rendimiento y superficie cosechada','¿Los casos persistentes están correctamente registrados?','Dentro de perfil','Parcela; campaña y fecha exactas','138Y existentes; documentos primarios pendientes','Bajo-medio, cualitativo','Errores persistentes y extremos','Auditoría ciega a preferencia de modelo','1: necesario para todos los estimandos'),
      ('Siembra/cosecha y variedad','¿NDVI mayo mezcla fases o cultivos?','Dentro de perfil y entre campañas','Fechas diarias; variedad por parcela','No verificadas como campos completos','Bajo-medio, cualitativo','NDVI en fecha fija; dinámica no fenología validada','V1/V5, registro antes de Y','1: identifica comparabilidad temporal'),
      ('Fertilización/manejo/malezas/enfermedades','¿Contrastes locales corresponden a manejo?','Dentro de perfil','Dosis, fechas y eventos por parcela','Pendiente de levantamiento','Medio, cualitativo','Grandes diferencias climáticamente idénticas','V1, varios grupos repetidos','2: variación local efectiva'),
      ('Riego/condiciones hídricas','¿Clima regional omite agua disponible?','Dentro de perfil','Eventos y fuente; parcela/campaña','Pendiente de verificación','Medio, cualitativo','Lluvia de malla común no representa manejo hídrico','V1/V3, observación independiente','2: hipótesis agronómica concreta'),
      ('Textura/profundidad de suelo medidas','¿Suelo real aporta contraste no captado por cartografía?','Dentro de perfil','Muestras georreferenciadas y profundidades registradas','Pendiente; coberturas250k no son mediciones','Medio-alto, cualitativo','Resolución y semántica cartográfica','Submuestra V1 estratificada sin elegir por Y','2: medir antes de ampliar índices'),
      ('Suelo local de mayor resolución','¿El mapa distingue propiedades y límites reales?','Dentro de perfil','Escala documentada, fecha y geometría validada','Fuente50k no presente','Desconocido; requiere cotización','Ausencia fuente edafológica local','Verificación campo y comparación de límites','3: condicionada a disponibilidad'),
      ('Geología oficial vectorial50k','¿Contrastes250k persisten a escala más fina?','Dentro de perfil','Polígonos oficiales, CRS y fecha verificadas','PDF SGM2017 existe; vector no verificado','Desconocido; no estimación monetaria','Límites250k y PDF no clasificable','V1, categorías repetidas y reservas de límite','3: no ganancia predictiva demostrada'),
      ('Rendimientos de nuevas campañas','¿Las señales actuales transfieren en el tiempo?','Entre campañas y dentro de municipios','Campaña completa; varias campañas para inferencia temporal','No disponibles como etiquetas independientes verificadas','Alto por seguimiento, cualitativo','Solo etiquetas2025','V5, sin mezclar con comparación geográfica','1: falta central de validación temporal'),
      ('Calidad/fechas imágenes','¿Disponibilidad satelital afecta señales y comparabilidad?','Dentro de perfil y entre campañas','Fechas de adquisición, nubes, gaps, cultivo y cobertura','Soporte procesado existente; verificación campo pendiente','Bajo-medio, cualitativo','Índices redundantes y ventanas distintas','V1/V5, reglas predefinidas','1: control de medición y corte temporal')]
    z=pd.DataFrame(rows,columns=['source','question','required_variation','resolution','availability','relative_cost','current_limitation','validation_needed','priority']);d.save(z,'data_acquisition_agenda.csv');return z

PROSPECTIVE='''# Etapa D — Protocolo prospectivo de validación independiente

Este documento congela el conjunto de hipótesis y procedimientos de referencia. Las cuotas de reclutamiento, presupuesto y margen económico final siguen pendientes de decisión de FIRA. Ningún candidato se entrenó sobre las 138 etiquetas completas durante D. No se adquirieron nuevas etiquetas.

## Estimandos y poblaciones

R_similar(M)=E[(Y−f_M(X))²] en parcelas nuevas de la misma campaña, municipios representados y condiciones productivas elegibles del universo original. V1 verifica perfiles conocidos mediante los vectores climáticos completos, no solo el nombre municipal. El estimando corresponde a la población de reclutamiento descrita; no a toda la cebada nacional.

R_newmun(M) usa municipios sin ninguna parcela etiquetada de entrenamiento, dentro de la región objetivo que FIRA delimite antes del reclutamiento. Unidad primaria: municipio; objetivo principal municipal con igual peso por municipio, secundario ponderado por parcelas. Clima coincidente no convierte un municipio en conocido.

R_newseason(M) usa una campaña agrícola futura completa, conservando las definiciones mensuales relativas al año de aplicación, fuentes y manejo del cultivo elegible. Una sola campaña mide esa campaña; generalizar entre campañas requiere varias campañas independientes. Reutilizar parcelas puede medir transferencia temporal, pero no independencia parcelaria: se debe reportar y agrupar por parcela además de campaña.

R_newprofile y R_newregion quedan como objetivos secundarios diferenciados: perfil nuevo = vector exacto de clima no observado; región nueva = unidades territoriales separadas elegidas por un marco geográfico previo, no a partir de residuos. Las probabilidades de inclusión y el marco objetivo deben quedar registrados para saber si la estimación es ponderada o corresponde solo a la muestra.

## Grupos de adquisición

| Grupo | Diseño operacional | Independencia y contraste |
|---|---|---|
| V1 | Parcelas adicionales en perfiles conocidos; distribuir esfuerzo entre varios perfiles repetidos, además de los dos grandes de Chignahuapan | IDs/geometrías nuevas; auditar solapamiento y duplicados; comparar nivel y diferencias intraperfil |
| V2 | Perfiles nuevos dentro de municipios representados | Verificar vector climático; no confundir igualdad por malla con parcelas repetidas; aislar perfil del cambio administrativo |
| V3 | Municipios no presentes en las 138 etiquetas; seleccionar municipios y luego parcelas probabilísticamente cuando sea viable | Ninguna etiqueta de esos municipios entra al ajuste; comparar C-T3 con F4-S1, H0M control |
| V4 | Regiones nuevas elegidas por geografía y covariables sin Y; incluir condiciones semejantes y diferentes a bloque3 | Selección territorial previa y separación registrada; comprobar si ganancias T1/T3 se repiten entre regiones |
| V5 | Nueva campaña; combinar municipios representados y nuevos en estratos separados | Predicciones bloqueadas antes de Y; separar contraste temporal de geográfico; panel repetido y parcelas nuevas identificados |

Prioridad si hay recursos limitados: auditoría de Y/superficie y fechas primero; V3 para la hipótesis municipal más prometedora y V5 para el vacío temporal. V1 es prioritario si el objetivo operativo es diferenciación local. V4 debe disponer de varias regiones, no de una única réplica del bloque3. V2 sirve para distinguir transferencia climática de administrativa. Evitar prometer cubrir todos los objetivos con una sola muestra conveniente.

Las 59 PRED existentes pueden constituir un subconjunto sellado de evaluación de la misma campaña solo si sus Y permanecieron totalmente inaccesibles y no se modificó su selección a partir de resultados. No equivalen automáticamente a municipios nuevos ni a una campaña nueva; sus X ya participaron en auditorías descriptivas. Registrar esa limitación y su independencia de etiquetas.

## Candidatos y procedimientos que se preservan

- S1: Champion archivado como referencia; mezcla exactamente 0.5Champion+0.5F4-S1 como candidato; F4-S1 como control sencillo. No buscar pesos ni reconstruir protocolos geográficos del Champion.
- V2/V3/V4: F4-S1, C-T3, C-T1 y C-H0M, usando las mismas especificaciones y reglas internas de C. C-T0 no se considera un modelo distinto de F4-S1.
- Local: F4-E2 como control de dinámica, comparado con F4-S1; no promover B3. H1 y nuevas combinaciones quedan fuera del conjunto confirmatorio prioritario.
- F4-S1 = EN(lluvia mensual7 + NDVI mayo); T1 = EN(lluvia7 + SD mensualDTR); T3 = EN(total7, fracciónabril–junio, HHI mensual + NDVI mayo). Epsilon=1e−6mm. H0M usa las variables de S1, Ridge alpha_solver=n·alpha, intercepto libre y ratio0.
- Imputación mediana, medias/escalas entrenadas solo en entrenamiento; piso NDVI0.05 y tratamiento de constantes original. Mantener α={0.001,0.01,0.1,1}, ρ={0.1,0.5,0.9} EN; H0M α igual. Selección min mediaRMSE de folds internos, según fuentes congeladas; ningún Y externo entra en selección. Para el futuro ajuste final, la regla pendiente de concretar es reutilizar como CV interna las particiones aleatorias originales sobre138, sin adaptar protocolos según resultados externos. Debe aprobarse y sellarse antes de ajustar o ver Y nueva.
- Champion requiere confirmar que su entrenamiento final y fuentes están reproducibles con el procedimiento original. Si no puede producirse un artefacto final fiel sin modificar arquitectura/selección, omitir Champion y mezcla de esa validación, explicarlo y conservar los candidatos simples. No reconstruir retrospectivamente una nueva versión bajo el mismo ID.
- Calendario: NDVI mayo solo es una señal de mayo. Lluvia/DTR abril–octubre y dinámicaE2 requieren toda esa ventana. La evaluación principal es estimación poscampaña, no pronóstico anticipado. Si Y se conoce antes de completar X, mantener Y sellada hasta bloquear predicciones.

## Tamaño de muestra y precisión

No se fija un n óptimo. Antes de recolectar, decidir diferencia mínima útil Δ en pérdida cuadrática (t/ha)² y tolerancia MAE en t/ha con FIRA. El margen histórico0.01t/ha es una referencia de no deterioro exploratoria, no una diferencia clínica/económica validada. Puede traducirse una mejora objetivo δ_RMSE alrededor de referencia r en Δ=r²−(r−δ_RMSE)²; esta traducción no sustituye utilidad operativa.

Para D_i=SE_A−SE_B, positivo favorece B. Si unidades primarias independientes son municipios, construir D̄_g dentro de cada municipio y estimar D̄=G⁻¹ΣD̄_g. Error estándar descriptivo s(D̄_g)/√G; intervalos con grados G−1, cuando la aproximación sea defendible. Ponderaciones de población deben fijarse a partir del muestreo, no de desempeño. Con pocos municipios, presentar cada contraste municipal y reconocer incertidumbre alta; no usar 138 parcelas como tamaño inferencial territorial.

Planificar G para semiamplitud objetivo h explorando G≈(z·s_G/h)², reemplazando después z por t y revisando recursos. Para potencia aproximada puede explorarse ((z_conf+z_power)s_G/Δ)². Ambos son cálculos de sensibilidad, no tamaños garantizados: dependencia espacial entre municipios y pocas unidades pueden invalidar independencia. Incorporar variación de s_G, ICC e imbalance de tamaños y concentraciones; DEFF≈1+(m−1)ICC solo ilustra agrupamiento simple, no resuelve perfiles cruzados con municipios.

Usar un piloto verdaderamente externo o supuestos conservadores para rangos de s_G/ICC. Las pérdidas OOF reutilizadas actuales son un insumo exploratorio para rangos, no una estimación insesgada de varianza externa. Si el piloto se usa para diseñar y congelar procedimientos, separarlo de la muestra confirmatoria final. Para campañas la unidad de generalización es campaña; más parcelas de una sola campaña no reemplazan más campañas. Para diferencias locales, inferencia por perfil y parcelas, nunca por parejas solapadas.

## Bloqueo y evaluación

1. Registrar marco de muestreo, municipios/campañas, reglas de elegibilidad y IDs; deduplicar geometrías y documentar parcelas que reaparecen.
2. Aprobar cuotas, utilidad práctica, estimando principal y regla final de CV/ajuste pendientes. Sellar especificaciones, fuentes, código, modelos futuros y hashes antes de recibir Y nueva.
3. Ajustar candidatos usando exclusivamente138Y actuales en una operación futura separada. Producir predicciones externas, registrar soporte/faltantes y bloquearlas con fecha/hash.
4. Obtener rendimientos con definición uniforme producción/superficie cosechada y documentos verificables. Registrar pérdidas de seguimiento; no sustituir faltantes con valores predichos.
5. Evaluar cada comparación con llave (ID,campaña,modelo) y mismo conjunto de Y. Publicar n completo, n emparejado y razones de datos faltantes. No elegir candidatos por rendimiento externo.

Primaria V3: pérdida cuadrática pareada con igual peso municipal; acompañar RMSE/MAE parcela y municipal, sesgo y porcentaje de municipios con mejora. Primaria V1: MSE por parcela; secundaria diferencias intraperfil con igual peso de perfiles y pares del mismo modelo final. Primaria V5: MSE por campaña y detalle regional. Reportar intervalos adecuados a unidades objetivo, sin tratar campañas/repeticiones/parejas dependientes como independientes.

Decisión propuesta a concretar antes de Y: utilidad si la ganancia supera Δ y su incertidumbre respalda una mejora práctica, sin deterioro MAE mayor al margen acordado; si la incertidumbre cruza umbrales de utilidad o daño, declarar inconcluso. Reportar todos los contrastes predefinidos y designar uno principal por estimando; no seleccionar el menor p. No juntar escenarios mediante pesos retrospectivos.

Municipios con n<2: mantener en métricas parcelarias y municipal con su tamaño explícito; no estimar diferencias intraperfil allí. Si no hay varios perfiles o municipios, declarar no estimable el objetivo correspondiente. Comparaciones incompletas: tabla de disponibilidad y análisis sobre intersección etiquetada, con advertencia de posible selección por faltantes. No imputar Y.

Valores fuera de soporte permanecen en evaluación principal con bandera y análisis secundario predefinido. Faltantes de X: transformaciones congeladas; una fuente completamente ausente se registra como indisponibilidad operacional del modelo, sin diseñar un sustituto. No eliminar casos por residuo; una corrección documental de Y requiere evidencia independiente y bitácora ciega al modelo, reportando métricas original y corregida.

## Intervalos futuros

H1 no se promueve y sus intervalos actuales no se recalibran. Un futuro módulo de incertidumbre requiere rendimientos independientes de calibración, regiones/perfiles representados y otro conjunto de evaluación sellado. Investigar calibración por grupos o particiones territoriales, con supuestos y unidad de intercambio explícitos. Bootstrap ordinario parcelario y conformal estándar no garantizan cobertura bajo cambio de dominio. Si no hay intervalos congelados válidos para un candidato, no inventarlos ni reportar cobertura.
'''

def build(t,p,metrics):
    evidence=evidence_matrix();agenda=acquisition();plot_all(t,p,metrics)
    comp=read('block_composition.csv');dist=read('block_covariate_distributions.csv');smd=read('block3_standardized_differences.csv');gain=read('spatial_block_gains.csv');omit=read('spatial_block_omission.csv');conc=read('gain_concentration.csv');overlap=read('spatial_gain_overlap_summary.csv');variance=read('yield_within_between_decomposition.csv');cases=read('persistent_case_audit.csv');local=read('equal_profile_pair_metrics_summary.csv');prof=read('repeated_profile_description.csv')
    interval=pd.read_csv(c.OUT/'tables/interval_calibration_summary.csv');d.save(interval,'archived_interval_calibration.csv')
    reg=pd.read_csv(c.OUT/'tables/hierarchy_registry.csv');h=reg[reg.experiment.eq('C-H1')]
    source_pairs=pd.read_csv(c.b.a.OUT/'tables/dominant_x_only_pair_inventory.csv');geology=pd.read_csv(c.b.a.OUT/'tables/dominant_geology_category_support.csv')
    total3=comp.loc[comp.block.eq(3),'n'].iloc[0]
    biasparts=read('block_bias_variance_decomposition.csv')
    omission=read('parcel_omission_sensitivity.csv')
    narr_block='''El bloque 3 contiene 35 etiquetas: 30 de Calpulalpan, 3 de Emiliano Zapata, 1 de Nanacamilpa y 1 de Apan; 31 son de Tlaxcala y 4 de Hidalgo, sin Chignahuapan. Su Y medio de 3.028571 t/ha y rango 2.5–3.5 están dentro del rango restante. El problema no es un extremo de Y fuera del entrenamiento: sí hay extrapolación de covariables. 33/35 exceden el máximo del resto en fracción temprana de lluvia y 34/35 en DTRstd. La lluvia total tiene SMD 0.231077, frente a 5.137570 de fracción temprana y 3.868436 de DTRstd; NDVI es menor (SMD −1.317668). Por tanto, distribución temporal y temperatura distinguen más este bloque que intensidad total. Estas diferencias no prueban una causa agronómica.

El modelo F4-S1 tiene sesgo +1.041033 t/ha en bloque 3; T1 baja a +0.064922 y T3 a +0.718204. La ganancia SSE del bloque 3 es 33.852255 para T1 y 15.550063 para T3. La reducción de sesgo cuadrático aporta 37.783737 y 19.877660 respectivamente, compensada por **aumento** de la dispersión de errores. La mejora es principalmente corregir nivel regional; no reducir toda la variabilidad local. 31/35 parcelas mejoran con ambos, 2 solo con T3 y 2 con ninguno. El bloque representa 25.36% de parcelas pero 131.9%/132.2% de las ganancias netas T3/T1 porque otros bloques deterioran. No es únicamente peso por tamaño ni solo cinco casos extremos.'''
    narr_influence='''La mezcla fija depende más de pocos beneficiarios: top 5 explican 163.69% de la ganancia neta y omitirlos descriptivamente revierte SSE. En T3 municipal top 5 explican 55.33%, y al omitirlos todavía mejora RMSE en 0.045040 t/ha; no es la misma fragilidad de la mezcla. Sin embargo, solo 54/138 parcelas (39.13%) mejoran su pérdida cuadrática municipal y la mediana de ganancia es negativa: el beneficio se concentra en reducir errores grandes, no en mejorar a la mayoría. En espacio, top 5 explican 45.12% de la ganancia T3 y 45.64% de T1; omitirlos conserva la ventaja de ambos. Su fragilidad espacial es principalmente regional: omitir bloque 3 elimina/revierte la ganancia. En perfil, T3 sí revierte al omitir sus cinco principales beneficiarios. Cada conclusión corresponde a un protocolo concreto, sin combinar rankings.'''
    executive=f'''# Etapa D — Síntesis ejecutiva para FIRA

**El programa identifica candidatos con fortalezas diferentes, pero no un ganador universal ni una validación externa concluida.** Las 138 etiquetas de2025 se han reutilizado para descubrir y comparar hipótesis. Nuevas particiones de esas mismas etiquetas no sustituyen nuevos rendimientos.

Para parcelas semejantes a las observadas, Champion continúa como referencia histórica. La mezcla fija50/50 mejora ligeramente en validación aleatoria, pero parte importante de su ganancia depende de pocas parcelas y no tiene evaluación geográfica equivalente.

Para municipios no representados, lluvia compacta + NDVI mayo (C-T3) es el candidato más defendible de esta investigación. Su ventaja municipal se compara con lluvia mensual + NDVI en las mismas parcelas/folds; no demuestra transferencia entre campañas, ni un beneficio universal dentro de Chignahuapan. Su compresión resume cantidad, fracción temprana y concentración temporal de lluvia.

{md(metrics[metrics.experiment.isin(['CHAMPION','FIXED_50_50',d.BASE,'C-T3','C-T1','C-H0M'])][['experiment','protocol','RMSE','MAE','n_parcels','n_repeats']])}

El bloque espacial3 contiene {int(total3)} etiquetas. La menor cifra espacial de C-T1 y C-T3 depende fuertemente de sus errores en ese bloque. Al omitirlo solo del cálculo, sin volver a entrenar, la ventaja de C-T3 se revierte. Este resultado impide prometer una mejora general para otras regiones.

La ventaja municipal de C-T3 resiste omitir del cálculo sus cinco mayores beneficiarios, aunque mejora el error cuadrático de solo 54 de 138 parcelas. Es una reducción importante de algunos errores grandes, no una mejora para la mayoría. La dependencia espacial es territorial: el bloque 3 muestra distinta temporalidad de lluvia/DTR y una sobreestimación regional del modelo base. No se ha demostrado el mecanismo que causa ese patrón.

El intercepto jerárquico no mejora de manera consistente frente al control Ridge equivalente. La pérdida intraperfil tampoco justifica sustituir el entrenamiento convencional. Añadir temperatura, suelo, relieve o índices vegetales no asegura una mejora: asociación agronómica y utilidad incremental del modelo son preguntas diferentes.

Dentro de perfiles idénticos quedan diferencias grandes que clima no puede distinguir. NDVI mayo aporta contraste parcelario y la dinámica LAI aporta una mejora local pequeña. No hemos resuelto la heterogeneidad local ni demostrado que sea irreducible. Conviene verificar rendimientos/superficies y medir fechas, variedad, manejo y suelo real antes de añadir complejidad.

Decisiones actuales: preservar Champion; congelar la mezcla para comparación aleatoria independiente, C-T3 para municipios, F4-S1 como referencia sencilla y C-T1 como hipótesis espacial. Mantener Ridge como control. No integrar jerarquía, pérdidas adicionales ni cartografía50k sin geometrías fiables.

Prioridades de validación: municipios nuevos para comprobar C-T3, una nueva campaña para comprobar estabilidad temporal, y parcelas adicionales de varios perfiles repetidos si la prioridad es explicar diferencias locales. El tamaño se decidirá por precisión, municipios/campañas independientes y recursos; no por contar parejas ni por sumar diez repeticiones de las mismas etiquetas.

Los intervalos jerárquicos nominales90% subcubren perfiles nuevos municipales y son mucho más amplios en espacio. No deben usarse como garantía operacional. Cualquier calibración futura necesita datos separados.

Etapa D no entrenó modelos, no produjo nuevas estimaciones predictivas ni alteró Champion, mezcla, folds, etiquetas o resultados A–C. El reporte técnico, matriz de evidencia, protocolo prospectivo y auditoría sustentan estas decisiones. Las cifras y límites de esta síntesis provienen de `metrics_summary.csv`, `block_composition.csv`, `spatial_block_gains.csv`, `spatial_block_omission.csv`, `gain_concentration.csv` y `archived_interval_calibration.csv`.
'''
    tech=f'''# Etapa D — Síntesis de evidencia y diagnóstico de generalización

## 1. Resumen

Cierre metodológico A–D, exclusivamente descriptivo sobre predicciones archivadas. Se preservan las decisiones previas; no se vuelve a seleccionar un ganador ni se entrena ningún modelo. C-T3 merece validación municipal; Champion/mezcla siguen limitados al ámbito aleatorio compatible; C-T1 mantiene una hipótesis espacial con dependencia del bloque3; H1 no aporta ventaja frente a H0M.

## 2. Objetivos

D1 concentración de ganancias; D2 composición bloque3; D3 escenarios de generalización; D4 heterogeneidad local; D5 información/validación externa; D6 candidatos y controles; D7 alcance científico. Ninguno introduce un nuevo experimento predictivo.

## 3. Datos y protocolos

197 parcelas:138Y y59PRED sin uso de etiquetas;53perfiles completos,43conY,12repetidos. Chignahuapan71Y. Los subconjuntos locales de perfiles4/24 tienen29/33etiquetas; el perfil24 completo incluye una observación fuera del municipio y tiene34. No confundir n local con tamaño total del perfil.

65folds congelados:50aleatorios(5×10),5porperfil,5municipales,5espaciales, con sus particiones internas originales. Métrica primaria:138OOF completas por repetición, después media de repeticiones. Media de folds, métrica de predicción media por parcela y RMS de pérdidas promediadas entre repeticiones son diagnósticos distintos, identificados por separado.

## 4. Inventario y 5. Comparabilidad

`model_inventory.csv` recupera todas las series OOF de antecedentes, incluidos controles descartados, IDs exactos, configuraciones/especificaciones recuperables, disponibilidad y hashes. `background_artifact_inventory.csv` registra reportes/configuraciones; `protected_inputs.csv` conserva scripts, fuentes, métricas y modelos previos. Donde una especificación no está en JSON se conserva referencia a fuentes/tablas, sin inventarla.

Llave explícita: (ID_POLIGONO, protocolo, repetición, fold), con Y idéntico. `comparability.csv` verifica conjuntos completos uno-a-uno; los IDs de validación corresponden a splits congelados y a procedencia OOF anterior. Champion no se reconstruye. F4-S1 y C-T0 son la misma referencia, y B2/F4-E2 son alias: no constituyen evidencia independiente.

{md(metrics[metrics.protocol.eq('random')])}

{md(metrics[metrics.protocol.ne('random')])}

Estas tablas son universos separados. Los resultados históricos de Familias2/3 con mediafold se preservan en sus archivos y no se insertan como si fueran estas mismas métricas. Las decisiones originales estaban basadas en comparaciones propias; D no altera sus números archivados.

## 6. Caracterización del bloque espacial3

{md(comp)}

{narr_block}

Distribuciones seleccionadas, con unidades originales: lluvia total mm, DTRstd °C, NDVI sin unidad, Y t/ha, altitud m, pendiente grados.

{md(dist[dist.feature.isin([c.COMPACT[0],c.DTR,c.NDVI,d.TARGET,'altitude_m','slope_degrees'])])}

Contraste3/resto SMD usa desviaciones muestrales y no se calcula ante varianza degenerada. No hay pruebas masivas ni búsqueda de una variable ganadora.

{md(smd[smd.feature.isin(c.COMPACT+[c.DTR,c.NDVI,d.TARGET,'altitude_m','slope_degrees'])])}

`spatial_support.csv` distingue rangos marginales, cercanía al límite y distancia estandarizada conjunta al entrenamiento en lluvia total/DTR/NDVI. Estar dentro de cada rango no garantiza combinaciones conocidas ni soporte del Champion. Los rangos de Y son descripción ex post, nunca una regla para definir soporte predictivo. Suelo y geología se describen mediante cuotas cartográficas existentes; no se atribuyen textura o capacidad hídrica física a una categoría.

## 7. Descomposición de errores y sensibilidad

Ganancia=SSE_F4S1−SSE_candidato; positiva favorece candidato. Las contribuciones suman la ganancia total; ganancia deRMSE no es sumable. La tabla separa tamaño, SSE y sesgo.

{md(gain[gain.candidate.isin(['C-T1','C-T3'])])}

{md(omit[omit.candidate.isin(['C-T1','C-T3'])])}

Se denomina **sensibilidad de agregación OOF al omitir el bloque**. Ningún modelo fue ajustado de nuevo. La reversión T3 al omitir3 es un límite de estabilidad territorial, no una nueva validación leave-one-block-out.

{md(overlap)}

{md(biasparts[biasparts.block.eq(3)])}

Las ganancias superpuestas y las contribuciones por parcela están en `spatial_parcel_gain_overlap.csv`; un mismo caso puede beneficiar ambos modelos. `spatial_block_errors.csv` registraRMSE/MAE/sesgo y cuantiles de error. La diferenciaSSE por bloque puede descomponerse como n·(bias_base²−bias_candidato²) más cambio de varianza de errores: ambos términos se reportan en `block_bias_variance_decomposition.csv`. Un sesgo regional reducido no demuestra que DTR cause el rendimiento.

Hipótesis futuras verificables: comprobar en varias regiones independientes si condiciones parecidas al bloque3 vuelven a producir sesgo de lluvia mensual y si T1/T3 lo reducen; contrastar regiones con solapamiento y fuera del soporte; verificar si la ventaja persiste sin pocos beneficiarios. No se crea una regla territorial de activación.

## 8. Influencia de parcelas y casos persistentes

`paired_losses.parquet` conserva todas las filas e IDs. En aleatoria se promedian pérdidas de las diez repeticiones por parcela para influencia; no se promedian predicciones para métricas primarias. Se reportan SE/AE, medianas, cuantiles, proporciones de mejora y ganancias municipales/perfil.

{md(conc[(conc.k.isin([1,5]))&conc.candidate.isin(['FIXED_50_50','C-T3','C-T1'])])}

Las fracciones de ganancia neta pueden superar100% porque otros casos deterioran; si el neto es negativo, esa razón no mide concentración de una mejora. Se acompaña fracción de ganancias positivas. `parcel_omission_sensitivity.csv` elimina IDs solo del cálculo diagnóstico y preserva predicciones/etiquetas. No se utiliza para favorecer un ranking.

{narr_influence}

{md(omission[(omission.k.eq(5))&omission.order.eq('largest_gain')&omission.candidate.isin(['FIXED_50_50','C-T3','C-T1'])])}

Casos prioritarios, orden descriptivo por recurrencia en el top10% de error absoluto y magnitud, equilibrando modelo/protocolo para que diez repeticiones no pesen como diez campañas:

{md(cases.head(15)[[d.ID,'Municipio','climate_profile','balanced_mean_AE','balanced_large_error_fraction','same_sign_unit_fraction','archived_C_support_outside_fraction','classification']])}

Signo se define predicho−observado. Errores constantes de signo, signos variables y compensaciones entre modelos se conservan en `case_model_protocol_details.csv`. Las banderas de soporte abarcan solo tres covariables deC. No hay evidencia independiente de error de etiqueta; la tabla es una agenda de verificación documental/campo, no una lista de exclusión. Registro primario, superficie y fechas deben verificarse antes de atribuir causas individuales.

## 9. Heterogeneidad intraperfil

{md(variance)}

SS_total=SS_entre+SS_dentro es una identidad descriptiva ponderada por parcelas. La fracción entre perfiles no equivale a varianza causalmente explicada por clima ni aR² predictivo fuera de muestra. Los perfiles singleton tienen SS_dentro0 por construcción.

En las 138 etiquetas, 74.4534% de la suma de cuadrados queda entre perfiles y 25.5466% dentro. En Chignahuapan, 85.8179% queda dentro de perfiles y 14.1821% entre ellos. El problema local tiene una estructura distinta del contraste regional; esas proporciones no son una cota del error reducible ni explicación causal del clima. Los casos AGC_171, AGC_015 y AGC_024 mantienen sobreestimación alta entre modelos/protocolos y son prioridades documentales, sin evidencia de etiqueta incorrecta.

{md(prof[(prof.profile.isin([4,24]))])}

{md(local[local.scope.isin(['full_profile','outside_Chignahuapan'])])}

Las parejas se calculan solo cuando las dos parcelas fueron evaluadas por el mismo ajuste externo. En aleatoria muchos pares entre folds no son evaluables para esta métrica; cada protocolo tiene soporte distinto. Tablas por perfil reportan n_parejas/n_parcelas y dispersión de predicciones. Las934parejas posibles locales no son934observaciones independientes. Ninguna línea resuelve la heterogeneidad de manera general; B3 añade un beneficio local pequeño con costo municipal inaceptable.

EtapaA: {int(source_pairs.geology_different.sum())}/{len(source_pairs)} parejas presentan geología250k distinta; {int((source_pairs.geology_different & source_pairs.ndvi_similar).sum())} además tienen NDVI similar. Soporte de categorías:

{md(geology)}

Son contrastes repetidos en solo dos perfiles, con categorías escasas y reservas de límites. La no redundancia descriptiva respecto a NDVI no demuestra contribución incremental. Se justificaría una investigación futura separada si se verifican unidades/límites y se amplían grupos, no integración automática. Suelo50k no existe en el repositorio; imagen1996 es topográfica; PDF SGM2017 no proporciona geometría temática fiable. D no reabre esas fuentes.

Parcelas semejantes enX pueden diferir en variedad, fecha de siembra, densidad, fertilización, malezas, agua, profundidad/textura, enfermedades, cosecha o calidad de registro. Son variables no observadas hipotéticas; residuo no equivale a error irreducible.

## 10. Escenarios y decisiones

{md(evidence)}

S1:Champion como referencia histórica y mezcla como candidato exploratorio; S2:compararF4-S1/T3/H0M sin confundir perfil con municipio; S3:T3 es candidato principal observado, con costo aleatorio y local; S4:no hay ganador espacial robusto general; S5:E2 ofrece una mejora local pequeña, H0M sirve de control yB3 no se promueve. No hay ponderación retrospectiva para combinar escenarios.

La sensibilidad municipal existente de T3 está preservada en `municipal_fold_omission_archived.csv`: el beneficio RMSE persiste al omitir cada fold del cálculo, pero MAE puede deteriorar ligeramente al omitir uno. Su costo aleatorio e intraperfil está en las tablas compatibles. La persistencia de RMSE no implica que cada municipio ni cada parcela mejore.

## 11. Incertidumbre y límites

{md(interval[interval.experiment.eq('C-H1')])}

Intervalos realmente generados:90% Gaussian working posterior, con sigma/ratio/alpha fijados por ajuste/CV. Incluyen ruido residual, incertidumbre condicional del intercepto y covarianza de efectos fijos bajo regularización; nuevos perfiles añaden tau². Omiten incertidumbre de hiperparámetros, selección, especificación, fuentes/medición y cambio de dominio. No son intervalos plenamente bayesianos ni garantías de cobertura.

La cobertura y ancho por perfil conocido/nuevo y protocolo muestran subcobertura municipal nueva y mayor amplitud espacial. H1 selecciona ratio0 en {int((h[h.protocol.eq('random')].ratio==0).sum())}/50ajustes aleatorios; solo12grupos repetidos limitan evidencia de varianza no nula. D no calibra un nuevo método. Investigación futura necesita conjuntos independientes de calibración/evaluación y suficientes grupos/campañas, sin garantías automáticas de bootstrapparcelario o conformal estándar bajo cambio de dominio.

## 12. Diseño independiente y 13. Información adicional

Ver `prospective_validation_protocol.md`: estimandos R_similar/R_newmun/R_newseason, gruposV1–V5, candidatos fijos, reglas pendientes explícitas, precisión agrupada, sellado previo aY, tratamientos de faltantes/soporte y comparaciones incompletas. No se fija un tamaño óptimo inventado ni se entrena el modelo final enD.

{md(agenda)}

## 14. Síntesis científica transversal

Clima distingue contextos, pero una malla compartida no distingue parcelas con vectores iguales. NDVI mayo aporta estado observado y contraste local; no asegura misma fase fenológica. LAI se deriva de SAVI por la ecuaciónFIRA y no es una fuente espectral independiente. Redundancia conSAVI/FAPAR/EVI no es identidad perfecta; las asociaciones parciales deF4-E delimitan evidencia, no justifican otro screening. Descriptores hasta octubre no deben presentarse como predictores disponibles enmayo.

Terreno/suelo/geología pueden tener importancia agronómica aun cuando no mejoren incrementalmente estos modelos. Escala250k, clases con pocas etiquetas, redundancia regional y errores de medición limitan su uso; DEM120m tampoco mide microtopografía ni humedad observada. EnJ/K una arquitectura residual reduce ciertos deterioros de la adición directa, sin demostrar beneficio estable de cada bloque. L/M muestran quePCA y sumar sensores/historia no crean información nueva automáticamente ni una ventaja común entre protocolos.

La pérdida intraperfilB no logró una mejora útil general. Lambda0 puede coexistir con peor validación por cambio de selecciónalpha/rho; no atribuir todo el efecto a una penalización activa. C muestra otra separación: mejoras frente aEN pueden provenir deL2, no de interceptos aleatorios. Para perfiles nuevos el efecto medio es0; conocido no equivale a transferible, y el intercepto cancela en diferencias del mismo perfil.

Compactar lluvia es regularización estructural: reduce siete coeficientes mensuales a tres descriptores, pero fracción/HHI son funciones no lineales del vector original; no es simplemente una rotaciónPCA ni un mecanismo probado. Puede limitar extrapolación de coeficientes mensuales, hipótesis consistente con desempeño municipal, peroRMSE no demuestra esa explicación.

Familias2/3 aportaron interpretación funcional/estructural sin justificar mayor complejidad predictiva. Screening1473 seleccionó señales retrospectivamente sobre las mismas138Y:NDVI/DTR no se descubrieron en una muestra independiente. El propio screening ya evaluóNDVI mayo solo; su predicción global individual fue inferior a lluvia. No confundir esa evidencia con una nueva prueba autorizada de invertir la arquitectura residual, queD no ejecuta.

La complejidad puede distribuir información limitada de manera inestable. Estos resultados distinguen límites de medición/datos y de las hipótesis evaluadas; no prueban que todos los algoritmos complejos fracasen ni que todos los residuos sean inmodelables.

## 15. Conclusiones, 16. Limitaciones y 17. Trabajo futuro

RespuestasD1–D7: concentración y reversión se documentan porIDs/bloques; bloque3 se caracteriza sin causalidad; los candidatos dependen del estimando; heterogeneidad local permanece; validar municipios/campañas y medir manejo/fechas/suelo real es más informativo que otro concurso; se congelan hipótesis/control sin ajuste final;138Y permiten evidencia exploratoria dentro de los protocolos existentes, no generalización nacional/temporal confirmada.

No independencia entre repeticiones, folds entrenados con datos solapados, parejas o modelos aliados; pocas unidades geográficas; regiones definidas con covariables disponibles; múltiples hipótesis retrospectivas; cartografía histórica; ausencia de nuevosY. Omisiones e influencia son sensibilidades descriptivas, no intervalos/p-valores confirmatorios. D no entrena, optimiza, combina pesos, corrige etiquetas, elimina parcelas ni produce nuevas predicciones.

Trabajo futuro se limita al protocolo prospectivo y adquisición, no nuevos experimentos enD. Las cuotas, margen de utilidad y reglas finales de entrenamiento pendientes deben sellarse antes deYexterna. Mantener reportesA–C inmutables, incluso cuando sus frases históricas dicen que etapas posteriores aún no se habían ejecutado.
'''
    mapping=[('technical_report.md','territorial_program_stage_d.md',tech),('executive_summary.md','territorial_program_stage_d_executive.md',executive),('evidence_matrix.md','territorial_program_stage_d_evidence.md','# Etapa D — Matriz final de evidencia\n\n'+md(evidence)),('prospective_validation_protocol.md','territorial_program_stage_d_validation.md',PROSPECTIVE)]
    for name,doc,text in mapping:
        if name=='technical_report.md':text+='\n\n## Visualizaciones\n\n'+'\n\n'.join(f'![{path.stem}](../figures/{path.name})' for path in sorted((d.OUT/'figures').glob('*.png')))
        (d.OUT/'report'/name).write_text(text,encoding='utf8')
        doc_text=text.replace('../figures/','../'+(d.OUT/'figures').relative_to(d.ROOT).as_posix()+'/')
        (d.ROOT/'documentation'/doc).write_text(doc_text,encoding='utf8')
    print('D reports and12figures ready',flush=True)
