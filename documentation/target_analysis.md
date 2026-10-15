# Análisis de la variable objetivo — Rendimiento

Se usa RENDIMIENTO_T_HA, rendimiento por superficie (t/ha), no producción total.138 etiquetas se verifican exactamente contra el archivo maestro original. No hay vacíos, ceros ni negativos entre esas138;59 parcelas sin etiqueta se mantienen fuera del análisis. No se ajustan modelos ni cambian datos.

Media 3.955; mediana 4.340; desviación estándar muestral 0.851; mínimo 2.00; máximo 5.59. Q1=3.20, Q3=4.55, IQR=1.35;67 valores distintos. Asimetría -0.325: leve hacia valores bajos, no una única población regional homogénea.114/138 parcelas (82.6%) están entre3 y5 inclusive;14 están por debajo de3 y10 por encima de5. Percentiles y frecuencias se conservan en tablas.

Puebla:71 parcelas, media4.477 y mediana4.52; todas corresponden a Chignahuapan. Hidalgo:36, media3.763; Tlaxcala:31, media2.984. Las diferencias pueden mezclar ambiente, manejo, muestreo y medición; no identifican efectos estatales ni climáticos. Municipios de1–5 parcelas no sostienen comparaciones poblacionales robustas.

Tlaxcala registra exclusivamente2.5/3.0/3.5 (9/14/8 parcelas); Puebla54 valores distintos y solo1/71 en incrementos de0.5. Hidalgo21 valores distintos y13/36 en pasos de0.5. Esto sugiere auditar precisión, redondeo y método de obtención del rendimiento por fuente; no demuestra que sean estimaciones ni autoriza corregir labels. Los modelos aprenden valores registrados con distintas granularidades. El promedio por parcela no equivale al promedio ponderado por hectáreas.

No hay extremos por regla global de Tukey1.5IQR: límites1.175 y6.575. Ello no elimina casos difíciles locales. En Chignahuapan la regla regional marca ocho valores bajos (<3.9275), entre ellos AGC_171=2.15 y AGC_015=2.64. Son flags descriptivos conservados, no errores comprobados ni motivos de eliminación. Máximo AGC_162=5.59, en Chignahuapan.

Perfil24:34 parcelas, rango2.15–5.57; perfil4:29, rango2.64–5.59. Vectores climáticos iguales conviven con diferencias grandes de rendimiento. La descomposición descriptiva deja25.55% de TSS dentro de perfiles y74.45% entre sus medias; estas medias usan todos los labels de cada perfil, por lo que NO significan que un modelo climático explique74.45% en validación ni que el clima cause esa proporción. No llamar ruido irreducible a la heterogeneidad restante.

Implicaciones: priorizar evaluación municipal/espacial además de aleatoria; revisar sesgo en rendimientos bajos y ambos extremos; evaluar diferencias intraperfil y error absoluto por separado; auditar granularidad regional de medición. No construir reglas con cuartiles observados de validación, ni normalizar y por estado usando labels retenidos. La escala positiva y asimetría leve no justifican por sí solas log-transformar; cualquier transformación futura debe ajustarse dentro de entrenamiento y evaluarse tras invertir a t/ha, con controles de sesgo de inversión. No se ejecuta esa sensibilidad aquí.

![Distribución y perfiles](../outputs/research/target_distribution/v1/figures/target_distribution.png)
