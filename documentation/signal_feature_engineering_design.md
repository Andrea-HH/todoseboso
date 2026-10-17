# Ingeniería de señales: diseño congelado

Etapa exploratoria motivada por residuos ya examinados. No constituye confirmación independiente. Se preservan CT3, J7, fuentes, 138 targets, 65 folds y sus particiones internas. No PRED59, ajuste final138, promoción de Champion, selección regional ni eliminación de observaciones.

Se prueban por separado tres hipótesis, cada una frente a sus componentes originales:

| Bloque | Control original | Representación derivada |
|---|---|---|
| H: historia propia | 18 entradas: CURRENT, media2022–2024 y SD muestral para NDVI/EVI/NDWI en mayo–junio y julio–agosto | 6 anomalías (CURRENT−media)/max(SD,.02), recortadas ±6; exigir los tres años históricos |
| T: evolución y heterogeneidad | 21 medianas mensuales abril–octubre: EVI, NDVI y brecha NDVI medio−mínimo calculada por adquisición | 6: cambio EVI temprano/tardío, brecha relativa media, cambio tardío−temprano, momento de máximo y persistencia |
| P: interacciones físicas | 4 padres: TPI, pendiente, anomalía propia NDWI julio–agosto y cambio EVI julio–agosto menos mayo–junio | Los cuatro padres más TPI negativo, TPI negativo×anomalía NDWI, TPI positivo×anomalía NDWI y pendiente×cambio EVI |

Los modelos P_ENG retienen sus padres: la comparación P_ENG vs P_RAW evalúa adiciones no lineales bajo la misma regularización. Interacciones construidas con escalas del entrenamiento, magnitudes recortadas ±6 antes de productos. TPI describe posición relativa; no demuestra inundación, humedal ni causalidad.

Brecha relativa = clip((NDVI medio−mínimo)/max(abs(NDVI medio),.1),0,5), usando medianas mensuales y meses mayo–octubre. Persistencia = media/máximo mensual (0 si toda brecha es cero), no proporción del área afectada. Momento = (mes del primer máximo−5)/5, ausente si toda brecha es cero. Diferencias de EVI se basan en medias de medianas mensuales mayo–junio, julio–agosto y septiembre–octubre. Resúmenes requieren los meses correspondientes; no interpolación ni acortamiento silencioso. T_RAW conserva abril como contexto adicional; no se atribuye una ventaja de T_RAW exclusivamente a la transformación, pues puede aprovechar información mensual descartada por los resúmenes. Las fechas son ventanas comunes, no fechas parcelarias de siembra/cosecha observadas.

Cada uno de los seis bloques se evalúa como corrector de CT3 y J7. Se añade SHIFT, un corrector sólo de intercepto, para distinguir información de las variables de una recalibración global: 14 recetas, 910 modelos externos. No se combina automáticamente H/T/P después de ver OOF; una combinación requerirá evidencia y diseño posterior. Los contrastes con pares físicos y nuevas señales entre sensores se posponen para no ampliar esta batería.

Correctores Elastic Net con intercepto, imputación por mediana y escalado del entrenamiento; sin indicadores de faltantes. Grilla original alpha={.001,.01,.1,1}, l1_ratio={.1,.5,.9}; amplitud={0,.25,.5}. Corrección EN recortada ±.5 t/ha antes de amplitud: ajuste desplegado máximo ±.25. SHIFT evalúa sólo amplitudes0/.25/.5. Empates: menor amplitud, mayor alpha, mayor l1_ratio. No se modifican límites después de resultados.

Para cada entrenamiento externo A se recupera la calibración CT3/J7 fuera de muestra exactamente congelada en neighbor_signal_linear. Para evaluar un candidato dentro de A se ajusta en A_j con residuos de predicciones base cross-fitted dentro de A_j, y se evalúa en su D_j excluido. Ningún target externo ni residuo OOF calculado globalmente entrena correctores. Se reutilizan componentes de base de cachés exactas y se conservan respaldos territoriales profundos ya documentados; no se sustituye un protocolo por aleatorio. Las referencias externas CT3/J7 se copian exactamente.

Evaluación RMSE, R², MAE, sesgo, dispersión, cuartiles, pares intraperfil, estados/municipios/bloques, omisiones sin reajuste, ganancias por parcela, y exclusión descriptiva de171/015 y del top10 J7 aleatorio previamente congelado. Métricas sobre138 OOF completas por repetición, luego promedio de diez aleatorias; nunca promedio de RMSE por fold ni combinación de protocolos. Comparaciones:14 recetas vs su base y6 comparaciones derivado vs original, cada una en4 protocolos (80 contrastes). Holm conjunto80, bootstrap5000 por conglomerados y prueba de signos agrupada; carácter exploratorio, pocos conglomerados territoriales, selección histórica y OOF fijas limitan la inferencia.

La historia de tres años puede reflejar cobertura/cultivo distintos, no rendimiento histórico de cebada. Sus SD no son climatología estable. Se registra soporte y colinealidad; se distinguen descriptores fuente, transformados y coeficientes activos. Los coeficientes y asociaciones con residuos no son efectos causales.
