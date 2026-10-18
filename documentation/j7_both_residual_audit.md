> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Evaluación completa de residuos OOF de J7_BOTH

**Conclusión:** J7_BOTH está bien calibrado globalmente en validación aleatoria y por perfil, pero tiene tres límites claros: algunos rendimientos bajos generan errores positivos muy grandes y persistentes; el R² global oculta diferencias marcadas dentro de los estados; y la transferencia espacial introduce sobreestimación territorial. No aparece evidencia de que un ajuste lineal global simple vaya a resolver los tres problemas.

Se analizan1,794 predicciones OOF de138 parcelas:10 repeticiones aleatorias y una evaluación completa por perfil, municipal y espacial. No son1,794 parcelas independientes. No se reajusta ningún predictor ni calibrador operativo, no se eliminan casos, no se modifican etiquetas, Champion o experimentos anteriores, ni se generan nuevas59PRED.

El signo usado en todo el informe es **error = predicho − observado**: positivo significa sobreestimación. Las métricas aleatorias se calculan en las138 OOF de cada repetición y después se promedian. La media de predicciones por parcela se utiliza únicamente para ilustrar estabilidad y mapas; no sustituye esas métricas por las de un ensamble de diez modelos.

## 1. Tamaño y distribución del error

| Protocolo | RMSE t/ha | R² | MAE t/ha | Sesgo t/ha | Mediana de error | Percentil95 de error absoluto | Dentro de±0.5t/ha | Dentro de±1t/ha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Aleatoria | 0.4864 | 0.6709 | 0.3470 | −0.0121 | −0.0571 | 0.8553 | 76.2% | 96.2% |
| Perfil | 0.4890 | 0.6675 | 0.3445 | −0.0139 | −0.0734 | 0.9172 | 76.1% | 95.7% |
| Municipal | 0.5808 | 0.5309 | 0.4604 | −0.0205 | −0.1507 | 1.0790 | 68.8% | 93.5% |
| Espacial | 0.6808 | 0.3556 | 0.5291 | +0.2913 | +0.2299 | 1.4279 | 55.8% | 84.8% |

El RMSE aleatorio de0.4864 no significa que cada parcela tenga error de±0.4864 ni es un intervalo predictivo. El MAE y los umbrales muestran un error habitual menor que el RMSE, junto con una cola de errores grandes. En espacial,64.5% de predicciones sobreestiman; en aleatoria43.5% sobreestiman, pero algunas sobreestimaciones extremas compensan muchas subestimaciones pequeñas.

Los residuos aleatorios tienen asimetría positiva1.42 y exceso de curtosis4.43; por perfil1.24 y4.60. Los QQ y histogramas muestran colas que no justifican asumir sin más una distribución normal para construir intervalos individuales. La combinación de regiones, rendimientos redondeados y modelos distintos por fold también importa. No se usa una prueba de normalidad con independencia ficticia.

Los rendimientos observados van de2.00 a5.59t/ha. Las predicciones aleatorias, considerando todas las repeticiones, van de2.647 a5.101; las espaciales de2.681 a5.106. Esa compresión del rango es compatible con predicción de medias condicionales y regularización; no demuestra por sí sola que haya que expandir linealmente todas las predicciones.

## 2. Calibración: promedio, pendiente y regiones

Se ajusta únicamente como diagnóstico descriptivo la recta `observado = a + b*predicho` sobre OOF. Ideal global: a=0,b=1. No se aplica esa recta a nuevas predicciones.

| Protocolo | Intercepto a, t/ha | Pendiente b | IC bootstrap95% de b | Sesgo medio, t/ha | IC bootstrap95% del sesgo |
|---|---:|---:|---:|---:|---:|
| Aleatoria | +0.0287 | 0.9958 | 0.904–1.070 | −0.0121 | −0.055–+0.044 |
| Perfil | −0.0404 | 1.0138 | 0.880–1.148 | −0.0139 | −0.109–+0.073 |
| Municipal | −0.5255 | 1.1388 | 0.372–1.700 | −0.0205 | −0.212–+0.414 |
| Espacial | −1.5258 | 1.2907 | 0.447–1.616 | +0.2913 | +0.010–+0.591 |

