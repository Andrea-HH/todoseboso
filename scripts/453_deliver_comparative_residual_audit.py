"""Package frozen OOF diagnostics; no predictive fitting or model selection."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/research/case_outliers_and_model_residual_comparison/v1'
TABLES = OUT / 'tables'
MAIN = ['LOCAL04D', 'CT3', 'J7_BOTH', 'MIX_EXPERT10', 'MIX_EXPERT9']

def md(frame):
    def cell(value):
        if isinstance(value, (float, np.floating)):
            return f'{value:.4f}'
        return str(value).replace('|', '/').replace('\n', ' ')
    rows = ['| ' + ' | '.join(map(str, frame.columns)) + ' |',
            '| ' + ' | '.join(['---'] * len(frame.columns)) + ' |']
    rows.extend('| ' + ' | '.join(cell(v) for v in row) + ' |'
                for row in frame.itertuples(index=False, name=None))
    return '\n'.join(rows)

def main():
    verified = 0
    for filename in ['case_audit_manifest.json', 'residual_comparison_manifest.json']:
        manifest = json.loads((OUT / filename).read_text(encoding='utf-8'))
        for filename, expected in manifest.get('source_sha256', {}).items():
            assert hashlib.sha256(Path(filename).read_bytes()).hexdigest() == expected, filename
            verified += 1
    p = pd.read_parquet(OUT / 'comparison_oof_residuals.parquet')
    assert len(p) == 16146 and p.groupby('experiment').size().eq(1794).all()
    assert not p.duplicated(['experiment', 'protocol', 'repeat', 'ID_POLIGONO']).any()
    for _, g in p.groupby(['experiment', 'protocol', 'repeat']):
        assert len(g) == 138 and g.ID_POLIGONO.nunique() == 138
        e = (g.y_pred - g.y_true).to_numpy()
        assert np.isclose(np.mean(e**2), np.var(e) + np.mean(e)**2)
    frames = {f.stem: pd.read_csv(f) for f in TABLES.glob('*.csv')}
    metrics = frames['models_summary']
    metrics = metrics[metrics.experiment.isin(MAIN)]
    regions = frames['regions_summary']
    quarters = frames['quartiles_summary']
    workbook = OUT / 'comparacion_residuos_y_outliers.xlsx'
    with pd.ExcelWriter(workbook, engine='openpyxl') as writer:
        pd.DataFrame({'lectura': [
            'Error = predicho menos observado; positivo indica sobreestimación.',
            'Aleatoria: métricas sobre OOF completas por repetición, luego media de 10 repeticiones.',
            'Las métricas regionales y cuartiles son descriptivas, no reglas de selección.',
            'MIX_EXPERT9/10 son mezclas; EXPERT9/10 son ramas antes de mezcla.',
            'No se ajustaron nuevos predictores ni se usaron las 59 parcelas PRED.',
            'Los CSV contienen los mismos diagnósticos; outliers_all_numeric incluye el censo completo.',
        ]}).to_excel(writer, sheet_name='LEEME', index=False)
        for name, frame in frames.items():
            if name == 'outliers_all_numeric':
                continue
            frame.to_excel(writer, sheet_name=name[:31], index=False)
        for sheet in writer.book.worksheets:
            sheet.freeze_panes = 'A2'
            sheet.auto_filter.ref = sheet.dimensions
    parts = ['''# Comparación completa de residuos: L40, C-T3, J7 y expertos 9/10

## Alcance y comparabilidad

Se auditaron las predicciones externas de las 138 parcelas conocidas en las mismas 65 particiones: 50 aleatorias (10 repeticiones de cinco folds), cinco por perfil climático, cinco municipales y cinco espaciales. Cada modelo aporta 1,794 predicciones; nueve variantes, 16,146. En aleatoria se calcula cada métrica sobre las 138 OOF de cada repetición y después se promedian las diez métricas. No se promedian métricas de folds ni se fusionan protocolos. El error se define como predicho menos observado.

L40 significa Local04D original: representación de 2,082 descriptores, PCA20 y Ridge local con 24 vecinos geográficos. Su PCA original utiliza características de las 197 parcelas sin targets ocultos (representación transductiva); esta auditoría conserva esa definición. No es una comparación puramente inductiva de todos los preprocesamientos. Se excluyó el banco GeoC 97/41, incompatible con estas particiones. La referencia CT3 coincide exactamente entre pipelines y J7 se reprodujo exactamente desde sus modelos guardados.

J7_BOTH es la mezcla compacta con experto local de siete variables y asignación de peso mediante características físicas. MIX_EXPERT10 y MIX_EXPERT9 son las mezclas alternativas; no deben confundirse con sus ramas EXPERT10 y EXPERT9 aisladas. Los recuentos 28/31/30 son campos de entrada distintos de las arquitecturas completas, no grados de libertad efectivos; las etiquetas 7/9/10 cuentan variables del experto local. Se reconstruyeron las ramas desde parámetros congelados, sin reentrenar ni modificar modelos.

## Panorama: RMSE / R²
''', md(frames['presentation_RMSE_R2'].rename(columns={'Unnamed: 0':'modelo'})), '''

J7 reduce frente a CT3 el RMSE aleatorio en 0.0252 t/ha (4.9%) y por perfil en 0.0316 (6.1%). La diferencia municipal es 0.0004 y espacial empeora 0.0020: no hay evidencia de una ganancia territorial relevante. Local04D conserva una interpolación competitiva, pero pierde mucho al excluir municipios o bloques. Las tres mezclas compactas son prácticamente indistinguibles a esta escala.

## Magnitud, dirección y frecuencia del error
''', md(metrics[['experiment','protocol','rmse','mae','r2','bias','error_sd','p95_absolute','within_050','within_100']]), '''

within_050 y within_100 son fracciones de errores absolutos dentro de 0.5 y 1 t/ha. RMSE penaliza especialmente errores grandes; MAE mide la desviación absoluta media. No son intervalos predictivos por parcela.

CT3 coloca el 77.5% de errores aleatorios dentro de 0.5 t/ha, frente al 76.2% de J7, aunque J7 tiene menor RMSE y MAE. J7 mejora el balance de magnitudes y reduce la cola: percentil 95 del error absoluto de 0.855 frente a 1.053 t/ha. Por ello no mejora cada parcela ni cada umbral. Local04D queda en 73.6% dentro de 0.5.

El sesgo aleatorio agregado es cercano a cero para todos, pero no significa ausencia de sesgos regionales. En espacial, CT3 sobreestima 0.191 t/ha; J7 0.291; Local04D 0.471. La componente local puede reducir dispersión mientras incrementa el desplazamiento positivo. Las tablas incluyen la identidad MSE = varianza del error + sesgo² por repetición.

## Dónde funciona cada modelo
''', md(regions[(regions.experiment.isin(MAIN)) & (regions.kind=='Estado')][['experiment','protocol','zone','n','rmse','mae','r2','bias']]), '''

La principal fortaleza propia de Local04D aparece en Hidalgo bajo aleatoria: RMSE 0.341 y R² 0.802, frente a 0.368/0.770 de J7 y 0.439/0.673 de CT3. Con vecinos territoriales presentes aprovecha estructura local. Esta ventaja no se conserva al retirar territorios.

En Puebla aleatoria, CT3 obtiene RMSE 0.556 y R² 0.080 frente a 0.563/0.060 de J7. El R² global de aproximadamente 0.67 no equivale a explicar 67% dentro de cada estado. En Tlaxcala el R² aleatorio es negativo para todos; su escasa variabilidad del target hace que diferencias moderadas de error produzcan R² muy negativos. Un R² negativo compara contra la media observada del subconjunto, que no sería conocida al predecir.

## Transferencia municipal
''', md(regions[(regions.experiment.isin(MAIN)) & (regions.kind=='Municipio') & (regions.protocol=='municipality')][['experiment','zone','n','rmse','mae','r2','bias']]), '''

En Singuilucan, Local04D tiene RMSE 1.401 y sesgo +1.338, frente a 0.888/+0.778 de J7 y 0.868/+0.759 de CT3. En Calpulalpan, J7 mejora respecto a CT3 (0.471 frente a 0.493) y claramente respecto a Local04D (0.713). En Chignahuapan, J7 y CT3 quedan prácticamente empatados (0.580 y 0.581). Los expertos 9/10 no resuelven una estructura municipal diferente de J7.

## Transferencia espacial y bloques
''', md(regions[(regions.experiment.isin(MAIN)) & (regions.kind=='fold') & (regions.protocol=='spatial')][['experiment','zone','n','rmse','mae','r2','bias']]), '''

En bloque 3, Local04D presenta RMSE 1.459 y sesgo +1.396; CT3 0.910/+0.718; J7 0.916/+0.731. El bloque 4 también es difícil: Local04D 1.313, CT3 0.799 y J7 0.799. No todo el problema espacial se limita al bloque 3. Local04D sí gana en bloque 5 (0.214 frente a 0.360 de CT3): su debilidad es la inestabilidad entre territorios, no una derrota en absolutamente todos.

## Rendimientos bajos, medios y altos
''', md(quarters[quarters.experiment.isin(MAIN)][['experiment','protocol','ymin','ymax','n','rmse','mae','r2','bias']]), '''

En el cuartil bajo (2–3.2 t/ha), todos tienden a sobreestimar. En aleatoria Local04D tiene RMSE 0.658, J7 0.665 y CT3 0.721. En espacial Local04D se deteriora a 1.670 con sesgo +1.640; CT3 queda en 1.108 y J7 en 1.120. En el cuartil alto (4.56–5.59), todos subestiman: J7 mejora espacialmente respecto a CT3 (0.437 frente a 0.530), pero ese beneficio se compensa con otros errores. Los cuartiles dependen del target observado: sirven para diagnóstico, nunca para decidir qué modelo usar en una parcela sin rendimiento conocido.

## Diferencias entre parcelas del mismo perfil

Se comparan errores al predecir diferencias de rendimiento entre pares del mismo perfil, separando igual peso a cada perfil y peso por número de pares. Estas métricas no son el RMSE convencional por parcela.
''', md(frames['intraprofile_summary']), '''

En aleatoria, con igual peso por perfil, Local04D obtiene 0.575, J7 0.578 y CT3 0.590; ponderando por pares, Local04D obtiene 0.801, J7 0.777 y CT3 0.771. La conclusión cambia con la ponderación: no hay una superioridad intraperfil universal. Los perfiles grandes requieren atención propia.

## Concentración, dependencia espacial y estabilidad al omitir zonas

Las cinco parcelas de mayor error concentran aproximadamente el 39.3% del SSE aleatorio de Local04D, 37.5% de CT3 y 40.8% de J7. No se eliminaron casos. Una fracción alta muestra influencia de la cola; una fracción menor tampoco implica robustez si muchos errores son grandes, como ocurre con Local04D espacial.

El Moran descriptivo espacial de residuos es 0.676 para Local04D, 0.441 para CT3 y 0.389 para J7. Tras centrar residuos por estado queda en 0.323, 0.245 y 0.254. Parte de la estructura de error es regional, pero queda dependencia local. No se presentan estos índices como pruebas de significancia ni como evidencia causal.

Las tablas omissions_* recalculan métricas quitando una zona completa, conservando todas las predicciones originales: no se reajusta ningún modelo. Permiten comprobar si la conclusión depende de un bloque, estado o municipio. El bloque 4 confirma que el deterioro de Local04D no procede exclusivamente del bloque 3.

## ¿Se complementan los residuos?
''', md(frames['error_complementarity_summary']), '''

J7 y las mezclas de expertos 9/10 tienen correlaciones de errores cercanas a 0.999–1: son pequeñas sensibilidades de una misma solución, no expertos de errores muy distintos. Local04D y J7 tienen correlación aproximada de 0.973 en aleatoria y 0.850 espacial. Esa menor correlación espacial no garantiza una mezcla útil: Local04D añade mucho sesgo y error propio. Se entregan ganancias pareadas por parcela; no se entrenó una nueva mezcla usando estos resultados.

Las ramas EXPERT7/9/10 aisladas tienen RMSE municipal de aproximadamente 0.656 y espacial de 0.809/0.814/0.834. Las mezclas completas bajan a aproximadamente 0.581 y 0.681. La protección territorial proviene en parte importante de conservar CT3 y controlar el peso del experto.

## Incertidumbre de las comparaciones
''', md(frames['paired_cluster_tests']), '''

Se realizaron 40 comparaciones pareadas principales, con bootstrap agrupado y prueba de cambio de signo de diferencias de pérdida por grupo; ajuste Holm entre las 40. Ninguna conserva p<0.05 tras Holm. Hay pocos grupos territoriales y la potencia es limitada: con cinco bloques una prueba bilateral exacta de signos tiene resolución mínima de 0.0625. Los intervalos bootstrap y esta prueba responden a supuestos distintos; un intervalo que excluye cero no autoriza ignorar la prueba y su multiplicidad. Tampoco la falta de significancia demuestra equivalencia. La reutilización histórica de esta validación obliga a tratar las decisiones nuevas como exploratorias.

## Parcelas 171 y 015 en el contexto completo

Ambas son outliers de rendimiento en Chignahuapan y en su perfil, no outliers globales por Tukey. Ninguna presenta un outlier continuo evaluable en las 28 entradas de J7; sus categorías de suelo son comunes. Todos los modelos las sobreestiman cerca de 2 t/ha en aleatoria. No son un problema exclusivo de una arquitectura.

Fuera de esas entradas, 171 destaca por bajo cambio neto de EVI Planet (0.014 frente a mediana municipal 0.177); 015 por TPI 3×3 bajo (−3.637 frente a −0.065) y una tasa derivada de crecimiento NDVI alta (0.108 frente a 0.039). Son pistas distintas, no una causa compartida demostrada. TPI bajo no demuestra humedal ni inundación. Fechas y tasas derivadas no equivalen a fechas observadas de siembra/cosecha.

El censo cubre 1,867 variables propias, 1,831 predictores no climáticos auditados de GeoC y las entradas de J7; no equivale a auditar cada uno de los 2,082 descriptores originales de Local04D. Los outliers se describen en TRAIN138, estado, municipio y perfil, incluyendo el caso focal. Se usa Tukey y se muestra sensibilidad MAD; en variables climáticas repetidas, MAD muy pequeño puede producir z enormes sin percentiles extremos. No se cuentan columnas correlacionadas como pruebas independientes ni se atribuye causalidad a las banderas.

## Fortalezas, debilidades y recomendación

- **CT3:** referencia de cuatro entradas, mejor equilibrio espacial y resultados municipales casi idénticos a las mezclas. Pierde algo de precisión aleatoria/por perfil y no distingue todos los rendimientos dentro del mismo clima.
- **Local04D:** fortaleza de interpolación geográfica, especialmente Hidalgo, y algunos bloques. Debilidad de transferencia: errores regionales amplios y sesgo positivo fuerte al excluir territorios. Su complejidad y representación transductiva requieren documentar el escenario de uso.
- **J7_BOTH:** mejora pequeña pero consistente en magnitud aleatoria y por perfil; reduce cola de error y conserva el nivel territorial de CT3. No mejora realmente el RMSE espacial y aumenta su sesgo positivo. Es una alternativa de precisión/interpolación, no un ganador universal.
- **Mezcla experto10:** mínima ventaja por perfil (0.487 frente a 0.489 de J7), con mayor sesgo y RMSE espacial. No justifica por sí sola aumentar complejidad.
- **Mezcla experto9:** prácticamente reproduce J7 y logra una diferencia municipal de solo 0.00014 t/ha. No demuestra una ventaja material.

Conservar CT3 como benchmark territorial y J7 como mezcla compacta de referencia. No añadir 9/10 o una calibración global por diferencias milimétricas. La oportunidad es explicar fallos compartidos mediante información adicional respaldada por más casos y validación interna, no crear una regla para dos parcelas. Las trayectorias estacionales y posición topográfica son hipótesis para una fase futura acotada, no variables ya demostradas como correctores generales. No se promovió un champion ni se generaron predicciones PRED.

## Entregables

Libro `outputs/research/case_outliers_and_model_residual_comparison/v1/comparacion_residuos_y_outliers.xlsx`: métricas completas, regiones, bloques, cuartiles, intraperfil, omisiones, concentración, comparaciones y residuos por cada parcela. CSV y Parquet conservan los datos numéricos de origen. Figuras: `model_calibration_comparison.png` y `bias_and_threshold_comparison.png`. Scripts reproducibles: 451 (outliers), 452 (residuos), 453 (empaquetado y verificación).
''']
    report = ROOT / 'documentation/comparative_residuals_and_case_outliers.md'
    report.write_text('\n\n'.join(parts), encoding='utf-8')
    result = {'status':'complete','source_hashes_verified':verified,'oof_rows':len(p),
              'models':p.experiment.nunique(),'no_predictive_refit':True,
              'report_sha256':hashlib.sha256(report.read_bytes()).hexdigest(),
              'workbook_sha256':hashlib.sha256(workbook.read_bytes()).hexdigest()}
    (OUT/'delivery_manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__ == '__main__':
    main()
