> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **champion histórico**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Líneas de investigación después de F4-E

Propuesta basada en la revisión de Familias 1–4, Champion RS6, diagnósticos F3.2.1, screening y concentración de errores de Chignahuapan. No se entrenaron nuevas arquitecturas ni se modificaron resultados anteriores. Una mezcla fija de predicciones archivadas se examinó únicamente como diagnóstico exploratorio retrospectivo.

## Evidencia que determina las prioridades

- F4-S1 lluvia+NDVI mayo tiene RMSE aleatorio 0.50483, por perfil 0.52626, municipal 0.67110 y espacial 0.73904.
- F4-E2 añade inicio de ascenso LAI: mejora pequeña de diferencias intraperfil con igual peso —0.58920→0.58335 en aleatoria—, pero no mejora RMSE global. El contraste local también aparece fuera de Chignahuapan.
- F4-S5 lluvia+variabilidad de amplitud térmica tiene RMSE espacial 0.60047, con deterioro por perfil respecto a lluvia. La fortaleza regional y la local son diferentes.
- Chignahuapan tiene 71/138 etiquetas, dos perfiles grandes de 33 y 29 parcelas y mayor error de diferencias por pareja. La validación municipal/espacial de errores por parcela es, en cambio, más difícil fuera del municipio.
- Familias 2 y 3 no aportaron mejoras claras con FPCA/SOF híbridos, factores estructurales o interacciones amplias. Sus cifras históricas usan otras agregaciones: no se comparan literalmente sus RMSE de folds con los RMSE medios de repetición de Familia 4.
- Las arquitecturas alternativas RS6 tienen residuos muy correlacionados; cambiar su orden produjo beneficios pequeños. El diagnóstico previo F3.2.1 encontró sesgos persistentes y concentración de SSE en pocas parcelas, con poca evidencia de autocorrelación espacial residual bajo su definición de vecindad.
- El suelo cartográfico grueso y el relieve medio no aportaron una mejora incremental consistente. LAI q10 es una alternativa regional menos estable que NDVI mayo.

## Paso previo: semántica y auditoría de errores

Las ecuaciones locales `docs/guidelines/Ecuaciones_indices_AgroCebada_FIRA_2026.pdf`, página1, establecen LAI=(-log((0.69−SAVI)/0.59))/0.91. Por ello, LAI no es una fuente independiente de SAVI. La fórmula da valores negativos cuando SAVI<0.10 dentro de su dominio, explicando que la negatividad no pruebe por sí sola corrupción de datos. El promedio de una transformación no lineal no equivale a la transformación del promedio: no puede verificarse exactamente esa relación entre medias parcelarias sin los valores de píxel. La fecha del máximo runup también puede cambiar bajo la transformación no lineal; su utilidad no demuestra una fase fenológica real.

El mismo PDF informa que NDDI/ENDDI usan remuestreo a8bits y que VI6T combina una banda Landsat espectral con ST_B10. Esto refuerza la necesidad de auditar implementación, escala y procesamiento antes de asignar significado físico a nuevos predictores. Esta evidencia afina la reserva interpretativa anterior sobre LAI, sin reescribir sus resultados congelados.

Auditar las parcelas de sesgo recurrente: correspondencia ID-geometría-rendimiento, fecha/cultivo del ciclo, definición de área usada en rendimiento, cobertura válida y alineación de observaciones. No eliminar ni corregir etiquetas por tener gran residuo; solo modificar con evidencia de origen, en una versión nueva. Si se corrige una fuente, congelar la regla antes de revaluar.

## 1. Objetivo explícito de diferenciación intraperfil — prioridad alta

**Pregunta:** ¿el modelo pierde señal local porque seleccionamos todos los ajustes por error global de parcela?

**Prueba mínima:** conservar lluvia+NDVI mayo y su alternativa con inicio LAI; añadir una penalización de error de diferencias dentro del perfil a la pérdida de parcelas. Cada perfil recibe igual peso en el término local. Seleccionar el peso de ese término dentro de entrenamiento interno, con criterio global/local previamente declarado.

Una propuesta es L=L_parcelas+λ·media_g[media_(i,j en g)((Y_i−Y_j)−(ŷ_i−ŷ_j))²]+regularización. Solo se construyen parejas de etiquetas pertenecientes al entrenamiento actual. La suma de diferencias puede calcularse como pérdida centrada por grupo: las parejas no crean etiquetas independientes ni nueva información. La novedad es el objetivo y la ponderación.

