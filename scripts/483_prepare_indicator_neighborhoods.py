"""Freeze reductions, three neighbor geometries and paired correction uses."""
from pathlib import Path
import sys,json,hashlib
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.indicator_neighborhoods import OUT,PREVIOUS,ENGINEERING,CALIBRATION,REDUCTIONS,TERRAIN,KGRID,CLUSTERS


def main():
    if (OUT/'frozen_design.json').exists():raise FileExistsError('Preserve neighborhood design')
    for n in ['cache','checkpoints','models','tables','audit','figures']:(OUT/n).mkdir(parents=True,exist_ok=True)
    t=pd.read_parquet(ROOT/'outputs/modeling/ct3_residual_conditional/v1/cache/train138.parquet');ids=t.ID_POLIGONO.tolist();x=pd.read_parquet(PREVIOUS/'cache/features_train138_target_free.parquet');assert x.ID_POLIGONO.tolist()==ids
    definitions=json.loads((ROOT/'outputs/modeling/physical_representation/v1/frozen_design.json').read_text())['atoms'];physical=pd.read_parquet(ROOT/'outputs/modeling/physical_representation/v1/cache/features138_target_free.parquet').set_index('ID_POLIGONO').loc[ids];columns=list(dict.fromkeys(TERRAIN+sum([definitions[n]['columns'] for n in ['soil_texture_phase','geologic_composition','geologic_distances']],[])))
    coords=pd.read_parquet(ROOT/'outputs/modeling/geoc_signal_research/v1/cache/features197_target_free.parquet').set_index('ID_POLIGONO').loc[ids,['base_centroid_lat','base_centroid_lon']]
    x=x.set_index('ID_POLIGONO').join(coords).join(physical[columns]).reset_index();assert len(x)==138 and not x.columns.duplicated().any();x.to_parquet(OUT/'cache/features_train138_target_free.parquet',index=False)
    recipes={}
    for base in ['CT3','J7']:
        for reduction in REDUCTIONS:recipes[base+'_GLOBAL_'+reduction]=dict(base=base,mode='GLOBAL',reduction=reduction)
        for mode in ['KNN','CLUSTER']:
            for geometry in ['GEO','PHYSICAL','SATELLITE']:
                for use in ['DIRECT','WEIGHT']:recipes[f'{base}_{mode}_{geometry}_{use}']=dict(base=base,mode=mode,geometry=geometry,use=use)
    protected=dict(json.loads((PREVIOUS/'frozen_design.json').read_text())['source_sha256'])
    files=[ROOT/'src/indicator_neighborhoods.py',Path(__file__),ROOT/'scripts/484_run_indicator_neighborhoods.py',ROOT/'scripts/485_evaluate_indicator_neighborhoods.py',ROOT/'tests/test_indicator_neighborhoods.py',ROOT/'documentation/indicator_neighborhoods_design.md',OUT/'cache/features_train138_target_free.parquet',PREVIOUS/'tables/predictions.parquet',ENGINEERING/'tables/predictions.parquet',ROOT/'outputs/modeling/physical_representation/v1/frozen_design.json',ROOT/'outputs/modeling/physical_representation/v1/cache/features138_target_free.parquet',ROOT/'outputs/modeling/geoc_signal_research/v1/cache/features197_target_free.parquet']+sorted((ENGINEERING/'checkpoints').glob('*.joblib'))+sorted((CALIBRATION/'checkpoints').glob('*.joblib'))
    for f in files:protected[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
    cfg=dict(status='frozen_before_training',exploratory=True,recipes=recipes,reductions=REDUCTIONS,definitions=definitions,terrain_columns=TERRAIN,k_grid=KGRID,cluster_grid=CLUSTERS,amplitudes=[0.,.25,.5],ridge_alpha=30.,local_shrinkage=20.,weight_shrinkage=20.,paired_selection='Same k/cluster count and strength chosen by direct-correction inner OOF RMSE, then shared between DIRECT and WEIGHT. Weight is a fixed alternate use, not separately retuned; zero direct amplitude also disables weight.',satellite_support='Three finite history/heterogeneity indicators required for reference membership. Unsupported query falls back to global R4/weight, never artificial neighbors due to median imputation.',outer_folds=65,workers=8,no_PRED=True,no_final138_fit=True,no_champion_change=True,source_sha256=protected)
    assert len(recipes)==34 and all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in protected.items());(OUT/'frozen_design.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8');print('Frozen34recipes;65folds;k=',KGRID,'clusters=',CLUSTERS,'frame=',x.shape)


if __name__=='__main__':main()
