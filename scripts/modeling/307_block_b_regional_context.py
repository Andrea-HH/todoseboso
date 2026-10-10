"""Bloque B B0-B6: contexto regional, ENA y síntesis A+B.

No descarga fuentes, no modifica Bloque A/Champion y no asigna estimaciones
estatales o nacionales de ENA a parcelas como si fueran observaciones locales.
"""
from pathlib import Path
import json, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr, rankdata
from sklearn.cluster import KMeans

warnings.filterwarnings("ignore"); sns.set_theme(style="whitegrid")
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"outputs/research/block_b_regional_context";TAB=BASE/"tables";FIG=BASE/"figures";REP=BASE/"report"
for p in (TAB,FIG,REP):p.mkdir(parents=True,exist_ok=True)
ID="ID_POLIGONO";RNG=np.random.default_rng(2026)

def rho(a,b):
 z=pd.DataFrame({'a':a,'b':b}).dropna()
 return float(spearmanr(z.a,z.b).statistic) if len(z)>=8 and z.a.nunique()>1 and z.b.nunique()>1 else np.nan

def boot_rho(a,b,n=999):
 z=pd.DataFrame({'a':a,'b':b}).dropna();aa=z.a.to_numpy(float);bb=z.b.to_numpy(float);vals=[]
 for _ in range(n):
  ix=RNG.integers(0,len(z),len(z));ra=rankdata(aa[ix]);rb=rankdata(bb[ix]);vals.append(np.corrcoef(ra,rb)[0,1])
 return rho(aa,bb),*np.quantile(vals,[.025,.975])

def partial_spearman(df,x,y,covs):
 z=df[[x,y]+covs].dropna();X=np.c_[np.ones(len(z)),*[rankdata(z[c]) for c in covs]]
 rx=rankdata(z[x]);ry=rankdata(z[y]);ex=rx-X@np.linalg.lstsq(X,rx,rcond=None)[0];ey=ry-X@np.linalg.lstsq(X,ry,rcond=None)[0]
 return float(np.corrcoef(ex,ey)[0,1]),len(z)

def ols_table(df,y,terms):
 z=df[[y]+terms].dropna();X=np.c_[np.ones(len(z)),z[terms].to_numpy(float)];coef=np.linalg.lstsq(X,z[y],rcond=None)[0];res=z[y]-X@coef
 n,p=X.shape;s2=(res@res)/max(n-p,1);cov=s2*np.linalg.pinv(X.T@X);se=np.sqrt(np.diag(cov));r2=1-(res@res)/((z[y]-z[y].mean())@(z[y]-z[y].mean()))
 return pd.DataFrame({'term':['intercept']+terms,'coefficient':coef,'standard_error':se,'ci95_low':coef-1.96*se,'ci95_high':coef+1.96*se,'n':n,'R2':r2})

