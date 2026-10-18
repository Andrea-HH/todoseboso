> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Local04D sin clima explícito y complementariedad con C-T3

## Resultado y decisión

Se completó la fase autorizada. Retirar clima explícito de la representación de Local04D apenas cambia su comportamiento. Las correcciones muestran complementariedad en algunos protocolos, pero ninguna resuelve la transferencia municipal y espacial frente a C-T3. No se promueve un modelo ni se actualizan las 59 predicciones.

La recomendación es conservar C-T3 como referencia compacta y pausar la expansión de esta receta local fija. Una continuación necesitaría una hipótesis distinta de representación o regularización y confirmación independiente; estos resultados no justifican añadir más variantes automáticamente.

## Representación y controles

Se reconstruyó C4 desde las fuentes y ascendencias de GeoC. Antes de exclusiones, la reproducción de sus puntuaciones PCA originales difiere como máximo 1.01e-13, tras ajustar signos. Se excluyeron clima y derivados declarados, evapotranspiración WaPOR, contexto de rendimientos SIAP, códigos administrativos y campos de calidad de área. También se retiraron NDVI de mayo de Sentinel-2, copias afines detectadas y descendientes declarados para reservar la entrada directa a C-T3.

La representación no climática conserva 1,831 variables utilizables: señales satelitales, suelo, topografía, geometría y productividad WaPOR NPP, incluidas sus transformaciones admitidas. Un control con las mismas exclusiones de seguridad, pero conservando clima, utiliza 2,000 variables. No se agregaron fuentes nuevas.

“Sin clima explícito” no significa independencia del clima: vegetación, suelo y localización pueden reflejarlo. Agregados estacionales pueden contener información de mayo y otros sensores conservan mediciones distintas. El inventario documenta exactamente las exclusiones.

Se mantuvo PCA20, 24 vecinos, Ridge alfa 30 y potencia de distancia 1. PCA20 explica 76.29% de la variación de X no climática, no del rendimiento. Se conserva el esquema transductivo de GeoC: imputación, escalado y PCA sobre X de las 197 parcelas, sin usar rendimientos ocultos. Esto no constituye una validación inductiva de la representación para parcelas arbitrarias futuras.

## Modelos y validación

Se evaluaron cinco variantes sobre las 65 particiones originales y, por separado, las 16 particiones GeoC de 97 entrenamientos y 41 evaluaciones. Las correcciones usan residuos generados sin utilizar el rendimiento del caso correspondiente. Su amplitud se selecciona internamente entre 0, 0.25 y 0.5. La corrección compacta reajusta Elastic Net sobre residuos; no reutiliza los coeficientes del C-T3 original.

### RMSE en los 65 folds originales (t/ha)

| Modelo | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| C-T3 | 0.5116 | 0.5206 | 0.5813 | 0.6788 |
| Local04D original | 0.4930 | 0.5031 | 0.7602 | 0.9794 |
| Control local conservando clima | 0.4931 | 0.5032 | 0.7601 | 0.9793 |
| Local sin clima | 0.4911 | 0.5033 | 0.7617 | 0.9807 |
| C-T3 + corrección local sin clima | 0.4959 | 0.5159 | 0.5779 | 0.7647 |
| Local sin clima + corrección compacta EN | 0.4879 | 0.4971 | 0.6613 | 0.8026 |
| Promedio geográfico de 24 vecinos | 0.4974 | 0.5066 | 0.7582 | 0.9807 |

La columna aleatoria promedia métricas de diez repeticiones, cada una calculada sobre OOF completas. Las otras tres utilizan sus OOF completas. No se promedian RMSE por fold.

### Banco GeoC 97/41, separado

| Modelo | RMSE OOF agrupadas | MAE OOF agrupadas |
|---|---:|---:|
| C-T3 | 0.5289 | 0.3780 |
| Local04D original | 0.4957 | 0.3425 |
| Control local conservando clima | 0.4961 | 0.3424 |
| Local sin clima | 0.4952 | 0.3425 |
| C-T3 + corrección local sin clima | 0.5115 | 0.3584 |
| Local sin clima + corrección compacta EN | 0.4929 | 0.3472 |
| Promedio geográfico de 24 vecinos | 0.5020 | 0.3434 |

