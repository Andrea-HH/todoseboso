> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Diez parcelas difíciles: entradas de los modelos y diferencias descriptivas

Se identifican las diez parcelas con mayor media del error cuadrático OOF de J7_BOTH en validación aleatoria, promediando sus diez repeticiones. No se mezclan protocolos. No es un ranking universal: la validación municipal o espacial puede producir otro orden. No se reajustaron modelos ni se consultaron rendimientos PRED.

## Qué condicionaba los modelos

J7_BOTH combina CT3 con un experto local corregido mediante compact4. El experto utiliza siete descriptores no climáticos y vecinos geográficos. Su mezcla física utiliza textura y fase del suelo, diez proporciones geológicas y tres distancias geológicas. Estas entradas físicas condicionan el peso entre componentes; las coordenadas definen el vecindario local. Son funciones diferentes.

Los experimentos posteriores difficult_case_signals añadieron dos o tres señales nominadas tras estudiar casos difíciles: cambio neto de EVI Planet, TPI medio 3×3 y máximo incremento temporal de la brecha NDVI medio–mínimo. Se colocaron alternativamente en el experto local o en su corrector.

Los últimos neighbor_signal_contrasts y neighbor_signal_linear utilizaron esas tres señales, expresadas como seis diferencias estandarizadas respecto a vecinos: dos contrastes por señal. GEO define vecinos por distancia geográfica; COMPACT, por compact4 estandarizado. No define vecinos usando estas señales nuevas ni la composición física. La base J7 conserva su mezcla física. Las variantes ATTENUATE reducen la contribución J7−CT3; las RESIDUAL y LINEAR añaden una corrección a J7.

Por tanto, composición física y señales de casos difíciles están presentes en capas distintas. Su inclusión en el modelo no demuestra importancia predictiva ni causal.

## Ranking y diferencias municipales

P indica percentil dentro del municipio, incluyendo la parcela focal: Chignahuapan n=71, Singuilucan n=16. Los percentiles extremos en n=16 requieren especial prudencia. Error = predicción menos observado, en t/ha. Se muestra el error medio, no el RMSE individual; el CSV conserva ambos.

| Parcela | Municipio | Observado | Predicho medio | Error medio | Diferencias frente a su municipio |
|---|---|---:|---:|---:|---|
|171|Chignahuapan|2.15|4.31|+2.16|Cambio EVI 0.014 frente a mediana 0.177, P1; NDWI medio 0.010 frente a 0.056, P15.|
|015|Chignahuapan|2.64|4.72|+2.08|TPI −3.64, P5; dinámica brecha NDVI 0.108 frente a 0.039, P96.|
|024|Chignahuapan|3.03|4.29|+1.26|Delta NDVI junio–agosto 0.424 frente a 0.296, P95; pendiente 0.72 frente a 2.67, P18.|
|034|Singuilucan|2.00|3.20|+1.20|NDVI mayo 0.0866 frente a 0.1254, P3; NDWI medio 0.068 frente a 0.107, P9.|
|160|Chignahuapan|3.62|4.75|+1.13|Delta NDVI junio–agosto 0.078 frente a 0.296, P2; distancia a estructura 5637 frente a 3203 m, P99.|
|162|Chignahuapan|5.59|4.70|−0.89|Desviación temporal NDWI 0.104 frente a 0.180, P1; NDVI histórico medio 0.222 frente a 0.264, P4.|
|069|Chignahuapan|5.46|4.59|−0.87|TPI −5.44, P1; dinámica brecha NDVI 0.0152 frente a 0.039, P4.|
|026|Chignahuapan|3.55|4.41|+0.86|Pendiente 0.86 frente a 2.67, P22. Las tres señales nuevas no son extremas: EVI P49, TPI P35 y brecha NDVI P36.|
|055|Chignahuapan|5.45|4.67|−0.78|Dinámica brecha NDVI 0.133, P99; TPI −3.47, P6.|
|166|Singuilucan|2.50|3.26|+0.76|Precipitación compacta 1135 frente a 1275 mm, P3; TPI −2.69 frente a −0.54, P3. Textura 3 y fase N: cada nivel aparece en 2/16 parcelas.|

Estas diez parcelas son el 7.25% de TRAIN138 y acumulan 51.54% de su error cuadrático OOF aleatorio J7. Ocho son de Chignahuapan y dos de Singuilucan. El ranking es exploratorio y seleccionado por error; no prueba que sus características expliquen ese error.

## Qué se aprende y qué no

No aparece una composición física única de las diez. Por ejemplo, 171/024/026 comparten textura 2 y fase N; 015/162/055 comparten textura 3 y fase len, pero sus errores tienen signos opuestos. Se conservan los códigos originales: no se infieren propiedades adicionales de ellos en este informe.

015 y 055 comparten TPI bajo y dinámica alta de heterogeneidad NDVI, pero 015 es sobreestimada y 055 subestimada. 069 también tiene TPI bajo y es subestimada. No se justifica una regla universal de bajar rendimiento cuando TPI sea bajo o la brecha NDVI sea alta. 026 tampoco presenta anomalías claras en las tres señales nuevas; el error difícil no equivale a anomalía en ese pequeño bloque.

El inventario extendido examina OWN1867, GEOC1831 y entradas J7, frente a TRAIN138, estado, municipio y perfil climático. Las comparaciones incluyen la parcela focal y son descriptivas, no transformaciones para validación predictiva. Se registran datos faltantes, categorías, soporte, percentiles, cercas IQR y z robusto. Las distribuciones pequeñas, discretas o degeneradas no se etiquetan como outliers continuos. La búsqueda en miles de descriptores correlacionados produce extremos por construcción: no se les atribuye significancia estadística ni capacidad de corregir sin validación nueva. Los perfiles con una sola parcela no permiten evaluar diferencias intraperfil ni distancias a vecinos dentro del perfil; sus estadísticas multivariadas se marcan sin soporte.

## Archivos y reproducción

- `scripts/468_top10_difficult_parcels_inventory.py`: extiende en una salida nueva el censo descriptivo 451, sin entrenamiento.
- `scripts/469_package_top10_difficult_parcels.py`: valida diez IDs únicos, marca soporte multivariado insuficiente y genera tablas y Excel.
- `outputs/research/top10_difficult_parcels/v1/inventario_10_parcelas_dificiles.xlsx`: resumen, entradas y señales, diferencias destacadas, categorías y errores de otros modelos/protocolos.
- `tables/outliers_all_numeric.csv` y `.parquet`: censo numérico completo.
- `tables/architecture_inputs_and_three_signals.csv`: bloque de interés arquitectónico por los cuatro ámbitos.
- `tables/top15_differences_by_scope.csv`: quince diferencias extremas por parcela y ámbito, sin campos de calidad.
- `tables/top10_errors_all_models_protocols.csv`: mismas diez parcelas en todos los modelos y protocolos de la auditoría compatible previa.

La reproducción genera advertencias de media vacía en el diagnóstico heredado de distancia para perfiles singleton; el empaquetado sustituye sus resultados por NaN y `insufficient_support`, sin alterar fuentes ni modelos anteriores.
