"""Diagnóstico no supervisado y reporte contestado de Etapa 3."""
from pathlib import Path
import sys,json
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
from family_1.feature_pipeline import OUT,AUD,ID
AUD.mkdir(parents=True,exist_ok=True)
blocks={p.stem:p for p in OUT.glob('*features*.parquet') if p.name!='family1_features_all.parquet'}
summary=[]; miss=[]; high=[]; near=[]
for name,p in blocks.items():
 d=pd.read_parquet(p); num=d.drop(columns=ID).select_dtypes('number')
 summary.append({'block':name,'rows':len(d),'features':d.shape[1]-1,'mean_missing_pct':100*num.isna().mean().mean(),'max_missing_pct':100*num.isna().mean().max()})
 for c in num: miss.append({'block':name,'feature_name':c,'missing_n':num[c].isna().sum(),'missing_pct':100*num[c].isna().mean(),'finite_n':np.isfinite(num[c]).sum()})
 scale=num.std(); means=num.mean().abs();
 for c in num.columns[(scale<=1e-10)|(scale/(means+1e-12)<=1e-8)]: near.append({'block':name,'feature_name':c,'std':scale[c],'mean':num[c].mean()})
 corr=num.corr(min_periods=20); a=np.triu(np.ones(corr.shape,dtype=bool),1); ix=np.where(a&(corr.abs().to_numpy()>.98))
 for i,j in zip(*ix): high.append({'block':name,'feature_1':corr.index[i],'feature_2':corr.columns[j],'correlation':corr.iloc[i,j]})
 corr.to_csv(AUD/f'correlation_{name}.csv')
pd.DataFrame(summary).to_csv(AUD/'feature_count_and_missingness_by_block.csv',index=False)
pd.DataFrame(miss).to_csv(AUD/'feature_missingness.csv',index=False);pd.DataFrame(near).to_csv(AUD/'near_constant_features.csv',index=False);pd.DataFrame(high).to_csv(AUD/'high_correlation_pairs.csv',index=False)
master=pd.read_parquet(OUT/'family1_features_all.parquet'); elim=pd.read_csv(AUD/'feature_eliminations.csv'); counts=pd.DataFrame(summary)
master.drop(columns=ID).describe(percentiles=[.01,.1,.25,.5,.75,.9,.99]).T.to_csv(AUD/'feature_distribution_summary.csv')
cross=[]
for pc in [c for c in master if c.startswith('PLANET_')]:
 sc='S2_'+pc[len('PLANET_'):]
 if sc in master:
  pair=master[[sc,pc]].dropna()
  if len(pair)>=20: cross.append({'sentinel_feature':sc,'planet_feature':pc,'n':len(pair),'correlation':pair[sc].corr(pair[pc])})
cross_df=pd.DataFrame(cross)
if not cross_df.empty: cross_df=cross_df.sort_values('correlation',key=lambda x:x.abs(),ascending=False)
cross_df.to_csv(AUD/'sentinel_planet_descriptive_correlations.csv',index=False)
events=[]
for suffix in ['peak_day','max_growth_rate','max_decline_rate','max_drawdown','max_runup','pre_peak_slope','post_peak_slope']:
 cs=[c for c in master if c.endswith(suffix)]
 events.append({'event_or_statistic':suffix,'n_features':len(cs),'mean_calculable_pct':100*master[cs].notna().mean().mean() if cs else np.nan})
pd.DataFrame(events).to_csv(AUD/'temporal_event_coverage.csv',index=False)
(AUD/'temporal_feature_configuration.json').write_text(json.dumps({'window_start':'2025-04-01','default_eos':'2025-10-31','prepared_cutoffs':['2025-06-30','2025-07-31','2025-08-31','2025-09-30','2025-10-31'],'timing_unit':'days_from_window_start','auc':'trapezoidal_actual_days','no_global_interpolation':True,'sentinel_cv_abs_mean_threshold':0.05,'historical_std_threshold':1e-6},indent=2),encoding='utf-8')
def n(prefix): return sum(c.startswith(prefix) for c in master.columns)
def pct_calc(prefix,stat):
 cs=[c for c in master if c.startswith(prefix) and c.endswith(stat)]; return 100*master[cs].notna().mean().mean() if cs else np.nan
