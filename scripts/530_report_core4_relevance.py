"""Interpret completed529 tests without new fits, model changes or PRED reads."""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/'results/core4_relevance/v1'


def main():
    tests=pd.read_csv(PUB/'association_tests.csv');coefs=pd.read_csv(PUB/'association_coefficients.csv')
    metrics=pd.read_csv(PUB/'metrics.csv');abl=pd.read_csv(PUB/'ablation_tests.csv')
    old=pd.read_csv(PUB/'existing_26_vs_CT3_tests.csv')
    audit=json.loads((PUB/'audit.json').read_text(encoding='utf-8'))
    t=pd.read_parquet(ROOT/'data/processed/current_champions/v1/train138.parquet')
    support=t.groupby('climate_profile').agg(n=('ID_POLIGONO','size'),ndvi_unique=('S2_ndvi_month_05','nunique'))
    active=support[(support.n>1)&(support.ndvi_unique>1)]
    body='# Relevancia del núcleo C-T3 y evidencia para Reference26\n\n'
    body+='Análisis exploratorio retrospectivo,2026-10-18. Se estudiaron138 rendimientos conocidos, agrupados en43 perfiles climáticos. **No se modificaron los champions, sus hiperparámetros, sus predicciones finales ni las59 PRED.** Se reprodujo C-T3 exactamente y se reentrenaron sólo sus ablaciones y controles con las65 particiones originales.\n\n'
    body+='## Qué pregunta responde cada prueba\n\n'
    body+='| Análisis | Hipótesis nula | Qué permite concluir | Qué no demuestra |\n|---|---|---|---|\n'
    body+='| Asociación OLS ajustada por estado | Coeficiente parcial de la variable igual a cero, manteniendo las otras entradas y el estado | Evidencia de asociación lineal condicional bajo el modelo de diagnóstico | Significancia del coeficiente penalizado de Elastic Net, causalidad o ganancia predictiva de26 |\n'
    body+='| Contraste conjunto del bloque de lluvia | Los tres coeficientes de lluvia son simultáneamente cero | Asociación conjunta que no depende de que cada columna pase un umbral individual | Que las tres sean indispensables para todo protocolo |\n'
    body+='| NDVI con efectos fijos por perfil | Coeficiente NDVI dentro del perfil igual a cero | Asociación entre parcelas de un mismo perfil climático | Que se hayan eliminado todas las diferencias de suelo, manejo o medición |\n'
    body+='| Ablación reajustada de C-T3 | Diferencia agrupada de pérdidas cuadráticas entre modelo reducido y completo compatible con cero | Aporte predictivo bajo la receta, rejillas y protocolos evaluados | Aporte de esa entrada en la arquitectura completa de26 ni información causal |\n'
    body+='| Contrastes pareados26 frente a C-T3 ya existentes | Ausencia de diferencia de pérdidas entre las arquitecturas | Evidencia sobre el sistema completo en el protocolo identificado | Relevancia individual de sus26 entradas o confirmación independiente nueva |\n'
    body+='\n## Asociación: ajustes y resultados\n\n'
    body+='Se ajustaron OLS diagnósticas con las cuatro entradas estandarizadas: una sin estado y otra con interceptos por estado. No son sustitutos de Elastic Net ni se usaron para seleccionar parámetros de los champions. En ambas, la covarianza se agrupó por los43 perfiles, con corrección de muestra finita y referencia t/F con grados de libertad por número de grupos. El contraste de NDVI con efectos fijos se restringe a los12 perfiles informativos,107 parcelas, con referencia t de11 grados de libertad; los31 perfiles sin variación interna no cuentan como grupos informativos. No se intentó identificar lluvia dentro de perfil porque allí es constante. Este criterio de soporte depende de X, no del rendimiento ni de su p-valor; su corrección quedó registrada en [la enmienda metodológica](../../../configs/core4_relevance/v1/amendment_01.json).\n\n'
    body+='La familia conjunta contiene **13 contrastes**: cuatro coeficientes y dos bloques en cada una de las dos OLS, más NDVI intraperfil. Se aplica Holm a los13. Los intervalos95% de coeficientes son marginales, sin ajuste simultáneo.\n\n'
    body+='| Entrada en OLS ajustada por estado | Coeficiente por1 SD, t/ha | IC95% marginal | p sin ajuste | p Holm,13 pruebas |\n|---|---|---|---|---|\n'
    for _,r in coefs[coefs.model=='CORE4_PLUS_STATE'].iterrows():
        p=tests[(tests.model==r.model)&tests.hypothesis.str.startswith(r.feature+' coefficient')].iloc[0]
        body+=f"| `{r.feature}` | {r.coefficient_per_SD:+.4f} | [{r.ci95_low:+.4f}, {r.ci95_high:+.4f}] | {r.p_value:.5g} | {p.p_holm_family13:.5g} |\n"
    rain=tests[(tests.model=='CORE4_PLUS_STATE')&tests.hypothesis.str.startswith('RAIN_BLOCK')].iloc[0]
    within=tests[tests.model=='NDVI_PLUS_PROFILE_FIXED_EFFECTS'].iloc[0]
    body+=f'\nEl bloque conjunto de lluvia conserva asociación ajustada por estado: **p Holm={rain.p_holm_family13:.5g}**. NDVI conserva asociación intraperfil: **p Holm={within.p_holm_family13:.5g}**. Este último contraste dispone de{len(active)} perfiles con varias parcelas y NDVI variable, que reúnen{int(active.n.sum())} parcelas; los perfiles restantes no aportan variación interna de NDVI.\n\n'
    body+='Lluvia total, fracción temprana y NDVI presentan evidencia de asociación en este diagnóstico. **HHI no mantiene evidencia suficiente tras ajustar por estado** (p ajustada≈.2024), aunque sí la presenta en la OLS sin estado. Esto muestra sensibilidad a la estructura territorial; no demuestra que HHI carezca de información. Los coeficientes negativos de lluvia son asociaciones condicionales del conjunto observado, no una demostración agronómica de que aumentar lluvia reduzca rendimiento.\n\n'
    body+='## Aporte predictivo: ablaciones con reajuste\n\n'
    body+='Se congelaron siete recetas: núcleo completo, retirada individual de cada entrada, NDVI solo y media de entrenamiento. Cada Elastic Net reducido se recalibró con las particiones internas originales y la misma rejilla12 de alpha/l1_ratio, con imputación/escalado propios del entrenamiento. **C-T3 completo reproduce sus1,794 predicciones originales con diferencia máxima0.0.** Se generaron12,558 predicciones de evaluación, siete recetas por1,794 casos; no se tratan como12,558 observaciones independientes.\n\n'
    body+='Cada celda es **RMSE t/ha / R²**; MAE y sesgo están en [metrics.csv](metrics.csv). Aleatoria: métricas sobre138 OOF por repetición y promedio de10 repeticiones. Otros protocolos:138 OOF completas.\n\n'
    body+='| Receta C-T3 | Aleatoria | Perfil | Municipal | Espacial |\n|---|---|---|---|---|\n'
    names={'FULL4':'Completo4','DROP_compact_precip_total':'Sin lluvia total','DROP_compact_early_fraction':'Sin fracción temprana','DROP_compact_concentration_hhi':'Sin HHI','DROP_S2_ndvi_month_05':'Sin NDVI de mayo','NDVI_ONLY':'Sólo NDVI de mayo','TRAIN_MEAN':'Media de entrenamiento'}
    for name,label in names.items():
        cells=[]
        for protocol in ['random','climate_profile','municipality','spatial']:
            r=metrics[(metrics.experiment==name)&(metrics.protocol==protocol)].iloc[0]
            cells.append(f'{r.rmse:.4f} / {r.r2:.4f}')
        body+='| '+label+' | '+' | '.join(cells)+' |\n'
    body+='\n**Lectura:** retirar total, fracción temprana o NDVI empeora el RMSE en los cuatro protocolos. Eliminar HHI empeora ligeramente aleatoria/perfil/municipal, pero mejora espacial de.6788 a.5596 t/ha (−.1192). Es una señal exploratoria específica de transferencia, no un criterio para borrar HHI de26 sin reajustar su arquitectura completa.\n\n'
    body+='### Qué respaldo estadístico tienen las diferencias predictivas\n\n'
    body+='Se contrastan24 diferencias: seis recetas frente a completo, en cuatro protocolos. Prueba bilateral de inversión de signos de pérdidas cuadráticas agregadas por perfil (aleatoria/perfil), municipio (municipal) o bloque (espacial). Las repeticiones aleatorias se promedian por parcela antes de inferir. Se enumeran todas las asignaciones para9 municipios y5 bloques; con43 perfiles se usan20,000 asignaciones y semilla2026. Holm se aplica a las24 comparaciones.\n\n'
    body+='**Ninguna de las cuatro retiradas individuales resulta significativa tras Holm.** Los cuatro contrastes que sobreviven corresponden a completo frente a NDVI solo y a media de entrenamiento, bajo aleatoria y por perfil. Por tanto, existe respaldo del conjunto frente a controles débiles; no una prueba de indispensabilidad individual de cada entrada.\n\n'
    body+='Con sólo cinco bloques, el mínimo p bilateral de la enumeración de signos es2/32=.0625 incluso antes de Holm. La ausencia de significancia espacial es especialmente poco informativa. La enumeración es exacta para las asignaciones de signos, no una garantía de exactitud inferencial si no se cumplen independencia y simetría de pérdidas por grupo. Los modelos comparten datos de entrenamiento, por lo que los contrastes se interpretan con cautela adicional.\n\n'
    body+='## Qué respalda ya al modelo26\n\n'
    body+='Los siguientes contrastes proceden de la comparación previa de cuatro líderes; **se recuperan, no se cuentan como replicación nueva**. Su Holm original comprende24 comparaciones entre modelos y protocolos, distinto de la familia nueva de24 ablaciones.\n\n'
    body+='| Protocolo | Reducción RMSE26 frente a C-T3, t/ha | p bilateral | p Holm original |\n|---|---|---|---|\n'
    for _,r in old.iterrows():body+=f'| {r.protocol} | {r.delta_rmse:.4f} | {r.p_mse_signflip:.5g} | {r.p_holm:.5g} |\n'
    body+='\nLa mejora aleatoria26 frente a C-T3 conserva p ajustada≈.0253 bajo esa prueba. Las diferencias por perfil, municipal y espacial no sobreviven su ajuste. Esto respalda una parte del rendimiento observado, no superioridad territorial demostrada. El banco97/41 es otra evaluación sobre las mismas etiquetas, no una campaña independiente.\n\n'
    body+='## Límites y decisión metodológica\n\n'
    body+='Los predictores y arquitecturas se eligieron después de investigación extensa con estas etiquetas. **Holm corrige las familias enumeradas aquí, no toda la selección histórica**; los p-valores no son confirmatorios posteriores a selección ni una certificación del modelo. Agrupar por perfil evita tratar duplicados climáticos como independientes, pero no garantiza independencia geográfica entre perfiles. La OLS supone una forma aditiva y su ajuste por estado no controla todas las diferencias territoriales. No se interpreta su R² ajustado ni sus p-valores como propiedades del modelo26.\n\n'
    body+='La evidencia mejora la documentación: permite sostener asociación del núcleo, mostrar aportes predictivos observados y explicitar que HHI es la entrada más discutible. No permite escribir que «las26 variables son estadísticamente significativas».\n\n'
    body+='Para aumentar credibilidad de26 priorizaría: (1) conservar la receta congelada y obtener rendimientos externos o de las59 cuando se revelen; (2) si se abre otra sensibilidad, retirar HHI **en C-T3 y en el corrector interno del experto**, recalibrando pesos y R3 dentro de entrenamiento con los mismos protocolos; (3) evaluar ablaciones de bloques completos y estabilidad regional antes de añadir complejidad. Esa sensibilidad completa no se ejecutó aquí y un nuevo resultado sobre estos mismos folds seguiría siendo exploratorio.\n\n'
    body+='## Reproducción y archivos\n\n'
    body+='Ejecución: `python scripts/529_core4_relevance.py`; informe: `python scripts/530_report_core4_relevance.py`. Configuración previa: [frozen_design.json](../../../configs/core4_relevance/v1/frozen_design.json). Excel y OOF privados: `outputs/research/core4_relevance/v1/relevancia_core4.xlsx` y `oof_predictions.parquet`. Resultados agregados en este directorio, sin IDs ni rendimientos por parcela. [Auditoría](audit.json), [contrastes de asociación](association_tests.csv), [coeficientes diagnósticos](association_coefficients.csv), [contrastes de ablación](ablation_tests.csv), [contrastes previos26](existing_26_vs_CT3_tests.csv). No se leyó PRED ni se modificaron finales.\n\n'
    body+='Fuentes metodológicas: [Statsmodels: covarianza robusta y agrupada, corrección y grados de libertad](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html); [scikit-learn: importancia predictiva y variables correlacionadas](https://scikit-learn.org/1.7/modules/permutation_importance.html). No se usó permutación irrestricta de variables correlacionadas ni se inventaron p-valores para Elastic Net.\n'
    (PUB/'README.md').write_text(body,encoding='utf-8',newline='\n')
    files=['scripts/529_core4_relevance.py','scripts/530_report_core4_relevance.py','src/family_4/conditional_response.py','src/ct3_residual_conditional/models.py']
    provenance=dict(source_sha256={f:hashlib.sha256((ROOT/f).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for f in files},
        input_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['data/processed/current_champions/v1/train138.parquet','data/processed/current_champions/v1/splits.json','outputs/research/four_leaders/v1/paired_tests.csv']},
        source_hash_convention='CRLF normalized to LF for code only; raw bytes for inputs',claims='Exploratory and conditional; not causal or post-selection-valid confirmation')
    (PUB/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'Report complete; within-profile NDVI support:{len(active)} profiles,{int(active.n.sum())} parcels; no new fits.')


if __name__=='__main__':main()
