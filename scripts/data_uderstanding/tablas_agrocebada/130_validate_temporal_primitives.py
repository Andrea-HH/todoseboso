from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]; sys.path.insert(0,str(ROOT/'src'))
import numpy as np, pandas as pd
from family_1.temporal_primitives import extract_temporal_features
r=extract_temporal_features(pd.to_datetime(['2025-04-01','2025-04-03','2025-04-10']),[1,3,2])
assert np.isclose(r['auc'],21.5) and r['max_growth_rate']==1 and r['max_drawdown']==1 and r['max_runup']==2
print('Primitivas temporales validadas con spacing irregular:',r)
