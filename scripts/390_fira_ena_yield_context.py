"""Descriptive external-yield context; no model fitting or PRED inference."""
from pathlib import Path
import hashlib,json
import requests
import pandas as pd
import numpy as np
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/research/fira_ena_yield_context/v1'
if (OUT/'provenance.json').exists(): raise FileExistsError('Preserve completed versions')
(OUT/'sources').mkdir(parents=True,exist_ok=True)
url='https://www.inegi.org.mx/contenidos/programas/ena/2025/tabulados/ena2025_agr01.xlsx'
r=requests.get(url,timeout=90);r.raise_for_status()
x=OUT/'sources/ena2025_agr01.xlsx';x.write_bytes(r.content)
sheet=pd.read_excel(x,sheet_name='ena2025_agr01',header=None)
precision=pd.read_excel(x,sheet_name='ena2025_ipagr01',header=None)
ena=[]
for state,code in [('Nacional','Estados Unidos Mexicanos'),('Hidalgo','13 Hgo.'),('Tlaxcala','29 Tlax.')]:
    matches=sheet[sheet[1].astype(str).str.strip().eq('Cebada grano')]
    if state=='Nacional': row=matches.iloc[0]
    else: row=matches[matches[0].astype(str).str.strip().eq(code)].iloc[0]
    p=precision[precision[1].astype(str).str.strip().eq('Cebada grano')]
    pr=p.iloc[0] if state=='Nacional' else p[p[0].astype(str).str.strip().eq(code)].iloc[0]
    ena.append(dict(Estado=state,sown_ha=float(row[3]),harvested_ha=float(row[4]),production_t=float(row[5]),yield_t_ha=float(row[5]/row[4]),harvested_area_cv_pct=float(pr[12]),production_cv_pct=float(pr[17])))
ena=pd.DataFrame(ena);ena.to_csv(OUT/'ena2025_barley.csv',index=False)
train=pd.read_parquet(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet')
train=train.rename(columns={'RENDIMIENTO_T_HA':'Y'})
original=pd.read_csv(ROOT/'data/original/01_tablas_maestras/ID_area_rendimiento_70_30_Reto_AgroCebada.csv')
t=train.merge(original[['ID_POLIGONO','AREA_HA','RENDIMIENTO_T_HA']],on='ID_POLIGONO',validate='one_to_one')
assert len(t)==138 and np.allclose(t.Y,t.RENDIMIENTO_T_HA) and (t.AREA_HA>0).all()
rows=[]
for state,g in t.groupby('Estado'):
    rows.append(dict(Estado=state,n=len(g),mean_t_ha=g.Y.mean(),median_t_ha=g.Y.median(),min_t_ha=g.Y.min(),max_t_ha=g.Y.max(),parcel_area_ha=g.AREA_HA.sum(),area_weighted_mean_t_ha=np.average(g.Y,weights=g.AREA_HA)))
ours=pd.DataFrame(rows);ours.to_csv(OUT/'parcel_state_summary.csv',index=False)
compare=ours.merge(ena,on='Estado',how='left');compare['difference_mean_minus_ena']=compare.mean_t_ha-compare.yield_t_ha
compare['relative_difference_pct']=100*(compare.mean_t_ha/compare.yield_t_ha-1)
compare.to_csv(OUT/'parcel_vs_ena.csv',index=False)
spec=[('hidalgo22agenciashidalgo.pdf','Hidalgo','CEBADA ALTA PRODUCTIVIDAD','Agencias Hidalgo',3.5,2.04),('puebla22altorendimiento.pdf','Puebla','CEBADA ALTA PRODUCTIVIDAD','Sierra Norte Puebla',5.5,3.31),('puebla22cebadasinclasificacion.pdf','Puebla','CEBADA','Agencia Teziutlan',3.,3.31),('tlaxacla22altaprod.pdf','Tlaxcala','CEBADA','Agencias De Tlaxcala',4.,2.56)]
records=[];hashes={str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest()}
for name,state,label,zone,probable,siap in spec:
    path=ROOT/'docs/resources/rendimientoshistoricosfira'/name
    with pymupdf.open(path) as pdf:
        text='\n'.join(f'PAGE {i+1}\n{p.get_text()}' for i,p in enumerate(pdf))
    (OUT/'sources'/f'{path.stem}.txt').write_text(text,encoding='utf-8')
    hashes[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
    records.append(dict(file=name,Estado=state,crop_label=label,zone=zone,cycle='PV2022',technology='Temporal-mejorada-fertilizada',probable_yield_2022_t_ha=probable,siap_state_yield_2020_t_ha=siap))
pd.DataFrame(records).to_csv(OUT/'fira_reference_inventory.csv',index=False)
(OUT/'provenance.json').write_text(json.dumps(dict(url=url,sha256=hashes,train_n=138,model_fits=0,pred_inference=0,notes=['Puebla barley absent from consulted ENA table, not zero.','ENA yield derived as production / harvested area.','Area weighting uses parcel area, not verified harvested area.','Component CVs are not a CV or confidence interval for the yield ratio.','FIRA inventory manually transcribed from supplied PDFs; extracted texts retained.']),indent=2),encoding='utf-8')
print(compare.to_string(index=False))
print(ena.to_string(index=False))
