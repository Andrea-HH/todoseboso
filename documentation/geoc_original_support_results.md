# C-T3 + Local04D original con soporte geográfico

**Resultado: esta mezcla no mejora de forma equilibrada a C-T3 y no se recomienda integrarla.** Se probó el Local04D completo que pidió el usuario: PCA20 de C4 (2,082 variables de origen),24 vecinos, alpha30 y potencia1. No se sustituyó por una Ridge local climatológica de cuatro variables.

[Excel de resultados](../outputs/modeling/geoc_support_blend/v1/mezcla_CT3_Local04D_original_soporte.xlsx), [métricas](../outputs/modeling/geoc_support_blend/v1/diagnostics/metrics_summary.csv), [comparaciones estadísticas](../outputs/modeling/geoc_support_blend/v1/diagnostics/paired_cluster_tests.csv), [figura](../outputs/modeling/geoc_support_blend/v1/diagnostics/original_local_support_comparison.png).

## Diseño congelado

Predicción = CT3 + w × soporte(q) × (Local04D − CT3). La representación original de Local04D permanece congelada y transductiva en las197 X; no se presenta como una PCA inductiva entrenada solo con TRAIN. Todas las etiquetas, selección de C-T3 y vecinos etiquetados se restringen al entrenamiento correspondiente.

Soporte(q) = min(1, mediana de las distancias TRAIN al24.º vecino excluyendo la propia parcela / distancia del objetivo a su24.º vecino TRAIN), con denominador mínimo1e-6. El cálculo solo usa geometría del entrenamiento, sin reglas por municipio. El peso w se elige entre0,.25,.5,.75,1 sobre MSE de OOF internas completas; empates a doce decimales favorecen menor peso local. Cero devuelve exactamente C-T3. Local04D no se retunea.

Como control necesario se ejecutó una mezcla con la misma rejilla de pesos y las mismas bases internas, pero soporte=1. Este control reproduce exactamente las1,794 OOF anteriores de INNER_BLEND. Por tanto, las diferencias no se deben a reemplazar el modelo local o a cambiar particiones. La variante con soporte vuelve a seleccionar w internamente; el contraste incluye soporte y su interacción con selección de peso, no un efecto causal aislado del soporte a peso idéntico.

Se conservaron los65 folds originales y las16 máscaras97/41 originales de GeoC. Los C-T3 internos de97/41 se ajustaron y seleccionaron exclusivamente en cada entrenamiento interno. No se ejecutó el banco08 ni se utilizaron modelos finales entrenados con138 para evaluar pseudoobjetivos conocidos.

## Resultados en65 folds

RMSE en t/ha. Aleatoria promedia diez OOF completas por repetición; los otros protocolos tienen138 OOF cada uno.

| Modelo | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| C-T3 | .511582 | .520604 | .581259 | .678778 |
| Local04D original | .492957 | .503052 | .760246 | .979401 |
| Promedio fijo50/50 anterior | .487540 | .489058 | .644949 | .803979 |
| Mezcla original con peso interno, sin soporte | .489739 | .507542 | .604414 | .691801 |
| **C-T3 + Local04D original con soporte** | **.505720** | **.535563** | **.600689** | **.702300** |
| Mezcla con soporte de Ridge local4, referencia anterior distinta | .504034 | .516660 | .577981 | .681186 |

La nueva mezcla mejora aleatoria frente a C-T3 en.005862, pero empeora perfil.014959, municipal.019430 y espacial.023522. También empeora al control sin soporte en aleatoria/perfil/espacial; municipal mejora solo.003725 respecto a ese control, sin recuperar C-T3. La representación amplia no ofrece una ventaja en esta formulación frente a la mezcla compacta anterior.

El soporte efectivo no garantiza acierto: describe geometría y no afinidad agronómica de los vecinos ni la calibración de Local04D. Un vecino cercano puede compartir errores sistemáticos; un peso prudente tampoco elimina el sesgo de extrapolación.

## Banco GeoC97/41, separado

RMSE pooled sobre656 predicciones repetidas de125 parcelas. Es un banco de desarrollo reutilizado, no confirmación en datos nuevos.

