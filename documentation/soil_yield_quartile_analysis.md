> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Suelo y cuartiles de rendimiento

El suelo contiene señal asociada con el rendimiento, pero los modelos evaluados no demuestran una aportación adicional consistente a lluvia. Se analiza exclusivamente a las 138 parcelas TRAIN con rendimiento observado, utilizando las predicciones fuera de muestra ya guardadas de J, K y L. No se entrenaron modelos nuevos ni se modificaron esas secciones o el Champion.

## Distribución observada y errores

Los cortes se calculan sobre el rendimiento observado: Q1 [2, 3.20], Q2 (3.20, 4.34], Q3 (4.34, 4.55] y Q4 (4.55, 5.59] t/ha. Hay 36, 33, 35 y 34 parcelas, respectivamente. Los empates permanecen juntos; por eso los tamaños no son exactamente iguales. Estos cuartiles son un diagnóstico posterior, no una variable predictora ni un criterio utilizado para seleccionar modelos.

RMSE en t/ha, validación aleatoria, calculado sobre todas las parcelas de cada cuartil en cada repetición y después promediado entre las diez repeticiones:

| Modelo | Q1 | Q2 | Q3 | Q4 |
|---|---:|---:|---:|---:|
| Media del entrenamiento | 1.207 | 0.397 | 0.540 | 0.989 |
| Suelo S1 solo | 0.924 | 0.422 | 0.397 | 0.806 |
| Suelo S2 solo | 0.766 | 0.473 | 0.263 | 0.587 |
| Lluvia | 0.726 | 0.492 | 0.194 | 0.520 |
| Lluvia + suelo S1 | 0.741 | 0.492 | 0.194 | 0.531 |
| Lluvia + corrección residual de suelo S1 | 0.729 | 0.491 | 0.196 | 0.521 |
| Lluvia + corrección residual PCA de suelo | 0.729 | 0.488 | 0.195 | 0.521 |

S1 representa la cobertura de unidades cartográficas que mencionan cada grupo. S2 conserva las unidades edafológicas completas, agrupando categorías escasas dentro de cada entrenamiento. Todos son Elastic Net; la variante PCA comprime suelo antes de ajustar la corrección residual. Los parámetros y componentes se seleccionaron dentro de la validación interna de los experimentos originales.

El suelo solo supera claramente a la media en Q1, Q3 y Q4; S2 describe mejor estos grupos que S1. En Q2 incluso la media tiene menor error que suelo o lluvia: ganar en un cuartil central no basta para justificar un modelo. Frente a lluvia, S2 mejora ligeramente Q2, pero empeora los otros tres cuartiles. Al añadir S1 directamente a lluvia, empeoran los extremos: +0.0145 t/ha en Q1 y +0.0109 en Q4. La corrección residual y PCA producen cambios de pocas milésimas, sin ganancia sustancial.

Lluvia sobreestima Q1 en promedio +0.433 t/ha y subestima Q4 −0.425. Suelo S2 solo tiene sesgos mayores: +0.498 y −0.485. La corrección residual S1 tampoco resuelve esa contracción de los extremos: +0.436 y −0.425. El RMSE bajo de Q3 no significa que ese rango tenga un suelo universalmente mejor: también tiene menor dispersión y distinta composición territorial.

## Qué cambia en el mapa de suelo

Cobertura media de unidades que mencionan el grupo, expresada como porcentaje:

| Grupo cartográfico | Q1 | Q2 | Q3 | Q4 |
|---|---:|---:|---:|---:|
| AN (Andosol) | 25.9 | 15.0 | 0.0 | 0.0 |
| CM (Cambisol) | 26.3 | 18.7 | 2.7 | 0.0 |
| DU (Durisol) | 18.1 | 16.9 | 0.0 | 0.0 |
| LV (Luvisol) | 2.8 | 10.1 | 23.5 | 30.0 |
| PL (Planosol) | 5.6 | 27.3 | 41.0 | 43.7 |
| PH (Phaeozem) | 61.6 | 52.3 | 53.2 | 53.4 |
| VR (Vertisol) | 70.7 | 61.9 | 67.4 | 66.4 |

AN, CM y DU se concentran en los cuartiles inferiores; LV y PL aumentan hacia los superiores. PH y VR aparecen ampliamente en toda la distribución. Son asociaciones cartográficas: una unidad puede mencionar varios grupos y sus coberturas no tienen por qué sumar 100 %. No representan porcentajes físicos medidos de cada suelo dentro de la parcela ni análisis de fertilidad.

La distribución territorial explica parte de esta estructura:

| Estado | Q1 | Q2 | Q3 | Q4 |
|---|---:|---:|---:|---:|
| Hidalgo | 10 | 11 | 9 | 6 |
| Puebla | 3 | 14 | 26 | 28 |
| Tlaxcala | 23 | 8 | 0 | 0 |

Por ello no se puede concluir que un grupo edafológico cause rendimientos altos o bajos. El mapa también identifica regiones que comparten clima, manejo y otros factores no aislados aquí. Su escala 1:250,000 limita la resolución intraparcela; la intersección exacta con el polígono no vuelve más fina la información original.

## Generalización y lectura de los resultados

Las tablas adjuntas conservan los cuatro protocolos: aleatorio, por perfil climático, municipal y espacial. Las diferencias se calculan contra lluvia en exactamente las mismas parcelas y folds. Una diferencia negativa de RMSE o MAE indica mejora. El sesgo se define como predicción menos rendimiento observado. Las medias por cuartil no deben promediarse para reconstruir el RMSE global; primero deben agregarse los errores cuadrados con su tamaño de muestra.

La conclusión global de K y L permanece: ninguna incorporación de suelo evaluada cumple simultáneamente los criterios de mejora aleatoria y ausencia de deterioro relevante en las validaciones agrupadas. Mejorar algún cuartil o separar estados en PCA no prueba generalización. Tampoco se infiere significación estadística a partir de diez repeticiones que reutilizan las mismas parcelas.

Para estas representaciones y modelos, suelo sirve para describir heterogeneidad regional y aporta señal por sí solo, pero no hay evidencia suficiente para integrarlo como mejora predictiva sobre lluvia. Esto no demuestra que las propiedades físicas del suelo sean irrelevantes: los datos disponibles son unidades cartográficas, no mediciones parcelarias de profundidad, materia orgánica, humedad o nutrientes.

![Errores y cobertura cartográfica por cuartil](../outputs/research/family_1/soil_yield_quartile_analysis/v1/soil_quartiles.png)

Reproducción: `python scripts/334_soil_yield_quartiles.py`. Tablas en `outputs/research/family_1/soil_yield_quartile_analysis/v1/`: asignación de parcelas, métricas por repetición y protocolo, resumen, cobertura de los diez grupos y conteos por estado y municipio. El script valida unicidad de etiquetas, coincidencia de rendimientos y folds contra lluvia y presencia de todas las parcelas de cada cuartil por repetición.
