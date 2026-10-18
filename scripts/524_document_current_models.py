"""Build current model cards and an explicit, non-destructive historical status map.

Only documentation and registry metadata are changed. No fitting or prediction.
"""
from pathlib import Path
import csv
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]


def write(path, text):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')


def fresh_metrics():
    path=ROOT/'results/comparison_97_41/v1/metrics.csv'
    if not path.exists():return {}
    with path.open(encoding='utf-8',newline='') as stream:
        return {r['experiment']:r for r in csv.DictReader(stream)}


CORE = [
    ('compact_precip_total', 'Precipitación acumulada abril–octubre de 2025; cantidad de lluvia.'),
    ('compact_early_fraction', 'Fracción de lluvia abril–junio respecto al total abril–octubre; distribución temprana.'),
    ('compact_concentration_hhi', 'Suma de cuadrados de las participaciones mensuales; concentración temporal de lluvia.'),
    ('S2_ndvi_month_05', 'NDVI Sentinel-2 de mayo de 2025; estado de vegetación temprano.'),
]
LOCAL = [
    ('sat_basic_hist__sentinel_2__ndvi_promedio__mean', 'Media histórica de NDVI promedio Sentinel-2; abril–octubre, hasta 2024 según manifiesto GeoC.'),
    ('sat_basic_hist__sentinel_2__ndvi_promedio__std', 'Dispersión histórica de NDVI promedio Sentinel-2; abril–octubre, hasta 2024 según manifiesto GeoC.'),
    ('emp_shape__y2025_planet_evi__turning_fraction', 'Fracción de pendientes consecutivas que cambian de signo en los siete resúmenes mensuales EVI Planet, abril–octubre de 2025; forma empírica, no etapa fenológica observada.'),
    ('agro_pheno__y2025_planet_ndvi__jun_to_aug_delta', 'NDVI Planet de agosto menos NDVI de junio de 2025.'),
    ('sat_basic_2025__sentinel_2__ndwi_promedio__mean', 'Media de NDWI Sentinel-2 en 2025.'),
    ('sat_basic_2025__sentinel_2__ndwi_promedio__std', 'Dispersión de NDWI Sentinel-2 en 2025.'),
    ('topo_official__slope__mean', 'Pendiente topográfica media en grados; estadístico zonal de Pendiente_INEGI_CEM4_120m_grados.tif según manifiesto GeoC.'),
]
COORDS = [('base_centroid_lat', 'Latitud del centroide: selección y ponderación de vecinos geográficos.'),
          ('base_centroid_lon', 'Longitud del centroide: selección y ponderación de vecinos geográficos.')]
GEO = [('geology_physiography::geo250_share__' + c,
        'Proporción cartográfica de la categoría ' + c + '; entrada de la compuerta, no coeficiente directo de rendimiento.')
       for c in ['Q(B)', 'Q(B-Bvb)', 'Q(Bvb)', 'Q(al)', 'Ts(A)', 'Ts(B)', 'Ts(R)', 'Ts(R-Ta)', 'Ts(Ta)', 'Ts(Ti)']]
R3 = [
    ('I_history_ndvi_floor', 'Media 2022–2024 de medias anuales de medianas mensuales de NDVI mínimo, mayo–octubre; exige tres años completos.'),
    ('I_gap_excess_persistence', 'Persistencia del exceso positivo de la brecha relativa NDVI promedio−mínimo en mayo–octubre de 2025 frente a los mismos meses de 2022–2024: (suma z+)²/(6·suma z+²). Brecha normalizada por max(|NDVI promedio|,.1), limitada a [0,5]; piso de SD histórica .05 y z limitado a ±6. Cero si no hay exceso; faltante si falta soporte mensual.'),
    ('I_slope_min', 'Pendiente mínima TOPO_BASIC_slope_min; contexto topográfico del corrector, no pendiente temporal de NDVI.'),
]
SETS = {'CT3': CORE, 'Reference26': CORE + LOCAL + COORDS + GEO + R3,
        'Compact14': CORE + [v for v in LOCAL if 'planet' not in v[0]] + COORDS + R3}
