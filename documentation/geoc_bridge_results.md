# Comparación y combinaciones de C-T3 y Local04D, ejecutadas en fira_nuria

Se implementó un puente independiente en este repositorio. GeoC, nuestros ganadores históricos y sus 59 predicciones finales permanecen intactos. Se comparan exactamente C-T3 y Local04D, un promedio fijo, una mezcla elegida internamente y una corrección residual local. No se ejecutó una búsqueda de k, PCA, alpha ni nuevas variables.

[Excel de resultados](../outputs/modeling/geoc_bridge/v1/comparacion_CT3_Local04D.xlsx), [figura de ambos bancos separados](../outputs/modeling/geoc_bridge/v1/diagnostics/comparison_two_banks.png), [OOF completas](../outputs/modeling/geoc_bridge/v1/tables/oof_predictions.csv).

## Reproducción e información disponible

Se extrajeron sin alterar sus cuerpos cuatro funciones de GeoC a `src/geoc_local04d_snapshot.py`, revisión fe056a759790e5e4cf5d1d62dec323851625b121. Se conservaron k24, alpha30, potencia1, la PCA20 C4 congelada, el escalado posterior de scores sobre197 X y la normalización original de distancia por mediana de vecino más cercano (0.399745483 km). La escala de distancias determina la escala de pesos y la regularización efectiva; no se sustituyó por una implementación aproximada.

La diferencia máxima frente a las 59 predicciones originales de Local04D fue 8.88e-16 t/ha. En sus 656 predicciones históricas de validación también fue 8.88e-16. Los 197 IDs y los 138 rendimientos coinciden entre proyectos. La PCA es **transductiva**, usa X de197 y no se reajusta dentro del fold. Esta evaluación no se presenta como prueba de una PCA inductiva para parcelas nuevas; sí se restringen todas las etiquetas y vecinos a TRAIN del fold. No se auditó de nuevo toda la generación de las 2,082 variables C4.

## Modelos congelados

- **CT3:** bases originales recuperadas exactamente en65 folds. En el banco97/41 se reajusta y selecciona su grid original únicamente con97 etiquetas, CV interna4-fold semilla2026.
- **LOCAL04D:** Ridge local original sobre24 vecinos geográficos etiquetados, utilizando los20 scores PCA; parámetros fijos.
- **FIXED50:** promedio .5 CT3 + .5 LOCAL04D, establecido antes de entrenar.
- **INNER_BLEND:** peso Local04D en [0,.25,.5,.75,1], seleccionado en las OOF internas originales; empate a doce decimales favorece menor peso local. No hay reglas municipales.
- **RESIDUAL_LOCAL:** CT3 + amplitud * Ridge local de sus residuos, con k24/alpha30/power1 fijos y amplitud [0,.25,.5]. Cada residuo de entrenamiento procede de C-T3 recursivamente ajustado y seleccionado sin esa observación. La selección del corrector excluye etiquetas de validación interna y externa. Cero retorna exactamente C-T3. Persiste el cambio de tamaño de entrenamiento entre bases cross-fitted y la reajustada.

Las dos últimas variantes se ejecutaron en los65 folds; el banco97/41 se limita a los dos modelos directos y el promedio fijo. Los modelos finales ajustados con138 etiquetas no se utilizaron para predecir pseudoobjetivos que ya hubieran visto.

## Banco 1: los65 folds originales

RMSE en t/ha. OOF completas por repetición; aleatoria media de diez repeticiones. Las otras validaciones contienen138 OOF cada una.

| Modelo | Aleatoria | Perfil climático | Municipal | Espacial |
|---|---:|---:|---:|---:|
| C-T3 | .511582 | .520604 | .581259 | .678778 |
| Local04D | .492957 | .503052 | .760246 | .979401 |
| Promedio50/50 | .487540 | .489058 | .644949 | .803979 |
| Mezcla seleccionada internamente | .489739 | .507542 | .604414 | .691801 |
| C-T3 + corrector residual local | .496553 | .516386 | .577901 | .764134 |

