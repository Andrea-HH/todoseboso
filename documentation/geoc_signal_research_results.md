> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Investigación de señales GeoC y reducción del experto local

Se ejecutaron las 56 recetas y controles definidos antes del entrenamiento, sobre las 65 particiones externas originales. No se modifica el Champion ni se generan modelos finales o predicciones nuevas de las 59 parcelas. Resultados en `outputs/modeling/geoc_signal_research/v1`.

**Recomendación:** conservar la mezcla física anterior como referencia y avanzar con la mezcla de experto reducido SMALL12 como candidata de simplificación. Esta fase encuentra una reducción grande de entradas con cambios predictivos pequeños; no demuestra superioridad, equivalencia estadística ni una nueva combinación ganadora. No conviene añadir las correcciones residuales de 12/30 variables a C-T3 tal como se implementaron aquí.

## Qué se comparó

- A: retirar familias y todos sus derivados, reconstruir PCA20 y reajustar la corrección compacta. Comparación emparejada con el local completo y con local + corrector. Las familias se solapan y tienen tamaños distintos.
- B: expertos locales con 12 o 30 variables predefinidas; originales estandarizadas o PCA3/5/8. Se mantiene Ridge geográfica de 24 vecinos, alfa30 y pesos originales. Se compara cada modo fijo y un selector interno.
- C: correcciones Ridge de C-T3 con esos conjuntos; controles de coordenadas, estado y municipio.
- D: usar esos conjuntos para aprender pesos entre C-T3 y el experto grande; controles territoriales equivalentes.
- E: sustituir al experto grande por uno pequeño manteniendo la mezcla global o la mezcla física BOTH de textura/fase y geología.

El diseño exacto, listas, límites, referencias y hashes están en `frozen_design.json` y `documentation/geoc_signal_research_design.md`. Los modos, amplitudes y pesos se deciden dentro del entrenamiento externo. Las etiquetas y folds ya participaron en exploraciones anteriores: estos resultados son exploratorios, no una confirmación independiente.

«Sin clima» significa que se retiraron las columnas climáticas explícitas y sus derivados documentados, no que la representación sea estadísticamente independiente del clima. Vegetación, humedad espectral, suelo y geografía pueden compartir gradientes regionales con la lluvia; los agregados y otros sensores también pueden recoger parte del comportamiento de mayo. La ablación no demuestra separación física completa entre ambos expertos.

## Resultado predictivo principal

RMSE en t/ha; menor es mejor. Aleatoria es la media de las métricas calculadas sobre las OOF completas de cada una de las 10 repeticiones. No se promedian RMSE de folds.

| Receta | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| C-T3 | 0.511582 | 0.520604 | 0.581259 | 0.678778 |
| Local sin clima + corrector compacto, experto grande | 0.487910 | 0.497101 | 0.661346 | 0.802610 |
| Mezcla física BOTH anterior, experto grande | 0.485226 | 0.499572 | 0.584656 | 0.681142 |
| Mezcla física BOTH, experto SMALL12 | 0.489733 | 0.491141 | 0.580630 | 0.683286 |
| Mezcla física BOTH, experto EXPANDED30 | 0.490173 | 0.485892 | 0.582362 | 0.685574 |
| C-T3 + corrector SMALL12 | 0.513186 | 0.525837 | 0.633095 | 0.701708 |
| C-T3 + corrector EXPANDED30 | 0.513016 | 0.521848 | 0.599510 | 0.680411 |

La mezcla SMALL12 cambia frente a BOTH grande en +0.004507 / −0.008431 / −0.004026 / +0.002144. Conserva un desempeño cercano reduciendo las entradas del experto de 1,831 a12, pero no mejora todos los protocolos. EXPANDED30 mejora más por perfil y no justifica por sí sola sus 18 entradas adicionales. Las correcciones directas de C-T3 no consiguen una mejora consistente.

R² de SMALL12 BOTH: 0.666432 / 0.664611 / 0.531258 / 0.350857. MAE: 0.349862 / 0.345419 / 0.460134 / 0.530092. Su sesgo espacial es +0.295453 t/ha, frente a +0.284157 de BOTH grande y +0.191161 de C-T3. Parecerse en RMSE no significa tener idéntica calibración.

