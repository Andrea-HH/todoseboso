# R1–R3: diseño congelado

Diseño guardado antes de la primera ejecución en `outputs/modeling/territorial_mixtures/v1/frozen_design.json`, con fuentes y archivos consumidos protegidos por SHA-256.

## Objetivo y controles

Evaluar mezclas globales, municipales y por características usando tres expertos globales: C-T3 Elastic Net, F5-01 GPR Matérn 3/2 y F7-00 CatBoost. Sus cuatro entradas son lluvia total abril–octubre, fracción abril–junio, concentración HHI y NDVI de mayo. Expertos externos y rendimientos se conservan sin modificación. Controles recuperados: C-T3, GPR, CatBoost, promedio fijo EQUAL3 y mezcla libre BLEND3.

## Modelos

**R1:** peso global no negativo, suma uno, penalizado hacia el promedio equiponderado. Candidatos de pesos: los 66 puntos del simplex con paso .1 más el promedio exacto. Objetivo de ajuste: MSE OOF + α × varianza del rendimiento de entrenamiento × distancia cuadrática de pesos al promedio. α: infinito (promedio fijo), 1, .1, .01, 0.

**R2:** misma mezcla global regularizada, más pesos municipales contraídos hacia ella. Los pesos locales minimizan MSE OOF; la mezcla local aplicada es `global + n/(n+s) × (local-global)`. s: infinito (sin adaptación), 150, 50, 15. Requiere al menos 15 parcelas y 2 perfiles climáticos en el municipio de entrenamiento. Municipio desconocido o sin soporte usa mezcla global. Clave Estado::Municipio para evitar ambigüedad. α y s se eligen conjuntamente dentro del entrenamiento; 20 configuraciones.

**R3:** árbol de asignación de pesos, optimizado por mejora directa de SSE de la predicción combinada, sin etiquetas de modelo ganador. Profundidad 0, 1 o 2; hojas mínimas 20 o 35; al menos 2 perfiles por hija. Pesos de hojas contraídos hacia mezcla global con s=150 o 50. Cortes candidatos: cuantiles .2/.4/.6/.8 de cada predictor, calculados en el nodo de entrenamiento. Cada división debe reducir SSE más de 1e−10. Profundidad cero es el control global. α y arquitectura se seleccionan conjuntamente: 45 configuraciones. Solo usa compact3 y NDVI de mayo, con transformación de entrenamiento. Predictores fuera de algún rango marginal del entrenamiento usan la mezcla global. No usa nombres municipales, estado, coordenadas o altitud.

## Validación anidada

1. Mantener 65 particiones externas y sus cuatro particiones internas originales.
2. Dentro de cada entrenamiento interno, generar predicciones profundas excluyendo la etiqueta que cada experto predice. Elastic Net profundo ya está tuneado honestamente en caché. GPR profundo conserva sus límites y dos reinicios originales; CatBoost profundo retunea sus ocho candidatos en validación todavía más interna del mismo protocolo.
3. Ajustar cada candidato de mezclador con esas predicciones profundas y etiquetas de entrenamiento interno. Evaluarlo en el fold interno retenido usando los expertos internos ajustados sin sus etiquetas.
4. Seleccionar por RMSE sobre las OOF internas completas. Empates redondeados a diez decimales favorecen el primer candidato: mayor regularización, sin adaptación territorial y menor profundidad/hojas mayores.
5. Ajustar el mezclador seleccionado sobre las OOF internas honestas del entrenamiento externo y aplicarlo a los expertos externos globales archivados. No reajustar esos expertos.

No reutilizar una regularización global elegida con todos los folds internos para después aparentar validación independiente de R2/R3: cada candidato incorpora su α y se valida completo.

## Diagnósticos y decisión

RMSE, MAE, sesgo sobre OOF completas por repetición y media de diez repeticiones aleatorias. Comparaciones pareadas contra C-T3, EQUAL3 y R1; errores por municipio/bloque/estado, ganancias por parcela, omisión de municipios/bloques sin reajuste, errores intraperfil con ponderación por pares y perfiles. Pesos, reglas, soporte y frecuencia de fallback se reportan explícitamente.

El control global de R2/R3 con sus propios pesos permite distinguir el efecto de adaptar reglas del efecto de seleccionar otra mezcla global. Es diagnóstico del modelo ya ajustado, sin nueva selección o entrenamiento.

Criterios prácticos exploratorios: ganancia de al menos .01 en algún protocolo agrupado, sin daño de RMSE/MAE superior a .01 respecto a C-T3 o EQUAL3; daño de sesgo geográfico absoluto hasta .02; daño espacial al omitir bloques hasta .01; revisar daño intraperfil en ambas ponderaciones. No son pruebas de significancia. No elegir reglas retrospectivas por observar resultados externos.

## Límites

Sin corrección aditiva, intercepto, variables nuevas, reglas especiales para municipios particulares, modelos finales de 138 etiquetas, 59 PRED o promoción de Champion. Validación municipal de R2 mide su fallback cuando el municipio es desconocido: no confirma una corrección local en ese municipio.

Coste congelado: 914 contextos nuevos profundos, 914 ajustes GPR y 29,858 ajustes CatBoost incluidos los candidatos y reajustes. C-T3 se reutiliza íntegramente. Modelos y datos anteriores se conservan.

Las OOF ya se han explorado repetidamente; los resultados serán exploratorios y requerirán datos independientes para confirmar transferencia. Intervalos de mezcla no se ofrecen sin calibración adicional.
