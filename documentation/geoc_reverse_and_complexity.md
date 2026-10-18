> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Local04D como base y C-T3 como corrección: resultado y complejidad

Se ejecutó la dirección inversa en este repositorio: **Local04D + amplitud × Elastic Net de sus residuos usando las cuatro entradas de C-T3**. Los coeficientes del corrector se vuelven a estimar para los nuevos targets residuales; no se suma sin más la predicción original de C-T3.

[Excel](../outputs/modeling/geoc_bridge/v1/reverse/v1/comparacion_inversa_y_complejidad.xlsx), [métricas](../outputs/modeling/geoc_bridge/v1/reverse/v1/diagnostics/metrics_summary.csv), [contrastes pareados](../outputs/modeling/geoc_bridge/v1/reverse/v1/diagnostics/paired_cluster_tests.csv), [benchmark](../outputs/modeling/geoc_bridge/v1/reverse/v1/audit/complexity_benchmark.json).

## Diseño y controles

Se conservaron Local04D k24/alpha30/potencia1 y su PCA20 transductiva congelada. El corrector usa las cuatro variables originales, ConditionalFeatures original, grid Elastic Net de12 combinaciones y amplitud [0,.25,.5], incluido cero. Selección sobre RMSE de OOF internas completas; empates favorecen menor amplitud y mayor penalización. Intercepto estándar permitido, sin reglas municipales. Los residuos de cada entrenamiento se generan con Local04D sobre vecinos que excluyen las etiquetas retenidas; las selecciones de corrector y amplitud no usan la evaluación externa. En cada validación interna se genera otra capa de residuos cross-fitted. Las subparticiones agrupadas siguen su protocolo; nunca se reemplazan por aleatorias.

Se usaron65 folds originales y16 máscaras97/41 originales de GeoC. Las diferencias entre direcciones incluyen cambiar arquitectura y grid del corrector: no es una prueba causal aislada del orden. Persiste el desajuste entre bases cross-fitted y bases reajustadas. No se reabrió la búsqueda de vecinos/PCA ni se modificaron los archivos anteriores o las59 predicciones finales.

## Resultados en65 folds

RMSE en t/ha; aleatoria promedia diez OOF completas por repetición.

| Formulación | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| C-T3 | .511582 | .520604 | .581259 | .678778 |
| Local04D | .492957 | .503052 | .760246 | .979401 |
| Promedio fijo50/50 | .487540 | .489058 | .644949 | .803979 |
| C-T3 base + corrector local | .496553 | .516386 | .577901 | .764134 |
| **Local04D base + corrector compacto** | **.489986** | **.496240** | **.659273** | **.807728** |

La nueva dirección mejora a Local04D en los cuatro RMSE: -.002970 aleatoria, -.006812 perfil, -.100973 municipal y -.171674 espacial. Pero no recupera C-T3 municipalmente ni espacialmente: errores mayores en+.078014 y+.128950. Tampoco supera al promedio fijo en aleatoria, perfil o municipal, ni a la dirección anterior en municipal o espacial. No hay una dirección residual ganadora en todos los protocolos.

MAE de la nueva dirección: .353260 aleatoria, .341440 por perfil, .468125 municipal y .619533 espacial. R2: .665951, .657612, .395682 y .092879. El corrector se activa en47/50 folds aleatorios y en todos los folds agrupados. Amplitud media .455/.40/.45/.50 respectivamente. Seleccionarlo internamente con frecuencia no garantiza mejora externa.

## Banco GeoC97/41, separado

| Modelo | RMSE pooled656 | MAE pooled | Media RMSE de16 splits |
|---|---:|---:|---:|
| C-T3 | .528906 | .378042 | .521743 |
| Local04D | .495741 | .342501 | .487845 |
| Promedio50/50 | .498809 | .342898 | .490737 |
| Local04D + corrector compacto | .494551 | .347536 | .486569 |

La reducción de RMSE frente a Local04D es .001190 t/ha, aproximadamente1.19 kg/ha. A la vez, MAE empeora .005035 t/ha. No se interpreta como mejora práctica consolidada: parece un pequeño intercambio entre cola de errores y error absoluto medio. No se mezcla este banco de125 parcelas evaluadas con el de confirmación08.

## Regiones e intraperfil

En municipal, la dirección inversa mejora Chignahuapan frente a C-T3 de .580680 a .558584 y Calpulalpan de .493347 a .440116, pero empeora Singuilucan de .867689 a1.314474. Espacialmente obtiene .605156 en Chignahuapan,1.116764 en Calpulalpan y1.097592 en Singuilucan, frente a .549926/.908773/.824659 de C-T3. Estos resultados no se convierten en reglas de elección municipal.

Intraperfil aleatorio mejora el RMSE equilibrado por perfil frente a C-T3 (.589951→.570102) pero empeora el ponderado por pares (.771183→.794789). Espacialmente ocurre lo mismo: .540147→.534551 por perfil y .767538→.789518 por pares. No demuestra una solución local consistente bajo ambas ponderaciones.

## Estadística y reproducción

