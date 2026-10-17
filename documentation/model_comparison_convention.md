# Convención de presentación de modelos

Preferencia del usuario: presentar RMSE y R² juntos por defecto, indicando protocolo y procedimiento de agregación. RMSE en t/ha, menor es mejor; R² mayor es mejor. MAE y sesgo quedan como diagnósticos complementarios.

Para un resumen del desempeño global entre parcelas representadas en esta muestra, usar RMSE y R² de OOF completas de validación aleatoria, calculados por repetición y después promediados entre las10 repeticiones. Identificarlo explícitamente como validación aleatoria OOF; no llamarlo error de las59PRED ni resultado independiente. No usar métricas del ajuste sobre las138 parcelas como prueba de capacidad predictiva.

Mantener separados perfil, municipal y espacial, cada uno con RMSE y R². La media de los cuatro protocolos no es una métrica global válida por defecto. Si el uso es transferencia a territorios no representados, priorizar municipal/espacial según el destino; no seleccionar únicamente por aleatoria. R² global no equivale a explicación dentro de cada estado o perfil.

Comparaciones siempre con los mismos casos, folds y agregación. Sobre un conjunto fijo, RMSE y R² derivan del mismo error cuadrático; no son dos pruebas independientes. Cuando se promedian repeticiones, no convertir el RMSE medio directamente a R²: recuperar ambas métricas por repetición.
