# Calendarios, Sentinel e historia: resultados del modelado pendiente

Ejecutado el 14 de octubre de 2026. **Las nuevas representaciones no desplazan de forma equilibrada al núcleo compacto de lluvia y NDVI de mayo.** El CatBoost compacto confirma sus ventajas agregadas ya conocidas. Añadir ventanas, EVI, humedad espectral o historia no produce una mejora consistente entre protocolos. No se declara un nuevo champion ni superioridad estadística.

## Ejecución y comparabilidad

La batería principal contiene 17 bloques para Elastic Net y CatBoost, con los mismos 65 folds externos y sus particiones internas originales: 2,210 modelos externos. Se completó un suplemento de tres adiciones espectrales directas a compact4: otros 390 modelos. En total: **40 configuraciones, 2,600 modelos externos y 71,760 predicciones OOF nuevas**.

Los 189,800 ajustes nominales incluyen los candidatos internos y ajustes externos completados. No incluyen intentos internos incompletos al reanudar procesos. No representan nuevas muestras: seguimos teniendo 138 rendimientos de 2025. Los años 2022–2024 aportan contexto X, sin repetir Y2025 como etiquetas históricas.

Imputación, escalado, selección y regularización se ajustan exclusivamente dentro del entrenamiento correspondiente. Elastic Net utiliza L1 para eliminar coeficientes y selecciona también el peso histórico, incluyendo la opción de omitirlo. CatBoost utiliza los ocho candidatos conservadores originales, profundidades 2/3 y 150/300 árboles; sin early stopping externo. Los pesos históricos de selección de divisiones son 0.5, frente a 1 para 2025: una preferencia, no un porcentaje de la predicción.

Se recuperaron C-T3, F7-00, F5-01, EQUAL3 y el Ridge anterior sin modificarlos. Los controles CAL00 se ajustan bajo el criterio interno común de esta batería; no son reproducciones idénticas de las búsquedas antiguas. Por eso distinguimos mejora de representación y cambio de procedimiento.

El suplemento se definió después de ver la batería principal para cerrar un hueco de comparador: EVI y humedad se habían añadido a CAL04, una base ampliada débil, en lugar de directamente a compact4. Se congelaron las tres hipótesis espectrales y se probaron todas. Es exploratorio sobre las mismas etiquetas, **no confirmación independiente**. Sus archivos y diseño permanecen separados.

## Resultados principales

RMSE en t/ha; menor es mejor. Aleatoria es la media de métricas sobre OOF completas de cada una de las diez repeticiones. Los otros protocolos tienen una repetición completa de 138 parcelas. No son medias de RMSE por fold.

| Modelo | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| C-T3 archivado, compact4 | 0.5116 | 0.5206 | 0.5813 | 0.6788 |
| F7-00 archivado, CatBoost compacto | 0.5049 | 0.5153 | 0.5282 | 0.6426 |
| EQUAL3 archivado | 0.4982 | 0.4979 | 0.5277 | 0.6709 |
| EN_CAL00: compact4 | 0.5117 | 0.5190 | 0.5758 | 0.6779 |
| CB_CAL00: compact4 | 0.5054 | 0.5191 | 0.5271 | 0.6442 |
| EN_CAL02: lluvia + Tmax por ventanas y NDVI mayo | 0.4975 | 0.5032 | 0.8393 | 0.6253 |
| CB_CAL02: mismas entradas | 0.5215 | 0.5343 | 0.7074 | 0.7641 |
| CB_CAL03: compact4 + trayectoria NDVI | 0.5156 | 0.5452 | 0.5203 | 0.7786 |
| CB_CAL04: clima + trayectoria 2025 | 0.5274 | 0.5844 | 0.6899 | 0.7981 |
| CB_CAL05: CAL04 + historia NDVI | 0.5290 | 0.5945 | 0.6718 | 0.7618 |
| CB_CAL10: CAL04 + EVI + NDWI/MSI | 0.5363 | 0.5609 | 0.7026 | 0.8158 |
| CB_CAL11: CAL04 + historia climática | 0.5279 | 0.5849 | 0.6787 | 0.7969 |
| CB_CAL13: compact4 + satélite trimestral | 0.5207 | 0.5220 | 0.5440 | 0.7595 |
| CB_CAL14: compact4 + satélite de siete meses | 0.5167 | 0.5197 | 0.5327 | 0.7273 |
| CB_CAL15: clima trimestral/temporada + NDVI mayo | 0.5192 | 0.5293 | 0.6012 | 0.6613 |

El CatBoost compacto nuevo es prácticamente igual al F7-00 ya conocido. Su ventaja no proviene de las nuevas variables. Tampoco domina todos los objetivos: su MAE por perfil es 0.4027, frente a 0.3915 de C-T3, y varios errores intraperfil son mayores. C-T3, CatBoost compacto y EQUAL3 siguen ofreciendo compromisos distintos.

## Clima: ganancia localizada y transferencia desigual

