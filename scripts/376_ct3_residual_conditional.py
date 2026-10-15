import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.ct3_residual_conditional.execution import run
if __name__=='__main__':run()
