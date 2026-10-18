# Validación OOF — Reference26 y Compact14

**Predicciones finales disponibles:** [resultados de las59 de26/14](../../current_champions_final/v1/README.md). Las tablas de esta página son errores OOF sobre138 conocidas; no errores de las59.

Champions seleccionados por instrucción del responsable del proyecto: **Reference26** y **Compact14**. La entrega reproducible incluye además **CT3** como control y **B1** como sensibilidad. No incluyeL40/Local04D, sus componentesPCA ni sus predicciones. L40 se conserva como benchmark externo fuerte en las tablas del README principal y en su ficha; este paquete reproduce únicamente los cuatro modelos propios. Los hashes de procedencia de esta auditoría corresponden a la revisión documental existente cuando se ejecutó, anterior a las nuevas fichas.

## Archivos de resultados

- [Métricas por protocolo](metrics.csv): RMSE/R²/MAE, sesgo, percentil95 y proporción dentro de±.5t/ha.
- [Métricas por repetición](metrics_by_repeat.csv): agregación verificable, sin promediar RMSE de folds.
- [Diagnósticos por estado](metrics_by_state.csv): métricas regionales agregadas, sin datos individuales.
- [Diagnósticos municipales](metrics_by_municipality.csv) y [por bloque espacial original](metrics_by_spatial_block.csv): soporte,RMSE/R²/MAE ysesgo; los identificadores de bloque no son los números de fold.
- [Auditoría de reproducción](reproduction_audit.json): alcance y máxima diferencia entre predicciones reconstruidas y archivadas.
- [Verificación de reentrenamiento](cold_refit_verification.json): folds comprobados desde las entradas, sin confundirlos con el replay.
- [Procedencia del código](source_provenance.json): hashes normalizadosLF de las implementaciones y configuración.
- [Comprobación de exclusión](held_out_target_invariance.json): modificar sólo en memoria las respuestas externas de un fold no cambia sus predicciones reentrenadas.

Estos archivos los genera `python scripts/521_current_champions.py replay` con el bundle privado. El reentrenamiento es un comando distinto: consultar [reproducción actual](../../../documentation/current_champions_reproduction.md). La auditoría distingue reconstrucción de modelos guardados frente a entrenamiento desde las entradas; no confundirlos.

## Cómo leerlos

26 se conserva por el equilibrio de precisión y transferencia.14 elimina las dos entradasPlanet, diez proporciones geológicas y la corrección climática interna del experto, con una pérdida pequeña en las métricas agregadas. B1 tiene una ventaja municipal puntual pero pierde espacial; se conserva como sensibilidad, no como tercer champion. La selección no depende exclusivamente de elegir la cifra aleatoria más pequeña.

Son65 folds originales:50aleatorios (10repeticiones),5por perfil,5municipales y5espaciales. Se calculan métricas sobre OOF completas por repetición y después se promedian. Las16 particiones adicionales97/41 se reportan por separado y reutilizan los mismos rendimientos.

Error=predicho−observado: positivo sobreestimación, negativo subestimación. Los dos champions siguen siendo arquitecturas regulares/locales con varias etapas:14/26 no son números de coeficientes globales. No se publica un R² ajustado clásico usando esos conteos como grados de libertad. RMSE yMAE están en t/ha; R² no es porcentaje de aciertos.

Esta es evidencia exploratoria de 138 parcelas; no conoce el error real de 59 ni demuestra superioridad universal. Ambos champions ya tienen ajuste final138 y59 predicciones. Esos archivos se presentan por separado; esta página conserva exclusivamente la evidencia de validación.

<!-- CURRENT_METRICS_START -->
## Tabla de métricas reproducidas

| Protocolo | Modelo | RMSE | R² | MAE | Sesgo |
|---|---|---:|---:|---:|---:|
| Aleatoria | Reference26 | 0.4748 | 0.6865 | 0.3396 | -0.0071 |
| Aleatoria | Compact14 | 0.4773 | 0.6832 | 0.3399 | -0.0074 |
| Aleatoria | CT3 | 0.5116 | 0.6361 | 0.3749 | +0.0005 |
| Aleatoria | B1 | 0.4755 | 0.6856 | 0.3396 | -0.0069 |
| Perfil | Reference26 | 0.4774 | 0.6831 | 0.3342 | -0.0010 |
| Perfil | Compact14 | 0.4793 | 0.6805 | 0.3336 | +0.0177 |
| Perfil | CT3 | 0.5206 | 0.6232 | 0.3915 | +0.0046 |
| Perfil | B1 | 0.4839 | 0.6744 | 0.3408 | +0.0021 |
| Municipal | Reference26 | 0.5752 | 0.5400 | 0.4491 | -0.0413 |
| Municipal | Compact14 | 0.5755 | 0.5395 | 0.4468 | -0.0103 |
| Municipal | CT3 | 0.5813 | 0.5302 | 0.4603 | -0.0203 |
| Municipal | B1 | 0.5681 | 0.5513 | 0.4426 | -0.0417 |
| Espacial | Reference26 | 0.6333 | 0.4423 | 0.5004 | +0.2285 |
| Espacial | Compact14 | 0.6431 | 0.4250 | 0.5140 | +0.1232 |
| Espacial | CT3 | 0.6788 | 0.3594 | 0.5306 | +0.1912 |
| Espacial | B1 | 0.6813 | 0.3546 | 0.5388 | +0.2857 |
| 97/41 separado | Reference26 | 0.4625 | 0.6971 | 0.3387 | +0.0016 |
| 97/41 separado | Compact14 | 0.4661 | 0.6933 | 0.3398 | +0.0020 |
| 97/41 separado | CT3 | 0.4918 | 0.6571 | 0.3642 | +0.0172 |
| 97/41 separado | B1 | 0.4622 | 0.6975 | 0.3373 | +0.0026 |

Reconstrucción completa de81 particiones; reentrenamiento desde entradas verificado en7 folds representativos. No se reentrenaron de nuevo los81.
<!-- CURRENT_METRICS_END -->
