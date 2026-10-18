> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Geografía con el núcleo compacto: prueba acotada terminada

**Sí hay una razón para continuar, pero en una línea pequeña.** La localidad se puede aprovechar con cuatro variables sin PCA. Sin embargo, la Ridge local pura conserva los problemas de transferencia de Local04D. La mezcla contraída hacia C-T3 es más equilibrada, con ganancias pequeñas; el control Ridge global mejora municipalmente sin usar geografía y debe mantenerse como referencia. No se promueve un ganador ni se cambian las59 predicciones finales.

[Excel de comparación](../outputs/modeling/compact_geography/v1/geografia_compacta_resultados.xlsx), [métricas completas](../outputs/modeling/compact_geography/v1/diagnostics/metrics_summary.csv), [figura](../outputs/modeling/compact_geography/v1/diagnostics/compact_geographic_comparison.png), [estadística pareada](../outputs/modeling/compact_geography/v1/diagnostics/paired_cluster_tests.csv).

## Diseño congelado y ejecutado

Se evaluaron siete variantes en los65 folds externos originales con sus particiones internas y en las16 máscaras97/41 originales de GeoC. Las entradas predictivas son exclusivamente las cuatro de C-T3: total de lluvia, fracción temprana, HHI y NDVI mayo. La geometría procede de las coordenadas originales y distancias normalizadas de GeoC; **no se usan los scores PCA ni las2,082 variables C4** en las siete variantes nuevas. La normalización geográfica histórica usa localizaciones X conocidas; la imputación y el escalado de las cuatro variables se reajustan solo con TRAIN.

ConditionalFeatures conserva el piso original de escala NDVI. Los parámetros Ridge son alpha de sklearn sin dividir por n; se conservan los pesos originales 1/(distancia_normalizada+1e-6)^power, sin renormalizarlos a media1. Así, el efecto de alpha cambia con pesos y tamaño de vecindario; se selecciona internamente, no se considera idéntico al de Elastic Net.

| Variante | Definición |
|---|---|
| GLOBAL_RIDGE4 | Ridge global de las mismas cuatro variables; control de cambiar Elastic Net por L2 |
| LOCAL_FIXED4 | Ridge local k24, alpha30, potencia1; control cercano a Local04D sin PCA |
| LOCAL_TUNED4 | Ridge local con k12/24/36, alpha1/10/30/100 y potencia0/1 |
| BLEND_LOCAL4 | C-T3 + w × (Ridge local4 − C-T3) |
| SUPPORT_BLEND4 | La mezcla anterior multiplicada por un factor de soporte geográfico |
| NN_RESIDUAL | C-T3 + w × promedio ponderado de residuos honestos de vecinos |
| NN_SUPPORT | Corrección vecinal anterior multiplicada por soporte |

En mezclas y correctores w pertenece a [0,.25,.5]; cero devuelve exactamente C-T3. Se seleccionan conjuntamente parámetros locales y w mediante MSE de OOF internas completas; empates a doce decimales favorecen menor w y el orden conservador congelado. El modelo fijo no usa validación para elegir sus parámetros. La rejilla no se amplió después de ver resultados.

Soporte(q) = min(1, mediana TRAIN de distancia al k-ésimo vecino excluyendo la propia parcela / distancia del objetivo a su k-ésimo vecino TRAIN), con piso1e-6. No utiliza rendimientos ni reglas por estado/municipio. Es una heurística de soporte, no probabilidad de acierto o garantía frente a extrapolación. En todas las consultas se excluyen TODOS los objetivos retenidos del conjunto de vecinos etiquetados.

Los targets correctores son errores de C-T3 generados fuera de muestra. Para seleccionar el corrector dentro de un entrenamiento interno, otra capa excluye cada etiqueta residual tanto del ajuste como de la selección de la base C-T3. Se reutilizan contextos originales admisibles; en97/41 se generan y guardan nuevas bases profundas restringidas a las etiquetas permitidas. Persiste el desajuste de tamaño entre bases cross-fitted y bases reajustadas.

## Resultados:65 folds originales

RMSE en t/ha. Aleatoria promedia métricas sobre diez OOF completas; los otros protocolos usan138 OOF. No se comparan medias de folds con métricas completas.

