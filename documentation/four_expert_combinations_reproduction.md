> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Reproducción de las seis combinaciones

**Documento histórico de la batería conL40.** La etapa actual selecciona26/14 como champions y utiliza la [ruta propia sinL40](current_champions_reproduction.md) para C-T3,26,14 yB1. Estas instrucciones se conservan para reproducir la investigación anterior, no son el punto de entrada actual.

Se requieren los datos y artefactos históricos locales que enumera `outputs/modeling/four_expert_combinations/v1/frozen_design.json`. El repositorio público sin datos/outputs no contiene por sí solo esos prerrequisitos. Las referencias anteriores se consultan sin sobrescribirlas.

## Preparación inicial

Sólo cuando no exista el diseño de esta ejecución:

```powershell
python scripts/503_prepare_four_expert_combinations.py
python scripts/508_verify_four_expert_fast.py
python scripts/515_verify_four_expert_tuner.py
```

El primer comando congela las seis mezclas, cuatro controles,65 folds originales y16 particiones nuevas97/41. Los siguientes verifican optimizaciones equivalentes; no seleccionan otra rejilla ni otro modelo. Los diseños/manifiestos ya existentes se conservan al reanudar.

## Entrenamiento y entrega

Ejecutar una sola instancia; los checkpoints completos se reutilizan:

```powershell
python scripts/516_run_four_expert_cached_tuner.py all
python scripts/507_run_four_expert_fast.py
python scripts/511_finalize_four_expert_combinations.py
python scripts/513_summarize_four_expert_combinations.py
python scripts/517_review_four_expert_results.py
```

El segundo comando recoge los81 checkpoints y verifica integridad; al estar completos no vuelve a entrenarlos. El finalizador ejecuta nueve pruebas, evaluación/replay, diagnósticos y Excel. La síntesis espera su finalización. La revisión final comprueba los límites convexos, la integridad de modelos y la interpretación específica de los resultados. Los scripts512/511/513 también permiten supervisar una ejecución en curso. La separación de colas usada durante esta investigación está registrada en `execution_topology.json`; no cambia los modelos ni las particiones.

## Equivalencia de las optimizaciones

- `performance_amendment.json`: mismo Ridge ponderado, selección de vecinos, intercepto, alpha y orden de empates;32 comparaciones reales de predicción con diferencia máxima4.44e−16.
- `tuner_performance_amendment.json`: C-T3 reutiliza imputación/escalado dentro de cada entrenamiento interno entre los12 puntos de la rejilla. Conserva su orden, semillas, media de RMSE por fold del selector original, desempate, ajuste final y puerta de convergencia.32 contextos reales conservaron parámetros, puntuaciones y predicciones exactamente. En columnas completamente vacías se usa la ruta original para preservar también sus advertencias.
- `evaluation_amendment.json`: el contraste pareado del banco97/41 suma diferencias OOF por parcela para respetar sus distintos números de apariciones; los65 folds originales tienen conteos iguales y sus contrastes no cambian.

La media por fold se conserva únicamente donde ya la usaba el selector original C-T3. Las métricas externas se calculan sobre OOF completas por repetición y luego se promedian. En97/41 se calculan sobre sus41 casos y se reportan aparte.

## Archivos de revisión

- `tables/oof_residuals.parquet`: predicción, respuesta, error, ID, protocolo, repetición, fold y ejecución.
- `models/`: expertos, mezcladores, referencias de soporte y predicciones internas por partición.
- `comparaciones_y_residuos.xlsx`: métricas, regiones, omisiones, cuartiles, intraperfil, pesos, contrastes y cambios por parcela.
- `audit/`: equivalencia, reconstrucciones y comprobaciones de fuentes.
- `delivery_audit.json`: integridad, pruebas y hashes de entregables.
- `documentation/four_expert_combinations_conclusions.md`: interpretación de la batería completa.

Las tablas retrospectivas que eligen el experto usando el rendimiento observado son diagnósticos no aplicables, no modelos ni límites inferiores de una mezcla convexa. Las nuevas particiones reutilizan los mismos138 rendimientos: no constituyen confirmación independiente. L40 conserva su PCA transductiva congelada en197 covariables. No hay ajuste final138, predicciones59 ni promoción de modelo TOP20/TOP15.
