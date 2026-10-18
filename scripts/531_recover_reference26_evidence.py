"""Recover archived component evidence for26; no fitting, new tests or PRED read."""
from pathlib import Path
import csv
import hashlib
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/'results/reference26_component_evidence/v1'
PRIVATE=ROOT/'outputs/research/reference26_component_evidence/v1'
PROTOCOLS=['random','climate_profile','municipality','spatial']
REF='FULL7_ON_RAW_MASK'

CONTRASTS=[
 ('R3 final','FULL7_ON_RAW_BASE',REF,'Añadir R3 con máscara a la misma familia de base; corrector e intensidad calibrados internamente','Directo de arquitectura26'),
 ('Corrector interno','FULL7_OFF_RAW_MASK',REF,'Activar el corrector interno, manteniendo siete señales y gate geológico; recalibración posterior','Directo de arquitectura26'),
 ('Gate geológico','FULL7_ON_GLOBAL_MASK',REF,'Sustituir peso global por gate geológico, conservando corrector interno','Directo de arquitectura26'),
 ('Gate PCA2','FULL7_ON_PCA2_MASK',REF,'Comparar dos componentes del gate con las diez proporciones originales; mismas diez entradas','Sensibilidad de representación'),
 ('Historia NDVI local','NO_HISTORY_ON_RAW_MASK',REF,'Retirar conjuntamente media y std históricas del experto; historia en R3 permanece','Bloque retirado; hiperparámetros internos heredados'),
 ('Planet local','NO_PLANET_ON_RAW_MASK',REF,'Retirar las dos señales Planet juntas del experto','Bloque retirado; hiperparámetros internos heredados'),
 ('NDWI local','NO_NDWI_ON_RAW_MASK',REF,'Retirar media y std NDWI2025 juntas del experto','Bloque retirado; hiperparámetros internos heredados'),
 ('Pendiente media local','NO_SLOPE_ON_RAW_MASK',REF,'Retirar pendiente media del experto; pendiente mínima de R3 permanece','Columna retirada; hiperparámetros internos heredados'),
 ('Sin interno ni gate','FULL7_OFF_GLOBAL_MASK',REF,'Retirar simultáneamente corrección interna y geología, aprendiendo peso global','Combinación; no atribuir efecto a una sola retirada'),
 ('Compact14','NO_PLANET_OFF_GLOBAL_MASK',REF,'Retirar Planet, interno y geología; conservar experto5, peso global y R3','Combinación con reproducción independiente podada'),
 ('R3 en alternativa global','FULL7_OFF_GLOBAL_BASE','FULL7_OFF_GLOBAL_MASK','Añadir R3 al modelo sin corrector interno ni geología','Evidencia contextual en otra arquitectura'),
]


