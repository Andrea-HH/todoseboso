> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Síntesis conjunta: señal continua, reglas de corrección y peso del experto

Se probaron las cuatro alternativas de árboles inicialmente autorizadas y, tras la aclaración del usuario, dos correctores continuos. Se conservaron J7_BOTH y CT3, las 65 particiones y las validaciones internas. No se promovió un modelo TOP20/TOP15 ni se generaron PRED59.

## La alternativa continua solicitada

Las diferencias respecto a vecinos se usaron como **variables explicativas de la corrección**, no como reglas manuales. Se construyeron seis contrastes a partir de tres señales (cambio EVI, TPI y dinámica de heterogeneidad NDVI), usando vecinos geográficos o similares en compact4. El corrector Elastic Net no incluye intercepto ni centra los contrastes: si todas las diferencias son cero, el ajuste es cero. Se ajusta a residuos J7 cross-fitted y se limita a ±0.5 t/ha. No agrega de nuevo compact4 ni aprende una corrección municipal fija.

| Modelo | Aleatoria RMSE / R² | Perfil RMSE / R² | Municipal RMSE / R² | Espacial RMSE / R² |
|---|---:|---:|---:|---:|
| J7_BOTH | 0.4864 / 0.6709 | 0.4890 / 0.6675 | 0.5808 / 0.5309 | 0.6808 / 0.3556 |
| CT3 | 0.5116 / 0.6361 | 0.5206 / 0.6232 | 0.5813 / 0.5302 | 0.6788 / 0.3594 |
| GEO_LINEAR | 0.4882 / 0.6686 | 0.4851 / 0.6728 | 0.5813 / 0.5302 | 0.7402 / 0.2383 |
| COMPACT_LINEAR | 0.4904 / 0.6656 | 0.4853 / 0.6725 | 0.5829 / 0.5277 | 0.7072 / 0.3047 |

No hay una mejora equilibrada. La espacial empeora aproximadamente 8.7% para GEO y 3.9% para COMPACT. El MAE espacial pasa de 0.5291 a 0.5959 y 0.5686. La reducción del sesgo medio no compensa el aumento de error y dispersión.

## La ventaja por perfil depende de dos casos

Al excluir 171 y 015 únicamente del cálculo de métricas, sin reajustar, la diferencia de RMSE por perfil frente a J7 cambia a **+0.000728 para GEO y +0.002581 para COMPACT**: ambas empeoran. La ganancia total de SSE por perfil es 0.523 y 0.497, pero esas dos parcelas aportan 0.607 y 0.795; el resto de la muestra tiene pérdida neta.

En aleatoria tampoco se corrigen consistentemente esas parcelas. Los errores de 171/015 son +2.1625/+2.0800 t/ha con J7, +2.1694/+2.0827 con GEO_LINEAR y +2.1806/+2.0833 con COMPACT_LINEAR. La pérdida aleatoria persiste al excluirlas.

En espacial, GEO_LINEAR empeora sobre todo en bloque 2 (+0.1955 RMSE) y bloque 1 (+0.0663), aunque mejora bloque 4 (−0.0238). COMPACT_LINEAR empeora bloques 1 y 2 (+0.0747 y +0.0397). Ninguna modifica el bloque 3. No se ajustaron parámetros para beneficiar o evitar esos bloques.

La opción de no ajustar se seleccionó en 42/50 folds aleatorios GEO y 39/50 COMPACT. Estos recuentos corresponden a decisiones internas, no a quitar retrospectivamente los modelos de peor evaluación.

## Incertidumbre estadística y significado de coeficientes

En los 20 contrastes de la ampliación continua, no hay una mejora que sobreviva a Holm. Sí se detecta deterioro aleatorio de COMPACT_LINEAR frente a J7: ΔRMSE +0.003949, intervalo bootstrap agrupado [0.001584, 0.006082], p de pérdida pareada ajustada 0.003. Esto corresponde a esta batería exploratoria; no corrige toda la selección histórica de modelos del proyecto.

