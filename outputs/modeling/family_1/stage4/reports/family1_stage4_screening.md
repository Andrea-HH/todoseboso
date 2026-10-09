# Familia 1 — Etapa 4, Ronda 1: screening supervisado

## Resumen ejecutivo

Se evaluaron 12 pipelines sobre exactamente los mismos 50 outer folds (RepeatedKFold 5×10), con tuning y todo el preprocesamiento dentro de inner CV de 4 folds. Se guardaron 16,560 predicciones OOF. No se entrenó el modelo final, no se predijeron las 59 parcelas y no se ejecutó Ronda 2.

## Respuestas

1. **Menor RMSE medio:** XGB_CORE, RMSE=0.5270 t/ha.
2. **Menor RMSE mediano:** XGB_CORE, RMSE mediano=0.5220.
3. **Mayor estabilidad:** LOCAL_PCA_RIDGE tiene la menor std (0.0841) pero desempeño pobre; dentro del grupo competitivo, ENET_ALL es el más estable (std=0.0925).
4. **Superación del baseline:** baseline RMSE=0.8520. Todos los modelos lo superan en 100% de folds salvo LOCAL_PCA_RIDGE (80%). No se aplicó t-test ingenuo.
5. **CORE vs ALL:** ENET: delta medio=-0.0059, mediano=-0.0046, 60% de folds gana ENET_ALL; PLS: delta medio=-0.0009, mediano=-0.0002, 50% de folds gana PLS_ALL; PCR: delta medio=+0.0056, mediano=+0.0049, 42% de folds gana PCR_ALL; LGBM: delta medio=+0.0103, mediano=+0.0066, 24% de folds gana LGBM_ALL.
6. **Estabilidad Elastic Net:** {'ENET_ALL': {'features_selected_ge_80pct': 8, 'features_selected_any_fold': 172}, 'ENET_CORE': {'features_selected_ge_80pct': 0, 'features_selected_any_fold': 168}}. La frecuencia por feature está en `elasticnet_feature_frequency.csv`.
7. **PLS y ALL:** delta medio=-0.0009, mediano=-0.0002, 50% de folds gana PLS_ALL.
8. **PCA global:** PCR_CORE RMSE=0.5565; PCR_ALL=0.5622. Comparar con ENET/PLS indica si la compresión no supervisada preservó la dirección predictiva.
9. **PCA local vs global:** LOCAL=0.7792; delta medio=+0.2171, mediano=+0.2159, 0% de folds gana LOCAL_PCA_RIDGE. La PCA local no debe avanzar si la pérdida es consistente.
10. **LightGBM ALL:** delta medio=+0.0103, mediano=+0.0066, 24% de folds gana LGBM_ALL; su RMSE ALL=0.5436.
11. **XGBoost/CatBoost:** XGB_CORE=0.5270; CAT_CORE=0.5545; frente a LGBM_CORE=0.5333. Aportan algoritmos distintos, pero el paso a Ronda 2 depende de mejora y estabilidad, no sólo de un fold.
12. **Standard vs Robust:** ENET_CORE: Standard 29/50, Robust 21/50; PLS_CORE: Standard 30/50, Robust 20/50. Robust no mejora consistentemente; adoptar StandardScaler como default.
13. **Componentes seleccionados:** {'LOCAL_PCA_RIDGE': {'median': 1104.5, 'min': 1006.0, 'max': 1115.0}, 'PCR_ALL': {'median': 20.0, 'min': 10.0, 'max': 20.0}, 'PCR_CORE': {'median': 20.0, 'min': 10.0, 'max': 20.0}, 'PLS_ALL': {'median': 2.0, 'min': 2.0, 'max': 2.0}, 'PLS_CORE': {'median': 2.0, 'min': 2.0, 'max': 5.0}}.
14. **Candidatos para Ronda 2:** XGB_PRUNED; LGBM_PRUNED/CORE_TOPOADV/CORE_EXTENDED; ENET_PRUNED/CORE_TOPOADV/CORE_EXTENDED. XGB_CORE, LGBM_CORE y ENET_ALL forman el grupo principal.
15. **Descartes antes de source ablation:** LOCAL_PCA_RIDGE; LGBM_ALL; PCR_ALL; PLS_ALL; y CAT_CORE salvo interés explícito como contraste. Mantener baseline sólo como referencia. No hacer ablation hasta revisar este reporte.

## Notas metodológicas

- Incertidumbre pareada: percentiles 2.5/97.5 de los 10 deltas medios por repetición; es descriptiva y no supone 50 folds independientes.
- X4 PRUNED se auditó por train fold sin usar y, pero no se entrenó porque pertenece a Ronda 2.
- CatBoost se limitó a 25/50 iteraciones, depth=3 y L2=10 como screening regularizado proporcional a n=138.
- Los archivos `obsolete_cat_grid*` son checkpoints archivados de configuraciones abortadas por costo/contención y no forman parte de resultados.
