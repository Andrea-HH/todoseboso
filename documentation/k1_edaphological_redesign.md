# K.1 — Auditoría y rediseño edafológico

| representation | n_columns | n_same_climate_pairs | n_pairs_L1_half_gt_5pp | scale_policy | coverage_retained_mean | mass_mean_note |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | 10 | 2136 | 816 | soil fractions kept in natural [0,1], no variance division | 2.0245 | S1 sum may exceed one; S4 includes unknown/remainder; not physical soil proportions |
| S2_reference | 22 | 2136 | 863 | soil fractions kept in natural [0,1], no variance division | 1.0000 | S1 sum may exceed one; S4 includes unknown/remainder; not physical soil proportions |
| S3 | 9 | 2136 | 404 | soil fractions kept in natural [0,1], no variance division | 1.0000 | S1 sum may exceed one; S4 includes unknown/remainder; not physical soil proportions |
| S4 | 23 | 2136 | 863 | soil fractions kept in natural [0,1], no variance division | 1.0000 | S1 sum may exceed one; S4 includes unknown/remainder; not physical soil proportions |

{
  "n_j5_j6_predictions": 1794,
  "max_abs_prediction_difference": 8.027186269110587e-05,
  "identical_model_files": 0,
  "n_exactly_different_full_top3_rows": 1,
  "max_omitted_unit_share": 0.013320920669379422,
  "mean_omitted_unit_share": 6.761888664659604e-05,
  "all_synthetic_passed": true,
  "primary": "S1",
  "secondary": "S2",
  "ready_for_modeling": true
}

J5 y J6 se reconstruyeron desde sus pipelines distintos y coinciden con sus propios OOF. Top3 suma codificaciones nominales ponderadas entre rangos: reconstruye casi toda la misma composición, no aporta un bloque independiente. Se conserva el remanente. No se sobrescribe J.

El z-score divide por desviaciones ínfimas: una cobertura razonable en validación puede crecer cientos de veces. K conserva TODAS las coberturas de suelo en [0,1]; no recorta rendimientos. Las columnas constantes se eliminan solo en entrenamiento. S2 aprende unidades con soporte >=3 o >=5 dentro del fit y acumula las demás, incluidas ausentes, en Other. Other constante no puede adquirir un efecto propio: queda eliminado por falta de variación.

S1 es primaria por soporte, escala estable, interpretación y diferenciación climática; no por rendimiento. S2 es la única sensibilidad predictiva. S3 suma coberturas por Grupo1 oficial, perdiendo grupos asociados y calificadores; S4 conserva identificadores ponderados, remanente y masa desconocida, y es diagnóstico secundario sin otro ajuste predictivo. No se armonizan automáticamente claves discrepantes de ediciones.

Elastic Net utiliza el mismo conjunto de 12 penalizaciones en todos los modelos K: alpha .001,.01,.1,1 y l1 .1,.5,.9; el nuevo .001 permite menor penalización coherente con suelo sin z-score. El clima J0 mantiene exactamente su grilla anterior. Políticas congeladas antes de entrenar K.2/K.3.

Residuos: nunca se usan los OOF globales para supervisar el corrector; las particiones más profundas respetan los grupos. La selección interna evalúa predicción climática + eta × corrección completa. ETA incluye cero. Margen geográfico/MAE exploratorio .01 t/ha; no prueba de significancia.
