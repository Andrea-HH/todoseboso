> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Complementariedad de C-T3, GPR y CatBoost compacto

La fase terminó. **Hay complementariedad aprovechable en las métricas agregadas, pero no una combinación territorialmente estable para promover.** El promedio fijo es más convincente que aprender pesos libres con esta muestra; su ventaja espacial sigue concentrada y no resuelve las diferencias intraperfil.

## Diseño congelado

Los tres modelos emplean las mismas cuatro entradas: lluvia total abril–octubre, fracción abril–junio, concentración HHI y NDVI de mayo. Se conservaron los 65 folds externos y sus particiones internas originales.

- **EQUAL3:** promedio fijo de un tercio de C-T3, F5-01 GPR y F7-00 CatBoost. Se fijó antes del entrenamiento.
- **BLEND3:** pesos no negativos que suman uno, con pasos de 0.1; 66 candidatos incluyendo los modelos individuales. Selección por RMSE sobre las OOF internas completas. Empates redondeados a diez decimales favorecen C-T3 y después GPR. No hay intercepto ni reglas territoriales.
- Los tres modelos externos se recuperaron intactos y se reprodujeron contra sus OOF originales.
- Las bases internas de C-T3 ya estaban ajustadas con selección recursiva; GPR utiliza su optimización LML dentro de entrenamiento. Los modelos internos anteriores de CatBoost no se reutilizaron: su configuración se había elegido usando todos los folds internos. Se retuneó CatBoost exclusivamente dentro de cada entrenamiento interno, con la misma rejilla de ocho configuraciones y validaciones locales del mismo protocolo. Así las etiquetas de selección de pesos no participaron en seleccionar su configuración.

## Resultados completos

RMSE en t/ha; menor es mejor. OOF completas de 138 parcelas por repetición y media de las diez repeticiones aleatorias. No se promedian métricas de folds.

| Modelo | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| C-T3 | 0.5116 | 0.5206 | 0.5813 | 0.6788 |
| GPR F5-01 | 0.5040 | 0.4998 | 0.5442 | 0.7348 |
| CatBoost F7-00 | 0.5049 | 0.5153 | 0.5282 | **0.6426** |
| EQUAL3, promedio fijo | **0.4982** | 0.4979 | **0.5277** | 0.6709 |
| BLEND3, pesos internos | 0.5024 | **0.4966** | 0.5683 | 0.6913 |

EQUAL3 mejora frente a C-T3 en los cuatro protocolos: diferencias de RMSE −0.0134, −0.0227, −0.0536 y −0.0078. Su MAE también mejora en los cuatro. No supera espacialmente a CatBoost y la diferencia municipal entre ambos es muy pequeña. Su RMSE aleatorio es prácticamente igual al Champion compatible, 0.498127, sin demostrar superioridad.

BLEND3 mejora frente a C-T3 en tres protocolos, pero empeora espacialmente 0.0125 de RMSE y 0.0138 de MAE. Su sesgo municipal pasa de −0.0203 a +0.0488; el aumento de sesgo absoluto es 0.0285. No cumple los límites exploratorios congelados.

## ¿Los modelos aportan errores distintos?

Sí, parcialmente. C-T3 y CatBoost tienen correlación de errores municipal 0.7989 y signos opuestos en 23.2% de las parcelas. Es la diferencia más clara entre estas arquitecturas. En aleatoria la correlación es 0.9178; en espacial, 0.9227. C-T3 y GPR presentan correlaciones de 0.9145–0.9638 según protocolo. Por tanto, existe compensación, pero la mayoría de sus errores siguen siendo compartidos.

Estas medidas se calcularon con OOF externas para interpretación. No seleccionaron pesos, modelos, rejillas ni territorios. Signos opuestos no bastan para demostrar una compensación útil: importan magnitudes y sesgos.

## Concentración territorial

EQUAL3 mejora municipalmente el error absoluto en 68.1% de las parcelas. Singuilucan explica 66.4% de la reducción neta de error cuadrático, Calpulalpan 27.3%; otros municipios aportan ganancias o pérdidas menores. Al excluir cualquiera de los municipios únicamente del cálculo, sin reajustar, EQUAL3 sigue mejor que C-T3. Excluyendo Singuilucan, la ventaja municipal de RMSE sigue siendo 0.0217. La ganancia municipal no depende completamente de ese municipio.

