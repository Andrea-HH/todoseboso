from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
from family_1.stage4_modeling import load_xy,save_splits
ids,_,_=load_xy();s=save_splits(ids);print('Splits congelados:',len(s),'repeats:',s.repeat.nunique())