SETS['B1'] = SETS['Reference26']
METRICS = {
    'CT3': ['.5116 / .6361 / .3749', '.5206 / .6232 / .3915', '.5813 / .5302 / .4603', '.6788 / .3594 / .5306'],
    'Reference26': ['.4748 / .6865 / .3396', '.4774 / .6831 / .3342', '.5752 / .5400 / .4491', '.6333 / .4423 / .5004'],
    'Compact14': ['.4773 / .6832 / .3399', '.4793 / .6805 / .3336', '.5755 / .5395 / .4468', '.6431 / .4250 / .5140'],
    'B1': ['.4755 / .6856 / .3396', '.4839 / .6744 / .3408', '.5681 / .5513 / .4426', '.6813 / .3546 / .5388'],
    'L40': ['.4930 / .6619 / .3526', '.5031 / .6481 / .3479', '.7602 / .1964 / .5991', '.9794 / −.3337 / .7434'],
}
DETAILS = {
'CT3': '''## Función y arquitectura

**Control compacto, no champion actual.** Elastic Net global sobre cuatro entradas. La imputación y estandarización se ajustan con el entrenamiento correspondiente. La selección interna compara alpha [.001,.01,.1,1] y l1_ratio [.1,.5,.9]. No tiene experto local ni compuerta ni corrección R3.

## Origen y evidencia

La exploración de lluvia y temperatura y las representaciones compactas llevaron al núcleo de tres resúmenes de lluvia más NDVI de mayo. Se conserva como C-T3 en las investigaciones de información incremental y residual; F5, F6 y F7 reutilizan esas cuatro entradas para aislar el efecto de arquitectura. Véanse [exploración de clima](../../h_rain_tmax_extension.md), [investigación C-T3](../../ct3_residual_conditional.md) y [comparación de líderes](../../four_leaders_comparison.md). Estas son etapas de procedencia; no se atribuye su selección a un único p-valor.

## Ventajas y límites

Cuatro entradas, un modelo global y bajo costo operativo. Es la referencia más fácil de explicar y conserva buena proporción de errores moderados. En la comparación de líderes, su proporción espacial dentro de ±.5 t/ha supera la de 26, aunque 26 reduce más los errores grandes. No domina toda la distribución del error.

La forma global lineal limita interacciones y diferenciación entre parcelas con valores idénticos. Comprime extremos. El R² global incorpora diferencias entre regiones y no implica el mismo poder explicativo dentro de cada estado. Tampoco es un modelo exclusivamente climático: incluye NDVI.
''',
'Reference26': '''## Función y arquitectura

**Champion actual de precisión y equilibrio territorial.** Alias: FULL7_ON_RAW_MASK y, en su etapa previa, SHARES_MASK.

`predicción = C-T3 + g(geología)·(experto7 − C-T3) + intensidad·soporte_R3·delta_R3`.

El experto utiliza siete señales no climáticas, estandarizadas en entrenamiento, en Ridge local de 24 vecinos geográficos, alpha30 y potencia de distancia1. Incluye una corrección Elastic Net interna sobre residuos propios con las cuatro entradas C-T3. Las dos coordenadas eligen vecinos; las diez proporciones geológicas gobiernan una mezcla convexa entre expertos mediante agrupaciones físicas y pesos regularizados. No son diez correcciones aditivas independientes ni un vecino elegido por similitud satelital.

R3 emplea tres indicadores en Elastic Net (alpha .01, l1_ratio .5); su salida se limita a ±.5 y multiplica por .5. La intensidad 0/.5/1 se selecciona internamente. La corrección máxima resultante es ±.25 t/ha y se desactiva para la parcela si falta cualquiera de sus tres indicadores. Imputación, escalado y calibración se ajustan dentro del entrenamiento correspondiente.

## En qué etapa surgió cada bloque

1. [Reparto de señales](../../signal_role_allocation_results.md): separar un núcleo compacto de un experto local no climático y estudiar dónde ubicar correcciones.
2. [Simplificación conjunta](../../joint_simplification_results.md): reducir el experto amplio a señales concretas; las siete locales no son componentes PCA.
3. [Indicadores temporales](../../temporal_indicator_weights_conclusions.md): los diagnósticos de residuos y contrastes motivaron indicadores de nivel histórico, heterogeneidad persistente y relieve, sin reglas exclusivas para parcelas difíciles.
4. [Corrección de bases](../../base_distribution_correction_conclusions.md): integración R3 con soporte explícito y mezcla condicionada a composición geológica.
5. [Descomposición factorial](../../architecture_decomposition_conclusions.md): FULL7_ON_RAW_MASK quedó como referencia de 26 entradas; la comparación posterior y la decisión del responsable la adoptaron como champion.

## Ventajas y límites

Menor RMSE observado que C-T3 y L40 en los cuatro protocolos compatibles; frente a 14 la ventaja es pequeña, especialmente en aleatoria. Reduce la cola de errores y la dispersión espacial. Conserva una base compacta y separa el papel de señales locales, mezcla y corrección.

Requiere más fuentes, dos señales Planet, composición geológica y varias capas de calibración. Los vecinos siguen siendo geográficos; no garantiza extrapolación a regiones nuevas. En espacial su sesgo +.2285 es mayor que el +.1232 de 14, aunque su RMSE es menor por menor dispersión. No mejora todas las parcelas o municipios: L40 conserva ventajas en Almoloya y Cuautepec. La mejora intraperfil es modesta y depende del soporte. Las 26 entradas no equivalen a 26 parámetros ajustables ni justifican un R² ajustado clásico.
''',
'Compact14': '''## Función y arquitectura

**Champion actual compacto.** Alias: NO_PLANET_OFF_GLOBAL_MASK.

`predicción = C-T3 + w·(Ridge_local5 − C-T3) + intensidad·soporte_R3·delta_R3`.

El Ridge local usa 24 vecinos geográficos, alpha30 y potencia1. Cinco señales describen el experto; dos coordenadas seleccionan vecinos. El peso convexo global w se aprende con predicciones internas fuera de muestra: no es un 50/50 fijo ni un peso por municipio. R3 conserva los tres indicadores, su máscara de disponibilidad, Elastic Net alpha .01/l1_ratio .5 y corrección máxima ±.25 t/ha con intensidad elegida internamente.

## Origen y análisis de simplificación

Parte de la arquitectura de 26 y de su [simplificación factorial](../../architecture_decomposition_conclusions.md). Quitar únicamente el corrector interno no mejoró el sistema completo. La combinación de retirar Planet, retirar el corrector interno y reemplazar la compuerta geológica por un peso global produjo una alternativa distinta, cercana a la referencia.

La reconstrucción podada independiente verificó las mismas predicciones en los 65 folds sin calibrar con las fuentes retiradas. Esto sustenta **14 entradas para calibración y predicción**, no sólo 14 columnas visibles al final. Véanse [implementación podada](../../../src/pruned_global_architecture.py) y [comparación posterior](../../four_leaders_comparison.md).

## Ventajas y límites

Elimina Planet, las diez proporciones geológicas, la agrupación de la compuerta y el corrector climático interno del experto. Reduce 46.2% de entradas respecto a 26, con pérdidas observadas pequeñas en RMSE. Mantiene Sentinel histórico, NDWI2025, pendiente y corrección R3. Su sesgo espacial es menor que el de 26.

No elimina geografía, historia ni topografía. Su error espacial y el comportamiento en el cuartil alto son peores que los de 26; menor sesgo no significa menor error total. Sigue siendo un sistema compuesto y no una única regresión de 14 coeficientes. No se ha demostrado equivalencia estadística con 26. El bundle conjunto contiene 26 columnas para servir ambos champions; eso no cambia las 14 dependencias de esta receta.
''',
'B1': '''## Función y arquitectura

**Sensibilidad, no champion.** `B1 = C-T3 + a·(Reference26 − C-T3)`, con a limitado a [0,1]. Sus entradas son exactamente las 26 de Reference26; añadir un peso aprendido no añade una fuente, pero tampoco simplifica el sistema.

El peso minimiza pérdida cuadrática sobre predicciones honestas de validación interna, con los expertos recalibrados dentro del entrenamiento. No se escoge mirando el fold externo, por reglas municipales ni por el acuerdo con L40. Cada ajuste aprende su propio peso.

## Origen y evidencia

Surge de la [batería de mezclas B1–B6](../../four_expert_combinations_conclusions.md), motivada por complementariedad entre el comportamiento central de C-T3 y los extremos de 26. Véanse [diseño congelado](../../four_expert_combinations_design.md) y [resultados](../../four_expert_combinations_results.md). No es EQUAL3 ni una mezcla de L40.

## Ventajas y límites

Ofrece una interpolación interpretable entre dos predicciones y el menor RMSE municipal observado entre los cinco modelos de esta comparación. En aleatoria queda cerca de 26.

Pierde espacial frente a ambos champions y no reduce sus dependencias. La ventaja municipal no justifica sustituir26 globalmente. Pesos distintos entre entrenamientos pueden empeorar una métrica agregada aunque cada predicción sea convexa entre sus dos extremos. La selección histórica de muchas alternativas impide presentar esa ventaja como confirmación independiente.
''',
'L40': '''## Función y arquitectura

**Benchmark fuerte del equipo, procedente de GeoC; no champion actual de fira_nuria.** Alias Local04D / LOCAL04D. Representación C4 de **2,082 variables originales**, imputación, estandarización y PCA20; Ridge local ponderado con 24 vecinos geográficos, alpha30 y potencia1. Cada consulta ajusta una regresión en su vecindario.

Los veinte componentes son combinaciones de las entradas originales, **no veinte variables originales seleccionadas**. Los centroides determinan vecinos. C4 integra características base, agronómicas y empíricas derivadas de series por parcela; la PCA conserva ejes de variabilidad conjunta, no una lista de veinte señales agronómicas significativas.

## Variables y trazabilidad

La receta conserva la representación C4 original de GeoC. El [inventario completo de 2,082 entradas](variables_C4_2082.csv) contiene nombre, capa, fuente, modo y descripción original: **1,397 base, 350 agronómicas y 335 empíricas**. Se reconstruyó aplicando la función original de selección y el filtro de columnas no vacías/no constantes a las tablas locales originales, sin ajustar PCA ni leer rendimientos. La [procedencia y hashes](inventory_provenance.json) y el [script de reconstrucción](../../../scripts/525_inventory_l40_inputs.py) permiten revisar el procedimiento.

Este catálogo no se sustituye por el de 1,831 señales no climáticas: corresponde a otra variante. Las descripciones genéricas del manifiesto se conservan como tales; no se inventan fórmulas ausentes. Reconstruir los nombres a partir de las fuentes locales actuales no reaudita cada transformación original ni certifica de nuevo las cargas históricas de PCA.

El [puente y su auditoría](../../geoc_bridge_results.md), el [inventario de señales GeoC](../../geoc_variable_signal_audit.md) y la [comparación compatible](../../four_leaders_comparison.md) distinguen esas representaciones. No se atribuye importancia puntual o causal a variables originales a partir de veinte componentes sin analizar cargas y ablaciones.

## Origen y protocolo

Es el modelo fuerte de la investigación del compañero, previo al puente entre repositorios. Su representación PCA se ajustó con X de las 197 parcelas, sin rendimientos ocultos: es un planteamiento transductivo. La evaluación compatible de fira_nuria conserva esa representación y reconstruye la receta local con exclusión de etiquetas externas. No equivale a una PCA inductiva reentrenada únicamente en cada fold.

## Ventajas y límites

Fuerte bajo particiones aleatorias y con vecinos territoriales representados; conserva ventajas locales en Almoloya y Cuautepec. Motivó estudiar separación de clima y señales complementarias y el experto local que antecedió a 26/14.

Pierde claramente en validación municipal y espacial de los 65 folds, con R² espacial negativo. Dependencia de vecindarios, C4 y representación transductiva; no es una receta compacta de veinte mediciones. Los resultados .4819 y .4957 de otros bancos no se mezclan con esta tabla. Se conserva la copia existente de sus 59 estimaciones; no se reentrena aquí ni se conoce su error real en esas parcelas.
'''
}


