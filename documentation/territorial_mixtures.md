> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# R1–R3: resultados de mezclas globales, municipales y por características

La fase terminó después de guardar el diseño y congelar parámetros. **Las adaptaciones municipales y por características aportaron ganancias pequeñas en validación aleatoria, pero no una mejora territorial consistente.** No se promueve ningún modelo ni se aplica una regla definitiva por municipio.

## Qué se ejecutó

- R1: mezcla global de C-T3, GPR y CatBoost, regularizada hacia el promedio equiponderado.
- R2: mezcla municipal contraída hacia una mezcla global; mínimo 15 parcelas y 2 perfiles, con retorno a global para municipios nuevos o sin soporte.
- R3: árbol de profundidad 0/1/2 que minimiza directamente el error de la mezcla. Hojas mínimas 20/35, al menos 2 perfiles por hija y contracción de pesos. Usa únicamente lluvia compacta y NDVI de mayo; fuera del rango marginal de entrenamiento vuelve a global.

Los tres expertos externos permanecen congelados y tienen las cuatro entradas originales. Las reglas se ajustaron usando predicciones profundas honestas. La regularización global y la adaptación se seleccionaron conjuntamente dentro del entrenamiento; no se reutilizó una selección global con acceso a las etiquetas que validan las reglas. No hay intercepto, corrección aditiva o reglas especiales por nombre de municipio.

## Métricas completas

RMSE en t/ha, menor es mejor. OOF completas por repetición y media de diez repeticiones aleatorias; no media de métricas de folds.

| Modelo | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| C-T3 | 0.5116 | 0.5206 | 0.5813 | 0.6788 |
| Promedio fijo EQUAL3 | 0.4982 | 0.4979 | **0.5277** | **0.6709** |
| R1 global regularizado | 0.4989 | 0.4982 | **0.5277** | 0.6783 |
| R2 municipal | 0.4960 | **0.4977** | **0.5277** | 0.6783 |
| R3 por características | **0.4957** | 0.4995 | 0.5326 | 0.6896 |

R1 no mejora al promedio fijo. R2 mejora aleatoria 0.0021 y R3 0.0025 frente a EQUAL3; ambos mejoran en 8 de las 10 repeticiones aleatorias, que no son muestras independientes. Las diferencias son pequeñas y no demuestran superioridad estadística. El modelo TOP20/TOP15 aleatorio compatible es 0.498127: las ventajas de R2/R3 frente a él siguen siendo pequeñas, y no hay una comparación territorial equivalente del modelo TOP20/TOP15.

## Qué aprendió R2

Pesos medios **solo en folds aleatorios donde existió una regla municipal aprendida**:

| Municipio | Folds con regla | C-T3 | GPR | CatBoost |
|---|---:|---:|---:|---:|
| Chignahuapan, Puebla | 42 de 50 | 76.6% | 9.9% | 13.5% |
| Calpulalpan, Tlaxcala | 42 de 50 | 23.0% | 32.5% | 44.5% |
| Singuilucan, Hidalgo | 6 de 50 | 25.2% | 15.6% | 59.2% |

La idea de favorecer CatBoost en Singuilucan aparece cuando existe soporte, mientras Chignahuapan favorece C-T3. Son pesos aprendidos sin las etiquetas externas y luego promediados para describirlos; **no son pesos para un modelo final ni una regla universal**.

Singuilucan tiene 16 parcelas en total. En numerosos entrenamientos aleatorios queda con menos del mínimo de 15 y usa global. Calpulalpan tiene 30 parcelas/14 perfiles y Chignahuapan 71/11, antes de las particiones. Municipios pequeños quedan sin adaptación bajo los límites congelados.

En validación municipal y espacial, las predicciones R2 son exactamente iguales a R1. En municipal no se seleccionaron adaptaciones; en espacial algunas se aprendieron en entrenamiento pero ninguna se aplicó a sus parcelas externas. Por tanto, R2 no demostró una mejora de transferencia territorial. Su caso de uso candidato es parcela nueva en un municipio representado, no municipio completamente nuevo.

El control con los pesos globales propios de R2 obtiene RMSE aleatorio 0.4995; activar sus reglas lo baja a 0.4960. Esta diferencia descriptiva distingue el efecto de las reglas de haber elegido otros pesos globales, sin reajustes o nueva selección.

## Qué aprendió R3

En aleatoria se usaron 41 nodos de división entre los 50 folds: 34 sobre NDVI de mayo, 6 sobre concentración de lluvia HHI y 1 sobre lluvia total. Las divisiones indican dónde el modelo ajusta su mezcla; no son evidencia causal sobre variables agronómicas.

Ejemplo reproducible del primer fold aleatorio, elegido por su posición y no por su rendimiento: una división en NDVI de mayo ≈0.1313. La hoja inferior tiene pesos CT3/GPR/CB de 17.7/55.2/27.1%, y la superior 59.9/25.7/14.4%. Ambas tienen soporte de varios perfiles. El umbral cambia entre entrenamientos y no debe convertirse en una regla manual definitiva.

En aleatoria, R3 usa una mezcla global en aproximadamente 26% de sus predicciones; en municipal, 82.5%; en espacial, 50.3%, según la media por fold. El retorno a global incluye raíz sin división y casos fuera de rango marginal. La cobertura exacta por parcela está en OOF.route.

