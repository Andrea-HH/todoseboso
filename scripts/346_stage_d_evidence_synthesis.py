"""Run Stage D exclusively: immutable archived predictions and descriptive diagnostics."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.family_4.stage_d_evidence import run
if __name__=='__main__':run()
