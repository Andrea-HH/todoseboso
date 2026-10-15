import json
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from src.family_4 import territorial_stage_a as a

def test_source_identity_and_worldfile_half_pixel():
    metadata=json.loads((a.OUT/'audit/source_metadata.json').read_text())
    assert metadata['source_findings']['A1'].startswith('No historical50k')
    assert metadata['cartageologicadechignahuapan.pdf']['geospatial_objects']==[]
    coeff=np.loadtxt(a.ROOT/'data/externo/chignahuapan/e14b13.tfw')
    with rasterio.open(a.ROOT/'data/externo/chignahuapan/e14b13.tif') as src:
        assert src.crs is None and str(src.colorinterp[0]).endswith('2')
        np.testing.assert_allclose([src.transform.a,src.transform.e],[coeff[0],coeff[3]],atol=1e-12)
        np.testing.assert_allclose([src.transform.c+src.transform.a/2,src.transform.f+src.transform.e/2],coeff[4:6],atol=1e-9)

def test_geometry_and_full_polygon_coverage():
    parcels=gpd.read_file(a.PROC/'parcels_projected.gpkg');frames=gpd.read_file(a.PROC/'verified_sheet_frames.gpkg')
    assert parcels.crs.to_epsg()==6372 and parcels.geometry.is_valid.all() and (parcels.area>0).all()
    cov=pd.read_csv(a.OUT/'tables/source_coverage_197.csv')
    assert len(cov)==197*3 and cov.coverage_share.between(-1e-8,1+1e-6).all()
    for row in frames.itertuples():
        shares=parcels.geometry.intersection(row.geometry).area/parcels.area
        ref=cov[cov.source.eq(row.source)].set_index(a.ID).loc[parcels[a.ID]]
        np.testing.assert_allclose(shares,ref.coverage_share,atol=1e-10)
    assert (cov[cov.source.eq('topographic1996_sheet')].classification.eq('full')).sum()==118
    ops=json.loads((a.OUT/'audit/crs_operations.json').read_text())
    assert ops['ballpark_allowed'] is False and all(x['accuracy_m']>=0 for x in ops['operations'])

def test_area_conservation_and_complete_geology_representation():
    long=pd.read_parquet(a.PROC/'geology_intersections_full.parquet')
    np.testing.assert_allclose(long.share,long.intersection_m2/long.parcel_area_m2,atol=1e-12)
    comp=pd.read_parquet(a.PROC/'geology_full_composition_197.parquet').set_index(a.ID)
    assert len(comp)==197 and (comp.to_numpy()>=-1e-8).all()
    np.testing.assert_allclose(comp.sum(axis=1),1,atol=1e-5)
    for unit in long.unit_key.unique():
        expected=long[long.unit_key.eq(unit)].groupby(a.ID).share.sum().reindex(comp.index,fill_value=0)
        np.testing.assert_allclose(expected,comp['geo250_share__'+unit],atol=1e-12)

def test_no_target_in_matrix_and_pair_classification_reconstructs_from_x():
    features=pd.read_parquet(a.PROC/'territorial_candidate_matrix_197_target_free.parquet').set_index(a.ID)
    assert a.TARGET not in features and features.index.is_unique and len(features)==197
    comp=pd.read_parquet(a.PROC/'geology_full_composition_197.parquet').set_index(a.ID)
    pairs=pd.read_csv(a.OUT/'tables/dominant_x_only_pair_inventory.csv')
    assert len(pairs)==934 and not pairs.duplicated(['id_a','id_b']).any()
    assert not any(c in pairs for c in ['observed_difference','pair_error','y_true'])
    for row in pairs.itertuples():
        distance=float(abs(comp.loc[row.id_a]-comp.loc[row.id_b]).sum()/2)
        np.testing.assert_allclose(distance,row.geo250_tv,atol=1e-12)
        assert row.geology_different==(distance>a.CONFIG['geology_different_tv'])
        assert row.ndvi_similar==(abs(features.loc[row.id_a,a.e.f.NDVI]-features.loc[row.id_b,a.e.f.NDVI])<=.03)

def test_pair_errors_use_same_fold_and_baseline_labels():
    pairs=pd.read_parquet(a.OUT/'tables/dominant_same_model_pairs.parquet')
    baseline=pd.read_parquet(a.e.OUT/'tables/oof_predictions.parquet');baseline=baseline[baseline.experiment.eq('F4-E1')]
    for field,suffix in [('id_a','a'),('id_b','b')]:
        z=baseline.rename(columns={a.ID:field,'y_pred':'pred_'+suffix,'y_true':'true_'+suffix})
        pairs=pairs.merge(z[[field,'protocol','repeat','fold','pred_'+suffix,'true_'+suffix]],on=[field,'protocol','repeat','fold'],validate='many_to_one')
    np.testing.assert_allclose(pairs.pair_error,(pairs.true_a-pairs.true_b)-(pairs.pred_a-pairs.pred_b),atol=1e-12)

def test_previous_program_results_and_source_files_unchanged():
    for out in [a.e.OUT,a.e.f.OUT]:
        manifest=json.loads((out/'manifest.json').read_text())
        assert all(a.sha(a.ROOT/path)==digest for path,digest in manifest['artifacts'].items())
    inventory=pd.read_csv(a.OUT/'audit/source_inventory.csv')
    assert all(a.sha(a.ROOT/path)==digest for path,digest in zip(inventory.path,inventory.sha256))
