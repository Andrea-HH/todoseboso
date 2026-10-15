# GeoC y fira_nuria: comparación e integración propuesta

Se realizó una auditoría de lectura de GeoC en `../fira/GeoC`, revisión fe056a759790e5e4cf5d1d62dec323851625b121. No se modificó ese repositorio ni se entrenó o mezcló ningún modelo. Script 413 y tablas en `outputs/research/geoc_bridge_audit/v1`.

## Compatibilidad comprobada

Las tablas canónicas coinciden en los 197 IDs, los 138 rendimientos, las 59 etiquetas ausentes, superficies y partición TRAIN/PRED. El archivo bajo `data/samples/` de GeoC solo contiene ocho ejemplos: no debe confundirse con la tabla canónica bajo `data/source/tabular/`.

Se alinearon las 59 predicciones finales de Local04D con nuestras tres salidas. Correlaciones Local04D/C-T3 .9530, Local04D/Champion .9550 y Local04D/EQUAL3 .9639. Diferencias absolutas medias .1687, .1676 y .1400 t/ha. Es desacuerdo entre pronósticos, no error observado o complementariedad de residuos.

## Los resultados actuales no forman un ranking común

GeoC prioriza reconstrucción transductiva de 59 objetivos fijos: X de las 197 parcelas puede intervenir en PCA y normalización sin usar y ocultos. Su Checkpoint08 reporta 16 splits de 97 TRAIN/41 pseudoobjetivos, 656 predicciones de 132 parcelas distintas. Local04D fijo RMSE pooled .481936; media de RMSE por split .477557. Su resumen de Checkpoint07 usa otro banco. Estos números no se comparan directamente con nuestro RMSE medio de diez OOF completas aleatorias, y menos con validación municipal o espacial.

Nuestro PCA/imputación de modelos inductivos ocurre en entrenamiento. La PCA X-only conjunta de GeoC no implica por sí sola contaminación con y: define otro esquema de información. Debe conservarse ese esquema al evaluar y distinguirlo de una sensibilidad inductiva. Además debe verificarse que las 2,082 variables C4 y su construcción no incorporen agregados supervisados de las etiquetas retenidas. Esta auditoría no certifica toda la procedencia de C4 ni las reglas de la competencia.

Checkpoint08 comparte aquí resúmenes agregados; los registros individuales y su membership de confirmación deben recuperarse de la ejecución original para reutilizar exactamente ese banco. El archivo de membership bajo checkpoint05 está vacío y no equivale al banco08. No inferir ni inventar particiones desde resúmenes. La documentación de 08 dice todavía preparado, mientras las tablas compartidas contienen resultados; priorizar manifiesto, memberships y predicciones de la ejecución efectiva.

## Dirección recomendada

Usar fira_nuria como sede de una comparación adicional, importando un paquete mínimo y versionado de Local04D. Conservar GeoC intacto y nuestro historial de evaluación. No copiar repositorios completos ni sustituir bibliotecas o archivos de ganadores.

El paquete requiere: código exacto del predictor; embedding C4 PCA20 de los 197 IDs; metadatos y coordenadas; normalización exacta de distancia geográfica y posterior escalado de scores PCA; configuración k24/alpha30/power1; manifiesto de fuentes y commit; OOF por parcela y memberships de los bancos07/08; 59 pronósticos canónicos solo para reproducción. Para auditar o ajustar una versión inductiva se necesita además la matriz C4, diccionario y pipeline de imputación/escalado/PCA, no solo los scores.

Importante: el código Ridge pondera con 1/(distancia+1e-6)^power. Cambiar unidades o normalización de distancias cambia los pesos y, por tanto, la regularización efectiva de alpha30. No reproducirlo con una implementación aproximada de vecinos. El predictor solo admite y de vecinos pertenecientes al entrenamiento del fold; deben excluirse TODOS los objetivos retenidos, no solo la propia parcela.