El control con los pesos globales propios de R3 obtiene 0.4987 aleatorio; las reglas lo bajan a 0.4957. Pero municipalmente empeoran ese control 0.5277 → 0.5326 y espacialmente 0.6783 → 0.6896.

## Bloques espaciales

R1/R2 empeoran respecto al promedio fijo en los bloques 1/2/5. R3 añade deterioro en el bloque 4: RMSE 0.6233 del promedio fijo y de su control global → 0.7121 con la compuerta. Los demás bloques de R3 coinciden con su control global. El sesgo del bloque 4 sube +0.3295 → +0.4693.

Al omitir cualquiera de los cinco bloques únicamente del cálculo, sin reajustar, R1/R2/R3 siguen peor espacialmente que EQUAL3. Las diferencias de RMSE son +0.0041–0.0122 para R1/R2 y +0.0083–0.0308 para R3. No es un deterioro que desaparezca al quitar un único bloque.

## Errores intraperfil

No hubo una mejora consistente con ambas ponderaciones frente a C-T3. Ejemplos:

- Aleatoria: R2 reduce el RMSE ponderado por pares respecto a EQUAL3 0.7832 → 0.7786, pero empeora el equilibrado por perfil 0.6040 → 0.6055. C-T3 conserva 0.7712 y 0.5900, respectivamente.
- Municipal: R2/R1 tienen RMSE por pares 0.7895 y R3 0.7892, frente a 0.7688 de C-T3.
- Espacial: R3 mejora el indicador equilibrado por perfil 0.5401 → 0.5340 frente a C-T3, pero empeora por pares 0.7675 → 0.7874.

No interpretar una mejora de niveles de rendimiento como mejor diferenciación entre parcelas climáticamente semejantes.

## Recomendación

Conservar EQUAL3 y C-T3 como referencias. **No promover R1–R3 ni programar una regla rígida “Singuilucan = CatBoost”.** R2 merece conservarse como candidato exploratorio para municipios representados: los pesos tienen una interpretación territorial coherente y una ganancia aleatoria pequeña. R3 no justifica una compuerta de aplicación general, dado su deterioro agrupado y espacial.

No ampliar profundidad, variar límites o elegir pesos regionales retrospectivamente con estos mismos resultados. Si se autoriza continuación, priorizar validación independiente de la adaptación municipal en parcelas nuevas de municipios conocidos, especialmente aumentando el soporte de Singuilucan. La utilidad en territorios desconocidos requiere otra evidencia; no se deduce de esta batería.

## Reproducibilidad y corrección de implementación

Se guardaron 5,382 nuevas OOF y 195 paquetes de mezcladores, con reglas, rutas, parámetros y dependencias de expertos externos. Se verificó la reproducción de los 195 modelos. Cuatro pruebas pasaron, incluida la alteración de +10,000 en etiquetas externas sin cambio de reglas, parámetros o predicciones.

Se ajustaron 914 GPR profundos y 29,858 CatBoost incluyendo sus selecciones y reajustes. C-T3 se recuperó íntegramente. La ejecución completa de mezcladores produjo 18,395 ajustes internos/finales de validación. Los 914 optimizadores GPR seleccionados convergieron; 104 contextos alcanzaron límites, conservados sin ampliación. No hubo advertencias de ajuste CatBoost.

Después de terminar los expertos se corrigió un error de exportación: el campo params estaba duplicado en la llamada que construye filas de la tabla de selección. Se archivó la fuente anterior y se registraron hashes anterior/corregido en `audit/implementation_fix.json`. No cambió ninguna especificación, rejilla, partición, criterio o dato congelado. Se reutilizaron los 914 paquetes profundos, sin nuevos ajustes. El intento interrumpido realizó 21 ajustes de R1 adicionales, registrados aparte; no contribuyen a las predicciones finales. La fuente original, la corregida y los archivos consumidos se verificaron mediante la cadena de auditoría. El tiempo de manifest.wall_seconds corresponde a la ejecución reanudada, excluyendo la fase profunda ya terminada.

No se ajustó un modelo final de 138 etiquetas, no se generaron las 59 predicciones PRED y no se modificó modelo TOP20/TOP15. Las etiquetas se han explorado repetidamente: resultados exploratorios, sin confirmación independiente o superioridad estadística. No se presentan intervalos de mezcla sin calibración.

- [Diseño prospectivo](territorial_mixtures_design.md)
- [Configuración congelada](../outputs/modeling/territorial_mixtures/v1/frozen_design.json)
- [OOF y rutas](../outputs/modeling/territorial_mixtures/v1/tables/oof_predictions.csv)
- [Reglas por fold](../outputs/modeling/territorial_mixtures/v1/tables/rules.csv)
- [Diagnósticos y comparaciones](../outputs/research/territorial_mixtures_synthesis/v1/informe.md)
- [Figura de resultados y retorno a global](../outputs/research/territorial_mixtures_synthesis/v1/performance_and_fallback.png)
- [Auditoría de corrección de código](../outputs/modeling/territorial_mixtures/v1/audit/implementation_fix.json)
