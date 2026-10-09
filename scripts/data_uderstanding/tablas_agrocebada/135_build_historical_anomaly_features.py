from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]; sys.path.insert(0,str(ROOT/'src'))
from family_1.feature_pipeline import build_history_anomaly
build_history_anomaly(); print('History/anomaly features generadas')