| Modelo | Aleatoria | Perfil | Municipal | Espacial |
|---|---:|---:|---:|---:|
| C-T3 original | .511582 | .520604 | .581259 | .678778 |
| Local04D original, referencia PCA20 | .492957 | .503052 | .760246 | .979401 |
| GLOBAL_RIDGE4 | .512299 | .518008 | .556108 | .679305 |
| LOCAL_FIXED4 | .497047 | .505619 | .748816 | .980191 |
| LOCAL_TUNED4 | .501418 | .515390 | .688783 | 1.108190 |
| BLEND_LOCAL4 | .493515 | .481938 | .619570 | .682437 |
| SUPPORT_BLEND4 | .504034 | .516660 | .577981 | .681186 |
| NN_RESIDUAL | .499740 | .514149 | .580764 | .763567 |
| NN_SUPPORT | .507929 | .516252 | .579841 | .729762 |

### La localidad no necesita toda la representación grande

LOCAL_FIXED4 queda cerca de Local04D: diferencias+.004090 aleatoria,+.002567 por perfil,-.011430 municipal y+.000790 espacial. Es evidencia descriptiva de que una representación de cuatro variables reproduce gran parte del comportamiento del método local. No es una prueba formal de equivalencia y cambia el escalado de la representación además de su dimensión. Ambos modelos locales puros siguen transfiriendo mal fuera de sus vecindarios.

Seleccionar k/alpha/potencia no resolvió ese límite: LOCAL_TUNED4 tiene peor resultado espacial,1.108190. Una validación interna correcta reduce contaminación, pero no garantiza anticipar los errores de extrapolación externa.

### Mezcla más equilibrada, pero ganancia pequeña

SUPPORT_BLEND4 mejora C-T3 en aleatoria-.007548, perfil-.003944 y municipal-.003278, con deterioro espacial+.002408. Es una sensibilidad razonable para continuar, no una mejora demostrada o un sustituto listo. Su selección conjunta cambia parámetros y pesos respecto a BLEND_LOCAL4; no se atribuye causalmente todo el cambio al factor de soporte.

BLEND_LOCAL4 logra mejoras mayores aleatoria/perfil, pero pierde+.038311 municipal. Las dos mezclas seleccionan peso cero en3/5 folds espaciales. El mecanismo ayuda a limitar exposición local, sin eliminar por completo las pérdidas externas.

### Parte del beneficio no es geografía

GLOBAL_RIDGE4 reduce RMSE municipal de .581259 a .556108 (-.025151) sin vecinos, con diferencias pequeñas en los otros protocolos. Es mejor municipalmente que todas las variantes geográficas nuevas. SUPPORT_BLEND4 frente a este control mejora aleatoria aproximadamente.008265 y por perfil.001348, pero empeora municipal.021873 y espacial.001881. No afirmar que la geografía aporta una mejora equilibrada simplemente comparando todo contra C-T3 Elastic Net.

### Correcciones de residuos por vecinos

NN_RESIDUAL mejora aleatoria y por perfil, cambia muy poco municipal y empeora espacial+.084789. El soporte reduce ese costo espacial a+.050984 en NN_SUPPORT, pero sigue siendo apreciable. No se recomienda integrar estas correcciones ni aumentar su complejidad con los resultados actuales.

## Banco GeoC97/41, separado

Son16 máscaras originales de desarrollo,656 predicciones repetidas sobre125 parcelas. La métrica de esta tabla es RMSE pooled, no media de los16 RMSE. No es el banco08 ni prueba independiente de una nueva campaña.

| Modelo | RMSE pooled | MAE pooled |
|---|---:|---:|
| C-T3 | .528906 | .378042 |
| Local04D original | .495741 | .342501 |
| GLOBAL_RIDGE4 | .527914 | .376868 |
| LOCAL_FIXED4 | .501748 | .344169 |
| LOCAL_TUNED4 | .513096 | .360836 |
| BLEND_LOCAL4 | .506200 | .349234 |
| SUPPORT_BLEND4 | .523507 | .370902 |
| NN_RESIDUAL | .512794 | .359093 |
| NN_SUPPORT | .524229 | .373010 |

Ninguna variante nueva supera el punto estimado de Local04D original en esta tarea. LOCAL_FIXED4 se aproxima con muchas menos entradas, pero la diferencia .006007 t/ha no se considera equivalencia demostrada. La mezcla conservadora que reduce daño territorial sacrifica parte de la ventaja local en este banco. El compromiso depende del objetivo de uso.

## Regiones, soporte e intraperfil

Municipalmente SUPPORT_BLEND4 mejora Chignahuapan .580680→.563749 y Calpulalpan .493347→.481850, pero empeora Singuilucan .867689→.928724. GLOBAL_RIDGE4 mejora Singuilucan a.758805 y obtiene.577259 en Chignahuapan. No se combinan estas ventajas creando reglas por municipio: sería selección externa retrospectiva.