| Modelo | RMSE pooled | MAE pooled |
|---|---:|---:|
| C-T3 | .528906 | .378042 |
| Local04D original | .495741 | .342501 |
| Promedio50/50 | .498809 | .342898 |
| Mezcla con peso interno, sin soporte | .500812 | .346197 |
| **Local04D original con soporte + C-T3** | **.520974** | **.369054** |

La nueva mezcla mejora frente a C-T3, pero pierde respecto a Local04D y a las mezclas directas anteriores. No confundir con el RMSE.481936 del banco08, que utiliza otras máscaras. La media de los16 RMSE de la nueva mezcla es.513556; no es su RMSE pooled.520974.

## Pesos, regiones y soporte

Peso local nominal medio y efectivo medio, respectivamente: aleatoria.610/.462; perfil.450/.381; municipal.200/.042; espacial.400/.392; GeoC97/41.422/.291. Las cifras son diagnósticas por entrenamiento, no pesos finales ni reglas regionales. La variación entre nominal y efectivo depende del soporte disponible en cada consulta.

Municipalmente el modelo conserva exactamente C-T3 en Chignahuapan y Calpulalpan, pero empeora Singuilucan de.867689 a.975174. Espacialmente empeora Chignahuapan de.549926 a.607561, mientras Singuilucan queda igual a C-T3 (.824659). No se diseñan reglas a partir de estas zonas. Las tablas guardan resultados por estado/municipio/bloque, omisiones sin reajuste, intraperfil y ganancias parcelarias.

## Estadística

Se fijaron15 contrastes: la mezcla con soporte frente a C-T3, Local04D y la mezcla sin soporte en cinco protocolos/bancos. Se realizaron5,000 remuestreos por conglomerados y pruebas por signos de diferencias de pérdida cuadrática, con Holm dentro de esta familia. Las repeticiones permanecen agrupadas; no se tratan como muestras independientes. Clusters: perfiles para aleatoria/perfil/97/41, municipios para municipal y bloques para espacial. Inferencia condicional a OOF fijas, sin reentrenamiento ni corrección por toda la búsqueda histórica.

No se demostró mejora sobre C-T3 después de Holm. Frente a la mezcla sin soporte aparecen señales de deterioro bajo este procedimiento exploratorio: p Holm.039898 en aleatoria,.006750 por perfil y.040298 en97/41. No se declaran conclusiones independientes de nueva campaña. La ausencia de significación de otros contrastes no demuestra equivalencia. Cinco bloques y nueve municipios ofrecen potencia territorial limitada.

## Decisión

No integrar ni generar nuevas59 predicciones de esta variante. Queda debilitada la hipótesis concreta de que esta regla de soporte por distancia al24.º vecino permita combinar equilibradamente C-T3 con el Local04D original. No se rechaza toda mezcla geográfica ni se concluye que el bloque amplio carezca de información; el problema puede estar en cómo identifica soporte útil, en errores compartidos o en la transferencia local.

Conservar las referencias actuales y cerrar esta sensibilidad antes de ampliar rejillas o programar reglas regionales. La ventaja de un modelo compacto no desaparece al introducir la representación amplia: en esta prueba no hubo compensación territorial que justificara esa complejidad. Cualquier siguiente definición de soporte o mezcla requiere otro diseño congelado y se mantiene exploratoria por reutilizar estas etiquetas.

## Reproducibilidad

Se guardaron4,900 OOF nuevas y162 predictores externos (81 por cada mezcla). Se recargaron y reprodujeron exactamente todos, con diferencia máxima cero. El control sin soporte coincide con INNER_BLEND previo en los65 folds. Dos pruebas pasaron: límites convexos/fallback y selección con desempate a favor de C-T3. Se comprobaron exclusiones de entrenamiento/validación y hashes de las fuentes. La ejecución terminó sin advertencias de ajuste; se observó la advertencia operacional Intel/LLVM OpenMP sin afectar reproducción.

Implementación: `src/geoc_support_blend.py`; scripts420/421. Diseño, modelos, selección, soporte por parcela, métricas y estadísticas en `outputs/modeling/geoc_support_blend/v1/`. GeoC, Champion, C-T3, los138 rendimientos y las59 predicciones finales permanecen intactos. No se entrenó un modelo final138 ni se amplió la familia automáticamente.
