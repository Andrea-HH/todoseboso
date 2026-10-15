# Experimento PLS con 1,867 descriptores

Resultados y dise?o: ../outputs/modeling/experimental_pls1867/v1/informe.md

Se ejecutaron 65 folds externos originales, con selecci?n de componentes [1,2,3,5,8,12,16] exclusivamente en los folds internos congelados. Preprocesamiento ajustado por entrenamiento: imputaci?n, one-hot para categor?as, retiro de constantes y escalado. Duplicados retenidos deliberadamente. Se preservaron 65 modelos y 1,794 predicciones OOF; no se ajust? un modelo final ni se generaron las 59 predicciones PRED.

RMSE aleatoria/perfil/municipal/espacial: 0.538506 / 0.559928 / 0.716929 / 0.891999 t/ha. C-T3: 0.511582 / 0.520604 / 0.581259 / 0.678778. PLS empeora en los cuatro protocolos. La representaci?n completa no mostr? ventaja en esta formulaci?n; no es evidencia contra todo PLS ni demuestra que las variables complementarias carezcan de utilidad. Compresi?n lineal global, redundancias, categor?as territoriales y muestra peque?a son limitaciones plausibles, no causas aisladas por este experimento. No se cambi? el dise?o tras observar los resultados.

Dos pruebas unitarias pasaron. Se verific? reproducci?n OOF desde los 65 modelos guardados e integridad de todos los artefactos sellados. Las m?tricas se calcularon sobre OOF completas por repetici?n y luego se promediaron las diez repeticiones aleatorias; las m?tricas por fold son diagn?sticas.

Durante la ejecuci?n threadpoolctl emiti? advertencias de coexistencia Intel y LLVM OpenMP fuera del contexto de captura de ajustes. La ejecuci?n concluy? y produjo predicciones finitas; estas advertencias de runtime no deben confundirse con advertencias de convergencia, registradas en fit_registry.csv. No se ampli? la bater?a ni se promovi? un Champion.

Reproducci?n: python scripts/369_experimental_pls1867.py, con salida nueva/versionada al repetir para preservar v1. Implementaci?n: src/experimental_pls.py.
