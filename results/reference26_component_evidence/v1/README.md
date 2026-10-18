# Reference26: evidencia recuperada por componente y por función

**Se recuperaron resultados ya ejecutados; no se entrenó ningún modelo ni se hizo una nueva selección.** Champions vigentes: Reference26 y Compact14. Las tablas principales se refieren a las mismas65 particiones y138 rendimientos; cada celda es **RMSE t/ha / R²**. MAE, sesgo, diferencias y procedencia se conservan en CSV y Excel. El banco97/41 es independiente como tabla, no como muestra, y no tiene todas estas ablaciones: [comparación97/41](../../comparison_97_41/v1/README.md). No se mezclan sus cifras.

## Cómo interpretar el respaldo

La función asignada a un componente es una hipótesis arquitectónica. Una retirada emparejada permite estudiar su aporte condicional al resto; un control en una arquitectura anterior sólo aporta evidencia contextual. Una combinación que cambia tres piezas no atribuye su diferencia a una sola. Ninguna de estas comparaciones demuestra causalidad, optimalidad universal o significancia individual de26 entradas.

En las ablaciones ON de la batería factorial, se reajustaron coeficientes del corrector interno con residuos propios, **pero se heredaron de FULL7 sus hiperparámetros e intensidad del mismo entrenamiento**. Por tanto, una retirada de bloque no equivale necesariamente a eliminar sus fuentes de toda la calibración. Las reconstrucciones OFF/GLOBAL de14 y12 sí verificaron independencia de las fuentes retiradas.

## 1. Núcleo C-T3: ancla agroclimática

Función: ofrecer una estimación global estable de cantidad/distribución de lluvia y vegetación temprana; también permitir corregir errores del experto local. La evidencia específica de sus cuatro entradas está en [asociación y ablaciones recientes](../../core4_relevance/v1/README.md): total, fracción temprana y NDVI tienen respaldo más consistente; HHI muestra debilidad espacial. Esto no se transfiere automáticamente a su doble uso dentro de26.

Los pesos aprendidos de26 muestran cuánto usa el sistema esa ancla. No son reglas manuales por protocolo ni p-valores de relevancia:

| Protocolo | Peso medio experto7 | Peso medio C-T3 | Amplitud media corrector interno | Corrección R3 absoluta media, t/ha |
|---|---|---|---|---|
| random | 0.720 | 0.280 | 0.470 | 0.0464 |
| climate_profile | 0.704 | 0.296 | 0.409 | 0.0476 |
| municipality | 0.099 | 0.901 | 0.471 | 0.0316 |
| spatial | 0.482 | 0.518 | 0.500 | 0.1020 |

En municipal, la mezcla asigna en promedio sólo≈.099 al experto y≈.901 a C-T3 **antes de R3**. Es evidencia del mecanismo de respaldo aprendido, no de que el experto aislado generalice a municipios nuevos ni de una regla que debamos programar con esos porcentajes.

## 2. Siete señales locales: relevancia conjunta y sustitutos

Función: permitir que una regresión por vecindario distinga parcelas con condiciones vegetativas y relieve diferentes. Se recuperaron estas retiradas, manteniendo gate geológico, corrector interno y R3 con recalibración posterior:

| Modelo / variante | Aleatoria | Perfil | Municipal | Espacial |
|---|---|---|---|---|
| 26 completo | 0.4748 / 0.6865 | 0.4774 / 0.6831 | 0.5752 / 0.5400 | 0.6333 / 0.4423 |
| Sin media/std NDVI histórico del local | 0.4748 / 0.6865 | 0.4775 / 0.6829 | 0.5758 / 0.5390 | 0.6359 / 0.4378 |
| Sin las dos Planet del local | 0.4745 / 0.6869 | 0.4782 / 0.6821 | 0.5738 / 0.5422 | 0.6333 / 0.4424 |
| Sin media/std NDWI2025 del local | 0.4750 / 0.6861 | 0.4791 / 0.6809 | 0.5764 / 0.5380 | 0.6334 / 0.4423 |
| Sin pendiente media del local | 0.4748 / 0.6865 | 0.4816 / 0.6775 | 0.5740 / 0.5419 | 0.6318 / 0.4451 |

