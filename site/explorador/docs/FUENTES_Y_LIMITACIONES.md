# Fuentes, integridad y límites de la propuesta

La fuente científica principal es el repositorio público [heri-espino/GeoC](https://github.com/heri-espino/GeoC). Esta interfaz es un desarrollo visual separado.

## Archivos reutilizados

| Archivo local | Archivo público verificado | SHA-1 de blob Git |
| --- | --- | --- |
| `data/predictions.csv` | [`reports/checkpoint_05/final_predictions.csv`](https://github.com/heri-espino/GeoC/blob/main/reports/checkpoint_05/final_predictions.csv) | `fc67353fe761251b012c885c31cfc0fb9f38a868` |
| `data/checkpoint07_summary.csv` | [`website/data/checkpoint07_summary.csv`](https://github.com/heri-espino/GeoC/blob/main/website/data/checkpoint07_summary.csv) | `644700050eec21864cf22ede9477bf5db3696e99` |
| `data/checkpoint08_summary.csv` | [`website/data/checkpoint08_summary.csv`](https://github.com/heri-espino/GeoC/blob/main/website/data/checkpoint08_summary.csv) | `efcd3f3f7a0caf586400d424eb8f2d601185a223` |

Estos identificadores fueron comprobados al construir el starter. La verificación en `scripts/verificar_datos.py` detecta cambios locales respecto a los CSV fuente utilizados al crear esta versión. Si el repositorio original actualiza resultados, **no** cambies los CSV sin revisar primero la decisión de selección del modelo.

## Datos y método

- El concurso tiene 197 parcelas; 138 con objetivo observable, y **59 con rendimiento reservado**.
- `ID_POLIGONO` es el identificador canónico, `RENDIMIENTO_T_HA` representa rendimiento en t/ha.
- El modelo seleccionado es **Local04D**, regresión Ridge geográfica local con 24 vecinos y regularización α = 30.
- Las 59 cifras mostradas son estimaciones publicadas, no valores verdaderos ni rendimientos ya comprobados.
- La media e histograma del dashboard describen **únicamente las estimaciones**, no la precisión del modelo.

## Validación

- Checkpoint 07: Local04D tiene RMSE pooled = **0.495741 t/ha** en 16 particiones de desarrollo. Cada partición reserva 41 pseudo-objetivos y utiliza 97 parcelas de entrenamiento.
- Checkpoint 08: Local04D fijo tiene RMSE pooled = **0.481936 t/ha** en **otro** banco de 16 particiones.
- Las métricas de 07 y 08 **no son directamente comparables entre sí** como mejora del modelo, pues difieren las máscaras de validación.
- Las predicciones repetidas de validación no son 656 parcelas independientes; varias parcelas pueden repetirse entre particiones.
- El error de las 59 parcelas reales **no puede calcularse** con este frontend, porque sus etiquetas siguen ocultas.

Para detalles metodológicos y experimentos consultables: [`docs/METODOLOGIA_Y_RESULTADOS.md` del repositorio fuente](https://github.com/heri-espino/GeoC/blob/main/docs/METODOLOGIA_Y_RESULTADOS.md).

## Lo que no hace esta web

1. No ejecuta entrenamiento de Local04D en el navegador.
2. No permite inferencia real para una nueva parcela arbitraria.
3. No incluye cartografía real, ni inventa coordenadas. La ilustración del encabezado es conceptual.
4. No garantiza desempeño fuera de estas parcelas.
5. No sustituye informes científicos, bibliografía o anexos del concurso.

## Antes de publicar

Verifica con el equipo la autorización de uso y redistribución de estos resultados y los derechos sobre datos originales. Aunque los CSV estén disponibles públicamente, su disponibilidad no establece por sí sola una licencia de reutilización.

## Cobertura regional de registros de nuevas parcelas

El formulario **únicamente admite Hidalgo, Puebla y Tlaxcala**. Se valida el estado seleccionado y la pertenencia de coordenadas al polígono de referencia de ese estado. La capa utilizada se consulta vía HTTPS desde [strotgen/mexico-leaflet](https://github.com/strotgen/mexico-leaflet/blob/master/states.geojson) (archivo público `states.geojson`, propiedades `state_name`, CRS84). **No se incorpora una copia en este repositorio**. No se conoce en esta revisión una licencia explícita de redistribución para este archivo; revisar sus términos antes de empaquetar o redistribuir sus geometrías.

La geometría externa puede variar o no estar disponible: si falla, el formulario **no acepta** el registro. Son límites de referencia para un prototipo, no delimitaciones oficiales definitivas; cerca de fronteras estatales conviene revisar con cartografía oficial. Se trata de una comprobación en cliente; cuando haya un servicio de inferencia real, debe repetirse en servidor.

El municipio es de captura libre y no se verifica con un catálogo. No se determina que la parcela esté sembrada con cebada mediante estas coordenadas: el usuario debe proporcionar información verificada sobre la unidad de producción.

**Estado del módulo:** consulta de las 59 predicciones reales + preparación de registro para nuevas parcelas. La nueva parcela no obtiene todavía un rendimiento predicho.
