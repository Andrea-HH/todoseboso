# Correcci?n residual condicional sobre C-T3: dise?o aplicado

Esta investigaci?n es independiente de F8. Se autorizaron las correcciones al prompt y la ejecuci?n; no se modifica el Champion ni se entrenan modelos finales o las 59 predicciones PRED.

## Modelos y preguntas

| Serie | Corrector | Entradas | Pregunta |
|---|---|---|---|
| M0 | Ninguno | C-T3 original | Referencia exacta |
| M1_LAI | Ridge centrado | Inicio del ascenso LAI | Se?al residual lineal de LAI |
| M1_Z | Ridge centrado | LAI, fracci?n temprana, HHI, NDVI mayo | Control lineal con informaci?n id?ntica a M2 |
| M2_Z | CART centrado | Las mismas cuatro entradas | Partici?n no lineal condicional |
| C_CONTEXT | CART centrado | Fracci?n temprana, HHI, NDVI mayo | Recalibraci?n sin LAI |

M1_Z y M2_Z permiten comparar arquitectura. M2_Z frente a C_CONTEXT investiga aporte de LAI. Ninguna comparaci?n demuestra por s? sola interacci?n frente a funciones aditivas: no se ejecuta un control aditivo ni un CART LAI-only. H3 conserva car?cter exploratorio. No se incorporan historia, pendiente, suelo, SAVI, coordenadas o identificadores como predictores.

## Grids y tratamiento

Ridge: alpha normalizado 1, 0.1 y 0.01; el solver recibe n_train ? alpha, con predictores centrados/escalados, sin intercepto. CART: profundidad m?xima 1 o 2, min_samples_leaf 25 o 15, ccp_alpha 0, random_state 2026. Se conserva un ?rbol ra?z cuando no puede dividirse. Centrar su predicci?n de entrenamiento convierte una correcci?n constante en cero. Soporte de perfiles/municipios por hoja es diagn?stico, no un filtro aprendido mirando validaci?n.

Amplitud: 0, 0.25 o 0.5. Se selecciona sobre RMSE de OOF internas completas; empates a diez decimales favorecen amplitud menor, luego profundidad menor/hojas mayores o penalizaci?n Ridge mayor. ?=0 retorna exactamente C-T3. No se aprende un intercepto corrector ni se ejecuta un control de desplazamiento constante.

Se mantiene la transformaci?n ConditionalFeatures original, incluidos mediana de entrenamiento, eliminaci?n de constantes y piso de escala NDVI 0.05. LAI se expresa en d?as desde el 1 de abril seg?n la trayectoria suministrada. No se llama fecha de siembra/emergencia, no se eliminan negativos ni se inventan m?scaras/interpolaciones.

## Anidamiento

Los 65 folds externos y sus cuatro particiones internas son originales. C-T3 conserva su grid de 12 combinaciones y selecci?n por media de RMSE de folds internos. Sus 65 modelos externos se recuperan y reproducen exactamente. Los par?metros del entrenamiento externo no se utilizan para generar sus residuos internos.

Para cada entrenamiento externo A, cada A_j genera una base retuneada solo con A_j y predice B_j. Para entrenar el corrector dentro de A_j, se realiza otro cross-fitting: bases sobre A_j menos D_k, con selecci?n interna solo all?, predicen D_k. Ninguna etiqueta D_k, B_j o externa E interviene en esa selecci?n. La selecci?n del corrector compara candidatos sobre B_j; una vez elegida, usa residuos cross-fitted de A y la base externa archivada. Cada residuo conserva IDs y contexto de exclusi?n.

Subparticiones profundas: KFold hasta cuatro con semilla 2026 en aleatoria; GroupKFold hasta cuatro en protocolos agrupados, sin sustituir por aleatoria. Un selector requiere al menos dos grupos. Las filas de ajuste de un fold de ese selector pueden pertenecer a un solo grupo; eso no equivale a seleccionar hiperpar?metros con un solo grupo. Constancia completa de la base tiene fallback expl?cito de media de entrenamiento; no se esperan estos casos seg?n la auditor?a previa.

Los contextos id?nticos por IDs ordenados, particiones, protocolo, grid y columnas se comparten entre los cuatro correctores. Se congelaron 1,218 contextos; el presupuesto m?ximo nuevo de base es 55,909 ajustes, recuperando los 65 modelos externos. Ning?n ajuste utiliza las 138 etiquetas completas.

## Evaluaci?n y l?mites

RMSE, MAE y sesgo se calculan sobre 138 OOF por repetici?n y luego se promedian las diez repeticiones aleatorias. No se reemplazan por promedios de RMSE de fold. Se eval?an diferencias intraperfil con parejas del mismo modelo externo, ambos pesos, Chignahuapan/resto y omisiones de perfiles dominantes. Las parejas y repeticiones son dependientes.

Omisiones de municipios, bloques y mayores beneficiarios recalculan m?tricas sin reajustar. Perturbaciones de fechas se aplican a modelos fijos y son diagn?sticas; no eligen par?metros. Las reglas se comparan entre entrenamientos existentes, sin refits adicionales.

El margen 0.01 t/ha es pr?ctico y exploratorio. Se exige considerar mejora absoluta o local bajo ambos pesos, sin da?o absoluto superior a ese margen en otros protocolos, estabilidad territorial e influencia. La correcci?n cero se informa por protocolo, sin un umbral arbitrario de frecuencia que reemplace esas m?tricas. No se presenta como confirmaci?n independiente una selecci?n basada en estas mismas OOF externas.

Se registra el desajuste crossfit/refit: los residuos pertenecen a bases entrenadas con menos datos que la base aplicada externamente. El centrado no elimina todo ese desajuste ni garantiza ausencia de sesgo regional.

## Trazabilidad

Configuraci?n congelada: outputs/modeling/ct3_residual_conditional/v1/frozen_design.json. C?digo: src/ct3_residual_conditional. Ejecuci?n: scripts/376_ct3_residual_conditional.py. Contextos, targets honestos, par?metros, modelos, OOF, hojas, reglas, errores y hashes se conservan dentro de esa versi?n.
