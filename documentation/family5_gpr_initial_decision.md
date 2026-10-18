> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# F5 inicial — Síntesis para decisiones

**F5-01 aporta una mejora municipal y por perfil frente a C-T3, pero empeora la transferencia espacial. No se propone un nuevo líder.**

| index | experiment | protocol | RMSE | MAE | bias | n | n_repeats |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | C-T3 | climate_profile | 0.52060 | 0.39150 | 0.00459 | 138 | 1 |
| 1 | C-T3 | municipality | 0.58126 | 0.46033 | -0.02033 | 138 | 1 |
| 2 | C-T3 | random | 0.51158 | 0.37495 | 0.00053 | 138 | 10 |
| 3 | C-T3 | spatial | 0.67878 | 0.53061 | 0.19116 | 138 | 1 |
| 4 | F5-00-C | climate_profile | 0.51885 | 0.36909 | -0.01200 | 138 | 1 |
| 5 | F5-00-C | municipality | 0.55341 | 0.39887 | 0.04496 | 138 | 1 |
| 6 | F5-00-C | random | 0.51530 | 0.36354 | 0.00556 | 138 | 10 |
| 7 | F5-00-C | spatial | 0.79047 | 0.58996 | 0.27169 | 138 | 1 |
| 8 | F5-01 | climate_profile | 0.49976 | 0.36237 | 0.00221 | 138 | 1 |
| 9 | F5-01 | municipality | 0.54421 | 0.38894 | 0.02103 | 138 | 1 |
| 10 | F5-01 | random | 0.50401 | 0.36156 | -0.00027 | 138 | 10 |
| 11 | F5-01 | spatial | 0.73480 | 0.54194 | 0.28501 | 138 | 1 |

La RMSE municipal baja 0.581259→0.544208 t/ha, una mejora de 0.037051. También mejora aleatoria y por perfil. En espacio aumenta 0.678778→0.734797: excede el margen congelado 0.01 t/ha de deterioro.

NDVI mayo contribuye positivamente frente a F5-00-C en los cuatro RMSE globales. Su ganancia municipal adicional es menor que 0.01 t/ha, aunque las demás diferencias y los errores intraperfil permiten evaluar su papel con mayor detalle. No se concluye que NDVI solo sea suficiente ni que discrimine parcelas con vectores de entrada idénticos.

Su aporte local es desigual: en municipal, RMSE de diferencias con igual peso por perfil pasa de0.518899 en lluviaGP sola a0.538821 conNDVI; también supera0.520989 deC-T3. En aleatoria, F5-01 mejora frente aGPlluvia, pero empeora diferencias frente aC-T3. Una mejor predicción del nivel regional no garantiza mejor diferenciación parcelaria.

El costo espacial se concentra en el bloque3: allí F5-01 tiene sesgo+1.016142t/ha frente a+0.718204 deC-T3. Al omitirlo solo de la agregaciónOOF, F5-01 mejoraRMSE en0.039437t/ha. En municipal mejora3/5folds; omitir suscinco principales beneficiarios conserva una gananciaRMSE de0.022305t/ha. En aleatoria, omitir loscinco principales beneficiarios revierte la mejoraRMSE frente aC-T3: esa ganancia pequeña es más frágil.

La prueba principal municipal cumple el margen de ganancia; la guarda global de costo no cumple; 3/5 folds municipales mejoran RMSE. La aceptación conjunta es False. Una mejora agregada no demuestra beneficio para la mayoría de parcelas ni estabilidad entre todas las regiones.

**Recomendación:** conservar F5-01 como candidato exploratorio municipal y continuar únicamente mediante revisión de una sensibilidad acotada de representación/kernel que investigue el deterioro espacial. Posponer bloques históricos hasta entender ese límite. No ampliar automáticamente F5 ni modificar modelo TOP20/TOP15. La suavidad conjunta recibe apoyo parcial; su extrapolación espacial bajo media constante no ofrece una ventaja general. No se rechaza la representación compacta —el control C-T3 sigue siendo útil— ni todos los Gaussian Processes.

Intervalos90%: cobertura y amplitud por protocolo/perfil conocido/nuevo están en el reporte técnico. Son Gaussian plug-in, con parámetros estimados y ruido observado; no garantías de calibración bajo cambio de dominio. Las omisiones de bloques/casos reutilizan las mismas OOF, sin reentrenamiento.

Se ejecutaron únicamente F5-00-C y F5-01: 130 ajustes externos y 520 diagnósticos internos sobre las particiones originales. C-T3 se recuperó y reprodujo exactamente en sus 65 folds. No se ajustó un modelo final sobre138 ni se predijeron las59PRED. Las cifras son OOF completa por repetición y luego media de repeticiones; no media de RMSE por fold.


## Verificación final

Pasaron22pruebas matemáticas y de integración, incluido replay de los650modelos externos/internos y los65controles C-T3. Se verificaron5529archivos anteriores protegidos y hashes delcódigo de ajuste congelado. Los1950inicios deoptimización pertenecen exclusivamente a lasdosconfiguraciones autorizadas; todaslas650soluciones seleccionadas convergieron y lascovarianzas fueron positivas. No se ajustó unmodelo final con138Y ni se generaron59predicciones PRED. Los tiempos reales porfit y laaproximación de duración paralela están en `audit/execution_timing.json`. No se ejecutaronF5-02–06, F5-00-M u otrokernel.
