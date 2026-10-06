# Familia 1 — Etapa 2: capas temporales por sensor

Generado: 2026-10-02T12:44:39-06:00

## Alcance

Se construyeron tres capas separadas. No se usó rendimiento, no se fusionaron sensores, no se interpoló, no se suavizó, no se aplicó un umbral definitivo y no se eliminaron outliers. **Non-stationarity is potentially signal, not automatically a problem.**

## Respuestas a las preguntas de la etapa

### 1. ¿Cuál es la representación temporal exacta de Sentinel?

Una fila única por `ID_POLIGONO + fecha_captura`, ordenada por ambos campos. Conserva sensor, conjunto, fecha, año, mes, día del año, distancias temporales, ciclo 2025/historia, `cloud_raw`, flags de calidad, 22 índices originales con mean/std/min/max y 88 series DERIVED (`range`, `lower_gap`, `upper_gap`, `cv`). VI6T fue excluido porque está 100% vacío en Sentinel. El epsilon de CV es `1e-6`.

### 2. ¿Cuál es la cobertura efectiva tras ignorar capturas sin índices?

- Sentinel: mediana 227 capturas válidas por parcela, rango 210–247.
- Landsat: mediana 147, rango 113–253.
- Planet: mediana 185, rango 149–202.

### 3–5. ¿Cómo funciona la nubosidad por sensor?

No es puramente continua ni binaria en ninguno. Es una mezcla de masas puntuales en 0 y 100 con valores intermedios:

- Sentinel: 0 = 62.24%, 100 = 23.99%, intermedios = 13.78%, missing = 0.00%.
- Landsat: 0 = 59.42%, 100 = 31.87%, intermedios = 8.71%, missing = 6.28%.
- Planet: 0 = 63.42%, 100 = 25.22%, intermedios = 11.36%, missing = 0.00%.

En los tres sensores, 100 está fuertemente asociado con ausencia de índices. Landsat además tiene nubosidad faltante y no debe heredar automáticamente la regla de Sentinel.

### 6–7. ¿Qué tan irregular es Landsat y hay parcelas peor cubiertas?

Landsat tiene 392 fechas globales, pero por parcela hay 195–391 observaciones (mediana 211). Su gap mediano es 7 días y máximo 16. Sí existen 50 parcelas sistemáticamente en el cuartil inferior de capturas con VI6T válido; están identificadas en `landsat_coverage_by_parcel.csv`. La densidad es heterogénea y debe conservarse como calidad/covariable.

### 8. ¿TRAIN y PREDICTION son comparables?

Los resúmenes separados en `quality_variable_summary.csv` y las tablas por parcela no muestran una diferencia estructural grande en número de parcelas, cobertura válida o nubosidad. Esto no demuestra igualdad distribucional completa, pero no aparece un fallo de cobertura exclusivo de PREDICTION.

### 9. ¿Las fechas Sentinel están alineadas?

Sentinel tiene 301 fechas globales; 296 aparecen en las 197 parcelas. Existen 4 calendarios exactos de parcela. La alineación es muy alta, aunque no perfecta, principalmente por unas pocas fechas ausentes.

### 10–11. ¿Necesitamos grilla común y qué pérdida produciría?

Para Familia 1 tabular no es obligatorio interpolar: pueden calcularse agregados por ventanas usando timestamps observados y acompañarlos con conteos/cobertura. Si se reduce a un valor por bin, la mediana de puntos temporales colapsados sería:

| Sensor | Semanal | Quincenal | Mensual |
|---|---:|---:|---:|
| Sentinel-2 | 27.6% | 56.3% | 78.9% |
| Landsat | 7.9% | 37.2% | 67.8% |
| Planet | 73.4% | 85.9% | 93.5% |

Esto es compresión, no pérdida completa de valores si se guardan estadísticas dentro de cada bin. Una grilla mensual es demasiado agresiva para dinámica rápida; semanal/quincenal puede evaluarse después sin reemplazar la capa observada.

### 12. ¿Qué rangos son sospechosos?

El diccionario proporcionado es conceptual y no incluye ecuaciones estrictas. Por ello, `index_physical_range_audit.csv` marca el rango matemático como `UNKNOWN`, conserva mínimos/máximos y reporta extremos 3×IQR sólo como diagnóstico. Las mayores cuentas descriptivas están en: Sentinel-2:mra_promedio, Sentinel-2:crc_std, Sentinel-2:lai_promedio, Sentinel-2:crc_promedio, Sentinel-2:lai_std, Sentinel-2:mcrc_std, Sentinel-2:lai_min, Sentinel-2:evi_promedio. No hay infinitos. Ningún valor fue declarado error ni eliminado.

### 13–14. ¿Qué aportan min/max/std y son fiables las derivadas?

Mean describe nivel medio; std describe heterogeneidad interna; min/max permiten detectar colas y amplitud dentro de parcela. Se construyeron `range=max-min`, `lower_gap=mean-min`, `upper_gap=max-mean` y `cv=std/(abs(mean)+1e-6)`. Son algebraicamente reproducibles y no usan target. CV puede explotar cuando mean está cerca de cero, por lo que debe auditarse o estabilizarse antes de modelar.

### 15–16. ¿Es razonable incluir Landsat y cómo?

Sí, como fuente independiente y complementaria. La evidencia favorece agregación mensual o por ventanas, AUC normalizada por duración y features de cobertura (`n_obs`, `valid_fraction`, `max_gap`). No debe interpolarse para imitar Sentinel ni usarse para features que exijan alta resolución uniforme.

### 17–18. ¿Es necesario hacer estacionarias las series?

No. El target es escalar y la tendencia contiene señal potencial. Posteriormente sí son útiles, junto con la serie original: primeras diferencias, pendientes, tasas de cambio, fechas de pico, AUC, anomalías 2025 respecto al histórico y cambios por ventanas. La tabla descriptiva de una muestra reproducible contiene tendencia lineal, autocorrelación lag-1 y diferencias, sin ADF/KPSS masivo.

### 19. ¿Qué decisiones quedan para Etapa 3?

1. Corte temporal de predicción dentro del ciclo 2025.
2. Regla de calidad por sensor y tratamiento de cloud=100/missing.
3. Ventanas temporales y calendario agronómico.
4. Manejo de CV extremo cuando mean≈0.
5. Conjunto inicial de agregados, sin selección supervisada fuera del CV.
6. Estrategia Landsat: mensual vs ventanas vs timestamps observados.
7. Ajuste de imputación/escalamiento exclusivamente dentro de folds.

### 20. ¿Qué tablas serán input de feature engineering?

- `sentinel_timeseries.parquet`: clave única parcela-fecha, Sentinel original + calidad + tiempo + DERIVED.
- `landsat_timeseries.parquet`: clave única parcela-fecha, VI6T + calidad + tiempo + DERIVED.
- `planet_timeseries.parquet`: clave única parcela-fecha, Planet original + calidad + tiempo + DERIVED.

Las tablas permanecen separadas. Feature engineering producirá después bloques con prefijos `S2_`, `LANDSAT_` y `PLANET_`, unidos sólo a nivel parcela y nunca combinando directamente índices homónimos.

## Trazabilidad

- Raw modificado: no.
- Target utilizado: no.
- Umbral de nubosidad aplicado: no.
- Interpolación o suavizado: no.
- Sensores fusionados: no.
- Epsilon CV: 1e-6.