## El hallazgo sobre la geografía

| Base local o control | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| Ridge local PCA20 sin clima | 0.491146 | 0.503259 | 0.761675 | 0.980671 |
| Media ponderada de los mismos vecinos, sin características | 0.497362 | 0.506613 | 0.758166 | 0.980664 |
| Media de vecinos + corrector compacto reajustado | 0.491976 | 0.497457 | 0.657315 | 0.791517 |

La media de vecinos recupera gran parte del comportamiento de esta receta. Las predicciones del local completo y esa media tienen correlación media0.995 en aleatoria; su diferencia RMS es0.066 t/ha. Con corrección compacta, la diferencia RMS es0.066 / 0.045 / 0.030 / 0.036 t/ha. Estos números describen concordancia entre predicciones; no equivalencia estadística ni rendimiento correcto.

Se calculó además la complejidad efectiva condicional del Ridge local, manteniendo fijos vecindario, representación y pesos: `1 + sum(lambda/(lambda+30))`, donde lambda son los autovalores del Gram ponderado y centrado local. El experto grande tiene una media de2.75 / 2.17 / 1.50 / 1.83 grados efectivos, incluido el intercepto. Los20 componentes disponibles no equivalen a20 efectos locales libres: dentro de los vecindarios hay poca variación efectiva y una regularización fuerte. SMALL12 BOTH tiene1.56 / 1.50 / 1.14 / 1.17. Esta medida no incluye selección de representación, ajuste del corrector ni aprendizaje de la mezcla.

Por tanto, sería incorrecto afirmar que el modelo demuestra que1,831 variables físicas son necesarias o que usa intensamente todas ellas. También sería incorrecto declarar que ninguna tiene información: el resultado depende de esta regularización, vecindarios y representación. Una familia puede tener sustitutos correlacionados.

## Qué familias sostienen la señal

Ninguna retirada produce un deterioro importante y consistente en los cuatro protocolos. Ejemplos del cambio de RMSE frente al experto grande + corrector:

| Familia retirada, incluyendo derivados | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| Vigor histórico | +0.003495 | −0.003304 | +0.000674 | −0.001744 |
| Proxies espectrales de agua históricos | −0.000942 | +0.000193 | −0.000792 | +0.011883 |
| Vigor actual | −0.000283 | −0.001020 | +0.000146 | +0.010003 |
| SoilGrids | +0.000971 | −0.001110 | +0.001194 | −0.006330 |
| Topografía | +0.000037 | −0.000075 | +0.000036 | −0.001304 |

Son contribuciones condicionales a toda la receta, no porcentajes aditivos ni importancia causal. Retirar topografía del PCA no retira topografía de otros modelos. Retirar coordenadas del PCA tampoco retira la selección geográfica de vecinos. La ablación de vigor mensual abril–junio se solapa con vigor actual; no identifica mayo de manera aislada.

El control FULL_INDUCTIVE20, con las mismas1,831 entradas pero transformaciones ajustadas solo en entrenamiento, obtiene0.488567 / 0.492108 / 0.660351 / 0.801747 después de corregir. No cambia sustancialmente la conclusión. Las ablaciones A conservan el esquema original de PCA sobre X197 sin Y para aislar la retirada de familias; B–E reducidos utilizan preparación inductiva. Nunca se utilizan los rendimientos PRED.

## Qué variables concretas quedan en SMALL12

| Entradas | Señal representada |
|---|---|
| Media y desviación histórica del NDVI Sentinel-2 | Nivel y variabilidad del vigor histórico |
| Media y desviación histórica del MSI Sentinel-2 | Nivel y variabilidad de un proxy espectral de estrés hídrico |
| Fracción de cambios de dirección del EVI Planet2025 | Forma temporal, sin equivaler a fechas de siembra observadas |
| Cambio del NDVI Planet de junio a agosto2025 | Evolución estacional |
| Media y desviación del NDWI Sentinel-22025 | Comportamiento espectral asociado al agua |
| Arcilla, densidad aparente y carbono orgánico SoilGrids0–30cm | Propiedades edáficas estimadas |
| Pendiente media oficial | Relieve |

