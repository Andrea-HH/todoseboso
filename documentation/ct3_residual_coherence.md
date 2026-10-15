# Coherencia residual sobre C-T3: ejecución controlada

La etapa se completó. **No se recomienda integrar ninguna de las cuatro correcciones ni reemplazar C-T3 por el conjunto de bases de esta prueba.**

## Qué se probó

Cada C-T3 se mantiene congelado: se entrena en una parte del entrenamiento externo y su corrector aprende errores en otra parte que esa base no vio. En evaluación se utiliza exactamente esa pareja. Se promedian cuatro parejas por fold externo. La selección interna reproduce este procedimiento con bases más profundas, sin etiquetas externas.

Se conservaron los 65 folds externos, las particiones internas, las variables y los límites anteriores. Correctores: Ridge LAI, Ridge LAI + contexto climático/NDVI, CART con las mismas cuatro entradas y CART de contexto sin LAI. Profundidad 1/2, hojas mínimas 15/25 y amplitud 0/.25/.5. No se ampliaron límites ni se entrenaron modelos regionales.

El contexto incluye fracción temprana de lluvia, concentración HHI y NDVI de mayo. LAI es el inicio del ascenso de LAI en 2025. Las bases utilizan las tres variables de lluvia compacta y NDVI de mayo.

## Resultados

RMSE en t/ha. Métricas sobre OOF completas por repetición; se promedian las diez repeticiones aleatorias, no las métricas de folds.

| Formulación | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| C-T3 original | **0.5116** | 0.5206 | **0.5813** | **0.6788** |
| Conjunto de bases, sin corrección | 0.5126 | 0.5166 | 0.5914 | 0.7596 |
| Conjunto + Ridge LAI | 0.5132 | 0.5166 | 0.5911 | 0.7596 |
| Conjunto + Ridge LAI/contexto | 0.5138 | 0.5160 | 0.6019 | 0.7276 |
| Conjunto + CART LAI/contexto | 0.5126 | 0.5174 | 0.5887 | 0.7751 |
| Conjunto + CART contexto sin LAI | 0.5126 | **0.5160** | 0.5887 | 0.7742 |

La ganancia por perfil es pequeña y no compensa el deterioro espacial. El conjunto sin corrección pierde 0.0809 de RMSE espacial respecto a C-T3. La corrección lineal conjunta recupera 0.0320 frente al conjunto, pero permanece 0.0489 peor que C-T3 y perjudica municipalmente.

## Concentración territorial

La mejora espacial de Ridge LAI/contexto frente al conjunto depende del bloque 3: RMSE 1.0269 → 0.8737 allí. En el bloque 4 empeora de 0.8049 a 1.0118. Si se excluye el bloque 3 únicamente del cálculo, sin reajustar, la corrección lineal pasa a ser **0.0267 peor** que el conjunto. Frente a C-T3, sigue peor al omitir cualquiera de los cinco bloques (diferencias de +0.0159 a +0.0910).

Reducir sesgo agregado no implica mejorar generalización. El conjunto tiene sesgo espacial +0.1039 frente a +0.1912 de C-T3, pero RMSE mayor: sobreestima los bloques 3/4 y subestima los bloques 1/2, cancelándose parcialmente en la media. CART LAI/contexto baja el sesgo agregado a +0.0855 mientras empeora RMSE a 0.7751.

La dispersión espacial de errores también es mayor. Usando la identidad MSE = sesgo² + varianza de errores, la desviación de errores es aproximadamente 0.6513 para C-T3, 0.7525 para el conjunto y 0.7704 para el conjunto con CART LAI/contexto.

## Información intraperfil

No apareció una mejora intraperfil de al menos 0.01 respaldada simultáneamente por ponderación de pares y de perfiles. Por ejemplo, el CART conjunto mejora frente a C-T3 el RMSE espacial equilibrado por perfil de 0.5401 a 0.5360, pero empeora el ponderado por pares de 0.7675 a 0.7779. No es una mejora local consistente.

Los correctores CART con y sin LAI producen exactamente las mismas predicciones municipales. Añadir LAI no aporta mejora municipal en esta formulación. Esto se comprobó en OOF, además de las métricas agregadas.

## Limitación de soporte

En aleatoria, las calibraciones internas tienen 20–21 parcelas y las externas 27–28. Con mínimo de 15 parcelas por hoja, se necesitan al menos 30 para dividir. Por ello los árboles no pueden dividir en ese protocolo y la selección elige amplitud cero en los 50 folds aleatorios.

También existen calibraciones agrupadas pequeñas o con pocos perfiles. Es un límite real de separar entrenamiento de base y calibración con 138 etiquetas. No se redujeron hojas mínimas para forzar correcciones. Un árbol desactivado por falta de soporte no demuestra ausencia de interacciones agronómicas.

## Hipótesis y recomendación

- **Apoyada:** la calibración con la base congelada es implementable sin contaminación de etiquetas externas; garantiza por construcción que el corrector se aplica a la base que generó sus residuos.
- **Debilitada:** eliminar ese cambio de base mediante este conjunto de parejas sea suficiente para mejorar C-T3. No sucedió.
- **No identificada aisladamente:** cuánto del problema anterior se debía al cambio crossfit/refit. El contraste también cambia tamaños de entrenamiento y calibración y promedia bases; no permite una atribución causal única.
- **Sin respaldo de integración:** las correcciones LAI/contexto, lineales o CART, no ofrecen ganancias territoriales equilibradas bajo esta formulación.

**Recomendación:** conservar C-T3 como referencia y cerrar esta formulación de parejas. No justificar árboles más profundos con estos resultados. Si se autoriza otra etapa, estudiar primero complementariedad de errores entre C-T3, GPR y CatBoost compacto y, solo si existe soporte, una combinación pequeña con pesos no negativos seleccionados completamente dentro del entrenamiento. Sería una pregunta distinta y no se ejecutó aquí. Datos adicionales de campañas y regiones siguen siendo la prioridad para confirmar transferencia.

## Artefactos y verificación

Se guardaron 8,970 nuevas OOF, 260 paquetes de modelos completos, selección interna, soporte de calibración, reglas, comparaciones pareadas, errores municipales/espaciales y omisiones de regiones. Se realizaron 14,548 ajustes de correctores y **cero nuevos ajustes de bases**. Se verificó la reproducción de los 260 predictores guardados y la integridad de todos los archivos consumidos.

Cuatro pruebas pasaron, incluida una prueba del pipeline completo que altera en +10,000 los rendimientos externos y comprueba que predicciones, parámetros, amplitudes y selección interna permanecen iguales dentro de tolerancia numérica. No se ajustó modelo final de 138 etiquetas, no se modificó Champion y no se generaron predicciones PRED. Los correctores deterministas no tienen intervalos predictivos calibrados.

- [Diseño congelado](../outputs/modeling/ct3_residual_coherence/v1/report/frozen_design.md)
- [OOF nuevas](../outputs/modeling/ct3_residual_coherence/v1/tables/oof_predictions.csv)
- [Resultados y diagnósticos](../outputs/research/ct3_residual_coherence_synthesis/v1/informe.md)
- [Figura de desempeño y sesgo](../outputs/research/ct3_residual_coherence_synthesis/v1/performance_and_spatial_bias.png)
- [Implementación](../src/ct3_residual_coherence.py)
- [Pruebas](../tests/test_ct3_residual_coherence.py)