El promedio reduce RMSE aleatorio .024042 y por perfil .031546 frente a C-T3. Es una complementariedad predictiva descriptiva real en esas tareas, pero empeora RMSE municipal .063690 y espacial .125201. No se recomienda como reemplazo territorial de C-T3.

R2 aleatorio: CT3 .636069, Local04D .661916, promedio .669405. Espacial: CT3 .359394, Local04D -.333695 y promedio .101279. El R2 espacial negativo de Local04D corresponde a este protocolo: no invalida su uso para reconstrucción local de objetivos conocidos.

MAE aleatorio CT3/Local/promedio: .374948/.352615/.348162. MAE municipal: .460329/.599075/.511629; espacial: .530612/.743351/.616589. Por tanto, el deterioro territorial no es solo consecuencia de la penalización cuadrática de unos pocos errores.

El selector interno asigna a Local04D peso medio .665 en aleatoria, .55 por perfil, .05 municipal y .30 espacial. Reduce exposición local en validación municipal, pero no consigue superar a C-T3 en los protocolos territoriales. Estas frecuencias no se transforman en reglas regionales retrospectivas.

## Banco 2: las16 máscaras históricas97/41 de GeoC

Son las máscaras originales de desarrollo, no el banco nuevo de confirmación08. Se recuperaron exactamente de archivos y se verificaron656 observaciones repetidas sobre125 parcelas distintas. No todas las138 se evalúan y unas aparecen más veces que otras.

| Modelo | RMSE pooled656 | Media RMSE de16 splits | MAE pooled |
|---|---:|---:|---:|
| C-T3, reajustado en97 | .528906 | .521743 | .378042 |
| Local04D fijo | .495741 | .487845 | .342501 |
| Promedio50/50 | .498809 | .490737 | .342898 |

Local04D conserva el mejor punto estimado en este banco. El promedio supera a C-T3, pero **no supera a Local04D**. La reducción frente a CT3 es .030097 pooled. No se compara aquí con .481936 del banco08: son otros objetivos retenidos. La configuración de Local04D se eligió históricamente sobre desarrollo; reutilizar estas máscaras no ofrece una confirmación independiente.

## ¿Los residuos se complementan?

Sí, parcialmente. Correlación de errores Local04D/CT3: .8845 aleatoria, .8260 por perfil, .8600 municipal y .8810 espacial. Proporción de errores con signos opuestos:22.1%,23.9%,14.5% y13.8%. En las máscaras97/41, correlación .8955 y signos opuestos23.3%. No basta observar correlaciones menores de uno: las magnitudes y los sesgos explican por qué el promedio empeora territorialmente.

La corrección residual local mejora aleatoria .015029, por perfil .004218 y municipal .003358 respecto a CT3, pero empeora espacial .085356. Su amplitud media interna es .49/.30/.20/.25 respectivamente. No se recomienda su integración. La mezcla directa y el corrector residual responden preguntas distintas; no son formulaciones equivalentes.

## Concentración territorial e intraperfil

Local04D empeora Chignahuapan municipal de .580680 a .653851 y Singuilucan de .867689 a1.400922. El promedio obtiene .606700 y1.127044. Espacialmente, Calpulalpan pasa de .908773 a1.498488 con Local04D, y Singuilucan de .824659 a1.388133. La fortaleza anterior de CatBoost en Singuilucan no se reproduce con este modelo local.

Por bloques espaciales, Local04D empeora1/2/3/4 y mejora5 (Almoloya). El promedio también empeora1/2/3/4 y mejora5. No se trata solamente de un fallo del bloque3. El corrector residual empeora especialmente bloques1/2: .505445→.759776 y .572523→.678230. No se ajustaron reglas sobre estos hallazgos.

Intraperfil aleatorio, promedio50/50 mejora el RMSE de diferencias equilibrado por perfil .589951→.571491, pero empeora el ponderado por pares .771183→.773436. La corrección residual mejora ambos en aleatoria, a .577814 y .767721, pero no mantiene esa ventaja agrupada: espacial .541760/.772552 frente a .540147/.767538 de CT3. No se resolvió la diferenciación intraperfil de forma consistente.

