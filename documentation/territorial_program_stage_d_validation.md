# Etapa D — Protocolo prospectivo de validación independiente

Este documento congela el conjunto de hipótesis y procedimientos de referencia. Las cuotas de reclutamiento, presupuesto y margen económico final siguen pendientes de decisión de FIRA. Ningún candidato se entrenó sobre las 138 etiquetas completas durante D. No se adquirieron nuevas etiquetas.

## Estimandos y poblaciones

R_similar(M)=E[(Y−f_M(X))²] en parcelas nuevas de la misma campaña, municipios representados y condiciones productivas elegibles del universo original. V1 verifica perfiles conocidos mediante los vectores climáticos completos, no solo el nombre municipal. El estimando corresponde a la población de reclutamiento descrita; no a toda la cebada nacional.

R_newmun(M) usa municipios sin ninguna parcela etiquetada de entrenamiento, dentro de la región objetivo que FIRA delimite antes del reclutamiento. Unidad primaria: municipio; objetivo principal municipal con igual peso por municipio, secundario ponderado por parcelas. Clima coincidente no convierte un municipio en conocido.

R_newseason(M) usa una campaña agrícola futura completa, conservando las definiciones mensuales relativas al año de aplicación, fuentes y manejo del cultivo elegible. Una sola campaña mide esa campaña; generalizar entre campañas requiere varias campañas independientes. Reutilizar parcelas puede medir transferencia temporal, pero no independencia parcelaria: se debe reportar y agrupar por parcela además de campaña.

R_newprofile y R_newregion quedan como objetivos secundarios diferenciados: perfil nuevo = vector exacto de clima no observado; región nueva = unidades territoriales separadas elegidas por un marco geográfico previo, no a partir de residuos. Las probabilidades de inclusión y el marco objetivo deben quedar registrados para saber si la estimación es ponderada o corresponde solo a la muestra.

## Grupos de adquisición

| Grupo | Diseño operacional | Independencia y contraste |
|---|---|---|
| V1 | Parcelas adicionales en perfiles conocidos; distribuir esfuerzo entre varios perfiles repetidos, además de los dos grandes de Chignahuapan | IDs/geometrías nuevas; auditar solapamiento y duplicados; comparar nivel y diferencias intraperfil |
| V2 | Perfiles nuevos dentro de municipios representados | Verificar vector climático; no confundir igualdad por malla con parcelas repetidas; aislar perfil del cambio administrativo |
| V3 | Municipios no presentes en las 138 etiquetas; seleccionar municipios y luego parcelas probabilísticamente cuando sea viable | Ninguna etiqueta de esos municipios entra al ajuste; comparar C-T3 con F4-S1, H0M control |
| V4 | Regiones nuevas elegidas por geografía y covariables sin Y; incluir condiciones semejantes y diferentes a bloque3 | Selección territorial previa y separación registrada; comprobar si ganancias T1/T3 se repiten entre regiones |
| V5 | Nueva campaña; combinar municipios representados y nuevos en estratos separados | Predicciones bloqueadas antes de Y; separar contraste temporal de geográfico; panel repetido y parcelas nuevas identificados |

Prioridad si hay recursos limitados: auditoría de Y/superficie y fechas primero; V3 para la hipótesis municipal más prometedora y V5 para el vacío temporal. V1 es prioritario si el objetivo operativo es diferenciación local. V4 debe disponer de varias regiones, no de una única réplica del bloque3. V2 sirve para distinguir transferencia climática de administrativa. Evitar prometer cubrir todos los objetivos con una sola muestra conveniente.

Las 59 PRED existentes pueden constituir un subconjunto sellado de evaluación de la misma campaña solo si sus Y permanecieron totalmente inaccesibles y no se modificó su selección a partir de resultados. No equivalen automáticamente a municipios nuevos ni a una campaña nueva; sus X ya participaron en auditorías descriptivas. Registrar esa limitación y su independencia de etiquetas.

## Candidatos y procedimientos que se preservan

- S1: Champion archivado como referencia; mezcla exactamente 0.5Champion+0.5F4-S1 como candidato; F4-S1 como control sencillo. No buscar pesos ni reconstruir protocolos geográficos del Champion.
- V2/V3/V4: F4-S1, C-T3, C-T1 y C-H0M, usando las mismas especificaciones y reglas internas de C. C-T0 no se considera un modelo distinto de F4-S1.
- Local: F4-E2 como control de dinámica, comparado con F4-S1; no promover B3. H1 y nuevas combinaciones quedan fuera del conjunto confirmatorio prioritario.
- F4-S1 = EN(lluvia mensual7 + NDVI mayo); T1 = EN(lluvia7 + SD mensualDTR); T3 = EN(total7, fracciónabril–junio, HHI mensual + NDVI mayo). Epsilon=1e−6mm. H0M usa las variables de S1, Ridge alpha_solver=n·alpha, intercepto libre y ratio0.
- Imputación mediana, medias/escalas entrenadas solo en entrenamiento; piso NDVI0.05 y tratamiento de constantes original. Mantener α={0.001,0.01,0.1,1}, ρ={0.1,0.5,0.9} EN; H0M α igual. Selección min mediaRMSE de folds internos, según fuentes congeladas; ningún Y externo entra en selección. Para el futuro ajuste final, la regla pendiente de concretar es reutilizar como CV interna las particiones aleatorias originales sobre138, sin adaptar protocolos según resultados externos. Debe aprobarse y sellarse antes de ajustar o ver Y nueva.
- Champion requiere confirmar que su entrenamiento final y fuentes están reproducibles con el procedimiento original. Si no puede producirse un artefacto final fiel sin modificar arquitectura/selección, omitir Champion y mezcla de esa validación, explicarlo y conservar los candidatos simples. No reconstruir retrospectivamente una nueva versión bajo el mismo ID.
- Calendario: NDVI mayo solo es una señal de mayo. Lluvia/DTR abril–octubre y dinámicaE2 requieren toda esa ventana. La evaluación principal es estimación poscampaña, no pronóstico anticipado. Si Y se conoce antes de completar X, mantener Y sellada hasta bloquear predicciones.

