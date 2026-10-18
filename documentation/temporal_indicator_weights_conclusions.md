> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Indicadores temporales y pesos continuos: interpretación

Se construyeron ocho indicadores temporales propios y pendiente mínima como contexto. Se completaron12arquitecturas nuevas sobre65folds (780sistemas externos), con referencia exacta CT3/J7 y dos benchmarks del corrector anterior. Los resultados son exploratorios del mismo banco ya investigado; no hay promoción de Champion, ajuste final138 ni PRED59.

## Qué se derivó de las series

Las variables conservadas son: piso histórico de NDVImin, piso histórico de FAPARmin, intensidad del exceso de brecha NDVI, persistencia efectiva de ese exceso, anomalía de variabilidad de la brecha, exceso de brecha superior MSI, anomalía de forma del pico EVI y desacuerdo de forma Sentinel–Planet. Los nombres y fórmulas exactas están en indicator_dictionary.csv. La pendiente mínima original añade contexto físico; no es una pendiente temporal.

La persistencia utiliza(suma zpositivo)²/(6×suma zpositivo²), entre0y1. Un pico aislado produce1/6, un exceso igual en los seis meses produce1. No depende de un umbral de error aprendido ni representa superficie afectada. Las anomalías comparan2025con2022–2024de la misma parcela y el mismo mes; no con la media de todas las parcelas. No se infiere que la historia corresponda siempre al mismo cultivo.

Se exige historia completa de seis meses de cada uno de tres años;29/138parcelas(21.0%)no tienen esa referencia completa. Se preserva NaN y se imputa únicamente dentro del entrenamiento. Esto evita inventar historia, pero limita soporte y puede generar patrones de disponibilidad regional. Hay22/71faltantes en Chignahuapan,2/10Almoloya,2/16Singuilucan y3/5Cuautepec. Los dos indicadores no históricos tienen cobertura completa. La forma EVI Sentinel–Planet concuerda mucho: su indicador(1−r)/2está entre0.00033y0.0653, por lo que no constituye una discordancia grande en esta muestra.

## Cómo funciona la ponderación probada

Predicción=base+w(indicadores)×δC4. δC4proviene de un corrector fijo de cuatro padres: TPI medio, pendiente media, anomalía NDWI julio–agosto y cambio EVI julio–agosto menos mayo–junio. Se restringe δa±.25t/ha. westá entre0y1: puede retirar la corrección, nunca invertirla ni amplificarla.

Se compararon candidato sin ponderar, peso constante, peso variable compartido y pesos separados segúnδpositivo/negativo. El signo de ruta proviene de la corrección predicha, no del error verdadero desconocido. El aprendizaje utiliza correcciones candidatas cross-fitted dentro del entrenamiento y residuos base también cross-fitted. No usa etiquetas globales de35difíciles ni residuos externos como targets de entrenamiento. Todos los hiperparámetros se fijaron antes de los resultados.

Se añadieron controles de corrección directa con los nueve indicadores y de integración directa de nueve indicadores+cuatro padres. Eso permite distinguir el valor de una representación del valor específico de convertirla en un peso.

## RMSE / R²: comparación principal

|Modelo|Aleatoria|Perfil|Municipal|Espacial|
|---|---|---|---|---|
|CT3|0.5116 / 0.6361|0.5206 / 0.6232|0.5813 / 0.5302|0.6788 / 0.3594|
|J7 original|0.4864 / 0.6709|0.4890 / 0.6675|0.5808 / 0.5309|0.6808 / 0.3556|
|J7+C4previo seleccionado internamente|0.4863 / 0.6711|0.4955 / 0.6586|0.5774 / 0.5365|0.6490 / 0.4143|
|J7+C4fijo sin ponderar|0.4895 / 0.6668|0.4922 / 0.6632|0.5991 / 0.5010|0.6497 / 0.4131|
|J7+C4peso constante|0.4866 / 0.6707|0.4937 / 0.6611|0.5800 / 0.5323|0.6574 / 0.3992|
|J7+C4peso variable compartido|0.4865 / 0.6708|0.4915 / 0.6642|0.5815 / 0.5298|0.6508 / 0.4112|
|J7+C4pesos por signo predicho|0.4865 / 0.6708|0.4911 / 0.6647|0.5831 / 0.5273|0.6539 / 0.4054|
|J7+indicadores directamente|0.4827 / 0.6759|0.4865 / 0.6709|0.5852 / 0.5238|0.6595 / 0.3953|
|CT3+indicadores directamente|0.5064 / 0.6434|0.5185 / 0.6262|0.5896 / 0.5167|0.6696 / 0.3765|

