> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Descomposición y combinaciones: resultados e interpretación

## Conclusión

Hay simplificaciones útiles con pérdida pequeña en las métricas agregadas, pero no una mejora universal. La combinación de retirar el corrector interno y sustituir el gate geológico por un peso global aprende una mezcla distinta que puede funcionar con14 o12 entradas, sin Planet ni geología. Retirar únicamente el corrector interno perjudica los cuatro protocolos. Las interacciones entre componentes importan: no se pueden sumar las ganancias o pérdidas de cada retirada.

La batería fija comprendió48 bases (ocho conjuntos locales × corrector interno ON/OFF × tres gates), cada una sola y con R3_MASK, más tres controles:99 entradas sobre los65 folds originales. No se seleccionó una arquitectura usando el fold externo, no hubo nuevas fuentes/screenings, y se conservaron138 respuestas, referencias, Champion y PRED59. Estas comparaciones siguen siendo exploratorias sobre particiones ya utilizadas.

## Tabla principal

Cada celda es RMSE t/ha / R². Pred./calib. distingue entradas activas para predecir de las necesarias para la calibración de hiperparámetros de esta batería. Las ablaciones ON transfieren hiperparámetros del experto FULL7 dentro del mismo entrenamiento, aunque reajustan sus coeficientes con residuos propios. Por eso, menos entradas predictivas ON no equivale automáticamente a eliminar la fuente de toda la calibración.

| Modelo con R3_MASK | Pred./calib. | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---|---|---|---|
| Actual: FULL7 + interno + gate geológico | 26/26 | .4748 / .6865 | .4774 / .6831 | .5752 / .5400 | .6333 / .4423 |
| FULL7 sin interno + peso global | 16/16 | .4774 / .6830 | .4784 / .6818 | .5755 / .5395 | .6397 / .4311 |
| Sin Planet ni interno + peso global | 14/14 | .4773 / .6832 | .4793 / .6805 | .5755 / .5395 | .6431 / .4250 |
| NDWI + pendiente, sin interno + peso global | 12/12 | .4775 / .6829 | .4806 / .6789 | .5753 / .5398 | .6452 / .4212 |
| Historia NDVI + pendiente, sin interno + peso global | 12/12 | .4792 / .6806 | .4819 / .6772 | .5754 / .5397 | .6434 / .4244 |
| Sin Planet, interno conservado, gate PCA2 | 24/26 | .4744 / .6869 | .4781 / .6822 | .5719 / .5453 | .6317 / .4452 |
| Sin pendiente media, interno conservado, gate PCA2 | 25/26 | .4749 / .6863 | .4811 / .6782 | .5722 / .5447 | .6299 / .4483 |
| NDWI + pendiente, interno conservado, gate geológico | 22/26 | .4742 / .6873 | .4788 / .6812 | .5744 / .5412 | .6378 / .4344 |

El menor RMSE aleatorio de esta batería es .47415, no supera el .4725 / .6895 de vecinos satelitales DIRECT de una etapa anterior con protocolos compatibles. El menor RMSE espacial puntual, .62990, pierde por perfil. No se declara un nuevo Champion ni se presenta una sensibilidad escogida externamente como confirmación independiente.

## 1. Quitar el corrector interno: depende del resto del sistema

Con FULL7 y gate geológico, quitarlo cambia RMSE aleatoria/perfil/municipal/espacial de .4748/.4774/.5752/.6333 a .4770/.4840/.5799/.6549: pierde en los cuatro. R3 no sustituye sin pérdida esa capa manteniendo intacta la mezcla geológica.

Con gate GLOBAL, mantenerlo produce .4757/.4742/.6033/.6475; quitarlo deja .4774/.4784/.5755/.6397. Se pierde algo en aleatoria/perfil y se recupera mucha transferencia municipal. Frente al modelo actual, la combinación FULL7_OFF_GLOBAL pierde .0026 aleatoria, .0009 por perfil, .0003 municipal y .0063 espacial; a cambio elimina geología y una capa de Elastic Net.

La interacción descriptiva en MSE entre quitar interno y cambiar a gate GLOBAL es −.0381 (t/ha)² municipal y −.0379 espacial. La combinación perjudica mucho menos de lo que sugeriría sumar retiradas individuales. No es un efecto causal ni se suman RMSE. El archivo MSE_interactions contiene las interacciones dobles y triples por repetición.

