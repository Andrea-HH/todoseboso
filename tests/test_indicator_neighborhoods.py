import numpy as np
import pandas as pd
from src.indicator_neighborhoods import R4,SATELLITE,NeighborhoodSpace,LocalCorrection,ReducedCorrection
from src.temporal_indicator_weights import INDICATORS


def frame(n=20):
    rng=np.random.default_rng(62);f=pd.DataFrame(rng.normal(size=(n,len(INDICATORS))),columns=INDICATORS);f['ID_POLIGONO']=[f'P{i}' for i in range(n)];f['base_centroid_lat']=20+np.arange(n)*.001;f['base_centroid_lon']=-98.;return f


def test_satellite_ties_and_missing_history_fallback():
    f=frame();f.loc[:,SATELLITE]=1.;f.loc[0,SATELLITE]=np.nan;s=NeighborhoodSpace('SATELLITE',{}).fit(f);q=f.iloc[[1]].copy();q.ID_POLIGONO='NEW';ids,w=s.memberships(q,'KNN',8)[0];assert len(ids)==19 and 0 not in ids;np.testing.assert_allclose(w.sum(),1)
    q.loc[:,SATELLITE]=np.nan;assert len(s.memberships(q,'KNN',8)[0][0])==0


def test_geographic_neighbors_exclude_self_and_training_transform_is_frozen():
    f=frame();s=NeighborhoodSpace('GEO',{}).fit(f);ids,_=s.memberships(f.iloc[[4]],'KNN',8)[0];assert 4 not in ids and len(ids)>=8;lat=s.lat;s.memberships(f.iloc[[5]],'KNN',72);assert s.lat==lat


def test_reductions_and_local_weight_are_bounded():
    f=frame(30);q=frame(3);q.ID_POLIGONO=['Q1','Q2','Q3'];r=np.linspace(-1,1,30)
    for reduction in ['R9','R4','R3','R2','PCA2']:
        m=ReducedCorrection(reduction).fit(f,r);assert max(abs(m.delta(q)))<=.25+1e-12
    m=LocalCorrection('GEO','KNN',8,{}).fit(f,r,np.linspace(-.2,.2,30));d,records=m.predict(q,'WEIGHT',.5,True);assert max(abs(d))<=.25+1e-12 and all(0<=v['weight']<=1 for v in records)
    np.testing.assert_array_equal(m.predict(q,'DIRECT',0),np.zeros(3))
