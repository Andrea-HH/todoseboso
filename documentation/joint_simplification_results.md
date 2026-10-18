> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Simplificación conjunta: experto7 y gate geológico reducido

Se ejecutaron las cuatro configuraciones congeladas sobre las65 particiones externas e internas originales. La salida está en `outputs/modeling/joint_simplification/v1`. No se cambió el Champion, ningún resultado previo, GeoC, los138 rendimientos ni las59PRED; no hay nuevo entrenamiento final138.

**Recomendación:** conservar **J7_BOTH** como nueva candidata de simplificación para revisión: cuatro compactas, siete entradas del experto, quince del gate y dos coordenadas,28 campos distintos. Mantiene el balance predictivo del control33 con cambios pequeños. No se declara superioridad estadística, equivalencia ni un nuevo Champion automático. Reducir simultáneamente el gate hasta23 campos empeora espacialmente y no es la primera opción si importa transferencia territorial.

## RMSE y R² por protocolo

Cada celda contiene **RMSE t/ha / R²**. Aleatoria es la media de las métricas calculadas sobre OOF completas de cada una de las10 repeticiones; los otros protocolos se calculan sobre sus OOF completas. No son métricas de entrenamiento ni un promedio de protocolos.

| Modelo | Campos distintos | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|---:|
| C-T3 | 4 | 0.5116 / 0.6361 | 0.5206 / 0.6232 | 0.5813 / 0.5302 | 0.6788 / 0.3594 |
| Mezcla grande anterior | 1,850 | 0.4852 / 0.6725 | 0.4996 / 0.6530 | 0.5847 / 0.5247 | 0.6811 / 0.3549 |
| Control experto12 + gate15 | 33 | 0.4880 / 0.6688 | 0.4879 / 0.6691 | 0.5810 / 0.5307 | 0.6843 / 0.3490 |
| Anterior experto10 sin MSI + gate15 | 31 | 0.4870 / 0.6701 | 0.4871 / 0.6702 | 0.5811 / 0.5306 | 0.6840 / 0.3494 |
| Anterior experto9 sin SoilGrids + gate15 | 30 | 0.4874 / 0.6696 | 0.4897 / 0.6666 | 0.5807 / 0.5311 | 0.6811 / 0.3550 |
| Anterior experto12 + gate geológico10 | 28 | 0.4876 / 0.6693 | 0.4901 / 0.6660 | 0.5832 / 0.5271 | 0.6852 / 0.3472 |
| Anterior media de vecinos + corrector + gate15 | 21 | 0.4890 / 0.6674 | 0.4982 / 0.6549 | 0.5813 / 0.5301 | 0.6808 / 0.3555 |
| **J7_BOTH: experto7 + gate15** | **28** | **0.4864 / 0.6709** | **0.4890 / 0.6675** | **0.5808 / 0.5309** | **0.6808 / 0.3556** |
| J9_SHARES: experto9 + gate10 | 25 | 0.4875 / 0.6695 | 0.4917 / 0.6639 | 0.5826 / 0.5280 | 0.6904 / 0.3373 |
| J10_SHARES: experto10 + gate10 | 26 | 0.4869 / 0.6703 | 0.4882 / 0.6686 | 0.5839 / 0.5260 | 0.6846 / 0.3483 |
| J7_SHARES: experto7 + gate10 | 23 | 0.4865 / 0.6708 | 0.4913 / 0.6644 | 0.5835 / 0.5266 | 0.6894 / 0.3393 |

Las1,850 entradas de la mezcla grande son la unión de1,831 del experto, compact4 y15 físicas. Las coordenadas ya están entre las1,831, por lo que no se cuentan dos veces. No son1,850 coeficientes efectivos. Los nuevos conteos incluyen coordenadas y entradas originales por función; no contabilizan columnas codificadas como variables nuevas independientes.

## Qué contiene la candidata J7_BOTH

| Función | Entradas |
|---|---|
| C-T3,4 | Lluvia total abril–octubre, fracción temprana, concentración mensual HHI, NDVI S2 mayo2025 |
| Local,7 | Media/std NDVI S2 histórico; cambios de dirección EVI Planet2025; cambio NDVI Planet junio–agosto; media/std NDWI S22025; pendiente media |
| Corrector del local | Reutiliza las mismas compact4, con coeficientes propios y amplitud seleccionada internamente |
| Gate físico,15 | Textura/fase INEGI2, proporciones geológicas10 y distancias a estructuras/fallas/fracturas3 |
| Vecinos,2 | Latitud y longitud |

