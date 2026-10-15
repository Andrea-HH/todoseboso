# H — Extensión de estructura climática: precipitación + Tmax

Extensión acotada de [H original](../outputs/modeling/family_1/h_joint_climate_signal/v1/report/h_joint_climate_signal_report.md). No crea una sección I ni modifica G/H v1 o Champion.

[Reporte completo con tablas, biplots y figuras](../outputs/modeling/family_1/h_joint_climate_signal/extensions/rain_tmax/v1/report/h_rain_tmax_extension.md).

## Estructura climática

Siete precipitaciones y siete Tmax mensuales de abril–octubre de 2025. Se comparan lluvia sola, Tmax sola, combinación y balance por bloques. Se reutilizan las PCA descriptivas originales de lluvia/Tmax sobre 197 parcelas. Cada representación tiene además una sensibilidad con una fila por cada uno de los 53 perfiles exactos, ajustando tanto escala como PCA con peso igual por perfil.

Los primeros tres PC conjuntos explican **96.70%** de la variación con peso por parcela y **96.45%** con peso por perfil. La orientación cambia al evitar que los grupos de muchas parcelas dominen la covarianza: PC1 con peso por perfil contrapone lluvia total (r=−0.75) y Tmax media (r=+0.72). PC2 conserva un contraste de distribución temporal de lluvia, especialmente mayo frente a octubre, junto con Tmax y geografía.

El balance no añade una estructura distinta: siete columnas estandarizadas en cada bloque ya tienen la misma varianza total. Dividir ambos por √7 solo multiplica globalmente los scores y autovalores; no cambia direcciones ni fracciones de varianza. Por eso no se duplica una PCR balanceada.

Mapas de scores y biplots muestran separación de Tlaxcala y solapamiento parcial entre Puebla e Hidalgo; las relaciones con coordenadas y altitud se cuantifican descriptivamente. La combinación conserva los 53 perfiles existentes, sin distinguir nuevas parcelas. Ningún gráfico confirma clusters o capacidad de transferencia.

## Comparación predictiva

Se añade **una sola PCR OLS conjunta**, con K=1–14 seleccionado internamente. Se conservan los 65 folds externos e internos originales. Las 138 parcelas etiquetadas son el universo supervisado; las 59 restantes no aportan Y. La ponderación igual por perfil es exclusivamente descriptiva.

RMSE en t/ha, media de métricas de cada repetición OOF completa:

| Protocolo | H6: lluvia + Tmax, ENET | PCR lluvia, previa | PCR lluvia + Tmax, nueva | Lluvia sola, ENET |
|---|---:|---:|---:|---:|
| Aleatorio | 0.52011 | 0.52380 | 0.51617 | 0.52136 |
| Por perfil | 0.54910 | 0.51750 | 0.51639 | 0.54435 |
| Municipal | 0.76679 | 0.88405 | 0.93796 | 0.69536 |
| Espacial | 0.96014 | 0.76978 | 0.93078 | 0.73479 |

La PCR conjunta mejora algunos resultados, pero empeora la validación municipal y no supera lluvia sola en transferencia espacial. La mejora no es consistente. Comparar PCR conjunta con PCR de lluvia mantiene el mismo OLS y permite estudiar añadir Tmax; comparar con H6 también cambia algoritmo y no permite atribuir la diferencia exclusivamente a PCA.

Se conservan deltas pareados por fold/repetición y selección K. Folds y repeticiones se solapan; no se tratan como observaciones independientes ni se publican p-valores de esa comparación.

## Reproducción

```powershell
python scripts/modeling/322_h_rain_tmax_extension.py --run-id v2
python -m unittest discover -s tests -p 'test_h_rain_tmax_extension.py' -v
```

El comando crea una versión nueva dentro de `outputs/modeling/family_1/h_joint_climate_signal/extensions/rain_tmax/`. Una ejecución interrumpida reutiliza checkpoints con la misma configuración. Una ejecución completa no se sobrescribe.

Se registran diccionarios de columnas/escala, modelos descriptivos separados, pipelines predictivos completos, configuración, versiones de paquetes, hashes, folds congelados, métricas y referencia al protocolo de perfiles. Las pruebas de artefactos verifican la versión v1 entregada. Las propuestas posteriores quedan sin implementar y Champion se conserva intacto.
