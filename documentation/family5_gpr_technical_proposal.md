# F5 — Propuesta técnica para revisión

No se ha implementado ni entrenado un estimadorGPR. Se mantienen los65 folds y sus particiones internas originales; las59 PRED no participan como etiquetas. El diseño constituye una hipótesis nueva sobre representaciones anteriores, todavía exploratoria.

## Modelo y núcleo

y=m(X)+f(X)+ε, f~GP(0,k), ε~N(0,σn²). Se propone GPR exacto:138 observaciones permiten un sistema pequeño; los costos crecen con refits/selección interna y con reconstrucción residual, no solo con el tamaño de un único kernel. Las fórmulas de regresión/media y su interpretación se fundamentan en [GPML, capítulo2](https://gaussianprocess.org/gpml/chapters/RW2.pdf). Esta viabilidad computacional no implica capacidad de generalización.

Primer núcleo: (compact_precip_total,compact_early_fraction,compact_concentration_hhi,S2_ndvi_month_05). Reutiliza exactamente C-T3: suma de7lluvias, fracciónabril–junio conepsilon1e−6mm, HHI mensual, NDVI de mayo exacto. No importamos automáticamente TOP20Climate/History15/TOPO25 delChampion.

Primer kernel Matérnν=3/2, νfijo. r²=||zP−zP′||²/(3ℓP²)+(zV−zV′)²/ℓV²; ksignal=a(1+√3r)exp(−√3r). Hay4 hiperparámetros dekernel: amplituda, longitudesℓP/ℓV y varianza de ruido. Matérn permite elegir suavidad;RBF corresponde a una hipótesis más suave. νno se optimiza continuamente en la implementación de referencia. [DocumentaciónMatérn](https://scikit-learn.org/1.7/modules/generated/sklearn.gaussian_process.kernels.Matern.html).

Este kernel conjunto permite respuestas no aditivas suaves de lluvia/vegetación; no demuestra interacciones agronómicas. Longitud separada porvariable en el núcleo4elevaría a6losparámetros y se reserva como sensibilidad acotada. La escala de lluvia se comparte en3 variables, evitando7 longitudes mensuales más otras de historia/terreno. El número de parámetros propuesto es una restricción de diseño, no un umbral estadístico universal para n138.

## Comparaciones de kernels acotadas

Primario:Matérn3/2 con escalas porbloque. SensibilidadRBF sobre las mismas columnas y grupos; sensibilidadARD4 variables solo para el mismo núcleo si la fase principal resulta viable. Una eventual elección entre estas especificaciones debe hacerse medianteCVinterna, nunca por el menorRMSE externo. No añadirMatérn5/2, combinaciones deν, rationalquadratic, nuevos bloques o pesos después de verOOF.

F5-05: k=kA(A,A′)+kH(H,H′)+kT(T,T′)+σn²I;A=lluvia3+NDVI de mayo,H=histNDVImean/std,T=pendiente_media. Cada término tiene una amplitud y una longitud:7 parámetros, incluido ruido. El control conjunto debe usar **los mismos3 bloques y normalización**, con3 longitudes,1amplitud y1ruido=5 parámetros. Así se contrasta estructura aditiva/junta; el control no es el kernel deF5-01 ampliado con un reparto distinto de longitudes.

Sumas y productos de kernels admiten covarianzas válidas; productos de funcionesGP no implican una funciónGP. [GPML, capítulo4](https://gaussianprocess.org/gpml/chapters/RW4.pdf). Separar funciones aditivas facilita interpretar contribuciones, pero no las vuelve causales ni necesariamente identificables cuando bloques se correlacionan. [Duvenaud etal., AdditiveGaussianProcesses](https://arxiv.org/abs/1112.4394).

Interacción limitada alternativa conceptual: kP+kV+aPV·kP·kV, longitudesP/V compartidas entre términos,3amplitudes+2 longitudes+ruido=6 parámetros. Se documenta para evaluar la hipótesis; no se añade a la batería primaria ni se ejecuta. F5-01 ya permite interacción conjunta sin construir productos de columnas adicionales.

## Escala, faltantes y media

Imputación mediana y escalado solo en cada entrenamiento. PisoNDVI0.05 como C; demás desviaciones con guarda1e−12 y constantes descartadas con registro. Dividir vector de cada bloque por√d limita que un bloque gane peso solo por tener más columnas. No escalar usando197 parcelas. NormalizarY con media/desviación del entrenamiento correspondiente y restaurar unidades t/ha. Si un bloque es constante, registrar el kernel reducido efectivo, no reportar longitudes no identificables como relevancia.

Media inicial constante, con estadísticas deY de entrenamiento. Enscikit-learn, normalize_y centra/escalaY, no ajusta una media lineal. SuGPR optimiza el kernel por log-marginal-likelihood. [GuíaGP](https://scikit-learn.org/1.7/modules/gaussian_process.html). Una media lineal fija por entrenamiento podría conservar tendencia fuera del soporte, pero requiere controlar su ajuste/regularización: se deja para una fase posterior, evitando duplicar ahora núcleo/kernel/media.

UnDotProduct sumado alkernel representa una contribución lineal aleatoria a la covarianza, no la misma media lineal determinista. Media externaC-T3 aparece solo enF5-06 residual. Fuera del soporte, un kernel estacionario con covarianza decreciente vuelve hacia la media previa; no extrapola automáticamente una tendencia agrícola. Este comportamiento debe evaluarse especialmente en el bloque 3; no se supone queGP resolverá la sobreestimación regional.

## Optimización futura limitada y diagnósticos

Propuesta: L-BFGS-B, uninicio fijo y2 reinicios con seed2026; LML dentro del entrenamiento que corresponda. SobreYestandarizado: amplitud[0.01,100], longitud[0.2,20], ruido[0.001,2], inicios1/1/0.1 y jitter1e−8. Son límites e inicios propuestos para revisión, sin búsqueda ni ajuste ejecutados. Una longitud óptima en el límite debe declararse, no ampliar el rango retrospectivamente sin nueva versión.

El API permite bounds y reinicios; `alpha` yWhiteKernel son distintos. [GaussianProcessRegressor1.7](https://scikit-learn.org/1.7/modules/generated/sklearn.gaussian_process.GaussianProcessRegressor.html). La LML puede tener óptimos locales e intercambiar longitud corta/ruido alto o bajo; mayorLML no garantizaRMSEgeográfico menor. [GPML, capítulo5](https://gaussianprocess.org/gpml/chapters/RW5.pdf).

Registrar porfit: parámetros, LML, límites tocados, avisos deloptimizador, condición deK, fallasCholesky, jitterreal, tiempo, ntrain/perfiles, convergencia entre reinicios y dispersión de predicciones. No descartar automáticamente etiquetas ni usar errores para cambiarlas. Si la representación induce degeneración, suspender ese candidato y documentar la causa antes de crear otra formulación.

## Ruido, duplicados e incertidumbre

WhiteKernel modela varianza residual independiente; jitter pequeño estabiliza la diagonal numéricamente, no reemplaza ruido observacional. [WhiteKernel](https://scikit-learn.org/1.7/modules/generated/sklearn.gaussian_process.kernels.WhiteKernel.html). Mantener observaciones con climaigual yYdistinto: la media condicionada solo al clima coincide, yWhiteKernel absorbe discrepancias sin crear discriminación parcelaria. Dependencia de manejo/perfil no observado puede violar ese supuesto de ruido; los protocolos grupales lo ponen a prueba.

Reportar por separado incertidumbre latente y predictiva deY: conWhiteKernel, la varianza devuelta puede incluir el ruido del kernel; identificar exactamente implementación/unidades. Para un kernel homoscedástico, varlatente=varpredictiva−σn², después de desnormalizar; `alpha` como jitter de entrenamiento no se añade automáticamente a la incertidumbre de una nueva observación. Verificar estas identidades matemáticamente en la futura implementación.

Intervalos plug-in omiten incertidumbre de selección/hiperparámetros, errores deX/Y y cambio de dominio. Evaluar cobertura90%, ancho y sesgo por perfil conocido/nuevo, municipio y bloque, sin asumir calibración. AntecedenteH1:77.9%de cobertura municipal nueva y mayorancho espacial. GPR no convierte ese problema en una garantía. La incertidumbre residual condicionada albase tampoco integra la incertidumbre ni covarianza deerror del base.

## GPR residual: trazabilidad antes de complejidad

F5-06 propone primero C-T3 como media externa reproducible, usando exclusivamente cross-fitting interno. Dentro de outer-trainA, para cada inner-trainAi/validaciónBi: seleccionar y ajustarbase solo conAi; generar residuos deAi con sub-cross-fitting que no acceda aBi; ajustarGP a esosresiduos; sumar baseAi(Bi)+GPAi(Bi) y evaluarBi. Repetir íntegramente por opción interna. Una vez seleccionada configuración, generar residuosOOF internos deA conbases ajustadas sin cada heldout interno, ajustarbasefinal conA yGP con esosresiduos, evaluarouterVsinYusado. Mantener los65 folds externos y lasparticiones internas disponibles; subparticiones adicionales requeridas se congelarán en la futura implementación.

No entrenar elGP con residuosglobalesOOF delChampion: sus predictores deouter-train pueden haber vistoYdeouter-validation u otro heldout relevante. Tampoco ajustar un corrector a residuosin-sample. No reutilizar los hiperparámetros del base escogidos conBi al construir una predicción honesta deBi durante selección interna.

La variante sobreChampion completo permanece **suspendida para ejecución**: es necesario reconstruir sus3 capas, ranking y selección de manera anidada hasta elnivel de entrenamiento delGP. RS5 `outer_train_residual2.parquet` corresponde albase clima+historia previo a la tercera corrección; no es suficiente para elChampionfinal. L8/F4-S7 ya documentaron este límite. No se propone un sustituto diferente bajo elnombreChampion. El coste mayor de esta variante es reconstruirbase, no resolverK de138.

## Validación y criterios propuestos

Reutilizar exactamente65 folds y losIDs/innerpartitions congelados. Champion ymezcla solo se comparan donde hayOOFaleatoria compatible; no generar una validación geográfica ficticia. Métrica primaria:138OOFporrepetición, después media de10 repeticiones;municipal/perfil/espacial por separado. Conservar misma llave(ID,Y,protocolo,repeat,fold). Históricosmedia de folds y métricas nuevasOOFno se juntan enun ranking.

Primer objetivo propuesto: transferencia municipal deF5-01 frente aC-T3, conerror aleatorio/perfil/espacial e intraperfil como costos explícitos. Margen práctico tentativo0.01t/ha, para revisión: buscar≥0.01 de mejoraRMSEmunicipal y no deteriorarRMSE/MAEdeotros escenarios más de0.01frente al control comparable; mantener también F4-S1 como referencia de costo original. Este margen no tiene validación económica ni significancia estadística demostrada.

Exigir distribución de ganancias pormunicipio/bloque, sensibilidad de agregación alomitir cadafold, conservación de casosinfluyentes y proporción de mejoras. Almenos3/5 folds municipales conganancia sería una guarda de estabilidad propuesta, no una prueba con cinco réplicas independientes. Si unbeneficio espacial se revierte alomitirbloque 3, conservarlo solo como hipótesis regional. Diferencias locales: parejas del mismo ajuste externo, igualpeso por perfil y soporte real, sin pseudorreplicación.

No elegir“mejor núcleo anterior”usandoOOF externa. F5-03/04/05 se anclan al núcleo fijoF5-01. Si después se desea elegir representaciónmensual/compacta oDTR, la regla de selección completa debe estar dentro deCVinterna y evaluarse como otro procedimiento predefinido, no heredar globalmente unganador.

Escalado, medias, ranking, PCA eventualmente propuesto, parámetrosbase yGP se ajustan solo al train pertinente. No se creaPCApredictiva en esta etapa. Las59 PRED no eligen representaciones, hiperparámetros ni criterios. Nuevasetiquetas/regiones/campañas siguen necesarias para confirmación.