- **NDVI histórico, media/std:** quitar ambos apenas cambia aleatoria, empeora algo perfil/municipal y espacial. Su aporte marginal es pequeño en esta composición. La historia NDVI sigue en R3; no es una prueba de retirar toda la historia.
- **Planet, cambios de dirección EVI y delta NDVI junio–agosto:** retirarlos mejora ligeramente aleatoria/municipal/espacial, pero pierde por perfil. Pueden describir dinámica temporal, pero no hay respaldo de necesidad universal ni de que cada señal sea indispensable.
- **NDWI2025, media/std:** la retirada empeora ligeramente aleatoria/perfil/municipal y prácticamente no cambia espacial. Respaldo observado pequeño y dependiente del sistema; no prueba de humedad del suelo o anegamiento.
- **Pendiente media:** retirarla pierde por perfil y mejora algunas otras cifras. Pendiente mínima sigue en R3. El estudio respalda un compromiso contextual de relieve, no que la pendiente media tenga un aporte positivo uniforme.

Para los tres pares de señales se evaluó la retirada conjunta, **no cada columna por separado**. Su información puede estar compartida con otras señales. Los siete predictores no son siete componentes PCA ni siete variables con p-valores individuales significativos.

## 3. Vecinos geográficos y Ridge local

Función: construir un referente territorial con rendimientos conocidos y permitir relaciones locales. En26 se conservan24 vecinos geográficos, Ridge alpha30 y ponderación inversa de distancia. Las coordenadas eligen vecinos; las siete señales son predictores de la regresión, no la distancia de selección.

Los controles históricos de [reducción del experto GeoC](../../../documentation/geoc_signal_research_results.md) compararon local sin clima con media ponderada de los mismos vecinos: RMSE aleatorio≈.4911 frente a.4974 y espacial≈.9807 frente a.9807. La proximidad recuperaba gran parte del comportamiento; la regresión añadía una diferencia menor. Es evidencia contextual sobre otro experto, **no una comparación Ridge7 frente a media o frente a Ridge global dentro del26 final**.

No se recuperó una prueba que demuestre que k24 sea óptimo para26. Los k8/16/24/48/72 de las investigaciones de correctores locales corresponden a **otro mecanismo**, no al experto geográfico de26. La función de vecinos está implementada y auditada, pero su indispensabilidad y número óptimo en esta receta no están aislados. [Funcionamiento exacto](../../../documentation/models/Reference26/README.md).

## 4. Corrector interno: complementar al Ridge con el núcleo compacto

Función: aprender, mediante Elastic Net sobre las cuatro entradas C-T3, patrones en residuos OOF del experto local. Tiene coeficientes propios; no es sumar otra vez la predicción C-T3.

| Modelo / variante | Aleatoria | Perfil | Municipal | Espacial |
|---|---|---|---|---|
| 26 con interno | 0.4748 / 0.6865 | 0.4774 / 0.6831 | 0.5752 / 0.5400 | 0.6333 / 0.4423 |
| Misma familia sin interno | 0.4770 / 0.6836 | 0.4840 / 0.6743 | 0.5799 / 0.5325 | 0.6549 / 0.4037 |
| Interno y peso global | 0.4757 / 0.6853 | 0.4742 / 0.6873 | 0.6033 / 0.4940 | 0.6475 / 0.4170 |
| Sin interno y peso global | 0.4774 / 0.6830 | 0.4784 / 0.6818 | 0.5755 / 0.5395 | 0.6397 / 0.4311 |

Quitar sólo esa capa con gate geológico pierde en los cuatro protocolos. **Es uno de los respaldos condicionales más claros de una función del26**, aunque las diferencias no sobreviven el ajuste múltiple de aquella batería. Con peso global, mantener el interno perjudica municipal y espacial frente a quitarlo. La capa no es siempre beneficiosa por sí sola: depende de cómo se mezcla el experto con C-T3.

## 5. Compuerta geológica: repartir confianza entre expertos

Función: usar composición geológica para agrupar parcelas y aprender pesos convexos con contracción hacia un peso global. No estima directamente rendimiento con diez coeficientes ni selecciona los24 vecinos.

| Modelo / variante | Aleatoria | Perfil | Municipal | Espacial |
|---|---|---|---|---|
| Geología10 + interno | 0.4748 / 0.6865 | 0.4774 / 0.6831 | 0.5752 / 0.5400 | 0.6333 / 0.4423 |
| Peso global + interno | 0.4757 / 0.6853 | 0.4742 / 0.6873 | 0.6033 / 0.4940 | 0.6475 / 0.4170 |
| PCA2 de las diez proporciones + interno | 0.4748 / 0.6864 | 0.4774 / 0.6831 | 0.5735 / 0.5428 | 0.6301 / 0.4480 |
| Peso global sin interno | 0.4774 / 0.6830 | 0.4784 / 0.6818 | 0.5755 / 0.5395 | 0.6397 / 0.4311 |