**Control:** misma matriz, escalas y regresor, λ=0. **Éxito:** mejorar diferencias con igual peso, fuera de Chignahuapan y por perfil; mantener RMSE/MAE de parcela dentro de margen declarado. **Descarte:** si solo redistribuye errores hacia perfiles pequeños o pierde transferencia. No usar medias globales de Y como características.

## 2. Mezcla parsimoniosa de modelos existentes — afinamiento de bajo alcance

**Pregunta:** ¿Champion y F4-S1 tienen suficiente diversidad para compensar parte de sus errores?

Un diagnóstico de predicciones archivadas compatibles, con los mismos1,380 IDs/repeticiones/folds aleatorios, encontró correlación de residuos0.938. La media fija50/50 de Champion `A_CURRENT_CH_H_T` y F4-S1 da RMSE medio de repetición0.49360 frente a0.49813 de Champion y mejora nueve de diez repeticiones. Las repeticiones no son independientes. No es una confirmación ni una búsqueda autorizada de más mezclas.

**Prueba mínima propuesta:** comparar esa media fija con ambos modelos, sin abrir una búsqueda de pesos o miembros después de ver resultados. Si se aprende un peso, aprenderlo exclusivamente con predicciones cruzadas generadas dentro de cada entrenamiento externo e interno. Los contextos de toda la arquitectura Champion deben reconstruirse para ese ajuste; sus OOF globales no sirven para entrenar un meta-modelo ni una nueva capa.

**Éxito:** mantener MAE, extremos y diferenciación además de la ganancia aleatoria. Para afirmar transferencia, reconstruir una variante completa verificable en protocolos agrupados; no existe hoy un Champion archivado compatible para municipio/espacio. **Descarte:** si la diversidad resulta demasiado pequeña o la mejora se pierde en nuevos datos. Una ganancia~0.0045 t/ha quizá no justifique mayor complejidad operativa.

## 3. Modelo jerárquico compacto — alternativa principal

**Pregunta:** ¿conviene modelar explícitamente niveles regionales y variación parcelaria en vez de ajustar una única respuesta uniforme?

**Prueba mínima:** respuesta climática de baja dimensión + efectos parcelarios de NDVI mayo y trayectoria + interceptos de perfil parcialmente agrupados mediante regularización/priores compartidos. Inicialmente sin pendientes independientes por cada perfil; la mayoría tiene muy pocas etiquetas. Un intercepto de perfil puede ajustar el nivel regional, pero no explica diferencias entre sus parcelas: esas diferencias siguen dependiendo de las variables parcelarias.

Se distinguen predicciones para nuevos miembros de perfiles conocidos y perfiles enteramente nuevos. Para un perfil nuevo se integra su efecto bajo la distribución compartida, sin estimarlo con sus Y retenidos. Los promedios de características usados en transformaciones predictivas, si se introducen, se aprenden solo en entrenamiento y necesitan una regla de perfiles nuevos.

