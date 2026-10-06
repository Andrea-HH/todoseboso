# Familia 1 — Etapa 2.5: clima y topografía por parcela

Generado: 2026-10-06T12:31:34-06:00

## Alcance

Se transformaron rásteres climáticos mensuales y topográficos estáticos a la unidad parcela. No se utilizó rendimiento, no se seleccionaron variables y no se unieron todavía con satélites.

## Respuestas a las preguntas de la etapa

### 1. ¿Tenemos los 48 meses esperados?

Sí. Hay 48 rásteres de precipitación, 48 Tmin y 48 Tmax para enero de 2022 a diciembre de 2025. No hay combinaciones variable-año-mes faltantes ni duplicadas.

### 2. ¿Todas las parcelas tienen cobertura completa?

Sí. 197/197 parcelas tienen las tres fuentes climáticas en los 48 meses, 36 meses históricos y los 7 meses de abril–octubre 2025. No hay medias climáticas faltantes.

### 3. ¿Cuántos píxeles climáticos intersectan típicamente una parcela?

La mediana es 1 píxel tocado para precipitación, Tmin y Tmax. Aproximadamente 84.3% de las parcelas están típicamente dentro de un solo píxel; el máximo es 3. La fracción efectiva mediana de un píxel es muy pequeña porque la resolución es 0.05° y las parcelas son mucho menores.

### 4. ¿Tiene sentido conservar min/max/std climáticos intraparcela?

Se conservan por trazabilidad, pero para la mayoría son redundantes: con un píxel, min=median=mean=max y std=0. Sólo aportan variación en parcelas que cruzan límites de celda. Deben marcarse como potencialmente redundantes por resolución, no eliminarse todavía por relación con el target.

### 5–6. ¿Es necesaria ponderación por área y cambia respecto a la media estándar?

Sí es el método técnicamente correcto para parcelas que tocan varios píxeles, aunque para la parcela mediana la diferencia es 0 porque toca uno. La mediana absoluta global entre media ponderada y media igual de píxeles tocados es 0.0000; el máximo llega a 43.854, impulsado por precipitación en parcelas de frontera. Por ello se conserva la media ponderada como principal y la estándar sólo como diagnóstico.

### 7. ¿Existen valores climáticos físicamente sospechosos?

No aparecen precipitaciones negativas ni faltantes. Los rangos observados son precipitación 0–392.02 mm/mes, Tmin 5.42–16.26 °C y Tmax 18.76–30.16 °C. Son plausibles como rangos generales; no se eliminaron extremos.

### 8. ¿Tmin <= Tmax siempre?

Sí. Hay 0 violaciones en 9,456 combinaciones parcela-mes.

### 9. ¿Cómo se distribuye DTR?

DTR varía entre 7.45 y 17.81 °C, con mediana 12.42 °C y media 12.26 °C. No hay valores negativos.

### 10. ¿TRAIN y PREDICTION son comparables?

Ambos tienen cobertura climática completa y topografía completa. `train_prediction_environment_comparison.csv` permite revisar por grupo los rangos de clima, soporte de píxeles, elevación y pendiente. Las diferencias descriptivas pueden reflejar geografía; no se realizaron tests ni se usó rendimiento.

### 11. ¿Todas las parcelas tienen elevación y pendiente?

Sí. Las 197 parcelas tienen ambas variables y fracción válida completa.

### 12. ¿Cuánta variación topográfica existe dentro de parcela?

Elevación media: 2496.6–2906.0 m. El rango intraparcela tiene mediana 13.0 m y máximo 58.0 m. Pendiente media: 0.28–9.40°, con rango intraparcela mediano 1.75° y máximo 15.42°. Aquí min/max/std sí contienen variación real para muchas parcelas porque la resolución es 120 m.

### 13. ¿Área oficial y geométrica son consistentes?

Sí, con una diferencia sistemática pequeña. El área geométrica es en promedio -0.681% distinta de la oficial; mediana -0.675%, rango -1.936% a -0.163%. Se conserva el área oficial; área geométrica, perímetro y centroides quedan sólo para auditoría.

### 14. ¿Qué variables están listas para feature engineering?

- Serie mensual: precipitación, Tmin, Tmax con media ponderada, mediana, min, max, std, píxeles y cobertura.
- Derivadas mensuales directas: Tmean y DTR.
- Topografía estática: elevación y pendiente con mean/median/min/max/std/range y calidad.
- Flags temporales: ciclo abril–octubre 2025 e historia 2022–2024.

Todavía no se construyeron acumulados del ciclo, anomalías, ventanas early/mid/late ni interacciones.

### 15. ¿Qué parece redundante sólo por resolución?

En clima, min/max/median/std son redundantes para la mayoría de parcelas porque típicamente intersectan un solo píxel. `n_pixels`, `valid_fraction` y la comparación ponderada siguen siendo útiles para trazabilidad. En topografía, la resolución de 120 m produce una mediana de 10 píxeles de elevación y 10 de pendiente por parcela, por lo que la variabilidad intraparcela es más informativa.

## Método espacial

- Clima y parcelas: EPSG:4326; no fue necesaria reproyección para extracción.
- Topografía: EPSG:6372; parcelas reproyectadas únicamente en memoria.
- Área geométrica: EPSG:6372.
- Estadísticas principales: `exactextract`, ponderación exacta por fracción de píxel.
- Área efectiva válida: área geométrica métrica multiplicada por fracción válida.
- Raw modificado: no.
- Target utilizado: no.

## Decisiones pendientes para Etapa 3

1. Definir acumulados y ventanas climáticas del ciclo 2025.
2. Definir climatología/anomalías 2025 frente a 2022–2024.
3. Decidir si conservar min/max/std climáticos en el bloque final pese a su redundancia espacial.
4. Mantener la media ponderada como principal y decidir si retirar medias estándar diagnósticas.
5. Definir fecha de corte de predicción para impedir usar meses futuros.
6. Diseñar prefijos de features ambientales y unir sólo después de agregar a nivel parcela.
7. Evaluar aporte incremental de clima/topografía únicamente en etapas de modelado y dentro del protocolo CV.