EN_CAL02 mejora aleatoria y perfil, pero el R² municipal cae a **0.0206**, frente a 0.5302 de C-T3. Sus R² aleatorio, por perfil y espacial son 0.6558, 0.6480 y 0.4564, respectivamente. Mejor ajuste agregado no garantiza transferencia municipal.

Su ganancia espacial depende nuevamente del bloque 3: RMSE 0.9096 → 0.4698 frente a C-T3. El bloque 4 empeora 0.7990 → 1.1041. Al omitir el bloque 3 del cálculo, sin reajustar, EN_CAL02 queda **0.0901 t/ha peor** que C-T3. El bloque 3 contiene 31 parcelas de Tlaxcala y cuatro de Hidalgo; el 4 es principalmente Singuilucan.

En validación municipal, EN_CAL02 obtiene RMSE 0.9083 en Chignahuapan y 1.2979 en Singuilucan, frente a 0.5807 y 0.8677 de C-T3. Subestima más Chignahuapan y sobreestima más Singuilucan. CatBoost no rescata esta representación: CAL02 queda peor territorialmente que su control compacto.

## EVI y humedad sobre el comparador correcto

Resultados del suplemento directo, sin añadir simultáneamente las ventanas climáticas ampliadas:

| Adición a compact4 | Algoritmo | Aleatoria | Perfil | Municipal | Espacial |
|---|---|---:|---:|---:|---:|
| Ninguna | Elastic Net | 0.5117 | 0.5190 | 0.5758 | 0.6779 |
| EVI en cuatro ventanas | Elastic Net | 0.5257 | 0.5388 | 0.5942 | 0.7243 |
| NDWI/MSI en cuatro ventanas | Elastic Net | 0.5215 | 0.5313 | 0.5834 | 0.7180 |
| EVI + NDWI/MSI | Elastic Net | 0.5280 | 0.5421 | 0.6064 | 0.7333 |
| Ninguna | CatBoost | 0.5054 | 0.5191 | 0.5271 | 0.6442 |
| EVI en cuatro ventanas | CatBoost | 0.5157 | 0.5226 | 0.5215 | 0.7476 |
| NDWI/MSI en cuatro ventanas | CatBoost | 0.5184 | 0.5248 | 0.5233 | 0.7561 |
| EVI + NDWI/MSI | CatBoost | 0.5253 | 0.5244 | 0.5235 | 0.8081 |

Los tres suplementos Elastic Net empeoran los cuatro RMSE. Con CatBoost aparecen pequeñas mejoras municipales, pero grandes pérdidas espaciales. Para EVI, la mejora municipal es solo 0.0056 t/ha y el deterioro espacial es 0.1034.

Con EVI, el bloque espacial 3 pasa de 0.8794 a 1.1282; el 4 mejora ligeramente de 0.5298 a 0.5005. El deterioro espacial global persiste al omitir cualquiera de los cinco bloques. La pequeña mejora municipal se revierte al omitir Cuautepec del cálculo: no es un beneficio territorial sólido.

Sobre la base CAL04, EVI y humedad también producen intercambios entre protocolos. Su combinación mejora el RMSE por perfil de CatBoost de 0.5844 a 0.5609, pero empeora aleatoria, municipal y espacial. Sus beneficios individuales no se suman de manera equilibrada.

## Historia y desviaciones de 2025

En CAL05, **Elastic Net elige omitir toda la historia NDVI en 61 de 65 folds**: 48 de los 50 aleatorios, todos los de perfil y cuatro de cinco en municipal y espacial. CatBoost sí usa historia: medianas de tres variables históricas en aleatoria y cuatro en espacial. Mejora algunos errores de la base CAL04, pero no alcanza al compacto y empeora otros protocolos.

La historia climática tampoco es simplemente irrelevante: EN_CAL11 mejora municipal de 0.8543 a 0.6654 respecto de EN_CAL04, pero empeora espacial de 0.7090 a 0.9554. Es información con transferencia desigual, insuficiente para recomendar su integración.

Las desviaciones de 2025 no resuelven el problema. Current + historia y current + desviación son reparametrizaciones del mismo espacio lineal cuando hay datos completos; las diferencias bajo penalización e imputación no prueban información nueva. No se incluyeron simultáneamente current, media y delta. Algunas asociaciones descriptivas entre anomalías y ganancias son indefinidas cuando el modelo elige exactamente la base y la ganancia es constante.

## Trimestres y temporada completa

Se construyó un panel adicional de 24 variables anuales para 2022–2025, con historia y diferencias calculadas de la misma forma. Pasaron los 120 controles independientes de reconstrucción.

Los trimestres son abril–junio y julio–septiembre. La temporada abril–octubre incluye también octubre: la comparación cambia tanto anchura como cobertura temporal. No identifica exclusivamente un efecto de suavizado.

El resumen satelital de siete meses hace menos daño que los trimestres en CatBoost, pero ninguno supera al compacto. La representación climática CAL15 mejora a CAL02 en los cuatro protocolos de CatBoost, mostrando que la representación importa dentro de una arquitectura. Aun así, queda peor que CB_CAL00 en los cuatro RMSE.

