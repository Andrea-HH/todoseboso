> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Investigación de simplificación de J7 + R3

Se congelaron seis nuevas ablaciones antes del entrenamiento: tres indicadores individuales, dos parejas faltantes y una corrección constante. Se recuperó la pareja persistencia + pendiente (R2) ya existente, sin reentrenarla. Cada variante conserva J7 exactamente y selecciona amplitud 0/.25/.5 con OOF internas completas, imputación/escalado dentro del entrenamiento, Elastic Net alpha .01 y l1_ratio .5 y límite final ±.25 t/ha. La comparación externa es exploratoria; no constituye confirmación independiente ni selección final.

## Simplificar el corrector

| experiment | random | climate_profile | municipality | spatial |
| --- | --- | --- | --- | --- |
| CT3 | 0.5116 / 0.6361 | 0.5206 / 0.6232 | 0.5813 / 0.5302 | 0.6788 / 0.3594 |
| J7_ABL_CONSTANT | 0.4863 / 0.6712 | 0.4902 / 0.6659 | 0.5774 / 0.5365 | 0.6929 / 0.3326 |
| J7_ABL_NDVI_PERSISTENCE | 0.4767 / 0.6839 | 0.4812 / 0.6781 | 0.5751 / 0.5402 | 0.6836 / 0.3503 |
| J7_ABL_NDVI_SLOPE | 0.4809 / 0.6784 | 0.4803 / 0.6792 | 0.5730 / 0.5435 | 0.6798 / 0.3575 |
| J7_ABL_ONLY_NDVI | 0.4813 / 0.6778 | 0.4844 / 0.6737 | 0.5748 / 0.5406 | 0.6929 / 0.3326 |
| J7_ABL_ONLY_PERSISTENCE | 0.4812 / 0.6779 | 0.4864 / 0.6711 | 0.5771 / 0.5369 | 0.6824 / 0.3525 |
| J7_ABL_ONLY_SLOPE | 0.4861 / 0.6713 | 0.4886 / 0.6681 | 0.5756 / 0.5393 | 0.6707 / 0.3746 |
| J7_BOTH | 0.4864 / 0.6709 | 0.4890 / 0.6675 | 0.5808 / 0.5309 | 0.6808 / 0.3556 |
| J7_GLOBAL_R2 | 0.4802 / 0.6793 | 0.4802 / 0.6793 | 0.5746 / 0.5409 | 0.6528 / 0.4075 |
| J7_GLOBAL_R3 | 0.4756 / 0.6854 | 0.4748 / 0.6865 | 0.5726 / 0.5442 | 0.6550 / 0.4035 |

La simplificación más defendible es R2: persistencia de heterogeneidad NDVI + pendiente mínima. Frente a R3 pierde .0046 t/ha aleatoria, .0054 por perfil y .0020 municipal, y mejora .0022 espacial. No demuestra equivalencia, pero representa un compromiso de complejidad. Un solo indicador no conserva el balance: pendiente sola ayuda espacial, pero apenas mejora aleatoria/perfil; NDVI solo mejora aleatoria, pero empeora espacial a .6929. La pareja sin pendiente pierde espacial (.6836). No basta una corrección del promedio: el control constante llega a .6929 espacial.

## Qué complejidad se ahorra realmente

J7 usa 28 campos de entrada: compact4, siete entradas del experto local, quince del gate físico y dos coordenadas. R3 añade tres indicadores diferentes, por lo que son 31 campos de entrada; R2 añade dos y deja 30. No son 31 parámetros efectivos ni 31 mediciones originales. R3 requiere reconstruir historia de NDVI mínimo; R2 retira ese agregado del corrector, pero su persistencia sigue requiriendo NDVI medio/mínimo históricos. J7 también conserva NDVI histórico, Planet y geología. Quitar un indicador no elimina automáticamente una fuente ni el costo de entrenamiento del sistema.

