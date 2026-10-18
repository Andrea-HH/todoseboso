"""Attempt independent clean wheel installation and immutable59 model replay."""
from pathlib import Path
import json
import subprocess
import sys
import time
import venv

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/research/four_final_checks/v1'
PUB=ROOT/'results/four_final_checks/v1'


def main():
    start=time.perf_counter()
    info=json.loads((OUT/'isolated_replay.json').read_text(encoding='utf-8'))
    requirements=info['imported_distributions'];assert requirements
    req=ROOT/'configs/four_final_checks/v1/replay_requirements.txt'
    req.write_text('\n'.join(f'{n}=={v}' for n,v in sorted(requirements.items()))+'\n',encoding='utf-8',newline='\n')
    env=OUT/'clean_replay_env';python=env/'Scripts/python.exe'
    if not python.exists():venv.EnvBuilder(system_site_packages=False,with_pip=True).create(env)
    log=OUT/'clean_install.log'
    with log.open('w',encoding='utf-8') as stream:
        result=subprocess.run([str(python.resolve()),'-m','pip','install','--only-binary=:all:','--disable-pip-version-check','--timeout','20','--retries','1','-r',str(req.resolve())],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
    audit=dict(clean_venv=True,system_site_packages=False,requested_versions=requirements,install_exit_code=result.returncode,install_log=str(log.relative_to(ROOT)),elapsed_seconds=time.perf_counter()-start)
    if result.returncode==0:
        replay=subprocess.run([str(python.resolve()),str(ROOT/'scripts/536_operational_support_intervals.py'),'replay'],cwd=ROOT,capture_output=True,text=True)
        (OUT/'clean_replay_stderr.txt').write_text(replay.stderr,encoding='utf-8')
        audit['replay_exit_code']=replay.returncode
        if replay.returncode==0:
            actual=json.loads((OUT/'isolated_replay.json').read_text(encoding='utf-8'))
            (OUT/'clean_replay.json').write_text(json.dumps(actual,indent=2),encoding='utf-8')
            audit['status']='passed';audit['replay']=actual
        else:
            audit['status']='replay_failed';audit['error_tail']=replay.stderr[-2000:]
    else:
        audit['status']='install_failed';audit['error_tail']=log.read_text(encoding='utf-8',errors='replace')[-2500:]
    audit['elapsed_seconds']=time.perf_counter()-start
    (PUB/'clean_environment_audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in audit.items() if k not in ['requested_versions','replay']},indent=2),flush=True)


if __name__=='__main__':main()
