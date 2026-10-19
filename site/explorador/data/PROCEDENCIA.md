# Procedencia de los datos del mapa

- **Predicciones**: CSV original `Reference26_predictions59.csv` proporcionado por el equipo, generado por `nuriaarroyo/FIRA_AgroCebada` en `outputs/modeling/current_champions_final/v1/`. Se conserva sin cambiar valores ni IDs: 59 registros de `ID_POLIGONO,RENDIMIENTO_T_HA`.
- **Coordenadas y geometrías**: `GeoCebada-Frontend-Andrea 2.zip`, archivo `data/private/parcelas.geojson`; se conservaron las coordenadas y los 197 polígonos originales, sin recalcular centroides ni introducir posiciones nuevas.
- **Factores agroclimáticos**: del archivo `data/private/parcel_features_competition.csv` del frontend, filtrado exclusivamente a las columnas que consulta la ficha interactiva.
- **No incluidos**: rendimientos observados de las 138 parcelas de entrenamiento, variables del resto de la tabla de características, y artefactos de modelado.
- **Verificación**: los 59 ID de Reference26 coinciden exactamente con los 59 ID del conjunto PREDICCION de las 197 geometrías. La media de predicciones coincide con la documentada para Reference26 (3.956432328667021 t/ha).
- **Formato**: `mapa_publico.json.gz`, JSON UTF-8 comprimido con gzip; `geometry` es GeoJSON FeatureCollection y `climate` son mediciones por `ID_POLIGONO`.
- **Alcance**: las coordenadas de la capa vienen del frontend entregado, no se contrastaron numéricamente con un archivo geográfico original del repositorio de Nuria, que no está publicado.