def main():
 aroot=ROOT/"outputs/research/block_a_agroenvironmental"
 m=pd.read_csv(aroot/"tables/01_parcel_master_auditable.csv")
 import geopandas as gpd
 geo=gpd.read_file(ROOT/"data/original/02_conjunto_70_30/Parcelas_Reto_AGC_CONJUNTO.shp")[["ID_POLIGON","Estado","Municipio","geometry"]]
 geo[ID]=geo.ID_POLIGON.astype(str);m=m.merge(geo.drop(columns=["ID_POLIGON","geometry"]),on=ID,how="left")
 assert len(m)==138 and m.Estado.notna().all() and set(m.Estado)=={'Hidalgo','Puebla','Tlaxcala'}
 m.to_csv(TAB/"01_block_b_parcel_context.csv",index=False)

 # B0 audit and regional sample/variation.
 vars=['y_true','precip_early_sum','precip_cycle_sum','TOPO_ADV_twi_mean','TOPO_BASIC_slope_mean','S2_dswi4_green_duration','S2_ndvi_std_heterogeneity_mean','residual_mean','mean_absolute_error']
 audit=[]
 for state,g in m.groupby('Estado'):
  for v in vars:audit.append({'Estado':state,'variable':v,'n':g[v].notna().sum(),'mean':g[v].mean(),'sd':g[v].std(),'min':g[v].min(),'max':g[v].max(),'iqr':g[v].quantile(.75)-g[v].quantile(.25),'cv_abs':g[v].std()/abs(g[v].mean()) if abs(g[v].mean())>1e-9 else np.nan})
 audit=pd.DataFrame(audit);audit.to_csv(TAB/"02_regional_sample_variation.csv",index=False)

 # B2 global/within-state associations and state-adjusted partial ranks.
 exposures=['precip_early_sum','TOPO_ADV_twi_mean','TOPO_BASIC_slope_mean','S2_dswi4_green_duration','S2_ndvi_std_heterogeneity_mean']
 rows=[]
 for x in exposures:
  r,lo,hi=boot_rho(m[x],m.y_true);rows.append({'scope':'GLOBAL','group':'ALL','variable':x,'n':len(m),'spearman_y':r,'ci95_low':lo,'ci95_high':hi})
  for state,g in m.groupby('Estado'):
   r,lo,hi=boot_rho(g[x],g.y_true);rows.append({'scope':'STATE','group':state,'variable':x,'n':len(g),'spearman_y':r,'ci95_low':lo,'ci95_high':hi})
 reg=pd.DataFrame(rows)
 # Remove state means to isolate within-state rank covariance.
 for x in exposures:
  xr=m[x]-m.groupby('Estado')[x].transform('mean');yr=m.y_true-m.groupby('Estado').y_true.transform('mean')
  r,lo,hi=boot_rho(xr,yr);reg.loc[len(reg)]={'scope':'STATE_DEMEANED','group':'ALL','variable':x,'n':len(m),'spearman_y':r,'ci95_low':lo,'ci95_high':hi}
 reg.to_csv(TAB/"03_global_state_associations.csv",index=False)

 controls=[]
 basecov=['TOPO_BASIC_elevation_mean','TOPO_BASIC_slope_mean']
 state_d=pd.get_dummies(m.Estado,drop_first=True,dtype=float);mc=pd.concat([m,state_d],axis=1);statecols=state_d.columns.tolist()
 for x in exposures:
  cov=[c for c in basecov if c!=x];r,n=partial_spearman(mc,x,'y_true',cov);rs,ns=partial_spearman(mc,x,'y_true',cov+statecols)
  controls.append({'variable':x,'partial_rho_elevation_slope':r,'n':n,'partial_rho_plus_state':rs,'n_plus_state':ns,'controls':'+'.join(cov+statecols)})
 controls=pd.DataFrame(controls);controls.to_csv(TAB/"04_controlled_associations.csv",index=False)

 # Geographic clusters independent of y; useful to distinguish state from location.
 coords=m[['centroid_x_m','centroid_y_m']].to_numpy();coords=(coords-coords.mean(0))/coords.std(0)
 m['geo_cluster_5']=KMeans(5,n_init=50,random_state=2026).fit_predict(coords)+1
 cluster=[]
 for cl,g in m.groupby('geo_cluster_5'):
  cluster.append({'geo_cluster':cl,'n':len(g),'states':';'.join(f'{k}:{v}' for k,v in g.Estado.value_counts().items()),'yield_mean':g.y_true.mean(),'precip_early_mean':g.precip_early_sum.mean(),'rho_precip_y':rho(g.precip_early_sum,g.y_true),'residual_mean':g.residual_mean.mean()})
 pd.DataFrame(cluster).to_csv(TAB/"05_geographic_cluster_context.csv",index=False)

 # B3: retain ENA estimates at their valid geographic scale only.
 ena=ROOT/"data/processed/ena_preprocessed"
 barley=pd.read_csv(ena/"04_cebada_detalle_ena_agr01.csv");seed=pd.read_csv(ena/"07_cebada_semilla_precision_completa.csv")
 barley.to_csv(TAB/"06_ena_barley_context.csv",index=False);seed.to_csv(TAB/"07_ena_seed_context.csv",index=False)
 precision=pd.read_csv(ena/"05_cebada_indicadores_precision_interactivo.csv")
 precision.to_csv(TAB/"08_ena_barley_precision_context.csv",index=False)

 # B4 factor availability: documentary evidence versus parcel-linkable variable.
 factor_rows=[
 ['Propiedades y calidad del suelo','Ninguna estimación utilizable en archivos ENA disponibles','No','Textura/profundidad/materia orgánica/pH por polígono o mapa edafológico compatible'],
 ['Drenaje y retención de humedad','Ninguna estimación directa; régimen hídrico no mide drenaje','No','Clase de drenaje, capacidad de retención y humedad observada por parcela'],
 ['Riego o temporal','Estatal para superficie agrícola general; no cebada parcelaria','No','Modalidad por parcela/ciclo; ENA estatal sólo contextualiza'],
 ['Fechas de siembra y cosecha','Ninguna estimación utilizable en tablas disponibles','No','Fechas por parcela y ciclo'],
 ['Variedad o tipo de semilla','Nacional para cebada: criolla/mejorada/certificada; no variedad','No','Variedad y lote de semilla por parcela'],
 ['Fertilización y manejo agronómico','Ninguna estimación utilizable en extractos disponibles','No','Dosis, fechas, producto, labranza y manejo por parcela'],
 ['Enfermedades y afectaciones','Ninguna estimación utilizable en extractos disponibles','No','Incidencia/severidad y fecha por parcela'],
 ]
 factors=pd.DataFrame(factor_rows,columns=['factor','ena_2025_available_scale','parcel_linkable','additional_data_required']);factors.to_csv(TAB/"09_omitted_productive_factors.csv",index=False)

 # B5 residual regional diagnostics; do not repeat Moran.
 residual=[]
 for state,g in m.groupby('Estado'):
  residual.append({'Estado':state,'n':len(g),'yield_mean':g.y_true.mean(),'prediction_mean':g.prediction_mean.mean(),'bias_y_minus_pred':g.residual_mean.mean(),'MAE':g.mean_absolute_error.mean(),'overestimate_fraction':(g.residual_mean<0).mean(),'underestimate_fraction':(g.residual_mean>0).mean(),'SSE_fraction':g.mean_residual_squared.sum()/m.mean_residual_squared.sum()})
 residual=pd.DataFrame(residual);residual.to_csv(TAB/"10_regional_residual_diagnostics.csv",index=False)
 # Residual ~ y + state: state coefficients are remaining mean shifts conditional on y.
 rr=mc.copy();rr['state_Puebla']=(rr.Estado=='Puebla').astype(float);rr['state_Tlaxcala']=(rr.Estado=='Tlaxcala').astype(float)
 ols=ols_table(rr,'residual_mean',['y_true','state_Puebla','state_Tlaxcala']);ols.to_csv(TAB/"11_residual_y_state_adjustment.csv",index=False)

 # B6 joint matrix.
 def get(scope,var,group='ALL'):
  q=reg[(reg.scope==scope)&(reg.group==group)&(reg.variable==var)];return np.nan if q.empty else q.spearman_y.iloc[0]
 joint=[
 ['Rendimiento espacialmente agrupado','Moran I=0.666, p=.001','Diferencias estatales/geográficas cuantificadas; no se repite Moran','La geografía estructura Y, no implica una causa única','Estados, clima, suelo y manejo están confundidos','exploratoria','Comprensión regional; obtener suelo/manejo'],
 ['Precipitación abril-junio',f'ρ global={get("GLOBAL","precip_early_sum"):.3f}',f'Hidalgo={get("STATE","precip_early_sum","Hidalgo"):.3f}; Puebla={get("STATE","precip_early_sum","Puebla"):.3f}; Tlaxcala={get("STATE","precip_early_sum","Tlaxcala"):.3f}; within-state={get("STATE_DEMEANED","precip_early_sum"):.3f}', 'Separar gradiente regional de variación interna; no causalidad','Clima mensual y calendario de siembra desconocido','exploratoria','Contraste con calendario, suelo y manejo antes de modelar'],
 ['TWI/humedad potencial','ρ≈-0.20',f'Within-state ρ={get("STATE_DEMEANED","TOPO_ADV_twi_mean"):.3f}','Potencial geomorfológico, no humedad medida','Sin drenaje/suelo/humedad','exploratoria','Validar con suelo e hidrología observada'],
 ['Pendiente/relieve','Asociación positiva moderada',f'Within-state pendiente ρ={get("STATE_DEMEANED","TOPO_BASIC_slope_mean"):.3f}','Puede representar contexto regional o drenaje; no mecanismo probado','Resolución DEM y confusión espacial','exploratoria','No ampliar features; validar mecanismo'],
 ['Duración del vigor','DSWI4 duración ρ≈0.40',f'Within-state ρ={get("STATE_DEMEANED","S2_dswi4_green_duration"):.3f}','Trayectoria satelital distingue parcelas más allá o no del estado según estabilidad','No es fenología de campo','exploratoria','Validación nested compacta sólo si estable'],
 ['Heterogeneidad NDVI','ρ≈0.27',f'Within-state ρ={get("STATE_DEMEANED","S2_ndvi_std_heterogeneity_mean"):.3f}','Agregado intraparcela potencialmente informativo','No localiza parches','exploratoria','Conservar como hipótesis secundaria'],
 ['Regresión hacia la media','LOW sobreestimado/HIGH subestimado','Se evalúa sesgo por estado y condicionado por Y','Principal patrón de error; estado puede añadir o no desplazamiento','Sólo OOF 2025','respaldada','No recalibrar sin validación externa'],
 ['Factores de manejo/suelo','No medidos','ENA sólo contextualiza; no enlazable a parcela','Omisión plausible, aún no cuantificada','Faltan observaciones parcelarias','no evaluable','Fase C dirigida a suelo, manejo y calendario'],
 ['Valor predictivo incremental','No demostrado en A/F3.2','B es contextual, no entrena modelo','Comprensión mejora más que predicción','n=138; riesgo de fuga ecológica','sin evidencia suficiente','Congelar Champion; experimento sólo tras nuevos datos']]
 joint=pd.DataFrame(joint,columns=['Hipótesis','Evidencia Bloque A','Evidencia Bloque B','Interpretación conjunta','Limitación','Clasificación','Acción recomendada']);joint.to_csv(TAB/"12_joint_hypothesis_matrix_A_B.csv",index=False)

 make_figures(m,reg,residual,controls)
 make_report(m,audit,reg,controls,residual,ols,factors,joint,barley)
 manifest={'scope':'B0-B6','train_n':138,'states':m.Estado.value_counts().to_dict(),'external_downloads':False,'champion_modified':False,'block_a_modified':False,'ENA_rule':'context at published national/state scale; never assigned as parcel covariate','residual_sign':'y_true-prediction','geographic_clusters':'KMeans k=5 on standardized centroids; y excluded','seed':2026}
 (BASE/"block_b_manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
 print(f'Bloque B completo: {BASE}')

def make_figures(m,reg,residual,controls):
 fig,ax=plt.subplots(1,3,figsize=(14,4));
 for a,(state,g) in zip(ax,m.groupby('Estado')):sns.regplot(g,x='precip_early_sum',y='y_true',lowess=True,scatter_kws={'s':25},line_kws={'color':'black'},ax=a);a.set_title(f'{state} (n={len(g)})');a.set_xlabel('Precipitación abr–jun (mm)');a.set_ylabel('Rendimiento (t/ha)')
 fig.suptitle('Precipitación temprana y rendimiento dentro de cada estado');fig.tight_layout();fig.savefig(FIG/'01_precipitation_yield_by_state.png',dpi=180);plt.close(fig)
 q=reg[reg.variable.eq('precip_early_sum')].copy();plt.figure(figsize=(8,4));plt.errorbar(np.arange(len(q)),q.spearman_y,yerr=[q.spearman_y-q.ci95_low,q.ci95_high-q.spearman_y],fmt='o');plt.axhline(0,color='k',lw=.8);plt.xticks(np.arange(len(q)),q['scope']+': '+q.group,rotation=30,ha='right');plt.ylabel('Spearman precipitación–Y (IC95 bootstrap)');plt.tight_layout();plt.savefig(FIG/'02_precipitation_correlation_stratified.png',dpi=180);plt.close()
 fig,ax=plt.subplots(1,3,figsize=(13,4));
 for a,v in zip(ax,['TOPO_ADV_twi_mean','TOPO_BASIC_slope_mean','S2_dswi4_green_duration']):sns.scatterplot(m,x=v,y='y_true',hue='Estado',ax=a);a.set_ylabel('Rendimiento (t/ha)')
 fig.suptitle('Señales de A estratificadas por estado');fig.tight_layout();fig.savefig(FIG/'03_block_a_signals_by_state.png',dpi=180);plt.close(fig)
 fig,ax=plt.subplots(1,2,figsize=(10,4));sns.barplot(residual,x='Estado',y='bias_y_minus_pred',ax=ax[0]);ax[0].axhline(0,color='k');ax[0].set_ylabel('Sesgo OOF y−ŷ (t/ha)');sns.barplot(residual,x='Estado',y='MAE',ax=ax[1]);ax[1].set_ylabel('MAE OOF (t/ha)');fig.suptitle('Diagnóstico residual regional');fig.tight_layout();fig.savefig(FIG/'04_regional_residuals.png',dpi=180);plt.close(fig)
 plt.figure(figsize=(7,5));sns.scatterplot(m,x='y_true',y='residual_mean',hue='Estado',style='Estado');plt.axhline(0,color='k',ls='--');plt.xlabel('Rendimiento observado (t/ha)');plt.ylabel('Residuo OOF y−ŷ (t/ha)');plt.tight_layout();plt.savefig(FIG/'05_residual_y_by_state.png',dpi=180);plt.close()
 c=controls.set_index('variable')[['partial_rho_elevation_slope','partial_rho_plus_state']];c.plot.barh(figsize=(8,5));plt.xlabel('Spearman parcial con Y');plt.tight_layout();plt.savefig(FIG/'06_controlled_associations.png',dpi=180);plt.close()

def make_report(m,audit,reg,controls,residual,ols,factors,joint,barley):
 def row(scope,var,group='ALL'):
  q=reg[(reg.scope==scope)&(reg.variable==var)&(reg.group==group)].iloc[0];return f"ρ={q.spearman_y:.3f} (IC95 {q.ci95_low:.3f}, {q.ci95_high:.3f}; n={int(q.n)})"
 precip=[row('GLOBAL','precip_early_sum')]+[f'{s}: '+row('STATE','precip_early_sum',s) for s in ['Hidalgo','Puebla','Tlaxcala']]+['Centrado por estado: '+row('STATE_DEMEANED','precip_early_sum')]
 pc=controls.set_index('variable').loc['precip_early_sum'];state=residual.round(3).to_dict('records');adj=ols.round(4).to_dict('records')
 txt=f"""# Bloque B — Contexto regional, ENA y síntesis A+B

## Resumen ejecutivo

Bloque B usa las 138 parcelas TRAIN del Bloque A: Hidalgo 36, Puebla 71 y Tlaxcala 31. No modifica Champion ni A, no descarga datos y no asigna promedios ENA a parcelas. La pregunta central es si las asociaciones de A son regionales o persisten dentro de los estados.

Precipitación abril–junio: {'; '.join(precip)}. Al controlar rangos de elevación y pendiente, Spearman parcial={pc.partial_rho_elevation_slope:.3f}; al agregar indicadores de estado={pc.partial_rho_plus_state:.3f}. La magnitud debe compararse con la variación climática estatal de `02_regional_sample_variation.csv`: una correlación interna con rango estrecho es poco identificable. No se interpreta lluvia como causa negativa; puede resumir región, calendario, altitud, suelo o manejo.

El sesgo regional OOF es {state}. Después de considerar Y continuo, el ajuste descriptivo `residual ~ Y + estado` es {adj}. Esto separa parcialmente heterogeneidad regional de la regresión hacia la media, pero no identifica causas.

## B0 — Auditoría y controles

- 138/138 parcelas tienen estado; sólo TRAIN participa en asociaciones.
- El residual conserva la convención `y−ŷ`.
- Las estimaciones ENA mantienen su escala publicada y su incertidumbre.
- Puebla sin estimación ENA de cebada significa **dato no publicado**, nunca cero.
- Los cinco grupos geográficos se construyen sólo con centroides, sin Y.

## B1 — Alcance regional y ENA

ENA 2025 reporta cebada nacional y estimaciones para Hidalgo/Tlaxcala: {barley.round(3).to_dict('records')}. Sus rendimientos son producción/superficie cosechada, no mediciones FIRA ni covariables parcelarias. Los CV publicados para varias estimaciones son moderados/altos; revisar `08_ena_barley_precision_context.csv`.

## B2 — Diferencias regionales

La comparación global, estatal y centrada por estado está en `03_global_state_associations.csv`; los controles simples están en `04_controlled_associations.csv`. Las asociaciones de TWI, pendiente, duración DSWI4 y heterogeneidad NDVI también se estratificaron. Cambios de signo o intervalos amplios se consideran inestabilidad, no diferencias biológicas demostradas.

La precipitación mensual no permite inferir lluvia coincidente con siembra, emergencia o llenado. Diferencias compatibles con calendarios distintos sólo justifican pedir fechas de campo.

## B3 — Contexto productivo

ENA indica a escala nacional que 74.7% de la superficie de cebada usa semilla criolla, 12.7% mejorada y 12.4% certificada/registrada. No es una distribución de estas parcelas ni se puede estratificar por estado con el extracto disponible. La modalidad riego/temporal disponible es de superficie agrícola general, no cebada FIRA.

## B4 — Factores omitidos

{factors.to_csv(index=False)}

Ninguno de los siete factores prioritarios puede enlazarse actualmente a cada parcela. ENA aporta contexto nacional/estatal para algunos, pero no resuelve suelo, drenaje, calendario, variedad, manejo o sanidad parcelaria.

## B5 — Residuos regionales

No se repitió Moran. Las medias por estado y el ajuste condicionado por Y muestran si hay desplazamientos regionales aun sin autocorrelación residual global. Son diagnósticos OOF, no calibraciones. Una diferencia estatal puede reflejar distribución de Y, ambiente, manejo o tamaño muestral.

## B6 — Síntesis A+B

La matriz completa es `12_joint_hypothesis_matrix_A_B.csv`. Los patrones que mejoran comprensión son la compresión de extremos, el gradiente regional de Y y las trayectorias de duración. Las señales útiles para explicar región son clima, elevación/pendiente y TWI. Ninguna queda validada como incremento predictivo sobre Champion.

### Recomendación para fase C

Sí existe justificación concreta para una fase C, pero debe ser **adquisición dirigida**, no expansión indiscriminada: (1) fecha de siembra/cosecha y modalidad hídrica por parcela/ciclo; (2) textura, profundidad, drenaje, pH/materia orgánica y capacidad de retención por intersección parcelaria; (3) variedad/semilla; (4) fertilización y manejo; (5) afectaciones sanitarias. Sólo después se preespecificaría un experimento nested compacto.

## Conclusión

Bloque B distingue contexto regional de señal interna sin forzar causalidad. ENA contextualiza la producción, pero no cubre la unidad parcelaria necesaria. Champion permanece congelado: la evidencia actual mejora principalmente la explicación agronómica/regional, no demuestra una nueva mejora predictiva.
"""
 (REP/"block_b_technical_report.md").write_text(txt,encoding='utf-8')

if __name__=='__main__':main()
