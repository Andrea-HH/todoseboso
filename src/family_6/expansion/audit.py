"""Block evidence and exact-field semantics; no new variable screening."""
import json
import pandas as pd
from . import execution as e

def build():
    _,t,_=e.load();inventory=pd.read_csv(e.base.design.OUT/'tables/candidate_variable_inventory.csv')
    columns=list(dict.fromkeys(e.CORE+[x for c in e.BLOCKS.values() for x in c]+e.base.prior.RAIN))
    inventory[inventory.column.isin(columns)].to_csv(e.OUT/'audit/exact_F5_variable_inventory.csv',index=False)
    evidence=[dict(experiment='F6-E0',block='compact3+MayNDVI',source='F6-01 independently tuned original65folds',evidence='randomRMSE0.506296;municipal0.638586;spatial0.758923;no original continuation',hypothesis='exact core baseline; no new fit'),dict(experiment='F6-E1',block='NDVI historical mean/std',source='F5 inventory;RS2;RS4/RS6 History15/16;F4 locality',evidence='pair selected50/50 in TOP15 but15/16 features; historical block residual benefit does not isolate these two',hypothesis='stable parcel vegetation signature may differentiate same-climate parcels; not History15 equivalence'),dict(experiment='F6-E2',block='mean slope',source='F5 inventory;RS5 slope14;K5/F4 terrain',evidence='residual terrain-block evidence;mean-only direct utility not demonstrated;geographic costs',hypothesis='incremental topographic partition or proxy for geography; no assumption of hydrologic mechanism'),dict(experiment='F6-E3',block='DTR standard deviation',source='F5 inventory;F4-S5;C-T1/C-T4;G/H',evidence='rain7+DTR spatial gain depended strongly on block3;joint compact+DTR+NDVI did not consistently combine gains',hypothesis='thermal variability partitions may transfer or serve regional proxy; rain/temp exact profiles previously aligned')]
    pd.DataFrame(evidence).to_csv(e.OUT/'tables/block_evidence_matrix.csv',index=False)
    support=[]
    for column in columns:
        groups=t.groupby('climate_profile')[column];ranges=groups.max()-groups.min();repeated=t.groupby('climate_profile').size().ge(2)
        support.append(dict(feature=column,n_finite=int(t[column].notna().sum()),n_unique=t[column].nunique(),n_climate_profiles=t.climate_profile.nunique(),n_repeated_profiles=int(repeated.sum()),n_repeated_profiles_with_variation=int(((ranges>1e-10)&repeated).sum()),max_within_profile_range=float(ranges.max()),uses_y=False))
    pd.DataFrame(support).to_csv(e.OUT/'tables/predictor_intraprofile_support.csv',index=False)
    interpretation='''# F6-E — Evidencia y diseño congelado

La decisión anterior cerró la ejecución compact4, sin probar historia, pendiente ni DTR. La nueva solicitud autoriza E1–E3 independientemente de ese gate, sin modificarlo ni presentar sus resultados como aprobación retrospectiva de F6-02–05. E0 recupera exactamente F6-01, con65 modelos externos y325 externos/internos seleccionados disponibles. No se reajusta ni sobrescribe. E4/E5 no se ejecutan.

Historia NDVI2 conserva media y desviación entre siete promedios de meses calendario de2022–2024 (abril–octubre); std no es interanual. TOP15 se seleccionaba entre16 campos históricos efectivos: inclusión frecuente del par no demuestra utilidad exclusiva. La extensión es directa sobre Y, no residual del Champion. Pendiente media usa el alias TOPO_BASIC_slope_mean=slope_degrees; la fuente topográfica es más fina que clima, pero pendiente no mide manejo, humedad o causalidad. DTRstd es desviación muestral entre siete medias mensuales Tmax−Tmin y mantiene la misma malla climática auditada. Estas variables no sustituyen los bloques completos History15/16 o slope14.

Se reutilizan sin cambios TreeModel, ConditionalFeatures y el motor original de búsqueda interna: ocho configuraciones,384 árboles Extra Trees, bootstrap=False, semilla2026, profundidad3/5/sin límite con hojas5/10 y split10/20, max_features0.5/1.0. La misma fracción corresponde a diferente número efectivo de variables al ampliar dimensiones; se registra sin atribuir todo cambio únicamente a la información nueva. Cada representación se retunea solo dentro de cuatro folds internos originales. No se usan parámetros escogidos mediante OOF externos.

La ablación con reajuste es E1/E2/E3 frente a E0: modelos completos y núcleo se ajustaron y seleccionaron independientemente dentro de cada entrenamiento externo. El núcleo ya existe como F6-01 y se recupera; enmascarar columnas de un árbol completo no reemplaza esa ablación. Las comparaciones contextuales con C-T3/F5-01 conservan la misma evaluación; Champion y etapas solo tienen50 folds aleatorios compatibles.

El cache reduce la tabla de138 etiquetas a los predictores autorizados y metadatos de diagnóstico. No modifica valores, orden, folds ni transformaciones. Las predicciones de los65 modelos E0 se cotejan contra la tabla original y el cache a tolerancia1e-12. Los trabajadores redirigen de manera temporal y aislada rutas, specs y loader del motor original; siempre restauran sus globals. El código y los archivos de F6 permanecen protegidos por hashes.

Los diagnósticos se congelan antes de evaluar: ALE de cuatro cuantiles; mínimo cinco parcelas respaldadas y≥80% de esquinas dentro de un radio empírico. El radio es q95 de distancia al vecino más cercano de cada observación de entrenamiento, excluyendo su propio índice, en la transformación ajustada de ese modelo. Es un soporte local aproximado, no garantía causal ni física. Si un bin carece de soporte, no se conecta una curva ALE global a través del hueco. Las interacciones son las seis parejas predefinidas del diseño, en celdas de terciles con el mismo gate de soporte; no hay screening de pares.

La permutación adicional se realiza por bloque (historia2 conjuntamente) entre parcelas del mismo perfil climático en validación, diez veces, con al menos diez parcelas elegibles. Mantiene correlación interna del par histórico, pero no condiciona sobre todos los demás predictores. Si el bloque es constante dentro de los perfiles, se declara no identificable mediante esa permutación; no se interpreta un cero mecánico como irrelevancia. No se hacen permutaciones marginales DTR que fabriquen combinaciones climáticas sin soporte. La ablación reajustada proporciona la evidencia incremental primaria.

384 árboles y los límites de búsqueda permanecen fijos. Los prefijos128/256 del bosque completo diagnostican variación Monte Carlo; no abren automáticamente otra búsqueda. Frecuencia de partición, impureza, ALE, asociaciones y mecanismos causales son conceptos distintos. La utilidad se determina por OOF y estabilidad, no por frecuencia de variables.

E4/E5 recibirán una tabla de recomendación al terminar E1–E3. Se reportarán diferencias municipales/espaciales, pares intraperfil, omisiones de bloques, municipios y casos influyentes. La revisión es exploratoria sobre etiquetas y folds reutilizados. No se elige un ganador global y se lo presenta como confirmación independiente; no hay modelo final ni59 predicciones PRED.
'''
    (e.OUT/'report/evidence_and_frozen_design.md').write_text(interpretation,encoding='utf8')
