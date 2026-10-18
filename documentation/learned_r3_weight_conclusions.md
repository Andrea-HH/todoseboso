> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Peso aprendido, asimetría y disponibilidad de R3: conclusiones

## Resultado

No aparece un salto convincente en el desempeño aleatorio mediante pesos aprendidos o correcciones asimétricas. El control de disponibilidad histórica es más útil y sencillo: conserva la base en parcelas sin R3 completo, y aplica R3 donde hay soporte. Sobre SHARES (J7 con gate reducido) alcanza RMSE aleatorio .4748 / R² .6865 y espacial .6333 / .4423, con 26 campos de entrada. No supera el .4725 / .6895 aleatorio del experimento previo de vecinos satelitales DIRECT; no se declara un nuevo líder.

Se evaluaron33 entradas:24 sensibilidades nuevas y9 controles exactos, manteniendo65 folds. Las penalizaciones1/10 se fijaron antes de obtener resultados y se reportan separadas; no se eligió una usando folds externos. Esta es una arquitectura de stacking con entradas OOF y metamodelos de hiperparámetros fijos. No se completó ni usó la búsqueda interna de penalizaciones del diseño inicial: véase la enmienda previa a resultados. El error de ajuste del peso no es validación interna del peso.

## Comparaciones principales

Cada celda muestra RMSE t/ha / R². Aleatoria es media de diez métricas de OOF completas; no media de folds ni de protocolos.

| Modelo | Aleatoria | Perfil | Municipal | Espacial |
|---|---|---|---|---|
| J7 + R3 global, referencia | .4756 / .6854 | .4748 / .6865 | .5726 / .5442 | .6550 / .4035 |
| J7 + disponibilidad MASK | .4749 / .6863 | .4752 / .6861 | .5727 / .5440 | .6521 / .4087 |
| J7 + peso aprendido P1 | .4760 / .6849 | .4741 / .6875 | .5746 / .5410 | .6623 / .3901 |
| J7 + aprendido por signo P1 | .4763 / .6844 | .4748 / .6866 | .5731 / .5434 | .6549 / .4036 |
| SHARES + R3 global | .4753 / .6858 | .4772 / .6834 | .5751 / .5402 | .6447 / .4221 |
| SHARES + disponibilidad MASK | .4748 / .6865 | .4774 / .6831 | .5752 / .5400 | .6333 / .4423 |
| SHARES + pesos por signo P1 | .4757 / .6852 | .4772 / .6833 | .5754 / .5397 | .6408 / .4291 |
| SHARES + aprendido por signo P10 | .4758 / .6851 | .4773 / .6832 | .5774 / .5364 | .6419 / .4270 |
| C-T3 + R3 global | .4968 / .6568 | .5050 / .6454 | .5726 / .5442 | .6766 / .3635 |
| C-T3 + disponibilidad MASK | .4961 / .6578 | .5033 / .6478 | .5668 / .5533 | .6668 / .3818 |
| C-T3 + aprendido por signo P1 | .4975 / .6558 | .5101 / .6382 | .5668 / .5533 | .6620 / .3907 |

Las 33 filas, MAE, sesgo y diagnósticos están en el Excel y `learned_r3_weight_results.md`. Las filas destacadas permiten comparar hipótesis; no son un selector externo ni una confirmación independiente de las mejores cifras.

## Qué aporta realmente el control MASK

R3 depende de nivel histórico NDVI mínimo, persistencia de heterogeneidad NDVI y pendiente mínima. En29/138 parcelas falta soporte completo para esos indicadores. El control conserva exactamente esas parcelas y sus rendimientos, pero hace cero la corrección; no elimina casos ni asigna valores manuales por región. En consultas completas selecciona intensidad0/.5/1 dentro del entrenamiento mediante las propuestas R3 OOF.

SHARES+MASK mejora frente a SHARES+R3 global .00054 t/ha aleatoria y .01137 espacial, y pierde .00023 por perfil y .00015 municipal: cambios minúsculos salvo el espacial. MAE aleatorio pasa .3409→.3396; espacial .5137→.5004. No es solamente una mejora de RMSE que esconda un MAE peor en esos protocolos.

La ganancia espacial persiste al omitir cualquiera de los cinco bloques del cálculo, sin reajustar: entre .0054 y .0170 t/ha frente a SHARES+R3. Frente a J7+R3 también persiste, entre .0115 y .0350. La versión SHARES con peso satelital fijo anterior dependía más de Almoloya; MASK muestra un patrón más repartido.

No toda la mejora es apagar imputaciones: en espacial, las109 parcelas con R3 completo pasan de RMSE .6877 a .6782 y las29 incompletas .4477 a .4243. La intensidad seleccionada cambia en el bloque4 de .5 a1 al evaluar el control con disponibilidad; ésta es una decisión interna. No se eligió el bloque usando resultados externos. En J7+MASK las109 completas quedan iguales espacialmente y la mejora procede únicamente de las incompletas.

En SHARES, Singuilucan espacial mejora .7301→.6611 y Almoloya .5862→.5505. Chignahuapan apenas cambia .5474→.5450; Calpulalpan queda igual .8125. Tepeapulco empeora .4254→.5504, con una sola parcela. Almoloya sigue peor que J7 sin corrector (.3621): no se resolvió el deterioro original. Los municipios de uno/tres casos no sustentan reglas regionales.

