"""Section I official soil representation; does not fit yield models."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from src.family_1.i_geographic_edaphological import soil
if __name__=='__main__':print(json.dumps(soil(),indent=2,ensure_ascii=True))