Aleatoria/perfil: la calibración lineal global ya está próxima a la identidad. Municipal: el sesgo total pequeño esconde cancelación entre territorios. Espacial: hay sobreestimación importante; pendiente/intercepto son inciertos y la pendiente ideal1 sigue dentro del intervalo exploratorio. No se puede convertir esta recta espacial externa en corrección sin contaminar la evaluación.

El bootstrap usa5,000 remuestreos por conglomerados:43 perfiles TRAIN en aleatoria/perfil,9 municipios en municipal y5 bloques en espacial. Usa el mismo remuestreo para todas las repeticiones y promedia sus métricas. Son intervalos de métricas sobre OOF fijas, sin toda la incertidumbre de reentrenamiento, búsqueda histórica o dependencia espacial residual. Con5 bloques son especialmente frágiles. No son intervalos de rendimiento para una parcela.

## 3. Extremos de rendimiento

Los cuartiles se definen descriptivamente con el target observado, respetando empates:36/33/35/34 parcelas. No se fuerzan grupos iguales separando rendimientos idénticos. Se incluye R² para mantener la convención, pero **no debe compararse con el R² global**: el rango interno es pequeño y seleccionar por el target genera un diagnóstico condicionado a la respuesta.

| Rango observado t/ha | n | Aleatoria RMSE / R² | Sesgo aleatorio | Espacial RMSE / R² | Sesgo espacial |
|---|---:|---:|---:|---:|---:|
| 2.00–3.20 | 36 | 0.6648 / −3.958 | +0.3710 | 1.1198 / −13.060 | +1.0247 |
| 3.30–4.30 | 33 | 0.4723 / −1.474 | −0.0132 | 0.5535 / −2.396 | +0.3884 |
| 4.38–4.55 | 35 | 0.2007 / −13.755 | −0.0177 | 0.2508 / −22.014 | +0.0394 |
| 4.56–5.59 | 34 | 0.4837 / −1.337 | −0.4108 | 0.4374 / −0.909 | −0.3201 |

El bajo rendimiento es la mayor debilidad, especialmente en espacial: sobreestima en promedio1.025t/ha en el cuartil inferior. En el superior tiende a subestimar. El tercer cuartil tiene error absoluto pequeño, pero R² muy negativo porque su target apenas varía0.17t/ha: ese R² no lo convierte en el grupo con mayor error práctico.

La relación entre error y rendimiento observado tiene acoplamiento matemático porque el observado forma parte del error. La tendencia a sobreestimar bajos y subestimar altos puede coexistir con buena calibración `E[observado | predicho]`. Estos cuartiles no justifican una regla basada en el rendimiento verdadero, desconocido al predecir, ni una expansión global automática.

También se entregan niveles exactos de rendimiento y rangos dentro de cada estado. Si un estado tiene menos de cuatro valores distintos, se reportan niveles en lugar de inventar cuatro cuartiles con separación de empates.

## 4. Diferencias por estado

| Protocolo | Estado | n | RMSE | R² dentro del estado | Sesgo | Fracción del SSE total |
|---|---|---:|---:|---:|---:|---:|
| Aleatoria | Hidalgo | 36 | 0.3678 | 0.7698 | −0.0278 | 14.9% |
| Aleatoria | Puebla | 71 | 0.5626 | 0.0598 | −0.0127 | 68.8% |
| Aleatoria | Tlaxcala | 31 | 0.4136 | −0.2520 | +0.0077 | 16.3% |
| Municipal | Hidalgo | 36 | 0.6615 | 0.2558 | +0.2164 | 33.8% |
| Municipal | Puebla | 71 | 0.5798 | 0.0015 | −0.1983 | 51.3% |
| Municipal | Tlaxcala | 31 | 0.4731 | −0.6355 | +0.1114 | 14.9% |
| Espacial | Hidalgo | 36 | 0.6536 | 0.2733 | +0.3002 | 24.0% |
| Espacial | Puebla | 71 | 0.5493 | 0.1040 | +0.0928 | 33.5% |
| Espacial | Tlaxcala | 31 | 0.9361 | −5.4032 | +0.7357 | 42.5% |

