"""Resume/reproduce the frozen experiment and its documented packaging recovery."""
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/modeling/difficult_case_signals/v1'


def run(name,check=True):
    return subprocess.run([sys.executable,str(ROOT/'scripts'/name)],cwd=ROOT,check=check)


def main():
    if not (OUT/'frozen_design.json').exists():run('454_prepare_difficult_case_signals.py')
    if not (OUT/'execution_complete.json').exists():
        result=run('455_run_difficult_case_signals.py',check=False)
        if not (OUT/'execution_complete.json').exists():
            if not all((OUT/'checkpoints'/f'{i:02d}.joblib').exists() for i in range(65)):
                raise RuntimeError(f'Training incomplete (exit {result.returncode}); preserve checkpoints and inspect error.')
            run('457_finalize_difficult_case_signals.py')
    if not (OUT/'evaluation_complete.json').exists():run('456_evaluate_difficult_case_signals.py')
    run('458_audit_difficult_case_signals_delivery.py')


if __name__=='__main__':main()