def cards():
    for model, body in DETAILS.items():
        if model=='Reference26':
            details=(ROOT/'documentation/models/Reference26/blocks.md').read_text(encoding='utf-8')
            body=body.replace('## En qué etapa surgió cada bloque',details+'\n\n## En qué etapa surgió cada bloque')
        text = '# ' + model + ' — ficha del modelo\n\n'
        text += 'Estado vigente: 2026-10-18. Champions actuales: **Reference26 y Compact14**. [Índice de modelos](../README.md).\n\n' + body
        if model in SETS:
            text += '\n## Inventario exacto de entradas\n\n'
            text += '| # | Variable | Significado y ubicación |\n|---|---|---|\n'
            for i, (name, description) in enumerate(SETS[model], 1):
                role = ('Base C-T3' if (name, description) in CORE else 'Experto local' if (name, description) in LOCAL
                        else 'Vecindario' if (name, description) in COORDS else 'Compuerta física' if (name, description) in GEO else 'Corrector final R3')
                text += f'| {i} | `{name}` | **{role}.** {description} |\n'
            text += '\nLas ventanas y agregaciones de las columnas heredadas se conservan tal como están en las tablas procesadas; su nombre no acredita por sí solo uniformidad de fechas entre sensores. Las tres fórmulas R3 se implementan en [temporal_indicator_weights.py](../../../src/temporal_indicator_weights.py). Las entradas derivadas y sus hashes constan en [el manifiesto de insumos](../../../configs/current_champions_inputs.json).\n'
        text += '\n## Resultados compatibles y lectura\n\nRMSE t/ha / R² / MAE t/ha. OOF completas por repetición y después promedio; mismos 65 folds, 138 parcelas.\n\n'
        text += '| Aleatoria | Perfil climático | Municipal | Espacial |\n|---|---|---|---|\n| ' + ' | '.join(METRICS[model]) + ' |\n'
        fresh=fresh_metrics()
        if model in fresh:
            r=fresh[model]
            text+='\n### Banco adicional97/41 — resultado separado\n\n'
            text+='| RMSE t/ha | R² | MAE t/ha | Sesgo predicho−observado |\n|---|---|---|---|\n'
            text+=f"| {float(r['rmse']):.4f} | {float(r['r2']):.4f} | {float(r['mae']):.4f} | {float(r['bias']):+.4f} |\n"
            text+='\nMedia de las métricas de **16 particiones**, cada una con97 parcelas para entrenar y41 para evaluar. Reutiliza las mismas138 parcelas; no es muestra independiente ni error de las59 PRED. Se conserva separado de los cuatro protocolos anteriores. [Comparación completa y procedencia](../../../results/comparison_97_41/v1/README.md).\n'
        text += '\nSon resultados de validación exploratoria tras reutilización de etiquetas, no el error de las 59 desconocidas ni superioridad universal. Residuo = predicho − observado: positivo significa sobreestimación. El banco adicional 97/41 se interpreta por separado. No se presenta R² ajustado clásico para estas arquitecturas locales y calibradas.\n'
        if model in ['CT3','Reference26'] and (ROOT/'results/core4_relevance/v1/README.md').exists():
            text+='\n## Evidencia de relevancia del núcleo: análisis posterior\n\nYa se realizaron contrastes exploratorios de asociación, ajustados por estado y agrupados por perfil, y ablaciones reajustadas de C-T3 en los65 folds. Total de lluvia, fracción temprana y NDVI mantienen evidencia de asociación; HHI no después de ajustar por estado. Ninguna retirada individual supera Holm en los contrastes predictivos, y retirar HHI mejora el RMSE espacial de C-T3. Estos resultados no son p-valores de los coeficientes Elastic Net ni una prueba causal o confirmatoria. Las ablaciones corresponden a C-T3, no al26 completo; sus cuatro entradas intervienen en dos capas de26. [Informe, hipótesis, tablas y límites](../../../results/core4_relevance/v1/README.md).\n'
        if model=='Reference26' and (ROOT/'results/reference26_component_evidence/v1/README.md').exists():
            text+='\n## Evidencia recuperada del resto de componentes\n\n[Reporte por función, con RMSE/R² y límites](../../../results/reference26_component_evidence/v1/README.md): siete señales locales,24 vecinos, corrector interno, compuerta geológica, R3 y combinaciones que dieron origen a14. Distingue retiradas de bloques, columnas y cambios conjuntos; conserva los ajustes múltiples originales y señala las pruebas aún faltantes. Incluye un inventario del respaldo disponible para cada una de las26 entradas. Se recuperaron11 contrastes arquitectónicos, sin entrenar modelos nuevos ni alterar las59 predicciones.\n'
        text += '\n## Archivos y reproducción\n\n'
        if model != 'L40':
            text += 'Implementación integrada: [src/current_champions.py](../../../src/current_champions.py). [Reproducción y alcance de la verificación](../../current_champions_reproduction.md). Entrada: `python scripts/521_current_champions.py replay`; reentrenamiento: subcomando `refit` según esa guía. Bundle privado: `data/processed/current_champions/v1/`; OOF: `outputs/research/current_champions/v1/`; [métricas públicas](../../../results/current_champions/v1/README.md). Las fichas no generan nuevos ajustes finales ni predicciones59.\n'
        else:
            text += 'Implementación del puente: [src/geoc_bridge.py](../../../src/geoc_bridge.py). Artefactos privados: `outputs/modeling/geoc_bridge/v1/`; copia de estimaciones finales en `outputs/research/geoc_bridge_audit/v1/predictions59_aligned_descriptive.csv`, columna `Local04D_t_ha`, cuando los artefactos locales están presentes. Esa copia no es un ajuste nuevo ni una entrega validada con sus rendimientos.\n'
        if (ROOT/'outputs/modeling/current_champions_final/v1/complete.json').exists():
            text+='\n## Comparación final59 disponible\n\nLos champions26/14 ya tienen ajustes finales con138 y sus59 estimaciones se incorporaron a la comparación existente sin sobrescribir las anteriores. [Reporte de diferencias entre predicciones](../../../results/current_champions_final/v1/README.md). Archivo privado: `outputs/modeling/current_champions_final/v1/comparacion_predicciones59.xlsx`. Estas diferencias no son errores contra rendimientos observados.\n'
        write(f'documentation/models/{model}/README.md', text)
    write('documentation/models/historical_top20_top15/README.md', '''# Modelo histórico — TOP20 → TOP15 → topografía

**Estado: histórico. No es Reference26 ni Compact14, los dos champions actuales.** Identificador conservado: `A_CURRENT_CH_H_T`; alias antiguos `Champion` y `CHAMPION`. No se reasigna ese identificador a la receta de 26 entradas.

## Arquitectura y variables

Base climática Elastic Net con selección TOP20, corrección histórica XGBoost con selección TOP15 y corrección topográfica Ridge25. TOP20/TOP15 nombran cantidades de variables seleccionadas en su etapa, no conjuntos fijos universales ni componentes PCA. La selección se realiza con el entrenamiento correspondiente; las variables pueden cambiar entre folds. No es un modelo de 20+15 entradas fijas equivalente a 26/14.

## Origen, ventajas y limitaciones

Representa la etapa de integración secuencial clima → historia → topografía anterior a la investigación con expertos locales compactos. Permitió separar aportes incrementales y conserva una entrega histórica59. Su mayor número de fuentes y correcciones motivó comparaciones posteriores y simplificaciones; su antigua etiqueta de champion no implica que sea la elección vigente.

La lista concreta seleccionada corresponde a cada modelo guardado y a su auditoría histórica; no se inventa una lista única a partir de los nombres TOP20/TOP15. Véase [consolidación histórica](../../winner_predictions_statistical_validation.md) y [registro vigente](../../model_registry.md). Artefactos locales: `outputs/modeling/winner_predictions/v1/`. No se sobrescriben sus modelos ni sus predicciones. Las columnas históricas llamadas `Champion_t_ha` siguen correspondiendo a esta receta.
''')
    text = '# Modelos de la comparación final\n\n**Champions actuales: Reference26 y Compact14.** C-T3 es control, B1 sensibilidad y L40 referencia externa fuerte del equipo. La receta TOP20/TOP15 pertenece al historial.\n\n'
    text += '| Modelo | Estado | Entradas | Ficha con arquitectura, origen y límites |\n|---|---|---|---|\n'
    for m, n, state in [('Reference26',26,'Champion de precisión'),('Compact14',14,'Champion compacto'),('CT3',4,'Control'),('B1',26,'Sensibilidad'),('L40','2082 → PCA20 + geografía','Benchmark externo')]:
        text += f'| {m} | {state} | {n} | [README]({m}/README.md) |\n'
    text += '\n[Champion histórico TOP20/TOP15](historical_top20_top15/README.md). Los números 26/14 cuentan entradas distintas, no coeficientes ni componentes. Las entradas reutilizadas en varias capas se cuentan una sola vez.\n'
    if (ROOT/'outputs/modeling/current_champions_final/v1/complete.json').exists():
        text+='\n[Comparación final59 con ambos champions incorporados](../../results/current_champions_final/v1/README.md).\n'
    write('documentation/models/README.md',text)


