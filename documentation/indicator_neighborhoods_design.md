# Reducción y vecindarios para corrección: diseño congelado

En la etapa previa no había vecinos satelitales: indicadores globales o pesos globales continuos, sobre una base J7que conserva24vecinos geográficos y gate físico. Esta etapa varía el vecindario de la **nueva corrección**; no cambia los vecinos/pipelines internos de J7ni el Champion. Reutiliza65particiones externas e internas y138targets; sin PRED59, ajuste final138, eliminación de casos ni reglas municipales.

## Reducciones

R9=nueve indicadores anteriores. R4=pisos históricos NDVImin/FAPARmin, persistencia de exceso de brecha NDVI y pendiente mínima. R3=R4sin piso FAPAR. R2=persistencia y pendiente mínima. PCA2=dos componentes deR9, imputación/escalado/PCA dentro de entrenamiento; usa las nueve variables originales y no equivale a tener sólo dos variables fuente. Estas representaciones se evalúan globalmente con ENalpha.01,l1_ratio.5y amplitud interna0/.25/.5.

## Tres geometrías

- GEO: distancia haversine entre centroides, sin usar municipio o estado para elegir vecinos. Para KMeans se proyectan lat/lon en km con latitud de referencia del entrenamiento.
- PHYSICAL: espacio físico existente de textura/fase, proporciones geológicas y distancias a estructuras; se añade bloque equilibrado de altitud, pendiente media y TPI. Sin coordenadas ni satélite en esa distancia. Puede correlacionarse territorialmente; se mide después.
- SATELLITE: tres indicadores puros, pisos NDVImin/FAPARmin y persistencia. Sin pendiente, coordenadas ni clima explícito. Se requieren tres valores finitos para entrar como referencia de semejanza; consultas sin historia completa usan respaldo global, no vecinos artificiales por imputación. Los targets no se eliminan: todos entrenan la propuesta global y todos se evalúan.

KNN evalúa k={8,16,24,48,72}, limitado por referencias disponibles y conservando todos los empates del borde. Pesos1/(distancia/.escala+.25), escala de distancias vecinales positivas del entrenamiento. KMeans evalúa4/8clusters sobre cada geometría. Transformaciones y clusters se ajustan sólo con Xdel entrenamiento.

## Dos usos emparejados

DIRECT: Ridge local sobreR4a residuos de base cross-fitted, alpha30y pesos normalizados al número de vecinos; predicción contraída hacia la propuesta globalR4con n_efectivo/(n_efectivo+20). Un cluster actúa como vecindario de miembros; con<4referencias se usa respaldo global. Recorte residual±.5antes de amplitud0/.25/.5.

WEIGHT: regular la propuesta globalR4,δ=.5×clip(ENresidual,−.5,+.5), mediante peso local0..1. Peso global=clip(sumaδOOFr/(1.1sumaδOOF²),0,1). Peso local=clip((suma pesosδOOFr+prior×peso_global)/(suma pesosδOOF²+prior),0,1), con prior20×mediaδOOF². Se normalizan pesos vecinales al tamaño efectivo. Se utiliza el mismo vecindario/cluster queDIRECT.

**Selección emparejada:** k/n_clusters y amplitud se eligen exclusivamente por RMSEOOFinterno del métodoDIRECT; se comparten entreDIRECTyWEIGHT para comparar uso con igual vecindario. WEIGHT no recibe una búsqueda interna independiente; su fuerza es amplitud/.5. SiDIRECTelige amplitud0también se apagaWEIGHT. La interpretación debe reconocer que no se optimizó el vecindario específicamente para el peso.

Este diseño permite calibración honesta sin añadir profundidad: los candidatosδOOFde entrenamiento se ajustan enA_jusando residuos base cross-fitted dentro deA_jy predicenD_jexcluido. Con ellos se aprenden los pesos finales enA. Para elegir k/amplitud se evalúaDIRECTen las internas originales, sin usar la validación externa. No se emplean residuos externos globales como targets ni parámetros elegidos en el fold externo para contextos internos.

Cinco reducciones globales y doce rutas locales(3geometrías×2modos×2usos)por base:34recetas sobre CT3/J7,2210sistemas externos. No selector externo de ganador, nuevas variables, mezclas geográfico/físicas adicionales ni ampliación posterior de la grilla al ver resultados. Nulos empatan hacia menor amplitud y mayor k/menor número de clusters.

## Evaluación

RMSE/R²,MAE,sesgo,SD,predicciones OOFpor parcela/repetición/fold, municipios/estados/bloques, omisiones sin reajuste, cuartiles, diferencias intraperfil y análisis sin35difíciles/sin10peores/sin171/015. Medias de métricas sobre OOFcompletas por repetición, nunca RMSEmedio por fold ni mezcla de protocolos. Se conserva CT3/J7exacto y benchmarks previos de indicadores directos/correctorC4.

Registrar k/clusters elegidos, activación, vecinos realmente disponibles/ties, tamaño efectivo, respaldo por falta de historia, distancias geográficas y proporción de vecinos del mismo municipio/perfil, para distinguir similitud física/satelital de cercanía territorial. Estos diagnósticos usan etiquetas geográficas sólo después de predecir.

Pruebas pareadas predefinidas:34recetas vs su base;12usosWEIGHTvsDIRECTemparejados;R4vsR9en ambas bases;KNNPHYSICAL/SATELLITEvsGEOparaWEIGHTen ambas bases.52contrastes×4protocolos=208, Holm conjunto y bootstrap5000por conglomerados. Los demás contrastes son descriptivos. OOFfijas, reutilización histórica y pocos grupos espaciales limitan la inferencia. No promoción automática ni superioridad confirmatoria por un único resultado favorable.
