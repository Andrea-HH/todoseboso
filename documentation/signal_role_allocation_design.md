# Composición SMALL12 y asignación de funciones: diseño previo

Pregunta: qué señales pueden retirarse del experto reducido con menor pérdida predictiva y cuáles recuperan utilidad como correctores o como entradas de los pesos. «Información» se refiere a rendimiento fuera de muestra e intraperfil, no a porcentaje de varianza X del PCA ni a causalidad. Todo es exploratorio sobre etiquetas/folds ya utilizados.

Se preservan C-T3, Champion, GeoC y las ejecuciones anteriores. Nueva salida: `outputs/modeling/signal_role_allocation/v1`. No entrenamiento final138 ni nuevas59PRED. Se reutilizan las65 particiones externas e internas originales y cachés compatibles en lectura; no se buscan variables nuevas.

## Representación y controles

Para aislar funciones se fija el experto en originales estandarizadas (sin PCA). Ridge local24 vecinos, alfa30, pesos geográficos originales. El control BASE12_BOTH es SMALL12 original + corrector compacto + gate físico BOTH. No es idéntico al selector de representación anterior; ese resultado previo se recupera como referencia separada. Se verifica igualdad exacta de las predicciones del experto FULL12 con `B_SMALL12_raw_COMPACT` anterior. La coordenada se usa únicamente para vecinos, nunca como nueva regla de corrección.

El corrector del experto conserva el mismo grid12 de Elastic Net (alfa .001/.01/.1/1; l1_ratio .1/.5/.9) y amplitudes0/.25/.5. Se mantienen los tratamientos originales del núcleo compacto, incluido el piso de escala NDVI. Toda imputación/codificación/escalado se ajusta en el entrenamiento aplicable. Al mover señales al corrector se reajusta conjuntamente el EN sobre compact4 + bloque trasladado; se corrigen residuos OOF del local reducido. No se usan residuos externos, del Champion ni de una mezcla ajustada sobre todos los casos.

Se distinguen los cinco grupos SMALL12: vigor histórico2; proxy de agua histórico2; dinámica2025 cuatro; SoilGrids3; pendiente1. Ningún grupo se decide por los resultados de esta ejecución.

## 28 rutas fijadas

1. BASE12_BOTH y BASE12 con gate global:2.
2. Media de vecinos sin características + corrector compacto, con gate BOTH o global:2.
3. Gates solo textura/fase, solo proporciones geológicas, solo distancias y retirada de cada uno de esos tres bloques:6. Se conserva el experto FULL12.
4. Retirada de cada grupo SMALL12 del experto, conservando gate BOTH y corrector compact4:5.
5. Cada grupo retirado vuelve únicamente en el corrector del experto:5; contraste primario con su retirada correspondiente.
6. Cada grupo retirado vuelve únicamente en el gate, añadido a BOTH:5; contraste primario con su retirada correspondiente.
7. Movimiento inverso de cada bloque físico desde el gate al corrector del experto:3; contraste primario con el gate sin ese bloque. Se conservan las12 del local. No se trata textura/fase como números ordinales.

El gate conserva K4/8, pesos convexos aprendidos y contracción20. El global no usa K. La geometría física reproduce la anterior: categorías centradas sin inflar raras, raíces de proporciones, log-distancias y normalización por bloque. Un grupo satelital añadido al gate se estandariza en entrenamiento y se normaliza por norma RMS como un bloque adicional, con balance fijo entre bloques. Los bloques físicos trasladados al EN conservan esa representación; no se añade un screening ni una búsqueda de kernels o árboles.

## Dos pipelines de selección completamente interna

Además de reportar las rutas fijas, se evalúan SELECT_MIN_RMSE y SELECT_COMPACT_001. Ambos eligen conjuntamente ruta y K usando OOF internas de los expertos completos retuneados. El segundo admite candidatos a≤0.01t/ha del menor RMSE interno y prefiere menor número de campos originales distintos; después menor RMSE y orden congelado. La tolerancia es una decisión de parsimonia fijada antes del entrenamiento, no un margen de equivalencia estadística ni una garantía sobre el error externo. No usa resultados externos para elegir ruta o tamaño.

Los modelos pequeños y gates necesitan las coordenadas para vecindarios. El conteo incluye cuatro compactas y dos coordenadas más la unión de entradas del local/corrector/gate, sin duplicar un campo movido entre funciones. Las variables categóricas pueden producir varias columnas codificadas. Los30 pipelines nuevos se comparan con referencias y contrastes primarios explícitos en el diseño JSON.

## Anidamiento y auditoría

El entrenamiento externo tiene OOF completas de cada experto para entrenar el gate. Para decidir K o ruta, cada entrenamiento interno A_j dispone de sus propias OOF completas del experto y C-T3; el experto que predice D_k se retunea únicamente con A_j menos D_k. Los targets de corrección del local se generan por cross-fitting dentro del entrenamiento correspondiente. Se preserva el fallback anterior cuando faltan grupos o parcelas para anidar: usar solo base local; nunca cambiar a CV aleatoria. Se registran los contextos y el posible desajuste por tamaño entre niveles.

Pruebas previas: bloque movido ausente del local y presente en el corrector; invariancia del experto retuneado frente a etiquetas externas; identidad de geometría física previa; categorías nuevas y preparación solo en entrenamiento. Posteriormente se reproducen todas las predicciones desde modelos guardados y se comprueban ledgers, igualdad de referencias y hashes protegidos. Cachés previas se recuperan por posiciones/CV exactas y targets de entrenamiento idénticos; no se escriben.

## Análisis y decisión

RMSE, MAE, sesgo y R² sobre OOF completas por repetición (aleatoria media10); contrastes emparejados con bootstrap5000 por conglomerados y signos de diferencias cuadráticas, Holm sobre30×4 contrastes primarios. Intervalos exploratorios de OOF fijas, sin corregir toda búsqueda histórica o incertidumbre de reajuste. No declarar superioridad por un bloque aislado ni equivalencia por falta de significación.

Se reportan recuperación al reasignar cada grupo frente a su retirada y pérdida total frente a BASE12_BOTH, cambios por parcela, correlación/discrepancia de predicciones, errores por región, omisiones sin reajuste e intraperfil con dos ponderaciones. Se explicita qué campos sobreviven y en qué función. Una mejora relativa a un modelo mutilado no implica superar al completo. Los selectores internos son pipelines evaluados, no una licencia para escoger retrospectivamente el mejor resultado externo. No se promueve un champion automáticamente.
