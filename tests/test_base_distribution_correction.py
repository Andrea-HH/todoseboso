import numpy as np
import pandas as pd
from src.base_distribution_correction import DistributionWeight,R3

def frame(n=10):
    f=pd.DataFrame({c:np.arange(n,dtype=float) for c in R3});f['ID_POLIGONO']=[str(i) for i in range(n)];f['base_centroid_lat']=20+np.arange(n)*.001;f['base_centroid_lon']=-98.;return f

def test_support_and_novelty_complement_and_exclude_self():
    f=frame();m=DistributionWeight('GEO',8,{}).fit(f);s,rows=m.weights(f.iloc[[4]],'SUPPORT',True);n=m.weights(f.iloc[[4]],'NOVELTY');assert rows[0]['support'] and '4' not in rows[0]['neighbor_ids'];np.testing.assert_allclose(s+n,1);assert 0<=s[0]<=1

def test_outlier_loses_support_weight_and_missing_disables_both():
    f=frame();m=DistributionWeight('GEO',8,{}).fit(f);q=f.iloc[[4]].copy();q.ID_POLIGONO='NEW';q.loc[:,R3]=1000.;assert m.weights(q,'SUPPORT')[0]<1e-5 and m.weights(q,'NOVELTY')[0]>.99;q.loc[:,R3]=np.nan;assert m.weights(q,'SUPPORT')[0]==0 and m.weights(q,'NOVELTY')[0]==0