Se calcularon14 contrastes pareados: frente a C-T3/Local04D/dirección anterior en los cuatro protocolos originales y frente a C-T3/Local04D en97/41. Bootstrap5,000 por perfiles, municipios o bloques; prueba por signos de conglomerados y Holm dentro de esta nueva familia. No se trata todo el historial del proyecto como una sola búsqueda corregida. Inferencia exploratoria condicional a OOF fijas, sin incertidumbre de reentrenamiento y con solo cinco bloques espaciales.

Ningún contraste resiste Holm a .05. Frente a Local04D, el IC95% de delta RMSE es [-.007145,.004705] en aleatoria, [-.194390,.016168] municipal, [-.308880,.031464] espacial y [-.013091,.015628] en97/41. No se afirma equivalencia ni superioridad estadística. El beneficio de corregir Local04D es descriptivo y territorialmente incompleto.

Se guardaron2,450 OOF nuevas y81 predictores externos. Los81 se recargaron y reprodujeron con diferencia máxima cero. Se verificaron las exclusiones de membresía. Pasaron dos pruebas, incluida alteración de los rendimientos externos en+10,000 sin cambios en selección o predicciones. Cero advertencias de ajuste; se registró la advertencia operacional Intel/LLVM OpenMP sin interrupciones. Los archivos consumidos conservaron sus hashes.

## ¿Existe una ventaja real del modelo compacto?

Sí: tiene ventajas concretas de dependencia de datos, mantenimiento, interpretación y transferencia observada. No se deduce solo de contar variables.

| Aspecto | C-T3 | Local04D |
|---|---|---|
| Entradas finales |4 predictores |20 scores PCA + coordenadas |
| Construcción de entradas |7 lluvias mensuales para3 resúmenes + NDVI mayo |2,082 variables C4 para PCA20 |
| Ajuste supervisado |Una regresión global, hasta4 coeficientes y un intercepto |Una Ridge20 por consulta, con24 vecinos etiquetados |
| Dependencias al predecir |Transformación y coeficientes guardados |Representación, geometría y rendimientos de referencia disponibles |
| Interpretación |Coeficientes de entradas explícitas, con reservas por correlación |Efectos en componentes y vecindarios variables |
| Transferencia observada |Mejor municipal y espacial en estas pruebas |Mejor aleatoria y reconstrucción97/41 |

PCA20 sobre2,082 variables implica41,640 cargas del transformador, pero **no son41,640 parámetros supervisados ajustados contra138 rendimientos**. La PCA es no supervisada. Las regresiones locales se solapan y están regularizadas: tampoco se suman sus coeficientes como si fueran modelos independientes. Contar4 frente a2,082 por sí solo exageraría la comparación; hay que distinguir ingeniería, representación y capacidad supervisada.

Benchmark CPU, un hilo,20 repeticiones tras3 calentamientos, sobre las mismas59 X y componentes originales ya ajustados:

| Modelo | Mediana59 predicciones | Mediana por parcela |
|---|---:|---:|
| C-T3 |0.0004972 s |0.00843 ms |
| Local04D |0.0784906 s |1.33035 ms |

Local04D tardó unas158 veces más en este benchmark, porque ajusta una Ridge por consulta. **Ambos son rápidos para59 parcelas**; esta diferencia no justifica por sí sola elegir un modelo. No incluye extracción satelital, generación de variables, ajuste PCA ni carga de modelos. Es una medición de esta máquina, no un benchmark universal. El objeto C-T3 serializado ocupa1,771 bytes; el contenido numérico mínimo de scores20, coordenadas y etiquetas de138 referencias ya suma25,392 bytes, sin incluir el transformador PCA ni metadatos. No es una comparación de tamaños completos de artefactos equivalentes.

En términos prácticos, la ventaja principal de C-T3 es entregar una referencia fácil de auditar, reproducir y mantener, con menor dependencia de proximidad geográfica y mejor transferencia observada. Local04D conserva una razón de uso si el objetivo prioritario es reconstruir las59 parcelas dentro del territorio conocido. Estos resultados no prueban que la simplicidad siempre gane ni que C-T3 esté libre de error o sesgo regional.

## Otras combinaciones interesantes, propuestas sin ejecutar

1. **Ridge local con las cuatro variables de C-T3**, sin PCA ni bloque2082. Es el siguiente contraste más informativo: separa el beneficio de localidad del beneficio de la representación grande. Debe conservar control geográfico y seleccionar cualquier regularización solo internamente; no asumir que alpha30 tiene idéntico efecto tras cambiar escalado y número de entradas.
2. **Mezcla condicionada al soporte disponible**, que tienda hacia C-T3 cuando los vecinos etiquetados estén lejos o sean poco representativos. El soporte se calcula exclusivamente con X y vecinos TRAIN; pesos o umbrales se eligen internamente. No es una regla fija por municipio ni una garantía de rescatar los bloques difíciles. La mezcla global ya probada no resuelve esto.

No priorizaría otro modelo de muchos bloques ni una búsqueda abierta de correcciones. El siguiente estudio útil es descomponer localidad versus representación; si se busca decidir una entrega de competencia, debe mantenerse aparte de la pregunta de transferencia territorial y preservar los bancos originales.

Scripts416/417; implementación `src/geoc_reverse.py`; resultados en `outputs/modeling/geoc_bridge/v1/reverse/v1/`. No se modificó GeoC, Champion, los rendimientos ni las59 predicciones finales.
