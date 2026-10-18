import numpy as np
import pandas as pd
from src.learned_r3_weight import GateFeatures,R3

def test_support_excludes_identity_and_missing_query_is_not_imputed_neighbor():
    f=pd.DataFrame({c:np.arange(12,dtype=float) for c in R3});f['I_history_fapar_floor']=np.arange(12,dtype=float);f['ID_POLIGONO']=[str(i) for i in range(12)];m=GateFeatures({}).fit(f);q=f.iloc[[4]].copy();z=m.transform(q,np.array([4.]),np.array([.1]));assert z[0,3]>0 and z[0,-1]==1
    before=m.space.mean.copy();q.loc[:,R3]=np.nan;z=m.transform(q,np.array([4.]),np.array([.1]));assert np.isnan(z[0,3]) and np.isnan(z[0,4]) and z[0,-1]==0;np.testing.assert_array_equal(before,m.space.mean)
