"""Descriptive comparison of59 predictions and138 observed yields; no error tests."""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/'results/reference26_distribution/v1'
PRIVATE=ROOT/'outputs/research/reference26_distribution/v1'


def summary(values):
    s=pd.Series(values,dtype=float);q=s.quantile([.1,.25,.5,.75,.9])
    return dict(n=len(s),mean=s.mean(),median=q.loc[.5],std=s.std(ddof=1),minimum=s.min(),p10=q.loc[.1],q25=q.loc[.25],q75=q.loc[.75],p90=q.loc[.9],maximum=s.max(),range_width=s.max()-s.min(),iqr=q.loc[.75]-q.loc[.25],skew=s.skew(),n_unique=s.nunique(),below3=int((s<3).sum()),atleast5=int((s>=5).sum()))


def main():
    PUB.mkdir(parents=True,exist_ok=True);PRIVATE.mkdir(parents=True,exist_ok=True)
    paths=[ROOT/'data/processed/current_champions/v1/train138.parquet',ROOT/'outputs/modeling/current_champions_final/v1/predictions59_comparison.csv',ROOT/'outputs/modeling/current_champions_final/v1/Reference26_predictions59.csv']
    train=pd.read_parquet(paths[0]);pred=pd.read_csv(paths[1]);single=pd.read_csv(paths[2])
    assert len(train)==138 and len(pred)==len(single)==59
    assert not set(train.ID_POLIGONO)&set(pred.ID_POLIGONO)
    check=pred.merge(single,on='ID_POLIGONO',validate='one_to_one');np.testing.assert_allclose(check.Reference26_t_ha,check.RENDIMIENTO_T_HA,rtol=0,atol=1e-12)
    a=train[['Estado','Municipio','RENDIMIENTO_T_HA']].rename(columns={'RENDIMIENTO_T_HA':'value'}).assign(cohort='Observed138')
    b=pred[['Estado','Municipio','Reference26_t_ha']].rename(columns={'Reference26_t_ha':'value'}).assign(cohort='Predicted59')
    data=pd.concat([a,b],ignore_index=True);rows=[]
    for cohort,g in data.groupby('cohort'):
        rows.append(dict(scope='global',region='all',cohort=cohort,**summary(g.value)))
        for state,h in g.groupby('Estado'):rows.append(dict(scope='state',region=state,cohort=cohort,**summary(h.value)))
    descriptive=pd.DataFrame(rows);descriptive.to_csv(PUB/'descriptive_global_state.csv',index=False)
    municipality=pd.DataFrame([dict(Estado=state,Municipio=municipality,cohort=cohort,**summary(g.value)) for (state,municipality,cohort),g in data.groupby(['Estado','Municipio','cohort'])])
    municipality.to_csv(PRIVATE/'descriptive_municipality.csv',index=False)
    counts=data.groupby(['Estado','cohort']).value.size().unstack('cohort')
    means=data.groupby(['Estado','cohort']).value.mean().unstack('cohort')
    wt=counts.Observed138/138;wp=counts.Predicted59/59
    composition=counts.copy();composition['Observed138_share']=wt;composition['Predicted59_share']=wp
    composition['observed_mean']=means.Observed138;composition['predicted_mean']=means.Predicted59
    composition['difference_predicted_minus_observed']=means.Predicted59-means.Observed138
    composition.to_csv(PUB/'state_composition.csv')
    variance=[]
    for cohort,g in data.groupby('cohort'):
        grand=g.value.mean();total=np.mean((g.value-grand)**2)
        between=sum(len(h)/len(g)*(h.value.mean()-grand)**2 for _,h in g.groupby('Estado'))
        within=sum(len(h)/len(g)*np.mean((h.value-h.value.mean())**2) for _,h in g.groupby('Estado'))
        np.testing.assert_allclose(total,between+within,atol=1e-12)
        variance.append(dict(cohort=cohort,population_variance=total,between_state_variance=between,within_state_variance=within,between_state_share=between/total))
    variances=pd.DataFrame(variance);variances.to_csv(PUB/'variance_decomposition.csv',index=False)
    mix_effect=float(np.sum((wp-wt)*(means.Predicted59+means.Observed138)/2))
    conditional_effect=float(np.sum((wp+wt)/2*(means.Predicted59-means.Observed138)))
    difference=float(b.value.mean()-a.value.mean());np.testing.assert_allclose(mix_effect+conditional_effect,difference,atol=1e-12)
    decomposition=dict(global_mean_difference=difference,state_mix_component=mix_effect,within_state_mean_component=conditional_effect,
        predicted_mean_reweighted_to_training_state_mix=float(np.sum(wt*means.Predicted59)),
        caveat='Arithmetic cohort decomposition, not a causal effect or model bias estimate. Distinct parcels; no hidden outcomes.')
    (PUB/'mean_decomposition.json').write_text(json.dumps(decomposition,indent=2)+'\n',encoding='utf-8',newline='\n')
    fig,axes=plt.subplots(2,2,figsize=(11,8))
    for ax,zone in zip(axes.flat,['all','Hidalgo','Puebla','Tlaxcala']):
        subset=data if zone=='all' else data[data.Estado==zone]
        for cohort,g in subset.groupby('cohort'):
            values=np.sort(g.value.to_numpy());ax.step(values,np.arange(1,len(values)+1)/len(values),where='post',label=f'{cohort} (n={len(values)})')
        ax.set(title='Global' if zone=='all' else zone,xlabel='Rendimiento / estimación (t/ha)',ylabel='Proporción acumulada',ylim=(0,1.03));ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Reference26:59 estimaciones frente a138 rendimientos observados\nParcelas distintas; comparación descriptiva, no medición del error')
    fig.tight_layout();fig.savefig(PUB/'distribution_ECDF.png',dpi=160);plt.close(fig)
    with pd.ExcelWriter(PRIVATE/'distribucion_Reference26_59_vs_138.xlsx') as writer:
        for name,table in [('global_state',descriptive),('municipality',municipality),('state_mix',composition.reset_index()),('variance',variances)]:table.to_excel(writer,sheet_name=name,index=False)
    report(descriptive,composition,municipality,variances,decomposition)
    provenance=dict(n_observed=138,n_predictions=59,source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        code_sha256=hashlib.sha256(Path(__file__).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),std='sample ddof1',quantiles='pandas linear interpolation',
        weighting='equal weight per parcel, not hectares',target59_observed=False,new_training=0,hypothesis_tests=0,final_prediction_parity=True)
    (PUB/'audit.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(descriptive[['scope','region','cohort','n','mean','median','std','minimum','maximum']].to_string(index=False))
    print(json.dumps(decomposition,indent=2));print(variances.to_string(index=False))


def report(d,composition,municipal,variances,decomp):
    lookup=d.set_index(['scope','region','cohort']);obs=lookup.loc[('global','all','Observed138')];pred=lookup.loc[('global','all','Predicted59')]
    text='# Reference26: distribución de59 predicciones y138 rendimientos observados\n\n'
    text+='Las59 estimaciones pertenecen al champion26 final ajustado con138 rendimientos. **Los grupos contienen parcelas distintas; no conocemos los rendimientos verdaderos de59.** Comparar sus distribuciones no estima sesgo ni error. Cada parcela pesa igual, sin ponderación por hectáreas; desviación estándar muestral, cuantiles con interpolación lineal.\n\n'
    text+='## Comparación global\n\n| Estadístico | Observados138 | Predichos59 |\n|---|---|---|\n'
    for field,label in [('n','Parcelas'),('mean','Media'),('median','Mediana'),('std','Desviación estándar'),('minimum','Mínimo'),('p10','Percentil10'),('q25','Percentil25'),('q75','Percentil75'),('p90','Percentil90'),('maximum','Máximo'),('range_width','Amplitud del rango'),('iqr','Rango intercuartílico'),('atleast5','Parcelas con valor≥5')]:text+=f'| {label} | {obs[field]:.4f} | {pred[field]:.4f} |\n'
    text+=f"\nLa media cambia apenas{pred['mean']-obs['mean']:+.4f}t/ha y la mediana también es próxima. El rango predicho es **{pred['minimum']:.3f}–{pred['maximum']:.3f}**, frente a{obs['minimum']:.3f}–{obs['maximum']:.3f} observado. Su amplitud es{100*pred['range_width']/obs['range_width']:.1f}% de la observada y la desviación estándar es{100*(1-pred['std']/obs['std']):.1f}% menor. El IQR, en cambio, prácticamente coincide: no todas las medidas de dispersión se reducen por igual.\n\n"
    text+='No hay estimaciones≥5t/ha, frente a10/138 observadas. El centro se conserva y las colas son más moderadas. Media menor que mediana y la mezcla de estados muestran que una distribución normal única es una descripción incompleta; no se interpreta esto como prueba formal de multimodalidad.\n\n'
    text+='## Por estado\n\n| Estado | Grupo | n | Media | Mediana | SD | Mínimo | Máximo |\n|---|---|---|---|---|---|---|---|\n'
    for state in ['Hidalgo','Puebla','Tlaxcala']:
        for cohort in ['Observed138','Predicted59']:
            r=lookup.loc[('state',state,cohort)];text+=f"| {state} | {cohort} | {int(r['n'])} | {r['mean']:.3f} | {r['median']:.3f} | {r['std']:.3f} | {r['minimum']:.3f} | {r['maximum']:.3f} |\n"
    text+='\n**Puebla:** todas las parcelas de este estado son Chignahuapan en estos datos. Las medias son prácticamente iguales, pero las estimaciones evitan los extremos observados: SD.185 frente a.584. Es el cambio de dispersión más marcado, y no demuestra que las29 desconocidas deban tener la dispersión de las71 conocidas.\n\n'
    text+='**Hidalgo:** la media estimada es algo mayor y la mediana pasa de3.500 a4.303. La mezcla municipal importa: las59 incluyen allí4Almoloya,4Cuautepec y7Singuilucan; entre las36 conocidas hay10/5/16 respectivamente y5 de otros municipios. Las parcelas de Almoloya/Cuautepec pesan más en el grupo a estimar. La mayor mediana estatal no es evidencia de sobreestimación.\n\n'
    text+='**Tlaxcala:** los31 rendimientos conocidos sólo toman tres valores:2.5,3.0 y3.5. Las15 estimaciones son continuas y más cercanas al centro, con rango2.760–3.271 y media≈3.026. No deben redondearse automáticamente a esos tres niveles: no se ha establecido que sean las únicas respuestas posibles.\n\n'
    text+='## Municipios con soporte en ambos grupos\n\nSólo se muestran aquí grupos con al menos tres observaciones y tres predicciones. El Excel local contiene todos, incluidos grupos de una parcela; éstos no permiten describir de forma estable un municipio.\n\n| Municipio | n obs/pred | Media obs/pred | SD obs/pred | Rango predicho |\n|---|---|---|---|---|\n'
    for (state,name),g in municipal.groupby(['Estado','Municipio']):
        if set(g.cohort)!=set(['Observed138','Predicted59']):continue
        a=g[g.cohort=='Observed138'].iloc[0];b=g[g.cohort=='Predicted59'].iloc[0]
        if min(a['n'],b['n'])<3:continue
        text+=f"| {name} | {int(a['n'])}/{int(b['n'])} | {a['mean']:.3f}/{b['mean']:.3f} | {a['std']:.3f}/{b['std']:.3f} | {b['minimum']:.3f}–{b['maximum']:.3f} |\n"
    text+='\nNanacamilpa tiene sólo una observación conocida y una predicción: su diferencia no se generaliza al municipio.\n\n'
    text+='## Composición y dispersión entre estados\n\n| Estado | Proporción en138 | Proporción en59 |\n|---|---|---|\n'
    for state,r in composition.iterrows():text+=f'| {state} | {100*r.Observed138_share:.1f}% | {100*r.Predicted59_share:.1f}% |\n'
    text+=f"\nSi las medias predichas por estado se ponderaran con la composición de las138, la media sería{decomp['predicted_mean_reweighted_to_training_state_mix']:.4f}t/ha. La coincidencia global combina cambios que se compensan: componente de composición estatal{decomp['state_mix_component']:+.4f}t/ha y componente de diferencias de medias dentro de estados{decomp['within_state_mean_component']:+.4f}t/ha. Es una identidad aritmética, no descomposición causal ni sesgo.\n\n"
    for _,r in variances.iterrows():text+=f"- {r.cohort}: {100*r.between_state_share:.1f}% de la varianza poblacional se explica aritméticamente por diferencias entre las medias estatales.\n"
    text+='\nEsto explica por qué una SD global relativamente parecida puede ocultar estimaciones mucho más estrechas dentro de los estados. La SD estatal es una dispersión de parcelas, no incertidumbre de una predicción individual.\n\n'
    text+='## Interpretación y archivos\n\nUn modelo de regresión predice un valor central condicionado a sus entradas; sus predicciones no tienen por qué reproducir toda la variabilidad de resultados reales, que incluye ruido y factores no observados. Además aquí cambian las parcelas y sus características. **La cercanía de medias no prueba exactitud, y la menor dispersión no prueba por sí sola un defecto.** Para medir errores de extremos hay que usar OOF alineadas o esperar los59 rendimientos verdaderos. No se hicieron pruebas de igualdad de distribuciones ni se recalibraron los valores para hacerlos coincidir.\n\n'
    text+='![Distribuciones acumuladas globales y estatales](distribution_ECDF.png)\n\n'
    text+='[Descriptivos globales y estatales](descriptive_global_state.csv) · [Composición por estado](state_composition.csv) · [Varianza entre/dentro de estados](variance_decomposition.csv) · [Descomposición de medias](mean_decomposition.json) · [Auditoría y fuentes](audit.json). Excel local: `outputs/research/reference26_distribution/v1/distribucion_Reference26_59_vs_138.xlsx`. Reproducción: `python scripts/534_reference26_distribution.py`. [Modelo26](../../../documentation/models/Reference26/README.md) · [Predicciones finales](../../current_champions_final/v1/README.md).\n'
    (PUB/'README.md').write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':main()
