> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Composición y reasignación de funciones en SMALL12

Se completaron28 configuraciones fijas y2 selectores internos, sobre las65 particiones externas originales. Se congelaron las alternativas antes de entrenar. Salida: `outputs/modeling/signal_role_allocation/v1`. No se modifica ningún Champion, GeoC ni resultado anterior; no se ajusta un modelo final ni se generan nuevas59PRED.

**Conclusión:** las candidatas para simplificar son retirar el MSI histórico del experto (queda con10 entradas), retirar sus tres SoilGrids (queda con9) o conservar las12 y reducir el gate a las10 proporciones geológicas. Son alternativas separadas: requieren31,30 y28 campos totales, respectivamente. Trasladar grupos al corrector o al cálculo de pesos no produce una mejora consistente en los cuatro protocolos. Los selectores automáticos entre muchas rutas perjudican municipal y espacialmente: más flexibilidad no resolvió la transferencia territorial.

Las diferencias son pequeñas y exploratorias. Ninguno de los120 contrastes primarios supera Holm al5%; tampoco se demuestra equivalencia estadística. No se declara un nuevo ganador automático ni una composición óptima universal.

## Control comparable y significado de los roles

La comparación nueva fija las12 entradas originales estandarizadas del experto, sin PCA, para aislar retiradas y cambios de función. Conserva Ridge local24 vecinos, alfa30 y pesos originales; el corrector del experto mantiene Elastic Net con grid12 y amplitudes0/.25/.5. El gate mantiene K4/8 elegido internamente y contracción20. Las transformaciones se ajustan dentro del entrenamiento correspondiente.

El control `BASE12_BOTH` no es el selector PCA/originales de la etapa anterior: es un control de representación fija. La reproducción de su experto coincide exactamente con `B_SMALL12_raw_COMPACT` anterior. Se recuperan las mezclas anteriores como referencias separadas.

La ecuación es `predicción = C-T3 + peso(z)*(experto − C-T3)`, donde `experto = local + amplitud*corrector(residuos OOF del local)`. Trasladar al corrector significa añadir el bloque al Elastic Net que ya usa compact4 y reajustarlo conjuntamente, tras retirar ese bloque del local. No es una corrección añadida después de la mezcla ni utiliza residuos externos o del Champion. Trasladar al gate significa usar el bloque para formar grupos y aprender pesos, retirándolo del local.

## Simplificación del experto

RMSE en t/ha, menor es mejor. Se calcula sobre OOF completas por repetición; aleatoria es media10, nunca media de RMSE de folds.

| Configuración | Variables del local | Campos totales | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|---:|---:|
| C-T3 | — | 4 | 0.511582 | 0.520604 | 0.581259 | 0.678778 |
| Mezcla anterior con experto grande | 1,831 | Ver inventario anterior | 0.485226 | 0.499572 | 0.584656 | 0.681142 |
| Mezcla SMALL12 anterior, modo elegido internamente | 12 | 33 | 0.489733 | 0.491141 | 0.580630 | 0.683286 |
| **BASE12_BOTH, originales** | **12** | **33** | **0.487979** | **0.487873** | **0.580981** | **0.684253** |
| Sin vigor histórico NDVI | 10 | 31 | 0.487932 | 0.489296 | 0.581147 | 0.684221 |
| **Sin proxy de agua histórico MSI** | **10** | **31** | **0.487037** | **0.487067** | **0.581061** | **0.684031** |
| Sin dinámica2025 | 8 | 29 | 0.489907 | 0.491462 | 0.581118 | 0.684570 |
| **Sin SoilGrids** | **9** | **30** | **0.487391** | **0.489705** | **0.580708** | **0.681114** |
| Sin pendiente | 11 | 32 | 0.487930 | 0.490426 | 0.581009 | 0.683219 |
| Media de vecinos + corrector compacto + gate BOTH | 0 | 21 | 0.489038 | 0.498181 | 0.581342 | 0.680820 |

El conteo total incluye4 compactas, entradas originales usadas por cualquier función, y2 coordenadas. El corrector compacto vuelve a usar esas mismas4, no cuatro campos adicionales. Las15 del gate completo son textura/fase2, proporciones geológicas10 y distancias3. Contar campos no equivale a contar parámetros independientes ni observaciones necesarias: todos los modelos locales conservan vecinos con rendimiento conocido.