def status_audit():
    """Annotate historical reports, preserving original text and frozen designs."""
    rows = []
    previous_path=ROOT/'documentation/inventories/model_status_audit.csv'
    previous={}
    if previous_path.exists():
        with previous_path.open(encoding='utf-8',newline='') as stream:
            previous={r['document']:r for r in csv.DictReader(stream)}
    current = {'README.md','model_registry.md','current_champions_reproduction.md','reproducibility.md',
               'experiment_index.md','repository_organization.md','ai_usage.md','git_data_policy.md',
               'project_scope_and_guidelines.md','model_comparison_convention.md'}
    banner = ('> **Estado de lectura (2026-10-18):** los champions actuales son '
              '**Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). '
              'Este documento conserva la investigación y las decisiones de su etapa. '
              'Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta '
              'TOP20 → TOP15 → topografía corresponden al **champion histórico**, '
              'salvo que el texto identifique expresamente Reference26 o Compact14. '
              'Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.\n\n')
    for path in sorted((ROOT/'documentation').glob('*.md')):
        if path.name=='model_status_history.md':continue
        text = path.read_text(encoding='utf-8')
        if not re.search(r'champion|top\s*20|top\s*15',text,re.I): continue
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        protected = any(v in path.stem for v in ('design','proposal','plan'))
        if path.name in current:
            action = 'current_navigation'
        elif protected:
            action = 'frozen_design_preserved; status_in_index'
        elif '> **Estado de lectura (2026-10-18):**' in text:
            action = 'historical_banner'
        else:
            # Original body remains verbatim, below an explicit contextual notice.
            with path.open('w',encoding='utf-8',newline='') as stream:stream.write(banner+text)
            action = 'historical_banner'
        relative=path.relative_to(ROOT).as_posix()
        rows.append(dict(document=relative,treatment=action,
                         sha256_before=previous.get(relative,{}).get('sha256_before',before),
                         sha256_after=hashlib.sha256(path.read_bytes()).hexdigest()))
    target=ROOT/'documentation/inventories/model_status_audit.csv'
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    text='# Estado de documentos históricos y vigentes\n\nChampions actuales: **Reference26 y Compact14**. [Fichas](models/README.md). TOP20/TOP15 y `A_CURRENT_CH_H_T` son históricos.\n\n'
    text+='Los informes conservan su contenido original con una nota de contexto. Los diseños/propuestas/planes congelados se mantienen sin editar para preservar su identidad; su estado se aclara aquí. Sus decisiones describen su etapa, no la selección vigente. Los hashes de documentación anteriores siguen refiriéndose a su versión histórica en Git, no al texto con la nota añadida. No se modificaron recetas, modelos, OOF o rendimientos.\n\n'
    text+='| Documento | Tratamiento |\n|---|---|\n'
    for row in rows:
        name=Path(row['document']).name
        text+=f"| [{name}]({name}) | {row['treatment']} |\n"
    text+='\n[Auditoría estructurada](inventories/model_status_audit.csv).\n'
    write('documentation/model_status_history.md',text)
    return rows