Se conserva la tabla completa de16entradas y MAE/sesgo/SD en resultados y Excel. RMSE/R²se calculan sobre138OOF completas de cada repetición, luego media de diez repeticiones aleatorias. No se promedian RMSE por fold ni se combinan protocolos en una métrica única. El nuevo C4fijo no es idéntico al C4previo retuneado: compararlos sólo por nombre sin señalar sus parámetros confundiría el control.

## ¿Aprendieron los indicadores cuándo corregir?

El peso compartido supera ligeramente al constante en aleatoria, por perfil y espacial, y empeora municipal. Frente al mismo candidato sin ponderar evita parte del deterioro aleatorio/municipal, pero no mejora espacial(0.6508vs0.6497). Esto no demuestra que la nueva capa sea necesaria.

En aleatoria, el peso constante medio de J7 es0.033: la calibración prácticamente retira el candidato C4. El peso compartido sube a0.169pero es casi igual cuando el candidato tiene el signo correcto(0.171)y equivocado(0.167). No está identificando consistentemente qué correcciones convienen. Los pesos separados por signo tampoco mejoran de forma equilibrada la generalización.

En espacial el peso compartido distingue algo más:0.572cuandoδapunta en la dirección correcta frente a0.466cuando es incorrecto. Esa diferencia no basta para resolver la transferencia. El peso por signo espacial es0.596cuando acierta y0.600cuando se equivoca: no se interpreta como probabilidad de acierto ni como clasificador fiable del signo.

El candidato C4fijo tiene signo correcto para46.0%de parcelas aleatorias y58.7%espaciales. Un peso0..1puede atenuar una propuesta incorrecta, pero no crear la corrección contraria. Esta limitación de arquitectura ayuda a explicar por qué señales útiles directamente no se convierten automáticamente en un buen selector del candidato.

## Territorio y concentración de ganancias

|Bloque espacial|J7 original|Peso compartido|Indicadores directos|
|---|---:|---:|---:|
|1|0.5246|0.4800|0.5250|
|2|0.5537|0.5451|0.5641|
|3|0.9160|0.8753|0.8723|
|4|0.7988|0.6909|0.6555|
|5/Almoloya|0.3621|0.5727|0.5833|

Ambas variantes reducen errores espaciales globales y conservan una ganancia al omitir cualquier bloque del cálculo sin reajuste. Sin embargo, perjudican fuertemente Almoloya. El peso compartido reduce modestamente el deterioro del candidato fijo allí(0.5923→0.5727), pero no lo elimina.

La corrección directa con indicadores mejora J7en aleatoria−0.00370t/ha y perfil−0.00253, con deterioro municipal+0.00439. En aleatoria la ganancia cuadrática total es0.496; el cuartil difícil aporta0.836y las otras103parcelas pierden0.341. Al omitir las35difíciles, el cambio de RMSE pasa a+0.00657aleatorio,+0.01538por perfil,+0.02432municipal y+0.00255espacial. Esto sugiere una señal concentrada en el grupo que motivó la investigación, sin un mecanismo fiable para activarla selectivamente. No depende exclusivamente de171/015: al omitirlas, la ganancia aleatoria directa sigue siendo−0.00469, pero desaparece espacialmente al omitir las diez peores originales(+0.00042).

El peso compartido mantiene una mejora espacial fuera de las35(−0.01467), aunque no ofrece mejora en los otros tres protocolos fuera de ellas. No se presenta una mejora espacial como prueba de capacidad general para detectar parcelas difíciles.

## Inferencia, interpretación y decisión

