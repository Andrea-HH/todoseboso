# Reference26: distribución de59 predicciones y138 rendimientos observados

Las59 estimaciones pertenecen al champion26 final ajustado con138 rendimientos. **Los grupos contienen parcelas distintas; no conocemos los rendimientos verdaderos de59.** Comparar sus distribuciones no estima sesgo ni error. Cada parcela pesa igual, sin ponderación por hectáreas; desviación estándar muestral, cuantiles con interpolación lineal.

## Comparación global

| Estadístico | Observados138 | Predichos59 |
|---|---|---|
| Parcelas | 138.0000 | 59.0000 |
| Media | 3.9554 | 3.9564 |
| Mediana | 4.3400 | 4.3489 |
| Desviación estándar | 0.8512 | 0.6976 |
| Mínimo | 2.0000 | 2.7598 |
| Percentil10 | 2.8920 | 2.9634 |
| Percentil25 | 3.2000 | 3.1450 |
| Percentil75 | 4.5500 | 4.4959 |
| Percentil90 | 4.8420 | 4.6632 |
| Máximo | 5.5900 | 4.8196 |
| Amplitud del rango | 3.5900 | 2.0598 |
| Rango intercuartílico | 1.3500 | 1.3509 |
| Parcelas con valor≥5 | 10.0000 | 0.0000 |

La media cambia apenas+0.0011t/ha y la mediana también es próxima. El rango predicho es **2.760–4.820**, frente a2.000–5.590 observado. Su amplitud es57.4% de la observada y la desviación estándar es18.0% menor. El IQR, en cambio, prácticamente coincide: no todas las medidas de dispersión se reducen por igual.

No hay estimaciones≥5t/ha, frente a10/138 observadas. El centro se conserva y las colas son más moderadas. Media menor que mediana y la mezcla de estados muestran que una distribución normal única es una descripción incompleta; no se interpreta esto como prueba formal de multimodalidad.

## Por estado

| Estado | Grupo | n | Media | Mediana | SD | Mínimo | Máximo |
|---|---|---|---|---|---|---|---|
| Hidalgo | Observed138 | 36 | 3.762 | 3.500 | 0.778 | 2.000 | 4.870 |
| Hidalgo | Predicted59 | 15 | 3.877 | 4.303 | 0.650 | 3.080 | 4.558 |
| Puebla | Observed138 | 71 | 4.477 | 4.520 | 0.584 | 2.150 | 5.590 |
| Puebla | Predicted59 | 29 | 4.479 | 4.444 | 0.185 | 4.085 | 4.820 |
| Tlaxcala | Observed138 | 31 | 2.984 | 3.000 | 0.376 | 2.500 | 3.500 |
| Tlaxcala | Predicted59 | 15 | 3.026 | 3.033 | 0.162 | 2.760 | 3.271 |

**Puebla:** todas las parcelas de este estado son Chignahuapan en estos datos. Las medias son prácticamente iguales, pero las estimaciones evitan los extremos observados: SD.185 frente a.584. Es el cambio de dispersión más marcado, y no demuestra que las29 desconocidas deban tener la dispersión de las71 conocidas.

**Hidalgo:** la media estimada es algo mayor y la mediana pasa de3.500 a4.303. La mezcla municipal importa: las59 incluyen allí4Almoloya,4Cuautepec y7Singuilucan; entre las36 conocidas hay10/5/16 respectivamente y5 de otros municipios. Las parcelas de Almoloya/Cuautepec pesan más en el grupo a estimar. La mayor mediana estatal no es evidencia de sobreestimación.

**Tlaxcala:** los31 rendimientos conocidos sólo toman tres valores:2.5,3.0 y3.5. Las15 estimaciones son continuas y más cercanas al centro, con rango2.760–3.271 y media≈3.026. No deben redondearse automáticamente a esos tres niveles: no se ha establecido que sean las únicas respuestas posibles.

## Municipios con soporte en ambos grupos

Sólo se muestran aquí grupos con al menos tres observaciones y tres predicciones. El Excel local contiene todos, incluidos grupos de una parcela; éstos no permiten describir de forma estable un municipio.

| Municipio | n obs/pred | Media obs/pred | SD obs/pred | Rango predicho |
|---|---|---|---|---|
| Almoloya | 10/4 | 4.521/4.467 | 0.188/0.068 | 4.415–4.558 |
| Cuautepec de Hinojosa | 5/4 | 4.598/4.440 | 0.151/0.117 | 4.303–4.550 |
| Singuilucan | 16/7 | 3.081/3.218 | 0.434/0.160 | 3.080–3.509 |
| Chignahuapan | 71/29 | 4.477/4.479 | 0.584/0.185 | 4.085–4.820 |
| Calpulalpan | 30/14 | 3.000/3.008 | 0.371/0.152 | 2.760–3.252 |

Nanacamilpa tiene sólo una observación conocida y una predicción: su diferencia no se generaliza al municipio.

## Composición y dispersión entre estados

| Estado | Proporción en138 | Proporción en59 |
|---|---|---|
| Hidalgo | 26.1% | 25.4% |
| Puebla | 51.4% | 49.2% |
| Tlaxcala | 22.5% | 25.4% |

Si las medias predichas por estado se ponderaran con la composición de las138, la media sería3.9954t/ha. La coincidencia global combina cambios que se compensan: componente de composición estatal-0.0392t/ha y componente de diferencias de medias dentro de estados+0.0403t/ha. Es una identidad aritmética, no descomposición causal ni sesgo.

- Observed138: 50.3% de la varianza poblacional se explica aritméticamente por diferencias entre las medias estatales.
- Predicted59: 74.4% de la varianza poblacional se explica aritméticamente por diferencias entre las medias estatales.

Esto explica por qué una SD global relativamente parecida puede ocultar estimaciones mucho más estrechas dentro de los estados. La SD estatal es una dispersión de parcelas, no incertidumbre de una predicción individual.

## Interpretación y archivos

Un modelo de regresión predice un valor central condicionado a sus entradas; sus predicciones no tienen por qué reproducir toda la variabilidad de resultados reales, que incluye ruido y factores no observados. Además aquí cambian las parcelas y sus características. **La cercanía de medias no prueba exactitud, y la menor dispersión no prueba por sí sola un defecto.** Para medir errores de extremos hay que usar OOF alineadas o esperar los59 rendimientos verdaderos. No se hicieron pruebas de igualdad de distribuciones ni se recalibraron los valores para hacerlos coincidir.

![Distribuciones acumuladas globales y estatales](distribution_ECDF.png)

[Descriptivos globales y estatales](descriptive_global_state.csv) · [Composición por estado](state_composition.csv) · [Varianza entre/dentro de estados](variance_decomposition.csv) · [Descomposición de medias](mean_decomposition.json) · [Auditoría y fuentes](audit.json). Excel local: `outputs/research/reference26_distribution/v1/distribucion_Reference26_59_vs_138.xlsx`. Reproducción: `python scripts/534_reference26_distribution.py`. [Modelo26](../../../documentation/models/Reference26/README.md) · [Predicciones finales](../../current_champions_final/v1/README.md).
