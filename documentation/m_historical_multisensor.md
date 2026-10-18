> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# M — Historical and Multisensor Satellite Signal Exploration

| sensor | indices | years | period | n_rows | cloud_missing | n_parcels_any_valid | primary_mask | spatial_quantiles | availability_dates |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S2 | ndvi,evi,ndwi,msi | 2022,2023,2024,2025 | Apr-Oct; cutoff2025-10-31 | 34476 | 0 | 197 | native finite values, no new cloud cutoff | not supplied; q25/q75 below are TEMPORAL monthly-mean percentiles | not supplied separately from fecha_captura |
| PLANET | ndvi,evi | 2025 | Apr-Oct; cutoff2025-10-31 | 26255 | 0 | 197 | native finite values, no new cloud cutoff | not supplied; q25/q75 below are TEMPORAL monthly-mean percentiles | not supplied separately from fecha_captura |
| LANDSAT | vi6t | 2022,2023,2024,2025 | Apr-Oct; cutoff2025-10-31 | 28895 | 1863 | 197 | native finite values, no new cloud cutoff | not supplied; q25/q75 below are TEMPORAL monthly-mean percentiles | not supplied separately from fecha_captura |

| experiment | climate_profile | municipality | random | spatial |
| --- | --- | --- | --- | --- |
| M0_BLOCK_PCA | 0.7990 | 1.0002 | 0.7193 | 0.9154 |
| M0_RAW | 0.7363 | 0.9894 | 0.6921 | 0.9064 |
| M1_BLOCK_PCA | 0.9675 | 1.1329 | 0.7711 | 1.0593 |
| M1_RAW | 0.7366 | 0.8763 | 0.6309 | 1.0082 |
| M2_BLOCK_PCA | 0.8528 | 1.0512 | 0.7526 | 0.9507 |
| M2_RAW | 0.6816 | 0.9945 | 0.6515 | 0.9068 |
| M3_BLOCK_PCA | 0.8114 | 1.2033 | 0.7160 | 1.0331 |
| M3_RAW | 0.7078 | 0.9295 | 0.6637 | 0.8792 |
| M4_BLOCK_PCA | 0.8876 | 1.1157 | 0.7415 | 0.9862 |
| M4_RAW | 0.6490 | 0.9801 | 0.6457 | 0.9018 |
| M5_BLOCK_PCA | 0.9344 | 1.1339 | 0.7599 | 1.0406 |
| M5_RAW | 0.7323 | 0.9606 | 0.6299 | 1.0071 |
| MA_current_M0 | 0.5297 | 1.0398 | 0.5348 | 0.8070 |
| MA_current_M1 | 0.5872 | 0.7713 | 0.5424 | 0.8327 |
| MA_current_M5 | 0.5527 | 0.7821 | 0.5423 | 0.8114 |
| MA_rain_M0 | 0.5610 | 0.8881 | 0.5288 | 0.7733 |
| MA_rain_M1 | 0.6145 | 0.7392 | 0.5610 | 0.8123 |
| MA_rain_M5 | 0.6248 | 0.7895 | 0.5702 | 0.8778 |
| MB_CURRENT | 0.5403 | 0.7773 | 0.5200 | 0.9798 |
| MB_RAIN | 0.5444 | 0.6954 | 0.5214 | 0.7348 |
| MR_current_M0 | 0.5565 | 0.7584 | 0.5214 | 0.8295 |
| MR_current_M1 | 0.5480 | 0.8206 | 0.5225 | 0.8968 |
| MR_current_M5 | 0.5464 | 0.9589 | 0.5231 | 1.0103 |
| MR_rain_M0 | 0.5528 | 0.7083 | 0.5252 | 0.6813 |
| MR_rain_M1 | 0.5532 | 0.7913 | 0.5249 | 0.7344 |
| MR_rain_M5 | 0.5571 | 0.9001 | 0.5256 | 0.7241 |

M0=Sentinel2025; M1=actual+historia/anomalías; M2=actual+Planet; M3=actual+Landsat; M4=actual+Planet+Landsat; M5=todos. Cada combinación tiene control raw y PCAporbloque, mismos197/138IDs/folds sin borrar parcelas incompletas. MA/MR soloM0,M1,M5 sobre B1/B2, mismos bloques/escalas/grillas para separar arquitectura. PCApredictivo1/2/4componentes por bloque seleccionado internamente. No se seleccionan combinaciones por RMSEexterno.

SentinelNDVI/EVI/NDWI/MSI:28promedios mensuales. Historia44variables:28anomalías,12diferencias de media/dispersión/rango y4medias históricas. La referencia utiliza solo2022–24 y>=2años válidos por mes, igual peso anual. Diferencias de distribución usan>=4meses emparejados. Cada referencia conserva soporte de años; las no defendibles permanecenNaN y se imputan solo dentro de cada fit. No se utiliza2025 para su propia referencia. Tres años no son normal climatológica. Tabla05 identifica cuánto de anomalías ya estaba en Familia1; son nuevos controles/representaciones, no nuevos datos.

