# G y H — Señales climáticas y complementariedad

Investigaciones independientes de Familia 1; continúan el módulo de precipitación sin renumerar ni sustituir experimentos anteriores. Resultados retrospectivos al cierre de octubre de 2025, versión `v1`.

## Productos

- [G — Temperature Signal Exploration](../outputs/modeling/family_1/g_temperature_signal/v1/report/g_temperature_signal_report.md).
- [H — Joint Climate Signal Exploration](../outputs/modeling/family_1/h_joint_climate_signal/v1/report/h_joint_climate_signal_report.md).
- [Síntesis H1](../outputs/modeling/family_1/h_joint_climate_signal/v1/report/h1_joint_synthesis.md).
- Auditoría y correspondencia con las familias previas: `report/source_audit.json` y `tables/00_repository_correspondence.csv` en G.
- Diccionario y matriz térmica: `data/processed/family_1/g_temperature_signal/v1/`.
- Matriz conjunta de 21 meses/variables y especificación Climate Current original de 48 columnas: `data/processed/family_1/h_joint_climate_signal/v1/`.

Cada investigación contiene tablas, figuras, modelos completos, configuración, semillas, particiones externas e internas, hashes de entradas originales protegidas y manifiesto de artefactos. Los scores PCA descriptivos de 197 parcelas permanecen separados de las transformaciones entrenadas dentro de validación cruzada.

## Resultado principal

RMSE en t/ha: media de métricas por repetición OOF completa, cada una con las mismas 138 parcelas etiquetadas. Aleatoria: diez repeticiones de cinco folds. Cada protocolo geográfico: cinco folds y una repetición.

| Validación | Lluvia mensual | Tmin + Tmax | Lluvia + Tmin + Tmax | Climate Current original |
|---|---:|---:|---:|---:|
| Aleatoria | 0.52136 | 0.54048 | 0.51963 | 0.52002 |
| Perfil climático | 0.54435 | 0.54498 | 0.56072 | 0.54028 |
| Municipal | 0.69536 | 1.25509 | 0.84039 | 0.77735 |
| Espacial | 0.73479 | 1.74210 | 0.95001 | 0.97985 |

Añadir temperatura mejora la RMSE aleatoria en 0.00173 t/ha y solamente 52% de sus folds; empeora la RMSE por perfil en 0.01637, municipal en 0.14503 y espacial en 0.21522 t/ha. No hay evidencia consistente para sustituir el bloque climático actual. Esta conclusión corresponde al algoritmo y regularización auditados; no prueba que temperatura carezca de información en cualquier modelo o población.

La temperatura contiene información temporal estructurada: dos componentes de Tmin/Tmax explican 98.00% de su variación estandarizada entre parcelas. PCA descriptivo no determina cuánto rendimiento explica. La sensibilidad PCR selecciona componentes dentro de validación interna.

Lluvia, temperatura y combinación mantienen 53 perfiles exactos. Añadir temperatura subdivide cero grupos de lluvia y distingue cero pares antes iguales. Los rásteres tienen la misma resolución práctica de 0.05° y todas las parcelas intersectan las mismas celdas. Existe una diferencia de origen de aproximadamente 3.3 cm; no se afirma igualdad bit a bit de las cuadrículas.

El Climate Current original recuperado es Elastic Net con 48 resúmenes retenidos: diez de precipitación y 38 térmicos. Se reutilizaron exactamente sus predicciones aleatorias originales; su RMSE publicada, **0.509210**, es una media de RMSE de folds, mientras **0.520019** es la media de RMSE por repetición completa. Ambas agregaciones se conservan y no deben mezclarse. Champion usa una selección climática TOP20 y correcciones residuales de Sentinel histórico y topografía; sus resultados se recuperaron como contexto y permanecen intactos.

## Reproducción

Desde la raíz del repositorio:

```powershell
python scripts/modeling/318_g_h_climate_signal_modeling.py --phase all --run-id v2
```

También se pueden separar las fases:

```powershell
python scripts/modeling/316_g_temperature_signal_exploration.py --run-id v2
python scripts/modeling/317_h_joint_climate_signal_exploration.py --run-id v2
python scripts/modeling/318_g_h_climate_signal_modeling.py --run-id v2
```

Una corrida completa se protege contra sobrescritura. En una corrida interrumpida, la fase predictiva reutiliza checkpoints con la misma configuración. Para nuevas especificaciones se requiere una versión nueva.

La fase H reutiliza G descriptivo y la PCA y particiones existentes del módulo de precipitación. Mantiene nombres diferentes para perfiles de lluvia de enero de 2022 a octubre de 2025 y perfiles conjuntos exactos de abril–octubre de 2025; se verificó que las particiones de ID coinciden, por lo que pueden compartir los folds originales.

## Verificación

```powershell
python -m unittest discover -s tests -p 'test_climate_signal*.py' -v
python -m unittest discover -s tests -p 'test_rainfall*.py' -v
```

Las verificaciones abarcan cobertura y alineación, cálculo de resúmenes y anomalías, exclusión de meses futuros y etiquetas ocultas, fitting interno, conservación de folds, reproducción de modelos guardados, escalamiento exclusivo de entrenamiento, cache original y deltas pareados. La evaluación de 59 parcelas sin etiqueta, un entrenamiento definitivo y cambios al Champion quedan fuera de estas investigaciones.

## Investigaciones propuestas, aún sin implementar

Validar otros ciclos con rendimiento observado; estudiar fuentes con mayor detalle espacial y variables de manejo, suelo o fenología capaces de distinguir parcelas intraperfil; verificar en datos independientes cualquier sustitución climática. La dispersión de Y dentro de perfiles idénticos no identifica por sí sola una causa agronómica.