Se conserva el NDVI exclusivo de mayo. No se inventan fechas parcelarias ni se incluyen noviembre–diciembre. Las referencias históricas no certifican que todos los años correspondan al mismo cultivo.

## Selección y complejidad

Medianas sobre los 50 ajustes externos aleatorios, correspondientes a las diez repeticiones completas:

| Bloque | Entradas | Elastic Net: seleccionadas | CatBoost: utilizadas |
|---|---:|---:|---:|
| compact4 | 4 | 4 | 4 |
| CAL04: clima + NDVI por ventanas | 14 | 9 | 12 |
| CAL10: multiespectral completo | 26 | 10 | 20 |
| compact4 + EVI | 8 | 6 | 8 |
| compact4 + EVI/NDWI/MSI | 16 | 6 | 13 |

Elastic Net elimina coeficientes; CatBoost utiliza variables en divisiones. Usar cuatro variables en 150–300 árboles no equivale en complejidad a una regresión de cuatro coeficientes. Las hojas potenciales son capacidad estructural, no grados de libertad independientes.

En EN_CAL10, lluvia de mayo–junio y Tmax de abril se conservan en el 100% de los folds aleatorios; NDVI de mayo, en el 96%. EVI/MSI de abril aparecen con menor frecuencia y coeficiente mediano cero. CatBoost utiliza EVI de abril en el 100% de esos folds, sin que eso se traduzca en mejora OOF. **Frecuencia de selección no equivale a utilidad incremental ni a causalidad.**

Las cifras provisionales comunicadas durante las primeras cuatro repeticiones pueden diferir de estas medianas finales. Los archivos de estabilidad separan protocolos y denominadores.

## Diferencias entre parcelas del mismo perfil

Las señales satelitales sí distinguen parcelas, pero no reducen consistentemente el error de sus diferencias de rendimiento. El RMSE intraperfil aleatorio ponderado por pares es 0.7712 para C-T3, 0.7997 para CB_CAL00 y 0.8334 para CB_CAL10. En espacial: 0.7675, 0.7894 y 0.8401.

Hay mejoras puntuales al dar igual peso a cada perfil: CB_CMP_EVI espacial obtiene 0.5278 frente a 0.5401 de C-T3. Sin embargo, ponderando por pares empeora de 0.7675 a 0.8034. No se resuelve la heterogeneidad intraperfil de forma consistente. Los pares comparten parcelas y no son observaciones independientes.

## Verificación y límites numéricos

Pasaron siete pruebas automatizadas y los 120 controles nuevos de agregación temporal. Los replays recargaron los **2,600 modelos y reprodujeron exactamente las 71,760 predicciones nuevas**, con diferencia máxima 0.0. Se verificaron los IDs retenidos y los hashes protegidos.

Se registraron tres ConvergenceWarning en candidatos internos de EN_CAL12, repetición aleatoria 2, folds 1 y 5. Los modelos externos guardados de esos contextos usan 700 y 697 iteraciones, lejos del límite 100,000, y eligen omitir historia. No se ampliaron las rejillas retrospectivamente. Las advertencias limitan la precisión de esos candidatos de tuning y están conservadas en la auditoría.

El entorno emite también una advertencia de coexistencia Intel/LLVM OpenMP fuera de los ajustes. Se conserva en runtime_notes.json. No hubo discrepancias en los replays. La optimización de concurrencia afecta únicamente el número de hilos de predicción/importancia posterior al entrenamiento; no cambia candidatos ni aprendizaje. Los tiempos registrados, con varias reanudaciones, no son un benchmark limpio entre algoritmos.

## Recomendación

Mantener el núcleo compacto y las referencias anteriores. **No promover una ampliación ni continuar por ahora una búsqueda amplia de ventanas e índices.** La evidencia debilita estas representaciones regionales y estos agregados históricos bajo Elastic Net y CatBoost conservador; no rechaza toda historia ni todas las señales satelitales.

Antes de ampliar más el inventario, priorizar datos independientes sobre fechas de establecimiento/cosecha, cultivo histórico y calidad de observaciones. No se ejecutó esa nueva línea. No usar estos errores para fijar correcciones municipales, excluir parcelas o afirmar superioridad estadística sobre etiquetas repetidamente reutilizadas.

## Entregables

El paquete único de revisión está en `outputs/modeling/agronomic_calendar/completed_expansion_summary/v1/`: métricas de los 52 experimentos (40 nuevos y 12 referencias), OOF nuevas en CSV/Parquet, selección, complejidad, intraperfil, regiones y comparaciones pareadas.

Los modelos, búsquedas internas y auditorías permanecen separados en `expansion/v1/` y `compact_spectral_addendum/v1/`. La figura principal está en `expansion/v1/diagnostics/rmse_vs_ct3.png`.

Scripts 397–404 y módulos `src/calendar_expansion.py` y `src/calendar_execution.py`. El diseño principal está en `documentation/agronomic_calendar_expansion_design.md`; cada batería conserva su JSON congelado.

No se sobrescribieron Champion ni modelos anteriores, no se ajustó un modelo final con las 138 etiquetas y no se generaron predicciones PRED.
