# Complementariedad exploratoria: C-T3 y EN_CAL02

Se alinearon las 1,794 predicciones OOF de cada base por parcela, protocolo, repeticion y fold. Se verificaron objetivos identicos y 138 parcelas unicas por protocolo/repeticion. No se entrenaron modelos ni se ajustaron ponderaciones. Script reproducible: `scripts/405_calendar_base_complementarity.py`; resultados: `outputs/research/calendar_base_complementarity/v1` (la ejecucion rechaza sobrescribir).

Las mezclas usan pesos fijos de EN_CAL02 de 0, .25, .50, .75 y 1; se reportan todas. El peso restante corresponde a C-T3. Es un diagnostico exploratorio posterior a observar ambas bases, sin confirmacion independiente. No seleccionar un peso con estas OOF y presentarlo como seleccionado internamente. Los resultados aleatorios promedian metricas de las diez OOF completas por repeticion; los demas protocolos usan sus OOF completas, nunca promedios de metricas de folds.

| Peso EN_CAL02 | RMSE aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| 0 (C-T3) | .511582 | .520604 | .581259 | .678778 |
| .25 | .503053 | .504797 | .618197 | .620036 |
| .50 | .497804 | .496431 | .676778 | .589391 |
| .75 | .495937 | .495883 | .751961 | .591229 |
| 1 (EN_CAL02) | .497490 | .503178 | .839296 | .625262 |

El promedio 50/50 tiene R2 .655406 aleatorio, .657348 por perfil, .363164 municipal y .517005 espacial. MAE .363195, .377698, .551257 y .445142, respectivamente. Correlacion entre errores de ambas bases: .947013 aleatoria, .890577 por perfil, .856636 municipal y .655968 espacial. En la espacial, EN_CAL02 reduce el error absoluto en 47.1% de las parcelas; ambas bases tienen errores de signo opuesto en 23.9%. La menor correlacion espacial permite compensacion, pero no asegura estabilidad territorial.

## Concentracion territorial

El promedio reduce RMSE espacial del bloque 3 de .909593 a .515984 y del bloque 5 de .360198 a .145843. Empeora el bloque 4 de .798996 a .941248; tambien empeora ligeramente 1 y 2. El bloque 3 incluye principalmente Calpulalpan; el 4, principalmente Singuilucan. No son particiones por estado.

Al excluir el bloque 3 del calculo, sin reajustar modelos, el promedio empeora frente a C-T3: .612335 vs .579793. La ganancia espacial agregada depende de ese bloque. En validacion municipal, el promedio empeora Chignahuapan de .580680 a .714960 y Singuilucan de .867689 a 1.073865, aunque mejora Almoloya y Calpulalpan.

## Conclusion y siguiente paso

Existe complementariedad descriptiva de errores, especialmente espacial, pero no una mezcla global con mejora equilibrada en los cuatro protocolos dentro de los pesos examinados. Ningun peso positivo examinado mejora la validacion municipal. No promover el promedio ni adoptar reglas regionales derivadas de estos resultados.

Si se continua, comparar una union de predictores con Elastic Net y/o una mezcla regularizada hacia C-T3, seleccionando exclusivamente dentro del entrenamiento externo. Requiere una nueva ejecucion anidada; no se ha realizado aqui. No extrapolar este diagnostico a la utilidad de correcciones satelitales. No se modificaron modelos anteriores ni se generaron predicciones PRED.

Las tablas incluyen RMSE, MAE, sesgo, R2, diagnosticos por estado/municipio/bloque/perfil, omisiones sin reajuste y las predicciones pareadas. El analisis por perfil contiene errores individuales agrupados, no una nueva prueba de diferencias intraperfil. No se afirma superioridad estadistica ni se tratan repeticiones o parcelas correlacionadas como muestras independientes.
