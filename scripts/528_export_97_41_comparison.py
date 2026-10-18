"""Publish existing97/41 aggregate metrics, without fitting or private rows."""
from pathlib import Path
import csv
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/comparison_97_41/v1'


def main():
    source=ROOT/'outputs/modeling/four_expert_combinations/v1/tables/metrics.csv'
    with source.open(encoding='utf-8',newline='') as stream:
        rows=[r for r in csv.DictReader(stream) if r['protocol']=='fresh_97_41']
    assert len(rows)==10 and len({r['experiment'] for r in rows})==10
    assert all(float(r['n'])==41 for r in rows)
    fields=['experiment','protocol','n','rmse','r2','mae','bias']
    rows=[{c:r[c] for c in fields} for r in rows]
    plan=json.loads((ROOT/'configs/validation/original65_plus_fresh16.json').read_text(encoding='utf-8'))
    fresh=[f for f in plan['folds'] if f['protocol']=='fresh_97_41']
    assert len(fresh)==16 and all(len(f['train_positions'])==97 and len(f['validation_positions'])==41 for f in fresh)
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/'metrics.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    text='# Banco adicional97/41 — comparación separada\n\n'
    text+='**16 particiones:97 parcelas para entrenamiento y41 para evaluación en cada una**, reutilizando las mismas138 parcelas conocidas. RMSE, R², MAE y sesgo se calculan sobre las41 predicciones retenidas de cada partición y luego se promedian entre las16. No se concatenan como656 parcelas independientes ni se mezclan con las OOF completas de los65 folds originales.\n\n'
    text+='Simula un conjunto de rendimientos faltantes con entrenamiento territorialmente representado. Es evidencia exploratoria complementaria, no validación territorial por municipio/bloque, muestra independiente ni error conocido de las59 PRED. Los mismos41 identificadores no tienen que repetirse entre particiones.\n\n'
    text+='| Modelo | RMSE t/ha ↓ | R² ↑ | MAE t/ha ↓ | Sesgo predicho−observado |\n|---|---|---|---|---|\n'
    order=['CT3','L40','Reference26','Compact14','B1','B2','B3','B4','B5','B6']
    for name in order:
        r=next(r for r in rows if r['experiment']==name)
        text+=f"| {name} | {float(r['rmse']):.4f} | {float(r['r2']):.4f} | {float(r['mae']):.4f} | {float(r['bias']):+.4f} |\n"
    text+='\nReference26 y Compact14 son los champions actuales; C-T3 es control y L40 referencia externa. B1–B6 son sensibilidades, no champions adicionales. Las diferencias pequeñas no demuestran superioridad estadística. Este banco no se confunde con los checkpoints originales de GeoC, aunque utilicen también entrenamiento97/evaluación41.\n\n'
    text+='[Fichas](../../../documentation/models/README.md) · [Diseño de mezclas](../../../documentation/four_expert_combinations_design.md) · [Particiones posicionales](../../../configs/validation/original65_plus_fresh16.json) · [CSV agregado](metrics.csv). La tabla omite modelos sin evaluación compatible disponible, como Champion histórico y EQUAL3 en este archivo; no se les atribuyen resultados por analogía.\n'
    (OUT/'README.md').write_text(text,encoding='utf-8',newline='\n')
    (OUT/'provenance.json').write_text(json.dumps(dict(source=source.relative_to(ROOT).as_posix(),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        rows=len(rows),partitions=16,training_per_partition=97,evaluation_per_partition=41,new_fits=0,
        aggregation='mean of16 partition metrics; no pooled656-row score',private_rows_published=False),indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Published existing97/41 aggregates for10 models; no new training.')


if __name__=='__main__':main()