def main():
    PUB.mkdir(parents=True,exist_ok=True);PRIVATE.mkdir(parents=True,exist_ok=True)
    sources={}
    def read(relative):
        path=ROOT/relative;sources[relative]=hashlib.sha256(path.read_bytes()).hexdigest()
        return pd.read_csv(path)
    arch=read('outputs/modeling/architecture_decomposition/v1/tables/metrics_summary.csv')
    bd=read('outputs/modeling/base_distribution_correction/v1/tables/metrics_summary.csv')
    ind=read('outputs/modeling/indicator_neighborhoods/v1/tables/metrics_summary.csv')
    weights=read('outputs/modeling/architecture_decomposition/v1/tables/component_weights.csv')
    tests=read('outputs/modeling/architecture_decomposition/v1/tables/paired_tests.csv')
    bdtests=read('outputs/modeling/base_distribution_correction/v1/tables/paired_tests.csv')
    indtests=read('outputs/modeling/indicator_neighborhoods/v1/tables/paired_tests.csv')
    interactions=read('outputs/modeling/architecture_decomposition/v1/tables/MSE_interactions_summary.csv')
    regions=read('outputs/modeling/architecture_decomposition/v1/tables/regions_summary.csv')
    omissions=read('outputs/modeling/architecture_decomposition/v1/tables/omissions_summary.csv')
    complexity=read('outputs/modeling/architecture_decomposition/v1/tables/complexity_inventory.csv')
    current=read('results/current_champions/v1/metrics.csv')
    reference=arch[arch.experiment==REF].set_index('protocol')
    for protocol in PROTOCOLS:
        row=current[(current.experiment=='Reference26')&(current.protocol==protocol)].iloc[0]
        for metric in ['rmse','r2','mae','bias']:np.testing.assert_allclose(row[metric],reference.loc[protocol,metric],rtol=0,atol=1e-12)
    contrasts=[]
    for factor,variant,reference_name,question,scope in CONTRASTS:
        for protocol in PROTOCOLS:
            a=arch[(arch.experiment==variant)&(arch.protocol==protocol)].iloc[0]
            b=arch[(arch.experiment==reference_name)&(arch.protocol==protocol)].iloc[0]
            row=dict(factor=factor,variant=variant,reference=reference_name,protocol=protocol,question=question,evidence_scope=scope)
            for metric in ['rmse','r2','mae','bias']:
                row['variant_'+metric]=a[metric];row['reference_'+metric]=b[metric];row['delta_'+metric+'_variant_minus_reference']=a[metric]-b[metric]
            contrasts.append(row)
    contrast=pd.DataFrame(contrasts);contrast.to_csv(PUB/'component_contrasts.csv',index=False)
    names={REF,'CT3_BASE',*[x for _,a,b,_,_ in CONTRASTS for x in (a,b)],'NDWI_SLOPE_OFF_GLOBAL_MASK','HISTORY_SLOPE_OFF_GLOBAL_MASK'}
    selected=arch[arch.experiment.isin(names)].copy();selected.to_csv(PUB/'architecture_metrics.csv',index=False)
    local=arch[arch.experiment.str.match(r'NO_(HISTORY|PLANET|NDWI|SLOPE)_ON_RAW_MASK')].copy()
    local.to_csv(PUB/'local_block_metrics.csv',index=False)
    bw=weights[weights.experiment.isin(names)];bw.to_csv(PUB/'component_weights.csv',index=False)
    cx=complexity[complexity.experiment.isin(names)];cx.to_csv(PUB/'complexity_and_calibration_dependencies.csv',index=False)
    rt=tests[tests.experiment.isin(names)&tests.reference.isin(names)].copy();rt.to_csv(PUB/'archived_tests_selected.csv',index=False)
    interactions[interactions.local=='FULL7'].to_csv(PUB/'archived_FULL7_interactions.csv',index=False)
    r3names=['J7_BOTH','J7_GLOBAL_R2','J7_GLOBAL_R3','J7_GLOBAL_R4','J7_GLOBAL_R9','J7_KNN_SATELLITE_DIRECT']
    r3=ind[ind.experiment.isin(r3names)];r3.to_csv(PUB/'historical_R3_reductions.csv',index=False)
    basenames=['CT3_BASE','J7_BASE','SHARES_BASE','SHARES_GLOBAL_GLOBAL','EXPERT7_GLOBAL_GLOBAL','RAW7_GLOBAL_GLOBAL','EQUAL7_GLOBAL_GLOBAL']
    historical=bd[bd.experiment.isin(basenames)];historical.to_csv(PUB/'historical_base_controls.csv',index=False)
    region_selected=regions[regions.experiment.isin([REF,'FULL7_ON_RAW_BASE','NO_PLANET_OFF_GLOBAL_MASK','FULL7_ON_GLOBAL_MASK'])]
    region_selected.to_csv(PRIVATE/'regional_comparisons.csv',index=False)
    omit_selected=omissions[omissions.experiment.isin(names)]
    omit_selected.to_csv(PRIVATE/'omission_comparisons.csv',index=False)
    fields=json.loads((ROOT/'configs/current_champions_inputs.json').read_text(encoding='utf-8'))['features']
    inventory=[]
    for i,feature in enumerate(fields):
        if i<4:role='Base C-T3 y corrector interno';level='Asociación y ablación individual en C-T3, no en26 completo';source='results/core4_relevance/v1/README.md'
        elif i<11:
            role='Regresión del experto local'
            block='NDVI histórico' if i<6 else 'Planet2025' if i<8 else 'NDWI2025' if i<10 else 'pendiente media'
            level=('Retirada individual de columna' if i==10 else 'Retirada conjunta de bloque: '+block)+'; hiperparámetros internos heredados de FULL7';source='documentation/architecture_decomposition_conclusions.md'
        elif i<13:role='Selección y ponderación de24 vecinos';level='Controles históricos de vecindario; k24 fijo, sin prueba de optimalidad en26';source='documentation/geoc_signal_research_results.md'
        elif i<23:role='Agrupación geológica y peso entre expertos';level='Ablación del bloque10 y PCA2; no retirada individual de cada categoría';source='documentation/architecture_decomposition_conclusions.md'
        else:
            role='Corrector global R3'
            level='Retirada de R3 completo en26; retirada de NDVI floor R3→R2 sólo en J7' if i==23 else 'Retirada de R3 completo en26; no ablation individual exacta recuperada'
            source='documentation/indicator_neighborhoods_conclusions.md'
        inventory.append(dict(feature=feature,role=role,evidence_level=level,evidence_document=source))
    pd.DataFrame(inventory).to_csv(PUB/'variable_role_evidence26.csv',index=False)
    audit=dict(source_only=True,new_training=0,new_hypothesis_tests=0,PRED_read=False,reference26_metric_parity=True,
        components_compared=len(CONTRASTS),comparison_rows=len(contrast),variables=len(inventory),
        archived_families={name:dict(tests=len(table),significant_holm=int((table.p_holm<.05).sum())) for name,table in [('architecture',tests),('base_distribution',bdtests),('indicator_neighborhoods',indtests)]})
    (PUB/'audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8',newline='\n')
    (PUB/'provenance.json').write_text(json.dumps(dict(source_sha256=sources,code_sha256=hashlib.sha256(Path(__file__).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),code_hash_encoding='CRLF normalized to LF; raw input bytes'),indent=2)+'\n',encoding='utf-8',newline='\n')
    with pd.ExcelWriter(PRIVATE/'evidencia_componentes26.xlsx') as writer:
        for name,table in [('contrasts',contrast),('architecture_metrics',selected),('local_blocks',local),('weights',bw),('calibration_dependencies',cx),('archived_tests',rt),('R3_history',r3),('historical_controls',historical),('variable_roles',pd.DataFrame(inventory)),('regional',region_selected),('omissions',omit_selected)]:table.to_excel(writer,sheet_name=name,index=False)
    report(arch,contrast,bw,r3,historical,audit)
    print(json.dumps(audit,indent=2))


