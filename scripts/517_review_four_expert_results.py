"""Final numerical review and data-specific interpretation; no training."""
from pathlib import Path
import sys,json,hashlib,re
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.four_expert_combinations import OUT,OLD
from src.architecture_decomposition import load_design as architecture_design

def digest(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def main():
    audit=json.loads((OUT/'delivery_audit.json').read_text());assert audit['status']=='complete' and audit['interpretation_complete'];assert all(digest(f)==h for f,h in audit['artifact_sha256'].items() if Path(f).resolve()!=Path(__file__).resolve())
    p=pd.read_parquet(OUT/'tables/oof_residuals.parquet');z=p.pivot(index=['protocol','repeat','fold','ID_POLIGONO'],columns='experiment',values='y_pred');assert len(z)==2450;checks=[]
    for name,components in [('B1',['CT3','Reference26']),('B2',['CT3','Compact14']),('B3',['Reference26','L40']),('B4',['CT3','Reference26','L40']),('B5',['CT3','Reference26']),('B6',['Reference26','L40'])]:
        violation=float(np.maximum.reduce([z[components].min(axis=1).to_numpy()-z[name].to_numpy(),z[name].to_numpy()-z[components].max(axis=1).to_numpy(),np.zeros(len(z))]).max());assert violation<1e-12;checks.append(dict(experiment=name,n=len(z),max_bound_violation=violation))
    pd.DataFrame(checks).to_csv(OUT/'audit/convex_prediction_bounds.csv',index=False);profiles=z.loc['climate_profile'];assert np.max(abs(profiles.B2-profiles.Compact14))<1e-12
    path=OLD/'cache/groups.csv';old=architecture_design()['source_sha256'];expected=old.get(str(path.resolve()));actual=digest(path)
    if expected is not None:assert expected==actual
    group_review=dict(path=str(path),sha256=actual,matched_architecture_frozen_hash=expected==actual if expected is not None else None);(OUT/'audit/spatial_groups_source.json').write_text(json.dumps(group_review,indent=2))
    manifest=[]
    for f in sorted((OUT/'models').glob('*.joblib')):manifest.append(dict(path=str(f.relative_to(ROOT)),bytes=f.stat().st_size,sha256=digest(f)))
    assert len(manifest)==81;pd.DataFrame(manifest).to_csv(OUT/'audit/model_artifact_sha256.csv',index=False)
    m=pd.read_csv(OUT/'tables/metrics.csv').set_index(['experiment','protocol']);get=lambda name,pro,metric:float(m.loc[(name,pro),metric]);fresh_gain=get('Reference26','fresh_97_41','rmse')-get('B1','fresh_97_41','rmse')
    gains=pd.read_csv(OUT/'tables/parcel_gains.csv');cross=pd.read_csv(OUT/'tables/spatial_fold_block_crosswalk.csv');calpu=str(cross[cross.municipalities.str.contains('Calpulalpan',regex=False)].spatial_block.iloc[0]);blockmap=pd.read_csv(path).set_index('ID_POLIGONO').spatial.astype(str);loss=gains[(gains.protocol=='spatial')&(gains.experiment=='B6')&(gains.reference=='Reference26')].copy();loss['block']=loss.ID_POLIGONO.map(blockmap);share=float(loss[loss.block==calpu].mse_gain.sum()/loss.mse_gain.sum());om=pd.read_csv(OUT/'tables/actual_block_omissions.csv');remaining=om[(om.protocol=='spatial')&om.omitted_spatial_block.astype(str).eq(calpu)].set_index('experiment');tests=pd.read_csv(OUT/'tables/paired_tests.csv');assert not ((tests.reference=='Reference26')&(tests.p_holm<.05)).any()
    section=f'''\n<!-- FINAL_REVIEW_START -->
## Lectura final revisada

Recomendación: conservar Reference26 como referencia de precisión y Compact14 sin otra mezcla como alternativa de menor complejidad de datos. No incorporaría L40 mediante B3/B4/B6 ni promovería una nueva mezcla con esta evidencia. Reference26 ya contiene un experto Ridge local con24 vecinos geográficos: añadir L40 evalúa principalmente su representación C4 completa, no la utilidad de los vecinos por primera vez.

La mezcla constante C-T3/26 (B1) mejora municipal de .5752 a .5681 t/ha, pero pierde por perfil (.4774→.4839) y espacial (.6333→.6813). La variante condicional B5 no elimina ese deterioro. En el banco nuevo97/41, B1 mejora sólo {fresh_gain:.6f} t/ha de RMSE, aproximadamente {1000*fresh_gain:.2f} kg/ha. No es evidencia de una mejora relevante ni estadísticamente demostrada frente a Reference26. En ese mismo banco, Reference26 obtiene .4625/.6971 RMSE/R², frente a .4893/.6621 de L40. Este contraste se hace en las mismas particiones, sin mezclar el banco histórico de GeoC.

La ganancia municipal de B1 se concentra en Emiliano Zapata y Singuilucan; Chignahuapan y Calpulalpan quedan sin cambio y varios municipios empeoran. En espacial, en cambio, Singuilucan empeora de .6611 con Reference26 a .8247 con B1. La ventaja por municipio cambia con el escenario de validación y no respalda reglas fijas con nombres de municipios.

### El objetivo de conservar el centro y mejorar extremos

En las diez repeticiones aleatorias completas, C-T3 mantiene {100*get('CT3','random','within_05'):.2f}% dentro de±.5 t/ha, Reference26 {100*get('Reference26','random','within_05'):.2f}% y B1 {100*get('B1','random','within_05'):.2f}%. La pequeña recuperación frente a Reference26 no alcanza C-T3. El percentil95 absoluto pasa de {get('Reference26','random','p95_absolute'):.4f} a {get('B1','random','p95_absolute'):.4f}: la cola empeora ligeramente.

En espacial, Reference26 y B1 quedan ambos en55.07% dentro de±.5, por debajo del59.42% de C-T3. El percentil95 empeora de1.2538 a1.4223 t/ha al mezclar. Las ventajas no se combinan de manera consistente. Un mayor porcentaje dentro de una tolerancia no significa necesariamente mejor predicción de rendimientos próximos a la media; son ejes de análisis distintos. Se entregan ambos diagnósticos en level_bins.csv.

### Qué ocurre con L40

L40 conserva fortalezas descriptivas en Almoloya y Cuautepec. Pero B3 y B6 asignan peso cero a L40 en la evaluación espacial de Almoloya, perdiendo esa oportunidad. En Calpulalpan el RMSE pasa de .8125 con Reference26 a1.0513 con B3 y1.0581 con B6. El selector no reconoció de forma transferible dónde convenía L40.

El bloque que contiene Calpulalpan concentra {100*share:.1f}% del aumento de SSE espacial de B6 frente a Reference26. Al omitir ese bloque del cómputo, sin reajustar, RMSE queda {remaining.loc['Reference26','rmse']:.4f} para Reference26 y {remaining.loc['B6','rmse']:.4f} para B6: desaparece casi toda la pérdida grande, pero no aparece una ventaja general. Esta omisión es un diagnóstico de concentración, no una nueva validación ni una justificación para excluir parcelas.

Ese bloque contiene las31 parcelas etiquetadas de Tlaxcala y cuatro de Hidalgo. Por tanto, evalúa extrapolación con Tlaxcala completamente ausente del entrenamiento externo. El banco97/41 evalúa otro escenario: faltantes aleatorios dentro del mismo conjunto de parcelas. Ambos escenarios se conservan separados.

### Pesos y soporte

Los pesos son constantes dentro de cada modelo entrenado, no iguales entre todos los folds. Por eso una mezcla puede quedar peor que ambos extremos en la métrica agregada si selecciona al experto menos conveniente en distintos territorios. Se verificaron los límites convexos en las2,450 observaciones OOF por modelo: no es un error aritmético ni una mezcla fuera de[0,1].

En espacial, B1 conserva Reference26 en los dos bloques predominantemente de Chignahuapan, pero cambia a C-T3 en los bloques1 y3, precisamente donde Reference26 aporta ventajas. B3 asigna aproximadamente41.2% a L40 en el bloque1. Allí el desacuerdo RMS entre L40 y Reference26 pasa de .1793 en las predicciones internas a .8762 en las externas (4.89 veces). Este cambio y los pesos que no transfieren son compatibles con un problema de calibración bajo cambio territorial y tamaños de entrenamiento distintos. No prueban una causa única. Los cinco pesos B1 sí estaban identificados por diferencias internas no nulas; no se atribuye el resultado a un empate exacto.

La etiqueta espacial3 original corresponde al fold4: Singuilucan, Cuautepec y Tepeapulco. El fold3 corresponde a la etiqueta1, que contiene Calpulalpan y otros municipios. La correspondencia completa está en spatial_fold_block_crosswalk.csv y usa las etiquetas originales, sin renumerarlas.

### Alcance estadístico y siguiente paso

Ninguna comparación de las nuevas mezclas contra Reference26 supera Holm. El único contraste significativo de los130 es B2 frente a C-T3 por perfil; en ese protocolo B2 coincide exactamente con Compact14, por lo que recupera una ventaja ya existente del control, no una mejora nueva por mezclar. La falta de significación no demuestra equivalencia: con cinco bloques el test exacto bilateral no puede dar p menor de .0625.

Detendría esta batería sin añadir reglas regionales ni nuevos pesos elegidos retrospectivamente sobre estas OOF. Priorizaría cerrar la presentación reproducible del modelo26, mantener14 como opción compacta y buscar confirmación con nuevas respuestas para sostener afirmaciones de superioridad. Los resultados debilitan estas seis mezclas y estos indicadores de fiabilidad; no refutan todos los modelos locales ni todas las mezclas posibles.
<!-- FINAL_REVIEW_END -->
'''
    target=ROOT/'documentation/four_expert_combinations_conclusions.md';text=target.read_text(encoding='utf-8').split('\n<!-- FINAL_REVIEW_START -->')[0];text+=section
    text=text.replace('Las penalizaciones meta se congelaron y no se seleccionó la mejor variante sobre folds externos.','Las penalizaciones meta se congelaron. Las comparaciones externas y las recomendaciones posteriores son exploratorias; no se usaron para ajustar hiperparámetros ni se presentan como confirmación independiente.')
    text=text.replace('modelo final138','modelo final con las138 etiquetas').replace('predicciones59','predicciones para las59 parcelas').replace('y59PRED','y las59 parcelas PRED').replace('197X','197 X').replace('Scripts503–513','Scripts 503–517').replace('de[0,1]','de [0,1]')
    text=re.sub(r'\b(con|de|en|sobre|los|las|sus|modelo|modelos|son|hay|entre)(?=[\d±])',r'\1 ',text,flags=re.IGNORECASE);target.write_text(text,encoding='utf-8')
    files=[target,OUT/'audit/convex_prediction_bounds.csv',OUT/'audit/model_artifact_sha256.csv',OUT/'audit/spatial_groups_source.json',ROOT/'documentation/four_expert_combinations_reproduction.md',ROOT/'scripts/517_review_four_expert_results.py'];audit['artifact_sha256'].update({str(f):digest(f) for f in files});audit.update(final_review_complete=True,convex_bounds_verified=True,model_artifacts_hashed=81,original_spatial_groups_hash_match=group_review['matched_architecture_frozen_hash']);(OUT/'delivery_audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps(dict(status='review_complete',fresh_B1_gain_t_ha=fresh_gain,B6_spatial_SSE_loss_share_Calpulalpan_block=share,original_spatial_group_hash=group_review['matched_architecture_frozen_hash']),indent=2))
if __name__=='__main__':main()