El costo de fuentes tampoco es proporcional al conteo: retirar MSI histórico conserva Sentinel-2 histórico por el NDVI; retirar las tres SoilGrids sí elimina esa fuente de la configuración completa, porque el suelo del gate procede de INEGI. Reducir el gate a proporciones evita textura/fase y distancias, pero conserva SoilGrids dentro del experto y la cartografía geológica. Conviene elegir la simplificación también según disponibilidad y costo de extracción, sin confundirlos con significación estadística.

Retirar MSI histórico cambia el RMSE en−0.000942 / −0.000805 / +0.000079 / −0.000223 frente al control. Es la retirada con menor cambio perjudicial observado entre protocolos. No demuestra irrelevancia agronómica del MSI.

Retirar SoilGrids cambia el RMSE en−0.000588 / +0.001833 / −0.000274 / −0.003139. El experto conserva8 satelitales y pendiente. Las entradas retiradas son arcilla, densidad aparente y carbono orgánico0–30cm. **No se retira todo el suelo del modelo:** textura/fase INEGI siguen en el gate, al igual que geología. Es una simplificación por función, no evidencia de que el suelo no importe.

La media de vecinos con gate BOTH elimina todas las12 del experto. Tiene una pérdida por perfil de0.010308 y pequeñas diferencias en los otros protocolos. Es un control útil, pero no es una simplificación sin costo ni una demostración de equivalencia. El gate completo conserva valor territorial: la versión de solo6 campos y peso global obtiene0.490030 / 0.496498 / 0.608789 / 0.703727.

## ¿Recuperan utilidad en otra función?

Para cada grupo se compararon retiro, traslado al corrector y traslado al gate. En `diagnostics/role_recovery.csv` se entregan tanto el cambio frente al retiro como la pérdida total frente al control completo. Un traslado que supera al retiro puede seguir siendo peor que conservar el bloque en el local.

| Grupo trasladado desde el local | Resultado del corrector | Resultado del gate |
|---|---|---|
| NDVI histórico2 | Mejora espacial leve; empeora aleatoria, perfil y municipal frente al retiro | Pequeña mejora municipal; no mejora consistente |
| MSI histórico2 | Peor que retirarlo en los cuatro protocolos | Mejora por perfil; deterioro municipal y espacial |
| Dinámica2025 cuatro | Municipal baja a0.576973, pero empeoran los otros tres | Mejora perfil/municipal; espacial sube a0.704323 |
| SoilGrids3 | Municipal sube a0.624889; no recomendable | Perfil mejora a0.480086; municipal empeora a0.590939 |
| Pendiente1 | Espacial mejora a0.680731; municipal empeora a0.584883 | Resultados algo mejores en aleatoria/perfil/municipal; espacial empeora a0.687865 |

No hay un traslado que justifique un reemplazo general. Los resultados corresponden al corrector Elastic Net y al gate de clusters definidos, no a todos los correctores posibles. No se añadieron árboles, interacciones libres ni screening posterior.

## Composición de las15 entradas del gate

Se conserva el experto FULL12 fijo en esta comparación.

| Gate | Entradas del gate | Campos totales | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|---:|---:|
| Completo BOTH | 15 | 33 | 0.487979 | 0.487873 | 0.580981 | 0.684253 |
| Global, sin características | 0 | 18 | 0.488777 | 0.487072 | 0.597660 | 0.703907 |
| Solo textura/fase | 2 | 20 | 0.485567 | 0.478757 | 0.591673 | 0.704193 |
| Solo proporciones geológicas | 10 | 28 | 0.487623 | 0.490093 | 0.583172 | 0.685204 |
| Solo distancias geológicas | 3 | 21 | 0.487135 | 0.479108 | 0.617271 | 0.696904 |
| Sin textura/fase | 13 | 31 | 0.487981 | 0.485866 | 0.576496 | 0.689914 |
| Sin proporciones geológicas | 5 | 23 | 0.483745 | 0.474084 | 0.605411 | 0.707159 |
| Sin distancias geológicas | 12 | 30 | 0.490846 | 0.490172 | 0.578017 | 0.692913 |

