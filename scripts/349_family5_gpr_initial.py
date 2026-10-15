"""Only the authorized initial F5 GPR experiments and exact C-T3 control."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.family_5.gpr_initial.execution import run
if __name__=='__main__':run(workers=3)
