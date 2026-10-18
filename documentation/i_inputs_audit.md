> **Estado de lectura (2026-10-18):** los champions actuales son **Reference26 y Compact14**; véanse sus [fichas vigentes](models/README.md). Este documento conserva la investigación y las decisiones de su etapa. Los nombres heredados `Champion`/`CHAMPION`/`A_CURRENT_CH_H_T` y la receta TOP20 → TOP15 → topografía corresponden al **modelo histórico TOP20/TOP15**, salvo que el texto identifique expresamente Reference26 o Compact14. Una frase de esta etapa como «no se promueve» no revoca la selección posterior de 26/14.

# Sección I — Auditoría inicial de insumos

Primera entrega, previa a crear scripts de análisis. Se reutiliza el procesamiento existente; esta sección no entrena modelos ni modifica E–H o el modelo TOP20/TOP15.

| Insumo | Estado | Uso y reserva |
|---|---|---|
| Parcelas y maestro originales | Utilizable | 197 geometrías, ID y conjunto; rendimiento exclusivamente de 138 TRAIN. Los 59 PREDICT no se consultan para asociaciones. |
| Perfiles de G/H | Utilizable | 53 perfiles exactos; reutilizar `06_profile_memberships.csv`. La partición conjunta coincide con lluvia, Tmin y Tmax. |
| Elevación y pendiente | Utilizable | `topography_basic_features.parquet`, 197 filas; DEM CEM4 y pendiente de 120 m. Elevación en metros, pendiente en grados. |
| Estado y municipio | Utilizable | Campos reales de la geometría original; no existe campo de localidad. |
| Localidades externas | Proximidad únicamente | CSV con CVEGEO, nombre, municipio y coordenadas decimales; puntos, sin delimitación de pertenencia y sin fecha comprobada. |
| Carta E1402, PDF y reversos | Contexto temático | Serie III, 1:250 000, WRB 2014. Hay claves y leyenda; los perfiles de laboratorio no tienen correspondencia parcelaria validada. |
| E1402 TIFF | Requiere validación | Transformación geográfica y leyenda no bastan para asignar unidades por RGB. Píxel gráfico no equivale a precisión temática. |
| Vector nacional oficial INEGI 794551118313 | En validación | Serie III, WRB 2014, edición 2024, cobertura 2021; descarga oficial disponible. Comprobar geometrías, CRS, atributos, cobertura y compatibilidad local antes de intersectar. |

Familia 1 utiliza extracciones canónicas y arquitectura residual; Familia 2 estudia representaciones funcionales y Familia 3 estructurales. Los resultados y protocolos existentes de E–H se conservan. No se reconstruyen series climáticas, topografía ni folds.

El resultado guardado del modelo TOP20/TOP15 muestra RMSE medio por fold 0.505247 en clima, 0.489548 después de historia satelital y 0.486505 después de topografía: la mejora incremental topográfica es 0.003042 t/ha en esa arquitectura. Es evidencia previa específica de ese protocolo, no garantía para las variables de esta sección.

La auditoría anterior de suelo (`outputs/data_audit/soil_pdf_review/assessment.md`) validó contexto y leyenda, pero no intersecciones parcela–unidad. Las representaciones RGB exploradas en fase C no se reinterpretan como categorías edafológicas.

Fuente oficial del vector: [INEGI, conjunto nacional Serie III](https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=794551118313). Su datum declarado ITRF92 época 1988 debe respetarse; no se asignará el CRS de las parcelas a sus coordenadas originales.
