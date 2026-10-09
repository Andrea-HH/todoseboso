from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]; sys.path.insert(0,str(ROOT/'src'))
from family_1.feature_pipeline import build_sentinel
build_sentinel(); print('Sentinel features generadas')
