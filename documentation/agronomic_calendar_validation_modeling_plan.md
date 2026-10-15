# Validación del set y planteamiento de modelos: 2025 como núcleo

Validación ejecutada el14 de octubre2026. Alcance: datos y comparación temporal, no evaluación predictiva de nuevos modelos. No se leyeron targets, no se hicieron fits ni inferencias PRED. Se mantuvieron sellados los modelos anteriores.

## Validación ejecutada

Pasaron180 comprobaciones: reconstrucción independiente desde el panel mensual de las32 variables de ventana y comprobación de CURRENT, HIST_MEAN, HIST_SD y DELTA para las37 variables. Pasaron controles de dominios: NDVI de ventanas en[-1,1], precipitación/rango/desviación espacial no negativos. Las tres pruebas unitarias del constructor también pasaron. La validación de calendario no demuestra fechas fenológicas reales, precisión de sensores ni que una parcela tuviera cebada en cada año histórico.

Las37 variables2025 están completas en TRAIN. El histórico incompleto permaneceNaN: ciertos resúmenes exigen tres años y tienen hasta21% de faltantes. Para contrastar años se utiliza una cohorte de parcelas con cuatro valores válidos por variable; el denominador se reporta. No se comparan medias con una composición cambiante de parcelas.

## Qué distingue a2025

Cambios pareados contra la media2022–2024; las cifras son medianas de diferencias por parcela, no diferencias entre dos medianas independientes:

|Variable|TRAIN con cuatro años|Cambio2025|Fuera del rango2022–2024|
|---|---:|---:|---:|
|Lluvia mayo–junio|138|+217.55mm|100%, por encima|
|Tmax mayo–junio|138|−1.62°C|100%, por debajo|
|NDVI mayo–junio|138|+0.0099|37.7%|
|NDVI julio–agosto|136|+0.0688|66.9%|
|NDVI septiembre–octubre|111|+0.1182|49.5%|

El contraste climático2025 se observa en los tres estados. Las138 parcelas no son138 realizaciones climáticas independientes. El cambio de lluvia mayo–junio con igual peso por perfil es+256.45mm y el de Tmax−1.71°C; ponderar por perfiles confirma dirección, no produce una prueba de significancia ni elimina dependencia espacial entre perfiles.

El NDVI posterior tiene patrón regional: cambio mediano julio–agosto Hidalgo+0.1674 (n36), Puebla+0.0237(n69), Tlaxcala−0.0353(n31). Por tanto, no hay aumento uniforme de verdor. En septiembre–octubre los cambios son Hidalgo+0.0698(n29), Puebla+0.1528(n51), Tlaxcala+0.1353(n31).

La sensibilidad con al menos dos observaciones válidas por mes en cada uno de los cuatro años conserva dirección: NDVI mayo–junio+0.0098(n137), julio–agosto+0.0716(n123), septiembre–octubre+0.0966(n42). La reducción tardía de muestra es importante: no demuestra ausencia de sesgo por nubes ni generaliza al subconjunto excluido. En esta revisión no se cuantificó la causa del cambio ni se corrigió por cultivo histórico o procesamiento.

2024 también es singular: Tmax mayo–junio tiene mediana27.76°C frente a24.43°C en2025,25.16°C en2022 y25.58°C en2023 (las138 parcelas). Las medianas de NDVI tardío2024 y2025 son similares en la cohorte anual disponible; la tabla leave-one-year-out con la misma cohorte por variable muestra cambios respecto a los otros tres años de+0.1135 y+0.1182. El año2023 tiene−0.2023. Parte del contraste contra el promedio histórico proviene de2023 y no de una condición exclusiva de2025.

**Salir del rango de tres antecedentes no es una rareza estadística:** bajo cuatro observaciones continuas intercambiables, la cuarta queda fuera del rango de las otras tres con probabilidad50%. No se asignan p-valores, periodos de retorno ni etiquetas climáticas extremas a estos porcentajes. La tabla que trata cada año como focal es descriptiva; cuando2025 aparece como referencia de2024 no constituye un pronóstico histórico ni entra en los predictores2025.

## Qué debe aprender el modelo

El target disponible es2025. Hay138 etiquetas, no552 etiquetas anuales. No repetir Y2025 para entrenar como si hubiese rendimientos2022–2024. El nivel absoluto de2025 es el bloque principal; historia describe el contexto de cada parcela y su desviación. Una subida común a todas las parcelas puede desplazar el intercepto pero no explicar por sí sola diferencias entre parcelas2025. Necesitamos amplitud y forma del cambio entre parcelas, especialmente dentro de perfil climático y municipio.

