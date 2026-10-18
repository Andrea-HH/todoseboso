# Comparación de C-T3, Local04D, Compact14 y Reference26

Comparación descriptiva y pareada, sin entrenamiento nuevo: 7,176 predicciones OOF, 1,794 por arquitectura, sobre las mismas 138 parcelas y 65 folds. Diez repeticiones aleatorias y una evaluación completa por perfil, municipal y espacial. Se verifican coincidencia de IDs, fold, respuesta y predicciones históricas C-T3. Métricas sobre OOF completas por repetición y después promedio; no se tratan repeticiones como parcelas independientes. Error = predicho − observado.

Resultados y residuos completos: `outputs/research/four_leaders/v1/comparacion_cuatro_modelos.xlsx`; tablas CSV, residuos por parcela y OOF Parquet en la misma carpeta. Reproducción: `scripts/502_compare_four_leaders.py`.

## RMSE t/ha / R²

| Modelo | Aleatoria | Perfil | Municipal | Espacial |
|---|---|---|---|---|
| C-T3 | .5116 / .6361 | .5206 / .6232 | .5813 / .5302 | .6788 / .3594 |
| Local04D | .4930 / .6619 | .5031 / .6481 | .7602 / .1964 | .9794 / −.3337 |
| Compact14 | .4773 / .6832 | .4793 / .6805 | .5755 / .5395 | .6431 / .4250 |
| Reference26 | .4748 / .6865 | .4774 / .6831 | .5752 / .5400 | .6333 / .4423 |

Reference26 tiene el menor RMSE observado de los cuatro en cada protocolo. Compact14 queda muy cerca; su mayor pérdida es espacial, .00972 t/ha. No se demuestra equivalencia ni superioridad estadística entre ambos. Local04D no sostiene transferencia territorial equilibrada en este banco.

## Residuos y distribución de ventajas

En espacial, sesgo C-T3/Local04D/Compact14/Reference26 = +.1912/+.4707/+.1232/+.2285; MAE .5306/.7434/.5140/.5004; percentil95 absoluto 1.4223/1.9792/1.2776/1.2538. La dispersión espacial del error es .6513/.8589/.6312/.5907: el menor sesgo de Compact14 no implica menor RMSE. Reference26 reduce más la dispersión.

Proporción dentro de ±.5 t/ha espacial =59.4%/49.3%/55.8%/55.1%; aleatoria=77.5%/73.6%/76.4%/76.9%. C-T3 conserva ventaja bajo esta tolerancia concreta; Reference26 controla mejor la cola. No hay dominancia de toda la distribución de errores.

RMSE espacial por municipio (C-T3/Local04D/Compact14/Reference26): Almoloya .360/.214/.456/.551; Chignahuapan .550/.608/.561/.545; Singuilucan .825/1.388/.745/.661; Calpulalpan .909/1.498/.813/.812; Cuautepec .421/.229/.440/.524. Tamaños respectivamente10/71/16/30/5. Son descripciones, no reglas para seleccionar modelo usando esos mismos resultados.

Todos comprimen el rango: sobreestiman rendimientos bajos y subestiman altos. En espacial, sesgo del cuartil bajo=+1.013/+1.640/+.894/+.887 y del alto=−.466/−.459/−.549/−.337. Compact14 sacrifica particularmente rendimientos altos frente a Reference26. No se usa R² dentro de cuartiles como criterio principal porque su rango es reducido.

Para diferencias entre parcelas del mismo perfil, dando igual peso a cada perfil, RMSE espacial C-T3/Local04D/Compact14/Reference26=.540/.536/.523/.517. Mejora modesta; no indica resolver heterogeneidad intraperfil. El soporte y pares elegibles están en intraprofile.csv; esta métrica no es RMSE individual del rendimiento.

## Alcance estadístico y arquitectónico

Se calculan24 contrastes de diferencias pareadas de pérdidas cuadráticas, signos por grupo (perfil para aleatoria/perfil, municipio para municipal y bloque para espacial), ajuste Holm conjunto. Dos contrastes sobreviven: Reference26 frente a C-T3 aleatoria (p ajustada .0253) y Compact14 frente a C-T3 por perfil (.0036). Los territoriales no, con solo9 municipios o5 bloques. No demostrar diferencia no prueba igualdad; la selección histórica de arquitecturas exige una confirmación nueva para una conclusión definitiva.

Local04D conserva PCA20 C4 transductiva sobre197 X, sin usar etiquetas externas: no equivale a una evaluación inductiva de PCA para nuevas parcelas. Los resultados históricos97/41 y sus RMSE .4819/.4957 pertenecen a otro banco y no se mezclan aquí. La PCA no reduce la necesidad de sus entradas originales, y sus cargas no son importancias causales.

C-T3: cuatro variables, Elastic Net global, menor costo y explicación directa. Compact14: C-T3 + Ridge local24 vecinos en cinco señales complementarias, coordenadas, peso global aprendido y R3 final con tres indicadores. Reference26: siete señales locales, corrección interna, mezcla condicionada a diez proporciones geológicas y R3; mayor complejidad. Las coordenadas cuentan como entradas en14/26 y siguen definiendo vecinos. Compact14 no es una única regresión de14 coeficientes.

Recomendación: Reference26 para menor error agregado en este banco; Compact14 para reducir fuentes y capas con pérdida pequeña observada; C-T3 como referencia operativa parsimoniosa y buena alternativa cuando se prioriza sencillez. Local04D aporta complementariedad local, pero no se recomienda como sustituto global para transferencia territorial. No se promueve ni se cambia ningún Champion o predicción PRED.
