# Cuatro investigaciones finales — entrega, soporte, intervalos y HHI

**Los únicos champions siguen siendo Reference26 y Compact14.** Se preservaron los modelos y las59 predicciones finales por SHA256. La sensibilidad Reference25_NoHHI es una candidata experimental; no sustituye automáticamente a26. Las59 etiquetas siguen desconocidas.

## 1. Entrega congelada y reproducción

Los archivos de ambos champions contienen59 IDs únicos, coincidentes con el conjunto esperado, valores finitos/positivos y las mismas predicciones que la comparación conjunta. Se generaron copias locales de presentación con encabezado `ID_parcela` y rendimiento en t/ha, sin envío externo. La reproducción se ejecutó en proceso y venv aislados, con barrera de lectura que impide acceder a otros datos privados fuera del paquete final.

Reproducción en venv que comparte paquetes instalados: **passed**. Intento adicional de instalación limpia, sin paquetes compartidos: **passed**. [Auditoría operativa](operational_audit.json) · [Instalación limpia](clean_environment_audit.json). Un resultado en Windows no demuestra portabilidad a otros sistemas.

La instalación limpia reprodujo las59 estimaciones dentro de1e-10t/ha con versiones fijadas. Los requisitos efectivos están en [replay_requirements.txt](../../../configs/four_final_checks/v1/replay_requirements.txt).

## 2. Soporte de las59 parcelas

Se usan distancias sin objetivo, umbrales95% de referencias de entrenamiento y disponibilidad de indicadores. No se ajustan modelos con las59 ni se usan sus etiquetas. Un aviso de soporte es diagnóstico, **no probabilidad de fallo ni evidencia de que la estimación sea incorrecta**.

| Región | n | R3 incompleto | Geografía fuera q95 | Núcleo4 fuera q95 | Local7 fuera q95 | Geología nueva | Desacuerdo26–14 elevado | Algún aviso |
|---|---|---|---|---|---|---|---|---|
| all | 59 | 8 | 1 | 2 | 2 | 0 | 0 | 11 |
| Hidalgo | 15 | 4 | 1 | 0 | 0 | 0 | 0 | 5 |
| Puebla | 29 | 4 | 0 | 0 | 0 | 0 | 0 | 4 |
| Tlaxcala | 15 | 0 | 0 | 2 | 2 | 0 | 0 | 2 |

Los avisos pueden coincidir en la misma parcela; no se suman como casos distintos. Los ocho R3 incompletos conservan la predicción de base sin esa corrección, conforme a la receta. El bajo desacuerdo26–14 no garantiza acierto compartido. La tabla privada `support59.csv` contiene IDs, municipios y distancias para el dashboard.

## 3. Intervalos: cobertura observada y límites

Se evaluaron niveles80% y90% con modelos OOF ya congelados. Cada fold externo se divide sin mirar Y en dos mitades: una calibra residuos absolutos y la otra evalúa; se intercambian después sus funciones. Una parcela no usa su propia etiqueta para calibrar su intervalo. El radio usa el estadístico de orden `ceil((m+1)·nivel)`; si no existe ese orden, se conserva radio infinito, sin inventar un límite finito.

**Diagnóstico principal: aleatorio, separación por parcelas, nivel nominal90%.**

| Modelo | Cobertura observada | Ancho medio t/ha | Intervalos finitos |
|---|---|---|---|
| Reference26 | 92.90% | 2.085 | 100.0% |
| Compact14 | 92.97% | 2.120 | 100.0% |

Las mitades de calibración pequeñas hacen que el90% nominal sea conservador. La cobertura se acompaña de intervalos amplios: no equivale a gran precisión parcelaria. Los resultados por estado están en [interval_metrics_by_state.csv](interval_metrics_by_state.csv); la cobertura marginal no asegura cobertura por cada estado o parcela.

**Advertencia de dependencia:** al separar perfiles completos y calibrar máximos por perfil, hay pocos grupos. Para90%, sólo≈4.7% de los casos aleatorios tienen intervalos finitos; una cobertura cercana a100% con radios infinitos no es un éxito útil. Esto muestra el límite de138 observaciones agrupadas, no un método listo para prometer certidumbre territorial.

Los protocolos municipal/espacial se incluyen como diagnósticos, pero su calibración utiliza algunas etiquetas del territorio externo: **no certifican transferencia a un territorio sin ninguna etiqueta disponible**. El banco97/41 se mantiene separado. [Tabla completa](interval_metrics.csv) · [Auditoría](interval_audit.json).