dictionary=pd.read_csv(OUT/'family1_feature_dictionary.csv'); included=dictionary[dictionary.included_in_master.fillna(False)]
level_counts=included.core_or_extended.value_counts().to_dict()
slope=pd.read_parquet(OUT/'topography_basic_features.parquet'); classes=[c for c in slope if 'pct_area_slope' in c]
report=f"""# Familia 1 — Etapa 3: reporte de features sin target

## Resumen ejecutivo

Se construyó una tabla de **{len(master)} parcelas × {master.shape[1]-1} features**, con ID único y sin rendimiento. Las fechas reales se usan en pendientes, AUC y tasas; no se interpolaron series. CORE y EXTENDED permanecen separados y los cutoffs futuros pueden reproducirse cambiando el final de ventana sin mirar datos posteriores.

## Respuestas a las preguntas de la etapa

1. **Features por fuente/bloque.** {counts[['block','features']].to_dict('records')}.
2. **CORE estables.** Nivel, cuantiles, AUC normalizada, slope, bordes y eventos son calculables cuando existen ≥2 observaciones; cobertura media no faltante de CORE Sentinel: {100-master[[c for c in master if c.startswith('S2_')]].isna().mean().mean():.1f}%.
3. **Pico, crecimiento y caída.** El pico requiere ≥1 dato; crecimiento/caída requieren ≥2 fechas distintas. Se registra timing en días desde 2025-04-01, evitando strings de fecha en la matriz.
4. **Pre/post-peak slope.** Calculabilidad promedio: pre {pct_calc('S2_','pre_peak_slope'):.1f}% y post {pct_calc('S2_','post_peak_slope'):.1f}% de parcela-serie.
5. **Drawdown/runup.** Son matemáticamente estables con ≥2 puntos, pero su comparabilidad depende de densidad/cobertura; se deben acompañar por n_obs y gaps.
6. **Heterogeneidad Sentinel.** std, range, lower/upper gap son utilizables. CV se recalculó sólo con |media|≥0.05; fuera de ello queda NaN para evitar explosiones silenciosas.
7. **Landsat robusto.** Mediana/cuantiles, AUC normalizada, slope con días reales, extremos, n válido, fracción válida y gaps; sin interpolación.
8. **Sentinel vs Planet.** Se conservaron como sensores distintos. Hay {sum(abs(r['correlation'])>.98 for r in cross)} pares homólogos con |r|>0.98 de {len(cross)} comparables; están en `sentinel_planet_descriptive_correlations.csv`. No se eliminó por correlación ni se usó rendimiento.
9. **Clima redundante.** El CORE usa sólo medias espaciales mensuales; min/max/median/std espaciales se excluyen porque la resolución gruesa suele producir un píxel efectivo por parcela.
10. **Histórico.** Para cada parcela y mes calendario abril-octubre se calculó baseline exclusivamente con 2022-2024; luego se resume por variable.
11. **Anomalías.** Absolutas son estables; estandarizadas sólo se calculan con std histórica≥1e-6 e incluyen `unstable_fraction`.
12. **Topografía.** Elevación y pendiente incluyen cuantiles ponderados, dispersión y relieve; consultar los parquets y diagnósticos para rangos.
13. **Clases de pendiente.** Cortes configurables 0–2, 2–5, 5–10, >10°. Desviaciones entre parcelas: {slope[classes].std().round(2).to_dict()}; sus porcentajes suman aproximadamente 100%.
14. **Aspect/TPI/curvatura.** Sí. Aspect se representa como sin/cos; TPI/relieve usan vecindad 3×3; curvaturas usan derivadas del DEM y se reportan por signo sin imponer interpretación universal.
15. **Flow direction/accumulation.** Sí, D8 después de llenar pits/depresiones y resolver planos, sobre el DEM entregado completo, sin recortes por parcela ni buffer arbitrario.
16. **TWI.** Se calculó como `ln((accumulation_cells × cellsize) / max(tan(slope), 1e-6))`; es defendible como índice estructural relativo dentro del DEM, no como humedad medida.
17. **Limitaciones hidrológicas.** El borde del raster desconoce aportes externos; resolución 120 m; el acondicionamiento y D8 simplifican el flujo; lluvia y topografía siguen separadas; TWI no valida escurrimiento ni humedad.
18. **CORE vs EXTENDED.** Conteo exacto de features incluidas según el catálogo: {level_counts}. Los archivos Sentinel CORE y EXTENDED permanecen separados.
19. **Duplicadas por construcción.** Se eliminaron {sum(elim.reason=='exact_duplicate')} duplicados exactos y {sum(elim.reason=='constant_or_all_missing')} constantes/all-missing; detalle en `feature_eliminations.csv`. Correlación alta no implicó eliminación.
20. **Lista para modelado.** Sí como matriz no supervisada de 197 filas e ID único. Antes de entrenar hay que unir target externamente, definir validación, estrategia de missingness y controlar dimensionalidad dentro de cada fold.

## Decisiones antes de modelado supervisado

- Definir EOS frente a cutoffs tempranos y recalcular todos los bloques con el mismo cutoff.
- Diseñar validación que respete la estructura espacial y sólo entonces ajustar imputación/selección.
- Elegir CORE inicial dado el número reducido de parcelas con target y evaluar EXTENDED como ablation.
- Tratar correlaciones >0.98 y eventos con baja cobertura dentro de folds, nunca usando todo el target para seleccionar.
- No interpretar flow accumulation/TWI como mediciones de agua; interacciones clima×terreno requieren una etapa posterior y validación explícita.
"""
(AUD/'family1_feature_report.md').write_text(report,encoding='utf-8')
(AUD/'feature_diagnostics_manifest.json').write_text(json.dumps({'rows':len(master),'features':master.shape[1]-1,'id_unique':master[ID].is_unique,'target_used':False,'infinite_values':int(np.isinf(master.select_dtypes('number')).sum().sum())},indent=2),encoding='utf-8')
print(f'Reporte generado: {AUD / "family1_feature_report.md"}')