La predicción sigue siendo `C-T3 + w(z)*(experto7 − C-T3)`. El experto7 es Ridge geográfico de24 vecinos, alfa30, originales estandarizadas dentro de entrenamiento, más corrección Elastic Net de residuos OOF locales. El gate aprende pesos convexos contraídos20 y K4/8 usando solo validación interna. Las siete entradas no son siete variables demostradas como significativas individualmente ni un modelo de siete coeficientes globales.

El peso medio externo del experto7 es0.690 aleatoria,0.720 por perfil,0.061 municipal y0.396 espacial. Su resultado municipal cercano a C-T3 se explica en parte por el peso pequeño del experto; no demuestra que el local aislado generalice a municipios nuevos. Son promedios de pesos aprendidos en folds, no reglas operativas manuales por protocolo.

Se eliminaron del local las dos estadísticas históricas de MSI y las tres SoilGrids (arcilla, densidad aparente, carbono0–30cm), sin reintroducirlas en corrector o gate. Esto elimina la dependencia de SoilGrids de esta configuración, pero conserva suelo INEGI en el gate. Mantiene Sentinel-2 histórico por NDVI y Planet2025; no elimina esas fuentes. Las ventanas2025 posteriores a mayo implican evaluación retrospectiva del ciclo, no un pronóstico disponible únicamente en mayo.

## Pérdida frente al control y frente a los padres

Cambios de RMSE de J7_BOTH frente al control33: **−0.001570 / +0.001156 / −0.000133 / −0.003446**. Son diferencias pequeñas. Frente al experto9 + gate15, cambia−0.000982 / −0.000677 / +0.000141 / −0.000306. La retirada conjunta de MSI y SoilGrids conserva bien el comportamiento observado, sin justificar afirmar igualdad verdadera.

Frente a la mezcla grande anterior, J7_BOTH pierde0.001183 aleatoria y mejora0.010544 por perfil,0.003807 municipal y0.000334 espacial. Son comparaciones descriptivas entre alternativas ya exploradas, no una confirmación independiente. C-T3 sigue ligeramente mejor espacialmente (0.678778 frente a0.680808); no hay un ganador uniforme en todos los usos.

La versión23 tiene RMSE aleatorio casi igual a J7_BOTH (+0.000129), pero pierde0.002281 por perfil,0.002638 municipal y0.008558 espacial. Su deterioro espacial persiste al omitir cualquiera de los cinco bloques del cálculo, entre+0.005506 y+0.011764 frente a J7_BOTH. No depende únicamente del bloque3.

J10_SHARES26 es una alternativa de costo: mantiene SoilGrids, retira MSI y reduce el gate, con errores cercanos al control. No mejora claramente a J7_BOTH y tiene peor municipal/espacial. Si las fuentes geológicas de distancias o INEGI textura/fase resultaran costosas, sus compromisos se pueden revisar; no se elige retrospectivamente para un protocolo particular.

## Las retiradas no son aditivas

Se calculó un contraste descriptivo en MSE: `MSE(combinado) − MSE(retirada1) − MSE(retirada2) + MSE(control)`, por repetición y después promedio. No se suman RMSE ni se interpreta este contraste como efecto causal o prueba estadística independiente.

Retirar SoilGrids con gate15 mejora espacial respecto al control, de0.684253 a0.681114. Reducir solo el gate a10 aumenta ligeramente a0.685204. Hacer ambas cosas sube a0.690370: peor que lo sugerido por sumar las retiradas individuales. La interacción descriptiva espacial es+0.011393(t/ha)² en MSE. Mantener ciertas señales en otra parte del sistema puede amortiguar una retirada: el resultado de eliminar una familia depende de qué señales permanecen.

Retirar conjuntamente MSI y SoilGrids con gate15 sí mantiene el desempeño; la interacción descriptiva espacial de esas dos retiradas es−0.000112(t/ha)², pequeña. No se deduce que cualquier nueva retirada vaya a ser inocua. No se ejecutan búsquedas abiertas de subcombinaciones.

## Regiones, calibración e intraperfil

La pequeña ganancia espacial de J7_BOTH frente al control33 persiste al omitir cualquiera de los cinco bloques: cambios deRMSE entre−0.002162 y−0.004089 sin reajustar. Su variación municipal frente al control cambia de signo según el fold omitido, por lo que no se presenta como ganancia municipal consolidada.

Municipal: Calpulalpan cambia de0.475875 a0.471039; Chignahuapan de0.579937 a0.579824; Singuilucan de0.882247 a0.887704. No resuelve el error de Singuilucan ni produce una mejora universal por municipio. Espacial: el bloque3 cambia de0.922032 a0.915962, el1 de0.526681 a0.524623 y el2 de0.557834 a0.553669. No se eliminan casos ni se adaptan reglas a esos resultados.

