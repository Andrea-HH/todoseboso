# F8 — Matriz acotada y criterios propuestos

Primero R0-B recuperado y R1. R2 solo después de revisar R1, acompañado de C-V para separar aporte de pendiente de simple recalibración de May. R3 se pospone; R4 conceptual. No hay nuevos modelos entrenados ni autorización inferida para fases futuras. Una base estricta rain3 R0-A sería sensibilidad nueva, no referencia EN existente; se propone fuera del primer bloque de ejecución.

R1 tiene un coeficiente de pendiente y un alpha. R2 máximo4 hojas por árbol y100/150 árboles, seis combinaciones curadas y tres λ que no agregan fits. La regularización reduce complejidad efectiva, pero contar4 hojas no implica solo4 parámetros en todo booster; hay umbrales, valores y selección secuencial. SymmetricTree no impone soporte mínimo por hoja: registrar hojas vacías/pequeñas. Cap de amplitud λ≤.5 es una restricción nueva propuesta, no se modifica F7 ni se afirma su optimalidad.

La base conserva12 combinaciones C-T3; las correcciones reutilizan contexto de base solo cuando IDs/CV/grids/preprocesamiento/proveniencia coinciden. La simulación cuenta contextos necesarios y tamaños mínimos, no ajusta. El presupuesto de base puede exceder el de correctores por retuning recursivo; cache de entrenamiento idéntico evita duplicarlo por candidatos o λ.

## Utilidad práctica: propuesta previa, exploratoria

Usar0.01t/ha (10kg/ha) como unidad operativa ya usada en K/L/M/F4; no ajustarla según diferencias F7. Proponer mejora≥.01RMSE en municipal o espacial, daño≤.01RMSE/MAE en cada protocolo y en el otro geográfico, y daño de |sesgo| geográfico≤.02. Esto no establece relevancia económica ni significancia formal. Requiere revisión antes de ejecutar.

Para avanzar, exigir mejora RMSE en≥3/5 folds del protocolo geográfico beneficiado; omitir cada bloque/municipio del cálculo no debe producir daño>.01RMSE/MAE respecto del control. La ganancia no debería invertirse al omitir las cinco mayores beneficiarias (solo sensibilidad OOF). Revisar ambas ponderaciones intraperfil y evitar daño>.01RMSE/MAE bajo cualquiera; no sacrificar absoluto por objetivo local. Grupos diminutos se documentan sin regla regional de selección.

Si λ0 prevalece o no existe ganancia distribuida, cerrar ese corrector bajo esta formulación. No forzar R2/R3 porque R1 no gane: un contraste no lineal requiere hipótesis/apoyo de soporte explícito y revisión, no expansión automática. R2 necesita contraste incremental frente a C-V; R3 requiere R2 viable y evidencia específica de residuos honestos asociados a historia con soporte, plus ablación y transferencia futura. Asociaciones OOF retrospectivas existentes solo motivan, no autorizan ni prueban.

No seleccionar variante externamente y presentar su misma OOF como confirmación. Registrar toda la matriz ejecutada futura; nuevas campañas/regiones serán necesarias para validación independiente. No usar las59 PRED para elegir representaciones, λ, umbrales o fases. No se crean predicciones finales ni un Champion nuevo.


| candidate | phase | hypothesis | base | corrector | inputs | free_params | n_corrector_candidates | lambda_grid | paired_control | risk | continue_if |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R0-B | first, control only | exact current C-T3 control | ElasticNet compact4 | none | C3+V | base12 existing combinations | 0 | 0 | exact archived C-T3 | base absorbs May parcel signal; reused labels | exact fidelity and honest context availability |
| R1 | first proposed scientific contrast | slope residual linear information remains beyond C-T3 | same C-T3 algorithm | centered Ridge, no intercept | T | alpha .01,.1,1; solver=n*alpha | 3 | 0,.25,.5 | R0-B | slope may proxy geography; crossfit/refit residual mismatch | practical geographic benefit without territorial/local deterioration |
| R2 | second; review after R1 | small nonlinear slope-May correction | same C-T3 algorithm | centered CatBoost | T,V | six curated configurations; depth1/2,100/150trees,lr.03,L2=10/30 | 6 | 0,.25,.5 | R0-B, R1 and C-V | Ridge vs R2 changes algorithm AND May inputs; cannot attribute all difference to nonlinearity | survives C-V ablation and geographic criteria |
| C-V | strictly necessary only with R2 | May-only nonlinear recalibration explains apparent R2 gain | same C-T3 algorithm | same centered CatBoost | V only | exact R2 grid and lambda | 6 | 0,.25,.5 | R2 | redistribution of May signal between stages | control, not independent discovery or extra screening |
| R0-A | optional strict-climate sensitivity; review | removing May changes operational decomposition | ElasticNet compact3 only | none | C3 | same12 base grid; no new representational screening | 0 | 0 | R0-B; contextual F5-00-C uses another algorithm | not already evaluated EN reference; dimensions/constants differ | only to answer base A/B explicitly, not automatic A-by-corrector factorial |
| R3 | not initially proposed for execution | history2 predicts honest residual beyond T,V | same C-T3 algorithm | centered conservative CatBoost | T,V,H2 | if later authorized, exact R2 grid | 6 | 0,.25,.5 | R2; joint history2 ablation | same direct-history spatial bias; increasing local proxy capacity | R2 viable and specific residual conditional/local signal with support |
| R4 | concept only | separate T/H corrections improve regularization/interpretability | same C-T3 algorithm | independent centered gT/gH | T and H2 separate | two penalties and two amplitudes; not searched | 0 | not authorized | R1,R3 if later defined | arbitrary signal split and coupled correlated residuals;138 labels | block utility independently demonstrated and independent selection/crossfit design approved |

