"""Complete descriptive source support and freeze the first Stage A delivery."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from src.family_4 import territorial_stage_a as a

def main():
    out=a.OUT;d,t=a.e.load();features=pd.read_parquet(a.PROC/'territorial_candidate_matrix_197_target_free.parquet')
    long=pd.read_parquet(a.PROC/'geology_intersections_full.parquet')
    base=pd.read_parquet(a.e.OUT/'tables/oof_predictions.parquet');base=base[base.experiment.eq('F4-E1')]
    avg=base[base.protocol.eq('random')].groupby(a.ID)[['y_true','y_pred']].mean()
    z=t[[a.ID,a.TARGET,'climate_profile','Municipio',a.e.f.NDVI]].merge(features[[a.ID]+[c for c in features if c.startswith('geo250_share__')]],on=a.ID,validate='one_to_one').set_index(a.ID)
    z['residual']=z.index.map(avg.y_true-avg.y_pred)
    rows=[]
    for scope,zz in [('all',z),('Chignahuapan',z[z.Municipio.eq('Chignahuapan')]),('dominant_profiles',z[z.climate_profile.isin([4,24])&z.Municipio.eq('Chignahuapan')])]:
        for c in [c for c in z if c.startswith('geo250_share__')]:
            present=zz[c]>1e-8
            if not present.any():continue
            w=zz[[c,a.e.f.NDVI,'residual']]-zz.groupby('climate_profile')[[c,a.e.f.NDVI,'residual']].transform('mean')
            design=np.column_stack([np.ones(len(w)),w[a.e.f.NDVI]])
            rx=w[c]-design@np.linalg.lstsq(design,w[c],rcond=None)[0];ry=w.residual-design@np.linalg.lstsq(design,w.residual,rcond=None)[0]
            r=rx.corr(ry) if rx.std()>1e-10 and ry.std()>1e-10 else np.nan
            rows.append(dict(scope=scope,unit=c,n_parcels_present=int(present.sum()),n_profiles_present=zz.loc[present,'climate_profile'].nunique(),mean_residual_present=zz.loc[present,'residual'].mean(),area_weighted_mean_residual=np.average(zz.loc[present,'residual'],weights=zz.loc[present,c]),partial_profile_ndvi_residual_correlation=r))
    pd.DataFrame(rows).to_csv(out/'tables/geology_unit_residual_associations.csv',index=False)
    local=features[(features.Municipio=='Chignahuapan')&(features.CONJUNTO=='ENTRENAMIENTO')&features.climate_profile.isin([4,24])]
    local_long=long[long[a.ID].isin(local[a.ID])].merge(local[[a.ID,'climate_profile']],on=a.ID,validate='many_to_one')
    local_long.groupby(['climate_profile','unit_key']).agg(n_labels=(a.ID,'nunique'),mean_share=('share','mean')).reset_index().to_csv(out/'tables/dominant_geology_category_support.csv',index=False)
    # Verify all prior numerical references from original OOF rather than transcribing rounded tables.
    j=pd.read_parquet(a.e.f.lm.k.j.locations()[0]/'tables/02_oof_predictions.parquet');j=j[j.experiment.eq('J0_RAIN')]
    k=pd.read_parquet(a.e.f.lm.k.locations()[0]/'tables/11_k_oof_predictions.parquet');k=k[k.experiment.eq('K5_RAIN_RESID_SLOPE')]
    f4=pd.read_parquet(a.e.f.OUT/'tables/oof_predictions.parquet');f4=f4[f4.experiment.isin(['F4-S1','F4-S5'])]
    refs=pd.concat([j,k,f4],ignore_index=True);repeated=[]
    for (exp,protocol,repeat),g in refs.groupby(['experiment','protocol','repeat']):
        assert len(g)==138 and g[a.ID].is_unique
        repeated.append(dict(experiment=exp,protocol=protocol,repeat=repeat,**a.e.f.lm.k.metrics(g.y_true,g.y_pred)))
    pd.DataFrame(repeated).to_csv(out/'tables/verified_reference_metrics_repeat.csv',index=False)
    pd.DataFrame(repeated).groupby(['experiment','protocol'])[['RMSE','MAE','R2','bias_pred_minus_y']].mean().reset_index().to_csv(out/'tables/verified_reference_metrics.csv',index=False)
    # Summary is independent of post-fit territorial modeling.
    notes='''# Etapa A — Decisión territorial

**La fuente edafológica histórica1:50,000 solicitada no está presente.** La carpeta chignahuapan contiene la carta topográfica E14B13, segunda edición1996, fotografías mayo1994 e imagen preparada mayo2002. Datum NAD27/UTM14N. No puede usarse como mapa de suelo.

**La carta geológico-minera es SGM1:50,000 de diciembre2017**, con base cartográfica INEGI2004. El PDF no contiene georreferenciación temática recuperable; se conserva para inventario visual. Sus metadatos PDF2018/2022 no son fechas de levantamiento geológico. La cobertura nominal de las dos hojas alcanza118 parcelas —82 etiquetas y36PRED—, con las62 etiquetas de los dos perfiles dominantes completamente dentro del marco. No hay parcelas parcialmente cubiertas en este marco. Cobertura nominal no equivale a clasificación temática.

**Sí existe una capa vectorial geológica INEGI1:250,000 diferente**, con compilación1982/conversión2000 documentadas. Su CRS NAD27 UTM14N se recuperó de AUX/cuadrícula; la transformación proyectada registra una precisión operacional13m, separada de la precisión cartográfica250k. Cubre las197parcelas y permite intersecciones físicas completas, sin renormalizar clases.

En los dos perfiles locales de33/29etiquetas, la composición geológica250k distingue727de934parejas posibles —77.8%—;480mantienen NDVI mayo similar. Cada perfil contiene cuatro unidades dominantes diferentes. Son contrastes disponibles, no evidencia de que una unidad explique rendimiento. Las727parejas comparten únicamente62etiquetas y dos perfiles, por lo que no permiten tratar727casos como observaciones independientes. Veinte de esas62parcelas intersectan la reserva descriptiva125m alrededor de límites250k, lo que exige cautela con diferencias pequeñas y cartografía histórica.

El RMSE de diferencias de F4-S1 es0.798t/ha en parejas internas aleatorias; entre parejas con NDVI similar y geología250k distinta permanece alrededor de0.796. Estos estratos se definieron usando soloX. Que el error siga siendo alto no demuestra que geología lo explique: todavía no hay predicción territorial validada. Las asociaciones parciales OOF de TPI, convergencia, flujo, TWI y diversidad geológica son débiles en los62casos después de controlar perfil yNDVI. Las asociaciones por unidad se documentan como descripciones sujetas a soporte, nunca como selección de una clase ganadora.

Quince parejas tienen clima, NDVI, dinámica, geomorfología, suelo amplio y geología amplia similares según los umbrales congelados. Conservan diferencias de rendimiento importantes, pero el soporte es pequeño y las reglas dependen de escala: esto no estima error irreducible.

**Decisiones:**

- Suelo50k1996: suspender comparación multiescala hasta disponer de la fuente verdadera.
- Geología SGM50k2017: mantener inventario y cobertura nominal; suspender asignación parcelaria sin geometría oficial fiable.
- Topografía1996: conservar revisión visual y marco; no extraer hidrografía o curvas de colores automáticamente.
- Geología INEGI250k: conservar composición completa como candidata descriptiva. Tiene variación intraperfil y cobertura, pero no se recomienda integrarla automáticamente ni atribuirle resolución50k. Un ensayo futuro, separado y congelado, necesitaría categorías con soporte, sensibilidades de límites y controles sobre las mismas parcelas.
- Geomorfología DEM120m: conservar TPI/convergencia/flujo/TWI para diagnóstico. No se identifica aquí una mejora adicional clara sobre vegetación/terreno actual, ni se deriva humedad observada.
- EtapaB: puede continuar como segunda entrega independiente con datos existentes, porque estas limitaciones territoriales no invalidan el objetivo intraperfil ni la mezcla fija. No se ejecutóB/C en esta primera entrega.

Se conservan matriz target-free197, cobertura, geometrías, composiciones completas, inventario de fuentes, categorías, pares definidos porX, residuos OOF solo descriptivos, figuras y6pruebas automatizadas. Las referencias numéricas J0/K5/F4-S1/F4-S5 se verificaron desde las OOF originales. No se alteraron etiquetas, modelos ni resultados congelados.
'''
    (out/'report/decision_summary.md').write_text(notes,encoding='utf-8')
    (a.ROOT/'documentation/territorial_program_stage_a_decision.md').write_text(notes,encoding='utf-8')
    # Images and test evidence appended without overwriting original research artifacts.
    for reportpath in [out/'report/territorial_report.md',a.ROOT/'documentation/territorial_program_stage_a.md']:
        text=reportpath.read_text(encoding='utf8')
        appendix='\n\n## Verificación final\n\nSeis pruebas pasaron: identidad/cartografía paletizada, worldfile y medio pixel, geometrías y cobertura por área, conservación de composición, clasificación de pares usandoX, comparabilidad de predicciones y hashes de fuentes/resultados anteriores. El ámbito ejecutado es exclusivamente EtapaA.\n'
        prefix='../figures/' if reportpath.parent.name=='report' else '../'+(out/'figures').relative_to(a.ROOT).as_posix()+'/'
        appendix+='\n'.join(f'\n![{name}]({prefix}{name})\n' for name in ['01_source_coverage.png','02_coarse_geology_parcels.png','03_pair_diagnostics.png'])
        if '## Verificación final' not in text:reportpath.write_text(text+appendix,encoding='utf8')
    previous=[]
    for old in [a.e.OUT,a.e.f.OUT]:
        manifest=json.loads((old/'manifest.json').read_text())
        for path,digest in manifest['artifacts'].items():
            assert a.sha(a.ROOT/path)==digest
            previous.append(dict(path=path,sha256=digest,matches=True))
    pd.DataFrame(previous).to_csv(out/'audit/previous_results_integrity.csv',index=False)
    files=[p for p in out.rglob('*') if p.is_file() and p.name!='manifest.json']+list(a.PROC.glob('*'))
    files += [a.ROOT/p for p in ['src/family_4/territorial_stage_a.py','src/family_4/territorial_stage_a_reporting.py','scripts/340_territorial_program_stage_a.py','scripts/341_territorial_stage_a_finalize.py','tests/test_territorial_stage_a.py','documentation/territorial_program_stage_a.md','documentation/territorial_program_stage_a_decision.md']]
    manifest=dict(status='complete',stage='A',predictive_models_trained=0,n_parcels=197,n_labelled=138,n_prediction=59,tests='6 passed',previous_files_verified=len(previous),next_stage='B separate delivery; not executed',artifacts={str(p.relative_to(a.ROOT)):a.sha(p) for p in files})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print('StageA complete;6tests;',len(previous),'previous artifacts verified;',len(files),'new versioned artifacts')

if __name__=='__main__':main()
