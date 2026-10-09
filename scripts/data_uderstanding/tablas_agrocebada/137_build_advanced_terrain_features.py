from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
from family_1.terrain_features import build_advanced
build_advanced();print('Topografía avanzada generada')