Parámetros y reglas propuestas:

```json
{
  "status": "research proposal for review; NO execution authorization inferred",
  "first": [
    "R0-B",
    "R1"
  ],
  "second_after_review": [
    "R2",
    "C-V"
  ],
  "strict_base_sensitivity": "R0-A only after review; no automatic residual factorial",
  "secondary": "R3 conditional only",
  "concept_only": "R4",
  "base_grid": {
    "alpha": [
      0.001,
      0.01,
      0.1,
      1
    ],
    "l1_ratio": [
      0.1,
      0.5,
      0.9
    ]
  },
  "base_implementation": "original C-T3 ConditionalFeatures and ElasticNet pipeline; mean internal fold RMSE as archived base algorithm",
  "R1_alpha": [
    0.01,
    0.1,
    1
  ],
  "R1_alpha_solver": "n_train*alpha; zero intercept on training-centered predictors",
  "R2_CV_grid": [
    {
      "iterations": 100,
      "depth": 1,
      "learning_rate": 0.03,
      "l2_leaf_reg": 10
    },
    {
      "iterations": 150,
      "depth": 1,
      "learning_rate": 0.03,
      "l2_leaf_reg": 10
    },
    {
      "iterations": 150,
      "depth": 1,
      "learning_rate": 0.03,
      "l2_leaf_reg": 30
    },
    {
      "iterations": 100,
      "depth": 2,
      "learning_rate": 0.03,
      "l2_leaf_reg": 10
    },
    {
      "iterations": 150,
      "depth": 2,
      "learning_rate": 0.03,
      "l2_leaf_reg": 10
    },
    {
      "iterations": 150,
      "depth": 2,
      "learning_rate": 0.03,
      "l2_leaf_reg": 30
    }
  ],
  "CatBoost_constants": {
    "loss_function": "RMSE",
    "grow_policy": "SymmetricTree",
    "boosting_type": "Plain",
    "bootstrap_type": "No",
    "random_strength": 0,
    "border_count": 64,
    "leaf_estimation_iterations": 1,
    "allow_writing_files": false,
    "thread_count": 1,
    "random_seed": 2026,
    "early_stopping": false
  },
  "lambda_grid": [
    0,
    0.25,
    0.5
  ],
  "correction_centering": "g(X)=h(X)-mean_training(h(X)); deterministic training-only intercept convention, not pure parcel effect",
  "selection": "complete pooled inner OOF RMSE of whole pipeline; tie tolerance1e-10, smaller lambda, simpler depth/trees, stronger regularization; never external selection",
  "base_refit": "all current training only; outer R0-B matches C-T3; inner R0 baseline retunes on inner-training only, not archived global best HP",
  "deeper_CV": "KFold4 seed2026 random; GroupKFold min(4,remaining original groups) otherwise; preserve65outer/original4inner",
  "failure_policy": "if <2 groups required at deeper CV: mark context not evaluable, stop corresponding candidate, no random substitution; if all base predictors constant, predefined training-mean prediction; if all corrector predictors constant, correction0; record rates",
  "primary_metrics": "complete138 OOF per repetition; mean10 random metrics; other protocols single repeat",
  "practical_margins": {
    "utility_geographic_RMSE_min": 0.01,
    "max_RMSE_MAE_harm_each_protocol": 0.01,
    "max_abs_bias_harm_geographic": 0.02,
    "territorial_folds_RMSE_improve_min": 3,
    "max_RMSE_MAE_harm_under_each_region_omission": 0.01,
    "max_intraprofile_RMSE_MAE_harm_each_weighting": 0.01,
    "top5_gain_omission": "net utility must not reverse for advancing; diagnostic only"
  },
  "margin_rationale": "retain existing0.01t/ha engineering convention (10kg/ha), not calibrated against prior deltas or economic/statistical proof; bias .02 exploratory new operational ceiling; proposals need review",
  "no_region_specific_rule": true,
  "no_target_quartile_gate": true,
  "no_ensemble_weights": true,
  "actual_models_fitted": 0,
  "PRED_predictions": false
}
```


Verificación: cinco pruebas pasaron; cero ajustes/predicciones nuevos; 158 fuentes consumidas verificadas. Se conserva inventario de15382 hashes anteriores; los archivos no utilizados no se reabrieron para rehash. Escrituras limitadas a nueva versión F8 y sus documentos.
