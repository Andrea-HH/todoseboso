"""Gather only when all disjoint training pools have written their checkpoints."""
from pathlib import Path
import time,importlib.util,sys
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/modeling/four_expert_combinations/v1'
def main():
    while not all((OUT/'checkpoints'/f'{i:02d}.joblib').exists() for i in range(81)):time.sleep(30)
    time.sleep(5)  # Allow the final compressed checkpoint writer to close its file.
    spec=importlib.util.spec_from_file_location('gather507',ROOT/'scripts/507_run_four_expert_fast.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);sys.argv=[str(ROOT/'scripts/507_run_four_expert_fast.py')];module.main()
if __name__=='__main__':main()
