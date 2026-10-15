# F8 — Identificabilidad, soporte y extrapolación

{
  "n_labels": 138,
  "n_climate_profiles": 43,
  "n_repeated_profiles": 12,
  "n_singleton_profiles": 31,
  "n_parcels_repeated": 107,
  "n_pairs": 1073,
  "n_municipalities": 9,
  "n_states": 3,
  "within_profile_TSS": 25.355813353617307,
  "total_TSS": 99.25303188405798,
  "within_fraction": 0.25546638598644117,
  "between_fraction": 0.7445336140135588,
  "Chignahuapan_n": 71,
  "Chignahuapan_profiles": 11,
  "warning": "Descriptive full TRAIN means only; never operational targets or validation-dependent transforms"
}

Estos conteos y la descomposición de sumas de cuadrados son descriptivos de TRAIN completo, no estimadores causales ni targets operativos. Solo12 perfiles repetidos informan variación intraperfil;31 son singleton. Chignahuapan concentra71 etiquetas repartidas en11 perfiles, pero solo dos tienen varias parcelas y aportan parejas; centenares de parejas dependientes no crean centenares de unidades climáticas independientes. La falta de señal estable no demuestra ruido irreducible: manejo, suelo físico, fechas, calidad/temporalidad de NDVI o mediciones no observadas pueden explicarla.

La fracción entre medias de perfil usa los mismos labels para definir esas medias; no es varianza explicada OOF por lluvia ni una estimación de su contribución causal. Los tamaños profundos mínimos de10 observaciones pertenecen al tuning de la base en subtraining, no a un corrector ajustado con10 filas. La viabilidad computacional no elimina esa fragilidad estadística.

## Dos definiciones de nivel

A usa m(C3), idéntico ante vector climático idéntico. B usa m(C3,V) y ya absorbe señal parcelaria de May. Recomendar B para primer control emparejado no implica mayor pureza agroclimática: debería escribirse m(C,V), no m(C) si V varía dentro del perfil. GP rain3 existente no sustituye a un control ElasticNet rain3.

Sin restricciones, m+δ no tiene reparto único: cualquier función compartida q puede moverse entre etapas. Fijar algoritmo/entradas de la base, orden de ajuste y centrar g respecto del entrenamiento impone una convención predictiva; no identifica un efecto puro de parcela ni elimina proxies regionales. C,V,T,H son correlacionados, y repetir V en base/corrector exige ablar V-only. No residualizar automáticamente X contra toda la muestra ni centrar y por perfiles de validación.

La evidencia necesaria no es equivalente: correlación X–Y, frecuencia de uso, mejora directa, mejora residual de pipeline, mejora de diferencias intraperfil y transferencia municipal/espacial son seis pruebas distintas. F7 muestra mejora igual-perfil pero deterioro ponderado por parejas y absoluto. Fuera de Chignahuapan existe señal local parcial; convertirla en regla regional sería una decisión no validada.

## Mecanismos diferentes

Para GP con kernel que decae con distancia, μ*(x)=m0(x)+k(x,X)[K+σ²I]^-1(y-m0(X)). Si k→0, retorna a m0: cero en escala normalizada o media de entrenamiento al desnormalizar. No ocurre así con todo kernel estacionario (por ejemplo componente constante no decae) ni con media lineal que extrapola. S1-C deja tendencia cuando residual GP≈0; eso no demuestra que el GP residual esté corrigiendo extrapolación. [Documentación primaria GPR](https://scikit-learn.org/1.7/modules/gaussian_process.html).

Árboles de regresión con hojas constantes enrutan un valor fuera del rango a una hoja; no prolongan una pendiente aprendida. Un booster puede generar valores fuera del rango de y y una suma de etapas puede ampliar amplitud, pero esa amplitud no constituye extrapolación estructural justificada. [Árboles](https://scikit-learn.org/1.7/modules/tree.html), [CatBoost](https://catboost.ai/docs/en/references/training-parameters/common).

Una base lineal extrapola mediante βx; esto puede ser razonable si la relación permanece estable o peligroso si cambia dominio. Ridge/ElasticNet contraen coeficientes; L2 de hojas y learning rate contraen ajustes de boosting; λ multiplica corrección. Ninguna garantiza dirección o elimina sesgo geográfico.

Mezcla convexa w f1+(1-w)f2 permanece entre predicciones completas para0≤w≤1. Corrección fbase+λg no: g es un target residual y puede ser positivo/negativo. Si ambas etapas sobreestiman el bajo rendimiento, los sesgos se suman. Centrar g globalmente en TRAIN evita intercepto duplicado pero no sesgo por municipio: E_valid(g) puede no ser cero. No recortar y ni usar etiqueta validación para activar signo, λ o soporte.

## Diagnósticos propuestos

Registrar base, g propuesto, λg aplicado, signos, cuantiles, máximo absoluto, cambios de RMSE/MAE/sesgo y SSE=sesgo²+dispersión por repetición/región. Soporte: rangos marginales y distancia al entrenamiento preprocesado de cada etapa; grupos conocidos/nuevos; ratio de corrección frente a dispersión residual TRAIN. Radios/umbrales se definen con X TRAIN, no errores externos. Folds/repeticiones no son iid. Cuartiles de rendimiento observado externos solo estratifican diagnóstico posterior; nunca gobiernan la predicción. Cuartiles del nivel base disponibles en inferencia pueden servir para describir correcciones, pero cualquier gate futuro tendría que seleccionarse internamente.

Comparar daño/amplitud fuera y dentro de soporte, estabilidad de λ y coeficientes, asociación de corrección con estado/municipio solo como auditoría de proxy, pares intraperfil y omisiones de municipios/bloques sin refits. Un corrector regionalmente sesgado se rechaza aunque reduzca error de perfiles pequeños. No prometer cobertura probabilística de Ridge/CatBoost ni inferirla de dispersión de árboles.


Verificación: cinco pruebas pasaron; cero ajustes/predicciones nuevos; 158 fuentes consumidas verificadas. Se conserva inventario de15382 hashes anteriores; los archivos no utilizados no se reabrieron para rehash. Escrituras limitadas a nueva versión F8 y sus documentos.