No se puede evaluar transferencia entre años sin rendimientos observados de otros años. La evaluación temporal realizada es de X; las65 particiones originales evalúan generalización entre parcelas y territorios dentro del target2025.

## Batería propuesta, aún sin ejecutar

Conservar C-T3 y sus OOF como referencia. Antes de entrenar, fijar las siguientes comparaciones, separando representación de arquitectura:

1. **Clima2025 afinado:** cuatro acumulados de lluvia y cuatro Tmax de ventanas, más NDVI de mayo original. ElasticNet conservador con selección interna acotada. Comparar contra C-T3 para comprobar si el calendario mejora sobrecompact3. Tmin queda como sensibilidad posterior, por evidencia previa de redundancia territorial; no screening de todas las variables.
2. **Sentinel2025 afinado:** mantener C-T3 y añadir los cuatro niveles NDVI de ventanas y la heterogeneidad NDVI de julio–agosto. No incluir simultáneamente niveles y todos los cambios algebraicamente derivados. Así se pregunta si trayectoria y heterogeneidad añaden señal al NDVI de mayo original.
3. **Complementariedad actual:** combinar el bloque climático afinado y ese bloque Sentinel2025 bajo la misma regularización y particiones. No presuponer que mejoras individuales se suman.
4. **Contexto histórico sobre2025:** añadir medias y SD2022–2024 de esas mismas cinco variables Sentinel, sin añadir automáticamente todo el inventario. El histórico recibe penalización igual o mayor que2025. Propuesta fija de factor de bloque gamma={0.25,0.5,1}, seleccionado solo internamente; tras escalar por entrenamiento, multiplicar histórico por gamma equivale en Ridge a penalización histórica proporcional a1/gamma². No imponer pesos80/20 sobre características sin significado comparable. Una penalización adicional de historia no garantiza a priori dominancia predictiva2025: se comprobará mediante ablación y estabilidad.
5. **Sensibilidad de desviaciones:** usar niveles2025 más desviaciones2025−historia en lugar de medias históricas, conservando SD histórica. No meter CURRENT+MEAN+DELTA simultáneamente porque CURRENT=MEAN+DELTA. En regresión lineal, nivel+historia y nivel+delta son reparametrizaciones del mismo espacio; sus diferencias con regularización no prueban información nueva. Una SD usada para normalizar anomalías con solo tres años es inestable y no se propone inicialmente.

No seleccionar entre las salidas externas la variante ganadora y describirla como confirmación independiente. La primera batería identifica representación. Si se quiere contrastar no linealidad, fijar antes de entrenar el mismo CatBoost conservador para las representaciones, con algoritmo e hiperparámetros seleccionados internamente; evitar seleccionar la arquitectura por el bloque espacial3. Mantener límites acotados y no abrir otra búsqueda de kernels/modelos residuales.

La comparación entre entradas climáticas8 ycompact3 no aísla solo calendario: también introduce Tmax. Deben recuperarse como controles las OOF compatibles de H6/lluvia+Tmax o definirse una ablación con y sin Tmax dentro de la misma representación. No atribuir a fechas un cambio que provenga de añadir temperatura.

## Cómo leer los resultados futuros

- Reutilizar65folds y particiones internas originales. Imputación, indicadores de ausencia, escalado, regularización y elección de bloques exclusivamente dentro de entrenamiento. La ausencia histórica puede estar territorialmente estructurada; reportar ablación de indicadores de ausencia.
- RMSE,MAE,sesgo yR² sobre OOF completas por repetición; comparaciones pareadas. No promediar métricas porfold como si fueran métricas OOF globales.
- Separar aleatoria, perfil, municipio y espacial. Reportar omisión de cada región/bloque sin reajustar, concentración de mejoras y sensibilidad a espacial3.
- Comparar errores e información incremental dentro de perfil y estado. No basta con que una nueva variable distinga X o identifique la región.
- Analizar asociación de ganancias con desviaciones2025 usando OOF, con soporte y carácter exploratorio; no crear reglas regionales a partir de los errores externos.
- Ablación2025solo frente a2025+historia responde si historia ayuda. Una historia variable o una anomalía grande no demuestra utilidad por sí misma.

## Archivos

`outputs/research/agronomic_calendar_validation/v1/`: `summary.json`, `reconstruction_checks.csv`, `domain_checks.csv`, `annual_shift_2025.csv`, `annual_shift_by_state.csv`, `leave_one_year_out_descriptive.csv`, `anomaly_intraprofile_support.csv`, `annual_context.png`.

Scripts392 y393. No Champion modificado, no entrenamiento final138 ni predicciones de las59 parcelas.