Con el interno conservado, reemplazar geología por un peso global pierde aleatoria, municipal y espacial, aunque mejora por perfil. La mayor pérdida municipal respalda su función de asignación de confianza **en esa composición**. PCA2 conserva resultados próximos, pero mantiene las diez entradas originales y añade una transformación: no es un gate de dos mediciones.

Quitar interno y geología conjuntamente reduce mucho la pérdida frente a las retiradas individuales. La interacción MSE municipal≈−.0381 y espacial≈−.0379 documenta no aditividad; no es un efecto causal. Tampoco se probó retirar una por una las diez categorías para identificar una categoría imprescindible. La compuerta es una alternativa útil, **no la única manera respaldada de combinar expertos**.

## 6. R3: corregir estructura residual con soporte explícito

Función: corregir errores de la mezcla mediante nivel histórico NDVI mínimo, persistencia de heterogeneidad anómala2025 y pendiente mínima. Se ajusta a residuos propios cross-fitted, es global, conserva signo aprendido y está limitado a±.25t/ha. La máscara apaga el ajuste cuando falta un indicador.

| Modelo / variante | Aleatoria | Perfil | Municipal | Espacial |
|---|---|---|---|---|
| Base26 sin R3 | 0.4865 / 0.6708 | 0.4913 / 0.6644 | 0.5835 / 0.5266 | 0.6894 / 0.3393 |
| 26 con R3 y máscara | 0.4748 / 0.6865 | 0.4774 / 0.6831 | 0.5752 / 0.5400 | 0.6333 / 0.4423 |
| Alternativa global sin R3 | 0.4907 / 0.6651 | 0.4964 / 0.6574 | 0.6105 / 0.4818 | 0.6856 / 0.3464 |
| Alternativa global con R3 | 0.4774 / 0.6830 | 0.4784 / 0.6818 | 0.5755 / 0.5395 | 0.6397 / 0.4311 |

R3 mejora los cuatro protocolos en ambas arquitecturas recuperadas. En26 espacial pasa de.6894 a.6333, con mejora también en las otras validaciones. **Es el respaldo observado más consistente de un bloque completo**; no demuestra que cada indicador sea indispensable. Puede mejorar un agregado y perjudicar una región. Los CSV/Excel conservan regiones, omisiones y magnitud de ajuste para examinar ese límite.

### Qué respaldo existe para sus tres indicadores

| Modelo / variante | Aleatoria | Perfil | Municipal | Espacial |
|---|---|---|---|---|
| J7 anterior sin corrector | 0.4864 / 0.6709 | 0.4890 / 0.6675 | 0.5808 / 0.5309 | 0.6808 / 0.3556 |
| J7 + persistencia y pendiente mínima | 0.4802 / 0.6793 | 0.4802 / 0.6793 | 0.5746 / 0.5409 | 0.6528 / 0.4075 |
| J7 + NDVI floor, persistencia y pendiente mínima | 0.4756 / 0.6854 | 0.4748 / 0.6865 | 0.5726 / 0.5442 | 0.6550 / 0.4035 |
| J7 + R3 y FAPAR floor | 0.4755 / 0.6856 | 0.4765 / 0.6843 | 0.5782 / 0.5351 | 0.6615 / 0.3916 |
| J7 + nueve indicadores | 0.4855 / 0.6722 | 0.4894 / 0.6670 | 0.5811 / 0.5306 | 0.6705 / 0.3750 |

**NDVI floor:** R3 frente a R2 añade únicamente esa representación, con corrección recalibrada en la base J7 anterior. Mejora aleatoria/perfil/municipal y empeora ligeramente espacial: aporte contextual, no ventaja universal dentro del26. **Persistencia y pendiente mínima:** se recuperó evidencia del conjunto R2/R3, pero no retiradas individuales exactas de cada una dentro del26 final. No se les asigna un p-valor ni una ganancia propia inventada. FAPAR adicional y nueve indicadores no mejoran uniformemente a R3; más información no produjo automáticamente mejor predicción.

