# Conclusiones: nuevas señales y ubicación arquitectónica

Se ejecutaron las doce alternativas congeladas y sus tres referencias en las mismas 65 particiones. Las señales no aportan una mejora equilibrada en estas formulaciones. Se conservan J7_BOTH y las mezclas anteriores; no se promueve ninguna extensión ni se generan PRED59.

## Resultado por ubicación

**LOCAL:** ampliar la regresión local aporta pequeñas ganancias por perfil, entre aproximadamente 0.0011 y 0.0018 t/ha de RMSE, pero todas las variantes empeoran la validación aleatoria y espacial. La mejor cifra por perfil es E10_ETN_LOCAL: RMSE 0.48527 y R² 0.67259 frente a 0.48707/0.67015 de su referencia. En aleatoria empeora a 0.49322/0.66171 frente a 0.48704/0.67009. No justifica aumentar la complejidad.

**CORRECTION:** ampliar el corrector Elastic Net de los residuos locales es menos perjudicial en aleatoria y municipal que añadir las señales a LOCAL. Sin embargo, tampoco supera el RMSE aleatorio de sus referencias y pierde la pequeña ganancia por perfil. En espacial E10_ET_CORRECTION y E10_ETN_CORRECTION mejoran solamente 0.000027 y 0.000030 t/ha: diferencias prácticamente nulas. En J7, el MAE espacial mejora levemente (0.52770 frente a 0.52910), pero el RMSE empeora (0.68097 frente a 0.68081). No deben confundirse esos criterios.

La tercera señal (ETN frente a ET) empeora el RMSE aleatorio en ambas ubicaciones y las tres arquitecturas. Reduce ligeramente el RMSE por perfil, sin evidencia de una ganancia territorial relevante. Ninguno de los 96 contrastes conserva significancia tras Holm; esto no prueba equivalencia y el estudio sigue siendo exploratorio por el origen de las variables en residuos ya observados.

## Parcelas difíciles y resto de la muestra

Las señales no resuelven las parcelas que motivaron la prueba. En aleatoria, J7 original sobreestima 171 en 2.1625 y 015 en 2.0800 t/ha. Con EVI+TPI en LOCAL los errores son +2.2137 y +2.1140; en CORRECTION son +2.1876 y +2.0775. El pequeño alivio de 015 en CORRECTION se acompaña de deterioro en 171. Añadir la tercera señal no cambia la conclusión.

Todas las alternativas siguen empeorando el RMSE aleatorio al excluir 171 y 015 del cálculo, sin reajustar. La pérdida no se debe exclusivamente a esas dos parcelas. En J7_ET_LOCAL el deterioro restante es +0.00299 t/ha y en J7_ET_CORRECTION +0.00257.

Tampoco todo deteriora para todos: J7_ET_CORRECTION reduce el error absoluto medio por parcela respecto a J7 en aproximadamente 55.1% de las parcelas aleatorias, aunque su SSE agregado empeora. Las magnitudes de las pérdidas compensan las mejoras; contar parcelas beneficiadas no sustituye RMSE/MAE.

## Qué muestra la arquitectura

La rama local ampliada J7_ET_LOCAL obtiene RMSE espacial 0.97514; el experto después de su corrección compacta queda en 0.81488; la mezcla final con CT3 en 0.68159. En J7_ET_CORRECTION, el experto corregido queda en 0.80663 y la mezcla en 0.68097. La protección territorial viene de la corrección compacta y, especialmente, de la mezcla con CT3, más que de estas nuevas señales.

El peso medio del experto en municipal está alrededor de 0.05. En espacial varía mucho por bloque: para J7_ET_CORRECTION es aproximadamente 0.57, 0.82, 0.051, 0.0018 y 0.14 en bloques 1–5. Esto explica por qué cambios del experto se amortiguan en los bloques 3 y 4. No se modificó el gate para forzar el uso de las señales.

Hay intercambios regionales: J7_ET_CORRECTION mejora el RMSE municipal de Singuilucan en 0.00850, pero empeora Calpulalpan en 0.00974; Chignahuapan casi no cambia (−0.000038). J7_ET_LOCAL empeora Singuilucan en 0.01309 y Calpulalpan en 0.00572. No hay una recuperación regional amplia. El bloque espacial 3 tampoco mejora con J7_ET_LOCAL ni J7_ET_CORRECTION.

## Qué hipótesis debilita y qué no demuestra

Se debilita la hipótesis de que añadir directamente estas columnas a la Ridge local o a su corrector lineal regularizado permita recuperar de manera generalizable las pérdidas de rendimiento no explicadas. Ser un outlier en un predictor no implica una relación repetible con rendimientos bajos, y un patrón llamativo en dos casos no basta para aprenderla al excluirlos del entrenamiento.

No se demuestra que la topografía o la evolución satelital sean agronómicamente irrelevantes; tampoco que las etiquetas sean erróneas, que el error sea irreducible o que toda arquitectura no lineal vaya a fracasar. Estas pruebas no incluyen añadir señales al gate, árboles nuevos, reglas por municipio ni ajuste específico de las dos parcelas. Un experimento futuro de otra ubicación o no linealidad necesitaría una hipótesis propia y control de complejidad, no presentarse como rescate confirmado de este resultado.

## Definiciones y reproducibilidad

La tercera señal es el máximo aumento por día de `NDVI_mean − NDVI_min` entre observaciones sucesivas, es decir, dinámica de heterogeneidad interna. No es crecimiento directo del cultivo. EVI es última menos primera observación válida; no garantiza las mismas fechas extremas en cada parcela. TPI es elevación menos media espacial 3×3, agregada por parcela; no equivale a inundación observada.

Se conservaron parámetros, representaciones, referencias y particiones originales. Los siete tests del pipeline pasaron. Los 780 expertos externos no presentaron fallback. Se registraron cuatro avisos de bibliotecas OpenMP y ninguna advertencia de convergencia en el registro de entrenamiento. Se verificaron predicciones de referencia exactas y replay de todas las ramas con tolerancia 1e−12.

El entrenamiento terminó para los 65 folds; el empaquetado inicial colisionó con una columna `index` ya presente en las referencias. El script 457 recuperó únicamente la agregación usando `execution_index`, conservando el script de entrenamiento congelado y todos sus hashes y checkpoints. No se reentrenó por este fallo.

Para reproducir o reanudar sin sobrescribir resultados completados: `python scripts/459_reproduce_difficult_case_signals.py`. El lanzador conserva las etapas terminadas, ejecuta las pendientes y aplica la recuperación de empaquetado solo si existen los 65 checkpoints. Una ejecución completa nueva requiere un directorio de resultados nuevo y una congelación correspondiente, en lugar de borrar la evidencia existente.

Resultados completos: [tablas e incertidumbre](difficult_case_signals_results.md). Libro: `outputs/modeling/difficult_case_signals/v1/evaluacion_ubicacion_senales.xlsx`. Predicciones OOF, ramas, pesos, coeficientes, residuos, cambios regionales, omisiones y análisis sin 171/015 están bajo `tables`. El archivo `delivery_audit.json` verifica los productos y las exclusiones de entrenamiento.