Los nombres técnicos, fórmulas y advertencias de las30 candidatas están en `audit/selected_definitions_30.csv`. No se demuestra que cada una de las12 sea indispensable. No se realizaron12 ablaciones individuales nuevas después de observar resultados.

La mezcla reducida completa tampoco tiene solo12 variables: necesita las4 de C-T3 y del corrector compacto; las12 del experto;15 entradas del gate físico (textura/fase,10 proporciones geológicas y3 distancias); y2 coordenadas para elegir vecinos. Son33 campos en esos roles, sin contar ID ni el target. El gate no usa directamente las coordenadas, pero el experto sí. La lista completa está en `diagnostics/reduced_mixture_input_inventory.csv`. Reducir el PCA no convierte la arquitectura completa en una regresión de12 coeficientes.

El selector interno SMALL12 BOTH utiliza originales/PCA3/5/8 según el fold. En las50 particiones aleatorias elige respectivamente9/16/7/18 veces. No hay un único número de componentes universalmente seleccionado. La reducción facilita estudiar señales y calcular el experto, pero conserva el costo conceptual de vecindarios, corrección y gate.

## Pesos, territorios e intraperfil

El modelo sigue la estructura `C-T3 + w(z)*(experto_reducido − C-T3)`, con0≤w≤1. El experto reducido es a su vez `local_reducido + amplitud*ElasticNet_compacto(residuo_local)`. Este último usa las mismas cuatro entradas compactas, pero no los coeficientes de C-T3. Los pesos y amplitudes se estiman con predicciones internas; no se asignan correcciones manuales por municipio.

El peso medio externo del experto SMALL12 es0.695 / 0.723 / 0.065 / 0.399. La cercanía municipal a C-T3 se explica en parte por ese peso pequeño: no demuestra que el experto reducido aislado transfiera bien. Estos promedios describen lo aprendido en los folds; no son pesos manuales por protocolo para un modelo final.

SMALL12 BOTH mejora levemente frente a BOTH grande en municipal al omitir cualquiera de sus cinco folds del cálculo. Su diferencia espacial cambia de signo al omitir el bloque3: sin él pasa de un deterioro total de0.002144 a una mejora de0.001702. Por tanto, ni la diferencia global pequeña ni un solo bloque justifican declarar vencedor.

Municipal: SMALL12 BOTH obtiene0.57983 en Chignahuapan,0.46926 en Calpulalpan y0.88749 en Singuilucan; C-T3 obtiene0.58068 / 0.49335 / 0.86769. La mezcla no resuelve automáticamente Singuilucan. Espacial: su bloque3 tieneRMSE0.92203 frente a0.91257 de BOTH grande y0.90959 de C-T3.

Intraperfil se comparan diferencias entre parcelas del mismo perfil y del mismo fold de evaluación. Con igual peso por perfil, SMALL12 BOTH obtieneRMSE0.57920 / 0.53285 / 0.52557 / 0.53285; BOTH grande0.57034 / 0.53752 / 0.52351 / 0.53638. Con peso por par el orden puede cambiar: no hay mejora intraperfil universal. En perfil hay soporte en12 perfiles repetidos y107 parcelas; los1,073 pares no son observaciones independientes. La documentación y tablas conservan ambos pesos.

Las ganancias y deterioros individuales se entregan en `parcel_gains_mean_repeat.csv` y `largest_changes.csv`, junto con errores por estado, municipio y fold y omisiones sin reajuste. No se usan esos diagnósticos para modificar retrospectivamente la receta.

## Controles administrativos y coordenadas

Los gates de estado/municipio mejoran algunos resultados aleatorios y por perfil, pero no transfieren mejor que BOTH en municipal/espacial. El gate municipal obtiene0.483201 / 0.484160 / 0.603057 / 0.703793. En municipal reproduce el peso global porque las categorías evaluadas no fueron vistas; su corrector categórico reproduce exactamente C-T3 allí. No se inventa un efecto para municipios nuevos.

