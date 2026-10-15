# Complementos de C-T3 y EN_CAL02: diseno congelado

Autorizacion: ejecutar los complementos de modelado propuestos, conservando C-T3 y las referencias anteriores. Configuracion mecanica previa al entrenamiento: `outputs/modeling/agronomic_calendar/complements/v1/frozen_design.json`. Esta bateria no repite los correctores LAI/contexto anteriores ni ejecuta nuevos CatBoost, modelos finales o PRED.

## Representaciones y controles

Todas usan Elastic Net, mediana y escalado ajustados solo en entrenamiento. Grid identico al de la expansion anterior: alpha [1,.1,.01,.001], l1_ratio [1,.9,.5,.1]. Los controles compact4 y CAL02 deben reproducir EN_CAL00 y EN_CAL02; no se presentan como nuevos experimentos independientes. C-T3 original se recupera sin retunear y se distingue del control compact4, cuya seleccion interna difiere del protocolo original C-T3.

| Nombre | Entradas | Pregunta |
|---|---|---|
| COMPACT4 | Lluvia total, fraccion temprana, HHI, NDVI mayo | Control de procedimiento |
| CAL02 | Cuatro lluvias, cuatro Tmax y NDVI mayo | Control de ventanas |
| WINDOW_SHAPES7 | Cuatro lluvias, fraccion temprana, HHI y NDVI mayo | Valor de las transformaciones compactas sin temperatura |
| UNION11 | CAL02 + fraccion temprana + HHI | Complementariedad completa, omitiendo total redundante |
| COMPACT_TMAX8 | Compact4 + cuatro Tmax | Temperatura sin cambiar la representacion de lluvia |

SELECTED_BASE escoge representacion e hiperparametros dentro de cada entrenamiento por RMSE de OOF internas completas. No se elige una base global mirando los resultados espaciales. Los empates a 12 decimales favorecen el orden conservador congelado.

## Correccion residual acotada

Sobre SELECTED_BASE se comparan cinco correctores por separado, sin sumar sus efectos ni elegirlos retrospectivamente:

- VEG_RIDGE: NDVI, EVI, NDWI y MSI en cuatro ventanas, mas heterogeneidad NDVI de julio-agosto (17 entradas).
- VEG_CONTEXT_CART: esas 17 entradas mas fraccion temprana, HHI y NDVI mayo (20 entradas).
- CONTEXT_CART: las tres entradas de contexto anteriores; control para distinguir vegetacion adicional de recalibracion del nucleo.
- SLOPE_RIDGE: pendiente media, control secundario.
- HISTORY_RIDGE: las dos variables historicas NDVI heredadas, control secundario. Su dispersion conserva la definicion original; no se renombra como variabilidad interanual.

Ridge sin intercepto: penalizacion normalizada [1,.1,.01]. CART: profundidad [1,2], hojas minimas [25,15], sin nuevas reglas territoriales. Se centra la prediccion correctora de entrenamiento. Amplitud [0,.25,.5], elegida internamente, empate a favor de cero y menor amplitud. No hay desplazamiento constante independiente. El control sin vegetacion es necesario porque una ganancia de un arbol contextual no demuestra aporte satelital.

## Exclusiones y limites

Se conservan los 65 folds externos y sus particiones internas originales. Dentro de cada entrenamiento se selecciona la base; los residuos de calibracion se generan con bases cuyos ajustes Y selecciones excluyen cada observacion objetivo. Para evaluar correctores en un fold interno, sus residuos de ajuste se generan mediante otra capa interna. Las nuevas subparticiones usan KFold semilla 2026 o GroupKFold del mismo protocolo; nunca se sustituye validacion agrupada por aleatoria.

El desajuste entre bases cross-fitted pequenas y la base reajustada con todo el entrenamiento externo permanece y se declara: no se atribuyen sus efectos a un mecanismo causal. No se utilizan residuos del Champion ni rendimientos externos para tunear. Cero implica exactamente SELECTED_BASE, no necesariamente C-T3.

Las metricas se calculan sobre OOF completas por repeticion; se promedian las diez repeticiones aleatorias. Se entregan MAE, RMSE, sesgo, R2, diferencias pareadas, regiones, omisiones sin reajuste, intraperfil con ambos pesos, frecuencia de seleccion y reproduccion de modelos guardados. No se interpretan repeticiones o pares como muestras independientes ni se declara superioridad estadistica. La reutilizacion de las mismas etiquetas hace exploratoria toda la bateria.

Cuatro pruebas comprueban centrado, transformaciones exclusivas de entrenamiento, integridad de grupos y exclusiones en generacion de residuos. La prueba temporal de pytest requirio una carpeta temporal nueva dentro del workspace porque la carpeta temporal global de pytest no era accesible; las cuatro pasaron sin cambiar el pipeline.
