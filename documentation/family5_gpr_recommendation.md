# F5 — Recomendación para la primera ejecución futura

**Primer candidato: F5-01, GPR exacto Matérn3/2 con lluvia compacta + NDVI Sentinel de mayo2025.** Cuatroentradas, cuatrohiperparámetros dekernel: amplitud, longitud de lluvia compartida, longitud NDVI y ruido. Mantener C-T3ElasticNet como control de idénticas variables y F5-00-Ccomo ablación de lluvia. No sustituir NDVI de mayo por un índice anual ni comenzar con History15+TOPO25.

La evidencia más clara para esta elección es representacional: C-T3 tuvo la mayor ventaja municipal reciente con unnúcleo compacto, yNDVI de mayo aporta contraste parcelario dentro de perfiles dondeclima no distingue. La hipótesis nueva es que una respuesta suave conjunta pueda aprovechar mejor esas entradas que un modelo lineal. **No tenemos resultados GPR que respalden superioridad.**

Prioridad siguiente: control mensualF5-00-M para vigilar pérdida de información temporal; después sensibilidadDTR, sin asumir que se combinará conNDVI. Cambiar Tmin de la propuesta original porDTR es una decisión de prioridad basada enG/H/F4/C, no una afirmación de que Tmin sea agronómicamenteirrelevante. Tmin permanece eninventario/reserva, sin añadir siete dimensiones al primerGP.

Historia: conservar todos los16nombres efectivos ylistasTOP15 por fold como evidencia, pero probar elparNDVIhist nivel/estacionalidad solo como hipótesiscompacta. Su beneficio individual no equivale aldelbloqueresidualRS4. Topografía: comenzar, si corresponde, porpendiente_media; su utilidad conGPR directo tampoco estádemostrada.

Kernels aditivos yGP residual vienen después de controles simples. La variante residualsobreChampion permanece suspendida hasta disponer de reconstrucción honesta de sus3 capas para cada entrenamientointerno. ElbaseC-T3es la opción residual verificable propuesta.

No se ejecutó ninguno de estos experimentos, no se llamó aloptimizador y no se generaron predicciones finales. La matriz y losmárgenes son una propuesta para revisión. Si se acepta la estructura, el siguiente trabajo será implementar una primera comparación acotadaF5-01/F5-00-C/C-T3 sobrelos65 folds, con pruebas dekernel/ruido/cross-validation y sin abrir labatería completa automáticamente.
