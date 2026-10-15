# F4-E — Síntesis para decisiones

**La dimensión temporal LAI añade una mejora intraperfil pequeña; no mejora la predicción general.** Mantener lluvia + NDVI mayo como referencia sencilla. Considerar el inicio del mayor ascenso LAI únicamente como candidato de diferenciación local que merece validación independiente.

| Modelo | RMSE aleatorio | RMSE municipal | RMSE espacial | RMSE diferencias, igual peso por perfil, aleatorio |
|---|---:|---:|---:|---:|
| E1 lluvia + NDVI mayo | 0.50483 | 0.67110 | 0.73904 | 0.58920 |
| E2 añade inicio ascenso LAI | 0.50561 | 0.67500 | 0.73845 | 0.58335 |
| E3 añade relieve medio | 0.50740 | 0.68197 | 0.78146 | 0.59240 |
| E4 sustituye NDVI por LAI q10 | 0.51194 | 0.83558 | 0.95262 | 0.57991 |

**Estado frente a dinámica.** La correlación parcial del inicio LAI con diferencias de Y, después de controlar NDVI dentro del perfil, es −0.210 y −0.237 fuera de Chignahuapan. Al excluir perfiles por turno permanece entre −0.232 y −0.202. La mejora predictiva de E2 es pequeña, pero aparece con igual peso por perfil en los cuatro protocolos y también al excluir Chignahuapan. En aleatoria, el RMSE ponderado por parejas baja 0.77325→0.76724 y el MAE global apenas 0.36411→0.36368. Su signo es negativo en 94% de ajustes aleatorios. Es una dimensión temporal parcialmente distinta del estado NDVI, sin demostrar una fase fenológica real ni efecto causal.

**Estado frente a relieve.** La asociación parcial del relieve baja a +0.077 global intraperfil y +0.006 fuera de Chignahuapan. E3 no mejora la perspectiva local con igual peso por perfil en aleatoria, y empeora transferencia espacial en +0.0424 t/ha. Un coeficiente frecuentemente positivo no basta para justificar su incorporación. No añadir esta representación de relieve a E1.

**Redundancia entre índices.** NDVI q10, LAI q10 y FAPAR q10 muestran asociaciones parciales intraperfil pequeñas en el conjunto completo: −0.008, −0.026 y +0.024. Hay diferencias al excluir Chignahuapan; no puede afirmarse redundancia perfecta en todas las regiones. EVI mayo conserva una asociación parcial negativa (−0.173), pero no se entrenó una sensibilidad para convertir ese diagnóstico en búsqueda de un ganador. E4 mejora algunas métricas locales con igual peso, pero empeora la perspectiva ponderada por parejas frente a E1 y deteriora mucho municipios y espacio. LAI q10 no es una alternativa más estable para transferencia.

**Dentro frente a entre perfiles.** La evidencia más clara de E2 es local: mejora de diferencias entre parcelas del mismo clima, mismo modelo externo y después de controlar NDVI. Su RMSE general aumenta ligeramente. Los cambios de E2 en RMSE y MAE globales por protocolo permanecen dentro del margen descriptivo de 0.01 t/ha, pero eso no prueba equivalencia estadística. E4 ilustra que una mejora local de determinados perfiles puede coexistir con una transferencia regional pobre.

**Dependencia de Chignahuapan.** En aleatoria hay en promedio 208.4 parejas, 8.6 perfiles y 87.7 parcelas por repetición. Sin Chignahuapan quedan 21.3 parejas, 6.4 perfiles y 24.2 parcelas. El RMSE con igual peso fuera de ese municipio mejora E1→E2 de 0.50572 a 0.49992; no es exclusivamente un hallazgo de Chignahuapan. Esa muestra restante es pequeña y las parejas se solapan. E2 mejora MSE de diferencias en aproximadamente 76% de perfiles elegibles por repetición aleatoria y 70% fuera de Chignahuapan; son promedios de proporciones, no probabilidades independientes.

**Soporte y significado.** Los cinco índices tienen 31–43 fechas válidas únicas y siete meses válidos por parcela, con gaps máximos de hasta 28 días. Ninguna parcela incumple el umbral descriptivo de cuatro fechas/cuatro meses, pero eso no elimina sensibilidad a la distribución temporal. Al omitir un mes, el percentil 90 del cambio absoluto del inicio LAI es 15 días. Hay LAI negativos y no se estableció una escala física; el predictor representa la forma del índice suministrado. El relieve de DEM120m/vecindad360m no mide microtopografía fina. Las reservas de orientación en terrenos planos están en una auditoría secundaria, sin convertirlas en modelos nuevos.

**Complejidad y conjunto mínimo.** Para predicción general conservar lluvia + NDVI mayo. Para estudiar diferencias locales, añadir únicamente inicio LAI como candidato de una dimensión temporal, sin sumar índices de estado redundantes ni relieve medio. No se cambia el Champion ni se adopta automáticamente E2. No se entrenó una corrección residual adicional.

**Cuatro niveles de evidencia.** Las correlaciones parciales y descomposiciones son asociaciones descriptivas. E2 muestra complementariedad predictiva local modesta en estos folds. E3/E4 no muestran una mejora de transferencia frente a E1. Todo el módulo conserva sesgo de descubrimiento del screening retrospectivo: se necesitan nuevos rendimientos o geografías para confirmación independiente.

Se congelaron tres contrastes y se guardaron 195 modelos nuevos, cinco referencias/candidatos y 8,970 predicciones fuera de muestra. Los controles originales se recuperaron y reprodujeron en los 65 folds. Cinco pruebas automatizadas pasaron, incluidos replay de los 195 modelos, comparación exacta de controles, definiciones de características y métrica intraperfil. Ningún modelo ni resultado anterior se sobrescribió.
