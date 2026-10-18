"""Resume65 sensitivity folds in six isolated worker processes after controls."""
from pathlib import Path
import subprocess
import sys
import time
import json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/research/four_final_checks/v1'


def main():
    for i in [0,63]:
        p=OUT/'control_memory'/f'{i:02d}'/'complete.json';assert p.exists(),f'Control{i} still pending'
        assert json.loads(p.read_text())['maximum_difference_vs26']<1e-10
    pending=[i for i in range(65) if not (OUT/'no_hhi_memory'/f'{i:02d}'/'complete.json').exists()]
    pending=[i for i in pending if i>=50]+[i for i in pending if i<50]
    directory=OUT/'worker_logs';directory.mkdir(parents=True,exist_ok=True)
    processes=[];handles=[]
    for j in range(min(6,len(pending))):
        ids=pending[j::6];handle=(directory/f'worker{j}.log').open('w',encoding='utf-8');handles.append(handle)
        command=[sys.executable,str(ROOT/'scripts/535_no_hhi_reference26.py'),'worker','--mode','no_hhi','--fast','--folds',','.join(map(str,ids))]
        processes.append(subprocess.Popen(command,cwd=ROOT,stdout=handle,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)))
    previous=-1
    while any(p.poll() is None for p in processes):
        done=len(list((OUT/'no_hhi_memory').glob('*/complete.json'))) if (OUT/'no_hhi_memory').exists() else 0
        if done!=previous:print(f'Sensitivity completed{done}/65 folds; workers active{sum(p.poll() is None for p in processes)}',flush=True);previous=done
        time.sleep(15)
    for handle in handles:handle.close()
    codes=[p.returncode for p in processes]
    if any(codes):raise RuntimeError('Sensitivity worker failed; inspect worker_logs; codes='+str(codes))
    assert len(list((OUT/'no_hhi_memory').glob('*/complete.json')))==65
    print('All65 sensitivity folds completed.',flush=True)


if __name__=='__main__':main()
