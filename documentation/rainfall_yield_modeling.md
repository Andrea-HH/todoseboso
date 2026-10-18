> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Rainfall Yield Modeling — versión 1

Módulo retrospectivo de rendimiento de cebada, abril–octubre 2025, que consume
las series canónicas de Familia 1. La unidad supervisada es la parcela: 138
ENTRENAMIENTO y 59 PREDICCION. Los 48 meses no multiplican la muestra etiquetada.

## Ejecución

Desde la raíz del repositorio, en el entorno Python existente:

```powershell
python -m unittest discover -s tests -p "test_rainfall_*.py" -v
python scripts/modeling/313_rainfall_yield_audit.py --run-id v2
python scripts/modeling/314_rainfall_yield_modeling.py --audit-id v2 --run-id v2
```

Cada ejecución exige un identificador nuevo y rechaza sobrescrituras. La segunda
orden verifica de nuevo todos los rásteres, todas las intersecciones y la tabla
canónica, sin publicar una segunda serie longitudinal. La tercera comprueba los
hashes de entradas auditadas y guarda configuraciones antes del entrenamiento.
No hay descargas ni dependencias nuevas frente al entorno del proyecto.

## Integración

Los módulos reutilizan `family_1.temporal_primitives` para estadísticos compatibles
en ventanas completas y `family_1.stage4_modeling.save_splits` para los 50 folds
aleatorios existentes. Las diferencias/rachas se definen en transiciones
mensuales, no días ni intervalos irregulares; las ventanas de etapa solicitadas
difieren de las ya usadas por el proyecto y quedan explícitamente versionadas.

```python
import pandas as pd
from family_1.rainfall_features import merge_rainfall

existing = pd.read_parquet("data/processed/family_1/features/family1_features_all.parquet")
rain = pd.read_parquet("data/processed/family_1/rainfall_yield/v1/rainfall_features.parquet")
combined = merge_rainfall(existing, rain)
```

El consumidor selecciona una familia compacta y ajusta imputación, escala y
cualquier selección supervisada dentro de su propia CV. No se debe añadir todo
el diccionario simultáneamente a un modelo. El módulo no sobrescribe
`family1_features_all`, modelo TOP20/TOP15 ni los experimentos anteriores.

## Definiciones y decisiones

- Los acumulados requieren todos los meses de su ventana. Una referencia
  histórica mensual requiere los tres años 2022, 2023 y 2024 para ese mes.
  No se rellenan ni se interpolan meses antes del modelado.
- Desviación estándar muestral: divisor 6 para siete meses. Total/mean son
  exactamente redundantes; la biblioteca conserva ambos para reutilización,
  pero los experimentos no los incorporan juntos.
- CV y fracciones de lluvia son NaN con denominador ≤0.000001 mm. Anomalías
  relativas son NaN para referencia <1 mm: umbral declarado de estabilidad,
  sin sustituir denominadores ni diagnosticar sequía.
- Empates exactos de máximos/mínimos: primer mes cronológico. Si no hay déficit
  histórico, el mes de déficit es NaN. Los meses extremos se codifican one-hot
  con abril como referencia en modelos lineales; son categorías, no magnitudes.
- Rachas dinámicas: número de transiciones consecutivas, hasta seis.
  Anomalías: número de meses consecutivos, hasta siete. Un valor dentro de
  ±0.000001 mm de cero rompe la racha; un faltante invalida la racha de la ventana.
- Etapas: abril–mayo, junio–agosto, septiembre–octubre. Son calendáricas;
  no hay fechas fenológicas observadas por parcela en las fuentes revisadas.
- Pre-ciclo enero–marzo es una sensibilidad separada. No representa humedad
  de suelo observada. SPI, climatologías largas, sequía externa, lluvia diaria,
  extremos e interacciones se dejan para futuras etapas, sin generar proxies.
- La predicción usa lluvia hasta octubre; no mide capacidad de pronóstico
  antes de la cosecha ni generalización a otro ciclo etiquetado.
- La agrupación de validación climática usa los 46 meses disponibles hasta
  octubre 2025. Los 48 meses completos se usan solo para auditar y describir
  el universo climático; se verificó que excluir noviembre/diciembre conserva
  exactamente grupos y folds de esta ejecución.

## Productos v1

- Auditoría y contexto del repositorio:
  `outputs/data_audit/family_1/rainfall_yield/v1/`. La auditoría ampliada `v2/`
  incluye hashes de todas las piezas de geometría, días acumulados, escala,
  offset y sensibilidad geodésica, sin crear otra serie climática.
- Características sin objetivo y diccionario completo con fórmulas, unidades,
  periodo, fuente, interpretación, faltantes, advertencias y versión:
  `data/processed/family_1/rainfall_yield/v1/`.
- Configuración, manifiesto, tablas, gráficos, informes, splits externos/internos
  y modelos serializados de cada fold:
  `outputs/modeling/family_1/rainfall_yield/v1/`.

