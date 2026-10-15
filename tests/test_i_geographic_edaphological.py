"""Scientific invariants for Section I; synthetic and generated-artifact audits."""
import json
import numpy as np
import pandas as pd
import pytest
from src.family_1.i_geographic_edaphological import DATA,OUT,ID,TARGET,structure,variance_parts,pair_indices

def test_missing_coverage_is_not_redistributed_and_ties_are_deterministic():
    w=pd.DataFrame({'B':[.3,0.],'A':[.3,0.]},index=['p','q'])
    s=structure(w)
    assert s.iloc[0].soil_dominant_unit=='A'
    assert s.iloc[0].soil_unclassified_share==pytest.approx(.4)
    assert s.iloc[0].soil_entropy==pytest.approx(np.log(2))
    assert np.isnan(s.iloc[1].soil_entropy)
    assert s.iloc[1].soil_unclassified_share==1

def test_overlap_is_rejected():
    with pytest.raises(ValueError):structure(pd.DataFrame({'A':[.8],'B':[.4]}))

def test_variance_partition_identity_and_repeated_pairs():
    z=variance_parts([1,3,4,6],[1,1,2,2])
    assert z['ss_between']==9
    assert z['ss_within']==4
    assert z['ss_total']==z['ss_between']+z['ss_within']
    assert pair_indices(np.array([1,1,1,2])).tolist()==[[0,1],[0,2],[1,2]]

def test_generated_full_coverage_and_long_wide_alignment():
    w=pd.read_parquet(DATA/'soil_full_composition.parquet').set_index(ID)
    l=pd.read_parquet(DATA/'soil_intersections_long.parquet')
    actual=l.pivot_table(index=ID,columns='unidad_edafologica',values='porcentaje_parcela',aggfunc='sum',fill_value=0).reindex(index=w.index,columns=w.columns)
    assert len(w)==197 and w.index.is_unique
    assert np.allclose(w.sum(axis=1),1,atol=1e-6)
    assert np.allclose(w,actual)
    assert np.allclose(l.porcentaje_parcela,l.area_interseccion_m2/l.area_parcela_m2)
    assert pd.read_csv(OUT/'tables/49_boundary_aoi_edge_check.csv').artificial_edge_is_farther.all()

def test_generated_hidden_targets_and_profile_centering():
    d=pd.read_parquet(DATA/'integrated_diagnostic_197.parquet')
    assert d.climate_profile.nunique()==53
    assert d[TARGET].notna().sum()==138
    assert d.loc[d.CONJUNTO.eq('PREDICCION'),TARGET].isna().all()
    shares=[c for c in d if c.startswith('soil_unit_share__')]
    assert len(shares)==22
    assert np.allclose(d[shares].sum(axis=1),1,atol=1e-6)
    assert d.soil_share_key_not_found_in_E1402_text.between(-1e-9,1+1e-9).all()
    for c in ['altitude_m','slope_degrees']:
        assert np.allclose(d.groupby('climate_profile')[c+'_within_profile_all197'].mean(),0,atol=1e-9)

def test_generated_topn_and_association_semantics():
    w=pd.read_parquet(DATA/'soil_full_composition.parquet').set_index(ID)
    for p in DATA.glob('soil_topn_per_parcel_*.parquet'):
        t=pd.read_parquet(p);shares=[c for c in t if c.endswith('_share')]
        assert np.allclose(t[shares].sum(axis=1),1)
    a=pd.read_parquet(DATA/'soil_attributes.parquet').set_index(ID)
    legend=pd.read_csv(OUT/'tables/02_unit_legend_audit.csv').set_index('Clave_wrb')
    for code in ['PH','AN','LP']:
        c='soil_map_share_mentions_group_'+code
        if c in a:
            selected=[u for u in w if code in legend.loc[u,['Grupo1','Grupo2','Grupo3']].tolist()]
            assert np.allclose(a[c].reindex(w.index),w[selected].sum(axis=1))

def test_generated_pair_count_and_y_identity():
    p=pd.read_csv(OUT/'tables/35_identical_climate_pairs.csv')
    assert len(p)==2136
    y=pd.read_csv(OUT/'tables/31_y_variance_decomposition_138.csv').iloc[0]
    assert y.ss_total==pytest.approx(y.ss_between+y.ss_within)
    assert y.n==138