Planet:14promedios mensualesNDVI/EVI y6estadísticas de heterogeneidad suministrada/dispersión temporal. Mediana y percentiles calculados aquí son TEMPORALES; no se inventan cuantiles de píxeles. Landsat:7mensualidadesVI6T y3resúmenes propios. VI6T no es asumidoNDVI, ni se mezcla como observación intercambiable de Sentinel. Comparación por mes calendario no garantiza misma fecha, bandas, ecuación o calibración; no se atribuye mejora solo a resolución. Tablasfuente no suministran rasters/bandas originales, pesos exactos de intersección, conteo de píxeles, máscaras de píxeles ni fecha separada de procesamiento/disponibilidad; límites explícitos para parcelas pequeñas y pronóstico.

La calidad retiene valores nativos finitos sin nuevo cutoffde nube. Sensibilidades<=20/50% se describen sin retunear resultados; falta de observaciones, nubes, años y meses se conservan como diagnósticos. No hay interpolación entre sensores ni fechas. Noviembre/diciembre2025 se excluyeron; estudio retrospectivo al31octubre, no pronóstico temprano. Máximos espectrales no son fechas de siembra/emergencia/cosecha.

Cross-fitting y selección interna de toda la base climática, sin OOFglobal usado para supervisar correctores. Residuos por etapa en tabla15 y14proveniencia; propuesta,eta,aplicación,final en tabla10. Coeficientes y estabilidad de signos/magnitudes, errores extremos, nubes/faltantes, perfiles, regiones, Chignahuapan y buffers en tablas20–31. Las parejas intraperfil solo usan un mismo modelo externo; distinguir parcelas no garantiza acertar diferencias de rendimiento.

Asociaciones de suelo después de clima+satélite se reportan descriptivamente, no como validación de una tercera etapa. No se añade ninguna etapa al modelo TOP20/TOP15; su historiaSentinel ya contenía resúmenes2022–24. M propone integración solo si la señal geográfica complementaria resulta consistente; folds/repeticiones superpuestos no son evidencia independiente.

![RMSE](../outputs/modeling/family_1/m_historical_multisensor/v1/figures/RMSE_protocol.png)

![MAE](../outputs/modeling/family_1/m_historical_multisensor/v1/figures/MAE_protocol.png)

## Comparaciones controladas finales