Ninguno de112contrastes supera Holm0.05. Para J7+indicadores directos frente a J7, el intervalo bootstrap agrupado95%del cambio RMSE aleatorio es[−0.0143,+0.0043]; para el peso compartido frente al peso constante espacial es[−0.0222,+0.0037]. Son intervalos de OOFfijas, limitados por5bloques espaciales, selección histórica y reutilización de datos. No se declara superioridad estadística.

Las nuevas representaciones sugieren señal complementaria débil para algunos errores, pero no demuestran un activador continuo estable. No se recomienda desplegar el peso variable, reemplazar J7ni combinar automáticamente más capas. Se conservan el corrector directo de indicadores como candidato exploratorio centrado en errores difíciles y el benchmarkC4previo; ninguno resuelve la estabilidad territorial.

Antes de aumentar complejidad conviene separar dos objetivos en un nuevo diseño: mejorar la propuesta de corrección y comprobar cuándo usarla. Una posible pregunta posterior es ponderar la propuesta específica de los indicadores (distinta de C4), con el mismo control constante y calibración cruzada; no se ejecutó retrospectivamente en esta batería. Otra prioridad es calidad/soporte y alineación temporal por parcela, contrastando con representaciones ya existentes, no un nuevo screening masivo. No se presume que esas alternativas funcionen.

La interpretación por permutación agrupada mantiene cada grupo dentro del municipio del fold externo, sin reajustes; se documenta aparte como diagnóstico post hoc. Puede romper correlaciones con otros bloques y reemparejar datos faltantes, por lo que no es causal ni una validación independiente. Los coeficientes describen el modelo estandarizado y tampoco equivalen a importancia causal.

En J7+indicadores directos, permutar conjuntamente dinámica de brecha aumenta RMSEaleatorio aproximadamente0.0051y espacial0.0056; permutar los dos pisos históricos aumenta aleatorio0.0043pero no aporta señal espacial consistente. Pendiente mínima aporta cambios0.0016aleatorio y0.0034espacial. La forma del pico/desacuerdo entre sensores no muestra aportación robusta: su permutación mejora modestamente el RMSEen los cuatro protocolos. MSIes débil o perjudicial salvo espacial. Son diagnósticos, no ablaciones con reajuste; no se retiraron variables tras observarlos.

Dentro del bloque de brecha, persistencia efectiva es un coeficiente no nulo en los50folds aleatorios del corrector directo; también lo son NDVIminhistórico y pendiente mínima. La correlación entre indicadores obliga a interpretar los pisos históricos conjuntamente: coeficientes de NDVIyFAPARpueden tener signos opuestos por ajuste condicional, sin implicar efectos agronómicos opuestos. En el peso compartido las perturbaciones de bloques apenas cambian el error aleatorio, compatible con su escasa discriminación entre correcciones acertadas y erróneas.

La comparación X-only con los inventarios previos exige≥80observaciones compartidas,≥5valores distintos y SD>1e−8para no confundir columnas casi constantes o con pocos datos con equivalencias. Los pisos históricos son próximos a descriptores ya existentes(|r|≈0.95–0.97,n=109). Persistencia efectiva y anomalía de volatilidad no tienen un equivalente lineal tan cercano: máximos|r|≈0.43y0.44,n=109. Esto caracteriza una representación distinta de las mismas series, no nueva información independiente ni mejora predictiva demostrada.

Si se decide una próxima batería, los candidatos más justificados para una reducción previamente congelada son persistencia de brecha, los pisos históricos y pendiente mínima. Quedaría por comparar esa propuesta específica reducida como corrector y como candidato ponderado, con sus controles; esta interpretación no autoriza a presentar tal selección como confirmación independiente ni se ejecutó aquí.

Entregables: scripts478preparación,479ejecución,480evaluación,481auditoría y482interpretación; src/temporal_indicator_weights.py; ocho fórmulas temporales/contexto, soporte mensual, OOF, modelos, pesos por parcela, regiones, omisiones, cuartiles, pares intraperfil, coeficientes y Excel. Cuatro pruebas automatizadas pasaron. Se conserva alerta de bibliotecas OpenMP coexistentes del entorno; la ejecución terminó y se verifica replay numérico. No se alteran fuentes ni modelos anteriores.