Métrica principal: media de métricas OOF de cada repetición completa, con MAE,
RMSE, R² y sesgo predicción−real. Las métricas espaciales se reportan aparte.
Las gráficas regionales y de residuos usan OOF promediado y se etiquetan como
diagnóstico. Los folds repetidos se solapan: su dispersión no es un intervalo
confirmatorio basado en muestras independientes.

Resultado observado: Ridge mensual tiene RMSE aleatorio 0.5237 t/ha,
MAE 0.3716 y R² 0.6185, frente a RMSE 0.8560 del baseline. RMSE por perfiles
climáticos 0.5336, por municipios 0.6892 y espacial 0.7843 t/ha. Las 23 pruebas
matemáticas y de integración pasaron. El reporte técnico analiza las diferencias
entre familias, sesgos y transferencia espacial.

E7 selecciona una combinación compacta de familias dentro de la CV interna.
El candidato exige ≥5% de mejora RMSE aleatoria, ganar ≥80% de folds aleatorios
y superar el baseline de cada protocolo agrupado. Aun si pasa, es exploratorio:
no existe prueba final independiente y la selección entre experimentos puede
ser optimista. Ninguna asociación se interpreta como efecto causal.

## E8 — Rainfall PCA & Principal Component Regression

E8 consume exclusivamente los siete acumulados CHIRPS de abril–octubre de
2025. Se integró sobre las características y funciones del módulo, con copias
idénticas de los 65 folds externos y las asignaciones internas de E3. Los
resultados E0–E7/F y modelo TOP20/TOP15 se verificaron mediante hashes y se conservaron.
Los modelos integrales del repositorio se auditan por separado.

El PCA descriptivo usa 197 parcelas y nunca suministra scores al entrenamiento
supervisado. Cada ajuste predictivo aprende escalamiento, PCA y regresión
dentro de entrenamiento; K y alpha se seleccionan en CV interna. Se evaluaron
PCR con K fijo 1–7, PCR seleccionado y PCA + Ridge seleccionado. El control
K=7 reproduce OLS mensual, verificado en los 65 folds.

Dos componentes explican 93.29% y tres 97.20% de la variación climática. PC1
resume variación conjunta de abril–septiembre; PC2 contrapone octubre con
abril/mayo. PC4 explica solo 2.20%, pero contiene asociación con rendimiento.
PCR aleatorio seleccionó cuatro componentes en 37 de 50 folds: conservar
97% de varianza climática con tres componentes no basta para conservar señal
predictiva. Estas asociaciones son descriptivas, no causales.

RMSE OOF medio por repetición completa, en t/ha:

| Protocolo | E3 Ridge mensual | E8 PCR | E8 PCA + Ridge |
|---|---:|---:|---:|
| Aleatorio | 0.52375 | 0.52380 | 0.52421 |
| Perfiles climáticos | 0.53357 | 0.51750 | 0.51814 |
| Municipal | 0.68920 | 0.88405 | 0.81839 |
| Espacial | 0.78430 | 0.76978 | 0.76703 |

PCR no supera consistentemente a Ridge mensual: el cambio aleatorio es
prácticamente nulo, la mejora espacial gana solo dos de cinco folds y el
deterioro municipal es considerable. La representación total + forma
temporal (seis contrastes Helmert, PCA y Ridge anidado) empeoró frente a
Ridge mensual en los cuatro protocolos. La extensión reconoce la dependencia
de las proporciones y la limitación de usar geometría Euclidiana del simplex.

Hay 53 perfiles mensuales exactos entre 197 parcelas. PCA no incorpora
información para distinguir parcelas con los mismos siete valores. Las
bandas se diagnostican separando lluvia repetida, Y repetido, predicciones
cercanas entre perfiles distintos y promedios de OOF. Los promedios se usan
solo para diagnóstico; las métricas principales mantienen cada repetición.

Productos y ejecución:

- [Reporte técnico E8](../outputs/modeling/family_1/rainfall_yield/e8/v1/report/e8_technical_report.md).
- [Interpretación y nueve respuestas](../outputs/modeling/family_1/rainfall_yield/e8/v1/report/e8_interpretation.md).
- Tablas, figuras, configuración, manifiesto y 715 pipelines predictivos:
  `outputs/modeling/family_1/rainfall_yield/e8/v1/`.
- Matriz mensual y scores descriptivos:
  `data/processed/family_1/rainfall_yield/e8/v1/`.
- Diccionario: `tables/53_transformation_dictionary.csv`; censo y dispersión
  por perfil: `tables/55_profile_census_and_oof_dispersion.csv`.

```powershell
python scripts/modeling/315_rainfall_pca_pcr.py --run-id v2
python -m unittest discover -s tests -p 'test_rainfall_*.py' -v
```

Un run completo es inmutable: para repetir se debe elegir un identificador
nuevo. También se puede separar `--phase audit` y `--phase model` con el mismo
run-id. Los checkpoints permiten continuar un cálculo incompleto con la
misma configuración. E8 no sustituye modelo TOP20/TOP15 ni requiere una mejora positiva
para ser informativo.