| question | representation | protocol | baseline | candidate | delta_RMSE | delta_MAE |
| --- | --- | --- | --- | --- | --- | --- |
| history | RAW | random | M0 | M1 | 0.0612 | 0.0449 |
| history | RAW | climate_profile | M0 | M1 | -0.0003 | 0.0042 |
| history | RAW | municipality | M0 | M1 | 0.1130 | 0.1251 |
| history | RAW | spatial | M0 | M1 | -0.1018 | -0.1057 |
| Planet | RAW | random | M0 | M2 | 0.0406 | 0.0314 |
| Planet | RAW | climate_profile | M0 | M2 | 0.0547 | 0.0607 |
| Planet | RAW | municipality | M0 | M2 | -0.0051 | -0.0138 |
| Planet | RAW | spatial | M0 | M2 | -0.0004 | 0.0154 |
| Landsat | RAW | random | M0 | M3 | 0.0284 | 0.0294 |
| Landsat | RAW | climate_profile | M0 | M3 | 0.0285 | 0.0254 |
| Landsat | RAW | municipality | M0 | M3 | 0.0599 | 0.0458 |
| Landsat | RAW | spatial | M0 | M3 | 0.0271 | 0.0218 |
| Landsat_given_Planet | RAW | random | M2 | M4 | 0.0058 | 0.0090 |
| Landsat_given_Planet | RAW | climate_profile | M2 | M4 | 0.0326 | 0.0340 |
| Landsat_given_Planet | RAW | municipality | M2 | M4 | 0.0144 | 0.0113 |
| Landsat_given_Planet | RAW | spatial | M2 | M4 | 0.0050 | -0.0073 |
| history_given_multisensor | RAW | random | M4 | M5 | 0.0158 | 0.0104 |
| history_given_multisensor | RAW | climate_profile | M4 | M5 | -0.0832 | -0.0855 |
| history_given_multisensor | RAW | municipality | M4 | M5 | 0.0195 | 0.0304 |
| history_given_multisensor | RAW | spatial | M4 | M5 | -0.1053 | -0.1111 |
| multisensor_given_history | RAW | random | M1 | M5 | 0.0010 | 0.0059 |
| multisensor_given_history | RAW | climate_profile | M1 | M5 | 0.0043 | 0.0050 |
| multisensor_given_history | RAW | municipality | M1 | M5 | -0.0842 | -0.0972 |
| multisensor_given_history | RAW | spatial | M1 | M5 | 0.0011 | 0.0027 |
| history | BLOCK_PCA | random | M0 | M1 | -0.0518 | -0.0502 |
| history | BLOCK_PCA | climate_profile | M0 | M1 | -0.1685 | -0.1914 |
| history | BLOCK_PCA | municipality | M0 | M1 | -0.1328 | -0.1764 |
| history | BLOCK_PCA | spatial | M0 | M1 | -0.1439 | -0.1787 |
| Planet | BLOCK_PCA | random | M0 | M2 | -0.0333 | -0.0268 |
| Planet | BLOCK_PCA | climate_profile | M0 | M2 | -0.0538 | -0.0491 |
| Planet | BLOCK_PCA | municipality | M0 | M2 | -0.0510 | -0.0609 |
| Planet | BLOCK_PCA | spatial | M0 | M2 | -0.0354 | -0.0240 |
| Landsat | BLOCK_PCA | random | M0 | M3 | 0.0033 | -0.0004 |
| Landsat | BLOCK_PCA | climate_profile | M0 | M3 | -0.0124 | -0.0313 |
| Landsat | BLOCK_PCA | municipality | M0 | M3 | -0.2031 | -0.2609 |
| Landsat | BLOCK_PCA | spatial | M0 | M3 | -0.1178 | -0.1592 |
| Landsat_given_Planet | BLOCK_PCA | random | M2 | M4 | 0.0111 | 0.0078 |
| Landsat_given_Planet | BLOCK_PCA | climate_profile | M2 | M4 | -0.0348 | -0.0611 |
| Landsat_given_Planet | BLOCK_PCA | municipality | M2 | M4 | -0.0645 | -0.0940 |
| Landsat_given_Planet | BLOCK_PCA | spatial | M2 | M4 | -0.0354 | -0.0740 |
| history_given_multisensor | BLOCK_PCA | random | M4 | M5 | -0.0184 | -0.0175 |
| history_given_multisensor | BLOCK_PCA | climate_profile | M4 | M5 | -0.0468 | -0.0389 |
| history_given_multisensor | BLOCK_PCA | municipality | M4 | M5 | -0.0182 | -0.0195 |
| history_given_multisensor | BLOCK_PCA | spatial | M4 | M5 | -0.0544 | -0.0505 |
| multisensor_given_history | BLOCK_PCA | random | M1 | M5 | 0.0111 | 0.0135 |
| multisensor_given_history | BLOCK_PCA | climate_profile | M1 | M5 | 0.0331 | 0.0422 |
| multisensor_given_history | BLOCK_PCA | municipality | M1 | M5 | -0.0010 | 0.0021 |
| multisensor_given_history | BLOCK_PCA | spatial | M1 | M5 | 0.0187 | 0.0302 |

Mejoras positivas favorecen al candidato. Interpretar cada protocolo por separado; revisar MAE, categorías y error intraperfil antes de integrar. La síntesis transversal conserva resultados negativos y limita conclusiones al objetivo evaluado.

## Interpretación de la referencia y calidad

El PCA predictivo por bloques primero reduce cada sensor/familia y luego concatena sus scores con balance de energía; un PCA final conserva el mismo presupuesto total de1/2/4componentes en M0–M5, elegido dentro de entrenamiento. El balance divide por max(raíz de energía,1), por lo que no amplifica bloques casi constantes. No hay whitening. La dimensión efectivamente elegida se conserva por fold; igualdad de presupuesto no implica que todos los modelos hayan seleccionado el mismo K.

Las diferencias de dispersión y rango principales comparan2025 con la curva mensual media2022–24. Promediar años suaviza la curva histórica: una diferencia positiva deσ no demuestra por sí sola mayor variabilidad anual. La sensibilidad descriptiva en annual_distribution_delta_sensitivity_descriptive.parquet compara también estadísticas de cada año y su promedio, sin nuevos modelos ni elecciones por Y. El soporte de años y observaciones se registra por parcela, mes e índice.

Las fechas son observaciones agregadas, no un conteo verificable de escenas originales. No se suministran fechas separadas de procesamiento/disponibilidad, versiones de procesamiento por año, bandas/píxeles ni tipos de cultivo históricos. Comparar el mismo calendario no garantiza el mismo cultivo o estado fenológico. Esta evaluación retrospectiva no valida pronóstico temprano ni transferencia a otro año.

Calidad temporal efectiva(gaps de fechas válidas), nubes y cobertura en tablas36–38; no se eliminan parcelas por esas reservas ni se retunea ningún modelo.