La arquitectura mantiene C-T3, Ridge local de 24 vecinos, su corrector de compact4, el gate físico y ahora el corrector global final. Este último suma pocos coeficientes; el costo principal sigue en los ajustes locales, la validación anidada y la construcción de señales. No se ha demostrado que convertir el sistema entero en un único Elastic Net conserve su capacidad.

## Simplificar J7 completo: evidencia ya existente

| experiment | random | climate_profile | municipality | spatial |
| --- | --- | --- | --- | --- |
| BASE12_BOTH | 0.4880 / 0.6688 | 0.4879 / 0.6691 | 0.5810 / 0.5307 | 0.6843 / 0.3490 |
| CT3 | 0.5116 / 0.6361 | 0.5206 / 0.6232 | 0.5813 / 0.5302 | 0.6788 / 0.3594 |
| DROP_HISTORY_WATER | 0.4870 / 0.6701 | 0.4871 / 0.6702 | 0.5811 / 0.5306 | 0.6840 / 0.3494 |
| DROP_SOIL | 0.4874 / 0.6696 | 0.4897 / 0.6666 | 0.5807 / 0.5311 | 0.6811 / 0.3550 |
| GATE_ONLY_SHARES | 0.4876 / 0.6693 | 0.4901 / 0.6660 | 0.5832 / 0.5271 | 0.6852 / 0.3472 |
| J10_SHARES | 0.4869 / 0.6703 | 0.4882 / 0.6686 | 0.5839 / 0.5260 | 0.6846 / 0.3483 |
| J7_BOTH | 0.4864 / 0.6709 | 0.4890 / 0.6675 | 0.5808 / 0.5309 | 0.6808 / 0.3556 |
| J7_SHARES | 0.4865 / 0.6708 | 0.4913 / 0.6644 | 0.5835 / 0.5266 | 0.6894 / 0.3393 |
| J9_SHARES | 0.4875 / 0.6695 | 0.4917 / 0.6639 | 0.5826 / 0.5280 | 0.6904 / 0.3373 |
| MEAN_BOTH | 0.4890 / 0.6674 | 0.4982 / 0.6549 | 0.5813 / 0.5301 | 0.6808 / 0.3555 |
| PRIOR_BIGBOTH | 0.4852 / 0.6725 | 0.4996 / 0.6530 | 0.5847 / 0.5247 | 0.6811 / 0.3549 |

Estos modelos se recuperan sin nuevas ejecuciones. J7_SHARES reduce 28→23 campos usando sólo diez proporciones geológicas en el gate: conserva aleatoria (.4865 vs .4864), pero empeora espacial (.6894 vs .6808). MEAN_BOTH reduce a 21 campos sustituyendo Ridge por promedio de vecinos; pierde aleatoria/perfil y no ofrece una mejora territorial consistente. Ninguna de estas filas incluye el nuevo R3. No se suman sus diferencias a la ganancia de R3 ni se simula la combinación añadiendo un corrector entrenado sobre otra base.

## Recomendación y siguiente prueba concreta

Mantener R3 como referencia y R2 como alternativa mínima, sin declarar equivalencia estadística. Para simplificar todo el sistema, la siguiente prueba acotada sería J7_SHARES + corrector R2/R3 y MEAN_BOTH + R2/R3, reconstruyendo residuos y calibraciones internas de cada base. Permitiría saber si el nuevo corrector compensa retirar parte del gate o Ridge; esa compensación no está probada. No se ejecutaron estas nuevas arquitecturas en esta investigación. Evitar una búsqueda abierta por todas las subcombinaciones o elegir pesos usando los folds espaciales.

Las seis nuevas ablaciones produjeron 390 sistemas externos; se guardaron modelos por fold, selecciones y predicciones OOF. Scripts reproducibles: 487 y 488. Fuentes/modelos previos permanecen intactos; no hay ajuste final138, PRED59 ni cambio de Champion. Las tablas muestran RMSE/R² separados por protocolo; no se crea una métrica mezclando validaciones distintas.