R3 sigue siendo importante: FULL7_OFF_GLOBAL sin R3 tiene .4907/.4964/.6105/.6856. Con R3_MASK pasa a .4774/.4784/.5755/.6397. La simplificación conserva la corrección final, no elimina todas las correcciones.

## 2. Reducir el gate

GLOBAL aprende un peso convexo escalar entre C-T3 y el experto local usando sus predicciones OOF; no es promedio fijo50/50. El peso es común a las consultas del mismo modelo entrenado. Las coordenadas siguen formando los24 vecinos del experto, aunque se elimina geología.

PCA2 se ajusta sólo con entrenamiento sobre raíces centradas de las diez proporciones geológicas, conservando el tratamiento original de composición. Retiene, en promedio,48.5% de varianza aleatoria,50.3% por perfil,55.0% municipal y54.8% espacial. Es pérdida considerable de varianza; no implica perder igual proporción de información predictiva. Las cargas y varianza por fold se entregan en tablas. No se asocian los componentes con causas agronómicas sin evidencia adicional.

FULL7_ON_PCA2 tiene .4748/.4774/.5735/.6301, cerca del actual y con mejoras puntuales municipal/espacial. Sigue necesitando26 entradas y añade una transformación PCA. Reduce dimensión del espacio del gate, no las diez mediciones originales ni necesariamente la complejidad total.

La alternativa NO_PLANET_ON_PCA2 mejora ligeramente aleatoria, municipal y espacial frente a la referencia, pero pierde .0006 por perfil. Al omitir el bloque1 de la métrica espacial, la mejora se convierte en deterioro de .0049 t/ha. La variante sin pendiente media también pierde su ganancia espacial al omitir ese bloque. No son mejoras espaciales uniformes.

## 3. Dos modelos compactos reproducidos sin fuentes retiradas

Las opciones OFF/GLOBAL de14 y12 entradas se reconstruyeron además con un pipeline podado independiente: sin variables Planet/geología y sin calibración del experto FULL7. Para NDWI_SLOPE se retiraron también las columnas locales de media/std de NDVI histórico. Se conservaron las tres variables históricas/topográficas de R3 que correspondían. La auditoría source_independence verifica las mismas predicciones BASE/MASK en los65 folds; esto es reproducción, no otro experimento ni otro banco de confirmación.

### Modelo de14 entradas: NO_PLANET_OFF_GLOBAL_MASK

Fórmula: `C-T3 + w_entrenamiento*(Ridge_local5 − C-T3) + intensidad*disponibilidad_R3*delta_R3`. Ridge usa24 vecinos geográficos, alpha30 y potencia1. El peso escalar se aprende en entrenamiento; R3 tiene imputación/escalado propios de cada entrenamiento y corrección final máxima ±.25 t/ha.

Entradas: cuatro C-T3 (lluvia total, fracción abril–junio, concentración HHI, NDVI mayo); cinco locales (media/std histórica NDVI, media/std NDWI2025, pendiente media); dos coordenadas; tres R3 (nivel histórico NDVI mínimo, persistencia de heterogeneidad NDVI, pendiente mínima). No tiene corrector climático interno del local, Planet, proporciones geológicas ni KMeans/PCA del gate. Mantiene Sentinel histórico, topografía y geografía.

Frente al actual pierde .0025 t/ha aleatoria y .0097 espacial. No es equivalencia demostrada. El peso medio del local es .686 aleatoria, .609 por perfil, .055 municipal y .344 espacial. Son promedios de modelos entrenados en diferentes folds, no pesos manuales definidos por protocolo ni reglas para municipios. En municipal depende principalmente de C-T3 y de R3; esto no demuestra generalización municipal del local aislado.

### Modelo de12 entradas: NDWI_SLOPE_OFF_GLOBAL_MASK

Mantiene la misma arquitectura y retira las dos estadísticas locales de NDVI histórico. Su experto usa media/std NDWI2025 y pendiente media. Conserva historia NDVI para R3; no es un modelo sin historia. Pierde .0027 t/ha aleatoria y .0118 espacial frente al actual; municipal queda prácticamente igual en el valor puntual. Requiere12 entradas en predicción y calibración.