def navigation():
    path=ROOT/'README.md';text=path.read_text(encoding='utf-8')
    text=text.replace('La entrega reproducible actual excluyeL40.', 'L40 se conserva como benchmark fuerte del equipo; queda fuera del reentrenamiento propio, no de la comparación.')
    text=text.replace('L40/Local04D pertenece al repositorioGeoC y queda como comparación histórica; no forma parte del paquete ni de los resultados reproducibles actuales. Se conservan los informes históricos sin reescribirlos.', 'L40/Local04D pertenece a GeoC y se conserva en las tablas como benchmark externo fuerte del equipo. No se reentrena dentro del paquete propio. Cada modelo tiene una [ficha completa](documentation/models/README.md), con variables, función de sus bloques, origen, ventajas y límites. Los [documentos históricos](documentation/model_status_history.md) se distinguen de la selección vigente.')
    if '| **L40 / Local04D**' not in text:
        marker='| **Champion histórico**'
        text=text.replace(marker,'| **L40 / Local04D** | PCA20 de C4 (2082 variables) + Ridge local24 geográfico | Benchmark fuerte externo del equipo; no es champion actual de este repositorio |\n'+marker)
    if '| L40 / Local04D | .4930' not in text:
        text=text.replace('| C-T3 | .5116', '| L40 / Local04D | .4930 / .6619 | .5031 / .6481 | .7602 / .1964 | .9794 / −.3337 |\n| C-T3 | .5116')
    text=text.replace('Esta tabla compara los champions actuales, el control y la sensibilidad;', 'Esta tabla compara los champions actuales, el control, la sensibilidad y L40 sobre evaluación compatible;')
    fresh=fresh_metrics()
    if fresh:
        start='<!-- comparison97:start -->';end='<!-- comparison97:end -->'
        block=start+'\n### Banco adicional97/41 — comparación separada\n\n'
        block+='**16 particiones con97 parcelas de entrenamiento y41 de evaluación**, sobre las mismas138 conocidas. Media de métricas por partición; no es una muestra independiente ni el error real de las59.\n\n'
        block+='| Modelo | RMSE t/ha ↓ | R² ↑ | MAE t/ha ↓ |\n|---|---|---|---|\n'
        for model in ['CT3','L40','Reference26','Compact14','B1']:
            r=fresh[model];block+=f"| {model} | {float(r['rmse']):.4f} | {float(r['r2']):.4f} | {float(r['mae']):.4f} |\n"
        block+='\n[Resultados de los10 modelos disponibles y metodología](results/comparison_97_41/v1/README.md). No se mezclan con la tabla de los65 folds originales ni con los checkpoints propios de GeoC.\n'+end+'\n\n'
        if start in text:
            text=text[:text.index(start)]+block+text[text.index(end)+len(end):].lstrip('\n')
        else:text=text.replace('## Cómo leer y reproducir',block+'## Cómo leer y reproducir')
    if (ROOT/'results/core4_relevance/v1/README.md').exists():
        note='**Relevancia del núcleo C-T3:** [contrastes de asociación y ablaciones reajustadas](results/core4_relevance/v1/README.md). Evidencia exploratoria, con resultados favorables para algunas señales y límites explícitos para HHI; no certifica significancia de las26 entradas.\n\n'
        if note not in text:text=text.replace('## Cómo leer y reproducir',note+'## Cómo leer y reproducir')
    if (ROOT/'results/reference26_component_evidence/v1/README.md').exists():
        note='**Componentes de26:** [evidencia recuperada por función y variable](results/reference26_component_evidence/v1/README.md), con ablaciones existentes, interacciones, dependencias de calibración y límites.\n\n'
        if note not in text:text=text.replace('## Cómo leer y reproducir',note+'## Cómo leer y reproducir')
    write('README.md',text)
    for name in ['documentation/README.md','documentation/model_registry.md','documentation/current_champions_reproduction.md']:
        path=ROOT/name;text=path.read_text(encoding='utf-8')
        text=text.replace('L40 queda fuera de la entrega reproducible actual.', 'L40 se conserva en la comparación como benchmark externo fuerte; queda fuera del reentrenamiento propio.')
        text=text.replace('Benchmark externo histórico; excluido de la entrega actual.', 'Benchmark externo fuerte del equipo; incluido en las tablas, excluido del reentrenamiento propio.')
        note='**Lectura vigente:** champions Reference26 y Compact14. [Fichas completas de los cinco modelos](models/README.md) · [Estado de la documentación histórica](model_status_history.md).\n\n'
        if note not in text:
            first,sep,rest=text.partition('\n');text=first+'\n\n'+note+rest.lstrip('\n')
        write(name,text)
    registry_path=ROOT/'configs/model_registry.json';registry=json.loads(registry_path.read_text(encoding='utf-8'))
    for model in registry['models']:
        if model['id'] in DETAILS:model['documentation']=f"documentation/models/{model['id']}/README.md"
        if model['id']=='L40':model['status']='external_team_benchmark_in_final_comparison_not_retrained'
        if model['id']=='A_CURRENT_CH_H_T':model['documentation']='documentation/models/historical_top20_top15/README.md'
    write('configs/model_registry.json',json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
    # Keep the original reproduction-only scope intact; clarify comparison scope.
    stage_path=ROOT/'configs/current_stage.json';stage=json.loads(stage_path.read_text(encoding='utf-8'))
    stage['comparison_models']=['CT3','Reference26','Compact14','B1','L40']
    stage['external_reference']='L40: included in comparative documentation; excluded_from_current_delivery refers only to the own-model reproducibility bundle and retraining.'
    write('configs/current_stage.json',json.dumps(stage,ensure_ascii=False,indent=2)+'\n')
    replacements={
        'results/README.md': [('L40 queda fuera del alcance actual.', 'L40 se conserva como benchmark externo fuerte en las tablas del README principal; este directorio de reproducción propia no lo reentrena.')],
        'results/current_champions/v1/README.md': [('Los informes anteriores conL40 se conservan como historia.', 'L40 se conserva como benchmark externo fuerte en las tablas del README principal y en su ficha; este paquete reproduce únicamente los cuatro modelos propios. Los hashes de procedencia de esta auditoría corresponden a la revisión documental existente cuando se ejecutó, anterior a las nuevas fichas.')],
        'configs/README.md': [('yL40 queda fuera de esta entrega.', 'y L40 queda fuera del bundle de reentrenamiento propio, pero figura como benchmark externo fuerte en la comparación.')],
        'documentation/project_scope_and_guidelines.md': [('e incluyeC-T3', 'e incluye C-T3'),('incluyeC-T3 y B1 y excluyeL40.', 'incluye C-T3 y B1, sin reentrenar L40; L40 sí permanece en las tablas comparativas como referencia externa fuerte.')],
        'documentation/reproducibility.md': [('junto aC-T3 y B1, excluyendoL40.', 'junto a C-T3 y B1, sin reentrenar L40. L40 sí permanece como benchmark externo fuerte en las tablas y en su ficha.')],
        'documentation/ai_usage.md': [('**37 prompts**,21 adjuntos originales y16 mensajes', '**40 prompts**,21 adjuntos originales y19 mensajes'),('**38 prompts**,21 adjuntos originales y17 mensajes', '**40 prompts**,21 adjuntos originales y19 mensajes'),('**39 prompts**,21 adjuntos originales y18 mensajes', '**40 prompts**,21 adjuntos originales y19 mensajes')],
    }
    for name,pairs in replacements.items():
        text=(ROOT/name).read_text(encoding='utf-8')
        for old,new in pairs:text=text.replace(old,new)
        if name=='documentation/ai_usage.md':
            with (ROOT/'documentation/ai/prompt_inventory.csv').open(encoding='utf-8',newline='') as stream:
                prompt_count=len(list(csv.DictReader(stream)))
            text=re.sub(r'\*\*\d+ prompts\*\*,21 adjuntos originales y\d+ mensajes',
                        f'**{prompt_count} prompts**,21 adjuntos originales y{prompt_count-21} mensajes',text)
        write(name,text)


def main():
    cards();navigation()
    refresh=ROOT/'scripts/532_refresh_results_readmes.py'
    if refresh.exists() and (ROOT/'results/current_champions_final/v1/prediction_audit.json').exists():
        import runpy
        runpy.run_path(str(refresh))['main']()
    rows=status_audit()
    naming=ROOT/'scripts/533_current_champion_naming.py'
    if naming.exists():
        import runpy
        runpy.run_path(str(naming))['main']()
    print(json.dumps(dict(model_cards=6,documents_reviewed=len(rows),training_performed=False,
                          frozen_designs_modified=False,predictions_generated=False),indent=2))


if __name__=='__main__':main()
