"""Technical derivation and decision report for the frozen Stage B experiment."""
import numpy as np
import pandas as pd
from . import stage_b_learning as b

def md(frame):
    z=frame.reset_index()
    lines=['| '+' | '.join(map(str,z.columns))+' |','| '+' | '.join(['---']*len(z.columns))+' |']
    for row in z.itertuples(index=False,name=None):lines.append('| '+' | '.join(f'{v:.5f}' if isinstance(v,(float,np.floating)) else str(v).replace('|','/') for v in row)+' |')
    return '\n'.join(lines)

def write(global_summary,pair_summary,blend,blend_local):
    out=b.OUT;g=global_summary[global_summary.stratum.eq('all')]
    rmse=g.pivot(index='experiment',columns='protocol',values='RMSE');mae=g.pivot(index='experiment',columns='protocol',values='MAE')
    local=pair_summary[pair_summary.scope.eq('all')].pivot(index='experiment',columns='protocol',values='equal_profile_rmse')
    outside=pair_summary[pair_summary.scope.eq('without_Chignahuapan')].pivot(index='experiment',columns='protocol',values='equal_profile_rmse')
    reg=pd.read_csv(out/'tables/registry.csv');lam=reg.groupby(['experiment','protocol']).lam.agg(mean='mean',zero_fraction=lambda x:(x==0).mean())
    blendtable=blend[blend.stratum.eq('all')].set_index('experiment')[['RMSE','MAE','R2','bias_pred_minus_y']]
    decisions=pd.DataFrame([dict(model='B1',decision='descartar complejidad adicional',reason='no mejora local consistente;lambda0frecuente y gran deterioro municipal'),dict(model='B3',decision='conservar exclusivamente para investigación',reason='mejora local pequeña aleatoria/perfil, incluida sensibilidadsinChignahuapan, con deterioro municipal y local espacial'),dict(model='FIXED_50_50',decision='conservar como candidato exploratorio aleatorio',reason='mejora RMSE/MAE; transferencia no evaluable con Champion disponible'),dict(model='Stage C',decision='posible investigación independiente; no ejecutar aquí',reason='B no justifica promover objetivo intraperfil; jerarquía puede probar otra hipótesis con control compacto')])
    decisions.to_csv(out/'tables/decisions.csv',index=False)
    text=f'''# Etapa B — Aprendizaje de diferencias intraperfil y mezcla fija

El objetivo intraperfil no produce una mejora defendible de predicción regional. B1 empeora la diferenciación equilibrada; B3 obtiene una mejora local pequeña, con un costo municipal importante. La mezcla fija Champion/F4-S1 mejora modestamente RMSE y MAE aleatorios. Son dos conclusiones independientes y exploratorias, no una confirmación de mejora en regiones nuevas.

## Antecedentes, congelación y ámbito

Se recuperaron Etapa A, F4-S1/F4-E1/F4-E2, J0, Champion y los65folds externos/particiones internas existentes. Etapa A documentó fuentes50k suspendidas; ninguna variable territorial, pendiente, relieve, amplitud térmica ni otros índices se introduce en B. Hay138TRAIN,59PRED sin etiquetas utilizadas. El manifiesto `frozen_design.json` se generó antes de las métricas externas nuevas. Los hashes del código de aprendizaje se congelaron después de las pruebas sintéticas y antes del ajuste externo. Los cambios previos a ese ajuste fueron correcciones técnicas para admitir grupos y verificar el caso límite cuadrático, sin alterar variables, grilla o criterios.

B0 reutiliza literalmente F4-E1/F4-S1; B2 reutiliza F4-E2. B1 usa las mismas siete lluvias+NDVI mayo queB0 y B3 añade el mismo inicio de ascensoLAI queB2. Se guardaron130modelos candidatos externos y130controles de implementación lambda0, que no son nuevas candidatas predictivas. Las cuatro arquitecturas tienen7,176prediccionesOOF. No se recalculan rasgos ni se entrenan modelos finales sobre las59PRED. Champion no se reentrena.

## Identidad, normalización y solver

Para un grupo de tamaño n_g≥2:

sum_(i<j)(e_i−e_j)² = n_g·sum_i(e_i−mean_g(e))².

Al dividir por n_g(n_g−1)/2, se obtiene L_delta,g=2/(n_g−1)·sum_i(e_i−mean_g(e))². LI promedia esas cantidades entre grupos elegibles; singleton no contribuye al término local. Los sumatorios se implementan con acumulación por grupo, sin generar parejas ni una matriz densa n×n para optimizar. El número de filas aumentadas es a lo sumo2n.

Definiendo Q como la forma de centrado ponderado por grupo, J=SSE/n+lambda·e'Qe+alpha_joint[ rho|beta|_1+(1−rho)|beta|²/2 ]. Q es semidefinida positiva y anula la constante. El intercepto óptimo libre es mean(y)−mean(X)'beta.

Se usan X e y centrados globalmente, y filas adicionales sqrt(n·lambda·2/[G2(n_g−1)]) veces las desviaciones de X/y respecto a sus medias de entrenamiento por grupo. El SSE aumentado es SSE+n·lambda·LI. Si hay m filas aumentadas, el solver estándar minimiza SSE_aug/(2m)+alpha_solver·penalty. Se establece alpha_solver=alpha_archive·n/m y alpha_joint=2·alpha_archive. Multiplicar el objetivo del solver por2m/n reproduce exactamente J. **Los valores de alpha archivados conservan su significado original**; alpha_joint es su traducción a la normalización de la solicitud.

Lambda0 usa nfilas y alpha_solver=alpha_archive: reproduce el ElasticNet convencional. Rho0/alpha0 se admiten mediante solución cuadrática cerrada como casos matemáticos límite de ese mismo objetivo, sin agregarlos a la grilla predictiva. La grilla real mantiene rho0.1/0.5/0.9 y alpha0.001/0.01/0.1/1. El solver principal sigue siendo ElasticNet, max_iter200000 y tol1e-4, exactamente la tolerancia convencional archivada. Se registran gapsduales, normalización, residuosKKT, iteraciones, pérdidas y finitud. No se afirma optimalidad exacta más allá de la tolerancia numérica verificada.

Gradiente suave respecto a beta: −2X'e/n−2lambdaX'Qe+alpha_joint(1−rho)beta; respecto al intercepto: −2mean(e). El operadorL1 corresponde a alpha_joint·rho. Las pruebas comprueban gradiente con diferencias finitas, identidad de parejas, constante por perfil, grupos2/3/33/29, singleton, permutación, intercepto libre y solución cuadrática de referencia.

La puerta de implementación reprodujo los130controles históricos lambda0 con **diferencia máxima0.0 t/ha**, por debajo de1e-8. Ninguna mejora externa se atribuye al solver antes de superar esa comprobación.

## Selección interna y soporte

Grilla lambda congelada:{{0,0.1,0.3,1}}. Para cada configuración se recalculan imputación y escala en cada entrenamiento interno, se utiliza únicamente su vector de grupos y sus etiquetas y se predice su validación interna. Los grupos nunca entran como predictor en inferencia.

La referencia de restricciones es el lambda0 con los parámetros originales seleccionados por promedio deRMSE de folds internos. Ese criterio se reproduce; luego RMSE/MAE de restricciones se calculan sobre laOOF interna completa, no promedios de folds. La selección minimizaRMSE de diferencias con igual peso por perfil, con restricciones RMSE≤referencia+0.01 y MAE≤referencia+0.01t/ha. Son tolerancias operativas exploratorias.

Las diferencias internas solo usan parcelas del mismo perfil evaluadas por el mismo modelo interno. Cuando un perfil aporta varios segmentos de validación, susMSE se combinan ponderando por número de parejas antes de dar igual peso a los perfiles. Se requiere≥2perfiles evaluables,≥2folds informativos y≥10%de parcelas elegibles. Si falta soporte o no hay lambda positivo factible, se conserva el ancla convencional. Entrenamientos sin grupos elegibles desactivan LI. Empates numéricos a1e-10 priorizan menorlambda y luego mayoralpha/menorrho. Todo se decide antes de evaluar outer-validation.

Importante: cuando existe un lambda positivo factible, el conjunto de selección también contiene otras regularizaciones con lambda0. Por ello **cambiar el criterio de selección puede cambiar alpha/rho sin activar la pérdida local**. Se registra por separado este fenómeno. El protocolo evalúa la combinación de objetivo y selección restringida; no puede atribuir todo cambio al término LI. En municipal B1 selecciona lambda0 en sus cincofolds: su deterioro procede de los parámetros elegidos por el criterio local, no de una penalización local activa. No se cambiaron retrospectivamente las reglas para corregir ese resultado.

## Predicción por parcela y transferencia

RMSEt/ha, OOFcompleta por repetición y luego media:

{md(rmse)}

MAEt/ha:

{md(mae)}

B1 tiene costo municipal≈+0.191t/haRMSE y+0.242MAE respecto aB0; B3≈+0.190RMSE y+0.229MAE respecto aB2. Las restricciones internas no garantizan restricciones en regiones nuevas. En espacial ambos reducen modestamenteRMSE global, pero no mejoran la diferenciación local equilibrada. R², sesgo, SSE, municipios/estados, extremos y comparaciones por repetición están en las tablas.

## Diferenciación intraperfil

Los pares se ordenan porID para fijar orientación; compartenperfil yfold externo. El error es diferenciaobservada−diferenciapredicha. No se mezclan modelos externos para atribuir contraste a rasgos. RMSE equilibrado es raíz de la media deMSE porperfil, después de acumular errores individuales del mismo modelo; no media deRMSE de grupos. Las parejas solapadas no son observaciones independientes.

{md(local)}

Igualpeso fuera deChignahuapan:

{md(outside)}

B1 no demuestra mejora local consistente. B3 reduce aleatoria0.58335→0.58116 y porperfil0.53876→0.53459; la señal persiste débilmente fuera deChignahuapan, pero empeora localmente municipal yespacial. No hay evidencia de que el objetivo global sea el único impedimento para distinguir parcelas. La dimensiónLAI aprovecha algo del objetivo local, con un costo regional que impide adoptarlo.

Los perfiles locales4/24 se reportan separadamente. Los otros perfiles deChignahuapan tienen una sola etiqueta local y no ofrecen parejas internas; aparecen en error porparcela. Se separan parejas ambas dentro, ambas fuera ymixtas. El umbral deerrorabsoluto>1t/ha es un diagnóstico posterior, nunca una activación deentrenamiento. La cobertura efectiva de evaluación queda registrada porprotocolo/repetición y en los criterios internos.

## Estabilidad de lambda

{md(lam)}

Lambda no es uniformemente mayor quecero: B1 lo desactiva en64%deajustes aleatorios y100%municipales; B3 en38%aleatorios y80%municipales. Sus coeficientes y cambios de regularización están registrados. No se interpreta un solo lambda seleccionado como evidencia de heterogeneidad causal.

## Mezcla fija independiente

Se recuperan exactamente1,380prediccionescompatibles porID/repetición/fold yY. Cada entrada procede del archivo OOF de su modelo; se mantiene la definición y configuración archivada sin certificar retrospectivamente toda su selección interna como un algoritmo nuevo. No existen Champion municipal/espacial compatibles y no se construyen métricas ficticias. El peso0.5/0.5 no se ajusta y B1/B3 no entran en la mezcla.

{md(blendtable)}

MSE_mix=0.25MSE_A+0.25MSE_B+0.5mean(e_Ae_B), verificado numéricamente por repetición. El término cruzado es covarianza+producto de sesgos, distinto de correlación. Las tablas descomponen variación y sesgo, ganancias de error porparcela, concentración deSSE y sensibilidad a casos influyentes.

La mejoraRMSE0.49813→0.49360 yMAE0.35887→0.35343 se reproduce. Nueve repeticiones mejoranRMSE, pero reutilizan etiquetas. El resultado es una mezcla retrospectiva exploratoria; no demuestra transferencia ni independencia del descubrimiento. Los resultadoslocales,Q1–Q4 yChignahuapan/resto se evalúan por separado.

## Decisiones y diez respuestas

{md(decisions.set_index('model'))}

1. Objetivo local: B1 no reduce elRMSE equilibrado deforma consistente; B3 logra mejora pequeña enaleatoria/perfil.
2. Igualpeso: la pequeña mejora deB3 persiste, sin necesidad de dominar por cantidad deparejas.
3. Fuera deChignahuapan: B3 conserva mejora pequeña aleatoria/perfil; falla municipal/espacial.
4. Costo global: aleatoria empeora ligeramente ymunicipal mucho; no se recomienda adopción general.
5. Transferencia: espacial global mejora modestamente mientras municipal empeora; objetivoslocal/regional no son intercambiables.
6. Lambda: frecuentemente0; no existe una elección estable positiva entodoslosprotocolos.
7. DinámicaLAI: B3 aporta una mejora marginal de diferencias frente aB2, insuficiente para pagar eldeteriororegional.
8. Mezcla: compensa parcialmente errores y mejoraRMSE/MAE aleatorios; no se aprendieronpesos.
9. Pocoscasos: se cuantifica porparcela yexclusióndescriptiva decasos deSSE alto; esa selección posterior no es una reglaoperativa.
10. EtapaC: puede justificarse como hipótesisjerárquica independiente deagrupación/región, pero B no demuestra una mejora integral ni autoriza mayorcomplejidadpor sísolo. C/D no se ejecutaron.

Reproducción: `python scripts/342_stage_b_within_profile_learning.py`. Pruebas matemáticas: `python -m pytest tests/test_stage_b_objective.py -q`; integración: `tests/test_stage_b_integration.py`. Una versión finalizada es inmutable. Fuentes/código/folds/configuración/modelos/transformaciones ysalidas tienenSHA-256. Las59parcelas sinY quedan conservadas, sinpredicción final. No se sobrescriben EtapaA, Familia4/F4-E, E–M niChampion. La reutilización de138etiquetas mantiene sesgodeselecciónretrospectiva; se necesitan nuevasetiquetas/campañas/regiones para confirmación.
'''
    image_names=sorted(p.name for p in (out/'figures').glob('*.png'))
    for path,prefix in [(out/'report/technical_report.md','../figures/'),(b.ROOT/'documentation/territorial_program_stage_b.md','../'+(out/'figures').relative_to(b.ROOT).as_posix()+'/')]:
        path.write_text(text+'\n\n## Figuras\n\n'+'\n\n'.join(f'![{name}]({prefix}{name})' for name in image_names),encoding='utf8')
    print(rmse.round(5).to_string(),flush=True);print(local.round(5).to_string(),flush=True);print(blendtable.round(6).to_string(),flush=True)
