"""Stage A descriptive report and explicit advancement decisions."""
import json
import numpy as np
import pandas as pd
from . import territorial_stage_a as a

def markdown(frame):
    z=frame.reset_index(drop=True)
    lines=['| '+' | '.join(map(str,z.columns))+' |','| '+' | '.join(['---']*len(z.columns))+' |']
    for row in z.itertuples(index=False,name=None):lines.append('| '+' | '.join(f'{v:.4f}' if isinstance(v,(float,np.floating)) else str(v).replace('|','/') for v in row)+' |')
    return '\n'.join(lines)

def report(parcels,geology,coverage,features,pairs,metadata):
    out=a.OUT
    cov=pd.read_csv(out/'tables/coverage_summary.csv')
    strata=pd.read_csv(out/'tables/pair_strata_summary.csv')
    units=pd.read_csv(out/'tables/geology_unit_inventory.csv')
    support=pd.read_csv(out/'tables/geology_category_support.csv')
    profiles=features[features.Municipio.eq('Chignahuapan')&features.climate_profile.isin([4,24])].groupby('climate_profile').agg(n_all=(a.ID,'size'),n_geology_units=('geo250_dominant_unit','nunique'),mean_entropy=('geo250_composition_entropy','mean'))
    profiles.reset_index().to_csv(out/'tables/dominant_profile_geology_diversity.csv',index=False)
    local=pairs.drop_duplicates(['id_a','id_b'])
    counts=pd.DataFrame([dict(stratum='all_possible_local_pairs',n_pairs=len(local)),dict(stratum='different_geology250k',n_pairs=int(local.geology_different.sum())),dict(stratum='similar_NDVI_different_geology250k',n_pairs=int((local.ndvi_similar&local.geology_different).sum())),dict(stratum='similar_soil_different_geomorphology',n_pairs=int((local.soil_similar&local.terrain_different).sum())),dict(stratum='all_observed_similar',n_pairs=int(local.all_observed_similar.sum()))])
    counts.to_csv(out/'tables/x_only_pair_stratum_counts.csv',index=False)
    status=pd.DataFrame([
        dict(component='A1 edaphological50k1996',status='suspended',reason='Source absent/misidentified; local folder is topographic scan'),
        dict(component='A2 topographic1996',status='inventory_and_sheet_coverage_complete',reason='Georeferenced palette scan; no verified contour/hydro vector layers, no thematic extraction'),
        dict(component='A3 SGM geology50k2017',status='inventory_and_nominal_sheet_coverage_complete',reason='Documented frame and datum; no embedded geospatialPDF metadata or local official vectors, thematic parcel classification suspended'),
        dict(component='Existing INEGI geology250k',status='descriptive_intersections_complete',reason='Separate coarser official vector; CRS recovered from aux, no equivalence to SGM50k'),
        dict(component='Existing DEM120m terrain',status='descriptive_reuse_complete',reason='Existing TPI/convergence/flow/TWI, no new measured moisture or hydrography'),
        dict(component='Territorial predictive integration',status='not_started',reason='Fine local thematic sources unavailable; any coarse-vector candidate needs a separate frozen experiment and sufficient support'),
        dict(component='Stage B nonterritorial objective and fixed blend',status='methodologically_possible_next_delivery',reason='A source gaps do not invalidate existing rainfall/NDVI/LAI matrices; deliver A before B'),
    ]);status.to_csv(out/'tables/advancement_decisions.csv',index=False)
    plots(parcels,geology,coverage,features,pairs)
    text=f'''# Programa territorial intraperfil — Primera entrega: Etapa A

La auditoría encontró una discrepancia de fuentes: `data/externo/chignahuapan/e14b13.tif` **es una carta topográfica**, no una carta edafológica. No se localizó la fuente edafológica histórica1:50,000 descrita en la solicitud. Se mantiene suspendida su comparación multiescala y clasificación por parcela. La carta geológico-minera suministrada es SGM1:50,000, primera edición de diciembre2017, no1996.

Esta etapa es descriptiva. No se entrenó ningún modelo territorial ni se iniciaron B/C. Se identificó y procesó separadamente una capa geológica oficial INEGI1:250,000 ya existente, y se reutilizaron características geomorfológicas del DEM120m. Esto permite medir diferenciación coarse dentro de perfiles, pero no demostrar que la cartografía local50k explica errores.

## Fuentes y fechas verificadas

| Fuente solicitada | Archivo realmente disponible | Hallazgo |
|---|---|---|
| A1 suelo histórico1996 | Carpeta con e14b13.tif/.tfw/.txt | El TXT y el marginal dicen carta topográfica. No hay suelo50k aquí. |
| A2 topografía E14B13 | Esa misma imagen INEGI | Escala1:50,000, segunda edición/primera impresión1996; fotografías mayo1994; preparación de imagen mayo2002. No se encontró un PDF topográfico independiente en docs/resources. |
| A3 geología E14-B13 | cartageologicadechignahuapan.pdf | SGM1:50,000, primera edición diciembre2017; base INEGI segunda edición2004; PDF creado2018/modificado2022. |
| Fuente adicional recuperada | e1402pg/lg/ptg.shp INEGI | Geología1:250,000 SerieI: compilación1982 y conversión enero2000 según AUX; no es la carta SGM2017. |
| Documento adicional | 6249Chignahuapan - Zacatlan.pdf.crdownload | Se puede abrir como PDF225p de estudio de cuenca de abasto forestal; metadatos2015. El sufijo no garantiza descarga íntegra; no es una carta temática parcelaria. |

La imagen topográfica es un raster de paleta de4500×3386, con pixel de unos10.04m, geometría a partir de worldfile y sin CRS embebido. El pixel representa impresión escaneada y **no equivale a DEM10m ni a clases numéricas de suelo**. La hoja muestra curvas cada10m, hidrografía, cuerpos de agua y elementos territoriales, que permanecen cartografía visual. Datum NAD27/Clarke1866, UTM14N, malla1000m. No se extrajeron drenajes, alturas de cauce ni distancias hidrológicas a partir del color.

El marginal SGM indica transformación desde ITRF92 a NAD27; se usa ITRF92 para el marco nominal documentado. Se verificó ausencia de objetos geoespaciales PDF GPTS/LGIDict/Measure GEO. Tener dibujos/texto vectoriales dentro del PDF no equivale a tener polígonos geológicos georreferenciados con atributos.

La leyenda SGM contiene14 unidades, incluyendo caliza-lutita, andesita-dacita, dacita, riolita, riolita-ignimbrita, toba riolítica-ignimbrita, andesita-brecha andesítica, basalto-andesita, piroclásticos/arena y aluvión. Distingue contactos, fallas/fracturas, lineamientos, caldera/dom os y depósitos. Se conserva el texto completo para revisión; no se asignan categorías a parcelas por colores ni se usan minas/bancos como calidad agrícola. Litología mapeada no es una observación del horizonte radicular ni de nutrientes/retención.

Las fichas oficiales de [SGM](https://www.sgm.gob.mx/cartas/Cartas_Ed50.jsp) registran E14-B13 en2017. INEGI tiene un [producto vectorial E14B13 SerieIII](https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=702825268978), que no debe confundirse con la imagen SerieII1996; se documenta como posibilidad de adquisición y no se afirma que esté descargado. El programa oficial de [geología INEGI](https://www.inegi.org.mx/programas/geol/) contextualiza productos y conversiones históricas. No se descargaron nuevas capas en esta etapa.

## Geometría, proyección y cobertura

Las parcelas originales están en EPSG4326; áreas/intersecciones se calculan en EPSG6372, no en grados ni por centroides. Las geometrías parcelarias válidas se conservan. Los vectores geológicos carecen de PRJ; se recupera NAD27 UTM14N del AUX, cuadrícula y coherencia de coordenadas, registrándolo como asignación de CRS sustentada, sin modificar fuentes.

Se seleccionan operaciones PROJ no-ballpark para el área de interés. NAD27→EPSG6372 tiene precisión declarada aproximada13m; ITRF92→EPSG6372,2m. Son cifras de la operación, no exactitud total de las cartas. Se guardan pipelines y fuente/objetivo para reproducción. No se usa el desplazamiento marginal aproximado como una transformación universal.

Para las cartas50k se construye el marco geográfico documentado98°20′–98°00′W,19°45′–20°00′N, densificando límites antes de proyectarlos. Se calcula el área de intersección completa del polígono parcelario. **Cobertura nominal de hoja no significa clasificación temática disponible.** La cobertura del vector250k usa la unión real de polígonos, reteniendo agua/categorías no conocidas. Para A1 ausente la cobertura no puede evaluarse, no se inventa una fracción cero.

{markdown(cov)}

La tabla `source_coverage_197.csv` conserva cada fracción, estado, municipio, perfil y conjunto. `dominant_profile_coverage.csv` detalla los perfiles4/24. Los marcos y parcelas proyectadas se guardan como GPKG; cobertura parcial/fuera no se descarta.

## Geología250k y suelo existente

Se conservan intersecciones completas y fracciones respecto del área original. La suma de unidades mapeadas no se renormaliza; el faltante se conserva como UNKNOWN_OUTSIDE. Se registra dominante, número de unidades, entropía, distancia a límites cartográficos y reservas de50/125/250m. Las reservas son escenarios de sensibilidad, no intervalos de exactitud. Límites por CLAVE disuelta evitan confundir segmentación de polígonos con cambios de unidad, pero no certifican contactos de campo.

{markdown(units)}

El soporte por categoría se registra separadamente en TRAIN/PRED, perfiles y municipios. Agua y entidades geológicas denominadas suelo se mantienen con sus atributos originales; **“suelo” en geología no es una clasificación edafológica WRB**. No se deriva textura/profundidad ni se equiparan taxonomías. El cruce con la representación WRB2014 usada en I–L es coexistencia cartográfica a250k, no la comparación edafológica50k/250k solicitada, que permanece suspendida.

## Geomorfología e hidrología potencial

Se reutilizan únicamente cuatro columnas ya construidas: TPI3×3, curvatura de planta, log1p de acumulación y TWI, conservando pendiente, altitud y relieve como controles descriptivos. El DEM de120m utilizó relleno de pits/depresiones y resolución de flats antes de D8 sobre toda su extensión; la documentación previa advierte desconocimiento de aportes fuera del borde. No se recalculan superficies ni se presentan como humedad, nivel freático o drenaje observado. No hay aquí una red hidrográfica vectorial verificada para distancia a cauce o altura sobre drenaje.

Se guardan correlaciones con NDVI, pendiente, altitud/relieve y asociaciones de residuos OOF existentes. Las matrices permiten reconocer redundancia; una correlación parcial no autoriza integración predictiva.

## Parejas de los perfiles dominantes

La referencia es F4-S1 archivado, recuperado como F4-E1. Se preservan197 parcelas,138 etiquetas,59 PRED,53 perfiles totales/43 etiquetados y los dos perfiles de Chignahuapan con33/29 etiquetas. Las934 parejas posibles no son934 muestras independientes. El inventario de parejas se define usando X antes de examinar error; la evaluación usa solo pares retenidos por el mismo modelo externo.

Criterios congelados: NDVI similar si diferencia absoluta≤0.03; composición diferente si distancia de variación total>0.05; suelo amplio similar si TV≤0.05; geomorfología diferente si RMS de diferencias estandarizadas≥1, similar si≤0.5. La escala geomorfológica se calcula con X de TRAIN completo únicamente para descripción, no como transformación predictiva. Para el estrato de características observadas similares se requiere además diferencia de inicio LAI≤15d y geología TV≤0.05. Ninguna regla se optimizó contra Y o residuo.

{markdown(counts)}

Diagnóstico aleatorio, promediado entre repeticiones:

{markdown(strata[strata.protocol.eq('random')])}

Los otros tres protocolos están en las tablas. Se registra soporte por parcela/perfil, diferencias observadas/predichas y error de pareja. Parejas solapadas y repeticiones no son independientes, y las reglas de similitud son elecciones descriptivas sensibles a escala. No se interpreta el error de parcelas similares como error irreducible formal.

Las comparaciones “distinto suelo50k” y “distinta geología local50k” no pueden realizarse con las fuentes presentes. La diferenciación geológica aquí corresponde exclusivamente al vector250k. Se conserva el inventario sin errores/Y para que la clasificación no dependa de parejas difíciles seleccionadas a posteriori.

## Decisión por componente y avance

{markdown(status)}

El reporte responde qué fuentes realmente existen, qué cobertura geométrica es verificable y qué contrastes pueden medirse. No demuestra mejora predictiva territorial. Las limitaciones de A impiden atribuir a suelo/geología50k una explicación de errores, pero **no invalidan la Etapa B**, que utiliza las matrices existentes y una función objetivo diferente. B corresponde a la segunda entrega solicitada y no se ejecutó automáticamente en esta primera entrega.

Los atributos geológicos coarse solo podrían pasar a un experimento posterior si su soporte por categoría/perfil, reserva de límites y diferenciación adicional resultan defendibles, con controles de mismas parcelas y diseño congelado. Prioridad territorial: obtener la verdadera fuente edafológica histórica y/o polígonos geológicos oficiales50k, con CRS/leyenda/metadatos completos, antes de integrar precisión local supuesta. No se digitalizó una carta completa ni se inferieron clases por color.

## Reproducción e integridad

`python scripts/340_territorial_program_stage_a.py`. Una versión completada es inmutable. Fuentes, inventario SHA-256, operaciones CRS, geometrías, fracciones y matriz target-free quedan versionados. La Etapa A requiere pruebas de conservación de área, geometrías, límites de composición, identidad de perfiles/folds, ausencia de Y en clasificación de parejas y verificación de resultados previos. La evidencia de esas pruebas se agrega al finalizar. No se alteran rendimientos, fuentes, modelos, Champion ni resultados anteriores.
'''
    (out/'report/territorial_report.md').write_text(text,encoding='utf-8')
    (a.ROOT/'documentation/territorial_program_stage_a.md').write_text(text,encoding='utf-8')
    print(cov.to_string(index=False),flush=True);print(counts.to_string(index=False),flush=True)

