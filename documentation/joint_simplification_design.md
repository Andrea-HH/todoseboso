# Simplificaciones conjuntas: diseño previo

Continuación exploratoria motivada por la ejecución de roles; no confirmación independiente. Se mantienen65 particiones e internas originales, target138, fuentes, geografía, entrenamiento y evaluación de la etapa previa. Salida nueva `outputs/modeling/joint_simplification/v1`; ningún Champion, GeoC, experimento anterior, entrenamiento final138 o nueva predicción59PRED se modifica.

Se prueban exclusivamente cuatro configuraciones fijas:

| Ruta | Local | Gate | Campos totales |
|---|---|---|---:|
| J7_BOTH | Sin MSI histórico ni las3 SoilGrids:7 | BOTH15 | 28 |
| J9_SHARES | Sin SoilGrids:9 | Proporciones geológicas10 | 25 |
| J10_SHARES | Sin MSI histórico:10 | Proporciones geológicas10 | 26 |
| J7_SHARES | Sin ambos bloques:7 | Proporciones geológicas10 | 23 |

Se cuentan cuatro compactas y dos coordenadas en todos los totales. Las7 restantes son media/std NDVI histórico, cambios de dirección EVI Planet2025, delta NDVI Planet junio–agosto, media/std NDWI S22025 y pendiente media. No se reintroduce ningún bloque retirado en el corrector o gate. El corrector del experto conserva únicamente compact4.

Representación local original estandarizada dentro del entrenamiento, Ridge24 vecinos alfa30 y pesos originales. Se reutilizan clases/pipelines sin cambios: Elastic Net grid12 original y amplitudes0/.25/.5, gate convexo contraído20 con K4/8 elegido únicamente sobre OOF internas de expertos completos retuneados. No nuevo selector entre rutas, nueva PCA, vecinos, regularización, árboles o pesos regionales. El fallo del selector amplio anterior motiva mantener las rutas fijas.

Se recuperan en lectura los expertos9/10 de cachés previas por posiciones y CV exactas, targets de entrenamiento iguales y fuente original; se comprueba reproducción exacta externa en65 folds. Solo el experto7 necesita ajustes nuevos. Se conservan transformaciones y targets OOF locales dentro de cada entrenamiento aplicable. Para decidir K se usan OOF de ambos expertos dentro de cada entrenamiento interno A_j, excluyendo el fold externo y los casos retenidos D_k. Mismo fallback profundo si no hay grupos/parcelas para retunear: base local sin corrector, nunca CV aleatoria sustituta.

Controles archivados: C-T3, BASE12_BOTH, DROP_HISTORY_WATER, DROP_SOIL, GATE_ONLY_SHARES, MEAN_BOTH y mezcla grande anterior. Contrastes primarios: J7_BOTH vs DROP_SOIL; J9_SHARES vs DROP_SOIL; J10_SHARES vs DROP_HISTORY_WATER; J7_SHARES vs J7_BOTH. Así se identifica la pérdida al añadir una retirada. Además se reportarán todos frente a BASE12_BOTH y a los padres pertinentes para interpretar interacciones; los contrastes adicionales son descriptivos.

RMSE y R² siempre juntos por protocolo, sobre OOF completas por repetición (aleatoria media10), MAE/sesgo complementarios. Bootstrap5000 por conglomerados y signos de diferencias de pérdida cuadrática; Holm sobre4×4=16 contrastes primarios. Intervalos exploratorios de OOF fijas: no corrigen toda búsqueda histórica, dependencia espacial residual ni reajuste. No se interpreta falta de significación como equivalencia. No se promedian protocolos distintos para producir un ganador único.

Se analizan cambios por parcela, municipios/bloques, omisiones sin reajuste, errores intraperfil con dos pesos, pesos aprendidos y uso de fallback. Se entrega inventario por función, modelos por fold, OOF y decisiones internas. Pruebas de contratos de composición y exclusión de etiquetas externas del experto7, además de regresión de las tres pruebas de roles. Reproducción independiente de los260 modelos de mezcla nuevos y hashes protegidos. No promoción automática; no se presupone que las retiradas se sumen ni que contar menos campos implique menos costo en igual proporción.