También conviene llevar nuestros predictores congelados y sus cuatro entradas al banco GeoC como adaptadores, sin reconstruir allí toda nuestra investigación. Así se contestan dos preguntas: rendimiento bajo nuestro protocolo de transferencia y rendimiento bajo su protocolo de reconstrucción de objetivos. La sede del código no cambia la validez; la identidad de datos, particiones, preprocessing y exclusiones sí.

## Batería propuesta, sin ejecutar

1. Reproducir Local04D contra sus resultados existentes y sus 59 predicciones, sin ajustar parámetros. Recuperar membership08 y OOF completas antes de atribuirle el RMSE compartido.
2. Comparar Local04D, C-T3 y EQUAL3 bajo los 65 folds originales, más Champion solo donde haya evaluación compatible. Si se desea Champion agrupado, requiere una reconstrucción anidada adicional; no utilizar su ajuste final ni sus OOF aleatorias como sustitutos. Separar Local04D transductivo y sensibilidad PCA entrenada en TRAIN si se ejecuta.
3. Evaluar C-T3 y EQUAL3 en las mismas máscaras97/41 de GeoC, con selección interna restringida a esos97. No aplicar modelos finales entrenados con138 para predecir pseudoobjetivos que ya vieron.
4. Con OOF alineadas por split/ID: errores correlacionados, signos opuestos, ganancias cuadráticas por parcela, perfiles, municipios y distancia a soporte. Preservar ambas agregaciones de RMSE y cobertura/frecuencia de evaluación; evitar que parcelas retenidas con más frecuencia reciban peso implícito sin declararlo.
5. Primer control de combinación: promedio fijo .5 C-T3 + .5 Local04D, fijado antes del entrenamiento, con ambos predictores entrenados sin los y externos. EQUAL3 + Local04D puede ser un segundo contraste definido previamente, no escogido por resultados territoriales.
6. Solo si el diagnóstico lo sostiene: C-T3 + lambda * Ridge local sobre residuos, k24/alpha30/power1 congelados y lambda en [0,.25,.5]. Cada residuo de entrenamiento se genera cross-fitted excluyendo también su etiqueta de la selección de C-T3. Selección de lambda exclusivamente dentro del entrenamiento externo; cero retorna C-T3. No añadir reglas municipales o búsqueda abierta.

Una mezcla de predicciones directas no equivale a un corrector residual. No entrenar un modelo para predecir los residuos OOF externos y evaluar sobre esas mismas observaciones. No usar desacuerdo entre los59 pronósticos como criterio de pesos ni los y ocultos para decisiones.

## Estadística y límites de nuestro repo

Mantener métricas sobre OOF completas por repetición y pares compartidos. Bootstrap por parcela de GeoC preserva repeticiones, pero no dependencia entre parcelas vecinas: agregar sensibilidad por perfiles y bloques. Usar comparaciones pareadas, omisiones de regiones y multiplicidad; no interpretar los 16 splits como16 muestras independientes. Un banco nuevo con las mismas138 etiquetas sigue sin ser confirmación en otra campaña.

Nuestros contrastes actuales no demostraron superioridad después de Holm. Tenemos solo cinco bloques espaciales y nueve municipios; la incertidumbre territorial es grande. Champion carece de OOF agrupadas exactas compatibles en la entrega actual. La consolidación final por hiperparámetros modales y targets residuales OOF se definió para entregar los59, no dispone de una nueva prueba independiente. Para certificarla como procedimiento de selección habría que reproducir esa consolidación dentro de cada entrenamiento externo o usar una campaña verdaderamente nueva. Este límite también afecta a cualquier integración final que se defina ahora.

Recomendación: empezar por controles de comparación y promedio fijo; no añadir otra batería grande de correctores o variables. La hipótesis nueva defendible es que Local04D capta estructura local de los errores de C-T3 que no captan nuestras ventanas climáticas. Tiene que probarse, no se deduce de sus RMSE publicados.