La corrección Ridge de coordenadas sobre C-T3 obtiene0.509851 / 0.518613 / 0.569755 / 0.651023. Es una señal exploratoria, no una recomendación: al excluir el bloque3, su cambio espacial deRMSE frente a C-T3 pasa de−0.027755 a+0.082521. Empeora los bloques1 y2 y aumenta el sesgo espacial total de+0.191 a+0.301t/ha. El menorRMSE se debe a menor dispersión de errores, no a menor sesgo global. No demuestra haber recuperado variabilidad física intraperfil.

## Incertidumbre y siguiente paso

Ninguno de los224 contrastes primarios supera Holm al5%. Los intervalos bootstrap por conglomerados y las pruebas de signos son exploratorios de las OOF fijas; no incorporan toda la incertidumbre de reentrenamiento, la búsqueda histórica ni la dependencia espacial residual. Hay43 perfiles climáticos TRAIN,9 municipios y solo5 bloques espaciales. La falta de significación no prueba equivalencia.

La siguiente investigación justificada sería un contraste pequeño y congelado entre la mezcla BOTH grande, SMALL12 BOTH y un experto aún más simple de media geográfica + corrector compacto bajo el mismo gate. El control de media existente aquí todavía no se evaluó dentro de ese gate: no atribuirle resultados que no tiene. Esto aislaría si vale la pena conservar el PCA, sin abrir otra búsqueda masiva de variables. Para afirmar valor físico único, después habría que mostrar mejora incremental e intraperfil frente a estos controles y validarla con datos realmente nuevos.

No recomiendo ampliar automáticamente las variables, profundizar correctores ni elegir reglas por municipio a partir de estos folds. La prioridad es simplificar y comprobar estabilidad. Se conserva la referencia anterior hasta una revisión explícita.

## Reproducción y archivos

1. `python -m pytest tests/test_geoc_signal_research.py -q --basetemp <directorio_nuevo_en_outputs>`: cuatro pruebas aprobadas antes de ejecutar.
2. `python scripts/436_prepare_geoc_signal_research.py`: diseño, hashes, inventarios y PCA de ablaciones. Protege una ejecución ya preparada.
3. `python scripts/437_run_geoc_signal_research.py`:65 particiones; checkpoints reanudables y modelos guardados. Protege resultados completos.
4. `python scripts/438_summarize_geoc_signal_research.py`: métricas, contrastes, replay independiente, Excel y figura.
5. `python scripts/439_geoc_signal_structural_diagnostics.py`: concordancia, grados efectivos condicionales e inventario completo de la mezcla reducida; sin reajustes.
6. `python scripts/440_finalize_geoc_signal_research.py`: comprueba referencias archivadas, respuestas ante municipios inéditos e inventarios; incorpora diagnósticos adicionales al Excel y sella la entrega.

Los scripts se ejecutan desde la raíz con las dependencias del proyecto. Usar un hilo BLAS/OpenMP por proceso; el runner utiliza cuatro procesos. El entrenamiento tardó2,289.9s de reloj. Se registraron cuatro advertencias de convivencia de bibliotecas OpenMP; la ejecución terminó sin errores de ajuste ni fallos de convergencia reportados. La auditoría definitiva de hashes, separación y reproducción se guarda en `manifest.json` y `audit/`.

La entrega verifica111,228 filas OOF (100,464 nuevas y10,764 de referencia),3,835 reproducciones de modelos por fold con diferencia máxima0 y181,152 comprobaciones de exclusión. Las cinco referencias recuperadas permanecen idénticas, al igual que los archivos protegidos por hashes.

Se registran459 usos del fallback en cachés profundas:51 contextos por nueve variantes del experto (21 municipales y30 espaciales). Allí no hay grupos o parcelas suficientes para retunear la corrección compacta: se usa únicamente la base local, según la política congelada, sin sustituir el protocolo por validación aleatoria. El ajuste final de cada fold externo sí dispone de su entrenamiento correspondiente; este desajuste de tamaño y complejidad entre niveles limita la interpretación de los pesos. No son459 folds externos fallidos.

El Excel es `resultados_senales_y_reduccion_GeoC.xlsx`; predicciones en `tables/predictions.parquet`, modelos por fold en `models/` y decisiones en `diagnostics/selection_by_fold.csv`. Outputs continúa excluido de Git; no se hizo push ni se modificó el otro repositorio.
