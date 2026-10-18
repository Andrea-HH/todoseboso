"""Finish evaluations only after the frozen execution has completed."""
from pathlib import Path
import subprocess,sys,time,json,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/modeling/four_expert_combinations/v1'
def main():
    while not (OUT/'execution_complete.json').exists():time.sleep(30)
    for filename in ['performance_amendment.json','evaluation_amendment.json','tuner_performance_amendment.json']:
        cfg=json.loads((OUT/filename).read_text());assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in cfg['source_sha256'].items())
    commands=[['-m','pytest','tests/test_four_expert_combinations.py','tests/test_four_expert_support.py','tests/test_local_ridge_sufficient_statistics.py','tests/test_four_expert_fast_tuner.py','-q'],['scripts/510_evaluate_four_expert_combinations.py'],['scripts/509_diagnose_expert_complementarity.py'],['scripts/506_deliver_four_expert_combinations.py']]
    for i,args in enumerate(commands):
        with (OUT/'audit'/f'finalize_{i}.log').open('w',encoding='utf-8') as stream:subprocess.run([sys.executable]+args,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
        print('Finished '+str(args),flush=True)
    (OUT/'finalizer_complete.json').write_text(json.dumps(dict(status='complete',commands=len(commands),no_PRED=True,no_champion_change=True),indent=2));print('Delivery complete',flush=True)
if __name__=='__main__':main()
