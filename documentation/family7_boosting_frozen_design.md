# F7 — Auditoría y diseño congelado

Primera ejecución limitada a F7-00 (CatBoost) y F7-01 (XGBoost), directos sobre las mismas cuatro entradas de C-T3/F5-01/F6-E0. Las 138 etiquetas y las 65 particiones externas, con sus cuatro particiones internas originales, permanecen intactas. No se ajusta modelo final, ni se consultan 59 PRED para decidir, ni se modifica Champion/F5/F6.

RS3 utilizó diez resúmenes CLIMATE_precip_, no compact3+NDVI de mayo. Reutilizó parámetros de Family2 para subfamilias y solo tiene validación aleatoria compatible. RS4 incorpora historia de 15/16 campos como corrección residual. RS5 explora un segundo residuo con bloques topográficos, sin aislar la pendiente media. RS6/Champion encadena Elastic Net climático TOP20 → XGBoost histórico → Ridge topográfico. Sus objetivos residuales, representaciones y arquitectura difieren de F7 directo sobre rendimiento. La auditoría copia los parámetros realmente guardados; no reajusta configuraciones equivalentes. Champion se compara únicamente en los 50 folds aleatorios compatibles y mediante métricas recalculadas de OOF completas; su RMSE publicado como media por fold no se mezcla.

F6-E se conserva: historia NDVI2 y pendiente mejoraron espacialmente frente a Extra Trees compacto pero perjudicaron municipal; DTRstd empeoró los cuatro protocolos. DTR queda como sensibilidad potencial, sin concluir irrelevancia agronómica. Lluvia mensual abril–octubre es control conceptual, sin ejecución inicial.

Total = suma de siete lluvias abril–octubre 2025; fracción temprana = lluvia abril–junio / (total+1e-6); HHI = suma de cuadrados de fracciones mensuales con ese denominador. May NDVI = media de observaciones válidas Sentinel-2 en mayo2025. Historia NDVI2 resume siete promedios de meses calendario 2022–24: std entre esos meses, no variación interanual. Pendiente media es TOPO_BASIC_slope_mean, alias de slope_degrees, DEM120m; no es humedad ni manejo. Esta representación usa lluvia de toda la temporada y no constituye pronóstico disponible en mayo.

CatBoost aprende árboles simétricos de profundidad2/3, L2 de hoja10/30, aprendizaje.03/.06 e iteraciones150/300 en ocho combinaciones predefinidas. Sin bootstrap y random_strength=0 para aislar boosting, border_count64 y estimación de hoja de una iteración. SymmetricTree no impone una cota de mínimo de observaciones por hoja mediante min_data_in_leaf; se documentan hojas vacías y pequeñas. XGBoost usa hist64, profundidad2/3, los mismos pares de aprendizaje/árboles/L2, min_child_weight10 y L1=1, todas las filas/columnas. Bajo squared error sin pesos ni submuestreo, Hessiano=1 y min_child_weight coincide con el soporte de construcción, distinto del soporte posterior al enrutar filas completas. No se afirma que ambos algoritmos tengan regularización numéricamente equivalente.

Se seleccionan ocho configuraciones por algoritmo mediante RMSE medio de cuatro folds internos originales; empates a diez decimales favorecen el primer candidato. Imputación, escalado y eliminación de constantes ocurren en cada entrenamiento correspondiente. Se usa rendimiento en su escala nativa; no hay early stopping ni eval_set externo. Solo se conservan modelos internos de la configuración elegida y el externo, además de OOF/registro de todos los candidatos. Los límites no se amplían después de resultados.

E1/E2/E3 quedan prospectivamente asignadas a CatBoost, por el contraste metodológico de árboles simétricos conservadores con Extra Trees; esta elección precede a las OOF F7. E1 añade historia2; E2 pendiente; E3 ambos. Ninguna extensión se ejecuta antes de revisión del usuario. Si se cambia después el algoritmo usando OOF externas, será decisión exploratoria, no confirmación independiente. E3 requerirá comparar contra ambos bloques por separado, sin suponer aditividad.

Interpretabilidad: ablaciones con reajuste previas se conservan como evidencia; no hay bloques nuevos ajustados en esta etapa. Permutación conjunta condicionada al mismo perfil climático de validación, con mínimo10 parcelas elegibles; núcleo lluvia3 se permuta conjuntamente, MayNDVI aparte. Bloque constante dentro de perfiles se marca no identificable, no cero importancia. Esta condición no controla todas las otras covariables. ALE de cuatro cuantiles e interacciones de terciles se calculan solo con cinco parcelas respaldadas y80% de esquinas dentro de radio q95 de distancias al vecino de entrenamiento excluyendo sí mismo. Los huecos sin soporte no se conectan. Las tres interacciones lluvia–NDVI quedan fijadas; NDVI–historia y lluvia–pendiente se difieren hasta E1–E3. Frecuencia, ganancias y umbrales son diagnósticos descriptivos, no causas. No se usa SHAP para afirmaciones causales.

Métricas principales: 138 OOF completas por repetición, después promedio de diez repeticiones aleatorias. Perfil, municipal y espacial tienen una repetición. Métricas por fold son diagnósticas. Se comparan pérdidas pareadas, sesgo versus dispersión, pares intraperfil del mismo modelo, regiones, omisiones de bloques/municipios y1/5/10 casos sin reajustar. Selección interna y evaluación externa permanecen separadas; folds/repeticiones/casos compartidos no son réplicas independientes y no se declara superioridad estadística.

Se detiene tras F7-00/F7-01 para revisión. La recomendación siguiente distinguirá continuar hacia complementos, revisar regularización o detener arquitectura. Un experimento residual solo se propone; no se ejecuta. Fuentes técnicas primarias: https://catboost.ai/docs/en/concepts/parameter-tuning y https://xgboost.readthedocs.io/en/stable/parameter.html .


Configuraciones exactas:

```json
{
  "CatBoost": [
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
  "XGBoost": [
    {
      "n_estimators": 150,
      "max_depth": 2,
      "learning_rate": 0.03,
      "reg_lambda": 10,
      "min_child_weight": 10,
      "reg_alpha": 1
    },
    {
      "n_estimators": 300,
      "max_depth": 2,
      "learning_rate": 0.03,
      "reg_lambda": 10,
      "min_child_weight": 10,
      "reg_alpha": 1
    },
    {
      "n_estimators": 300,
      "max_depth": 2,
      "learning_rate": 0.06,
      "reg_lambda": 10,
      "min_child_weight": 10,
      "reg_alpha": 1
    },
    {
      "n_estimators": 300,
      "max_depth": 2,
      "learning_rate": 0.03,
      "reg_lambda": 30,
      "min_child_weight": 10,
      "reg_alpha": 1
    },
    {
      "n_estimators": 150,
      "max_depth": 3,
      "learning_rate": 0.03,
      "reg_lambda": 10,
      "min_child_weight": 10,
      "reg_alpha": 1
    },
    {
      "n_estimators": 300,
      "max_depth": 3,
      "learning_rate": 0.03,
      "reg_lambda": 10,
      "min_child_weight": 10,
      "reg_alpha": 1
    },
    {
      "n_estimators": 300,
      "max_depth": 3,
      "learning_rate": 0.06,
      "reg_lambda": 10,
      "min_child_weight": 10,
      "reg_alpha": 1
    },
    {
      "n_estimators": 300,
      "max_depth": 3,
      "learning_rate": 0.03,
      "reg_lambda": 30,
      "min_child_weight": 10,
      "reg_alpha": 1
    }
  ]
}
```