**No se atribuye un intervalo garantizado a la predicción final del modelo entrenado con138.** La cobertura se midió para modelos retenidos y una calibración separada. Reentrenar con todas las138 y trasladar esos anchos sin validar sería otra receta. Las etiquetas se han reutilizado históricamente y la intercambiabilidad no está garantizada por perfiles o espacio. Referencia: [MAPIE, split y cross-conformal y sus supuestos](https://mapie.readthedocs.io/en/stable/content/conformal-prediction/split-cross-conformal/).

## 4. Reference25_NoHHI: retiro de HHI en sus dos usos

Se eliminó físicamente HHI de las entradas: la base y el corrector interno usan lluvia total, fracción temprana y NDVI mayo. Se mantuvieron experto7,24 vecinos, Ridge30, geología10 y K4/8, rejillas Elastic Net e intensidad/soporte R3. Cada capa se recalibró dentro del entrenamiento externo, con las65 particiones e internas originales. No se reajustó el campeón final ni se generaron59 predicciones para la candidata.

Antes de entrenar la sensibilidad, el adaptador de26 sin cambios reprodujo los controles aleatorio0 y espacial63 con diferencia máxima inferior a1e-10t/ha. Los trabajadores están aislados: configurar tres entradas no altera módulos o modelos históricos en disco. [Diseño congelado](../../../configs/four_final_checks/v1/frozen_design.json).

Los65 folds completaron la verificación de exclusión de entrenamiento/evaluación; advertencias de convergencia: **0**. Se registraron advertencias ambientales, sin ocultarlas: `{'RuntimeWarning': 65}`. El detalle permanece en cada checkpoint privado y los tiempos en [auditoría de ejecución](sensitivity_execution_audit.csv).

Cada celda es **RMSE t/ha / R²**. Se promedian métricas de OOF completas por repetición.

| Modelo | Aleatoria | Perfil | Municipal | Espacial |
|---|---|---|---|---|
| Reference26 | 0.4748 / 0.6865 | 0.4774 / 0.6831 | 0.5752 / 0.5400 | 0.6333 / 0.4423 |
| Reference25_NoHHI | 0.4748 / 0.6865 | 0.4743 / 0.6872 | 0.5982 / 0.5025 | 0.5328 / 0.6053 |
| Compact14 | 0.4773 / 0.6832 | 0.4793 / 0.6805 | 0.5755 / 0.5395 | 0.6431 / 0.4250 |
| CT3 | 0.5116 / 0.6361 | 0.5206 / 0.6232 | 0.5813 / 0.5302 | 0.6788 / 0.3594 |

### Comparaciones pareadas contra26

Delta negativo favorece la candidata sin HHI; positivo favorece26. Holm cubre los cuatro contrastes primarios. Los IC95% son bootstrap5000 por grupos sobre OOF fijas, no incertidumbre del reajuste ni confirmación independiente.

| Protocolo | Delta RMSE sinHHI−26 | IC95% OOF fijas | p Holm4 |
|---|---|---|---|
| climate_profile | -0.0031 | [-0.0119, +0.0009] | 0.75376 |
| municipality | +0.0230 | [-0.0733, +0.0705] | 1 |
| random | -0.0000 | [-0.0034, +0.0016] | 1 |
| spatial | -0.1005 | [-0.2608, +0.0293] | 1 |

Los grupos de inferencia son perfiles para aleatoria/perfil, municipios para municipal y bloques para espacial. La enumeración de signos presupone condiciones de simetría/independencia de grupos; cinco bloques dan escasa resolución estadística. La corrección no elimina la selección histórica previa. [Pruebas](sensitivity_paired_tests.csv) · [MAE, sesgo y métricas](sensitivity_metrics.csv) · [Regiones](sensitivity_regional_metrics.csv) · [Omisiones sin reajustar](sensitivity_omission_metrics.csv).

La candidata mejora puntualmente en: climate_profile, random, spatial. Empeora en: municipality. No se declara un nuevo champion a partir de esta comparación. El resultado de retirar HHI de C-T3 no se traslada automáticamente al sistema compuesto; ésta es su comprobación en la arquitectura completa.

**Recomendación:** conservar26/14 como entrega vigente. Retirar HHI representa un intercambio entre protocolos y no una sustitución que domine a26. La credibilidad aumenta al documentar esa sensibilidad, no al ocultar el protocolo que empeora. Una decisión de cambio requeriría un criterio de uso declarado y evidencia adicional; estos resultados reutilizan las mismas138 etiquetas.

### Distribución espacial de la diferencia

| Bloque | RMSE26 | RMSE sin HHI | Delta |
|---|---|---|---|
| 0 | 0.5347 | 0.5505 | +0.0157 |
| 1 | 0.8029 | 0.4730 | -0.3300 |
| 2 | 0.5505 | 0.2951 | -0.2554 |
| 3 | 0.6765 | 0.7527 | +0.0762 |
| 4 | 0.5366 | 0.4885 | -0.0481 |

Los bloques son conjuntos geográficos de validación; se conservan sus etiquetas0–4 del artefacto original, sin renumerarlos. Esta descomposición no seleccionó hiperparámetros ni reglas regionales. Las omisiones publicadas recalculan métricas sin un grupo, sin reajustar modelos. No convierten el resultado externo en confirmación independiente.

La mayor contribución a la reducción neta de error cuadrático espacial proviene del bloque **1**: equivale al **91.1%** de esa reducción neta, después de compensar bloques que empeoran. Al omitir ese bloque del cálculo, el delta RMSE sinHHI−26 es **-0.0125t/ha**. Es una medida de concentración del beneficio, no porcentaje de parcelas beneficiadas.

### Distribución municipal

| Municipio | RMSE26 | RMSE sin HHI | Delta |
|---|---|---|---|
| Almoloya | 0.3468 | 0.2582 | -0.0886 |
| Apan | 0.3392 | 0.4463 | +0.1071 |
| Calpulalpan | 0.4166 | 0.5363 | +0.1196 |
| Chignahuapan | 0.5807 | 0.6162 | +0.0356 |
| Cuautepec de Hinojosa | 0.4835 | 0.3591 | -0.1244 |
| Emiliano Zapata | 0.5162 | 0.4540 | -0.0622 |
| Nanacamilpa de Mariano Arista | 0.5986 | 0.2032 | -0.3954 |
| Singuilucan | 0.8850 | 0.8477 | -0.0373 |
| Tepeapulco | 0.5801 | 0.3539 | -0.2262 |

Un cambio de RMSE municipal en municipios pequeños tiene escaso soporte. Estas tablas describen el intercambio territorial y no justifican seleccionar modelos distintos por municipio con sus mismos residuos externos.

![Sensibilidad y rangos de variación](NoHHI_delta_RMSE.png)

## Entrega y uso recomendado

Para el dashboard, mostrar predicción y componentes junto con disponibilidad histórica, distancia al soporte y avisos descriptivos. No convertir avisos o desacuerdo en probabilidades de error, ni anunciar intervalos garantizados para59. La sensibilidad se presenta como investigación adicional y los champions permanecen26/14 hasta una decisión explícita.

Excel privado: `outputs/research/four_final_checks/v1/cuatro_investigaciones.xlsx`; contiene resultados, soporte por ID, regiones y candidatos OOF. Copias de presentación59 en `submission/` dentro de esa carpeta; no se enviaron externamente. [Auditoría de cierre](complete_audit.json) · [Configuración](../../../configs/four_final_checks/v1/frozen_design.json). Scripts535–539 reproducen la ejecución; las operaciones nuevas se guardaron separadas de los artefactos previos.

## Reproducción local

Requiere los artefactos privados del proyecto. Mantener los archivos de configuración congelados y sus enmiendas de implementación, que registran cambios de rendimiento computacional sin cambiar decisiones estadísticas. Las seis copias finales se verifican por SHA256 antes y después.

```powershell
python scripts/535_no_hhi_reference26.py worker --mode control --fast --folds 0,63
python scripts/537_run_sensitivity_battery.py
python scripts/536_operational_support_intervals.py support
python scripts/536_operational_support_intervals.py intervals
python scripts/538_finalize_four_checks.py
```

El supervisor reanuda únicamente folds que no tienen marcador de finalización. La auditoría operativa inicial y la instalación limpia se ejecutan con `python scripts/536_operational_support_intervals.py operational` y `python scripts/539_clean_replay_environment.py`. La primera crea el registro de los archivos protegidos; conservar ese registro para auditar la misma entrega. Los modelos transitorios interiores se mantienen en memoria; cada ajuste externo final se guarda. Se comprobó paridad con la ejecución original antes de utilizar esta optimización, sin ampliar rejillas o cambiar particiones.
