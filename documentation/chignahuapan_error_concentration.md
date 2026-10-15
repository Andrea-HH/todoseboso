# Concentración del error en Chignahuapan

Diagnóstico posterior sobre F4-E1, lluvia mensual + NDVI mayo. Se reutilizan las predicciones y parejas del mismo modelo externo de F4-E, sin entrenar modelos ni modificar sus resultados. Chignahuapan tiene 71 de las 138 etiquetas (51.45%). Sus dos perfiles con muchas etiquetas tienen 33 y 29 parcelas, que generan 528 y 406 parejas posibles: 934. Otros nueve perfiles locales tienen una sola etiqueta cada uno y no generan parejas internas de Chignahuapan.

Las parejas se clasifican por ambos miembros: ambos en Chignahuapan, ambos fuera o mixta. No se atribuyen todas las parejas mixtas al municipio. En aleatoria se comparan solo miembros retenidos por el mismo modelo; se promedian métricas de repetición. Las parejas se solapan y una pareja puede aparecer en varias repeticiones.

| Diagnóstico aleatorio | Ambos en Chignahuapan | Ambos fuera | Mixta |
|---|---:|---:|---:|
| Parejas elegibles medias por repetición | 181.1 | 21.3 | 6.0 |
| Proporción de parejas | 86.91% | 10.21% | 2.88% |
| Proporción de suma de errores cuadrados | 92.54% | 4.92% | 2.55% |
| RMSE de diferencias t/ha | 0.7983 | 0.5308 | 0.5922 |
| MAE de diferencias t/ha | 0.5536 | 0.4144 | 0.3886 |
| RMSE diferencias, igual peso por perfil | 0.8013 | 0.5057 | 0.5954 |

El error por pareja de Chignahuapan es aproximadamente 50% mayor en RMSE y 34% mayor en MAE. Con igual peso por perfil el contraste persiste. La concentración bruta es además amplificada por el número combinatorio de parejas de solo dos perfiles grandes, no por 934 observaciones independientes.

Con un umbral diagnóstico de error absoluto de diferencia >1 t/ha, 15.30% de las evaluaciones de parejas internas de Chignahuapan lo exceden, frente a 3.76% fuera y 8.33% mixtas. Chignahuapan reúne 95.52% de esas evaluaciones difíciles. Se cuentan evaluaciones de las diez repeticiones (1,811 internas, 213 externas y 60 mixtas), no parejas independientes; ese umbral se fija aquí como descripción y no como regla predictiva.

| Protocolo | RMSE diferencias interno Chignahuapan | RMSE diferencias ambos fuera |
|---|---:|---:|
| Aleatorio | 0.7983 | 0.5308 |
| Perfil climático | 0.7907 | 0.5466 |
| Municipal | 0.7877 | 0.5689 |
| Espacial | 0.7955 | 0.5482 |

El contraste local persiste en los cuatro protocolos. E2 —inicio del ascenso LAI— mejora modestamente la diferenciación, pero conserva la concentración de error; no resuelve este problema local.

Esto no implica que Chignahuapan sea el mayor problema en toda la predicción regional:

| Protocolo | RMSE por parcela Chignahuapan | RMSE por parcela fuera | Proporción SSE parcelaria en Chignahuapan |
|---|---:|---:|---:|
| Aleatorio | 0.5576 | 0.4420 | 62.78% |
| Perfil | 0.5488 | 0.5012 | 55.96% |
| Municipal | 0.5530 | 0.7769 | 34.94% |
| Espacial | 0.5585 | 0.8913 | 29.38% |

La dificultad local es mayor dentro de Chignahuapan; la transferencia a municipios/regiones no vistos presenta mayores errores por parcela fuera. Son objetivos distintos. Los perfiles dominantes locales tienen desviaciones observadas de rendimiento ~0.579 y ~0.591 t/ha; esa variación real no queda explicada por las características actuales, pero no es una prueba de impredecibilidad intrínseca.

Tiene sentido investigar fuentes específicas para Chignahuapan si el objetivo es diferenciar parcelas con el mismo clima. Las nuevas fuentes deberían medir variación parcelaria dentro de esos dos perfiles: manejo/siembra, características de suelo con mayor detalle o condiciones locales de agua/terreno son hipótesis posibles, no causas demostradas por este análisis. Repetir información regional constante no atacaría el problema observado. Para priorizar gasto o recolección conviene comprobar primero que la fuente varía entre parcelas y tiene soporte compatible, y medir su mejora en las mismas parejas. No hay todavía evidencia para prometer que una nueva fuente resolverá esos residuos.

Tablas de este diagnóstico: `outputs/modeling/family_4/conditional_yield_response/extensions/within_profile_complementarity/v1/diagnostics/chignahuapan_error_concentration/`. Las tablas `strict_location_*` separan ambos miembros y las mixtas; las tablas iniciales `pair_concentration_*` usan la convención previa “algún miembro en Chignahuapan”. La clasificación estricta es la utilizada en esta conclusión.