El R² global0.671 no significa explicar67% de las diferencias entre parcelas de cada estado. Hidalgo tiene buena discriminación interna aleatoria; Puebla presenta poca explicación interna, aunque su media esté bien calibrada; Tlaxcala tiene poca variación del target y discriminación insuficiente, agravada espacialmente. R² negativo significa peor SSE que el promedio observado de ese subconjunto, usado aquí como referencia descriptiva, no como predictor disponible legítimamente en el fold externo.

Si se centran observado y predicho por sus medias de estado solo para diagnóstico, el R² combinado dentro de estados es0.339 aleatoria,0.331 por perfil,0.154 municipal y0.121 espacial. Ese centrado utiliza targets retenidos y **no es un modelo corregido válido**. Sirve para mostrar cuánto cambia la lectura al retirar las diferencias medias entre estados.

Los31 casos de Tlaxcala representan22.5% de la muestra y42.5% del SSE espacial: carga de error desproporcionada. Puebla tiene51.4% de parcelas y68.8% del SSE aleatorio, pero33.5% del espacial. No hay un único territorio que concentre el problema en todos los protocolos.

## 5. Municipios y bloques espaciales

Resultados municipales principales:

| Municipio | n | RMSE / R² | Sesgo t/ha | Fracción SSE municipal |
|---|---:|---:|---:|---:|
| Chignahuapan | 71 | 0.5798 / 0.0015 | −0.1983 | 51.3% |
| Singuilucan | 16 | 0.8877 / −3.4641 | +0.7781 | 27.1% |
| Calpulalpan | 30 | 0.4710 / −0.6641 | +0.0975 | 14.3% |
| Almoloya | 10 | 0.3529 / −2.8963 | −0.3197 | 2.7% |

Chignahuapan aporta una fracción de SSE municipal similar a su51.4% de parcelas; Singuilucan aporta27.1% del SSE con11.6% de parcelas. Los municipios de1–5 parcelas se conservan en el Excel, sin interpretar R² cuando el target es constante ni rankings fiables con soporte mínimo.

| Bloque espacial | n | RMSE / R² | Sesgo | Fracción SSE | Distancia media al entrenamiento, km | Peso medio experto7 |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 38 | 0.5246 / 0.0687 | +0.1869 | 16.4% | 2.42 | 0.572 |
| 2 | 37 | 0.5537 / 0.0436 | +0.0131 | 17.7% | 2.37 | 0.811 |
| 3 | 35 | 0.9160 / −4.9066 | +0.7311 | 45.9% | 28.68 | 0.044 |
| 4 | 18 | 0.7988 / −0.6980 | +0.5746 | 18.0% | 13.00 | 0.002 |
| 5 | 10 | 0.3621 / −3.1012 | −0.3316 | 2.0% | 7.52 | 0.136 |

El bloque3 contiene31 parcelas de Tlaxcala y4 de Hidalgo: no es exactamente un estado. Los bloques1/2 son principalmente Puebla;4/5 Hidalgo. El3 y4 suman63.9% del SSE espacial con38.4% de parcelas.

**En3/4 la mezcla ya confía casi por completo en C-T3.** El gran sesgo no procede principalmente de asignar demasiado peso al local7. Contraer todavía más esos pesos tiene poco margen para corregir su error principal; conviene revisar soporte y transferencia de la base compacta. Esto no identifica una nueva variable causal ni autoriza una corrección calculada con el target de esos bloques.

## 6. Concentración y casos persistentes

| Protocolo | SSE en peores5 | SSE en peores10 | SSE en peores20 |
|---|---:|---:|---:|
| Aleatoria, promedio por repetición | 40.8% | 52.2% | 67.4% |
| Perfil | 40.8% | 53.7% | 69.6% |
| Municipal | 30.4% | 43.7% | 59.6% |
| Espacial | 24.7% | 40.8% | 59.8% |

Los errores aleatorios no se reparten homogéneamente. Dos parcelas, AGC_171 y AGC_015, concentran27.6% del SSE aleatorio medio usando su error cuadrático por parcela a través de repeticiones.

