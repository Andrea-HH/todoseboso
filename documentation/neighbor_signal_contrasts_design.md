# Contrastes de señales respecto a vecinos: diseño congelado

Se prueban cuatro alternativas sobre J7_BOTH: GEO_ATTENUATE, COMPACT_ATTENUATE, GEO_RESIDUAL y COMPACT_RESIDUAL. Se conservan CT3 y J7 externos originales como referencias. No se repite el experimento sobre expertos 9/10 ni se buscan variables nuevas.

## Comparables y contrastes

Se utilizan las tres señales previamente nominadas: cambio neto EVI Planet, TPI 3×3 medio y máximo aumento temporal de la brecha NDVI medio−mínimo. Esta última mide dinámica de heterogeneidad interna, no crecimiento directo del cultivo.

GEO utiliza los 24 vecinos geográficos; COMPACT utiliza los 24 más cercanos en compact4 estandarizado dentro del entrenamiento. Las señales nuevas no definen la distancia. Se incluyen todos los empates en la distancia del vecino 24, excluyendo siempre la propia parcela y cualquier parcela del fold de evaluación.

Cada señal produce dos características: diferencia con la mediana vecinal dividida por SD del entrenamiento, y diferencia dividida por max(1.4826×MAD vecinal, 0.25×SD del entrenamiento, 1e−8). Ambas se recortan a ±6. Las seis características conservan signo. Imputación, escalas y vecinos se calculan con los predictores del entrenamiento de la predicción correspondiente; no se utilizan rendimientos para elegir vecinos. Las tres columnas originales tienen datos válidos en las 138 parcelas.

## Dos aplicaciones

**ATTENUATE:** un árbol aprende cuándo reducir la contribución J7−CT3. La predicción queda entre J7 y CT3; no permite aumentar el peso local ni extrapolar fuera de ambos. Los cortes se aprenden mediante regresión ponderada sobre la proporción objetivo (y−CT3)/(J7−CT3), con pesos (J7−CT3)². Las hojas se recalibran al óptimo cuadrático, con prior equivalente a 20 observaciones hacia no cambiar J7, y se acotan a [0,1]. Diferencias entre rutas menores a 1e−6 no definen cortes. Esto es un control de uso del experto, no una nueva regla regional.

**RESIDUAL:** árbol sobre y−J7, con predicciones de J7 cross-fitted. El ajuste de cada hoja se contrae mediante n/(n+20) y se limita a ±0.5 t/ha. Se añade a J7. No se usa el rendimiento de la parcela evaluada para calcular su residuo operativo.

Ambos modelos prueban profundidad {1,2}, mínimo de hoja {15,25}, amplitud {0.5,1}, más la opción nula de no ajustar. Los umbrales, estructura y amplitud se eligen exclusivamente mediante las particiones internas originales del entrenamiento externo. Los parámetros y límites no cambian al observar resultados.

## Anidamiento y soporte

Se mantienen las 65 particiones externas y las internas originales. Para entrenar los ajustes se generan nuevas predicciones J7 internas fuera de muestra: se recuperan los componentes congelados cuando existe exactamente el mismo conjunto de entrenamiento y se ajustan solo los contextos adicionales necesarios. El gate físico J7 conserva sus entradas y selección interna k={4,8}; CT3 y la corrección del experto se seleccionan dentro del entrenamiento correspondiente. Cada fila de calibración obtiene contrastes utilizando exactamente el entrenamiento de su predicción base.

La nueva capa requiere mayor profundidad de validación que la ejecución original. Si queda un solo grupo territorial, CT3 usa parámetros conservadores fijados previamente (alpha=1, l1_ratio=0.5); el experto es local sin corrector. Si un gate interno no dispone de OOF para calibrarse, utiliza CT3 en ese contexto. Estos respaldos se registran; nunca se usa validación aleatoria para sustituir un protocolo territorial. J7 y CT3 de evaluación externa permanecen exactamente como estaban: estos respaldos solo afectan a la calibración interna adicional.

## Evaluación

Reportar RMSE, MAE, R², sesgo, dispersión, error por estado/municipio/bloque/perfil, diferencias intraperfil y ganancias por parcela. Las métricas aleatorias se calculan sobre las 138 OOF completas de cada repetición y luego se promedian diez repeticiones. Recalcular sin 171/015 y omitiendo zonas completas sin reajustar modelos.

Comparaciones pareadas: cuatro alternativas frente a J7 en cuatro protocolos, dos vecindarios entre sí para cada uso y dos usos entre sí para cada vecindario: 32 contrastes, con ajuste Holm conjunto y bootstrap por grupos. No se crea una métrica promedio entre protocolos. No se selecciona externamente un ganador y se presenta como confirmación independiente.

Para incertidumbre se estudia descriptivamente si el máximo contraste absoluto se asocia con errores absolutos de J7: correlación de rangos, AUC para error>1 t/ha y error del quintil de mayor anomalía frente al resto. El quintil es diagnóstico descriptivo del conjunto evaluado, no un umbral operativo aprendido. No se construyen intervalos calibrados ni se afirma cobertura.

Se conservan modelos, reglas, parámetros seleccionados, predicciones, vecinos y respaldos. Sin entrenamiento final sobre 138 targets, PRED59, modificación del Champion, reglas para 171/015, nuevos screenings ni push. El origen de las señales en residuos ya examinados obliga a tratar toda esta etapa como exploratoria.

Scripts: 460 prepara y congela; 461 ejecuta; 462 evalúa y entrega. Fuente numérica congelada: `outputs/modeling/neighbor_signal_contrasts/v1/frozen_design.json`.

## Corrección de implementación antes de revisar resultados

Una prueba de soporte identificó que un municipio con una sola parcela deja cero predictores variables en el nivel más profundo. Se completó el respaldo CT3 con la media del entrenamiento, equivalente al ajuste de intercepto sin predictores y al comportamiento de CT3 original con compact4 constante. Se conservaron el código, diseño y hashes iniciales bajo `audit`, y se registró la modificación en `implementation_amendments`. No cambiaron señales, reglas, grillas, límites, particiones ni referencias externas. Se preservaron ocho checkpoints aleatorios completos, donde ese respaldo no se utiliza, y se aumentó únicamente la concurrencia de ejecución de cuatro a ocho procesos. Las siete pruebas pasaron tras la corrección. El script 463 verifica al final que las decisiones coincidan con los candidatos internos y que los ocho checkpoints conservados no hayan cambiado.

Una mejora frente a J7 no demostraría por sí sola que los contrastes son indispensables: no se incluyó un corrector global independiente con el mismo ajuste. Se distinguen las reglas con cortes de los árboles constantes; si apareciera una ganancia convincente, haría falta ese control para atribuirla específicamente al contraste vecinal. La etapa no se amplía automáticamente para perseguir resultados.

Se añadió un segundo caso del mismo respaldo: si un fold de calibración interna queda sin variables compact4 con variación, no se seleccionan hiperparámetros usando ese CV y se aplican los parámetros conservadores ya fijados. Se preservaron 48 checkpoints aleatorios sin cambios. Las fuentes, prueba de dos municipios con una observación cada uno y hashes anteriores se guardaron en `audit`; tampoco se modificaron grillas, reglas ni particiones para este caso.