Las24 o36 referencias nominales no son24 o36 unidades independientes. Se guardan número efectivo de vecinos por pesos y diversidad de perfiles. Por ejemplo, SUPPORT_BLEND4 tiene mediana aleatoria de9.4 vecinos efectivos y5 perfiles entre sus vecinos activos. Las medianas de soporte se calculan solo cuando el componente está activo; no se interpretan como cobertura de todas las parcelas o como calibración de confianza.

Intraperfil aleatorio, SUPPORT_BLEND4 mejora ligeramente la ponderación equilibrada por perfil .589951→.587143 pero empeora por pares .771183→.777917. Espacialmente ocurre algo similar: .540147→.537786 por perfil y .767538→.770251 por pares. No se demostró una mejora local consistente con ambas ponderaciones. BLEND_LOCAL4 sí mejora ambos indicadores espaciales, .535820/.763596, pero no conserva ambos beneficios en aleatoria y los otros protocolos. No se trata a las parejas como observaciones independientes.

Las tablas contienen RMSE, MAE, sesgo y R2, errores por estado/municipio/bloque, omisiones de regiones sin reajuste, selección interna, ganancias por parcela y los mayores deterioros. Los resultados agregados no sustituyen esos diagnósticos.

## Estadística

Se realizaron35 contrastes contra C-T3: siete variantes × cinco protocolos/bancos. Bootstrap5,000 por perfiles, municipios o bloques; pruebas de signos de pérdida cuadrática y Holm dentro de esta batería. Se conservan juntas las repeticiones de una parcela y los conglomerados; no se tratan65 folds o16 splits como muestras independientes. No se corrige toda la búsqueda histórica ni se incorpora incertidumbre de volver a entrenar. Los perfiles pueden conservar dependencia espacial y solo hay cinco bloques.

En los65 folds, ninguna variante resiste Holm a.05. BLEND_LOCAL4 por perfil tiene p ajustado.095195, aunque su IC percentil de delta RMSE es[-.090500,-.014194]; el intervalo no tiene corrección de multiplicidad. SUPPORT_BLEND4 presenta intervalos de delta[-.034399,.003336] aleatoria,[-.011127,.000401] perfil,[-.027674,.038019] municipal y[0,.006936] espacial. No se declara superioridad estadística.

NN_RESIDUAL frente a C-T3 en97/41 conserva p Holm.038498 bajo estas hipótesis exploratorias, pero su RMSE.512794 sigue peor que Local04D.495741 y su costo espacial es grande. La significación en ese contraste no justifica integración ni una conclusión de transferencia general. No se afirma equivalencia a partir de pruebas no significativas.

## Decisión: continuar solo con una pregunta pequeña

1. Conservar **GLOBAL_RIDGE4** como control compacto fuerte: mejora municipal sin adquirir complejidad geográfica.
2. Conservar **SUPPORT_BLEND4** como candidato exploratorio para estudiar el compromiso entre reconstrucción local y transferencia, comparándolo también contra Ridge global, no solo contra C-T3.
3. Detener por ahora Ridge local pura y las correcciones de residuos vecinos como línea de promoción: tuning y soporte no han producido equilibrio territorial suficiente.
4. No ampliar k, fuentes, PCA ni reglas regionales retrospectivamente. Antes de otra exploración grande, decidir si la prioridad es reconstruir las59 parcelas fijas o transferir a territorios ausentes y confirmar en datos independientes cuando existan.

No se recomienda reemplazar automáticamente las59 predicciones actuales. Si la prioridad es únicamente el reto fijo, Local04D sigue siendo una referencia más competitiva en su banco específico; la simplicidad de cuatro variables es útil, pero no demuestra menor error en las59 etiquetas desconocidas.

## Reproducibilidad

Se guardaron17,150 OOF nuevas y567 predictores externos. Se recargaron y reprodujeron exactamente todos los567, con diferencia máxima cero. Se verificó la exclusión de etiquetas en contextos residuales; las fuentes y modelos previos conservaron hashes. Tres pruebas pasaron: Ridge vectorizada contra sklearn ponderado, exclusión de vecinos objetivo y comportamiento del soporte fuera de entrenamiento. Cero advertencias de ajuste; se registró la advertencia operacional Intel/LLVM OpenMP, sin fallos de reproducción.

Implementación: `src/compact_geographic.py`; scripts418/419; diseño congelado `outputs/modeling/compact_geography/v1/frozen_design.json`. Se guardan modelos, targets correctores, bases profundas nuevas de97/41, procedencia, selección, diagnósticos y estadísticas. No se modificó GeoC, modelo TOP20/TOP15, C-T3, los138 rendimientos ni se ajustó un modelo final de138 etiquetas o se generaron nuevas59 PRED. El experimento fue de evaluación, no una nueva entrega final.
