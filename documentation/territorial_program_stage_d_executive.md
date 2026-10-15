# Etapa D — Síntesis ejecutiva para FIRA

**El programa identifica candidatos con fortalezas diferentes, pero no un ganador universal ni una validación externa concluida.** Las 138 etiquetas de2025 se han reutilizado para descubrir y comparar hipótesis. Nuevas particiones de esas mismas etiquetas no sustituyen nuevos rendimientos.

Para parcelas semejantes a las observadas, Champion continúa como referencia histórica. La mezcla fija50/50 mejora ligeramente en validación aleatoria, pero parte importante de su ganancia depende de pocas parcelas y no tiene evaluación geográfica equivalente.

Para municipios no representados, lluvia compacta + NDVI mayo (C-T3) es el candidato más defendible de esta investigación. Su ventaja municipal se compara con lluvia mensual + NDVI en las mismas parcelas/folds; no demuestra transferencia entre campañas, ni un beneficio universal dentro de Chignahuapan. Su compresión resume cantidad, fracción temprana y concentración temporal de lluvia.

| index | experiment | protocol | RMSE | MAE | n_parcels | n_repeats |
| --- | --- | --- | --- | --- | --- | --- |
| 8 | C-H0M | climate_profile | 0.51777 | 0.38212 | 138 | 1 |
| 9 | C-H0M | municipality | 0.63945 | 0.47859 | 138 | 1 |
| 10 | C-H0M | random | 0.50945 | 0.36840 | 138 | 10 |
| 11 | C-H0M | spatial | 0.67244 | 0.52226 | 138 | 1 |
| 12 | C-T1 | climate_profile | 0.56029 | 0.40777 | 138 | 1 |
| 13 | C-T1 | municipality | 0.68540 | 0.51500 | 138 | 1 |
| 14 | C-T1 | random | 0.52412 | 0.37360 | 138 | 10 |
| 15 | C-T1 | spatial | 0.60047 | 0.44654 | 138 | 1 |
| 16 | C-T3 | climate_profile | 0.52060 | 0.39150 | 138 | 1 |
| 17 | C-T3 | municipality | 0.58126 | 0.46033 | 138 | 1 |
| 18 | C-T3 | random | 0.51158 | 0.37495 | 138 | 10 |
| 19 | C-T3 | spatial | 0.67878 | 0.53061 | 138 | 1 |
| 20 | CHAMPION | random | 0.49813 | 0.35887 | 138 | 10 |
| 25 | F4-S1 | climate_profile | 0.52626 | 0.38889 | 138 | 1 |
| 26 | F4-S1 | municipality | 0.67110 | 0.49856 | 138 | 1 |
| 27 | F4-S1 | random | 0.50483 | 0.36411 | 138 | 10 |
| 28 | F4-S1 | spatial | 0.73904 | 0.57291 | 138 | 1 |
| 29 | FIXED_50_50 | random | 0.49360 | 0.35343 | 138 | 10 |

El bloque espacial3 contiene 35 etiquetas. La menor cifra espacial de C-T1 y C-T3 depende fuertemente de sus errores en ese bloque. Al omitirlo solo del cálculo, sin volver a entrenar, la ventaja de C-T3 se revierte. Este resultado impide prometer una mejora general para otras regiones.

La ventaja municipal de C-T3 resiste omitir del cálculo sus cinco mayores beneficiarios, aunque mejora el error cuadrático de solo 54 de 138 parcelas. Es una reducción importante de algunos errores grandes, no una mejora para la mayoría. La dependencia espacial es territorial: el bloque 3 muestra distinta temporalidad de lluvia/DTR y una sobreestimación regional del modelo base. No se ha demostrado el mecanismo que causa ese patrón.

El intercepto jerárquico no mejora de manera consistente frente al control Ridge equivalente. La pérdida intraperfil tampoco justifica sustituir el entrenamiento convencional. Añadir temperatura, suelo, relieve o índices vegetales no asegura una mejora: asociación agronómica y utilidad incremental del modelo son preguntas diferentes.

Dentro de perfiles idénticos quedan diferencias grandes que clima no puede distinguir. NDVI mayo aporta contraste parcelario y la dinámica LAI aporta una mejora local pequeña. No hemos resuelto la heterogeneidad local ni demostrado que sea irreducible. Conviene verificar rendimientos/superficies y medir fechas, variedad, manejo y suelo real antes de añadir complejidad.

Decisiones actuales: preservar Champion; congelar la mezcla para comparación aleatoria independiente, C-T3 para municipios, F4-S1 como referencia sencilla y C-T1 como hipótesis espacial. Mantener Ridge como control. No integrar jerarquía, pérdidas adicionales ni cartografía50k sin geometrías fiables.

Prioridades de validación: municipios nuevos para comprobar C-T3, una nueva campaña para comprobar estabilidad temporal, y parcelas adicionales de varios perfiles repetidos si la prioridad es explicar diferencias locales. El tamaño se decidirá por precisión, municipios/campañas independientes y recursos; no por contar parejas ni por sumar diez repeticiones de las mismas etiquetas.

Los intervalos jerárquicos nominales90% subcubren perfiles nuevos municipales y son mucho más amplios en espacio. No deben usarse como garantía operacional. Cualquier calibración futura necesita datos separados.

Etapa D no entrenó modelos, no produjo nuevas estimaciones predictivas ni alteró Champion, mezcla, folds, etiquetas o resultados A–C. El reporte técnico, matriz de evidencia, protocolo prospectivo y auditoría sustentan estas decisiones. Las cifras y límites de esta síntesis provienen de `metrics_summary.csv`, `block_composition.csv`, `spatial_block_gains.csv`, `spatial_block_omission.csv`, `gain_concentration.csv` y `archived_interval_calibration.csv`.