def report(arch,contrast,weights,r3,historical,audit):
    def table(frame,names):
        text='| Modelo / variante | Aleatoria | Perfil | Municipal | Espacial |\n|---|---|---|---|---|\n'
        for name,label in names:
            cells=[]
            for p in PROTOCOLS:
                r=frame[(frame.experiment==name)&(frame.protocol==p)].iloc[0];cells.append(f'{r.rmse:.4f} / {r.r2:.4f}')
            text+='| '+label+' | '+' | '.join(cells)+' |\n'
        return text+'\n'
    text='# Reference26: evidencia recuperada por componente y por función\n\n'
    text+='**Se recuperaron resultados ya ejecutados; no se entrenó ningún modelo ni se hizo una nueva selección.** Champions vigentes: Reference26 y Compact14. Las tablas principales se refieren a las mismas65 particiones y138 rendimientos; cada celda es **RMSE t/ha / R²**. MAE, sesgo, diferencias y procedencia se conservan en CSV y Excel. El banco97/41 es independiente como tabla, no como muestra, y no tiene todas estas ablaciones: [comparación97/41](../../comparison_97_41/v1/README.md). No se mezclan sus cifras.\n\n'
    text+='## Cómo interpretar el respaldo\n\n'
    text+='La función asignada a un componente es una hipótesis arquitectónica. Una retirada emparejada permite estudiar su aporte condicional al resto; un control en una arquitectura anterior sólo aporta evidencia contextual. Una combinación que cambia tres piezas no atribuye su diferencia a una sola. Ninguna de estas comparaciones demuestra causalidad, optimalidad universal o significancia individual de26 entradas.\n\n'
    text+='En las ablaciones ON de la batería factorial, se reajustaron coeficientes del corrector interno con residuos propios, **pero se heredaron de FULL7 sus hiperparámetros e intensidad del mismo entrenamiento**. Por tanto, una retirada de bloque no equivale necesariamente a eliminar sus fuentes de toda la calibración. Las reconstrucciones OFF/GLOBAL de14 y12 sí verificaron independencia de las fuentes retiradas.\n\n'
    text+='## 1. Núcleo C-T3: ancla agroclimática\n\n'
    text+='Función: ofrecer una estimación global estable de cantidad/distribución de lluvia y vegetación temprana; también permitir corregir errores del experto local. La evidencia específica de sus cuatro entradas está en [asociación y ablaciones recientes](../../core4_relevance/v1/README.md): total, fracción temprana y NDVI tienen respaldo más consistente; HHI muestra debilidad espacial. Esto no se transfiere automáticamente a su doble uso dentro de26.\n\n'
    text+='Los pesos aprendidos de26 muestran cuánto usa el sistema esa ancla. No son reglas manuales por protocolo ni p-valores de relevancia:\n\n| Protocolo | Peso medio experto7 | Peso medio C-T3 | Amplitud media corrector interno | Corrección R3 absoluta media, t/ha |\n|---|---|---|---|---|\n'
    for p in PROTOCOLS:
        r=weights[(weights.experiment==REF)&(weights.protocol==p)].iloc[0]
        text+=f'| {p} | {r.expert_weight:.3f} | {1-r.expert_weight:.3f} | {r.internal_amplitude:.3f} | {r.mean_abs_R3:.4f} |\n'
    text+='\nEn municipal, la mezcla asigna en promedio sólo≈.099 al experto y≈.901 a C-T3 **antes de R3**. Es evidencia del mecanismo de respaldo aprendido, no de que el experto aislado generalice a municipios nuevos ni de una regla que debamos programar con esos porcentajes.\n\n'
    text+='## 2. Siete señales locales: relevancia conjunta y sustitutos\n\n'
    text+='Función: permitir que una regresión por vecindario distinga parcelas con condiciones vegetativas y relieve diferentes. Se recuperaron estas retiradas, manteniendo gate geológico, corrector interno y R3 con recalibración posterior:\n\n'
    text+=table(arch,[(REF,'26 completo'),('NO_HISTORY_ON_RAW_MASK','Sin media/std NDVI histórico del local'),('NO_PLANET_ON_RAW_MASK','Sin las dos Planet del local'),('NO_NDWI_ON_RAW_MASK','Sin media/std NDWI2025 del local'),('NO_SLOPE_ON_RAW_MASK','Sin pendiente media del local')])
    text+='- **NDVI histórico, media/std:** quitar ambos apenas cambia aleatoria, empeora algo perfil/municipal y espacial. Su aporte marginal es pequeño en esta composición. La historia NDVI sigue en R3; no es una prueba de retirar toda la historia.\n'
    text+='- **Planet, cambios de dirección EVI y delta NDVI junio–agosto:** retirarlos mejora ligeramente aleatoria/municipal/espacial, pero pierde por perfil. Pueden describir dinámica temporal, pero no hay respaldo de necesidad universal ni de que cada señal sea indispensable.\n'
    text+='- **NDWI2025, media/std:** la retirada empeora ligeramente aleatoria/perfil/municipal y prácticamente no cambia espacial. Respaldo observado pequeño y dependiente del sistema; no prueba de humedad del suelo o anegamiento.\n'
    text+='- **Pendiente media:** retirarla pierde por perfil y mejora algunas otras cifras. Pendiente mínima sigue en R3. El estudio respalda un compromiso contextual de relieve, no que la pendiente media tenga un aporte positivo uniforme.\n\n'
    text+='Para los tres pares de señales se evaluó la retirada conjunta, **no cada columna por separado**. Su información puede estar compartida con otras señales. Los siete predictores no son siete componentes PCA ni siete variables con p-valores individuales significativos.\n\n'
    text+='## 3. Vecinos geográficos y Ridge local\n\n'
    text+='Función: construir un referente territorial con rendimientos conocidos y permitir relaciones locales. En26 se conservan24 vecinos geográficos, Ridge alpha30 y ponderación inversa de distancia. Las coordenadas eligen vecinos; las siete señales son predictores de la regresión, no la distancia de selección.\n\n'
    text+='Los controles históricos de [reducción del experto GeoC](../../../documentation/geoc_signal_research_results.md) compararon local sin clima con media ponderada de los mismos vecinos: RMSE aleatorio≈.4911 frente a.4974 y espacial≈.9807 frente a.9807. La proximidad recuperaba gran parte del comportamiento; la regresión añadía una diferencia menor. Es evidencia contextual sobre otro experto, **no una comparación Ridge7 frente a media o frente a Ridge global dentro del26 final**.\n\n'
    text+='No se recuperó una prueba que demuestre que k24 sea óptimo para26. Los k8/16/24/48/72 de las investigaciones de correctores locales corresponden a **otro mecanismo**, no al experto geográfico de26. La función de vecinos está implementada y auditada, pero su indispensabilidad y número óptimo en esta receta no están aislados. [Funcionamiento exacto](../../../documentation/models/Reference26/README.md).\n\n'
    text+='## 4. Corrector interno: complementar al Ridge con el núcleo compacto\n\n'
    text+='Función: aprender, mediante Elastic Net sobre las cuatro entradas C-T3, patrones en residuos OOF del experto local. Tiene coeficientes propios; no es sumar otra vez la predicción C-T3.\n\n'
    text+=table(arch,[(REF,'26 con interno'),('FULL7_OFF_RAW_MASK','Misma familia sin interno'),('FULL7_ON_GLOBAL_MASK','Interno y peso global'),('FULL7_OFF_GLOBAL_MASK','Sin interno y peso global')])
    text+='Quitar sólo esa capa con gate geológico pierde en los cuatro protocolos. **Es uno de los respaldos condicionales más claros de una función del26**, aunque las diferencias no sobreviven el ajuste múltiple de aquella batería. Con peso global, mantener el interno perjudica municipal y espacial frente a quitarlo. La capa no es siempre beneficiosa por sí sola: depende de cómo se mezcla el experto con C-T3.\n\n'
    text+='## 5. Compuerta geológica: repartir confianza entre expertos\n\n'
    text+='Función: usar composición geológica para agrupar parcelas y aprender pesos convexos con contracción hacia un peso global. No estima directamente rendimiento con diez coeficientes ni selecciona los24 vecinos.\n\n'
    text+=table(arch,[(REF,'Geología10 + interno'),('FULL7_ON_GLOBAL_MASK','Peso global + interno'),('FULL7_ON_PCA2_MASK','PCA2 de las diez proporciones + interno'),('FULL7_OFF_GLOBAL_MASK','Peso global sin interno')])
    text+='Con el interno conservado, reemplazar geología por un peso global pierde aleatoria, municipal y espacial, aunque mejora por perfil. La mayor pérdida municipal respalda su función de asignación de confianza **en esa composición**. PCA2 conserva resultados próximos, pero mantiene las diez entradas originales y añade una transformación: no es un gate de dos mediciones.\n\n'
    text+='Quitar interno y geología conjuntamente reduce mucho la pérdida frente a las retiradas individuales. La interacción MSE municipal≈−.0381 y espacial≈−.0379 documenta no aditividad; no es un efecto causal. Tampoco se probó retirar una por una las diez categorías para identificar una categoría imprescindible. La compuerta es una alternativa útil, **no la única manera respaldada de combinar expertos**.\n\n'
    text+='## 6. R3: corregir estructura residual con soporte explícito\n\n'
    text+='Función: corregir errores de la mezcla mediante nivel histórico NDVI mínimo, persistencia de heterogeneidad anómala2025 y pendiente mínima. Se ajusta a residuos propios cross-fitted, es global, conserva signo aprendido y está limitado a±.25t/ha. La máscara apaga el ajuste cuando falta un indicador.\n\n'
    text+=table(arch,[('FULL7_ON_RAW_BASE','Base26 sin R3'),(REF,'26 con R3 y máscara'),('FULL7_OFF_GLOBAL_BASE','Alternativa global sin R3'),('FULL7_OFF_GLOBAL_MASK','Alternativa global con R3')])
    text+='R3 mejora los cuatro protocolos en ambas arquitecturas recuperadas. En26 espacial pasa de.6894 a.6333, con mejora también en las otras validaciones. **Es el respaldo observado más consistente de un bloque completo**; no demuestra que cada indicador sea indispensable. Puede mejorar un agregado y perjudicar una región. Los CSV/Excel conservan regiones, omisiones y magnitud de ajuste para examinar ese límite.\n\n'
    text+='### Qué respaldo existe para sus tres indicadores\n\n'
    text+=table(r3,[('J7_BOTH','J7 anterior sin corrector'),('J7_GLOBAL_R2','J7 + persistencia y pendiente mínima'),('J7_GLOBAL_R3','J7 + NDVI floor, persistencia y pendiente mínima'),('J7_GLOBAL_R4','J7 + R3 y FAPAR floor'),('J7_GLOBAL_R9','J7 + nueve indicadores')])
    text+='**NDVI floor:** R3 frente a R2 añade únicamente esa representación, con corrección recalibrada en la base J7 anterior. Mejora aleatoria/perfil/municipal y empeora ligeramente espacial: aporte contextual, no ventaja universal dentro del26. **Persistencia y pendiente mínima:** se recuperó evidencia del conjunto R2/R3, pero no retiradas individuales exactas de cada una dentro del26 final. No se les asigna un p-valor ni una ganancia propia inventada. FAPAR adicional y nueve indicadores no mejoran uniformemente a R3; más información no produjo automáticamente mejor predicción.\n\n'
    text+='Los109 casos con historia completa y29 incompletos de entrenamiento tienen distinto soporte. La máscara es una protección ante falta de referencia histórica; su efecto aislado con los mismos coeficientes y fuerza R3 no queda demostrado por el mero contraste añadir/quitar R3. Las sensibilidades antiguas de atenuación por vecinos mezclan disponibilidad y ponderación; no prueban una regla universal de corregir más a parcelas atípicas.\n\n'
    text+='## 7. Arquitectura completa: simplificación y función compartida\n\n'
    text+=table(arch,[(REF,'26 actual'),('FULL7_OFF_GLOBAL_MASK','16: experto7, global, sin interno, con R3'),('NO_PLANET_OFF_GLOBAL_MASK','14 actual'),('NDWI_SLOPE_OFF_GLOBAL_MASK','12: NDWI y pendiente, global, R3'),('HISTORY_SLOPE_OFF_GLOBAL_MASK','12: historia NDVI y pendiente, global, R3')])
    text+='14 elimina Planet, interno y geología con pérdidas pequeñas de RMSE, y mejora algunas métricas de sesgo/MAE. Es evidencia de sustitución y complementariedad, no prueba de que las piezas retiradas carezcan de señal. La auditoría podada comprobó independencia de esas fuentes para14. Ninguna combinación domina todos los protocolos, municipios y extremos; la pequeña diferencia26–14 no certifica equivalencia.\n\n'
    text+='## Fuerza estadística, faltantes y conclusión defendible\n\n'
    text+='Las familias archivadas contienen:\n\n| Batería | Contrastes archivados | Superan Holm al5% |\n|---|---|---|\n'
    for name,r in audit['archived_families'].items():text+=f"| {name} | {r['tests']} | {r['significant_holm']} |\n"
    text+='\nSe conservan sus ajustes originales: no se recalcularon p-valores con una familia menor para hacerlos significativos. Falta de significancia no demuestra ausencia de aporte ni equivalencia; hay sólo nueve municipios y cinco bloques. Los intervalos y contrastes sobre OOF fijas no incorporan toda la selección histórica o incertidumbre de reentrenamiento. Muchos experimentos usan las mismas138 etiquetas.\n\n'
    text+='**Qué puede afirmarse:**26 combina una base global, un referente local y una corrección residual con funciones explícitas y mejoras condicionales observadas. R3 y el corrector interno tienen respaldo de bloque; el gate ayuda en ciertas composiciones; las siete señales contienen sustitutos; k24 y las26 columnas no quedaron certificados como necesarios individualmente.\n\n'
    text+='**Qué falta realmente:** sensibilidad HHI en los dos usos de26; retiradas individuales de los pares locales si se necesita atribución por columna; retiradas individuales de persistencia/pendiente mínima; contraste local7 versus media y Ridge global dentro del26; sensibilidad propia k del experto; confirmación con rendimientos independientes. Este informe no ejecuta esas nuevas pruebas ni cambia champions.\n\n'
    text+='## Fuentes, tablas y reproducción\n\n'
    text+='[Ficha26](../../../documentation/models/Reference26/README.md) · [Descomposición factorial](../../../documentation/architecture_decomposition_conclusions.md) · [Bases y distribución](../../../documentation/base_distribution_correction_conclusions.md) · [Reducción R3](../../../documentation/indicator_neighborhoods_conclusions.md) · [Simplificación J7](../../../documentation/joint_simplification_results.md).\n\n'
    text+='Script: `python scripts/531_recover_reference26_evidence.py`. [Auditoría](audit.json) verifica igualdad de métricas del26 con el registro vigente. [Procedencia](provenance.json) conserva hashes de tablas recuperadas. [Contrastes por componente](component_contrasts.csv), [inventario de evidencia de26 variables](variable_role_evidence26.csv), [métricas](architecture_metrics.csv), [pruebas archivadas seleccionadas](archived_tests_selected.csv) y [dependencias de calibración](complexity_and_calibration_dependencies.csv). Excel privado: `outputs/research/reference26_component_evidence/v1/evidencia_componentes26.xlsx`, con hojas regionales y omisiones. No se publican predicciones o filas por parcela.\n'
    (PUB/'README.md').write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':main()
