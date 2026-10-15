"""X-only interpretation review: preserve v1 and publish corrected v2 catalogue."""
from pathlib import Path
import json,hashlib,shutil
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/research/ct3_incremental_information/phase_iii/v1'
OUT=SOURCE.parent/'v2'
if OUT.exists():raise FileExistsError(OUT)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=json.loads((SOURCE/'manifest.json').read_text())
for p,h in old['artifacts'].items():assert sha(ROOT/p)==h
for file in SOURCE.rglob('*'):
    if not file.is_file() or file.name=='manifest.json':continue
    target=OUT/file.relative_to(SOURCE);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,target)
catalog=pd.read_csv(OUT/'representation_catalog.csv');comparison=pd.read_csv(OUT/'block_comparison.csv')
catalog['interpretation_review']='Original geometric classification; does not certify stable measurements or predictive utility'
climate=catalog.block.eq('climate_monthly_between')
catalog.loc[climate,'category']='C — regional; no nueva información parcelaria medida'
catalog.loc[climate,'reason']='Raw climate constant by profile; CT3 residual variation may be induced by subtracting the NDVI term; within centering has rank0'
catalog.loc[climate,'interpretation_review']='Do not count NDVI-induced residual contrasts as new climate information'
dyn=catalog.block.eq('dynamics_original')
catalog.loc[dyn,'category']='B — original definida, estabilidad temporal limitada'
catalog.loc[dyn,'reason']='LAI/SAVI are compact and defined but deletion sensitivity and shared timing dimension limit automatic technical-readiness claims'
catalog.loc[dyn,'interpretation_review']='Can be tested after explicit review using complete7-month support; not automatically stable under missing dates'
catalog.to_csv(OUT/'representation_catalog.csv',index=False)
comparison['climate_residual_contrast_caveat']=np.where(comparison.block.eq('climate_monthly_between') & comparison['mode'].eq('ct3_residual'),'source has0raw within contrast; residual variation includes existing NDVI term','')
comparison['variance_90_95_scope']=np.where(comparison.kind.eq('hierarchical'),'intermediate hierarchical score variance, NOT original1041-column variance','mode-input scaled X variance; original reconstruction reported separately')
comparison.to_csv(OUT/'block_comparison.csv',index=False)
classify=pd.read_csv(OUT/'audit/descriptive_classification.csv');classify=classify.drop(columns=['category','reason']).merge(catalog[['representation','category','reason']],on='representation',validate='one_to_one');classify.to_csv(OUT/'audit/descriptive_classification.csv',index=False)
note='''# Fase III: información complementaria y límites de representación

Esta versión v2 conserva todos los cálculos no supervisados de v1 y revisa dos interpretaciones: variación climática inducida por residualización y estabilidad temporal de LAI/SAVI. No se recalcularon ni seleccionaron representaciones usando rendimiento. Los artefactos anteriores permanecen intactos.

**La conclusión es que hay contrastes adicionales de X, pero no encontramos una compresión pequeña que conserve casi toda la variación parcelaria.** Tampoco se demuestra utilidad predictiva; Fase IV sigue sin ejecutarse.

## 1. Información ya representada por C-T3

C-T3 contiene total, fracción abril–junio y concentración temporal de lluvia abril–octubre, más NDVI promedio de mayo. Los tres resúmenes de lluvia son constantes dentro de los perfiles. La residualización elimina únicamente la reconstrucción lineal de un bloque a partir de esas cuatro entradas; no prueba independencia condicional.

## 2. Dimensiones adicionales

Se conservaron indicadores originales, PCA por bloques y jerarquía sensor/índice/ventana/familia. El bloque satelital actual contiene 764 descriptores Sentinel-2 y 277 Planet; las 82 variables Sentinel históricas/anómalas del inventario se separaron de este bloque actual. Historia NDVI2 se conserva con dos indicadores, sin PCA artificial.

## 3. Contraste intraperfil

LAI/SAVI, fuentes satelitales, terreno y cartografía conservan contrastes entre parcelas de perfiles repetidos. Tener contraste no demuestra que ayude a explicar rendimiento. Los tamaños efectivos, resultados fuera de Chignahuapan y concentración en perfiles dominantes están en block_comparison.csv, separados para138 y197 parcelas.

## 4. Estructura entre perfiles y variación inducida

Clima mensual tiene cero contraste original dentro de perfiles y rango0 tras centrado por perfil. Residualizarlo contra C-T3 puede producir diferencias dentro del perfil porque se resta el término NDVI:

R_clima = clima − proyección sobre lluvia compacta y NDVI.

Dentro de un perfil, clima y lluvia compacta son constantes, por lo que la diferencia residual inducida corresponde a −beta_NDVI × diferencia_NDVI. No es una nueva medición climática parcelaria. Las12 filas de contraste que aparecen para ese residuo se marcan con esta reserva en la versión revisada. No priorizar ese bloque como diferenciador local.

## 5. Redundancia y peso de sensores

Se organizaron variables por sensor, índice, ventana y familia estadística. La jerarquía conserva máximo dos dimensiones por subgrupo y equilibra energía de subgrupos y sensores. Eso reduce el dominio por cantidad de columnas, pero puede perder información en dos etapas. Igualdad casi afín observada no certifica equivalencia física. Escalado, omisiones y deduplicación se evaluaron sin Y.

## 6. LAI, SAVI y NDVI mayo

En138 parcelas, la correlación intraperfil LAIinicio–SAVIduración es −0.703 (fuera de Chignahuapan −0.702). No son dos dimensiones independientes. Sus correlaciones intraperfil con NDVI mayo son −0.180 y +0.176, respectivamente: tienen poca redundancia lineal directa con el estado espectral de mayo. Esto es geometría de X, no importancia causal o predictiva.

La extracción original se reprodujo desde las fechas suministradas. Sentinel tiene31–43 fechas y siete meses válidos por parcela para estos índices; Planet NDVI tiene al menos69 fechas. Se detectaron1,885observaciones LAI negativas y no se certifica una escala física ni evento de siembra/emergencia.

Al retirar20% de fechas, P90 del cambio de LAIinicio está entre17.4 y22 días; para SAVIduración,21.2–25 días. La mediana es0, pero algunos casos cambian mucho. Omitir un mes completo produce P90 de hasta30 días. Son perturbaciones de disponibilidad, no una distribución validada de error de medición. La estabilidad del subespacio original de dos ejes es trivial y no garantiza estabilidad de sus valores temporales.

## 7. Qué conserva PCA

Para el bloque satelital residualizado linealmente contra C-T3:

| Representación | Dimensiones | Reconstrucción intraperfil por observación | Igual peso por perfil |
|---|---:|---:|---:|
| PCA conjunta | 2 | 29.8% | 28.3% |
| PCA conjunta | 5 | 46.1% | 40.9% |
| PCA conjunta | 48 | 89.0% | 87.8% |
| PCA conjunta | 70 | 94.4% | 93.7% |
| Jerarquía equilibrada | 2 | 29.6% | 28.1% |
| Jerarquía equilibrada | 5 | 44.3% | 39.0% |
| Jerarquía equilibrada | 13 | 60.1% | 54.8% |

Estas fracciones son reconstrucción lineal de X (1−SSE/TSS), no porcentaje del rendimiento explicado. Compactar a cinco dimensiones pierde más de la mitad del contraste equilibrado. Eso no prueba que se pierda información predictiva: podría descartarse ruido, pero esta fase no utilizó Y para averiguarlo.

## 8. Ventaja de jerarquía

A cinco dimensiones, la jerarquía no supera a PCA conjunta en retención. Su ventaja es organización y ponderación explícita; no presenta una ventaja descriptiva universal. El90/95% que aparece en la etapa final se refiere a sus scores intermedios, NO al bloque original de1,041 columnas. Por eso13dimensiones pueden alcanzar95% en el espacio jerárquico y reconstruir solo54.8% del contraste original equilibrado.

La jerarquía residual muestra cambios de subespacio al omitir Chignahuapan (solapamiento0.622), omitir perfiles dominantes (0.706) o usar IQR (0.556). Las12 réplicas por perfil son sensibilidad, no muestras independientes ni intervalos de confianza. La carga de cada dimensión se documenta con sus variables dominantes; no se nombran factores agronómicos automáticamente.

## 9. Qué está listo, qué sigue exploratorio

El catálogo revisado utiliza A/B/C sin score agregado. A indica definición y soporte geométrico para una prueba, no prioridad predictiva. Historia2 es sencilla técnicamente pero secundaria por evidencia previa. LAI/SAVI queda exploratoria por redundancia y sensibilidad temporal, aunque puede someterse a una prueba original acotada tras revisión. Los grandes bloques satelitales requieren aceptar explícitamente su pérdida de contraste y sensibilidad. Clima queda principalmente regional; cartografía permanece exploratoria por escala y soporte.

La geometría de X no identifica información condicional general; una representación estable no es automáticamente predictiva y una representación inestable no demuestra irrelevancia agronómica. No hay ganador universal.

## 10. Mediciones necesarias

Validar índices y fechas con observaciones fenológicas reales; documentar producción/superficie/rendimiento; registrar variedad, manejo y fechas; medir suelo parcelario y condiciones de agua; ampliar perfiles y campañas. Más transformaciones de las mismas fuentes no fabrican estas mediciones.

## Cierre

Se entregan catálogo, comparación, estabilidad, espectros, cargas, sensibilidad temporal y dos figuras. Nueve pruebas pasaron para la ejecución v1; la revisión v2 agrega controles de las interpretaciones anteriores. Todo ajuste fue no supervisado respecto al rendimiento. Los65 folds se preservan para la eventual Fase IV y ninguna componente197 se usará como transformación inductiva congelada.

La propuesta conserva máximo tres contrastes: C-T3+LAIinicio; C-T3+LAIinicio+SAVIduración; una representación satelital jerárquica residual de X solo como reserva, si se acepta su pérdida de contraste y se justifica una pregunta distinta de L/M. No se recomienda ejecutar automáticamente el tercero. No hay F8, PLS, entrenamiento de rendimiento ni59predicciones PRED.
'''
(OUT/'representation_report.md').write_text(note,encoding='utf-8')
iv=(OUT/'phase_iv_design.md').read_text(encoding='utf-8')
iv+='\n\nRevisión v2: LAI/SAVI no se clasifican como automáticamente estables ante faltantes. Las pruebas originales requieren revisar esa reserva. La alternativa jerárquica conserva solo39% del contraste equilibrado con5dimensiones y no gana a PCAconjunta; sigue reserva, no prioridad. El95%de varianza de etapa final es intermedio, no original. Clima residualizado no se propone como fuente de nuevas diferencias locales inducidas porNDVI.\n'
(OUT/'phase_iv_design.md').write_text(iv,encoding='utf-8')
consumed=pd.read_csv(OUT/'audit/consumed_hashes.csv');consumed=pd.concat([consumed,pd.DataFrame([dict(path=(SOURCE/'manifest.json').relative_to(ROOT).as_posix(),sha256=sha(SOURCE/'manifest.json'))])],ignore_index=True);consumed.to_csv(OUT/'audit/consumed_hashes.csv',index=False)
artifacts={p.relative_to(ROOT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file()}
(OUT/'manifest.json').write_text(json.dumps(dict(status='complete',phase='III',yield_values_used=0,new_yield_models=0,PRED_predictions=0,F8_executed=False,source_version='v1',source_manifest_sha256=sha(SOURCE/'manifest.json'),review_script_sha256=sha(__file__),review='interpretation only; no new fits or representation tuning',artifacts=artifacts),indent=2),encoding='utf-8')
(ROOT/'documentation/ct3_information_phase_iii.md').write_text('# Fase III: representaciones condicionadas a C-T3\n\n[Informe e interpretación revisada](../outputs/research/ct3_incremental_information/phase_iii/v2/representation_report.md).\n\n[Catálogo](../outputs/research/ct3_incremental_information/phase_iii/v2/representation_catalog.csv), [comparación](../outputs/research/ct3_incremental_information/phase_iii/v2/block_comparison.csv), [estabilidad](../outputs/research/ct3_incremental_information/phase_iii/v2/stability_analysis.csv).\n\n[Fase IV: diseño sin ejecutar](../outputs/research/ct3_incremental_information/phase_iii/v2/phase_iv_design.md).\n\nLa versión v1 conserva cálculos y controles; v2 aclara contraste climático inducido y sensibilidad temporal, sin nuevos ajustes. Scripts374/375. Cero rendimiento usado en representación, cero nuevos modelos de rendimiento, cero59PRED.\n',encoding='utf-8')
print('PhaseIII v2 interpretation review complete; no new fits')
