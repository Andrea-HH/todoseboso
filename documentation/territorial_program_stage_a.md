> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Programa territorial intraperfil — Primera entrega: Etapa A

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

| source | classification | CONJUNTO | n_parcels | n_profiles |
| --- | --- | --- | --- | --- |
| INEGI250k_geology_vector | full | ENTRENAMIENTO | 138 | 43 |
| INEGI250k_geology_vector | full | PREDICCION | 59 | 22 |
| SGM2017_nominal_sheet | full | ENTRENAMIENTO | 82 | 15 |
| SGM2017_nominal_sheet | full | PREDICCION | 36 | 10 |
| SGM2017_nominal_sheet | outside | ENTRENAMIENTO | 56 | 28 |
| SGM2017_nominal_sheet | outside | PREDICCION | 23 | 12 |
| topographic1996_sheet | full | ENTRENAMIENTO | 82 | 15 |
| topographic1996_sheet | full | PREDICCION | 36 | 10 |
| topographic1996_sheet | outside | ENTRENAMIENTO | 56 | 28 |
| topographic1996_sheet | outside | PREDICCION | 23 | 12 |

La tabla `source_coverage_197.csv` conserva cada fracción, estado, municipio, perfil y conjunto. `dominant_profile_coverage.csv` detalla los perfiles4/24. Los marcos y parcelas proyectadas se guardan como GPKG; cobertura parcial/fuera no se descarta.

## Geología250k y suelo existente

Se conservan intersecciones completas y fracciones respecto del área original. La suma de unidades mapeadas no se renormaliza; el faltante se conserva como UNKNOWN_OUTSIDE. Se registra dominante, número de unidades, entropía, distancia a límites cartográficos y reservas de50/125/250m. Las reservas son escenarios de sensibilidad, no intervalos de exactitud. Límites por CLAVE disuelta evitan confundir segmentación de polígonos con cambios de unidad, pero no certifican contactos de campo.

| unit_key | entity | rock_class | rock_type | age | n_parcels | total_parcel_share |
| --- | --- | --- | --- | --- | --- | --- |
| Q(B) | UNIDAD CRONOESTRATIGRÁFICA | Ígnea extrusiva | Basalto | Cenozoico | 4 | 2.4823 |
| Q(B-Bvb) | UNIDAD CRONOESTRATIGRÁFICA | Ígnea extrusiva | Basalto-Brecha volcánica básica | Cenozoico | 1 | 1.0000 |
| Q(Bvb) | UNIDAD CRONOESTRATIGRÁFICA | Ígnea extrusiva | Brecha volcánica básica | Cenozoico | 4 | 1.5925 |
| Q(al) | SUELO | nan | Aluvial | Cenozoico | 44 | 32.8406 |
| Ts(A) | UNIDAD CRONOESTRATIGRÁFICA | Ígnea extrusiva | Andesita | Cenozoico | 15 | 10.3154 |
| Ts(B) | UNIDAD CRONOESTRATIGRÁFICA | Ígnea extrusiva | Basalto | Cenozoico | 45 | 40.4367 |
| Ts(R) | UNIDAD CRONOESTRATIGRÁFICA | Ígnea extrusiva | Riolita | Cenozoico | 43 | 33.5068 |
| Ts(R-Ta) | UNIDAD CRONOESTRATIGRÁFICA | Ígnea extrusiva | Riolita-Toba ácida | Cenozoico | 18 | 14.2565 |
| Ts(Ta) | UNIDAD CRONOESTRATIGRÁFICA | Ígnea extrusiva | Toba ácida | Cenozoico | 19 | 16.5015 |
| Ts(Ti) | UNIDAD CRONOESTRATIGRÁFICA | Ígnea extrusiva | Toba intermedia | Cenozoico | 45 | 44.0678 |

El soporte por categoría se registra separadamente en TRAIN/PRED, perfiles y municipios. Agua y entidades geológicas denominadas suelo se mantienen con sus atributos originales; **“suelo” en geología no es una clasificación edafológica WRB**. No se deriva textura/profundidad ni se equiparan taxonomías. El cruce con la representación WRB2014 usada en I–L es coexistencia cartográfica a250k, no la comparación edafológica50k/250k solicitada, que permanece suspendida.

## Geomorfología e hidrología potencial

Se reutilizan únicamente cuatro columnas ya construidas: TPI3×3, curvatura de planta, log1p de acumulación y TWI, conservando pendiente, altitud y relieve como controles descriptivos. El DEM de120m utilizó relleno de pits/depresiones y resolución de flats antes de D8 sobre toda su extensión; la documentación previa advierte desconocimiento de aportes fuera del borde. No se recalculan superficies ni se presentan como humedad, nivel freático o drenaje observado. No hay aquí una red hidrográfica vectorial verificada para distancia a cauce o altura sobre drenaje.

Se guardan correlaciones con NDVI, pendiente, altitud/relieve y asociaciones de residuos OOF existentes. Las matrices permiten reconocer redundancia; una correlación parcial no autoriza integración predictiva.

## Parejas de los perfiles dominantes

La referencia es F4-S1 archivado, recuperado como F4-E1. Se preservan197 parcelas,138 etiquetas,59 PRED,53 perfiles totales/43 etiquetados y los dos perfiles de Chignahuapan con33/29 etiquetas. Las934 parejas posibles no son934 muestras independientes. El inventario de parejas se define usando X antes de examinar error; la evaluación usa solo pares retenidos por el mismo modelo externo.