## 4. Residuos: hay intercambios reales

En NO_PLANET_OFF_GLOBAL, Almoloya espacial mejora .5505→.4562, aunque sigue subestimada (sesgo −.4048). Chignahuapan empeora .5450→.5607 y cambia sesgo +.1002→−.1230; Singuilucan empeora .6611→.7450; Calpulalpan queda casi igual .8125→.8129. La reducción no soluciona todas las regiones.

Su MAE aleatorio es .3399 frente a .3396 actual; municipal mejora .4491→.4468 pese al RMSE casi igual. Espacial empeora .5004→.5140, aunque reduce mucho el sesgo global +.2285→+.1232. Reducir sesgo no garantiza menor dispersión ni mejor RMSE.

En aleatoria, la pérdida SSE total del modelo14 es .3288 frente al actual: las35 difíciles pierden .5779 y las103 restantes ganan .2491. Espacialmente, las difíciles pierden2.0374 y las restantes ganan .3252. La pequeña diferencia agregada no debe ocultar que se sacrifica parte del comportamiento en casos difíciles.

En cuartiles aleatorios, modelo14 mejora los dos centrales y empeora extremos: cuartil inferior RMSE .6432→.6526, superior .4705→.4884. Espacialmente el superior pasa .4736→.6112, mientras los centrales mejoran. No se generan reglas usando el rendimiento observado, desconocido al predecir.

Las diferencias intraperfil con igual peso por perfil pasan, en aleatoria, de RMSE .5665 a .5723 para modelo14 y .5725 para modelo12; espacial de .5169 a .5232/.5228. Por perfil climático mejoran algo (.5200→.5144/.5152); municipal empeoran levemente (.5183→.5204). Son errores de diferencias entre pares dentro del mismo fold con soporte, no errores individuales comparables directamente con la tabla principal.

## Recomendación

Mantener el actual26 como referencia de precisión; conservar el modelo14 como alternativa compacta y el12 como sensibilidad de mayor reducción. Son compromisos de costo/precisión, con deterioros identificados. Si importa eliminar fuentes y capas, las opciones OFF/GLOBAL ofrecen una reducción real; si importa conservar precisión, NO_PLANET_ON_PCA2 y FULL7_ON_PCA2 son candidatas exploratorias, con el límite de calibración/source del primero.

La hipótesis de redundancia entre corrector interno y R3 no se sostiene como regla general: la retirada aislada pierde; combinada con otra mezcla es competitiva. Las siete entradas locales tampoco son indispensables en toda arquitectura. No se identificó una combinación que mejore todas las métricas, regiones y extremos ni se certifica un subconjunto óptimo global de variables.

Ninguno de412 contrastes supera .05 tras Holm. Intervalos de OOF fijas y mismos folds no incorporan toda la selección histórica/reajuste, y sólo hay cinco bloques espaciales. Ausencia de significancia no demuestra equivalencia. No se promueve Champion ni se entrenan final138 o PRED59.

## Entregables y auditoría

Scripts497–501 y módulos architecture_decomposition/pruned_global_architecture. Salida `outputs/modeling/architecture_decomposition/v1`:99 entradas,177,606 OOF,6,240 modelos BASE/MASK reproducidos,3,120 calibraciones R3 y3,120 decisiones de gate verificadas. El Excel incluye RMSE/R², MAE/sesgo, regiones/cuartiles/intraperfil, omisiones, pesos, activación, efectos, interacciones e inventario de predicción/calibración. Los modelos podados tienen su propio registro de reproducción.

La enmienda performance_amendment sólo aceleró el solver Ridge y el paralelismo, sin cambiar recetas, vecinos, regularización o particiones. Se comprobó equivalencia exacta en32 comparaciones de datos reales, se preservó la implementación original y se reprodujeron todos los modelos con el predictor original. Las referencias actuales coinciden en65 folds; todas las fuentes protegidas permanecen intactas. Las cuatro pruebas cubren composiciones, gate global sin geología, reutilización de clusters sin etiquetas y equivalencia de Ridge con empates/columnas constantes.