Las proporciones geológicas parecen conservar buena parte del balance territorial de esta receta. Solo textura/fase mejora interpolación/perfil, pero pierde municipal y espacialmente; por ello las dos variables por sí solas no sustituyen claramente al gate completo. No se infiere causalidad: las proporciones geológicas pueden funcionar como diferenciadores regionales.

Conservar solo las10 proporciones reduce el total de33 a28 campos. Sus cambios frente al control son−0.000357 / +0.002220 / +0.002190 / +0.000951. Es una candidata de simplificación del gate con pérdidas observadas pequeñas, distinta de reducir el experto. Sigue usando SoilGrids dentro del local; no se ejecutó aquí la combinación de este gate reducido con el experto9/10.

Su diferencia espacial cambia al omitir bloques, entre−0.004260 y+0.006011; la cifra total pequeña no prueba igualdad región por región. La reducción de campos es real, pero su suficiencia predictiva requiere confirmación independiente.

También se retiró cada bloque físico del gate y se añadió al corrector del experto, manteniendo el resto. Textura/fase trasladadas consiguen0.489743 / 0.487085 / 0.578313 / 0.681482; mejoran espacialmente frente al gate que simplemente las omite, pero no los otros tres protocolos. Las proporciones trasladadas al corrector llegan a0.469313 por perfil, junto con0.618913 municipal y0.727734 espacial. Ese mínimo por perfil no justifica promoverlas. Las distancias trasladadas obtienen0.492118 / 0.490931 / 0.573857 / 0.695135, con compromisos similares.

## Selección automática frente a configuración fija

SELECT_MIN_RMSE elige ruta y K dentro de cada entrenamiento externo. SELECT_COMPACT_001 admite rutas a≤0.01t/ha del mejor RMSE interno y prefiere menos campos. La tolerancia fue congelada; no es equivalencia estadística.

| Pipeline | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| Control fijo BASE12_BOTH, solo K interno | 0.487979 | 0.487873 | 0.580981 | 0.684253 |
| Selector de menor RMSE interno | 0.488993 | 0.473971 | 0.624930 | 0.734772 |
| Selector con preferencia por menos campos | 0.490726 | 0.494052 | 0.621903 | 0.734772 |

El selector compacto elige MEAN_GLOBAL de6 campos en39/50 entrenamientos aleatorios, pero no mantiene transferencia municipal/espacial. Los dos selectores coinciden en sus decisiones espaciales: MEAN_GLOBAL en3 folds, GATE_NO_SHARES en1 y PHYS_CORRECT_SHARES en1. Empeoran frente al control aun omitiendo cualquiera de los cinco bloques espaciales del cálculo. No es solo el bloque3. Este resultado debilita la utilidad de ampliar automáticamente el menú con estos datos y este procedimiento interno; no demuestra que toda selección interna sea inútil.

## Regiones, calibración e intraperfil

La pequeña mejora espacial de retirar SoilGrids sobrevive a omitir cualquiera de los cinco bloques: cambios deRMSE de−0.001542 a−0.003726 sin reajustar. Su cambio municipal puede cambiar de signo al omitir algunos folds; no se presenta como ganancia municipal consolidada. En municipal, Calpulalpan cambia de0.475875 a0.470250, Chignahuapan de0.579937 a0.579839 y Singuilucan de0.882247 a0.887665. No es una mejora universal por municipio.

Trasladar SoilGrids al corrector empeora Singuilucan hasta1.106068; el selector también elige esa ruta al dejarlo fuera, por lo que parte del deterioro municipal procede de ese caso territorial, no principalmente de Chignahuapan. Los errores espaciales de los selectores aumentan especialmente en los bloques1 y3. Se mantienen los casos influyentes, sin reajustes dirigidos a ellos.

El R² de retirar SoilGrids es0.669619 / 0.666570 / 0.531132 / 0.354978; MAE0.347872 / 0.345141 / 0.460209 / 0.530009. El sesgo espacial baja de+0.305100 a+0.292841t/ha, mientras la varianza de errores aumenta de0.375117 a0.378160: la pequeña ganancia deRMSE procede de menor sesgo, no de menor dispersión. Retirar MSI histórico tieneR²0.670093 / 0.670152 / 0.530562 / 0.349441.

