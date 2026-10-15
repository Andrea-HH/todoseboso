# F7 — Expansión controlada: diseño congelado

Solo E1/E2/E3 CatBoost; F7-00/F7-01 y referencias recuperados sin ajustes. Historia NDVI2 conserva las dos columnas F5: mean/std entre siete promedios de meses calendario históricos 2022–24, no std interanual. Pendiente media usa TOPO_BASIC_slope_mean=slope_degrees. No History15/16, slope14, DTR, coordenadas, estado ni municipio como entradas. Se conservan ocho configuraciones y65 folds externos con4 internos. E3 se reajusta conjuntamente. Interacciones predefinidas, soporte y permutación conjunta se fijan abajo. Las permutaciones expandidas se restringen además a esquinas respaldadas en espacio de entrenamiento; condicionan al perfil climático, no a todas las otras variables.

Igual peso por perfil y por parejas se reporta por separado; solo parejas del mismo ajuste externo. Grupos con <10 parcelas o <3 perfiles se marcan de soporte reducido para interpretación intraperfil, sin borrar resultados descriptivos. Todas las omisiones son de cálculo OOF, nunca de ajustes. La evaluación es exploratoria sobre etiquetas y particiones previamente reutilizadas. No hay superioridad estadística, selección externa de pesos, ensemble, stacking, corrector residual, modelo final, PRED ni promoción.

```json
{
  "specs": {
    "F7-E1": {
      "algorithm": "CatBoost",
      "columns": [
        "compact_precip_total",
        "compact_early_fraction",
        "compact_concentration_hhi",
        "S2_ndvi_month_05",
        "HIST_S2_ndvi_promedio_mean",
        "HIST_S2_ndvi_promedio_std"
      ]
    },
    "F7-E2": {
      "algorithm": "CatBoost",
      "columns": [
        "compact_precip_total",
        "compact_early_fraction",
        "compact_concentration_hhi",
        "S2_ndvi_month_05",
        "TOPO_BASIC_slope_mean"
      ]
    },
    "F7-E3": {
      "algorithm": "CatBoost",
      "columns": [
        "compact_precip_total",
        "compact_early_fraction",
        "compact_concentration_hhi",
        "S2_ndvi_month_05",
        "HIST_S2_ndvi_promedio_mean",
        "HIST_S2_ndvi_promedio_std",
        "TOPO_BASIC_slope_mean"
      ]
    }
  },
  "grid": [
    {
      "iterations": 150,
      "depth": 2,
      "learning_rate": 0.03,
      "l2_leaf_reg": 10
    },
    {
      "iterations": 300,
      "depth": 2,
      "learning_rate": 0.03,
      "l2_leaf_reg": 10
    },
    {
      "iterations": 300,
      "depth": 2,
      "learning_rate": 0.06,
      "l2_leaf_reg": 10
    },
    {
      "iterations": 300,
      "depth": 2,
      "learning_rate": 0.03,
      "l2_leaf_reg": 30
    },
    {
      "iterations": 150,
      "depth": 3,
      "learning_rate": 0.03,
      "l2_leaf_reg": 10
    },
    {
      "iterations": 300,
      "depth": 3,
      "learning_rate": 0.03,
      "l2_leaf_reg": 10
    },
    {
      "iterations": 300,
      "depth": 3,
      "learning_rate": 0.06,
      "l2_leaf_reg": 10
    },
    {
      "iterations": 300,
      "depth": 3,
      "learning_rate": 0.03,
      "l2_leaf_reg": 30
    }
  ],
  "seed": 2026,
  "implementation": "immutable family_7.models.BoostModel and scoped family_6 execution reuse",
  "selection": "original eight CatBoost configurations x four frozen inner folds; mean inner fold RMSE; round10 ties first; no early stopping",
  "normalization": "original ConditionalFeatures fitted separately on each corresponding training set; native Y",
  "aggregation": "138 complete OOF per repetition; average ten random repetition metrics; per-fold metrics diagnostic",
  "interactions": {
    "F7-E1": [
      [
        "compact_precip_total",
        "S2_ndvi_month_05"
      ],
      [
        "compact_early_fraction",
        "S2_ndvi_month_05"
      ],
      [
        "compact_concentration_hhi",
        "S2_ndvi_month_05"
      ],
      [
        "S2_ndvi_month_05",
        "HIST_S2_ndvi_promedio_mean"
      ],
      [
        "S2_ndvi_month_05",
        "HIST_S2_ndvi_promedio_std"
      ]
    ],
    "F7-E2": [
      [
        "compact_precip_total",
        "S2_ndvi_month_05"
      ],
      [
        "compact_early_fraction",
        "S2_ndvi_month_05"
      ],
      [
        "compact_concentration_hhi",
        "S2_ndvi_month_05"
      ],
      [
        "compact_precip_total",
        "TOPO_BASIC_slope_mean"
      ]
    ],
    "F7-E3": [
      [
        "compact_precip_total",
        "S2_ndvi_month_05"
      ],
      [
        "compact_early_fraction",
        "S2_ndvi_month_05"
      ],
      [
        "compact_concentration_hhi",
        "S2_ndvi_month_05"
      ],
      [
        "S2_ndvi_month_05",
        "HIST_S2_ndvi_promedio_mean"
      ],
      [
        "S2_ndvi_month_05",
        "HIST_S2_ndvi_promedio_std"
      ],
      [
        "compact_precip_total",
        "TOPO_BASIC_slope_mean"
      ],
      [
        "HIST_S2_ndvi_promedio_mean",
        "TOPO_BASIC_slope_mean"
      ],
      [
        "HIST_S2_ndvi_promedio_std",
        "TOPO_BASIC_slope_mean"
      ]
    ]
  },
  "support": "q95 train LOO nearest-neighbor radius; >=5 supported parcels and >=80percent corners; no predictions on unsupported corners",
  "permutation": "joint rainfall3 and joint history2; MayNDVI and slope separately; within validation climate profile; min10 eligible; empirical training-neighbor gate added for expanded conditional permutations",
  "expected_fits": 6435,
  "expected_models": 975,
  "expected_oof": 17526,
  "workers": 6,
  "no_final_training": true,
  "no_PRED": true,
  "no_XGB_fit": true,
  "no_ensemble": true,
  "no_residual": true,
  "decision": "stop after E1-E3; descriptive error covariance only; never optimize combination weights on external OOF",
  "cache_sha": {
    "outputs/modeling/family_7/expansion/v1/cache/frozen65_splits.joblib": "e4bc85766377b3f3b8a2f5a12aa3dc1a43d73d2ae7aa36cc6d8cc6244e26e130",
    "outputs/modeling/family_7/expansion/v1/cache/train138_exact_features.parquet": "6be568a66d02846b9d78d1944c5cf1e029c49854a4900fe5b5d43a785f9ad9b1"
  },
  "source_sha": {
    "src/family_7/expansion/execution.py": "056a6a7b13dd663fff082d4e9b500f1e4be2c96c61c42bf4327df7b4ead1031e",
    "src/family_7/models.py": "e8153eb94850755241f329a5a982d6246420058f6dde0a796bcd8e559923005d",
    "src/family_6/execution.py": "a799a73c024928ca4d21b17ebf01736519a94848eb02b9355133ae06bfa64581",
    "src/family_4/conditional_response.py": "10a15b9ba07f83e190f7b496b4bda8549cc32565ca9ca9a5eec94afdc69d651b"
  }
}
```