MAE de J7_BOTH:0.347013 / 0.344483 / 0.460376 / 0.529095. Sesgo:−0.012057 / −0.013897 / −0.020525 / +0.291326. En espacial baja el sesgo frente al control (+0.305100), aunque la varianza de errores aumenta de0.375117 a0.378628. La pequeña mejora del RMSE procede de menor sesgo, no de menor dispersión. Frente a J7_BOTH, reducir a23 aumenta sobre todo sesgo espacial (+0.310535), con varianza de errores muy parecida0.378792.

Intraperfil con igual peso por perfil: J7_BOTH consigue0.577734 / 0.531695 / 0.525679 / 0.531955, frente al control0.579284 / 0.531804 / 0.523697 / 0.532478. Hay mejora leve en tres protocolos y empeoramiento municipal. El resultado con peso por par también se entrega; el orden puede cambiar y los pares no son independientes. No se demuestra resolver la variabilidad entre parcelas climáticamente semejantes.

## Incertidumbre, decisión y próximos límites

Ninguno de los16 contrastes primarios supera Holm al5%. El bootstrap5000 por conglomerados y los signos de pérdida cuadrática se aplican sobre predicciones fijas; no incorporan toda la búsqueda histórica ni incertidumbre de reentrenamiento. Hay43 perfiles TRAIN,9 municipios y5 bloques espaciales. Falta de significación no demuestra equivalencia ni ausencia de aporte agronómico.

La decisión razonable es mantener J7_BOTH como candidata compacta y las referencias anteriores intactas. Para una entrega que priorice simplicidad y balance, es más justificable revisar esta receta fija28 que seguir persiguiendo unos campos menos mediante un menú amplio. No conviene volver a seleccionar retrospectivamente un modelo diferente por protocolo ni añadir automáticamente correcciones o reglas municipales.

El siguiente paso útil sería confirmar esta configuración en datos realmente nuevos o un banco independiente compatible, y preparar su pipeline operativo mínimo si se aprueba. Un nuevo ciclo anual permitiría revisar estabilidad temporal; estos resultados no la prueban. Si se continúa con reducción individual, debería ser una batería nueva congelada sobre las siete, con controles físicos conservados y sin asumir aditividad. No se ejecutó esa siguiente batería en esta etapa.

## Reproducción y artefactos

- `scripts/445_prepare_joint_simplification.py`: diseño, cuatro recetas, referencias y hashes.
- `scripts/446_run_joint_simplification.py`: ejecución reanudable por fold; nuevas salidas sin sobrescribir.
- `scripts/447_summarize_joint_simplification.py`: RMSE/R² por defecto, MAE/sesgo, contrastes, no aditividad, regiones, omisiones, pesos, inventarios y replay.
- `scripts/448_audit_joint_simplification_delivery.py`: comprueba identidad R²/MSE por repetición, agregación OOF, conteos y hashes finales.
- Cinco pruebas previas aprobadas: dos de esta composición y tres de regresión de los componentes de roles; exclusión de etiquetas externas y representación física previa verificadas.
- Libro `resultados_simplificacion_conjunta.xlsx`, figura `diagnostics/joint_RMSE_R2.png`, decisiones e inventario en `diagnostics/`, predicciones en `tables/predictions.parquet` y modelos en `models/`.

El entrenamiento tardó827.5s de reloj. Los expertos9/10 se recuperan y su reproducción se verifica por separado; solo el7 requiere ajustes nuevos. Se mantiene el fallback profundo congelado a base local cuando faltan grupos/parcelas, sin sustituir por CV aleatoria. Esto limita la interpretación de pesos al cambiar el tamaño de entrenamiento entre niveles. Las comprobaciones definitivas constan en `manifest.json`, `delivery_audit.json` y `audit/`.

La auditoría completa260 reproducciones exactas de mezclas por fold,260 decisiones internas de K y24,404 comprobaciones de exclusión. Las siete referencias archivadas y los dos expertos recuperados coinciden exactamente; hashes protegidos intactos. Se conservan19,734 filas OOF:7,176 nuevas y12,558 de referencia. Hay153 usos de fallback profundo,51 contextos por tres variantes (21 municipales y30 espaciales por variante), no153 fallos externos. Se registraron cuatro advertencias ambientales OpenMP y ninguna de convergencia durante el entrenamiento.

Outputs sigue excluido de Git; no se hizo push ni se generaron nuevas predicciones finales. Las métricas se presentan conforme a `documentation/model_comparison_convention.md`.