| Parcela | Municipio | Observado | Predicción aleatoria media10 | Error medio |
|---|---|---:|---:|---:|
| AGC_171 | Chignahuapan | 2.15 | 4.3125 | +2.1625 |
| AGC_015 | Chignahuapan | 2.64 | 4.7200 | +2.0800 |
| AGC_024 | Chignahuapan | 3.03 | 4.2853 | +1.2553 |
| AGC_034 | Singuilucan | 2.00 | 3.1964 | +1.1964 |

Son errores persistentes a través de repeticiones, no solamente una partición desafortunada. AGC_171 también tiene+2.3536 por perfil,+1.9511 municipal y+2.0788 espacial. AGC_015 tiene+1.7598/+1.7868/+2.0004 en esos protocolos. Se recomienda auditar su trazabilidad, fechas, unidades y circunstancias agronómicas, sin asumir que el rendimiento esté mal ni eliminarlo para mejorar métricas.

Las métricas al omitir los casos de mayor error se entregan únicamente como sensibilidad descriptiva; no se recomiendan como resultados del modelo sobre una población filtrada. No se reajusta ningún modelo ni se modifica la muestra.

## 7. Estructura intraperfil y espacial

La descomposición exacta de MSE por perfil climático asigna aproximadamente22.5% a diferencias de sesgo entre perfiles y77.5% a variación dentro de perfiles en aleatoria. Espacialmente pasa a64.2% entre perfiles y35.8% dentro. Es una partición descriptiva de errores, no porcentaje de error corregible con perfiles ni estimación causal. Los perfiles de un solo caso y su asociación geográfica también influyen.

Las diferencias entre pares del mismo perfil y mismo fold tienen RMSE igual-peso-por-perfil0.5777 / 0.5317 / 0.5257 / 0.5320. Con peso por par:0.7774 / 0.7750 / 0.7706 / 0.7596. Que la métrica de diferencias sea mayor que el RMSE individual es esperable por su definición; no se comparan directamente como si fueran el mismo error. Solo se calculan donde existen pares; no son observaciones independientes.

Moran I descriptivo con un grafo simétrico de6 vecinos, normalizado por fila:−0.080 aleatoria,≈0 por perfil,+0.301 municipal,+0.389 espacial. Después de centrar residuos por estado, municipal sigue en+0.200 y espacial en+0.254. Existe agrupación territorial residual que no se reduce solo a diferencias medias estatales. No se presenta p-valor ni significación: las OOF proceden de modelos/folds distintos, hay dependencia territorial y no se presupone intercambio libre de etiquetas.

## 8. Soporte de entrenamiento y extrapolación

| Protocolo | Fuera del rango de al menos una compacta | Distancia media al vecino geográfico más cercano | Peso medio del experto7 |
|---|---:|---:|---:|
| Aleatoria | 5.3% | 0.72km | 0.690 |
| Perfil | 15.2% | 1.80km | 0.720 |
| Municipal | 24.6% | 5.50km | 0.061 |
| Espacial | 32.6% | 10.82km | 0.396 |

El rango y las distancias se calculan respecto al entrenamiento externo de cada caso, con sus propias transformaciones guardadas. Estar dentro del rango marginal no garantiza estar dentro del soporte conjunto. Tampoco se identifica extrapolación exclusivamente con coordenadas.

Espacialmente, la correlación Spearman entre error absoluto y distancia al soporte compacto es+0.479; con distancia geográfica,+0.411; con distancia física,+0.268. Son asociaciones descriptivas, muy influidas por las diferencias entre bloques. Dentro del bloque3, la correlación error absoluto/distancia geográfica es−0.524, no positiva; no sería válido diseñar una regla universal a partir del coeficiente global. Las asociaciones con cada entrada del modelo y su versión centrada por estado se entregan sin p-valores ni selección de nuevas variables.

## 9. Qué parte del sistema limita la transferencia

Resultados de las partes guardadas, con sus predicciones externas respectivas:

| Parte | Aleatoria RMSE / R² | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| C-T3 | 0.5116 / 0.6361 | 0.5206 / 0.6232 | 0.5813 / 0.5302 | 0.6788 / 0.3594 |
| Local7 sin corrector | 0.4937 / 0.6610 | 0.4950 / 0.6594 | 0.7569 / 0.2036 | 0.9760 / −0.3245 |
| Local7 + corrector compacto | 0.4898 / 0.6664 | 0.4880 / 0.6689 | 0.6560 / 0.4016 | 0.8089 / 0.0902 |
| Mezcla J7_BOTH | 0.4864 / 0.6709 | 0.4890 / 0.6675 | 0.5808 / 0.5309 | 0.6808 / 0.3556 |

La mezcla protege frente al deterioro territorial del experto, pero no supera claramente la base compacta en espacial. La correlación de sus errores con C-T3 es0.944 aleatoria,0.913 perfil,0.997 municipal y0.974 espacial. La complementariedad territorial es limitada: muchos casos difíciles son compartidos. Por tanto, seguir mezclando predictores muy semejantes tiene un techo probable en estos datos, sin demostrar un límite universal.

La diferencia espacial entre J7_BOTH y C-T3 combina menor varianza de errores (0.3786 frente a0.4242) y mayor sesgo (+0.2913 frente a+0.1912). Ese balance explica sus RMSE casi iguales. No se debe usar únicamente el sesgo ni únicamente la dispersión para elegir modelo.

## 10. Recomendación

1. Conservar J7_BOTH como candidata compacta y mantener referencias sin promoción automática. La buena calibración aleatoria/perfil reduce la expectativa de una ganancia grande por corregir globalmente intercepto y pendiente.
2. Auditar las pocas parcelas de bajo rendimiento con errores persistentes, primero como trazabilidad y búsqueda de información faltante, no como exclusión o alteración del target.
3. Priorizar transferencia territorial y soporte de C-T3, especialmente bloque3/Tlaxcala y Singuilucan. La contracción adicional de la mezcla por sí sola difícilmente resolverá bloques que ya tienen peso local≈0.
4. Si se prueba calibración predictiva, debe ser una batería pequeña contra identidad, aprendida con OOF dentro de cada entrenamiento externo y regularizada hacia intercepto0/pendiente1. Evaluar RMSE/R², sesgo y territorios; no aplicar los coeficientes descriptivos de este informe.
5. Investigar incertidumbre y alertas de poco soporte en una fase independiente; los intervalos bootstrap actuales no son intervalos individuales. La validación en datos nuevos o un ciclo adicional tiene más valor confirmatorio que seguir ajustando sobre estos mismos errores.

No se ejecuta ninguna de estas modificaciones durante esta auditoría. No se atribuye causalidad a asociaciones de residuos, ni se concluye que corregir medias estatales vaya a transferir a un estado sin soporte de entrenamiento.

## Reproducción y entregables

`scripts/449_j7_both_residual_audit.py` genera tablas, componentes, soporte, intervalos y figuras desde artefactos congelados. `scripts/450_j7_residual_delivery.py` valida métricas, descomposición y entrega; las figuras usan la primera repetición cronológica real (1), sin escoger por desempeño. Se comprobó en ejemplos sintéticos la identidad MSE=sesgo²+varianza y la pendiente/intercepto de calibración ponderada y no ponderada.

Salida `outputs/research/j7_both_residual_audit/v1`: libro `evaluacion_residuos_J7_BOTH.xlsx`, `oof_residuals_components.parquet`, tablas por repetición y resúmenes, inventario de errores por parcela, casos extremos, soporte y comparación de errores con referencias. Figuras: `calibration_and_residuals.png`, `residual_distribution_QQ.png`, `residual_map.png`, `bias_dispersion_and_thresholds.png`.

Se reprodujeron exactamente las65 predicciones externas por fold del modelo (1,794 filas en total), con diferencia máxima0. Hashes de predicciones,65 modelos y fuentes protegidas intactos. No se entrenó un nuevo predictor; las regresiones de calibración son únicamente diagnósticas. `manifest.json` y `delivery_audit.json` documentan comprobaciones y código. Outputs permanece excluido de Git; no se hizo push.
