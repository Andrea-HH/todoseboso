# Etapa B — Resumen de decisiones

**El objetivo intraperfil no justifica sustituir el entrenamiento convencional.** B1 no mejora las diferencias equilibradas; B3 logra una mejora pequeña aleatoria/por perfil, pero el costo municipal es demasiado grande. Mantener B0/B2 como referencias.

| Modelo | RMSE aleatorio | RMSE por perfil | RMSE municipal | RMSE espacial | RMSE diferencias equilibrado aleatorio |
|---|---:|---:|---:|---:|---:|
| B0 lluvia + NDVI mayo convencional | 0.50483 | 0.52626 | 0.67110 | 0.73904 | 0.58920 |
| B1 mismos predictores, objetivo/selección intraperfil | 0.50924 | 0.53747 | 0.86245 | 0.72967 | 0.59035 |
| B2 añade inicio LAI, convencional | 0.50561 | 0.53333 | 0.67500 | 0.73845 | 0.58335 |
| B3 mismos predictores de B2, objetivo/selección intraperfil | 0.51244 | 0.54364 | 0.86500 | 0.72267 | 0.58116 |

La mejora local de B3 persiste ligeramente fuera de Chignahuapan —0.49992→0.49802 en aleatoria— y por perfil —0.46906→0.46650—, pero no en municipios o espacio. No basta para declarar superioridad general ni para afirmar que el objetivo global era la causa principal de los errores.

**La selección interna forma parte del resultado.** En B1 municipal, lambda=0 en los cinco folds, pese a un RMSE externo mayor. La selección de regularización orientada a diferencias cambió alpha/rho dentro de restricciones internas y perjudicó transferencia. Ese deterioro no lo causa una penalización local activa. B3 también desactiva lambda en cuatro de cinco folds municipales. La estabilidad lambda0 es64%en B1 aleatorio y38%en B3. No se alteraron reglas después de ver los resultados.

**Decisiones independientes:**

- B1: descartar complejidad adicional bajo este procedimiento congelado.
- B3: conservar exclusivamente para investigación local; su mejora es marginal y deteriora transferencia municipal.
- Mezcla fija50/50: conservar como candidata exploratoria aleatoria, con reservas de extremos e influencia; no promoverla como Champion ni afirmar desempeño geográfico.
- Etapa C: puede estudiar agrupación parcial como otra hipótesis, con control compacto y tratamiento explícito de perfiles nuevos. B no proporciona una ganancia integral que la haga obligatoria; C/D no se ejecutaron.

**Mezcla fija, evaluada por separado:**

| Modelo | RMSE aleatorio | MAE aleatorio |
|---|---:|---:|
| Champion archivado | 0.498127 | 0.358869 |
| F4-S1 | 0.504834 | 0.364105 |
| Media50/50 | 0.493604 | 0.353426 |

La identidad MSE_mix=0.25MSE_A+0.25MSE_B+0.5mean(e_Ae_B) se verificó por repetición. La correlación de errores media es0.9382, pero el término cruzado utiliza producto medio, incluyendo sesgo. De la reducción de MSE, aproximadamente96.6%proviene de reducción de variación de errores y3.4%del cambio de sesgo cuadrático por repetición. No se aprendieron pesos ni se probaron otras mezclas.

La mezcla mejora MAE medio en77de138parcelas y MSE en80. Nueve de diez repeticiones mejoranRMSE; las repeticiones no son independientes. En diferencias locales equilibradas baja0.59729→0.58787 frente al Champion y0.58920→0.58787 frente aF4-S1. Dentro de Chignahuapan apenas empata F4-S1, mientras fuera mejora modestamente.

La ganancia no es uniforme: Q4 empeora RMSE0.45644→0.46728 y MAE0.38936→0.39797 frente aChampion. Q1 mejora apenasRMSE0.68966→0.68796, pero empeoraMAE0.44607→0.45545. En Chignahuapan mejoraRMSE0.56112→0.55366; fuera0.42111→0.42065, prácticamente empate.

**Influencia:** la parcela con mayor ganancia explica49.7%de la ganancia neta deSSE, y las cinco mayores explican163.7%, porque otras deterioran. Al excluir esas cinco beneficiarias, la ventaja neta se revierte. Excluir las parcelas de mayor error inicial Champion no elimina necesariamente la mejora. Son sensibilidades descriptivas seleccionadas después de observar pérdidas; no reglas de activación ni confirmación. La ganancia es pequeña y depende de compensaciones entre casos.

**Matemática e integridad:** la pérdida se implementó con residuos centrados y filas aumentadas, sin optimizar con parejas expandidas. alpha_joint=2·alpha_archivado, alpha_solver=alpha_archivado·n/m; intercepto libre. Lambda0 reprodujo130controles con diferencia máxima0.0t/ha. El solver conserva tol1e-4 original; máximo residuoKKT externo8.93e-5 y máximo gapdual deJ2.33e-4. Todos los ajustes cumplieron la parada declarada. La identidad/gradiente/solución de referencia y reproducción completa se probaron automatizadamente.

Se ejecutaron únicamenteB1/B3 y controles de implementación, con los65folds congelados y los predictores permitidos. Se reutilizaronB0/B2 y1,380predicciones compatibles deChampion/F4-S1 para la mezcla. Hay7,176prediccionesB0–B3 y4,140registrosdecomparación demezcla. Pasaron24pruebas matemáticas/deintegración. No se integraron capas territoriales, ni se modificaronChampion,EtapaA,Familia4/F4-Eoetiquetas. Las59PREDseconservaronsinYutilizado. Todo permanece exploratorio por reutilización de las mismas138etiquetas.
