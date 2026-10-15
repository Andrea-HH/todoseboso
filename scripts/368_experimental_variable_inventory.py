"""Inventory existing experimental representations without fitting models."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/research/experimental_variable_inventory/v1'
OUT.mkdir(parents=True,exist_ok=True)
baseline=pd.read_csv(ROOT/'outputs/research/variable_inventory/v1/inventario_1557.csv')
known=set(baseline.variable)
label=pd.read_csv(ROOT/'data/original/01_tablas_maestras/ID_area_rendimiento_70_30_Reto_AgroCebada.csv')
train=set(label.loc[label.RENDIMIENTO_T_HA.notna(),'ID_POLIGONO'])
suffixes=['rainfall_yield/v1/rainfall_features.parquet','g_temperature_signal/v1/climate_candidates_197.parquet','h_joint_climate_signal/v1/joint_monthly_197.parquet','j_incremental_geographic_edaphological_yield/v1/j_features_197_target_free.parquet','k_standalone_residual_geographic_edaphological/v1/k_features_197_target_free.parquet','l_multiblock_representation/v1/l_features_197_target_free.parquet','m_historical_multisensor/v1/m_features_197_target_free.parquet']
paths=[ROOT/'data/processed/family_1'/s for s in suffixes]
paths+=sorted((ROOT/'data/processed/family_4').rglob('*target_free.parquet'))
paths += [ROOT/'outputs/modeling/family_7/expansion/v1/cache/train138_exact_features.parquet']
dicts={}
for p in sorted((ROOT/'data/processed/family_1').rglob('*dictionary.csv')):
    d=pd.read_csv(p)
    key=next((k for k in ['feature_name','feature','variable'] if k in d),None)
    if key:
        for _,r in d.iterrows(): dicts.setdefault(str(r[key]),[]).append((p,r))
for p in [ROOT/'outputs/research/family_4/territorial_intraprofile_program/v1/stage_c/audit/feature_dictionary.csv',ROOT/'outputs/research/family_8/residual_design/v1/audit/F5_variable_dictionary.csv']:
    d=pd.read_csv(p);key=next(k for k in ['feature','column'] if k in d)
    for _,r in d.iterrows(): dicts.setdefault(str(r[key]),[]).append((p,r))
excluded={'ID_POLIGONO','CONJUNTO','RENDIMIENTO_T_HA','Estado','Municipio','Cultivo','AREA_HA','Área_ha','climate_profile','longitude','latitude','locality_CVEGEO','locality_name','locality_municipality','locality_state','locality_source','locality_method','locality_confidence','previous_distance_method','previous_nearest_name_agrees','soil_all_units_summary','EXT_LOC_nearest_name'}
found={}; occurrences=[]; audited=[]
for p in paths:
    d=pd.read_parquet(p)
    assert len(d) in [138,197] and not d.ID_POLIGONO.duplicated().any()
    audited.append(str(p.relative_to(ROOT)).replace('\\','/'))
    for c in d:
        if c in known or c in excluded or c.startswith('Unnamed'):continue
        s=d.set_index('ID_POLIGONO')[c]
        occurrences.append(dict(variable=c,tabla=audited[-1],n=len(d)))
        if c not in found: found[c]=[s,[audited[-1]]]
        else:
            old=found[c][0]; common=old.index.intersection(s.index)
            a=pd.to_numeric(old.loc[common],errors='coerce');b=pd.to_numeric(s.loc[common],errors='coerce')
            compatible=np.allclose(a,b,equal_nan=True,rtol=1e-10,atol=1e-10) if pd.api.types.is_numeric_dtype(s) else old.loc[common].fillna('').equals(s.loc[common].fillna(''))
            if not compatible: raise ValueError(f'Conflicting representation {c}: {p}')
            found[c][1].append(audited[-1])
            if len(s)>len(old):found[c][0]=s

def group(c):
    if c.startswith('compact_'):return 'Lluvia compacta'
    if c.startswith('rain'):return 'Lluvia: mensual, temporal e histórica'
    if c.startswith(('tmin','tmax','tmean','dtr','temp')):return 'Temperatura: mensual y derivados'
    if c.startswith(('S2','HIST_S2','ANOM_S2')):return 'Sentinel-2: ventanas y derivados'
    if c.startswith(('HIST_','HISTORY_','ANOM_','LS','LANDSAT','PLANET')):return 'Historia/anomalías multisensor'
    if c.startswith(('soil','s1_','s2_','s3_','s4_')):return 'Suelo: representaciones alternativas'
    if c.startswith(('altitude','slope','TOPO')):return 'Topografía/alias'
    return 'Otros derivados o diagnóstico'

rows=[]
master=pd.read_parquet(ROOT/'data/processed/family_1/features/family1_features_all.parquet').set_index('ID_POLIGONO')
master_matrices={}
for c,(s,tables) in found.items():
    numeric=pd.api.types.is_numeric_dtype(s) or pd.api.types.is_bool_dtype(s)
    vals=s.dropna();typ='binaria' if numeric and len(vals) and set(vals.unique())<={0,1,True,False} else ('numérica' if numeric else 'categórica/texto')
    metadata=dicts.get(c,[])
    descriptions=[];units=[];sources=[]
    for p,r in metadata:
        descriptions += [str(r[k]) for k in ['definition','formula','description','transformation'] if k in r and pd.notna(r[k])]
        units += [str(r[k]) for k in ['units','unit'] if k in r and pd.notna(r[k])]
        sources += [str(r[k]) for k in ['source','period','window','experiments'] if k in r and pd.notna(r[k])]
    aliases=[]
    if numeric:
        common=s.index.intersection(master.index);a=s.loc[common].to_numpy(float)
        key=tuple(common)
        if key not in master_matrices: master_matrices[key]=master.loc[common].to_numpy(float)
        b=master_matrices[key]
        equal=np.all(np.isclose(a[:,None],b,rtol=1e-10,atol=1e-10,equal_nan=True),axis=0)
        if len(common)>=138: aliases=list(master.columns[equal])
    row=dict(variable=c,grupo=group(c),tipo=typ,tablas='; '.join(tables),documentos_diccionarios='; '.join(dict.fromkeys(str(p.relative_to(ROOT)).replace('\\','/') for p,_ in metadata)),definicion_documentada='; '.join(dict.fromkeys(descriptions)),unidad_documentada='; '.join(dict.fromkeys(units)),fuente_periodo_uso_documentado='; '.join(dict.fromkeys(sources)),equivalencia_numerica_con_maestro='; '.join(aliases),nota_equivalencia='Igualdad observada; no certifica identidad de definición' if aliases else '')
    for tag,sub in [('disponibles',s),('138',s.loc[s.index.isin(train)])]:
        v=sub.dropna();row.update({f'n_{tag}':len(sub),f'faltantes_{tag}':int(sub.isna().sum()),f'unicos_{tag}':int(v.nunique())})
        if numeric:
            v=pd.to_numeric(v).astype(float);v=v[np.isfinite(v)]
            row.update({f'min_{tag}':v.min(),f'mediana_{tag}':v.median(),f'max_{tag}':v.max()})
    rows.append(row)
inv=pd.DataFrame(rows).sort_values(['grupo','variable'])
inv.to_csv(OUT/'variables_adicionales.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(occurrences).to_csv(OUT/'apariciones_por_tabla.csv',index=False,encoding='utf-8-sig')
summary=inv.groupby('grupo').size()
lines=['# Inventario separado de variables experimentales','',f'{len(inv)} nombres adicionales al inventario de 1,557 en {len(paths)} matrices experimentales canónicas auditadas. Son nombres/representaciones, no fuentes independientes ni variables necesariamente utilizadas en modelos. No es un censo de toda transformación interna del repositorio.','', '| Grupo | Nombres adicionales |','|---|---:|']
lines += [f'| {g} | {n} |' for g,n in summary.items()]
lines += ['', '## Alcance','', 'Se revisaron matrices canónicas por parcela de lluvia, G, H, J, K, L, M, Familia 4 y etapas A/B/C, más la matriz exacta F7. Se excluyeron ID, target, estado, municipio, coordenadas y metadatos de identificación. Se validó consistencia de valores para nombres repetidos. La columna de equivalencia identifica igualdad numérica con el maestro en las parcelas disponibles, no igualdad semántica. No se suman estos nombres como información independiente.','', 'Los registros sin definición documentada requieren consultar la implementación; no se inventaron unidades. Rangos del entrenamiento se separan de los de todas las parcelas disponibles. No hubo ajuste ni predicciones PRED.','', '## Transformaciones dependientes del entrenamiento','', 'No se cuentan como columnas fijas: componentes PCA/PLS/PCR, centrado y escalado, splines, interacciones estandarizadas, predicciones de base/expected_y, residuos cross-fitted e interceptos jerárquicos. Sus valores o definición dependen del fold; no deben tratarse como covariables brutas disponibles. Los scores PCA descriptivos de 197 parcelas son artefactos exploratorios, no los componentes ajustados dentro de validación.','', 'Familia 4 documenta interacciones pendiente×lluvia, NDVI×lluvia, NDVI×predicción de base y pendiente×suelo, además de splines de pendiente. Véase src/family_4/conditional_response.py. Los ajustes de escala/kernel y objetivos centrados de B/C/F5 son transformaciones del modelo, no fuentes nuevas.','', '## Tablas auditadas','']
lines += [f'- {p}' for p in audited]
lines += ['', '## Núcleo C-T3','', 'compact_precip_total = suma abril–octubre; compact_early_fraction = suma abril–junio/(total+1e-6); compact_concentration_hhi = suma de cuadrados de fracciones mensuales; S2_ndvi_month_05 = media de observaciones válidas de mayo de 2025. Las fórmulas compactas corresponden a src/family_4/stage_c_models.py y su diseño congelado.','']
(OUT/'informe.md').write_text('\n'.join(lines),encoding='utf-8')
print(summary.to_string());print('TOTAL',len(inv));print(inv.loc[inv.variable.str.startswith('compact_')|inv.variable.eq('S2_ndvi_month_05'),['variable','min_138','max_138','equivalencia_numerica_con_maestro']].to_string(index=False))