Intraperfil: al retirar MSI histórico, RMSE con igual peso por perfil pasa de0.579284 / 0.531804 / 0.523697 / 0.532478 a0.577593 / 0.530997 / 0.523625 / 0.532006. Son cambios pequeños, no una solución a la heterogeneidad entre parcelas. Retirar SoilGrids no mejora uniformemente ese criterio: municipal pasa a0.525753 frente a0.523697. Se entregan también métricas con peso por par; los pares no son observaciones independientes.

## Decisión y alcance de lo aprendido

1. Mantener C-T3 y las mezclas anteriores como referencias. Ninguna promoción automática.
2. Conservar como candidatas fijas DROP_HISTORY_WATER (experto10,31 campos totales), DROP_SOIL (experto9,30 totales) y GATE_ONLY_SHARES (experto12, gate10,28 totales). La primera preserva más estrechamente las cuatro métricas; la segunda reduce una entrada adicional y mejora ligeramente espacial a costa de perfil; la tercera elimina cinco campos del gate con pérdidas observadas de hasta0.002220t/ha.
3. Mantener MEAN_BOTH como control de complejidad mínima del experto:21 campos totales, con pérdida por perfil explícita.
4. No añadir SoilGrids al corrector del experto ni adoptar los selectores amplios para producción a partir de estos resultados.
5. Una siguiente comparación acotada podría retirar conjuntamente MSI histórico y SoilGrids, dejando7 entradas locales, frente a los controles9/10/12 y media de vecinos, con el mismo gate. **Esa combinación conjunta no se ejecutó aquí:** las retiradas individuales no garantizan que sus efectos se sumen. Tampoco se probaron las4,096 subcombinaciones posibles ni se identificaron efectos individuales causales.

Si el objetivo operativo es transferencia a territorios nuevos, C-T3 conservaRMSE espacial0.678778, ligeramente menor que las candidatas simplificadas. La justificación de estas mezclas sigue siendo ganar aleatoria/perfil manteniendo errores territoriales cercanos al compacto, no superarlo de forma uniforme.

## Reproducción y entrega

- Diseño: `documentation/signal_role_allocation_design.md`, `frozen_design.json`.
- Preparación441, ejecución442, análisis443 y auditoría444 en `scripts/`; implementación `src/signal_role_allocation.py`.
- Tres pruebas previas aprobadas en `tests/test_signal_role_allocation.py`: retirada/traslado e invariancia a etiquetas externas; identidad de representación física y categorías nuevas; transformaciones ajustadas solo en entrenamiento.
- Se preservan modelos por fold, checkpoints reanudables, predicciones OOF y decisiones internas. `role_input_inventory.csv` enumera cada campo por función; `selector_choices.csv` documenta elecciones.
- Libro `resultados_composicion_y_roles.xlsx`: métricas, recuperación por función, pérdidas frente al control, contrastes, cantidades, inventarios, pesos, regiones, omisiones e intraperfil.
- `manifest.json`, `delivery_audit.json` y `audit/` contienen comprobaciones definitivas de reproducción, separación y hashes. Los intervalos bootstrap5000 son exploratorios de OOF fijas, con43 perfiles TRAIN,9 municipios y5 bloques; no incorporan toda la búsqueda histórica ni incertidumbre de reajuste.

El entrenamiento tardó947.4s de reloj. Se registraron cuatro advertencias ambientales de convivencia de bibliotecas OpenMP, sin advertencias de convergencia durante la ejecución. Se mantiene el fallback congelado de base local sin corrector en contextos profundos con grupos/parcelas insuficientes, sin sustituir por CV aleatoria. Esto limita la comparabilidad de tamaños de entrenamiento entre niveles y la interpretación de los pesos.

La auditoría completó2,015 reproducciones de modelos por fold, con diferencia máxima0, y292,898 comprobaciones de exclusión. Se conservan60,996 filas OOF:53,820 nuevas y7,176 de referencia. Hay765 usos del fallback en cachés profundas (51 contextos por15 variantes:21 municipales y30 espaciales), no765 fallos de evaluación externa. Las referencias recuperadas y las decisiones de los dos selectores se comprueban adicionalmente en la auditoría444.

Outputs permanece excluido de Git. No se hizo push, no se escribieron archivos del otro repositorio y no se generaron nuevas predicciones finales.