**Control:** versión sin efectos de perfil, con iguales predictores. **Éxito:** mejor diferenciación y calibración, sin presentar la memorización de grupos conocidos como transferencia. **Riesgo:** solo43 perfiles etiquetados y12 con varias parcelas; limitar parámetros y evaluar sensibilidad a priors. La metodología de agrupación parcial está documentada en [Stan: regresión jerárquica](https://mc-stan.org/docs/stan-users-guide/regression.html#hierarchical-regression). Su adecuación a esta muestra es una propuesta, no un resultado demostrado.

## 4. Clima compacto orientado a transferencia — línea independiente de la local

**Pregunta:** ¿una representación breve de cantidad/distribución de lluvia y amplitud térmica evita dependencias regionales inestables?

**Prueba mínima:** un conjunto pequeño predefinido de lluvia —cantidad total y contrastes temporales físicos—, amplitud térmica y NDVI mayo; comparar con lluvia mensual+NDVI y lluvia mensual+amplitud térmica. No seleccionar nuevos meses usando métricas externas. Contrastar cada adición individual antes de combinar dimensiones.

Usar Elastic Net como control y, como sensibilidad, pocas curvas suaves de complejidad fija. Una separación adicional por estado puede ser una prueba de estrés si hay soporte interno suficiente, sin sustituir las particiones previas ni presentarla como selección confirmatoria.

**Éxito:** beneficio espacial/municipal también fuera de Chignahuapan, MAE y extremos; estabilidad ante regiones completas. **Descarte:** si amplitud térmica solo identifica ubicación y el contraste desaparece cuando cambia el dominio. Alta correlación con coordenadas no demuestra por sí sola inutilidad ni causalidad.

## 5. Proceso gaussiano aditivo de baja dimensión — alternativa secundaria

**Pregunta:** ¿hay curvas suaves no lineales de verdor/dinámica que el ajuste lineal pierde?

**Prueba mínima:** una representación climática compacta, NDVI mayo y un único descriptor temporal, con kernel aditivo y término de ruido; controlar flexibilidad y escalas dentro de entrenamiento. Contrastar con el lineal sobre exactamente los mismos predictores. Sin kernel geográfico inicial: el diagnóstico residual previo no aporta evidencia fuerte de una corrección espacial simple.

Los [kernels aditivos](https://arxiv.org/abs/1103.4023) permiten representar sumas de funciones en un proceso gaussiano; la [documentación de scikit-learn](https://scikit-learn.org/stable/modules/gaussian_process.html) describe predicciones probabilísticas y limitaciones dimensionales. Que pueda generar desviaciones predictivas no implica intervalos calibrados en esta muestra ni bajo cambio geográfico.

**Éxito:** mejora repetible sobre el control lineal y buen diagnóstico de cobertura. **Descarte:** si interpolación local mejora aleatoria pero empeora perfiles/espacio, o aumenta complejidad sin utilidad. No abrir una búsqueda amplia de kernels.

## 6. Información parcelaria dirigida a Chignahuapan — potencial alto, disponibilidad por verificar

**Pregunta:** ¿el error persistente corresponde a diferencias de manejo, ciclo o ambiente local no observadas?

Antes de obtener una fuente, verificar si diferencia parcelas de los dos perfiles dominantes locales y si su fecha/resolución es compatible. Posibles dimensiones: fecha de siembra/cosecha y cultivo real del periodo, variedad/manejo hídrico/fertilización, mediciones o cartografía de suelo más fina y drenaje local. Son hipótesis; no se ha comprobado disponibilidad, costo ni explicación causal. Otra capa regional uniforme o más nombres de índices de las mismas bandas probablemente no atacaría la heterogeneidad observada.

Una campaña de nuevas etiquetas debe cubrir Chignahuapan y municipios externos: obtener únicamente más parcelas locales no valida transferencia. Los casos difíciles guían auditoría/recolección, no eliminación ni activación con el Y real.

## Qué pospondría

No priorizar nuevas rondas indiscriminadas de PCA/FPCA, índices vegetales muy redundantes, GMM/mixture-of-experts, modelos separados por cada perfil, redes profundas con138 etiquetas o sustitución de modelo por un simulador agronómico que requiere manejo/fenología/calibración actualmente ausentes. Los modelos de riesgo/intervalos pueden estudiarse después como objetivo de incertidumbre, sin prometer reducir RMSE ni convertir dispersión entre folds en incertidumbre calibrada.

## Orden propuesto y criterio de avance

1. Auditoría semántica y de casos difíciles, sin alterar etiquetas por residuo.
2. Dos contrastes acotados: objetivo intraperfil y mezcla fija existente.
3. Una alternativa jerárquica compacta; estudiar clima compacto si el objetivo operativo es transferencia.
4. Proceso gaussiano solo si los contrastes anteriores dejan una hipótesis concreta de no linealidad.
5. Nuevas fuentes/etiquetas dirigidas a preguntas no resueltas, con validación independiente.

Mantener dos objetivos explícitos —diferenciar parcelas en perfiles conocidos y predecir regiones nuevas—; RMSE/MAE globales, errores de diferencias con igual peso y sin Chignahuapan, Q1/Q4 y estabilidad. Mantener los folds para comparabilidad exploratoria. Congelar cada matriz y reglas antes del ajuste; toda selección supervisada y calibración debe estar dentro del entrenamiento interno, como describe la [validación anidada de scikit-learn](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html). Esa corrección del protocolo no elimina el sesgo de descubrimiento de las mismas etiquetas exploradas repetidamente. Nuevos rendimientos o geografías son necesarios para confirmación independiente.