## Tamaño de muestra y precisión

No se fija un n óptimo. Antes de recolectar, decidir diferencia mínima útil Δ en pérdida cuadrática (t/ha)² y tolerancia MAE en t/ha con FIRA. El margen histórico0.01t/ha es una referencia de no deterioro exploratoria, no una diferencia clínica/económica validada. Puede traducirse una mejora objetivo δ_RMSE alrededor de referencia r en Δ=r²−(r−δ_RMSE)²; esta traducción no sustituye utilidad operativa.

Para D_i=SE_A−SE_B, positivo favorece B. Si unidades primarias independientes son municipios, construir D̄_g dentro de cada municipio y estimar D̄=G⁻¹ΣD̄_g. Error estándar descriptivo s(D̄_g)/√G; intervalos con grados G−1, cuando la aproximación sea defendible. Ponderaciones de población deben fijarse a partir del muestreo, no de desempeño. Con pocos municipios, presentar cada contraste municipal y reconocer incertidumbre alta; no usar 138 parcelas como tamaño inferencial territorial.

Planificar G para semiamplitud objetivo h explorando G≈(z·s_G/h)², reemplazando después z por t y revisando recursos. Para potencia aproximada puede explorarse ((z_conf+z_power)s_G/Δ)². Ambos son cálculos de sensibilidad, no tamaños garantizados: dependencia espacial entre municipios y pocas unidades pueden invalidar independencia. Incorporar variación de s_G, ICC e imbalance de tamaños y concentraciones; DEFF≈1+(m−1)ICC solo ilustra agrupamiento simple, no resuelve perfiles cruzados con municipios.

Usar un piloto verdaderamente externo o supuestos conservadores para rangos de s_G/ICC. Las pérdidas OOF reutilizadas actuales son un insumo exploratorio para rangos, no una estimación insesgada de varianza externa. Si el piloto se usa para diseñar y congelar procedimientos, separarlo de la muestra confirmatoria final. Para campañas la unidad de generalización es campaña; más parcelas de una sola campaña no reemplazan más campañas. Para diferencias locales, inferencia por perfil y parcelas, nunca por parejas solapadas.

## Bloqueo y evaluación

1. Registrar marco de muestreo, municipios/campañas, reglas de elegibilidad y IDs; deduplicar geometrías y documentar parcelas que reaparecen.
2. Aprobar cuotas, utilidad práctica, estimando principal y regla final de CV/ajuste pendientes. Sellar especificaciones, fuentes, código, modelos futuros y hashes antes de recibir Y nueva.
3. Ajustar candidatos usando exclusivamente138Y actuales en una operación futura separada. Producir predicciones externas, registrar soporte/faltantes y bloquearlas con fecha/hash.
4. Obtener rendimientos con definición uniforme producción/superficie cosechada y documentos verificables. Registrar pérdidas de seguimiento; no sustituir faltantes con valores predichos.
5. Evaluar cada comparación con llave (ID,campaña,modelo) y mismo conjunto de Y. Publicar n completo, n emparejado y razones de datos faltantes. No elegir candidatos por rendimiento externo.

Primaria V3: pérdida cuadrática pareada con igual peso municipal; acompañar RMSE/MAE parcela y municipal, sesgo y porcentaje de municipios con mejora. Primaria V1: MSE por parcela; secundaria diferencias intraperfil con igual peso de perfiles y pares del mismo modelo final. Primaria V5: MSE por campaña y detalle regional. Reportar intervalos adecuados a unidades objetivo, sin tratar campañas/repeticiones/parejas dependientes como independientes.

Decisión propuesta a concretar antes de Y: utilidad si la ganancia supera Δ y su incertidumbre respalda una mejora práctica, sin deterioro MAE mayor al margen acordado; si la incertidumbre cruza umbrales de utilidad o daño, declarar inconcluso. Reportar todos los contrastes predefinidos y designar uno principal por estimando; no seleccionar el menor p. No juntar escenarios mediante pesos retrospectivos.

Municipios con n<2: mantener en métricas parcelarias y municipal con su tamaño explícito; no estimar diferencias intraperfil allí. Si no hay varios perfiles o municipios, declarar no estimable el objetivo correspondiente. Comparaciones incompletas: tabla de disponibilidad y análisis sobre intersección etiquetada, con advertencia de posible selección por faltantes. No imputar Y.

Valores fuera de soporte permanecen en evaluación principal con bandera y análisis secundario predefinido. Faltantes de X: transformaciones congeladas; una fuente completamente ausente se registra como indisponibilidad operacional del modelo, sin diseñar un sustituto. No eliminar casos por residuo; una corrección documental de Y requiere evidencia independiente y bitácora ciega al modelo, reportando métricas original y corregida.

## Intervalos futuros

H1 no se promueve y sus intervalos actuales no se recalibran. Un futuro módulo de incertidumbre requiere rendimientos independientes de calibración, regiones/perfiles representados y otro conjunto de evaluación sellado. Investigar calibración por grupos o particiones territoriales, con supuestos y unidad de intercambio explícitos. Bootstrap ordinario parcelario y conformal estándar no garantizan cobertura bajo cambio de dominio. Si no hay intervalos congelados válidos para un candidato, no inventarlos ni reportar cobertura.