Los coeficientes permiten expresar aumentos y disminuciones continuas según cada contraste. Se conservan su signo, magnitud y frecuencia no nula por protocolo/fold en `coefficients_by_fold.csv` y `coefficient_stability.csv`. Son parámetros predictivos regularizados y correlacionados, no efectos causales ni significancia individual. Su existencia no implica que la relación se transfiera a otra región.

## Qué aportaron las otras aplicaciones

Los árboles que solo reducen la contribución de J7 hacia CT3 muestran una pequeña mejora espacial: GEO_ATTENUATE 0.6749/0.3667 y COMPACT_ATTENUATE 0.6756/0.3655. La aleatoria empeora un poco y la ganancia espacial depende casi enteramente del bloque 1; al omitirlo, GEO queda prácticamente empatado y COMPACT empeora. Ninguna comparación de esa batería supera Holm. No hay control independiente de reducción global del peso que permita atribuir una aportación única a los contrastes.

Los correctores residuales arbóreos tampoco justifican incorporarse: RMSE espacial 0.7096 y 0.7152. La comparación de regresión continua y árbol es válida entre los correctores residuales; la atenuación del peso resuelve otra tarea y su resultado no demuestra por sí mismo superioridad de árboles como arquitectura.

El máximo contraste absoluto no constituye una alerta de incertidumbre estable. En aleatoria, su AUC para error absoluto>1 t/ha cae de 0.682 a 0.555 para vecinos compactos y de 0.624 a 0.491 para vecinos geográficos al excluir 171/015. En espacial las AUC son aproximadamente 0.501 y 0.558. La rareza de los predictores no equivale a un error grande, ni indica automáticamente su signo. No se recomiendan umbrales universales de confianza basados en este puntaje.

## Recomendación

**Conservar J7_BOTH y CT3. No integrar estos correctores continuos ni los correctores arbóreos.** La reducción condicionada del peso local queda como hipótesis exploratoria pequeña y regionalmente concentrada, no como un nuevo ganador. Antes de continuar esa dirección haría falta contrastarla con una reducción global del peso y evidencia territorial adicional; no se ejecutó automáticamente esa ampliación.

Se debilita la hipótesis de que estas tres señales, expresadas como diferencias vecinales y con estas regularizaciones, produzcan una corrección generalizable. No se rechaza toda señal contextual, toda corrección continua ni una explicación agronómica de las parcelas; el soporte de casos anómalos es pequeño, y las relaciones pueden variar entre territorios. Una diferencia respecto a una única media general sería una reparametrización con intercepto; las referencias específicas por parcela sí aportan una representación distinta, pero aquí no produjeron una ganancia estable.

## Entregables e integridad

- Libro conjunto: `outputs/modeling/neighbor_signal_linear/v1/evaluacion_contrastes_continuos_y_arboles.xlsx`.
- Tablas y predicciones: `combined_oof_residuals.parquet`, residuos por parcela, regiones, bloques, cuartiles, intraperfil, omisiones, ganancias y análisis sin 171/015 bajo `tables`.
- Reglas aplicadas de los árboles: `deployed_tree_rules_by_fold.csv` del entregable conjunto. Muestran los multiplicadores o ajustes finales; los textos originales de sklearn mostraban valores antes de contracción/acotación y no deben leerse como pesos aplicados.
- Resultados completos: [continuos y comparación conjunta](neighbor_signal_linear_results.md), [batería de árboles](neighbor_signal_contrasts_results.md), [interpretación de árboles](neighbor_signal_contrasts_conclusions.md).

Las referencias externas son exactas. La calibración base se compara mediante las puntuaciones internas de la opción nula entre ambas etapas. Se verifican predicciones, vecinos y exclusiones, límite del ajuste y anclaje cero. Pasaron nueve pruebas entre las nuevas representaciones, soporte de calibración y pipeline existente. Los respaldos para cero predictores variables están documentados y versionados; las 48 particiones aleatorias anteriores a la última corrección de implementación permanecen intactas. No se usaron rendimientos PRED, no se ajustó un modelo final138 ni se alteraron los modelos anteriores.
