"""Une bloques no supervisados y elimina sólo constantes/duplicados exactos."""
from pathlib import Path
import sys, hashlib
import numpy as np, pandas as pd
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
from family_1.feature_pipeline import OUT,AUD,ID,parcels,combine_dictionary

names=['sentinel_features_core.parquet','sentinel_features_extended.parquet','landsat_features.parquet','planet_features.parquet','climate_features.parquet','history_features.parquet','anomaly_features.parquet','topography_basic_features.parquet','topography_advanced_features.parquet']
t=parcels(); eliminations=[]; seen={}
for name in names:
    b=pd.read_parquet(OUT/name); keep=[ID]
    for c in b.columns[1:]:
        s=b[c]
        if s.notna().sum()==0 or s.nunique(dropna=True)<=1:
            eliminations.append({'feature_name':c,'reason':'constant_or_all_missing','duplicate_of':None}); continue
        h=hashlib.sha256(pd.util.hash_pandas_object(s, index=False).values.tobytes()).hexdigest()
        duplicate=seen.get(h)
        if duplicate is not None and s.reset_index(drop=True).equals(duplicate[1]):
            eliminations.append({'feature_name':c,'reason':'exact_duplicate','duplicate_of':duplicate[0]}); continue
        seen[h]=(c,s.reset_index(drop=True));keep.append(c)
    t=t.merge(b[keep],on=ID,how='left',validate='one_to_one')
assert len(t)==197 and t[ID].is_unique
t.to_parquet(OUT/'family1_features_all.parquet',index=False)
pd.DataFrame(eliminations).to_csv(AUD/'feature_eliminations.csv',index=False)
d=combine_dictionary(); d['included_in_master']=d.feature_name.isin(t.columns); d.to_csv(OUT/'family1_feature_dictionary.csv',index=False)
print('Master:',t.shape,'eliminadas:',len(eliminations))
