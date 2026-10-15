# Etapa D — Auditoría de integridad

Estado: completa. Se verificaron 5108 archivos protegidos anteriores y 5 referencias directas a fuentes contra la procedencia deB. Incluye artefactosA–C/F4/F4-E, Champion, antecedentes, métricas, configuraciones y scripts. Los archivos previos permanecen intactos.

Se conservaron138etiquetas,59parcelas sinYutilizado y65folds. Hay15318filas OOFcompatibles archivadas en9series, con138IDsúnicos; aliasB2/E2 no son modelos independientes. Hay21comparaciones protocolo/candidato compatibles. Inventario histórico:228series de modelo/archivo, incluyendo controles descartados.

**Cero nuevos modelos, cero nuevas estimaciones predictivas, cero llamadas de entrenamiento.** La prueba AST verifica ausencia de fit/predict en los módulosD. Las importaciones de fuentes anteriores solo recuperan datos, constantes y folds; no llaman a estimadores. No existe directorioD/models. No se modificaronChampion,mezcla,pesos,variables,labels o splits.

Pasaron20pruebas automatizadas: identidadY/IDs y exclusión59PRED; particiones; llaves exactas; reproducción de métricasC; OOFporrepetición; SSEycontribuciones; omisiones sinreentrenamiento; pérdidas agrupadas por parcela; pares del mismo ajuste y ponderaciónperfil; protocolos separados; conservación de influyentes; hashes previos; Champion/mezcla exactos; ausencia de entrenamiento; trazabilidadfiguras; consistenciadocumental y soporte. Log:`audit/automated_tests.txt`.

`audit/protected_inputs.csv` registra hashes previos; `audit/read_only_input_provenance.csv` comprueba entradas realmente utilizadas; `tables/comparability.csv` documenta n por comparación; `tables/model_inventory.csv` registra IDs/modelos/procedencia. La llave es(ID_POLIGONO,protocolo,repetición,fold),Y idéntico. Los resultados Champion solo son aleatorios; no se inventaron OOFgeográficas. C-T0/F4-S1yB2/F4-E2son alias.

Los modelos iniciales y finales de esta etapa tienen el mismo conteo porque no se ajusta ninguno. El análisis omite comparaciones que no tienen protocolos compatibles, nunca recupera especulativamente predicciones inexistentes. Las sensibilidades no eliminan observaciones de las fuentes. Los nuevos artefactosD se identifican porSHA-256 en `manifest.json`; el propio manifiesto se excluye de su lista para evitar autorreferencia.

El diseñoD.0 conservó hashes del código diagnóstico inicial. El manifiesto final registra las fuentes de análisis/reportes/pruebas definitivas; refinamientos descriptivos/documentales no modificaron predicciones ni la matriz experimental. Las conclusiones siguen siendo exploratorias y los parámetros operativos de adquisición/precisión pendientes están señalados en el protocolo.
