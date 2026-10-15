"""Descriptive inventory only: no fitting, feature selection or PRED inference."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/research/variable_inventory/v1'
OUT.mkdir(parents=True, exist_ok=True)
master_path = 'data/processed/family_1/features/family1_features_all.parquet'
external_path = 'data/processed/phase_c/c0_c1/external_parcel_features.parquet'
soil_path = 'data/processed/family_1/i_climate_conditioned_geographic_edaphological/v1/integrated_diagnostic_197.parquet'
geo_root = 'data/processed/family_4/territorial_intraprofile_program/v1/stage_a/'
fd_path = 'data/processed/family_1/features/family1_feature_dictionary.csv'
ed_path = 'data/processed/phase_c/c0_c1/external_integrated_variable_dictionary.csv'
fd = pd.read_csv(ROOT / fd_path).drop_duplicates('feature_name').set_index('feature_name')
ed = pd.read_csv(ROOT / ed_path).drop_duplicates('variable').set_index('variable')
labels = pd.read_csv(ROOT / 'data/original/01_tablas_maestras/ID_area_rendimiento_70_30_Reto_AgroCebada.csv')
train_ids = set(labels.loc[labels.RENDIMIENTO_T_HA.notna(), 'ID_POLIGONO'])
rows = []
sources = {
 'Sentinel-2': ('data/original/01_tablas_maestras', 'data/processed/family_1/timeseries/sentinel_timeseries_data_dictionary.csv'),
 'Planet': ('data/original/01_tablas_maestras', 'data/processed/family_1/timeseries/planet_timeseries_data_dictionary.csv'),
 'Landsat': ('data/original/01_tablas_maestras', 'data/processed/family_1/timeseries/landsat_timeseries_data_dictionary.csv'),
 'Clima': ('data/original/03_presipitacion; data/original/04_temperatura', 'documentation/g_h_climate_signal_exploration.md'),
 'Topografía': ('data/original/05_topografia', 'data/processed/family_1/environment/topography_data_dictionary.csv'),
 'Suelo': ('data/externo/suelo/inegi_serie_iii_794551118313/conjunto_de_datos', 'data/externo/suelo/e1402.pdf; data/externo/suelo/e1402_reverso_1.pdf; data/externo/suelo/e1402_reverso_2.pdf; data/externo/suelo/inegi_serie_iii_794551118313/diccionario_de_datos/702825092023.pdf; documentation/i_geographic_edaphological_exploration.md'),
 'Geología 250k detallada': ('data/externo/geologia/702825674595_s', 'data/externo/geologia/702825674595_s/metadatos/metadatos_cdgv_1_250_000_serie1.txt; documentation/territorial_program_stage_a.md'),
}

def add(path, columns, block):
    frame = pd.read_parquet(ROOT / path).set_index('ID_POLIGONO')
    for name in columns:
        s = frame[name]; numeric = pd.api.types.is_numeric_dtype(s) or pd.api.types.is_bool_dtype(s)
        vals = s.dropna(); unique = int(vals.nunique())
        typ = 'binaria' if numeric and len(vals) and set(vals.unique()) <= {0, 1, False, True} else ('numérica' if numeric else 'categórica/texto')
        source = block; raw = ''; doc = ''; unit = ''; desc = ''; family = block
        if block == 'Maestro':
            meta = fd.loc[name]; sensor = str(meta.sensor)
            source = {'S2':'Sentinel-2','PLANET':'Planet','LANDSAT':'Landsat','CLIMATE':'Clima','CHIRPS_OR_WORLDCLIM':'Clima','DEM_OR_SLOPE':'Topografía','CONTINUOUS_DEM':'Topografía'}[sensor]
            family = str(meta.feature_family); desc = str(meta.description)
            raw, doc = sources[source]; doc += '; ' + fd_path
        elif block == 'Externas':
            meta = ed.loc[name]; source = str(meta.family); raw = str(meta['file']); doc = ed_path
            unit = str(meta.unit); desc = str(meta.physical_interpretation)
            folder = {'Physiography':'fisiografia','Geology':'geologia','External hydrology':'hidrografia','Wetlands':'humedales','Localities':'localidades'}[source]
            docs = sorted(str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'data/externo'/folder).rglob('*') if p.suffix.lower() in {'.pdf','.txt','.xml'} and ('metadat' in str(p).lower() or p.suffix.lower()=='.pdf'))
            doc += '; ' + '; '.join(docs)
        else:
            raw, doc = sources[source]
        row = dict(variable=name, bloque=block, fuente=source, familia=family, tipo=typ, dtype=str(s.dtype), unidad_documentada=unit, descripcion_documentada=desc, tabla_procesada=path, archivo_o_directorio_origen=raw, documentos_y_diccionarios=doc)
        for suffix, sub in [('197',s),('138',s.loc[s.index.isin(train_ids)])]:
            v = sub.dropna(); row.update({f'n_{suffix}':len(sub),f'faltantes_{suffix}':int(sub.isna().sum()),f'unicos_{suffix}':int(v.nunique()),f'constante_{suffix}':bool(v.nunique()<=1)})
            if numeric:
                a = pd.to_numeric(v).astype(float); finite = a[np.isfinite(a)]
                for key, value in [('min',finite.min()),('q25',finite.quantile(.25)),('mediana',finite.median()),('q75',finite.quantile(.75)),('max',finite.max())]: row[f'{key}_{suffix}']=value
                row[f'no_finitos_{suffix}']=int((~np.isfinite(a)).sum())
        row['categorias_o_ejemplos'] = json.dumps([str(x) for x in vals.unique()[:12]],ensure_ascii=False) if typ=='categórica/texto' else ''
        rows.append(row)

m = pd.read_parquet(ROOT/master_path)
add(master_path,[c for c in m if c!='ID_POLIGONO'],'Maestro')
e = pd.read_parquet(ROOT/external_path)
add(external_path,[c for c in e if c in ed.index and ed.loc[c,'family']!='FIRA interpreted selection'],'Externas')
s = pd.read_parquet(ROOT/soil_path)
add(soil_path,[c for c in s if c.startswith('soil_')],'Suelo')
for filename in ['geology_attributes_197.parquet','geology_full_composition_197.parquet']:
    p = geo_root+filename; g = pd.read_parquet(ROOT/p)
    add(p,[c for c in g if c!='ID_POLIGONO'],'Geología 250k detallada')
inventory = pd.DataFrame(rows)
assert len(inventory)==1557, len(inventory)
assert inventory.variable.nunique()==1557
inventory.to_csv(OUT/'inventario_1557.csv',index=False,encoding='utf-8-sig')
summary = inventory.groupby('fuente',sort=False).agg(variables=('variable','size'),constantes_197=('constante_197','sum'),constantes_138=('constante_138','sum'),con_faltantes_197=('faltantes_197',lambda x:int((x>0).sum())),con_faltantes_138=('faltantes_138',lambda x:int((x>0).sum())))
types = pd.crosstab(inventory.fuente,inventory.tipo)
summary = summary.join(types).fillna(0).astype(int)
summary.to_csv(OUT/'resumen_fuentes.csv',encoding='utf-8-sig')
lines = ['# Inventario descriptivo de 1,557 variables','', 'Alcance: las cinco tablas del conteo previo; no todo archivo bruto ni todas las transformaciones experimentales del repositorio. Se excluyen ID, rendimiento y metadatos ajenos al conteo. Rangos observados, no límites físicos ni recomendaciones de selección. 197 incluye 59 parcelas sin rendimiento únicamente para descripción; no se ajustaron modelos ni se generaron predicciones. Los rangos de entrenamiento se proporcionan por separado sobre las 138 etiquetadas.','','| Fuente | ' + ' | '.join(summary.columns) + ' |\n|---|' + '---|' * len(summary.columns) + '\n' + '\n'.join('| '+str(i)+' | '+' | '.join(map(str,r))+' |' for i,r in summary.iterrows()),'', '## Lectura y procedencia','', 'El CSV completo contiene una fila por variable, tabla procesada, fuente, diccionarios/documentos, tipo, valores únicos, faltantes, mínimos, cuartiles y máximos. Las referencias a carpetas señalan el conjunto de origen, no una atribución individual certificada a un CSV. Los documentos listados son recursos de procedencia/documentación disponibles, no prueba de que cada definición aparezca en cada documento. Las unidades vacías no se infirieron del nombre.','', 'El código CHIRPS_OR_WORLDCLIM del diccionario maestro es genérico y antiguo: la precipitación procede de CHIRPS y la temperatura del paquete CHIRTS/ERA5 del proyecto. Historia y anomalías son transformaciones de las fuentes satelitales y climáticas, no fuentes físicas nuevas. Suelo aporta categorías y proporciones de unidades cartográficas; la fracción que menciona un grupo no es porcentaje químico ni composición interna de un suelo. Geología aparece con una extracción externa resumida y otra detallada; son representaciones de información relacionada.','', '## Documentos por fuente','']
for source, group in inventory.groupby('fuente',sort=False):
    lines += [f'### {source}', '', f'{len(group)} variables. Tablas: '+ '; '.join(group.tabla_procesada.unique()), '', 'Origen: '+ '; '.join(group.archivo_o_directorio_origen.unique()), '', 'Documentación: '+ '; '.join(group.documentos_y_diccionarios.unique()), '']
lines += ['## Ejemplos de rangos en entrenamiento','', '| Variable | Fuente | Mínimo | Mediana | Máximo | Faltantes |','|---|---|---:|---:|---:|---:|']
examples=['S2_ndvi_month_05','HIST_S2_ndvi_promedio_mean','HIST_S2_ndvi_promedio_std','TOPO_BASIC_elevation_mean','TOPO_BASIC_slope_mean','soil_unit_count','soil_entropy','soil_boundary_distance_m','geo250_boundary_distance_m']
for name in examples:
    matches=inventory.loc[inventory.variable.eq(name)]
    if matches.empty: continue
    r=matches.iloc[0]
    lines.append(f'| {name} | {r.fuente} | {r.min_138:.5g} | {r.mediana_138:.5g} | {r.max_138:.5g} | {r.faltantes_138} |')
(OUT/'informe.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(summary.to_string())
print(inventory.tipo.value_counts().to_string())
print(inventory.loc[inventory.variable.isin(examples),['variable','min_138','max_138']].to_string(index=False))
