"""Read-only cross-repository identity and 59-prediction agreement audit."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
GEO=ROOT.parent/'fira/GeoC'
OUT=ROOT/'outputs/research/geoc_bridge_audit/v1'

if __name__=='__main__':
    if OUT.exists():raise FileExistsError('Preserve audit')
    OUT.mkdir(parents=True)
    paths=[ROOT/'data/original/01_tablas_maestras/ID_area_rendimiento_70_30_Reto_AgroCebada.csv',GEO/'data/source/tabular/ID_area_rendimiento_70_30_Reto_AgroCebada.csv',ROOT/'outputs/modeling/winner_predictions/v1/tables/predictions59.csv',GEO/'reports/checkpoint_05/final_predictions.csv',GEO/'reports/checkpoint_07/shared/checkpoint08_comparison_summary.csv',GEO/'src/geocebada/evaluation/checkpoint04d1.py',GEO/'src/geocebada/evaluation/checkpoint08_local.py',GEO/'reports/checkpoint_04a/embedding_manifest.json']
    a=pd.read_csv(paths[0]);b=pd.read_csv(paths[1]);j=a.merge(b,on='ID_POLIGONO',suffixes=('_ours','_geoc'),validate='one_to_one')
    assert len(j)==197 and len(a)==len(b)==197
    np.testing.assert_allclose(j.RENDIMIENTO_T_HA_ours,j.RENDIMIENTO_T_HA_geoc,equal_nan=True)
    np.testing.assert_allclose(j.AREA_HA_ours,j.AREA_HA_geoc)
    assert (j.CONJUNTO_ours==j.CONJUNTO_geoc).all()
    z=pd.read_csv(paths[2]).merge(pd.read_csv(paths[3]).rename(columns={'RENDIMIENTO_T_HA':'Local04D_t_ha'}),on='ID_POLIGONO',validate='one_to_one');assert len(z)==59
    z.to_csv(OUT/'predictions59_aligned_descriptive.csv',index=False)
    rows=[]
    for name in ['CT3','Champion','EQUAL3']:
        e=z[name+'_t_ha']-z.Local04D_t_ha
        rows.append(dict(model=name,correlation_with_Local04D=z[name+'_t_ha'].corr(z.Local04D_t_ha),mean_prediction_difference=e.mean(),mean_absolute_prediction_difference=abs(e).mean(),max_absolute_prediction_difference=abs(e).max()))
    pd.DataFrame(rows).to_csv(OUT/'prediction_agreement_not_error.csv',index=False)
    audit=dict(status='read_only_audit_complete',same_197_IDs=True,same_138_labels=True,same_59_missing_targets=True,same_areas_and_split=True,new_model_fits=0,OOF_alignment_not_yet_available=True,warning='59-prediction agreement is not residual correlation or predictive error; no blended final predictions generated.',source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    (OUT/'manifest.json').write_text(json.dumps(audit,indent=2),encoding='utf-8');print(pd.DataFrame(rows).to_string(index=False))
