> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# F5 — Redundancia, soporte e identificabilidad

Se calcularon únicamente relaciones entre covariables existentes de138 TRAIN. No se empleó Y para nuevos rankings, se usó PRED para seleccionar ni se ajustaron regresiones de reconstrucción nuevas. Las asociaciones conY citadas proceden de artefactos anteriores. `predictor_pearson_TRAIN138.csv` y `predictor_within_profile_pearson.csv` conservan las matrices; `high_redundancy_pairs.csv` identifica pares |r|≥0.9, criterio descriptivo, no eliminación supervisada automática.

| index | representation | n | n_variables | rank | condition_number | n_distinct_vectors | note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | rain7 | 138 | 7 | 7 | 24.17297 | 43 | descriptive TRAIN geometry; no model fitted; no new predictive PCA |
| 1 | compact3 | 138 | 3 | 3 | 3.54630 | 43 | descriptive TRAIN geometry; no model fitted; no new predictive PCA |
| 2 | core4 | 138 | 4 | 4 | 3.90194 | 136 | descriptive TRAIN geometry; no model fitted; no new predictive PCA |
| 3 | core_history6 | 138 | 6 | 6 | 4.93687 | 138 | descriptive TRAIN geometry; no model fitted; no new predictive PCA |
| 4 | core_slope5 | 138 | 5 | 5 | 4.13323 | 138 | descriptive TRAIN geometry; no model fitted; no new predictive PCA |
| 5 | history16 | 138 | 16 | 16 | 125.30073 | 138 | descriptive TRAIN geometry; no model fitted; no new predictive PCA |

Lluvia7 contiene43vectores exactos entre etiquetas. Clima solo siempre asignará la misma media a parcelas con el mismo X; añadirWhiteKernel facilita el ruido/solución numérica, pero no aporta un predictor parcelario. No deduplicar observaciones conYdiferentes ni tratarlas como una única etiqueta sin un modelo explícito de agregación. NDVI de mayo/historia/pendiente pueden distinguir algunas parcelas, sin asegurar que resuelvan el residuo.

Redundancias deterministas: precip_mean=total/7; early+mid+late=total; precip_cv=std/mean, cuando no hay degeneración. C fracción temprana incorpora early/total y HHI concentración: no son una rotación lineal de meses ni información nueva de otra fuente. Evitar sumar resúmenes redundantes y meses sin una ablación planificada.

Históricos: cobertura`months`=7 en el bloqueSentinel, sin variación útil;mean/std no indican variabilidad interanual. NDVI/EVI/SAVI/LAI/FAPAR pueden repetir estructura de verdor. QueLAI deriveSAVI no significa correlación1 luego de agregaciones no lineales: media de transformación no es transformación de media. No usar bajas correlaciones aisladas como garantía de información incremental.

| index | column | period | incremental_evidence | stability | redundancy_risk |
| --- | --- | --- | --- | --- | --- |
| 7 | compact_precip_total | Apr-Oct2025 | C-T3 compact + NDVI de mayo municipal benefit; compact rainfall alone not validated as same configuration | compact benefit municipal; spatial dependsblock3; no universal representation winner | mean=total/7; early+mid+late=total; std/cv and fractions overlap |
| 8 | compact_early_fraction | Apr-Oct2025 | C-T3 compact + NDVI de mayo municipal benefit; compact rainfall alone not validated as same configuration | compact benefit municipal; spatial dependsblock3; no universal representation winner | mean=total/7; early+mid+late=total; std/cv and fractions overlap |
| 9 | compact_concentration_hhi | Apr-Oct2025 | C-T3 compact + NDVI de mayo municipal benefit; compact rainfall alone not validated as same configuration | compact benefit municipal; spatial dependsblock3; no universal representation winner | mean=total/7; early+mid+late=total; std/cv and fractions overlap |
| 20 | CLIMATE_dtr_mean_std | 2025-04-01/2025-10-31 | S5 spatial benefit, but T2/T4 do not combine NDVI benefit consistently | spatial improvement primarilyblock3; weak random/municipal | correlated seasonal/rain/state structure; not meanTmax |
| 37 | S2_ndvi_month_05 | 2025-05-01/2025-05-31 | S1 additive improves random/profile/municipal relative rain; local discrimination, not sole predictor superiority | 138labels,65 folds; exploratory discovery on reusedY | date not necessarily same phenological stage; correlated indices |
| 44 | HIST_S2_ndvi_promedio_mean | Apr-Oct2022-2024 pooled by calendar month | Sentinel historical16 block improves residualXGB; this exact2column subset not proven | CLIMATE_ENET:50/50 selected; PRECIPITATION_XGB:50/50 selected; TOP20_ENET:50/50 selected | indices correlated; std is seasonal of historical meanmonths, not year-to-year variability |
| 45 | HIST_S2_ndvi_promedio_std | Apr-Oct2022-2024 pooled by calendar month | Sentinel historical16 block improves residualXGB; this exact2column subset not proven | CLIMATE_ENET:50/50 selected; PRECIPITATION_XGB:50/50 selected; TOP20_ENET:50/50 selected | indices correlated; std is seasonal of historical meanmonths, not year-to-year variability |
| 70 | TOPO_BASIC_slope_mean | STATIC | slope14block survives RS5; mean-only exact subset hypothesis; TWI/relief no incremental stable evidence | RS5 slope block8/10 repeats; geography K costs; variablewise effect unproven | quantiles correlated; DEM120m; derivedhydrology not measuredwater |

Topografía: alias pendiente media exacto; estadísticas de elevación/pendiente correlacionadas y fuentes con escalaDEM120m. Elegir una media paraF5 es una restricción estructural hipotética, no prueba de suficiencia. La matriz de correlación global puede ocultar relaciones regionales; la matriz centrada por perfil usa solo perfiles repetidos para describir X. Variables climáticas constantes dentro del perfil producen varianza local0 y correlaciones indefinidas, no asociación local negativa ni ausencia de importancia regional.

Colinealidad enGP: distintos repartos de longitudes pueden inducir distancias similares; ARD no es un selector causal ni una prueba de relevancia. Nuestra restricción propuesta comparte longitud porbloque, excluye duplicados y normaliza dimensiones de bloque. No eliminar ejes automáticamente por correlación para después afirmar evaluación independiente.

![Redundancia candidata](../outputs/research/family_5/gpr_evidence_design/v1/figures/candidate_redundancy.png)

![Selección histórica](../outputs/research/family_5/gpr_evidence_design/v1/figures/history_selection_frequency.png)