## Estadística

Se calculan diferencias pareadas frente a CT3,5,000 remuestreos por conglomerados y pruebas por cambio de signos de pérdidas cuadráticas. Clusters: perfiles para aleatoria/perfil/GeoC, municipios para municipal, bloques para espacial. Diez repeticiones o16 splits no se consideran muestras independientes. Holm cubre los18 contrastes de esta batería, no toda la búsqueda histórica del proyecto. Las inferencias son condicionales a OOF congeladas y no incorporan reentrenamiento, selección histórica ni toda la dependencia espacial entre perfiles.

Promedio50/50 frente a CT3:

| Banco/protocolo | Delta RMSE | IC percentil95% | p Holm de pérdida cuadrática |
|---|---:|---|---:|
| Aleatoria65 | -.024042 | [-.069025,-.005902] | .069597 |
| Perfil65 | -.031546 | [-.083002,-.009061] | .062047 |
| Municipal65 | +.063690 | [-.011550,.185489] | 1.000000 |
| Espacial65 | +.125201 | [.003651,.224518] | 1.000000 |
| GeoC97/41 pooled | -.030097 | [-.069522,-.012271] | .002700 |

La señal promedio-vs-CT3 en97/41 resiste Holm **bajo esta prueba exploratoria**, pero no demuestra superioridad frente a Local04D ni confirmación en otra campaña. En los65 folds ninguna comparación de esta batería resiste Holm a .05. Diferencias entre intervalos y p ajustados responden a métodos y multiplicidad distintos. Con cinco bloques el p bilateral exacto mínimo es .0625; la potencia espacial es limitada.

## Decisión

Existe una combinación prometedora para reconstrucción dentro de territorio representado: promedio50/50 reduce errores aleatorios y por perfil. Sin embargo, sacrifica transferencia municipal y espacial, y tampoco gana a Local04D en las máscaras específicas de GeoC. La corrección local residual no elimina ese sacrificio.

Conservar CT3 como referencia territorial simple, Local04D como candidato transductivo de reconstrucción local y el promedio como sensibilidad, sin promover ninguno automáticamente ni reemplazar las59 salidas finales. No iniciar búsquedas de pesos por municipio o vecinos a partir de estos resultados. Si la prioridad pasa a ser exclusivamente el conjunto fijo de59, la siguiente pregunta sería una comparación congelada en el banco08 real recuperando sus memberships y OOF; ese banco tampoco es una campaña nueva y no debe reutilizarse como confirmación independiente después de seleccionar allí mezclas.

## Artefactos y verificación

Se guardaron10,938 registros OOF:8,970 de los65 folds y1,968 del banco97/41. Las bases CT3 de los65 folds se recuperaron intactas; en97/41 se entrenaron16 nuevas bases con su selección interna. Se recargaron y reprodujeron exactamente los325 predictores de los65 folds. La comprobación de exclusiones verifica los IDs reales de entrenamiento de cada base profunda utilizada para los targets residuales, además de recuperar la procedencia original. Dos pruebas pasaron. Los hashes consumidos permanecen iguales; las advertencias operacionales Intel/LLVM OpenMP no impidieron completar ni reproducir la ejecución.

Diseño congelado, cachés de scores/distancias y datos197, modelos por fold, selección interna, estadísticas, métricas regionales, omisiones sin reajuste y ganancias por parcela están en `outputs/modeling/geoc_bridge/v1`. El archivo de scores y los metadatos originales se conservan localmente; no se publicaron datos de GeoC. No se reconstruyó la PCA desde sus2082 columnas, no se ejecutó una sensibilidad inductiva ni el banco08 sin su membership original, y no se generaron nuevas predicciones finales.

Implementación: `src/geoc_bridge.py`, `src/geoc_local04d_snapshot.py`; entrenamiento y síntesis: scripts414/415. La reproducción tiene controles que preservan versiones completas y exige una carpeta nueva para otra configuración.