Los109 casos con historia completa y29 incompletos de entrenamiento tienen distinto soporte. La máscara es una protección ante falta de referencia histórica; su efecto aislado con los mismos coeficientes y fuerza R3 no queda demostrado por el mero contraste añadir/quitar R3. Las sensibilidades antiguas de atenuación por vecinos mezclan disponibilidad y ponderación; no prueban una regla universal de corregir más a parcelas atípicas.

## 7. Arquitectura completa: simplificación y función compartida

| Modelo / variante | Aleatoria | Perfil | Municipal | Espacial |
|---|---|---|---|---|
| 26 actual | 0.4748 / 0.6865 | 0.4774 / 0.6831 | 0.5752 / 0.5400 | 0.6333 / 0.4423 |
| 16: experto7, global, sin interno, con R3 | 0.4774 / 0.6830 | 0.4784 / 0.6818 | 0.5755 / 0.5395 | 0.6397 / 0.4311 |
| 14 actual | 0.4773 / 0.6832 | 0.4793 / 0.6805 | 0.5755 / 0.5395 | 0.6431 / 0.4250 |
| 12: NDWI y pendiente, global, R3 | 0.4775 / 0.6829 | 0.4806 / 0.6789 | 0.5753 / 0.5398 | 0.6452 / 0.4212 |
| 12: historia NDVI y pendiente, global, R3 | 0.4792 / 0.6806 | 0.4819 / 0.6772 | 0.5754 / 0.5397 | 0.6434 / 0.4244 |

14 elimina Planet, interno y geología con pérdidas pequeñas de RMSE, y mejora algunas métricas de sesgo/MAE. Es evidencia de sustitución y complementariedad, no prueba de que las piezas retiradas carezcan de señal. La auditoría podada comprobó independencia de esas fuentes para14. Ninguna combinación domina todos los protocolos, municipios y extremos; la pequeña diferencia26–14 no certifica equivalencia.

## Fuerza estadística, faltantes y conclusión defendible

Las familias archivadas contienen:

| Batería | Contrastes archivados | Superan Holm al5% |
|---|---|---|
| architecture | 412 | 0 |
| base_distribution | 332 | 0 |
| indicator_neighborhoods | 208 | 0 |

Se conservan sus ajustes originales: no se recalcularon p-valores con una familia menor para hacerlos significativos. Falta de significancia no demuestra ausencia de aporte ni equivalencia; hay sólo nueve municipios y cinco bloques. Los intervalos y contrastes sobre OOF fijas no incorporan toda la selección histórica o incertidumbre de reentrenamiento. Muchos experimentos usan las mismas138 etiquetas.

**Qué puede afirmarse:**26 combina una base global, un referente local y una corrección residual con funciones explícitas y mejoras condicionales observadas. R3 y el corrector interno tienen respaldo de bloque; el gate ayuda en ciertas composiciones; las siete señales contienen sustitutos; k24 y las26 columnas no quedaron certificados como necesarios individualmente.

**Qué falta realmente:** sensibilidad HHI en los dos usos de26; retiradas individuales de los pares locales si se necesita atribución por columna; retiradas individuales de persistencia/pendiente mínima; contraste local7 versus media y Ridge global dentro del26; sensibilidad propia k del experto; confirmación con rendimientos independientes. Este informe no ejecuta esas nuevas pruebas ni cambia champions.

## Fuentes, tablas y reproducción

[Ficha26](../../../documentation/models/Reference26/README.md) · [Descomposición factorial](../../../documentation/architecture_decomposition_conclusions.md) · [Bases y distribución](../../../documentation/base_distribution_correction_conclusions.md) · [Reducción R3](../../../documentation/indicator_neighborhoods_conclusions.md) · [Simplificación J7](../../../documentation/joint_simplification_results.md).

Script: `python scripts/531_recover_reference26_evidence.py`. [Auditoría](audit.json) verifica igualdad de métricas del26 con el registro vigente. [Procedencia](provenance.json) conserva hashes de tablas recuperadas. [Contrastes por componente](component_contrasts.csv), [inventario de evidencia de26 variables](variable_role_evidence26.csv), [métricas](architecture_metrics.csv), [pruebas archivadas seleccionadas](archived_tests_selected.csv) y [dependencias de calibración](complexity_and_calibration_dependencies.csv). Excel privado: `outputs/research/reference26_component_evidence/v1/evidencia_componentes26.xlsx`, con hojas regionales y omisiones. No se publican predicciones o filas por parcela.
