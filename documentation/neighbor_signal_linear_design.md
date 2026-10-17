# Contrastes como variables continuas de corrección

Ampliación explícita solicitada durante la exploración: usar la diferencia respecto al grupo como variable continua en lugar de depender de cortes de un árbol. Se conservan las cuatro variantes de árboles como comparación, sin modificar su diseño ni sus resultados.

Se añaden GEO_LINEAR y COMPACT_LINEAR sobre J7_BOTH. Son las mismas seis variables de contraste de las tres señales: diferencias con la mediana de vecinos en unidades locales robustas y en unidades de dispersión del entrenamiento. Los vecinos se eligen con geografía o compact4, hasta k24 con empates y exclusión de la propia parcela. Una diferencia respecto a una única media general no aporta información nueva a una regresión lineal con intercepto; no se reejecuta esa parametrización redundante.

El nuevo ajuste es Elastic Net sobre residuos J7 cross-fitted, con **solo contrastes**, sin intercepto ni centrado de los contrastes. Se escala por SD del entrenamiento, se eliminan columnas constantes y se limita la corrección a ±0.5 t/ha. Por construcción, cuando todas las diferencias son cero, el ajuste es cero. No se agrega compact4 al corrector: ya está representado en la base.

Se mantiene la grilla de Elastic Net existente: alpha {0.001,0.01,0.1,1}, l1_ratio {0.1,0.5,0.9}, amplitud {0.5,1}, más no ajustar. Parámetros, soportes y escalas se seleccionan exclusivamente con las particiones internas originales. Se reusan los contextos base desde la caché del experimento de árboles en modo lectura; cada registro valida posiciones y targets de entrenamiento. Se guardan las predicciones y contrastes de calibración. La puntuación interna de la opción nula se compara contra el experimento anterior para verificar que la calibración base sea idéntica.

Evaluación: las mismas 65 particiones, OOF completas por repetición, RMSE/MAE/R²/sesgo por protocolo, regiones, intraperfil, ganancias por parcela y análisis sin 171/015. Comparar las dos variantes contra J7, entre vecindarios y contra sus correctores arbóreos correspondientes. Los nuevos contrastes estadísticos se reportan como una ampliación exploratoria distinta, con Holm sobre 20 comparaciones; no reinterpretar la batería de árboles como confirmación independiente. No se promueve Champion, ni se ajusta modelo final138, ni se generan PRED59.

Scripts 464 (ejecución), 465 (congelación previa a su entrenamiento) y 466 (evaluación). Carpeta: `outputs/modeling/neighbor_signal_linear/v1`.