La pequeña ganancia aleatoria de SHARES+MASK frente a R3 global se produce en las103 parcelas fuera del grupo difícil: ganancia SSE +.1777; en las35 difíciles pierde .1071; total +.0706. En espacial mejora ambos grupos (+.7776 y +1.2282). Este control ayuda a evitar parte del daño de correcciones, pero no resuelve el núcleo de casos difíciles.

El control no demuestra que los valores imputados sean siempre dañinos ni que más datos históricos empeoren el modelo. Indica que extrapolar R3 desde indicadores incompletos requiere cautela. La ausencia de datos tiene distribución territorial desigual; aun sin usar nombres de región, puede reflejar características regionales. Si se completa la historia o cambia la cobertura en otro ciclo, hay que reevaluar este comportamiento.

## Qué pasó con la asimetría

Se aprendieron pesos positivos/negativos distintos, contraídos a un peso global, con mínimo15 propuestas por signo; no se usó el rendimiento verdadero de la consulta ni una regla por municipio. La sensibilidad SHARES_ASYM_P1 baja espacial .6447→.6408, pero pierde ligeramente aleatoria/municipal y no supera MASK. En J7 la asimetría no mejora espacial frente a R3 global. El supuesto de que separar signos bastaría para resolver extrapolación queda debilitado bajo esta formulación.

No se puede traducir el signo aprendido en una regla universal como «bajar siempre menos». Los promedios de pesos por signo dependen de los entrenamientos y del soporte. Tampoco se rechaza toda corrección asimétrica: se probaron sólo estas dos penalizaciones y esta representación R3, sin búsqueda abierta.

## Qué pasó con el peso condicionado

Los seis descriptores fueron predicción base, magnitud/signo de propuesta R3, distancia al soporte, diferencia respecto a los24 vecinos satelitales y disponibilidad de historia. El peso queda entre0/1: atenúa, nunca amplifica ni invierte la propuesta. La geometría requiere FAPAR histórico adicional; añade una entrada frente al corrector simple.

En aleatoria el peso aprendido apenas distingue correcciones útiles de perjudiciales. J7_LEARNED_P1 asigna .969 a propuestas que ayudan y .961 a las que dañan; SHARES_LEARNED_P1 .962 y .960. Son pesos casi constantes cercanos a1, sin discriminación suficiente para mejorar el agregado. En espacial SHARES_LEARNED_P1 incluso pondera más las propuestas perjudiciales (.786) que las útiles (.725). Estas son asociaciones descriptivas de OOF, no pruebas causales ni probabilidades calibradas.

J7_LEARNED_P1 mejora algo por perfil (.4748→.4741), pero empeora aleatoria, municipal y espacial. C-T3 aprendido-asimétrico P1 tiene cifras municipales/espaciales interesantes, pero MASK mantiene menor RMSE aleatorio/perfil y prácticamente igual municipal. No se justifica la mayor complejidad para un ganador general.

La hipótesis de que estos seis descriptores permiten reconocer de forma estable cuándo corregir no recibe apoyo suficiente. Puede faltar señal, haber ruido o cambiar la relación entre protocolos; esta batería no identifica de manera concluyente cuál es la causa. Los modelos de pesos más flexibles no constituyen evidencia de superioridad por sus errores de ajuste en entrenamiento.

## Recomendación

Conservar SHARES+MASK como candidata sencilla de26 entradas y J7+R3 global como referencia. C-T3+MASK mantiene una alternativa de siete entradas y mejora sus cuatro protocolos frente a C-T3+R3 global; C-T3 soporte satelital anterior conserva mejor espacial, con ocho entradas y peor aleatoria/perfil. No promover automáticamente ninguna.

No ampliaría ahora la complejidad del peso ni su búsqueda de penalizaciones. La evidencia favorece tratar explícitamente la disponibilidad/fiabilidad de historia. Para superar de manera material el entorno .47/.68, el siguiente trabajo debería auditar cobertura y construir un bloque temporal pequeño, previamente definido, que aporte información nueva sobre caída/recuperación o desfase de2025 respecto a su historia. Antes debe comprobarse que esas señales no estén ya representadas. Esa ampliación de variables no se ejecutó en esta etapa.

Se realizaron372 contrastes predefinidos; ninguno supera .05 tras Holm. Se mantienen duplicados de propio-global/referencia J7 por fidelidad al plan conservador. Los intervalos de OOF fijas no incorporan toda búsqueda histórica, reajuste ni dependencia espacial residual; sólo hay cinco bloques espaciales. La ausencia de significancia no demuestra equivalencia. No se interpreta el menor valor puntual de una sensibilidad como superioridad confirmada.

## Reproducibilidad y alcance

Salida: `outputs/modeling/learned_r3_weight/v1`. Se guardaron59,202 filas OOF,1,560 modelos externos nuevos y9 controles exactos. La auditoría reconstruyó195 calibraciones R3, sus características OOF y los pesos ajustados, y reprodujo las1,560 predicciones de modelos por fold. Cuatro pruebas verifican límites, asimetría/fallback, disponibilidad, exclusión de identidad y tratamiento de soporte incompleto.

El peso se ajustó sólo en el entrenamiento externo con entradas cross-fitted. Sus penalizaciones se fijaron antes de resultados externos, según `learned_r3_weight_amendment.md` y `amendment_01.json`; no se completó la selección interna del diseño inicial. El runner original se conserva en `pre_amendment`, junto con su diseño. El runner ejecutado fue494b;495 evalúa y496 cierra la entrega. No se alteraron las138 etiquetas, modelo TOP20/TOP15 o experimentos anteriores, ni se ajustó final138 o generaron nuevas59PRED.