Son 656 evaluaciones repetidas de 125 parcelas distintas; no son 656 muestras independientes. Este banco es el de desarrollo original, no el banco nuevo de confirmación citado para GeoC. Aquí se reportan métricas agrupadas, separadas de las medias por repetición disponibles en los archivos.

## Qué se aprendió

- La eliminación de clima cambia muy poco tanto frente al original como frente al control con clima. Bajo esta receta fija, se debilita la hipótesis de que la redundancia climática explícita explique el problema territorial.
- C-T3 con corrector no climático mejora aleatoria y ligeramente perfil y municipal, pero empeora espacial de 0.6788 a 0.7647. En Chignahuapan espacial, el RMSE pasa de 0.5499 a 0.7229. No es una mejora territorial equilibrada.
- La dirección inversa obtiene 0.4929 en GeoC, una mejora de apenas 0.0028 t/ha frente al Local04D original. Su MAE empeora de 0.3425 a 0.3472. Municipal y espacial siguen por detrás de C-T3.
- El promedio geográfico sin PCA queda cerca del local, especialmente en transferencias territoriales. La diferencia absoluta media entre sus predicciones y las del local sin clima es 0.0189 t/ha municipal y 0.0203 espacial. Esto señala el peso de la proximidad bajo esta regularización, sin demostrar que las características sean inútiles ni establecer causalidad.
- Existe una señal complementaria intraperfil limitada: C-T3 + corrector mejora el error de diferencias tanto ponderando por perfil como por pares en aleatoria y GeoC. Ese beneficio no se sostiene en municipal y espacial.

Los diagnósticos incluyen errores regionales, omisión de regiones sin reajustar, ganancias por parcela y ambas ponderaciones intraperfil. No se derivaron reglas regionales de estos resultados.

## Incertidumbre estadística

Se calcularon 30 contrastes pareados exploratorios, bootstrap por conglomerados y pruebas de cambio de signo de diferencias de error cuadrático, con corrección Holm dentro de esta fase. Se usan perfiles para aleatoria, perfil y GeoC, municipios para municipal y cinco bloques para espacial. Con cinco bloques, la resolución de una prueba exacta bilateral es limitada: su mínimo p posible es 0.0625.

Ninguna comparación de los 65 folds originales supera la corrección Holm. En GeoC, C-T3 + corrector mejora frente a C-T3 con p ajustado 0.009, pero sigue detrás de Local04D y presenta deterioro espacial. La mejora de la dirección inversa frente a Local04D no está demostrada: diferencia RMSE -0.0028, intervalo bootstrap [-0.0140, 0.0119] y p ajustado 1.

La inferencia está condicionada a predicciones ya ajustadas; no incorpora toda la incertidumbre de reentrenamiento ni corrige la búsqueda histórica completa. Los perfiles pueden retener dependencia espacial. Ningún contraste constituye una confirmación independiente de superioridad.

## Reproducibilidad y entregables

Se guardaron 405 predictores de validación y 12,250 predicciones OOF nuevas. Cinco pruebas pasaron; la reproducción de las 405 predicciones guardadas tuvo diferencia máxima cero. Se verificaron 2,548 contextos de exclusión de residuos y la integridad de fuentes protegidas. El registro de ajuste contiene cero advertencias; esto no es una garantía general sobre todas las condiciones del entorno numérico.

- Scripts: `scripts/422_prepare_nonclimatic_local.py`, `423_run_nonclimatic_local.py` y `424_summarize_nonclimatic_local.py`.
- Implementación: `src/nonclimatic_local.py`.
- Pruebas: `tests/test_nonclimatic_local.py` y pruebas existentes del corrector inverso.
- Carpeta: `outputs/modeling/nonclimatic_local/v1/`.
- Libro: `fase_sin_clima_resultados.xlsx`.
- Inventario: `audit/feature_inventory_ancestry.csv`.
- Resultados: `diagnostics/metrics_summary.csv`, `paired_cluster_tests.csv`, diagnósticos regionales e intraperfil.
- Predicciones: `tables/new_oof_predictions.parquet` y tabla con referencias archivadas.
- Diseño, modelos y auditoría: `frozen_design.json`, `models/`, `manifest.json`.

No se modificaron Champion, C-T3, GeoC ni resultados anteriores. No se entrenó un modelo final sobre las 138 parcelas ni se generaron nuevas predicciones para las 59 parcelas PRED.
