import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.r2_residual_diagnosis import run
if __name__=='__main__':run()
