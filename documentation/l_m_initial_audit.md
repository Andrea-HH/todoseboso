> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# L/M — Auditoría inicial y diseño congelado

| Antecedente | Código | Existente | Nueva pregunta |
| --- | --- | --- | --- |
| E | 315 / rainfall_pcr.py | monthly precipitation PCA/PCR, exact frozen folds | L reuses folds/base; no repeated rain-only PCA search |
| G/H | 316–322; climate_signal_modeling.py | temperature PCA, rain+Tmax and joint21 PCR | L adds geographic/edaphological blocks and base48 comparison |
| I/K | 323–328; soil parquet matrices | S1 mentions, S2 pooled support, S3 main group, S4 Top3 | L primary S1, single S2 Hellinger sensitivity; no ordinal IDs |
| Family1 | 135; feature_pipeline.build_history_anomaly | monthly 2022–24 means/std and 2025 anomalies already built | M reuses their definition; adds support checks, distribution deltas, controlled multisensor comparisons |
| Family2 | 201–204 functional preprocessing/fPCA | functional curves and fPCA hybrids already evaluated | M monthly blocks/regularized PCA are a distinct controlled representation, not first functional analysis |
| Family3 | 301–305 structural modeling | structured/multisource representations | M maps coverage and existing blocks before controlled comparisons |
| Champion | 210–212; TOP20 EN -> HISTORY15 XGB -> TOPO Ridge | 48 climate features screened20;16 historical S2 effective;25 terrain features | L8 descriptive only unless full nested parameter-selection provenance can be reproduced |

197 parcelas,138etiquetas y59ocultas;53perfiles completos y43etiquetados. B1 reproduce J0; B2 reproduce las48columnas originales de Climate Current, no TOP20. Ambas bases usan exactamente la misma grilla original alpha .01,.1,1 / l1 .1,.5,.9 y folds. La grilla complementaria conserva K incluyendo .001.

S1 es primaria, sin amplificar coberturas raras. S2 es una sola sensibilidad con soporte>=5 aprendido por fit y Other; Hellinger=sqrt(p), conserva ceros sin pseudoconteos. Los PCA predictivos no se blanquean y seleccionan1/2/4componentes internamente, con cap por dimensión disponible. Las estrategias se comparan con originales y transformaciones equivalentes; cambiar base también cambia representación térmica/temporal y no aísla temperatura.

La auditoría conjunta verifica antes de entrenar que Sentinel/Landsat poseen2022–2025 y Planet solo2025 en las tablas disponibles. Se reutilizarán NDVI/EVI/NDWI/MSI de Sentinel; Planet NDVI/EVI y estadísticas espaciales suministradas; Landsat VI6T independiente, sin asumir equivalencia espectral con NDVI. No se extraen bandas ni píxeles inexistentes. Historia2022–24 con al menos2años válidos por mes; M0–M5 y PCAsolo por bloque se predefinen; aditivo/residual soloM0,M1,M5 sobre cada base para evitar matriz exhaustiva. M usa28mensualidades actuales,44históricas/anomalías como máximo,20Planet y10Landsat. Sin selección por Y antes de folds.

L8 se limita a auditoría descriptiva por la ausencia de procedencia de cross-fitting anidado de la arquitectura completa y la reutilización histórica de parámetros externos dentro de subfolds. Reajustar toda la selección produciría una variante distinta cuya fidelidad al Champion no se puede certificar. Se conserva este resultado negativo explícito.
