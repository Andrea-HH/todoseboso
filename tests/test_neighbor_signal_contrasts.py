import numpy as np
from scipy.spatial.distance import cdist
from src.neighbor_signal_contrasts import NeighborContrasts,ContrastAdjustment


def test_neighbor_excludes_self_preserves_training_statistics_and_ties():
    rng=np.random.default_rng(12);signals=rng.normal(size=(40,3));core=np.zeros((40,4));geo=cdist(np.arange(40)[:,None],np.arange(40)[:,None]);fit=np.arange(30)
    m=NeighborContrasts('COMPACT',24).fit(signals,core,geo,fit);z,rows=m.transform([0,35],details=True)
    assert 0 not in rows[0]['neighbors'] and set(rows[1]['neighbors'])==set(fit)
    assert rows[0]['neighbor_count']==29 and np.isfinite(z).all()
    before=m.transform([0]);signals[35:]+=1e6;np.testing.assert_array_equal(before,m.transform([0]))


def test_geographic_reference_positions_and_zero_variability_are_safe():
    geo=cdist(np.arange(40)[:,None],np.arange(40)[:,None]);signals=np.ones((40,3));m=NeighborContrasts('GEO',24).fit(signals,np.ones((40,4)),geo,np.arange(30));z,rows=m.transform([35],details=True)
    assert set(rows[0]['neighbors']).issubset(set(range(30))) and len(rows[0]['neighbors'])==24
    np.testing.assert_array_equal(z,np.zeros((1,6)))


def test_adjustments_include_identity_bound_corrections_and_only_attenuate():
    rng=np.random.default_rng(8);z=rng.normal(size=(100,6));ct=np.full(100,3.);base=ct+z[:,0];y=base+np.where(z[:,1]<0,-4.,4.)
    for kind in ['RESIDUAL','ATTENUATE']:
        null=ContrastAdjustment(kind,amplitude=0).fit(z,y,base,ct);np.testing.assert_array_equal(null.predict(z,base,ct),base)
        model=ContrastAdjustment(kind,depth=2,leaf=15,amplitude=1).fit(z,y,base,ct);p=model.predict(z,base,ct)
        if kind=='RESIDUAL':assert np.max(abs(p-base))<=.5+1e-12
        else:assert np.all(p>=np.minimum(ct,base)-1e-12) and np.all(p<=np.maximum(ct,base)+1e-12)


def test_nested_j7_ignores_external_labels_and_records_deep_support(tmp_path,monkeypatch):
    import pandas as pd
    import src.neighbor_signal_contrasts as module
    from src.ct3_residual_conditional.models import CORE
    rng=np.random.default_rng(44);n=18;raw=rng.normal(size=(n,7));features=pd.DataFrame(raw,columns=list('abcdefg'));frame=pd.DataFrame(raw[:,:4],columns=CORE);frame['ID_POLIGONO']=[str(i) for i in range(n)];frame['soil_texture']='loam';frame['soil_phase']='none';frame['geo_share']=rng.uniform(size=n);frame['geo_distance']=rng.uniform(1,10,size=n)
    role=pd.concat([frame,features],axis=1);ids=frame.ID_POLIGONO.tolist();groups=pd.DataFrame({'municipality':np.repeat([0,1,2],6)},index=ids);y=3+raw[:,0];defs={'soil_texture_phase':dict(columns=['soil_texture','soil_phase'],summary=['soil_texture','soil_phase'],composition=False),'geologic_composition':dict(columns=['geo_share'],summary=['geo_share'],composition=True),'geologic_distances':dict(columns=['geo_distance'],summary=['geo_distance'],composition=False)}
    a=dict(a=dict(train=frame,train_global=np.arange(n),distance=cdist(raw[:,:2],raw[:,:2])),y=y,features197=features,role_frame=role,physical_definitions=defs,variants={'DROP_JOINT':dict(type='small',columns=list(features),mode='raw',correction_columns=[],correction_atoms=[])},static={});monkeypatch.setattr(module,'OLD',tmp_path/'no_original_cache');fit=np.arange(12);held=np.arange(12,18)
    f=module.NestedJ7(a,'municipality',groups,tmp_path/'first',tmp_path/'empty_reference');p=f.predict(f.fit(fit),held)[0]
    changed={**a,'y':y.copy()};changed['y'][held]+=10000;g=module.NestedJ7(changed,'municipality',groups,tmp_path/'second',tmp_path/'empty_reference');np.testing.assert_array_equal(p,g.predict(g.fit(fit),held)[0]);assert any(r['kind']=='ct3_fixed_single_group' for r in f.logs)
    assert all(not set(row['train'])&(set(row['held'])|set(held)) for row in f.ledger+f.role.ledger)
    constant=f.ct3(np.array([0]));np.testing.assert_array_equal(constant.predict(frame.iloc[held]),np.repeat(y[0],len(held)))
    assert any(r['kind']=='ct3_mean_zero_features' for r in f.logs)
    sparse=f.ct3(np.array([0,6]));assert np.isfinite(sparse.predict(frame.iloc[held])).all()
    assert any(r['kind']=='ct3_fixed_unsupported_cv' for r in f.logs)
