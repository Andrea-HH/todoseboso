# Familia 1 - Etapa 4.5: contribucion por fuente

## Protocolo

Se reutilizaron exactamente los 50 outer folds congelados y el inner KFold de 4 particiones. XGBoost uso el mismo grid regularizado de XGB_CORE; Elastic Net uso mediana, StandardScaler y el grid pequeno existente. Todas las diferencias son pareadas fold a fold. AREA no se evaluo porque no pertenece a CORE ni al diccionario predictivo. No se entreno LightGBM, PLS ni modelos finales.

## Respuestas

1. **Mejor fuente sola:** CLIMATE, RMSE medio XGB=0.5107.
2. **Peor fuente sola:** TOPO_BASIC, RMSE=0.7489.
3. **¿Sentinel domina individualmente?** No; ranking completo en `source_only_metrics.csv`.
4. **¿Planet independiente de Sentinel?** Añadir Planet a S2 cambia RMSE en -0.0003; retirar Planet de CORE cambia -0.0062. Su correlacion residual con S2 es 0.908.
5. **¿Landsat util o redundante?** Delta al retirarlo=+0.0016, empeora en 56% de folds.
6. **¿Climate fuerte solo?** RMSE=0.5107, frente a mejor fuente=0.5107 y CORE=0.5270.
7. **¿Climate mejora Satellite?** Ganancia=+0.0579, win rate=90%.
8. **¿History aporta mas alla?** Delta al retirarlo=+0.0031; Satellite+Context gana +0.0514 frente a Satellite, compartido con Anomaly.
9. **¿Anomaly distinta?** S2+Anomaly gana +0.0893; delta al retirarla=-0.0054.
10. **¿Topography aporta incrementalmente?** Delta al retirarla=+0.0020, win rate=64%.
11. **Mayor perdida al retirar:** S2, delta=+0.0036.
12. **Redundantes:** fuentes con delta cercano a cero o negativo: [{'source': 'S2', 'mean_delta_RMSE': 0.0036}, {'source': 'PLANET', 'mean_delta_RMSE': -0.0062}, {'source': 'LANDSAT', 'mean_delta_RMSE': 0.0016}, {'source': 'CLIMATE', 'mean_delta_RMSE': 0.0018}, {'source': 'HISTORY', 'mean_delta_RMSE': 0.0031}, {'source': 'ANOMALY', 'mean_delta_RMSE': -0.0054}, {'source': 'TOPO_BASIC', 'mean_delta_RMSE': 0.002}].
13. **Debiles solas pero complementarias:** [].
14. **Satellite cerca de CORE:** Satellite=0.5845, CORE=0.5270, diferencia=+0.0575.
15. **Environment-only:** RMSE=0.5251; contiene señal si supera claramente un baseline ingenuo, pero su distancia a CORE es -0.0019.
16. **Satellite+Climate casi todo CORE:** RMSE=0.5267; diferencia frente CORE=-0.0004.
17. **Ayuda en extremos:** Climate-only es la mejor fuente individual en bajos (RMSE=0.7146, bias=+0.4619) y altos (RMSE=0.5132, bias=-0.4192); Sentinel-only lidera el segmento medio (RMSE=0.3571). Ninguna fuente elimina la regresion hacia la media.
18. **Parcelas dificiles:** Climate rescata por >=0.1 t/ha a Sentinel en 16/28; Satellite rescata Climate en 5/28; Environment rescata Satellite en 12/28. De las 9 y-atipicas, 9 mantienen error >=0.5 en los cinco bloques/modelos principales. Los casos transversales mayores son {'AGC_171': 2.165, 'AGC_015': 2.03, 'AGC_034': 1.345, 'AGC_024': 1.345, 'AGC_055': 0.972}.
19. **Errores Satellite/Environment:** correlacion Pearson=0.870; ensemble 50/50 RMSE=0.5324, frente Satellite=0.5845 y Environment=0.5251. No es candidato final.
20. **Coherencia con PLS:** tabla conjunta en `source_contribution_vs_pls.csv`. VIP alto no equivale a aporte unico y su suma depende del numero de features.
21. **Eliminable sin costo aparente:** [{'source': 'PLANET', 'mean_delta_RMSE': -0.0062, 'removal_worsens_rate': 0.38}, {'source': 'ANOMALY', 'mean_delta_RMSE': -0.0054, 'removal_worsens_rate': 0.44}, {'source': 'LANDSAT', 'mean_delta_RMSE': 0.0016, 'removal_worsens_rate': 0.56}]; esto es descriptivo, no autorizacion automatica para borrar features.
22. **Representacion minima eficiente:** Climate-only es la candidata minima estricta: 48 features, RMSE=0.5107, diferencia CORE=-0.0163. Como bloque conceptual mas amplio, Environment Current usa 73 features y RMSE=0.5160. Antes de sustituir CORE debe validarse temporal y espacialmente: Climate 2025 puede actuar como proxy de geografia/temporada bajo CV aleatoria.
23. **Historia cientifica defendible:** separar capacidad individual, aporte unico y complementariedad evita confundir volumen de columnas con informacion. La conclusion se basa en source-only, ablaciones pareadas y ganancias incrementales, no en una sola importancia.
24. **¿Congelar Familia 1?** Si para el protocolo actual: la ganancia no justifica mas tuning o feature engineering dentro de Familia 1. Para despliegue, queda pendiente validar la solucion compacta Climate/Environment fuera de temporada y geografia; no debe reemplazar automaticamente XGB_CORE con este unico experimento. No se inicio Familia 2.

## Cautelas

- Los 50 folds estan correlacionados por RepeatedKFold; no se aplico t-test ingenuo.
- Los intervalos Q25-Q75 y win rates son descriptivos y pareados.
- Una fuente con muchas columnas no necesariamente aporta mas informacion unica.
- El ranking no es causal ni una regla automatica de eliminacion.