def plots(parcels,geology,coverage,features,pairs):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=a.OUT
    fig,axes=plt.subplots(1,2,figsize=(14,7))
    for ax,source in zip(axes,['topographic1996_sheet','INEGI250k_geology_vector']):
        z=parcels.merge(coverage[coverage.source.eq(source)][[a.ID,'classification']],on=a.ID)
        z.plot(ax=ax,column='classification',legend=True,markersize=3)
        ax.set_title(source);ax.set_xlabel('EPSG6372, m');ax.set_ylabel('m')
    fig.tight_layout();fig.savefig(out/'figures/01_source_coverage.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,8));local=geology[geology.geometry.intersects(parcels.geometry.union_all().buffer(1000))]
    local.plot(ax=ax,column='TIPO',legend=True,legend_kwds={'loc':'upper left','bbox_to_anchor':(1.01,1),'fontsize':8},alpha=.7)
    parcels[parcels.Municipio.eq('Chignahuapan')].boundary.plot(ax=ax,color='black',linewidth=.6)
    ax.set_title('Geología existente INEGI250k; parcelas Chignahuapan');fig.subplots_adjust(right=.7);fig.savefig(out/'figures/02_coarse_geology_parcels.png',dpi=180,bbox_inches='tight');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    attrs=features[features.Municipio.eq('Chignahuapan')&features.CONJUNTO.eq('ENTRENAMIENTO')]
    for profile,g in attrs.groupby('climate_profile'):
        if profile in [4,24]:axes[0].scatter(g[a.e.f.NDVI],g.geo250_composition_entropy,label=f'Perfil{profile}')
    axes[0].set(xlabel='NDVI mayo',ylabel='Entropía composición geológica250k');axes[0].legend()
    s=pd.read_csv(out/'tables/pair_strata_summary.csv');s=s[s.protocol.eq('random')]
    axes[1].barh(s.stratum,s.pair_rmse);axes[1].set_xlabel('RMSE diferencias t/ha; diagnóstico')
    fig.tight_layout();fig.savefig(out/'figures/03_pair_diagnostics.png',dpi=180);plt.close(fig)