En espacial la evidencia es más frágil: el bloque 4 aporta una reducción de SSE de 4.4985, mientras el bloque 3 pierde 3.4738; la ganancia neta total es solo 1.4584. La contribución del bloque 4 supera 100% porque compensa pérdidas de otros bloques. Excluir el bloque 4 transforma la ventaja espacial en un deterioro de **+0.0190 de RMSE** frente a C-T3. No hay transferencia espacial equilibrada.

## Pesos aprendidos

Pesos medios CT3/GPR/CatBoost: aleatoria 0.376/0.250/0.374; perfil 0.120/0.660/0.220; municipal 0.160/0.480/0.360. Son diagnósticos de estabilidad, no pesos para un modelo final.

En espacial la selección interna eligió CatBoost puro en los bloques 1/2 y C-T3 puro en los bloques 3/4/5: no se mezclaron modelos. Esa selección empeoró el resultado espacial global. No son reglas regionales programadas; son resultados del mismo criterio interno global aplicado a diferentes entrenamientos externos. La selección interna no pudo anticipar las ventajas externas de CatBoost en el bloque 4.

El promedio fijo ganó a los pesos aprendidos en aleatoria, municipal y espacial. Eso apoya mantener fuerte regularización de cualquier futura combinación; no demuestra que un promedio fijo sea óptimo universalmente.

## Diferencias entre parcelas del mismo perfil

El promedio no resuelve la heterogeneidad intraperfil. EQUAL3 empeora el RMSE ponderado por pares en los cuatro protocolos respecto a C-T3. En municipal pasa 0.7688 → 0.7895; en espacial 0.7675 → 0.7784. Por perfil mejora el indicador equilibrado entre perfiles 0.5479 → 0.5362, pero empeora el ponderado por pares 0.7634 → 0.7689. No constituye una mejora local consistente con ambas ponderaciones.

Las ganancias en rendimiento absoluto no deben interpretarse como mejor diferenciación de parcelas climáticamente semejantes.

## Recomendación

Conservar EQUAL3 como **referencia exploratoria de combinación**, no como nuevo Champion. Detener la búsqueda de pesos libres en esta batería: no ofrece una ventaja consistente sobre el control simple. Si se autoriza una continuación, formular una sensibilidad pequeña de pesos fuertemente contraídos al promedio, elegida completamente dentro del entrenamiento, y exigir estabilidad frente a omisión de bloques y ausencia de daño intraperfil. No realizar selección externa de la pareja más favorable ni convertir el bloque 4 en una regla regional.

La prioridad para confirmar transferencia sigue siendo disponer de campañas o parcelas independientes, especialmente fuera del territorio dominante. Las etiquetas se han explorado repetidamente: no se declara superioridad estadística ni se interpretan estas mejoras como confirmación independiente.

## Reproducibilidad y alcance

Se reutilizaron todas las bases externas y las internas admisibles de C-T3/GPR; se ajustaron 239 contextos internos de CatBoost, con 7,799 ajustes incluyendo selección y reajuste. Se guardaron 65 combinaciones y 3,588 nuevas OOF de EQUAL3/BLEND3, junto con 5,382 OOF de referencias reproducidas. Los modelos de mezcla guardan pesos y rutas de los tres modelos originales; esos archivos archivados son dependencias explícitas.

Pasaron tres pruebas, incluyendo alterar los rendimientos externos en +10,000 y comprobar que predicciones, pesos y métricas de selección interna permanecen iguales. Se reprodujeron los tres controles externos y las 65 mezclas guardadas. Todos los archivos consumidos conservaron sus hashes. El runtime notificó coexistencia Intel/LLVM OpenMP; terminó sin interrupciones. Las advertencias de ajuste CatBoost se registran en cb_registry.csv.

No se agregaron variables, no se ejecutaron correcciones residuales, no se ajustó un modelo final sobre 138 etiquetas, no se modificó Champion y no se generaron predicciones PRED. No se ofrecen intervalos de mezcla sin calibración.

- [Diseño congelado](../outputs/modeling/compact_ensemble/v1/report/design.md)
- [OOF](../outputs/modeling/compact_ensemble/v1/tables/oof_predictions.csv)
- [Pesos por fold](../outputs/modeling/compact_ensemble/v1/tables/weights.csv)
- [Diagnósticos y comparaciones](../outputs/research/compact_ensemble_synthesis/v1/informe.md)
- [Figura de resultados y pesos](../outputs/research/compact_ensemble_synthesis/v1/results_and_weights.png)
- [Implementación](../src/compact_ensemble.py)
- [Pruebas](../tests/test_compact_ensemble.py)