Criterios congelados: NDVI similar si diferencia absoluta≤0.03; composición diferente si distancia de variación total>0.05; suelo amplio similar si TV≤0.05; geomorfología diferente si RMS de diferencias estandarizadas≥1, similar si≤0.5. La escala geomorfológica se calcula con X de TRAIN completo únicamente para descripción, no como transformación predictiva. Para el estrato de características observadas similares se requiere además diferencia de inicio LAI≤15d y geología TV≤0.05. Ninguna regla se optimizó contra Y o residuo.

| stratum | n_pairs |
| --- | --- |
| all_possible_local_pairs | 934 |
| different_geology250k | 727 |
| similar_NDVI_different_geology250k | 480 |
| similar_soil_different_geomorphology | 232 |
| all_observed_similar | 15 |

Diagnóstico aleatorio, promediado entre repeticiones:

| protocol | stratum | repeat | n_pairs | n_parcels | n_profiles | pair_rmse | pair_mae | observed_difference_rms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random | all | 5.5000 | 181.1000 | 62.0000 | 2.0000 | 0.7983 | 0.5536 | 0.8320 |
| random | different_geology250k | 5.5000 | 139.8000 | 61.7000 | 2.0000 | 0.7592 | 0.5326 | 0.7986 |
| random | similar_NDVI_different_geology250k | 5.5000 | 92.2000 | 56.7000 | 2.0000 | 0.7960 | 0.5489 | 0.8011 |
| random | similar_observed_climate_vegetation_terrain_soil_geo | 5.6667 | 4.0000 | 5.5556 | 1.0000 | 0.7986 | 0.5936 | 0.8156 |
| random | similar_soil_different_geomorphology | 5.5000 | 43.7000 | 40.6000 | 2.0000 | 0.8627 | 0.6048 | 0.8802 |

Los otros tres protocolos están en las tablas. Se registra soporte por parcela/perfil, diferencias observadas/predichas y error de pareja. Parejas solapadas y repeticiones no son independientes, y las reglas de similitud son elecciones descriptivas sensibles a escala. No se interpreta el error de parcelas similares como error irreducible formal.

Las comparaciones “distinto suelo50k” y “distinta geología local50k” no pueden realizarse con las fuentes presentes. La diferenciación geológica aquí corresponde exclusivamente al vector250k. Se conserva el inventario sin errores/Y para que la clasificación no dependa de parejas difíciles seleccionadas a posteriori.

## Decisión por componente y avance

| component | status | reason |
| --- | --- | --- |
| A1 edaphological50k1996 | suspended | Source absent/misidentified; local folder is topographic scan |
| A2 topographic1996 | inventory_and_sheet_coverage_complete | Georeferenced palette scan; no verified contour/hydro vector layers, no thematic extraction |
| A3 SGM geology50k2017 | inventory_and_nominal_sheet_coverage_complete | Documented frame and datum; no embedded geospatialPDF metadata or local official vectors, thematic parcel classification suspended |
| Existing INEGI geology250k | descriptive_intersections_complete | Separate coarser official vector; CRS recovered from aux, no equivalence to SGM50k |
| Existing DEM120m terrain | descriptive_reuse_complete | Existing TPI/convergence/flow/TWI, no new measured moisture or hydrography |
| Territorial predictive integration | not_started | Fine local thematic sources unavailable; any coarse-vector candidate needs a separate frozen experiment and sufficient support |
| Stage B nonterritorial objective and fixed blend | methodologically_possible_next_delivery | A source gaps do not invalidate existing rainfall/NDVI/LAI matrices; deliver A before B |

El reporte responde qué fuentes realmente existen, qué cobertura geométrica es verificable y qué contrastes pueden medirse. No demuestra mejora predictiva territorial. Las limitaciones de A impiden atribuir a suelo/geología50k una explicación de errores, pero **no invalidan la Etapa B**, que utiliza las matrices existentes y una función objetivo diferente. B corresponde a la segunda entrega solicitada y no se ejecutó automáticamente en esta primera entrega.

Los atributos geológicos coarse solo podrían pasar a un experimento posterior si su soporte por categoría/perfil, reserva de límites y diferenciación adicional resultan defendibles, con controles de mismas parcelas y diseño congelado. Prioridad territorial: obtener la verdadera fuente edafológica histórica y/o polígonos geológicos oficiales50k, con CRS/leyenda/metadatos completos, antes de integrar precisión local supuesta. No se digitalizó una carta completa ni se inferieron clases por color.

## Reproducción e integridad

`python scripts/340_territorial_program_stage_a.py`. Una versión completada es inmutable. Fuentes, inventario SHA-256, operaciones CRS, geometrías, fracciones y matriz target-free quedan versionados. La Etapa A requiere pruebas de conservación de área, geometrías, límites de composición, identidad de perfiles/folds, ausencia de Y en clasificación de parejas y verificación de resultados previos. La evidencia de esas pruebas se agrega al finalizar. No se alteran rendimientos, fuentes, modelos, modelo TOP20/TOP15 ni resultados anteriores.


## Verificación final

Seis pruebas pasaron: identidad/cartografía paletizada, worldfile y medio pixel, geometrías y cobertura por área, conservación de composición, clasificación de pares usandoX, comparabilidad de predicciones y hashes de fuentes/resultados anteriores. El ámbito ejecutado es exclusivamente EtapaA.

![01_source_coverage.png](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_a/figures/01_source_coverage.png)


![02_coarse_geology_parcels.png](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_a/figures/02_coarse_geology_parcels.png)


![03_pair_diagnostics.png](../outputs/research/family_4/territorial_intraprofile_program/v1/stage_a/figures/03_pair_diagnostics.png)
