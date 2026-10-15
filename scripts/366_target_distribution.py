"""Descriptive target audit only; no models, target edits or PRED inference."""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/research/target_distribution/v1'
def main():
    if (OUT/'manifest.json').exists():raise FileExistsError('Completed target analysis immutable')
    for d in ['tables','figures','report']:(OUT/d).mkdir(parents=True,exist_ok=True)
    source=ROOT/'outputs/modeling/family_7/expansion/v1/cache/train138_exact_features.parquet'
    master=ROOT/'data/original/01_tablas_maestras/ID_area_rendimiento_70_30_Reto_AgroCebada.csv'
    t=pd.read_parquet(source);raw=pd.read_csv(master).set_index('ID_POLIGONO')
    y=t.RENDIMIENTO_T_HA
    np.testing.assert_allclose(y,raw.RENDIMIENTO_T_HA.reindex(t.ID_POLIGONO),atol=0,rtol=0)
    assert len(t)==138 and t.ID_POLIGONO.is_unique and y.notna().all() and (y>0).all()
    summary=y.describe(percentiles=[.05,.1,.25,.5,.75,.9,.95]).to_dict()
    q1,q3=y.quantile([.25,.75]);summary.update(skew=float(y.skew()),n_unique=y.nunique(),n_missing=int(y.isna().sum()),IQR=float(q3-q1),Tukey_lower=float(q1-1.5*(q3-q1)),Tukey_upper=float(q3+1.5*(q3-q1)),n_Tukey_global=int(((y<q1-1.5*(q3-q1))|(y>q3+1.5*(q3-q1))).sum()),n_below3=int(y.lt(3).sum()),n_3_to5_inclusive=int(y.between(3,5).sum()),n_above5=int(y.gt(5).sum()),descriptive_mean_prediction_RMSE=float(np.sqrt(np.mean((y-y.mean())**2))))
    pd.DataFrame([summary]).to_csv(OUT/'tables/target_summary.csv',index=False)
    for field in ['Estado','Municipio']:
        rows=[]
        for value,g in t.groupby(field):
            a=g.RENDIMIENTO_T_HA
            rows.append(dict(group=value,n=len(g),mean=a.mean(),median=a.median(),std_sample=a.std(),min=a.min(),max=a.max(),n_unique=a.nunique(),n_half_ton_steps=int(np.isclose(2*a,np.round(2*a)).sum())))
        pd.DataFrame(rows).to_csv(OUT/'tables'/f'target_by_{field}.csv',index=False)
    counts=t.groupby(['Estado','RENDIMIENTO_T_HA']).size().rename('n').reset_index();counts.to_csv(OUT/'tables/recorded_value_frequencies.csv',index=False)
    profiles=t.groupby('climate_profile').RENDIMIENTO_T_HA.agg(n='size',mean='mean',std_sample='std',min='min',max='max').reset_index();profiles['range']=profiles['max']-profiles['min'];profiles['n_pairs']=profiles.n*(profiles.n-1)//2
    profiles.to_csv(OUT/'tables/target_by_profile.csv',index=False)
    means=t.groupby('climate_profile').RENDIMIENTO_T_HA.transform('mean');within=float(np.sum((y-means)**2));total=float(np.sum((y-y.mean())**2))
    decomposition=dict(within_TSS=within,total_TSS=total,within_fraction=within/total,between_fraction=1-within/total,n_profiles=len(profiles),n_repeated_profiles=int(profiles.n.ge(2).sum()),role='Full-label descriptive decomposition; not OOF explained variance, causal climate attribution or operational training targets')
    (OUT/'tables/profile_decomposition.json').write_text(json.dumps(decomposition,indent=2),encoding='utf8')
    local=[]
    for field in ['Estado','Municipio']:
        for group,g in t.groupby(field):
            if len(g)<10:continue
            a,b=g.RENDIMIENTO_T_HA.quantile([.25,.75]);lo=a-1.5*(b-a);hi=b+1.5*(b-a)
            for row in g[(g.RENDIMIENTO_T_HA<lo)|(g.RENDIMIENTO_T_HA>hi)].itertuples():local.append(dict(group_type=field,group=group,ID_POLIGONO=row.ID_POLIGONO,y=row.RENDIMIENTO_T_HA,lower_fence=lo,upper_fence=hi,action='descriptive flag only; no deletion or target change'))
    pd.DataFrame(local).to_csv(OUT/'tables/local_distribution_flags.csv',index=False)
    fig,axs=plt.subplots(1,3,figsize=(15,4.5))
    bins=np.arange(1.875,5.876,.25)
    axs[0].hist(y,bins=bins,color='#2c7a7b',edgecolor='white');axs[0].axvline(y.mean(),color='black',ls='--',label=f'Media {y.mean():.2f}');axs[0].axvline(y.median(),color='#b83280',ls=':',label=f'Mediana {y.median():.2f}');axs[0].set(title='138 rendimientos observados',xlabel='Rendimiento (t/ha)',ylabel='Parcelas');axs[0].legend(fontsize=8)
    colors={'Puebla':'#2c7a7b','Hidalgo':'#dd6b20','Tlaxcala':'#805ad5'}
    for state,g in t.groupby('Estado'):axs[1].hist(g.RENDIMIENTO_T_HA,bins=bins,histtype='step',lw=2,label=f'{state} (n={len(g)})',color=colors[state])
    axs[1].set(title='Distribuciones por estado',xlabel='Rendimiento (t/ha)',ylabel='Parcelas');axs[1].legend(fontsize=8)
    repeated=profiles[profiles.n.ge(2)].sort_values('n',ascending=False)
    for position,row in enumerate(repeated.itertuples()):
        vals=t.loc[t.climate_profile.eq(row.climate_profile),'RENDIMIENTO_T_HA'].to_numpy();offset=np.linspace(-.12,.12,len(vals));axs[2].scatter(np.full(len(vals),position)+offset,vals,s=14,alpha=.6,color='#2c7a7b')
    axs[2].set(xticks=range(len(repeated)),xticklabels=[f'{p}\n(n={n})' for p,n in zip(repeated.climate_profile,repeated.n)],title='Variación en perfiles climáticos repetidos',xlabel='Perfil (identificador diagnóstico)',ylabel='Rendimiento (t/ha)');axs[2].tick_params(axis='x',labelsize=7)
    fig.tight_layout();fig.savefig(OUT/'figures/target_distribution.png',dpi=170);plt.close(fig)
    report=f'''# Análisis de la variable objetivo — Rendimiento

Se usa RENDIMIENTO_T_HA, rendimiento por superficie (t/ha), no producción total.138 etiquetas se verifican exactamente contra el archivo maestro original. No hay vacíos, ceros ni negativos entre esas138;59 parcelas sin etiqueta se mantienen fuera del análisis. No se ajustan modelos ni cambian datos.

Media {y.mean():.3f}; mediana {y.median():.3f}; desviación estándar muestral {y.std():.3f}; mínimo {y.min():.2f}; máximo {y.max():.2f}. Q1={q1:.2f}, Q3={q3:.2f}, IQR={q3-q1:.2f};67 valores distintos. Asimetría {y.skew():.3f}: leve hacia valores bajos, no una única población regional homogénea.114/138 parcelas (82.6%) están entre3 y5 inclusive;14 están por debajo de3 y10 por encima de5. Percentiles y frecuencias se conservan en tablas.

Puebla:71 parcelas, media4.477 y mediana4.52; todas corresponden a Chignahuapan. Hidalgo:36, media3.763; Tlaxcala:31, media2.984. Las diferencias pueden mezclar ambiente, manejo, muestreo y medición; no identifican efectos estatales ni climáticos. Municipios de1–5 parcelas no sostienen comparaciones poblacionales robustas.

Tlaxcala registra exclusivamente2.5/3.0/3.5 (9/14/8 parcelas); Puebla54 valores distintos y solo1/71 en incrementos de0.5. Hidalgo21 valores distintos y13/36 en pasos de0.5. Esto sugiere auditar precisión, redondeo y método de obtención del rendimiento por fuente; no demuestra que sean estimaciones ni autoriza corregir labels. Los modelos aprenden valores registrados con distintas granularidades. El promedio por parcela no equivale al promedio ponderado por hectáreas.

No hay extremos por regla global de Tukey1.5IQR: límites1.175 y6.575. Ello no elimina casos difíciles locales. En Chignahuapan la regla regional marca ocho valores bajos (<3.9275), entre ellos AGC_171=2.15 y AGC_015=2.64. Son flags descriptivos conservados, no errores comprobados ni motivos de eliminación. Máximo AGC_162=5.59, en Chignahuapan.

Perfil24:34 parcelas, rango2.15–5.57; perfil4:29, rango2.64–5.59. Vectores climáticos iguales conviven con diferencias grandes de rendimiento. La descomposición descriptiva deja25.55% de TSS dentro de perfiles y74.45% entre sus medias; estas medias usan todos los labels de cada perfil, por lo que NO significan que un modelo climático explique74.45% en validación ni que el clima cause esa proporción. No llamar ruido irreducible a la heterogeneidad restante.

Implicaciones: priorizar evaluación municipal/espacial además de aleatoria; revisar sesgo en rendimientos bajos y ambos extremos; evaluar diferencias intraperfil y error absoluto por separado; auditar granularidad regional de medición. No construir reglas con cuartiles observados de validación, ni normalizar y por estado usando labels retenidos. La escala positiva y asimetría leve no justifican por sí solas log-transformar; cualquier transformación futura debe ajustarse dentro de entrenamiento y evaluarse tras invertir a t/ha, con controles de sesgo de inversión. No se ejecuta esa sensibilidad aquí.

![Distribución y perfiles](../figures/target_distribution.png)
'''
    (OUT/'report/target_analysis.md').write_text(report,encoding='utf8')
    # Local documentation link uses a path relative to its own directory.
    (ROOT/'documentation/target_analysis.md').write_text(report.replace('../figures/target_distribution.png','../outputs/research/target_distribution/v1/figures/target_distribution.png'),encoding='utf8')
    def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    files=[p for p in OUT.rglob('*') if p.is_file()]+[Path(__file__),ROOT/'documentation/target_analysis.md']
    manifest=dict(status='complete',n_labels=138,models_trained=0,targets_modified=False,PRED_predictions=False,source_hashes={p.relative_to(ROOT).as_posix():digest(p) for p in [source,master]},artifacts={p.relative_to(ROOT).as_posix():digest(p) for p in files})
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
